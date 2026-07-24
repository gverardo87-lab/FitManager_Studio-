"""
Tunnel Manager — babysitter del processo frpc.

Gestisce il ciclo di vita del tunnel FRP:
- Genera frpc.toml da TunnelConfig
- Avvia frpc come processo figlio (subprocess.Popen)
- Monitora e riavvia con backoff esponenziale + jitter
- Shutdown pulito (kill frpc alla chiusura dell'app)
- Log strutturato di ogni evento (avvio, crash, restart, stop)

Pattern: stesso ruolo di systemd sul VPS (babysitter di frps),
ma dentro l'applicazione invece che a livello di sistema operativo.
"""

from __future__ import annotations

import atexit
import logging
import random
import subprocess
import sys
import threading
import time
from enum import Enum

from api.services.tunnel_config import TunnelConfig

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Windows Job Object — kill frpc quando il backend muore (anche brusco)
# ---------------------------------------------------------------------------
#
# frpc viene lanciato come processo NIPOTE detached (CREATE_NO_WINDOW): se il
# backend viene terminato bruscamente (chiusura finestra launcher, TerminateProcess)
# ne' atexit ne' lo shutdown ASGI scattano, e frpc resta orfano. Un frpc orfano
# tiene il lock sul proprio binario -> il prossimo installer non riesce a
# sovrascrivere backend\frpc.exe (ERROR_ACCESS_DENIED, codice 5).
#
# Soluzione: assegnare frpc a un Job Object con JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE.
# Il SO uccide tutti i processi del job quando l'ultimo handle al job si chiude —
# cioe' quando il processo backend (che tiene l'handle) termina, comunque termini.
# Questo e' l'unico meccanismo affidabile su Windows contro l'orfanaggio.


def _create_kill_on_close_job():
    """Crea un Job Object Windows con KILL_ON_JOB_CLOSE.

    Restituisce l'handle del job, o None su non-Windows / errore (in tal caso si
    ricade sul cleanup best-effort via atexit + stop(), gia' presente).
    L'handle va tenuto vivo per tutta la vita del manager: alla sua chiusura il
    SO killa i processi assegnati.
    """
    if not sys.platform.startswith("win"):
        return None
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        CreateJobObject = kernel32.CreateJobObjectW
        CreateJobObject.restype = wintypes.HANDLE
        CreateJobObject.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]

        job = CreateJobObject(None, None)
        if not job:
            return None

        class _BasicLimit(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_int64),
                ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class _IoCounters(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_uint64),
                ("WriteOperationCount", ctypes.c_uint64),
                ("OtherOperationCount", ctypes.c_uint64),
                ("ReadTransferCount", ctypes.c_uint64),
                ("WriteTransferCount", ctypes.c_uint64),
                ("OtherTransferCount", ctypes.c_uint64),
            ]

        class _ExtendedLimit(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", _BasicLimit),
                ("IoInfo", _IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
        JobObjectExtendedLimitInformation = 9

        info = _ExtendedLimit()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE

        SetInformationJobObject = kernel32.SetInformationJobObject
        SetInformationJobObject.restype = wintypes.BOOL
        SetInformationJobObject.argtypes = [
            wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD,
        ]

        ok = SetInformationJobObject(
            job,
            JobObjectExtendedLimitInformation,
            ctypes.byref(info),
            ctypes.sizeof(info),
        )
        if not ok:
            kernel32.CloseHandle(job)
            return None

        logger.info("Job Object tunnel creato (kill-on-close): frpc morira' col backend")
        return job
    except Exception as e:
        logger.warning("Job Object non disponibile (%s) — fallback cleanup atexit/stop", e)
        return None


def _assign_process_to_job(job, pid: int) -> bool:
    """Assegna il processo `pid` al Job Object. False su errore (non fatale)."""
    if job is None:
        return False
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        PROCESS_SET_QUOTA = 0x0100
        PROCESS_TERMINATE = 0x0001

        OpenProcess = kernel32.OpenProcess
        OpenProcess.restype = wintypes.HANDLE
        OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]

        hproc = OpenProcess(PROCESS_SET_QUOTA | PROCESS_TERMINATE, False, pid)
        if not hproc:
            return False
        try:
            AssignProcessToJobObject = kernel32.AssignProcessToJobObject
            AssignProcessToJobObject.restype = wintypes.BOOL
            AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
            return bool(AssignProcessToJobObject(job, hproc))
        finally:
            kernel32.CloseHandle(hproc)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Stato tunnel (per health endpoint e diagnostica UI)
# ---------------------------------------------------------------------------

class TunnelState(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


# ---------------------------------------------------------------------------
# Backoff esponenziale con jitter
# ---------------------------------------------------------------------------

class BackoffTimer:
    """Attesa crescente tra retry per evitare retry storm.

    Primo retry: 1s, poi 2s, 4s, 8s, ... fino a max 60s.
    Jitter: aggiunge 0-1s casuale (evita thundering herd se frps si riavvia).
    Reset: dopo 5 minuti di connessione stabile, torna a 1s.
    """

    BASE_DELAY = 1.0
    MAX_DELAY = 60.0
    STABILITY_RESET = 300.0  # 5 minuti

    def __init__(self):
        self._attempt = 0
        self._last_success: float = 0.0

    def next_delay(self) -> float:
        delay = min(self.BASE_DELAY * (2 ** self._attempt), self.MAX_DELAY)
        jitter = random.uniform(0, self.BASE_DELAY)
        self._attempt += 1
        return delay + jitter

    def record_success(self):
        self._last_success = time.monotonic()

    def maybe_reset(self):
        if self._last_success and (time.monotonic() - self._last_success) >= self.STABILITY_RESET:
            self._attempt = 0

    def reset(self):
        self._attempt = 0
        self._last_success = 0.0


# ---------------------------------------------------------------------------
# Generazione frpc.toml
# ---------------------------------------------------------------------------

def generate_frpc_toml(config: TunnelConfig) -> str:
    """Genera il contenuto di frpc.toml da TunnelConfig.

    Il proxy HTTPS applicativo usa https2http: il VPS fa SNI passthrough,
    frpc termina TLS sul PC trainer e inoltra a Next.js locale.

    Il secondo proxy HTTP serve esclusivamente il path ACME HTTP-01 da un
    webroot statico dedicato. Non ha Next.js/API come upstream: tutte le altre
    route HTTP restano senza proxy e ricevono 404 da frps.
    """
    return (
        f'# frpc.toml — generato da FitManager\n'
        f'# Instance: {config.instance_id}\n'
        f'# NON modificare: rigenerato ad ogni avvio.\n'
        f'\n'
        f'serverAddr = "{config.server_addr}"\n'
        f'serverPort = {config.server_port}\n'
        f'\n'
        f'[[proxies]]\n'
        f'name = "{config.instance_id}"\n'
        f'type = "https"\n'
        f'customDomains = ["{config.public_url}"]\n'
        f'\n'
        f'[proxies.plugin]\n'
        f'type = "https2http"\n'
        f'localAddr = "127.0.0.1:3000"\n'
        f'crtPath = "{config.cert_path.as_posix()}"\n'
        f'keyPath = "{config.key_path.as_posix()}"\n'
        f'\n'
        f'[[proxies]]\n'
        f'name = "{config.instance_id}-acme-http"\n'
        f'type = "http"\n'
        f'customDomains = ["{config.public_url}"]\n'
        f'locations = ["/.well-known/acme-challenge/"]\n'
        f'\n'
        f'[proxies.plugin]\n'
        f'type = "static_file"\n'
        f'localPath = "{config.acme_webroot_path.as_posix()}"\n'
    )


def _write_frpc_config(config: TunnelConfig) -> None:
    """Scrive frpc.toml su disco."""
    content = generate_frpc_toml(config)
    config.config_path.parent.mkdir(parents=True, exist_ok=True)
    config.config_path.write_text(content, encoding="utf-8")
    logger.info("frpc.toml scritto: %s", config.config_path)


# ---------------------------------------------------------------------------
# TunnelManager
# ---------------------------------------------------------------------------

class TunnelManager:
    """Babysitter del processo frpc.

    Uso:
        config = get_tunnel_config()
        manager = TunnelManager(config)
        manager.start()   # avvia frpc + monitor in background
        ...
        manager.stop()     # shutdown pulito
    """

    MONITOR_INTERVAL = 5.0  # secondi tra un check e l'altro

    def __init__(self, config: TunnelConfig):
        self.config = config
        self.state = TunnelState.STOPPED
        self._process: subprocess.Popen | None = None
        self._should_run = False
        self._monitor_thread: threading.Thread | None = None
        self._backoff = BackoffTimer()
        self._lock = threading.Lock()

        # Job Object: garantisce che frpc venga ucciso dal SO quando il backend
        # termina, anche su kill brusco (atexit/stop sotto sono il fallback).
        self._job = _create_kill_on_close_job()

        # Registra cleanup alla chiusura dell'app (evita processi orfani)
        atexit.register(self._cleanup)

    # --- API pubblica ---

    def start(self):
        """Genera config, avvia frpc, avvia monitor in background."""
        if self._should_run:
            logger.warning("TunnelManager gia' in esecuzione, start() ignorato")
            return

        logger.info(
            "Tunnel avvio: %s -> %s",
            self.config.instance_id,
            self.config.public_url,
        )

        # 1. Genera frpc.toml
        _write_frpc_config(self.config)

        # 2. Avvia frpc
        self._should_run = True
        self._launch()

        # 3. Avvia monitor in background (daemon thread: muore col programma)
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="tunnel-monitor",
            daemon=True,
        )
        self._monitor_thread.start()

    def stop(self):
        """Ferma il tunnel e il monitor."""
        logger.info("Tunnel stop: %s", self.config.instance_id)
        self._should_run = False
        self._kill()
        self.state = TunnelState.STOPPED

    def get_status(self) -> dict:
        """Stato corrente per health endpoint / diagnostica UI."""
        return {
            "state": self.state.value,
            "instance_id": self.config.instance_id,
            "public_url": self.config.public_url,
            "pid": (
                self._process.pid
                if self._process and self._process.poll() is None
                else None
            ),
        }

    # --- Gestione processo ---

    def _launch(self):
        """Avvia frpc come processo figlio."""
        with self._lock:
            if self._process and self._process.poll() is None:
                logger.warning(
                    "frpc gia' in esecuzione (PID %d), skip",
                    self._process.pid,
                )
                return

            self.state = TunnelState.STARTING
            cmd = [str(self.config.frpc_path), "-c", str(self.config.config_path)]

            try:
                self._process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    # Windows: non aprire finestra console visibile al trainer
                    creationflags=(
                        subprocess.CREATE_NO_WINDOW
                        if hasattr(subprocess, "CREATE_NO_WINDOW")
                        else 0
                    ),
                )
                logger.info(
                    "frpc avviato (PID %d): %s",
                    self._process.pid,
                    " ".join(cmd),
                )

                # Aggancia frpc al Job Object: morira' col backend (no orfani)
                if self._job is not None:
                    if _assign_process_to_job(self._job, self._process.pid):
                        logger.debug("frpc agganciato al Job Object (kill-on-close)")
                    else:
                        logger.warning(
                            "Assegnazione frpc al Job Object fallita — "
                            "cleanup affidato a atexit/stop"
                        )

                self.state = TunnelState.CONNECTED
                self._backoff.record_success()

                # Thread per leggere output frpc (evita buffer pieno → deadlock)
                threading.Thread(
                    target=self._drain_output,
                    name="tunnel-output",
                    daemon=True,
                ).start()

            except FileNotFoundError:
                logger.error("frpc non trovato: %s", self.config.frpc_path)
                self.state = TunnelState.ERROR
            except PermissionError:
                logger.error(
                    "Permesso negato per frpc: %s — possibile blocco antivirus/firewall",
                    self.config.frpc_path,
                )
                self.state = TunnelState.ERROR
            except OSError as e:
                logger.error("Errore avvio frpc: %s", e)
                self.state = TunnelState.ERROR

    def _kill(self):
        """Termina frpc: prima terminate (gentile), poi kill (forza) dopo 5s."""
        with self._lock:
            if self._process is None:
                return

            if self._process.poll() is not None:
                self._process = None
                return

            pid = self._process.pid
            logger.info("Terminazione frpc (PID %d)...", pid)

            try:
                self._process.terminate()
                try:
                    self._process.wait(timeout=5)
                    logger.info("frpc terminato (PID %d)", pid)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    logger.warning("frpc ucciso forzatamente (PID %d)", pid)
            except OSError as e:
                logger.error("Errore terminazione frpc: %s", e)
            finally:
                self._process = None

    def _drain_output(self):
        """Legge output di frpc e lo logga. Previene deadlock da buffer pieno."""
        proc = self._process
        if not proc or not proc.stdout:
            return
        try:
            for line in proc.stdout:
                line = line.rstrip()
                if line:
                    logger.debug("[frpc] %s", line)
        except (ValueError, OSError):
            pass  # pipe chiusa durante shutdown — normale

    # --- Monitor loop ---

    def _monitor_loop(self):
        """Loop in background: controlla che frpc sia vivo, riavvia se crasha."""
        logger.info("Monitor tunnel avviato")

        while self._should_run:
            time.sleep(self.MONITOR_INTERVAL)

            if not self._should_run:
                break

            with self._lock:
                proc = self._process

            if proc is None:
                if self._should_run:
                    self._restart()
                continue

            exit_code = proc.poll()

            if exit_code is None:
                # Processo vivo — tutto ok
                self._backoff.maybe_reset()
                continue

            # Processo morto — restart con backoff
            logger.warning("frpc terminato (exit code %d)", exit_code)
            with self._lock:
                self._process = None

            if self._should_run:
                self._restart()

        logger.info("Monitor tunnel fermato")

    def _restart(self):
        """Riavvia frpc dopo attesa con backoff."""
        self.state = TunnelState.RECONNECTING
        delay = self._backoff.next_delay()
        logger.info("Restart frpc tra %.1fs...", delay)

        # Attendi con check periodico (per uscire subito se stop() chiamato)
        waited = 0.0
        while waited < delay and self._should_run:
            time.sleep(min(1.0, delay - waited))
            waited += 1.0

        if self._should_run:
            self._launch()

    # --- Cleanup ---

    def _cleanup(self):
        """Handler atexit: uccide frpc alla chiusura dell'app (evita orfani)."""
        if self._process and self._process.poll() is None:
            logger.info("Cleanup atexit: terminazione frpc...")
            self._kill()

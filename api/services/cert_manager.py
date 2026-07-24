"""Gestione R0.1.5 dei certificati pubblici del tunnel FRP.

Il protocollo ACME non viene reimplementato: viene eseguito lego, client standalone
pinato dal build, in modalita HTTP-01 webroot. Certificato e chiave restano sul PC
trainer e vengono promossi sui path attivi solo dopo controlli crittografici.
"""

from __future__ import annotations

import datetime
import hashlib
import logging
import os
import secrets
import shutil
import subprocess
import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable

import requests
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed448, ed25519, padding, rsa

from api import __version__
from api.services.tunnel_config import TunnelConfig

logger = logging.getLogger(__name__)

ACME_CLIENT_VERSION = "5.2.1"
ACME_CLIENT_SHA256_WINDOWS_AMD64 = (
    "e2d5f33c26032197db5953f8cfd93aa960f08cf2014c887b79ba950cb5b525e5"
)
ACME_SERVER = "letsencrypt"
RENEW_BEFORE_DAYS = 30
CHECK_INTERVAL_SECONDS = 12 * 60 * 60
FAILURE_RETRY_SECONDS = 15 * 60
STARTUP_DELAY_SECONDS = 5
ACME_COMMAND_TIMEOUT_SECONDS = 15 * 60


@dataclass(frozen=True)
class CertificateCheck:
    usable: bool
    public_chain: bool
    reason: str
    expires_at: datetime.datetime | None = None

    @property
    def days_remaining(self) -> float | None:
        if self.expires_at is None:
            return None
        remaining = self.expires_at - datetime.datetime.now(datetime.timezone.utc)
        return remaining.total_seconds() / 86400


class CertificateAction(str, Enum):
    CURRENT = "current"
    INSTALLED = "installed"
    FAILED = "failed"
    DISABLED = "disabled"


@dataclass(frozen=True)
class CertificateRunResult:
    action: CertificateAction
    detail: str
    expires_at: datetime.datetime | None = None


CommandRunner = Callable[[list[str]], subprocess.CompletedProcess[str]]
HTTP01Probe = Callable[[], bool]


def _load_certificates(path: Path) -> list[x509.Certificate]:
    data = path.read_bytes()
    loader = getattr(x509, "load_pem_x509_certificates", None)
    if loader is not None:
        return list(loader(data))

    marker = b"-----END CERTIFICATE-----"
    certificates: list[x509.Certificate] = []
    for chunk in data.split(marker):
        if b"-----BEGIN CERTIFICATE-----" not in chunk:
            continue
        certificates.append(x509.load_pem_x509_certificate(chunk + marker + b"\n"))
    return certificates


def _public_keys_match(certificate: x509.Certificate, key_path: Path) -> bool:
    private_key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
    cert_public = certificate.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    key_public = private_key.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return cert_public == key_public


def _leaf_signature_is_valid(leaf: x509.Certificate, issuer: x509.Certificate) -> bool:
    if leaf.issuer != issuer.subject:
        return False
    try:
        public_key = issuer.public_key()
        if isinstance(public_key, rsa.RSAPublicKey):
            public_key.verify(
                leaf.signature,
                leaf.tbs_certificate_bytes,
                padding.PKCS1v15(),
                leaf.signature_hash_algorithm,
            )
        elif isinstance(public_key, ec.EllipticCurvePublicKey):
            public_key.verify(
                leaf.signature,
                leaf.tbs_certificate_bytes,
                ec.ECDSA(leaf.signature_hash_algorithm),
            )
        elif isinstance(public_key, (ed25519.Ed25519PublicKey, ed448.Ed448PublicKey)):
            public_key.verify(leaf.signature, leaf.tbs_certificate_bytes)
        else:
            return False
    except Exception:
        return False
    return True


def inspect_certificate_pair(
    cert_path: Path,
    key_path: Path,
    hostname: str,
    *,
    require_public_chain: bool,
    now: datetime.datetime | None = None,
) -> CertificateCheck:
    """Valida SAN, finestra temporale, key-match e (se richiesto) chain bundled."""
    if not cert_path.is_file() or not key_path.is_file():
        return CertificateCheck(False, False, "cert_or_key_missing")

    now = now or datetime.datetime.now(datetime.timezone.utc)
    try:
        certificates = _load_certificates(cert_path)
        if not certificates:
            return CertificateCheck(False, False, "certificate_missing")
        leaf = certificates[0]

        if leaf.not_valid_before_utc > now:
            return CertificateCheck(False, False, "certificate_not_yet_valid")
        if leaf.not_valid_after_utc <= now:
            return CertificateCheck(
                False,
                False,
                "certificate_expired",
                leaf.not_valid_after_utc,
            )

        sans = leaf.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        ).value.get_values_for_type(x509.DNSName)
        if hostname not in sans:
            return CertificateCheck(False, False, "hostname_not_in_san")
        if not _public_keys_match(leaf, key_path):
            return CertificateCheck(False, False, "certificate_key_mismatch")

        public_chain = (
            leaf.subject != leaf.issuer
            and len(certificates) >= 2
            and _leaf_signature_is_valid(leaf, certificates[1])
            and certificates[1].not_valid_before_utc <= now
            and certificates[1].not_valid_after_utc > now
        )
        if require_public_chain and not public_chain:
            return CertificateCheck(
                False,
                False,
                "public_chain_missing_or_invalid",
                leaf.not_valid_after_utc,
            )

        return CertificateCheck(
            True,
            public_chain,
            "ok",
            leaf.not_valid_after_utc,
        )
    except Exception as exc:
        logger.warning("Coppia TLS illeggibile: %s", exc.__class__.__name__)
        return CertificateCheck(False, False, "certificate_parse_error")


def _write_staged_file(path: Path, data: bytes, *, private: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    if private and os.name != "nt":
        path.chmod(0o600)


def recover_interrupted_install(config: TunnelConfig) -> bool:
    """Ripristina la coppia precedente se un processo e morto durante la promozione."""
    marker = config.data_dir / "certificate-install.pending"
    previous_cert = config.cert_path.with_name(f"{config.cert_path.name}.previous")
    previous_key = config.key_path.with_name(f"{config.key_path.name}.previous")
    if not marker.exists():
        return False
    if not previous_cert.is_file() or not previous_key.is_file():
        logger.error("Recovery TLS impossibile: backup pair incompleta")
        return False

    os.replace(previous_key, config.key_path)
    os.replace(previous_cert, config.cert_path)
    marker.unlink(missing_ok=True)
    logger.warning("Recovery TLS: ripristinata la coppia precedente")
    return True


def install_certificate_pair(
    config: TunnelConfig,
    candidate_cert: Path,
    candidate_key: Path,
) -> bool:
    """Promuove cert/key con marker di recovery e rollback della coppia precedente."""
    hostname = config.public_url
    candidate = inspect_certificate_pair(
        candidate_cert,
        candidate_key,
        hostname,
        require_public_chain=True,
    )
    if not candidate.usable:
        raise ValueError(f"candidate_{candidate.reason}")

    cert_data = candidate_cert.read_bytes()
    key_data = candidate_key.read_bytes()
    if (
        config.cert_path.is_file()
        and config.key_path.is_file()
        and config.cert_path.read_bytes() == cert_data
        and config.key_path.read_bytes() == key_data
    ):
        return False

    staged_cert = config.cert_path.with_name(f"{config.cert_path.name}.new")
    staged_key = config.key_path.with_name(f"{config.key_path.name}.new")
    previous_cert = config.cert_path.with_name(f"{config.cert_path.name}.previous")
    previous_key = config.key_path.with_name(f"{config.key_path.name}.previous")
    marker = config.data_dir / "certificate-install.pending"

    _write_staged_file(staged_cert, cert_data, private=False)
    _write_staged_file(staged_key, key_data, private=True)
    staged = inspect_certificate_pair(
        staged_cert,
        staged_key,
        hostname,
        require_public_chain=True,
    )
    if not staged.usable:
        staged_cert.unlink(missing_ok=True)
        staged_key.unlink(missing_ok=True)
        raise ValueError(f"staged_{staged.reason}")

    config.data_dir.mkdir(parents=True, exist_ok=True)
    had_previous_pair = config.cert_path.is_file() and config.key_path.is_file()
    if had_previous_pair:
        shutil.copy2(config.cert_path, previous_cert)
        shutil.copy2(config.key_path, previous_key)
    _write_staged_file(marker, b"pending\n", private=False)

    try:
        os.replace(staged_key, config.key_path)
        os.replace(staged_cert, config.cert_path)
        installed = inspect_certificate_pair(
            config.cert_path,
            config.key_path,
            hostname,
            require_public_chain=True,
        )
        if not installed.usable:
            raise ValueError(f"installed_{installed.reason}")
    except Exception:
        if had_previous_pair and previous_cert.exists() and previous_key.exists():
            os.replace(previous_key, config.key_path)
            os.replace(previous_cert, config.cert_path)
            marker.unlink(missing_ok=True)
        raise
    else:
        marker.unlink(missing_ok=True)
    finally:
        staged_cert.unlink(missing_ok=True)
        staged_key.unlink(missing_ok=True)

    previous_cert.unlink(missing_ok=True)
    previous_key.unlink(missing_ok=True)
    return True


class CertificateManager:
    """Scheduler fail-local per emissione/rinnovo e installazione del cert pubblico."""

    def __init__(
        self,
        config: TunnelConfig,
        *,
        on_certificate_updated: Callable[[], object] | None = None,
        command_runner: CommandRunner | None = None,
        http01_probe: HTTP01Probe | None = None,
        expected_client_sha256: str = ACME_CLIENT_SHA256_WINDOWS_AMD64,
        expected_client_version: str = ACME_CLIENT_VERSION,
    ):
        self.config = config
        self._on_certificate_updated = on_certificate_updated
        self._command_runner = command_runner or self._run_command
        self._http01_probe = http01_probe or self._probe_http01_path
        self._expected_client_sha256 = expected_client_sha256
        self._expected_client_version = expected_client_version
        self._stop_event = threading.Event()
        self._run_lock = threading.Lock()
        self._process_lock = threading.Lock()
        self._process: subprocess.Popen[str] | None = None
        self._thread: threading.Thread | None = None
        self._last_result = CertificateRunResult(
            CertificateAction.DISABLED,
            "not_started",
        )

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            logger.warning("CertificateManager gia in esecuzione, start ignorato")
            return
        if self.config.acme_client_path is None:
            self._last_result = CertificateRunResult(
                CertificateAction.DISABLED,
                "acme_client_missing",
            )
            logger.warning("Client ACME assente: tunnel bootstrap e CRM locale preservati")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._scheduler_loop,
            name="certificate-manager",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._terminate_active_process()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._thread = None

    def get_status(self) -> dict:
        return {
            "action": self._last_result.action.value,
            "detail": self._last_result.detail,
            "expires_at": (
                self._last_result.expires_at.isoformat()
                if self._last_result.expires_at
                else None
            ),
        }

    def _scheduler_loop(self) -> None:
        if self._stop_event.wait(STARTUP_DELAY_SECONDS):
            return
        while not self._stop_event.is_set():
            result = self.run_once()
            delay = (
                FAILURE_RETRY_SECONDS
                if result.action in {CertificateAction.FAILED, CertificateAction.DISABLED}
                else CHECK_INTERVAL_SECONDS
            )
            if self._stop_event.wait(delay):
                return

    def run_once(self) -> CertificateRunResult:
        if not self._run_lock.acquire(blocking=False):
            return self._last_result
        try:
            recover_interrupted_install(self.config)
            hostname = self.config.public_url
            current = inspect_certificate_pair(
                self.config.cert_path,
                self.config.key_path,
                hostname,
                require_public_chain=True,
            )
            if (
                current.usable
                and current.days_remaining is not None
                and current.days_remaining > RENEW_BEFORE_DAYS
            ):
                self._last_result = CertificateRunResult(
                    CertificateAction.CURRENT,
                    "certificate_not_due",
                    current.expires_at,
                )
                return self._last_result

            client_error = self._validate_acme_client()
            if client_error:
                self._last_result = CertificateRunResult(
                    CertificateAction.DISABLED,
                    client_error,
                    current.expires_at,
                )
                return self._last_result

            if not self._http01_probe():
                logger.warning("Preflight HTTP-01 fallito: ordine ACME non avviato")
                self._last_result = CertificateRunResult(
                    CertificateAction.FAILED,
                    "http01_preflight_failed",
                    current.expires_at,
                )
                return self._last_result

            command = self._build_command()
            result = self._command_runner(command)
            if result.returncode != 0:
                detail = (result.stderr or result.stdout or "acme_failed").strip()[:500]
                logger.warning("ACME fallito (exit %s): %s", result.returncode, detail)
                self._last_result = CertificateRunResult(
                    CertificateAction.FAILED,
                    f"acme_exit_{result.returncode}",
                    current.expires_at,
                )
                return self._last_result

            candidate_cert, candidate_key = self._candidate_paths()
            candidate = inspect_certificate_pair(
                candidate_cert,
                candidate_key,
                hostname,
                require_public_chain=True,
            )
            if not candidate.usable:
                self._last_result = CertificateRunResult(
                    CertificateAction.FAILED,
                    f"candidate_{candidate.reason}",
                    current.expires_at,
                )
                return self._last_result

            changed = install_certificate_pair(
                self.config,
                candidate_cert,
                candidate_key,
            )
            if changed and self._on_certificate_updated:
                self._on_certificate_updated()
            self._last_result = CertificateRunResult(
                CertificateAction.INSTALLED if changed else CertificateAction.CURRENT,
                "certificate_installed" if changed else "certificate_already_installed",
                candidate.expires_at,
            )
            return self._last_result
        except Exception as exc:
            logger.exception("Certificate manager fallito: %s", exc)
            self._last_result = CertificateRunResult(
                CertificateAction.FAILED,
                exc.__class__.__name__,
            )
            return self._last_result
        finally:
            self._run_lock.release()

    def _validate_acme_client(self) -> str | None:
        client_path = self.config.acme_client_path
        if client_path is None or not client_path.is_file():
            return "acme_client_missing"
        digest = hashlib.sha256(client_path.read_bytes()).hexdigest()
        if digest != self._expected_client_sha256:
            logger.error("Client ACME hash mismatch: esecuzione rifiutata")
            return "acme_client_hash_mismatch"

        result = self._command_runner([str(client_path), "--version"])
        version_output = f"{result.stdout}\n{result.stderr}"
        if result.returncode != 0 or self._expected_client_version not in version_output:
            return "acme_client_version_mismatch"
        return None

    def _build_command(self) -> list[str]:
        assert self.config.acme_client_path is not None
        return [
            str(self.config.acme_client_path),
            "--log.format",
            "json",
            "run",
            "--accept-tos",
            "--domains",
            self.config.public_url,
            "--key-type",
            "RSA2048",
            "--server",
            ACME_SERVER,
            "--http",
            "--http.webroot",
            str(self.config.acme_webroot_path),
            "--path",
            str(self.config.acme_state_path),
            "--cert.name",
            self.config.public_url,
            "--renew-days",
            str(RENEW_BEFORE_DAYS),
            "--user-agent",
            f"FitManager/{__version__}",
        ]

    def _candidate_paths(self) -> tuple[Path, Path]:
        certificates_dir = self.config.acme_state_path / "certificates"
        return (
            certificates_dir / f"{self.config.public_url}.crt",
            certificates_dir / f"{self.config.public_url}.key",
        )

    def _probe_http01_path(self) -> bool:
        challenge_dir = (
            self.config.acme_webroot_path / ".well-known" / "acme-challenge"
        )
        challenge_dir.mkdir(parents=True, exist_ok=True)
        token = f"fitmanager-preflight-{secrets.token_urlsafe(24)}"
        expected = secrets.token_urlsafe(32)
        token_path = challenge_dir / token
        _write_staged_file(token_path, expected.encode("ascii"), private=False)
        try:
            response = requests.get(
                f"http://{self.config.public_url}/.well-known/acme-challenge/{token}",
                allow_redirects=False,
                timeout=10,
            )
            return response.status_code == 200 and response.text == expected
        except requests.RequestException as exc:
            logger.info("Preflight HTTP-01 non raggiungibile: %s", exc.__class__.__name__)
            return False
        finally:
            token_path.unlink(missing_ok=True)

    def _run_command(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        with self._process_lock:
            if self._stop_event.is_set():
                return subprocess.CompletedProcess(
                    command,
                    -1,
                    stdout="",
                    stderr="certificate_manager_stopping",
                )
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.config.data_dir,
                text=True,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if hasattr(subprocess, "CREATE_NO_WINDOW")
                    else 0
                ),
            )
            self._process = process

        try:
            stdout, stderr = process.communicate(timeout=ACME_COMMAND_TIMEOUT_SECONDS)
            return subprocess.CompletedProcess(
                command,
                process.returncode,
                stdout=stdout,
                stderr=stderr,
            )
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            raise subprocess.TimeoutExpired(
                command,
                ACME_COMMAND_TIMEOUT_SECONDS,
                output=stdout,
                stderr=stderr,
            )
        finally:
            with self._process_lock:
                if self._process is process:
                    self._process = None

    def _terminate_active_process(self) -> None:
        with self._process_lock:
            process = self._process
        if process is None or process.poll() is not None:
            return

        logger.info("Arresto del processo ACME in corso")
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)
        except OSError as exc:
            logger.warning("Arresto processo ACME fallito: %s", exc)

"""
Machine Fingerprint — identifica univocamente la macchina per binding licenza.

Dual-platform, dispatch in `_compute_fingerprint()` su `platform.system()`:

Windows — 3 identificatori hardware via PowerShell Get-CimInstance (WMI):
- CPU ProcessorId, Motherboard SerialNumber, BIOS SerialNumber
- hash = SHA-256 di "cpu|board|bios" (forma storica: le licenze gia' firmate
  restano valide, il refactor multi-piattaforma non tocca questo output).

macOS (Darwin) — 2 identificatori letti ENTRAMBI da una SOLA invocazione
`ioreg -rd1 -c IOPlatformExpertDevice`:
- IOPlatformUUID (UUID della logic board) + IOPlatformSerialNumber (seriale macchina)
- hash = SHA-256 di "IOPlatformUUID|IOPlatformSerialNumber" (ordine fissato).
- La singola invocazione e' una clausola di design: con la disciplina AND ogni
  comando di sistema in piu' e' un punto di fallimento in piu' sul piano
  disponibilita'. Leggendo entrambi i campi dallo stesso output, "entrambi
  presenti" e "ioreg ha risposto" sono lo stesso evento.

Altre piattaforme → "unavailable" (safe-default).

Il fingerprint sopravvive a: aggiornamenti OS, driver, reinstall app, cambio disco/RAM.

INVARIANTE CRITICO (INC-2026-06-18) — vale identico su ENTRAMBE le piattaforme:
Il fingerprint si calcola SOLO se tutti gli identificatori previsti sono presenti.
Un set parziale (una lettura ritorna vuoto a causa di un singhiozzo transitorio)
NON deve mai essere hashato: produrrebbe un hash diverso dal `machine_id` firmato
nella licenza → falso "wrong_machine" → blocco accesso CRM. In caso di incompletezza
si ritorna "unavailable" (fail-closed) SENZA cacharlo, cosi' il tentativo successivo
ritenta e si auto-guarisce. Vedi `docs/incidents/INC-2026-06-18-...`.
"""

from __future__ import annotations

import hashlib
import logging
import platform
import re
import subprocess
import time

logger = logging.getLogger(__name__)

# Valore restituito quando l'hardware non e' (ancora) leggibile. Riconosciuto da
# license.py come fail-closed in frozen mode. NON cacharlo (vedi get_machine_fingerprint).
UNAVAILABLE = "unavailable"

_cached_fingerprint: str | None = None

# Robustezza letture hardware (WMI su Windows, ioreg su macOS): i singhiozzi sono
# frequenti su alcune macchine (system load, antivirus, risveglio da sleep).
# Si ritenta sui vuoti "veloci"; sui timeout no (la lettura ha gia' atteso a lungo)
# per non far esplodere la latenza.
_QUERY_TIMEOUT_SEC = 8
_QUERY_ATTEMPTS = 3
_RETRY_BACKOFF_SEC = 0.4


# ── Ramo Windows (WMI via PowerShell) ──────────────────────────────────────

# Mapping: (CIM class, property) per i 3 identificatori hardware
_HW_QUERIES: list[tuple[str, str]] = [
    ("Win32_Processor", "ProcessorId"),
    ("Win32_BaseBoard", "SerialNumber"),
    ("Win32_BIOS", "SerialNumber"),
]


def _powershell_query_once(cim_class: str, prop: str) -> str:
    """Singola query WMI via PowerShell. Stringa vuota se vuoto o returncode != 0.

    Solleva subprocess.TimeoutExpired sul timeout (gestito dal chiamante).
    """
    cmd = f"(Get-CimInstance -ClassName {cim_class}).{prop}"
    creationflags = (
        getattr(subprocess, "CREATE_NO_WINDOW", 0) if platform.system() == "Windows" else 0
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", cmd],
        capture_output=True,
        text=True,
        timeout=_QUERY_TIMEOUT_SEC,
        creationflags=creationflags,
    )
    value = result.stdout.strip()
    if value and result.returncode == 0:
        return value
    return ""


def _powershell_query(cim_class: str, prop: str) -> str:
    """Query WMI con retry sui fallimenti transitori. '' se tutti i tentativi falliscono.

    - Vuoto "veloce" (returncode != 0 o stdout vuoto) → ritenta (fino a _QUERY_ATTEMPTS).
    - Timeout → NON ritenta (ha gia' atteso _QUERY_TIMEOUT_SEC): ritorna '' subito.
    - Altra eccezione → ritenta.
    """
    for attempt in range(1, _QUERY_ATTEMPTS + 1):
        try:
            value = _powershell_query_once(cim_class, prop)
            if value:
                return value
            logger.warning(
                "WMI %s.%s vuoto (tentativo %d/%d)", cim_class, prop, attempt, _QUERY_ATTEMPTS
            )
        except subprocess.TimeoutExpired:
            logger.warning(
                "WMI %s.%s timeout dopo %ds — niente retry", cim_class, prop, _QUERY_TIMEOUT_SEC
            )
            return ""
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "WMI %s.%s errore (tentativo %d/%d): %s",
                cim_class, prop, attempt, _QUERY_ATTEMPTS, exc,
            )
        if attempt < _QUERY_ATTEMPTS:
            time.sleep(_RETRY_BACKOFF_SEC)
    return ""


def _fingerprint_windows() -> str:
    """Fingerprint Windows: SOLO se tutti e 3 gli identificatori WMI sono presenti.

    Se anche uno solo manca (dopo i retry) → 'unavailable'. MAI hashare un set
    parziale: un segmento vuoto cambia l'hash e rompe il binding licenza.

    NB: con i 3 valori presenti, l'hash e' identico alla forma storica
    `sha256("cpu|board|bios")` → le licenze gia' firmate restano valide.
    """
    values = [_powershell_query(cls, prop) for cls, prop in _HW_QUERIES]
    missing = [f"{cls}.{prop}" for (cls, prop), v in zip(_HW_QUERIES, values) if not v]

    if missing:
        logger.warning(
            "Fingerprint incompleto: %d/%d identificatori mancanti (%s) → 'unavailable' "
            "(non cachato, ritento al prossimo accesso)",
            len(missing), len(_HW_QUERIES), ", ".join(missing),
        )
        return UNAVAILABLE

    raw = "|".join(values)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ── Ramo macOS (ioreg, singola invocazione) ────────────────────────────────

_IOREG_CMD = ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"]

# Ordine di concatenazione FISSATO: "IOPlatformUUID|IOPlatformSerialNumber".
# Cambiare l'ordine cambierebbe l'hash → invaliderebbe le licenze macOS firmate.
_IOREG_FIELDS: tuple[str, ...] = ("IOPlatformUUID", "IOPlatformSerialNumber")


def _ioreg_read_once() -> dict[str, str]:
    """Singola invocazione ioreg. Ritorna {campo: valore} per i campi trovati.

    Entrambi gli identificatori vengono estratti dallo STESSO output: un solo
    comando di sistema = un solo punto di fallimento sul piano disponibilita'.
    Solleva subprocess.TimeoutExpired sul timeout (gestito dal chiamante).
    """
    result = subprocess.run(
        list(_IOREG_CMD),
        capture_output=True,
        text=True,
        timeout=_QUERY_TIMEOUT_SEC,
    )
    if result.returncode != 0:
        return {}
    found: dict[str, str] = {}
    for field in _IOREG_FIELDS:
        match = re.search(rf'"{field}"\s*=\s*"([^"]*)"', result.stdout)
        if match and match.group(1).strip():
            found[field] = match.group(1).strip()
    return found


def _fingerprint_macos() -> str:
    """Fingerprint macOS: SOLO se ENTRAMBI i campi ioreg sono presenti (tutto-o-niente).

    Stessa disciplina del ramo Windows (INC-2026-06-18):
    - Set incompleto "veloce" → ritenta (fino a _QUERY_ATTEMPTS), poi 'unavailable'.
    - Timeout → NON ritenta (ha gia' atteso _QUERY_TIMEOUT_SEC): 'unavailable' subito.
    - MAI hashare un set parziale.

    Hash = sha256("IOPlatformUUID|IOPlatformSerialNumber") — ordine fissato.
    """
    for attempt in range(1, _QUERY_ATTEMPTS + 1):
        try:
            found = _ioreg_read_once()
            if all(field in found for field in _IOREG_FIELDS):
                raw = "|".join(found[field] for field in _IOREG_FIELDS)
                return hashlib.sha256(raw.encode("utf-8")).hexdigest()
            missing = [field for field in _IOREG_FIELDS if field not in found]
            logger.warning(
                "ioreg incompleto: %s mancanti (tentativo %d/%d)",
                ", ".join(missing), attempt, _QUERY_ATTEMPTS,
            )
        except subprocess.TimeoutExpired:
            logger.warning("ioreg timeout dopo %ds — niente retry", _QUERY_TIMEOUT_SEC)
            return UNAVAILABLE
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "ioreg errore (tentativo %d/%d): %s", attempt, _QUERY_ATTEMPTS, exc
            )
        if attempt < _QUERY_ATTEMPTS:
            time.sleep(_RETRY_BACKOFF_SEC)
    logger.warning(
        "Fingerprint macOS incompleto dopo %d tentativi → 'unavailable' "
        "(non cachato, ritento al prossimo accesso)",
        _QUERY_ATTEMPTS,
    )
    return UNAVAILABLE


# ── Dispatch e contratto pubblico ──────────────────────────────────────────


def _compute_fingerprint() -> str:
    """Dispatch per piattaforma: Windows → WMI, Darwin → ioreg, altro → 'unavailable'."""
    system = platform.system()
    if system == "Windows":
        return _fingerprint_windows()
    if system == "Darwin":
        return _fingerprint_macos()
    logger.warning("Piattaforma non supportata per il fingerprint: %s → 'unavailable'", system)
    return UNAVAILABLE


def get_machine_fingerprint() -> str:
    """Ritorna SHA-256 hex completo (64 char), deterministico tra riavvii.

    Cacha SOLO un fingerprint completo: un esito 'unavailable' (lettura fiacca) NON
    viene congelato, cosi' un singhiozzo transitorio si auto-guarisce alla
    richiesta successiva invece di bloccare l'intera sessione (INC-2026-06-18).
    """
    global _cached_fingerprint
    if _cached_fingerprint is not None:
        return _cached_fingerprint
    fp = _compute_fingerprint()
    if fp != UNAVAILABLE:
        _cached_fingerprint = fp
    return fp


def get_machine_fingerprint_short() -> str:
    """Ritorna i primi 16 caratteri del fingerprint per visualizzazione UI."""
    fp = get_machine_fingerprint()
    if fp == UNAVAILABLE:
        return fp
    return fp[:16].upper()


def get_machine_fingerprint_display() -> str:
    """Formato leggibile con spazi ogni 4 caratteri (es. 'A3F8 B9C2 D1E4 F5A7')."""
    short = get_machine_fingerprint_short()
    if short == UNAVAILABLE:
        return short
    return " ".join(short[i : i + 4] for i in range(0, len(short), 4))

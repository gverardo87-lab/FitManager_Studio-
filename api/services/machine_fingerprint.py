"""
Machine Fingerprint — identifica univocamente il PC per binding licenza.

Combina 3 identificatori hardware stabili via PowerShell Get-CimInstance (Windows):
- CPU ProcessorId
- Motherboard SerialNumber
- BIOS SerialNumber

Il fingerprint e' un hash SHA-256 dei 3 valori concatenati.
Sopravvive a: aggiornamenti Windows, driver, reinstall app, cambio disco/RAM.
"""

from __future__ import annotations

import hashlib
import logging
import platform
import subprocess

logger = logging.getLogger(__name__)

_cached_fingerprint: str | None = None

# Mapping: (CIM class, property) per i 3 identificatori hardware
_HW_QUERIES: list[tuple[str, str]] = [
    ("Win32_Processor", "ProcessorId"),
    ("Win32_BaseBoard", "SerialNumber"),
    ("Win32_BIOS", "SerialNumber"),
]


def _powershell_query(cim_class: str, prop: str) -> str:
    """Esegue query WMI via PowerShell Get-CimInstance. Ritorna stringa vuota se fallisce."""
    try:
        cmd = f"(Get-CimInstance -ClassName {cim_class}).{prop}"
        creationflags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=creationflags,
        )
        value = result.stdout.strip()
        if value and result.returncode == 0:
            return value
    except Exception as exc:
        logger.warning("PowerShell query fallita (%s.%s): %s", cim_class, prop, exc)
    return ""


def _compute_fingerprint() -> str:
    """Calcola fingerprint dalla combinazione di 3 identificatori hardware."""
    values = [_powershell_query(cls, prop) for cls, prop in _HW_QUERIES]
    cpu_id, board_serial, bios_serial = values

    non_empty = [v for v in values if v]

    if not non_empty:
        logger.error("Nessun identificatore hardware disponibile — fingerprint non generabile")
        return "unavailable"

    if len(non_empty) < len(values):
        logger.warning(
            "Fingerprint parziale: %d/3 identificatori disponibili",
            len(non_empty),
        )

    raw = f"{cpu_id}|{board_serial}|{bios_serial}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_machine_fingerprint() -> str:
    """Ritorna SHA-256 hex completo (64 char). Deterministico tra riavvii."""
    global _cached_fingerprint
    if _cached_fingerprint is None:
        _cached_fingerprint = _compute_fingerprint()
    return _cached_fingerprint


def get_machine_fingerprint_short() -> str:
    """Ritorna i primi 16 caratteri del fingerprint per visualizzazione UI."""
    fp = get_machine_fingerprint()
    if fp == "unavailable":
        return fp
    return fp[:16].upper()


def get_machine_fingerprint_display() -> str:
    """Formato leggibile con spazi ogni 4 caratteri (es. 'A3F8 B9C2 D1E4 F5A7')."""
    short = get_machine_fingerprint_short()
    if short == "unavailable":
        return short
    return " ".join(short[i : i + 4] for i in range(0, len(short), 4))

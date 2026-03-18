"""Test per machine fingerprint — hardware binding licenza."""

import hashlib
from unittest.mock import patch

from api.services.machine_fingerprint import (
    _compute_fingerprint,
    get_machine_fingerprint,
    get_machine_fingerprint_display,
    get_machine_fingerprint_short,
)


def _mock_powershell(cim_class: str, prop: str) -> str:
    """PowerShell mock deterministico per test."""
    data = {
        ("Win32_Processor", "ProcessorId"): "BFEBFBFF000906A3",
        ("Win32_BaseBoard", "SerialNumber"): "PF3R2CG0",
        ("Win32_BIOS", "SerialNumber"): "5CD2345ABC",
    }
    return data.get((cim_class, prop), "")


def test_compute_fingerprint_deterministic():
    """Lo stesso hardware produce lo stesso fingerprint."""
    with patch("api.services.machine_fingerprint._powershell_query", side_effect=_mock_powershell):
        fp1 = _compute_fingerprint()
        fp2 = _compute_fingerprint()
    assert fp1 == fp2
    assert len(fp1) == 64  # SHA-256 hex


def test_compute_fingerprint_correct_hash():
    """Il fingerprint e' SHA-256 dei 3 valori concatenati con pipe."""
    with patch("api.services.machine_fingerprint._powershell_query", side_effect=_mock_powershell):
        fp = _compute_fingerprint()
    expected = hashlib.sha256(
        "BFEBFBFF000906A3|PF3R2CG0|5CD2345ABC".encode("utf-8")
    ).hexdigest()
    assert fp == expected


def test_fingerprint_short_is_first_16_chars():
    with patch("api.services.machine_fingerprint._powershell_query", side_effect=_mock_powershell):
        with patch("api.services.machine_fingerprint._cached_fingerprint", None):
            full = get_machine_fingerprint()
            short = get_machine_fingerprint_short()
    assert short == full[:16].upper()


def test_fingerprint_display_has_spaces():
    with patch("api.services.machine_fingerprint._powershell_query", side_effect=_mock_powershell):
        with patch("api.services.machine_fingerprint._cached_fingerprint", None):
            display = get_machine_fingerprint_display()
    # Formato: "XXXX XXXX XXXX XXXX"
    parts = display.split(" ")
    assert len(parts) == 4
    assert all(len(p) == 4 for p in parts)


def test_graceful_degradation_all_fail():
    """Se tutti i query WMI falliscono, ritorna 'unavailable'."""

    def _all_fail(entity: str, field: str) -> str:
        return ""

    with patch("api.services.machine_fingerprint._powershell_query", side_effect=_all_fail):
        fp = _compute_fingerprint()
    assert fp == "unavailable"


def test_partial_failure_still_produces_fingerprint():
    """Con 2/3 query funzionanti, il fingerprint viene comunque generato."""

    def _partial(cim_class: str, prop: str) -> str:
        if cim_class == "Win32_BIOS":
            return ""  # BIOS fallisce
        return _mock_powershell(cim_class, prop)

    with patch("api.services.machine_fingerprint._powershell_query", side_effect=_partial):
        fp = _compute_fingerprint()
    assert fp != "unavailable"
    assert len(fp) == 64

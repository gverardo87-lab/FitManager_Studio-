"""Test per machine fingerprint — hardware binding licenza.

Include la regressione INC-2026-06-18: una query WMI vuota a intermittenza
("Fingerprint parziale: 2/3" nel log reale di Chiara) NON deve produrre un hash
parziale (sarebbe != machine_id firmato → falso 'wrong_machine' → blocco CRM).
"""

import hashlib
import subprocess
import types
from unittest.mock import patch

import pytest

from api.services import machine_fingerprint as mf
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


def _make_run(script: dict[str, list[str]]):
    """Fake di subprocess.run: classe CIM -> sequenza di output per chiamata.
    Valore 'TIMEOUT' solleva TimeoutExpired (per testare il no-retry sul timeout)."""
    calls: dict[str, int] = {}

    def run(cmd, **kwargs):  # noqa: ANN001
        command = cmd[-1]
        cls = next(
            (c for c in ("Win32_Processor", "Win32_BaseBoard", "Win32_BIOS") if c in command),
            "?",
        )
        seq = script.get(cls, ["X"])
        i = calls.get(cls, 0)
        calls[cls] = i + 1
        item = seq[min(i, len(seq) - 1)]
        if item == "TIMEOUT":
            raise subprocess.TimeoutExpired(cmd, mf._QUERY_TIMEOUT_SEC)
        return types.SimpleNamespace(stdout=item + "\n", returncode=0 if item else 1)

    return run


_FULL = {
    "Win32_Processor": ["CPU123"],
    "Win32_BaseBoard": ["BOARD456"],
    "Win32_BIOS": ["BIOS789"],
}
_EXPECTED_FULL = hashlib.sha256(b"CPU123|BOARD456|BIOS789").hexdigest()


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    """Resetta la cache di modulo tra i test e azzera i backoff (test veloci)."""
    mf._cached_fingerprint = None
    monkeypatch.setattr(mf.time, "sleep", lambda *_a, **_k: None)
    yield
    mf._cached_fingerprint = None


# ── Comportamento base (preesistente) ──────────────────────────────────────

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
    expected = hashlib.sha256("BFEBFBFF000906A3|PF3R2CG0|5CD2345ABC".encode("utf-8")).hexdigest()
    assert fp == expected


def test_fingerprint_short_is_first_16_chars():
    with patch("api.services.machine_fingerprint._powershell_query", side_effect=_mock_powershell):
        full = get_machine_fingerprint()
        short = get_machine_fingerprint_short()
    assert short == full[:16].upper()


def test_fingerprint_display_has_spaces():
    with patch("api.services.machine_fingerprint._powershell_query", side_effect=_mock_powershell):
        display = get_machine_fingerprint_display()
    parts = display.split(" ")
    assert len(parts) == 4
    assert all(len(p) == 4 for p in parts)


def test_graceful_degradation_all_fail():
    """Se tutti i query WMI falliscono, ritorna 'unavailable'."""
    with patch("api.services.machine_fingerprint._powershell_query", side_effect=lambda *_: ""):
        fp = _compute_fingerprint()
    assert fp == "unavailable"


# ── Regressione INC-2026-06-18 ─────────────────────────────────────────────

def test_partial_failure_returns_unavailable_not_a_hash():
    """IL FIX (capovolge il vecchio test bacato): 2/3 → 'unavailable', MAI un hash.

    Un hash su set parziale sarebbe != machine_id firmato → falso wrong_machine.
    """
    def _partial(cim_class: str, prop: str) -> str:
        if cim_class == "Win32_BIOS":
            return ""  # BIOS vuoto (singhiozzo WMI)
        return _mock_powershell(cim_class, prop)

    with patch("api.services.machine_fingerprint._powershell_query", side_effect=_partial):
        fp = _compute_fingerprint()
    assert fp == "unavailable"
    assert len(fp) != 64  # mai un fingerprint valido-in-apparenza


def test_full_set_hash_is_backcompat(monkeypatch):
    """3/3 → hash nella forma storica sha256('cpu|board|bios') (licenze esistenti restano valide)."""
    monkeypatch.setattr(mf.subprocess, "run", _make_run(_FULL))
    assert mf.get_machine_fingerprint() == _EXPECTED_FULL


def test_unavailable_is_not_cached_and_self_heals(monkeypatch):
    """Un fallimento transitorio non viene congelato → la chiamata dopo ritenta."""
    bad = {"Win32_Processor": ["CPU123"], "Win32_BaseBoard": ["BOARD456"], "Win32_BIOS": [""]}
    monkeypatch.setattr(mf.subprocess, "run", _make_run(bad))
    assert mf.get_machine_fingerprint() == mf.UNAVAILABLE
    assert mf._cached_fingerprint is None  # NON congelato

    monkeypatch.setattr(mf.subprocess, "run", _make_run(_FULL))  # WMI guarita
    assert mf.get_machine_fingerprint() == _EXPECTED_FULL
    assert mf._cached_fingerprint == _EXPECTED_FULL


def test_transient_empty_then_retry_recovers(monkeypatch):
    """Vuoto al 1° tentativo, valore al 2° → il retry recupera (3/3)."""
    script = {
        "Win32_Processor": ["CPU123"],
        "Win32_BaseBoard": ["", "BOARD456"],  # 1° vuoto, 2° ok
        "Win32_BIOS": ["BIOS789"],
    }
    monkeypatch.setattr(mf.subprocess, "run", _make_run(script))
    assert mf.get_machine_fingerprint() == _EXPECTED_FULL


def test_timeout_not_retried_yields_unavailable(monkeypatch):
    """Un timeout non si ritenta (latenza) → identificatore mancante → unavailable."""
    script = {"Win32_Processor": ["CPU123"], "Win32_BaseBoard": ["BOARD456"], "Win32_BIOS": ["TIMEOUT"]}
    monkeypatch.setattr(mf.subprocess, "run", _make_run(script))
    assert mf.get_machine_fingerprint() == mf.UNAVAILABLE


def test_complete_fingerprint_is_cached(monkeypatch):
    """Un fingerprint completo viene cachato e non ricalcolato."""
    monkeypatch.setattr(mf.subprocess, "run", _make_run(_FULL))
    first = mf.get_machine_fingerprint()
    monkeypatch.setattr(
        mf.subprocess,
        "run",
        _make_run({"Win32_Processor": ["DIFF"], "Win32_BaseBoard": ["DIFF"], "Win32_BIOS": ["DIFF"]}),
    )
    assert mf.get_machine_fingerprint() == first  # serve la cache, non ricalcola

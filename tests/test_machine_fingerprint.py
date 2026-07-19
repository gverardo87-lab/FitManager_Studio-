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
    """Resetta la cache di modulo tra i test e azzera i backoff (test veloci).

    Forza il dispatch sul ramo Windows: i test WMI restano validi su qualsiasi
    host (CI macOS/Linux inclusi). I test del ramo macOS ri-forzano 'Darwin'.
    """
    mf._cached_fingerprint = None
    monkeypatch.setattr(mf.time, "sleep", lambda *_a, **_k: None)
    monkeypatch.setattr(mf.platform, "system", lambda: "Windows")
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


# ── Ramo macOS (G-MAC.0: SPEC_FINGERPRINT_CROSSPLATFORM T2) ────────────────

_IOREG_OK = """+-o MacBookAir10,1  <class IOPlatformExpertDevice, id 0x100000110, registered>
  {
      "IOPlatformUUID" = "AAAABBBB-CCCC-DDDD-EEEE-FFFF00001111"
      "IOPlatformSerialNumber" = "FVFLG2TEST01"
      "board-id" = <"Mac-747B1AEFF11738BE">
  }
"""
_IOREG_NO_SERIAL = _IOREG_OK.replace('"IOPlatformSerialNumber" = "FVFLG2TEST01"\n', "")
_EXPECTED_MAC = hashlib.sha256(
    b"AAAABBBB-CCCC-DDDD-EEEE-FFFF00001111|FVFLG2TEST01"
).hexdigest()


def _make_ioreg_run(outputs: list[str]):
    """Fake subprocess.run per ioreg: sequenza di output per chiamata.
    'TIMEOUT' solleva TimeoutExpired. Espone .calls per contare le invocazioni."""
    def run(cmd, **kwargs):  # noqa: ANN001
        assert cmd == ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"]
        i = run.calls
        run.calls += 1
        item = outputs[min(i, len(outputs) - 1)]
        if item == "TIMEOUT":
            raise subprocess.TimeoutExpired(cmd, mf._QUERY_TIMEOUT_SEC)
        return types.SimpleNamespace(stdout=item, returncode=0)

    run.calls = 0
    return run


def test_macos_full_set_hash_and_order(monkeypatch):
    """Entrambi i campi presenti → sha256('IOPlatformUUID|IOPlatformSerialNumber')."""
    monkeypatch.setattr(mf.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(mf.subprocess, "run", _make_ioreg_run([_IOREG_OK]))
    assert mf.get_machine_fingerprint() == _EXPECTED_MAC
    assert mf._cached_fingerprint == _EXPECTED_MAC


def test_macos_single_invocation(monkeypatch):
    """Clausola §4.1: i due identificatori vengono da UNA sola chiamata ioreg."""
    monkeypatch.setattr(mf.platform, "system", lambda: "Darwin")
    fake = _make_ioreg_run([_IOREG_OK])
    monkeypatch.setattr(mf.subprocess, "run", fake)
    mf.get_machine_fingerprint()
    assert fake.calls == 1


def test_macos_partial_returns_unavailable_not_a_hash(monkeypatch):
    """Tutto-o-niente (INC-2026-06-18): serial mancante → 'unavailable', MAI hash parziale."""
    monkeypatch.setattr(mf.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(mf.subprocess, "run", _make_ioreg_run([_IOREG_NO_SERIAL]))
    fp = mf.get_machine_fingerprint()
    assert fp == mf.UNAVAILABLE
    assert mf._cached_fingerprint is None  # NON congelato: la chiamata dopo ritenta


def test_macos_transient_then_retry_recovers(monkeypatch):
    """Set incompleto al 1° tentativo, completo al 2° → il retry recupera."""
    monkeypatch.setattr(mf.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(mf.subprocess, "run", _make_ioreg_run([_IOREG_NO_SERIAL, _IOREG_OK]))
    assert mf.get_machine_fingerprint() == _EXPECTED_MAC


def test_macos_timeout_not_retried(monkeypatch):
    """Timeout → 'unavailable' subito, senza retry (ha gia' atteso il timeout pieno)."""
    monkeypatch.setattr(mf.platform, "system", lambda: "Darwin")
    fake = _make_ioreg_run(["TIMEOUT"])
    monkeypatch.setattr(mf.subprocess, "run", fake)
    assert mf.get_machine_fingerprint() == mf.UNAVAILABLE
    assert fake.calls == 1  # nessun secondo tentativo dopo il timeout


def test_macos_self_heals_after_unavailable(monkeypatch):
    """'unavailable' non congelato: alla chiamata dopo, ioreg guarito → hash completo."""
    monkeypatch.setattr(mf.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(mf.subprocess, "run", _make_ioreg_run([_IOREG_NO_SERIAL]))
    assert mf.get_machine_fingerprint() == mf.UNAVAILABLE
    monkeypatch.setattr(mf.subprocess, "run", _make_ioreg_run([_IOREG_OK]))
    assert mf.get_machine_fingerprint() == _EXPECTED_MAC


# ── Dispatch per piattaforma (G-MAC.0 AC1) ─────────────────────────────────

def test_dispatch_unsupported_platform_is_unavailable(monkeypatch):
    """Piattaforma né Windows né Darwin → safe-default 'unavailable', zero subprocess."""
    monkeypatch.setattr(mf.platform, "system", lambda: "Linux")

    def _boom(*_a, **_k):  # nessuna lettura hardware deve partire
        raise AssertionError("subprocess.run non deve essere invocato su piattaforma non supportata")

    monkeypatch.setattr(mf.subprocess, "run", _boom)
    assert mf.get_machine_fingerprint() == mf.UNAVAILABLE

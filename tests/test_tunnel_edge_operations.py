"""Test degli artefatti operativi edge R0.1.5, senza accesso al VPS."""

from __future__ import annotations

import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
APPLY_SCRIPT = ROOT / "tools" / "operations" / "apply-frps-http01.sh"
PROBE_SCRIPT = ROOT / "tools" / "operations" / "probe-r015-tls.ps1"


def _bash() -> str:
    executable = shutil.which("bash")
    if executable is not None:
        return executable
    git_bash = Path("C:/Program Files/Git/bin/bash.exe")
    if git_bash.is_file():
        return str(git_bash)
    pytest.skip("bash non disponibile sul contributor host")


def _render(source: Path, destination: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            _bash(),
            str(APPLY_SCRIPT),
            "--render-only",
            "--config",
            source.as_posix(),
            "--output",
            destination.as_posix(),
        ],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )


def test_render_inserts_top_level_http_port_without_touching_secrets(tmp_path):
    source = tmp_path / "frps.toml"
    candidate = tmp_path / "candidate.toml"
    source.write_text(
        'bindPort = 7000\nvhostHTTPSPort = 443\n\n[webServer]\npassword = "keep-me"\n',
        encoding="utf-8",
    )

    result = _render(source, candidate)

    assert result.returncode == 0, result.stdout + result.stderr
    parsed = tomllib.loads(candidate.read_text(encoding="utf-8"))
    assert parsed["vhostHTTPPort"] == 80
    assert parsed["vhostHTTPSPort"] == 443
    assert parsed["webServer"]["password"] == "keep-me"
    assert candidate.read_text(encoding="utf-8").index("vhostHTTPPort") < (
        candidate.read_text(encoding="utf-8").index("[webServer]")
    )


def test_render_is_byte_idempotent(tmp_path):
    source = tmp_path / "frps.toml"
    first = tmp_path / "first.toml"
    second = tmp_path / "second.toml"
    source.write_text('bindPort = 7000\n[log]\nlevel = "info"\n', encoding="utf-8")

    assert _render(source, first).returncode == 0
    assert _render(first, second).returncode == 0

    assert first.read_bytes() == second.read_bytes()
    assert first.read_text(encoding="utf-8").count("vhostHTTPPort") == 1


def test_render_refuses_existing_noncanonical_http_port(tmp_path):
    source = tmp_path / "frps.toml"
    candidate = tmp_path / "candidate.toml"
    source.write_text("bindPort = 7000\nvhostHTTPPort = 8080\n", encoding="utf-8")

    result = _render(source, candidate)

    assert result.returncode != 0
    assert "diverso da 80" in result.stderr


def test_apply_path_has_backup_verify_rollback_and_no_firewall_auto_enable():
    script = APPLY_SCRIPT.read_text(encoding="utf-8")

    assert '"$FRPS_BIN" verify -c "$CANDIDATE_PATH"' in script
    assert script.index('cp -p -- "$CONFIG_PATH" "$BACKUP_PATH"') < script.index(
        'mv -f -- "$CANDIDATE_PATH" "$CONFIG_PATH"'
    )
    assert "trap on_exit EXIT" in script
    assert "ROLLBACK INCOMPLETO" in script
    assert "if cp -p -- \"$BACKUP_PATH\" \"$restore_path\" && mv -f" in script
    assert 'if [ "$restored" -eq 1 ]' in script
    assert "ufw --force enable" not in script
    assert "install -d -m 700" in script
    assert 'FRPS_BIN="$FRP_ROOT_REAL/frps"' in script
    assert "/opt/frp" not in script


def test_apply_waits_bounded_for_http_listener_after_restart():
    """Type=simple può risultare active prima che il socket vhost sia osservabile."""
    script = APPLY_SCRIPT.read_text(encoding="utf-8")

    assert "wait_for_listener()" in script
    assert "wait_for_listener 80 10" in script
    assert "sleep 1" in script
    assert "for ((attempt = 1; attempt <= max_attempts; attempt++))" in script


def test_strict_probe_never_disables_tls_or_prints_public_url():
    script = PROBE_SCRIPT.read_text(encoding="utf-8")

    assert "AuthenticateAsClient" in script
    assert "$handler.AllowAutoRedirect = $false" in script
    assert "SkipCertificateCheck" not in script
    assert "ServerCertificateCustomValidationCallback" not in script
    assert "HTTPS_PRIVATE=404" in script
    assert "HTTPS_PUBLIC_200=PASS" in script
    assert "Write-Output $publicUrl" not in script


def test_strict_probe_loads_http_assembly_before_first_http_type_use():
    """Il closeout deve funzionare in Windows PowerShell senza preload manuale."""
    script = PROBE_SCRIPT.read_text(encoding="utf-8")

    load = "Add-Type -AssemblyName System.Net.Http"
    first_http_type = "$handler = [System.Net.Http.HttpClientHandler]::new()"
    assert load in script
    assert script.index(load) < script.index(first_http_type)

"""Gate packaging R0.1.5 per il client ACME pinato."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

import pytest

from api.services.cert_manager import (
    ACME_CLIENT_SHA256_WINDOWS_AMD64,
    ACME_CLIENT_VERSION,
)

ROOT = Path(__file__).resolve().parents[1]
STAGE_SCRIPT = ROOT / "tools" / "build" / "stage-acme-client.sh"
FETCH_SCRIPT = ROOT / "tools" / "build" / "fetch-lego.ps1"
BUILD_SCRIPT = ROOT / "tools" / "build" / "build-installer.sh"
LICENSE_PATH = ROOT / "tools" / "licenses" / "lego-MIT.txt"
LEGO_PATH = ROOT / "tools" / "bin" / "lego.exe"
LICENSE_SHA256 = "bf12923e71046c564f4163c00c3aa6b3581b51858f099a035f5baf2216addf6e"
ARCHIVE_SHA256 = "3e87c133bcb0a6fd4236d11e0583967ecd2f04f454d2ff48286f1ab1183d699e"


def _bash() -> str:
    executable = shutil.which("bash")
    if executable is not None:
        return executable
    git_bash = Path("C:/Program Files/Git/bin/bash.exe")
    if git_bash.is_file():
        return str(git_bash)
    pytest.skip("bash non disponibile sul contributor host")


def _run_stage(source: Path, destination: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            _bash(),
            str(STAGE_SCRIPT),
            "--source",
            source.as_posix(),
            "--destination-dir",
            destination.as_posix(),
            "--license-source",
            LICENSE_PATH.as_posix(),
        ],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )


def test_build_invokes_fail_closed_acme_staging_after_backend_build():
    build_script = BUILD_SCRIPT.read_text(encoding="utf-8")

    backend_build = 'bash "$ROOT/tools/build/build-backend.sh"'
    acme_staging = 'bash "$ROOT/tools/build/stage-acme-client.sh"'
    assert acme_staging in build_script
    assert build_script.index(backend_build) < build_script.index(acme_staging)
    assert 'Source: "..\\dist\\fitmanager\\*"' in (
        ROOT / "installer" / "fitmanager.iss"
    ).read_text(encoding="utf-8")


def test_supply_chain_pins_are_synchronized_across_runtime_and_build_scripts():
    stage_script = STAGE_SCRIPT.read_text(encoding="utf-8")
    fetch_script = FETCH_SCRIPT.read_text(encoding="utf-8")

    for content in (stage_script, fetch_script):
        assert ACME_CLIENT_VERSION in content
        assert ACME_CLIENT_SHA256_WINDOWS_AMD64 in content
        assert LICENSE_SHA256 in content
    assert ARCHIVE_SHA256 in fetch_script
    assert "/releases/download/v${legoVersion}/" in fetch_script
    assert "/latest/" not in fetch_script
    assert "Invoke-WebRequest" not in stage_script
    assert hashlib.sha256(LICENSE_PATH.read_bytes()).hexdigest() == LICENSE_SHA256


def test_staging_rejects_missing_client_without_creating_bundle(tmp_path):
    destination = tmp_path / "bundle"

    result = _run_stage(tmp_path / "missing-lego.exe", destination)

    assert result.returncode != 0
    assert "lego.exe non trovato" in result.stderr
    assert not (destination / "lego.exe").exists()


def test_staging_rejects_hash_mismatch_before_copy(tmp_path):
    source = tmp_path / "lego.exe"
    source.write_bytes(b"tampered-acme-client")
    destination = tmp_path / "bundle"

    result = _run_stage(source, destination)

    assert result.returncode != 0
    assert "hash mismatch" in result.stderr
    assert not (destination / "lego.exe").exists()


def test_staging_accepts_only_the_pinned_real_client(tmp_path):
    if not LEGO_PATH.is_file():
        pytest.skip("lego.exe pinato non presente sul contributor host")
    destination = tmp_path / "bundle"

    result = _run_stage(LEGO_PATH, destination)

    assert result.returncode == 0, result.stdout + result.stderr
    staged_client = destination / "lego.exe"
    staged_license = destination / "THIRD_PARTY_LICENSES" / "lego-MIT.txt"
    assert hashlib.sha256(staged_client.read_bytes()).hexdigest() == (
        ACME_CLIENT_SHA256_WINDOWS_AMD64
    )
    assert hashlib.sha256(staged_license.read_bytes()).hexdigest() == LICENSE_SHA256

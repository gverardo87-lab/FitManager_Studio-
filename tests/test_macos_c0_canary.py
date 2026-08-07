"""Unit guards for the C0.1 macOS portability canary tooling."""

import subprocess
import sys
from pathlib import Path

from tools.canary.check_macos_runtime_contract import evaluate_runtime_contract
from tools.canary.wheelhouse_manifest import _tag_is_arm64_safe


def test_runtime_contract_exposes_current_darwin_filename_coupling():
    report = evaluate_runtime_contract(
        target_system="Darwin",
        frpc_filename="frpc.exe",
        acme_client_filename="lego.exe",
    )

    assert report["result"] == "RED"
    assert [finding["code"] for finding in report["findings"]] == [
        "G-MAC.1-FRPC-FILENAME",
        "G-MAC.1-ACME-FILENAME",
    ]


def test_runtime_contract_accepts_native_darwin_filenames():
    report = evaluate_runtime_contract(
        target_system="Darwin",
        frpc_filename="frpc",
        acme_client_filename="lego",
    )

    assert report["result"] == "PASS"
    assert report["findings"] == []


def test_wheel_policy_accepts_pure_and_arm64_tags_only():
    assert _tag_is_arm64_safe("py3-none-any")
    assert _tag_is_arm64_safe("cp312-cp312-macosx_11_0_arm64")
    assert not _tag_is_arm64_safe("cp312-cp312-macosx_10_13_x86_64")
    assert not _tag_is_arm64_safe("cp312-cp312-macosx_10_13_universal2")


def test_runtime_is_deny_by_default_and_allows_only_loopback_cors():
    script = """
from fastapi.testclient import TestClient
from tools.canary.macos_c0_runtime import app

with TestClient(app) as client:
    assert client.get('/health').status_code == 200
    assert client.get('/api/clients').status_code == 403
    cors = client.options(
        '/api/auth/setup-status',
        headers={
            'Origin': 'http://127.0.0.1:3000',
            'Access-Control-Request-Method': 'GET',
        },
    )
    assert cors.status_code == 200
    assert cors.headers['access-control-allow-origin'] == 'http://127.0.0.1:3000'
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr

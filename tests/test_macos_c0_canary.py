"""Unit guards for the C0.1 macOS portability canary tooling."""

import subprocess
import sys
from pathlib import Path

from tools.canary.check_macos_runtime_contract import evaluate_runtime_contract
from tools.canary.wheelhouse_manifest import _tag_is_arm64_safe


ROOT = Path(__file__).resolve().parents[1]


def test_nuitka_build_backend_is_hash_pinned_before_sdist_install():
    bootstrap_path = ROOT / "tools" / "canary" / "requirements-macos-c0-build-bootstrap.txt"
    workflow_path = ROOT / ".github" / "workflows" / "macos-portability-canary.yml"

    bootstrap = bootstrap_path.read_text(encoding="utf-8")
    workflow = workflow_path.read_text(encoding="utf-8")

    assert "setuptools==84.0.0" in bootstrap
    assert "sha256:51a52592b3b99e102b609654876bd65f19f999935166d1352678931132b0c670" in bootstrap
    bootstrap_install = "-r tools/canary/requirements-macos-c0-build-bootstrap.txt"
    nuitka_install = "-r tools/canary/requirements-macos-c0-build.txt"
    bootstrap_index = workflow.index(bootstrap_install)
    nuitka_index = workflow.index(nuitka_install)
    bootstrap_block = workflow[bootstrap_index - 180 : nuitka_index]

    assert bootstrap_index < nuitka_index
    assert "--no-deps" in bootstrap_block
    assert "--only-binary=:all:" in bootstrap_block
    assert "--require-hashes" in bootstrap_block
    assert "import setuptools.build_meta" in bootstrap_block


def test_macos_smoke_timeboxes_chrome_and_disables_background_updates():
    workflow_path = ROOT / ".github" / "workflows" / "macos-portability-canary.yml"
    workflow = workflow_path.read_text(encoding="utf-8")
    smoke = workflow[workflow.index("Run compiled self-test, auth, stability, memory and display smoke") :]

    assert "timeout-minutes: 10" in smoke[:500]
    assert "run_headless_chrome()" in smoke
    assert "const [expectedOutput, command, ...args]" in smoke
    assert "fs.statSync(expectedOutput).size > 0" in smoke
    assert "if (outputIsReady())" in smoke
    assert "process.kill(-child.pid" in smoke
    assert '"SIGKILL"' in smoke
    assert "if (timedOut) return;" in smoke
    assert 'process.exit(124)' in smoke
    assert "--disable-background-networking" in smoke
    assert "--disable-component-update" in smoke
    assert "--no-first-run" in smoke
    assert 'run_headless_chrome "$output" "$chrome"' in smoke
    assert 'run_headless_chrome "$setup_dom" "$chrome"' in smoke
    assert 'run_headless_chrome "$login_dom" "$chrome"' in smoke
    assert "grep -Eqi '</html>'" in smoke


def test_runtime_contract_cli_is_invoked_as_repo_root_module():
    workflow_path = ROOT / ".github" / "workflows" / "macos-portability-canary.yml"
    workflow = workflow_path.read_text(encoding="utf-8")
    contract_step = workflow[
        workflow.index("Record the current G-MAC.1 runtime coupling") : workflow.index(
            "Compile the source-free technical/auth runtime"
        )
    ]

    assert "python -m tools.canary.check_macos_runtime_contract" in contract_step
    assert "python tools/canary/check_macos_runtime_contract.py" not in contract_step


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


def test_wheel_policy_accepts_arm64_compatible_inputs_and_rejects_x86_only():
    assert _tag_is_arm64_safe("py3-none-any")
    assert _tag_is_arm64_safe("cp312-cp312-macosx_11_0_arm64")
    assert _tag_is_arm64_safe("cp39-abi3-macosx_10_12_universal2")
    assert not _tag_is_arm64_safe("cp312-cp312-macosx_10_13_x86_64")


def test_green_canary_requires_both_build_contracts_before_transfer():
    workflow_path = ROOT / ".github" / "workflows" / "macos-portability-canary.yml"
    workflow = workflow_path.read_text(encoding="utf-8")

    assert '"api/services/tunnel_manager.py"' in workflow
    assert "Require build contracts before transfer" in workflow
    assert 'test "${{ steps.runtime-contract.outcome }}" = "success"' in workflow
    assert 'test "${{ steps.wheelhouse-contract.outcome }}" = "success"' in workflow


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

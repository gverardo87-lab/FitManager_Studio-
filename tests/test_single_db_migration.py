"""Canary R0.2: le procedure vive usano un solo database business."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tools.admin_scripts import e2e_distribution_rehearsal as rehearsal

ROOT = Path(__file__).resolve().parents[1]
MIGRATE_SCRIPT = ROOT / "tools" / "scripts" / "migrate-all.sh"
ALEMBIC_CONFIG = ROOT / "alembic.ini"


def _bash() -> str:
    executable = shutil.which("bash")
    if executable is not None:
        return executable
    git_bash = Path("C:/Program Files/Git/bin/bash.exe")
    if git_bash.is_file():
        return str(git_bash)
    pytest.skip("bash non disponibile sul contributor host")


def _alembic_stub(tmp_path: Path) -> Path:
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    stub = stub_dir / "alembic"
    stub.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf '%s\\t%s\\n' "${DATABASE_URL:-}" "$*" >> "$ALEMBIC_CALL_LOG"
if [ "${DATABASE_URL:-}" != "$EXPECTED_DATABASE_URL" ]; then
    exit 93
fi
if [ "$*" = "upgrade head" ]; then
    mkdir -p "$(dirname "$EXPECTED_TARGET")"
    : > "$EXPECTED_TARGET"
fi
""",
        encoding="utf-8",
        newline="\n",
    )
    stub.chmod(0o755)
    return stub_dir


def _run_migrate(
    tmp_path: Path, database_url: str
) -> tuple[subprocess.CompletedProcess[str], Path, Path]:
    target = Path(database_url.removeprefix("sqlite:///"))
    call_log = tmp_path / "alembic-calls.tsv"
    stub_dir = _alembic_stub(tmp_path)
    env = os.environ.copy()
    env.update(
        {
            "DATABASE_URL": database_url,
            "ALEMBIC_CALL_LOG": call_log.as_posix(),
            "EXPECTED_DATABASE_URL": database_url,
            "EXPECTED_TARGET": target.as_posix(),
        }
    )
    result = subprocess.run(
        [
            _bash(),
            "-c",
            'stub_dir="$(cygpath -u "$1")"; PATH="$stub_dir:$PATH"; export PATH; bash "$2"',
            "r02-canary",
            stub_dir.as_posix(),
            MIGRATE_SCRIPT.as_posix(),
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        check=False,
        text=True,
    )
    return result, target, call_log


def test_migrate_all_runs_one_upgrade_on_configured_database(tmp_path):
    target_url = f"sqlite:///{(tmp_path / 'configured' / 'crm.db').as_posix()}"

    result, target, call_log = _run_migrate(tmp_path, target_url)

    assert result.returncode == 0, result.stdout + result.stderr
    assert target.is_file()
    assert not (tmp_path / "data" / "crm_dev.db").exists()
    assert call_log.read_text(encoding="utf-8").splitlines() == [
        f"{target_url}\tupgrade head"
    ]


def test_migrate_all_default_and_alembic_config_are_single_db():
    script = MIGRATE_SCRIPT.read_text(encoding="utf-8")
    alembic_config = ALEMBIC_CONFIG.read_text(encoding="utf-8")

    assert 'TARGET_DB="${DATABASE_URL:-sqlite:///data/crm.db}"' in script
    assert script.count("alembic upgrade head") == 1
    assert "sqlalchemy.url = sqlite:///data/crm.db" in alembic_config
    assert "crm_dev.db" not in alembic_config


def test_migrate_all_rejects_legacy_database_before_alembic(tmp_path):
    legacy_url = f"sqlite:///{(tmp_path / 'configured' / 'crm_dev.db').as_posix()}"

    result, target, call_log = _run_migrate(tmp_path, legacy_url)

    assert result.returncode != 0
    assert "crm_dev.db" in result.stderr
    assert not call_log.exists()
    assert not target.exists()


def test_distribution_rehearsal_requires_no_legacy_database(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "crm.db").touch()
    (data_dir / "catalog.db").touch()
    observed: list[tuple[bool, str]] = []

    monkeypatch.setattr(rehearsal, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        rehearsal,
        "_log",
        lambda ok, label, detail="": observed.append((ok, label)),
    )
    monkeypatch.setattr(rehearsal, "_warn", lambda label, detail="": None)

    rehearsal.phase_7_config()

    assert (True, "Business DB (crm.db) exists") in observed
    assert all("crm_dev" not in label for _, label in observed)

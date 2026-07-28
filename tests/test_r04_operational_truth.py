"""Canary R0.4: le fonti operative descrivono il percorso FRP realmente rilasciato."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE_CHECKLIST = ROOT / "docs" / "operations" / "RELEASE_CHECKLIST.md"
SUPPORT_RUNBOOK = ROOT / "docs" / "operations" / "SUPPORT_RUNBOOK.md"
LAUNCH_SCOPE = ROOT / "LAUNCH_SCOPE.md"
API_ADAPTER = ROOT / "api" / "CLAUDE.md"
FRONTEND_ADAPTER = ROOT / "frontend" / "CLAUDE.md"
REHEARSAL = ROOT / "tools" / "admin_scripts" / "e2e_distribution_rehearsal.py"

SCOPED_DOCS = (
    RELEASE_CHECKLIST,
    SUPPORT_RUNBOOK,
    LAUNCH_SCOPE,
    API_ADAPTER,
    FRONTEND_ADAPTER,
)

_MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_release_checklist_requires_managed_frp_strict_evidence():
    checklist = _read(RELEASE_CHECKLIST)

    assert "Tailscale Funnel:" not in checklist
    assert "Test Tailscale VPN" not in checklist
    assert "via Funnel" not in checklist
    assert "`public_access_provider = managed_frp`" in checklist
    assert "`GET /api/system/tunnel-status`" in checklist
    assert "`https://<instance_id>.fitmanagerstudio.com`" in checklist
    assert "`R0.1.5_STRICT_PROBE=PASS`" in checklist
    assert "`/api/clients` → 404" in checklist


def test_support_and_launch_scope_make_frp_the_operational_path():
    support = _read(SUPPORT_RUNBOOK)
    launch = _read(LAUNCH_SCOPE)

    assert "comandi Tailscale/Funnel" not in support
    assert "validazione reale LAN / Tailscale / Funnel" not in launch
    assert "PWA + Tailscale full-app" not in launch
    assert "`GET /api/system/tunnel-status`" in support
    assert "`public_access_provider = managed_frp`" in support
    assert "TLS strict" in launch
    assert "CRM → 404" in launch


def test_adapters_and_rehearsal_do_not_prescribe_legacy_connectivity():
    api_adapter = _read(API_ADAPTER)
    frontend_adapter = _read(FRONTEND_ADAPTER)
    rehearsal = _read(REHEARSAL)

    assert "probe legacy Tailscale/Funnel" in api_adapter
    assert "IP LAN o Tailscale" not in frontend_adapter
    assert "Access via Tailscale VPN" not in rehearsal
    assert "managed FRP origin" in rehearsal
    assert "public portal route returns 200" in rehearsal
    assert "CRM routes return 404" in rehearsal


def test_scoped_document_links_are_relative_and_resolve():
    broken: list[str] = []
    absolute: list[str] = []

    for document in SCOPED_DOCS:
        for raw_target in _MARKDOWN_LINK.findall(_read(document)):
            target = raw_target.split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            if target.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:[/\\]", target):
                absolute.append(f"{document.relative_to(ROOT)} -> {target}")
                continue
            resolved = (document.parent / target).resolve()
            if not resolved.exists():
                broken.append(f"{document.relative_to(ROOT)} -> {target}")

    assert absolute == []
    assert broken == []


def test_launch_scope_uses_the_live_log_and_not_retired_upgrade_specs():
    launch = _read(LAUNCH_SCOPE)
    support = _read(SUPPORT_RUNBOOK)

    assert "docs/learning/BUILD_LOG.md" in launch
    assert "docs/upgrades/specs/" not in launch
    assert "docs/upgrades/specs/" not in support

from pathlib import Path
from types import SimpleNamespace

from api.services import tunnel_config


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LAUNCHER_PATH = PROJECT_ROOT / "installer" / "launcher.bat"
INSTALLER_PATH = PROJECT_ROOT / "installer" / "fitmanager.iss"


def test_launcher_never_starts_tailscale_funnel_even_with_legacy_env():
    launcher = LAUNCHER_PATH.read_text(encoding="utf-8")
    normalized = launcher.lower()

    assert "tailscale funnel" not in normalized
    assert "public_portal_enabled" not in normalized


def test_installer_packages_the_guarded_launcher():
    installer = INSTALLER_PATH.read_text(encoding="utf-8")

    assert 'Source: "launcher.bat"; DestDir: "{app}"' in installer


def test_provisioned_public_base_url_comes_from_valid_license_instance_id(monkeypatch):
    monkeypatch.setattr(
        "api.services.license.check_license",
        lambda: SimpleNamespace(is_valid=True, instance_id="chiara-studio"),
    )

    assert (
        tunnel_config.get_provisioned_public_base_url()
        == "https://chiara-studio.fitmanagerstudio.com"
    )


def test_provisioned_public_base_url_is_absent_without_instance_id(monkeypatch):
    monkeypatch.setattr(
        "api.services.license.check_license",
        lambda: SimpleNamespace(is_valid=True, instance_id=None),
    )

    assert tunnel_config.get_provisioned_public_base_url() is None

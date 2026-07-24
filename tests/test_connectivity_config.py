import os

import pytest

from api.schemas.system import ConnectivityConfigRequest
from api.services import connectivity_config as config_service


def test_apply_connectivity_config_enables_public_portal_and_updates_runtime_env(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("JWT_SECRET=abc123\nPUBLIC_PORTAL_ENABLED=false\n", encoding="utf-8")
    monkeypatch.setattr(config_service, "ENV_FILE", env_file)
    monkeypatch.setattr(config_service, "get_provisioned_public_base_url", lambda: None)
    monkeypatch.delenv("PUBLIC_PORTAL_ENABLED", raising=False)
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)

    response = config_service.apply_connectivity_config(
        ConnectivityConfigRequest(
            profile="public_portal",
            public_base_url="https://chiara.tail8a3bc3.ts.net",
        )
    )

    content = env_file.read_text(encoding="utf-8")
    assert "JWT_SECRET=abc123" in content
    assert "PUBLIC_PORTAL_ENABLED=true" in content
    assert "PUBLIC_BASE_URL=https://chiara.tail8a3bc3.ts.net" in content
    assert response.public_portal_enabled is True
    assert response.public_base_url == "https://chiara.tail8a3bc3.ts.net"
    assert response.restart_required is False
    assert os.environ["PUBLIC_PORTAL_ENABLED"] == "true"
    assert os.environ["PUBLIC_BASE_URL"] == "https://chiara.tail8a3bc3.ts.net"


def test_apply_connectivity_config_clears_public_portal_settings_for_trusted_devices(
    monkeypatch,
    tmp_path,
):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "JWT_SECRET=abc123\nPUBLIC_PORTAL_ENABLED=true\nPUBLIC_BASE_URL=https://old.ts.net\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config_service, "ENV_FILE", env_file)
    monkeypatch.setattr(config_service, "get_provisioned_public_base_url", lambda: None)
    monkeypatch.setenv("PUBLIC_PORTAL_ENABLED", "true")
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://old.ts.net")

    response = config_service.apply_connectivity_config(
        ConnectivityConfigRequest(profile="trusted_devices")
    )

    content = env_file.read_text(encoding="utf-8")
    assert "PUBLIC_PORTAL_ENABLED=false" in content
    assert "PUBLIC_BASE_URL=" not in content
    assert response.profile == "trusted_devices"
    assert response.public_portal_enabled is False
    assert response.public_base_url is None
    assert os.environ["PUBLIC_PORTAL_ENABLED"] == "false"
    assert "PUBLIC_BASE_URL" not in os.environ


def test_apply_connectivity_config_creates_env_file_when_missing(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    monkeypatch.setattr(config_service, "ENV_FILE", env_file)
    monkeypatch.setattr(config_service, "get_provisioned_public_base_url", lambda: None)
    monkeypatch.delenv("PUBLIC_PORTAL_ENABLED", raising=False)
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)

    response = config_service.apply_connectivity_config(
        ConnectivityConfigRequest(profile="trusted_devices")
    )

    assert env_file.exists()
    content = env_file.read_text(encoding="utf-8")
    assert content == "PUBLIC_PORTAL_ENABLED=false\n"
    assert response.profile == "trusted_devices"
    assert response.restart_required is False


def test_apply_connectivity_config_rejects_legacy_write_for_managed_frp_without_mutation(
    monkeypatch,
    tmp_path,
):
    env_file = tmp_path / ".env"
    original_content = (
        "JWT_SECRET=abc123\n"
        "PUBLIC_PORTAL_ENABLED=true\n"
        "PUBLIC_BASE_URL=https://legacy.tailnet.ts.net\n"
    )
    env_file.write_text(original_content, encoding="utf-8")
    monkeypatch.setattr(config_service, "ENV_FILE", env_file)
    monkeypatch.setattr(
        config_service,
        "get_provisioned_public_base_url",
        lambda: "https://chiara.fitmanagerstudio.com",
    )
    monkeypatch.setenv("PUBLIC_PORTAL_ENABLED", "true")
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://legacy.tailnet.ts.net")

    with pytest.raises(config_service.ManagedPublicAccessError) as exc_info:
        config_service.apply_connectivity_config(
            ConnectivityConfigRequest(
                profile="public_portal",
                public_base_url="https://attacker.example.com",
            )
        )

    assert exc_info.value.public_base_url == "https://chiara.fitmanagerstudio.com"
    assert env_file.read_text(encoding="utf-8") == original_content
    assert os.environ["PUBLIC_BASE_URL"] == "https://legacy.tailnet.ts.net"

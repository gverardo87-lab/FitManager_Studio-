"""Contratto R0.1.5 del trasporto FRP per la challenge ACME HTTP-01."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from api.services import tunnel_config
from api.services.tunnel_config import TunnelConfig
from api.services.tunnel_manager import generate_frpc_toml


def _config(tmp_path: Path) -> TunnelConfig:
    return TunnelConfig(
        instance_id="gvera-dev",
        server_addr="edge.fitmanagerstudio.com",
        server_port=7000,
        tunnel_domain="fitmanagerstudio.com",
        frpc_path=tmp_path / "frpc.exe",
        data_dir=tmp_path,
        config_path=tmp_path / "frpc.toml",
        cert_path=tmp_path / "cert.pem",
        key_path=tmp_path / "key.pem",
        acme_webroot_path=tmp_path / "acme-webroot",
    )


def test_frpc_config_separates_https_app_from_http_acme_webroot(tmp_path):
    content = generate_frpc_toml(_config(tmp_path))

    https_proxy, acme_proxy = content.split("[[proxies]]")[1:]

    assert 'name = "gvera-dev"' in https_proxy
    assert 'type = "https"' in https_proxy
    assert 'localAddr = "127.0.0.1:3000"' in https_proxy
    assert 'type = "https2http"' in https_proxy

    assert 'name = "gvera-dev-acme-http"' in acme_proxy
    assert 'type = "http"' in acme_proxy
    assert 'locations = ["/.well-known/acme-challenge/"]' in acme_proxy
    assert 'type = "static_file"' in acme_proxy
    assert f'localPath = "{_config(tmp_path).acme_webroot_path.as_posix()}"' in acme_proxy
    assert "127.0.0.1:3000" not in acme_proxy
    assert "localAddr" not in acme_proxy


def test_get_tunnel_config_creates_only_dedicated_acme_webroot(monkeypatch, tmp_path):
    tunnel_dir = tmp_path / "tunnel"
    frpc_path = tmp_path / "frpc.exe"
    frpc_path.touch()

    monkeypatch.setattr(tunnel_config, "TUNNEL_DATA_DIR", tunnel_dir)
    monkeypatch.setattr(tunnel_config, "FRPC_CONFIG_PATH", tunnel_dir / "frpc.toml")
    monkeypatch.setattr(tunnel_config, "TUNNEL_CERT_PATH", tunnel_dir / "cert.pem")
    monkeypatch.setattr(tunnel_config, "TUNNEL_KEY_PATH", tunnel_dir / "key.pem")
    monkeypatch.setattr(tunnel_config, "ACME_WEBROOT_PATH", tunnel_dir / "acme-webroot")
    monkeypatch.setattr(tunnel_config, "get_provisioned_instance_id", lambda: "gvera-dev")
    monkeypatch.setattr(tunnel_config, "_resolve_frpc_path", lambda: frpc_path)
    monkeypatch.setattr(tunnel_config, "_ensure_self_signed_cert", lambda _instance_id: True)

    config = tunnel_config.get_tunnel_config()

    assert config is not None
    assert config.acme_webroot_path == tunnel_dir / "acme-webroot"
    assert (
        config.acme_webroot_path / ".well-known" / "acme-challenge"
    ).is_dir()


def test_generated_config_is_accepted_by_frpc_0_61_1(tmp_path):
    frpc_path = Path(__file__).resolve().parents[1] / "tools" / "bin" / "frpc.exe"
    if not frpc_path.exists():
        pytest.skip("frpc.exe non presente sul contributor host")

    config_path = tmp_path / "frpc.toml"
    config_path.write_text(generate_frpc_toml(_config(tmp_path)), encoding="utf-8")

    version = subprocess.run(
        [str(frpc_path), "--version"],
        capture_output=True,
        check=False,
        text=True,
        timeout=10,
    )
    verify = subprocess.run(
        [str(frpc_path), "verify", "-c", str(config_path)],
        capture_output=True,
        check=False,
        text=True,
        timeout=10,
    )

    assert version.returncode == 0
    assert version.stdout.strip() == "0.61.1"
    assert verify.returncode == 0, verify.stdout + verify.stderr
    assert "syntax is ok" in verify.stdout

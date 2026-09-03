"""Contratto R0.1.5 del trasporto FRP per la challenge ACME HTTP-01."""

from __future__ import annotations

import datetime
import subprocess
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from api.services import tunnel_config
from api.services import tunnel_manager
from api.services.tunnel_config import TunnelConfig
from api.services.tunnel_manager import TunnelManager, generate_frpc_toml


def _write_pair(cert_path: Path, key_path: Path, hostname: str, *, mismatched: bool) -> None:
    cert_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    stored_key = (
        rsa.generate_private_key(public_exponent=65537, key_size=2048)
        if mismatched
        else cert_key
    )
    now = datetime.datetime.now(datetime.timezone.utc)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, hostname)])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(cert_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=1))
        .not_valid_after(now + datetime.timedelta(days=30))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName(hostname)]),
            critical=False,
        )
        .sign(cert_key, hashes.SHA256())
    )
    cert_path.parent.mkdir(parents=True, exist_ok=True)
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        stored_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )


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
        acme_state_path=tmp_path / "acme",
        acme_client_path=tmp_path / "lego.exe",
    )


@pytest.mark.parametrize(
    ("system_name", "expected"),
    [
        ("Windows", ("frpc.exe", "lego.exe")),
        ("Darwin", ("frpc", "lego")),
        ("Linux", ("frpc.exe", "lego.exe")),
    ],
)
def test_companion_filenames_preserve_windows_and_enable_darwin(system_name, expected):
    assert tunnel_config._companion_filenames(system_name) == expected


def test_frpc_permission_hint_is_platform_specific():
    assert tunnel_manager._frpc_permission_hint("win32") == "possibile blocco antivirus/firewall"
    assert "Gatekeeper/quarantena" in tunnel_manager._frpc_permission_hint("darwin")


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
    monkeypatch.setattr(tunnel_config, "ACME_STATE_PATH", tunnel_dir / "acme")
    monkeypatch.setattr(tunnel_config, "get_provisioned_instance_id", lambda: "gvera-dev")
    monkeypatch.setattr(tunnel_config, "_resolve_frpc_path", lambda: frpc_path)
    monkeypatch.setattr(tunnel_config, "_resolve_acme_client_path", lambda: None)
    monkeypatch.setattr(tunnel_config, "_ensure_self_signed_cert", lambda _instance_id: True)

    config = tunnel_config.get_tunnel_config()

    assert config is not None
    assert config.acme_webroot_path == tunnel_dir / "acme-webroot"
    assert (
        config.acme_webroot_path / ".well-known" / "acme-challenge"
    ).is_dir()
    assert config.acme_state_path.is_dir()
    assert config.acme_client_path is None


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


def test_bootstrap_replaces_existing_mismatched_cert_key_pair(monkeypatch, tmp_path):
    tunnel_dir = tmp_path / "tunnel"
    cert_path = tunnel_dir / "cert.pem"
    key_path = tunnel_dir / "key.pem"
    _write_pair(
        cert_path,
        key_path,
        "gvera-dev.fitmanagerstudio.com",
        mismatched=True,
    )
    monkeypatch.setattr(tunnel_config, "TUNNEL_DATA_DIR", tunnel_dir)
    monkeypatch.setattr(tunnel_config, "TUNNEL_CERT_PATH", cert_path)
    monkeypatch.setattr(tunnel_config, "TUNNEL_KEY_PATH", key_path)

    assert tunnel_config._ensure_self_signed_cert("gvera-dev") is True

    cert = x509.load_pem_x509_certificate(cert_path.read_bytes())
    key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
    cert_public = cert.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    key_public = key.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    assert cert_public == key_public


def test_monitor_never_discards_process_installed_by_concurrent_restart(tmp_path):
    manager = TunnelManager(_config(tmp_path))
    observed_old_process = object()
    replacement_process = object()
    manager._process = replacement_process

    assert manager._forget_process_if_current(observed_old_process) is False
    assert manager._process is replacement_process
    assert manager._forget_process_if_current(replacement_process) is True
    assert manager._process is None


def test_launch_is_cancelled_after_concurrent_stop(monkeypatch, tmp_path):
    manager = TunnelManager(_config(tmp_path))
    manager._should_run = False

    def forbidden_popen(*_args, **_kwargs):
        raise AssertionError("frpc non deve partire dopo stop")

    monkeypatch.setattr("api.services.tunnel_manager.subprocess.Popen", forbidden_popen)

    manager._launch()

    assert manager._process is None

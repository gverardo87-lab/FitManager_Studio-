"""Test R0.1.5: emissione/rinnovo TLS fail-local e promozione sicura."""

from __future__ import annotations

import datetime
import hashlib
import subprocess
import threading
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from api.services import cert_manager
from api.services.cert_manager import (
    CertificateAction,
    CertificateManager,
    inspect_certificate_pair,
    install_certificate_pair,
)
from api.services.tunnel_config import TunnelConfig


def _config(tmp_path: Path, client_path: Path | None = None) -> TunnelConfig:
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
        acme_client_path=client_path,
    )


def _private_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _write_key(path: Path, key) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )


def _write_self_signed_pair(cert_path: Path, key_path: Path, hostname: str) -> None:
    key = _private_key()
    now = datetime.datetime.now(datetime.timezone.utc)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, hostname)])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=1))
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName(hostname)]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    cert_path.parent.mkdir(parents=True, exist_ok=True)
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    _write_key(key_path, key)


def _write_public_pair(
    cert_path: Path,
    key_path: Path,
    hostname: str,
    *,
    days: int = 90,
) -> None:
    now = datetime.datetime.now(datetime.timezone.utc)
    issuer_key = _private_key()
    issuer_name = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, "Test ACME Intermediate")]
    )
    issuer = (
        x509.CertificateBuilder()
        .subject_name(issuer_name)
        .issuer_name(issuer_name)
        .public_key(issuer_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(issuer_key, hashes.SHA256())
    )

    leaf_key = _private_key()
    leaf_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, hostname)])
    leaf = (
        x509.CertificateBuilder()
        .subject_name(leaf_name)
        .issuer_name(issuer.subject)
        .public_key(leaf_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=1))
        .not_valid_after(now + datetime.timedelta(days=days))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName(hostname)]),
            critical=False,
        )
        .sign(issuer_key, hashes.SHA256())
    )

    cert_path.parent.mkdir(parents=True, exist_ok=True)
    cert_path.write_bytes(
        leaf.public_bytes(serialization.Encoding.PEM)
        + issuer.public_bytes(serialization.Encoding.PEM)
    )
    _write_key(key_path, leaf_key)


def test_inspect_certificate_pair_requires_san_key_match_and_public_chain(tmp_path):
    config = _config(tmp_path)
    _write_public_pair(config.cert_path, config.key_path, config.public_url)

    check = inspect_certificate_pair(
        config.cert_path,
        config.key_path,
        config.public_url,
        require_public_chain=True,
    )

    assert check.usable is True
    assert check.public_chain is True
    assert check.days_remaining is not None and check.days_remaining > 89

    wrong_host = inspect_certificate_pair(
        config.cert_path,
        config.key_path,
        "wrong.fitmanagerstudio.com",
        require_public_chain=True,
    )
    assert wrong_host.usable is False
    assert wrong_host.reason == "hostname_not_in_san"

    _write_key(config.key_path, _private_key())
    mismatch = inspect_certificate_pair(
        config.cert_path,
        config.key_path,
        config.public_url,
        require_public_chain=True,
    )
    assert mismatch.usable is False
    assert mismatch.reason == "certificate_key_mismatch"


def test_self_signed_bootstrap_is_not_accepted_as_public_chain(tmp_path):
    config = _config(tmp_path)
    _write_self_signed_pair(config.cert_path, config.key_path, config.public_url)

    check = inspect_certificate_pair(
        config.cert_path,
        config.key_path,
        config.public_url,
        require_public_chain=True,
    )

    assert check.usable is False
    assert check.reason == "public_chain_missing_or_invalid"


def test_install_rejects_invalid_candidate_without_touching_active_pair(tmp_path):
    config = _config(tmp_path)
    _write_self_signed_pair(config.cert_path, config.key_path, config.public_url)
    active_cert = config.cert_path.read_bytes()
    active_key = config.key_path.read_bytes()

    candidate_cert = tmp_path / "candidate.crt"
    candidate_key = tmp_path / "candidate.key"
    _write_public_pair(candidate_cert, candidate_key, "wrong.fitmanagerstudio.com")

    try:
        install_certificate_pair(config, candidate_cert, candidate_key)
    except ValueError as exc:
        assert "hostname_not_in_san" in str(exc)
    else:
        raise AssertionError("La candidate con SAN errato doveva essere rifiutata")

    assert config.cert_path.read_bytes() == active_cert
    assert config.key_path.read_bytes() == active_key
    assert not (tmp_path / "certificate-install.pending").exists()


def test_install_rolls_back_pair_if_second_replace_fails(monkeypatch, tmp_path):
    config = _config(tmp_path)
    _write_self_signed_pair(config.cert_path, config.key_path, config.public_url)
    active_cert = config.cert_path.read_bytes()
    active_key = config.key_path.read_bytes()
    candidate_cert = tmp_path / "candidate.crt"
    candidate_key = tmp_path / "candidate.key"
    _write_public_pair(candidate_cert, candidate_key, config.public_url)
    real_replace = cert_manager.os.replace
    injected = False

    def fail_on_candidate_cert(source, destination):
        nonlocal injected
        if (
            not injected
            and Path(source).name == "cert.pem.new"
            and Path(destination) == config.cert_path
        ):
            injected = True
            raise OSError("injected second replace failure")
        return real_replace(source, destination)

    monkeypatch.setattr(cert_manager.os, "replace", fail_on_candidate_cert)

    with pytest.raises(OSError, match="injected second replace failure"):
        install_certificate_pair(config, candidate_cert, candidate_key)

    assert config.cert_path.read_bytes() == active_cert
    assert config.key_path.read_bytes() == active_key
    assert not (tmp_path / "certificate-install.pending").exists()


def test_manager_installs_candidate_and_requests_single_frpc_restart(tmp_path):
    client_path = tmp_path / "lego.exe"
    client_path.write_bytes(b"pinned-lego-test")
    config = _config(tmp_path, client_path)
    _write_self_signed_pair(config.cert_path, config.key_path, config.public_url)
    restarts: list[str] = []
    commands: list[list[str]] = []

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        if command[-1] == "--version":
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="lego version 5.2.1 windows/amd64\n",
                stderr="",
            )
        candidate_dir = config.acme_state_path / "certificates"
        _write_public_pair(
            candidate_dir / f"{config.public_url}.crt",
            candidate_dir / f"{config.public_url}.key",
            config.public_url,
        )
        return subprocess.CompletedProcess(command, 0, stdout="issued", stderr="")

    manager = CertificateManager(
        config,
        on_certificate_updated=lambda: restarts.append("restart"),
        command_runner=runner,
        http01_probe=lambda: True,
        expected_client_sha256=hashlib.sha256(client_path.read_bytes()).hexdigest(),
    )

    result = manager.run_once()

    assert result.action is CertificateAction.INSTALLED
    assert restarts == ["restart"]
    assert len(commands) == 2
    issuance_command = commands[1]
    assert "--http" in issuance_command
    assert "--http.webroot" in issuance_command
    assert "--dns" not in issuance_command
    assert "--email" not in issuance_command
    assert config.public_url in issuance_command
    installed = inspect_certificate_pair(
        config.cert_path,
        config.key_path,
        config.public_url,
        require_public_chain=True,
    )
    assert installed.usable is True
    assert not (tmp_path / "certificate-install.pending").exists()


def test_manager_skips_acme_when_public_certificate_is_not_due(tmp_path):
    config = _config(tmp_path)
    _write_public_pair(config.cert_path, config.key_path, config.public_url, days=90)

    def runner(_command: list[str]) -> subprocess.CompletedProcess[str]:
        raise AssertionError("lego non deve essere invocato con >30 giorni residui")

    manager = CertificateManager(config, command_runner=runner)
    result = manager.run_once()

    assert result.action is CertificateAction.CURRENT
    assert result.detail == "certificate_not_due"


def test_manager_failure_preserves_last_active_pair(tmp_path):
    client_path = tmp_path / "lego.exe"
    client_path.write_bytes(b"pinned-lego-test")
    config = _config(tmp_path, client_path)
    _write_self_signed_pair(config.cert_path, config.key_path, config.public_url)
    active_cert = config.cert_path.read_bytes()
    active_key = config.key_path.read_bytes()

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        if command[-1] == "--version":
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="lego version 5.2.1 windows/amd64\n",
                stderr="",
            )
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="challenge failed")

    manager = CertificateManager(
        config,
        command_runner=runner,
        http01_probe=lambda: True,
        expected_client_sha256=hashlib.sha256(client_path.read_bytes()).hexdigest(),
    )
    result = manager.run_once()

    assert result.action is CertificateAction.FAILED
    assert result.detail == "acme_exit_1"
    assert config.cert_path.read_bytes() == active_cert
    assert config.key_path.read_bytes() == active_key


def test_manager_refuses_unpinned_binary_without_executing_it(tmp_path):
    client_path = tmp_path / "lego.exe"
    client_path.write_bytes(b"tampered")
    config = _config(tmp_path, client_path)
    _write_self_signed_pair(config.cert_path, config.key_path, config.public_url)

    def runner(_command: list[str]) -> subprocess.CompletedProcess[str]:
        raise AssertionError("Un binario con hash errato non deve essere eseguito")

    manager = CertificateManager(
        config,
        command_runner=runner,
        expected_client_sha256="0" * 64,
    )
    result = manager.run_once()

    assert result.action is CertificateAction.DISABLED
    assert result.detail == "acme_client_hash_mismatch"


def test_manager_does_not_create_acme_order_until_http_path_is_live(tmp_path):
    client_path = tmp_path / "lego.exe"
    client_path.write_bytes(b"pinned-lego-test")
    config = _config(tmp_path, client_path)
    _write_self_signed_pair(config.cert_path, config.key_path, config.public_url)
    commands: list[list[str]] = []

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        assert command[-1] == "--version"
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="lego version 5.2.1 windows/amd64\n",
            stderr="",
        )

    manager = CertificateManager(
        config,
        command_runner=runner,
        http01_probe=lambda: False,
        expected_client_sha256=hashlib.sha256(client_path.read_bytes()).hexdigest(),
    )
    result = manager.run_once()

    assert result.action is CertificateAction.FAILED
    assert result.detail == "http01_preflight_failed"
    assert commands == [[str(client_path), "--version"]]


def test_manager_stop_terminates_active_acme_process(tmp_path, monkeypatch):
    config = _config(tmp_path)
    process_started = threading.Event()
    process_stopped = threading.Event()

    class FakeProcess:
        returncode: int | None = None

        def poll(self):
            return self.returncode

        def communicate(self, timeout=None):
            if not process_stopped.wait(timeout):
                raise subprocess.TimeoutExpired(["lego.exe"], timeout)
            return "", "terminated"

        def terminate(self):
            self.returncode = -15
            process_stopped.set()

        def kill(self):
            self.returncode = -9
            process_stopped.set()

        def wait(self, timeout=None):
            if not process_stopped.wait(timeout):
                raise subprocess.TimeoutExpired(["lego.exe"], timeout)
            return self.returncode

    fake_process = FakeProcess()

    def fake_popen(*_args, **_kwargs):
        process_started.set()
        return fake_process

    monkeypatch.setattr(cert_manager.subprocess, "Popen", fake_popen)
    manager = CertificateManager(config)
    command_thread = threading.Thread(
        target=manager._run_command,
        args=(["lego.exe", "run"],),
    )
    command_thread.start()
    assert process_started.wait(timeout=1)

    manager.stop()
    command_thread.join(timeout=1)

    assert process_stopped.is_set()
    assert fake_process.returncode == -15
    assert not command_thread.is_alive()

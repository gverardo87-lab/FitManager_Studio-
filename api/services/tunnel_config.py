"""
Configurazione tunnel FRP — layer tra identita' (licenza) e esecuzione (tunnel_manager).

Legge instance_id dalla licenza, assembla i parametri di connessione,
risolve i path del binario frpc e della directory dati.
Il tunnel_manager riceve un TunnelConfig e non deve sapere nulla di licenze o path.

Include generazione certificato self-signed per Fase 1 (SNI routing validation).
In Fase 2 il cert viene sostituito da Let's Encrypt — zero cambiamenti al codice.
"""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass
from pathlib import Path

from api.config import DATA_DIR, PROJECT_ROOT, is_compiled

logger = logging.getLogger(__name__)

# --- Costanti server FRP (VPS edge AVGV) ---
FRP_SERVER_ADDR = "edge.fitmanagerstudio.com"
FRP_SERVER_PORT = 7000
TUNNEL_DOMAIN = "fitmanagerstudio.com"

# --- Path ---
TUNNEL_DATA_DIR = DATA_DIR / "tunnel"
FRPC_CONFIG_PATH = TUNNEL_DATA_DIR / "frpc.toml"
TUNNEL_CERT_PATH = TUNNEL_DATA_DIR / "cert.pem"
TUNNEL_KEY_PATH = TUNNEL_DATA_DIR / "key.pem"

# frpc binary: in compiled mode sta accanto all'exe, in dev in tools/bin/
_FRPC_FILENAME = "frpc.exe"


@dataclass(frozen=True)
class TunnelConfig:
    """Configurazione immutabile per il tunnel_manager."""

    instance_id: str                  # slug trainer (es. "gvera-dev")
    server_addr: str                  # indirizzo frps (es. "edge.fitmanagerstudio.com")
    server_port: int                  # porta frps (es. 7000)
    tunnel_domain: str                # dominio base (es. "fitmanagerstudio.com")
    frpc_path: Path                   # path al binario frpc
    data_dir: Path                    # directory per config, cert, log tunnel
    config_path: Path                 # path al frpc.toml generato
    cert_path: Path                   # path al certificato TLS (self-signed o LE)
    key_path: Path                    # path alla chiave privata TLS

    @property
    def public_url(self) -> str:
        """URL pubblico del tunnel (es. 'gvera-dev.fitmanagerstudio.com')."""
        return f"{self.instance_id}.{self.tunnel_domain}"


def get_provisioned_instance_id() -> str | None:
    """Restituisce l'identita FRP assegnata da una licenza valida, se presente.

    La provision FRP dipende dalla licenza, non dalla disponibilita temporanea
    del binario ``frpc`` o dallo stato del processo tunnel.
    """
    from api.services.license import check_license

    result = check_license()
    if not result.is_valid:
        return None
    return result.instance_id or None


def get_provisioned_public_base_url() -> str | None:
    """Origine pubblica autoritativa per un'istanza FRP provisionata."""
    instance_id = get_provisioned_instance_id()
    if not instance_id:
        return None
    return f"https://{instance_id}.{TUNNEL_DOMAIN}"


def _ensure_self_signed_cert(instance_id: str) -> bool:
    """Genera cert self-signed se non esiste. Restituisce True se cert pronto.

    Fase 1: cert self-signed per validare SNI routing e P2 data-blind.
    Fase 2: sostituito da Let's Encrypt (cert_manager.py), stessi path.

    Il cert copre sia il subdomain specifico sia il wildcard (SAN).
    Durata: 365 giorni. Alla scadenza viene rigenerato al prossimo avvio.
    """
    if TUNNEL_CERT_PATH.exists() and TUNNEL_KEY_PATH.exists():
        # Verifica scadenza
        try:
            from cryptography import x509

            cert_data = TUNNEL_CERT_PATH.read_bytes()
            cert = x509.load_pem_x509_certificate(cert_data)
            if cert.not_valid_after_utc > datetime.datetime.now(datetime.timezone.utc):
                return True
            logger.info("Cert self-signed scaduto, rigenero")
        except Exception:
            logger.warning("Cert self-signed illeggibile, rigenero")

    try:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID

        # Genera chiave RSA 2048
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, f"{instance_id}.{TUNNEL_DOMAIN}"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "FitManager Studio (self-signed)"),
        ])

        now = datetime.datetime.now(datetime.timezone.utc)
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + datetime.timedelta(days=365))
            .add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(f"{instance_id}.{TUNNEL_DOMAIN}"),
                    x509.DNSName(f"*.{TUNNEL_DOMAIN}"),
                ]),
                critical=False,
            )
            .sign(key, hashes.SHA256())
        )

        TUNNEL_DATA_DIR.mkdir(parents=True, exist_ok=True)

        TUNNEL_KEY_PATH.write_bytes(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        TUNNEL_CERT_PATH.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

        logger.info(
            "Cert self-signed generato: %s.%s (valido fino %s)",
            instance_id,
            TUNNEL_DOMAIN,
            (now + datetime.timedelta(days=365)).strftime("%Y-%m-%d"),
        )
        return True

    except Exception as e:
        logger.error("Generazione cert self-signed fallita: %s", e)
        return False


def _resolve_frpc_path() -> Path | None:
    """Trova il binario frpc. None se non trovato."""
    if is_compiled():
        # Compiled: frpc accanto all'eseguibile principale
        bundled = Path(__import__("sys").executable).resolve().parent / _FRPC_FILENAME
        if bundled.exists():
            return bundled
    else:
        # Dev: in tools/bin/
        dev_path = PROJECT_ROOT / "tools" / "bin" / _FRPC_FILENAME
        if dev_path.exists():
            return dev_path

    return None


def get_tunnel_config() -> TunnelConfig | None:
    """
    Assembla la configurazione tunnel dalla licenza e dall'ambiente.

    Returns None se:
    - licenza non valida
    - licenza senza instance_id (installazione senza tunnel)
    - binario frpc non trovato
    """
    instance_id = get_provisioned_instance_id()
    if not instance_id:
        logger.debug("Tunnel config: nessuna istanza FRP provisionata, tunnel disabilitato")
        return None

    frpc_path = _resolve_frpc_path()
    if frpc_path is None:
        logger.warning(
            "Tunnel config: instance_id '%s' presente ma frpc non trovato. "
            "Dev: scaricare in tools/bin/frpc.exe. Compiled: verificare bundle.",
            instance_id,
        )
        return None

    # Assicura che la directory tunnel esista
    TUNNEL_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Genera cert self-signed se necessario (Fase 1: SNI validation)
    if not _ensure_self_signed_cert(instance_id):
        logger.warning("Tunnel config: cert self-signed non disponibile, tunnel disabilitato")
        return None

    config = TunnelConfig(
        instance_id=instance_id,
        server_addr=FRP_SERVER_ADDR,
        server_port=FRP_SERVER_PORT,
        tunnel_domain=TUNNEL_DOMAIN,
        frpc_path=frpc_path,
        data_dir=TUNNEL_DATA_DIR,
        config_path=FRPC_CONFIG_PATH,
        cert_path=TUNNEL_CERT_PATH,
        key_path=TUNNEL_KEY_PATH,
    )

    logger.info("Tunnel config: %s -> %s (frpc: %s)", instance_id, config.public_url, frpc_path)
    return config

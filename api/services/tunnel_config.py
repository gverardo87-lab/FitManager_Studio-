"""
Configurazione tunnel FRP — layer tra identita' (licenza) e esecuzione (tunnel_manager).

Legge instance_id dalla licenza, assembla i parametri di connessione,
risolve i path del binario frpc e della directory dati.
Il tunnel_manager riceve un TunnelConfig e non deve sapere nulla di licenze o path.

Include il certificato bootstrap self-signed e il webroot ACME dedicato.
R0.1.5 sostituisce il bootstrap con Let's Encrypt mantenendo gli stessi path cert/key.
"""

from __future__ import annotations

import datetime
import logging
import platform
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
ACME_WEBROOT_PATH = TUNNEL_DATA_DIR / "acme-webroot"
ACME_STATE_PATH = TUNNEL_DATA_DIR / "acme"

def _companion_filenames(system_name: str) -> tuple[str, str]:
    """Nomi companion per il target; ogni piattaforma non Darwin resta fail-safe Windows."""
    if system_name == "Darwin":
        return "frpc", "lego"
    return "frpc.exe", "lego.exe"


# In compiled mode i companion stanno accanto all'exe, in dev in tools/bin/.
# Il fallback conserva il comportamento Windows e non abilita piattaforme non supportate.
_FRPC_FILENAME, _ACME_CLIENT_FILENAME = _companion_filenames(platform.system())


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
    acme_webroot_path: Path           # root statica dedicata alla sola challenge HTTP-01
    acme_state_path: Path             # account e output del client ACME
    acme_client_path: Path | None     # client ACME; None non blocca tunnel/CRM locale

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
        # Una coppia esistente e' riusabile solo se tempo, SAN e key-match sono coerenti.
        try:
            from cryptography import x509
            from cryptography.hazmat.primitives import serialization

            cert_data = TUNNEL_CERT_PATH.read_bytes()
            cert = x509.load_pem_x509_certificate(cert_data)
            key = serialization.load_pem_private_key(
                TUNNEL_KEY_PATH.read_bytes(),
                password=None,
            )
            now = datetime.datetime.now(datetime.timezone.utc)
            sans = cert.extensions.get_extension_for_class(
                x509.SubjectAlternativeName
            ).value.get_values_for_type(x509.DNSName)
            cert_public = cert.public_key().public_bytes(
                serialization.Encoding.DER,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            key_public = key.public_key().public_bytes(
                serialization.Encoding.DER,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            hostname = f"{instance_id}.{TUNNEL_DOMAIN}"
            if (
                cert.not_valid_before_utc <= now < cert.not_valid_after_utc
                and hostname in sans
                and cert_public == key_public
            ):
                return True
            logger.warning("Coppia TLS esistente non coerente, genero bootstrap")
        except Exception:
            logger.warning("Coppia TLS esistente illeggibile, genero bootstrap")

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


def _resolve_acme_client_path() -> Path | None:
    """Trova il client ACME pinato. None mantiene operativo il tunnel bootstrap."""
    if is_compiled():
        bundled = Path(__import__("sys").executable).resolve().parent / _ACME_CLIENT_FILENAME
        if bundled.exists():
            return bundled
    else:
        dev_path = PROJECT_ROOT / "tools" / "bin" / _ACME_CLIENT_FILENAME
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
            "Dev: scaricare in tools/bin/%s. Compiled: verificare bundle.",
            instance_id,
            _FRPC_FILENAME,
        )
        return None

    # Assicura che la directory tunnel e il solo webroot pubblico ACME esistano.
    TUNNEL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    (ACME_WEBROOT_PATH / ".well-known" / "acme-challenge").mkdir(
        parents=True,
        exist_ok=True,
    )
    ACME_STATE_PATH.mkdir(parents=True, exist_ok=True)

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
        acme_webroot_path=ACME_WEBROOT_PATH,
        acme_state_path=ACME_STATE_PATH,
        acme_client_path=_resolve_acme_client_path(),
    )

    logger.info("Tunnel config: %s -> %s (frpc: %s)", instance_id, config.public_url, frpc_path)
    return config

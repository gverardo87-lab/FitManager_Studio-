"""
Configurazione tunnel FRP — layer tra identita' (licenza) e esecuzione (tunnel_manager).

Legge instance_id dalla licenza, assembla i parametri di connessione,
risolve i path del binario frpc e della directory dati.
Il tunnel_manager riceve un TunnelConfig e non deve sapere nulla di licenze o path.
"""

from __future__ import annotations

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

    @property
    def public_url(self) -> str:
        """URL pubblico del tunnel (es. 'gvera-dev.fitmanagerstudio.com')."""
        return f"{self.instance_id}.{self.tunnel_domain}"


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
    from api.services.license import check_license

    result = check_license()

    if not result.is_valid:
        logger.debug("Tunnel config: licenza non valida (%s)", result.status)
        return None

    instance_id = result.instance_id
    if not instance_id:
        logger.debug("Tunnel config: licenza valida ma senza instance_id, tunnel disabilitato")
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

    config = TunnelConfig(
        instance_id=instance_id,
        server_addr=FRP_SERVER_ADDR,
        server_port=FRP_SERVER_PORT,
        tunnel_domain=TUNNEL_DOMAIN,
        frpc_path=frpc_path,
        data_dir=TUNNEL_DATA_DIR,
        config_path=FRPC_CONFIG_PATH,
    )

    logger.info("Tunnel config: %s -> %s (frpc: %s)", instance_id, config.public_url, frpc_path)
    return config

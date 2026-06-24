"""
contract_settlement — conguaglio puro per la terminazione anticipata (G7.1).

Specchio di `contract_state.py`: funzioni **PURE** (zero DB). Il caller (endpoint `terminate`, G7.3)
deriva `sedute_erogate` server-side (count Event Completato PT) e passa i campi del contratto; qui si
calcola SOLO la matematica del conguaglio. **Policy-pluggable**: la *valorizzazione* del servizio reso
è l'unica parte gated dalla decisione del tributarista (default `pro_sedute`, marcato **PROVISIONAL**);
la *meccanica* (conguaglio firmato → esito) è ferma.

Modello: FINANCIAL_DOMAIN_MODEL §3.1/§7 (terminazione, Strada B) · IMPL_PLAN_FINANCIAL_REALIGN §4.2 ·
SPEC_G7.0 §2 (enum motivo_chiusura). Confine: niente endpoint, niente DB, niente residuo (è
contract_state). Qui non si SCRIVE nulla: si ritorna un Settlement che il caller traduce in
movimenti/colonne (fonte-unica-importo, IMPL_PLAN §4.6).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


# ── Vocabolario chiusura (SPEC_G7.0 §2) — esito economico, enum chiuso a 4 ──
class MotivoChiusura(str, Enum):
    COMPLETAMENTO = "COMPLETAMENTO"                # auto-close: saldato + crediti esauriti
    CONSUNZIONE = "CONSUNZIONE"                    # (riservato) regola il residuo post-scadenza
    TERMINAZIONE_RIMBORSO = "TERMINAZIONE_RIMBORSO"      # terminazione anticipata, gamba rimborso
    TERMINAZIONE_DECADENZA = "TERMINAZIONE_DECADENZA"    # terminazione/decadi, gamba storno (no cassa)


class SettlementEsito(str, Enum):
    RIMBORSO = "RIMBORSO"                # conguaglio < 0: il trainer deve restituire (abs)
    SALDO_A_PERDERE = "SALDO_A_PERDERE"  # conguaglio >= 0: write-off del dovuto (storno)
    NULLO = "NULLO"                      # conguaglio ~ 0


# ── Policy di valorizzazione (l'UNICO punto policy-gated) ──
@dataclass(frozen=True)
class SettlementPolicy:
    """Politica di valorizzazione del servizio reso. PLUGGABLE: la formula è l'unica parte gated
    dal tributarista. `mode='pro_sedute'` = pro-rata lineare sulle sedute (default, PROVISIONAL)."""
    mode: str = "pro_sedute"
    arrotondamento: int = 2


DEFAULT_POLICY = SettlementPolicy()


def valore_servizio_reso(
    sedute_erogate: int,
    prezzo_totale: float | None,
    crediti_totali: int | None,
    policy: SettlementPolicy = DEFAULT_POLICY,
) -> float:
    """Valore economico del servizio GIÀ reso, su **BASE SEDUTE** (mai tempo).

    ⚠️ **PROVISIONAL** (policy-gated, decisione tributarista). Default `pro_sedute` lineare:
    `prezzo * sedute_erogate / crediti_totali`, cappato a `prezzo`. Se `crediti_totali` è assente
    (contratto a denaro senza monte-sedute) il pro-sedute non si applica → si considera tutto reso.
    """
    prezzo = prezzo_totale or 0
    crediti = crediti_totali or 0
    sedute = max(sedute_erogate or 0, 0)
    if policy.mode == "pro_sedute":
        if crediti <= 0:
            return round(prezzo, policy.arrotondamento)
        return round(min(prezzo * sedute / crediti, prezzo), policy.arrotondamento)
    raise ValueError(f"SettlementPolicy.mode non supportato: {policy.mode!r}")


@dataclass(frozen=True)
class Settlement:
    """Risultato puro del conguaglio. Il caller (G7.3) traduce esito+importi in movimenti/colonne."""
    valore_servizio_reso: float
    conguaglio: float          # valore_reso − totale_versato (firmato)
    esito: SettlementEsito
    importo_rimborso: float    # abs(conguaglio) se RIMBORSO, altrimenti 0
    quota_da_stornare: float   # residuo corrente da azzerare (write-off), >= 0
    sedute_erogate: int


def compute_settlement(
    *,
    sedute_erogate: int,
    prezzo_totale: float | None,
    crediti_totali: int | None,
    totale_versato: float | None,
    residuo_corrente: float,
    policy: SettlementPolicy = DEFAULT_POLICY,
) -> Settlement:
    """Conguaglio di terminazione (FDM §7), firmato rispetto al servizio reso.

    `residuo_corrente` = `contract_state.residuo()` PRIMA dello storno, passato dal caller in UNA
    variabile (fonte-unica-importo, IMPL_PLAN §4.6) e riusato per la gamba di storno.

    conguaglio = valore_servizio_reso − totale_versato:
      • < 0  → il cliente ha pagato più del reso → **RIMBORSO** (importo = abs)
      • >= 0 → il cliente ha pagato meno del reso → **SALDO_A_PERDERE** (write-off del residuo)
      • ~ 0  → **NULLO**
    """
    reso = valore_servizio_reso(sedute_erogate, prezzo_totale, crediti_totali, policy)
    versato = totale_versato or 0
    conguaglio = round(reso - versato, policy.arrotondamento)

    if conguaglio < -0.009:
        esito = SettlementEsito.RIMBORSO
        importo_rimborso = round(abs(conguaglio), policy.arrotondamento)
    elif conguaglio > 0.009:
        esito = SettlementEsito.SALDO_A_PERDERE
        importo_rimborso = 0.0
    else:
        esito = SettlementEsito.NULLO
        importo_rimborso = 0.0

    return Settlement(
        valore_servizio_reso=reso,
        conguaglio=conguaglio,
        esito=esito,
        importo_rimborso=importo_rimborso,
        quota_da_stornare=round(max(residuo_corrente or 0, 0.0), policy.arrotondamento),
        sedute_erogate=max(int(sedute_erogate or 0), 0),
    )

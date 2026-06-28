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


# ── Vocabolario chiusura (SPEC_G7.0 §2 + ADR-018) — esito economico ──
class MotivoChiusura(str, Enum):
    COMPLETAMENTO = "COMPLETAMENTO"                # auto-close: saldato + crediti esauriti
    CONSUNZIONE = "CONSUNZIONE"                    # terminazione a conguaglio ~0 (esito PARI); in origine riservato per residuo post-scadenza (L2)
    TERMINAZIONE_RIMBORSO = "TERMINAZIONE_RIMBORSO"          # terminazione, ramo CREDITO_CLIENTE (rimborso al cliente)
    TERMINAZIONE_SALDO_TRAINER = "TERMINAZIONE_SALDO_TRAINER"  # terminazione, ramo CREDITO_TRAINER (incasso/rinuncia/a-credito; ADR-018)
    TERMINAZIONE_DECADENZA = "TERMINAZIONE_DECADENZA"        # LEGACY/storico: non più emesso da terminate su contratti vivi


class SettlementEsito(str, Enum):
    """Fatto economico puro (ADR-018), balance-based — non un'azione (l'azione la sceglie il caller)."""
    CREDITO_CLIENTE = "CREDITO_CLIENTE"  # versato > reso: il trainer deve restituire (rimborso)
    CREDITO_TRAINER = "CREDITO_TRAINER"  # reso > versato: il cliente deve ancora → incassa/rinuncia/a-credito
    PARI = "PARI"                        # reso ~ versato (entro dead-zone): nessun conguaglio


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
    """Fatto economico puro del conguaglio (ADR-018). Il caller (G7.3/G7.9) traduce le grandezze in
    azione + movimenti/colonne: rimborso (`credito_cliente`), incasso/rinuncia/a-credito
    (`credito_trainer`), storno (`residuo_pre − incassato`). Nessuna decisione d'azione qui.

    Con P=prezzo, N=netto incassato (versato − rimborsato, G8.1/ADR-019), R=valore_servizio_reso:
      credito_cliente = max(N−R, 0) · credito_trainer = max(R−N, 0) · quota_non_erogata = max(P−R, 0)
      residuo_pre = residuo() PRE-storno (net-aware, = residuo_corrente passato dal caller)."""
    valore_servizio_reso: float   # R
    conguaglio: float             # R − N (firmato), classificato con dead-zone ±0.009
    esito: SettlementEsito
    credito_cliente: float        # max(N − R, 0): il trainer deve restituire (rimborso al cliente)
    credito_trainer: float        # max(R − N, 0): il cliente deve ancora, per servizio già reso
    quota_non_erogata: float      # max(P − R, 0): servizio mai erogato (storno legittimo)
    residuo_pre: float            # == residuo() PRE-storno (net-aware)
    sedute_erogate: int


def compute_settlement(
    *,
    sedute_erogate: int,
    prezzo_totale: float | None,
    crediti_totali: int | None,
    totale_versato: float | None,
    residuo_corrente: float,
    totale_rimborsato: float | None = None,
    policy: SettlementPolicy = DEFAULT_POLICY,
) -> Settlement:
    """Conguaglio di terminazione (FDM §7 + ADR-018), **fatto economico puro** firmato sul servizio reso.

    `residuo_corrente` = `contract_state.residuo()` PRIMA dello storno, passato dal caller in UNA
    variabile (fonte-unica-importo, IMPL_PLAN §4.6); diventa `residuo_pre`, riusato per la gamba di storno.

    NET-AWARE (G8.1/ADR-019): il conguaglio confronta il servizio reso con l'INCASSATO NETTO
    `N = max(totale_versato − totale_rimborsato, 0)`, non col versato lordo. Con `totale_rimborsato`
    assente/0 → `N == versato` → byte-identico a pre-G8.1 (al terminate il rimborso è sempre 0). Diventa
    >0 solo ri-terminando un contratto RIAPERTO con un rimborso che resta (ADR-019): lì il netto già
    sconta il rimborso → una ri-terminazione PARI non ri-rimborsa (niente doppio rimborso).

    conguaglio = valore_servizio_reso − N, classificato con dead-zone ±0.009:
      • < 0  → N > reso → **CREDITO_CLIENTE** (il trainer deve restituire `credito_cliente`)
      • > 0  → reso > N → **CREDITO_TRAINER** (il cliente deve ancora `credito_trainer`)
      • ~ 0  → **PARI**
    Le tre azioni sul ramo CREDITO_TRAINER (incassa ora / rinuncia / a credito) le sceglie il caller:
    qui si espone solo il fatto (credito_trainer), mai il write-off come default.
    """
    a = policy.arrotondamento
    reso = valore_servizio_reso(sedute_erogate, prezzo_totale, crediti_totali, policy)
    prezzo = prezzo_totale or 0
    netto = round(max((totale_versato or 0) - (totale_rimborsato or 0), 0.0), a)
    conguaglio = round(reso - netto, a)

    if conguaglio < -0.009:
        esito = SettlementEsito.CREDITO_CLIENTE
    elif conguaglio > 0.009:
        esito = SettlementEsito.CREDITO_TRAINER
    else:
        esito = SettlementEsito.PARI

    return Settlement(
        valore_servizio_reso=reso,
        conguaglio=conguaglio,
        esito=esito,
        credito_cliente=round(max(netto - reso, 0.0), a),
        credito_trainer=round(max(reso - netto, 0.0), a),
        quota_non_erogata=round(max(prezzo - reso, 0.0), a),
        residuo_pre=round(max(residuo_corrente or 0, 0.0), a),
        sedute_erogate=max(int(sedute_erogate or 0), 0),
    )

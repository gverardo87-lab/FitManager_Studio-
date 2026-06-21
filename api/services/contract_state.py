"""
contract_state — SSoT della derivazione dello stato finanziario del contratto.

Implementa FINANCIAL_DOMAIN_MODEL.md (§3 stati di vita, §4 vocabolario/rollup/costanti,
§5 sotto-stato denaro). Funzioni **PURE**: nessun accesso al DB. I caller forniscono
`crediti_usati` (batch-fetch, anti-N+1), `rates` e `today`.

REGOLA D'ORO (modello §3): nessun endpoint/KPI ricalcola "attivo/scaduto" per conto suo.
Tutti derivano da qui. `aperto` (chiuso=False) ≠ `attivo` (ATTIVO = aperto + vigente).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional, Sequence

# ── §4.2 Costanti temporali (dichiarate UNA volta) ──────────────────
SOGLIA_IN_SCADENZA_GG = 30   # ATTIVO entra in "in scadenza"
SOGLIA_CHURN_GG = 90         # unica: raffreddamento lapsed = finestra retention = confine churn


class Lifecycle(str, Enum):
    ELIMINATO = "eliminato"
    CHIUSO = "chiuso"
    ATTIVO = "attivo"
    SOSPESO = "sospeso"
    ESAURITO = "esaurito"


class MoneySubstate(str, Enum):
    SALDATO = "saldato"
    DA_PIANIFICARE = "da_pianificare"
    PARZIALE = "parziale"        # parzialmente pianificato
    PIANIFICATO = "pianificato"


class ClientEngagement(str, Enum):
    INGAGGIATO = "ingaggiato"
    LAPSED_CALDO = "lapsed_caldo"
    LAPSED_FREDDO = "lapsed_freddo"
    # 'perso' è a-memoria (esito_rinnovo_motivo) → gestito dal caller, non derivato qui


def _as_date(d) -> Optional[date]:
    # Dalla ORM (SQLModel) le colonne `date` arrivano come datetime.date → ramo identità.
    # Il ramo-stringa copre SOLO i caller raw-SQL (es. dashboard.py GROUP BY) dove SQLite
    # ritorna le date come testo. Verificato sul crm.db reale (2026-06-21): ORM = date.
    return date.fromisoformat(d) if isinstance(d, str) else d


# ── Assi (§2) ──────────────────────────────────────────────────────

def crediti_residui(contract, crediti_usati: int) -> int:
    return max((contract.crediti_totali or 0) - (crediti_usati or 0), 0)


def residuo(contract) -> float:
    return round(max((contract.prezzo_totale or 0) - (contract.totale_versato or 0), 0.0), 2)


def is_scaduto(contract, today: date) -> bool:
    sc = _as_date(contract.data_scadenza)
    return sc is not None and sc < today


def is_vigente(contract, today: date) -> bool:
    """Vigente = scadenza assente o NON ancora passata. 'scade oggi' è ancora vigente."""
    sc = _as_date(contract.data_scadenza)
    return sc is None or sc >= today


# ── Stato di vita (§3) ─────────────────────────────────────────────

def contract_lifecycle(contract, crediti_usati: int, today: date) -> Lifecycle:
    """Stato di vita derivato (tempo × crediti × chiuso). Unica fonte."""
    if getattr(contract, "deleted_at", None) is not None:
        return Lifecycle.ELIMINATO
    if contract.chiuso:
        return Lifecycle.CHIUSO
    if is_scaduto(contract, today):
        return Lifecycle.SOSPESO if crediti_residui(contract, crediti_usati) > 0 else Lifecycle.ESAURITO
    return Lifecycle.ATTIVO


def is_in_scadenza(contract, today: date) -> bool:
    """ATTIVO con scadenza entro la soglia (worklist 'in scadenza')."""
    sc = _as_date(contract.data_scadenza)
    if sc is None:
        return False
    return today <= sc <= date.fromordinal(today.toordinal() + SOGLIA_IN_SCADENZA_GG)


# ── Sotto-stato denaro (§5, ortogonale) ────────────────────────────

def money_substate(contract, rates: Sequence, *, residuo_val: Optional[float] = None) -> MoneySubstate:
    """`rates` = Rate NON eliminate del contratto."""
    res = residuo(contract) if residuo_val is None else residuo_val
    if res <= 0.009:
        return MoneySubstate.SALDATO
    non_saldate = [r for r in rates if r.stato in ("PENDENTE", "PARZIALE")]
    if not non_saldate:
        return MoneySubstate.DA_PIANIFICARE
    somma_residui = sum((r.importo_previsto or 0) - (r.importo_saldato or 0) for r in non_saldate)
    return MoneySubstate.PARZIALE if somma_residui < res - 0.01 else MoneySubstate.PIANIFICATO


def has_rate_scadute(rates: Sequence, today: date) -> bool:
    for r in rates:
        if r.stato in ("PENDENTE", "PARZIALE"):
            sc = _as_date(r.data_scadenza)
            if sc is not None and sc < today:
                return True
    return False


# ── Rollup cliente (§4.1) ──────────────────────────────────────────

def is_engaged(lifecycles: Sequence[Lifecycle]) -> bool:
    """Ingaggiato = ≥1 contratto ATTIVO o SOSPESO (il sospeso conta: gli devi sedute)."""
    return any(lf in (Lifecycle.ATTIVO, Lifecycle.SOSPESO) for lf in lifecycles)


def client_engagement(
    lifecycles: Sequence[Lifecycle],
    *,
    giorni_lapse: Optional[int] = None,
    giorni_ultimo_contatto: Optional[int] = None,
) -> ClientEngagement:
    """
    Engagement DERIVATO (§4.1). 'perso' (a-memoria) lo decide il caller.
    lapsed_freddo: lapse > SOGLIA_CHURN AND (nessun contatto loggato o ultimo contatto > SOGLIA_CHURN).
    Assunzione-proxy (§4.1): i contatti loggati in communication_log sono proxy del contatto reale.
    """
    if is_engaged(lifecycles):
        return ClientEngagement.INGAGGIATO
    lapse_oltre = giorni_lapse is not None and giorni_lapse > SOGLIA_CHURN_GG
    contatto_freddo = giorni_ultimo_contatto is None or giorni_ultimo_contatto > SOGLIA_CHURN_GG
    if lapse_oltre and contatto_freddo:
        return ClientEngagement.LAPSED_FREDDO
    return ClientEngagement.LAPSED_CALDO


# ── Aggregato comodo per i caller ──────────────────────────────────

@dataclass(frozen=True)
class ContractState:
    """
    Stato finanziario completo di un contratto.

    ⚠️ `money` NON va MAI letto isolato da `lifecycle`. Lo stesso DA_PIANIFICARE
    significa cose opposte a seconda dello stato di vita:
      • ATTIVO + DA_PIANIFICARE  → azionabile: crea rata (worklist "da pianificare").
      • SOSPESO/ESAURITO + DA_PIANIFICARE → NON rateizzabile (contratto scaduto):
        il denaro è dovuto ma la via è "incassa residuo" diretto (G6).
    Per non sbagliare, i caller usano gli helper `is_rate_planificabile()` /
    `is_residuo_incassabile_diretto()` invece di ispezionare `money` a mano.
    Difesa SSoT contro G1/G2 (un contratto scaduto NON deve finire in "da pianificare").
    """
    lifecycle: Lifecycle
    money: MoneySubstate
    residuo: float
    crediti_residui: int
    rate_scadute: bool
    in_scadenza: bool


def is_rate_planificabile(state: ContractState) -> bool:
    """
    True solo se si PUÒ creare una rata: contratto ATTIVO ancora da pianificare.
    Worklist "contratti da pianificare" (G1) DEVE filtrare con questo, mai con
    `money == DA_PIANIFICARE` da solo (intercetterebbe gli scaduti = azione impossibile).
    """
    return state.lifecycle == Lifecycle.ATTIVO and state.money == MoneySubstate.DA_PIANIFICARE


def is_residuo_incassabile_diretto(state: ContractState) -> bool:
    """
    True se c'è denaro dovuto su un contratto scaduto (SOSPESO/ESAURITO) → non
    rateizzabile, si incassa il residuo direttamente (G6, Blocco 4). È l'altra
    metà dell'ambiguità di DA_PIANIFICARE: complementare a `is_rate_planificabile`.
    """
    return state.lifecycle in (Lifecycle.SOSPESO, Lifecycle.ESAURITO) and state.residuo > 0.009


def evaluate_contract(contract, crediti_usati: int, rates: Sequence, today: date) -> ContractState:
    """Stato finanziario completo di un contratto. Entry point per i caller."""
    lf = contract_lifecycle(contract, crediti_usati, today)
    res = residuo(contract)
    return ContractState(
        lifecycle=lf,
        money=money_substate(contract, rates, residuo_val=res),
        residuo=res,
        crediti_residui=crediti_residui(contract, crediti_usati),
        rate_scadute=has_rate_scadute(rates, today),
        in_scadenza=(lf == Lifecycle.ATTIVO and is_in_scadenza(contract, today)),
    )

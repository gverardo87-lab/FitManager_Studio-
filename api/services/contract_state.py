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


def sedute_non_erogate_alla_chiusura(contract, sedute_completate: int) -> int:
    """M4 (G7.7): per un contratto chiuso `COMPLETAMENTO` con servizio reso < monte-sedute, il numero di
    sedute prenotate-ma-non-erogate alla chiusura — segnala un rimborso recuperabile (Riapri→Termina).
    0 negli altri casi (non chiuso, motivo ≠ COMPLETAMENTO, senza monte-sedute, o tutto erogato).
    Indicatore di trasparenza: l'auto-close conta l'OCCUPAZIONE (Programmato+Completato), quindi un
    COMPLETAMENTO può chiudersi su sedute solo PRENOTATE; questo rende esplicito il delta erogato↔venduto."""
    if not contract.chiuso or getattr(contract, "motivo_chiusura", None) != "COMPLETAMENTO":
        return 0
    crediti = contract.crediti_totali or 0
    if crediti <= 0:
        return 0
    return max(crediti - (sedute_completate or 0), 0)


def residuo(contract) -> float:
    """Denaro ancora dovuto sul contratto (FDM §2). Strada B: il LORDO (prezzo/versato) è immutabile,
    lo storno (`quota_stornata`, G7) abbassa il residuo senza riscrivere il prezzo.

    NET-AWARE (G8.1 / ADR-019 D-RESIDUO-NETTO): sottrae `netto_incassato()` (versato − rimborsato),
    NON il versato lordo. Finché `totale_rimborsato == 0` (ovunque tranne i contratti terminati) è
    BYTE-IDENTICO al lordo. Cambia SOLO quando un rimborso «resta» su un contratto APERTO — possibile
    solo dopo `reopen` (che da G8.1 non cancella più la cassa di terminazione, ADR-019): lì il cliente
    ha riavuto denaro → deve di più → il residuo lo include attraverso il netto. È l'unico punto SSoT
    toccato; i ~15 consumer ne ereditano la correzione.

    `getattr` default 0 NON-negoziabile: i test usano SimpleNamespace senza i campi e la finestra
    pre-G7.0 in produzione non ha le colonne (`netto_incassato` è già null-safe alla stessa maniera)."""
    quota = getattr(contract, "quota_stornata", 0) or 0
    return round(max((contract.prezzo_totale or 0) - netto_incassato(contract) - quota, 0.0), 2)


def netto_incassato(contract) -> float:
    """Incassato NETTO dei rimborsi (Strada B, FDM §9.5): versato − rimborsato, mai negativo.
    DERIVATO — il LORDO `totale_versato` resta immutabile (mai ridotto a ritroso); il rimborso da
    terminazione (G7) cresce `totale_rimborsato`. `getattr` default 0: oggi == totale_versato."""
    rimborsato = getattr(contract, "totale_rimborsato", 0) or 0
    return round(max((contract.totale_versato or 0) - rimborsato, 0.0), 2)


def is_saldato(contract) -> bool:
    """Sotto-stato denaro SALDATO ⟺ `residuo() == 0` con prezzo valido (FDM §5, NET-AWARE). NON
    `versato ≥ prezzo` (LORDO, G8.1.1/F4): su un contratto con rimborso il lordo può toccare il prezzo
    mentre il netto no → SALDATO/auto-close prematuro con `residuo() > 0` (violazione di `residuo == 0`
    su CHIUSO). Backward-compat: con `totale_rimborsato == 0` il netto == versato → identico al lordo."""
    return (contract.prezzo_totale or 0) > 0 and residuo(contract) <= 0.01


def residuo_credito(importo, consumato) -> float:
    """Residuo di un credito a saldo progressivo: `importo − consumato`, mai negativo (clamp).
    SSoT unico (G9.0c) dei due `computed_field` DTO finora duplicati: `crediti_terminazione`
    (receivable trainer, `consumato = importo_incassato`) e `crediti_cliente` (wallet, `consumato =
    importo_erogato`). Pura. `getattr`-friendly (None → 0). NON è il `residuo()` del contratto: i ledger
    di credito vivono FUORI da `residuo()` (G7.10/ADR-020)."""
    return round(max((importo or 0) - (consumato or 0), 0.0), 2)


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


def is_insolvente(state: ContractState) -> bool:
    """
    True se il contratto è scaduto (SOSPESO/ESAURITO) **E** ha rate scadute.
    Flag DERIVATO cross-asse, **NON** uno stato di vita (FDM §4): il modello
    resta a 4 stati + ELIMINATO. È il sotto-caso *scaduto* del segnale "denaro
    arretrato" (`rate_scadute`); su un ATTIVO con rate scadute si parla di
    "in ritardo", non di insolvenza. **Mutuamente esclusivo con `in_scadenza`**
    per costruzione (uno è scaduto, l'altro è ATTIVO-non-scaduto).
    Gemello di `is_rate_planificabile`/`is_residuo_incassabile_diretto`.
    Resa UI vincolante: SPEC_VOCABOLARIO_E_CLASSIFICAZIONE_CONTRATTI.md.
    """
    return state.lifecycle in (Lifecycle.SOSPESO, Lifecycle.ESAURITO) and state.rate_scadute


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


# ── Sotto-stato pagamento — SSoT unico (G8.2-prep, de-dup di 4 copie inline) ─────────

def recompute_stato_pagamento(contract) -> str:
    """SALDATO/PARZIALE/PENDENTE del contratto — UNICA derivazione (Audit Bug-3). NET-AWARE via
    `is_saldato()` (residuo()≤0.01, MAI `versato≥prezzo` lordo). Sostituisce le 4 copie inline
    (pay_rate/unpay_rate/incassa_residuo/reopen) **byte-identico**: dove `versato>0` per costruzione
    (post-pagamento) il ramo PENDENTE è semplicemente irraggiungibile, quindi l'ordine
    PENDENTE→SALDATO→PARZIALE coincide con tutte le varianti pre-esistenti."""
    if (contract.totale_versato or 0) <= 0:
        return "PENDENTE"
    if is_saldato(contract):
        return "SALDATO"
    return "PARZIALE"


# ── Fotografia netta cliente↔contratto (PASSO 1, G8.2-prep · ADR-019 D1 forma-d) ─────

@dataclass(frozen=True)
class PosizioneContrattoCliente:
    """Fotografia NETTA della posizione del cliente SU UN contratto: quanto ha dato netto di quanto ha
    riavuto, contando ANCHE il wallet erogato (cassa a livello cliente, `id_contratto=None`, ma nata
    da QUESTO contratto). Pura/additiva/zero-scrittura.

    È il **gradino PER-CONTRATTO** che abilita la posizione-cliente intera (G8.2) come estensione della
    stessa formula (Σ sui contratti del cliente), non una riscrittura. Modello billing-leader
    (Stripe/Chargebee): ledger immutabile, posizione RICALCOLATA, mai riavvolta.

    Con V=`totale_versato` (lordo, Strada B), Rf=`totale_rimborsato` (USCITA RIMBORSO id_contratto==C),
    Werog=Σ `importo_erogato` dei wallet `crediti_cliente` ANCORA VIVI (stato≠ANNULLATO) nati da C:
      restituito_al_cliente = Rf + Werog      # tutto il denaro tornato al cliente per questo contratto
      netto_cliente         = V − Rf − Werog  # posizione netta del cliente (può essere il punto di
                                              # partenza del residuo alla riapertura: residuo = P − netto)
    `Werog` esclude i wallet ANNULLATO: la loro erogazione, alla riapertura, viene RIASSORBITA in
    `totale_rimborsato` (PASSO 4) → contarla anche qui la sottrarrebbe due volte. È così che la
    fotografia resta INVARIANTE attraverso il reopen (chiude Bug-1 dell'audit)."""
    versato: float
    rimborsato_contratto: float
    wallet_erogato: float
    restituito_al_cliente: float
    netto_cliente: float


def posizione_netta_contratto(contract, crediti_cliente: Sequence = ()) -> PosizioneContrattoCliente:
    """Fotografia netta cliente↔contratto (PASSO 1). **PURA**: il caller fornisce i `crediti_cliente`
    del cliente (batch-fetch, anti-N+1); si filtra qui per `id_contratto_origine == contract.id`.
    Nessuna scrittura, nessuna tabella. `getattr` default-0/None: retro-compat coi contratti pre-G7."""
    v = round(contract.totale_versato or 0, 2)
    rf = round(getattr(contract, "totale_rimborsato", 0) or 0, 2)
    werog = round(sum(
        (getattr(c, "importo_erogato", 0) or 0)
        for c in crediti_cliente
        if getattr(c, "id_contratto_origine", None) == contract.id and getattr(c, "stato", None) != "ANNULLATO"
    ), 2)
    restituito = round(rf + werog, 2)
    return PosizioneContrattoCliente(
        versato=v,
        rimborsato_contratto=rf,
        wallet_erogato=werog,
        restituito_al_cliente=restituito,
        netto_cliente=round(v - restituito, 2),
    )


# ── Invarianti del dominio finanziario — checker osservabile (PASSO 2) ───────────────

@dataclass(frozen=True)
class InvariantViolation:
    code: str       # I1 | I4 | I5
    message: str


def assert_contract_invariants(
    contract,
    crediti_cliente: Sequence = (),
    *,
    rimborso_cassa_diretto: Optional[float] = None,
    rate_attive: Sequence = (),
) -> list[InvariantViolation]:
    """Verifica gli invarianti globali del dominio SU UN contratto, **SENZA** il mascheramento dei clamp
    `max(0,…)` (espone `netto_raw`/`residuo_raw`). **PURA**: il caller fornisce i `crediti_cliente`
    (per I5 = la fotografia netta del PASSO 1) e, se disponibile, `rimborso_cassa_diretto` =
    Σ USCITA RIMBORSO_CONTRATTO con `id_contratto == contract.id` (ancora ledger forte per I5).

    Ritorna la lista delle violazioni (vuota = OK). **'Predisposta per 409'**: i caller in produzione la
    invocano in coda alla mutazione e OGGI LOGGANO (warn); l'escalation a 409 è una scelta successiva.
    È la rete strutturale che chiude la CLASSE di bug (l'harness la usa su transizione × stato).

    Invarianti (FDM + audit):
      I1  `residuo()==0` su un contratto chiuso da settlement/completamento.
      I4  campi monotòni ≥ 0 e `netto_raw = versato − rimborsato` ≥ 0 (il clamp di `netto_incassato`
          maschererebbe l'over-rimborso Σuscita>Σentrata).
      I5  «nessun euro della fotografia netta sparisce»: la cassa-wallet già erogata e RIASSORBITA
          (wallet ANNULLATO nato da C) dev'essere coperta da `totale_rimborsato`. È verificabile SOLO
          grazie al PASSO 1 e cattura Bug-1 (al reopen il wallet erogato spariva dalla posizione).
      I6  (INV-RATE, ADR-021) su un contratto NON chiuso il piano rate è una PARTIZIONE del residuo:
          `Σ(previsto−saldato)` sulle rate attive non-saldate ≤ `residuo()`. L'eccedenza è denaro-fantasma
          (rata che esige più del dovuto). Richiede `rate_attive`; sotto-copertura = legittima."""
    violations: list[InvariantViolation] = []
    P = contract.prezzo_totale or 0
    V = contract.totale_versato or 0
    Rf = getattr(contract, "totale_rimborsato", 0) or 0
    Q = getattr(contract, "quota_stornata", 0) or 0
    netto_raw = round(V - Rf, 2)            # SENZA clamp (netto_incassato lo porterebbe a max(·,0))
    residuo_raw = round(P - netto_raw - Q, 2)  # SENZA clamp (residuo lo porterebbe a max(·,0))

    # I4 — campi non-negativi + netto onesto
    if V < -0.01:
        violations.append(InvariantViolation("I4", f"totale_versato negativo ({V:.2f})"))
    if Rf < -0.01:
        violations.append(InvariantViolation("I4", f"totale_rimborsato negativo ({Rf:.2f})"))
    if Q < -0.01:
        violations.append(InvariantViolation("I4", f"quota_stornata negativa ({Q:.2f})"))
    if netto_raw < -0.01:
        violations.append(InvariantViolation(
            "I4", f"netto incassato negativo ({netto_raw:.2f}): Σrimborso > Σentrata, il clamp lo nasconderebbe"))

    # I1 — chiuso da settlement/completamento ⇒ residuo() == 0 (residuo_raw non deve essere < 0: over-assorbimento)
    motivo = getattr(contract, "motivo_chiusura", None) or ""
    if getattr(contract, "chiuso", False) and (
        motivo.startswith("TERMINAZIONE_") or motivo in ("COMPLETAMENTO", "CONSUNZIONE")
    ):
        res = residuo(contract)
        if res > 0.01:
            violations.append(InvariantViolation("I1", f"contratto chiuso ({motivo}) con residuo {res:.2f} ≠ 0"))
        if residuo_raw < -0.01:
            violations.append(InvariantViolation(
                "I1", f"contratto chiuso ({motivo}) con residuo_raw {residuo_raw:.2f} < 0 (over-storno/over-rimborso)"))

    # I5 — fotografia netta: la cassa-wallet RIASSORBITA (wallet ANNULLATO nato da C) dev'essere coperta
    #      da totale_rimborsato. `importo_erogato` sopravvive all'ANNULLATO → la grandezza è stabile.
    werog_riassorbito = round(sum(
        (getattr(c, "importo_erogato", 0) or 0)
        for c in crediti_cliente
        if getattr(c, "id_contratto_origine", None) == contract.id and getattr(c, "stato", None) == "ANNULLATO"
    ), 2)
    if rimborso_cassa_diretto is not None:
        # Ancora ledger FORTE: totale_rimborsato == Σ USCITA RIMBORSO[id_contratto==C] + Σ erogato riassorbito.
        atteso = round((rimborso_cassa_diretto or 0) + werog_riassorbito, 2)
        if abs(Rf - atteso) > 0.01:
            violations.append(InvariantViolation(
                "I5",
                f"totale_rimborsato {Rf:.2f} ≠ rimborso diretto {rimborso_cassa_diretto or 0:.2f} + "
                f"wallet riassorbito {werog_riassorbito:.2f} (euro perso/duplicato attraverso una transizione)"))
    elif werog_riassorbito - Rf > 0.01:
        # Forma PURA (senza ledger): il wallet riassorbito non può eccedere il rimborso registrato.
        # Cattura Bug-1 quando NON c'è un rimborso diretto che lo mascheri (caso canonico del reopen).
        violations.append(InvariantViolation(
            "I5",
            f"wallet erogato riassorbito {werog_riassorbito:.2f} non coperto da totale_rimborsato {Rf:.2f}"
            f" (Bug-1: euro erogato perso alla riapertura)"))

    # I6 (INV-RATE, ADR-021) — su un contratto NON chiuso il piano rate è una PARTIZIONE del residuo:
    #   Σ(previsto − saldato) sulle rate attive non-saldate ≤ residuo(). L'ECCEDENZA è denaro-fantasma
    #   (una rata esige più del dovuto del contratto → contratto saldato con rata scaduta-fantasma). La
    #   SOTTO-copertura (Σ < residuo) è legittima ("da pianificare", F2-bis) e NON è una violazione.
    if not getattr(contract, "chiuso", False) and rate_attive:
        somma_residui_rate = round(sum(
            max((getattr(r, "importo_previsto", 0) or 0) - (getattr(r, "importo_saldato", 0) or 0), 0.0)
            for r in rate_attive
            if getattr(r, "stato", None) != "SALDATA" and getattr(r, "deleted_at", None) is None
        ), 2)
        res = residuo(contract)
        if somma_residui_rate - res > 0.01:
            violations.append(InvariantViolation(
                "I6",
                f"Σ residui-rata {somma_residui_rate:.2f} > residuo() {res:.2f}: il piano rate eccede il "
                f"dovuto (denaro-fantasma a livello rata)"))

    return violations

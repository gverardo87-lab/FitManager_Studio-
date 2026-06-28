"""
Test del modulo SSoT `api/services/contract_state.py`.

Copre i 4 quadranti dello stato di vita + i confini (FINANCIAL_DOMAIN_MODEL §3),
il sotto-stato denaro (§5) e il rollup cliente (§4.1). Funzioni pure → stub
leggeri via SimpleNamespace, nessun DB.
"""

import itertools
from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from api.services import contract_state as cs

TODAY = date(2026, 6, 20)


def _contract(
    *,
    chiuso=False,
    deleted_at=None,
    data_scadenza=None,
    crediti_totali=10,
    prezzo_totale=500.0,
    totale_versato=500.0,
):
    return SimpleNamespace(
        chiuso=chiuso,
        deleted_at=deleted_at,
        data_scadenza=data_scadenza,
        crediti_totali=crediti_totali,
        prezzo_totale=prezzo_totale,
        totale_versato=totale_versato,
    )


def _rate(stato="PENDENTE", previsto=100.0, saldato=0.0, scadenza=None):
    return SimpleNamespace(
        stato=stato,
        importo_previsto=previsto,
        importo_saldato=saldato,
        data_scadenza=scadenza,
    )


# ── Giunzione _as_date: ramo-stringa (diventa caldo al Blocco 2, dashboard raw-SQL) ──

def test_as_date_parse_stringa_iso():
    assert cs._as_date("2026-06-20") == date(2026, 6, 20)  # raw-SQL SQLite → testo
    assert cs._as_date(date(2026, 6, 20)) == date(2026, 6, 20)  # ORM → identità
    assert cs._as_date(None) is None


# ── Costanti (§4.2) ────────────────────────────────────────────────

def test_costanti_dichiarate():
    assert cs.SOGLIA_IN_SCADENZA_GG == 30
    assert cs.SOGLIA_CHURN_GG == 90


# ── crediti_residui / residuo ──────────────────────────────────────

def test_crediti_residui_clamp_non_negativo():
    c = _contract(crediti_totali=10)
    assert cs.crediti_residui(c, 3) == 7
    assert cs.crediti_residui(c, 10) == 0
    assert cs.crediti_residui(c, 15) == 0  # mai negativo


def test_crediti_residui_totali_none():
    c = _contract(crediti_totali=None)
    assert cs.crediti_residui(c, 0) == 0


def test_residuo_clamp_e_round():
    assert cs.residuo(_contract(prezzo_totale=500.0, totale_versato=200.0)) == 300.0
    assert cs.residuo(_contract(prezzo_totale=500.0, totale_versato=500.0)) == 0.0
    # versato > prezzo (overpayment) → mai negativo
    assert cs.residuo(_contract(prezzo_totale=500.0, totale_versato=520.0)) == 0.0
    assert cs.residuo(_contract(prezzo_totale=100.0, totale_versato=33.333)) == 66.67


# ── G7.1: residuo esteso con quota_stornata + netto_incassato (getattr default 0) ──

def test_residuo_default_senza_quota_stornata():
    """Byte-invarianza: senza il campo (SimpleNamespace) → getattr default 0 → formula pre-G7."""
    c = _contract(prezzo_totale=1000.0, totale_versato=200.0)
    assert not hasattr(c, "quota_stornata")
    assert cs.residuo(c) == 800.0


def test_residuo_sottrae_quota_stornata():
    c = SimpleNamespace(prezzo_totale=1000.0, totale_versato=200.0, quota_stornata=800.0)
    assert cs.residuo(c) == 0.0  # 1000 − 200 − 800
    c2 = SimpleNamespace(prezzo_totale=1000.0, totale_versato=200.0, quota_stornata=500.0)
    assert cs.residuo(c2) == 300.0
    # storno che eccede → clamp a 0, mai negativo
    c3 = SimpleNamespace(prezzo_totale=1000.0, totale_versato=200.0, quota_stornata=9999.0)
    assert cs.residuo(c3) == 0.0


def test_netto_incassato():
    # default (nessun rimborso) → == totale_versato
    assert cs.netto_incassato(_contract(totale_versato=1000.0)) == 1000.0
    # con rimborso → versato − rimborsato
    assert cs.netto_incassato(SimpleNamespace(totale_versato=1000.0, totale_rimborsato=300.0)) == 700.0
    # mai negativo
    assert cs.netto_incassato(SimpleNamespace(totale_versato=100.0, totale_rimborsato=250.0)) == 0.0


# ── G8.1 (ADR-019): residuo NET-AWARE — sottrae (versato − rimborsato), non il versato lordo ──

@pytest.mark.parametrize("prezzo,versato,quota", [
    (500.0, 200.0, 0.0),
    (500.0, 500.0, 0.0),
    (500.0, 520.0, 0.0),       # overpayment → clamp a 0
    (1000.0, 200.0, 800.0),    # storno pieno → 0
    (1000.0, 200.0, 500.0),    # storno parziale
    (100.0, 33.333, 0.0),      # arrotondamento a 2 decimali
    (750.0, 0.0, 0.0),         # nessun versamento
])
def test_residuo_net_aware_byte_identico_senza_rimborso(prezzo, versato, quota):
    """AC-1 (G8.1): con `totale_rimborsato == 0` il net-aware è BYTE-IDENTICO al lordo pre-G8.1,
    sia con la colonna esplicita a 0 sia ASSENTE (getattr default 0). Griglia di contratti reali."""
    lordo_atteso = round(max(prezzo - versato - quota, 0.0), 2)
    c_zero = SimpleNamespace(prezzo_totale=prezzo, totale_versato=versato,
                             totale_rimborsato=0.0, quota_stornata=quota)
    assert cs.residuo(c_zero) == lordo_atteso
    c_absent = SimpleNamespace(prezzo_totale=prezzo, totale_versato=versato, quota_stornata=quota)
    assert not hasattr(c_absent, "totale_rimborsato")
    assert cs.residuo(c_absent) == lordo_atteso


def test_residuo_net_aware_include_rimborso_che_resta():
    """AC-2 (G8.1): un rimborso che «resta» su un contratto APERTO (post-reopen, ADR-019) alza il
    residuo attraverso il netto: `residuo = prezzo − (versato − rimborsato) − storno`. Il cliente ha
    riavuto denaro → deve di più."""
    # P=1000, versato 1000, rimborsato 300, storno 0 → netto 700 → residuo 300
    c = SimpleNamespace(prezzo_totale=1000.0, totale_versato=1000.0,
                        totale_rimborsato=300.0, quota_stornata=0.0)
    assert cs.netto_incassato(c) == 700.0
    assert cs.residuo(c) == 300.0
    # con storno residuo: 1000 − (1000−300) − 100 = 200
    c2 = SimpleNamespace(prezzo_totale=1000.0, totale_versato=1000.0,
                         totale_rimborsato=300.0, quota_stornata=100.0)
    assert cs.residuo(c2) == 200.0
    # rimborso che porterebbe il netto sotto zero → netto clampato a 0 → residuo = prezzo intero
    c3 = SimpleNamespace(prezzo_totale=500.0, totale_versato=200.0,
                         totale_rimborsato=250.0, quota_stornata=0.0)
    assert cs.netto_incassato(c3) == 0.0   # max(200−250, 0)
    assert cs.residuo(c3) == 500.0         # max(500−0−0, 0)


# ── Stato di vita: 4 quadranti + confini (§3) ──────────────────────

def test_lifecycle_eliminato_precede_tutto():
    c = _contract(deleted_at=date(2026, 1, 1), chiuso=True)
    assert cs.contract_lifecycle(c, 0, TODAY) == cs.Lifecycle.ELIMINATO


def test_lifecycle_chiuso():
    # chiuso vince su scaduto/crediti
    c = _contract(chiuso=True, data_scadenza=TODAY - timedelta(days=10), crediti_totali=10)
    assert cs.contract_lifecycle(c, 0, TODAY) == cs.Lifecycle.CHIUSO


def test_lifecycle_attivo_vigente():
    c = _contract(data_scadenza=TODAY + timedelta(days=30))
    assert cs.contract_lifecycle(c, 5, TODAY) == cs.Lifecycle.ATTIVO


def test_lifecycle_attivo_scadenza_nulla():
    # scadenza assente = vigente a tempo indeterminato
    c = _contract(data_scadenza=None)
    assert cs.contract_lifecycle(c, 5, TODAY) == cs.Lifecycle.ATTIVO


def test_lifecycle_confine_scade_oggi_e_attivo():
    # "scade oggi" è ancora ATTIVO (vigente fino a fine giornata)
    c = _contract(data_scadenza=TODAY)
    assert cs.contract_lifecycle(c, 5, TODAY) == cs.Lifecycle.ATTIVO


def test_lifecycle_sospeso_scaduto_con_crediti():
    # scaduto per data MA sedute prepagate residue → SOSPESO (caso Paola/Merchiori)
    c = _contract(data_scadenza=TODAY - timedelta(days=1), crediti_totali=20)
    assert cs.contract_lifecycle(c, 2, TODAY) == cs.Lifecycle.SOSPESO


def test_lifecycle_esaurito_scaduto_senza_crediti():
    c = _contract(data_scadenza=TODAY - timedelta(days=1), crediti_totali=10)
    assert cs.contract_lifecycle(c, 10, TODAY) == cs.Lifecycle.ESAURITO


# ── is_in_scadenza ─────────────────────────────────────────────────

def test_in_scadenza_entro_soglia():
    c = _contract(data_scadenza=TODAY + timedelta(days=15))
    assert cs.is_in_scadenza(c, TODAY) is True


def test_in_scadenza_oltre_soglia():
    c = _contract(data_scadenza=TODAY + timedelta(days=45))
    assert cs.is_in_scadenza(c, TODAY) is False


def test_in_scadenza_gia_scaduto_falso():
    c = _contract(data_scadenza=TODAY - timedelta(days=1))
    assert cs.is_in_scadenza(c, TODAY) is False


# ── Sotto-stato denaro (§5) ────────────────────────────────────────

def test_money_saldato():
    c = _contract(prezzo_totale=500.0, totale_versato=500.0)
    assert cs.money_substate(c, []) == cs.MoneySubstate.SALDATO


def test_money_da_pianificare_zero_rate():
    c = _contract(prezzo_totale=500.0, totale_versato=200.0)
    assert cs.money_substate(c, []) == cs.MoneySubstate.DA_PIANIFICARE


def test_money_pianificato_rate_coprono_residuo():
    c = _contract(prezzo_totale=500.0, totale_versato=200.0)
    rates = [_rate(previsto=150.0), _rate(previsto=150.0)]  # 300 = residuo
    assert cs.money_substate(c, rates) == cs.MoneySubstate.PIANIFICATO


def test_money_parziale_rate_non_coprono():
    c = _contract(prezzo_totale=500.0, totale_versato=200.0)
    rates = [_rate(previsto=100.0)]  # 100 < 300
    assert cs.money_substate(c, rates) == cs.MoneySubstate.PARZIALE


def test_money_ignora_rate_saldate():
    c = _contract(prezzo_totale=500.0, totale_versato=200.0)
    rates = [_rate(stato="SALDATA", previsto=300.0)]  # saldata non conta come piano residuo
    assert cs.money_substate(c, rates) == cs.MoneySubstate.DA_PIANIFICARE


# ── has_rate_scadute ───────────────────────────────────────────────

def test_rate_scadute_true():
    rates = [_rate(scadenza=TODAY - timedelta(days=1))]
    assert cs.has_rate_scadute(rates, TODAY) is True


def test_rate_scadute_false_futura_o_saldata():
    rates = [
        _rate(scadenza=TODAY + timedelta(days=5)),
        _rate(stato="SALDATA", scadenza=TODAY - timedelta(days=10)),
    ]
    assert cs.has_rate_scadute(rates, TODAY) is False


# ── Rollup cliente (§4.1) ──────────────────────────────────────────

def test_engaged_con_attivo():
    assert cs.is_engaged([cs.Lifecycle.CHIUSO, cs.Lifecycle.ATTIVO]) is True


def test_engaged_con_sospeso():
    # il sospeso conta: gli devi ancora sedute
    assert cs.is_engaged([cs.Lifecycle.CHIUSO, cs.Lifecycle.SOSPESO]) is True


def test_non_engaged_solo_terminali():
    assert cs.is_engaged([cs.Lifecycle.CHIUSO, cs.Lifecycle.ESAURITO]) is False


def test_engagement_ingaggiato_vince():
    lf = [cs.Lifecycle.ATTIVO]
    assert cs.client_engagement(lf, giorni_lapse=999, giorni_ultimo_contatto=999) == cs.ClientEngagement.INGAGGIATO


def test_engagement_lapsed_caldo_entro_churn():
    lf = [cs.Lifecycle.ESAURITO]
    assert cs.client_engagement(lf, giorni_lapse=30, giorni_ultimo_contatto=10) == cs.ClientEngagement.LAPSED_CALDO


def test_engagement_lapsed_freddo_oltre_churn_senza_contatto():
    lf = [cs.Lifecycle.CHIUSO]
    assert cs.client_engagement(lf, giorni_lapse=120, giorni_ultimo_contatto=None) == cs.ClientEngagement.LAPSED_FREDDO


def test_engagement_lapsed_caldo_se_contatto_recente():
    # lapse oltre soglia MA contatto recente → ancora caldo (decadimento asimmetrico §4.1)
    lf = [cs.Lifecycle.CHIUSO]
    assert cs.client_engagement(lf, giorni_lapse=120, giorni_ultimo_contatto=10) == cs.ClientEngagement.LAPSED_CALDO


# ── Aggregato evaluate_contract ────────────────────────────────────

def test_evaluate_contract_sospeso_con_residuo():
    c = _contract(
        data_scadenza=TODAY - timedelta(days=5),
        crediti_totali=20,
        prezzo_totale=500.0,
        totale_versato=300.0,
    )
    rates = [_rate(scadenza=TODAY - timedelta(days=2))]
    st = cs.evaluate_contract(c, 2, rates, TODAY)
    assert st.lifecycle == cs.Lifecycle.SOSPESO
    assert st.crediti_residui == 18
    assert st.residuo == 200.0
    assert st.rate_scadute is True
    assert st.in_scadenza is False  # solo ATTIVO può essere in scadenza


def test_evaluate_contract_attivo_in_scadenza():
    c = _contract(data_scadenza=TODAY + timedelta(days=10), prezzo_totale=500.0, totale_versato=500.0)
    st = cs.evaluate_contract(c, 0, [], TODAY)
    assert st.lifecycle == cs.Lifecycle.ATTIVO
    assert st.in_scadenza is True
    assert st.money == cs.MoneySubstate.SALDATO


# ── Mutua esclusività esaustiva (16 combinazioni → 1 solo stato, zero buchi) ──
# È il test che avrebbe preso il difetto SOSPESO alla scrittura, non sul dato reale.

def _expected_lifecycle(*, chiuso, scaduto, crediti_pos, deleted):
    if deleted:
        return cs.Lifecycle.ELIMINATO
    if chiuso:
        return cs.Lifecycle.CHIUSO
    if scaduto:
        return cs.Lifecycle.SOSPESO if crediti_pos else cs.Lifecycle.ESAURITO
    return cs.Lifecycle.ATTIVO


@pytest.mark.parametrize(
    "chiuso,scaduto,crediti_pos,deleted",
    list(itertools.product([False, True], repeat=4)),
)
def test_lifecycle_mutua_esclusivita_esaustiva(chiuso, scaduto, crediti_pos, deleted):
    c = _contract(
        chiuso=chiuso,
        deleted_at=date(2026, 1, 1) if deleted else None,
        data_scadenza=(TODAY - timedelta(days=1)) if scaduto else (TODAY + timedelta(days=30)),
        crediti_totali=10,
    )
    crediti_usati = 0 if crediti_pos else 10  # residui >0 vs ==0
    got = cs.contract_lifecycle(c, crediti_usati, TODAY)
    expected = _expected_lifecycle(
        chiuso=chiuso, scaduto=scaduto, crediti_pos=crediti_pos, deleted=deleted
    )
    assert got == expected, f"combo({chiuso=},{scaduto=},{crediti_pos=},{deleted=}) → {got}, atteso {expected}"


def test_lifecycle_copre_tutte_le_16_combinazioni():
    # invariante di copertura: ogni combo produce esattamente uno stato definito
    stati = {
        cs.contract_lifecycle(
            _contract(
                chiuso=chiuso,
                deleted_at=date(2026, 1, 1) if deleted else None,
                data_scadenza=(TODAY - timedelta(days=1)) if scaduto else (TODAY + timedelta(days=30)),
                crediti_totali=10,
            ),
            0 if crediti_pos else 10,
            TODAY,
        )
        for chiuso, scaduto, crediti_pos, deleted in itertools.product([False, True], repeat=4)
    }
    assert stati <= set(cs.Lifecycle)  # nessuno stato "fantasma"
    assert stati == {
        cs.Lifecycle.ATTIVO,
        cs.Lifecycle.SOSPESO,
        cs.Lifecycle.ESAURITO,
        cs.Lifecycle.CHIUSO,
        cs.Lifecycle.ELIMINATO,
    }


# ── Confine is_in_scadenza attraverso il 31 dicembre (aritmetica ordinale) ────

def test_in_scadenza_attraverso_capodanno():
    capodanno_today = date(2026, 12, 20)
    # 21 giorni, scavalca il 31/12 → in scadenza
    assert cs.is_in_scadenza(_contract(data_scadenza=date(2027, 1, 10)), capodanno_today) is True
    # 47 giorni oltre l'anno → NON in scadenza
    assert cs.is_in_scadenza(_contract(data_scadenza=date(2027, 2, 5)), capodanno_today) is False


def test_in_scadenza_confine_esatto_30gg_cross_year():
    today = date(2026, 12, 31)
    # +30 giorni esatti (inclusivo) → True
    assert cs.is_in_scadenza(_contract(data_scadenza=date(2027, 1, 30)), today) is True
    # +31 giorni → fuori soglia → False
    assert cs.is_in_scadenza(_contract(data_scadenza=date(2027, 1, 31)), today) is False


# ── Helper di consumo: money mai letto isolato da lifecycle ───────────────────

def test_is_rate_planificabile_solo_attivo():
    attivo = cs.evaluate_contract(
        _contract(data_scadenza=TODAY + timedelta(days=30), prezzo_totale=500.0, totale_versato=200.0),
        0, [], TODAY,
    )
    assert attivo.money == cs.MoneySubstate.DA_PIANIFICARE
    assert cs.is_rate_planificabile(attivo) is True


def test_is_rate_planificabile_falso_su_scaduto_con_residuo():
    # SOSPESO con residuo: money è DA_PIANIFICARE ma NON è rateizzabile (G1)
    sospeso = cs.evaluate_contract(
        _contract(data_scadenza=TODAY - timedelta(days=5), crediti_totali=20,
                  prezzo_totale=500.0, totale_versato=200.0),
        2, [], TODAY,
    )
    assert sospeso.lifecycle == cs.Lifecycle.SOSPESO
    assert sospeso.money == cs.MoneySubstate.DA_PIANIFICARE  # ambiguo se letto da solo
    assert cs.is_rate_planificabile(sospeso) is False  # difesa SSoT
    assert cs.is_residuo_incassabile_diretto(sospeso) is True  # via G6


def test_is_residuo_incassabile_falso_su_attivo_e_saldato():
    attivo = cs.evaluate_contract(
        _contract(data_scadenza=TODAY + timedelta(days=30), prezzo_totale=500.0, totale_versato=200.0),
        0, [], TODAY,
    )
    assert cs.is_residuo_incassabile_diretto(attivo) is False  # ATTIVO → si rateizza, non si forza
    esaurito_saldato = cs.evaluate_contract(
        _contract(data_scadenza=TODAY - timedelta(days=5), crediti_totali=10,
                  prezzo_totale=500.0, totale_versato=500.0),
        10, [], TODAY,
    )
    assert esaurito_saldato.lifecycle == cs.Lifecycle.ESAURITO
    assert cs.is_residuo_incassabile_diretto(esaurito_saldato) is False  # niente residuo


# ── is_insolvente (AC-1) + esclusività mutua con in_scadenza (AC-2b) ──────────
# SPEC_VOCABOLARIO §2.1: insolvente = lifecycle∈{SOSPESO,ESAURITO} AND rate_scadute.

def _eval(*, scaduto, crediti_pos, chiuso=False, rata_scaduta=False, in_scadenza_window=False,
          prezzo=500.0, versato=300.0):
    if in_scadenza_window:
        ds = TODAY + timedelta(days=10)       # ATTIVO entro soglia
    elif scaduto:
        ds = TODAY - timedelta(days=5)         # scaduto
    else:
        ds = TODAY + timedelta(days=200)       # ATTIVO oltre soglia
    c = _contract(
        chiuso=chiuso,
        data_scadenza=ds,
        crediti_totali=20 if crediti_pos else 10,
        prezzo_totale=prezzo,
        totale_versato=versato,
    )
    crediti_usati = 2 if crediti_pos else 10   # residui >0 vs ==0
    rates = [_rate(scadenza=TODAY - timedelta(days=2))] if rata_scaduta else []
    return cs.evaluate_contract(c, crediti_usati, rates, TODAY)


def test_is_insolvente_esaurito_con_rata_scaduta():
    st = _eval(scaduto=True, crediti_pos=False, rata_scaduta=True)
    assert st.lifecycle == cs.Lifecycle.ESAURITO
    assert cs.is_insolvente(st) is True


def test_is_insolvente_falso_su_attivo_con_rata_scaduta():
    # ATTIVO con rata arretrata = "in ritardo", NON insolvente (non è scaduto, §2.1)
    st = _eval(scaduto=False, crediti_pos=True, rata_scaduta=True)
    assert st.lifecycle == cs.Lifecycle.ATTIVO
    assert st.rate_scadute is True
    assert cs.is_insolvente(st) is False


def test_is_insolvente_falso_su_sospeso_senza_rate_scadute():
    st = _eval(scaduto=True, crediti_pos=True, rata_scaduta=False)
    assert st.lifecycle == cs.Lifecycle.SOSPESO
    assert cs.is_insolvente(st) is False


def test_is_insolvente_falso_su_chiuso():
    st = _eval(scaduto=True, crediti_pos=False, chiuso=True, rata_scaduta=True)
    assert st.lifecycle == cs.Lifecycle.CHIUSO
    assert cs.is_insolvente(st) is False


@pytest.mark.parametrize(
    "scaduto,crediti_pos,chiuso,rata_scaduta,in_scadenza_window",
    list(itertools.product([False, True], repeat=5)),
)
def test_is_insolvente_in_scadenza_mutuamente_esclusivi(
    scaduto, crediti_pos, chiuso, rata_scaduta, in_scadenza_window
):
    # AC-2b: per OGNI combinazione, mai entrambi True (uno scaduto, l'altro ATTIVO-non-scaduto)
    st = _eval(scaduto=scaduto, crediti_pos=crediti_pos, chiuso=chiuso,
               rata_scaduta=rata_scaduta, in_scadenza_window=in_scadenza_window)
    assert not (cs.is_insolvente(st) and st.in_scadenza)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Test del modulo SSoT `api/services/contract_state.py`.

Copre i 4 quadranti dello stato di vita + i confini (FINANCIAL_DOMAIN_MODEL §3),
il sotto-stato denaro (§5) e il rollup cliente (§4.1). Funzioni pure → stub
leggeri via SimpleNamespace, nessun DB.
"""

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Test del modulo SSoT `api/services/cash_categories.py` (Prereq P0).

Predicato "movimento contrattuale" bidirezionale (TASSONOMIA §2/§7): IN (acconto/rata) /
OUT (rimborso) / non-contrattuale. Funzioni pure → nessun DB.
"""

from api.services import cash_categories as cc


def test_costanti_valori_canonici():
    assert cc.CATEGORIA_ACCONTO_CONTRATTO == "ACCONTO_CONTRATTO"
    assert cc.CATEGORIA_PAGAMENTO_RATA == "PAGAMENTO_RATA"
    assert cc.CATEGORIA_RIMBORSO_CONTRATTO == "RIMBORSO_CONTRATTO"
    assert cc.CATEGORIA_STORNO_SPESA_FISSA == "STORNO_SPESA_FISSA"


def test_set_in_out_disgiunti():
    assert cc.CONTRACT_CASH_IN == {"ACCONTO_CONTRATTO", "PAGAMENTO_RATA"}
    assert cc.CONTRACT_CASH_OUT == {"RIMBORSO_CONTRATTO"}
    assert cc.CONTRACT_CASH_IN.isdisjoint(cc.CONTRACT_CASH_OUT)  # nessuna categoria è IN e OUT
    assert cc.CONTRACT_CASH_CATEGORIES == cc.CONTRACT_CASH_IN | cc.CONTRACT_CASH_OUT


def test_is_contract_inflow():
    assert cc.is_contract_inflow("ACCONTO_CONTRATTO") is True
    assert cc.is_contract_inflow("PAGAMENTO_RATA") is True
    assert cc.is_contract_inflow("RIMBORSO_CONTRATTO") is False
    assert cc.is_contract_inflow("STORNO_SPESA_FISSA") is False
    assert cc.is_contract_inflow(None) is False


def test_is_contract_outflow():
    assert cc.is_contract_outflow("RIMBORSO_CONTRATTO") is True
    assert cc.is_contract_outflow("ACCONTO_CONTRATTO") is False
    assert cc.is_contract_outflow("Affitto") is False
    assert cc.is_contract_outflow(None) is False


def test_is_contract_movement():
    for cat in ("ACCONTO_CONTRATTO", "PAGAMENTO_RATA", "RIMBORSO_CONTRATTO"):
        assert cc.is_contract_movement(cat) is True
    assert cc.is_contract_movement("STORNO_SPESA_FISSA") is False  # storno spesa NON è contrattuale
    assert cc.is_contract_movement("Altro") is False
    assert cc.is_contract_movement(None) is False


def test_signed_contractual_amount():
    assert cc.signed_contractual_amount("ACCONTO_CONTRATTO", 100.0) == 100.0   # IN: +
    assert cc.signed_contractual_amount("PAGAMENTO_RATA", 50.0) == 50.0        # IN: +
    assert cc.signed_contractual_amount("RIMBORSO_CONTRATTO", 30.0) == -30.0   # OUT: −
    assert cc.signed_contractual_amount("Affitto", 200.0) == 0.0              # non contrattuale: 0
    assert cc.signed_contractual_amount(None, 99.0) == 0.0

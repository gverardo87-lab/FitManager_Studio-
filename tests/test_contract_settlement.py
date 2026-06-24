"""
Test del modulo puro `api/services/contract_settlement.py` (G7.1).

Conguaglio di terminazione su BASE SEDUTE, policy-pluggable. Funzioni pure → zero DB.
La *valorizzazione* (`valore_servizio_reso`) è PROVISIONAL (policy-gated, tributarista); la
*meccanica* (conguaglio firmato → esito) è quella verificata qui. Nessuna scrittura: G7.3 tradurrà
il Settlement in movimenti/colonne.
"""

import pytest

from api.services import contract_settlement as st


# ── valore_servizio_reso (pro_sedute, PROVISIONAL) ─────────────────


def test_valore_pro_sedute_lineare():
    # prezzo 1000, 10 crediti, 4 sedute erogate → 1000 * 4/10 = 400
    assert st.valore_servizio_reso(4, 1000.0, 10) == 400.0
    assert st.valore_servizio_reso(0, 1000.0, 10) == 0.0
    assert st.valore_servizio_reso(10, 1000.0, 10) == 1000.0


def test_valore_cap_a_prezzo():
    # sedute > crediti (anomalia) → cappato a prezzo, mai oltre il venduto
    assert st.valore_servizio_reso(15, 1000.0, 10) == 1000.0


def test_valore_senza_crediti_tutto_reso():
    # contratto a denaro senza monte-sedute → il pro-sedute non si applica → tutto reso
    assert st.valore_servizio_reso(0, 1000.0, None) == 1000.0
    assert st.valore_servizio_reso(0, 1000.0, 0) == 1000.0


def test_valore_arrotondato():
    # 1000 * 1/3 = 333.33...
    assert st.valore_servizio_reso(1, 1000.0, 3) == 333.33


def test_policy_mode_non_supportato():
    with pytest.raises(ValueError):
        st.valore_servizio_reso(1, 100.0, 2, st.SettlementPolicy(mode="pro_tempo"))


# ── compute_settlement: i tre esiti ────────────────────────────────


def test_settlement_rimborso():
    """versato (600) > reso (400) → RIMBORSO di 200; storno = residuo corrente."""
    s = st.compute_settlement(
        sedute_erogate=4, prezzo_totale=1000.0, crediti_totali=10,
        totale_versato=600.0, residuo_corrente=400.0,
    )
    assert s.esito == st.SettlementEsito.RIMBORSO
    assert s.valore_servizio_reso == 400.0
    assert s.conguaglio == -200.0
    assert s.importo_rimborso == 200.0
    assert s.quota_da_stornare == 400.0
    assert s.sedute_erogate == 4


def test_settlement_saldo_a_perdere():
    """versato (300) < reso (400) → SALDO_A_PERDERE: nessun rimborso, write-off del residuo."""
    s = st.compute_settlement(
        sedute_erogate=4, prezzo_totale=1000.0, crediti_totali=10,
        totale_versato=300.0, residuo_corrente=700.0,
    )
    assert s.esito == st.SettlementEsito.SALDO_A_PERDERE
    assert s.conguaglio == 100.0
    assert s.importo_rimborso == 0.0
    assert s.quota_da_stornare == 700.0


def test_settlement_nullo():
    """versato == reso → NULLO (nessun rimborso); il residuo resta da stornare se >0."""
    s = st.compute_settlement(
        sedute_erogate=4, prezzo_totale=1000.0, crediti_totali=10,
        totale_versato=400.0, residuo_corrente=600.0,
    )
    assert s.esito == st.SettlementEsito.NULLO
    assert s.importo_rimborso == 0.0
    assert s.quota_da_stornare == 600.0


def test_settlement_quota_da_stornare_mai_negativa():
    s = st.compute_settlement(
        sedute_erogate=10, prezzo_totale=1000.0, crediti_totali=10,
        totale_versato=1000.0, residuo_corrente=0.0,
    )
    assert s.quota_da_stornare == 0.0
    assert s.esito == st.SettlementEsito.NULLO  # reso 1000 == versato 1000


def test_motivo_chiusura_enum_a_quattro():
    """SPEC_G7.0 §2: enum chiuso a 4. Stessi valori scritti dalla marcatura G7.0."""
    assert {m.value for m in st.MotivoChiusura} == {
        "COMPLETAMENTO", "CONSUNZIONE", "TERMINAZIONE_RIMBORSO", "TERMINAZIONE_DECADENZA"
    }

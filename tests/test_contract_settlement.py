"""
Test del modulo puro `api/services/contract_settlement.py` (G7.1 + ADR-018).

Conguaglio di terminazione su BASE SEDUTE, policy-pluggable. Funzioni pure → zero DB.
La *valorizzazione* (`valore_servizio_reso`) è PROVISIONAL (policy-gated, tributarista); la
*meccanica* (conguaglio firmato → esito **balance-based**) è quella verificata qui. Nessuna scrittura:
G7.3/G7.9 tradurranno il Settlement in azione + movimenti/colonne.
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


# ── compute_settlement: i tre esiti balance-based (ADR-018) ────────


def test_settlement_credito_cliente():
    """versato (600) > reso (400) → CREDITO_CLIENTE: il trainer deve restituire 200 (rimborso)."""
    s = st.compute_settlement(
        sedute_erogate=4, prezzo_totale=1000.0, crediti_totali=10,
        totale_versato=600.0, residuo_corrente=400.0,
    )
    assert s.esito == st.SettlementEsito.CREDITO_CLIENTE
    assert s.valore_servizio_reso == 400.0
    assert s.conguaglio == -200.0
    assert s.credito_cliente == 200.0
    assert s.credito_trainer == 0.0
    assert s.quota_non_erogata == 600.0   # P − R = 1000 − 400
    assert s.residuo_pre == 400.0
    assert s.sedute_erogate == 4


def test_settlement_credito_trainer():
    """versato (300) < reso (400) → CREDITO_TRAINER: il cliente deve ancora 100 per servizio reso.
    Il modulo espone il FATTO (credito_trainer 100), MAI il write-off come default (ADR-018)."""
    s = st.compute_settlement(
        sedute_erogate=4, prezzo_totale=1000.0, crediti_totali=10,
        totale_versato=300.0, residuo_corrente=700.0,
    )
    assert s.esito == st.SettlementEsito.CREDITO_TRAINER
    assert s.conguaglio == 100.0
    assert s.credito_trainer == 100.0     # R − V = 400 − 300
    assert s.credito_cliente == 0.0
    assert s.quota_non_erogata == 600.0   # P − R = 1000 − 400 (storno legittimo)
    assert s.residuo_pre == 700.0         # P − V = 1000 − 300 = quota_non_erogata + credito_trainer


def test_settlement_pari():
    """versato == reso → PARI (nessun conguaglio); il residuo resta da stornare se >0."""
    s = st.compute_settlement(
        sedute_erogate=4, prezzo_totale=1000.0, crediti_totali=10,
        totale_versato=400.0, residuo_corrente=600.0,
    )
    assert s.esito == st.SettlementEsito.PARI
    assert s.credito_cliente == 0.0
    assert s.credito_trainer == 0.0
    assert s.residuo_pre == 600.0


def test_settlement_residuo_pre_mai_negativo():
    s = st.compute_settlement(
        sedute_erogate=10, prezzo_totale=1000.0, crediti_totali=10,
        totale_versato=1000.0, residuo_corrente=0.0,
    )
    assert s.residuo_pre == 0.0
    assert s.esito == st.SettlementEsito.PARI  # reso 1000 == versato 1000


def test_motivo_chiusura_enum():
    """SPEC_G7.0 §2 + ADR-018: 5 valori (aggiunto TERMINAZIONE_SALDO_TRAINER per il ramo trainer).
    DECADENZA resta nell'enum come legacy/storico ma non è più emesso da terminate su contratti vivi."""
    assert {m.value for m in st.MotivoChiusura} == {
        "COMPLETAMENTO", "CONSUNZIONE", "TERMINAZIONE_RIMBORSO",
        "TERMINAZIONE_SALDO_TRAINER", "TERMINAZIONE_DECADENZA",
    }


# ════════════════════════════════════════════════════════════════════
# SPEC_G7.1_COPERTURA_SETTLEMENT — presidio dei confini di esito + clamp.
#
# ⚠️ DELTA BRIDGE (verificato sul modulo, 2026-06-24 — il modulo vince):
# `compute_settlement` fa `conguaglio = round(reso − versato, arrotondamento=2)`, quindi il
# conguaglio è SEMPRE un multiplo di €0.01. Nessun multiplo di 0.01 vive negli intervalli aperti
# (−0.009, 0) o (0, 0.009): la "dead-zone" della tolleranza ±0.009 è IRRAGGIUNGIBILE — il ramo
# PARI è raggiungibile solo da `conguaglio == 0.00` (vedi test_settlement_pari). Perciò gli AC
# 1/2 non si costruiscono come scritti; il confine reale più stretto è ∓0.01. La tolleranza ±0.009
# è quindi inerte (il pre-rounding rimuove già il rumore di virgola che proteggerebbe). → questi
# test pinnano i CONFINI REALI (∓0.01) e uccidono comunque il mutante soglia 0.009→0.9 (che i casi
# −200/+100 non colgono). Se un giorno `arrotondamento` cambia o si passa a Decimal, ricalibrare.
# ════════════════════════════════════════════════════════════════════


def test_settlement_confine_minimo_credito_cliente():
    """Confine reale inferiore: conguaglio −0.01 → CREDITO_CLIENTE (€0.01). reso(4,1000,10)=400.00,
    versato=400.01 → round(400.00−400.01, 2) = −0.01 (multiplo di 0.01, il più vicino a 0 dal basso).
    UCCIDE il mutante soglia 0.009→0.9 (sotto −0.9 questo cadrebbe in PARI)."""
    s = st.compute_settlement(
        sedute_erogate=4, prezzo_totale=1000.0, crediti_totali=10,
        totale_versato=400.01, residuo_corrente=0.0,
    )
    assert s.conguaglio == -0.01
    assert s.esito == st.SettlementEsito.CREDITO_CLIENTE
    assert s.credito_cliente == 0.01


def test_settlement_confine_minimo_credito_trainer():
    """Confine reale superiore speculare: conguaglio +0.01 → CREDITO_TRAINER (€0.01 a favore del trainer).
    reso 400.00, versato=399.99 → +0.01. UCCIDE il mutante soglia sul ramo positivo."""
    s = st.compute_settlement(
        sedute_erogate=4, prezzo_totale=1000.0, crediti_totali=10,
        totale_versato=399.99, residuo_corrente=0.0,
    )
    assert s.conguaglio == 0.01
    assert s.esito == st.SettlementEsito.CREDITO_TRAINER
    assert s.credito_trainer == 0.01
    assert s.credito_cliente == 0.0


def test_settlement_residuo_pre_clampa_negativo():
    """AC-G7.1c-3: `residuo_pre = round(max(residuo_corrente, 0.0), 2)`. Con residuo_corrente
    < 0 (overpayment, residuo() clampa ma il caller potrebbe passare un grezzo) → 0.0, mai negativo.
    Esercita il `max(…, 0.0)` reale, che nessun altro test batte (tutti passano residuo ≥ 0)."""
    s = st.compute_settlement(
        sedute_erogate=4, prezzo_totale=1000.0, crediti_totali=10,
        totale_versato=400.0, residuo_corrente=-50.0,
    )
    assert s.residuo_pre == 0.0


def test_settlement_credito_cliente_frazionario():
    """Rimborso con importo NON intero (266.67): reso(1,1000,3)=333.33, versato=600 →
    conguaglio −266.67 → CREDITO_CLIENTE 266.67. Copre il percorso frazionario end-to-end."""
    s = st.compute_settlement(
        sedute_erogate=1, prezzo_totale=1000.0, crediti_totali=3,
        totale_versato=600.0, residuo_corrente=400.0,
    )
    assert s.valore_servizio_reso == 333.33
    assert s.conguaglio == -266.67
    assert s.esito == st.SettlementEsito.CREDITO_CLIENTE
    assert s.credito_cliente == 266.67


# ── L3 (G7.7-R6): property del tetto credito_cliente <= totale_versato ──


@pytest.mark.parametrize("erogate,prezzo,crediti,versato", [
    (0, 1000.0, 10, 1000.0), (2, 1000.0, 10, 500.0), (5, 1000.0, 10, 100.0),
    (10, 1000.0, 10, 0.0), (3, 500.0, 5, 700.0),         # overpayment (versato > prezzo)
    (1, 300.0, 0, 200.0), (0, 0.0, 0, 0.0),               # crediti=0 (tutto reso) / contratto vuoto
    (7, 1234.56, 13, 999.99),                             # frazionario
])
def test_l3_tetto_credito_cliente_le_versato(erogate, prezzo, crediti, versato):
    """L3 property (gap di copertura dall'audit): `credito_cliente <= totale_versato` per costruzione
    (reso >= 0 → max(versato − reso, 0) <= versato). Un refactor della formula del conguaglio che
    violasse il tetto (I3) passerebbe muto senza questo presidio su griglia (incl. overpayment e
    crediti=0). Tiene anche l'invariante speculare `credito_trainer == max(reso − versato, 0)`."""
    residuo = max(prezzo - versato, 0.0)
    s = st.compute_settlement(
        sedute_erogate=erogate, prezzo_totale=prezzo, crediti_totali=crediti,
        totale_versato=versato, residuo_corrente=residuo,
    )
    assert s.credito_cliente <= (versato or 0) + 1e-9   # TETTO (I3)
    assert s.credito_cliente >= 0.0
    assert s.credito_trainer >= 0.0
    # esattamente uno dei due crediti è non-nullo (o entrambi 0 = PARI)
    assert not (s.credito_cliente > 0.009 and s.credito_trainer > 0.009)
    assert s.residuo_pre >= 0.0
    assert s.quota_non_erogata >= 0.0
    assert s.valore_servizio_reso >= 0.0

"""G9.4-bis (ADR-022 Addendum II) — read-model della cassa: ClasseContabile + classify_cash_movement.

Il gemello di LETTURA della penna: il piano dei conti (6 classi) ha un nome e un'unica funzione che lo
implementa. AC-RM-1 totalità/fail-loud (bis.1) · AC-RM-2 esaustività alla nascita (bis.4) ·
AC-RM-3 no re-inline (bis.4). Convalidato sul crm.db reale: 218/218 movimenti, zero celle violate.
"""

import pytest

from api.services.cash_categories import (
    CATEGORIA_ACCONTO_CONTRATTO,
    CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO,
    CATEGORIA_PAGAMENTO_RATA,
    CATEGORIA_RIMBORSO_CONTRATTO,
    CATEGORIA_STORNO_SPESA_FISSA,
    CONTRACT_CASH_IN,
    CONTRACT_CASH_OUT,
    ClasseContabile,
    classify_cash_movement,
)


# ── AC-RM-1a: le 6 classi, una per cella della partizione strutturale ──────────

@pytest.mark.parametrize("tipo,categoria,idc,ids,attesa", [
    ("ENTRATA", CATEGORIA_ACCONTO_CONTRATTO, 1, None, ClasseContabile.RICAVO_CONTRATTUALE),
    ("ENTRATA", CATEGORIA_PAGAMENTO_RATA, 1, None, ClasseContabile.RICAVO_CONTRATTUALE),
    ("ENTRATA", CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO, 1, None, ClasseContabile.RICAVO_CONTRATTUALE),
    ("ENTRATA", "Vendita integratori", None, None, ClasseContabile.ALTRO_INCASSO),
    ("ENTRATA", None, None, None, ClasseContabile.ALTRO_INCASSO),
    ("ENTRATA", CATEGORIA_STORNO_SPESA_FISSA, None, 3, ClasseContabile.RETTIFICA_COSTO_FISSO),
    ("USCITA", CATEGORIA_RIMBORSO_CONTRATTO, 1, None, ClasseContabile.CONTRA_RICAVO),
    ("USCITA", CATEGORIA_RIMBORSO_CONTRATTO, None, None, ClasseContabile.CONTRA_RICAVO),  # erogazione wallet
    ("USCITA", "Affitto", None, 1, ClasseContabile.COSTO_FISSO),
    ("USCITA", "Trasporto", None, None, ClasseContabile.COSTO_VARIABILE),
    ("USCITA", None, None, None, ClasseContabile.COSTO_VARIABILE),
])
def test_ac_rm1_classificazione(tipo, categoria, idc, ids, attesa):
    assert classify_cash_movement(tipo, categoria, idc, ids) is attesa


# ── AC-RM-1b: fail-loud sulle celle strutturalmente vincolate (gemello della penna) ──

@pytest.mark.parametrize("tipo,categoria,idc,ids", [
    ("ENTRATA", "Vendita integratori", 1, None),      # ENTRATA su contratto con categoria fuori asse
    ("ENTRATA", CATEGORIA_RIMBORSO_CONTRATTO, 1, None),  # categoria OUT su una ENTRATA contrattuale
    ("ENTRATA", "Affitto", None, 3, ),                # ENTRATA su spesa che non è lo storno
    ("USCITA", "Trasporto", 1, None),                 # USCITA su contratto che non è rimborso
    ("USCITA", CATEGORIA_PAGAMENTO_RATA, 1, None),    # categoria IN su una USCITA contrattuale
    ("BONIFICO", "x", None, None),                    # tipo sconosciuto
])
def test_ac_rm1_fail_loud_celle_vincolate(tipo, categoria, idc, ids):
    with pytest.raises(ValueError):
        classify_cash_movement(tipo, categoria, idc, ids)


# ── AC-RM-2: esaustività alla nascita — ogni categoria del SSoT ha una classe ──

def test_ac_rm2_esaustivita_categorie_ssot():
    """Una categoria-costante nuova senza classe dichiarata = QUESTO test rosso il giorno della nascita
    (i test G7.5 sono gemelli di regressione: proteggono i membri noti, non scattano sui nuovi).
    Enumera le costanti del SSoT e le classifica nella loro cella strutturale naturale."""
    import api.services.cash_categories as cc
    costanti = {v for k, v in vars(cc).items() if k.startswith("CATEGORIA_") and isinstance(v, str)}
    assert costanti == CONTRACT_CASH_IN | CONTRACT_CASH_OUT | {CATEGORIA_STORNO_SPESA_FISSA}, (
        "Categoria-costante nuova rilevata: dichiarane la ClasseContabile in classify_cash_movement "
        "e aggiorna questo test (esaustività alla nascita, AC-RM-2)."
    )
    for cat in CONTRACT_CASH_IN:
        assert classify_cash_movement("ENTRATA", cat, 1, None) is ClasseContabile.RICAVO_CONTRATTUALE
    for cat in CONTRACT_CASH_OUT:
        assert classify_cash_movement("USCITA", cat, 1, None) is ClasseContabile.CONTRA_RICAVO
    assert classify_cash_movement(
        "ENTRATA", CATEGORIA_STORNO_SPESA_FISSA, None, 1
    ) is ClasseContabile.RETTIFICA_COSTO_FISSO


def test_ac_rm1_totalita_partizione():
    """Totalità per costruzione: ogni cella (tipo × FK-ness) con categoria libera ha SEMPRE una classe."""
    for ids in (None, 7):
        assert classify_cash_movement("USCITA", "qualunque-testo-libero", None, ids) in (
            ClasseContabile.COSTO_FISSO, ClasseContabile.COSTO_VARIABILE,
        )
    assert classify_cash_movement("ENTRATA", "qualunque-testo-libero", None, None) \
        is ClasseContabile.ALTRO_INCASSO


# ── AC-RM-5/6 (bis.3): nessun netto nudo — lo scenario dell'INC è spiegabile dalla response ──

def test_ac_rm6_scenario_inc_componenti_esposti(client, auth_headers, session):
    """Il caso reale dell'INC-2026-07-03 (luglio: 375 lordi, 515.42 rimborsi → entrate nette -140.42):
    la response da sola spiega il numero. Movimenti seminati via ORM (il write-guard blocca i manuali
    con categorie riservate; qui simuliamo i writer di sistema)."""
    from datetime import date
    from sqlmodel import select
    from api.models.movement import CashMovement
    from api.models.trainer import Trainer

    tid = session.exec(select(Trainer)).first().id
    anno, mese = 2027, 3                              # mese vuoto dedicato al test
    session.add(CashMovement(trainer_id=tid, tipo="ENTRATA", categoria="Extra",
                             importo=375.0, data_effettiva=date(anno, mese, 10), operatore="TEST"))
    session.add(CashMovement(trainer_id=tid, tipo="USCITA", categoria="RIMBORSO_CONTRATTO",
                             importo=515.42, data_effettiva=date(anno, mese, 12), operatore="TEST"))
    session.commit()

    r = client.get(f"/api/movements/stats?anno={anno}&mese={mese}", headers=auth_headers)
    assert r.status_code == 200, r.text
    stats = r.json()
    assert stats["totale_entrate"] == -140.42         # il netto (matematica esatta dell'INC)
    assert stats["entrate_lorde"] == 375.00           # ...ora SPIEGABILE dai componenti
    assert stats["rimborsi_contratti"] == 515.42
    assert stats["storno_fisse"] == 0.0


def test_ac_rm5_senza_rimborsi_componenti_neutri(client, auth_headers, session):
    """Con rimborsi = 0 i bucket sono neutri (la UI resta invariata: sub-label solo se rimborsi > 0)."""
    from datetime import date
    from sqlmodel import select
    from api.models.movement import CashMovement
    from api.models.trainer import Trainer
    tid = session.exec(select(Trainer)).first().id
    session.add(CashMovement(trainer_id=tid, tipo="ENTRATA", categoria="Extra",
                             importo=200.0, data_effettiva=date(2027, 4, 5), operatore="TEST"))
    session.commit()
    stats = client.get("/api/movements/stats?anno=2027&mese=4", headers=auth_headers).json()
    assert stats["totale_entrate"] == 200.0 == stats["entrate_lorde"]
    assert stats["rimborsi_contratti"] == 0.0

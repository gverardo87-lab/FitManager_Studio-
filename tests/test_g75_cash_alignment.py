"""
G7.5a — Allineamento delle query-cassa al rimborso da terminazione (RIMBORSO_CONTRATTO).

Un RIMBORSO_CONTRATTO è una USCITA **contra-ricavo** (specchio di STORNO_SPESA_FISSA): non deve
comportarsi come un costo operativo. Verifica le 3 query che altrimenti mentirebbero con un rimborso:
- get_movement_stats: escluso dalle uscite variabili + sottratto dalle entrate (single-treatment)
- get_dashboard_summary.monthly_revenue: al netto dei rimborsi del mese
- get_forecast: escluso dal burn variabile proiettato

Il rimborso è prodotto dall'endpoint reale `POST /terminate` (G7.3), datato via `data_chiusura`.
"""

from datetime import date, datetime, timedelta

from sqlmodel import select

from api.models.movement import CashMovement
from api.models.trainer import Trainer
from api.models.event import Event

TODAY = date.today()
FUTURE = (TODAY + timedelta(days=120)).isoformat()


def _trainer(session) -> Trainer:
    return session.exec(select(Trainer)).first()


def _contract(client, auth_headers, client_id, *, prezzo, acconto, crediti, inizio=None):
    # `inizio` (ISO str) opzionale: l'acconto è datato min(inizio, today) → con un inizio nel mese
    # scorso l'ENTRATA cade nel mese scorso. Default = oggi.
    body = {
        "id_cliente": client_id, "tipo_pacchetto": "Pkg", "crediti_totali": crediti,
        "prezzo_totale": prezzo, "data_inizio": inizio or TODAY.isoformat(),
        "data_scadenza": FUTURE, "acconto": acconto,
    }
    if acconto > 0:
        body["metodo_acconto"] = "CONTANTI"
    r = client.post("/api/contracts", json=body, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


def _complete_pt(session, trainer_id, client_id, contract_id, n):
    for i in range(n):
        session.add(Event(
            trainer_id=trainer_id, id_cliente=client_id, id_contratto=contract_id,
            categoria="PT", stato="Completato", titolo="Seduta",
            data_inizio=datetime(2026, 1, 1, 9 + i), data_fine=datetime(2026, 1, 1, 10 + i),
        ))
    session.commit()


def _terminate(client, auth_headers, contract_id, *, data_chiusura=None):
    body = {"metodo_rimborso": "CONTANTI"}
    if data_chiusura is not None:
        body["data_chiusura"] = data_chiusura
    r = client.post(f"/api/contracts/{contract_id}/terminate", json=body, headers=auth_headers)
    assert r.status_code == 200, r.text
    return r.json()


def _last_month_day():
    first_of_this = date(TODAY.year, TODAY.month, 1)
    last = first_of_this - timedelta(days=1)
    return date(last.year, last.month, 15)


# ── get_movement_stats: rimborso = contra-ricavo (escluso da uscite-var, sottratto da entrate) ──

def test_movement_stats_rimborso_contra_ricavo(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)  # reso 200 → rimborso 300
    _terminate(client, auth_headers, c["id"])  # data_chiusura=oggi → rimborso questo mese

    r = client.get(f"/api/movements/stats?anno={TODAY.year}&mese={TODAY.month}", headers=auth_headers)
    assert r.status_code == 200, r.text
    stats = r.json()
    # il rimborso NON è un costo operativo variabile
    assert stats["totale_uscite_variabili"] == 0.0
    # contra-ricavo: entrate = acconto 500 − rimborso 300 = 200 (netto)
    assert stats["totale_entrate"] == 200.0
    assert stats["margine_netto"] == 200.0


# ── monthly_revenue: al netto dei rimborsi del mese ──

def test_monthly_revenue_netto_dei_rimborsi(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)
    _terminate(client, auth_headers, c["id"])  # rimborso 300 questo mese

    r = client.get("/api/dashboard/summary", headers=auth_headers)
    assert r.status_code == 200, r.text
    # lordo = 500 (acconto, id_contratto set); netto = 500 − 300 rimborso = 200
    assert r.json()["monthly_revenue"] == 200.0


# ── get_forecast: il rimborso non gonfia il burn variabile proiettato ──

def test_forecast_burn_esclude_rimborso(client, auth_headers, sample_client, session):
    t = _trainer(session)
    mese_scorso = _last_month_day()
    # baseline: una USCITA variabile (categoria None) di 300 nel mese scorso
    session.add(CashMovement(
        trainer_id=t.id, data_effettiva=mese_scorso, tipo="USCITA",
        categoria=None, importo=300.0, id_spesa_ricorrente=None,
    ))
    session.commit()

    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)  # reso 200 → rimborso 300
    _terminate(client, auth_headers, c["id"], data_chiusura=mese_scorso.isoformat())  # rimborso 300 mese scorso

    r = client.get("/api/movements/forecast?mesi=3", headers=auth_headers)
    assert r.status_code == 200, r.text
    forecast = r.json()
    # uscite variabili stimate = media 3 mesi delle SOLE uscite variabili (rimborso ESCLUSO):
    # baseline 300 in un mese su 3 → 100. Senza esclusione sarebbe (300+300)/3 = 200.
    assert forecast["monthly_projection"][0]["uscite_variabili_stimate"] == 100.0


# ── get_financial_trend: contra-linea rimborsi_contratti (G7.5b) — incassi LORDI, cash flow NETTO ──

def test_financial_trend_rimborso_contra_line(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)  # reso 200 → rimborso 300
    _terminate(client, auth_headers, c["id"])  # rimborso 300 questo mese

    r = client.get("/api/movements/financial-trend?mesi=12", headers=auth_headers)
    assert r.status_code == 200, r.text
    trend = r.json()
    cur = next(p for p in trend["periodi"] if p["anno"] == TODAY.year and p["mese"] == TODAY.month)
    # incassi_contratti resta LORDO (acconto 500); il rimborso NON lo abbatte
    assert cur["incassi_contratti"] == 500.0
    # contra-linea separata + cash flow netto (500 − 300)
    assert cur["rimborsi_contratti"] == 300.0
    assert cur["cash_flow_reale"] == 200.0
    # BLOCKER-4: le decomposizioni restano LORDE (non toccate dal rimborso)
    assert cur["incassi_acconti"] == 500.0
    assert cur["incassi_nuovi"] == 500.0
    # totali
    assert trend["tot_rimborsi_contratti"] == 300.0
    assert trend["tot_cash_flow_reale"] == 200.0


# ── SENTINELLA (G7.5b): cash_flow_reale può andare NEGATIVO e NON va clampato a 0 ──

def test_financial_trend_cash_flow_negativo_non_clampato(client, auth_headers, sample_client):
    """SENTINELLA anti-regressione. `cash_flow_reale` PUÒ legittimamente essere NEGATIVO (un mese in cui
    i rimborsi superano gli incassi) e va mostrato ESATTO, mai clampato a 0: un mese in rosso deve poter
    esistere nella serie. Stessa perdita-silenziosa che BLOCKER-4 impedisce sull'asse decomposizioni, qui
    sull'asse del netto. Questo test diventa ROSSO se qualcuno introduce un `max(0, ...)` su cash_flow_reale.

    Verificato sul codice vivo: `get_financial_trend` NON clampa (movements.py: cash_flow_reale =
    round(c + a - rb, 2); tot = round(tot_c + tot_a - tot_rimborsi, 2)) → l'invariante è intatto.

    Costruzione (cap di dominio): un rimborso ≤ `netto_incassato` del suo contratto → un SINGOLO rimborso
    non può eccedere gli incassi del proprio mese. Per ottenere `rimborsi > incassi NELLA FINESTRA` serve
    che l'incasso del contratto rimborsato sia FUORI finestra: contratto B incassato il mese scorso,
    terminato questo mese, query `mesi=1` (finestra = solo mese corrente) → il rimborso entra, l'acconto no.
    Contratto A fornisce l'incasso LORDO del mese corrente (prova che il rimborso non lo abbatte, B-4).
    """
    last = _last_month_day().isoformat()

    # A: incasso 100 questo mese, NON terminato → incassi_contratti LORDO del mese corrente
    _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=100.0, crediti=10)
    # B: acconto 500 datato il mese SCORSO (data_inizio mese scorso), 0 sedute, terminato questo mese
    b = _contract(client, auth_headers, sample_client["id"],
                  prezzo=500.0, acconto=500.0, crediti=10, inizio=last)
    _terminate(client, auth_headers, b["id"])  # reso 0 → rimborso 500, datato oggi (questo mese)

    # Finestra = solo mese corrente: l'acconto 500 di B (mese scorso) è ESCLUSO, il suo rimborso 500 è incluso.
    r = client.get("/api/movements/financial-trend?mesi=1", headers=auth_headers)
    assert r.status_code == 200, r.text
    trend = r.json()
    assert len(trend["periodi"]) == 1
    cur = trend["periodi"][0]
    # incassi del mese = solo A (100); B incassò il mese scorso, fuori finestra
    assert cur["incassi_contratti"] == 100.0     # LORDO positivo — il rimborso 500 NON lo abbatte (B-4)
    assert cur["rimborsi_contratti"] == 500.0
    # cash_flow_reale = 100 − 500 = −400: NEGATIVO ed ESATTO, NON clampato a 0
    assert cur["cash_flow_reale"] == -400.0
    # totale finestra (un solo mese) coerente col netto negativo
    assert trend["tot_cash_flow_reale"] == -400.0

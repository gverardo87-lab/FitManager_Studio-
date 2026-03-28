#!/usr/bin/env python3
"""
Seed demo crm_dev.db — scenario realistico per demo investitore.

Popola via API (porta 8001) cosi' tutti i trigger, audit trail,
e integrity engine funzionano correttamente.

Usage:
    python tools/scripts/seed_demo_crm.py

Prerequisito: backend dev avviato su porta 8001.
"""

import sys
import os
import requests
from datetime import date, datetime, timedelta
import random

# Fix encoding Windows
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://localhost:8001/api"
TRAINER_EMAIL = "chiarabassani96@gmail.com"
TRAINER_PASSWORD = "Fitness2026!"
HEADERS = {}


def api(method, path, json=None, expected=None):
    """Helper HTTP con error handling."""
    url = f"{BASE}{path}"
    r = getattr(requests, method)(url, json=json, headers=HEADERS)
    if expected and r.status_code != expected:
        print(f"  ERRORE {method.upper()} {path}: {r.status_code} {r.text[:300]}")
        return None
    if r.status_code >= 400:
        print(f"  WARN {method.upper()} {path}: {r.status_code} {r.text[:200]}")
        return None
    return r.json() if r.text else None


def login_or_register():
    """Login col trainer dev, oppure registra se non esiste."""
    global HEADERS
    # Prova login
    r = requests.post(f"{BASE}/auth/login", json={
        "email": TRAINER_EMAIL,
        "password": TRAINER_PASSWORD,
    })
    if r.status_code == 200:
        token = r.json()["access_token"]
        HEADERS = {"Authorization": f"Bearer {token}"}
        print(f"[OK] Login come {TRAINER_EMAIL}")
        return

    # Prova setup (primo avvio)
    r = requests.post(f"{BASE}/auth/setup/create", json={
        "email": TRAINER_EMAIL,
        "password": TRAINER_PASSWORD,
        "nome": "Chiara",
        "cognome": "Bassani",
    })
    if r.status_code == 201:
        token = r.json()["access_token"]
        HEADERS = {"Authorization": f"Bearer {token}"}
        print(f"[OK] Setup trainer {TRAINER_EMAIL}")
        return

    # Prova register (fallback)
    r = requests.post(f"{BASE}/auth/register", json={
        "email": TRAINER_EMAIL,
        "password": TRAINER_PASSWORD,
        "nome": "Chiara",
        "cognome": "Bassani",
    })
    if r.status_code == 201:
        token = r.json()["access_token"]
        HEADERS = {"Authorization": f"Bearer {token}"}
        print(f"[OK] Registrato trainer {TRAINER_EMAIL}")
        return

    print(f"FATAL: impossibile autenticare. Status: {r.status_code} {r.text[:200]}")
    sys.exit(1)


# ══════════════════════════════════════════════════════════════
# DATI REALISTICI
# ══════════════════════════════════════════════════════════════

CLIENTI = [
    {
        "nome": "Marco", "cognome": "Rossi",
        "telefono": "3401234567", "email": "marco.rossi@gmail.com",
        "data_nascita": "1988-05-14", "sesso": "Uomo",
        "note_interne": "Impiegato, vuole perdere peso. Motivato, viene 3x/settimana.",
        "anamnesi": {
            "obiettivo_primario": "Dimagrimento",
            "sport_praticati": "Calcetto amatoriale",
            "patologie": [],
            "farmaci": [],
            "infortuni_pregressi": "Distorsione caviglia dx 2022",
            "allergie_alimentari": [],
            "fumatore": False,
            "ore_sonno": 7,
            "livello_stress": "medio",
            "lavoro_sedentario": True,
        },
    },
    {
        "nome": "Giulia", "cognome": "Bianchi",
        "telefono": "3339876543", "email": "giulia.bianchi@outlook.it",
        "data_nascita": "1995-11-22", "sesso": "Donna",
        "note_interne": "Studentessa universitaria. Obiettivo tonificazione glutei e core.",
        "anamnesi": {
            "obiettivo_primario": "Tonificazione",
            "sport_praticati": "Yoga occasionale",
            "patologie": [],
            "farmaci": [],
            "infortuni_pregressi": "",
            "allergie_alimentari": ["Lattosio"],
            "fumatore": False,
            "ore_sonno": 6,
            "livello_stress": "alto",
            "lavoro_sedentario": True,
        },
    },
    {
        "nome": "Roberto", "cognome": "Ferrari",
        "telefono": "3287654321", "email": "r.ferrari@libero.it",
        "data_nascita": "1975-03-08", "sesso": "Uomo",
        "note_interne": "Imprenditore, 50 anni. Ipertensione controllata. Vuole massa muscolare.",
        "anamnesi": {
            "obiettivo_primario": "Ipertrofia",
            "sport_praticati": "Corsa 2x/settimana",
            "patologie": ["Ipertensione arteriosa (controllata)"],
            "farmaci": ["Ramipril 5mg"],
            "infortuni_pregressi": "Ernia L4-L5 operata 2018",
            "allergie_alimentari": [],
            "fumatore": False,
            "ore_sonno": 6,
            "livello_stress": "alto",
            "lavoro_sedentario": True,
        },
    },
    {
        "nome": "Francesca", "cognome": "Marino",
        "telefono": "3471122334", "email": "francesca.marino@gmail.com",
        "data_nascita": "1990-07-30", "sesso": "Donna",
        "note_interne": "Mamma di 2 bambini. Post-partum 8 mesi. Diastasi addominale.",
        "anamnesi": {
            "obiettivo_primario": "Recupero post-partum",
            "sport_praticati": "Nessuno da 2 anni",
            "patologie": ["Diastasi addominale (2 cm)"],
            "farmaci": [],
            "infortuni_pregressi": "",
            "allergie_alimentari": [],
            "fumatore": False,
            "ore_sonno": 5,
            "livello_stress": "alto",
            "lavoro_sedentario": False,
        },
    },
    {
        "nome": "Alessandro", "cognome": "Conti",
        "telefono": "3205566778", "email": "ale.conti92@gmail.com",
        "data_nascita": "1992-01-17", "sesso": "Uomo",
        "note_interne": "Crossfitter esperto. Vuole periodizzazione scientifica per gara.",
        "anamnesi": {
            "obiettivo_primario": "Performance atletica",
            "sport_praticati": "CrossFit 5x/settimana, arrampicata",
            "patologie": [],
            "farmaci": [],
            "infortuni_pregressi": "Tendinite spalla dx risolta 2024",
            "allergie_alimentari": [],
            "fumatore": False,
            "ore_sonno": 8,
            "livello_stress": "basso",
            "lavoro_sedentario": False,
        },
    },
    {
        "nome": "Elena", "cognome": "Ricci",
        "telefono": "3386677889", "email": "elena.ricci@yahoo.it",
        "data_nascita": "1968-12-03", "sesso": "Donna",
        "note_interne": "Pensionata attiva. Osteoporosi diagnosticata. Vuole prevenzione cadute.",
        "anamnesi": {
            "obiettivo_primario": "Salute e prevenzione",
            "sport_praticati": "Camminate quotidiane",
            "patologie": ["Osteoporosi", "Artrosi ginocchio sx"],
            "farmaci": ["Vitamina D", "Calcio"],
            "infortuni_pregressi": "Frattura polso 2020",
            "allergie_alimentari": [],
            "fumatore": False,
            "ore_sonno": 7,
            "livello_stress": "basso",
            "lavoro_sedentario": False,
        },
    },
    {
        "nome": "Luca", "cognome": "Moretti",
        "telefono": "3459988776", "email": "luca.moretti@hotmail.it",
        "data_nascita": "2000-09-25", "sesso": "Uomo",
        "note_interne": "Studente, primo approccio palestra. Molto magro, vuole mettere massa.",
        "anamnesi": {
            "obiettivo_primario": "Aumento massa",
            "sport_praticati": "Nessuno",
            "patologie": [],
            "farmaci": [],
            "infortuni_pregressi": "",
            "allergie_alimentari": ["Glutine"],
            "fumatore": False,
            "ore_sonno": 8,
            "livello_stress": "basso",
            "lavoro_sedentario": True,
        },
    },
    {
        "nome": "Sara", "cognome": "Romano",
        "telefono": "3271144556", "email": "sara.romano@gmail.com",
        "data_nascita": "1985-04-11", "sesso": "Donna",
        "note_interne": "Avvocato, alto stress. Vuole perdere 8kg e gestire ansia. Corre la domenica.",
        "anamnesi": {
            "obiettivo_primario": "Dimagrimento e benessere",
            "sport_praticati": "Running domenicale",
            "patologie": ["Ipotiroidismo (Hashimoto)"],
            "farmaci": ["Eutirox 75mcg"],
            "infortuni_pregressi": "",
            "allergie_alimentari": [],
            "fumatore": False,
            "ore_sonno": 6,
            "livello_stress": "molto alto",
            "lavoro_sedentario": True,
        },
    },
    {
        "nome": "Andrea", "cognome": "Colombo",
        "telefono": "3312233445", "email": "andrea.colombo@live.it",
        "data_nascita": "1982-08-19", "sesso": "Uomo",
        "note_interne": "Ex rugbista. Ginocchio operato (LCA). Rientro graduale all'attivita'.",
        "anamnesi": {
            "obiettivo_primario": "Riabilitazione sportiva",
            "sport_praticati": "Ex rugby, ora fermo",
            "patologie": [],
            "farmaci": [],
            "infortuni_pregressi": "Ricostruzione LCA ginocchio dx 2025",
            "allergie_alimentari": [],
            "fumatore": False,
            "ore_sonno": 7,
            "livello_stress": "medio",
            "lavoro_sedentario": True,
        },
    },
    {
        "nome": "Valentina", "cognome": "Greco",
        "telefono": "3498877665", "email": "valentina.greco@gmail.com",
        "data_nascita": "1998-02-28", "sesso": "Donna",
        "note_interne": "Ballerina semi-professionista. Vuole forza senza massa. Flessibilita' eccellente.",
        "stato": "Inattivo",
        "anamnesi": {
            "obiettivo_primario": "Forza funzionale",
            "sport_praticati": "Danza contemporanea 4x/settimana",
            "patologie": [],
            "farmaci": [],
            "infortuni_pregressi": "Fascite plantare ricorrente",
            "allergie_alimentari": [],
            "fumatore": False,
            "ore_sonno": 7,
            "livello_stress": "medio",
            "lavoro_sedentario": False,
        },
    },
    {
        "nome": "Giuseppe", "cognome": "De Luca",
        "telefono": "3366655443", "email": "giuseppe.deluca@gmail.com",
        "data_nascita": "1970-06-15", "sesso": "Uomo",
        "note_interne": "Diabetico tipo 2. Medico gli ha prescritto attivita' fisica. Motivato ma decondizionato.",
        "anamnesi": {
            "obiettivo_primario": "Controllo glicemico e salute",
            "sport_praticati": "Nessuno da anni",
            "patologie": ["Diabete tipo 2", "Sovrappeso (BMI 31)"],
            "farmaci": ["Metformina 1000mg"],
            "infortuni_pregressi": "",
            "allergie_alimentari": [],
            "fumatore": True,
            "ore_sonno": 6,
            "livello_stress": "medio",
            "lavoro_sedentario": True,
        },
    },
    {
        "nome": "Chiara", "cognome": "Fontana",
        "telefono": "3243344556",
        "data_nascita": "2003-03-28",  # Compleanno domani! Per la demo birthday alert
        "sesso": "Donna",
        "note_interne": "Nuova iscritta. Primo colloquio fatto, in attesa di iniziare.",
        "anamnesi": {},
    },
]


# ── Contratti realistici ──

TODAY = date.today()

CONTRATTI = [
    # (client_idx, tipo, crediti, prezzo, inizio_offset_days, durata_days, acconto, metodo, note)
    (0, "Personal Training 24", 24, 960.0, -90, 180, 200.0, "POS", "Pacchetto semestrale"),
    (1, "Personal Training 12", 12, 540.0, -60, 120, 100.0, "CONTANTI", "Pacchetto trimestrale"),
    (2, "Personal Training 36", 36, 1440.0, -120, 365, 300.0, "BONIFICO", "Annuale premium"),
    (3, "Posturale 16", 16, 640.0, -45, 120, 150.0, "POS", "Recupero post-partum"),
    (4, "Performance 20", 20, 1000.0, -75, 180, 200.0, "BONIFICO", "Prep gara CrossFit"),
    (5, "Silver Age 24", 24, 720.0, -100, 180, 200.0, "CONTANTI", "Prevenzione cadute"),
    (6, "Personal Training 12", 12, 480.0, -30, 120, 100.0, "POS", "Primo pacchetto"),
    (7, "Personal Training 16", 16, 720.0, -50, 150, 150.0, "BONIFICO", "Dimagrimento"),
    (8, "Riabilitazione 20", 20, 900.0, -40, 150, 200.0, "POS", "Post LCA"),
    # Valentina: contratto scaduto (inattiva)
    (9, "Personal Training 8", 8, 360.0, -200, 90, 100.0, "CONTANTI", "Trial"),
    (10, "Metabolico 16", 16, 640.0, -35, 120, 150.0, "POS", "Controllo glicemico"),
    # Rinnovo per Marco (contratto precedente scaduto)
    (0, "Personal Training 12", 12, 480.0, -250, 120, 100.0, "CONTANTI", "Primo pacchetto (scaduto)"),
]


def create_clients():
    """Crea tutti i clienti."""
    print("\n── Clienti ──")
    client_ids = []
    for c in CLIENTI:
        payload = {k: v for k, v in c.items()}
        result = api("post", "/clients", json=payload, expected=201)
        if result:
            client_ids.append(result["id"])
            print(f"  [+] {c['nome']} {c['cognome']} (id={result['id']})")
        else:
            client_ids.append(None)
    return client_ids


def create_contracts(client_ids):
    """Crea contratti con piani rata e pagamenti."""
    print("\n── Contratti ──")
    contract_ids = []

    for idx, (ci, tipo, crediti, prezzo, start_off, durata, acconto, metodo, note) in enumerate(CONTRATTI):
        cid = client_ids[ci]
        if not cid:
            contract_ids.append(None)
            continue

        data_inizio = TODAY + timedelta(days=start_off)
        data_scadenza = data_inizio + timedelta(days=durata)

        payload = {
            "id_cliente": cid,
            "tipo_pacchetto": tipo,
            "crediti_totali": crediti,
            "prezzo_totale": prezzo,
            "data_inizio": data_inizio.isoformat(),
            "data_scadenza": data_scadenza.isoformat(),
            "acconto": acconto,
            "metodo_acconto": metodo,
            "note": note,
        }
        result = api("post", "/contracts", json=payload, expected=201)
        if result:
            contract_ids.append(result["id"])
            nome = CLIENTI[ci]["nome"]
            print(f"  [+] {nome}: {tipo} €{prezzo} (id={result['id']})")
        else:
            contract_ids.append(None)

    return contract_ids


def create_payment_plans(contract_ids):
    """Genera piani rata e paga alcune rate (scenario realistico)."""
    print("\n── Piani rata e pagamenti ──")

    for idx, cid in enumerate(contract_ids):
        if not cid:
            continue

        ci = CONTRATTI[idx][0]
        prezzo = CONTRATTI[idx][3]
        acconto = CONTRATTI[idx][6]
        residuo = prezzo - acconto

        if residuo <= 0:
            continue

        start_off = CONTRATTI[idx][4]
        data_inizio = TODAY + timedelta(days=start_off)

        # 3-5 rate
        n_rate = min(5, max(2, int(residuo / 150)))
        data_prima = data_inizio + timedelta(days=30)

        plan_payload = {
            "importo_da_rateizzare": residuo,
            "numero_rate": n_rate,
            "data_prima_rata": data_prima.isoformat(),
            "frequenza": "MENSILE",
        }

        result = api("post", f"/rates/generate-plan/{cid}", json=plan_payload)
        if not result:
            continue

        nome = CLIENTI[ci]["nome"]
        print(f"  [+] {nome}: {n_rate} rate da €{residuo/n_rate:.0f}")

        # Paga le rate scadute (simulate pagamenti passati)
        rates_resp = api("get", f"/contracts/{cid}")
        if not rates_resp or "rate" not in rates_resp:
            continue

        rates = rates_resp["rate"]
        for rate in rates:
            rate_date = rate.get("data_scadenza", "")
            if rate_date and rate_date < TODAY.isoformat() and rate["stato"] == "PENDENTE":
                importo = rate["importo_previsto"]
                metodo_choices = ["CONTANTI", "POS", "BONIFICO"]
                pay = api("post", f"/rates/{rate['id']}/pay", json={
                    "importo": importo,
                    "metodo": random.choice(metodo_choices),
                })
                if pay:
                    print(f"    [€] Rata #{rate['id']} pagata: €{importo}")


def create_events(client_ids, contract_ids):
    """Crea eventi in agenda (sessioni passate + future)."""
    print("\n── Agenda (eventi) ──")

    # Mappa client_idx -> contract_id (prendi il primo contratto attivo)
    client_contract = {}
    for idx, (ci, *_) in enumerate(CONTRATTI):
        if contract_ids[idx] and ci not in client_contract:
            # Solo contratti non scaduti
            start_off = CONTRATTI[idx][4]
            durata = CONTRATTI[idx][5]
            data_scadenza = TODAY + timedelta(days=start_off + durata)
            if data_scadenza >= TODAY:
                client_contract[ci] = contract_ids[idx]

    # Genera sessioni passate (completate) e future (programmate)
    for ci in range(min(9, len(client_ids))):  # Primi 9 clienti attivi
        cid = client_ids[ci]
        if not cid:
            continue

        nome = CLIENTI[ci]["nome"]
        contr_id = client_contract.get(ci)

        # 4-8 sessioni passate (completate)
        n_past = random.randint(4, 8)
        for j in range(n_past):
            day_offset = -(n_past - j) * random.randint(3, 5)
            session_date = TODAY + timedelta(days=day_offset)
            # Orari realistici (9-19, slot da 1h)
            hour = random.choice([9, 10, 11, 14, 15, 16, 17, 18])
            dt_start = datetime(session_date.year, session_date.month, session_date.day, hour, 0)
            dt_end = dt_start + timedelta(hours=1)

            payload = {
                "data_inizio": dt_start.isoformat(),
                "data_fine": dt_end.isoformat(),
                "categoria": "PT",
                "titolo": f"Sessione {nome}",
                "id_cliente": cid,
                "stato": "Completato",
            }
            if contr_id:
                payload["id_contratto"] = contr_id

            result = api("post", "/events", json=payload)
            if result and j == 0:
                print(f"  [+] {nome}: {n_past} sessioni passate")

        # 2-3 sessioni future (programmate)
        n_future = random.randint(2, 3)
        for j in range(n_future):
            day_offset = (j + 1) * random.randint(2, 4)
            session_date = TODAY + timedelta(days=day_offset)
            hour = random.choice([9, 10, 11, 14, 15, 16, 17, 18])
            dt_start = datetime(session_date.year, session_date.month, session_date.day, hour, 0)
            dt_end = dt_start + timedelta(hours=1)

            payload = {
                "data_inizio": dt_start.isoformat(),
                "data_fine": dt_end.isoformat(),
                "categoria": "PT",
                "titolo": f"Sessione {nome}",
                "id_cliente": cid,
                "stato": "Programmato",
            }
            if contr_id:
                payload["id_contratto"] = contr_id

            api("post", "/events", json=payload)

    # Aggiungi eventi non-PT (corsi, colloqui)
    for j in range(5):
        day_offset = random.randint(-15, 10)
        session_date = TODAY + timedelta(days=day_offset)
        hour = random.choice([10, 16, 18])
        dt_start = datetime(session_date.year, session_date.month, session_date.day, hour, 0)
        dt_end = dt_start + timedelta(hours=1)

        cat = random.choice(["CORSO", "SALA"])
        titolo = "Pilates Gruppo" if cat == "CORSO" else "Sala pesi libera"
        stato = "Completato" if day_offset < 0 else "Programmato"

        api("post", "/events", json={
            "data_inizio": dt_start.isoformat(),
            "data_fine": dt_end.isoformat(),
            "categoria": cat,
            "titolo": titolo,
            "stato": stato,
        })

    # Colloquio Chiara (nuova cliente) - domani
    tomorrow = TODAY + timedelta(days=1)
    dt_start = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 10, 0)
    dt_end = dt_start + timedelta(minutes=45)
    api("post", "/events", json={
        "data_inizio": dt_start.isoformat(),
        "data_fine": dt_end.isoformat(),
        "categoria": "COLLOQUIO",
        "titolo": "Primo colloquio Chiara Fontana",
        "id_cliente": client_ids[11] if len(client_ids) > 11 else None,
        "stato": "Programmato",
    })
    print(f"  [+] Colloquio Chiara Fontana domani ore 10:00")
    print(f"  [+] 5 eventi CORSO/SALA")


def create_measurements(client_ids):
    """Crea sessioni di misurazione per i clienti attivi."""
    print("\n── Misurazioni ──")

    # Metriche: 1=Peso, 2=% grasso, 3=Massa magra, 4=Circ. vita, etc.
    # (id_metrica, base_values per profilo)
    profiles = {
        0: [(1, [92.0, 89.5, 87.8, 86.2]),     (2, [24.0, 22.8, 21.5, 20.5])],   # Marco: dimagrimento
        1: [(1, [58.0, 57.5, 57.2, 57.0]),      (2, [22.0, 21.5, 21.0, 20.5])],   # Giulia: tonificazione
        2: [(1, [85.0, 85.5, 86.2, 86.8]),      (2, [18.0, 17.5, 17.0, 16.5])],   # Roberto: ipertrofia
        3: [(1, [68.0, 67.0, 66.0, 65.5])],                                         # Francesca: post-partum
        7: [(1, [73.0, 72.0, 71.0, 70.2]),      (2, [28.0, 27.0, 26.5, 25.8])],   # Sara: dimagrimento
        10: [(1, [98.0, 96.5, 95.0, 93.8]),     (2, [32.0, 31.0, 30.2, 29.5])],   # Giuseppe: metabolico
    }

    for ci, metrics in profiles.items():
        cid = client_ids[ci]
        if not cid:
            continue

        nome = CLIENTI[ci]["nome"]
        n_sessions = len(metrics[0][1])

        for session_idx in range(n_sessions):
            day_offset = -(n_sessions - session_idx) * 21  # ogni 3 settimane
            measure_date = TODAY + timedelta(days=day_offset)

            valori = []
            for metric_id, values in metrics:
                valori.append({
                    "id_metrica": metric_id,
                    "valore": values[session_idx],
                })

            result = api("post", f"/clients/{cid}/measurements", json={
                "data_misurazione": measure_date.isoformat(),
                "note": f"Misurazione #{session_idx + 1}",
                "valori": valori,
            })
            if result and session_idx == 0:
                print(f"  [+] {nome}: {n_sessions} sessioni misurazione")


def create_goals(client_ids):
    """Crea obiettivi per alcuni clienti."""
    print("\n── Obiettivi ──")

    goals_data = [
        (0, 1, "diminuire", 82.0, "2026-01-01", "2026-06-30", 1, "Obiettivo peso forma entro estate"),
        (0, 2, "diminuire", 18.0, "2026-01-01", "2026-06-30", 2, "Body fat target"),
        (1, 1, "mantenere", None, "2026-02-01", None, 3, "Mantenere peso attuale"),
        (2, 1, "aumentare", 90.0, "2025-12-01", "2026-12-01", 1, "Massa target"),
        (7, 1, "diminuire", 65.0, "2026-02-01", "2026-07-31", 1, "Obiettivo -8kg"),
        (10, 1, "diminuire", 88.0, "2026-02-20", "2026-08-31", 1, "Peso target medico"),
    ]

    for ci, metric_id, direzione, target, inizio, scadenza, priorita, note in goals_data:
        cid = client_ids[ci]
        if not cid:
            continue

        payload = {
            "id_metrica": metric_id,
            "direzione": direzione,
            "data_inizio": inizio,
            "priorita": priorita,
            "note": note,
        }
        if target:
            payload["valore_target"] = target
        if scadenza:
            payload["data_scadenza"] = scadenza

        result = api("post", f"/clients/{cid}/goals", json=payload)
        nome = CLIENTI[ci]["nome"]
        if result:
            print(f"  [+] {nome}: {direzione} metrica #{metric_id}")


def create_recurring_expenses():
    """Crea spese ricorrenti realistiche."""
    print("\n── Spese ricorrenti ──")

    expenses = [
        ("Affitto sala", "Affitto", 350.0, 1, "MENSILE", "2025-09-01"),
        ("Assicurazione RC", "Assicurazione", 180.0, 15, "ANNUALE", "2025-09-01"),
        ("Software gestione (PRO)", "Software", 79.0, 1, "ANNUALE", "2026-01-01"),
        ("Materiale consumo", "Attrezzatura", 45.0, 15, "MENSILE", "2025-09-01"),
        ("Commercialista", "Consulenza", 120.0, 1, "TRIMESTRALE", "2025-10-01"),
    ]

    for nome, cat, importo, giorno, freq, inizio in expenses:
        result = api("post", "/recurring-expenses", json={
            "nome": nome,
            "categoria": cat,
            "importo": importo,
            "giorno_scadenza": giorno,
            "frequenza": freq,
            "data_inizio": inizio,
        })
        if result:
            print(f"  [+] {nome}: €{importo} ({freq})")


def create_communications(client_ids):
    """Crea log comunicazioni WhatsApp."""
    print("\n── Comunicazioni ──")

    comms = [
        (0, "whatsapp", "welcome", "Ciao Marco! Benvenuto nel mio studio. Ti aspetto..."),
        (0, "whatsapp", "workout_share", "Marco, la tua nuova scheda e' pronta! Troverai..."),
        (1, "whatsapp", "welcome", "Ciao Giulia! Benvenuta! Per il tuo primo allenamento..."),
        (1, "whatsapp", "appointment_reminder", "Ciao Giulia, ti ricordo la sessione di domani alle 16..."),
        (2, "whatsapp", "contract_confirm", "Roberto, il tuo contratto annuale e' stato attivato..."),
        (3, "whatsapp", "welcome", "Ciao Francesca! In bocca al lupo per il tuo percorso..."),
        (4, "whatsapp", "workout_share", "Alessandro, la periodizzazione per la gara e' pronta..."),
        (5, "whatsapp", "appointment_reminder", "Elena, le ricordo la sessione di domani alle 10..."),
        (5, "telefono", None, "Telefonata per spostare appuntamento al giovedi"),
        (7, "whatsapp", "checkin", "Ciao Sara, come va? Ho visto che non vieni da 10 giorni..."),
        (7, "whatsapp", "nutrition_plan", "Sara, il tuo nuovo piano alimentare e' pronto..."),
        (8, "whatsapp", "welcome", "Ciao Andrea! Iniziamo il percorso di recupero..."),
        (10, "whatsapp", "welcome", "Ciao Giuseppe! Il suo medico mi ha parlato di lei..."),
        (10, "whatsapp", "appointment_reminder", "Giuseppe, le ricordo la sessione di domani alle 14..."),
    ]

    for ci, canale, template, anteprima in comms:
        cid = client_ids[ci]
        if not cid:
            continue

        result = api("post", "/communications", json={
            "id_cliente": cid,
            "canale": canale,
            "template_usato": template,
            "anteprima": anteprima,
        })
        nome = CLIENTI[ci]["nome"]
        if result:
            print(f"  [+] {nome}: {canale} ({template or 'manuale'})")


def create_workouts(client_ids):
    """Crea alcune schede allenamento realistiche."""
    print("\n── Schede allenamento ──")

    # Scheda Marco - Full Body dimagrimento
    if client_ids[0]:
        result = api("post", "/workouts", json={
            "id_cliente": client_ids[0],
            "nome": "Full Body Dimagrimento - Fase 2",
            "obiettivo": "dimagrimento",
            "livello": "intermedio",
            "durata_settimane": 6,
            "sessioni_per_settimana": 3,
            "note": "Circuiti metabolici + forza. Attenzione caviglia dx.",
            "sessioni": [
                {
                    "nome_sessione": "Upper Body + Core",
                    "focus_muscolare": "Petto, Dorso, Core",
                    "durata_minuti": 60,
                    "esercizi": [
                        {"id_esercizio": 1, "ordine": 1, "serie": 4, "ripetizioni": "10-12", "tempo_riposo_sec": 60},
                        {"id_esercizio": 5, "ordine": 2, "serie": 4, "ripetizioni": "10-12", "tempo_riposo_sec": 60},
                        {"id_esercizio": 10, "ordine": 3, "serie": 3, "ripetizioni": "12-15", "tempo_riposo_sec": 45},
                        {"id_esercizio": 15, "ordine": 4, "serie": 3, "ripetizioni": "15", "tempo_riposo_sec": 45},
                    ],
                },
                {
                    "nome_sessione": "Lower Body + Cardio",
                    "focus_muscolare": "Quadricipiti, Glutei, Femorali",
                    "durata_minuti": 60,
                    "esercizi": [
                        {"id_esercizio": 20, "ordine": 1, "serie": 4, "ripetizioni": "8-10", "tempo_riposo_sec": 90},
                        {"id_esercizio": 25, "ordine": 2, "serie": 4, "ripetizioni": "10-12", "tempo_riposo_sec": 60},
                        {"id_esercizio": 30, "ordine": 3, "serie": 3, "ripetizioni": "12-15", "tempo_riposo_sec": 60},
                        {"id_esercizio": 35, "ordine": 4, "serie": 3, "ripetizioni": "15-20", "tempo_riposo_sec": 45},
                    ],
                },
                {
                    "nome_sessione": "Circuito Metabolico",
                    "focus_muscolare": "Full Body",
                    "durata_minuti": 45,
                    "esercizi": [
                        {"id_esercizio": 40, "ordine": 1, "serie": 3, "ripetizioni": "15", "tempo_riposo_sec": 30},
                        {"id_esercizio": 45, "ordine": 2, "serie": 3, "ripetizioni": "12", "tempo_riposo_sec": 30},
                        {"id_esercizio": 50, "ordine": 3, "serie": 3, "ripetizioni": "15", "tempo_riposo_sec": 30},
                    ],
                },
            ],
        })
        if result:
            print(f"  [+] Marco: Full Body Dimagrimento - Fase 2")

    # Scheda Giulia - Glutei & Core
    if client_ids[1]:
        result = api("post", "/workouts", json={
            "id_cliente": client_ids[1],
            "nome": "Glutei & Core - Tonificazione",
            "obiettivo": "generale",
            "livello": "intermedio",
            "durata_settimane": 4,
            "sessioni_per_settimana": 3,
            "note": "Focus glutei e core. Progressione carico settimanale.",
            "sessioni": [
                {
                    "nome_sessione": "Glutei Focus",
                    "focus_muscolare": "Glutei, Femorali",
                    "durata_minuti": 50,
                    "esercizi": [
                        {"id_esercizio": 20, "ordine": 1, "serie": 4, "ripetizioni": "10-12", "tempo_riposo_sec": 90},
                        {"id_esercizio": 25, "ordine": 2, "serie": 3, "ripetizioni": "12", "tempo_riposo_sec": 60},
                        {"id_esercizio": 30, "ordine": 3, "serie": 3, "ripetizioni": "15", "tempo_riposo_sec": 60},
                    ],
                },
                {
                    "nome_sessione": "Upper + Core",
                    "focus_muscolare": "Core, Spalle, Dorso",
                    "durata_minuti": 50,
                    "esercizi": [
                        {"id_esercizio": 1, "ordine": 1, "serie": 3, "ripetizioni": "12", "tempo_riposo_sec": 60},
                        {"id_esercizio": 10, "ordine": 2, "serie": 3, "ripetizioni": "12", "tempo_riposo_sec": 60},
                        {"id_esercizio": 15, "ordine": 3, "serie": 3, "ripetizioni": "20", "tempo_riposo_sec": 45},
                    ],
                },
            ],
        })
        if result:
            print(f"  [+] Giulia: Glutei & Core - Tonificazione")

    # Scheda Roberto - Ipertrofia
    if client_ids[2]:
        result = api("post", "/workouts", json={
            "id_cliente": client_ids[2],
            "nome": "Ipertrofia Push/Pull/Legs",
            "obiettivo": "ipertrofia",
            "livello": "avanzato",
            "durata_settimane": 8,
            "sessioni_per_settimana": 4,
            "note": "Split PPL. Attenzione zona lombare (ernia operata). No stacco da terra pesante.",
            "sessioni": [
                {
                    "nome_sessione": "Push (Petto + Spalle + Tricipiti)",
                    "focus_muscolare": "Petto, Deltoidi, Tricipiti",
                    "durata_minuti": 70,
                    "esercizi": [
                        {"id_esercizio": 1, "ordine": 1, "serie": 4, "ripetizioni": "6-8", "tempo_riposo_sec": 120},
                        {"id_esercizio": 5, "ordine": 2, "serie": 4, "ripetizioni": "8-10", "tempo_riposo_sec": 90},
                        {"id_esercizio": 10, "ordine": 3, "serie": 3, "ripetizioni": "10-12", "tempo_riposo_sec": 60},
                        {"id_esercizio": 15, "ordine": 4, "serie": 3, "ripetizioni": "12-15", "tempo_riposo_sec": 60},
                    ],
                },
                {
                    "nome_sessione": "Pull (Dorso + Bicipiti)",
                    "focus_muscolare": "Dorsali, Trapezio, Bicipiti",
                    "durata_minuti": 70,
                    "esercizi": [
                        {"id_esercizio": 20, "ordine": 1, "serie": 4, "ripetizioni": "6-8", "tempo_riposo_sec": 120},
                        {"id_esercizio": 25, "ordine": 2, "serie": 4, "ripetizioni": "8-10", "tempo_riposo_sec": 90},
                        {"id_esercizio": 30, "ordine": 3, "serie": 3, "ripetizioni": "10-12", "tempo_riposo_sec": 60},
                    ],
                },
                {
                    "nome_sessione": "Legs (Quadricipiti + Femorali + Glutei)",
                    "focus_muscolare": "Quadricipiti, Femorali, Glutei, Polpacci",
                    "durata_minuti": 70,
                    "esercizi": [
                        {"id_esercizio": 35, "ordine": 1, "serie": 4, "ripetizioni": "8-10", "tempo_riposo_sec": 120},
                        {"id_esercizio": 40, "ordine": 2, "serie": 4, "ripetizioni": "10-12", "tempo_riposo_sec": 90},
                        {"id_esercizio": 45, "ordine": 3, "serie": 3, "ripetizioni": "12-15", "tempo_riposo_sec": 60},
                        {"id_esercizio": 50, "ordine": 4, "serie": 3, "ripetizioni": "15-20", "tempo_riposo_sec": 60},
                    ],
                },
            ],
        })
        if result:
            print(f"  [+] Roberto: Ipertrofia Push/Pull/Legs")

    # Scheda Alessandro - Performance CrossFit
    if client_ids[4]:
        result = api("post", "/workouts", json={
            "id_cliente": client_ids[4],
            "nome": "Prep Gara - Mesociclo Forza",
            "obiettivo": "forza",
            "livello": "avanzato",
            "durata_settimane": 4,
            "sessioni_per_settimana": 5,
            "note": "Mesociclo forza pre-gara. Attenzione spalla dx (tendinite risolta).",
            "sessioni": [
                {
                    "nome_sessione": "Heavy Squat Day",
                    "focus_muscolare": "Quadricipiti, Glutei, Core",
                    "durata_minuti": 75,
                    "esercizi": [
                        {"id_esercizio": 35, "ordine": 1, "serie": 5, "ripetizioni": "3-5", "tempo_riposo_sec": 180, "carico_kg": 120.0},
                        {"id_esercizio": 40, "ordine": 2, "serie": 4, "ripetizioni": "6-8", "tempo_riposo_sec": 120, "carico_kg": 80.0},
                    ],
                },
                {
                    "nome_sessione": "Upper Strength",
                    "focus_muscolare": "Petto, Dorso, Spalle",
                    "durata_minuti": 60,
                    "esercizi": [
                        {"id_esercizio": 1, "ordine": 1, "serie": 5, "ripetizioni": "3-5", "tempo_riposo_sec": 180, "carico_kg": 100.0},
                        {"id_esercizio": 20, "ordine": 2, "serie": 4, "ripetizioni": "5-7", "tempo_riposo_sec": 150, "carico_kg": 90.0},
                    ],
                },
            ],
        })
        if result:
            print(f"  [+] Alessandro: Prep Gara - Mesociclo Forza")


def create_todos():
    """Crea alcuni reminder per il trainer."""
    print("\n── Todo / Reminder ──")

    todos = [
        ("Preparare piano alimentare Sara", "Ha chiesto specificamente un piano per ipotiroidismo", (TODAY + timedelta(days=2)).isoformat()),
        ("Chiamare medico Giuseppe De Luca", "Coordinamento piano esercizi con diabetologo", (TODAY + timedelta(days=3)).isoformat()),
        ("Ordinare elastici resistenza", "Servono per il programma di Elena (prevenzione cadute)", (TODAY + timedelta(days=5)).isoformat()),
        ("Aggiornare scheda Marco", "Progressione: aumentare carico su squat e panca", (TODAY + timedelta(days=1)).isoformat()),
        ("Contattare Valentina per rinnovo", "Contratto scaduto da 2 mesi, inviare proposta rinnovo", (TODAY + timedelta(days=1)).isoformat()),
    ]

    for titolo, desc, scadenza in todos:
        result = api("post", "/todos", json={
            "titolo": titolo,
            "descrizione": desc,
            "data_scadenza": scadenza,
        })
        if result:
            print(f"  [+] {titolo[:50]}...")


def set_saldo_iniziale():
    """Imposta il saldo iniziale cassa del trainer."""
    print("\n── Saldo iniziale cassa ──")
    # Il saldo iniziale si imposta via PATCH sul trainer
    result = api("patch", "/auth/me", json={
        "saldo_iniziale_cassa": 1500.0,
        "data_saldo_iniziale": "2025-09-01",
    })
    if result:
        print(f"  [+] Saldo iniziale: €1500 dal 01/09/2025")
    else:
        print(f"  [~] PATCH /auth/me non disponibile (saldo da impostare manualmente)")


def create_manual_movements():
    """Crea alcuni movimenti manuali (entrate/uscite extra)."""
    print("\n── Movimenti manuali ──")

    movements = [
        ("USCITA", "2026-02-15", 89.0, "POS", "Attrezzatura", "Elastici resistenza TheraBand"),
        ("USCITA", "2026-01-10", 45.0, "CONTANTI", "Materiale", "Tappetini yoga x3"),
        ("ENTRATA", "2026-03-01", 50.0, "CONTANTI", "Consulenza", "Consulenza nutrizionale una tantum - Marco"),
        ("USCITA", "2026-03-05", 29.0, "POS", "Software", "Abbonamento Canva Pro"),
    ]

    for tipo, data, importo, metodo, cat, note in movements:
        result = api("post", "/movements", json={
            "tipo": tipo,
            "data_movimento": data,
            "data_effettiva": data,
            "importo": importo,
            "metodo": metodo,
            "categoria": cat,
            "note": note,
        })
        if result:
            print(f"  [+] {tipo}: €{importo} - {note[:40]}")


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("  FitManager — Seed Demo CRM (via API porta 8001)")
    print("=" * 60)

    # Step 0: Auth
    login_or_register()

    # Step 1: Clienti (12 profili realistici)
    client_ids = create_clients()
    print(f"\n  Totale clienti: {sum(1 for x in client_ids if x)}")

    # Step 2: Contratti (12 contratti, mix attivi/scaduti)
    contract_ids = create_contracts(client_ids)

    # Step 3: Piani rata + pagamenti
    create_payment_plans(contract_ids)

    # Step 4: Agenda (sessioni completate + future)
    create_events(client_ids, contract_ids)

    # Step 5: Misurazioni (tracking progressi)
    create_measurements(client_ids)

    # Step 6: Obiettivi
    create_goals(client_ids)

    # Step 7: Spese ricorrenti
    create_recurring_expenses()

    # Step 8: Comunicazioni WhatsApp
    create_communications(client_ids)

    # Step 9: Schede allenamento
    create_workouts(client_ids)

    # Step 10: Todo/Reminder
    create_todos()

    # Step 11: Movimenti manuali
    create_manual_movements()

    # Step 12: Saldo iniziale
    set_saldo_iniziale()

    print("\n" + "=" * 60)
    print("  DONE! crm_dev.db popolato con scenario demo realistico.")
    print("  12 clienti, 12 contratti, rate, agenda, misurazioni,")
    print("  obiettivi, spese, comunicazioni, schede, todo.")
    print("=" * 60)
    print("\n  Credenziali: chiarabassani96@gmail.com / Fitness2026!")
    print(f"  Frontend: http://localhost:3001")
    print(f"  Backend:  http://localhost:8001/docs")


if __name__ == "__main__":
    main()

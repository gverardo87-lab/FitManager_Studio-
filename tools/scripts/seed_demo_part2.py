#!/usr/bin/env python3
"""Completa il seed demo: misurazioni, obiettivi, spese, comunicazioni, schede, todo, movimenti."""
import sys
import os
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import requests
from datetime import date, timedelta

BASE = "http://localhost:8001/api"
TODAY = date.today()

r = requests.post(f"{BASE}/auth/login", json={"email": "chiarabassani96@gmail.com", "password": "Fitness2026!"}, timeout=10)
TOKEN = r.json()["access_token"]
H = {"Authorization": f"Bearer {TOKEN}"}


def api(method, path, json=None):
    r = getattr(requests, method)(f"{BASE}{path}", json=json, headers=H, timeout=15)
    if r.status_code >= 400:
        return None
    return r.json() if r.text else None


# Get client IDs sorted by id
clients = api("get", "/clients")["items"]
cids = [c["id"] for c in sorted(clients, key=lambda x: x["id"])]
print(f"Clienti: {len(cids)} -> {cids}")

# == Misurazioni ==
print("--- Misurazioni ---")
profiles = {
    0: [(1, [92.0, 89.5, 87.8, 86.2]), (2, [24.0, 22.8, 21.5, 20.5])],
    1: [(1, [58.0, 57.5, 57.2, 57.0]), (2, [22.0, 21.5, 21.0, 20.5])],
    2: [(1, [85.0, 85.5, 86.2, 86.8]), (2, [18.0, 17.5, 17.0, 16.5])],
    3: [(1, [68.0, 67.0, 66.0, 65.5])],
    7: [(1, [73.0, 72.0, 71.0, 70.2]), (2, [28.0, 27.0, 26.5, 25.8])],
    10: [(1, [98.0, 96.5, 95.0, 93.8]), (2, [32.0, 31.0, 30.2, 29.5])],
}
for ci, metrics in profiles.items():
    if ci >= len(cids):
        continue
    n = len(metrics[0][1])
    ok = 0
    for si in range(n):
        d = TODAY + timedelta(days=-(n - si) * 21)
        valori = [{"id_metrica": mid, "valore": vals[si]} for mid, vals in metrics]
        r = api("post", f"/clients/{cids[ci]}/measurements", json={
            "data_misurazione": d.isoformat(),
            "note": f"Misurazione #{si + 1}",
            "valori": valori,
        })
        if r:
            ok += 1
    print(f"  client[{ci}]: {ok}/{n} sessioni")

# == Obiettivi ==
print("--- Obiettivi ---")
goals = [
    (0, 1, "diminuire", 82.0, "2026-01-01", "2026-06-30", 1, "Peso forma estate"),
    (0, 2, "diminuire", 18.0, "2026-01-01", "2026-06-30", 2, "Body fat target"),
    (1, 1, "mantenere", None, "2026-02-01", None, 3, "Mantenere peso"),
    (2, 1, "aumentare", 90.0, "2025-12-01", "2026-12-01", 1, "Massa target"),
    (7, 1, "diminuire", 65.0, "2026-02-01", "2026-07-31", 1, "-8kg"),
    (10, 1, "diminuire", 88.0, "2026-02-20", "2026-08-31", 1, "Peso target medico"),
]
for ci, mid, dire, target, ini, sca, pri, note in goals:
    if ci >= len(cids):
        continue
    p = {"id_metrica": mid, "direzione": dire, "data_inizio": ini, "priorita": pri, "note": note}
    if target:
        p["valore_target"] = target
    if sca:
        p["data_scadenza"] = sca
    r = api("post", f"/clients/{cids[ci]}/goals", json=p)
    status = "ok" if r else "FAIL"
    print(f"  goal {ci}: {status}")

# == Spese ricorrenti ==
print("--- Spese ricorrenti ---")
expenses = [
    ("Affitto sala", "Affitto", 350.0, 1, "MENSILE", "2025-09-01"),
    ("Assicurazione RC", "Assicurazione", 180.0, 15, "ANNUALE", "2025-09-01"),
    ("Software gestione PRO", "Software", 79.0, 1, "ANNUALE", "2026-01-01"),
    ("Materiale consumo", "Attrezzatura", 45.0, 15, "MENSILE", "2025-09-01"),
    ("Commercialista", "Consulenza", 120.0, 1, "TRIMESTRALE", "2025-10-01"),
]
for nome, cat, imp, gg, freq, ini in expenses:
    r = api("post", "/recurring-expenses", json={
        "nome": nome, "categoria": cat, "importo": imp,
        "giorno_scadenza": gg, "frequenza": freq, "data_inizio": ini,
    })
    status = "ok" if r else "FAIL"
    print(f"  {nome}: {status}")

# == Comunicazioni ==
print("--- Comunicazioni ---")
comms = [
    (0, "whatsapp", "welcome", "Ciao Marco! Benvenuto nel mio studio..."),
    (0, "whatsapp", "workout_share", "Marco, la tua nuova scheda e pronta!"),
    (1, "whatsapp", "welcome", "Ciao Giulia! Benvenuta!"),
    (1, "whatsapp", "appointment_reminder", "Giulia, ti ricordo la sessione di domani..."),
    (2, "whatsapp", "contract_confirm", "Roberto, contratto annuale attivato."),
    (3, "whatsapp", "welcome", "Ciao Francesca! In bocca al lupo!"),
    (4, "whatsapp", "workout_share", "Alessandro, periodizzazione pronta!"),
    (5, "whatsapp", "appointment_reminder", "Elena, le ricordo la sessione domani..."),
    (5, "telefono", None, "Telefonata spostamento appuntamento"),
    (7, "whatsapp", "checkin", "Sara, come va? Non vieni da 10 giorni..."),
    (7, "whatsapp", "nutrition_plan", "Sara, piano alimentare pronto!"),
    (8, "whatsapp", "welcome", "Andrea! Iniziamo il recupero..."),
    (10, "whatsapp", "welcome", "Giuseppe! Il medico mi ha parlato di lei..."),
    (10, "whatsapp", "appointment_reminder", "Giuseppe, sessione domani alle 14..."),
]
for ci, canale, tmpl, ant in comms:
    if ci >= len(cids):
        continue
    r = api("post", "/communications", json={
        "id_cliente": cids[ci], "canale": canale,
        "template_usato": tmpl, "anteprima": ant,
    })
    status = "ok" if r else "FAIL"
    print(f"  {ci} {canale}: {status}")

# == Todo ==
print("--- Todo ---")
todos = [
    ("Preparare piano alimentare Sara", "Piano per ipotiroidismo", 2),
    ("Chiamare medico Giuseppe De Luca", "Coordinamento diabetologo", 3),
    ("Ordinare elastici resistenza", "Per programma Elena", 5),
    ("Aggiornare scheda Marco", "Aumentare carico squat e panca", 1),
    ("Contattare Valentina per rinnovo", "Contratto scaduto, proposta rinnovo", 1),
]
for tit, desc, days in todos:
    r = api("post", "/todos", json={
        "titolo": tit, "descrizione": desc,
        "data_scadenza": (TODAY + timedelta(days=days)).isoformat(),
    })
    status = "ok" if r else "FAIL"
    print(f"  {tit[:40]}: {status}")

# == Movimenti manuali ==
print("--- Movimenti manuali ---")
movs = [
    ("USCITA", "2026-02-15", 89.0, "POS", "Attrezzatura", "Elastici TheraBand"),
    ("USCITA", "2026-01-10", 45.0, "CONTANTI", "Materiale", "Tappetini yoga x3"),
    ("ENTRATA", "2026-03-01", 50.0, "CONTANTI", "Consulenza", "Consulenza nutrizionale Marco"),
    ("USCITA", "2026-03-05", 29.0, "POS", "Software", "Canva Pro"),
]
for tipo, data, imp, met, cat, note in movs:
    r = api("post", "/movements", json={
        "tipo": tipo, "data_movimento": data, "data_effettiva": data,
        "importo": imp, "metodo": met, "categoria": cat, "note": note,
    })
    status = "ok" if r else "FAIL"
    print(f"  {tipo} {imp}: {status}")

# == Schede allenamento ==
print("--- Schede allenamento ---")

# Marco - Full Body
r = api("post", "/workouts", json={
    "id_cliente": cids[0], "nome": "Full Body Dimagrimento - Fase 2",
    "obiettivo": "dimagrimento", "livello": "intermedio",
    "durata_settimane": 6, "sessioni_per_settimana": 3,
    "note": "Circuiti metabolici + forza. Attenzione caviglia dx.",
    "sessioni": [
        {"nome_sessione": "Upper Body + Core", "focus_muscolare": "Petto, Dorso, Core",
         "durata_minuti": 60, "esercizi": [
            {"id_esercizio": 1, "ordine": 1, "serie": 4, "ripetizioni": "10-12", "tempo_riposo_sec": 60},
            {"id_esercizio": 5, "ordine": 2, "serie": 4, "ripetizioni": "10-12", "tempo_riposo_sec": 60},
            {"id_esercizio": 10, "ordine": 3, "serie": 3, "ripetizioni": "12-15", "tempo_riposo_sec": 45},
        ]},
        {"nome_sessione": "Lower Body", "focus_muscolare": "Quadricipiti, Glutei",
         "durata_minuti": 60, "esercizi": [
            {"id_esercizio": 20, "ordine": 1, "serie": 4, "ripetizioni": "8-10", "tempo_riposo_sec": 90},
            {"id_esercizio": 25, "ordine": 2, "serie": 4, "ripetizioni": "10-12", "tempo_riposo_sec": 60},
            {"id_esercizio": 30, "ordine": 3, "serie": 3, "ripetizioni": "12-15", "tempo_riposo_sec": 60},
        ]},
        {"nome_sessione": "Circuito Metabolico", "focus_muscolare": "Full Body",
         "durata_minuti": 45, "esercizi": [
            {"id_esercizio": 40, "ordine": 1, "serie": 3, "ripetizioni": "15", "tempo_riposo_sec": 30},
            {"id_esercizio": 45, "ordine": 2, "serie": 3, "ripetizioni": "12", "tempo_riposo_sec": 30},
        ]},
    ],
})
print(f"  Marco Full Body: {'ok' if r else 'FAIL'}")

# Giulia - Glutei
r = api("post", "/workouts", json={
    "id_cliente": cids[1], "nome": "Glutei & Core - Tonificazione",
    "obiettivo": "generale", "livello": "intermedio",
    "durata_settimane": 4, "sessioni_per_settimana": 3,
    "sessioni": [
        {"nome_sessione": "Glutei Focus", "focus_muscolare": "Glutei, Femorali",
         "durata_minuti": 50, "esercizi": [
            {"id_esercizio": 20, "ordine": 1, "serie": 4, "ripetizioni": "10-12", "tempo_riposo_sec": 90},
            {"id_esercizio": 25, "ordine": 2, "serie": 3, "ripetizioni": "12", "tempo_riposo_sec": 60},
        ]},
        {"nome_sessione": "Upper + Core", "focus_muscolare": "Core, Spalle",
         "durata_minuti": 50, "esercizi": [
            {"id_esercizio": 1, "ordine": 1, "serie": 3, "ripetizioni": "12", "tempo_riposo_sec": 60},
            {"id_esercizio": 10, "ordine": 2, "serie": 3, "ripetizioni": "12", "tempo_riposo_sec": 60},
        ]},
    ],
})
print(f"  Giulia Glutei: {'ok' if r else 'FAIL'}")

# Roberto - Ipertrofia PPL
r = api("post", "/workouts", json={
    "id_cliente": cids[2], "nome": "Ipertrofia Push/Pull/Legs",
    "obiettivo": "ipertrofia", "livello": "avanzato",
    "durata_settimane": 8, "sessioni_per_settimana": 4,
    "note": "Split PPL. Attenzione lombare (ernia operata).",
    "sessioni": [
        {"nome_sessione": "Push", "focus_muscolare": "Petto, Deltoidi, Tricipiti",
         "durata_minuti": 70, "esercizi": [
            {"id_esercizio": 1, "ordine": 1, "serie": 4, "ripetizioni": "6-8", "tempo_riposo_sec": 120},
            {"id_esercizio": 5, "ordine": 2, "serie": 4, "ripetizioni": "8-10", "tempo_riposo_sec": 90},
            {"id_esercizio": 10, "ordine": 3, "serie": 3, "ripetizioni": "10-12", "tempo_riposo_sec": 60},
        ]},
        {"nome_sessione": "Pull", "focus_muscolare": "Dorsali, Bicipiti",
         "durata_minuti": 70, "esercizi": [
            {"id_esercizio": 20, "ordine": 1, "serie": 4, "ripetizioni": "6-8", "tempo_riposo_sec": 120},
            {"id_esercizio": 25, "ordine": 2, "serie": 4, "ripetizioni": "8-10", "tempo_riposo_sec": 90},
        ]},
        {"nome_sessione": "Legs", "focus_muscolare": "Quadricipiti, Femorali, Glutei",
         "durata_minuti": 70, "esercizi": [
            {"id_esercizio": 35, "ordine": 1, "serie": 4, "ripetizioni": "8-10", "tempo_riposo_sec": 120},
            {"id_esercizio": 40, "ordine": 2, "serie": 4, "ripetizioni": "10-12", "tempo_riposo_sec": 90},
            {"id_esercizio": 45, "ordine": 3, "serie": 3, "ripetizioni": "12-15", "tempo_riposo_sec": 60},
        ]},
    ],
})
print(f"  Roberto PPL: {'ok' if r else 'FAIL'}")

# Alessandro - Performance
r = api("post", "/workouts", json={
    "id_cliente": cids[4], "nome": "Prep Gara - Mesociclo Forza",
    "obiettivo": "forza", "livello": "avanzato",
    "durata_settimane": 4, "sessioni_per_settimana": 5,
    "note": "Mesociclo forza pre-gara.",
    "sessioni": [
        {"nome_sessione": "Heavy Squat Day", "focus_muscolare": "Quadricipiti, Glutei, Core",
         "durata_minuti": 75, "esercizi": [
            {"id_esercizio": 35, "ordine": 1, "serie": 5, "ripetizioni": "3-5", "tempo_riposo_sec": 180, "carico_kg": 120.0},
            {"id_esercizio": 40, "ordine": 2, "serie": 4, "ripetizioni": "6-8", "tempo_riposo_sec": 120, "carico_kg": 80.0},
        ]},
        {"nome_sessione": "Upper Strength", "focus_muscolare": "Petto, Dorso",
         "durata_minuti": 60, "esercizi": [
            {"id_esercizio": 1, "ordine": 1, "serie": 5, "ripetizioni": "3-5", "tempo_riposo_sec": 180, "carico_kg": 100.0},
            {"id_esercizio": 20, "ordine": 2, "serie": 4, "ripetizioni": "5-7", "tempo_riposo_sec": 150, "carico_kg": 90.0},
        ]},
    ],
})
print(f"  Alessandro Forza: {'ok' if r else 'FAIL'}")

print("\n=== SEED PART 2 COMPLETATO ===")

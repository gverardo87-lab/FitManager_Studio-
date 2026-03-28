#!/usr/bin/env python3
"""Crea schede allenamento realistiche con ID esercizi corretti dal catalogo."""
import sys
import os

os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import requests

BASE = "http://localhost:8001/api"
r = requests.post(f"{BASE}/auth/login", json={
    "email": "chiarabassani96@gmail.com", "password": "Fitness2026!",
})
H = {"Authorization": f"Bearer {r.json()['access_token']}"}


def api(method, path, json=None):
    r = getattr(requests, method)(f"{BASE}{path}", json=json, headers=H, timeout=15)
    if r.status_code >= 400:
        print(f"  ERR {r.status_code}: {r.text[:200]}")
        return None
    return r.json() if r.text else None


# Real exercise IDs from catalog.db:
# 1=Squat Bil, 4=Pressa, 5=Squat CL, 8=Affondi, 13=Ext Gambe
# 18=Stacco, 20=Rumeno, 21=Hip Thrust, 22=Ponte, 27=Curl Gambe, 31=Swing KB
# 34=Calf Raise, 38=Panca Piana, 39=Panca Man, 40=Inclinata, 43=Piegamenti
# 44=Croci Cavi, 54=Spinta Alto, 55=Man Alto, 58=Alzate Lat
# 65=Dip, 71=Remata Bil, 72=Remata Man, 78=Rematore Cavi, 83=Trazioni

# Delete test workout (id=1) if exists
api("delete", "/workouts/1")

# Marco - Full Body Dimagrimento (3 sessioni)
r = api("post", "/workouts", json={
    "id_cliente": 1, "nome": "Full Body Dimagrimento - Fase 2",
    "obiettivo": "dimagrimento", "livello": "intermedio",
    "durata_settimane": 6, "sessioni_per_settimana": 3,
    "note": "Circuiti metabolici + forza. Attenzione caviglia dx.",
    "sessioni": [
        {"nome_sessione": "Upper Body + Core", "focus_muscolare": "Petto, Dorso, Core",
         "durata_minuti": 60, "esercizi": [
            {"id_esercizio": 38, "ordine": 1, "serie": 4, "ripetizioni": "10-12", "tempo_riposo_sec": 60},
            {"id_esercizio": 71, "ordine": 2, "serie": 4, "ripetizioni": "10-12", "tempo_riposo_sec": 60},
            {"id_esercizio": 54, "ordine": 3, "serie": 3, "ripetizioni": "12-15", "tempo_riposo_sec": 45},
            {"id_esercizio": 58, "ordine": 4, "serie": 3, "ripetizioni": "15", "tempo_riposo_sec": 45},
        ]},
        {"nome_sessione": "Lower Body + Cardio", "focus_muscolare": "Quadricipiti, Glutei, Femorali",
         "durata_minuti": 60, "esercizi": [
            {"id_esercizio": 1, "ordine": 1, "serie": 4, "ripetizioni": "8-10", "tempo_riposo_sec": 90},
            {"id_esercizio": 20, "ordine": 2, "serie": 4, "ripetizioni": "10-12", "tempo_riposo_sec": 60},
            {"id_esercizio": 21, "ordine": 3, "serie": 3, "ripetizioni": "12-15", "tempo_riposo_sec": 60},
            {"id_esercizio": 13, "ordine": 4, "serie": 3, "ripetizioni": "15-20", "tempo_riposo_sec": 45},
        ]},
        {"nome_sessione": "Circuito Metabolico", "focus_muscolare": "Full Body",
         "durata_minuti": 45, "esercizi": [
            {"id_esercizio": 31, "ordine": 1, "serie": 3, "ripetizioni": "15", "tempo_riposo_sec": 30},
            {"id_esercizio": 43, "ordine": 2, "serie": 3, "ripetizioni": "12", "tempo_riposo_sec": 30},
            {"id_esercizio": 5, "ordine": 3, "serie": 3, "ripetizioni": "15", "tempo_riposo_sec": 30},
        ]},
    ],
})
print(f"Marco Full Body: {'ok' if r else 'FAIL'}")

# Giulia - Glutei & Core (2 sessioni)
r = api("post", "/workouts", json={
    "id_cliente": 2, "nome": "Glutei & Core - Tonificazione",
    "obiettivo": "generale", "livello": "intermedio",
    "durata_settimane": 4, "sessioni_per_settimana": 3,
    "note": "Focus glutei e core. Progressione carico settimanale.",
    "sessioni": [
        {"nome_sessione": "Glutei Focus", "focus_muscolare": "Glutei, Femorali",
         "durata_minuti": 50, "esercizi": [
            {"id_esercizio": 21, "ordine": 1, "serie": 4, "ripetizioni": "10-12", "tempo_riposo_sec": 90},
            {"id_esercizio": 1, "ordine": 2, "serie": 3, "ripetizioni": "12", "tempo_riposo_sec": 60},
            {"id_esercizio": 8, "ordine": 3, "serie": 3, "ripetizioni": "10", "tempo_riposo_sec": 60},
        ]},
        {"nome_sessione": "Upper + Core", "focus_muscolare": "Core, Spalle, Dorso",
         "durata_minuti": 50, "esercizi": [
            {"id_esercizio": 38, "ordine": 1, "serie": 3, "ripetizioni": "12", "tempo_riposo_sec": 60},
            {"id_esercizio": 71, "ordine": 2, "serie": 3, "ripetizioni": "12", "tempo_riposo_sec": 60},
            {"id_esercizio": 54, "ordine": 3, "serie": 3, "ripetizioni": "12", "tempo_riposo_sec": 45},
        ]},
    ],
})
print(f"Giulia Glutei: {'ok' if r else 'FAIL'}")

# Roberto - Ipertrofia PPL (3 sessioni)
r = api("post", "/workouts", json={
    "id_cliente": 3, "nome": "Ipertrofia Push/Pull/Legs",
    "obiettivo": "ipertrofia", "livello": "avanzato",
    "durata_settimane": 8, "sessioni_per_settimana": 4,
    "note": "Split PPL. Attenzione zona lombare (ernia operata). No stacco pesante.",
    "sessioni": [
        {"nome_sessione": "Push (Petto + Spalle + Tricipiti)",
         "focus_muscolare": "Petto, Deltoidi, Tricipiti",
         "durata_minuti": 70, "esercizi": [
            {"id_esercizio": 38, "ordine": 1, "serie": 4, "ripetizioni": "6-8", "tempo_riposo_sec": 120},
            {"id_esercizio": 40, "ordine": 2, "serie": 4, "ripetizioni": "8-10", "tempo_riposo_sec": 90},
            {"id_esercizio": 55, "ordine": 3, "serie": 3, "ripetizioni": "10-12", "tempo_riposo_sec": 60},
            {"id_esercizio": 44, "ordine": 4, "serie": 3, "ripetizioni": "12-15", "tempo_riposo_sec": 60},
        ]},
        {"nome_sessione": "Pull (Dorso + Bicipiti)",
         "focus_muscolare": "Dorsali, Trapezio, Bicipiti",
         "durata_minuti": 70, "esercizi": [
            {"id_esercizio": 83, "ordine": 1, "serie": 4, "ripetizioni": "6-8", "tempo_riposo_sec": 120},
            {"id_esercizio": 71, "ordine": 2, "serie": 4, "ripetizioni": "8-10", "tempo_riposo_sec": 90},
            {"id_esercizio": 72, "ordine": 3, "serie": 3, "ripetizioni": "10-12", "tempo_riposo_sec": 60},
        ]},
        {"nome_sessione": "Legs (Quadricipiti + Femorali + Glutei)",
         "focus_muscolare": "Quadricipiti, Femorali, Glutei, Polpacci",
         "durata_minuti": 70, "esercizi": [
            {"id_esercizio": 1, "ordine": 1, "serie": 4, "ripetizioni": "8-10", "tempo_riposo_sec": 120},
            {"id_esercizio": 4, "ordine": 2, "serie": 4, "ripetizioni": "10-12", "tempo_riposo_sec": 90},
            {"id_esercizio": 27, "ordine": 3, "serie": 3, "ripetizioni": "12-15", "tempo_riposo_sec": 60},
            {"id_esercizio": 34, "ordine": 4, "serie": 3, "ripetizioni": "15-20", "tempo_riposo_sec": 60},
        ]},
    ],
})
print(f"Roberto PPL: {'ok' if r else 'FAIL'}")

print("\nDONE - schede create")

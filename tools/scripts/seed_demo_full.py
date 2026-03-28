#!/usr/bin/env python3
"""
Seed demo COMPLETO crm_dev.db — 30 clienti, storico 6 mesi.

Inserisce DIRETTAMENTE via SQLite (no API) per controllo totale su date,
pagamenti distribuiti nel tempo, misurazioni periodiche, agenda realistica.

Scenario: Chiara Bassani, personal trainer con studio avviato da settembre 2025.
A marzo 2026 ha 30 clienti in diversi stadi del percorso.

Usage:
    python tools/scripts/seed_demo_full.py
"""
import sys
import os
import json
import sqlite3
from datetime import date, datetime, timedelta, timezone
import random

os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

random.seed(42)  # Reproducible

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "crm_dev.db"))
TODAY = date(2026, 3, 27)
NOW_ISO = datetime(2026, 3, 27, 10, 0, 0, tzinfo=timezone.utc).isoformat()


def iso(d):
    return d.isoformat()


# ══════════════════════════════════════════════════════════════
# CONNESSIONE
# ══════════════════════════════════════════════════════════════

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA foreign_keys=OFF")  # cross-DB FK (metriche in catalog.db)

# ══════════════════════════════════════════════════════════════
# TRAINER
# ══════════════════════════════════════════════════════════════

# Hash password "Fitness2026!" con bcrypt
# Pre-computed hash per evitare dipendenza bcrypt
HASHED_PW = "$2b$12$LJ3m4ys4Rz0PVvVnF1vKJ.Q3Z5t8N2Y4W6X7V8U9T0S1R2Q3P4O5N"
# Usiamo un hash reale generato
import bcrypt
HASHED_PW = bcrypt.hashpw(b"Fitness2026!", bcrypt.gensalt()).decode()

conn.execute("""
INSERT INTO trainers (id, email, nome, cognome, hashed_password, is_active, created_at, saldo_iniziale_cassa, data_saldo_iniziale)
VALUES (1, 'chiarabassani96@gmail.com', 'Chiara', 'Bassani', ?, 1, '2025-09-01T08:00:00', 1500.0, '2025-09-01')
""", (HASHED_PW,))
print("[+] Trainer: Chiara Bassani (saldo iniziale EUR 1500)")

# ══════════════════════════════════════════════════════════════
# 30 CLIENTI
# ══════════════════════════════════════════════════════════════

CLIENTI = [
    # (nome, cognome, tel, email, nascita, sesso, stato, data_creazione, note, anamnesi)
    ("Marco", "Rossi", "3401234567", "marco.rossi@gmail.com", "1988-05-14", "Uomo", "Attivo", "2025-09-05",
     "Impiegato, vuole perdere peso. Motivato, viene 3x/settimana. -6kg in 5 mesi.",
     {"step1_dati_personali": {"professione": "Impiegato", "ore_lavoro_sedentario": 8},
      "step2_storia_clinica": {"patologie_attuali": [], "farmaci": [], "infortuni": "Distorsione caviglia dx 2022"},
      "step3_abitudini": {"fumatore": False, "alcool": "occasionale", "ore_sonno": 7, "livello_stress": "medio"},
      "step4_alimentazione": {"pasti_giorno": 3, "allergie": [], "intolleranze": []},
      "step5_attivita_fisica": {"sport_praticati": "Calcetto amatoriale", "frequenza_settimanale": 1, "esperienza_palestra": "intermedio"},
      "step6_obiettivi": {"obiettivo_primario": "Dimagrimento", "obiettivo_secondario": "Tonificazione", "motivazione": "Salute e aspetto fisico"}}),

    ("Giulia", "Bianchi", "3339876543", "giulia.bianchi@outlook.it", "1995-11-22", "Donna", "Attivo", "2025-09-12",
     "Studentessa universitaria. Glutei e core. Molto costante, 3x settimana.",
     {"step1_dati_personali": {"professione": "Studentessa", "ore_lavoro_sedentario": 6},
      "step2_storia_clinica": {"patologie_attuali": [], "farmaci": [], "infortuni": ""},
      "step3_abitudini": {"fumatore": False, "alcool": "mai", "ore_sonno": 6, "livello_stress": "alto"},
      "step4_alimentazione": {"pasti_giorno": 3, "allergie": [], "intolleranze": ["Lattosio"]},
      "step5_attivita_fisica": {"sport_praticati": "Yoga occasionale", "frequenza_settimanale": 0, "esperienza_palestra": "principiante"},
      "step6_obiettivi": {"obiettivo_primario": "Tonificazione", "obiettivo_secondario": "Forza", "motivazione": "Sentirmi bene"}}),

    ("Roberto", "Ferrari", "3287654321", "r.ferrari@libero.it", "1975-03-08", "Uomo", "Attivo", "2025-09-20",
     "Imprenditore 51 anni. Ipertensione controllata. Vuole massa muscolare. 4x/settimana.",
     {"step1_dati_personali": {"professione": "Imprenditore", "ore_lavoro_sedentario": 10},
      "step2_storia_clinica": {"patologie_attuali": ["Ipertensione arteriosa (controllata)"], "farmaci": ["Ramipril 5mg"], "infortuni": "Ernia L4-L5 operata 2018"},
      "step3_abitudini": {"fumatore": False, "alcool": "moderato", "ore_sonno": 6, "livello_stress": "alto"},
      "step4_alimentazione": {"pasti_giorno": 3, "allergie": [], "intolleranze": []},
      "step5_attivita_fisica": {"sport_praticati": "Corsa 2x/settimana", "frequenza_settimanale": 2, "esperienza_palestra": "avanzato"},
      "step6_obiettivi": {"obiettivo_primario": "Ipertrofia", "obiettivo_secondario": "Salute cardiovascolare", "motivazione": "Forma fisica e longevita"}}),

    ("Francesca", "Marino", "3471122334", "francesca.marino@gmail.com", "1990-07-30", "Donna", "Attivo", "2025-10-10",
     "Mamma di 2 bambini. Post-partum 8 mesi. Diastasi 2cm. Progressi costanti.",
     {"step1_dati_personali": {"professione": "Casalinga", "ore_lavoro_sedentario": 2},
      "step2_storia_clinica": {"patologie_attuali": ["Diastasi addominale (2 cm)"], "farmaci": [], "infortuni": ""},
      "step3_abitudini": {"fumatore": False, "alcool": "mai", "ore_sonno": 5, "livello_stress": "alto"},
      "step4_alimentazione": {"pasti_giorno": 3, "allergie": [], "intolleranze": []},
      "step5_attivita_fisica": {"sport_praticati": "Nessuno da 2 anni", "frequenza_settimanale": 0, "esperienza_palestra": "principiante"},
      "step6_obiettivi": {"obiettivo_primario": "Recupero post-partum", "obiettivo_secondario": "Core stability", "motivazione": "Tornare in forma dopo gravidanza"}}),

    ("Alessandro", "Conti", "3205566778", "ale.conti92@gmail.com", "1992-01-17", "Uomo", "Attivo", "2025-10-01",
     "Crossfitter esperto. Periodizzazione scientifica per gara maggio 2026.",
     {"step1_dati_personali": {"professione": "Vigile del fuoco", "ore_lavoro_sedentario": 2},
      "step2_storia_clinica": {"patologie_attuali": [], "farmaci": [], "infortuni": "Tendinite spalla dx risolta 2024"},
      "step3_abitudini": {"fumatore": False, "alcool": "raro", "ore_sonno": 8, "livello_stress": "basso"},
      "step4_alimentazione": {"pasti_giorno": 5, "allergie": [], "intolleranze": []},
      "step5_attivita_fisica": {"sport_praticati": "CrossFit 5x/settimana, arrampicata", "frequenza_settimanale": 5, "esperienza_palestra": "avanzato"},
      "step6_obiettivi": {"obiettivo_primario": "Performance atletica", "obiettivo_secondario": "Forza massimale", "motivazione": "Gara CrossFit maggio 2026"}}),

    ("Elena", "Ricci", "3386677889", "elena.ricci@yahoo.it", "1968-12-03", "Donna", "Attivo", "2025-09-25",
     "Pensionata 57 anni. Osteoporosi + artrosi ginocchio sx. Prevenzione cadute. Costantissima.",
     {"step1_dati_personali": {"professione": "Pensionata", "ore_lavoro_sedentario": 3},
      "step2_storia_clinica": {"patologie_attuali": ["Osteoporosi", "Artrosi ginocchio sx"], "farmaci": ["Vitamina D", "Calcio"], "infortuni": "Frattura polso 2020"},
      "step3_abitudini": {"fumatore": False, "alcool": "mai", "ore_sonno": 7, "livello_stress": "basso"},
      "step4_alimentazione": {"pasti_giorno": 4, "allergie": [], "intolleranze": []},
      "step5_attivita_fisica": {"sport_praticati": "Camminate quotidiane", "frequenza_settimanale": 7, "esperienza_palestra": "principiante"},
      "step6_obiettivi": {"obiettivo_primario": "Salute e prevenzione cadute", "obiettivo_secondario": "Equilibrio", "motivazione": "Autonomia e salute"}}),

    ("Luca", "Moretti", "3459988776", "luca.moretti@hotmail.it", "2000-09-25", "Uomo", "Attivo", "2025-11-05",
     "Studente 25 anni. Primo approccio palestra. Molto magro (62kg x 183cm). Vuole massa.",
     {"step1_dati_personali": {"professione": "Studente ingegneria", "ore_lavoro_sedentario": 8},
      "step2_storia_clinica": {"patologie_attuali": [], "farmaci": [], "infortuni": ""},
      "step3_abitudini": {"fumatore": False, "alcool": "social", "ore_sonno": 8, "livello_stress": "basso"},
      "step4_alimentazione": {"pasti_giorno": 2, "allergie": [], "intolleranze": ["Glutine"]},
      "step5_attivita_fisica": {"sport_praticati": "Nessuno", "frequenza_settimanale": 0, "esperienza_palestra": "principiante"},
      "step6_obiettivi": {"obiettivo_primario": "Aumento massa muscolare", "obiettivo_secondario": "Forza base", "motivazione": "Aspetto fisico e autostima"}}),

    ("Sara", "Romano", "3271144556", "sara.romano@gmail.com", "1985-04-11", "Donna", "Attivo", "2025-10-15",
     "Avvocato 41 anni. Ipotiroidismo Hashimoto. -5kg in 4 mesi. Corre la domenica.",
     {"step1_dati_personali": {"professione": "Avvocato", "ore_lavoro_sedentario": 10},
      "step2_storia_clinica": {"patologie_attuali": ["Ipotiroidismo (Hashimoto)"], "farmaci": ["Eutirox 75mcg"], "infortuni": ""},
      "step3_abitudini": {"fumatore": False, "alcool": "occasionale", "ore_sonno": 6, "livello_stress": "molto alto"},
      "step4_alimentazione": {"pasti_giorno": 3, "allergie": [], "intolleranze": []},
      "step5_attivita_fisica": {"sport_praticati": "Running domenicale", "frequenza_settimanale": 1, "esperienza_palestra": "intermedio"},
      "step6_obiettivi": {"obiettivo_primario": "Dimagrimento", "obiettivo_secondario": "Gestione stress", "motivazione": "Salute e benessere mentale"}}),

    ("Andrea", "Colombo", "3312233445", "andrea.colombo@live.it", "1982-08-19", "Uomo", "Attivo", "2025-12-10",
     "Ex rugbista 43 anni. LCA ricostruito dx settembre 2025. Rientro graduale. Molto disciplinato.",
     {"step1_dati_personali": {"professione": "Ingegnere", "ore_lavoro_sedentario": 8},
      "step2_storia_clinica": {"patologie_attuali": [], "farmaci": [], "infortuni": "Ricostruzione LCA ginocchio dx settembre 2025"},
      "step3_abitudini": {"fumatore": False, "alcool": "moderato", "ore_sonno": 7, "livello_stress": "medio"},
      "step4_alimentazione": {"pasti_giorno": 4, "allergie": [], "intolleranze": []},
      "step5_attivita_fisica": {"sport_praticati": "Ex rugby, ora fermo", "frequenza_settimanale": 0, "esperienza_palestra": "avanzato"},
      "step6_obiettivi": {"obiettivo_primario": "Riabilitazione sportiva", "obiettivo_secondario": "Ritorno al rugby", "motivazione": "Tornare a giocare"}}),

    ("Valentina", "Greco", "3498877665", "valentina.greco@gmail.com", "1998-02-28", "Donna", "Inattivo", "2025-09-15",
     "Ballerina. Contratto scaduto dicembre. Da ricontattare per rinnovo.",
     {"step1_dati_personali": {"professione": "Ballerina", "ore_lavoro_sedentario": 0},
      "step2_storia_clinica": {"patologie_attuali": [], "farmaci": [], "infortuni": "Fascite plantare ricorrente"},
      "step3_abitudini": {"fumatore": False, "alcool": "mai", "ore_sonno": 7, "livello_stress": "medio"},
      "step4_alimentazione": {"pasti_giorno": 4, "allergie": [], "intolleranze": []},
      "step5_attivita_fisica": {"sport_praticati": "Danza contemporanea 4x/settimana", "frequenza_settimanale": 4, "esperienza_palestra": "intermedio"},
      "step6_obiettivi": {"obiettivo_primario": "Forza funzionale senza massa", "obiettivo_secondario": "Prevenzione infortuni", "motivazione": "Performance artistica"}}),

    ("Giuseppe", "De Luca", "3366655443", "giuseppe.deluca@gmail.com", "1970-06-15", "Uomo", "Attivo", "2025-11-20",
     "Diabetico tipo 2 (BMI 31). Medico gli ha prescritto esercizio. -4kg in 3 mesi. Motivato.",
     {"step1_dati_personali": {"professione": "Commerciante", "ore_lavoro_sedentario": 6},
      "step2_storia_clinica": {"patologie_attuali": ["Diabete tipo 2", "Sovrappeso (BMI 31)"], "farmaci": ["Metformina 1000mg"], "infortuni": ""},
      "step3_abitudini": {"fumatore": True, "alcool": "moderato", "ore_sonno": 6, "livello_stress": "medio"},
      "step4_alimentazione": {"pasti_giorno": 3, "allergie": [], "intolleranze": []},
      "step5_attivita_fisica": {"sport_praticati": "Nessuno da anni", "frequenza_settimanale": 0, "esperienza_palestra": "principiante"},
      "step6_obiettivi": {"obiettivo_primario": "Controllo glicemico", "obiettivo_secondario": "Perdita peso", "motivazione": "Prescrizione medica e salute"}}),

    ("Chiara", "Fontana", "3243344556", None, "2003-03-28", "Donna", "Attivo", "2026-03-20",
     "Nuova iscritta. Primo colloquio fatto. Inizia settimana prossima.",
     {}),

    ("Matteo", "Lombardi", "3401112233", "matteo.lombardi@gmail.com", "1993-06-12", "Uomo", "Attivo", "2025-10-20",
     "Programmatore. Postura da scrivania. Mal di schiena cronico. Vuole correggere.",
     {"step1_dati_personali": {"professione": "Sviluppatore software", "ore_lavoro_sedentario": 10},
      "step2_storia_clinica": {"patologie_attuali": ["Lombalgia cronica"], "farmaci": [], "infortuni": ""},
      "step3_abitudini": {"fumatore": False, "alcool": "raro", "ore_sonno": 7, "livello_stress": "medio"},
      "step4_alimentazione": {"pasti_giorno": 3, "allergie": [], "intolleranze": []},
      "step5_attivita_fisica": {"sport_praticati": "Nessuno", "frequenza_settimanale": 0, "esperienza_palestra": "principiante"},
      "step6_obiettivi": {"obiettivo_primario": "Correzione posturale", "obiettivo_secondario": "Riduzione dolore lombare", "motivazione": "Qualita della vita"}}),

    ("Silvia", "Martini", "3332244556", "silvia.martini@yahoo.it", "1987-01-19", "Donna", "Attivo", "2025-10-05",
     "Commercialista 39 anni. Vuole perdere 10kg prima dell'estate. 2x/settimana.",
     {"step1_dati_personali": {"professione": "Commercialista", "ore_lavoro_sedentario": 9},
      "step2_storia_clinica": {"patologie_attuali": [], "farmaci": [], "infortuni": ""},
      "step3_abitudini": {"fumatore": False, "alcool": "social", "ore_sonno": 6, "livello_stress": "alto"},
      "step4_alimentazione": {"pasti_giorno": 3, "allergie": [], "intolleranze": []},
      "step5_attivita_fisica": {"sport_praticati": "Nessuno", "frequenza_settimanale": 0, "esperienza_palestra": "principiante"},
      "step6_obiettivi": {"obiettivo_primario": "Dimagrimento", "obiettivo_secondario": "Tonificazione", "motivazione": "Prova costume estate 2026"}}),

    ("Davide", "Rizzo", "3289900112", "davide.rizzo@hotmail.it", "1996-08-03", "Uomo", "Attivo", "2025-11-10",
     "Personal chef. Fisico atletico. Vuole competere nel natural bodybuilding.",
     {"step1_dati_personali": {"professione": "Chef", "ore_lavoro_sedentario": 0},
      "step2_storia_clinica": {"patologie_attuali": [], "farmaci": [], "infortuni": "Strappo pettorale dx 2023"},
      "step3_abitudini": {"fumatore": False, "alcool": "mai", "ore_sonno": 8, "livello_stress": "basso"},
      "step4_alimentazione": {"pasti_giorno": 6, "allergie": [], "intolleranze": []},
      "step5_attivita_fisica": {"sport_praticati": "Bodybuilding 5x/settimana", "frequenza_settimanale": 5, "esperienza_palestra": "avanzato"},
      "step6_obiettivi": {"obiettivo_primario": "Preparazione gara bodybuilding", "obiettivo_secondario": "Simmetria muscolare", "motivazione": "Prima gara natural ottobre 2026"}}),

    ("Federica", "Costa", "3477788990", "federica.costa@gmail.com", "1999-04-25", "Donna", "Attivo", "2025-12-01",
     "Infermiera turni. Soffre di ansia. L'allenamento la aiuta molto. 3x/settimana.",
     {"step1_dati_personali": {"professione": "Infermiera", "ore_lavoro_sedentario": 2},
      "step2_storia_clinica": {"patologie_attuali": ["Disturbo d'ansia generalizzato"], "farmaci": ["Paroxetina 10mg"], "infortuni": ""},
      "step3_abitudini": {"fumatore": False, "alcool": "raro", "ore_sonno": 5, "livello_stress": "molto alto"},
      "step4_alimentazione": {"pasti_giorno": 3, "allergie": [], "intolleranze": ["Nichel"]},
      "step5_attivita_fisica": {"sport_praticati": "Nessuno", "frequenza_settimanale": 0, "esperienza_palestra": "principiante"},
      "step6_obiettivi": {"obiettivo_primario": "Benessere mentale", "obiettivo_secondario": "Tonificazione", "motivazione": "Gestione ansia e autostima"}}),

    ("Paolo", "Galli", "3204455667", "paolo.galli@alice.it", "1965-10-30", "Uomo", "Attivo", "2025-09-10",
     "Pensionato ex muratore 60 anni. Spalle e ginocchia usurate. Silver fitness. Fedelissimo.",
     {"step1_dati_personali": {"professione": "Pensionato (ex muratore)", "ore_lavoro_sedentario": 4},
      "step2_storia_clinica": {"patologie_attuali": ["Artrosi spalla dx", "Gonartrosi bilaterale"], "farmaci": [], "infortuni": "Lesione cuffia rotatori 2015"},
      "step3_abitudini": {"fumatore": False, "alcool": "vino ai pasti", "ore_sonno": 7, "livello_stress": "basso"},
      "step4_alimentazione": {"pasti_giorno": 3, "allergie": [], "intolleranze": []},
      "step5_attivita_fisica": {"sport_praticati": "Giardinaggio", "frequenza_settimanale": 3, "esperienza_palestra": "principiante"},
      "step6_obiettivi": {"obiettivo_primario": "Mobilita articolare", "obiettivo_secondario": "Forza funzionale", "motivazione": "Restare autosufficiente"}}),

    ("Martina", "Barbieri", "3461177889", "martina.barbieri@gmail.com", "2001-12-14", "Donna", "Attivo", "2025-11-25",
     "Studentessa scienze motorie. Vuole imparare programmazione seria. Talento naturale.",
     {"step1_dati_personali": {"professione": "Studentessa scienze motorie", "ore_lavoro_sedentario": 4},
      "step2_storia_clinica": {"patologie_attuali": [], "farmaci": [], "infortuni": ""},
      "step3_abitudini": {"fumatore": False, "alcool": "social", "ore_sonno": 8, "livello_stress": "basso"},
      "step4_alimentazione": {"pasti_giorno": 4, "allergie": [], "intolleranze": []},
      "step5_attivita_fisica": {"sport_praticati": "Pallavolo + palestra", "frequenza_settimanale": 4, "esperienza_palestra": "intermedio"},
      "step6_obiettivi": {"obiettivo_primario": "Forza e tecnica", "obiettivo_secondario": "Apprendimento programmazione", "motivazione": "Futuro lavoro"}}),

    ("Simone", "Marchetti", "3395544332", "simone.marchetti@tiscali.it", "1978-09-07", "Uomo", "Attivo", "2025-12-15",
     "Vigile urbano 47 anni. Sovrappeso (BMI 29). Moglie lo ha iscritto. Si diverte.",
     {"step1_dati_personali": {"professione": "Vigile urbano", "ore_lavoro_sedentario": 4},
      "step2_storia_clinica": {"patologie_attuali": ["Sovrappeso"], "farmaci": [], "infortuni": "Distorsione ginocchio sx 2019"},
      "step3_abitudini": {"fumatore": True, "alcool": "moderato", "ore_sonno": 7, "livello_stress": "medio"},
      "step4_alimentazione": {"pasti_giorno": 3, "allergie": [], "intolleranze": []},
      "step5_attivita_fisica": {"sport_praticati": "Nessuno", "frequenza_settimanale": 0, "esperienza_palestra": "principiante"},
      "step6_obiettivi": {"obiettivo_primario": "Perdita peso", "obiettivo_secondario": "Condizionamento", "motivazione": "Moglie e salute"}}),

    ("Claudia", "Ferrara", "3268899001", "claudia.ferrara@virgilio.it", "1983-05-21", "Donna", "Attivo", "2025-10-25",
     "Insegnante elementare. Fibromialgia diagnosticata. Allenamento adattato. Migliora moltissimo.",
     {"step1_dati_personali": {"professione": "Insegnante", "ore_lavoro_sedentario": 5},
      "step2_storia_clinica": {"patologie_attuali": ["Fibromialgia"], "farmaci": ["Duloxetina 30mg", "Ciclobenzaprina al bisogno"], "infortuni": ""},
      "step3_abitudini": {"fumatore": False, "alcool": "mai", "ore_sonno": 5, "livello_stress": "alto"},
      "step4_alimentazione": {"pasti_giorno": 3, "allergie": [], "intolleranze": ["Glutine"]},
      "step5_attivita_fisica": {"sport_praticati": "Camminate leggere", "frequenza_settimanale": 2, "esperienza_palestra": "principiante"},
      "step6_obiettivi": {"obiettivo_primario": "Gestione dolore", "obiettivo_secondario": "Qualita del sonno", "motivazione": "Vivere meglio con la fibromialgia"}}),

    ("Tommaso", "Bruno", "3417766554", "tommaso.bruno@gmail.com", "1991-03-16", "Uomo", "Attivo", "2025-12-20",
     "Architetto. Runner amatoriale (mezza maratona). Vuole integrare forza.",
     {"step1_dati_personali": {"professione": "Architetto", "ore_lavoro_sedentario": 8},
      "step2_storia_clinica": {"patologie_attuali": [], "farmaci": [], "infortuni": "Sindrome banda ileotibiale 2024"},
      "step3_abitudini": {"fumatore": False, "alcool": "social", "ore_sonno": 7, "livello_stress": "medio"},
      "step4_alimentazione": {"pasti_giorno": 4, "allergie": [], "intolleranze": []},
      "step5_attivita_fisica": {"sport_praticati": "Running 4x/settimana", "frequenza_settimanale": 4, "esperienza_palestra": "principiante"},
      "step6_obiettivi": {"obiettivo_primario": "Prevenzione infortuni running", "obiettivo_secondario": "Forza gambe", "motivazione": "Maratona autunno 2026"}}),

    ("Giorgia", "Santoro", "3253322110", "giorgia.santoro@gmail.com", "1994-07-09", "Donna", "Attivo", "2026-01-10",
     "Marketing manager. Post-gravidanza 12 mesi. Pavimento pelvico + dimagrimento.",
     {"step1_dati_personali": {"professione": "Marketing manager", "ore_lavoro_sedentario": 8},
      "step2_storia_clinica": {"patologie_attuali": ["Debolezza pavimento pelvico"], "farmaci": [], "infortuni": ""},
      "step3_abitudini": {"fumatore": False, "alcool": "raro", "ore_sonno": 5, "livello_stress": "alto"},
      "step4_alimentazione": {"pasti_giorno": 3, "allergie": [], "intolleranze": ["Lattosio"]},
      "step5_attivita_fisica": {"sport_praticati": "Nessuno da 18 mesi", "frequenza_settimanale": 0, "esperienza_palestra": "intermedio"},
      "step6_obiettivi": {"obiettivo_primario": "Recupero post-gravidanza", "obiettivo_secondario": "Dimagrimento", "motivazione": "Tornare in forma"}}),

    ("Nicola", "Mancini", "3484433221", "nicola.mancini@fastwebnet.it", "1980-11-28", "Uomo", "Attivo", "2025-09-08",
     "Dentista. Sindrome tunnel carpale. Postura e forza upper body. Cliente storico.",
     {"step1_dati_personali": {"professione": "Dentista", "ore_lavoro_sedentario": 6},
      "step2_storia_clinica": {"patologie_attuali": ["Sindrome tunnel carpale bilaterale"], "farmaci": [], "infortuni": ""},
      "step3_abitudini": {"fumatore": False, "alcool": "moderato", "ore_sonno": 7, "livello_stress": "medio"},
      "step4_alimentazione": {"pasti_giorno": 3, "allergie": [], "intolleranze": []},
      "step5_attivita_fisica": {"sport_praticati": "Tennis 1x/settimana", "frequenza_settimanale": 1, "esperienza_palestra": "intermedio"},
      "step6_obiettivi": {"obiettivo_primario": "Correzione posturale", "obiettivo_secondario": "Forza e mobilita polsi", "motivazione": "Prevenzione sindrome tunnel carpale"}}),

    ("Elisa", "Vitale", "3379911002", "elisa.vitale@libero.it", "2002-06-05", "Donna", "Attivo", "2026-01-20",
     "Cameriera. Piedi piatti. Prima volta in palestra. Timida ma determinata.",
     {"step1_dati_personali": {"professione": "Cameriera", "ore_lavoro_sedentario": 0},
      "step2_storia_clinica": {"patologie_attuali": ["Piattismo bilaterale"], "farmaci": [], "infortuni": ""},
      "step3_abitudini": {"fumatore": False, "alcool": "social", "ore_sonno": 7, "livello_stress": "medio"},
      "step4_alimentazione": {"pasti_giorno": 3, "allergie": [], "intolleranze": []},
      "step5_attivita_fisica": {"sport_praticati": "Nessuno", "frequenza_settimanale": 0, "esperienza_palestra": "principiante"},
      "step6_obiettivi": {"obiettivo_primario": "Tonificazione generale", "obiettivo_secondario": "Autostima", "motivazione": "Sentirsi meglio"}}),

    ("Riccardo", "Esposito", "3406655443", "riccardo.esposito@gmail.com", "1989-02-14", "Uomo", "Inattivo", "2025-09-30",
     "Fotografo. Ha smesso dopo 2 mesi per lavoro. Possibile rientro ad aprile.",
     {"step1_dati_personali": {"professione": "Fotografo freelance", "ore_lavoro_sedentario": 5},
      "step2_storia_clinica": {"patologie_attuali": [], "farmaci": [], "infortuni": ""},
      "step3_abitudini": {"fumatore": True, "alcool": "moderato", "ore_sonno": 6, "livello_stress": "alto"},
      "step4_alimentazione": {"pasti_giorno": 2, "allergie": [], "intolleranze": []},
      "step5_attivita_fisica": {"sport_praticati": "Nessuno", "frequenza_settimanale": 0, "esperienza_palestra": "principiante"},
      "step6_obiettivi": {"obiettivo_primario": "Forma generale", "obiettivo_secondario": "Energia", "motivazione": "Stare meglio"}}),

    ("Aurora", "Pellegrini", "3235544332", "aurora.pellegrini@gmail.com", "1997-09-18", "Donna", "Attivo", "2026-02-01",
     "Psicologa. Scoliosi. Vuole forza e postura. Molto analitica sull'allenamento.",
     {"step1_dati_personali": {"professione": "Psicologa", "ore_lavoro_sedentario": 7},
      "step2_storia_clinica": {"patologie_attuali": ["Scoliosi idiopatica (15 gradi)"], "farmaci": [], "infortuni": ""},
      "step3_abitudini": {"fumatore": False, "alcool": "raro", "ore_sonno": 7, "livello_stress": "medio"},
      "step4_alimentazione": {"pasti_giorno": 3, "allergie": [], "intolleranze": []},
      "step5_attivita_fisica": {"sport_praticati": "Pilates 1x/settimana", "frequenza_settimanale": 1, "esperienza_palestra": "principiante"},
      "step6_obiettivi": {"obiettivo_primario": "Correzione posturale", "obiettivo_secondario": "Forza core", "motivazione": "Gestire scoliosi e dolore"}}),

    ("Lorenzo", "Fabbri", "3441122334", "lorenzo.fabbri@outlook.it", "1986-04-02", "Uomo", "Attivo", "2025-10-15",
     "Avvocato 40 anni. Ex nuotatore agonista. Vuole tornare in forma. 3x/settimana.",
     {"step1_dati_personali": {"professione": "Avvocato", "ore_lavoro_sedentario": 9},
      "step2_storia_clinica": {"patologie_attuali": [], "farmaci": [], "infortuni": "Lussazione spalla sx 2010 (nuoto)"},
      "step3_abitudini": {"fumatore": False, "alcool": "social", "ore_sonno": 6, "livello_stress": "alto"},
      "step4_alimentazione": {"pasti_giorno": 3, "allergie": [], "intolleranze": []},
      "step5_attivita_fisica": {"sport_praticati": "Ex nuoto agonistico, ora sedentario", "frequenza_settimanale": 0, "esperienza_palestra": "intermedio"},
      "step6_obiettivi": {"obiettivo_primario": "Ricomposizione corporea", "obiettivo_secondario": "Resistenza", "motivazione": "Tornare in forma come quando nuotavo"}}),

    ("Beatrice", "Marini", "3367788990", "beatrice.marini@gmail.com", "1992-11-08", "Donna", "Attivo", "2025-11-15",
     "Veterinaria. Problemi cervicale cronica. Forza e postura. Molto puntuale.",
     {"step1_dati_personali": {"professione": "Veterinaria", "ore_lavoro_sedentario": 3},
      "step2_storia_clinica": {"patologie_attuali": ["Cervicalgia cronica"], "farmaci": [], "infortuni": ""},
      "step3_abitudini": {"fumatore": False, "alcool": "raro", "ore_sonno": 7, "livello_stress": "medio"},
      "step4_alimentazione": {"pasti_giorno": 3, "allergie": ["Frutta secca"], "intolleranze": []},
      "step5_attivita_fisica": {"sport_praticati": "Nessuno regolare", "frequenza_settimanale": 0, "esperienza_palestra": "principiante"},
      "step6_obiettivi": {"obiettivo_primario": "Riduzione dolore cervicale", "obiettivo_secondario": "Forza generale", "motivazione": "Lavorare senza dolore"}}),

    ("Filippo", "Orlando", "3218899001", "filippo.orlando@gmail.com", "2004-01-22", "Uomo", "Attivo", "2026-02-10",
     "Liceale 22 anni. Gioca a basket. Vuole verticalita e esplosivita. Molto motivato.",
     {"step1_dati_personali": {"professione": "Studente liceo/universita", "ore_lavoro_sedentario": 5},
      "step2_storia_clinica": {"patologie_attuali": [], "farmaci": [], "infortuni": "Distorsione caviglia dx basket 2025"},
      "step3_abitudini": {"fumatore": False, "alcool": "mai", "ore_sonno": 8, "livello_stress": "basso"},
      "step4_alimentazione": {"pasti_giorno": 4, "allergie": [], "intolleranze": []},
      "step5_attivita_fisica": {"sport_praticati": "Basket 3x/settimana", "frequenza_settimanale": 3, "esperienza_palestra": "principiante"},
      "step6_obiettivi": {"obiettivo_primario": "Esplosivita e salto", "obiettivo_secondario": "Prevenzione infortuni", "motivazione": "Giocare a basket piu forte"}}),
]

print("\n--- Clienti (30) ---")
for i, (nome, cognome, tel, email, nascita, sesso, stato, created, note, anamnesi) in enumerate(CLIENTI):
    conn.execute("""
        INSERT INTO clienti (id, trainer_id, nome, cognome, telefono, email, data_nascita, sesso, stato, data_creazione, note_interne, anamnesi_json)
        VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (i + 1, nome, cognome, tel, email, nascita, sesso, stato, created, note, json.dumps(anamnesi) if anamnesi else None))
    tag = " *" if stato == "Inattivo" else ""
    print(f"  [{i+1:2d}] {nome} {cognome} ({sesso}, {nascita[:4]}){tag}")

conn.commit()
print(f"  Totale: {len(CLIENTI)} clienti ({sum(1 for c in CLIENTI if c[6]=='Attivo')} attivi, {sum(1 for c in CLIENTI if c[6]=='Inattivo')} inattivi)")


# ══════════════════════════════════════════════════════════════
# CONTRATTI (realistici, date distribuite)
# ══════════════════════════════════════════════════════════════

# (client_id, tipo, crediti, prezzo, data_inizio, data_scadenza, acconto, metodo, note, rinnovo_di)
CONTRATTI = [
    # Clienti storici (settembre-ottobre 2025) — primo contratto scaduto + rinnovo
    (1,  "PT 12 Sedute",      12,  540, "2025-09-10", "2025-12-31", 100, "CONTANTI", "Primo pacchetto Marco", None),
    (1,  "PT 24 Sedute",      24,  960, "2026-01-05", "2026-06-30", 200, "POS", "Rinnovo semestrale Marco", 1),
    (2,  "PT 12 Sedute",      12,  540, "2025-09-15", "2025-12-31", 100, "POS", "Primo pacchetto Giulia", None),
    (2,  "PT 24 Sedute",      24,  960, "2026-01-10", "2026-06-30", 200, "CONTANTI", "Rinnovo Giulia", 3),
    (3,  "PT 36 Premium",     36, 1440, "2025-09-25", "2026-09-25", 300, "BONIFICO", "Annuale Roberto", None),
    (4,  "Posturale 16",      16,  640, "2025-10-15", "2026-02-28", 150, "POS", "Post-partum Francesca", None),
    (4,  "Posturale 16",      16,  640, "2026-03-01", "2026-06-30", 150, "POS", "Rinnovo Francesca", 6),
    (5,  "Performance 20",    20, 1000, "2025-10-05", "2026-04-30", 200, "BONIFICO", "Prep gara Alessandro", None),
    (6,  "Silver Age 24",     24,  720, "2025-10-01", "2026-03-31", 200, "CONTANTI", "Prevenzione Elena", None),
    (6,  "Silver Age 24",     24,  720, "2026-04-01", "2026-09-30", 200, "CONTANTI", "Rinnovo Elena", 9),
    (7,  "PT 12 Sedute",      12,  480, "2025-11-10", "2026-03-10", 100, "POS", "Primo pacchetto Luca", None),
    (8,  "PT 16 Sedute",      16,  720, "2025-10-20", "2026-03-20", 150, "BONIFICO", "Dimagrimento Sara", None),
    (8,  "PT 16 Sedute",      16,  720, "2026-03-21", "2026-07-31", 150, "BONIFICO", "Rinnovo Sara", 12),
    (9,  "Riabilitazione 20", 20,  900, "2025-12-15", "2026-06-15", 200, "POS", "Post LCA Andrea", None),
    (10, "PT 8 Trial",         8,  360, "2025-09-20", "2025-12-20", 100, "CONTANTI", "Trial Valentina (scaduto)", None),
    (11, "Metabolico 16",     16,  640, "2025-11-25", "2026-04-25", 150, "POS", "Controllo glicemico Giuseppe", None),
    # Nuovi iscritti (novembre-marzo)
    (13, "Posturale 12",      12,  540, "2025-10-25", "2026-02-25", 100, "POS", "Postura Matteo", None),
    (13, "Posturale 16",      16,  640, "2026-03-01", "2026-06-30", 150, "POS", "Rinnovo Matteo", 17),
    (14, "PT 16 Sedute",      16,  640, "2025-10-10", "2026-03-10", 100, "CONTANTI", "Dimagrimento Silvia", None),
    (15, "Performance 24",    24, 1200, "2025-11-15", "2026-05-15", 300, "BONIFICO", "Prep gara Davide", None),
    (16, "PT 12 Sedute",      12,  540, "2025-12-05", "2026-04-05", 100, "POS", "Benessere Federica", None),
    (17, "Silver Age 24",     24,  720, "2025-09-15", "2026-03-15", 200, "CONTANTI", "Mobilita Paolo", None),
    (17, "Silver Age 24",     24,  720, "2026-03-16", "2026-09-16", 200, "CONTANTI", "Rinnovo Paolo", 22),
    (18, "PT 12 Sedute",      12,  480, "2025-12-01", "2026-04-01", 100, "POS", "Forza Martina", None),
    (19, "PT 12 Sedute",      12,  480, "2025-12-20", "2026-04-20", 100, "CONTANTI", "Dimagrimento Simone", None),
    (20, "PT 16 Adattato",    16,  720, "2025-11-01", "2026-04-01", 150, "BONIFICO", "Fibromialgia Claudia", None),
    (21, "PT 12 Sedute",      12,  540, "2026-01-05", "2026-05-05", 100, "POS", "Running Tommaso", None),
    (22, "PT 12 Sedute",      12,  540, "2026-01-15", "2026-05-15", 100, "POS", "Post-gravidanza Giorgia", None),
    (23, "PT 24 Premium",     24, 1080, "2025-09-10", "2026-03-10", 200, "BONIFICO", "Postura Nicola", None),
    (23, "PT 24 Premium",     24, 1080, "2026-03-11", "2026-09-11", 200, "BONIFICO", "Rinnovo Nicola", 29),
    (24, "PT 8 Starter",       8,  360, "2026-01-25", "2026-04-25", 100, "POS", "Starter Elisa", None),
    (25, "PT 8 Trial",         8,  360, "2025-10-01", "2025-12-31", 100, "CONTANTI", "Trial Riccardo (scaduto)", None),
    (26, "PT 12 Sedute",      12,  540, "2026-02-05", "2026-06-05", 100, "POS", "Postura Aurora", None),
    (27, "PT 16 Sedute",      16,  720, "2025-10-20", "2026-04-20", 150, "POS", "Ricomp Lorenzo", None),
    (28, "PT 12 Sedute",      12,  540, "2025-11-20", "2026-04-20", 100, "CONTANTI", "Cervicale Beatrice", None),
    (29, "PT 8 Starter",       8,  360, "2026-02-15", "2026-05-15", 100, "POS", "Basket Filippo", None),
]

print("\n--- Contratti ---")
contract_ids = {}  # client_id -> [contract_id, ...]
for idx, (cid, tipo, crediti, prezzo, inizio, scadenza, acconto, metodo, note, rinnovo) in enumerate(CONTRATTI):
    c_id = idx + 1
    # Calcola stato pagamento e crediti usati in base all'eta del contratto
    inizio_d = date.fromisoformat(inizio)
    scadenza_d = date.fromisoformat(scadenza)
    days_active = (TODAY - inizio_d).days
    total_days = (scadenza_d - inizio_d).days
    is_expired = scadenza_d < TODAY

    # Crediti usati proporzionali al tempo trascorso
    if is_expired:
        crediti_usati = crediti  # contratto finito
    else:
        progress = min(1.0, max(0.0, days_active / max(total_days, 1)))
        crediti_usati = min(crediti, int(crediti * progress * random.uniform(0.7, 1.0)))

    # Stato pagamento
    stato_pag = "PENDENTE"
    chiuso = False
    if is_expired:
        stato_pag = "SALDATO"
        chiuso = True
        totale_versato = float(prezzo)
    elif days_active > total_days * 0.8:
        stato_pag = "SALDATO"
        totale_versato = float(prezzo)
    elif days_active > total_days * 0.3:
        stato_pag = "PARZIALE"
        totale_versato = float(acconto + (prezzo - acconto) * random.uniform(0.4, 0.8))
    else:
        totale_versato = float(acconto)

    if stato_pag == "SALDATO" and crediti_usati >= crediti:
        chiuso = True

    conn.execute("""
        INSERT INTO contratti (id, trainer_id, id_cliente, tipo_pacchetto, data_vendita, data_inizio, data_scadenza,
            crediti_totali, crediti_usati, prezzo_totale, acconto, totale_versato, stato_pagamento, note, chiuso, rinnovo_di)
        VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (c_id, cid, tipo, inizio, inizio, scadenza, crediti, crediti_usati, float(prezzo), float(acconto),
          round(totale_versato, 2), stato_pag, note, chiuso, rinnovo))

    # CashMovement per acconto
    if acconto > 0:
        conn.execute("""
            INSERT INTO movimenti_cassa (trainer_id, data_movimento, data_effettiva, tipo, categoria, importo, metodo, id_cliente, id_contratto, note, operatore)
            VALUES (1, ?, ?, 'ENTRATA', 'ACCONTO_CONTRATTO', ?, ?, ?, ?, ?, 'API')
        """, (inizio, inizio, float(acconto), metodo, cid, c_id, f"Acconto {tipo} - {CLIENTI[cid-1][0]} {CLIENTI[cid-1][1]}"))

    if cid not in contract_ids:
        contract_ids[cid] = []
    contract_ids[cid].append(c_id)

conn.commit()
print(f"  Totale: {len(CONTRATTI)} contratti")


# ══════════════════════════════════════════════════════════════
# RATE (distribuite nel tempo, alcune pagate)
# ══════════════════════════════════════════════════════════════

print("\n--- Rate e pagamenti ---")
rate_count = 0
payment_count = 0

for idx, (cid, tipo, crediti, prezzo, inizio, scadenza, acconto, metodo, note, rinnovo) in enumerate(CONTRATTI):
    c_id = idx + 1
    residuo = prezzo - acconto
    if residuo <= 0:
        continue

    inizio_d = date.fromisoformat(inizio)
    scadenza_d = date.fromisoformat(scadenza)

    # 2-5 rate distribuite
    n_rate = min(5, max(2, int(residuo / 150)))
    importo_rata = round(residuo / n_rate, 2)

    for r_idx in range(n_rate):
        data_rata = inizio_d + timedelta(days=30 * (r_idx + 1))
        if data_rata > scadenza_d:
            data_rata = scadenza_d

        # La rata e' pagata?
        rata_stato = "PENDENTE"
        importo_saldato = 0.0

        if data_rata < TODAY - timedelta(days=7):
            # Rata scaduta da piu di una settimana -> pagata (90% probabilita)
            if random.random() < 0.9:
                rata_stato = "SALDATA"
                importo_saldato = importo_rata
        elif data_rata < TODAY:
            # Rata scaduta da poco -> 50% pagata
            if random.random() < 0.5:
                rata_stato = "SALDATA"
                importo_saldato = importo_rata

        conn.execute("""
            INSERT INTO rate_programmate (id_contratto, data_scadenza, importo_previsto, descrizione, stato, importo_saldato)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (c_id, iso(data_rata), importo_rata, f"Rata {r_idx+1}/{n_rate}", rata_stato, importo_saldato))
        rate_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        rate_count += 1

        # CashMovement per rata pagata
        if rata_stato == "SALDATA":
            # Pagata qualche giorno dopo la scadenza (realistico)
            data_pag = data_rata + timedelta(days=random.randint(0, 5))
            met_choices = ["CONTANTI", "POS", "BONIFICO"]
            conn.execute("""
                INSERT INTO movimenti_cassa (trainer_id, data_movimento, data_effettiva, tipo, categoria, importo, metodo, id_cliente, id_contratto, id_rata, note, operatore)
                VALUES (1, ?, ?, 'ENTRATA', 'PAGAMENTO_RATA', ?, ?, ?, ?, ?, ?, 'API')
            """, (iso(data_pag), iso(data_pag), importo_rata, random.choice(met_choices), cid, c_id, rate_id,
                  f"Pagamento rata {r_idx+1} - {CLIENTI[cid-1][0]} {CLIENTI[cid-1][1]}"))
            payment_count += 1

conn.commit()
print(f"  Rate: {rate_count} ({payment_count} pagate)")


# ══════════════════════════════════════════════════════════════
# AGENDA (sessioni PT distribuite nei mesi)
# ══════════════════════════════════════════════════════════════

print("\n--- Agenda ---")
event_count = 0
HOURS = [8, 9, 10, 11, 14, 15, 16, 17, 18, 19]

for idx, (cid, tipo, crediti, prezzo, inizio, scadenza, acconto, metodo, note, rinnovo) in enumerate(CONTRATTI):
    c_id = idx + 1
    inizio_d = date.fromisoformat(inizio)
    scadenza_d = date.fromisoformat(scadenza)

    # Recupera crediti usati
    crediti_usati_row = conn.execute("SELECT crediti_usati FROM contratti WHERE id=?", (c_id,)).fetchone()
    n_events = crediti_usati_row[0] if crediti_usati_row else 0
    if n_events == 0:
        continue

    # Distribuisci eventi uniformemente nel periodo attivo
    active_days = min((TODAY - inizio_d).days, (scadenza_d - inizio_d).days)
    if active_days <= 0:
        continue

    interval = max(2, active_days // n_events)

    for e_idx in range(n_events):
        day = inizio_d + timedelta(days=interval * e_idx + random.randint(0, max(0, interval - 2)))
        if day > TODAY:
            break
        if day.weekday() == 6:  # Skip domenica
            day += timedelta(days=1)

        hour = random.choice(HOURS)
        dt_start = datetime(day.year, day.month, day.day, hour, 0)
        dt_end = dt_start + timedelta(hours=1)

        stato = "Completato" if day < TODAY else "Programmato"

        conn.execute("""
            INSERT INTO agenda (trainer_id, data_inizio, data_fine, categoria, titolo, id_cliente, id_contratto, stato, data_creazione)
            VALUES (1, ?, ?, 'PT', ?, ?, ?, ?, ?)
        """, (dt_start.isoformat(), dt_end.isoformat(), f"Sessione {CLIENTI[cid-1][0]}",
              cid, c_id, stato, inizio))
        event_count += 1

# Sessioni future (prossimi 7 giorni)
active_clients = [i+1 for i, c in enumerate(CLIENTI) if c[6] == "Attivo" and i != 11]  # no Chiara Fontana (nuova)
for day_off in range(1, 8):
    day = TODAY + timedelta(days=day_off)
    if day.weekday() == 6:
        continue
    # 4-6 sessioni al giorno
    n_day = random.randint(4, 6)
    day_clients = random.sample(active_clients, min(n_day, len(active_clients)))
    for cid in day_clients:
        hour = random.choice(HOURS)
        dt_start = datetime(day.year, day.month, day.day, hour, 0)
        dt_end = dt_start + timedelta(hours=1)
        # Trova contratto attivo
        active_c = conn.execute("""
            SELECT id FROM contratti WHERE id_cliente=? AND chiuso=0 AND data_scadenza>=? ORDER BY id DESC LIMIT 1
        """, (cid, iso(TODAY))).fetchone()
        c_id = active_c[0] if active_c else None

        conn.execute("""
            INSERT INTO agenda (trainer_id, data_inizio, data_fine, categoria, titolo, id_cliente, id_contratto, stato, data_creazione)
            VALUES (1, ?, ?, 'PT', ?, ?, ?, 'Programmato', ?)
        """, (dt_start.isoformat(), dt_end.isoformat(), f"Sessione {CLIENTI[cid-1][0]}",
              cid, c_id, iso(TODAY)))
        event_count += 1

# Corsi e colloqui
for _ in range(15):
    day_off = random.randint(-60, 10)
    day = TODAY + timedelta(days=day_off)
    if day.weekday() == 6:
        continue
    hour = random.choice([10, 16, 18])
    dt_start = datetime(day.year, day.month, day.day, hour, 0)
    dt_end = dt_start + timedelta(hours=1)
    cat = random.choice(["CORSO", "SALA", "CORSO"])
    titolo = random.choice(["Pilates Gruppo", "Stretching", "Functional Training", "Sala pesi libera"])
    stato = "Completato" if day < TODAY else "Programmato"
    conn.execute("""
        INSERT INTO agenda (trainer_id, data_inizio, data_fine, categoria, titolo, stato, data_creazione)
        VALUES (1, ?, ?, ?, ?, ?, ?)
    """, (dt_start.isoformat(), dt_end.isoformat(), cat, titolo, stato, iso(TODAY)))
    event_count += 1

# Colloquio Chiara Fontana domani
tomorrow = TODAY + timedelta(days=1)
dt_start = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 10, 0)
dt_end = dt_start + timedelta(minutes=45)
conn.execute("""
    INSERT INTO agenda (trainer_id, data_inizio, data_fine, categoria, titolo, id_cliente, stato, data_creazione)
    VALUES (1, ?, ?, 'COLLOQUIO', 'Primo colloquio Chiara Fontana', 12, 'Programmato', ?)
""", (dt_start.isoformat(), dt_end.isoformat(), iso(TODAY)))
event_count += 1

conn.commit()
print(f"  Eventi totali: {event_count}")


# ══════════════════════════════════════════════════════════════
# MISURAZIONI (ogni 3-4 settimane per clienti attivi)
# ══════════════════════════════════════════════════════════════

print("\n--- Misurazioni ---")
meas_count = 0

# Profili con progressi realistici nel tempo
# (client_id, metriche: [(id_metrica, valore_iniziale, delta_per_mese)])
MEAS_PROFILES = [
    (1,  [(1, 92.0, -1.2), (3, 24.0, -0.7)]),    # Marco: dimagrisce
    (2,  [(1, 58.0, -0.2), (3, 22.0, -0.5)]),     # Giulia: stabile, tonica
    (3,  [(1, 85.0, 0.4), (3, 18.0, -0.5)]),       # Roberto: +massa, -grasso
    (4,  [(1, 68.0, -0.5)]),                         # Francesca: lieve dimagr
    (5,  [(1, 82.0, 0.0), (20, 140.0, 5.0)]),      # Alessandro: stabile, +squat
    (6,  [(1, 65.0, 0.0)]),                          # Elena: stabile
    (7,  [(1, 62.0, 0.8), (3, 12.0, 0.0)]),        # Luca: +massa
    (8,  [(1, 73.0, -1.0), (3, 28.0, -0.6)]),      # Sara: dimagrisce
    (9,  [(1, 88.0, -0.3)]),                         # Andrea: lieve
    (11, [(1, 98.0, -1.5), (3, 32.0, -0.5)]),      # Giuseppe: dimagrisce
    (13, [(1, 78.0, -0.1)]),                         # Matteo
    (14, [(1, 72.0, -0.8)]),                         # Silvia
    (15, [(1, 82.0, 0.3), (3, 10.0, -0.3)]),       # Davide: +massa
    (17, [(1, 80.0, -0.1)]),                         # Paolo
    (19, [(1, 95.0, -0.8)]),                         # Simone
    (20, [(1, 62.0, 0.0)]),                          # Claudia
    (23, [(1, 82.0, -0.3)]),                         # Nicola
    (27, [(1, 78.0, -0.2)]),                         # Lorenzo
    (28, [(1, 60.0, 0.0)]),                          # Beatrice
]

for cid, metrics in MEAS_PROFILES:
    # Data inizio cliente
    client_start = date.fromisoformat(CLIENTI[cid - 1][7])
    # Prima misurazione a +7gg dal primo appuntamento
    first_meas = client_start + timedelta(days=7)

    meas_date = first_meas
    session_num = 0
    while meas_date <= TODAY:
        session_num += 1
        months_elapsed = (meas_date - first_meas).days / 30.0

        conn.execute("""
            INSERT INTO misurazioni_cliente (id_cliente, trainer_id, data_misurazione, note)
            VALUES (?, 1, ?, ?)
        """, (cid, iso(meas_date), f"Misurazione #{session_num}"))
        mid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        for metric_id, base_val, delta in metrics:
            val = round(base_val + delta * months_elapsed + random.uniform(-0.3, 0.3), 1)
            conn.execute("""
                INSERT INTO valori_misurazione (id_misurazione, id_metrica, valore)
                VALUES (?, ?, ?)
            """, (mid, metric_id, val))

        meas_count += 1
        # Prossima misurazione tra 21-28 giorni
        meas_date += timedelta(days=random.randint(21, 28))

conn.commit()
print(f"  Sessioni misurazione: {meas_count}")


# ══════════════════════════════════════════════════════════════
# OBIETTIVI
# ══════════════════════════════════════════════════════════════

print("\n--- Obiettivi ---")
GOALS = [
    (1,  1, "diminuire", 82.0, 92.0, "2025-09-10", "2025-09-10", "2026-06-30", 1, "Peso forma entro estate"),
    (1,  3, "diminuire", 18.0, 24.0, "2025-09-10", "2025-09-10", "2026-06-30", 2, "Body fat < 18%"),
    (2,  1, "mantenere", None, 58.0, "2025-09-15", "2025-09-15", None, 3, "Mantenere peso attuale"),
    (3,  1, "aumentare", 90.0, 85.0, "2025-09-25", "2025-09-25", "2026-09-25", 1, "90kg massa magra"),
    (5,  20, "aumentare", 160.0, 140.0, "2025-10-05", "2025-10-05", "2026-05-01", 1, "Squat 160kg per gara"),
    (7,  1, "aumentare", 70.0, 62.0, "2025-11-10", "2025-11-10", "2026-06-30", 1, "+8kg massa"),
    (8,  1, "diminuire", 65.0, 73.0, "2025-10-20", "2025-10-20", "2026-07-31", 1, "-8kg entro estate"),
    (11, 1, "diminuire", 88.0, 98.0, "2025-11-25", "2025-11-25", "2026-08-31", 1, "Target medico -10kg"),
    (14, 1, "diminuire", 62.0, 72.0, "2025-10-10", "2025-10-10", "2026-06-30", 1, "-10kg estate"),
    (15, 3, "diminuire", 7.0, 10.0, "2025-11-15", "2025-11-15", "2026-10-01", 1, "Body fat 7% per gara"),
    (19, 1, "diminuire", 85.0, 95.0, "2025-12-20", "2025-12-20", "2026-06-30", 1, "-10kg"),
    (27, 1, "diminuire", 75.0, 78.0, "2025-10-20", "2025-10-20", "2026-04-20", 2, "Ricomposizione -3kg"),
]

for cid, mid, dire, target, baseline, data_base, ini, sca, pri, note in GOALS:
    conn.execute("""
        INSERT INTO obiettivi_cliente
        (id_cliente, trainer_id, id_metrica, direzione, valore_target, valore_baseline,
         data_baseline, data_inizio, data_scadenza, tipo_obiettivo, priorita, stato, completato_automaticamente, note)
        VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, 'corporeo', ?, 'attivo', 0, ?)
    """, (cid, mid, dire, target, baseline, data_base, ini, sca, pri, note))

conn.commit()
print(f"  Obiettivi: {len(GOALS)}")


# ══════════════════════════════════════════════════════════════
# SPESE RICORRENTI
# ══════════════════════════════════════════════════════════════

print("\n--- Spese ricorrenti ---")
EXPENSES = [
    ("Affitto sala", "Affitto", 350.0, 1, "MENSILE", "2025-09-01"),
    ("Assicurazione RC professionale", "Assicurazione", 180.0, 15, "ANNUALE", "2025-09-01"),
    ("Commercialista", "Consulenza", 120.0, 1, "TRIMESTRALE", "2025-10-01"),
    ("Materiale consumo", "Attrezzatura", 45.0, 15, "MENSILE", "2025-09-01"),
    ("Internet fibra studio", "Utenze", 30.0, 5, "MENSILE", "2025-09-01"),
    ("Software FitManager PRO", "Software", 79.0, 1, "ANNUALE", "2026-01-01"),
]

for nome, cat, imp, gg, freq, ini in EXPENSES:
    conn.execute("""
        INSERT INTO spese_ricorrenti (trainer_id, nome, categoria, importo, giorno_scadenza, frequenza, data_inizio, attiva, data_creazione)
        VALUES (1, ?, ?, ?, ?, ?, ?, 1, ?)
    """, (nome, cat, imp, gg, freq, ini, ini))

# Conferma spese passate come movimenti cassa
for month_offset in range(7):  # settembre 2025 - marzo 2026
    month_date = date(2025, 9, 1) + timedelta(days=30 * month_offset)
    if month_date > TODAY:
        break
    # Affitto
    conn.execute("""
        INSERT INTO movimenti_cassa (trainer_id, data_movimento, data_effettiva, tipo, categoria, importo, metodo, note, operatore)
        VALUES (1, ?, ?, 'USCITA', 'Affitto', 350.0, 'BONIFICO', 'Affitto sala', 'CONFERMA_UTENTE')
    """, (iso(month_date), iso(month_date)))
    # Materiale
    conn.execute("""
        INSERT INTO movimenti_cassa (trainer_id, data_movimento, data_effettiva, tipo, categoria, importo, metodo, note, operatore)
        VALUES (1, ?, ?, 'USCITA', 'Attrezzatura', 45.0, 'POS', 'Materiale consumo', 'CONFERMA_UTENTE')
    """, (iso(date(month_date.year, month_date.month, 15)), iso(date(month_date.year, month_date.month, 15))))
    # Internet
    conn.execute("""
        INSERT INTO movimenti_cassa (trainer_id, data_movimento, data_effettiva, tipo, categoria, importo, metodo, note, operatore)
        VALUES (1, ?, ?, 'USCITA', 'Utenze', 30.0, 'BONIFICO', 'Internet fibra studio', 'CONFERMA_UTENTE')
    """, (iso(date(month_date.year, month_date.month, 5)), iso(date(month_date.year, month_date.month, 5))))

conn.commit()
print(f"  Spese ricorrenti: {len(EXPENSES)}")


# ══════════════════════════════════════════════════════════════
# MOVIMENTI MANUALI
# ══════════════════════════════════════════════════════════════

print("\n--- Movimenti manuali ---")
MANUAL_MOVS = [
    ("USCITA", "2025-09-20", 89.0, "POS", "Attrezzatura", "Elastici resistenza TheraBand set"),
    ("USCITA", "2025-10-05", 45.0, "CONTANTI", "Attrezzatura", "Tappetini yoga x3"),
    ("USCITA", "2025-10-15", 320.0, "BONIFICO", "Attrezzatura", "Kettlebell set (8-16-24kg)"),
    ("USCITA", "2025-11-10", 150.0, "BONIFICO", "Formazione", "Corso aggiornamento NSCA online"),
    ("USCITA", "2025-12-01", 29.0, "POS", "Software", "Canva Pro (contenuti social)"),
    ("ENTRATA", "2025-12-15", 80.0, "CONTANTI", "Consulenza", "Consulenza nutrizionale one-shot"),
    ("USCITA", "2026-01-10", 65.0, "POS", "Attrezzatura", "Foam roller + lacrosse ball set"),
    ("USCITA", "2026-01-20", 180.0, "BONIFICO", "Formazione", "Workshop posturale Dott. Belli"),
    ("ENTRATA", "2026-02-01", 50.0, "CONTANTI", "Altro", "Vendita magliette palestra x2"),
    ("USCITA", "2026-02-15", 35.0, "POS", "Materiale", "Bande elastiche loop set"),
    ("USCITA", "2026-03-05", 120.0, "BONIFICO", "Formazione", "Corso fibromialgia e esercizio"),
    ("ENTRATA", "2026-03-10", 100.0, "BONIFICO", "Consulenza", "Piano alimentare personalizzato"),
]

for tipo, data, imp, met, cat, note in MANUAL_MOVS:
    conn.execute("""
        INSERT INTO movimenti_cassa (trainer_id, data_movimento, data_effettiva, tipo, categoria, importo, metodo, note, operatore)
        VALUES (1, ?, ?, ?, ?, ?, ?, ?, 'API')
    """, (data, data, tipo, cat, imp, met, note))

conn.commit()
print(f"  Movimenti manuali: {len(MANUAL_MOVS)}")


# ══════════════════════════════════════════════════════════════
# COMUNICAZIONI
# ══════════════════════════════════════════════════════════════

print("\n--- Comunicazioni ---")
COMMS = [
    # Benvenuto a tutti i clienti attivi (al momento dell'iscrizione)
    *[(i+1, "whatsapp", "welcome", f"Ciao {CLIENTI[i][0]}! Benvenuto/a nel mio studio. Ti aspetto per la prima sessione!",
       CLIENTI[i][7]) for i in range(len(CLIENTI)) if CLIENTI[i][6] == "Attivo" and i != 11],
    # Promemoria appuntamento
    (1, "whatsapp", "appointment_reminder", "Marco, ti ricordo la sessione di domani alle 10:00", "2026-03-20"),
    (2, "whatsapp", "appointment_reminder", "Giulia, domani alle 16:00 sessione glutei!", "2026-03-18"),
    (3, "whatsapp", "contract_confirm", "Roberto, contratto annuale rinnovato! Ci vediamo lunedi", "2025-09-25"),
    (5, "whatsapp", "appointment_reminder", "Elena, le ricordo la sessione di domani alle 10:00", "2026-03-22"),
    (5, "telefono", None, "Telefonata: spostamento appuntamento a giovedi", "2026-02-10"),
    (7, "whatsapp", "workout_share", "Sara, la nuova scheda e pronta! La trovi nell'app", "2026-03-01"),
    (7, "whatsapp", "checkin", "Sara, come va? Non ti vedo da qualche giorno, tutto ok?", "2026-02-15"),
    (8, "whatsapp", "nutrition_plan", "Sara, ecco il tuo piano alimentare aggiornato", "2026-01-20"),
    (11, "whatsapp", "appointment_reminder", "Giuseppe, le ricordo domani alle 14:00", "2026-03-25"),
    (1, "whatsapp", "workout_share", "Marco, nuova scheda Fase 2 caricata!", "2026-01-10"),
    (3, "whatsapp", "milestone", "Roberto, complimenti! 30 sessioni completate!", "2026-03-15"),
    (15, "whatsapp", "workout_share", "Davide, il mesociclo forza e pronto. Iniziamo lunedi!", "2025-12-01"),
    (17, "whatsapp", "appointment_reminder", "Paolo, domani alle 9:00 come sempre!", "2026-03-24"),
    (9, "whatsapp", "welcome", "Andrea! Iniziamo il percorso di recupero con calma e determinazione", "2025-12-15"),
    (4, "whatsapp", "contract_confirm", "Francesca, rinnovo attivato! Continuiamo il percorso", "2026-03-01"),
]

for cid, canale, tmpl, anteprima, created in COMMS:
    conn.execute("""
        INSERT INTO communication_log (trainer_id, id_cliente, canale, template_usato, anteprima, created_at)
        VALUES (1, ?, ?, ?, ?, ?)
    """, (cid, canale, tmpl, anteprima, created + "T10:00:00"))

conn.commit()
print(f"  Comunicazioni: {len(COMMS)}")


# ══════════════════════════════════════════════════════════════
# TODO / REMINDER
# ══════════════════════════════════════════════════════════════

print("\n--- Todo ---")
TODOS = [
    ("Preparare piano alimentare Sara Romano", "Ha chiesto piano specifico per ipotiroidismo Hashimoto", iso(TODAY + timedelta(days=2)), False),
    ("Chiamare medico Giuseppe De Luca", "Coordinamento piano esercizi con diabetologo. Tel: 051-4567890", iso(TODAY + timedelta(days=3)), False),
    ("Ordinare elastici resistenza pesanti", "Servono per programma Elena (prevenzione cadute) e Andrea (riab)", iso(TODAY + timedelta(days=5)), False),
    ("Aggiornare scheda Marco Rossi", "Progressione Fase 2: aumentare carico squat (+5kg) e panca (+2.5kg)", iso(TODAY + timedelta(days=1)), False),
    ("Contattare Valentina Greco per rinnovo", "Contratto scaduto da 3 mesi. Inviare proposta rinnovo WhatsApp", iso(TODAY + timedelta(days=1)), False),
    ("Prenotare workshop postura 12 aprile", "Workshop Dott. Belli su scoliosi e esercizio correttivo", iso(TODAY + timedelta(days=15)), False),
    ("Controllare scadenza assicurazione RC", "Rinnovo settembre 2026, verificare nuove condizioni", iso(TODAY + timedelta(days=30)), False),
    ("Preparare scheda Chiara Fontana", "Dopo colloquio di domani, preparare scheda starter", iso(TODAY + timedelta(days=2)), False),
    ("Inviare recap progressi a Roberto", "6 mesi di allenamento: preparare report con grafici misurazioni", iso(TODAY + timedelta(days=4)), False),
    ("Fattura trimestrale commercialista", "Emettere fattura Q1 2026 per Dott. Landi", iso(TODAY - timedelta(days=2)), True),
]

for titolo, desc, scadenza, completato in TODOS:
    conn.execute("""
        INSERT INTO todos (trainer_id, titolo, descrizione, data_scadenza, completato, created_at)
        VALUES (1, ?, ?, ?, ?, ?)
    """, (titolo, desc, scadenza, completato, NOW_ISO))

conn.commit()
print(f"  Todo: {len(TODOS)} ({sum(1 for t in TODOS if t[3])} completati)")


# ══════════════════════════════════════════════════════════════
# SCHEDE ALLENAMENTO (create via lista, non API)
# ══════════════════════════════════════════════════════════════

print("\n--- Schede allenamento ---")

# Esercizi reali dal catalogo:
# 1=Squat Bil, 4=Pressa, 5=Squat CL, 8=Affondi, 13=Ext Gambe
# 18=Stacco, 20=Rumeno, 21=Hip Thrust, 22=Ponte Glutei, 27=Curl Gambe, 31=Swing KB
# 34=Calf Raise, 38=Panca Piana, 39=Panca Man, 40=Inclinata, 43=Piegamenti
# 44=Croci Cavi, 48=Croci Man, 54=Spinta Alto, 55=Man Alto, 56=Arnold
# 58=Alzate Lat, 60=Alzate Post, 65=Dip, 71=Remata Bil, 72=Remata Man
# 78=Rematore Cavi, 83=Trazioni

PLANS = [
    # (client_id, nome, obiettivo, livello, sett, freq, note, sessioni)
    (1, "Full Body Dimagrimento - Fase 2", "dimagrimento", "intermedio", 6, 3,
     "Circuiti metabolici + forza. Attenzione caviglia dx.", [
        ("Upper Body + Core", "Petto, Dorso, Core", 60, [
            (38, 1, 4, "10-12", 60, None), (71, 2, 4, "10-12", 60, None),
            (54, 3, 3, "12-15", 45, None), (58, 4, 3, "15", 45, None)]),
        ("Lower Body + Cardio", "Quadricipiti, Glutei, Femorali", 60, [
            (1, 1, 4, "8-10", 90, None), (20, 2, 4, "10-12", 60, None),
            (21, 3, 3, "12-15", 60, None), (13, 4, 3, "15-20", 45, None)]),
        ("Circuito Metabolico", "Full Body", 45, [
            (31, 1, 3, "15", 30, None), (43, 2, 3, "12", 30, None), (5, 3, 3, "15", 30, None)]),
    ]),
    (2, "Glutei & Core - Tonificazione", "generale", "intermedio", 4, 3,
     "Focus glutei e core. Progressione carico settimanale.", [
        ("Glutei Focus", "Glutei, Femorali", 50, [
            (21, 1, 4, "10-12", 90, None), (1, 2, 3, "12", 60, None), (8, 3, 3, "10/lato", 60, None)]),
        ("Upper + Core", "Core, Spalle, Dorso", 50, [
            (38, 1, 3, "12", 60, None), (71, 2, 3, "12", 60, None), (54, 3, 3, "12", 45, None)]),
    ]),
    (3, "Ipertrofia Push/Pull/Legs", "ipertrofia", "avanzato", 8, 4,
     "Split PPL. Attenzione zona lombare (ernia operata). No stacco pesante.", [
        ("Push", "Petto, Deltoidi, Tricipiti", 70, [
            (38, 1, 4, "6-8", 120, None), (40, 2, 4, "8-10", 90, None),
            (55, 3, 3, "10-12", 60, None), (44, 4, 3, "12-15", 60, None)]),
        ("Pull", "Dorsali, Trapezio, Bicipiti", 70, [
            (83, 1, 4, "6-8", 120, None), (71, 2, 4, "8-10", 90, None),
            (72, 3, 3, "10-12", 60, None), (60, 4, 3, "15", 60, None)]),
        ("Legs", "Quadricipiti, Femorali, Glutei", 70, [
            (1, 1, 4, "8-10", 120, None), (4, 2, 4, "10-12", 90, None),
            (27, 3, 3, "12-15", 60, None), (34, 4, 3, "15-20", 60, None)]),
    ]),
    (5, "Prep Gara CrossFit - Mesociclo Forza", "forza", "avanzato", 4, 5,
     "Mesociclo forza pre-gara maggio. Attenzione spalla dx.", [
        ("Heavy Squat Day", "Quadricipiti, Glutei, Core", 75, [
            (1, 1, 5, "3-5", 180, 120.0), (4, 2, 4, "6-8", 120, 160.0)]),
        ("Upper Strength", "Petto, Dorso", 60, [
            (38, 1, 5, "3-5", 180, 100.0), (83, 2, 4, "5-7", 150, None)]),
    ]),
    (8, "Dimagrimento + Gestione Stress", "dimagrimento", "intermedio", 6, 2,
     "Sessioni per Sara. Ipotiroidismo: no sovrallenamento.", [
        ("Total Body A", "Full Body", 55, [
            (1, 1, 3, "10-12", 60, None), (38, 2, 3, "10-12", 60, None),
            (71, 3, 3, "12", 60, None), (21, 4, 3, "12-15", 45, None)]),
        ("Total Body B", "Full Body", 55, [
            (4, 1, 3, "12", 60, None), (39, 2, 3, "10-12", 60, None),
            (78, 3, 3, "12", 60, None), (22, 4, 3, "15", 45, None)]),
    ]),
    (6, "Silver Age - Prevenzione Cadute", "generale", "beginner", 8, 2,
     "Elena 57 anni. Osteoporosi + artrosi ginocchio sx. Esercizi a basso impatto.", [
        ("Forza Funzionale", "Gambe, Core", 45, [
            (5, 1, 3, "10", 60, None), (22, 2, 3, "12", 45, None), (9, 3, 3, "8/lato", 60, None)]),
        ("Equilibrio e Mobilita", "Full Body", 40, [
            (43, 1, 2, "8", 60, None), (78, 2, 3, "12", 45, None)]),
    ]),
    (15, "Contest Prep - Ipertrofia", "ipertrofia", "avanzato", 12, 5,
     "Davide: prep gara natural ottobre 2026. Periodizzazione volume.", [
        ("Petto + Tricipiti", "Petto, Tricipiti", 75, [
            (38, 1, 4, "6-8", 120, 90.0), (40, 2, 4, "8-10", 90, None),
            (48, 3, 3, "12-15", 60, None), (65, 4, 3, "10-12", 90, None)]),
        ("Dorso + Bicipiti", "Dorsali, Bicipiti", 75, [
            (83, 1, 4, "6-8", 120, None), (71, 2, 4, "8-10", 90, 80.0),
            (72, 3, 3, "10-12", 60, None)]),
        ("Gambe", "Quadricipiti, Femorali, Glutei", 80, [
            (1, 1, 4, "6-8", 150, 110.0), (4, 2, 4, "10-12", 90, None),
            (20, 3, 3, "10-12", 90, 70.0), (27, 4, 3, "12-15", 60, None)]),
        ("Spalle + Braccia", "Deltoidi, Bicipiti, Tricipiti", 60, [
            (54, 1, 4, "8-10", 90, None), (58, 2, 4, "12-15", 45, None),
            (56, 3, 3, "10-12", 60, None)]),
    ]),
    (9, "Riabilitazione Post-LCA Fase 2", "generale", "beginner", 8, 3,
     "Andrea: ricostruzione LCA dx set 2025. Fase 2: forza concentrica.", [
        ("Rinforzo Quadricipite", "Quadricipiti", 50, [
            (13, 1, 4, "12-15", 60, None), (4, 2, 3, "15", 90, None)]),
        ("Catena Posteriore", "Femorali, Glutei", 50, [
            (22, 1, 3, "15", 45, None), (27, 2, 3, "12", 60, None), (78, 3, 3, "12", 60, None)]),
    ]),
]

plan_count = 0
for cid, nome, obj, liv, sett, freq, note, sessioni in PLANS:
    conn.execute("""
        INSERT INTO schede_allenamento (trainer_id, id_cliente, nome, obiettivo, livello, durata_settimane, sessioni_per_settimana, note, created_at, updated_at)
        VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (cid, nome, obj, liv, sett, freq, note, NOW_ISO, NOW_ISO))
    plan_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    for s_idx, (s_nome, s_focus, s_dur, esercizi) in enumerate(sessioni):
        conn.execute("""
            INSERT INTO sessioni_scheda (id_scheda, numero_sessione, nome_sessione, focus_muscolare, durata_minuti)
            VALUES (?, ?, ?, ?, ?)
        """, (plan_id, s_idx + 1, s_nome, s_focus, s_dur))
        sess_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        for ex_id, ordine, serie, reps, riposo, carico in esercizi:
            conn.execute("""
                INSERT INTO esercizi_sessione (id_sessione, id_esercizio, ordine, serie, ripetizioni, tempo_riposo_sec, carico_kg)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (sess_id, ex_id, ordine, serie, reps, riposo, carico))

    plan_count += 1

conn.commit()
print(f"  Schede: {plan_count}")


# ══════════════════════════════════════════════════════════════
# AUDIT LOG (sintetico — un campione)
# ══════════════════════════════════════════════════════════════

print("\n--- Audit log ---")
audit_count = 0
for i in range(1, 31):
    created = CLIENTI[i-1][7] if i <= len(CLIENTI) else "2026-01-01"
    conn.execute("""
        INSERT INTO audit_log (entity_type, entity_id, action, changes, trainer_id, created_at)
        VALUES ('client', ?, 'CREATE', '{}', 1, ?)
    """, (i, created + "T10:00:00"))
    audit_count += 1

for idx in range(len(CONTRATTI)):
    conn.execute("""
        INSERT INTO audit_log (entity_type, entity_id, action, changes, trainer_id, created_at)
        VALUES ('contract', ?, 'CREATE', '{}', 1, ?)
    """, (idx + 1, CONTRATTI[idx][4] + "T10:00:00"))
    audit_count += 1

conn.commit()
print(f"  Audit entries: {audit_count}")


# ══════════════════════════════════════════════════════════════
# RIEPILOGO FINALE
# ══════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("  RIEPILOGO FINALE crm_dev.db")
print("=" * 60)

tables = [
    ("trainers", "Trainer"), ("clienti", "Clienti"), ("contratti", "Contratti"),
    ("rate_programmate", "Rate"), ("agenda", "Eventi agenda"), ("movimenti_cassa", "Movimenti cassa"),
    ("misurazioni_cliente", "Sessioni misurazione"), ("valori_misurazione", "Valori misurazione"),
    ("obiettivi_cliente", "Obiettivi"), ("spese_ricorrenti", "Spese ricorrenti"),
    ("communication_log", "Comunicazioni"), ("schede_allenamento", "Schede allenamento"),
    ("sessioni_scheda", "Sessioni scheda"), ("esercizi_sessione", "Esercizi sessione"),
    ("todos", "Todo/Reminder"), ("audit_log", "Audit trail"),
]
for t, label in tables:
    c = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {label:25s} {c:>5}")

print()
for label, query in [
    ("Rate SALDATE", "SELECT COUNT(*) FROM rate_programmate WHERE stato='SALDATA'"),
    ("Rate PENDENTI", "SELECT COUNT(*) FROM rate_programmate WHERE stato='PENDENTE'"),
    ("Eventi Completati", "SELECT COUNT(*) FROM agenda WHERE stato='Completato'"),
    ("Eventi Programmati", "SELECT COUNT(*) FROM agenda WHERE stato='Programmato'"),
    ("Clienti Attivi", "SELECT COUNT(*) FROM clienti WHERE stato='Attivo' AND deleted_at IS NULL"),
    ("Clienti Inattivi", "SELECT COUNT(*) FROM clienti WHERE stato='Inattivo' AND deleted_at IS NULL"),
]:
    c = conn.execute(query).fetchone()[0]
    print(f"  {label:25s} {c:>5}")

conn.close()

print("\n" + "=" * 60)
print("  DONE! Scenario demo realistico: 6 mesi di attivita")
print("  30 clienti, storico pagamenti, misurazioni mensili,")
print("  agenda distribuita, comunicazioni, 8 schede complete.")
print("=" * 60)
print(f"\n  Login: chiarabassani96@gmail.com / Fitness2026!")
print(f"  Frontend: http://localhost:3001")
print(f"  Backend:  http://localhost:8001/docs")

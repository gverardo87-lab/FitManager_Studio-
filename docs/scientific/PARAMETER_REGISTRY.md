# PARAMETER_REGISTRY.md — Registro Parametri Certificabili

> **Stato**: DRAFT | **Versione**: 1.0 | **Data**: 2026-04-19
> **Copertura**: ~850 parametri su 5 motori scientifici (~13,500 LOC)
> **Supersedes**: valori sparsi nel codice senza registro unificato

Ogni numero nel motore scientifico FitManager e' tracciabile a una fonte, un livello di confidenza e una riga di codice.

## Legenda Confidenza

| Livello | Significato | Esempio |
|---------|-------------|---------|
| **ALTA** | Fonte prescrive il valore, consenso in letteratura | EMG primari 1.0, push:pull 1.0, NSCA rep-max table |
| **MEDIA** | Fonte supporta il range, valore scelto per ragionamento | EMG 0.4, hypertrophy weights, age brackets |
| **BASSA** | Convenzione pratica, necessita validazione empirica | Score weights, deload factor, trend thresholds |

---

## A. Matrice EMG — Contributo Pattern-Muscolo

**Fonte codice**: `api/services/training_science/muscle_contribution.py` linee 37-133
**Scala**: 1.0 (motore primario, >70% MVC) | 0.7 (sinergista maggiore, 40-70%) | 0.4 (sinergista minore, 20-40%) | 0.2 (stabilizzatore, 10-20%)

### A.1 Upper Body

| Pattern | Muscolo | Contributo | Confidenza | Fonte | Riga |
|---------|---------|-----------|------------|-------|------|
| PUSH_H | PETTO | 1.0 | ALTA | Motore primario bench press (Schoenfeld 2010) | 40 |
| PUSH_H | DELT_ANT | 0.7 | ALTA | Sinergista maggiore (Trebs 2010) | 41 |
| PUSH_H | TRICIPITI | 0.7 | ALTA | Sinergista maggiore (NSCA 2016) | 42 |
| PUSH_H | CORE | 0.2 | MEDIA | Stabilizzatore, sotto soglia ipertrofica | 43 |
| PUSH_V | DELT_ANT | 1.0 | ALTA | Motore primario OHP (NSCA 2016) | 46 |
| PUSH_V | DELT_LAT | 0.7 | ALTA | Sinergista maggiore (Schoenfeld 2010) | 47 |
| PUSH_V | TRICIPITI | 0.7 | ALTA | Sinergista maggiore (NSCA 2016) | 48 |
| PUSH_V | TRAPEZIO | 0.4 | MEDIA | Sinergista minore, stabilizzazione scapolare | 49 |
| PUSH_V | PETTO | 0.2 | MEDIA | Clavicular head ~30% MVC (Trebs 2010) | 50 |
| PUSH_V | CORE | 0.2 | MEDIA | Stabilizzatore | 51 |
| PULL_H | DORSALI | 1.0 | ALTA | Motore primario row (Contreras 2010) | 55 |
| PULL_H | TRAPEZIO | 0.7 | ALTA | Sinergista maggiore (NSCA 2016) | 56 |
| PULL_H | DELT_POST | 0.7 | ALTA | Sinergista maggiore (Schoenfeld 2010) | 57 |
| PULL_H | BICIPITI | 0.7 | ALTA | Sinergista maggiore (NSCA 2016) | 58 |
| PULL_H | AVAMBRACCI | 0.7 | MEDIA | Grip essenziale 50-70% MVC (Contreras 2010) | 59 |
| PULL_V | DORSALI | 1.0 | ALTA | Motore primario lat pulldown (NSCA 2016) | 62 |
| PULL_V | BICIPITI | 0.7 | ALTA | Sinergista maggiore (NSCA 2016) | 63 |
| PULL_V | DELT_POST | 0.4 | MEDIA | Sinergista minore | 64 |
| PULL_V | TRAPEZIO | 0.4 | MEDIA | Sinergista minore | 65 |
| PULL_V | AVAMBRACCI | 0.4 | MEDIA | Sinergista minore | 66 |
| CURL | BICIPITI | 1.0 | ALTA | Motore primario isolamento | 119 |
| CURL | AVAMBRACCI | 0.4 | MEDIA | Sinergista minore | 120 |
| EXTENSION_TRI | TRICIPITI | 1.0 | ALTA | Motore primario isolamento | 123 |
| LATERAL_RAISE | DELT_LAT | 1.0 | ALTA | Motore primario isolamento | 126 |
| LATERAL_RAISE | TRAPEZIO | 0.2 | MEDIA | Stabilizzatore | 127 |
| FACE_PULL | DELT_POST | 1.0 | ALTA | Motore primario isolamento | 130 |
| FACE_PULL | TRAPEZIO | 0.4 | MEDIA | Sinergista minore | 131 |

### A.2 Lower Body

| Pattern | Muscolo | Contributo | Confidenza | Fonte | Riga |
|---------|---------|-----------|------------|-------|------|
| SQUAT | QUADRICIPITI | 1.0 | ALTA | Motore primario (NSCA 2016) | 70 |
| SQUAT | GLUTEI | 0.7 | ALTA | Sinergista maggiore (Contreras 2010) | 71 |
| SQUAT | FEMORALI | 0.4 | MEDIA | Sinergista minore | 72 |
| SQUAT | ADDUTTORI | 0.4 | MEDIA | Sinergista minore (Schoenfeld 2010) | 73 |
| SQUAT | CORE | 0.4 | MEDIA | Sinergista minore anti-flessione | 74 |
| SQUAT | POLPACCI | 0.4 | MEDIA | Soleus attivo stabilizzazione caviglia (Ebben 2009) | 75 |
| HINGE | FEMORALI | 1.0 | ALTA | Motore primario (NSCA 2016) | 78 |
| HINGE | GLUTEI | 1.0 | ALTA | Motore primario (Contreras 2010) | 79 |
| HINGE | DORSALI | 0.7 | ALTA | Erector spinae 70-80% MVC deadlift (NSCA 2016) | 80 |
| HINGE | TRAPEZIO | 0.4 | MEDIA | Sinergista minore | 81 |
| HINGE | CORE | 0.4 | MEDIA | Sinergista minore anti-flessione | 82 |
| HINGE | AVAMBRACCI | 0.4 | MEDIA | Grip necessario deadlift (Contreras 2010) | 83 |
| HIP_THRUST | GLUTEI | 1.0 | ALTA | Motore primario (Contreras 2010) | 101 |
| HIP_THRUST | FEMORALI | 0.4 | MEDIA | Sinergista minore | 102 |
| HIP_THRUST | CORE | 0.2 | MEDIA | Stabilizzatore | 103 |
| LEG_EXTENSION | QUADRICIPITI | 1.0 | ALTA | Motore primario isolamento | 106 |
| LEG_CURL | FEMORALI | 1.0 | ALTA | Motore primario isolamento | 109 |
| CALF_RAISE | POLPACCI | 1.0 | ALTA | Motore primario isolamento | 112 |
| ADDUCTOR | ADDUTTORI | 1.0 | ALTA | Motore primario isolamento | 115 |

### A.3 Functional

| Pattern | Muscolo | Contributo | Confidenza | Fonte | Riga |
|---------|---------|-----------|------------|-------|------|
| CORE | CORE | 1.0 | ALTA | Motore primario | 87 |
| ROTATION | CORE | 0.7 | ALTA | Sinergista maggiore (obliqui) | 90 |
| ROTATION | DELT_POST | 0.4 | MEDIA | Sinergista minore extra-rotazione | 91 |
| CARRY | AVAMBRACCI | 1.0 | ALTA | Motore primario grip | 94 |
| CARRY | CORE | 0.7 | ALTA | Sinergista maggiore anti-flessione laterale | 95 |
| CARRY | TRAPEZIO | 0.7 | ALTA | Sinergista maggiore (NSCA 2016) | 96 |
| CARRY | GLUTEI | 0.2 | MEDIA | Stabilizzatore deambulazione | 97 |

**Totale celle non-zero**: 53 su 270 possibili (18 pattern x 15 muscoli)

---

## B. Hypertrophy Weights — Peso Ipertrofico per Livello Contributo

**Fonte codice**: `api/services/training_science/muscle_contribution.py` linee 299-304
**Principio**: Israetel RP 2020 — "count indirect volume as roughly half a set"

| Contributo EMG | Peso Ipertrofico | Significato | Confidenza | Fonte |
|----------------|-----------------|-------------|------------|-------|
| 1.0 (primario) | 1.0 | Stimolo pieno — EMG > 70% MVC | ALTA | Consenso letteratura |
| 0.7 (sinergista maggiore) | 0.5 | Mezzo set — "half a set" rule | MEDIA | Israetel RP 2020 |
| 0.4 (sinergista minore) | 0.25 | Quarto di set — EMG 20-40% | MEDIA | Derivazione da Israetel |
| 0.2 (stabilizzatore) | 0.0 | Sotto soglia ipertrofica — EMG 10-20% | ALTA | Consenso: stabilizzatori non ipertrofizzano |

**Computazione duale**: ogni esercizio produce (1) volume meccanico = serie totali, (2) volume ipertrofico = serie x peso ipertrofico. Il rapporto tra i due indica l'efficienza dello stimolo.

---

## C. Volume Targets — MEV/MAV/MRV per Muscolo x Livello

**Fonte codice**: `api/services/training_science/volume_model.py` linee 120-226
**Formato**: (MEV, MAV_min, MAV_max, MRV, note)
**Unita**: serie ipertrofiche settimanali

### C.1 Tabella completa

| Muscolo | Livello | MEV | MAV_min | MAV_max | MRV | Confidenza | Note |
|---------|---------|-----|---------|---------|-----|------------|------|
| PETTO | Princ. | 4 | 6 | 8 | 12 | ALTA | Solo push_h (1.0) |
| PETTO | Inter. | 4 | 8 | 12 | 16 | ALTA | Schoenfeld 2017 |
| PETTO | Avanz. | 6 | 12 | 16 | 20 | ALTA | Israetel RP 2020 |
| DORSALI | Princ. | 4 | 8 | 12 | 18 | ALTA | pull_h(1.0) + pull_v(1.0) + hinge(0.5) |
| DORSALI | Inter. | 4 | 12 | 18 | 25 | ALTA | Hub muscle: triplo contributo |
| DORSALI | Avanz. | 6 | 16 | 22 | 28 | MEDIA | Range alto, necessita conferma |
| DELT_ANT | Princ. | 0 | 0 | 4 | 8 | ALTA | Volume indiretto da push sufficiente |
| DELT_ANT | Inter. | 0 | 0 | 8 | 14 | ALTA | push_v(1.0) + push_h(0.5) |
| DELT_ANT | Avanz. | 0 | 0 | 10 | 16 | MEDIA | |
| DELT_LAT | Princ. | 4 | 6 | 8 | 12 | ALTA | lateral_raise(1.0) + push_v(0.5) |
| DELT_LAT | Inter. | 4 | 8 | 12 | 16 | ALTA | Richiede isolamento diretto |
| DELT_LAT | Avanz. | 6 | 10 | 16 | 20 | ALTA | |
| DELT_POST | Princ. | 0 | 4 | 6 | 10 | ALTA | Volume indiretto da pull |
| DELT_POST | Inter. | 0 | 6 | 10 | 14 | ALTA | face_pull(1.0) + pull_h(0.5) + pull_v(0.25) |
| DELT_POST | Avanz. | 0 | 8 | 14 | 18 | MEDIA | |
| BICIPITI | Princ. | 4 | 6 | 10 | 14 | ALTA | curl(1.0) + pull_h(0.5) + pull_v(0.5) |
| BICIPITI | Inter. | 4 | 10 | 14 | 18 | ALTA | Hub muscle: doppio contributo indiretto |
| BICIPITI | Avanz. | 4 | 12 | 18 | 22 | ALTA | |
| TRICIPITI | Princ. | 2 | 6 | 8 | 12 | ALTA | extension(1.0) + push_h(0.5) + push_v(0.5) |
| TRICIPITI | Inter. | 2 | 8 | 12 | 16 | ALTA | Hub muscle: doppio contributo indiretto |
| TRICIPITI | Avanz. | 4 | 10 | 16 | 20 | ALTA | |
| QUADRICIPITI | Princ. | 4 | 6 | 10 | 14 | ALTA | squat(1.0) + leg_extension(1.0) |
| QUADRICIPITI | Inter. | 4 | 10 | 16 | 20 | ALTA | Hub muscle: 2-3 esercizi diretti |
| QUADRICIPITI | Avanz. | 6 | 14 | 20 | 24 | ALTA | |
| FEMORALI | Princ. | 4 | 6 | 8 | 12 | ALTA | hinge(1.0) + leg_curl(1.0) + squat(0.25) |
| FEMORALI | Inter. | 4 | 8 | 12 | 16 | ALTA | |
| FEMORALI | Avanz. | 4 | 10 | 16 | 20 | ALTA | |
| GLUTEI | Princ. | 2 | 4 | 6 | 10 | ALTA | hinge(1.0) + squat(0.5) + hip_thrust(1.0) |
| GLUTEI | Inter. | 2 | 6 | 10 | 14 | ALTA | MEV 0→2 (fix H2: pattern primari) |
| GLUTEI | Avanz. | 0 | 8 | 14 | 18 | MEDIA | Volume indiretto da squat/hinge |
| POLPACCI | Princ. | 4 | 6 | 8 | 12 | ALTA | calf_raise(1.0) + squat(0.25) |
| POLPACCI | Inter. | 4 | 8 | 12 | 16 | ALTA | Richiedono alta frequenza e rep |
| POLPACCI | Avanz. | 6 | 10 | 14 | 18 | ALTA | |
| TRAPEZIO | Princ. | 0 | 4 | 6 | 10 | ALTA | pull_h(0.5) + carry(0.5) + compound(0.25) |
| TRAPEZIO | Inter. | 0 | 6 | 10 | 16 | ALTA | Hub muscle: volume indiretto da pull/hinge |
| TRAPEZIO | Avanz. | 0 | 8 | 14 | 20 | MEDIA | |
| CORE | Princ. | 0 | 4 | 6 | 10 | ALTA | rotation(0.5) + carry(0.5) + compound(0.25) |
| CORE | Inter. | 0 | 6 | 10 | 14 | ALTA | Hub muscle: volume indiretto |
| CORE | Avanz. | 0 | 8 | 14 | 18 | MEDIA | |
| AVAMBRACCI | Princ. | 2 | 2 | 4 | 10 | ALTA | carry(1.0) + pull_h(0.5) + pull_v/curl/hinge(0.25) |
| AVAMBRACCI | Inter. | 2 | 4 | 8 | 12 | ALTA | MEV 0→2 (fix H1: pattern primario carry) |
| AVAMBRACCI | Avanz. | 2 | 6 | 10 | 14 | MEDIA | |
| ADDUTTORI | Princ. | 0 | 2 | 4 | 8 | MEDIA | adductor(1.0) + squat(0.25) |
| ADDUTTORI | Inter. | 0 | 4 | 8 | 10 | MEDIA | Volume indiretto minimo |
| ADDUTTORI | Avanz. | 0 | 6 | 10 | 12 | MEDIA | |

**Totale**: 45 combinazioni (15 muscoli x 3 livelli) = 180 valori (MEV + MAV_min + MAV_max + MRV)

### C.2 Invarianti del modello

1. MEV = 0 per muscoli con volume indiretto sufficiente (delt_ant, delt_post, trapezio, core, adduttori)
2. MEV > 0 per muscoli che necessitano stimolo diretto esplicito
3. MAV_min < MAV_max < MRV (sempre)
4. Scaling demografico: MAV_min, MAV_max, MRV scalano per demo_factor. MEV scala solo per fattore_volume dell'obiettivo

---

## D. Parametri di Carico — 5 Obiettivi x 10 Parametri

**Fonte codice**: `api/services/training_science/principles.py` linee 25-101

| Parametro | FORZA | IPERTROFIA | RESISTENZA | DIMAGRIMENTO | TONIFICAZIONE | Confidenza |
|-----------|-------|-----------|-----------|-------------|--------------|------------|
| Intensita min (%1RM) | 0.85 | 0.65 | 0.50 | 0.65 | 0.60 | ALTA |
| Intensita max (%1RM) | 1.00 | 0.85 | 0.65 | 0.80 | 0.75 | ALTA |
| Rep min | 1 | 6 | 15 | 8 | 10 | ALTA |
| Rep max | 5 | 12 | 25 | 15 | 15 | ALTA |
| Serie compound (sec, prim) | (3, 5) | (3, 4) | (2, 3) | (3, 4) | (2, 3) | ALTA |
| Serie isolation (sec, prim) | (2, 3) | (3, 4) | (2, 3) | (2, 3) | (2, 3) | MEDIA |
| Riposo compound (sec) | (180, 300) | (90, 120) | (30, 60) | (45, 90) | (60, 90) | ALTA |
| Riposo isolation (sec) | (120, 180) | (60, 90) | (30, 45) | (30, 60) | (45, 60) | ALTA |
| % compound | 0.80 | 0.60 | 0.50 | 0.70 | 0.60 | MEDIA |
| Freq per muscolo (/sett) | (2, 3) | (2, 2) | (2, 3) | (2, 3) | (2, 2) | ALTA |
| Fattore volume | 0.70 | 1.00 | 0.60 | 0.80 | 0.70 | MEDIA |
| Fonte | NSCA 2016, Ralston 2017 | Schoenfeld 2010/2017, Krieger 2010 | ACSM 2009, NSCA 2016 | NSCA 2016, Schoenfeld 2021 | ACSM 2009 | — |

**Totale**: 50 parametri (5 obiettivi x 10 parametri)

---

## E. Rapporti Biomeccanici — Balance Ratios

**Fonte codice**: `api/services/training_science/balance_ratios.py` linee 28-131

| Rapporto | Target | Tolleranza | Range OK | Numeratore | Denominatore | Confidenza | Fonte |
|----------|--------|-----------|----------|------------|-------------|------------|-------|
| Push : Pull | 1.0 | ±0.15 | [0.85, 1.15] | push_h, push_v | pull_h, pull_v | ALTA | NSCA 2016 cap.21, Sahrmann 2002, Janda 1983 |
| Push H : Push V | 1.5 | ±1.0 | [0.5, 2.5] | push_h | push_v | MEDIA | Sahrmann 2002, Boettcher 2008, Schoenfeld 2010 |
| Pull H : Pull V | 1.2 | ±0.80 | [0.4, 2.0] | pull_h | pull_v | MEDIA | Sahrmann 2002, NSCA 2016 |
| Quad : Ham | 0.80 | ±0.30 | [0.50, 1.10] | QUADRICIPITI | FEMORALI | MEDIA | NSCA 2016 cap.21, Alentorn-Geli 2009 (ACL risk H:Q<0.6), Israetel RP 2020 |
| Ant : Post | 0.65 | ±0.25 | [0.40, 0.90] | PETTO+DELT_ANT+QUAD | DORSALI+DELT_POST+FEM+GLUTEI | MEDIA | Sahrmann 2002 (upper/lower crossed syndrome), Janda 1983 |

**Derivazione Quad:Ham target 0.80**: dato squat:hinge ratio, n/(0.25n+n) = 0.80

**Totale**: 15 valori (5 rapporti x target + tolleranza + range)

---

## F. Scaling Demografico

**Fonte codice**: `api/services/training_science/volume_model.py` linee 55-66

### F.1 Fattore Sesso

| Sesso | Fattore | Confidenza | Fonte |
|-------|---------|------------|-------|
| M | 1.0 | ALTA | Baseline (riferimento letteratura NSCA/Schoenfeld) |
| F | 0.85 | MEDIA | Schoenfeld 2017, Vingren 2010 (testosterone ~15x inferiore) |

### F.2 Fattore Eta

| Range Eta | Fattore | Confidenza | Fonte |
|-----------|---------|------------|-------|
| 0-29 | 1.0 | ALTA | Piena capacita' di recupero |
| 30-44 | 0.95 | MEDIA | Hakkinen 2001 (-5%) |
| 45-59 | 0.85 | MEDIA | Peterson 2011 (-15%) |
| 60+ | 0.75 | MEDIA | Recupero rallentato, sarcopenia |

**Totale**: 6 parametri

---

## G. Score Composition — Formula Composita 4D

**Fonte codice**: `api/services/training_science/plan_analyzer.py` linee 760-837

### G.1 Pesi Componenti Score

| Componente | Peso (punti) | Confidenza | Razionale |
|------------|-------------|------------|-----------|
| Volume coverage | 40 | BASSA | Il piu' predittivo per ipertrofia (design choice) |
| Balance | 25 | BASSA | Importanza clinica e prestativa |
| Frequency | 20 | BASSA | Letteratura freq >= 2x/muscolo |
| Recovery | 15 | BASSA | Peso basso perche' preventivo, non predittivo |

### G.2 Muscle Importance Tiers

| Tier | Muscoli | Peso | Confidenza | Riga |
|------|---------|------|------------|------|
| 1 | PETTO, DORSALI, QUADRICIPITI, FEMORALI | 1.0 | MEDIA | 789-791 |
| 2 | DELT_ANT/LAT/POST, GLUTEI, BICIPITI, TRICIPITI | 0.7 | MEDIA | 790 |
| 3 | TRAPEZIO, CORE, POLPACCI, AVAMBRACCI, ADDUTTORI | 0.4 | BASSA | 792 |

### G.3 Coverage Weights

| Zona Volume | Peso | Confidenza | Riga |
|-------------|------|------------|------|
| Ottimale (in MAV) | 1.0 | MEDIA | 810 |
| Sopra MAV < MRV | 0.8 | BASSA | 811 |
| MEV < vol < MAV | 0.5 | BASSA | 812 |
| Sotto MEV | 0.0 | ALTA | 813 |
| Sopra MRV | 0.0 | ALTA | 814 |

**Totale**: 7 parametri strutturali + 15 pesi muscolo + 5 pesi coverage = 27

---

## H. Costanti Algoritmiche

**Fonte codice**: vari file in `api/services/training_science/`

### H.1 Recovery

| Parametro | Valore | Unita | Confidenza | Fonte | Modulo | Riga |
|-----------|--------|-------|------------|-------|--------|------|
| Recovery min per session | 2.0 | serie | MEDIA | Design choice (soglia rilevanza) | plan_analyzer.py | 62 |
| Recovery cumulative threshold | 5.0 | serie | MEDIA | NSCA 2016 (48-72h recupero) | plan_analyzer.py | 63 |

### H.2 Limiti Sessione e Volume

| Parametro | Princ. | Inter. | Avanz. | Confidenza | Fonte | Modulo | Riga |
|-----------|--------|--------|--------|------------|-------|--------|------|
| Max slot per sessione | 6 | 8 | 10 | ALTA | NSCA 2016 | plan_builder.py | 139-142 |
| Max isolation per sessione | 2 | 3 | 4 | MEDIA | Design choice | plan_builder.py | 145-148 |
| Max serie per slot | 6 | 6 | 6 | ALTA | NSCA 2016: qualita' degrada >5-6 | plan_builder.py | 157 |
| Max compound boost/session | 2 | 2 | 2 | BASSA | Design choice aggressivita' | plan_builder.py | 160 |
| Max serie settimanali | 35 | 55 | 75 | MEDIA | Israetel RP 2020 | plan_builder.py | 165-168 |

### H.3 Soglie e Costanti

| Parametro | Valore | Confidenza | Fonte | Modulo | Riga |
|-----------|--------|------------|-------|--------|------|
| Frequency stimulus threshold | 2.0 serie | ALTA | Schoenfeld 2016 (freq >= 2x) | plan_builder.py | 177 |
| Max feedback iterations | 1 | BASSA | Design choice | plan_builder.py | 759 |
| Frequency penalty per warning | -4 pt | BASSA | Design choice | plan_analyzer.py | 827 |
| Recovery penalty per warning | -5 pt | BASSA | Design choice | plan_analyzer.py | 832 |

### H.4 Load Model

**Fonte codice**: `api/services/training_science/load_model.py`

| Parametro | Valore | Confidenza | Fonte | Riga |
|-----------|--------|------------|-------|------|
| PCT decrement per RIR | 0.025 (-2.5%) | ALTA | Zourdos 2016 | 83 |

### H.5 NSCA Rep-Max Table

**Fonte codice**: `api/services/training_science/load_model.py` linee 49-65

| Reps | %1RM | Confidenza | Fonte |
|------|------|------------|-------|
| 1 | 1.00 | ALTA | NSCA 2016 Table 15.1 |
| 2 | 0.95 | ALTA | " |
| 3 | 0.93 | ALTA | " |
| 4 | 0.90 | ALTA | " |
| 5 | 0.87 | ALTA | " |
| 6 | 0.85 | ALTA | " |
| 7 | 0.83 | ALTA | " |
| 8 | 0.80 | ALTA | " |
| 9 | 0.77 | ALTA | " |
| 10 | 0.75 | ALTA | " |
| 11 | 0.72 | ALTA | " |
| 12 | 0.70 | ALTA | " |
| 15 | 0.65 | ALTA | " |
| 20 | 0.60 | ALTA | " |
| 25 | 0.55 | ALTA | " |

### H.6 Intensity Zones

**Fonte codice**: `api/services/training_science/load_model.py` linee 100-107

| Min % | Max % | Zona | Effetto | Confidenza |
|-------|-------|------|---------|------------|
| 0.90 | 1.00 | Massimale | Forza massimale, reclutamento neurale completo | ALTA |
| 0.80 | 0.90 | Sub-massimale | Forza-ipertrofia, alto stress meccanico | ALTA |
| 0.67 | 0.80 | Ipertrofia | Volume ottimale, tensione meccanica | ALTA |
| 0.50 | 0.67 | Resistenza | Resistenza muscolare, adattamento metabolico | ALTA |
| 0.00 | 0.50 | Attivazione | Riscaldamento, apprendimento motorio | ALTA |

### H.7 Fasi Mesociclo — RPE e %1RM

**Fonte codice**: `api/services/training_science/load_model.py` linee 127-167

| Fase | RPE min | RPE max | %1RM min | %1RM max | Confidenza |
|------|---------|---------|----------|----------|------------|
| Accumulazione | 6.0 | 7.5 | 0.60 | 0.72 | ALTA |
| Intensificazione | 7.0 | 8.5 | 0.70 | 0.80 | ALTA |
| Overreaching | 8.0 | 9.5 | 0.75 | 0.85 | ALTA |
| Deload | 5.0 | 6.5 | 0.55 | 0.65 | ALTA |

### H.8 Periodizzazione

**Fonte codice**: `api/services/training_science/periodization.py` linee 72-123

| Parametro | Princ. | Inter. | Avanz. | Confidenza | Fonte |
|-----------|--------|--------|--------|------------|-------|
| Durata mesociclo (sett) | 4 | 5 | 6 | ALTA | NSCA 2016 |
| Volume base (fattore) | 0.85 | 0.90 | 0.90 | MEDIA | Helms 2019 |
| Volume picco (fattore) | 1.10 | 1.20 | 1.30 | MEDIA | Israetel RP 2020 |
| Volume deload (fattore) | 0.50 | 0.50 | 0.50 | ALTA | Helms 2019 (40-60% range, scelta 50%) |

**Interpolazione lineare**: fattore = base + t × (picco - base), t in [0, 1] per settimane di carico

### H.9 Split Logic

**Fonte codice**: `api/services/training_science/split_logic.py`

| Frequenza | Split | Confidenza | Fonte |
|-----------|-------|------------|-------|
| 2-3x | FULL_BODY | ALTA | Schoenfeld 2016 |
| 4-5x | UPPER_LOWER | ALTA | NSCA 2016 |
| 6x | PUSH_PULL_LEGS | ALTA | Helms 2019 |

| Livello | Max Frequenza | Confidenza |
|---------|---------------|------------|
| Princ. | 3 | ALTA |
| Inter. | 5 | ALTA |
| Avanz. | 6 | ALTA |

### H.10 Session Order — Priorita Esecuzione

**Fonte codice**: `api/services/training_science/session_order.py` linee 48-73
**Principio**: NSCA "Large to Small" + prioritizzazione risorse SNC

| Livello Priorita | Pattern | Ordine |
|-------------------|---------|--------|
| 1 (Compound Heavy) | SQUAT, HINGE, PULL_H, PULL_V, PUSH_H, PUSH_V | 1-6 |
| 2 (Compound Light) | CARRY, ROTATION | 10-11 |
| 3 (Core Stability) | CORE | 30 |
| 4 (Isolation) | HIP_THRUST, LEG_EXT, LEG_CURL, ADDUCTOR, LAT_RAISE, FACE_PULL, CURL, EXT_TRI, CALF_RAISE | 20-28 |

### H.11 Training Intelligence

**Fonte codice**: `api/routers/training_intelligence.py`

| Parametro | Valore | Confidenza | Scopo |
|-----------|--------|------------|-------|
| Finestra analisi default | 3 mesi | BASSA | Periodo osservazione |
| Soglia contributo EMG | 0.4 (40%) | MEDIA | Minimo per stimolazione muscolo |
| Soglia trend volume | ±1.5 serie | BASSA | Crescente/calante/stabile |
| Gap recupero tollerato | ≤ 1 giorno | MEDIA | Sessioni adiacenti |
| Overlap recupero cumulativo | 5 serie totali | MEDIA | Carico concorrente significativo |

### H.12 Workout Diff — Compliance

**Fonte codice**: `api/routers/workout_diff.py` linee 127-164

| Parametro | Valore | Confidenza | Scopo |
|-----------|--------|------------|-------|
| Peso serie | 40% | BASSA | Importanza carico lavoro |
| Peso reps | 35% | BASSA | Importanza zona esecuzione |
| Peso carico (kg) | 25% | BASSA | Importanza progressione peso |
| Peso serie (no-kg) | 55% | BASSA | Redistribuzione senza carico |
| Peso reps (no-kg) | 45% | BASSA | Redistribuzione senza carico |
| Bonus cap | 120% | BASSA | Max compliance per esercizio |
| Ratio cap | 1.2 | BASSA | Max bonus singola componente |
| Sopra piano | >= 105% | BASSA | Soglia classificazione |
| In linea | 90-105% | BASSA | Soglia classificazione |
| Sotto piano | < 90% | BASSA | Soglia classificazione |

### H.13 Feasibility Engine

**Fonte codice**: `api/services/training_science/runtime/feasibility_engine.py`

| Safety Severity | Verdetto | Penalty Score | Confidenza |
|----------------|----------|---------------|------------|
| None | feasible | 0 | ALTA |
| Caution | feasible | -20 | MEDIA |
| Modify | discouraged | -40 | MEDIA |
| Avoid | infeasible | -80 | ALTA |

### H.14 Exercise Ranker — Scoring Components

**Fonte codice**: `api/services/training_science/runtime/exercise_ranker.py`

| Componente | Max Punti | Confidenza |
|------------|----------|------------|
| Pattern match (esatto) | 50 | BASSA |
| Muscle target (primario) | 25 | BASSA |
| Muscle target (secondario) | 12 | BASSA |
| Difficulty alignment | ±12 | BASSA |
| Objective alignment | +8 / -12 a -30 | BASSA |
| Safety penalty | -80 max | MEDIA |
| Pattern balance | ±8 | BASSA |
| Frequency bonus/penalty | ±12 cap | BASSA |

---

## I. Tabelle LARN — Riferimenti Nutrizionali

**Fonte codice**: `api/services/nutrition_science/larn_tables.py` linee 34-283

### I.1 Proteine (g/kg/giorno)

| Eta | Sesso | AR | PRI | Confidenza | Riga |
|-----|-------|----|----|------------|------|
| 18-29 | M/F | 0.71 | 0.90 | ALTA | 37-38 |
| 30-59 | M/F | 0.71 | 0.90 | ALTA | 39-40 |
| 60-74 | M/F | 0.71 | 1.10 | ALTA | 41-42 |
| 75+ | M/F | 0.71 | 1.10 | ALTA | 43-44 |

### I.2 Vitamina A (ug RE/giorno)

| Eta | Sesso | AR | PRI | UL | Confidenza | Riga |
|-----|-------|----|----|----|-----------|----|
| 18-29 | M | 500 | 700 | 3000 | ALTA | 56 |
| 18-29 | F | 400 | 600 | 3000 | ALTA | 57 |
| 30-59 | M | 500 | 700 | 3000 | ALTA | 58 |
| 30-59 | F | 400 | 600 | 3000 | ALTA | 59 |
| 60+ | M/F | 500/400 | 700/600 | 3000 | ALTA | 60-63 |

### I.3 Vitamina D (ug/giorno)

| Eta | AI | UL | Confidenza | Riga |
|-----|----|----|------------|------|
| 18-59 | 15 | 100 | ALTA | 68-69 |
| 60-74 | 15 | 100 | ALTA | 70-71 |
| 75+ | 20 | 100 | ALTA | 72-73 |

### I.4 Vitamina E (mg/giorno, alfa-tocoferolo)

| Sesso | AI | UL | Riga |
|-------|----|----|------|
| M | 13 | 300 | 78 |
| F | 12 | 300 | 79 |

### I.5 Vitamina C (mg/giorno)

| Sesso | AR | PRI | Riga |
|-------|----|----|------|
| M | 75 | 105 | 84-91 |
| F | 60 | 85 | 84-91 |

### I.6 Vitamine B (valori adulti)

| Vitamina | Sesso | AR | PRI | UL | Riga |
|----------|-------|----|----|----|----|
| B1 Tiamina (mg) | M | 1.0 | 1.2 | — | 94-99 |
| B1 Tiamina (mg) | F | 0.9 | 1.1 | — | 94-99 |
| B2 Riboflavina (mg) | M | 1.1 | 1.6 | — | 102-107 |
| B2 Riboflavina (mg) | F | 1.0 | 1.3 | — | 102-107 |
| B3 Niacina (mg NE) | M | 14 | 18 | 900 | 110-115 |
| B3 Niacina (mg NE) | F | 11 | 14 | 900 | 110-115 |
| B6 Piridossina (mg) | 18-59 | 1.1 | 1.3 | 25 | 118-123 |
| B6 Piridossina (mg) | 60+ | 1.4 | 1.7 | 25 | 118-123 |
| B9 Folato (ug DFE) | M/F | 320 | 400 | 1000 | 126-129 |
| B12 Cobalamina (ug) | M/F | 2.0 | 2.4 | — | 132-135 |

### I.7 Minerali

| Minerale | Eta/Sesso | AR | PRI/AI | UL | Riga |
|----------|-----------|----|----|----|----|
| Calcio (mg) | 18-59 | 800 | 1000 | 2500 | 142-151 |
| Calcio (mg) | 60+ F | 1000 | 1200 | 2500 | 148-149 |
| Ferro (mg) | M | 7 | 10 | — | 154-163 |
| Ferro (mg) | F 18-59 | 10 | 18 | — | 157-158 |
| Zinco (mg) | M | 10 | 12 | 25 | 166-169 |
| Zinco (mg) | F | 8 | 9 | 25 | 166-169 |
| Magnesio (mg) | M/F | — | AI 240 | — | 172-175 |
| Fosforo (mg) | M/F | 580 | 700 | — | 178-181 |
| Potassio (mg) | M/F | — | AI 3900 | — | 184-187 |
| Selenio (ug) | M/F | 45 | 55 | 300 | 190-193 |
| Sodio (mg) | M/F | — | AI 1500 | SDT <2000 (OMS) | 196-199 |
| Fibra (g) | M/F | — | AI 25 | — | 203-206 |

### I.8 Gravidanza/Allattamento (Addizioni)

| Nutriente | Gravidanza | Allattamento | Riga |
|-----------|-----------|-------------|------|
| Proteine (g) | +1/+8/+26 (per trimestre) | +21 (primi 6 mesi) | 213-243 |
| Vitamina A PRI | +100 | +350 | 213-243 |
| Vitamina C PRI | +10 | +30 | 213-243 |
| B9 PRI (ug) | +200 (→ 600) | +100 (→ 500) | 213-243 |
| B12 (ug) | +0.2 (→ 2.6) | +0.4 (→ 2.8) | 213-243 |
| Ferro PRI | +9 (→ 27) | -7 (→ 11, amenorrea) | 213-243 |
| Zinco PRI | +2 | +3 | 213-243 |
| Selenio PRI | +5 (→ 60) | +10 (→ 65) | 213-243 |

**Confidenza**: ALTA (tutti i valori LARN 2014)
**Totale sezione I**: ~200 parametri

---

## J. Frequenze CREA — Porzioni Settimanali

**Fonte codice**: `api/services/nutrition_science/larn_portions.py` linee 183-258

### J.1 Frequenze Settimanali Gruppi Alimentari

| Sottogruppo | Min/sett | Max/sett | Confidenza | Fonte |
|-------------|----------|----------|------------|-------|
| primo_piatto | 5 | 7 | ALTA | CREA-Dir 2018 (pranzo giornaliero) |
| secondo_piatto | 10 | 14 | ALTA | CREA-Dir 2018 (pranzo + cena) |
| pane | 5 | 14 | MEDIA | Adattamento (cena + colazione) |
| cereali_colazione | 5 | 7 | MEDIA | Colazione giornaliera |
| frutta_fresca | 14 | 21 | ALTA | CREA-Dir 2018 (2-3 porzioni/giorno) |
| verdura_altra | 10 | 21 | ALTA | CREA-Dir 2018 (contorni) |
| yogurt | 7 | 14 | MEDIA | 1-2/giorno (colazione + spuntino) |
| olio | 3 | 14 | MEDIA | Condimento extra verdure (ridotto) |
| frutta_secca | 5 | 7 | ALTA | CREA-Dir 2018 (quasi giornaliera) |

### J.2 Sub-frequenze Proteiche

| Sottocategoria | Min/sett | Max/sett | Confidenza | Fonte |
|---------------|----------|----------|------------|-------|
| Pesce | 2 | 4 | ALTA | CREA-Dir 2018 Dir.9 |
| Carne bianca | 1 | 4 | ALTA | CREA-Dir 2018 |
| Carne rossa | 0 | 2 | ALTA | WCRF 2018 (limitare) |
| Uova | 2 | 4 | ALTA | CREA-Dir 2018 |
| Legumi | 2 | 5 | ALTA | CREA-Dir 2018 (fonte vegetale) |
| Affettati | 0 | 1 | ALTA | CREA-Dir 2018 (limitare insaccati) |

**Totale sezione J**: ~15 parametri

---

## K. Safety Rules — Regole Keyword Anamnesi

**Fonte codice**: `api/services/condition_rules.py` linee 27-222

### K.1 Condizioni Specifiche (ID 1-30)

| ID | Condizione | Keywords principali | Categoria | Confidenza |
|----|-----------|-------------------|-----------|------------|
| 1 | Ernia/Lombare | ernia, lombare | Schiena | ALTA |
| 2 | Ernia cervicale | ernia cervicale, cervicobrachialgia | Cervicale | ALTA |
| 3 | Scoliosi | scoliosi | Schiena | ALTA |
| 4 | Stenosi spinale | stenosi spinale | Schiena | ALTA |
| 5 | Spondilolistesi | spondilolistesi | Schiena | ALTA |
| 6 | Impingement spalla | subacromiale, impingement spalla | Spalla | ALTA |
| 7 | Cuffia rotatori | cuffia dei rotatori | Spalla | ALTA |
| 8 | Instabilita scapolare | instabilita scapolare, instabilita gleno | Spalla | ALTA |
| 9 | Spalla congelata | spalla congelata, capsulite | Spalla | ALTA |
| 10 | Lesione LCA | crociato, lca | Ginocchio | ALTA |
| 11 | Lesione menisco | menisco | Ginocchio | ALTA |
| 12 | Sindrome femoro-rotulea | femoro-rotulea, rotula | Ginocchio | ALTA |
| 13 | Artrosi ginocchio | artrosi ginocchio, gonartrosi | Ginocchio | ALTA |
| 14 | Artrosi anca | artrosi anca, coxartrosi | Anca | ALTA |
| 15 | Conflitto FAA | conflitto femoro-acetabolare, impingement anca | Anca | ALTA |
| 16 | Epicondilite | epicondilite, gomito del tennista | Gomito | ALTA |
| 17 | Tunnel carpale | tunnel carpale | Polso | ALTA |
| 18 | Fascite plantare | fascite plantare | Caviglia/Piede | ALTA |
| 19 | Instabilita caviglia | instabilita caviglia, distorsione caviglia | Caviglia/Piede | ALTA |
| 20 | Ipertensione | ipertensione, pressione alta | Cardiovascolare | ALTA |
| 21 | Cardiopatia | cardiopatia, cardiaci gravi | Cardiovascolare | ALTA |
| 22 | Insufficienza cardiaca | insufficienza cardiaca, scompenso | Cardiovascolare | ALTA |
| 23 | Diabete | diabete, glicemia alta | Metabolico | ALTA |
| 24 | Osteoporosi | osteoporosi | Metabolico | ALTA |
| 25 | Obesita | obeso, obesit | Metabolico | ALTA |
| 26 | Sciatica | sciatica, radicolopatia | Neurologico | ALTA |
| 27 | Sindrome piriforme | piriforme | Neurologico | ALTA |
| 28 | Asma | asma, respiratori | Respiratorio | ALTA |
| 29 | Gravidanza | gravidanza | Speciale | ALTA |
| 30 | Diastasi | diastasi | Speciale | ALTA |

### K.2 Condizioni Post-Traumatiche Generiche (ID 31-39)

| ID | Condizione | Keywords principali | Categoria |
|----|-----------|-------------------|-----------|
| 31 | Frattura/intervento polso | frattura polso, polso, avambraccio | Post-trauma |
| 32 | Frattura/intervento ginocchio | frattura ginocchio, ginocchio | Post-trauma |
| 33 | Frattura/intervento spalla | frattura spalla, lussazione spalla | Post-trauma |
| 34 | Frattura/intervento caviglia | frattura caviglia, caviglia, achille | Post-trauma |
| 35 | Frattura/intervento anca | frattura femore, protesi anca | Post-trauma |
| 36 | Frattura/intervento colonna | frattura vertebrale, spondilite anchilosante | Post-trauma |
| 37 | Frattura/intervento gomito | frattura gomito, gomito | Post-trauma |
| 38 | Cervicalgia | cervicalgia, collo, dolore cervicale | Sintomatologica |
| 39 | Lombalgia | lombalgia, mal di schiena, dolore lombare | Sintomatologica |

### K.3 Condizioni Aggiuntive (ID 40-47)

| ID | Condizione | Keywords principali | Categoria |
|----|-----------|-------------------|-----------|
| 40 | Fibromialgia | fibromialgia | Reumatologica |
| 41 | Ipermobilita | ipermobilita, ehlers, lassita articolare | Ortopedica |
| 42 | Ipotiroidismo | ipotiroidismo, tiroide, levotiroxina, eutirox | Metabolica |
| 43 | BPCO | bpco, broncopneumopatia, enfisema | Respiratoria |
| 44 | Diabete tipo 1 | diabete tipo 1, insulinodipendente | Metabolica |
| 45 | Neuropatia | neuropatia, formicolio piedi | Neurologica |
| 46 | Artrosi spalla | artrosi spalla, gleno-omerale | Ortopedica |
| 47 | Artrosi mani | artrosi mani, artrosi polso, rizoartrosi | Ortopedica |

### K.4 Flag Strutturali Anamnesi

| Flag Booleano | Condition ID Mappate | Riga |
|---------------|---------------------|------|
| problemi_cardiovascolari | [20, 21] (ipertensione + cardiopatia) | 186 |
| problemi_respiratori | [28] (asma) | 187 |

### K.5 Regole Farmacologiche

| Flag | Keywords | Nota Clinica | Riga |
|------|---------|-------------|------|
| beta_blocker | betabloccante, atenololo, bisoprololo, metoprololo, propranololo, carvedilolo, nebivololo | FC a riposo non affidabile. Usare RPE. | 199-202 |
| anticoagulant | anticoagulante, warfarin, coumadin, eparina, eliquis, xarelto, pradaxa | Rischio emorragico. Evitare alto rischio caduta. | 204-207 |
| corticosteroid | cortisone, prednisone, desametasone, betametasone, metilprednisolone | Uso prolungato indebolisce tendini. Cautela carichi pesanti. | 209-212 |
| insulin | insulina, novorapid, lantus, humalog, toujeo, fiasp, levemir | Rischio ipoglicemia. Zuccheri rapidi a portata. | 214-217 |
| statin | statina, atorvastatina, rosuvastatina, simvastatina | Possibile mialgia da statine. Monitorare dolore post-esercizio. | 219-221 |

**Confidenza**: ALTA (tutte le regole basate su evidenza clinica consolidata)
**Totale sezione K**: 80 keyword rules + 2 flag strutturali + 5 regole farmacologiche = 87

---

## Riepilogo Parametri

| Sezione | Parametri | Confidenza prevalente |
|---------|-----------|----------------------|
| A. EMG Matrix | 53 (celle non-zero) | ALTA (primari), MEDIA (secondari) |
| B. Hypertrophy Weights | 4 | MEDIA |
| C. Volume Targets | 180 (15×3×4) | ALTA |
| D. Parametri Carico | 50 (5×10) | ALTA |
| E. Balance Ratios | 15 (5×3) | MEDIA |
| F. Scaling Demografico | 6 | MEDIA |
| G. Score Composition | 27 | BASSA |
| H. Costanti Algoritmiche | ~80 | Misto |
| I. Tabelle LARN | ~200 | ALTA |
| J. Frequenze CREA | 15 | ALTA |
| K. Safety Rules | 87 | ALTA |
| **TOTALE** | **~717** | — |

---

## Changelog

| Data | Versione | Modifica |
|------|----------|---------|
| 2026-04-19 | 1.0 | Estrazione iniziale da codice — 717 parametri in 11 sezioni |

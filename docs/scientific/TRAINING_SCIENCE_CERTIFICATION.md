# TRAINING_SCIENCE_CERTIFICATION.md — Training Science + Intelligence + Diff

> **Stato**: DRAFT | **Versione**: 1.0 | **Data**: 2026-04-19
> **Copertura**: ~3,500 LOC core + ~1,100 LOC intelligence/diff = ~4,600 LOC
> **File**: 38 file in `api/services/training_science/` + 2 router
> **Supersedes**: `TRAINING_SCIENCE_ENGINE.docx`, `TRAINING_SCIENCE_AUDIT.docx`, `archive/specs/TRAINING-SCIENCE-SPEC.md`

---

## 1. Architettura

### 1.1 Mappa dei 6 Sottosistemi

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TRAINING SCIENCE ENGINE                          │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ Fondamenta   │  │ Algoritmi    │  │ SMART Runtime            │  │
│  │              │  │              │  │                          │  │
│  │ EMG Matrix   │  │ Plan Builder │  │ Protocol Registry        │  │
│  │ Volume Model │  │ Plan Analyzer│  │ Constraint Engine        │  │
│  │ Balance      │  │ Periodization│  │ Evidence Types           │  │
│  │ Principles   │  │ Split Logic  │  │ Feasibility Engine       │  │
│  │ Load Model   │  │ Session Order│  │ Exercise Ranker          │  │
│  │              │  │              │  │ Exercise Catalog         │  │
│  │              │  │              │  │ Plan Package Service     │  │
│  │              │  │              │  │ Profile Resolver         │  │
│  │              │  │              │  │ Validation Contracts     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ Safety       │  │ Training     │  │ Workout Diff             │  │
│  │ Engine       │  │ Intelligence │  │                          │  │
│  │ (→ doc sep.) │  │              │  │ Piano vs Eseguito        │  │
│  │              │  │ Dose-Response│  │ Compliance %             │  │
│  │              │  │ Balance Real │  │ Punti deboli/forti       │  │
│  │              │  │ Intensity    │  │                          │  │
│  │              │  │ Recovery     │  │                          │  │
│  │              │  │ Alerts       │  │                          │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow

```
Input                 Planning              Analysis            Post-Execution
─────                 ────────              ────────            ──────────────
Client Profile   ──→  Profile Resolver  ──→ Plan Analyzer  ──→ Training Intelligence
  (eta, sesso,        Protocol Select       Score 4D           Dose-Response
   livello,           Split Logic           Balance Check      Volume Trend
   obiettivo,         Session Order         Frequency Check    Balance Real
   frequenza)         Plan Builder          Recovery Check     Intensity Zones
                      Exercise Ranker                          Recovery Overlap
Safety Map       ──→  Feasibility Engine                       Alert Predittivi
  (47 condizioni)     Constraint Engine
                                                           ──→ Workout Diff
Catalog.db       ──→  Exercise Catalog                         Compliance %
  (500 esercizi)      Demand Vector 10D                        Delta per variabile
```

### 1.3 Principi Architetturali

1. **Determinismo**: stesso input → stesso output. Zero randomness nel core (seed solo in SMART runtime).
2. **Dual Volume**: ogni esercizio produce volume meccanico (serie totali) E volume ipertrofico (serie x peso ipertrofico). Il modello traccia entrambi.
3. **SSoT Backend**: il frontend consuma via API, mai duplica costanti scientifiche.
4. **Dual-Session**: funzioni che toccano catalogo e business usano session separate (crm.db vs catalog.db).
5. **Feedback Loop**: dopo la prima build, il plan analyzer trova carenze; il builder corregge in max 1 iterazione.

---

## 2. Fondamenta

### 2.1 Matrice EMG

La matrice EMG e' il cuore del motore: mappa 18 pattern di movimento a 15 gruppi muscolari con coefficienti di attivazione 0.0-1.0.

**Scala a 4 livelli**: 1.0 (>70% MVC), 0.7 (40-70%), 0.4 (20-40%), 0.2 (10-20%)
**Sparsita**: 53 celle non-zero su 270 possibili (20%)

Razionale: la scala discreta a 4 livelli cattura le differenze EMG significative senza falsa precisione. La letteratura EMG (Contreras 2010, Schoenfeld 2010, Trebs 2010) riporta bande di attivazione, non valori puntuali.

→ Valori completi: **PARAMETER_REGISTRY.md §A**

### 2.2 Hypertrophy Weights

Trasforma il volume meccanico in volume ipertrofico applicando un peso per livello di contributo.

**Regola fondamentale**: Israetel RP 2020 — "count indirect volume as roughly half a set". FitManager implementa questa regola con 4 pesi discreti:
- Primario (1.0 EMG) → 1.0 set ipertrofico
- Sinergista maggiore (0.7) → 0.5 set
- Sinergista minore (0.4) → 0.25 set
- Stabilizzatore (0.2) → 0.0 set (sotto soglia)

**Computazione duale**: il sistema traccia sempre due colonne parallele — volume meccanico e volume ipertrofico. Il ratio tra i due indica l'efficienza di un programma: un piano con molti compound ha alto volume meccanico ma meno ipertrofico per muscoli piccoli.

→ Valori: **PARAMETER_REGISTRY.md §B**

### 2.3 Volume Model — MEV/MAV/MRV

Definisce i target di volume settimanale per 15 muscoli x 3 livelli.

**Terminologia** (Israetel RP 2020):
- **MEV** (Minimum Effective Volume): sotto questa soglia, zero stimolo adattativo
- **MAV** (Maximum Adaptive Volume): range ottimale per ipertrofia/adattamento
- **MRV** (Maximum Recoverable Volume): oltre questa soglia, overtraining

**Invarianti**:
1. MEV = 0 per muscoli con volume indiretto sufficiente (delt_ant, trapezio, core, adduttori)
2. MEV > 0 solo per muscoli che necessitano stimolo diretto esplicito
3. MAV_min < MAV_max < MRV (sempre, per ogni muscolo x livello)
4. I valori sono in serie ipertrofiche pesate (dopo applicazione hypertrophy weights)

**Scaling demografico**:
- Formula: `target_scalato = target × sex_factor × age_factor`
- MEV scala solo per `fattore_volume` dell'obiettivo, NON per demografici
- MAV_min, MAV_max, MRV scalano per entrambi

→ Valori: **PARAMETER_REGISTRY.md §C, §F**

### 2.4 Scaling Demografico

Due fattori indipendenti moltiplicati:
- **Sesso**: M=1.0, F=0.85 (Schoenfeld 2017, Vingren 2010 — testosterone ~15x inferiore)
- **Eta**: 0-29=1.0, 30-44=0.95, 45-59=0.85, 60+=0.75

Cosa scala: MAV e MRV (capacita' di recupero)
Cosa NON scala: MEV (soglia minima universale per stimolo)

→ Valori: **PARAMETER_REGISTRY.md §F**

### 2.5 Parametri di Carico

5 obiettivi (forza, ipertrofia, resistenza, dimagrimento, tonificazione) x 10 parametri ciascuno. Ogni obiettivo ha range intensita, rep range, distribuzione compound/isolation, tempi di riposo, frequenza target e fattore di volume.

**Design choice critica**: `fattore_volume` scala l'intero volume target MEV/MAV/MRV per adattare il piano all'obiettivo. Ipertrofia = 1.0 (baseline), forza/tonificazione = 0.70, dimagrimento = 0.80, resistenza = 0.60.

→ Valori: **PARAMETER_REGISTRY.md §D**

### 2.6 Rapporti Biomeccanici

5 rapporti che misurano l'equilibrio del piano:
1. **Push:Pull** (1.0 ±0.15) — NSCA gold standard, prevenzione upper crossed syndrome
2. **Push H:V** (1.5 ±1.0) — bilancio orizzontale/verticale pushing
3. **Pull H:V** (1.2 ±0.80) — bilancio orizzontale/verticale pulling
4. **Quad:Ham** (0.80 ±0.30) — prevenzione ACL, equilibrio catena anteriore/posteriore
5. **Ant:Post** (0.65 ±0.25) — Sahrmann/Janda upper-lower crossed syndrome prevention

**Derivazione Quad:Ham 0.80**: dato che squat:hinge e' il ratio prevalente e squat contribuisce quad(1.0)+ham(0.4), il ratio naturale e' n/(0.25n+n) = 0.80.

→ Valori: **PARAMETER_REGISTRY.md §E**

### 2.7 Intensita e %1RM

**NSCA Rep-Max Table**: tabella empirica validata (Haff & Triplett 2016, Table 15.1) che mappa reps → %1RM. 15 punti dati da 1RM (100%) a 25RM (55%).

**RIR Adjustment**: -2.5% per ogni RIR aggiuntivo (Zourdos 2016). Consente di calcolare il carico target dato un RIR desiderato.

**5 Zone Intensita** (NSCA): massimale (90-100%), sub-massimale (80-90%), ipertrofia (67-80%), resistenza (50-67%), attivazione (0-50%).

**4 Fasi Mesociclo**: accumulazione (RPE 6-7.5), intensificazione (RPE 7-8.5), overreaching (RPE 8-9.5), deload (RPE 5-6.5).

→ Valori: **PARAMETER_REGISTRY.md §H.4-H.7**

---

## 3. Algoritmi

### 3.1 Plan Builder — 4 Fasi + Feedback Loop

**Input**: `ResolvedPlanContext` (profilo scientifico, safety map, obiettivo, frequenza, livello)
**Output**: `TSCanonicalPlan` (piano strutturato con sessioni → slot → esercizi)

```
FASE 1: Struttura (Split Logic)
  frequenza → split (full_body / upper_lower / PPL)
  split → session_roles (lista ruoli per sessione)
  ruoli → compound_patterns per sessione

FASE 2: Volume Allocation
  Per ogni muscolo:
    target_volume = volume_table[muscolo][livello] × demo_factor × fattore_volume
  Per ogni sessione:
    Distribuisci target su compound patterns via CONTRIBUTION_MATRIX
    Calcola serie per pattern: target / (freq × hyp_weight)

FASE 3: Compensazione (Isolamenti)
  Per ogni muscolo con volume < MAV_min:
    Se ISOLAMENTO_PER_MUSCOLO[muscolo] esiste:
      Aggiungi isolamento in sessioni affini (AFFINITA_ISOLAMENTO)
    Altrimenti:
      Boost compound patterns correlati (COMPOUND_PER_MUSCOLO)
  Limiti: max _MAX_ISOLATION_SESSIONE, max _MAX_COMPOUND_BOOST_PER_SESSION

FASE 4: Validazione e Capping
  Cap serie per slot: max _MAX_SERIE_PER_SLOT (6)
  Cap slot per sessione: max _MAX_SLOT_SESSIONE[livello]
  Cap volume settimanale: max _MAX_WEEKLY_SERIES[livello]
  Feedback → Plan Analyzer → se carenze → FASE 3 (max 1 iterazione)
```

**Design choice**: `_MAX_FEEDBACK_ITERATIONS = 1`. Una sola iterazione di correzione per evitare oscillazioni. L'esperienza ha mostrato che una iterazione risolve >90% delle carenze senza creare nuovi problemi.

### 3.2 Plan Analyzer — Scoring 4D

**Input**: `TSCanonicalPlan` + profilo scientifico
**Output**: Score 0-100 + breakdown + warnings

```
SCORE = Volume(40) + Balance(25) + Frequency(20) + Recovery(15)

Volume (max 40 punti):
  Per ogni muscolo m:
    volume_hyp = sum(serie × hyp_weight per pattern)
    zona = classify(volume_hyp, MEV[m], MAV_min[m], MAV_max[m], MRV[m])
    punti_m = coverage_weight[zona] × muscle_importance[m]
  volume_score = (sum(punti_m) / sum(muscle_importance)) × 40

Balance (max 25 punti):
  Per ogni rapporto in BALANCE_RATIOS:
    ratio = numeratore / denominatore
    ok = |ratio - target| <= tolleranza
  balance_score = (rapporti_ok / 5) × 25

Frequency (max 20 punti):
  Per ogni muscolo m:
    freq_ok = freq[m] >= 2
  freq_score = (muscoli_freq_ok / 15) × 20
  freq_score -= 4 per ogni warning frequenza

Recovery (max 15 punti):
  Per ogni coppia sessioni adiacenti (gap <= 48h):
    overlap = muscoli con serie >= 2.0 in ENTRAMBE
    Se overlap cumulativo >= 5.0 → warning
  recovery_score = 15 - (5 × n_warnings)
```

### 3.3 Periodizzazione

**Modello**: periodizzazione lineare ondulata per mesociclo.

```
Mesociclo:
  Durata: DURATA_MESOCICLO[livello] settimane (4/5/6)
  Struttura: N-1 settimane carico + 1 settimana deload

Volume settimanale:
  Per settimana k (1..N-1):
    t = (k-1) / (N-2)    # normalizzato [0, 1]
    fattore = base + t × (picco - base)    # interpolazione lineare
  Settimana N (deload):
    fattore = deload (0.50)

RPE/Intensita:
  Accumulazione (sett 1-2): RPE 6.0-7.5, %1RM 60-72%
  Intensificazione (sett 3-N-2): RPE 7.0-8.5, %1RM 70-80%
  Overreaching (sett N-1): RPE 8.0-9.5, %1RM 75-85%
  Deload (sett N): RPE 5.0-6.5, %1RM 55-65%
```

### 3.4 SMART Runtime — 18 File

Il sistema SMART (Science-Managed Automated Ranking Technology) e' la pipeline che trasforma un profilo cliente in un piano allenamento concreto con esercizi specifici.

```
Profile Resolver → Protocol Registry → Constraint Engine → Evidence Types
                                                              ↓
Exercise Catalog → Feasibility Engine → Exercise Ranker → Plan Package Service
                                                              ↓
                                      Validation Contracts ← Validation Catalog
                                                              ↓
                                                     TSPlanPackage (output)
```

**Protocol Registry**: registra protocolli (es. "PRT-001 Beginner Full Body") con constraint, obiettivo, frequenza, split.

**Constraint Engine**: valuta vincoli di protocollo (volume ceiling, pattern obbligatori, skill gate).

**Feasibility Engine v2**: classifica esercizi in 3 categorie (feasible / discouraged / infeasible) attraverso 3 gate:
1. Beginner gate (blocca esercizi avanzati)
2. Safety gate (mappa severity → verdetto)
3. Demand ceiling (verifica demand vector 10D)

**Exercise Ranker v2**: scoring multi-componente per selezione esercizi:
- Pattern match: 50 pt (esatto) / 36 pt (compatibile)
- Muscle target: 25 pt (primario) / 12 pt (secondario)
- Difficulty: ±12 pt (allineamento livello)
- Objective: +8 / -12 a -30 pt (allineamento rep range)
- Safety: -20 (caution) / -40 (modify) / -80 (avoid)
- Balance: ±8 pt (prevenzione squilibri push/pull)
- Frequency/Recovery: ±12 pt cap

**Validation Contracts**: 6 benchmark cases (VM-001..VM-006) con 5 profili client (CFG-A..E) che verificano invarianti (protocol selection, split, ceiling, beginner gate) e snapshot comportamentali.

---

## 4. Training Intelligence (Post-Execution)

**Fonte codice**: `api/routers/training_intelligence.py` (716 LOC)
**Endpoint**: `GET /api/clients/{id}/training-intelligence?mesi=3`

### 4.1 Architettura 3 Livelli

```
Livello 1: Metriche Esecuzione
  Tonnage: serie × reps × kg (aggregato per slot, trend temporale)
  Densita: tonnage / durata_effettiva_min

Livello 2: Dose-Response (Muscolo × Volume × Frequenza)
  Volume settimanale per muscolo (via hypertrophy sets computation)
  Trend detection: diff first_2_weeks vs last_2_weeks
  Frequenza: settimane stimolate / settimane totali (soglia 0.4 EMG)

Livello 3: Balance, Intensita, Recovery, Alert
  Balance ratios reali (calcolati su esecuzione, non su piano)
  Distribuzione intensita per zona (via Epley/Brzycki %1RM estimation)
  Recovery: overlap muscoli in sessioni adiacenti (gap ≤ 1 giorno)
  Alert predittivi: sotto_mev, sopra_mrv, squilibrio, recovery
```

### 4.2 Stima %1RM da Esecuzione

Due formule utilizzate in base al range rep:
- **Epley** (reps ≤ 15): `e1rm = kg × (1 + reps/30)`
- **Brzycki** (16-36 reps): `e1rm = kg × 36 / (37 - reps)`
- **%1RM**: `pct = kg_effettivo / e1rm`
- Classificazione in 5 zone NSCA (→ Registry §H.6)

### 4.3 Trend Detection

```
volume_first_2_weeks = media(volume settimana 1, 2)
volume_last_2_weeks = media(volume settimana N-1, N)
diff = volume_last_2_weeks - volume_first_2_weeks

Se diff > 1.5: trend = "crescente"
Se diff < -1.5: trend = "calante"
Altrimenti: trend = "stabile"
```

Soglia 1.5 serie: scelta conservativa per evitare falsi positivi da variabilita' naturale.

### 4.4 Alert Predittivi

| Tipo Alert | Trigger | Severita |
|-----------|---------|----------|
| sotto_mev | Volume medio muscolo = 0 o < MEV | Warning |
| sopra_mrv | Volume medio muscolo > MRV | Warning |
| squilibrio | Ratio fuori tolleranza ±10% | Warning |
| recovery_overlap | Serie cumulative ≥ 5 in 48h, ≥ 2 per sessione | Warning |

### 4.5 Dashboard Frontend — 10 Sezioni

1. Score complessivo del piano
2. Volume coverage per muscolo (barre con zone MEV/MAV/MRV)
3. Frequenza per muscolo (heatmap settimanale)
4. Balance ratios reali vs target (radar chart)
5. Distribuzione intensita per zona (pie chart)
6. Tonnage trend (line chart temporale)
7. Densita allenamento (tonnage/min)
8. Recovery overlap (matrice sessioni)
9. Trend muscolo per muscolo (crescente/stabile/calante)
10. Alert predittivi (lista actionable)

---

## 5. Workout Diff

**Fonte codice**: `api/routers/workout_diff.py` (411 LOC)
**Endpoint**: `GET /api/clients/{id}/workout-diff?mesi=3`

### 5.1 Compliance Formula

```
Per ogni esercizio con piano ed esecuzione:

  serie_ratio = min(fatto/piano, 1.2)
  reps_ratio = min(media_fatto/media_piano, 1.2)
  kg_ratio = min(fatto/piano, 1.2)

  SE carico nel piano:
    compliance = (serie_ratio × 0.40 + reps_ratio × 0.35 + kg_ratio × 0.25) × 100
  SE no carico (bodyweight):
    compliance = (serie_ratio × 0.55 + reps_ratio × 0.45) × 100

  compliance = min(compliance, 120)    # capped a 120%
```

**Design choices**:
- Pesi 40/35/25: serie pesa di piu' perche' e' il fattore volume; reps secondo perche' determina la zona; carico terzo perche' puo' variare per motivi legittimi (fatica, attrezzatura)
- Cap 120%: consente un bonus per overperformance ma limita outlier
- Redistribuzione no-kg (55/45): mantiene proporzioni relative senza penalizzare bodyweight

### 5.2 Aggregazione

```
Compliance sessione = media(compliance esercizi nella sessione)
Compliance globale = media(compliance sessioni)

Per-esercizio (se esecuzioni >= 2):
  media_compliance_esercizio = media(tutte le esecuzioni)

Punti deboli: top 3 esercizi con compliance piu' bassa
Punti forti: top 3 esercizi con compliance piu' alta
```

### 5.3 Classificazione

| Categoria | Range | Significato |
|-----------|-------|-------------|
| Sopra piano | >= 105% | Overperformance (possibile progressione) |
| In linea | 90-105% | Aderenza al piano |
| Sotto piano | < 90% | Sottoperformance (indagare cause) |

---

## 6. Zone di Incertezza

### 6.1 Confidenza ALTA — Fondazioni Solide

Parametri dove la letteratura e' convergente e il valore e' prescrittivo:
- EMG primari (1.0) per tutti i pattern
- Push:Pull ratio 1.0 (NSCA standard)
- NSCA rep-max table (validata empiricamente)
- Intensita zones (consenso NSCA/ACSM/Schoenfeld)
- MEV = 0 per muscoli con volume indiretto forte
- MEV/MAV/MRV di gruppi muscolari grandi (petto, quad, dorsali)

### 6.2 Confidenza MEDIA — Scelte Ragionate

Parametri dove la letteratura supporta un range ma il valore specifico e' una scelta:
- EMG sinergisti minori (0.4 vs 0.3 vs 0.5 — la letteratura non converge)
- Hypertrophy weights (0.5 "half a set" — Israetel suggerisce un range)
- Age factors (-5%, -15%, -25% — basati su studi ma applicazione pratica varia)
- Sex factor (0.85 — media di studi, range 0.80-0.90)
- Balance ratios secondari (Push H:V, Pull H:V — meno studiati del push:pull)
- Quad:Ham derivazione (0.80 — basato su squat:hinge ratio, non su studi diretti)

### 6.3 Confidenza BASSA — Design Choices

Parametri senza supporto diretto in letteratura, necessitano validazione empirica:
- **Score weights** (40/25/20/15): nessuna fonte prescrive questi pesi. Scelti per importanza percepita.
- **Muscle importance tiers** (1.0/0.7/0.4): classificazione pragmatica, non da letteratura.
- **Coverage weights** (1.0/0.8/0.5): scaling arbitrario per zone volume.
- **Compliance weights** (40/35/25): pesi workout diff senza fonte.
- **Trend threshold** (±1.5 serie): soglia conservativa senza validazione.
- **Feedback iterations** (max 1): scelta ingegneristica.
- **Ranker scoring** (50/25/12/±12/±8): tutti i pesi sono design choices.

### 6.4 Validazione Empirica Necessaria

Lista actionable per trainer reali (POC con 10 Fondatori):

1. **Score weights**: il 40/25/20/15 produce score che riflettono la qualita' percepita dai trainer?
2. **Hypertrophy weights**: il "mezzo set" per sinergisti maggiori e' troppo generoso o troppo conservativo?
3. **Age factors**: clienti 50+ rispondono effettivamente al 85% del volume dei 30enni?
4. **Balance tolerances**: le tolleranze sono troppo larghe (falsi OK) o troppo strette (troppi warning)?
5. **Compliance thresholds**: 90% e 105% sono le soglie giuste per classificare aderenza?
6. **Trend detection**: ±1.5 serie e' sensibile abbastanza? Troppi falsi positivi/negativi?
7. **Recovery overlap**: 5 serie cumulative in 48h e' la soglia giusta per alert?
8. **Ranker scoring**: gli esercizi selezionati automaticamente corrispondono alle scelte dei trainer esperti?

---

## 7. Riferimenti Bibliografici

### Fonti Primarie (textbook)

1. **NSCA 2016**: Haff, G.G. & Triplett, N.T. *Essentials of Strength Training and Conditioning* (4th ed.). National Strength and Conditioning Association. — Riferimento per rep-max table (Tab. 15.1), intensity zones, periodizzazione, exercise order, push:pull ratio.

2. **Schoenfeld 2010**: Schoenfeld, B.J. *The mechanisms of muscle hypertrophy and their application to resistance training*. J Strength Cond Res, 24(10):2857-72. — Meccanismi ipertrofia, tensione meccanica, stress metabolico.

3. **Schoenfeld 2016**: Schoenfeld, B.J. et al. *Effects of resistance training frequency on measures of muscle hypertrophy*. Sports Med, 46(11):1689-97. — Meta-analisi: frequenza >= 2x/settimana superiore.

4. **Schoenfeld 2017**: Schoenfeld, B.J. et al. *Dose-response relationship between weekly resistance training volume and increases in muscle mass*. Med Sci Sports Exerc, 49(3):661-71. — Volume dose-response, range ipertrofia.

### Fonti Secondarie (specialistiche)

5. **Israetel RP 2020**: Israetel, M., Hoffmann, J. & Smith, C.W. *Scientific Principles of Hypertrophy Training*. Renaissance Periodization. — MEV/MAV/MRV framework, "half a set" rule per volume indiretto, volume ceilings.

6. **Helms 2019**: Helms, E.R., Valdez, A. & Morgan, A. *The Muscle and Strength Pyramid: Training* (2nd ed.). — Mesociclo design, deload strategy, upper/lower split rationale.

7. **Contreras 2010**: Contreras, B. *The Glute Guy*. T Nation / research publications. — EMG glutei, hip thrust, grip contribution nei pull.

8. **Trebs 2010**: Trebs, A.A. et al. *An electromyography analysis of 3 muscles surrounding the shoulder joint during the performance of a chest press exercise at several angles*. J Strength Cond Res, 24(7):1925-30. — EMG petto clavicolare in push verticale.

9. **Ebben 2009**: Ebben, W.P. et al. *Muscle activation during lower body resistance training*. Int J Sports Med, 30(1):1-8. — Soleus in squat, attivazione lower body.

### Fonti Biomeccaniche

10. **Sahrmann 2002**: Sahrmann, S.A. *Diagnosis and Treatment of Movement Impairment Syndromes*. Mosby. — Upper/lower crossed syndrome, razionale rapporti biomeccanici.

11. **Janda 1983**: Janda, V. *Muscle Function Testing*. Butterworths. — Crossed syndromes, squilibri posturali.

12. **Alentorn-Geli 2009**: Alentorn-Geli, E. et al. *Prevention of non-contact anterior cruciate ligament injuries*. Knee Surg Sports Traumatol Arthrosc, 17(7):705-29. — ACL risk con H:Q < 0.6, razionale quad:ham ratio.

13. **Boettcher 2008**: Boettcher, C.E. et al. *Which is the optimal exercise to strengthen supraspinatus?*. Med Sci Sports Exerc, 40(11):1920-7. — Push H:V rationale spalla.

### Fonti Carico e Intensita

14. **Zourdos 2016**: Zourdos, M.C. et al. *Novel resistance training-specific rating of perceived exertion scale measuring repetitions in reserve*. J Strength Cond Res, 30(1):267-75. — RIR-based RPE, -2.5% per RIR.

15. **ACSM 2009**: American College of Sports Medicine. *Position Stand: Progression models in resistance training*. Med Sci Sports Exerc, 41(3):687-708. — Resistenza muscolare, range rep alto, raccomandazioni base.

16. **Ralston 2017**: Ralston, G.W. et al. *The effect of weekly set volume on strength gain: A meta-analysis*. Sports Med, 47(12):2585-601. — Volume forza.

17. **Krieger 2010**: Krieger, J.W. *Single vs. multiple sets of resistance exercise for muscle hypertrophy*. J Strength Cond Res, 24(4):1150-9. — Dose-response volume.

### Fonti Demografiche

18. **Hakkinen 2001**: Hakkinen, K. et al. *Neuromuscular adaptations during concurrent strength and endurance training versus strength training*. Eur J Appl Physiol, 89(1):42-52. — Adattamenti neuromuscolari con l'eta.

19. **Peterson 2011**: Peterson, M.D. et al. *Resistance exercise for muscular strength in older adults*. Ageing Res Rev, 10(2):226-37. — Meta-analisi volume/forza over 50.

20. **Vingren 2010**: Vingren, J.L. et al. *Testosterone physiology in resistance exercise and training*. Sports Med, 40(12):1037-53. — Differenze ormonali M/F.

21. **Schoenfeld 2021**: Schoenfeld, B.J. *Science and Development of Muscle Hypertrophy* (2nd ed.). Human Kinetics. — Dimagrimento e preservazione massa.

---

## 8. Changelog Certificazione

| Data | Versione | Modifica |
|------|----------|---------|
| 2026-04-19 | 1.0 | Prima stesura completa — architettura, 6 sottosistemi, algoritmi, intelligence, diff, 21 riferimenti |

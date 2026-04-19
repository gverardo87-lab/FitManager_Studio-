# NUTRITION_SCIENCE_CERTIFICATION.md — Nutrition Science Engine

> **Stato**: DRAFT | **Versione**: 1.0 | **Data**: 2026-04-19
> **Copertura**: 2,448 LOC in 10 moduli (`api/services/nutrition_science/`)
> **Fonti**: LARN 2014, CREA 2019, CREA-Dir 2018, OMS, EFSA
> **Supersedes**: `docs/technical/NUTRITION_ENGINE_V3.md` (design doc → questa e' la spec dello stato implementato)

---

## 1. Architettura

### 1.1 Pipeline 7 Moduli

```
┌───────────────┐     ┌──────────────┐     ┌──────────────┐
│ Profile       │────>│ Food Pool    │────>│ Food         │
│ Resolver      │     │ Builder      │     │ Selector     │
│               │     │              │     │              │
│ BMR, PAL,     │     │ 880 alimenti │     │ Nutrient-    │
│ target macro  │     │ → 18 pool    │     │ aware top-3  │
└───────────────┘     └──────────────┘     └──────────────┘
                                                  │
                                                  v
┌───────────────┐     ┌──────────────┐     ┌──────────────┐
│ Plan          │<────│ LARN         │<────│ Day          │
│ Generator     │     │ Validator    │     │ Composer     │
│               │     │              │     │              │
│ Orchestrator  │     │ Score 3 assi │     │ 5 pasti/gg   │
│ 7 giorni      │     │ 25+35+40    │     │ Dual protein │
└───────────────┘     └──────────────┘     │ rotation     │
        │                                   └──────────────┘
        v                                          │
┌───────────────┐                                  v
│ Portion       │                          ┌──────────────┐
│ Optimizer     │<─────────────────────────│ Meal         │
│               │                          │ Archetypes   │
│ 4-step        │                          │              │
│ caloric/macro │                          │ 14 slot      │
│ rebalancing   │                          │ proteici     │
└───────────────┘                          └──────────────┘
```

### 1.2 File Manifest

| File | LOC | Funzione |
|------|-----|----------|
| `larn_tables.py` | 284 | Tabelle LARN 2014 (proteine, vitamine, minerali) |
| `larn_portions.py` | 277 | Porzioni standard LARN, gruppi alimentari, frequenze |
| `meal_archetypes.py` | 151 | Template pasti + rotazione proteica duale 7+7 slot |
| `types.py` | 91 | Data classes: Sex, LarnLevel, ClientProfile, Assessment |
| `food_pool_builder.py` | 269 | Auto-classificazione 880 alimenti → 18 pool funzionali |
| `food_selector.py` | 243 | Selezione nutrient-aware con scoring e diversita |
| `portion_optimizer.py` | 249 | Ottimizzazione porzioni multi-criterio 4-step |
| `plan_validator.py` | 379 | Scoring 3 assi: macro 25% + micro 35% + freq 40% |
| `frequency_validator.py` | 227 | Validazione frequenze CREA 2018 |
| `plan_generator.py` | 265 | Orchestratore: selezione giornaliera + ottimizzazione |

**Totale**: 2,448 LOC

### 1.3 Principi

1. **LARN 2014 SSoT**: tutti i target nutrizionali derivano dalle tabelle LARN italiane (non FDA/RDA americane)
2. **CREA 2019**: 880 alimenti dal database composizione alimenti italiano
3. **Servability v5**: solo pietanze (piatti pronti) come secondi piatti — zero ingredienti crudi a tavola
4. **Dual protein rotation**: 7 slot pranzo + 7 slot cena per varieta settimanale proteica
5. **Determinismo con seed**: `random.seed()` per riproducibilita piano
6. **19 micronutrienti tracciati**: 9 minerali + 10 vitamine vs target LARN individuali

---

## 2. Tabelle LARN Certificate

Tutti i valori LARN sono codificati in `larn_tables.py` con 4 livelli di riferimento:
- **AR** (Average Requirement): fabbisogno medio della popolazione
- **PRI** (Population Reference Intake): copre il 97.5% della popolazione
- **AI** (Adequate Intake): usato quando AR/PRI non sono determinabili
- **UL** (Tolerable Upper Intake Level): livello massimo sicuro

→ Tabelle complete: **PARAMETER_REGISTRY.md §I**

### 2.1 Nutrienti Tracciati (19)

**9 Minerali**: Calcio, Ferro, Zinco, Magnesio, Fosforo, Potassio, Selenio, Sodio, Fibra
**10 Vitamine**: A, D, E, C, B1 (Tiamina), B2 (Riboflavina), B3 (Niacina), B6 (Piridossina), B9 (Folato), B12 (Cobalamina)

### 2.2 Nutrienti Diet-Limited

La Vitamina D e' classificata come "diet-limited": il LARN 2014 riconosce che l'apporto alimentare e' insufficiente per la maggior parte della popolazione italiana. La sintesi cutanea (esposizione solare) e/o la supplementazione sono le fonti primarie.

**Impatto scoring**: se carente, contribuisce 60 punti (vs 0-45 per nutrienti normali) per evitare che nutrienti irraggiungibili dalla sola dieta penalizzino ingiustamente il piano.

### 2.3 Gravidanza e Allattamento

Addizioni ai fabbisogni base gestite tramite lookup tables separate. Per le proteine, la gravidanza ha fabbisogni per trimestre (+1, +8, +26 g/giorno).

→ Valori completi: **PARAMETER_REGISTRY.md §I.8**

---

## 3. Frequenze CREA-Dir 2018

### 3.1 Frequenze Settimanali per Gruppo

9 sottogruppi alimentari con range minimo/massimo di porzioni settimanali, derivati dalle Linee Guida CREA 2018.

→ Valori: **PARAMETER_REGISTRY.md §J.1**

### 3.2 Sub-frequenze Proteiche

6 sottocategorie proteiche con vincoli settimanali:
- Pesce: 2-4x (preferire pesce azzurro)
- Carne bianca: 1-4x
- Carne rossa: 0-2x (WCRF 2018: limitare)
- Uova: 2-4x
- Legumi: 2-5x (fonte vegetale)
- Affettati: 0-1x (CREA: limitare insaccati)

→ Valori: **PARAMETER_REGISTRY.md §J.2**

### 3.3 Assessment Algorithm

```
Per ogni sottogruppo:
  porzioni_settimana = sum(grammi_pasto / porzione_standard_LARN)

  Se porzioni < min × 0.70: status = BASSO
  Se porzioni > max × 1.30: status = ALTO
  Altrimenti: status = OTTIMALE

Score frequenze:
  OTTIMALE: 100 punti
  BASSO: proporzionale alla copertura (max 60 punti)
  ALTO: moderato (min 30 punti)
  Finale: media su tutti i sottogruppi valutabili
```

---

## 4. Algoritmi

### 4.1 Profile Resolver

**Input**: eta, sesso, peso_kg, altezza_cm, gravidanza, allattamento
**Output**: target kcal, target macro (g), target LARN per 19 micronutrienti

```
1. BMR (Harris-Benedict o Mifflin-St Jeor)
2. TDEE = BMR × PAL (Physical Activity Level)
3. Target kcal = TDEE × fattore_obiettivo

4. Macro default (centro range LARN):
   Proteine: 15% kcal → g = kcal × 0.15 / 4
   Carboidrati: 52.5% kcal → g = kcal × 0.525 / 4
   Grassi: 27.5% kcal → g = kcal × 0.275 / 9

5. Protein floor: se peso_kg × 0.90 > target_prot:
   target_prot = peso_kg × 0.90 (LARN PRI)

6. LARN lookup: per ogni micronutriente
   target = lookup_larn(nutriente, eta, sesso)
   Se gravidanza/allattamento: target += addizione
```

### 4.2 Food Pool Builder (v5 Servability Architecture)

**Input**: 880 alimenti attivi da nutrition.db
**Output**: 18 pool funzionali

```
18 pool:
  Dairy: dairy, dairy_breakfast, dairy_light, dairy_aged, dairy_plant
  Cereal: cereal, carb_light
  Fruit: fruit, nuts
  Fat: fat, condimento
  Sides: primo_piatto, contorno
  Protein: secondo_fish, secondo_poultry, secondo_red_meat,
           secondo_egg, secondo_legume, secondo_deli

Classificazione per ogni alimento:
  1. Filtra per categoria CREA (es. cat 8 = carne)
  2. Applica keyword filter (positivi e negativi)
  3. Applica soglie nutrizionali (proteine, grassi, kcal)
  4. v5: solo pietanze per pool proteici (piatti pronti, non ingredienti crudi)

Ordinamento interno:
  Per _micro_count() decrescente (alimenti nutrient-dense prima)
  _micro_count = count(campi_micronutrienti non-null)
```

**Design choice v5**: i pool proteici (secondo_*) contengono solo pietanze (piatti finiti con ricetta). Questo garantisce che il piano nutrizionale suggerisca piatti reali servibili a tavola, non ingredienti crudi come "petto di pollo, crudo".

### 4.3 Day Composer — Rotazione Proteica Duale

**5 pasti/giorno**: COLAZIONE, SPUNTINO_MATTINA, PRANZO, SPUNTINO_POMERIGGIO, CENA

**14 slot proteici** (7 pranzi + 7 cene):

| Giorno | Pranzo | Cena |
|--------|--------|------|
| Lun | Legumi | Pesce |
| Mar | Pollo | Uova |
| Mer | Pesce | Pollo |
| Gio | Legumi | Legumi |
| Ven | Carne rossa | Pesce |
| Sab | Pollo | Uova |
| Dom | Affettati | Legumi |

**Compliance CREA 2018**:
- Pesce: 3x/sett (2 cena + 1 pranzo) — range 2-4 OK
- Pollo: 3x/sett — range 1-4 OK
- Legumi: 4x/sett — range 2-5 OK
- Uova: 2x/sett — range 2-4 OK
- Carne rossa: 1x/sett — range 0-2 OK
- Affettati: 1x/sett — range 0-1 OK

### 4.4 Portion Optimizer — 4 Step

**Input**: pasti giornalieri con porzioni standard, target kcal/macro
**Output**: porzioni ottimizzate clamped a ±50% della standard LARN

```
STEP 1: Scaling calorico globale
  kcal_ratio = target_kcal / kcal_attuali
  Clamp ratio a [0.4, 1.6]
  Scala tutte le porzioni, clamp a limiti per ruolo

STEP 2: Aggiustamento proteine
  Se |delta_prot| > 5g:
    Distribuisci su ~3 pasti proteici
    extra_g = delta / (prot_per_g × 3)
    Clamp a limiti ruolo

STEP 3: Aggiustamento grassi
  3a: Se |delta_fat| > 3g:
    Scala ruoli grassi (olio, noci)
  3b: Se eccesso > 5g:
    Riduci piatti ad alto contenuto grasso
    shrink = max(0.65, 1 - eccesso / fat_kcal)

STEP 4: Ribilanciamento carboidrati
  Ricalcola kcal dopo step 2-3
  Se |gap_kcal| > 50:
    Scala fonti carb (primo, pane, cereali)
    carb_scale = 1 + (gap / carb_kcal)
    Clamp a [0.5, 2.5]
```

### 4.5 LARN Validator — Score 3 Assi

**Formula composita**:

```
SCORE_FINALE = macro_score × 0.25 + micro_score × 0.35 + freq_score × 0.40
```

**Fallback** (senza dati frequenze): `macro × 0.35 + micro × 0.65`

**Asse 1 — Macro (max 100)**:

```
Range LARN:
  Proteine: 12-20% kcal
  Carboidrati: 45-60% kcal
  Grassi: 20-35% kcal

Per ogni macro:
  Se nel range: +33 punti
  Se fuori: penalty lineare max(0, 33 - distanza% × 1.5)
Score = sum(3 macro) + rounding
Cap a 100
```

**Asse 2 — Micro (max 100)**:

```
Per ogni nutriente (19 tracciati):
  OTTIMALE (≥ PRI o AI): 100 punti
  SUFFICIENTE (≥ AR < PRI): 70 punti
  CARENTE diet-limited: 60 punti (penalita attenuata)
  CARENTE (altro): max(0, min(45, coverage_ratio × 0.45))
  ECCESSO (> UL): 35 punti

Score = media(punti nutrienti valutabili)
```

**Asse 3 — Frequenze CREA (max 100)**:

→ Algoritmo descritto in §3.3

---

## 5. Warning Clinici

6 trigger per warning nel piano nutrizionale:

| Trigger | Condizione | Nota | Confidenza |
|---------|-----------|------|------------|
| Ferro basso | apporto < AR | Rischio anemia, soprattutto donne in eta fertile | ALTA |
| Calcio basso | apporto < AR | Rischio osteoporosi, soprattutto over 60 | ALTA |
| Vitamina D bassa | apporto < AI | Supplementazione quasi sempre necessaria (LARN nota) | ALTA |
| Fibra bassa | apporto < 20g | Rischio stipsi, microbiota impoverito | ALTA |
| Sodio alto | apporto > 2000mg | SDT OMS: < 2000 mg/giorno | ALTA |
| Zuccheri | nota informativa | Monitorare zuccheri semplici < 15% kcal (OMS 2015) | MEDIA |

---

## 6. Zone di Incertezza

### 6.1 PAL (Physical Activity Level)

Il PAL e' il moltiplicatore piu' incerto della pipeline. Dipende da:
- Tipo e frequenza attivita (non solo allenamento)
- Lavoro sedentario vs attivo
- NEAT (Non-Exercise Activity Thermogenesis)

**Attuale**: valore fisso o range semplificato. **Necessita**: questionario dettagliato attivita giornaliera.
**Confidenza**: MEDIA

### 6.2 Optimizer Weights

I pesi nell'optimizer (soglie 5g proteine, 3g grassi, 50 kcal gap) sono convenzioni pratiche:
- 5g proteine: ~1 uovo di delta, sotto questa soglia l'aggiustamento non e' percepibile
- 3g grassi: ~1/3 cucchiaio olio
- 50 kcal: variabilita naturale giornaliera

**Confidenza**: BASSA — necessitano validazione con dietisti

### 6.3 Score Weights (25/35/40)

La distribuzione 25% macro + 35% micro + 40% frequenze e' una scelta architetturale:
- **40% frequenze**: peso dominante perche' le linee guida CREA enfatizzano la varieta come indicatore primario di qualita dieta
- **35% micro**: peso alto perche' i micronutrienti sono il vero discriminante tra diete "buone" e "ottime"
- **25% macro**: peso minore perche' il portion optimizer gia' forza la compliance macro

**Confidenza**: BASSA — necessita validazione con confronto panel dietisti

### 6.4 Porzioni Standard

Le porzioni standard LARN sono per popolazione generale. Per sportivi il range potrebbe essere insufficiente:
- Porzione proteica standard: 100g carne → potrebbe servire 150-200g per atleta
- Scaling ±50%: copre 1400-2800 kcal ma non piani ipercalorici (>3000 kcal)

**Confidenza**: MEDIA — OK per target FitManager (trainer, non nutrizionisti sportivi)

---

## 7. Riferimenti

### Fonti Primarie

1. **LARN 2014**: SINU (Societa Italiana di Nutrizione Umana). *Livelli di Assunzione di Riferimento di Nutrienti ed Energia per la Popolazione Italiana* (IV revisione). — SSoT per tutti i target nutrizionali.

2. **CREA 2019**: Consiglio per la Ricerca in Agricoltura. *Tabelle di Composizione degli Alimenti* (aggiornamento 2019). — 880 alimenti con composizione per 100g, base del database nutrition.db.

3. **CREA-Dir 2018**: CREA. *Linee Guida per una Sana Alimentazione* (revisione 2018). 13 direttive. — Frequenze settimanali, varieta, proteine alternate.

### Fonti Secondarie

4. **EFSA 2017**: European Food Safety Authority. *Dietary Reference Values for Nutrients*. EFSA Journal. — Cross-check su valori LARN, soprattutto UL.

5. **OMS 2015**: World Health Organization. *Guideline: Sugars intake for adults and children*. — Limite zuccheri semplici < 10% kcal (obiettivo < 5%).

6. **OMS Sodium**: WHO. *Guideline: Sodium intake for adults and children*. — SDT < 2000 mg/giorno.

7. **WCRF 2018**: World Cancer Research Fund. *Diet, Nutrition, Physical Activity and Cancer: a Global Perspective*. — Limite carne rossa/processata, varieta frutta/verdura.

8. **Harris-Benedict 1919**: Harris, J.A. & Benedict, F.G. *A biometric study of human basal metabolism*. — Formula BMR classica (rivista Roza & Shizgal 1984).

9. **Mifflin-St Jeor 1990**: Mifflin, M.D. et al. *A new predictive equation for resting energy expenditure*. Am J Clin Nutr. — Formula BMR alternativa piu' accurata.

---

## 8. Changelog

| Data | Versione | Modifica |
|------|----------|---------|
| 2026-04-19 | 1.0 | Prima stesura — 10 moduli, 2,448 LOC, pipeline 7-stage, scoring 3 assi, 19 micronutrienti |

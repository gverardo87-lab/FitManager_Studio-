# Nutrition Engine v3 — Piano Architetturale

## Fondamento scientifico

Ogni riga di codice del generatore di piani alimentari deve essere riconducibile a una fonte scientifica. Nessun numero magico, nessun coefficiente inventato.

### Fonti primarie

| Sigla | Fonte | Edizione | Ambito |
|-------|-------|----------|--------|
| **LARN** | Livelli di Assunzione di Riferimento di Nutrienti ed Energia | IV rev. 2014, SINU | Fabbisogni nutrizionali per sesso, eta', livello attivita' |
| **CREA** | Tabelle di Composizione degli Alimenti | IV ed. 2019, ex-INRAN | Composizione nutrizionale alimenti italiani |
| **CREA-Dir** | Linee Guida per una Sana Alimentazione | Ed. 2018, CREA | 13 direttive alimentari, frequenze settimanali |
| **USDA-FDC** | FoodData Central | 2024, USDA | Composizione nutrizionale (fallback per alimenti non CREA) |
| **OMS/WHO** | Guideline: Sugars intake | 2015 | Zuccheri liberi <10% energia |
| **EFSA** | Dietary Reference Values | 2017 | Valori di riferimento europei (cross-check LARN) |

### Gerarchia delle fonti

```
LARN 2014 (primaria — fabbisogni italiani)
  ↓ se dato non disponibile
EFSA DRV 2017 (europea — compatibile LARN)
  ↓ se dato non disponibile
OMS/WHO (globale — soglie di sicurezza)
```

Per la composizione degli alimenti:
```
CREA 2019 (primaria — database italiano)
  ↓ se alimento non presente
USDA FDC (secondaria — database USA)
  ↓ se alimento non presente
Stima da alimento simile (terziaria — marcata come "stima")
```

---

## Architettura v3 — i 7 moduli

```
┌────────────────────────────────────────────────────────────┐
│                    NUTRITION ENGINE v3                      │
│                                                            │
│  1. PROFILE RESOLVER                                       │
│     ClientProfile → fabbisogni LARN personalizzati         │
│                                                            │
│  2. DYNAMIC POOL BUILDER                                   │
│     nutrition.db → pool alimentari per ruolo funzionale    │
│                                                            │
│  3. WEEKLY PLANNER                                         │
│     Frequenze CREA-Dir → struttura 7 giorni                │
│                                                            │
│  4. DAY COMPOSER                                           │
│     Archetipi pasto → selezione alimenti con varieta'     │
│                                                            │
│  5. PORTION OPTIMIZER                                      │
│     Target macro/micro → aggiustamento porzioni            │
│                                                            │
│  6. LARN VALIDATOR                                         │
│     Piano → score 3 assi (macro + micro + frequenze)       │
│                                                            │
│  7. OUTPUT FORMATTER                                       │
│     Piano validato → struttura per salvataggio + report    │
└────────────────────────────────────────────────────────────┘
```

---

## Modulo 1: Profile Resolver

### Scopo
Tradurre il profilo del cliente in fabbisogni nutrizionali giornalieri personalizzati.

### Input
```
ClientProfile:
  - sesso: M | F
  - eta: anni
  - peso_kg: float
  - altezza_cm: float
  - livello_attivita: sedentario | leggero | moderato | attivo | molto_attivo
  - obiettivo: mantenimento | dimagrimento | massa | ricomposizione
  - condizioni: [gravidanza, allattamento, menopausa, ...] (opzionali)
```

### Output
```
NutrientTargets:
  - energia_kcal: int (BMR × PAL × fattore obiettivo)
  - proteine_g: range (min, target, max)
  - carboidrati_g: range
  - grassi_g: range
  - fibra_g: min
  - 17 micronutrienti: target (PRI o AI da LARN)
```

### Calcolo energia — fonte LARN 2014 cap. 3

**BMR (Basal Metabolic Rate)** — Equazione di Mifflin-St Jeor (LARN 2014 raccomandata):

```
Uomo:  BMR = 10 × peso(kg) + 6.25 × altezza(cm) - 5 × eta(anni) + 5
Donna: BMR = 10 × peso(kg) + 6.25 × altezza(cm) - 5 × eta(anni) - 161
```

Fonte alternativa: Harris-Benedict rivista (Roza & Shizgal, 1984). LARN 2014 riporta entrambe ma raccomanda Mifflin-St Jeor per soggetti normopeso/sovrappeso.

**PAL (Physical Activity Level)** — LARN 2014 tab. 3.6:

| Livello | PAL | Descrizione LARN |
|---------|-----|-----------------|
| Sedentario | 1.40 | Lavoro sedentario, nessun esercizio |
| Leggero | 1.55 | Lavoro sedentario + attivita' leggera 2-3x/settimana |
| Moderato | 1.70 | Lavoro in piedi o attivita' moderata 3-5x/settimana |
| Attivo | 1.85 | Lavoro attivo o esercizio intenso 5-6x/settimana |
| Molto attivo | 2.00-2.20 | Atleti o lavoro fisico pesante + allenamento |

**Fattore obiettivo**:
```
Mantenimento:    ×1.00
Dimagrimento:    ×0.80-0.85 (deficit 15-20%, LARN raccomanda max -500 kcal/die)
Massa:           ×1.10-1.15 (surplus 10-15%)
Ricomposizione:  ×0.95 (leggero deficit con proteine elevate)
```

Fonte deficit: LARN 2014 cap. 3.4 — "riduzione non superiore al 20-25% del fabbisogno stimato".

### Calcolo macronutrienti — fonte LARN 2014 cap. 4-7

**Proteine** — LARN 2014 tab. 4.1 PRI (Population Reference Intake):

| Popolazione | g/kg/die | Fonte LARN |
|-------------|----------|------------|
| Adulto sedentario | 0.90 | PRI tab. 4.1 |
| Adulto attivo (resistenza) | 1.20-1.40 | LARN cap. 4.3 |
| Adulto attivo (forza) | 1.40-1.80 | LARN cap. 4.3 + ISSN 2017 |
| Anziano >65 anni | 1.10-1.20 | LARN cap. 4.4 |
| Gravidanza (II trimestre) | +6 g/die | LARN tab. 4.1 |
| Gravidanza (III trimestre) | +11 g/die | LARN tab. 4.1 |
| Allattamento | +17 g/die | LARN tab. 4.1 |

Range LARN ammesso: 12-20% dell'energia totale (LARN cap. 4.2).
Per obiettivo dimagrimento: 1.6-2.2 g/kg (ISSN Position Stand 2017, Helms et al. 2014).

**Carboidrati** — LARN 2014 cap. 5:

| Parametro | Valore | Fonte |
|-----------|--------|-------|
| Range energia | 45-60% | LARN cap. 5.1 |
| Zuccheri semplici | <15% energia | LARN cap. 5.2 |
| Zuccheri liberi (aggiunti) | <10% energia | OMS 2015 |
| Fibra | ≥25 g/die (AI) | LARN tab. 5.1 |

**Grassi** — LARN 2014 cap. 6:

| Parametro | Valore | Fonte |
|-----------|--------|-------|
| Range energia | 20-35% | LARN cap. 6.1 |
| Saturi | <10% energia | LARN cap. 6.2 |
| Trans | <1% energia | OMS/EFSA |
| Omega-6 (LA) | 4-8% energia | LARN tab. 6.1 |
| Omega-3 (ALA) | 0.5-2% energia | LARN tab. 6.1 |
| EPA+DHA | 250 mg/die (AI) | LARN tab. 6.1 |

### Calcolo micronutrienti — fonte LARN 2014 cap. 8-16

Per ogni micronutriente, LARN definisce:
- **AR** (Average Requirement): fabbisogno medio della popolazione
- **PRI** (Population Reference Intake): copre il 97.5% della popolazione
- **AI** (Adequate Intake): usato quando AR/PRI non determinabili
- **UL** (Upper Level): limite massimo tollerabile

Il target del generatore usa il **PRI** (o AI se PRI non disponibile).

Tabelle complete in `larn_tables.py` (gia' implementato) per:
- 7 minerali: Ca, Fe, Zn, Mg, P, K, Se
- 10 vitamine: A, D, E, C, B1, B2, B3, B6, B9, B12

Valori stratificati per: sesso × fascia eta' (18-29, 30-59, 60-74, >75) × condizioni speciali.

---

## Modulo 2: Dynamic Pool Builder

### Problema v2
I FOOD_POOLS sono 71 nomi hardcoded su 957 alimenti nel DB. Il generatore usa il 7% del catalogo.

### Soluzione v3
Query dinamiche al DB per costruire i pool a runtime, basate su:
- `categoria_id` (mapping ruolo → categorie)
- `food_type` (ingrediente vs pietanza)
- `is_active = True`
- Esclusioni per intolleranze/preferenze del cliente

### Mapping ruolo → query DB

| Ruolo funzionale | Categorie DB | food_type | Filtro aggiuntivo |
|-----------------|-------------|-----------|-------------------|
| dairy | 12 (latticini) | ingrediente | nome LIKE '%yogurt%' OR '%latte%' |
| cereal | 1 (cereali), 3 (pane) | ingrediente | fiocchi, fette, gallette, pane |
| fruit | 6 (frutta fresca) | ingrediente | — |
| nuts | 7 (frutta secca) | ingrediente | — |
| primo_piatto | 16 (primi piatti) | pietanza | — |
| secondo_* | 17 (secondi piatti) | pietanza | filtro per tipo proteina |
| contorno | 20 (contorni), 5 (verdure) | misto | — |
| fat | 13 (oli) | ingrediente | nome LIKE '%olio%' |

### Esclusioni basate su profilo cliente

```
Se vegetariano:  escludi cat 8, 9, 10 (carne, salumi, pesce)
Se vegano:       escludi cat 8, 9, 10, 11, 12 (+ uova, latticini)
Se no lattosio:  escludi latticini con lattosio (mantieni yogurt, formaggi stagionati)
Se no glutine:   escludi cereali con glutine (mantieni riso, mais, grano saraceno, quinoa)
Se no frutta secca: escludi cat 7
```

### Varieta' garantita
Ogni pool deve avere almeno 5 alimenti. Se dopo le esclusioni un pool ha <5 elementi, il generatore emette un warning e rilassa i filtri.

---

## Modulo 3: Weekly Planner

### Scopo
Definire la struttura della settimana rispettando le frequenze CREA-Dir 2018.

### Frequenze settimanali — CREA 2018 Direttiva 9

| Gruppo alimentare | Frequenza settimanale | Fonte |
|-------------------|----------------------|-------|
| Cereali/pane/pasta | Ogni giorno (1-2 porzioni/pasto) | Dir. 1 |
| Frutta | 2-3 porzioni/die | Dir. 2 |
| Verdura | 2-3 porzioni/die | Dir. 2 |
| Latte e yogurt | 2-3 porzioni/die | Dir. 3 |
| Olio EVO | 2-4 porzioni/die | Dir. 4 |
| **Pesce** | **2-3 volte/settimana** | Dir. 9 |
| **Carne bianca** | **1-3 volte/settimana** | Dir. 9 |
| **Legumi** | **2-4 volte/settimana** | Dir. 9 |
| **Uova** | **2-4 volte/settimana** | Dir. 9 |
| **Carne rossa** | **max 1-2 volte/settimana** | Dir. 9 |
| **Affettati/salumi** | **max 1 volta/settimana** | Dir. 9 |
| Formaggi | 2-3 volte/settimana | Dir. 3 |
| Dolci | max 1-2 volte/settimana | Dir. 10 |

### Rotazione proteica v3

La rotazione proteica v2 era fissa (Lun=pollo, Mar=pesce...). v3 genera una rotazione randomizzata ma vincolata:

```
Vincoli CREA-Dir 9:
  pesce:          min 2, max 3
  carne_bianca:   min 1, max 3
  legumi:         min 2, max 4
  uova:           min 2, max 4
  carne_rossa:    min 0, max 2
  affettati:      min 0, max 1

  TOTALE = 7 cene

Algoritmo:
  1. Piazza i minimi obbligatori: 2 pesce + 1 bianca + 2 legumi + 2 uova = 9
     → eccede 7: riduci uova a 1, legumi a 1 → 2+1+1+1 = 5
  2. Riempi i 2 slot rimanenti randomizzando tra:
     carne_rossa (se <2), affettati (se <1), extra pesce/bianca/legumi/uova
  3. Shuffle l'ordine dei 7 giorni (non sempre Lun=pollo)
```

### Variazione struttura pasti

v2: ogni giorno ha la stessa struttura (5 pasti identici).
v3: 3 template giornalieri che si alternano:

| Template | Colazione | Sp. Matt. | Pranzo | Sp. Pom. | Cena |
|----------|-----------|-----------|--------|----------|------|
| **A — Standard** | Yogurt+cereali+frutta | Frutta | Primo+contorno | Yogurt+noci | Secondo+contorno+pane |
| **B — Colazione proteica** | Uova+pane+frutta | Noci | Primo+contorno | Frutta+yogurt | Secondo+contorno |
| **C — Pranzo leggero** | Yogurt+cereali+frutta | Frutta | Secondo+contorno | Pane+formaggio | Primo+contorno |

Distribuzione settimanale: 3×A + 2×B + 2×C (randomizzato).

---

## Modulo 4: Day Composer

### Scopo
Per ogni giorno, selezionare gli alimenti specifici dai pool dinamici.

### Vincoli di selezione
1. **No ripetizioni**: stesso alimento non puo' apparire 2 giorni consecutivi
2. **No ripetizioni intra-giorno**: stesso alimento non puo' apparire in 2 pasti dello stesso giorno
3. **Varieta' settimanale**: massimo 3 occorrenze dello stesso alimento nella settimana
4. **Diversita' cromatica** (verdure): variare colori (verde, rosso, arancio, bianco) — basato su categoria_nome

### Selezione alimenti
Per ogni slot del pasto:
1. Filtra il pool per il ruolo dello slot
2. Rimuovi alimenti gia' usati oggi e ieri
3. Se il pool e' troppo ristretto (<3 candidati), rilassa il vincolo "ieri"
4. Seleziona randomicamente con peso uniforme

---

## Modulo 5: Portion Optimizer

### Scopo
Aggiustare le porzioni per centrare i target nutrizionali del profilo.

### Miglioramenti v3

**v2 (attuale)**: 4 passaggi lineari (kcal → proteine → grassi → carb).
Problematico perche' ogni step altera il risultato del precedente.

**v3**: ottimizzazione iterativa multi-obiettivo.

```
Funzione obiettivo:
  minimize(
    w1 × |kcal_effettive - target_kcal|² +
    w2 × |prot_effettive - target_prot|² +
    w3 × |carb_effettive - target_carb|² +
    w4 × |fat_effettive  - target_fat|² +
    w5 × |fibra_effettiva - target_fibra|²
  )

  dove w1=1.0, w2=0.8, w3=0.5, w4=0.6, w5=0.3

Vincoli:
  Per ogni alimento: porzione_min ≤ grammi ≤ porzione_max (LARN)
  Totale kcal: ±10% del target
  Proteine: ≥ PRI (g/kg/die)
  Fibra: ≥ 25g
```

Algoritmo: gradient descent semplificato (3-5 iterazioni).
Non serve scipy — i vincoli sono lineari e il numero di variabili e' piccolo (~15-20 alimenti/giorno).

### Porzioni LARN — fonte SINU 2014

Le porzioni standard LARN (gia' in PORTION_LIMITS) definiscono il range ammissibile. L'optimizer puo' variare entro questi limiti ma non uscire.

---

## Modulo 6: LARN Validator

### Scopo
Validare il piano generato contro i riferimenti LARN e CREA.

### Score composito — 3 assi

```
Score finale = Macro(25%) + Micro(35%) + Frequenze(40%)
```

**Asse 1: Macro (25%)**
Per ogni macro (proteine, carb, grassi):
- 100 punti se nel range LARN
- Penalita' lineare per deviazione dal range
- Bonus per proteine ≥ PRI (g/kg)

**Asse 2: Micro (35%)**
Per ogni micronutriente (17 totali):
- 100 punti se ≥ PRI (o AI)
- Penalita' proporzionale al deficit (50% del PRI = 50 punti)
- Zero punti se <25% del PRI
- Nessun bonus per eccesso (eccetto ferro in donne fertili)

**Asse 3: Frequenze (40%)**
Per ogni gruppo alimentare (CREA-Dir 9):
- 100 punti se nel range di frequenza
- Penalita' per eccesso (es. carne rossa 3x = -30 punti)
- Penalita' per deficit (es. pesce 0x = -50 punti)

### Warning clinici

Il validator emette warning per:
- Ferro <80% PRI in donne fertili (Dir. 12)
- Calcio <80% PRI in donne >50 anni (Dir. 12)
- Vitamina D <50% AI in tutti (carenza endemica, Dir. 12)
- Fibra <20g/die (Dir. 5)
- Sodio >2000mg/die (Dir. 8 — attualmente non tracciato nei micro)
- Zuccheri semplici >15% energia (Dir. 10)

---

## Modulo 7: Output Formatter

### Output del generatore

```python
GeneratedPlan:
  pasti: list[GeneratedMeal]        # 35 pasti (7 giorni × 5 pasti)
  kcal_die_media: float             # media giornaliera effettiva
  score_larn: int                   # 0-100 composito
  macro_score: int                  # 0-100 solo macro
  micro_score: int                  # 0-100 solo micro
  frequency_score: int              # 0-100 solo frequenze
  warnings: list[str]              # warning clinici
  nutrient_breakdown: dict          # breakdown per nutriente vs target
  confidence: str                   # "high" | "medium" | "low"
```

### Report per il trainer

Il report mostra:
1. **Panoramica**: kcal, macro distribuzione, score LARN
2. **Nutrienti critici**: micro sotto il PRI con suggerimento alimentare
3. **Frequenze**: tabella gruppi alimentari vs target CREA
4. **Varieta'**: indice di diversita' alimentare (quanti alimenti diversi in 7 giorni)

---

## Differenze v2 → v3

| Aspetto | v2 (attuale) | v3 (target) |
|---------|-------------|-------------|
| Pool alimenti | 71 hardcoded | 957 dinamici da DB |
| Rotazione proteica | Fissa (stessa sequenza) | Randomizzata + vincolata CREA |
| Struttura giornata | Identica ogni giorno | 3 template alternati |
| Optimizer | 4 step lineari | Iterativo multi-obiettivo |
| Profilo cliente | Solo peso | Peso + attivita' + obiettivo + preferenze |
| Micro target | Generici | Personalizzati per sesso/eta' (LARN PRI) |
| Warning clinici | Nessuno | Ferro, calcio, vitamina D, fibra, sodio |
| Varieta' | Solo no-repeat ieri | No-repeat + max 3/settimana + diversita' colori |
| Esclusioni | Nessuna | Vegetariano, vegano, intolleranze, allergie |
| Score | 3 assi | 3 assi + breakdown dettagliato |

---

## Ordine di implementazione

| Fase | Modulo | Impatto | Complessita' |
|------|--------|---------|-------------|
| **1** | Dynamic Pool Builder | ALTO — sblocca 957 alimenti | Media |
| **2** | Weekly Planner (rotazione) | ALTO — varieta' cene | Bassa |
| **3** | Profile Resolver (BMR+PAL) | ALTO — target personalizzati | Bassa |
| **4** | Day Composer (varieta') | MEDIO — meno ripetizioni | Media |
| **5** | Portion Optimizer v2 | MEDIO — migliore aderenza macro | Media |
| **6** | LARN Validator (warning) | MEDIO — feedback clinico | Bassa |
| **7** | Esclusioni/preferenze | ALTO per UX — personalizzazione | Media |

### Fase 1 (impatto immediato): Dynamic Pool Builder
Risolvere il problema "71 su 957" e' il singolo cambiamento con il maggior impatto sulla varieta' dei piani generati. Dopo questa fase, ogni generazione produrra' un piano significativamente diverso.

---

## Riferimenti bibliografici

1. SINU (2014). LARN — Livelli di Assunzione di Riferimento di Nutrienti ed Energia per la Popolazione Italiana. IV Revisione. Coordinamento scientifico: SINU.

2. CREA (2019). Tabelle di Composizione degli Alimenti. IV Edizione. Centro di Ricerca Alimenti e Nutrizione.

3. CREA (2018). Linee Guida per una Sana Alimentazione. Dossier Scientifico. 13 Direttive.

4. Mifflin MD, St Jeor ST, et al. (1990). "A new predictive equation for resting energy expenditure in healthy individuals." Am J Clin Nutr 51:241-7.

5. EFSA (2017). "Dietary Reference Values for nutrients." EFSA Journal 15(11):e04991.

6. WHO (2015). "Guideline: Sugars intake for adults and children." WHO, Geneva.

7. ISSN (2017). "International society of sports nutrition position stand: diets and body composition." JISSN 14:16.

8. Helms ER, et al. (2014). "A systematic review of dietary protein during caloric restriction in resistance trained lean athletes." Int J Sport Nutr Exerc Metab 24:127-38.

9. USDA (2024). FoodData Central. U.S. Department of Agriculture. fdc.nal.usda.gov.

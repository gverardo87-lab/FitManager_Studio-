# SAFETY_ENGINE_CERTIFICATION.md — Safety Engine

> **Stato**: DRAFT | **Versione**: 1.0 | **Data**: 2026-04-19
> **Copertura**: ~350 LOC (`condition_rules.py`) + ~300 LOC (`safety_engine.py`) = ~650 LOC
> **Funzione**: Mappa condizioni anamnestiche → restrizioni per esercizio (avoid/modify/caution)

---

## 1. Architettura

### 1.1 Pipeline 4-Query Dual-Session

```
┌──────────────┐     ┌──────────────────────────┐     ┌──────────────────┐
│ crm.db       │     │ SAFETY ENGINE            │     │ catalog.db       │
│              │     │                          │     │                  │
│ Q1: Client   │────>│ extract_client_conditions │     │ Q2: Conditions   │
│    bouncer   │     │ extract_medication_flags  │────>│ Q3: Exercise IDs │
│              │     │ build_safety_map          │     │ Q4: ExConditions │
│              │     │                          │     │                  │
│ (ownership)  │     │ Aggregation:             │     │ (500 esercizi    │
│              │     │ worst-case severity      │     │  47 condizioni   │
│              │     │ per exercise             │     │  ExerciseCondition│
└──────────────┘     └──────────────────────────┘     │  mappings)       │
                                                       └──────────────────┘
```

**Dual-session critica**: Q1 usa `session` (crm.db), Q2-Q4 usano `catalog_session` (catalog.db). Violazione = 500 error runtime. Incidente documentato: INC-2026-03-28.

### 1.2 Flusso Dettagliato

1. **Bouncer** (crm.db): verifica client ownership (`trainer_id`), soft-delete (`deleted_at`)
2. **Extract conditions**: analisi testo anamnesi → set di `condition_id`
   - Livello 1: flag strutturali booleani (2 flag → 3 condition_id)
   - Livello 2: keyword matching su 80 regole (testo normalizzato, case/accent-insensitive)
3. **Early return**: se zero condizioni → safety map vuota (con medication_flags)
4. **Query condizioni** (catalog.db): nomi condizioni per ID
5. **Query esercizi attivi** (catalog.db): 500 esercizi con `in_subset=True`
6. **Query mappings** (catalog.db): `ExerciseCondition` JOIN `MedicalCondition`
7. **Aggregazione**: per ogni esercizio, worst-case severity (`avoid > modify > caution`)

### 1.3 Text Normalization

Normalizzazione accenti italiani per keyword matching robusto:
- 10 caratteri gestiti: `a e e i o u` accentati (gravi e acuti)
- Preserva apostrofi di elisione (`l'ernia` → invariato)
- Rimuove apostrofi finali dopo vocale (`instabilita'` → `instabilita`)
- Case-insensitive
- Substring matching: `keyword in testo_normalizzato`

---

## 2. Tabella 47 Condizioni

### 2.1 Condizioni Specifiche (ID 1-30)

| ID | Condizione | Categoria Anatomica | Severity tipica |
|----|-----------|-------------------|-----------------|
| 1 | Ernia/Problemi lombari | Schiena | modify/avoid |
| 2 | Ernia cervicale | Cervicale | modify/avoid |
| 3 | Scoliosi | Schiena | caution/modify |
| 4 | Stenosi spinale | Schiena | modify/avoid |
| 5 | Spondilolistesi | Schiena | modify/avoid |
| 6 | Impingement spalla (subacromiale) | Spalla | modify |
| 7 | Cuffia dei rotatori | Spalla | modify/avoid |
| 8 | Instabilita scapolare/gleno-omerale | Spalla | modify |
| 9 | Spalla congelata (capsulite adesiva) | Spalla | avoid |
| 10 | Lesione LCA | Ginocchio | modify/avoid |
| 11 | Lesione menisco | Ginocchio | modify |
| 12 | Sindrome femoro-rotulea | Ginocchio | modify |
| 13 | Artrosi ginocchio grave (gonartrosi) | Ginocchio | modify/avoid |
| 14 | Artrosi anca (coxartrosi) | Anca | modify |
| 15 | Conflitto femoro-acetabolare (FAA) | Anca | modify |
| 16 | Epicondilite (gomito del tennista) | Gomito | caution/modify |
| 17 | Tunnel carpale | Polso | caution/modify |
| 18 | Fascite plantare | Caviglia/Piede | caution |
| 19 | Instabilita caviglia | Caviglia/Piede | caution/modify |
| 20 | Ipertensione arteriosa | Cardiovascolare | caution |
| 21 | Cardiopatia | Cardiovascolare | caution/modify |
| 22 | Insufficienza cardiaca (scompenso) | Cardiovascolare | modify/avoid |
| 23 | Diabete | Metabolico | caution |
| 24 | Osteoporosi | Metabolico | modify |
| 25 | Obesita | Metabolico | caution/modify |
| 26 | Sciatica (radicolopatia) | Neurologico | modify |
| 27 | Sindrome del piriforme | Neurologico | caution/modify |
| 28 | Asma da sforzo | Respiratorio | caution |
| 29 | Gravidanza | Speciale | modify/avoid |
| 30 | Diastasi dei retti | Speciale | modify |

### 2.2 Condizioni Post-Traumatiche Generiche (ID 31-39)

| ID | Condizione | Categoria |
|----|-----------|-----------|
| 31 | Frattura/intervento polso | Post-trauma polso |
| 32 | Frattura/intervento ginocchio | Post-trauma ginocchio |
| 33 | Frattura/intervento spalla | Post-trauma spalla |
| 34 | Frattura/intervento caviglia/piede | Post-trauma caviglia |
| 35 | Frattura/intervento anca/femore | Post-trauma anca |
| 36 | Frattura/intervento colonna + spondilite anchilosante | Post-trauma colonna |
| 37 | Frattura/intervento gomito | Post-trauma gomito |
| 38 | Cervicalgia (generica) | Sintomatologica |
| 39 | Lombalgia (generica) | Sintomatologica |

### 2.3 Condizioni Aggiuntive (ID 40-47)

| ID | Condizione | Categoria |
|----|-----------|-----------|
| 40 | Fibromialgia | Reumatologica |
| 41 | Ipermobilita / Ehlers-Danlos | Ortopedica |
| 42 | Ipotiroidismo | Metabolica |
| 43 | BPCO / Broncopneumopatia | Respiratoria |
| 44 | Diabete tipo 1 (insulinodipendente) | Metabolica |
| 45 | Neuropatia periferica | Neurologica |
| 46 | Artrosi spalla (gleno-omerale) | Ortopedica |
| 47 | Artrosi mani / polso / rizoartrosi | Ortopedica |

---

## 3. Tabella 80 Keyword Rules

### 3.1 Regole per Categoria (tutte da `condition_rules.py` ANAMNESI_KEYWORD_RULES)

**Schiena/Lombare** (righe 32-37):

| Keywords | Condition ID | Confidenza |
|----------|-------------|------------|
| ernia, ernie, hernia discale | 1 | ALTA |
| lombare | 1 | ALTA |
| scoliosi | 3 | ALTA |
| stenosi spinale | 4 | ALTA |
| spondilolistesi | 5 | ALTA |

**Cervicale** (righe 39-40):

| Keywords | Condition ID | Confidenza |
|----------|-------------|------------|
| ernia cervicale, ernia del disco cervicale, cervicobrachialgia | 2 | ALTA |

**Spalla** (righe 42-46):

| Keywords | Condition ID | Confidenza |
|----------|-------------|------------|
| subacromiale, impingement spalla | 6 | ALTA |
| cuffia dei rotatori, cuffia rotatori | 7 | ALTA |
| instabilita scapolare, instabilita gleno | 8 | ALTA |
| spalla congelata, capsulite | 9 | ALTA |

**Ginocchio** (righe 48-53):

| Keywords | Condition ID | Confidenza |
|----------|-------------|------------|
| crociato, lca | 10 | ALTA |
| menisco | 11 | ALTA |
| femoro-rotulea, rotula, sindrome femoro | 12 | ALTA |
| artrosi ginocchio, artrosi grave del ginocchio, gonartrosi | 13 | ALTA |

**Anca** (righe 55-58):

| Keywords | Condition ID | Confidenza |
|----------|-------------|------------|
| artrosi anca, coxartrosi, artrosi severa dell'anca | 14 | ALTA |
| conflitto femoro-acetabolare, impingement anca | 15 | ALTA |

**Gomito** (riga 61):

| Keywords | Condition ID | Confidenza |
|----------|-------------|------------|
| epicondilite, gomito del tennista | 16 | ALTA |

**Polso** (riga 64):

| Keywords | Condition ID | Confidenza |
|----------|-------------|------------|
| tunnel carpale | 17 | ALTA |

**Caviglia/Piede** (righe 67-69):

| Keywords | Condition ID | Confidenza |
|----------|-------------|------------|
| fascite plantare, plantare | 18 | ALTA |
| instabilita caviglia, distorsione caviglia, caviglia instabile, lassita caviglia | 19 | ALTA |

**Cardiovascolare** (righe 71-78):

| Keywords | Condition ID | Confidenza |
|----------|-------------|------------|
| ipertensione, pressione sanguigna, pressione alta, ipertensione arteriosa | 20 | ALTA |
| cardiopatia, cardiaci gravi, cardiovascol | 21 | ALTA |
| problemi cardiaci | 20 | MEDIA |
| insufficienza cardiaca, scompenso cardiaco, scompenso | 22 | ALTA |

**Metabolico** (righe 80-83):

| Keywords | Condition ID | Confidenza |
|----------|-------------|------------|
| osteoporosi | 24 | ALTA |
| diabete, diabetico, glicemia alta | 23 | ALTA |
| obeso, obesit | 25 | ALTA |

**Neurologico** (righe 85-87):

| Keywords | Condition ID | Confidenza |
|----------|-------------|------------|
| sciatica, radicolopatia, nervo sciatico | 26 | ALTA |
| piriforme | 27 | ALTA |

**Respiratorio** (riga 90):

| Keywords | Condition ID | Confidenza |
|----------|-------------|------------|
| asma, respiratori | 28 | ALTA |

**Speciale** (righe 92-94):

| Keywords | Condition ID | Confidenza |
|----------|-------------|------------|
| gravidanza | 29 | ALTA |
| diastasi | 30 | ALTA |

**Aggiuntive** (righe 100-116):

| Keywords | Condition ID | Confidenza |
|----------|-------------|------------|
| fibromialgia, fibromialgica | 40 | ALTA |
| ipermobilita, ehlers, iper-lassita, lassita articolare | 41 | ALTA |
| artrosi spalla, artrosi gleno-omerale | 46 | ALTA |
| artrosi mani, artrosi polso, rizoartrosi | 47 | ALTA |
| ipotiroidismo, tiroide, levotiroxina, eutirox | 42 | ALTA |
| diabete tipo 1, diabete insulinodipendente | 44 | ALTA |
| bpco, broncopneumopatia, enfisema, bronchite cronica | 43 | ALTA |
| neuropatia, formicolio piedi, perdita sensibilita | 45 | ALTA |

### 3.2 Regole Post-Traumatiche Generiche (righe 119-161)

Queste regole catturano condizioni generiche (es. "operato al polso") con keyword specifiche e poi fallback generico:

| Keywords specifici | Keywords generici | Condition ID |
|-------------------|------------------|-------------|
| frattura polso, frattura radio, intervento polso, operato polso | polso, avambraccio | 31 |
| frattura ginocchio, intervento ginocchio, artroscopia ginocchio | ginocchio, ginocchia | 32 |
| frattura spalla, frattura clavicola, lussazione spalla, intervento spalla | spalla, spalle | 33 |
| frattura caviglia, frattura piede, intervento caviglia | caviglia, caviglie, achille, piede | 34 |
| frattura femore, protesi anca, intervento anca | anca, anche | 35 |
| frattura vertebrale, intervento colonna, operato schiena | — | 36 |
| frattura gomito, intervento gomito | gomito | 37 |
| spondilite, anchilosante, morbo di bechterew | — | 36 |

### 3.3 Regole Sintomatologiche (righe 163-177)

| Keywords | Condition ID |
|----------|-------------|
| cervicalgia, cervical, collo, dolore cervicale, rigidita cervicale | 38 |
| lombalgia, mal di schiena, dolore lombare, rigidita lombare, dolore alla schiena, problemi di schiena, schiena bloccata | 39 |

---

## 4. Flag Strutturali Anamnesi

**Fonte codice**: `condition_rules.py` righe 185-188

Oltre al keyword matching, 2 campi booleani dell'anamnesi mappano direttamente a condizioni:

| Campo Booleano | Condizioni Attivate | Logica |
|---------------|--------------------|---------|
| `problemi_cardiovascolari.presente = true` | [20, 21] (ipertensione + cardiopatia) | OR con keyword matching |
| `problemi_respiratori.presente = true` | [28] (asma) | OR con keyword matching |

**Razionale**: questi campi sono checkbox nell'anamnesi. Il trainer puo' segnalare il problema senza scrivere dettagli nel testo libero. I flag strutturali garantiscono che la condizione venga rilevata anche senza keyword.

---

## 5. Regole Farmacologiche

**Fonte codice**: `condition_rules.py` righe 198-222

5 classi di farmaci con nota clinica per il trainer:

| Flag | Keywords Farmaco | Nota Clinica | Impatto sull'Allenamento |
|------|-----------------|-------------|-------------------------|
| `beta_blocker` | betabloccante, atenololo, bisoprololo, metoprololo, propranololo, carvedilolo, nebivololo | FC a riposo non affidabile per monitorare intensita'. Usare RPE. | Monitoraggio intensita |
| `anticoagulant` | anticoagulante, warfarin, coumadin, eparina, eliquis, xarelto, pradaxa | Rischio emorragico aumentato. Evitare esercizi ad alto rischio caduta. | Selezione esercizi |
| `corticosteroid` | cortisone, prednisone, desametasone, betametasone, metilprednisolone | Uso prolungato indebolisce tendini. Cautela con carichi pesanti. | Carico massimo |
| `insulin` | insulina, novorapid, lantus, humalog, toujeo, fiasp, levemir | Rischio ipoglicemia durante esercizio. Zuccheri rapidi a portata. | Protocollo sessione |
| `statin` | statina, atorvastatina, rosuvastatina, simvastatina | Possibile mialgia da statine. Monitorare dolore muscolare post-esercizio. | Monitoraggio sintomi |

**Nota**: i farmaci generano **flag informativi** per il trainer, non restrizioni automatiche sugli esercizi. Il trainer decide come adattare la programmazione.

---

## 6. Zone di Incertezza

### 6.1 Keyword Generiche — Rischio Falsi Positivi

Alcune keyword sono molto generiche e possono generare falsi positivi:
- `"polso"` → condition 31 (post-trauma polso). Ma "polso" puo' comparire in contesti non patologici.
- `"ginocchio"` → condition 32. Stessa problematica.
- `"spalla"`, `"anca"`, `"gomito"`, `"caviglia"` → conditions 33-37.
- `"collo"` → condition 38 (cervicalgia). Potrebbe essere in contesto diverso.
- `"respiratori"` → condition 28. Troppo generico.

**Mitigazione attuale**: queste keyword generiche sono usate come fallback DOPO le keyword specifiche (es. "frattura polso" viene matchata prima di "polso"). Ma il substring matching (`kw in text`) puo' comunque generare falsi positivi in frasi complesse.

**Validazione necessaria**: testare su un corpus di 50+ anamnesi reali per misurare precision/recall.

### 6.2 Condizioni Mancanti

Condizioni non coperte dal sistema attuale:
- **Aritmie** (non solo ipertensione/cardiopatia)
- **Sindrome metabolica** (combinazione diabete + ipertensione + obesita)
- **Depressione/ansia** (impatto su aderenza, non su selezione esercizi)
- **Allergie a materiali** (lattice guanti, nichel attrezzature)
- **Interventi chirurgici recenti** (timeline post-operatoria)
- **Protesi articolari** (diverse restrizioni da frattura)

### 6.3 Copertura Farmaci

5 classi coperte su molte esistenti. Classi non coperte con impatto sull'allenamento:
- **Diuretici** (rischio disidratazione)
- **Ansiolitici/sedativi** (rischio coordinazione)
- **Immunosoppressori** (rischio infezione in palestra)
- **Terapia ormonale sostitutiva** (impatto su recupero)

### 6.4 Severity Mapping

Le severity (avoid/modify/caution) per ogni coppia condizione-esercizio vivono in `ExerciseCondition` nel catalog.db. Sono state definite manualmente per 500 esercizi x condizioni rilevanti. Questa mappatura necessita:
- Revisione da fisioterapista/medico sportivo
- Aggiornamento quando nuovi esercizi vengono aggiunti al catalogo
- Validazione per condizioni rare (es. Ehlers-Danlos, fibromialgia)

---

## 7. Riferimenti Clinici

1. **NSCA 2016**: Haff, G.G. & Triplett, N.T. *Essentials of Strength Training and Conditioning* (4th ed.) — Linee guida esercizio per popolazioni speciali.
2. **ACSM 2022**: *ACSM's Guidelines for Exercise Testing and Prescription* (11th ed.) — Controindicazioni assolute/relative all'esercizio.
3. **ACSM Special Populations**: Raccomandazioni per ipertensione, diabete, osteoporosi, gravidanza, cardiopatia.
4. **ACL Prevention Guidelines**: Alentorn-Geli 2009 — Prevenzione ACL, rapporti di forza.
5. **Sahrmann 2002**: *Diagnosis and Treatment of Movement Impairment Syndromes* — Sindromi incrociate, squilibri.
6. **ESC 2020**: European Society of Cardiology — Raccomandazioni attivita fisica per pazienti cardiovascolari.
7. **WCRF 2018**: World Cancer Research Fund — Raccomandazioni dietetiche e attivita fisica per prevenzione oncologica.

---

## 8. Changelog

| Data | Versione | Modifica |
|------|----------|---------|
| 2026-04-19 | 1.0 | Prima stesura — 47 condizioni, 80 keyword rules, 5 farmaci, pipeline dual-session |

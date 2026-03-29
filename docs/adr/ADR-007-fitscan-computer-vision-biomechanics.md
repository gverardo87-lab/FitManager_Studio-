# ADR-007 — FitScan: Computer Vision per Analisi Corporea e Biomeccanica

- Date: 2026-03-25
- Status: accepted
- Deciders: gvera
- Related: ADR-006 (FitManager Box), POST_LAUNCH_ROADMAP_90D, FITSCAN_ARCHITECTURE.md

## Context

FitManager possiede gia' motori scientifici unici nel mercato:
- **Training Science Engine** (~3500 LOC): periodizzazione, matrice EMG 18×15, volume MEV/MAV/MRV, Demand Vector 10D
- **Safety Engine**: 47 condizioni mediche, 80 pattern rules, mapping esercizio-condizione
- **Client Avatar**: 6 dimensioni, readiness_score, clinical freshness

Ma il sistema di **misurazioni corporee** (ClientMeasurement → MeasurementValue, 22 metriche) e' sottoutilizzato perche' richiede input manuale. La prima utilizzatrice reale non inserisce misurazioni → il monitoraggio scientifico resta vuoto → i motori non possono calcolare progressione.

Parallelamente, nessun competitor offre **analisi biomeccanica degli esercizi** in tempo reale. I trainer valutano la forma a occhio, senza dati oggettivi, senza storico, senza correlazione con le condizioni del cliente.

L'evoluzione hardware verso FitManager Box (ADR-006, Raspberry Pi 5) apre la possibilita' di integrare computer vision direttamente nel sistema.

### Background tecnico

Il fondatore ha competenza diretta in architetture YOLO/CV per edge inference, maturata in contesto industriale (sistemi YOLO+OCR su impianti industriali e terminal container). La pipeline edge AI (train → export ONNX → quantize → deploy su NPU) e' una competenza acquisita, non sperimentale.

## Decision Drivers

1. **Eliminare la frizione dell'input manuale**: se il sistema misura automaticamente, il monitoraggio si popola da solo.
2. **Sfruttare l'hardware gia' presente**: la FitManager Box (Pi 5) o il telefono del trainer hanno gia' camera e compute.
3. **Collegare CV ai motori scientifici esistenti**: nessun competitor puo' farlo perche' nessuno ha i motori.
4. **Costruire un moat competitivo inattaccabile**: pose estimation e' commodity, l'analisi biomeccanica integrata con Safety Engine + Training Science no.
5. **Onorare una visione familiare**: l'analisi biomeccanica degli esercizi tramite CV e' un progetto concepito con il fondatore del know-how AI della famiglia.

## Considered Options

### Option A — Solo modello custom (fine-tuned da zero)

- Pro: massima precisione su keypoints fitness-specifici
- Contro: richiede dataset annotato (migliaia di video), mesi di training, rischio overfitting. Non realistico per il prototipo.

### Option B — Solo browser commodity (MediaPipe / MoveNet)

- Pro: zero setup, funziona ovunque, 33 keypoints 3D sufficienti per la maggior parte delle metriche
- Contro: nessun tracking attrezzi (bilanciere, manubri), nessun keypoint scapolare/spinale, qualita' variabile per dispositivo

### Option C — Architettura a strati: commodity + engine proprietario (scelta)

- Pro: usa pose estimation commodity come input, investe il lavoro nell'**analisi proprietaria** che nessun competitor puo' replicare. Il modello di pose si puo' sostituire/migliorare senza riscrivere l'engine. Funziona sia in browser (telefono) che su NPU (Box Pro).
- Contro: complessita' architetturale su due livelli. Gestibile con separazione pulita.

## Decision

**Option C — Architettura a strati**.

Il modello di pose estimation e' il **telescopio**: commodity, sostituibile. Il Biomechanical Analysis Engine e' l'**astronomo**: proprietario, costruito sui motori scientifici esistenti, non replicabile.

### Principio architetturale

```
LAYER 1 — Pose Provider (commodity, sostituibile)
  Browser: MediaPipe Pose Landmarker (33 keypoints 3D)
  Box Pro: YOLOv8s-pose su Hailo-8L NPU (17 keypoints, 30 FPS)
  Futuro: modello custom fine-tuned (keypoints aggiuntivi)

  Output standard: PoseFrame { keypoints: [{x, y, z, confidence}], timestamp }

LAYER 2 — Biomechanical Analysis Engine (proprietario)
  Input: PoseFrame[] + contesto FitManager (esercizio, condizioni, protocollo)
  Output: BodyScanResult | ExerciseFormResult

  Sub-engines:
    a) Body Ratio Calculator (rapporti corporei, simmetria, postura)
    b) Exercise Form Analyzer (angoli articolari, ROM, deviazioni per esercizio)
    c) Movement Screener (test standardizzati, scoring automatico)
    d) Safety Cross-Reference (alert basati su condizioni + dati CV)
```

### 3 livelli funzionali (delivery incrementale)

| Livello | Nome | Descrizione | Dipendenza |
|---|---|---|---|
| L1 | **Body Scan** | Foto statica → rapporti corporei → tracking nel tempo | Solo Pose Provider |
| L2 | **Exercise Form Analysis** | Video live → analisi biomeccanica per esercizio → feedback RT | Pose Provider + catalog.db (500 esercizi con biomeccanica) + Safety Engine |
| L3 | **Movement Screening** | Test codificati → scoring automatico → input per Smart Programming | Pose Provider + Clinical Analysis + regole FMS/SFMA |

### Integrazione con motori esistenti

| Motore FitManager | Come FitScan lo alimenta | Come il motore alimenta FitScan |
|---|---|---|
| **ClientMeasurement** | Body Scan scrive automaticamente MeasurementValue (circonferenze relative, simmetria, postura) | Metriche storiche mostrano progressione |
| **Client Avatar** | Scan aggiorna measurement freshness → readiness_score migliora | Avatar fornisce condizioni + medications per contesto analisi |
| **Safety Engine** | Posture alerts suggeriscono revisione anamnesi (non auto-assign condizioni) | Condizioni cliente modificano soglie di allerta nel form analysis |
| **Training Science** | Dati asimmetria corpo → possono pesare l'exercise ranking | Pattern/muscoli/EMG definiscono come analizzare ciascun esercizio |
| **Demand Vector 10D** | Metriche ROM individuali → ceiling personalizzato per skill/stability | Demand vector definisce quali dimensioni monitorare per esercizio |
| **Smart Programming** | Movement screening → scoring diretto per il matching | Scoring 14D consuma risultati FitScan come input |

### Vincoli architetturali

1. **catalog.db resta read-only**: nessun dato FitScan nelle tabelle catalogo. Tutto va in crm.db.
2. **Safety Engine resta deterministico**: FitScan NON assegna condizioni automaticamente. Suggerisce revisione.
3. **Pose Provider e' un'interfaccia, non un'implementazione**: il Biomechanical Engine consuma `PoseFrame[]`, non sa se vengono da MediaPipe, YOLO, o un modello custom.
4. **Dati grezzi sempre salvati**: keypoints raw persistiti per ricalcolo futuro con engine migliorato.
5. **Privacy**: frame video processati in locale, mai trasmessi. Solo keypoints (coordinate numeriche) e metriche calcolate persistiti.

## Consequences

### Positive

1. Il monitoraggio scientifico si popola **automaticamente** — risolve il problema #1 della prima utilizzatrice
2. L'analisi biomeccanica degli esercizi e' un differenziale che nessun competitor puo' replicare (richiede Safety Engine + Training Science + catalog 500 esercizi)
3. L'architettura a strati permette di migliorare il Pose Provider nel tempo senza riscrivere l'Engine
4. Privacy intatta: tutto in locale, nessun video/immagine trasmesso
5. Il prototipo funziona in browser (zero hardware extra), la produzione scala su NPU (Box Pro)

### Negative

1. Complessita' significativa (nuovo engine, nuove tabelle, nuovo layer frontend)
2. MediaPipe 33 keypoints non coprono: scapole, segmenti spinali, pianta del piede
3. Precisione tracking relativo dipende da consistenza della posa e della distanza camera
4. Richiede educazione del trainer ("posizionati qui", "girati cosi'")

### Follow-up actions

1. Documentazione tecnica completa: `docs/product/FITSCAN_ARCHITECTURE.md`
2. DB schema: tabelle `body_scans`, `body_scan_metrics`, `exercise_form_sessions`
3. Prototipo L1 (Body Scan) come primo deliverable
4. Aggiornamento roadmap con Phase 4 FitScan
5. Aggiornamento MANIFESTO.md con visione AI/CV

## Rollback / Exit Strategy

FitScan e' un modulo aggiuntivo, non modifica i motori esistenti. Se la qualita' CV non soddisfa:
- I motori scientifici continuano a funzionare con input manuale
- Le tabelle FitScan restano in crm.db ma inutilizzate
- Il codebase del Biomechanical Engine e' isolato in `api/services/fitscan/`
- Nessun impatto sul CRM core

## Supersedes / Superseded By

- Supersedes: nessuno
- Superseded by: eventuale ADR futura per modello CV custom fine-tuned

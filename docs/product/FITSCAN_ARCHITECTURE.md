# FitScan — Architettura Tecnica

> Data: 2026-03-25
> ADR: ADR-010
> Stato: specifica tecnica approvata, pre-implementazione

---

## 1. Visione

FitScan trasforma la camera (telefono, tablet, PiCam) nello strumento di misura del professionista fitness. Tre livelli funzionali, delivery incrementale:

```
L1  BODY SCAN         Foto statica → rapporti corporei → tracking nel tempo
L2  FORM ANALYSIS     Video live  → biomeccanica per esercizio → feedback real-time
L3  MOVEMENT SCREEN   Test codificati → scoring automatico → input per programmazione
```

Ogni livello consuma dati dal precedente e dai motori scientifici esistenti.

---

## 2. Architettura a Strati

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │ ScanCapture     │  │ FormAnalysis    │  │ ScreeningFlow  │  │
│  │ (3 pose guide)  │  │ (live overlay)  │  │ (test wizard)  │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬───────┘  │
│           │                    │                     │          │
│  ┌────────v────────────────────v─────────────────────v───────┐  │
│  │              Pose Provider (browser)                      │  │
│  │  MediaPipe Pose Landmarker — 33 keypoints 3D             │  │
│  │  Output: PoseFrame { keypoints[], timestamp, confidence } │  │
│  └────────────────────────────┬──────────────────────────────┘  │
└───────────────────────────────┼──────────────────────────────────┘
                                │ PoseFrame[] + context
                                v
┌───────────────────────────────────────────────────────────────────┐
│                        BACKEND (FastAPI)                          │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              Biomechanical Analysis Engine                  │  │
│  │              api/services/fitscan/                          │  │
│  │                                                             │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │  │
│  │  │ Body Ratio   │  │ Form         │  │ Movement         │  │  │
│  │  │ Calculator   │  │ Analyzer     │  │ Screener         │  │  │
│  │  │ (L1)         │  │ (L2)         │  │ (L3)             │  │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────────┘  │  │
│  │         │                 │                  │              │  │
│  │  ┌──────v─────────────────v──────────────────v───────────┐  │  │
│  │  │           Safety Cross-Reference                      │  │  │
│  │  │  condizioni cliente → soglie modificate               │  │  │
│  │  │  alert posturali → suggerimento revisione anamnesi    │  │  │
│  │  └───────────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                              │                                    │
│  ┌───────────────────────────v────────────────────────────────┐   │
│  │  crm.db — body_scans, body_scan_metrics,                  │   │
│  │           exercise_form_sessions, exercise_form_reps       │   │
│  │           + bridge → client_measurements (metriche std)    │   │
│  └────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
```

### Pose Provider Interface

Il Biomechanical Engine NON dipende da un'implementazione specifica. Consuma un formato standard:

```python
class PoseKeypoint(BaseModel):
    """Singolo keypoint del corpo."""
    name: str                    # es. "left_shoulder", "right_knee"
    x: float                     # coordinata normalizzata [0, 1]
    y: float                     # coordinata normalizzata [0, 1]
    z: float                     # profondita' relativa (MediaPipe) o 0.0
    confidence: float            # [0, 1]

class PoseFrame(BaseModel):
    """Un frame di pose estimation."""
    keypoints: list[PoseKeypoint]  # 17 (YOLO) o 33 (MediaPipe)
    timestamp_ms: int              # millisecondi dall'inizio cattura
    source: str                    # "mediapipe_browser" | "yolov8_hailo" | "mediapipe_python"
    image_width: int               # dimensioni frame originale
    image_height: int

class PoseSequence(BaseModel):
    """Sequenza temporale di frame (per L2 e L3)."""
    frames: list[PoseFrame]
    duration_ms: int
    fps: float
```

Qualsiasi Pose Provider che produce `PoseFrame` e' compatibile. Oggi: MediaPipe JS nel browser. Domani: YOLOv8 su Hailo, modello custom, qualsiasi cosa.

---

## 3. Database Schema (crm.db)

Tutte le tabelle FitScan vanno in **crm.db** (business, tenant-isolated). catalog.db resta read-only.

### 3.1 body_scans — Sessione di scansione corporea (L1)

```python
class BodyScan(SQLModel, table=True):
    __tablename__ = "body_scans"

    id: int | None = Field(default=None, primary_key=True)
    id_cliente: int = Field(foreign_key="clienti.id", index=True)
    trainer_id: int = Field(foreign_key="trainers.id", index=True)
    scan_date: datetime
    scan_type: str                 # "static_3pose" | "quick_front"
    pose_provider: str             # "mediapipe_browser" | "yolov8_hailo"
    pose_provider_version: str     # "0.10.14"

    # Dati grezzi (sempre salvati per ricalcolo futuro)
    keypoints_front: str | None    # JSON: PoseFrame (frontale)
    keypoints_side_r: str | None   # JSON: PoseFrame (laterale destro)
    keypoints_side_l: str | None   # JSON: PoseFrame (laterale sinistro)

    # Foto riferimento (path relativo in data/scans/)
    photo_front: str | None
    photo_side_r: str | None
    photo_side_l: str | None

    # Metadati cattura
    camera_distance_cm: int | None  # distanza stimata camera-soggetto
    subject_height_cm: float | None # altezza dichiarata (per normalizzazione)

    note: str | None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = None
```

### 3.2 body_scan_metrics — Metriche calcolate (L1)

```python
class BodyScanMetric(SQLModel, table=True):
    __tablename__ = "body_scan_metrics"

    id: int | None = Field(default=None, primary_key=True)
    id_scan: int = Field(foreign_key="body_scans.id", index=True)
    metric_name: str               # es. "shoulder_hip_ratio", "pelvic_tilt_deg"
    metric_category: str           # "ratio" | "angle" | "symmetry" | "composite"
    value: float                   # valore calcolato
    unit: str                      # "ratio" | "degrees" | "percent" | "score"
    confidence: float              # [0, 1] basato su confidence dei keypoints usati
    source_pose: str               # "front" | "side_r" | "side_l" | "composite"
```

### 3.3 exercise_form_sessions — Sessione di analisi esercizio (L2)

```python
class ExerciseFormSession(SQLModel, table=True):
    __tablename__ = "exercise_form_sessions"

    id: int | None = Field(default=None, primary_key=True)
    id_cliente: int = Field(foreign_key="clienti.id", index=True)
    trainer_id: int = Field(foreign_key="trainers.id", index=True)
    id_esercizio: int              # cross-DB ref a catalog.db Exercise.id
    session_date: datetime
    pose_provider: str
    pose_provider_version: str

    # Serie analizzata
    total_reps: int
    avg_form_score: float          # 0-100 media tra le rep
    min_form_score: float          # peggior rep
    max_form_score: float          # miglior rep

    # Keypoints grezzi (intera sequenza compressa)
    keypoints_sequence: str | None  # JSON compresso: PoseFrame[] (opzionale, pesante)
    duration_ms: int
    fps: float

    # Alert aggregati
    alerts_json: str | None        # JSON: [{type, message, severity, count}]

    note: str | None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = None
```

### 3.4 exercise_form_reps — Analisi per singola rep (L2)

```python
class ExerciseFormRep(SQLModel, table=True):
    __tablename__ = "exercise_form_reps"

    id: int | None = Field(default=None, primary_key=True)
    id_session: int = Field(foreign_key="exercise_form_sessions.id", index=True)
    rep_number: int                # 1-based

    # Timing
    start_ms: int                  # inizio rep nella sequenza
    end_ms: int                    # fine rep
    concentric_ms: int             # durata concentrica
    eccentric_ms: int              # durata eccentrica
    pause_ms: int                  # pausa in bottom/top position

    # Metriche biomeccaniche (dipendono dall'esercizio)
    metrics_json: str              # JSON: {metric_name: value} — esercizio-specifico
    form_score: float              # 0-100 per questa rep
    alerts_json: str | None        # JSON: [{type, message, severity}]
```

### Relazione con tabelle esistenti

```
                    crm.db
┌──────────────┐    ┌───────────────────┐    ┌──────────────────────┐
│ clienti      │◄───│ body_scans        │───►│ body_scan_metrics    │
│              │    │ (L1)              │    │ (metriche calcolate) │
│              │    └───────────────────┘    └──────────────────────┘
│              │
│              │    ┌───────────────────┐    ┌──────────────────────┐
│              │◄───│ exercise_form_    │───►│ exercise_form_reps   │
│              │    │ sessions (L2)     │    │ (per-rep analysis)   │
│              │    └───────────────────┘    └──────────────────────┘
│              │
│              │    ┌───────────────────┐    ┌──────────────────────┐
│              │◄───│ client_           │───►│ measurement_values   │
│              │    │ measurements      │    │ (22 metriche std)    │
│              │    │ (esistente)       │    │ (esistente)          │
└──────────────┘    └───────────────────┘    └──────────────────────┘

Bridge: quando un BodyScan produce metriche mappabili alle 22 metriche standard
(es. simmetria, angoli posturali), il sistema PUO' creare automaticamente un
ClientMeasurement + MeasurementValues corrispondenti → il monitoraggio esistente
si popola senza input manuale.
```

---

## 4. Biomechanical Analysis Engine

### 4.1 Struttura del modulo

```
api/services/fitscan/
├── __init__.py
├── types.py                    # PoseFrame, PoseSequence, ScanResult, FormResult
├── pose_normalizer.py          # Normalizzazione keypoints (scala, rotazione, centratura)
├── body_ratios.py              # L1: calcolo rapporti corporei da pose statiche
├── posture_analyzer.py         # L1: analisi posturale (cifosi, lordosi, valgismo, tilt)
├── symmetry_analyzer.py        # L1: indice simmetria bilaterale
├── exercise_form_rules.py      # L2: regole biomeccaniche per esercizio
├── rep_detector.py             # L2: detection cicli (rep) da sequenza angoli articolari
├── tempo_analyzer.py           # L2: durata fasi concentrica/eccentrica/pausa
├── form_scorer.py              # L2: scoring composito per rep e per sessione
├── safety_crossref.py          # L1+L2: cross-reference con Safety Engine
├── measurement_bridge.py       # L1: bridge verso ClientMeasurement (auto-populate)
└── exercise_profiles/          # L2: profili biomeccanici per esercizio
    ├── __init__.py
    ├── squat.py                # angoli ideali, ROM, errori comuni
    ├── deadlift.py
    ├── bench_press.py
    ├── overhead_press.py
    ├── row.py
    ├── lunge.py
    └── ...                     # top 20 esercizi compound
```

### 4.2 Body Ratio Calculator (L1)

Calcola metriche da pose statiche (1-3 frame).

```python
# Metriche calcolabili dai 33 keypoints MediaPipe
BODY_SCAN_METRICS = {
    # --- Rapporti corporei (frontale) ---
    "shoulder_hip_ratio": {
        "formula": "dist(l_shoulder, r_shoulder) / dist(l_hip, r_hip)",
        "source_pose": "front",
        "unit": "ratio",
        "normal_range_m": (1.35, 1.55),  # Reiss & Minkoff 2016
        "normal_range_f": (1.15, 1.35),
    },
    "torso_leg_ratio": {
        "formula": "dist(mid_shoulder, mid_hip) / dist(mid_hip, mid_ankle)",
        "source_pose": "front",
        "unit": "ratio",
        "normal_range": (0.45, 0.55),     # proporzione aurea approssimata
    },
    "arm_span_height_ratio": {
        "formula": "dist(l_wrist, r_wrist) / dist(mid_head, mid_ankle)",
        "source_pose": "front",
        "unit": "ratio",
        "normal_range": (0.95, 1.05),     # vitruviano ~1.0
    },

    # --- Simmetria (frontale) ---
    "bilateral_symmetry_upper": {
        "formula": "1 - abs(dist(l_shoulder,l_elbow) - dist(r_shoulder,r_elbow)) / avg",
        "source_pose": "front",
        "unit": "percent",
        "ideal": 100,                      # 100% = perfettamente simmetrico
    },
    "bilateral_symmetry_lower": {
        "formula": "1 - abs(dist(l_hip,l_knee) - dist(r_hip,r_knee)) / avg",
        "source_pose": "front",
        "unit": "percent",
        "ideal": 100,
    },

    # --- Postura (frontale) ---
    "shoulder_alignment_deg": {
        "formula": "angle(l_shoulder, r_shoulder, horizontal)",
        "source_pose": "front",
        "unit": "degrees",
        "ideal": 0,                        # 0 = perfettamente orizzontale
        "threshold_warning": 3,
        "threshold_alert": 5,
    },
    "pelvic_tilt_frontal_deg": {
        "formula": "angle(l_hip, r_hip, horizontal)",
        "source_pose": "front",
        "unit": "degrees",
        "ideal": 0,
        "threshold_warning": 3,
        "threshold_alert": 5,
    },

    # --- Postura (laterale) ---
    "forward_head_deg": {
        "formula": "angle(ear, shoulder, vertical)",
        "source_pose": "side_r",
        "unit": "degrees",
        "ideal": 0,                        # 0 = orecchio sopra la spalla
        "threshold_warning": 15,
        "threshold_alert": 25,
    },
    "thoracic_kyphosis_deg": {
        "formula": "angle(shoulder, mid_spine_est, hip)",
        "source_pose": "side_r",
        "unit": "degrees",
        "normal_range": (20, 45),          # Griegel-Morris 1992
    },
    "knee_valgus_left_deg": {
        "formula": "angle(l_hip, l_knee, l_ankle) deviation from 180",
        "source_pose": "front",
        "unit": "degrees",
        "ideal": 180,                      # asse retto
        "threshold_warning": 8,
        "threshold_alert": 15,
    },
    "knee_valgus_right_deg": {
        "formula": "angle(r_hip, r_knee, r_ankle) deviation from 180",
        "source_pose": "front",
        "unit": "degrees",
        "ideal": 180,
        "threshold_warning": 8,
        "threshold_alert": 15,
    },

    # --- Score composito ---
    "posture_score": {
        "formula": "weighted_composite(alignment, symmetry, kyphosis, valgus)",
        "source_pose": "composite",
        "unit": "score",
        "range": (0, 100),                 # 100 = postura ideale
    },
}
```

### 4.3 Exercise Form Analyzer (L2)

Per ogni esercizio, un **profilo biomeccanico** definisce:
- Quali angoli articolari monitorare
- I range ideali per ogni fase del movimento (eccentrica, bottom, concentrica, top)
- Le deviazioni che costituiscono errore
- Le soglie modificate per condizioni (via Safety Engine)

```python
# Esempio: profilo Back Squat
SQUAT_PROFILE = ExerciseFormProfile(
    exercise_patterns=["squat"],  # match con pattern_movimento in catalog.db
    exercise_names=["back squat", "front squat", "goblet squat"],

    # Keypoints coinvolti
    primary_joints=["l_hip", "l_knee", "l_ankle", "r_hip", "r_knee", "r_ankle"],
    secondary_joints=["l_shoulder", "r_shoulder", "nose"],

    # Angoli da monitorare frame-by-frame
    tracked_angles={
        "knee_flexion_l": AngleSpec(
            points=("l_hip", "l_knee", "l_ankle"),
            phase_ranges={
                "standing":    (170, 180),  # quasi esteso
                "descending":  (90, 170),   # eccentrica
                "bottom":      (70, 100),   # massima flessione
                "ascending":   (90, 170),   # concentrica
            },
            error_threshold=10,  # gradi fuori range = warning
        ),
        "hip_hinge": AngleSpec(
            points=("l_shoulder", "l_hip", "l_knee"),
            phase_ranges={
                "standing":    (160, 180),
                "bottom":      (60, 90),
            },
        ),
        "trunk_lean": AngleSpec(
            points=("mid_shoulder", "mid_hip", "vertical"),
            phase_ranges={
                "bottom":      (30, 55),   # inclinazione busto accettabile
            },
            error_threshold=15,
        ),
        "knee_valgus": AngleSpec(
            points=("l_hip", "l_knee", "l_ankle"),
            ideal=180,  # asse retto
            error_threshold=10,
        ),
    },

    # Rilevamento rep: il ciclo e' definito dall'angolo ginocchio
    rep_detection_angle="knee_flexion_l",
    rep_bottom_threshold=100,   # sotto 100 gradi = bottom della rep
    rep_top_threshold=160,      # sopra 160 gradi = top della rep

    # Errori comuni con label e gravita'
    common_errors=[
        FormError("knee_cave", "Ginocchia verso l'interno (valgismo dinamico)",
                  condition="knee_valgus < 170", severity="warning"),
        FormError("depth_insufficient", "Profondita' insufficiente",
                  condition="knee_flexion_min > 100", severity="info"),
        FormError("excessive_lean", "Busto troppo inclinato in avanti",
                  condition="trunk_lean > 55", severity="warning"),
        FormError("heels_rising", "Talloni che si alzano",
                  condition="ankle_dorsiflexion > threshold", severity="warning"),
    ],

    # Tempo target (secondi)
    ideal_tempo={
        "eccentric": (2.0, 4.0),    # discesa controllata
        "pause":     (0.0, 1.0),    # pausa in basso (opzionale)
        "concentric": (1.0, 3.0),   # risalita
    },

    # Modifiche per condizioni (Safety Engine cross-ref)
    condition_overrides={
        # condizione_id → override degli angoli
        1:  {"knee_flexion.bottom": (90, 120)},         # ernia discale: squat piu' alto
        14: {"knee_valgus.error_threshold": 5},          # ACL: soglia valgismo dimezzata
        15: {"knee_flexion.bottom": (80, 110)},          # menisco: ROM limitato
        16: {"knee_flexion.bottom": (90, 120)},          # gonartrosi: squat piu' alto
    },
)
```

### 4.4 Safety Cross-Reference

```python
def cross_reference_scan_with_safety(
    scan_metrics: dict[str, float],
    client_conditions: set[int],       # da extract_client_conditions()
    client_medications: dict[str, bool] # da medication_flags()
) -> list[ScanAlert]:
    """
    Incrocia i risultati dello scan con le condizioni del cliente.

    NON assegna condizioni automaticamente.
    Genera SUGGERIMENTI per il trainer.
    """
    alerts = []

    # Esempio: simmetria bassa + nessuna condizione nota → suggerire revisione
    if scan_metrics.get("bilateral_symmetry_upper", 100) < 90:
        if not any(c in client_conditions for c in SHOULDER_CONDITIONS):
            alerts.append(ScanAlert(
                type="review_suggestion",
                message="Asimmetria significativa nelle spalle. "
                        "Verificare se il cliente ha condizioni non registrate.",
                severity="info",
                related_conditions=SHOULDER_CONDITIONS,
            ))

    # Esempio: valgismo significativo + ACL nota → alert critico
    if scan_metrics.get("knee_valgus_left_deg", 0) > 10:
        if 14 in client_conditions:  # ACL
            alerts.append(ScanAlert(
                type="safety_alert",
                message="Valgismo dinamico significativo con storia di ACL. "
                        "Rivalutare esercizi a catena cinetica chiusa.",
                severity="critical",
            ))

    return alerts
```

---

## 5. Pose Provider: implementazioni

### 5.1 MediaPipe Pose Landmarker (browser) — PROTOTIPO

```
Keypoints: 33 (3D relativo)
FPS: 25-30 su telefono medio
SDK: @mediapipe/tasks-vision (JavaScript)
Requisiti: HTTPS o localhost (per camera access)
Accuracy: buona per pose statiche, media per movimenti veloci
```

Keypoints MediaPipe rilevanti per FitScan:

```
 0  nose              11 left_shoulder    23 left_hip
 1  left_eye_inner    12 right_shoulder   24 right_hip
 2  left_eye          13 left_elbow       25 left_knee
 3  left_eye_outer    14 right_elbow      26 right_knee
 4  right_eye_inner   15 left_wrist       27 left_ankle
 5  right_eye         16 right_wrist      28 right_ankle
 6  right_eye_outer   17 left_pinky       29 left_heel
 7  left_ear          18 right_pinky      30 right_heel
 8  right_ear         19 left_index       31 left_foot_index
 9  mouth_left        20 right_index      32 right_foot_index
10  mouth_right       21 left_thumb
                      22 right_thumb
```

**Keypoints mancanti** (limitazione nota):
- Nessun punto scapolare (approssimabile dalla traiettoria spalla)
- Nessun segmento spinale (stimabile da shoulder-hip-ear in vista laterale)
- Nessun punto sulla pianta del piede (heel + foot_index coprono parzialmente)

### 5.2 YOLOv8-pose su Hailo-8L (Box Pro) — PRODUZIONE

```
Keypoints: 17 (COCO format, 2D)
FPS: 30 su Hailo-8L (13 TOPS)
Pipeline: ONNX → Hailo DFC → HEF compiled model
Requisiti: Hailo-8L M.2 HAT + PiCam v3
Accuracy: alta per detection + pose, meno keypoints di MediaPipe
```

Keypoints COCO (YOLOv8-pose):

```
 0  nose               5  left_shoulder    11 left_hip
 1  left_eye           6  right_shoulder   12 right_hip
 2  right_eye          7  left_elbow       13 left_knee
 3  left_ear           8  right_elbow      14 right_knee
 4  right_ear          9  left_wrist       15 left_ankle
                      10  right_wrist      16 right_ankle
```

**Mapping**: il Biomechanical Engine usa un **keypoint_mapper** che traduce i nomi del provider nel formato interno. 17 keypoints COCO sono un sottoinsieme dei 33 MediaPipe — tutte le metriche articolari funzionano con entrambi. Le metriche che richiedono heel/foot_index (MediaPipe only) vengono marcate `confidence: 0` con provider YOLO.

### 5.3 Modello custom (futuro)

Quando e se:
- Servono keypoints aggiuntivi (scapole, spine, piedi) non coperti da MediaPipe
- Serve tracking attrezzi (barbell, dumbbell) per bar path analysis
- Si dispone di dataset fitness-specifico annotato (>5000 video)

Il Biomechanical Engine non cambia: riceve `PoseFrame[]`, analizza. Solo il Pose Provider viene sostituito.

---

## 6. Frontend Components

### 6.1 L1 — ScanCapture (Body Scan)

```
Flusso:
1. Trainer seleziona cliente nel profilo
2. Tocca "Nuova scansione" → apre camera
3. Guida visiva: sagoma frontale + countdown 3s
4. Cattura frame frontale → overlay keypoints → conferma
5. "Girati a destra" → sagoma laterale → cattura
6. "Girati a sinistra" → sagoma laterale → cattura
7. Invio 3 PoseFrame al backend → calcolo metriche
8. Risultato: card con metriche + confronto con scan precedente

Componenti:
  - CameraView: gestione stream, permessi, fallback
  - PoseOverlay: canvas sovrapposto con keypoints + connessioni
  - GuideSilhouette: sagoma target per posizionamento corretto
  - ScanResultCard: metriche calcolate + delta + score
  - ScanHistoryChart: grafico progressione nel tempo
```

### 6.2 L2 — FormAnalysis (Exercise Form)

```
Flusso:
1. Durante sessione di allenamento, trainer tocca "Analizza forma"
2. Seleziona esercizio (pre-selezionato se in workout attivo)
3. Camera attiva, overlay keypoints + angoli live
4. Cliente esegue le rep
5. Feedback real-time: angoli visualizzati, alert colorati
6. Fine serie → riepilogo: rep count, form score per rep, errori comuni
7. Dati salvati in exercise_form_sessions + reps

Componenti:
  - LiveFormOverlay: keypoints + angoli + feedback colorato in tempo reale
  - RepCounter: rilevamento cicli, display conteggio
  - FormScoreCard: punteggio per rep con breakdown errori
  - FormHistoryComparison: confronto sessione attuale vs precedenti
```

---

## 7. Privacy e Sicurezza

| Dato | Dove vive | Chi puo' accedervi |
|---|---|---|
| Frame video raw | Mai persistiti. Processati in memoria (browser o backend). | Solo il dispositivo locale |
| Foto riferimento (3 pose) | `data/scans/{client_id}/` sul dispositivo locale | Solo il trainer autenticato |
| Keypoints raw (JSON) | crm.db, tabella body_scans | Solo il trainer (bouncer pattern) |
| Metriche calcolate | crm.db, tabella body_scan_metrics | Solo il trainer (bouncer pattern) |
| Sequenza video (L2) | Opzionale. Se salvata, in `data/scans/` locale. | Solo il trainer |

**Invarianti**:
- Nessun frame/video trasmesso in rete (processing locale)
- Nessun dato biometrico su cloud
- Consent del cliente richiesto prima della prima scansione (tracciato in anamnesi)
- Soft delete su body_scans (coerente con il resto del CRM)
- Backup USB include scans (coerente con backup crm.db)

---

## 8. Piano di Delivery

| Fase | Scope | Prerequisiti | Effort stimato |
|---|---|---|---|
| **Prototipo L1** | Body Scan statico, 3 pose, 12 metriche, MediaPipe browser | Nessuno (funziona su PC dev) | 5-7 giorni |
| **Integrazione L1** | Bridge con ClientMeasurement, scan nel profilo cliente, history chart | Prototipo L1 funzionante | 3-4 giorni |
| **Prototipo L2** | Form Analysis per 3 esercizi (squat, deadlift, bench), rep detection | L1 completato, profili biomeccanici definiti | 7-10 giorni |
| **Scaling L2** | Profili per top 20 esercizi compound | Prototipo L2 validato | 5-7 giorni |
| **L3** | Movement screening (overhead squat test, single-leg) | L2 maturo | 5-7 giorni |
| **Box Pro** | YOLOv8 su Hailo, PiCam, inferenza server-side | Box funzionante (ADR-006 Fase 2) | 3-5 giorni |

---

## 9. Limiti noti e onesta' tecnica

| Limitazione | Impatto | Mitigazione |
|---|---|---|
| No misure assolute in cm da camera 2D | Non possiamo dire "girovita = 82cm" | Tracking relativo (delta %) + altezza dichiarata per normalizzazione |
| MediaPipe z (profondita') e' relativo, non metrico | Analisi 3D approssimata | Per L1 basta 2D frontale + laterale. Per L2, z migliora con Hailo stereo (futuro) |
| Occlusioni (mani davanti al corpo, bilanciere) | Keypoints con bassa confidence | Filtro confidence > 0.5, marcatura metriche come "bassa affidabilita'" |
| Abbigliamento largo nasconde landmark | Keypoints spostati | Guida per il trainer: "clienti in abbigliamento aderente per scan" |
| Illuminazione scarsa | Confidence cala | Guida: "illuminazione frontale uniforme" + soglia minima per accettare scan |
| No tracking attrezzi | Non possiamo analizzare bar path | Futuro: object detection per bilanciere/manubri (modello aggiuntivo) |
| No attivazione muscolare | Impossibile da video | Dichiarato come limitazione. EMG richiede sensori fisici. |

---

## 10. Riferimenti scientifici

| Fonte | Uso in FitScan |
|---|---|
| Reiss & Minkoff 2016 | Range normali rapporti corporei |
| Griegel-Morris 1992 | Range normali cifosi toracica |
| Schoenfeld 2010, Contreras 2010 | Matrice EMG (gia' in Training Science Engine) |
| Israetel/Renaissance Periodization 2020 | Volume MEV/MAV/MRV (gia' in volume_model.py) |
| Sahrmann 2002 | Assessment posturale, disfunzioni movimento |
| Cook 2010 (FMS) | Functional Movement Screen (base per L3) |
| Alentorn-Geli 2009 | Fattori rischio ACL, valgismo dinamico |
| NSCA 2016 (Essentials) | Angoli articolari ideali per esercizi compound |

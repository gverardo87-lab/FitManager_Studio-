# VIDEO_PRODUCTION.md — Runbook Operativo Produzione Video

Documento operativo per produrre video-guide FitManager Studio+.
Non teoria — solo procedure verificate, selettori testati, problemi risolti.

**Ultima revisione**: 2026-03-25 (consolidamento post-video 01 "Il Primo Cliente")

---

## 1. Toolchain

Percorsi fissi Windows (verificati):

```
FFmpeg:    C:\Users\gvera\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe
FFprobe:   (stessa directory)\ffprobe.exe
Playwright: npx playwright (v1.58.2, nel progetto)
ElevenLabs: API REST (chiave in ~/.fitmanager/elevenlabs.env)
```

---

## 2. Configurazione Audio (definitiva)

### Voce
| Parametro | Valore |
|-----------|--------|
| Provider | ElevenLabs |
| Modello | `eleven_multilingual_v2` |
| Voce | Daniel |
| Voice ID | `onwK4e9ZLuTAKqWW03F9` |
| Stability | 0.5 |
| Similarity boost | 0.75 |
| Lingua | Italiano nativo |
| Reference | `data/videos/voce-daniel-reference.mp3` |

### Musica
| Parametro | Valore |
|-----------|--------|
| Provider | ElevenLabs Sound Generation |
| Stile | Acoustic calm (fingerpicked guitar + warm pad) |
| Prompt | "gentle acoustic ambient music, soft fingerpicked guitar with subtle warm pad underneath, very calm and grounded, evokes trust and simplicity, background for a premium software demo" |
| Limite API | 22s per richiesta → concat 3 parti per 60s+ |
| Mix volume | 18% rispetto alla voce |
| Fade in | 2s |
| Fade out | 3s (ultimi 3s del video) |
| Reference | `data/videos/musica-reference-acoustic.mp3` |

### Limiti API ElevenLabs
- **Max 2 richieste parallele** (piano gratuito) → generare VO in sequenza, non parallelo
- **Encoding**: usare Python `urllib` con `.encode('utf-8')`, NON curl con bash (problemi accenti)
- **~10.000 caratteri/mese** piano gratuito

### Generazione VO (comando verificato)
```python
import json, urllib.request
data = json.dumps({
    'text': '<TESTO ITALIANO>',
    'model_id': 'eleven_multilingual_v2',
    'voice_settings': {'stability': 0.5, 'similarity_boost': 0.75}
}).encode('utf-8')
req = urllib.request.Request(
    'https://api.elevenlabs.io/v1/text-to-speech/onwK4e9ZLuTAKqWW03F9',
    data=data,
    headers={'xi-api-key': '<KEY>', 'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req) as resp, open('output.mp3', 'wb') as f:
    f.write(resp.read())
```

### Generazione Musica (comando verificato)
```python
data = json.dumps({
    'text': '<PROMPT MUSICALE>',
    'duration_seconds': 22  # MAX 22s per richiesta
}).encode('utf-8')
req = urllib.request.Request(
    'https://api.elevenlabs.io/v1/sound-generation',
    data=data,
    headers={'xi-api-key': '<KEY>', 'Content-Type': 'application/json'}
)
```
Per video >22s: genera 3 parti e concatena con FFmpeg + crossfade.

---

## 3. Configurazione Playwright (definitiva)

### Browser
```javascript
const browser = await chromium.launch({
  headless: false,
  slowMo: 80,            // 80ms tra azioni — visivamente leggibile
  args: ["--start-maximized"],
});
const context = await browser.newContext({
  viewport: null,         // OBBLIGATORIO con --start-maximized
  recordVideo: {
    dir: CLIPS_DIR,
    size: { width: 1440, height: 900 },  // Risoluzione output video
  },
  storageState: authStatePath,  // Cookie auth pre-salvati
});
```

### Regole ferree
- **MAI `viewport: { width: X, height: Y }`** con `--start-maximized` → causa layout sfalsato
- **MAI headless** per registrazione → il video non cattura nulla
- **MAI piu' di 2 richieste ElevenLabs in parallelo**
- **Sempre `--start-maximized` + `viewport: null`** → layout identico al browser reale

### Login e auth state
```javascript
// Login una volta, salva cookies, riusa per tutte le scene
await authCtx.storageState({ path: authStatePath });
// Ogni scena successiva usa: storageState: authStatePath
```

---

## 4. Mappa Selettori UI (verificati 2026-03-25)

### 4.1 Pagina Clienti (`/clienti`)

| Elemento | Selettore | Note |
|----------|-----------|------|
| Header | `[data-guide="clienti-header"]` | Usare come "pagina pronta" |
| Bottone Nuovo | `[data-guide="clienti-new-button"]` | Apre Sheet |
| KPI cards | `[data-guide="clienti-kpi"]` | |
| Riga cliente | `td:has-text("Cognome")` | Click apre profilo |
| Ricerca | `[data-guide="clienti-search"]` | |

### 4.2 Sheet Nuovo Cliente (dentro `/clienti`)

| Elemento | Selettore | Note |
|----------|-----------|------|
| Nome | `#nome` | Input text, `register("nome")` |
| Cognome | `#cognome` | Input text |
| Email | `#email` | Input email (opzionale) |
| Telefono | `#telefono` | Input text (opzionale) |
| Submit | `button:has-text("Crea Cliente")` | `type="submit"` |
| Submit (edit) | `button:has-text("Salva Modifiche")` | |

### 4.3 Profilo Cliente (`/clienti/[id]`)

| Elemento | Selettore | Note |
|----------|-----------|------|
| Avatar hero | `[data-guide="client-avatar-hero"]` | |
| Checklist | `[data-guide="client-onboarding-checklist"]` | |
| CTA "Crea contratto" | `text=Crea contratto` | Hero card OnboardingChecklist step 1 |
| CTA "Compila" (anamnesi) | `text=Compila` | Hero card step 2 |
| Tab Panoramica | `text=Panoramica` | Tab attivo di default |
| Tab Contratti | `text=Contratti` | |
| Tab Sessioni | `text=Sessioni` | |
| Tab Schede | `text=Schede` | |

### 4.4 Sheet Nuovo Contratto (`/contratti?new=1&cliente=ID`)

| Elemento | Selettore | Note |
|----------|-----------|------|
| Tipo pacchetto | `#tipo_pacchetto` | Input text |
| Crediti | `#crediti_totali` | Input number |
| Prezzo totale | `#prezzo_totale` | Input number, step 0.01 |
| Data inizio | `button:has-text("Inizio...")` | DatePicker trigger |
| Data scadenza | `button:has-text("Scadenza...")` | DatePicker trigger |
| Acconto | `#acconto` | Input number (solo creazione, non edit) |
| Metodo acconto | `[data-slot="select-trigger"]:has-text("Metodo")` | Radix Select, appare solo se acconto > 0. **MAI `:last-of-type`** (risolve a 2 elementi, vedi §8.3 punto 3) |
| Submit | `button[type="submit"]:has-text("Crea Contratto")` | |
| Sheet content | `[data-slot="sheet-content"]` | Per scroll interno |

### 4.5 Dettaglio Contratto (`/contratti/[id]`)

| Elemento | Selettore | Note |
|----------|-----------|------|
| Header | `[data-guide="contratto-header"]` | "Pagina pronta" |
| Hero finanziario | `[data-guide="contratto-hero-finanziario"]` | KPI cards |
| Piano rate | `[data-guide="contratto-piano-rate"]` | |
| Numero rate | `#numero_rate` | Input number nel form genera |
| Data prima rata | `button:has-text("Seleziona data...")` | DatePicker nel form genera |
| Frequenza | Select in GeneratePlanForm | Radix Select |
| Genera rate | `button:has-text("Genera Piano Pagamenti")` | **Disabled se data non selezionata** |

### 4.6 DatePicker (componente globale)

| Azione | Selettore/Metodo | Note |
|--------|------------------|------|
| Apri calendario | Click sul trigger button | Testo: placeholder o data formattata |
| Formato data-day | `DD/MM/YYYY` | Es: `button[data-day="01/04/2026"]` |
| Naviga mese avanti | `button.rdp-button_next` | |
| Naviga mese indietro | `button.rdp-button_previous` | |
| Seleziona giorno | `button[data-day="DD/MM/YYYY"]` | Potrebbe servire navigare prima |
| Chiudi senza selezionare | `Escape` | |

**Procedura `selectDate()` verificata:**
```javascript
async function selectDate(page, triggerText, targetDataDay, maxNavClicks = 6) {
  await page.locator(`button:has-text("${triggerText}")`).click();
  await wait(500);
  const daySelector = `button[data-day="${targetDataDay}"]`;
  let dayBtn = page.locator(daySelector);
  if (await dayBtn.isVisible({ timeout: 500 }).catch(() => false)) {
    await dayBtn.click();
    return;
  }
  for (let i = 0; i < maxNavClicks; i++) {
    await page.locator('button.rdp-button_next').click();
    await wait(400);
    if (await dayBtn.isVisible({ timeout: 500 }).catch(() => false)) {
      await dayBtn.click();
      return;
    }
  }
  throw new Error(`Data ${targetDataDay} non trovata`);
}
```

### 4.7 Radix Select (componente globale)

| Azione | Selettore | Note |
|--------|-----------|------|
| Apri dropdown | `[data-slot="select-trigger"]` | Potrebbe esserci piu' di uno → usare `.last()` o indice |
| Opzione | `[data-slot="select-item"]:has-text("VALORE")` | Testo esatto, case-sensitive |

**Procedura `selectRadixOption()` verificata:**
```javascript
async function selectRadixOption(page, triggerSelector, optionText) {
  await page.locator(triggerSelector).click();
  await wait(400);
  await page.locator(`[data-slot="select-item"]:has-text("${optionText}")`).click();
  await wait(300);
}
```

### 4.8 Pagina Anamnesi + Wizard (`/clienti/[id]/anamnesi`)

| Elemento | Selettore | Note |
|----------|-----------|------|
| Bottone "Compila tu" | `button:has-text("Compila tu")` | **Apre il wizard** — NON usare `?startWizard=1` (non affidabile con Playwright) |
| Bottone "Invia al cliente" | `button:has-text("Invia al cliente")` | Alternativa (portale self-service) |
| Avanti (dentro wizard) | `button:has-text("Avanti")` | Naviga al prossimo step |
| Indietro (dentro wizard) | `button:has-text("Indietro")` | |
| Salva (dentro wizard) | `button:has-text("Salva")` | Solo ultimo step |

**Flusso verificato**: navigare a `/clienti/[id]/anamnesi` → click "Compila tu" → wizard si apre → "Avanti" visibile.

### 4.9 Selettori "Pagina Pronta" (waitForSelector)

| Pagina | Selettore | Timeout |
|--------|-----------|---------|
| `/clienti` | `[data-guide="clienti-header"]` | 10s |
| `/clienti/[id]` | `[data-guide="client-avatar-hero"]` | 10s |
| `/contratti` | `[data-guide="contratti-header"]` | 10s |
| `/contratti/[id]` | `[data-guide="contratto-header"]` | 10s |
| `/agenda` | `[data-guide="agenda-header"]` | 10s |
| `/cassa` | `[data-guide="cassa-header"]` | 10s |
| `/esercizi` | `[data-guide="esercizi-header"]` | 10s |
| `/schede` | `[data-guide="schede-header"]` | 10s |
| `/impostazioni` | `[data-guide="impostazioni-header"]` | 10s |
| `/guida` | `[data-guide="guida-hero"]` | 10s |
| Dashboard | `[data-guide="dashboard-header"]` | 10s |

---

## 5. Mappa Navigazioni

### 5.1 Flusso Onboarding (video 01) — VERIFICATO 2026-03-25

```
/clienti                          → "Nuovo Cliente" → Sheet (stessa pagina)
Sheet "Crea Cliente"              → submit → AUTO-REDIRECT a /clienti/[id] (profilo)
                                    ⚠ NON torna alla lista — siamo GIA' sul profilo
/clienti/[id] checklist           → "Crea contratto" → ContractSheet INLINE (stessa pagina!)
                                    ⚠ NON naviga a /contratti?new=1 — apre sheet sul profilo
ContractSheet submit              → sheet si chiude → restiamo su /clienti/[id]
                                    ⚠ NON redirige a /contratti/[id] — serve navigazione esplicita
/clienti/[id]                     → API fetch per trovare contractId → goto /contratti/[id]
/contratti/[id]                   → scroll a piano rate → genera → rate visibili
/contratti/[id]                   → goBack → /clienti/[id] (profilo con checklist aggiornata)
/clienti/[id] checklist           → "Compila" → /clienti/[id]/anamnesi
/clienti/[id]/anamnesi            → "Compila tu" → wizard aperto → Avanti/Salva
```

### 5.2 Tempi di caricamento (dev, porta 3001)

| Navigazione | Tempo reale | Trim consigliato |
|-------------|-------------|------------------|
| goto qualsiasi pagina | 1.0-2.0s | 1.5s |
| Sheet apertura | 0.3-0.5s | 0s |
| Submit + redirect | 1.5-2.5s | 0s (l'azione e' parte del video) |
| Toast apparizione | 0.5-1.0s | 0s |

---

## 6. Pipeline Produzione (5 fasi + manifest)

### Architettura: Manifest SSoT

Ogni video ha un `manifest.json` che fa da **Single Source of Truth** per il timing.
Il manifest elimina tre classi di bug ricorrenti:
- **Clip corto**: impossibile — Playwright legge `vo_duration + gap` dal manifest e aspetta abbastanza
- **Trim sbagliato**: impossibile — `trim_start` misurato durante registrazione, non stimato
- **Offset sfasato**: impossibile — montaggio calcola offset da durate reali trimmate

```
VO generato → manifest-sync.js (misura durate) → manifest.json (SSoT)
                                                        |
                                          +-------------+-------------+
                                          |                           |
                                    Playwright LEGGE            montage.js LEGGE
                                    vo_duration + gap            trim + durate reali
                                    → wait VO-locked             → zero hardcode
```

**Comandi**:
```bash
node tools/video/manifest-sync.js data/videos/<slug>   # misura VO + clip, aggiorna manifest
node tools/video/montage.js data/videos/<slug>          # montaggio deterministico da manifest
```

**Infrastruttura** (`tools/video/`):
| File | Ruolo |
|------|-------|
| `lib.js` | SSoT percorsi FFmpeg, misurazione durate, manifest I/O, validazione, helper registrazione |
| `manifest-sync.js` | Scansiona VO + clip su disco, misura durate reali, aggiorna manifest |
| `montage.js` | Montaggio deterministico: GATE validazione → trim → xfade → VO sync → mix |

### Fase 1 — Script editoriale
**Input**: idea del video
**Output**: `docs/videos/<slug>.md` con timeline secondo per secondo
**Formato**: tabella `Secondo | Azione video | Sync con VO`

Regole:
- 150 parole = 1 minuto (stima TTS Daniel)
- 1 concetto = 1 scena
- Max 2 frasi per scena
- Ogni scena ha UN'AZIONE visibile
- Il VO dice quello che il video mostra (MAI incongruenze)

### Fase 2 — Asset audio + manifest
**Input**: script approvato
**Output**: VO per scena (`scenes/01_nome.mp3`) + musica (`music/background.mp3`) + `manifest.json`

Procedura:
1. Crea `manifest.json` con struttura scene (nome, VO file, gap, page_ready_selector)
2. Genera ogni VO in sequenza (max 2 parallele ElevenLabs) con Python urllib
3. Genera musica (3 parti da 22s → concat → fade in/out)
4. **`node tools/video/manifest-sync.js <dir>`** — misura durate reali, aggiorna manifest
5. Verifica report: tutti i VO hanno duration misurata

### Fase 3 — Pre-flight interazione
**Input**: script con azioni Playwright
**Output**: conferma che TUTTE le interazioni funzionano

**QUESTO STEP E' OBBLIGATORIO. Senza pre-flight, non si registra.**

Procedura:
1. Per ogni scena, scrivi un test che esegue le azioni SENZA registrare video
2. Verifica che ogni selettore trovi l'elemento
3. Verifica che ogni navigazione arrivi a destinazione
4. Verifica che lo stato del DB sia quello atteso (cliente creato, contratto presente, ecc.)
5. Se un test fallisce, correggi il selettore e ri-testa
6. Solo quando TUTTI i test passano, procedi alla fase 4

### Fase 4 — Registrazione video (VO-locked)
**Input**: pre-flight passato, manifest con durate VO
**Output**: clip per scena (`clips/01_nome.webm`) + manifest aggiornato con `trim_start` e `clip_duration`

Regole:
- Browser `--start-maximized` + `viewport: null`
- Auth state pre-salvato (login una volta sola)
- SlowMo 80ms per leggibilita' visiva
- Ogni scena = un browser context separato (cleanup automatico)
- Se una scena fallisce, ri-registra SOLO quella

**VO-locked timing** (il cuore del metodo):
```javascript
const { getSceneTiming, updateRecording } = require("../../tools/video/lib");
const timing = getSceneTiming(videoDir, "04_anamnesi");
// timing.minDuration = vo_duration + gap + 0.5s buffer

const recordingStart = Date.now();
// ... naviga alla pagina ...
await page.waitForSelector(selector, { timeout: 10000 });
const pageReady = Date.now();
// ... esegui azioni UI ...
const elapsed = (Date.now() - pageReady) / 1000;
if (elapsed < timing.minDuration) {
  await page.waitForTimeout((timing.minDuration - elapsed) * 1000);
}
// ... chiudi context ...

// Aggiorna manifest con timing MISURATO (non stimato)
updateRecording(videoDir, "04_anamnesi", {
  trimStart: (pageReady - recordingStart) / 1000
});
```

**Tempi caricamento dev** (porta 3001, NON installer):
- Navigazione pagina: 1.0-2.0s (variabile)
- `trim_start` viene MISURATO dal timestamp `pageReady - recordingStart`
- MAI hardcodare trim — i tempi cambiano tra sessioni

### Fase 4b — Registrazione continua (metodo preferito)

**UN browser, UN context, UN clip.** Navigazione diretta tra sezioni senza chiudere/riaprire.

```bash
node tools/scripts/video-01-primo-cliente.js   # registra tutto, salva full_flow.webm
```

Il flusso continuo e' piu' veloce, affidabile, e produce transizioni naturali.
Se una scena fallisce, ri-registra TUTTO (1-2 minuti, non ore).

**Pre-run obbligatorio**: `tools/scripts/video-cleanup-moretti.py` — hard-delete completo
di tutti i dati test (clienti + contratti + rate + movimenti). Senza pre-run, dati residui
da sessioni precedenti causano navigazioni a contratti vecchi, checklist gia' completate, ecc.

### Fase 5 — Montaggio deterministico

Due modalita' (scelta automatica dal `recording_mode` nel manifest):

**Modalita' `continuous`** (metodo preferito):
```bash
node tools/video/montage.js data/videos/<slug>
```
Pipeline: converti clip H.264 → VO sync (offset da scene_start) → mix con musica → output.
Zero split, zero crossfade — il clip continuo e' gia' il video finale, serve solo l'audio.

**Modalita' `clips`** (legacy):
```bash
node tools/video/manifest-sync.js data/videos/<slug>   # risincronizza durate
node tools/video/montage.js data/videos/<slug>          # trim + xfade + VO + mix
```

Parametri fissi (nel manifest, non hardcodati nello script):
```json
{
  "resolution": [1440, 900],
  "fps": 30,
  "codec": { "video": "libx264", "crf": 20, "audio": "aac", "audio_bitrate": "192k" },
  "crossfade_duration": 0.4,
  "music": { "volume": 0.18, "fade_in": 2.0, "fade_out": 3.0 }
}
```

---

## 7. Directory Structure

```
tools/video/                         # Infrastruttura (condivisa tra tutti i video)
├── lib.js                           # SSoT percorsi, FFprobe, manifest I/O, validazione
├── manifest-sync.js                 # Scansiona VO + clip, misura durate, aggiorna manifest
└── montage.js                       # Montaggio deterministico da manifest

data/videos/
├── voce-daniel-reference.mp3        # Campione voce definitiva
├── musica-reference-acoustic.mp3    # Campione musica definitiva
├── <slug>/
│   ├── manifest.json                # SSoT timing (durate VO, trim, gap, parametri video)
│   ├── scenes/                      # VO per scena (01_hook.mp3, 02_cliente.mp3, ...)
│   ├── clips/                       # Video clip per scena (01_hook.webm, ...)
│   ├── cards/                       # Title cards (intro.png, outro.png)
│   ├── music/                       # Background music (background.mp3, parti)
│   ├── auth-state.json              # Cookie auth Playwright (non committare)
│   └── <slug>.mp4                   # OUTPUT FINALE
└── exports/
    └── <slug>-<formato>.mp4         # Tagli (30s, 60s)
```

---

## 8. Errori Risolti

### 8.1 Playwright & Selettori (sessione iniziale)

| Errore | Causa | Soluzione |
|--------|-------|-----------|
| Layout sfalsato nel browser Playwright | `viewport: { width, height }` con `--start-maximized` | `viewport: null` — il viewport segue la finestra reale |
| Codegen inutilizzabile | Inspector panel ruba spazio, bussola resta aperta | Non usare codegen. Mappare selettori dal codice sorgente |
| DatePicker non seleziona data | Formato data-day sbagliato (provato US `M/D/YYYY`) | Formato corretto: `DD/MM/YYYY` (locale italiana) |
| Select BONIFICO risolve a 2 elementi | `text=BONIFICO` matcha sia `<option>` che `<span>` Radix | Usare `[data-slot="select-item"]:has-text("BONIFICO")` |
| Bottone "Genera Piano" disabled | DatePicker non compilato (data obbligatoria) | Selezionare data prima rata con `selectDate()` PRIMA del click |
| VO parla di azione ma video mostra risultato statico | Contratto e rate creati via API, non via UI | Registrare azioni REALI via UI — nessun dato pre-generato |

### 8.2 Audio (sessione iniziale)

| Errore | Causa | Soluzione |
|--------|-------|-----------|
| ElevenLabs rate limit | Piu' di 2 richieste parallele | Generare VO in sequenza, mai parallelo |
| ElevenLabs UTF-8 error | curl con bash non gestisce accenti italiani | Usare Python `urllib` con `.encode('utf-8')` |
| Musica SFX > 22s | Limite API ElevenLabs | Generare 3 parti da 22s e concatenare con FFmpeg |

### 8.3 Flusso Onboarding — CRITICI (sessione 2026-03-25)

Questi errori hanno causato ore di blocco. Tutti legati alla mappa navigazioni sbagliata.

| # | Errore | Causa root | Soluzione |
|---|--------|-----------|-----------|
| 1 | **Dopo "Crea Cliente" cerca `td:has-text("Moretti")` ma non trova nulla** | Il submit redirige AUTO a `/clienti/[id]` (profilo). NON torna alla lista clienti. Cercare nella tabella e' inutile — siamo gia' sul profilo | Dopo submit, aspettare `[data-guide="client-avatar-hero"]` direttamente. ZERO click sulla lista |
| 2 | **"Crea contratto" non naviga a `/contratti?new=1`** | La checklist CTA ha `onAction` che apre `ContractSheet` INLINE sul profilo (riga 113 di `clienti/[id]/page.tsx`). NON naviga via | Compilare il form nella sheet inline. I selettori §4.4 funzionano, ma siamo su `/clienti/[id]` non su `/contratti` |
| 3 | **Select metodo: `[data-slot="select-trigger"]:last-of-type` → strict mode violation** | La ContractSheet ha 2 select: cliente (pre-compilato "Moretti Luca") + metodo ("Metodo..."). `:last-of-type` risolve a entrambi (non sono fratelli nello stesso parent) | Usare `[data-slot="select-trigger"]:has-text("Metodo")` — seleziona per contenuto testuale, non posizione DOM |
| 4 | **Dopo submit contratto, navigazione al dettaglio trova contratto vecchio** | Il submit chiude la sheet e resta su `/clienti/[id]`. Il tab "Contratti" nel profilo potrebbe mostrare contratti di test precedenti se il pre-run non li ha puliti | Trovare `contractId` via API backend (`fetch("http://localhost:8001/api/contracts")` con Bearer token), filtrare per `id_cliente`, poi `goto /contratti/[contractId]` |
| 5 | **`#numero_rate` non trovato nella pagina contratto** | Navigava al contratto sbagliato (es. contratto 36 con rate gia' generate). Il form genera rate appare SOLO se `rate.length === 0` | Fix del punto 4 sopra — navigare al contratto CORRETTO del cliente appena creato |
| 6 | **Dati residui da test precedenti** | Soft-delete del cliente non rimuove contratti, rate, movimenti. I contratti vecchi restano attivi e possono interferire | Pre-run: hard-delete COMPLETO (clienti + contratti + rate + movimenti). Script: `tools/scripts/video-cleanup-moretti.py` |
| 7 | **Python multilinea in `execSync` fallisce** | `python -c "..."` con `\n` convertiti in `;` non supporta `if/for` blocks | Usare script `.py` separato, non `-c` inline |
| 8 | **Clip separati per scena causano desync, trim sbagliati, selettori ambigui** | Context separati per scena → ogni scena riparte da zero → deve cercare il cliente nella lista → selettori ambigui → crash | Registrazione continua: UN browser, UN context, UN clip. Navigazione diretta tra sezioni. Il `goBack()` funziona per tornare al profilo |
| 9 | **API fetch nel browser via proxy Next.js non trova i contratti** | `fetch("/api/contracts")` passa dal proxy Next.js che potrebbe non inoltrare correttamente | Usare URL backend diretto: `fetch("http://localhost:8001/api/contracts")` con header `Authorization: Bearer <token>` estratto dal cookie |

### 8.4 Montaggio — Errori risolti (sessione 2026-03-25)

| # | Errore | Causa root | Soluzione |
|---|--------|-----------|-----------|
| 1 | **Taskbar Windows catturata nel video** | `recordVideo` cattura 1440x900 ma la finestra browser non occupa l'intera altezza — la taskbar di Windows (~120px) appare come barra grigia in basso | `crop=1440:780:0:0,pad=1440:900:0:0:color=0xf0f4f8` — croppa la taskbar e pad con colore sfondo app. MAI `scale` dopo crop (stira l'immagine). Parametri nel manifest: `recording_crop_bottom`, `recording_pad_color` |
| 2 | **Flash bianco 0-2.5s all'inizio** | La prima navigazione (`goto /clienti`) mostra la pagina bianca di caricamento, catturata nella registrazione | `trim_start` nel manifest (es. 2.5s). Il montaggio usa `-ss` per saltare il flash. Gli offset VO vengono ricalcolati sottraendo il trim |
| 3 | **Outro tagliata dal video** | `-shortest` nel mix finale tronca il video alla durata dell'audio (VO piu' corto del video con outro) | Usare `apad=whole_dur=<videoDur>` per estendere il VO alla durata del video, poi `-t <videoDur>` invece di `-shortest` |
| 4 | **Immagine distorta dopo crop taskbar** | `crop` + `scale` stira verticalmente (780px → 900px) | Usare `crop` + `pad` con colore sfondo, non `crop` + `scale` |
| 5 | **Musica troppo invasiva (0.18)** | La musica ha picchi a -3.3 dB, anche a 0.18 i picchi raggiungono il livello medio della voce | Volume 0.10 + `acompressor=threshold=-20dB:ratio=4` sulla musica PRIMA di ridurre il volume. Il compressor appiattisce i picchi |

### 8.5 Regole derivate (NON NEGOZIABILI)

Dalla tabella §8.3, le regole da seguire **sempre** per la registrazione:

1. **MAI cercare un cliente nella tabella dopo la creazione** — il submit redirige al profilo
2. **MAI usare `:last-of-type` per i Select Radix** — usare `:has-text("Placeholder")`
3. **MAI navigare al contratto dal tab profilo** — usare API per trovare l'ID e `goto` diretto
4. **MAI registrare scene in context separati** — flusso continuo, un solo clip
5. **SEMPRE eseguire pre-run cleanup completo** — `video-cleanup-moretti.py`
6. **SEMPRE verificare il flusso navigazione REALE** prima di scriptare (il codice sorgente fa fede, non la documentazione vecchia)

---

## 9. Checklist Pre-Registrazione

Eseguire PRIMA di ogni sessione di registrazione:

- [ ] Backend dev running su porta 8001
- [ ] Frontend dev running su porta 3001
- [ ] Login verificato con credenziali dev
- [ ] **Pre-run cleanup eseguito** (`python tools/scripts/video-cleanup-moretti.py` — hard-delete completo)
- [ ] DB verificato pulito (zero Luca Moretti, zero contratti/rate orfani)
- [ ] Script editoriale completato con timeline secondo per secondo
- [ ] VO generati e durate reali misurate (`manifest-sync.js`)
- [ ] Musica generata (60s+)
- [ ] **Flusso navigazione verificato contro §5.1** (attenzione: redirect auto, sheet inline)
- [ ] **Selettori verificati contro §4** (attenzione: 2 select nella ContractSheet, §8.3 punto 3)
- [ ] Playwright `--start-maximized` + `viewport: null` verificato
- [ ] FFmpeg raggiungibile
- [ ] Spazio disco sufficiente per clip webm (~1-3 MB per scena)

---

## 10. Catalogo Video Pianificati

| # | Slug | Durata | Scopo | Stato |
|---|------|--------|-------|-------|
| 0 | `primi-10-minuti` | 78s | Panoramica generale (gia' in /guida) | COMPLETATO |
| 1 | `01-primo-cliente` | 86s | Crea cliente + contratto + anamnesi | COMPLETATO (v1) |
| 2 | `02-contratto-rate` | 60s | Approfondimento: pagamenti, parziali, rinnovi | PIANIFICATO |
| 3 | `03-agenda` | 45s | Sessioni, DnD, credit guard | PIANIFICATO |
| 4 | `04-cassa` | 60s | Pagamento rata, spese fisse, forecast | PIANIFICATO |
| 5 | `05-esercizi-safety` | 60s | Catalogo 500 + Safety Engine | PIANIFICATO |
| 6 | `06-scheda-allenamento` | 60s | Builder, blocchi, export PDF | PIANIFICATO |
| 7 | `07-misurazioni-progressi` | 45s | Misurazioni + analisi clinica | PIANIFICATO |
| 8 | `08-piano-alimentare` | 60s | Piano LARN 7 giorni | PIANIFICATO |
| 9 | `09-backup-dati` | 45s | Backup, restore, export | PIANIFICATO |

---

## 11. Naming Convention

| Tipo | Pattern | Esempio |
|------|---------|---------|
| Script editoriale | `docs/videos/<slug>.md` | `docs/videos/01-primo-cliente.md` |
| Script Playwright | `tools/scripts/video-<slug>.js` | `tools/scripts/video-01-primo-cliente.js` |
| Script montaggio | `tools/video/montage.js` | `node tools/video/montage.js data/videos/<slug>` |
| Script cleanup | `tools/scripts/video-cleanup-moretti.py` | Pre-run: hard-delete dati test |
| Script test | `tools/scripts/video-test-*.js` | `tools/scripts/video-test-full-flow.js` |
| Directory assets | `data/videos/<slug>/` | `data/videos/01-primo-cliente/` |
| Output finale | `data/videos/<slug>/<slug>.mp4` | `data/videos/01-primo-cliente/primo-cliente.mp4` |

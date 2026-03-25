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
| Metodo acconto | `[data-slot="select-trigger"]:last-of-type` | Radix Select, appare solo se acconto > 0 |
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

### 5.1 Flusso Onboarding (video 01)

```
/clienti                          → "Nuovo Cliente" → Sheet (stessa pagina)
Sheet "Crea Cliente"              → submit → toast → lista aggiornata
Lista clienti                     → click riga → /clienti/[id]
/clienti/[id] checklist           → "Crea contratto" → /contratti?new=1&cliente=[id]
/contratti?new=1&cliente=[id]     → auto-apre Sheet → compilazione → submit
Submit contratto                  → redirect → /contratti/[id]
/contratti/[id]                   → scroll a piano rate → genera → rate visibili
/clienti/[id] checklist           → "Compila" → /clienti/[id]/anamnesi?startWizard=1
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

### Fase 5 — Montaggio deterministico
**Input**: manifest.json completo (VO + clip + trim misurati)
**Output**: `<slug>.mp4` (H.264 + AAC, 1440x900, 30fps)

```bash
node tools/video/manifest-sync.js data/videos/<slug>   # 1. Risincronizza durate
node tools/video/montage.js data/videos/<slug>          # 2. Monta (con GATE validazione)
```

Il montaggio:
1. **GATE**: valida manifest — blocca se dati incompleti o clip corti
2. **TRIM**: `-ss trim_start -t (vo_duration + gap)` per ogni clip
3. **XFADE**: crossfade con offset da durate REALI trimmate (mai da target stimati)
4. **VO SYNC**: `adelay` con offset da durate REALI (allineamento perfetto)
5. **MIX**: video + VO + musica (volume, fade in/out da manifest)

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

## 8. Errori Risolti (2026-03-25)

| Errore | Causa | Soluzione |
|--------|-------|-----------|
| Layout sfalsato nel browser Playwright | `viewport: { width, height }` con `--start-maximized` | `viewport: null` — il viewport segue la finestra reale |
| Codegen inutilizzabile | Inspector panel ruba spazio, bussola resta aperta | Non usare codegen. Mappare selettori dal codice sorgente |
| DatePicker non seleziona data | Formato data-day sbagliato (provato US `M/D/YYYY`) | Formato corretto: `DD/MM/YYYY` (locale italiana) |
| Select BONIFICO risolve a 2 elementi | `text=BONIFICO` matcha sia `<option>` che `<span>` Radix | Usare `[data-slot="select-item"]:has-text("BONIFICO")` |
| ElevenLabs rate limit | Piu' di 2 richieste parallele | Generare VO in sequenza, mai parallelo |
| ElevenLabs UTF-8 error | curl con bash non gestisce accenti italiani | Usare Python `urllib` con `.encode('utf-8')` |
| Flash bianchi tra scene | Caricamento pagina (1-2s bianco) registrato nel clip | Trim iniziale per scena (`-ss 1.5`) + crossfade 0.4s |
| Bottone "Genera Piano" disabled | DatePicker non compilato (data obbligatoria) | Selezionare data prima rata con `selectDate()` PRIMA del click |
| VO parla di azione ma video mostra risultato statico | Contratto e rate creati via API, non via UI | Registrare azioni REALI via UI — nessun dato pre-generato |
| Musica SFX > 22s | Limite API ElevenLabs | Generare 3 parti da 22s e concatenare con FFmpeg |

---

## 9. Checklist Pre-Registrazione

Eseguire PRIMA di ogni sessione di registrazione:

- [ ] Backend dev running su porta 8001
- [ ] Frontend dev running su porta 3001
- [ ] Login verificato con credenziali dev
- [ ] DB in stato noto (sapere quali clienti/contratti esistono)
- [ ] Script editoriale completato con timeline secondo per secondo
- [ ] VO generati e durate reali misurate
- [ ] Timeline aggiornata con durate reali
- [ ] Musica generata (60s+)
- [ ] **Pre-flight interazione completato — TUTTI i selettori verificati**
- [ ] Playwright `--start-maximized` + `viewport: null` verificato
- [ ] FFmpeg raggiungibile
- [ ] Spazio disco sufficiente per clip webm (~1-3 MB per scena)

---

## 10. Catalogo Video Pianificati

| # | Slug | Durata | Scopo | Stato |
|---|------|--------|-------|-------|
| 0 | `primi-10-minuti` | 78s | Panoramica generale (gia' in /guida) | COMPLETATO |
| 1 | `01-primo-cliente` | ~60s | Crea cliente + contratto + anamnesi | IN PRODUZIONE |
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
| Script montaggio | `tools/scripts/video-<slug>-montaggio.js` | `tools/scripts/video-01-montaggio.js` |
| Script test | `tools/scripts/video-test-*.js` | `tools/scripts/video-test-full-flow.js` |
| Directory assets | `data/videos/<slug>/` | `data/videos/01-primo-cliente/` |
| Output finale | `data/videos/<slug>/<slug>.mp4` | `data/videos/01-primo-cliente/primo-cliente.mp4` |

# VIDEO_PRODUCTION.md — Format e Pipeline Video FitManager

Documento di processo per la produzione di tutti i video promozionali,
demo e esplicativi di FitManager Studio+.

**Principio fondante**: lo script è il master, il video è un derivato.
Cambia una feature → ri-registri solo quella scena → ri-assembli in 1 comando.

---

## 1. Filosofia: Audio-First Production

```
SBAGLIATO (video-first):  registra UI → spera che la voce ci stia sopra
GIUSTO (audio-first):     scrivi script → genera voce → registra UI sulla durata della voce
```

L'audio detta il ritmo. Il video si taglia e si adatta all'audio, mai il contrario.
Questo elimina qualsiasi disallineamento voce/video.

---

## 2. Pipeline in 5 Fasi

```
┌─────────────────────────────────────────────────────────┐
│  FASE 1 — SCRIPT EDITORIALE                            │
│  Input:  idea / feature da mostrare                     │
│  Output: script AV a 2 colonne (docs/videos/NOME.md)   │
│  Chi:    umano + Claude                                 │
├─────────────────────────────────────────────────────────┤
│  FASE 2 — ASSET AUDIO                                  │
│  Input:  script approvato                               │
│  Output: voiceover per scena + voiceover completo       │
│  Tool:   edge-tts (DiegoNeural) + FFmpeg               │
├─────────────────────────────────────────────────────────┤
│  FASE 3 — ASSET VIDEO                                  │
│  Input:  durate reali audio per scena                   │
│  Output: registrazione UI scena per scena               │
│  Tool:   Playwright (headless: false, recordVideo)      │
├─────────────────────────────────────────────────────────┤
│  FASE 4 — MONTAGGIO                                    │
│  Input:  clip video + audio + title cards               │
│  Output: video finale (MP4 H.264 + AAC)                │
│  Tool:   FFmpeg (concat, sidechain, fade)               │
├─────────────────────────────────────────────────────────┤
│  FASE 5 — REVIEW & MULTI-FORMATO                       │
│  Input:  video finale                                   │
│  Output: tagli per canale (30s, 60s, full)              │
│  Chi:    umano verifica sync → Claude taglia            │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Script Editoriale — Formato AV a 2 Colonne

Ogni video ha il suo script in `docs/videos/<nome-video>.md`.
Lo script è la **Single Source of Truth** del video.

### Struttura del file script

```markdown
# Video: <titolo>
# Durata target: <secondi>s
# Formato: <tipo> (demo | explainer | social | feature-spotlight)
# Voce: <voice-id>
# Musica: <stile>

## Scena 01 — <nome scena>
| VIDEO | AUDIO |
|-------|-------|
| **Schermata**: /pagina | **VO**: "Testo voiceover." |
| **Azione**: click su X, scroll fino a Y | **Musica**: sotto, corporate ambient |
| **Transizione**: fade 0.5s | **Pausa**: 0.5s prima della prossima scena |
| **Durata stimata**: ~Xs | |

## Scena 02 — <nome scena>
...
```

### Regole dello script

| Regola | Dettaglio |
|--------|-----------|
| **150 parole = 1 minuto** | Stima affidabile per TTS DiegoNeural a rate +5% |
| **1 concetto = 1 scena** | Mai due feature nella stessa scena |
| **Max 2 frasi per scena** | Voiceover breve, lascia respirare il video |
| **Azione visibile** | Ogni scena deve mostrare UN'AZIONE chiara (click, scroll, risultato) |
| **No gergo tecnico** | Il target è il PT, non lo sviluppatore |
| **Italiano parlato** | Scrivi come parli: "Crei il contratto", non "Il contratto viene creato" |

---

## 4. Struttura Narrativa (tutti i formati)

Ogni video segue questa struttura, indipendentemente dalla durata:

```
┌─ HOOK (10-15% della durata) ────────────────────────┐
│  Il dolore / il problema del target.                 │
│  "Ogni mese perdi ore su Excel e WhatsApp..."        │
├─ SOLUZIONE (5-10%) ─────────────────────────────────┤
│  Cos'è FitManager in una frase.                      │
│  "FitManager è il gestionale pensato per te."        │
├─ DIMOSTRAZIONE (60-70%) ────────────────────────────┤
│  Flusso reale. Feature in azione.                    │
│  Ogni scena = 1 feature = 1 azione visibile.         │
├─ CTA (10-15%) ──────────────────────────────────────┤
│  Cosa fare dopo. URL. Garanzia.                      │
│  "Provalo gratis. fitmanager.studio"                 │
└──────────────────────────────────────────────────────┘
```

### Applicazione per durata

| Formato | Durata | Hook | Soluzione | Demo | CTA |
|---------|--------|------|-----------|------|-----|
| **Social clip** | 30s | 4s | 3s | 18s (2-3 scene) | 5s |
| **Homepage hero** | 60-90s | 8s | 5s | 55-65s (5-7 scene) | 7s |
| **Full demo** | 2-3min | 12s | 8s | 100-140s (8-12 scene) | 10s |
| **Feature spotlight** | 45-60s | 5s | 3s | 30-45s (3-5 scene) | 7s |

---

## 5. Specifiche Tecniche

### Video
| Parametro | Valore |
|-----------|--------|
| Risoluzione | 1440×900 (16:10, match viewport) |
| FPS | 30 |
| Codec | H.264 (libx264), preset medium, CRF 20 |
| Container | MP4 (+faststart) |
| Pixel format | yuv420p |

### Audio
| Parametro | Valore |
|-----------|--------|
| Voiceover | edge-tts, `it-IT-DiegoNeural`, rate `+5%` |
| Sample rate | 44100 Hz |
| Voiceover codec | MP3 192kbps (intermedio), AAC 192kbps (finale) |
| Musica | Generata FFmpeg (pad + bass + kick + hihat + shimmer) |
| Mix | Voce a 1.0, musica a 0.18-0.22, sidechain compress |
| Ducking | threshold=0.02, ratio=4, attack=50ms, release=300ms |

### Title Cards
| Parametro | Valore |
|-----------|--------|
| Tool | Playwright headless, screenshot 2x |
| Stile | Gradiente teal scuro, font Inter/system-ui, logo FM |
| Intro | Fade in 1s, durata = VO_intro + 1s padding |
| Outro | Fade in 0.6s, fade out 1s, durata = VO_cta + 1.5s |

---

## 6. Toolchain

```
edge-tts          → TTS Microsoft Neural (gratuito, qualità alta)
Playwright 1.58   → Registrazione UI (headless: false + recordVideo)
FFmpeg 8.1        → Encoding, montaggio, mix audio, title cards → MP4
Node.js           → Script di automazione (orchestratore)
```

Percorsi fissi (Windows):
```javascript
const FF  = "C:/Users/gvera/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1-full_build/bin/ffmpeg.exe";
const TTS = "./venv/Scripts/edge-tts.exe";
```

---

## 7. Directory Structure

```
data/videos/
├── <nome-video>/
│   ├── scenes/              # VO per scena (01_hook.mp3, 02_soluzione.mp3, ...)
│   ├── clips/               # Video clip per scena (01_hook.mp4, 02_soluzione.mp4, ...)
│   ├── cards/               # Title cards (intro.png, outro.png, .html, .mp4)
│   ├── music/               # Tracce musicali generate
│   ├── voiceover.mp3        # VO completo concatenato
│   ├── music.wav            # Mix musicale completo
│   └── <nome-video>.mp4     # OUTPUT FINALE
└── exports/
    └── <nome-video>-<formato>.mp4  # Tagli (30s, 60s, ecc.)
```

**Regola**: i file intermedi restano nella cartella del video per debug e ri-assembly.
Solo il video finale e gli export vanno referenziati per l'uso.

---

## 8. Algoritmo di Sync Audio-Video

Questo è il cuore del metodo. Garantisce sync perfetto.

```
PER OGNI scena nello script:
  1. Genera VO scena → misura DURATA REALE (FFprobe)
  2. scena.durata_video = scena.durata_vo + scena.padding (0.5-1.5s)
  3. Registra UI per ESATTAMENTE scena.durata_video secondi

MONTAGGIO:
  4. Concatena clip video:  intro_card + clip_01 + clip_02 + ... + outro_card
  5. Concatena audio VO:    silenzio(intro) + vo_01 + vo_02 + ... + vo_cta
  6. VERIFICA: durata_video_totale ≈ durata_vo_totale (tolleranza ±0.5s)
  7. Mix finale: video + VO + musica (con sidechain ducking)
```

### Registrazione scena per scena (non un unico take)

A differenza del v4 che registrava tutto in un unico take e sperava nel sync,
il metodo corretto è:

```
PER OGNI scena:
  - Apri browser context con recordVideo
  - Esegui azioni UI (navigate, click, scroll)
  - Attendi fino a durata_video esatta
  - Chiudi context → salva clip
  - Prossima scena = nuovo context
```

Vantaggi:
- Ogni clip ha durata esatta
- Se una scena fallisce, ri-registri solo quella
- Cambi l'ordine delle scene senza ri-registrare nulla

---

## 9. Voci Disponibili

| Voice ID | Genere | Note |
|----------|--------|------|
| `it-IT-DiegoNeural` | Maschile | **Default**. Professionale, caldo, amichevole |
| `it-IT-IsabellaNeural` | Femminile | Alternativa per variare |
| `it-IT-GiuseppeMultilingualNeural` | Maschile | Multilingua, tono leggermente diverso |
| `it-IT-ElsaNeural` | Femminile | Più formale |

---

## 10. Musica Generativa

La musica è generata da FFmpeg con 5 layer sintetici.
BPM: 115. Tonalità: Am (220 Hz root). Stile: corporate ambient.

| Layer | Funzione | Entra a |
|-------|----------|---------|
| Pad | Atmosfera continua, accordi Am | 0s (fade in 4s) |
| Bass | Sub-bass pulsante | 6s |
| Kick | Ritmo base | 8s |
| Hihat | Texture ritmica | 10s |
| Shimmer | Armonici alti per il finale | ultimi 18s |

Tutti i layer hanno fade out sugli ultimi 3-4 secondi.
Il volume complessivo della musica è 18-22% rispetto alla voce.

---

## 11. Multi-Formato da Unico Girato

Dopo aver prodotto il video full, i tagli sono meccanici:

```bash
# 30s social (hook + 2 scene migliori + cta)
ffmpeg -i full.mp4 -filter_complex "..." -t 30 export-30s.mp4

# 60s homepage (hook + 4-5 scene + cta)
ffmpeg -i full.mp4 -filter_complex "..." -t 60 export-60s.mp4
```

Lo script editoriale deve indicare quali scene sono **core** (vanno in tutti i formati)
e quali sono **extended** (solo nel full).

Notazione nello script:
```
## Scena 03 — Cassa [CORE]        ← va in tutti i formati
## Scena 06 — Esercizio [EXTENDED] ← solo nel full demo
```

---

## 12. Checklist Pre-Produzione

Prima di avviare lo script di automazione:

- [ ] Backend dev in esecuzione (porta 8001)
- [ ] Frontend dev in esecuzione (porta 3001)
- [ ] Dati demo puliti (o script crea i propri dati via API)
- [ ] Script editoriale approvato (`docs/videos/<nome>.md`)
- [ ] `npm list playwright` OK
- [ ] FFmpeg raggiungibile
- [ ] edge-tts raggiungibile

---

## 13. Naming Convention

| Tipo | Pattern | Esempio |
|------|---------|---------|
| Script editoriale | `docs/videos/<slug>.md` | `docs/videos/primi-10-minuti.md` |
| Script automazione | `tools/scripts/video-<slug>.js` | `tools/scripts/video-primi-10-minuti.js` |
| Directory assets | `data/videos/<slug>/` | `data/videos/primi-10-minuti/` |
| Output finale | `data/videos/<slug>/<slug>.mp4` | `data/videos/primi-10-minuti/primi-10-minuti.mp4` |
| Export formato | `data/videos/exports/<slug>-<formato>.mp4` | `data/videos/exports/primi-10-minuti-60s.mp4` |

---

## 14. Catalogo Video Pianificati

| # | Slug | Tipo | Durata | Scopo | Stato |
|---|------|------|--------|-------|-------|
| 1 | `primi-10-minuti` | full demo | 90s | Homepage hero + YouTube | DA FARE |
| 2 | `feature-safety-engine` | feature spotlight | 45s | Pagina feature | DA FARE |
| 3 | `feature-nutrizione` | feature spotlight | 45s | Pagina feature | DA FARE |
| 4 | `social-hook-excel` | social clip | 30s | Instagram/TikTok | DA FARE |

---

## 15. Errori da Non Ripetere

| Errore | Lezione | Soluzione |
|--------|---------|-----------|
| Video-first production | Audio e video disallineati alla fine | **Audio-first**: genera VO, poi registra UI sulla sua durata |
| Unico take per tutto il video | Una scena sbagliata = ri-registrare tutto | **Scena per scena**: ogni scena = un clip indipendente |
| `waitForTimeout(vo.duration * 1000)` | Timing approssimativo, drift cumulativo | **FFprobe** per durata reale, padding esplicito |
| 5 iterazioni di script nello stesso file | 274MB di file intermedi, confusione | **1 script = 1 file**, naming convention rigorosa |
| Title card outro troppo corto | Schermata uscita visibile con voce ancora attiva | **Outro durata = VO_cta + 1.5s padding** |

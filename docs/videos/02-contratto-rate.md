# Video 02: Contratto e Rate — Il Rinnovo
# Durata target: ~50s (feature spotlight — guida in-app)
# Formato: feature spotlight
# Voce: ElevenLabs Daniel (onwK4e9ZLuTAKqWW03F9), eleven_multilingual_v2
# Musica: acoustic calm (ElevenLabs SFX) — riusa da video 01
# Risoluzione: 1440×900 (registrazione maximized)

---

## Metodo di produzione

```
1. SCRIPT (questo file)     → master, ogni secondo mappato
2. AUDIO (ElevenLabs)       → VO per scena, durata reale misurata
3. VIDEO (Playwright)       → azioni reali, flusso continuo, un solo clip
4. TRIM (FFmpeg)            → taglia bianchi caricamento, allinea a durata VO
5. MONTAGGIO (montage.js)   → VO sincronizzato + musica, mode=continuous
```

Regola fondamentale: **il VO detta il ritmo, il video si adatta**.

---

## Contesto narrativo

Questo video e' il sequel naturale di "Il Primo Cliente" (video 01).
Luca Moretti ha completato il suo primo mese. Il contratto di marzo e' in scadenza.
Il trainer rinnova dalle notifiche con un click — stesse condizioni, nuovo mese.

**Dati di partenza** (creati dal setup script `video-02-setup.py`):
- Cliente: Luca Moretti (gia' esistente dal video 01)
- Contratto: "Mensile 4 Sedute", 4 crediti, €300, 01/03-31/03/2026
- 2 rate SALDATE: €150 il 15/03 (BONIFICO), €150 il 22/03 (BONIFICO)
- Stato: SALDATO, chiuso=false (crediti non esauriti → visibile in rinnovi)
- Il contratto appare in /rinnovi-incassi con badge "Scade tra 5g"

**Azioni nel video** (Playwright):
1. Naviga a /rinnovi-incassi → vede card Moretti
2. Click "Rinnova" → Sheet pre-compilata
3. Compila date 01/04 e 30/04 → "Rinnova Contratto"
4. Naviga al dettaglio del nuovo contratto
5. Mostra catena di rinnovo + hero finanziario

**Nessun dato pre-generato via API durante la registrazione.**
Il rinnovo avviene via UI reale. Solo il contratto di partenza e' seedato.

---

## SCENA 01 — Hook: il contratto scade (VO: ~7s)

### VO (testo esatto)
"Il mese di Luca si chiude. Dalla pagina Rinnovi vedi subito chi sta per scadere — e rinnovi senza perdere un dato."

### Conteggio parole: 23 → ~9s a 150 wpm. Target reale: ~7s (Daniel e' veloce).

### Timeline video

| Secondo | Azione video | Sync con VO |
|---------|-------------|-------------|
| 0.0-1.5 | Pagina /rinnovi-incassi caricata. KPI visibili: "Da rinnovare", "Rate in ritardo", "Da incassare" | "Il mese di Luca si chiude." |
| 1.5-4.0 | Statica — il viewer legge le KPI e individua la card di Moretti | "Dalla pagina Rinnovi vedi subito chi sta per scadere" |
| 4.0-5.5 | Hover naturale sulla card Moretti (badge ambra "Scade tra 5g", barra crediti, €300) | "— e rinnovi" |
| 5.5-7.0 | Statica sulla card | "senza perdere un dato." |

### Registrazione Playwright
```
goto /rinnovi-incassi
waitFor p:has-text("Da rinnovare") [timeout 10s]
wait(500) — pagina stabile
// Nessuna azione click — solo visualizzazione
voLock(durata 01_hook)
```

### Trim: si — la prima navigazione ha 1-2s di caricamento bianco. Misurare trim_start.

### Selettori verificati (pre-flight 22/22)
- Page ready: `p:has-text("Da rinnovare")`
- Card Moretti: `div.rounded-xl` filter `hasText: "Luca Moretti"`
- Badge: card contiene "Scade tra 5g"

---

## SCENA 02 — Rinnova con un click (VO: ~9s)

### VO (testo esatto)
"Un click su Rinnova. Il sistema propone le stesse condizioni: pacchetto, crediti, prezzo. Tu scegli solo le nuove date."

### Conteggio parole: 22 → ~9s.

### Timeline video

| Secondo | Azione video | Sync con VO |
|---------|-------------|-------------|
| 0.0-1.5 | Click "Rinnova" nella card Moretti → Sheet si apre con animazione slide-in | "Un click su Rinnova." |
| 1.5-3.5 | Sheet visibile: titolo "Rinnova Contratto", form pre-compilato. Il viewer legge i campi: Cliente (locked), "Mensile 4 Sedute", 4 crediti, €300 | "Il sistema propone le stesse condizioni:" |
| 3.5-5.5 | Pausa sui campi pre-compilati — il viewer nota che Cliente e' disabilitato (grigio) | "pacchetto, crediti, prezzo." |
| 5.5-7.0 | Scroll lento nella sheet verso i DatePicker vuoti (Inizio... / Scadenza...) | "Tu scegli solo" |
| 7.0-9.0 | I due DatePicker vuoti sono in vista, pronti per l'input | "le nuove date." |

### Registrazione Playwright
```
// Click Rinnova nella card Moretti (scoped al card container)
morettiCard.locator('button:has-text("Rinnova")').click()
wait(600) — sheet animation
waitFor text=Rinnova Contratto [timeout 5s]

// Pausa per leggere i campi pre-compilati
wait(2000)

// Scroll sheet ai campi data
page.evaluate(() => {
  const s = document.querySelector('[data-slot="sheet-content"]');
  if (s) s.scrollTo({ top: 200, behavior: "smooth" });
})
wait(1000)

voLock(durata 02_rinnova)
```

### Selettori verificati
- Card Moretti scoped: `div.rounded-xl` filter `hasText: "Luca Moretti"`
- Bottone Rinnova in card: card `.locator('button:has-text("Rinnova")')`
- Sheet title: `text=Rinnova Contratto`
- Campo tipo_pacchetto: `#tipo_pacchetto` (valore "Mensile 4 Sedute")
- Campo crediti: `#crediti_totali` (valore "4")
- Campo prezzo: `#prezzo_totale` (valore "300")

---

## SCENA 03 — Compila date e conferma (VO: ~8s)

### VO (testo esatto)
"Primo aprile, trenta aprile. Confermi — e il nuovo contratto e' attivo. La ricevuta di rinnovo e' nel Libro Mastro."

### Conteggio parole: 21 → ~8s.

### Timeline video

| Secondo | Azione video | Sync con VO |
|---------|-------------|-------------|
| 0.0-1.5 | Click DatePicker "Inizio..." → calendario si apre → naviga ad Aprile → click 01 | "Primo aprile," |
| 1.5-3.0 | Click DatePicker "Scadenza..." → calendario si apre → click 30 (stesso mese) | "trenta aprile." |
| 3.0-4.5 | Scroll sheet al bottone submit. Click "Rinnova Contratto" | "Confermi —" |
| 4.5-6.0 | Toast "Contratto rinnovato" appare. Sheet si chiude con animazione | "e il nuovo contratto e' attivo." |
| 6.0-8.0 | Siamo su /rinnovi-incassi. La card Moretti e' sparita (query invalidata). Le KPI si aggiornano | "La ricevuta di rinnovo e' nel Libro Mastro." |

### Registrazione Playwright
```
// Seleziona Data Inizio: 01/04/2026
selectDate(page, "Inizio...", "01/04/2026")
wait(300)

// Seleziona Data Scadenza: 30/04/2026
selectDate(page, "Scadenza...", "30/04/2026")
wait(300)

// Scroll al submit
page.evaluate(() => {
  const s = document.querySelector('[data-slot="sheet-content"]');
  if (s) s.scrollTo({ top: s.scrollHeight, behavior: "smooth" });
})
wait(500)

// Submit
page.locator('button:has-text("Rinnova Contratto")').click()
wait(2000) — API + toast + sheet close

voLock(durata 03_conferma)
```

### Rischi anticipati e mitigati
| Rischio | Mitigazione | Verificato in pre-flight |
|---------|-------------|------------------------|
| DatePicker mostra Marzo, 01/04 nel mese successivo | `selectDate()` con `rdp-button_next` naviga avanti | SI — funziona |
| 30/04 nello stesso mese di 01/04 | Dopo aver selezionato inizio (Aprile), scadenza mostra Aprile → 30 visibile | SI — nessuna navigazione mese necessaria |
| Bottone submit disabled | Date compilate prima del click → enabled | SI |
| Sheet non scrolla al submit | `scrollTo` esplicito | SI |

### Selettori verificati
- DatePicker inizio: `button:has-text("Inizio...")`
- DatePicker scadenza: `button:has-text("Scadenza...")`
- Data-day format: `DD/MM/YYYY` (es. `button[data-day="01/04/2026"]`)
- Navigation mese: `button.rdp-button_next`
- Submit: `button:has-text("Rinnova Contratto")`
- Toast: `text=Contratto rinnovato`

---

## SCENA 04 — La catena di rinnovo (VO: ~10s)

### VO (testo esatto)
"Apriamo il nuovo contratto. In alto, la catena di rinnovo: dal contratto originale a quello di aprile. La storia del cliente resta collegata, mese dopo mese."

### Conteggio parole: 28 → ~11s. Target reale: ~10s.

### Timeline video

| Secondo | Azione video | Sync con VO |
|---------|-------------|-------------|
| 0.0-2.0 | Navigazione a /contratti/[newId]. Header carica: "Mensile 4 Sedute" con badge "Attivo" | "Apriamo il nuovo contratto." |
| 2.0-4.5 | Scroll alla sezione catena rinnovi. Due badge collegati con freccia: [Marzo] → [Aprile ← attuale] | "In alto, la catena di rinnovo:" |
| 4.5-6.5 | Pausa sulla catena — il viewer legge i badge e la freccia | "dal contratto originale a quello di aprile." |
| 6.5-8.5 | Scroll al hero finanziario. KPI visibili: Valore €300, Versato €0, Residuo €300, barra progresso a 0% | "La storia del cliente resta collegata," |
| 8.5-10.0 | Statica sull'hero — numeri puliti, tutto a zero, pronto per il nuovo ciclo | "mese dopo mese." |

### Registrazione Playwright
```
// Trova nuovo contratto via API backend diretto
const newContractId = await findNewContract(page, token);

// Naviga al dettaglio
page.goto(BASE_URL + "/contratti/" + newContractId)
waitForSelector [data-guide="contratto-header"] [timeout 10s]
wait(1000)

// Scroll alla catena rinnovi
page.locator('[data-guide="contratto-catena-rinnovi"]').scrollIntoViewIfNeeded()
wait(2000) — pausa per leggere la catena

// Scroll al hero finanziario
page.locator('[data-guide="contratto-hero-finanziario"]').scrollIntoViewIfNeeded()
wait(2000)

voLock(durata 04_catena)
```

### Logica `findNewContract()`
```javascript
async function findNewContract(page, token) {
  return page.evaluate(async (tkn) => {
    const r = await fetch("http://localhost:8001/api/contracts?page_size=200", {
      headers: { Authorization: "Bearer " + tkn },
    });
    const data = await r.json();
    const c = data.items?.find(
      (x) => x.data_inizio === "2026-04-01"
          && x.tipo_pacchetto === "Mensile 4 Sedute"
          && x.rinnovo_di
    );
    return c?.id;
  }, token);
}
```

### Selettori verificati
- Header contratto: `[data-guide="contratto-header"]`
- Catena rinnovi: `[data-guide="contratto-catena-rinnovi"]`
- Hero finanziario: `[data-guide="contratto-hero-finanziario"]`

---

## SCENA 05 — CTA (VO: ~5s)

### VO (testo esatto)
"Rinnovi, catena, finanze. Tutto sotto controllo, tutto in un posto."

### Conteggio parole: 11 → ~5s.

### Timeline video

| Secondo | Azione video | Sync con VO |
|---------|-------------|-------------|
| 0.0-5.0 | Title card: gradiente teal, testo "Contratto e Rate — Fatto." | VO completo |
| 5.0-7.0 | Title card resta visibile (silenzio + musica fade out) | Respiro finale |

### Registrazione: title card HTML → screenshot → video statico FFmpeg

### Note sulla title card
Stessa estetica del video 01: gradiente teal → indigo, font Inter 700, testo centrato.
Generata come immagine PNG 1440×900 e convertita in clip statico con FFmpeg:
```
ffmpeg -loop 1 -i cards/outro.png -t 7 -c:v libx264 -pix_fmt yuv420p cards/outro.mp4
```

---

## Riepilogo timing (stima pre-VO)

| # | Scena | VO stimato | Gap | Clip target |
|---|-------|-----------|-----|------------|
| 01 | Hook — rinnovi-incassi | ~7s | 0.5s | ~7.5s |
| 02 | Click Rinnova → Sheet | ~9s | 0.5s | ~9.5s |
| 03 | Date + conferma | ~8s | 0.5s | ~8.5s |
| 04 | Catena + hero | ~10s | 0.5s | ~10.5s |
| 05 | CTA | ~5s | 2.0s | ~7.0s |
| | **TOTALE** | **~39s** | | **~43s** |

Durata finale stimata: **~43-48s** (con trim iniziale + musica fade).
Piu' compatto del video 01 (69s) — flusso lineare, nessun wizard multi-step.

---

## Manifest iniziale (struttura scene)

```json
{
  "video": {
    "slug": "02-contratto-rate",
    "title": "Contratto e Rate — Il Rinnovo",
    "resolution": [1440, 900],
    "fps": 30,
    "codec": { "video": "libx264", "crf": 20, "audio": "aac", "audio_bitrate": "192k" },
    "crossfade_duration": 0.4,
    "music": {
      "file": "music/background.mp3",
      "volume": 0.10,
      "fade_in": 2.0,
      "fade_out": 3.0
    },
    "output": "contratto-rate.mp4"
  },
  "scenes": [
    {
      "name": "01_hook",
      "vo": { "file": "scenes/01_hook.mp3", "text": "Il mese di Luca si chiude. Dalla pagina Rinnovi vedi subito chi sta per scadere — e rinnovi senza perdere un dato." },
      "gap": 0.5,
      "recording": { "page_ready_selector": "p:has-text('Da rinnovare')" }
    },
    {
      "name": "02_rinnova",
      "vo": { "file": "scenes/02_rinnova.mp3", "text": "Un click su Rinnova. Il sistema propone le stesse condizioni: pacchetto, crediti, prezzo. Tu scegli solo le nuove date." },
      "gap": 0.5,
      "recording": {}
    },
    {
      "name": "03_conferma",
      "vo": { "file": "scenes/03_conferma.mp3", "text": "Primo aprile, trenta aprile. Confermi — e il nuovo contratto e' attivo. La ricevuta di rinnovo e' nel Libro Mastro." },
      "gap": 0.5,
      "recording": {}
    },
    {
      "name": "04_catena",
      "vo": { "file": "scenes/04_catena.mp3", "text": "Apriamo il nuovo contratto. In alto, la catena di rinnovo: dal contratto originale a quello di aprile. La storia del cliente resta collegata, mese dopo mese." },
      "gap": 0.5,
      "recording": {}
    },
    {
      "name": "05_cta",
      "vo": { "file": "scenes/05_cta.mp3", "text": "Rinnovi, catena, finanze. Tutto sotto controllo, tutto in un posto." },
      "gap": 2.0,
      "recording": {}
    }
  ],
  "recording_mode": "continuous",
  "recording_crop_bottom": 120,
  "recording_pad_color": "0xf0f4f8"
}
```

---

## Flusso navigazione REALE (verificato pre-flight 22/22)

```
/rinnovi-incassi                    → card Moretti visibile ("Scade tra 5g")
Card Moretti → click "Rinnova"      → Sheet "Rinnova Contratto" si apre (inline, stessa pagina)
                                      ⚠ NON naviga — sheet overlay sulla pagina /rinnovi-incassi
Sheet → fill date → submit          → sheet si chiude → restiamo su /rinnovi-incassi
                                      ⚠ La card Moretti SPARISCE (query invalidata)
                                      ⚠ NON c'e' redirect al nuovo contratto — serve navigazione esplicita
/rinnovi-incassi                    → API /contracts per trovare newContractId
                                      ⚠ URL backend diretto (http://localhost:8001/api/contracts)
                                      ⚠ MAI proxy Next.js per API call nel browser evaluate
goto /contratti/[newContractId]     → header + catena rinnovi + hero finanziario
```

---

## Errori anticipati (da VIDEO_PRODUCTION.md §8)

| # | Trappola | Come la evitiamo |
|---|----------|-------------------|
| 1 | Card Moretti non e' la prima — click "Rinnova" sbagliato | Card scoped: `div.rounded-xl` filter `hasText: "Luca Moretti"` → click Rinnova DENTRO la card |
| 2 | API nel browser via proxy Next.js | URL backend diretto: `http://localhost:8001/api/contracts` con Bearer token |
| 3 | DatePicker mostra Marzo | `selectDate()` con `rdp-button_next` — collaudato |
| 4 | Sheet non scrolla al submit | `scrollTo` esplicito prima del click |
| 5 | Taskbar Windows nel video | `crop` + `pad` nel manifest (stessi parametri video 01) |
| 6 | Flash bianco prima navigazione | `trim_start` misurato al recording, non stimato |
| 7 | VO overlap fra scene consecutive | Anti-overlap: `max(scene_start, prevVoEnd)` nel montaggio |

---

## Checklist pre-registrazione

- [ ] Backend dev running su porta 8001
- [ ] Frontend dev running su porta 3001
- [ ] `python tools/scripts/video-02-setup.py` eseguito (contratto seedato)
- [ ] Verifica in browser: /rinnovi-incassi mostra card Moretti
- [ ] Pre-flight passato: `node tools/scripts/video-02-preflight.js` → 22/22
- [ ] VO generati in `data/videos/02-contratto-rate/scenes/`
- [ ] Musica copiata (riusa da video 01 o genera nuova) in `music/`
- [ ] `manifest-sync.js` eseguito → durate VO reali nel manifest
- [ ] FFmpeg + FFprobe raggiungibili
- [ ] Title card outro generata in `cards/`

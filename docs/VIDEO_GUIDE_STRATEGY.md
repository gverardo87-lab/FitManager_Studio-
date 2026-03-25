# VIDEO_GUIDE_STRATEGY.md — Sistema Video-Guide Contestuali

Documento guida per l'integrazione dei video-guida nell'interfaccia.
Regole, gerarchie e punti di accesso per tutti i video.

**Principio**: l'utente non deve cercare l'aiuto — l'aiuto deve essere dove serve, mai invadente.

---

## 1. Gerarchia a 4 livelli

| Livello | Nome | Dove | Trigger | Componente |
|---------|------|------|---------|------------|
| **L1** | Hub | `/guida` | Navigazione menu | `VideoGuideCard` — catalogo completo con thumbnail, durata, player inline |
| **L2** | Contestuale | Header pagine operative | Click icona `CirclePlay` | `VideoGuidePopover` — popover con player + bottone fullscreen |
| **L3** | Bussola | SpotlightTour (19 step) | Click "Guarda il video" dentro lo step del tour | Link "Guarda il video" nello step → apre popover o naviga a `/guida#id` |
| **L4** | Command Palette | Ctrl+K | Cerca "video", "guida", "come fare" | Gruppo "Video Guide" con icona Play |

Ogni livello e' un punto di accesso DIVERSO allo stesso video. Il video e' UNO, i punti di accesso sono 4.

---

## 2. L1 — Hub `/guida`

Gia' implementato. Griglia card con tutti i video disponibili.
Solo video con `ready: true` appaiono. Nessun placeholder "Coming soon".

---

## 3. L2 — Contestuale (Header pagina)

### Posizionamento

L'icona video appare **nel header della pagina**, a sinistra del bottone azione primaria.
Posizione fissa, prevedibile, identica su ogni pagina.

```
┌──────────────────────────────────────────────────────┐
│  👤 Clienti                  [▶ Guida]  [+ Nuovo Cliente]  │
│  35 clienti nel tuo portafoglio                             │
└──────────────────────────────────────────────────────┘
```

### Comportamento

1. **Icona**: `CirclePlay` (lucide), `text-muted-foreground`, hover → `text-primary`, transizione
2. **Click icona** → popover si apre con:
   - Player video inline (piccolo, ~400px wide)
   - Titolo + durata
   - Bottone "Apri nella Guida" → naviga a `/guida#id` (video a pieno schermo)
3. **Solo video pronti** (`ready: true`): se il video della pagina non e' pronto, l'icona NON appare
4. **UN solo video per pagina**: il mapping e' in `video-guides.ts` campo `pages[]`

### Trigger aggiuntivo: Empty State

Quando una sezione e' vuota (0 clienti, 0 contratti, etc), l'empty state include il video come CTA secondaria:

```
┌──────────────────────────────────────┐
│         👤                           │
│    Nessun cliente ancora             │
│    Inizia creando il tuo primo       │
│    cliente dal bottone in alto.      │
│                                      │
│    [▶ Guarda come fare (1:26)]       │
│                                      │
│         [+ Nuovo Cliente]            │
└──────────────────────────────────────┘
```

Regola: video SOTTO il testo esplicativo, SOPRA il bottone azione. Mai il contrario.

---

## 4. L3 — Bussola (SpotlightTour)

Il tour ha 19 step organizzati in sezioni (Dashboard, Clienti, Contratti, Agenda, Cassa, Esercizi, Schede, Monitoraggio, Impostazioni, Ricerca).

Ogni step del tour che ha un video collegato mostra un link "Guarda il video" in fondo alla descrizione.

### Mapping Tour Step → Video

| Sezione Tour | Step target | Video collegato | ID video |
|-------------|-------------|-----------------|----------|
| Dashboard | `dashboard-header` | I Primi 10 Minuti | `panoramica` |
| Clienti | `clienti-header` | Il Primo Cliente | `primo-cliente` |
| Clienti | `clienti-new-button` | Il Primo Cliente | `primo-cliente` |
| Contratti | `contratti-header` | Contratto e Rate | `contratto-rate` |
| Contratti | `contratti-new-button` | Contratto e Rate | `contratto-rate` |
| Agenda | `agenda-header` | Agenda e Sessioni | `agenda` |
| Cassa | `cassa-header` | Cassa e Finanze | `cassa` |
| Esercizi | `esercizi-header` | Esercizi e Scudo Clinico | `esercizi-safety` |
| Schede | `schede-header` | Scheda Allenamento | `scheda-allenamento` |
| Impostazioni | `impostazioni-header` | Backup e Protezione Dati | `backup-dati` |

### Comportamento

- Il link "Guarda il video" appare SOLO se il video e' `ready: true`
- Click → apre `VideoGuidePopover` (stesso componente di L2) posizionato vicino allo step
- Alternativa: naviga a `/guida#id` chiudendo il tour (con conferma "Vuoi uscire dal tour?")
- Il tour NON si interrompe per il video: il popover si apre sopra, l'utente chiude e continua

### Implementazione

Aggiungere campo `videoId?: string` al tipo `TourStep` in `guide-tours.ts`:

```typescript
export interface TourStep {
  target: string;
  title: string;
  description: string;
  placement: "top" | "bottom" | "left" | "right";
  desktopOnly?: boolean;
  navigateTo?: string;
  videoId?: string;  // ← NUOVO: collegamento a VIDEO_GUIDES
}
```

Il componente `SpotlightTour` renderizza il link video in fondo allo step se `videoId` e' presente e il video e' `ready`.

---

## 5. L4 — Command Palette (Ctrl+K)

Nuovo gruppo "Video Guide" nella palette. Appare cercando "video", "guida", "come fare", o il nome della funzione (es. "clienti" mostra anche il video collegato).

```
  🎬 Video Guide
  ▶ I Primi 10 Minuti                    1:18
  ▶ Il Primo Cliente                     1:26
```

### Comportamento

- Solo video con `ready: true`
- Click → naviga a `/guida` con scroll automatico al video (`/guida#id`)
- Keywords: titolo video + pagine associate (es. "clienti" matcha "Il Primo Cliente")
- Icona: `CirclePlay` per ogni risultato
- Preview panel (desktop): mostra thumbnail + descrizione + durata

---

## 6. Mappa video → pagine

Fonte unica: `frontend/src/lib/video-guides.ts` campo `pages[]`.

| Video | ID | Pagine L2 (header) | Tour step L3 | Pronto |
|-------|----|--------------------|-------------|--------|
| I Primi 10 Minuti | `panoramica` | Dashboard (solo < 3 clienti) | `dashboard-header` | SI |
| Il Primo Cliente | `primo-cliente` | `/clienti` | `clienti-header`, `clienti-new-button` | SI (v1) |
| Contratto e Rate | `contratto-rate` | `/contratti`, `/contratti/[id]` | `contratti-header`, `contratti-new-button` | NO |
| Agenda e Sessioni | `agenda` | `/agenda` | `agenda-header` | NO |
| Cassa e Finanze | `cassa` | `/cassa` | `cassa-header` | NO |
| Esercizi e Scudo Clinico | `esercizi-safety` | `/esercizi` | `esercizi-header` | NO |
| Scheda Allenamento | `scheda-allenamento` | `/schede` | `schede-header` | NO |
| Misurazioni e Progressi | `misurazioni-progressi` | `/clienti/[id]` (tab) | — | NO |
| Piano Alimentare LARN | `piano-alimentare` | — | — | NO |
| Backup e Protezione Dati | `backup-dati` | `/impostazioni` | `impostazioni-header` | NO |

---

## 7. Regole NON negoziabili

### Posizionamento
1. **UN solo punto di ingresso video per pagina** — mai 2 icone video nella stessa vista
2. **Posizione fissa nell'header** — a sinistra del bottone azione primaria
3. **Mai video su singoli bottoni/campi** — troppo rumore, genera confusione

### Comportamento
4. **Mai auto-play** — l'utente clicca quando vuole
5. **Mai popup automatico** — nessun "Hai visto il video?" non richiesto
6. **Mai badge/contatore "3 video non visti"** — genera ansia
7. **Mai video obbligatorio** prima di usare una funzione
8. **Mai placeholder "Coming soon"** — se non e' pronto, non esiste

### Video
9. **Popover come default** — click icona apre player inline piccolo
10. **Fullscreen come opzione** — bottone "Apri nella Guida" naviga a `/guida#id`
11. **Un video, piu' punti di accesso** — il contenuto e' unico, i trigger sono 4 (hub, header, bussola, palette)
12. **Solo video `ready: true` sono visibili** — a qualsiasi livello

### Design
13. **Icona `CirclePlay`** — neutra (`text-muted-foreground`), hover → `text-primary`
14. **Zero animazioni sull'icona** — no pulse, no bounce, no glow
15. **Testo "Guida" accanto all'icona** nell'header (non solo icona senza label)
16. **Stile coerente** con il resto dell'UI — `shadcn/ui`, nessun componente custom esotico

---

## 8. Priorita' implementazione

1. **L2 — Header contestuale** con `VideoGuidePopover` (impatto immediato, visibile su ogni pagina)
2. **L3 — Bussola** con `videoId` nei tour step (espansione naturale del tour esistente)
3. **L4 — Command Palette** gruppo video (minimo sforzo, alto valore per power user)
4. **Empty state** con video CTA (richiede modifica per-pagina, fare dopo)

---

## 9. File coinvolti

| File | Modifica |
|------|----------|
| `frontend/src/lib/video-guides.ts` | Aggiornare `ready`, `pages[]`, `durationSec` |
| `frontend/src/lib/guide-tours.ts` | Aggiungere `videoId` ai `TourStep` rilevanti |
| `frontend/src/components/guide/VideoGuidePopover.tsx` | Componente popover con player + bottone fullscreen |
| `frontend/src/components/layout/CommandPalette.tsx` | Aggiungere gruppo "Video Guide" |
| Pagine header (`clienti`, `contratti`, etc.) | Aggiungere icona `CirclePlay` + `VideoGuidePopover` |
| `frontend/src/components/guide/SpotlightTour.tsx` | Renderizzare link video negli step con `videoId` |

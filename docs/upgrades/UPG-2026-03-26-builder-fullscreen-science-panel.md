# UPG-2026-03-26 — Builder Full-Screen con Science Panel

> ADR: ADR-008
> Branch: fit_launch_01
> Commit range: 866d492..10bfc11 (12 commit)
> Stato: completato

## Problema

I motori scientifici (Safety Engine, Training Science, Copertura Muscolare, Equilibrio Biomeccanico) erano invisibili nel workflow quotidiano del trainer. Richiedevano 4 click per essere consultati (builder → espandi SafetyCard → tab "Analisi" → espandi sezioni). La prima utilizzatrice reale non li consultava mai.

Il builder occupava lo spazio di una pagina standard (sidebar + padding) con header da 4 righe (~200px), session card limitate a 460px max, e ogni esercizio consumava ~100px verticali. Una sessione tipica (11 esercizi) richiedeva 2 scrollate complete.

## Soluzione

### Architettura UX (ADR-008)

Il builder entra in "builder mode": la sidebar scompare, lo spazio intero viene usato dal workspace. Il Flask toggle nell'header controlla la visibilita' del Science Panel a destra.

```
┌──────────────────────────────────────────────────────────────────┐
│ ← Nome Scheda — Cliente  ✎   │ [Analisi ON] [Salva]            │ header sticky
│ [Cliente ▾] Profilo [Obiettivo] [Livello]  │ Export buttons     │ 2 righe, ~80px
├───────────────────────────────────┬──────────────────────────────┤
│ ┌──────────────┐ ┌─────────────┐ │  ◐ Score ring (0-100)       │
│ │ Sessione 1   │ │ Sessione 2  │ │  V ████░░░ E ██░░░          │
│ │ ⓘ ⚠ Nome ex  │ │ ⓘ Nome ex   │ │  F ░░░░░░ R █████          │
│ │   [3] [8-12] │ │   [3] [15]  │ │  🛡 Safety (N condizioni)  │
│ │ ⓘ Nome ex    │ │ ⓘ ⚠ Nome ex │ │  [Mappa anatomica]         │
│ │   [S] [Rip]  │ │   [S][R][K] │ │  [anteriore] [posteriore]  │
│ └──────────────┘ └─────────────┘ │  ⚖ Equilibrio (N rapporti) │
│ [+ Sessione]                     │  ⚡ Azioni (N warnings)     │
├───────────────────────────────────┴──────────────────────────────┤
│  ⟲ ⟳  Modifiche non salvate · Ctrl+S                   [Salva]  │
└──────────────────────────────────────────────────────────────────┘
```

### Componenti creati/modificati

| File | Azione | Descrizione |
|------|--------|-------------|
| `src/lib/builder-mode.tsx` | **Nuovo** | Context che segnala al layout di nascondere la sidebar |
| `src/components/workouts/SciencePanel.tsx` | **Nuovo** | Pannello laterale 320px con Score Ring, barre sub-score, Safety, Mappa Anatomica, Equilibrio, Azioni. Live debounce 1s. |
| `src/app/(dashboard)/layout.tsx` | **Modificato** | DashboardShell consuma BuilderModeContext, sidebar condizionale, padding ridotto in builder mode |
| `src/app/(dashboard)/schede/[id]/page.tsx` | **Modificato** | Layout 2 colonne (sessioni + panel), griglia max 2 col, Flask toggle controlla panel |
| `src/components/workouts/BuilderHeader.tsx` | **Riscritto** | Da 4 righe (200px) a 2 righe compatte sticky (~80px). Row 1: nome + Flask + save. Row 2: client + metadata + export. |
| `src/components/workouts/SortableExerciseRow.tsx` | **Riscritto (boardView)** | Da 2 righe stacked (~100px/esercizio) a 1 riga griglia (~36px). Grip overlay su hover, info+safety inline col nome. |
| `src/components/workouts/SessionCard.tsx` | **Modificato** | Column header allineato alla nuova griglia. Visibile in boardView. |

### Linee guida del layout builder (consolidate)

#### Griglia esercizi (boardView)

```
Griglia: [nome_con_icone 1fr] [S 44px] [Rip 52px] [Kg 48px] [Rec 44px] [del 24px]
         (avviamento/stretching omettono Kg e Rec)

- Grip: overlay absolute -left-1, visibile solo su hover (group-hover/row)
- Info: icona inline h-5 w-5, prima del nome, nella cella 1fr
- Safety: icona inline dopo info, prima del nome (se presente)
- Nome: break-words + leading-snug (va a capo, mai troncato)
- Input: h-7, text-xs, tabular-nums, text-center
- Delete: visibile solo su hover, hover:bg-destructive/10
- aria-label su tutti i bottoni icon-only e input
```

#### Session card (boardView)

```
- Griglia: grid-cols-1 lg:grid-cols-2 (sempre 2 col su desktop)
- Nessun max-width (le card crescono nello spazio)
- Nessun overflow-x-auto (no scroll orizzontale)
- Column header (S, Rip, Kg, Rec) visibile per ogni sezione
- Bottone "+ Sessione" inline nella griglia
```

#### Header

```
- Sticky top-0 z-30, blur backdrop
- Row 1: [← back] [Nome — Cliente ✎] [spacer] [Flask toggle] [Save]
- Row 2: [Cliente ▾] [Profilo link] [| sep] [Obiettivo badge] [Livello badge] [spacer] [Export]
- Totale: ~80px (da ~200px)
- Mobile: Row 2 scrollabile orizzontalmente
```

#### Science Panel

```
- 320px fisso, border-l, bg-background
- Visibile quando showAdvanced = true (Flask ON) + viewport >= lg (1024px)
- Contenuto (dall'alto):
  1. Header "Analisi Live" + loader
  2. Score Ring SVG (animato, 100px, color-coded)
  3. 4 barre sub-score (V, E, F, R) con transizione 600ms
  4. Safety (collapsible, aperta se avoid > 0)
  5. Mappa Anatomica (sempre visibile, anteriore + posteriore)
  6. Equilibrio (collapsible, aperta se squilibri)
  7. Azioni (collapsible, aperta se warnings > 3)
- Debounce analisi: 1s su fingerprint change
- Nessun rendering senza esercizi
```

#### Builder Mode (Context)

```
- enterBuilderMode() al mount di schede/[id]
- exitBuilderMode() all'unmount
- Layout: sidebar lg:hidden quando isBuilderMode = true
- Padding main: p-3 lg:p-4 (ridotto da p-4 md:p-6 lg:p-8)
```

## Metriche di impatto

| Metrica | Prima | Dopo | Miglioramento |
|---|---|---|---|
| Altezza header | ~200px | ~80px | -60% |
| Altezza per esercizio | ~100px | ~36px | -64% |
| Altezza sessione (11 esercizi) | ~1410px | ~550px | -61% |
| Click per vedere Safety Engine | 4 | 0 (sempre visibile) | -100% |
| Click per vedere Score | 4 | 0 (sempre visibile) | -100% |
| Spazio nome esercizio | ~120px (troncato) | ~1fr (intero, va a capo) | Leggibilita' totale |

## Commit log

```
866d492 feat: builder full-screen con Science Panel live (ADR-008)
d0bfb40 fix: SciencePanel breakpoint xl→lg per display scaling Windows
8c6f6f3 feat: mappa anatomica visiva nel SciencePanel
3977a94 feat: SciencePanel v2 — score ring hero + mappa anatomica sempre visibile
5dfb9b1 feat: builder layout professionale — header compatto + card sbloccate
d8b029f feat: header 2 righe bilanciate + SciencePanel toggle via Flask
280f961 feat: exercise rows compressi — da ~100px a ~32px per esercizio
5e99084 feat: session card in griglia 2 colonne — nomi esercizi sempre leggibili
1f1ca78 a11y: touch target espansi + aria-label su tutti i bottoni esercizio
6827d1b fix: sessioni 1 colonna quando SciencePanel è aperto
d72be57 fix: nomi esercizi a capo invece che troncati — griglia 2 col mantenuta
10bfc11 feat: icone info/safety inline col nome — +76px per il testo
```

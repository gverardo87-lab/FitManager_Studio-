# INC-2026-03-30 — Portale Workout: UI invisibile su mobile + Rate Limiter bloccante

- **Data**: 2026-03-30
- **Gravita'**: ALTA (P1)
- **Impatto**: Portale clienti inutilizzabile su mobile — campi, nomi, metriche invisibili + link bloccato da rate limiter
- **Scope**: `/public/scheda/[token]` (frontend) + `public_portal.py` (backend rate limiter)
- **Rilevato da**: Giacomo Vera durante test end-to-end portale da smartphone

---

## Executive Summary

Il portale workout condiviso con i clienti via WhatsApp presentava **due bug critici indipendenti** che rendevano l'intera feature inutilizzabile su dispositivi mobili:

1. **UI invisibile**: testo bianco su sfondo bianco. Le classi CSS `text-muted-foreground` e `text-foreground` dipendono da CSS custom properties del tema shadcn (`--muted-foreground`, `--foreground`). Quando il telefono del cliente ha **dark mode di sistema attivo**, queste variabili risolvono a colori chiari (pensati per sfondo scuro), ma la pagina usa sfondi espliciti bianchi (`bg-white`, `bg-[#f3f4f6]`). Risultato: testo chiaro su sfondo chiaro = invisibile.

2. **Rate limiter troppo aggressivo**: 10 req/min per IP. Il page load fa 2 richieste simultanee (`Promise.all` validate + sessions). 5 refresh da dev = bloccato per 60 secondi. Il frontend trattava il 429 come "Link non valido" (catch generico), inducendo l'utente a pensare che il link fosse corrotto.

---

## Cronologia

| Ora | Evento |
|-----|--------|
| 2026-03-30 mattina | Generato link workout per Giacomo Verardo su dev (8001/3001) |
| 2026-03-30 mattina | Apertura link da smartphone → "Link non valido" (rate limit) |
| 2026-03-30 mattina | Dopo attesa, link aperto ma campi header (Cliente, Trainer, Periodo, Frequenza) invisibili |
| 2026-03-30 mattina | Sezioni Avviamento/Stretching invisibili, campi input non visibili |
| 2026-03-30 mattina | Root cause identificata: CSS variables + rate limiter |
| 2026-03-30 mattina | Fix completa applicata e verificata |

---

## Root Cause Analysis

### Bug 1 — CSS variables del tema non risolvono su pagina pubblica con dark mode

**Meccanismo**: shadcn/ui + Tailwind v4 definisce colori come CSS custom properties:
```css
:root        { --foreground: 0 0% 3.9%;      /* quasi nero */  }
.dark        { --foreground: 0 0% 98%;        /* quasi bianco */ }
:root        { --muted-foreground: 0 0% 45%;  /* grigio medio */ }
.dark        { --muted-foreground: 0 0% 64%;  /* grigio chiaro */ }
```

La pagina `/public/scheda/[token]` usa sfondi espliciti (`bg-white`, `bg-[#f3f4f6]`) ma colori testo dipendenti dal tema (`text-muted-foreground`, `text-foreground` implicito su `<strong>`).

Quando il sistema operativo del telefono del cliente e' in dark mode:
- Il browser applica le variabili `.dark`
- `text-foreground` → bianco → **invisibile su bg-white**
- `text-muted-foreground` → grigio chiarissimo → **quasi invisibile su bg-white**

**Impatto**: 22 elementi colpiti — tutti i label, nomi, metriche, titoli sezione.

**Lezione**: le pagine pubbliche DEVONO usare colori espliciti, MAI CSS variables del tema. Il trainer usa l'app con tema controllato (layout con ThemeProvider), ma il cliente apre il link su un dispositivo con configurazione sconosciuta.

### Bug 2 — Rate limiter per IP blocca uso legittimo

**Parametri originali**: 10 req/min, 30 req/ora per IP.

**Scenario reale**:
- Page load = 2 req simultanee (validate + sessions)
- Apertura sessione = 1 req (exercises)
- Salvataggio = 1 req (log)
- Totale per 1 sessione = 4 req
- 5 refresh rapidi in dev = 10 req → **bloccato per 60s**

**Frontend**: il 429 veniva catturato dal `catch` generico e mostrato come "Link non valido". L'utente non aveva modo di sapere che il link era valido ma temporaneamente bloccato.

---

## Fix Applicate

### Fix 1 — Colori espliciti su tutta la pagina pubblica

| Azione | Dettaglio |
|--------|-----------|
| `colorScheme: "light"` | Forzato su ogni div root (4 branch render) — blocca dark mode browser |
| `text-gray-900` | Colore base esplicito su ogni div root — ereditato da tutti i figli |
| `text-muted-foreground` → `text-gray-500` | Sostituzione globale (22 occorrenze) |
| `bg-muted/30` → `bg-gray-100` | Sostituzione globale (2 occorrenze) |
| `<strong>` senza colore → `text-gray-900` | Colore esplicito su tutti i valori header (4 campi) |
| Zero classi CSS-variable-dependent | Verificato con grep: 0 occorrenze residue |

### Fix 2 — Rate limiter ricalibrato

| Parametro | Prima | Dopo | Rationale |
|-----------|-------|------|-----------|
| `_MAX_PER_MIN` | 10 | 30 | Page load = 2 req, 15 refresh = 30. Bot realistico fa 100+/min |
| `_MAX_PER_HOUR` | 30 | 120 | 5 sessioni/ora × 4 req = 20. Ampio margine senza rischio bot |

### Fix 3 — Frontend distingue 429 da errori reali

| Componente | Cambiamento |
|------------|-------------|
| `ApiError` class | Nuova classe con `.status` per distinguere codici HTTP |
| `loadData()` catch | 429 → state `rateLimited`, messaggio dedicato |
| UI errore | 429: icona amber + "Attendi un momento" + bottone "Riprova". 404: icona rossa + "Link non valido" |

### Fix 4 — Sizing mobile (miglioramento contestuale)

Durante la sessione di debug sono stati corretti anche i font size per leggibilita' mobile:
- Label `text-[10px]` → `text-xs` (12px) su tutti i sub-componenti
- MetricBox, InputField, RatingRow, InfoBlock: sizing aumentato per tap target mobile
- Session note Textarea: `text-sm` → `!text-base` (previene iOS auto-zoom su font < 16px)
- Input: `px-1.5` → `px-2.5`, `h-10` → `h-11` per valori precompilati visibili

---

## Regole Derivate (da aggiungere a CLAUDE.md)

### Pagine pubbliche — Zero CSS variables

Ogni pagina in `app/public/` (anamnesi, workout) DEVE:
1. Avere `style={{ colorScheme: "light" }}` sul div root
2. Avere `text-gray-900` come colore base sul div root
3. Usare SOLO colori Tailwind espliciti (`text-gray-500`, `bg-gray-100`, etc.)
4. MAI usare classi tema-dipendenti: `text-muted-foreground`, `text-foreground`, `bg-muted`, `border-input`, `text-primary`, `bg-primary`, `text-destructive`, `bg-destructive`

**Perche'**: il dispositivo del cliente ha configurazione sconosciuta (dark mode, tema custom, browser non standard). Le CSS variables del tema sono controllate solo nel contesto `(dashboard)/layout.tsx`.

### Rate limiter — calibrazione per UX reale

Il rate limiter su endpoint pubblici deve considerare:
- Ogni page load = N richieste simultanee (non 1)
- Il cliente reale fa ~4 req per sessione di allenamento
- I limiti devono bloccare bot (100+ req/min) senza impattare uso umano
- Il frontend DEVE distinguere 429 da errori reali e offrire retry

---

## File Coinvolti

| File | Modifiche |
|------|-----------|
| `frontend/src/app/public/scheda/[token]/page.tsx` | Colori espliciti, ApiError, UI rate limit, sizing mobile |
| `api/routers/public_portal.py` | Rate limiter: 10→30 req/min, 30→120 req/ora |

---

## Verifica

- [x] `next build` zero errori
- [x] `ruff check api/` zero errori
- [x] Link testato e funzionante dopo fix
- [x] grep conferma 0 classi tema-dipendenti nel file

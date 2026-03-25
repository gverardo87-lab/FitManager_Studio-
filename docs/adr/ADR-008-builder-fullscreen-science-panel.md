# ADR-008 — Workout Builder Full-Screen con Science Panel integrato

- Date: 2026-03-25
- Status: accepted
- Deciders: gvera
- Related: ADR-007 (FitScan), Safety Engine, Training Science Engine

## Context

Il Workout Builder e' la pagina piu' importante di FitManager per il lavoro quotidiano del trainer. Tuttavia:

1. **I motori scientifici sono invisibili**: Safety Engine, Score scientifico, Copertura Muscolare, Equilibrio Biomeccanico richiedono 4 click per essere consultati (builder → espandi SafetyCard → tab "Analisi" → espandi sezioni). Nessun trainer lo fara' nella pratica quotidiana.

2. **Il builder e' sprecato nel layout standard**: la sidebar di navigazione (256px) rimane visibile mentre il trainer edita le sessioni. E' spazio perso — quando si costruisce una scheda non si naviga.

3. **Feedback dalla prima utilizzatrice reale**: Chiara non consulta mai l'analisi scientifica ne' il Safety Engine durante la creazione delle schede. I motori esistono, i dati sono calcolati, ma l'informazione non raggiunge il trainer nel momento in cui serve.

Il problema non e' di feature ma di **architettura UX**: i dati scientifici vivono in un posto diverso da dove il trainer lavora.

## Decision Drivers

1. **Il builder e' dove il trainer passa il tempo**: se la scienza non e' li', non esiste.
2. **Lo spazio c'e'**: eliminando la sidebar si recuperano 256px — abbastanza per un pannello informativo.
3. **I dati sono gia' calcolati**: Safety Engine, Score, Copertura, Balance — tutto esiste nel backend. Serve solo portarlo nel viewport giusto.
4. **Feedback continuo > analisi post-hoc**: il trainer deve vedere l'impatto scientifico di ogni modifica mentre la fa, non dopo aver salvato.
5. **Informativo, mai bloccante**: coerente con la filosofia del Safety Engine. Il pannello informa, il trainer decide.

## Considered Options

### Option A — Micro-patch (badge, toast, card espansa)

- Pro: effort minimo (poche ore), zero rischio
- Contro: non risolve il problema strutturale. Aggiunge cerotti su un'architettura UX sbagliata. Il trainer deve comunque navigare tra tab e sezioni.

### Option B — Builder full-screen con Science Panel (scelta)

- Pro: risolve il problema alla radice. Il builder diventa un workspace completo dove scienza e pratica coesistono. I motori scientifici diventano feedback continuo, non analisi separata. L'esperienza e' simile a editor professionali (Figma, VS Code).
- Contro: effort maggiore (~2-3 giorni), richiede un context per il layout.

### Option C — Pannello scienza come drawer laterale (toggle)

- Pro: non richiede full-screen, meno invasivo
- Contro: nasconde comunque la scienza dietro un click. Il drawer compete con la sidebar. Non risolve il problema.

## Decision

**Option B — Builder full-screen con Science Panel integrato.**

Quando il trainer entra nel Workout Builder (`/schede/[id]`), il layout entra in "builder mode":
- La sidebar di navigazione scompare
- Lo spazio recuperato viene usato dal builder
- Un pannello scientifico fisso (320px) appare a destra
- Il pannello si aggiorna live ad ogni modifica delle sessioni

### Architettura UX

```
BUILDER MODE (full-screen):
┌──────────────────────────────────────┬───────────────┐
│                                      │               │
│  Header + Client info + [Esci]       │  SCIENCE      │
│                                      │  PANEL        │
│  ┌─────────┐ ┌─────────┐ ┌────────┐ │  (320px)      │
│  │ Sess 1  │ │ Sess 2  │ │ Sess 3 │ │               │
│  │         │ │         │ │        │ │  Safety       │
│  │ Eser 1  │ │ Eser 1  │ │ Eser 1 │ │  Score live   │
│  │ Eser 2  │ │ Eser 2  │ │ Eser 2 │ │  Copertura    │
│  │ Eser 3  │ │ Eser 3  │ │        │ │  Equilibrio   │
│  │         │ │         │ │        │ │  Azioni       │
│  └─────────┘ └─────────┘ └────────┘ │               │
│                                      │               │
│  [Save bar]                          │               │
└──────────────────────────────────────┴───────────────┘
```

### Componenti tecnici

#### 1. BuilderModeContext

```typescript
// Nuovo context che segnala al layout di nascondere la sidebar
interface BuilderModeState {
  isBuilderMode: boolean;
  enterBuilderMode: () => void;
  exitBuilderMode: () => void;
}
```

Il builder chiama `enterBuilderMode()` al mount e `exitBuilderMode()` all'unmount o alla navigazione.

#### 2. Layout.tsx — sidebar condizionale

```
<aside className={cn(
  "hidden lg:flex lg:w-64 lg:flex-col lg:border-r lg:bg-sidebar",
  isBuilderMode && "lg:hidden"  // nascosta in builder mode
)}>
```

#### 3. SciencePanel — pannello laterale destro

Nuovo componente che compone in verticale, scrollabile:

| Sezione | Dati | Aggiornamento |
|---------|------|---------------|
| **Safety** | Condizioni rilevate, severity, farmaci, mini body map | Al caricamento (cache 5min) |
| **Score** | Punteggio 0-100, 4 barre (Volume, Balance, Frequenza, Recovery) | Live ad ogni modifica sessioni (debounce 1s) |
| **Copertura** | Lista muscoli con stato (ottimale/deficit/eccesso), mini body map | Live (segue lo score) |
| **Equilibrio** | 5 ratios con status (ok/warning) | Live (segue lo score) |
| **Azioni** | Lista prioritizzata: esercizi controindicati, muscoli sotto MEV, squilibri | Live (segue lo score) |

Ogni sezione e' collassabile individualmente. Lo stato collapsed/expanded e' persistito in localStorage.

#### 4. Responsive (mobile)

Su viewport < 1024px (dove gia' non c'e' sidebar):
- Il pannello scienza diventa un **bottom drawer** swipeable
- O un **tab** nel builder (come oggi, ma piu' accessibile)
- Il builder occupa il 100% dello schermo

#### 5. Navigazione

- **Bottone "Esci"** nella header del builder → torna a `/schede`
- **Keyboard shortcut** `Escape` → conferma uscita se ci sono modifiche non salvate
- **Back button browser** → gestito da `exitBuilderMode()` + navigazione

### Flusso dati

```
Builder Sessions (state locale)
    │
    ├── onModify ──→ debounce 1s ──→ POST /training-science/analyze
    │                                     │
    │                                     v
    │                              TSAnalisiPiano {
    │                                score, volume, balance,
    │                                warnings, dettagli
    │                              }
    │                                     │
    │                                     v
    │                              SciencePanel (render live)
    │
    └── onMount ───→ GET /exercises/safety-map?client_id=X
                           │
                           v
                    SafetyMapResponse {
                      conditions, entries, medications
                    }
                           │
                           v
                    SciencePanel > Safety section
```

## Consequences

### Positive

1. **I motori scientifici diventano visibili senza azione del trainer** — il pannello e' sempre li', sempre aggiornato
2. **Feedback continuo**: il trainer aggiunge un esercizio → lo score cambia → il pannello aggiorna le barre. Causa-effetto immediato.
3. **Zero click per la scienza**: non servono tab, espansioni, navigazioni. E' tutto nel viewport.
4. **Il builder diventa un workspace professionale**: simile a Figma (canvas + pannello proprieta'), non piu' un form dentro un layout generico.
5. **Lo spazio e' usato meglio**: la sidebar non serviva durante l'editing. Ora lo spazio e' produttivo.

### Negative

1. **Richiede un context per il layout**: nuovo meccanismo (BuilderModeContext) che non esisteva. Complessita' aggiuntiva nel layout.
2. **Il pannello occupa 320px**: su schermi < 1280px potrebbe comprimere troppo le sessioni. Necessario un breakpoint per collassare il pannello.
3. **La ScientificAnalysisTab esistente diventa parzialmente ridondante**: il pannello mostra un sottoinsieme dei dati. La tab completa rimane accessibile per l'analisi approfondita.

### Follow-up actions

1. Implementare `BuilderModeContext` e integrarlo nel layout
2. Creare il componente `SciencePanel` con le 5 sezioni
3. Convertire il builder page in layout 2-colonne
4. Collegare il live analysis (debounce su modifica sessioni)
5. Gestire responsive (drawer su mobile)
6. Test su viewport 1280px, 1440px, 1920px

## Rollback / Exit Strategy

Se il full-screen risulta problematico:
- Il context e' un semplice boolean — rimuoverlo ripristina il layout standard
- Il SciencePanel puo' essere riusato come componente standalone in altre pagine
- La ScientificAnalysisTab esistente resta intatta (non viene rimossa)

## Supersedes / Superseded By

- Supersedes: parzialmente la ScientificAnalysisTab come punto di accesso primario all'analisi (la tab resta per l'analisi approfondita)
- Superseded by: nessuno

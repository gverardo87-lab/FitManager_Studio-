# ADR-024 — Semantica per-classe: le leggi degli assi di stato valgono ovunque, non dove sono esplose

**Stato:** Accettata (2026-07-07) — ratifica founder («procedi col blocco di generalizzazione, la tua
proposta mi convince»). Pianificata: blocco **G9.7** (`SPEC_G9.7_SEMANTICA_PER_CLASSE.md`).
**Consolida (non supersede):** ADR-022 + Addendum II (leggi del read/write-model della cassa),
ADR-017/G7.8-bis (occupazione), ADR-019 D-PROPONE, ADR-023 (fence).

## Context

Audit `AUDIT_CREDITI_EVENTI_ORFANI_2026-07-07.md` (trigger: caso reale del founder, contratto 39):
13 finding su due assi MAI colpiti prima (eventi×contratto in scrittura, occupazione crediti in
lettura). Nessun finding è una classe nuova: (1) fail-silent in scrittura su ramo non presidiato —
3ª occorrenza; (2) derivato nudo a video — 2ª occorrenza (gemello del «netto nudo» INC-2026-07-03);
(3) transizione che non enumera le entità satellite — gemella dei «5 produttori mancati»;
(4) consumo-SSoT violato fuori dal perimetro del guard. Il finding strutturale: **deadlock da due
protezioni giuste** (auto-assign filtra i chiusi ✓ + re-parenting vietato ✓ = evento orfano
irrecuperabile) — nessuno guarda la COMPOSIZIONE delle protezioni.

Le leggi che curano queste classi esistono già (metodo in 4 regole: chiudi l'insieme · interprete
unico · totalità fail-loud · gemello di esaustività; D-NESSUN-NETTO-NUDO; TransitionExecutor;
Hypothesis) ma sono state applicate **per-asse** (cassa), non **per-classe**: ogni asse nuovo
ripresenta le stesse ferite. «Chi non anticipa insegue» (founder).

## Decision

1. **D-LEGGI-PER-CLASSE** — le 4 regole del metodo si applicano a OGNI asse di stato del dominio,
   non solo alla cassa. Artefatto vivo: **matrice assi×regole** in
   `docs/technical/MATRICE_ASSI_SEMANTICI.md` (nasce in G9.7.0 dai censimenti 2026-07-04 e
   2026-07-07). Un asse senza riga in matrice è un asse non governato.
2. **D-MAI-SILENZIO-IN-SCRITTURA** — ogni path di scrittura che DEGRADA (fallback, default,
   auto-assegnazione fallita) deve segnalarlo: nella response (fatto esplicito) e in UI (warning
   prima, segnale dopo). Il silenzio su degradazione è un bug di classe, mai una scelta UX.
   Gemello in lettura: D-LETTURA-FAIL-LOUD (ADR-022 Add. II).
3. **D-DERIVATO-MAI-NUDO** — generalizza D-NESSUN-NETTO-NUDO a ogni grandezza derivata mostrata:
   ogni numero a video è spiegabile dai componenti visibili nella STESSA vista (sub-label,
   breakdown, riga dedicata). Vale per denaro, crediti, occupazione, e ogni asse futuro.
4. **D-PERIMETRO-TRANSIZIONI** — ogni transizione di stato del contratto (terminate, reopen, …)
   **enumera** tutte le entità satellite (rate, cassa, receivable, wallet, **eventi**) e decide
   esplicitamente per ciascuna — anche «non toccare» è una decisione dichiarata nel codice e
   presidiata da un test di perimetro. L'enumerazione implicita è la classe «5 produttori mancati».
5. **D-RECUPERO-ESPLICITO** — un dato finito in limbo ha SEMPRE una via di recupero esplicita,
   guardata e auditata (endpoint dedicato); MAI riparazione silenziosa/automatica. Le transizioni
   PROPONGONO il recupero (coerente con D-PROPONE, ADR-019), non lo impongono.
6. **D-BIRTH-AUDITOR** — si attiva il charter `semantic-birth-auditor` (SPEC_G9.4-BIS §5) come
   agente in `.claude/agents/`: a ogni NASCITA di asse/stato/categoria/derivato verifica le 4
   regole + composizione con le protezioni esistenti. È lo strumento di anticipo.
7. **D-GENERATIVO-PER-ASSE** — la macchina Hypothesis (G9.5) si estende oltre il money-path:
   l'asse occupazione entra nelle rule (creare eventi su contratti chiusi/riaperti interleaved
   con le transizioni). Una rule del genere avrebbe trovato B1/B2 prima del founder.

## Consequences

- I 13 finding dell'audit diventano gli acceptance criteria di G9.7 — un blocco, non 13 rincorse.
- Il costo è un artefatto in più da mantenere (matrice) e un gate di nascita (auditor); il
  beneficio è spostare la scoperta dei difetti da «cliente reale» a «nascita dell'asse».
- Le 2 sessioni orfane reali (eventi 640/641, crm.db dev) si recuperano SOLO via G9.7.2
  (endpoint esplicito), mai a mano nel DB.

## Rollback / Exit

Le decisioni 1-3 sono documentali+test (reversibili). 4-7 aggiungono presidi, non cambiano l'asse
DENARO né schema DB. Se la matrice si rivela burocrazia morta, si fonde in ARCHITECTURE.md.

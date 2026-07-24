# SPEC R0 — Protezione release v1.0.15

**Stato:** 🟠 APERTA — R0.1 contenimento implementato e verificato; **HOLD decisione TLS live prima di R0.2**
**Data:** 2026-07-24
**Branch:** `FitManager_Studio`
**Tipo:** contenimento release cross-layer; nessuna nuova macro-feature e nessuna nuova regola finanziaria
**Audit fondante:** `docs/archive/AUDIT_OBSOLESCENZA_POST_MIGRAZIONI_2026-07-23.md`
**Autorità:** `AGENTS.md` → `MANIFESTO.md` → `LAUNCH_SCOPE.md` → layer `CLAUDE.md` → ADR/SSoT
**Sequenza ratificata:** FE-0 + FE-1.0/1.1 ✅ → **R0.1 → R0.2 → R0.3 → R0.4** → P1..P6 → candidate v1.0.15 → G-MAC

> Questa SPEC è la casa del solo lavoro release-critical emerso dall'audit. La bonifica massiva di
> codice morto, API dormienti e tool storici non entra in R0 e non interrompe il blocco P. A chiusura
> di R0: consuntivo, full suite proporzionata ai layer toccati, verifier finanziario sui money-read,
> fold-back degli evergreen realmente modificati, append al BUILD_LOG e archiviazione della SPEC nello
> stesso commit docs del gate finale.

## 1. Decisione e tesi falsificabile

Il founder approva un **gate ristretto di protezione release prima di P1**, non l'intera «Fascia A»
dell'audit originario.

Dopo R0 devono essere vere contemporaneamente quattro proprietà:

1. un'installazione provisionata FRP non avvia, propone o configura un secondo percorso Tailscale
   Funnel;
2. P1 può introdurre la propria migrazione Alembic senza alcuna procedura viva che ricrei
   `crm_dev.db`;
3. le superfici cliente toccate mostrano il denaro dal netto SSoT e non espongono importi nella
   Command Palette globale;
4. checklist e runbook di candidate verificano il percorso FRP reale, non quello Tailscale storico.

La tesi è falsificata se anche uno solo di questi scenari resta possibile: Funnel auto-avviato da un
`.env` preservato; wizard che propone Tailscale su istanza FRP; `migrate-all.sh` che crea
`crm_dev.db`; ContrattiTab che diverge da `/contratti`; Command Palette che mostra lordo/prezzo;
preflight che dichiara verde una verifica Tailscale senza provare FRP.

## 2. Impact map

- **Obiettivo:** eliminare i rischi capaci di compromettere la candidate v1.0.15 o la sua fiducia
  percepita prima di aggiungere il nuovo asse economico di P1.
- **Layer:** installer + tunnel backend/frontend; procedura Alembic/rehearsal; read-only finance FE;
  documentazione operativa.
- **Invarianti da preservare:**
  - FRP resta l'unico percorso target e il portale pubblico continua a funzionare;
  - l'assenza o il fermo temporaneo di FRP non apre automaticamente un percorso alternativo;
  - fallback locale sempre disponibile;
  - nessun cambio a ledger, rate, payload di pagamento, residuo, wallet o transizioni;
  - denaro letto dal wire SSoT, mai ricalcolato nel frontend;
  - privacy-first e finanze confinate ai contesti dedicati;
  - un solo `crm.db`, dati persistenti solo in `data/`;
  - ownership, Bouncer Pattern e audit trail invariati.
- **Non-obiettivi:** dismissione completa Fase 3 di Tailscale; apertura CRM via Strada B; rimozione
  massiva dei cluster morti; smontaggio Nutrition/Training; bonifica di tutti i tool storici;
  ottimizzazioni generali dashboard; modifica della semantica crediti già assegnata a P4/P5.

## 3. Rettifiche vincolanti dell'audit fondante

La verifica indipendente 2026-07-24 conferma i blocker ma corregge la stima del perimetro:

- `crm_dev` compare in **34 sorgenti tracciati**, non 63: il conteggio 63 includeva 29 `.pyc`
  ignorati in `__pycache__`;
- `workspace_engine.py` non è morto: `/workspace/today` e `collect_workspace_snapshot` sono vivi e
  consumati dalla pagina Oggi. Solo i rami list/detail senza UI sono candidati a un audit post-release;
- Nutrition è montato e privo di UI, ma gli endpoint richiedono autenticazione trainer e il tunnel
  FRP corrente non espone il CRM: decisione post-release, non blocker R0;
- la non-coesistenza Tailscale/FRP è un vincolo **a regime**. R0 chiude l'auto-Funnel e la confusione
  sulle istanze FRP; la dismissione completa resta una decisione Fase 3;
- le circa 6.900 LOC frontend non importate sono debito reale ma non entrano normalmente nel bundle
  Next: cleanup separato dopo v1.0.15.

## 4. Sequenza dei gate

| Ordine | Gate | Scopo | Dipendenza |
|---:|---|---|---|
| 1 | **R0.1 — Percorso pubblico unico** | Contenere transizione FRP/Tailscale | FE-1 chiuso LIVE |
| 2 | **R0.2 — Binario unico di migrazione** | Rendere sicura l'apertura P1/Alembic | R0.1 indipendente |
| 3 | **R0.3 — Verità finanziaria e privacy** | Chiudere lordo/netto e denaro globale | G8.4 SSoT |
| 4 | **R0.4 — Verità operativa release** | Allineare checklist/runbook/contesto | R0.1–R0.3 reali |
| 5 | **P1** | Apre il blocco P | R0 chiuso e consuntivato |

Ogni gate è un'unità coesa e verificabile. Nessun cleanup post-release viene infilato tra questi gate.

## 5. R0.1 — Percorso pubblico unico

### Contratto di transizione ratificato

- **Istanza FRP provisionata:** FRP è l'autorità dell'URL pubblico. La UI non propone installazione,
  login o Funnel Tailscale; una configurazione manuale non può sostituire in-process o su `.env`
  l'URL gestito da FRP.
- **Istanza non provisionata FRP:** comportamento locale attuale preservato. Il destino del fallback
  Tailscale viene deciso nella Fase 3, non in R0.
- **Ogni istanza:** `launcher.bat` non esegue mai `tailscale funnel`, anche se un upgrade conserva
  `PUBLIC_PORTAL_ENABLED=true` in `data/.env`.

### File/layer probabili

- `installer/launcher.bat`, `installer/fitmanager.iss` solo per verifica del packaging;
- `api/services/connectivity_config.py`, `api/services/connectivity_runtime.py`,
  `api/routers/system.py`, eventuale read-model tunnel condiviso;
- `frontend/src/components/dashboard/ConnectivityOnboardingCard.tsx`, componenti `settings/`
  Connettività, hook e `types/api.ts` se il contratto wire cambia;
- copy attivo in condivisione scheda/anamnesi.

### Criteri di accettazione

- **AC-R01-1:** grep/static guard: zero comando `tailscale funnel` nel launcher installato.
- **AC-R01-2:** fixture `.env` legacy con `PUBLIC_PORTAL_ENABLED=true` non abilita un secondo tunnel.
- **AC-R01-3:** istanza FRP provisionata non restituisce né rende `install_tailscale`,
  `connect_tailscale`, `enable_funnel` come prossima azione.
- **AC-R01-4:** su istanza FRP, POST di configurazione legacy non può cambiare il base URL autoritativo;
  il rifiuto o il no-op è esplicito e testato, mai silenzioso.
- **AC-R01-5:** portale pubblico FRP, route separation e fallback localhost restano funzionanti.
- **AC-R01-6:** test backend connectivity + Vitest mirati + `next build`; prova packaging che il launcher
  stageato è quello corretto.

### Consuntivo R0.1 — 2026-07-24

**Esito del contenimento:** implementato e verificato. La chiusura formale del gate resta in HOLD per
una decisione founder sul rischio TLS live emerso durante la prova esterna; R0.2 non è ancora aperto.

- `instance_id` della licenza valida è ora il segnale autorevole della provision FRP, indipendente
  dalla disponibilità temporanea di `frpc`; il runtime imposta sempre origine gestita e fallback
  localhost senza persistere un secondo flag.
- `launcher.bat` non legge più `PUBLIC_PORTAL_ENABLED` e contiene zero comando Funnel; il packaging
  Inno Setup continua a stageare esattamente quel launcher.
- il read-model espone `public_access_provider=managed_frp`; su tale ramo non esegue probe Funnel,
  non restituisce azioni Tailscale e usa esclusivamente l'origine `*.fitmanagerstudio.com`.
- ogni POST legacy di configurazione su istanza FRP riceve `409` esplicito prima di qualsiasi
  scrittura a `.env` o modifica dell'environment del processo.
- la UI FRP non monta il wizard legacy: mostra origine non modificabile, fallback locale, verifica
  end-to-end e validazione portale. Il percorso legacy non-FRP resta invariato, come ratificato.

**Evidenze:**

- backend connectivity **28/28**; full backend **880/880** (31 warning baseline);
- frontend mirato R0.1 **5/5**; suite frontend definitiva **157/157**; lint mirato e ruff mirato verdi;
- Next production build verde, **20 pagine**;
- static/package guard: zero `tailscale funnel`, zero `PUBLIC_PORTAL_ENABLED` nel launcher e sorgente
  `installer/launcher.bat` confermata da `fitmanager.iss`;
- live FRP applicativo: `/health` **200**, `/clienti` **404**, ma solo disabilitando la verifica della
  trust chain del certificato.

**Finding live non occultabile:** il client HTTPS strict rifiuta il certificato self-signed
(`Impossibile stabilire una relazione di trust`). Il routing e la route separation funzionano, ma
l'end-to-end pubblico non è dichiarabile production-ready finché la Fase 2 TLS descritta nel root
`CLAUDE.md` non viene completata oppure il founder non ratifica una collocazione diversa. Decisione
richiesta prima di R0.2: remediation immediata **R0.1.5** oppure blocker falsificabile dentro R0.4.

**Nota ambiente test:** i warning di rollover `fitmanager.log` dipendono dal server live
`uvicorn --reload` già in esecuzione che condivide il log con pytest. Il processo `frpc` osservato
non è orfano: è figlio di quel runtime live e non è stato terminato.

## 6. R0.2 — Binario unico di migrazione

### Scope

- ritirare o riscrivere `tools/scripts/migrate-all.sh` affinché esista un solo target `crm.db`;
- correggere la regola dual-DB in `api/CLAUDE.md`;
- rimuovere dal distribution rehearsal il requisito positivo `crm_dev.db`;
- aggiungere un guard che fallisca se una procedura release/migrazione viva tenta di creare
  `data/crm_dev.db`.

I restanti sorgenti storici che nominano `crm_dev` non vengono ripuntati alla cieca su `crm.db`: alcuni
sono script distruttivi di seed/curation e richiedono triage dedicato post-release.

### Criteri di accettazione

- **AC-R02-1:** la procedura prescritta esegue Alembic una sola volta sul DB configurato.
- **AC-R02-2:** nessun rehearsal sano richiede l'esistenza di `crm_dev.db`.
- **AC-R02-3:** prova in directory temporanea: l'esecuzione della procedura non crea un secondo DB.
- **AC-R02-4:** `api/CLAUDE.md`, root `CLAUDE.md` e ADR-014 non si contraddicono sul modello single-DB.
- **AC-R02-5:** gate Alembic/schema pertinenti verdi prima di aprire P1.

## 7. R0.3 — Verità finanziaria e privacy

### Scope

- `ContrattiTab` consuma `netto_incassato` dal wire; se serve disclosure lordo/rimborsi, riusa il
  pattern canonico senza sottrazioni frontend;
- il gemello anti-vacuità di G8.4 include esplicitamente ContrattiTab;
- la Command Palette globale non mostra `totale_versato` né `prezzo_totale_attivo` nel preview cliente;
- `ExpiringContractsSheet` non calcola `(prezzo / crediti) × residui` nel frontend: il valore
  approssimativo viene rimosso finché non esiste un read-model backend canonico;
- il tour Clienti descrive le colonne e gli stati realmente esistenti dopo FE-0.

### Criteri di accettazione

- **AC-R03-1:** su contratto con rimborso, netto in hero/lista/profilo è identico.
- **AC-R03-2:** guard G8.4 fallisce se ContrattiTab torna a leggere il lordo come posizione.
- **AC-R03-3:** test privacy Command Palette: nessun importo monetario nel preview cliente.
- **AC-R03-4:** zero formula monetaria del «valore sedute residue» in `ExpiringContractsSheet`.
- **AC-R03-5:** nessuna mutation, endpoint, invalidazione o payload money-path modificato.
- **AC-R03-6:** Vitest mirati + suite FE + lint/build; `financial-invariant-verifier` = MONEY AXIS
  PRESERVED.

## 8. R0.4 — Verità operativa release

Aggiornare solo i documenti e le prove che possono guidare male la candidate:

- `docs/operations/RELEASE_CHECKLIST.md`: FRP, `tunnel-status`, dominio
  `*.fitmanagerstudio.com`, route separation e conteggi catalogo correnti;
- `docs/operations/SUPPORT_RUNBOOK.md`: diagnosi FRP prima di ogni riferimento legacy;
- `LAUNCH_SCOPE.md`: accesso remoto coerente con FRP/Strada B;
- `docs/technical/TUNNEL_ARCHITECTURE.md`: esempio `https2http` e path reali;
- `api/CLAUDE.md` / `frontend/CLAUDE.md`: solo drift direttamente toccato da R0;
- `tools/admin_scripts/e2e_distribution_rehearsal.py`: checklist manuale FRP.

I conteggi cosmetici, la tabella WhatsApp e altra documentazione non release-critical restano fuori R0.

### Criteri di accettazione

- **AC-R04-1:** zero istruzioni attive di release/supporto che chiedono Funnel Tailscale.
- **AC-R04-2:** checklist FRP falsificabile: stato tunnel, URL pubblico, portale, 404 CRM dal tunnel.
- **AC-R04-3:** review coerenza cross-doc e link/path integrity.
- **AC-R04-4:** `docs/INDEX.md` rispecchia esattamente il fronte `docs/specs/`.

## 9. Findings già assorbiti o differiti

### Assorbiti da lavoro vivo

- `crediti_residui_attivi`, dropdown e filtri onesti → SPEC_P P4/P5;
- raw count e residuo workspace → SPEC_VOCABOLARIO Giro 2, dopo verifica dei soli siti vivi;
- `signed_contractual_amount` → HOLD fino al birth-audit P1; nessuna rimozione in R0.

### Differiti dopo v1.0.15

- cluster frontend morti e relativi test;
- soli rami workspace list/detail realmente orfani;
- alert/wire costosi non consumati e dipendenze orfane;
- triage dei 34 sorgenti tracciati con `crm_dev`;
- decisione founder su mount Nutrition/Training e dismissione completa Tailscale Fase 3.

Questi punti non sono autorizzazione a modificare codice: dopo la candidate ricevono una SPEC dedicata
solo se il founder apre il blocco.

## 10. Definition of Done R0

1. AC-R01, AC-R02, AC-R03 e AC-R04 verificati con evidenza reale;
2. full suite raccolta verde per backend/frontend e quality gate AGENTS.md;
3. financial-invariant-verifier PASS su R0.3;
4. test upgrade/installazione con `.env` legacy e test live FRP da rete esterna;
5. commit atomici per gate, con branch rilasciabile dopo ciascuno;
6. consuntivo con commit, suite, rischi residui e decisioni;
7. fold-back negli evergreen realmente toccati;
8. append a `docs/learning/BUILD_LOG.md`, aggiornamento `docs/INDEX.md` e spostamento di questa SPEC
   in `docs/archive/specs/` nello stesso commit docs di chiusura;
9. soltanto dopo questi punti si apre P1.

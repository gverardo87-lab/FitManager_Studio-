# Analisi Strategica Pre-POC — 2026-07-31 (Antigravity Senior Architect)

> **Esito 2026-07-31:** fotografia superseded. Il confronto cross-agent è stato risolto e foldato
> in `docs/specs/SPEC_PRE_POC.md`; questo file conserva il ragionamento storico, ma non governa
> priorità, scadenze o gate.

> **⚠️ DOCUMENTO OPERATIVO DI CONFRONTO (NON VINCOLANTE).** Non è una `SPEC_*` né un ADR. Non ha riga `Stato:`,
> non gatekeepa alcun lavoro e non richiede fold-back a DoD. È una **fotografia analitica e strategica**
> redatta da Antigravity (Senior AI Systems Architect) per il confronto incrociato con gli audit prodotti da
> Claude Code e Codex, al fine di congelare le decisioni pre-POC.
> La work-queue **vincolante** resta `docs/specs/`; la legge resta `docs/adr/`. Se una decisione qui contenuta
> viene approvata dal founder, migrerà in `docs/specs/SPEC_PRE_POC.md`.

- **Tipo:** Analisi strategica cross-agent (opera in `docs/operations/`)
- **Data:** 2026-07-31
- **Autore/Persona:** Antigravity (Senior AI Systems Architect)
- **Orizzonte Operativo:** Finestra dev **31 lug → 15 ago 2026** (~15 giorni effettivi); Freeze Didattico **16 → 31 ago**; Pilota POC **Settembre 2026**.
- **Stato Repository SSoT:** Branch `FitManager_Studio`. **Blocco R0 (R0.1..R0.4) UFFICIALMENTE CHIUSO** (commit `459a75d5`). Candidate `v1.0.15` sbloccata.
- **Scopo:** Valutazione architetturale dell'analisi incrociata del 29-07, riconciliazione con lo stato attuale del repo (R0.4 chiuso), e definizione della roadmap esecutiva a 3 corsie con confronto diretto tra tool AI (Claude Code vs Codex vs Antigravity).

---

## 0. Inquadramento nella Gerarchia Documentale (`AGENTS.md` §11)

In accordo con la governance di progetto (`AGENTS.md` e `docs/INDEX.md`):
- **`docs/adr/`**: La Legge (ADR-013, ADR-025, ADR-026 in corso).
- **`docs/specs/`**: Il Lavoro Aperto (work-queue vincolante).
- **`docs/technical/`**: SSoT Evergreen (com'è fatto il sistema).
- **`docs/operations/`**: **Sede di questo documento.** Ospita runbook, workflow multi-agente e analisi incrociate/comparative per la direzione strategica.

---

## 1. Riconciliazione Stato Reale (R0.4 Chiuso vs Audit 29-Luglio)

L'analisi incrociata del 29 luglio (`ANALISI_INCROCIATA_PRE_POC_2026-07-29.md`) registrava R0.4 come "in corso".
La verifica reale su Git conferma che in data 29-07 (commit `459a75d5`) **R0.4 è stato completato e consuntivato**:
1. `tests/test_r04_operational_truth.py` è committato e verde (suite di veridicità operativa).
2. `SPEC_R0_PROTEZIONE_RELEASE_V1_0_15.md` è stata consuntivata e archiviata in `docs/archive/specs/`.
3. Il branch `FitManager_Studio` è pulito e allineato a `origin/FitManager_Studio`.

> **Conseguenza Diretta:** Non ci sono pendenze release-critical sul blocco R0. La candidate `v1.0.15` è eleggibile per il packaging non appena completate le remediation FE e TLS-live.

---

## 2. Valutazione Architetturale della Strategia Pre-POC

### 2.1 Fase Audit Ufficialmente CHIUSA (20/20)
L'ipotesi che manchi "un ulteriore audit frontend" è stata smentita dai fatti: il repo conta già 20 audit (3 puri FE a luglio 2026).
Continuare a produrre audit in questa fase rappresenta un **rischio di prolificazione del lavoro**. A ~15 giorni dal freeze del 16 agosto, il team necessita di un **riduttore di perimetro**, non di un generatore.

### 2.2 Pilota Settembre (Ibrido) vs Apertura Commerciale (Dicembre)
L'analisi del 29 luglio ha introdotto una distinzione strategica fondamentale (Decisione D2):
- **Settembre 2026:** Pilota controllato con utenti selezionati (Alessio, Chiara, Daniele).
- **Dicembre 2026:** Apertura commerciale su largo pubblico.

Questa distinzione disinnesca la bloccanza di **G1 (SQLCipher cifratura `crm.db`)** per settembre. Alessio sta già operando con `crm.db` locale in chiaro; la cifratura resta un **Tier-1 Security Gate** obbligatorio prima della commercializzazione di dicembre, ma il suo sviluppo viene differito a ottobre/novembre per non soffocare la finestra dev di agosto.

### 2.3 G-MAC (macOS / Daniele) Disaccoppiato dall'Hardware Locale
Daniele rappresenta il primo prospect di rilievo su piattaforma macOS. La strategia approvata (D3-D5) rimuove la dipendenza da un Mac locale non disponibile:
- **Iscrizione Apple Developer Individual ($99):** Non richiede P.IVA né codice D-U-N-S, ed è la pole temporale più lunga (1-3 giorni di verifica Apple).
- **CI/CD GitHub Actions:** Compilazione Nuitka/clang, firma con `codesign` (hardened runtime sia per l'eseguibile Python che per il sub-binario `frpc`), notarizzazione via `notarytool` e stapling.
- **Mac Cloud Validation:** Prova interattiva finale su istanza Mac cloud a noleggio (~20-50€) prima della call di onboarding con Daniele a inizio settembre.

---

## 3. Roadmap Esecutiva a 3 Corsie Parallele (31 Luglio → 15 Agosto)

Le tre corsie individuate sono **architetturalmente ortogonali**: non competono per la stessa attenzione dev foreground.

```
+-----------------------------------------------------------------------------------+
|                        FINESTRA DEV: 31 LUG -> 15 AGO 2026                        |
+-----------------------------------------------------------------------------------+
| CORSIA 1 (Foreground Dev)  : FE Remediation (B0 -> B1 -> B2 -> B3)                |
| CORSIA 2 (Interlaced CI)   : G-MAC macOS (Apple ID -> CI Nuitka -> Cloud Mac)     |
| CORSIA 3 (Background/Ext)  : Sblocchi (VPS SSH TLS, Chiara v1.0.14, Tax, Design G1)|
+-----------------------------------------------------------------------------------+
```

### Corsia 1 — Frontend Remediation (Foreground Dev)
Priorità assoluta per le ore di sviluppo diretto:
1. **B0 — Bonifica Dead-Code UI (~0.5 giorni):**
   - Ripartire con rimozione pulita di `ProgressiTab.tsx` (739 LOC mai importato), `OverdueRatesSheet.tsx` e componenti `Workspace*` non montati. Risk profile nullo.
2. **B1 — Remediation RC-1 Deep-Link (~1.5–2 giorni):**
   - Preservare i query param contestuali (`?cliente=`, `?from=`) in `frontend/src/lib/url-state.ts` promovendoli a stato al mount (pattern nativo già operante in `/cassa`).
3. **B2 — Remediation RC-2 Focus Intenti (~2–3 giorni):**
   - Generalizzazione di `lib/renewals-focus.ts` nel nuovo `lib/context-focus.ts` e hook `useContextFocus` esteso a tutti i 6 intenti UX.
4. **B3 — Accessibilità & Igiene Residua FE-1 (~2 giorni):**
   - Completamento dei criteri di accettazione AC-FE1-1..6.

### Corsia 2 — G-MAC macOS Packaging (Interlaced Dev + CI)
1. **Day 0 (IMMEDIATO):** Avvio richiesta account **Apple Developer Individual**.
2. **Ratifica ADR-026** e implementazione **G-MAC.1** (portabilità cross-platform di `_FRPC_FILENAME` e percorsi binari).
3. **G-MAC.2 Workflow CI:** Configurazione runner `macos-latest` su GitHub Actions con Nuitka, `codesign` e `notarytool`.
4. **G-MAC.3 & G-MAC.4:** Script di packaging (`launcher.command`, `install.sh`, DMG) e validazione finale su Mac Cloud a noleggio.

### Corsia 3 — Sblocchi Esterni & Architectural Design (~0 dev-hours)
1. **Passphrase SSH VPS:** Sblocco TLS Let's Encrypt pubblico (`R0.1.5-live`) per chiudere i warning certificato browser.
2. **Chiara Field Delivery:** Test del pacchetto `v1.0.14` su PC non-dev con restore del backup reale e merge fast-forward di `main`.
3. **Allineamento Tributarista:** Definizione valore fiscale `pro_sedute`, penali recesso, e inquadramento P.IVA / NASpI.
4. **Design Dettagliato G1:** Finalizzazione delle specifiche per l'integrazione di SQLCipher senza produrre codice prima del cliff.

---

## 4. Matrice di Confronto Multi-Agente (Claude Code vs Codex vs Antigravity)

Questa matrice sintetizza il posizionamento strategico tra i 3 motori/agenti AI operativi sul progetto:

| Asse di Analisi | Claude Code (Audit 29-Jul) | Codex (Execution Gatekeeper) | Antigravity (Senior AI Architect) | Sintesi / Verdetto Unificato |
|---|---|---|---|---|
| **Stato R0.4** | In esecuzione (snapshot 29-07) | Richiede verifier & test deterministici | **CHIUSO & COMMITTATO** (commit `459a75d5`) | **R0 è 100% chiuso.** Nessun blocker residuo in R0. |
| **Pressione FE** | Identifica 33 difetti e RC-1/RC-2 | Pretende test d'integrazione frontend (Vitest) | **Prioritizza B0->B3 ed esclude i refactor monoliti** | **Remediation FE immediata**, ma zero refactor >1000 LOC prima del cliff. |
| **G1 (SQLCipher)** | Considerato debito ad alta severità | Esige contratti bouncer & zero regressioni su `crm.db` | **Differito a Ottobre/Novembre (post-cliff)** | **Non blocca il Pilota di Settembre**; blocca solo l'apertura commerciale di Dicembre. |
| **macOS (Daniele)** | Propone disaccoppiamento P.IVA e Apple Individual | Esige firma di tutti i sub-binari (`frpc`) | **Valida la pipeline CI + Cloud Mac** | **Account Apple Individual SUBITO**, build su GitHub Actions, test su Mac Cloud. |
| **Blocco P (SPEC_P)** | Classificato come nuovo sviluppo | Gated dietro stabilità R0 | **ESCLUSO dalla finestra di Agosto** | **Anti-scope per i prossimi 15 giorni.** Rinviato post-pilota. |

---

## 5. Anti-Scope Vincolante (Cosa NON fare prima del 16 Agosto)

Per garantire la consegna della candidato `v1.0.15` entro il freeze didattico del 16 agosto, sono tassativamente vietati:
1. ❌ **Refactor di monoliti FE >1000 LOC** (`CommandPalette.tsx`, `cassa/page.tsx`, `RecurringExpensesTab.tsx`).
2. ❌ **Apertura del Blocco P (`SPEC_P`, P1-P6)** per evitare l'introduzione di modifiche DB e nuove classi contabili a ridosso del freeze.
3. ❌ **Esecuzione di un 21° audit.**
4. ❌ **Implementazione codice G1 (SQLCipher)** prima del completamento dei test del pilota di settembre.

---

## 6. Prossimi Passi per la Formalizzazione

1. **Registrazione del documento** nell'indice di progetto [`docs/INDEX.md`](file:///c:/Users/gvera/Projects/FitManager_AI_Studio/docs/INDEX.md) sotto la sezione `operations/`.
2. **Conversione in Work-Queue Vincolante:** Se approvato dal founder, i gate B0..B3 e G-MAC.1..4 confluiranno in `docs/specs/SPEC_PRE_POC.md`.
3. **Start Immediato Microstep B0:** Bonifica file dead-code isolati in `frontend/src/`.

---
*Fine analisi strategica Antigravity. Pronta per il confronto con Claude Code e Codex.*

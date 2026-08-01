# Analisi incrociata pre-POC — 2026-07-29

> **Esito 2026-07-31:** fotografia superseded. Evidenze e finding ancora validi sono stati foldati
> in `docs/specs/SPEC_PRE_POC.md`; le priorità non ratificate non hanno autorità operativa. Il file
> resta disponibile solo come storia dell'analisi e non è contesto di lavoro.

> **⚠️ DOCUMENTO NON VINCOLANTE.** Non è una `SPEC_*` né un ADR. Non ha riga `Stato:`,
> non gatekeepa alcun lavoro, non richiede fold-back a DoD. È una **fotografia analitica**
> che incrocia BUILD_LOG + docs (specs, audit, archive) con il **codice reale**, per fissare
> la direzione di sviluppo pre-POC. La work-queue **vincolante** resta `docs/specs/`; la legge
> resta `docs/adr/`. Se una decisione qui contenuta va resa esecutiva, migra in una spec dedicata
> (`SPEC_PRE_POC.md`) o nell'ADR competente. Finché resta qui, è **contesto**, non contratto.

- **Tipo:** analisi non vincolante (cross-analysis)
- **Data:** 2026-07-29
- **Orizzonte:** ~30 giorni al POC di settembre 2026; finestra dev effettiva **29 lug → 15 ago** (cliff didattico dal 16 ago)
- **Versione SSoT al momento dell'analisi:** `api/__init__.py` = **1.0.14** (tagliata/sigillata, NON consegnata)
- **Metodo:** grounding via workflow multi-agente (7 agenti, ~824k token) con verifica `file:riga` sul codice reale e riconciliazione memoria↔realtà

---

## 0. Perché questo documento

A ~30 giorni dal lancio della POC serviva **concludere definitivamente la direzione di sviluppo pre-POC**, con tempistiche precise, prima del cliff del 16 agosto (dal 16 al 31 il founder si dedica a materiale didattico per clienti e per il partner Alessio). L'ipotesi di partenza del founder era: *«l'ultimo audit di sviluppo mancante è quello del frontend, fatto molto tempo fa con un ambiente più grezzo»*. Questa analisi la mette alla prova contro il repo reale.

---

## 1. Verdetto sulla premessa: NON regge (ma l'istinto sì)

La premessa «ultimo audit = FE, vecchio, grezzo» è **falsa su tutti e tre gli assi**:

1. **Non manca.** L'ultimo audit FE è `AUDIT_DEEPLINK_CROSS_PAGE_2026-07-24` — è **l'audit più recente dell'intero progetto**.
2. **Non è vecchio.** Esistono **tre** audit FE puri, tutti di luglio 2026:
   - `AUDIT_DEEPLINK_CROSS_PAGE_2026-07-24` (commit `4162e02`) — 77 link, 33 difetti, 10 pattern radice.
   - `AUDIT_FRONTEND_CORE_INTUITIVITA_2026-07-21` (commit `2de0520`, archiviato) → `SPEC_FRONTEND_CORE_INTUITIVITA` (gate FE-0..FE-4).
   - `AUDIT_FE_SEGNALI_E_SELETTORI_2026-07-07` (commit `c306498`) → input per ADR-025.
3. **Non è grezzo.** Usano l'ambiente **più maturo** del repo: workflow multi-agente (fino a 20 agenti / ~3.7M token), verifica adversariale con obbligo di evidenza `file:riga`. Probabile confusione con i vecchi `UPG-2026-03-*` FE (marzo 2026, in `docs/archive/specs/`), datati ma superati.

**Ma l'istinto del founder è per metà corretto:** c'è lavoro FE non concluso. Solo che **non è "un audit da fare", è remediation di audit già fatti e non implementati** — verificato nel codice, non a parole (§4).

---

## 2. Stato reale degli audit: la fase è chiusa

**20 audit inventariati, tutti committati e tracciati in git. Zero audit non committati al 2026-07-29.**

| Dominio | # | Note |
|---|---|---|
| Finanza | 11 | G6→G9.7 + G8.4: terminazione, wallet, integrità ledger, eventi orfani, trasparenza netto/lordo. Quasi tutti remediati/consuntivati. |
| Frontend | 3 | Deep-link (07-24), core-intuitività (07-21), segnali/selettori (07-07). |
| Cross | 4 | Obsolescenza (07-23, `824799d`), pre-release v1.0.14 (07-16), DB integrity (06-14), pre-delivery Alessio (04-17). |
| Security | 2 | Baseline (04-01), post-hardening (04-09). |

**Implicazione strategica:** continuare a cercare "l'ultimo audit" è il rischio più sottile. Un audit è un **generatore** di lavoro; a 18 giorni dal cliff serve un **riduttore**. Ciò che resta non è *scoprire*, è **eseguire**.

---

## 3. Divergenze memoria↔realtà (riconciliazione)

| Tema | Cosa si credeva | Realtà | Severità |
|---|---|---|---|
| Ultimo audit FE | «vecchio / mancante / grezzo» | È il più recente del progetto, luglio 2026, ambiente più maturo | ALTA |
| Audit obsolescenza + deep-link | «non committati» (snapshot MEMORY stale) | **Committati** (`824799d`, `4162e02`) | MEDIA |
| Blocco P | assimilato a «audit FE mancante» | È **nuovo sviluppo** (P1-P6 aperti), non un audit | MEDIA |
| Remediation FE recenti | «chiusi da tempo» | In gran parte **aperti/parziali** (§4) | ALTA |
| v1.0.14 | «vicino al lancio» | **Tagliata ma NON consegnata**; unico deployment reale = Alessio v1.0.13 | ALTA |
| Debito strutturale FE | «sotto controllo» | Comandamento 300/400 LOC violato su ~1 file su 4 | MEDIA |
| Security G1 | «RIPRESA / in avanzamento» | **ZERO codice in 6 settimane** | ALTA |

---

## 4. Verifica codice: i finding FE recenti sono ancora APERTI

Controllo `file:riga` sul codice reale (non sui report):

- **RC-1 (deep-link) — ANCORA PRESENTE.** `frontend/src/lib/url-state.ts:161-169` (`syncUrlParams`) riscrive l'URL dai soli filtri e **strippa** i parametri contestuali (`?cliente=`, `?from=`). `frontend/src/app/(dashboard)/contratti/page.tsx:190,193` legge `?cliente=` **solo** nel ramo `new=1` → il deep-link "Contratti di {nome}" viene ignorato **e** cancellato. Il modello corretto esiste già in casa (`/cassa` promuove il deep-link a stato al mount) ma non è generalizzato.
- **RC-2 (contratto FE-1.0 mono-intento) — ANCORA PRESENTE.** `frontend/src/lib/renewals-focus.ts:6,43` hardcoda `'overdue-rate'` come unico intento. Non esiste alcun `lib/context-focus.ts` / `useContextFocus` generalizzato: il contratto FE-1.0 (scroll+highlight+aria-live+stato-mancante) copre **1 flusso su 6**.

**Debito strutturale FE** (non catturato negli audit-status):
- **85 file >300 LOC, 44 >400** su 339 non-test (~1 su 4). Monoliti: `CommandPalette.tsx` 1189, `RecurringExpensesTab.tsx` 1137, `cassa/page.tsx` 1064, `rinnovi-incassi/page.tsx` 966.
- **Dead-code su disco:** `ProgressiTab.tsx` (739 LOC, mai importato), `OverdueRatesSheet.tsx`, componenti `Workspace*` mai montati.
- **Igiene di base BUONA:** ~zero TODO/FIXME reali, `any` quasi nullo (1 cast documentato), zero `@ts-ignore`, pattern vietati critici rispettati (nessun `text-muted-foreground` in `app/public/*`; `toISOString()` solo `.slice(0,10)` date-only).

Scala FE: 364 file `.ts/.tsx` (339 non-test), 27 `page.tsx`, 215 componenti, 33 hook. Suite: **~860 pytest / ~103 vitest**.

---

## 5. I veri open loop pre-POC (per criticità)

1. **G1 — cifratura `crm.db`.** ADR-013 *accepted* + spike SQLCipher validato, ma **ZERO codice di produzione in 6 settimane**, rinviato ~8 volte, spiazzato dalla finanza. Tier-1 del security gate (art. 9 GDPR su dati clinici/finanziari reali). *Nota:* Alessio è già in produzione con `crm.db` in chiaro → il rischio è **già vivo**, la POC lo amplia non lo crea.
2. **Coda release v1.0.15 bloccata.** `R0.1.5-live` (TLS Let's Encrypt) in HOLD per **passphrase SSH del VPS** non disponibile → blocca R0.4 → P1 → candidate. Il portale pubblico gira ancora su **cert self-signed** (avvisi browser anche per Alessio). Collo di bottiglia **esterno/umano**.
3. **v1.0.14 non consegnata.** Chiara ferma su v1.0.10 (bug fingerprint). Gate: restore backup reale sulla RC + installer su macchina non-dev. `main` indietro a v1.0.13.
4. **Blocco P (SPEC_P, P1-P6)** — il più grande blocco di **nuovo sviluppo** ancora da costruire (tabella `prestazioni_singole`, 7ª `ClasseContabile`, write-path, wallet, read-model Portafoglio, FE scelta 3 vie). Gated dietro R0. Assorbe la remediation dell'audit segnali/selettori (P4/P5).
5. **G-MAC / Daniele** — consegna macOS al primo prospect di spicco (§7). `SPEC_G-MAC`: G-MAC.0 fatto (T1 PASS), G-MAC.1-5 aperti, ADR-026 *proposed*.
6. **Remediation FE deep-link (RC-1/RC-2)** non avviata (§4).
7. **Debito strutturale FE** (monoliti + dead-code) — non release-blocking; differito post-v1.0.15 nell'audit obsolescenza.

---

## 6. Decisioni prese in questa sessione (locked)

| # | Decisione | Conseguenza |
|---|---|---|
| D1 | **FE remediation = priorità #1** della finestra dev | Fronte foreground; monoliti e coerenza-segnali differiti |
| D2 | **Audience POC = ibrida** (pilota controllato set → apertura commerciale entro dic) | G1 **non** blocca settembre; gate solo per l'apertura commerciale |
| D3 | **G-MAC re-incluso** (Daniele = primo prospect di spicco) | Target realistico **inizio settembre**; 15 ago = upside non-promesso |
| D4 | **Accesso macOS = CI (GitHub Actions) + Mac cloud a noleggio** (~20-50€) | Niente hardware locale (Mac di test non più disponibile); validazione interattiva su Mac cloud prima di Daniele |
| D5 | **Iscrizione Apple Developer = profilo Individual** | **Non richiede P.IVA**; parte oggi (pole più lunga, 1-3 giorni) |
| D6 | **P.IVA non blocca** Apple né il pilota | Materia commercialista/tributarista, milestone apertura-commerciale, incrocio NASpI |

---

## 7. Direzione pre-POC proposta (piano-of-record, non vincolante)

Le tre corsie **non competono per le stesse ore**: FE = foreground; G-MAC = calendario+CI+dev interlacciato; sblocchi = attese esterne.

### Corsia 1 — FE remediation (foreground)
- **B0** dead-code (`ProgressiTab`, `OverdueRatesSheet`, `Workspace*`) — ~0.5g, rischio nullo (warm-up)
- **B1** RC-1 deep-link (preserva param + promozione a stato al mount, pattern `/cassa`) — ~1.5-2g
- **B2** RC-2 `lib/context-focus.ts` + `useContextFocus` generalizzato ai 6 intenti — ~2-3g
- **B3** a11y FE-1 residue (AC-FE1-1..6) — ~2-3g
- ⛔ **Differito:** split monoliti 1000+ LOC (post-v1.0.15) · coerenza segnali wallet (è blocco P)

### Corsia 2 — G-MAC / Daniele (calendario + CI + dev interlacciato)
- **🔴 Giorno 0:** iscrizione **Apple Developer Individual** ($99, no P.IVA, no D-U-N-S; Apple ID + 2FA; poi app-specific password per notarizzare)
- Ratifica **ADR-026** (D-MAC-1..6)
- **G-MAC.1** portabilità `_FRPC_FILENAME` (~0.5-1g, Windows-side)
- **G-MAC.2** pipeline **GitHub Actions macOS**: build Nuitka/clang + `codesign` (hardened runtime, **firma anche i sub-binari incl. `frpc`**) + `notarytool` + staple. *Fallback:* firma/notarizzazione da Windows con **`rcodesign`**.
- **G-MAC.3** packaging (`launcher.command` + `install.sh` + DMG) — ~1-2g
- **G-MAC.4** validazione interattiva su **Mac cloud** (~20-50€, provisioning in ore) *prima* di Daniele
- **G-MAC.5** consegna Daniele (licenza + `instance_id` + DNS + runbook) → **inizio settembre**, call live (precedente Alessio)

### Corsia 3 — Sblocchi esterni + design G1 (calendario/sessioni, ~0 ore-dev)
- **SSH VPS** → R0.1.5-live TLS → R0.4 → candidate v1.0.15 (chiude cert self-signed)
- **Chiara**: verifica-campo (restore backup reale + installer macchina non-dev) → consegna v1.0.14 → allinea `main`
- **Tributarista**: call (pro_sedute + confine fiscale + **P.IVA** + incrocio **NASpI**)
- **Design G1** (cifratura crm.db): chiudi il design di dettaglio ora; implementazione dopo il cliff, **prima dell'apertura commerciale**

### Timeline
- **29 lug → 15 ago** — finestra dev (FE foreground · G-MAC interlacciato · sblocchi in parallelo) → chiusura con taglio candidate
- **16 → 31 ago** — materiale didattico (clienti + Alessio) · **freeze dev**
- **Inizio settembre** — consegna Daniele (pilota macOS) + finalizzazione Chiara · fase pilota
- **Set → Dic** — pilota → **G1 implementazione** → apertura commerciale

---

## 8. Rischi e incognite aperte

- **Tempi Apple** — l'iscrizione Individual (non ancora avviata) è l'unica pole che non si recupera accelerando dopo. Decide 15-ago-vs-inizio-settembre per Daniele.
- **Passphrase SSH VPS** — se persa, serve piano B per spedire i fix FE al pilota disaccoppiandoli dal gate TLS-live.
- **CI macOS Nuitka + codesigning** — primo giro: è dove si perdono 3-5 giorni (yak-shave). Con Mac cloud si valida, ma il build resta CI-bound.
- **P.IVA / NASpI** — non blocca Apple né il pilota; decisione commercialista, milestone apertura-commerciale.
- **Decisione tributarista** — `pro_sedute` resta PROVISIONAL finché non valorizzato: blocca parte del blocco P.

---

## 9. Cosa NON fare (anti-scope)

- ❌ Un altro audit (la fase audit è chiusa: 20 audit, tutti committati)
- ❌ Aprire blocco P nella finestra dei 18 giorni (nuovo sviluppo grande, gated dietro R0)
- ❌ Refactor dei monoliti 1000+ LOC a ridosso del cliff (rischio regressioni non intercettabili)
- ❌ Toccare la coerenza segnali wallet/receivable (è P4/P5)
- ❌ Promettere a Daniele il 15 ago prima che Apple approvi (under-promise/over-deliver su un prospect di spicco)

---

## 10. Riferimenti

- **Audit FE:** `AUDIT_DEEPLINK_CROSS_PAGE_2026-07-24.md` (`4162e02`), `AUDIT_FRONTEND_CORE_INTUITIVITA_2026-07-21.md` (`2de0520`, archive), `AUDIT_FE_SEGNALI_E_SELETTORI_2026-07-07.md` (`c306498`)
- **Spec aperte rilevanti:** `SPEC_R0_PROTEZIONE_RELEASE_V1_0_15.md`, `SPEC_P_PRESTAZIONI_SINGOLE_E_PORTAFOGLIO.md`, `SPEC_FRONTEND_CORE_INTUITIVITA.md`, `SPEC_G-MAC_CONSEGNA_MACOS.md`, `SPEC_FINGERPRINT_CROSSPLATFORM.md`
- **ADR:** ADR-013 (cifratura crm.db, accepted), ADR-025 (prestazioni singole/portafoglio, accepted), ADR-026 (macOS, proposed)
- **Codice citato:** `frontend/src/lib/url-state.ts:161-169`, `frontend/src/app/(dashboard)/contratti/page.tsx:190,193`, `frontend/src/lib/renewals-focus.ts:6,43`
- **Governance:** `AGENTS.md` (delivery loop), `LAUNCH_SCOPE.md` (scope), `docs/INDEX.md` (indice completo)

---

*Fine analisi non vincolante. Per rendere esecutiva la §7: migrare in `SPEC_PRE_POC.md` con gate falsificabili.*

# Session Handoff — 2026-06-14

**Scopo:** punto di ripresa. Da qui si riparte senza ricostruire il contesto. Snapshot dei thread aperti, con stato + prossima azione + doc di dettaglio.
**Branch:** `FitManager_Studio` · **Versione:** 1.0.10 · **Ultimo commit sessione:** vedi `git log`.
**Regola d'oro per riprendere:** leggere questo file → aprire il doc del thread che si vuole continuare → eseguire la "prossima azione".

---

## Board dei thread aperti

### Thread A — Remediation catalog.db (audit) — ATTIVO, è qui che eravamo
**Doc:** `docs/operations/DB_INTEGRITY_AUDIT_2026-06-14.md` (audit completo + analisi 32 orfani §8).
**Stato:**
- ✅ Audit read-only completo. catalog.db **pristino**; debito = detrito di migrazione in crm.db.
- ✅ **P2** — numeri canonici corretti (condizioni 5154, articolazioni 1452; doc + CLAUDE.md + memory).
- ✅ **Analisi 32 orfani** completata. **Confermato: le 5 schede impattate sono dati di TEST (gvera-dev)** → 58 referenze non preziose, decisione = merito di catalogo. Zero duplicati di nome; ID liberi → re-insert preservando l'ID.
**PROSSIMA AZIONE (P1 — passo 2): decidere/eseguire il re-insert dei keeper.**
- Ondata 1 (basso sforzo): 3 ricchi (Bear Hug Carry, Floor Press Bilanciere, Front Squat con Due KB) + 7 medi (Affondo Laterale, Belt Squat, Landmine Press, Rematore T-Bar, Seal Row, Rack Carry, Clean Kettlebell).
- Ondata 2 (curation founder): 22 gusci — distinguere veri (Bradford Press, Drag Curl, Curl al Cavo, Muscle Up, Split Jerk, allungamenti…) da ~5-7 sospetti (Buccinate da Seduto, Carico Kettlebell, Girata con Manubrio, Trazioni Laterali, Affondi Frontali mis-categorizzato).
- **GUARDRAIL:** mutazione → **backup crm.db + catalog.db prima** (`cp file.db file.db.bak`); pitfall #13 (rebuild catalog = `seed_taxonomy → populate_taxonomy → populate_conditions`); regola non negoziabile #11.
**Poi:** P1 DROP tabelle catalog stale da crm.db (dopo gli orfani, chiude ADR-003 a livello fisico, backup); P3 archiviare `crm_dev.db` + review 7 duplicati nomi catalog.db.

### Thread B — Strategia media cloud v2.2 — IN ATTESA DEL GATE (founder)
**Doc:** `docs/learning/LEARNING_MEDIA_CLOUD_ARCHITECTURE.md` (+ Appendice A impl.), `docs/technical/DELTA_v2.2_EXERCISE_LIBRARY_STRATEGY.md`.
**Stato:** decisione presa (hosting centrale media, routing per classificazione del dato). Corretto il punto ① (vincolo catalog.db read-only → **R1** build-time per la POC, **R2** manifest per v2). ADR-012 **riservato** (pending gate).
**PROSSIMA AZIONE:** **autotest §9 del founder** (a fonte chiusa). A gate superato → Claude Code applica gli 8 OP del delta a `EXERCISE_LIBRARY_STRATEGY.md`, ADR-012 riservato→accepted, azioni a valle (TUNNEL_SECURITY_BOUNDARY P2, DNS media, privacy policy, mail fornitore).
**Nota licenza emersa:** verificare con il fornitore non solo lo streaming video ma anche l'uso di **immagini + descrizioni** del bundle dentro catalog.db (uso diverso); rischio erosione differenziatore §0/AC-3 se le descrizioni derivano dal bundle → tenere lo strato scientifico AVGV-autoriale.

### Thread C — `is_fondamentale` lato UI — QUEUED (sbloccato da decisione di dominio)
**Doc:** `docs/technical/EXERCISE_LIBRARY_STRATEGY.md` §1.4/§5.6.1; concetto in `docs/learning/LEARNING_PROGRAMMAZIONE.md` ("Concetti dal campo").
**Stato:** campo cablato ma **vuoto** (0 marcati). Prerequisito = decisione founder su QUALI ~50-80 fondamentali. L'audit (Thread A) viene prima per dare la fotografia.
**PROSSIMA AZIONE:** dopo il cleanup catalog, proporre un criterio di selezione dei fondamentali (pattern, frequenza prescrizione, copertura muscolare) → marcare nel seed → UI (badge/filtro) + metrica copertura bundle.

### Thread D — Evoluzione `media.ts` — QUEUED (dipende dal media host)
**Doc:** `LEARNING_MEDIA_CLOUD_ARCHITECTURE.md` Appendice A.
**Stato:** `media.ts` vieta gli URL assoluti; due percorsi di risoluzione (dashboard `getMediaUrl` vs endpoint pubblico). Prerequisito = media host esistente (DNS + serving). Da fare insieme alla costruzione del media host, non prima.

---

## Strategia complessiva del founder (confermata)

Costruire l'architettura media contro un **DB/host di test** con clip placeholder (host reale cross-origin, non stub same-origin), su **esercizi reali** (non un catalog finto). Il **bundle di Alessio** (animazioni + immagini + descrizioni) arriverà come **specchio** di copertura/naming per il tuning, **non** come base di rebuild — l'audit ha confermato che catalog.db non ha nulla da ricostruire. Acquisto bundle **subordinato alla conferma scritta di licenza** (§5.1).

## Sequenza operativa consigliata alla ripresa
1. **Thread A** — eseguire il re-insert dei keeper orfani (backup prima). Chiude P1.
2. **Thread A** — DROP tabelle stale crm.db (ADR-003) + P3.
3. **Thread C** — `is_fondamentale` (criterio + marcatura + UI).
4. **Thread B** — quando il founder passa l'autotest §9.
5. **Thread D** — con la costruzione del media host.

## Guardrail permanenti
- DB sacri (crm.db, catalog.db, nutrition.db): **mai distruttivo senza backup preventivo** (regola #11). L'audit è read-only; le mutazioni no.
- Rebuild catalog.db = pipeline completa (pitfall #13).
- Quality gate prima di ogni commit (ruff + next build); il pre-commit hook lo applica.
- Documentazione allineata prima di nuovo sviluppo (no decisioni architetturali senza ADR; numeri canonici dall'audit).

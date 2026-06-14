# Session Handoff — 2026-06-14

**Scopo:** punto di ripresa. Da qui si riparte senza ricostruire il contesto. Snapshot dei thread aperti, con stato + prossima azione + doc di dettaglio.
**Branch:** `FitManager_Studio` · **Versione:** 1.0.10 · **Ultimo commit sessione:** vedi `git log`.
**Regola d'oro per riprendere:** leggere questo file → aprire il doc del thread che si vuole continuare → eseguire la "prossima azione".

---

## Board dei thread aperti

### Thread A — Remediation catalog.db (audit) — IN CORSO, Ondata 1 fatta
**Doc:** `docs/operations/DB_INTEGRITY_AUDIT_2026-06-14.md` (audit completo + analisi 32 orfani §8 + banner remediation).
**Stato:**
- ✅ Audit read-only completo. catalog.db **pristino**; debito = detrito di migrazione in crm.db.
- ✅ **P2** — numeri canonici corretti (condizioni 5154, articolazioni 1452; doc + CLAUDE.md + memory).
- ✅ **Analisi 32 orfani** completata (5 schede = dati TEST → decisione = merito di catalogo; ID liberi).
- ✅ **Ondata 1 ESEGUITA (sera 2026-06-14):** re-inseriti **10 keeper** in catalog.db preservando l'ID, `in_subset=0` (insert chirurgico + `seed_exercises.json` aggiornato + sha256). 3 ricchi (235/252/299) + 7 medi (15/16/46/73/81/140/142). Verifiche: 500→510, 466 attivi invariati, integrity OK, **orfani 32→22**. Backup `*.bak-threadA-20260614`. Scoperta: junction generate da `populate_taxonomy` (in_subset=1) → keeper inattivi = junction rigenerabili all'attivazione.
**PROSSIMA AZIONE (Ondata 2): curation founder dei 22 gusci residui.**
- 22 ID: 414 Board Press · 428 Bradford Press · 498 Panca Declinata French Press · 509 Dip al petto · 518 Drag Curl · 522 Girata con Manubrio · 599 Buongiorno alla Sbarra · 603 Curl al Cavo · 644 Carico Kettlebell · 656 Muscle Up · 700 Affondo Pass Through · 738 Allungamento Collo · 756 Split Jerk KB · 791 Allungamento Perone · 877 Buccinate da Seduto · 905 Trazioni Laterali · 962 Affondi Frontali · 984 Allungamento Quadricipiti · 987 Allungamento Gambe Post. · 1056 Allungamento In Alto · 1062 Dip alla Panca · 1064 Jump Squat con Peso.
- Distinguere veri da rinominare/scartare. Sospetti (possibile detrito auto-generato): Buccinate da Seduto, Carico Kettlebell, Girata con Manubrio, Trazioni Laterali, Affondi Frontali (962, mis-categorizzato `stretching`). I gusci hanno contenuto 1/7 → authoring richiesto (AC-3, dominio founder).
- **GUARDRAIL:** mutazione → backup prima (regola #11); per i gusci la meccanica è uguale (insert chirurgico + seed), ma il contenuto va scritto.
**Poi:** P1 DROP tabelle catalog stale da crm.db (dopo i 22, chiude ADR-003 a livello fisico, backup); P3 archiviare `crm_dev.db` + review 7 duplicati nomi catalog.db.

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

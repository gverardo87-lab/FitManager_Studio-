# SPEC_G9.4-BIS_READ_MODEL_CASSA

**Tipo:** specifica prescrittiva (cosa-deve-essere-vero). Bridge Chat→Code.
**Data:** 2026-07-05 · **Branch:** `FitManager_Studio`
**Stato:** ✅ **IMPLEMENTATA** (2026-07-05: bis.0 `85deb12` quick-win · bis.1 `99e5dd9` ClasseContabile+classify [218/218 movimenti reali, 0 celle violate] · bis.2 `3b788fa` migrazione superfici + write-guard categorie riservate [scoperta: trend/stats già divergevano sulla cella stringa-riservata/struttura-libera — unificata per D-CLASSIFY] · bis.3 `09d701e` bucket+sub-label+cassa-pura [AC-RM-6: il -140,42 dell'INC è spiegabile dalla response] · bis.4 `cd4046f`+`6e650a1` gemelli esaustività/no-re-inline). G9.4 eseguito in mezzo come da sequenza (`c3c5702` enforcement + `fd297e5` test semantici). Charter semantic-birth-auditor (§5) = da definire a valle, NON incluso.
**Blocco:** **G9.4-bis** — read-model della cassa (gemello di LETTURA della penna G9.1). **Parallelo a G9.4**
(write-enforcement, altra sessione): behavior-preserving, file disgiunti.
**Mappa di verità:** `ADR-022 Addendum II` · `AUDIT_CENSIMENTO_ASSI_SEMANTICI_CASSA_2026-07-04.md` (siti
`file:riga` = snapshot; esiti durevoli, righe da riverificare) · `INC-2026-07-03-falso-allarme-entrate-negative-cassa.md`
· `api/services/cash_categories.py` · `docs/technical/TASSONOMIA_FINANZIARIA.md` §2

---

## 1. Obiettivo (tesi falsificabile)

A fine gate: (1) **nessuna superficie di aggregazione** della cassa branca su `tipo`/`categoria` grezzi — tutte
consumano `classify_cash_movement()` o i predicati che ne derivano; (2) una **categoria nuova senza classe
dichiarata rompe la suite il giorno della nascita** (esaustività), non un KPI in produzione settimane dopo;
(3) **nessun KPI netto è nudo**: i componenti (lordo/contra/rettifica) sono nel contratto API; (4) l'asse
DENARO è **byte-identico** (golden pre/post).

## 2. Design

### 2.1 Le 6 classi (enum chiuso — dal censimento §4, oggi implicite)

| Classe | Predicato (struttura + categoria) |
|--------|-----------------------------------|
| `RICAVO_CONTRATTUALE` | ENTRATA ∧ `id_contratto≠NULL` (categoria ∈ `CONTRACT_CASH_IN`) |
| `ALTRO_INCASSO` | ENTRATA ∧ `id_contratto=NULL` ∧ `id_spesa=NULL` |
| `RETTIFICA_COSTO_FISSO` | ENTRATA ∧ `id_spesa≠NULL` ∧ categoria `STORNO_SPESA_FISSA` |
| `CONTRA_RICAVO` | USCITA ∧ categoria `RIMBORSO_CONTRATTO` (con o senza `id_contratto`: include erogazione wallet) |
| `COSTO_FISSO` | USCITA ∧ `id_spesa≠NULL` |
| `COSTO_VARIABILE` | USCITA ∧ `id_spesa=NULL` ∧ categoria ∉ OUT contrattuali |

### 2.2 `classify_cash_movement()` — casa e contratto

- Vive in **`api/services/cash_categories.py`** (casa naturale: ha già costanti e predicato bidirezionale).
  **Firma SCALARE** `(tipo, categoria, id_contratto, id_spesa_ricorrente)` → il modulo resta zero-DB/zero-ORM.
- **Totale per costruzione** sulla partizione strutturale (tipo × FK-ness copre ogni movimento possibile).
- **Fail-loud sulle celle vincolate** (D-LETTURA-FAIL-LOUD): ENTRATA con `id_contratto` e categoria ∉
  `CONTRACT_CASH_IN` → `ValueError`; USCITA con `id_contratto` e categoria ∉ `CONTRACT_CASH_OUT` → `ValueError`
  (gemello della penna). Le celle libere (spese, incassi manuali) classificano dalla struttura: l'asse A4
  (categorie spese, testo libero) resta aperto by-design — la stringa non decide mai la classe.
- Helper firmati derivati (es. `signed_amount_for(classe)`) SOLO se servono alle superfici — niente API
  speculative.

### 2.3 Trasparenza (D-NESSUN-NETTO-NUDO)

- `MovementStatsResponse` espone `entrate_lorde`, `rimborsi_contratti`, `storno_fisse` accanto ai netti
  (modello: `FinancialTrendResponse` G7.5b). Card Entrate (FE): sub-label "Lorde X · Rimborsi −Y" quando
  rimborsi > 0.
- `/movements/balance` dichiara l'asse **cassa-pura** in docstring/response description (semantica corretta,
  oggi anonima — F7).

## 3. Sequenza interna

| Step | Contenuto | Nota |
|------|-----------|------|
| **G9.4-bis.0** | Quick-win censimento: **F3** storno→costante (6 siti, anche in scrittura) · **F4** costanti asse stati credito/wallet in `contract_state.py` (~24 siti, 2 raw-SQL parametrizzati) · **F8** de-dup `signed_importo` → `financial/ledger.py` | ⏭️ primo commit della sessione-codice (prima di G9.4) |
| **G9.4-bis.1** | Enum `ClasseContabile` + `classify_cash_movement()` + test unitari (totalità, fail-loud, 6 classi) | additivo, zero consumer |
| **G9.4-bis.2** | Migrazione superfici (ordine per rischio): I1 `get_movement_stats` → I2 burn → I4 forecast (×2 query) → I6 `monthly_revenue` → I5 trend (già conforme nei numeri: adotta i simboli) → I8 recurring (lettura storno) | golden pre/post per superficie |
| **G9.4-bis.3** | Bucket in `MovementStatsResponse` + sub-label card Entrate + docstring asse cassa-pura su `/balance` | chiude F5/F7 e l'INC |
| **G9.4-bis.4** | Gemello di esaustività + no-re-inline (`tests/test_read_model_cassa.py`, pattern `test_occupazione_ssot`) | confluisce nel presidio G9.4-b |

## 4. Acceptance criteria

- **AC-RM-1 (totalità):** per ogni combinazione valida (tipo × FK × categoria nota) `classify` ritorna una e
  una sola classe; le celle vincolate violate → `ValueError` (test per ciascuna).
- **AC-RM-2 (esaustività alla nascita):** un test enumera le categorie del SSoT (costanti `cash_categories`) e
  fallisce se una non ha classe; aggiungere una costante-categoria senza classificarla = suite rossa.
- **AC-RM-3 (no re-inline):** le superfici I1/I2/I4/I5/I6/I8 non contengono più branch su literal
  categoria/storno — consumano `classify` o le costanti (verifica semantica, non grep).
- **AC-RM-4 (oracolo byte-identico):** `test_g75_cash_alignment` + golden test pre/post migrazione: stats,
  burn, forecast, trend, monthly_revenue identici al centesimo sul dataset dell'harness.
- **AC-RM-5 (trasparenza):** `/movements/stats` espone i bucket; con rimborsi > 0 la card Entrate mostra il
  sub-label; con rimborsi = 0 la UI è invariata.
- **AC-RM-6 (scenario INC):** il caso reale dell'INC (luglio: 375 lordi, 515,42 rimborsi) produce
  `totale_entrate=-140.42`, `entrate_lorde=375.00`, `rimborsi_contratti=515.42` — il numero è spiegabile
  dalla response da sola.

## 5. Charter agente `semantic-birth-auditor` (perimetro FINANZIARIO v1)

Terzo membro della famiglia auditor read-only (gemelli: `docs-code-drift-auditor`,
`financial-invariant-verifier`). Da definire in `.claude/agents/` a valle del gate. Controlli:
- **S1** censimento assi (set chiusi → SSoT + test gemello; assi "aperti" per literal = finding)
- **S2** interpreti impliciti (branch su valori grezzi fuori dal SSoT, salvo esenzione annotata DISPLAY-EXEMPT)
- **S3** totalità sul diff (membro nuovo → ogni interprete lo gestisce o fallisce rumoroso)
- **S4** netto nudo (response/KPI che netta senza esporre componenti)
- **S5** rito di nascita (membro nuovo senza SPEC/ADR + cattura learning)

**Regole del charter:** read-only (propone, non scrive) · ogni finding confermato si converte in STRUTTURA
(registrazione SSoT + test), mai babysitting permanente · metrica di successo: findings in calo nel tempo ·
invocazione pre-push quando il diff tocca costanti semantiche o branch su categoria/stato/tipo.

## 6. Fuori scope (dichiarato)

- A6 (stato Rate literal, ~25 siti): stabile da sempre, rischio basso — candidato a giro successivo.
- Denylist DISPLAY-EXEMPT (`!= "Cancellato"`, ADR-017 §3.2): asse diverso, INTATTE.
- Unificazione delle 3 query burn in una sola (I2+I4×2): la migrazione le fa consumare lo stesso predicato,
  il collasso in un helper condiviso è opzionale (non un AC).
- Estensione dell'agente oltre il perimetro finanziario (stati agenda, cascade FK, cache): v2, dopo che v1 ha
  dimostrato il segnale.

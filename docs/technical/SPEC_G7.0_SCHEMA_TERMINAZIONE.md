# SPEC G7.0 — Schema terminazione + marcatura completamento

**Tipo:** specifica prescrittiva (bridge Chat→Code), primo blocco dello scorporo G7.
**Stato:** ✅ **IMPLEMENTATA** (2026-06-24). Commit a sé, rilasciabile, zero comportamento di terminazione.
**Origine:** redatta in Claude Chat; i delta/conferme della verifica sul codice sono marcati `[Bridge Code 2026-06-24]`.
**SSoT di dominio:** `FINANCIAL_DOMAIN_MODEL.md` §3.1 (terminazione), §9.5.6/§9.5.7 (invarianti), §2 (asse denaro netto) · `IMPL_PLAN_FINANCIAL_REALIGN.md` §4.1 (schema).
**Posizione nella sequenza (scorporo G7):** **G7.0** → G7.1 (conguaglio + estensione SSoT) → G7.2 (reopen-allowlist) → G7.3 (endpoint terminate/preview) → G7.4 (inversi reopen/close/unterminate) → G7.5 (allineamento 9 query) → G7.6 (remediation runbook 3 muti).

---

## 0bis. Esito della verifica bridge `[Bridge Code 2026-06-24]`

Spec verificata contro il codice vivo prima dell'implementazione. **Verdetto: solida e accurata, implementabile come scritta — zero correzioni, due chiarimenti.**

**Conferme:**
- **§4.1** head Alembic `b2f1a9c7d4e3` (head unico, zero figli) → nuova revision `d83abb993ea8`.
- **§4** `schema_sync.sync_schema` aggiunge le colonne mancanti dai metadata ORM **e** crea l'indice `ix_{table}_{column}` con `CREATE INDEX IF NOT EXISTS` (idempotente) — `schema_sync.py:417-443`. "Zero codice schema_sync nuovo" confermato. Boot order `create_db_and_tables()` → `sync_schema()` confermato (`main.py:237-241`).
- **§5** `CATEGORIA_RIMBORSO_CONTRATTO` già in `cash_categories.py` (set `CONTRACT_CASH_OUT`) → **no-op**.
- **§3** i due punti di marcatura esistono: auto-close inline di `pay_rate` (`rates.py`) + ramo di chiusura di `_sync_contract_chiuso` (`agenda.py`).
- **AC-7.0-1 eseguito su CLONE di un backup reale** (`auto_20260620_082707.sqlite`, 39 contratti): 4 colonne aggiunte (default `0`/`None`), indice creato, **zero FK sulle nuove colonne** (solo le pre-esistenti `id_cliente`/`trainer_id`), righe preservate, idempotente al 2° boot. Backup-first rispettato (operato su copia temporanea).

**Chiarimenti (non correzioni):**
1. **§3 — `incassa_residuo` (G6) è già coperto.** L'auto-close di G6 passa da `_sync_contract_chiuso` → eredita la marcatura `COMPLETAMENTO` senza un terzo intervento. I 2 punti della spec sono completi.
2. **§3 — riapertura.** La marcatura è solo sul *close*; il *clear* del motivo quando `_sync` riapre (`riapertura_crediti`) NON è fatto in G7.0 (minimale, come prescrive §3). È innocuo (in G7.0 nessuno legge `motivo_chiusura`; la allowlist di G7.2 controlla solo su `chiuso=True`). Eventuale clear → rivalutare in G7.2.
3. **§6 — `netto_incassato` come `@computed_field`: empiricamente SAFE.** I builder di lista/dettaglio ricostruiscono via `ContractResponse.model_validate(c).model_dump()` + `**`. Un computed_field finisce nel `model_dump()`, ma i modelli *response* usano `extra='ignore'` (non `forbid`) → il kwarg `netto_incassato` viene ignorato in ricostruzione e ricomputato. Verificato empiricamente. (Se un domani si mettesse `extra='forbid'` sui response, si romperebbe — annotato.)

---

## 0. Cosa fa e cosa NON fa questo blocco

**Fa:** rende il sistema *capace di rappresentare* una terminazione — le colonne esistono, la categoria movimento esiste, i deployati le ricevono al boot, il completamento le popola. **NON fa:** nessuna terminazione avviene (nessun endpoint), nessun conguaglio si calcola, nessun rimborso si registra, `residuo()` non cambia ancora.

**Tesi falsificabile:** «lo schema regge le colonne su tutti i DB (fresh + deployati di Chiara/Alessio), e il completamento le marca, senza che nessun comportamento osservabile esistente cambi».
**Oracolo:** migrazione + schema_sync verdi su **clone del backup reale**, suite **byte-invariata**.

---

## 1. Le 4 colonne (PLAIN, mai FK — pitfall #15)

Su `contratti`, gemelle di `esito_rinnovo_motivo` (campi plain, nessun `foreign_key=`):

| Colonna | Tipo | Default | Semantica |
|---|---|---|---|
| `totale_rimborsato` | `float` | `0` | LORDO rimborsi, monotòno crescente. Mai ridotto a ritroso |
| `quota_stornata` | `float` | `0` | write-off del dovuto; azzera `residuo` senza riscrivere `prezzo_totale`. Monotòno |
| `data_chiusura` | `Optional[date]` | `None` | quando la chiusura ha effetto |
| `motivo_chiusura` | `Optional[str]` | `None` | esito economico, **enum chiuso a 4** (§2). Indicizzato |

`totale_rimborsato` e `quota_stornata` partono da 0 e **crescono solo** — questo è ciò che rende `netto_incassato = versato − rimborsato` derivabile senza toccare il lordo (Strada B, FDM §9.5).

---

## 2. L'enum di `motivo_chiusura` — chiuso a 4, copre TUTTE le vie a CHIUSO

```
COMPLETAMENTO          # auto-close: saldato + crediti esauriti
CONSUNZIONE            # (riservato) scadenza che regola il residuo post-scadenza
TERMINAZIONE_RIMBORSO  # terminazione anticipata, gamba rimborso (conguaglio < 0)
TERMINAZIONE_DECADENZA # terminazione anticipata / decadi, gamba storno (no cassa)
```

Scelta per **esito economico** (decisione Giacomo): il valore *guida la gamba* che l'endpoint G7.3 eseguirà. La *ragione* umana (recesso/risoluzione/consensuale) **non** vive qui — se servirà per analytics, sarà un campo separato in un blocco futuro. Non mescolare i due assi nello stesso campo.

> **⚠️ L'enum copre tutte e quattro le vie a CHIUSO, non solo le due nuove.** `COMPLETAMENTO` e `CONSUNZIONE` non sono terminazioni anticipate, ma stanno nello stesso campo perché *qualunque* via porti a CHIUSO deve qualificarlo. Se la migrazione ammettesse solo i due `TERMINAZIONE_*`, il completamento di §3 non avrebbe un valore da scrivere e la reopen-allowlist di G7.2 (che pretende `== COMPLETAMENTO`) si romperebbe al primo `pay_rate` che chiude.

`NULL` = legacy (contratti chiusi pre-G7) — letto come `COMPLETAMENTO implicito` solo in classificazione/runbook, **mai** riaperto automaticamente (la guardia di G7.2 lo tratta conservativamente). Questo doppio significato del NULL è dichiarato qui perché non diventi un mistero futuro.

> `[Bridge Code]` In G7.0 l'enum **non è enforced a livello di scrittura** (nessun endpoint scrive un motivo arbitrario; l'unico valore scritto è `COMPLETAMENTO`). L'enforcement formale dei 4 valori arriverà con lo schema d'input dell'endpoint `terminate` (G7.3). AC-7.0-5 verifica che il valore scritto sia nell'enum e che il non-chiuso resti `NULL`.

---

## 3. Marcatura del completamento (la seconda metà di G7.0 — load-bearing per G7.2)

I **due** percorsi di auto-close per completamento devono scrivere `motivo_chiusura = COMPLETAMENTO` quando chiudono:
- `pay_rate` (`rates.py`) — quando l'auto-close porta `chiuso=True`;
- il ramo di chiusura di `_sync_contract_chiuso` (`agenda.py`) — quando flippa `chiuso` per completamento.

> `[Bridge Code]` Terzo percorso `incassa_residuo` (G6) **già coperto**: chiude via `_sync_contract_chiuso`, eredita la marcatura. I 2 punti sopra sono completi.

Senza questa marcatura, la reopen-allowlist di G7.2 (che pretende `== COMPLETAMENTO` per auto-riaprire) **congelerebbe le riaperture legittime di completamento**: un contratto completato a cui cancelli per errore una seduta deve poter tornare a dovere quella seduta. È il prerequisito 1 della allowlist, e va installato **qui**, non in G7.2, perché G7.2 ci si aggancia.

> **Vincolo non negoziabile.** Questa marcatura **non deve cambiare alcun comportamento osservabile oggi**. Aggiunge un valore a un campo nuovo; non altera *quando* un contratto si chiude né *come* appare. **Aggiungi la scrittura del motivo, non riorganizzare nulla intorno** (non spostare `setattr`, non toccare il diff dell'audit). Va verificato che la suite resti byte-identica: un completamento che prima chiudeva, chiude ancora, ora con un motivo.

---

## 4. Migrazione a doppio binario (fresh + deployati)

- **Alembic**: nuova revision, `down_revision='b2f1a9c7d4e3'` (head unico, mai usato come down_revision — verificato §4.1 IMPL_PLAN). `batch_alter_table` add_column ×4 + indice `ix_contratti_motivo_chiusura` (nome `ix_{table}_{column}`, identico alla convenzione schema_sync → convergenza/idempotenza). `[Bridge Code]` Revision creata: `d83abb993ea8`. I float NOT NULL usano `server_default='0'` per backfillare le righe esistenti (gemello di `_resolve_default`).
- **schema_sync**: ADD-column automatico dai metadata ORM al boot, per i crm.db **già deployati** (Chiara/Alessio). Idempotente, frozen-safe. Zero codice schema_sync nuovo — è il path esistente (i campi nuovi compaiono nei metadata ORM, schema_sync li aggiunge + crea l'indice). `[Bridge Code]` Confermato `schema_sync.py:417-443`.
- **Boot order non negoziabile** (FDM/IMPL_PLAN §6): nessuna query ORM su `Contract` nel lifespan *prima* di `sync_schema`. La vera protezione contro "no such column" sui deployati è l'ordine di boot, non il `getattr`. `[Bridge Code]` Confermato `main.py:237-241`.

---

## 5. Categoria movimento

`RIMBORSO_CONTRATTO` (USCITA) in `cash_categories.py`: già presente come costante `CATEGORIA_RIMBORSO_CONTRATTO` e nei set `CONTRACT_CASH_OUT`/`CONTRACT_CASH_CATEGORIES` (Prereq P0). `[Bridge Code]` **Verificato presente → no-op.** Valore TEXT di `CashMovement.categoria`, nessuna DDL.

---

## 6. Schema response + tipo frontend

`ContractResponse` (`financial.py`) += `totale_rimborsato`, `quota_stornata`, `data_chiusura`, `motivo_chiusura` + `netto_incassato` come `@computed_field` (`= max(totale_versato − totale_rimborsato, 0)`). `ContractListResponse`/`ContractWithRatesResponse` ereditano. `types/api.ts` `Contract` **base** += i 5 campi (`float→number`, `Optional→string|null`) — su `Contract` base (non solo su `ContractListItem`) per propagare a tutti i discendenti, stessa lezione di Giro 1.

> `[Bridge Code]` Esposizione su `Contract` **base** è qui ACCURATA (≠ il caso `residuo` della SPEC_REVISIONE_PRE_G7): le 4 colonne sono campi reali e `netto_incassato` è un computed_field su `ContractResponse` base → anche le response POST/PUT le ritornano. Il round-trip `model_dump()`+`**` è SAFE (vedi §0bis nota 3).

> Nota: `netto_incassato` qui è derivato e **oggi == `totale_versato`** (nessun rimborso esiste ancora). Diventa load-bearing quando G7.3 registra il primo rimborso. Esporlo ora è gratis e prepara il frontend.

---

## 7. Acceptance criteria (il contratto di "fatto")

**AC-7.0-1 — Migrazione su dato reale.** La migrazione applica su un **clone del backup reale di Chiara** (backup-first, regola #11) senza errori; le 4 colonne esistono coi default corretti; i valori esistenti sono preservati. `PRAGMA foreign_key_list(contratti)` conferma **zero FK** sulle nuove colonne. `[Bridge Code] ✅ eseguito su clone (39 contratti).`

**AC-7.0-2 — schema_sync idempotente.** Su un crm.db deployato simulato (senza le colonne), il boot le aggiunge; un secondo boot è no-op. Test in `test_schema_sync.py`: 4 colonne + indice presenti, idempotenza verificata. `[Bridge Code] ✅ test_sync_schema_adds_termination_columns_and_index.`

**AC-7.0-3 — Completamento marca COMPLETAMENTO.** Dopo `pay_rate` che auto-chiude e dopo `_sync_contract_chiuso` che chiude per completamento, `motivo_chiusura == "COMPLETAMENTO"`. Test su entrambi i percorsi. `[Bridge Code] ✅ test_termination_schema.py.`

**AC-7.0-4 — Byte-invarianza.** La suite pre-esistente resta **verde e byte-identica nei valori osservabili**. Il test `test_manual_close_not_reopened_by_agenda_edit` resta **xfail-strict** — G7.0 non installa ancora la guardia, solo la marcatura su cui si aggancerà G7.2. `[Bridge Code] ✅ xfail confermato.`

**AC-7.0-5 — Enum esaustivo.** `motivo_chiusura`, quando valorizzato, appartiene ai 4 valori; il completamento scrive `COMPLETAMENTO`; `NULL` resta ammesso per i legacy. `[Bridge Code] ✅.`

**AC-7.0-6 — Response espone i 5 campi.** `GET /contracts/{id}` e `GET /contracts` (e la response base POST) espongono i 5 campi; `next build` verde coi tipi TS. `[Bridge Code] ✅.`

---

## 8. Cosa NON toccare in G7.0 (confini espliciti)

- **`residuo()` NON cambia** in G7.0. Resta `prezzo − versato`. L'estensione con `quota_stornata` è **G7.1**.
- **Nessun endpoint** terminate/close/reopen/unterminate. Tutto G7.3+.
- **Le 9 query NON cambiano.** Inerti finché non esiste un `RIMBORSO` reale (G7.3). G7.5.
- **`chiuso` resta settabile via `update_contract`.** La sua rimozione è decisione separata in G7.3 (o rimandata).

---

## 9. Bridge rule

Code è l'architetto della forma dall'interno. Output non banale (la doppia marcatura del completamento, il comportamento di schema_sync sui deployati) → learning capture + `BUILD_LOG.md`.

> **Il punto di rischio più alto di G7.0** è AC-7.0-1/AC-7.0-2: quella migrazione gira su PC di **clienti reali con dati reali**. È il momento di backup-first più importante di tutto G7. Il secondo punto di rischio è §3: è l'unico punto che tocca codice *vivo* — chirurgia, non riorganizzazione.

---

### Sequenza completa dello scorporo G7 (per contesto)

| Blocco | Scope | Rischio | Rilasciabile da solo |
|---|---|---|---|
| **G7.0** *(✅ fatto)* | Schema 4 colonne + categoria + marcatura completamento | Migrazione su deployati | ✅ |
| **G7.1** | `contract_settlement.py` (conguaglio puro, policy pluggable) + `residuo()` esteso con `quota_stornata` (getattr default 0) + `netto_incassato()` | Convergenza SSoT load-bearing | ✅ |
| **G7.2** | reopen-allowlist (`_sync_contract_chiuso` riapre solo se `== COMPLETAMENTO`) → `test_manual_close_*` xfail→xpass | Fix bug già latente | ✅ |
| **G7.3** | `POST /terminate` + `GET /settlement-preview`, 2 gambe atomiche, 4 BLOCKER §4.7, dialog FE | Il più alto (tutto si tocca) | ✅ |
| **G7.4** | reopen / close (decadi) / unterminate | Medio | ✅ |
| **G7.5** | allineamento 9 query al predicato bidirezionale, single-treatment | Inerte finché G7.3 non scrive RIMBORSO | ✅ |
| **G7.6** | remediation runbook 3 muti (id 4/9/13), per-contratto, mai bulk | Dato vivo | Runbook a sé |

**Da Giacomo (non blocca G7.0/G7.1/G7.2; blocca la *valorizzazione* di G7.3):** policy conguaglio (tributarista), conferma enum `motivo_chiusura`, R/T per i 3 contratti muti (id 4/9/13).

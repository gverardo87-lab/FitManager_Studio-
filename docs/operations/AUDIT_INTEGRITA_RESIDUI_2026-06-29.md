# Audit — Difetti residui di integrità contabile dopo G8.2-prep (audit-trail · force-delete · storico reopen)

> **Provenienza:** audit senior code-grounded read-only su `FitManager_Studio` dopo G8.1/G8.1.1/G8.2-prep
> (snapshot `8b699e7`). Trigger: terzo passaggio adversariale (Codex) sul filone finanziario, poi **verificato
> riga-per-riga** da Claude Code sul codice vivo.
> **Data:** 2026-06-29 · **Modalità:** sola lettura (nessun file mutato in questo giro).
> **Scope:** auditabilità di `terminate`/`reopen` + path amministrativo `DELETE force` + curation dello storico
> stato. **NON tocca** il calcolo economico (asse DENARO/EROGATO regge: 98 test mirati verdi al baseline).
> **Esito governance:** 3 difetti residui, tutti **completamenti di decisioni già accettate** (ADR-018/ADR-019),
> **nessuna nuova decisione** → `ADR-019 Addendum III` + `SPEC_INTEGRITA_CONTABILE_E_WALLET §16`.

## 1. Domanda di audit

Dopo che G8.1/G8.1.1/G8.2-prep hanno reso il modello contabile non-distruttivo e net-aware, restano punti in
cui **ciò che il sistema racconta di sé** (audit trail, worklist, timeline di stato) diverge da **ciò che il
modello prescrive** — anche se i conti tornano? Tre punti, tutti sulla *trasparenza/integrità amministrativa*,
non sull'aritmetica.

## 2. Executive summary

| # | Sev | Difetto | Verdetto verifica | È conseguenza residua di |
|---|-----|---------|-------------------|--------------------------|
| **P1** | media | La terminazione con **rimborso parziale** scrive **due verità diverse** sul rimborso nello stesso evento di audit grezzo | ✅ CONFERMATO | regressione introdotta dal **rimborso editabile** (ADR-019/020): `rimborso_out ≠ credito_cliente` |
| **P2** | media | `DELETE /contracts/{id}?force=true` **aggira** il guard sui crediti aperti → wallet/receivable vivi su un contratto soft-deleted | ✅ CONFERMATO (con precisazione) | il guard di **Bug-4** (ADR-019 Addendum II) è solo sul ramo `not force` |
| **P3** | bassa | Lo storico CRM-grade del reopen **non spiega la cassa preservata**: la curation cerca un campo mai emesso | ✅ CONFERMATO | intento documentato in **F6/D-CASSA-VISIBILE** (ADR-019 Addendum I) mai cablato |

Il core economico non perde denaro in nessuno dei tre. Tutti e tre degradano **auditabilità / difendibilità
amministrativa / supporto** — proprio dove il nuovo modello dovrebbe spiegarsi da sé.

## 3. P1 — Doppia verità sul rimborso parziale (auditabilità)

**Codice.** `api/routers/contracts.py::terminate_contract`:
- **Entry ricca** (`contracts.py:1756-1777`): `"importo_rimborsato": round(rimborso_out, 2)` (riga 1772) = la
  **cassa effettivamente uscita** (la USCITA `RIMBORSO_CONTRATTO`). Coerente al suo interno con
  `"totale_rimborsato": {old, new}` (riga 1760, delta = `rimborso_out`).
- **Companion lifecycle** (`contracts.py:1779-1787`): passa `importo_rimborsato=settlement.credito_cliente`
  (riga 1784), che `_audit.log_contract_lifecycle_transition` salva tal quale nel JSON `changes`
  (`_audit.py:72-73`) = il **credito teorico pieno**.

**Falsificazione.** Terminazione `CREDITO_CLIENTE` con `credito_cliente=600`, `importo_rimborso=400` (resto 200
→ wallet): la entry ricca scrive `importo_rimborsato=400`, la companion `importo_rimborsato=600`. **Stesso nome
campo, stesso evento di chiusura, due importi "rimborsati"** nel raw `audit_log`.

**Perché esiste solo ora.** Pre-G8.1 il rimborso era sempre l'intero `credito_cliente` → `rimborso_out ==
credito_cliente`, nessuna contraddizione. Il **rimborso editabile** (ADR-019/ADR-020) ha scisso i due valori
senza allineare la companion. È una **regressione** del rimborso editabile, non un difetto originario.

**Perché la UI lo maschera (e perché resta un bug).** `_curate_contract_event` tiene la entry ricca (caso #1) e
**scarta** la companion (caso #3, `motivo=="terminazione"` → `None`, `contracts.py:732-733`); inoltre la
curation legge `totale_rimborsato` delta (`contracts.py:694-698`), **non** `importo_rimborsato`. Quindi la
timeline è corretta. Ma una **query forense diretta** su `audit_log` (es. supporto, contenzioso, riconciliazione
contabile) trova due numeri di rimborso per la stessa chiusura: per un flusso finanziario legalmente rilevante è
un problema reale di auditabilità.

**Nessun invariante coinvolto.** I1/I4/I5 leggono ledger + colonne di contratto, **mai** il JSON di audit →
allineare la companion è invariant-neutral.

## 4. P2 — `force=true` orfana obbligazioni vive (path amministrativo)

**Codice.** `api/routers/contracts.py::delete_contract`:
- I **tre** guard RESTRICT (rate pendenti, crediti-seduta residui, **e** wallet/receivable APERTO) sono tutti
  dentro `if not force:` (gating a `contracts.py:1032`; il guard posizione-aperta a `1069-1091`). `force=true`
  li salta tutti.
- La cascade (`contracts.py:1124-1164`) tocca rate, `CashMovement`, eventi, contratto — **mai**
  `crediti_cliente` né `crediti_terminazione`.
- Le worklist `GET /dashboard/crediti-da-incassare` (`dashboard.py:747`) e `/rimborsi-da-erogare`
  (`dashboard.py:791`) filtrano `stato=="APERTO"` **senza join su `Contract.deleted_at`** → continuano a
  esporre gli orfani dopo il soft-delete del contratto.

**Precisazione vs il report originale ("bricked").** Il claim "il receivable diventa del tutto inattivabile" è un
filo troppo netto:
- `incassa`/`annulla` del receivable usano `_bouncer_credito` (`contracts.py:2178`) che fa join su `Contract`
  ma **non** filtra `deleted_at` → l'API tecnicamente risponderebbe ancora su un contratto soft-deleted.
- Ma l'**unico ingresso UI** (dettaglio contratto / `list_crediti_terminazione` via `_bouncer_contract_owned`,
  che filtra `deleted_at`, `contracts.py:1271`) → **404**. La worklist deep-linka al dettaglio contratto → 404.
- Il wallet `eroga` è client-scoped (`_bouncer_credito_cliente`, join su `Client`, `clients.py:1057`) → resta
  pienamente funzionante dal profilo cliente.
- `reopen` — che annullerebbe sia wallet sia receivable — passa da `_bouncer_contract_owned` → **404**: la via
  di rientro è chiusa.

**Stato risultante dopo `force`-delete con posizione aperta:** obbligazione viva (wallet e/o receivable APERTO),
contratto sparito dalla vista, reopen impossibile, receivable UI-orfanato, contesto storico degradato. Il core
non perde denaro, ma lo stato è **amministrativamente indifendibile**.

**Asimmetria che inchioda il finding.** `delete_client` ha **già** lo stesso guard *sempre attivo*
(`clients.py:1002`, RESTRICT su wallet/receivable APERTO, anch'esso da Bug-4). `delete_contract?force` è
l'**outlier**: il fix di Bug-4 (ADR-019 Addendum II) ha chiuso il ramo `not force` ma ha lasciato il buco su
`force`. Non è una nuova decisione — è il **completamento** di Bug-4.

## 5. P3 — Storico reopen incompleto (trasparenza)

**Codice.** `reopen_contract` emette nell'audit ricco (`contracts.py:2036-2049`): `motivo_chiusura`, `chiuso`,
`quota_stornata`, `rate_ripristinate`, `rate_riallineate`, `residuo_dopo`, `crediti_differiti_annullati`,
`wallet_cliente_annullati`, `wallet_erogato_riassorbito`, `totale_rimborsato{old,new}`,
`totale_versato_preservato`. **Non emette mai** `rimborso_preservato`.

La curation caso #2 (`contracts.py:711-727`) legge `changes.get("rimborso_preservato")` (riga 719) → **sempre
assente** → la riga "rimborso €X preservato" **non si stampa mai**. `residuo_dopo` (riga 713) e
`rate_riallineate` (riga 716) invece funzionano (sono emessi). È un **mismatch produttore/consumatore** su un
solo campo.

**Intento documentato, mai cablato.** Il `BUILD_LOG` F6 (riga 2328) descrive l'evento Riaperto come
"[residuo ricalcolato + rate riallineate + **rimborso preservato**]" e ADR-019 Addendum I (F6/D-CASSA-VISIBILE)
fa della cassa preservata l'informazione **più importante** del reopen non-distruttivo. Il dato per derivarla
**esiste già** nel payload (`totale_rimborsato`, `wallet_erogato_riassorbito`) → si fixa il **consumatore**, non
si allarga il produttore.

## 6. Rischio residuo (dichiarato, fuori scope di questo giro)

L'harness/checker strutturale `assert_contract_invariants` (`contract_state.py`) è cablato a runtime **solo su
reopen** (`contracts.py:77`, `2057`, via `_log_invariant_violations`, **log-only**). `terminate`,
`incassa_residuo`, `pay/unpay`, `eroga` wallet, `incassa` receivable **non** lo invocano. La rete strutturale
promessa non osserva ancora quei path.

**Questo è già noto e deliberatamente differito** da `AUDIT_POSIZIONE_FINANZIARIA_E_INVARIANTI_2026-06-28.md`
("predisposta per 409", log-only). NON è parte del fix minimo: allargare il rollout dell'harness è un blocco di
hardening a sé (il *dopo* logico di A/B/C), non una correzione. Lo si registra qui per non perderlo.

## 7. Decisioni di fix (3 slice, ciascuna con tesi falsificabile)

Principio guida (founder): **codice essenziale, testabile, falsificabile; 1 commit per slice; nessun refactor
d'architettura.** Le decisioni A e C sono confermate dal founder (2026-06-29); B presa per simmetria con
`delete_client`.

- **Slice A — normalizza l'audit della terminazione parziale.** Nel call-site di
  `log_contract_lifecycle_transition` (`contracts.py:1784`) passare `rimborso_out` (cassa uscita) invece di
  `settlement.credito_cliente` (credito teorico). Scelta `rimborso_out` (non `None`): tiene la companion
  auto-descrittiva **e** allineata alla entry ricca. `residuo_annullato` (riga 1785) **fuori scope** (semantica
  distinta "residuo annullato" ≠ "quota stornata", nessuna seconda contraddizione).
  - **Tesi falsificabile:** dopo terminazione `credito=600 / rimborso=400 / 200→wallet`, le due entry di audit
    grezzo per la chiusura **concordano** su `importo_rimborsato` (entrambe 400). Fail se una dice 400 e l'altra 600.
- **Slice B — il guard posizione-aperta vale SEMPRE.** Estrarre il RESTRICT su `crediti_cliente`/
  `crediti_terminazione` APERTO **fuori** da `if not force:` → sempre 409. Policy senior: `force` abbuona
  rate/crediti-seduta (write-off che il trainer conosce), **non** una posizione finanziaria aperta con
  controparte (si chiude via eroga/incassa/annulla, path auditato). Simmetrico a `delete_client`.
  - **Tesi falsificabile:** `force`-delete con wallet aperto → 409; con receivable aperto → 409; i delete
    forzati **senza** posizioni aperte restano verdi. Fail se il contratto sparisce ma resta una posizione APERTA in worklist.
- **Slice C — completa lo storico del reopen dai dati già presenti.** In `_curate_contract_event` caso #2,
  sostituire il lookup morto `rimborso_preservato` con derivazione da `totale_rimborsato.new` +
  `wallet_erogato_riassorbito`. Wording completo (scelta founder): "rimborso €{new} preservato" quando `new>0`,
  e — se `wallet_erogato_riassorbito>0` — append "(di cui €Y da wallet riassorbito)". Reopen senza cassa → niente riga.
  - **Tesi falsificabile:** dopo reopen con cassa preservata e/o wallet riassorbito, `GET /contracts/{id}/history`
    espone il fatto nel dettaglio dell'evento "Riaperto". Fail se la timeline dice "riaperto" ma tace la cassa
    preservata pur avendo i dati nell'audit.

**Ordine:** A → B → C, tre commit, ciascuno con la propria tesi. Backend-only; FE invariato (la timeline legge
già `dettaglio`). Gate per slice: i cluster `test_contract_terminate` / `test_wallet_cliente` /
`test_contract_history` / `test_contract_integrity` / `test_credito_differito` restano verdi + 1-2 test nuovi
per slice.

## 8. Output → governance

1. **ADR-019 Addendum III** — i 3 difetti come **conseguenze residue** di decisioni già accettate
   (P1 ↔ rimborso editabile ADR-019/020 + auditabilità ADR-018; P2 ↔ Bug-4 Addendum II; P3 ↔ F6 Addendum I);
   nessuna nuova decisione; stato implementazione PENDENTE al momento del commit governance.
2. **SPEC_INTEGRITA_CONTABILE_E_WALLET §16** — gli AC falsificabili (§7 sopra) che guidano i test.
3. **Limite dichiarato:** audit + decisioni; la validazione runtime avviene in fase implementativa (suite +
   `check-all.sh` + Playwright live a env libero).

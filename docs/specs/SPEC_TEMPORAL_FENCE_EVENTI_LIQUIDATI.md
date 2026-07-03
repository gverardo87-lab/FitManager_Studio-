# SPEC G7.8-ter — Temporal fence: eventi contabilizzati di contratti liquidati

**Stato:** ⏳ **DA IMPLEMENTARE** (governance docs-only, zero codice prodotto)
**Tipo:** specifica prescrittiva (bridge Chat→Code) · **ADR di copertura:** `ADR-023` (accepted 2026-07-03)
**Origine:** audit fattore-tempo del founder (2026-07-03) + ricerca competitor su fonti ufficiali
(Mindbody, WellnessLiving, Zen Planner/Daxko, Glofox/ABC, Vagaro — leggi L1-L5 in ADR-023).
**Posizione:** completa la serie agenda×denaro G7.8 (rinvio libera credito) → G7.8-bis (stati-penale) →
**G7.8-ter (fence temporale)**. Coordinate `file:riga` = snapshot 2026-07-03 (`3f47b20`); esiti durevoli,
righe da riverificare a implementazione.

---

## 0. Tesi unica (falsificabile)

> **T1 — La base del conguaglio è immutabile finché il contratto resta liquidato.**
> Su un contratto `chiuso` NON auto-riapribile (`NOT puo_auto_riaprire` ⇔ motivo `TERMINAZIONE_*` /
> `CONSUNZIONE` / `NULL`), nessuna mutazione di evento può cambiare l'insieme delle sedute
> CONTABILIZZATE (Completato + Cancellato_Tardivo + No_Show) che ha determinato la liquidazione
> (rimborso, storno, receivable, wallet). L'unico varco è `POST /reopen`.

Falsificabile su quattro fronti (contratto terminato con conguaglio già liquidato):
1. `Completato → Cancellato` via `PUT /events/{id}` → **409**, storia e colonne intatte.
2. `No_Show → Cancellato` → **409** (la penale è entrata nel conguaglio, G7.8-bis).
3. `DELETE /events/{id}` su un `Completato` → **409**.
4. `Programmato → Cancellato` → **200** (pulizia prenotazione orfana: NON è base di conguaglio;
   l'occupazione scende, il contratto RESTA chiuso via reopen-allowlist).

## 1. Modello ratificato (decisioni vincolanti — ADR-023)

| Decisione | Contenuto |
|---|---|
| **D-TF-BASE** | Fence su (a) cambio `stato` con partenza O arrivo ∈ CONTABILIZZATI, (b) delete di evento CONTABILIZZATO — quando `contract.chiuso ∧ NOT puo_auto_riaprire(contract)` |
| **D-TF-PULIZIA** | Liberi sul terminato: transizioni fra stati non-contabilizzati (es. `Programmato→Cancellato/Rinviato`), delete di non-contabilizzati, edit di date/titolo/note |
| **D-TF-VARCO** | Il 409 indirizza a `POST /reopen`; dopo reopen tutto torna editabile; la ri-terminazione ricalcola sul corretto |
| **D-TF-LEGACY** | I chiusi `motivo NULL` sono DENTRO il fence (stessa deliberatezza della reopen-allowlist) |
| **D-TF-COMPLETAMENTO** | I chiusi `COMPLETAMENTO` sono FUORI (auto-reopen simmetrico già corretto, zero conguaglio) |

## 2. Predicati canonici

Nuova costante SSoT in `api/services/contract_state.py` (terzo asse, accanto a credito e slot):

```python
# Asse CONTABILIZZATO (ADR-023): la base di compute_settlement (G7.9 + G7.8-bis) — ciò che è
# entrato in un conguaglio non si riscrive finché il contratto resta liquidato (temporal fence).
STATI_SERVIZIO_CONTABILIZZATO = frozenset({"Completato"}) | STATI_PENALE
```

Predicato del fence (helper puro, consumato dai 2 guard):

```python
FENCE ⟺ contract.chiuso AND NOT transitions.puo_auto_riaprire(contract)   # FSM G9.3, riuso
BLOCCA_UPDATE(old, new) ⟺ old ∈ STATI_SERVIZIO_CONTABILIZZATO OR new ∈ STATI_SERVIZIO_CONTABILIZZATO
BLOCCA_DELETE(stato)    ⟺ stato ∈ STATI_SERVIZIO_CONTABILIZZATO
```

Nota G7.8-bis: `count_sedute_erogate`+`count_sedute_penali` (transitions.py) DEVONO restare la somma
esatta di questo frozenset — a implementazione, derivarli o presidiarli con un assert nel test SSoT
(`test_occupazione_ssot.py`), mai due verità.

## 3. Inventario siti (CAMBIA / LASCIA)

### CAMBIA — 2 guard in `api/routers/agenda.py`
- **`update_event`** (`:499` circa): nuovo **Bouncer 5** dopo il Bouncer 4, PRIMA di applicare
  `update_data`: se l'evento ha `id_contratto`, `update_data` contiene `stato` diverso dall'attuale, e
  vale FENCE ∧ BLOCCA_UPDATE → **409** con microcopy §5. (Il Bouncer 4 `Completato→Rinviato` resta:
  copre i contratti APERTI; sul terminato il Bouncer 5 assorbe il caso.)
- **`delete_event`** (`:585` circa): stesso guard con BLOCCA_DELETE → **409**.

### LASCIA (verificati)
- `create_event`: già 400 su contratto chiuso (`:421-424`) — invariato.
- `id_contratto`: NON riassegnabile via update (`EventUpdate` docstring `:102`) — già protetto.
- D&D/resize del calendario: passano solo date → fuori dal fence per D-TF-PULIZIA.
- `_sync_contract_chiuso`/reopen-allowlist: invariati (il fence agisce PRIMA, il sync non vedrà mai la
  mutazione vietata).
- `terminate`/`reopen`/settlement: zero modifiche — il fence è interamente in agenda.

## 4. Acceptance criteria

| AC | Verifica |
|---|---|
| AC-TF-1 | `Completato→Cancellato` su TERMINAZIONE_RIMBORSO → 409; evento e `crediti_usati` invariati |
| AC-TF-2 | `No_Show→Cancellato` su terminato → 409 (base penale protetta) |
| AC-TF-3 | `Programmato→Completato` su terminato → 409 (arrivo contabilizzato: non si aggiunge base a liquidazione fatta) |
| AC-TF-4 | `DELETE` di `Completato` su terminato → 409; di `Programmato` → 200 |
| AC-TF-5 | `Programmato→Cancellato` su terminato → 200; occupazione scende; contratto resta chiuso |
| AC-TF-6 | Su chiuso `COMPLETAMENTO`: tutti gli edit passano come oggi (incl. auto-reopen da revoca) |
| AC-TF-7 | Chiuso legacy `motivo NULL`: fenced come TERMINAZIONE_* |
| AC-TF-8 | Dopo `POST /reopen`: gli stessi edit di AC-TF-1/3/4 passano (varco); ri-terminazione ricalcola sul corretto |
| AC-TF-9 | Eventi senza `id_contratto`: mai toccati dal fence |
| AC-TF-10 | Suite invariata sul resto; asse DENARO byte-identico (solo guard, zero calcoli) |

## 5. Microcopy (409, italiano)

> "Contratto terminato: la seduta è entrata nel conguaglio di chiusura e non è modificabile.
> Riapri il contratto per correggere la storia, poi termina di nuovo."

## 6. Test plan + piano commit

`tests/test_temporal_fence_eventi.py` (~10 test, mappa 1:1 sugli AC) + estensione di
`test_occupazione_ssot.py` (baseline del nuovo frozenset + coerenza con count_sedute_erogate/penali).
**1 commit backend** (`feat: G7.8-ter — temporal fence eventi contabilizzati (ADR-023)`), suite piena,
verifier, fold-back docs (questa spec consuntivata → archive, INDEX, BUILD_LOG), push su ok founder.
FE: nessun lavoro obbligatorio (409 → toast via `extractErrorMessage`); disabilitazioni proattive
opzionali censite per G8.4.

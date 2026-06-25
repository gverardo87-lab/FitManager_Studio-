# RUNBOOK — Remediation contratti "muti" (chiusure legacy, `motivo_chiusura = NULL`)

**Stato:** operativo · **Owner:** AVGV (con il trainer per le decisioni) · **Blocco:** G7.6 (chiude la catena G7)
**Prerequisiti:** G7.3 (`POST /terminate`) + G7.4 (`POST /reopen`) in produzione · **Modello:** `FINANCIAL_DOMAIN_MODEL.md` §7/§9.5 · `IMPL_PLAN_FINANCIAL_REALIGN.md` §7

---

## 1. Cos'è un "contratto muto" e perché esiste

Un **contratto muto** è un contratto con `chiuso = 1` **e** `motivo_chiusura IS NULL` (non eliminato). Il `NULL`
è il segno di una **chiusura avvenuta PRIMA di G7.0** (quando lo schema non aveva ancora le 4 colonne di
terminazione) — tipicamente una chiusura **manuale** (vecchio `PUT chiuso=True`, rimosso in G7.3b) o da **import**
di dati storici. Da G7.0 in poi ogni chiusura scrive un `motivo` (auto-close → `COMPLETAMENTO`, terminazione →
`TERMINAZIONE_*`), quindi **non si generano nuovi muti**: questa è una bonifica una-tantum dello storico.

**Comportamento attuale già corretto (NON è un bug aperto):** la reopen-allowlist (G7.2) tratta il `NULL` come
**COMPLETAMENTO implicito** → un muto **non si auto-riapre** (né credit-driven da agenda, né payment-driven da
`unpay_rate`). In UI rende come "Chiuso". Per la **maggioranza** dei muti (completamenti veri) questo è giusto e
**non serve alcuna azione**. La remediation serve **solo** ai muti il cui stato chiuso **mente** sulla realtà
(relazione viva, sedute prepagate non erogate, soldi ancora dovuti).

> ⚠️ **Gli ID dei muti sono diversi su ogni DB.** Le vecchie note ("id 4/9/13") erano specifiche del crm.db di un
> trainer. **Mai** lavorare su ID hard-coded: identificarli sempre con la query diagnostica (§4) sul DB in oggetto.

---

## 2. Principi non negoziabili

1. **Per-contratto, MAI bulk.** Ogni muto ha un suo profilo e una sua decisione. Niente UPDATE di massa.
2. **Decisione col trainer.** R vs T vs LEAVE dipende dalla realtà del rapporto, che solo il trainer conosce.
3. **Solo via endpoint.** Mutazioni esclusivamente via `POST /reopen` / `POST /terminate` (atomici, auditati,
   con tutte le invarianti). **Mai** UPDATE diretto in SQL sul DB (salta audit e invarianti).
4. **Backup-first** (regola #11 CLAUDE.md): `cp crm.db crm.db.bak` PRIMA di toccare qualunque cosa.
5. **Snapshot PRE e POST** per ogni contratto (read-only), per dimostrare cosa è cambiato.
6. **Reversibile.** R è invertito da terminate; T è invertito da reopen. Documentare l'inverso di ogni passo.

---

## 3. Step 0 — Backup

```bash
cp data/crm.db data/crm.db.bak    # timbrare con la data nel nome se più di uno
```

---

## 4. Step 1 — Diagnostica (data-driven, READ-ONLY)

Identifica i muti **e** arricchiscili col profilo che guida la decisione. SQLite read-only, zero scritture:

```sql
SELECT
  c.id, c.id_cliente, c.tipo_pacchetto, c.prezzo_totale, c.totale_versato,
  c.crediti_totali, c.data_scadenza,
  (SELECT COUNT(*) FROM agenda e WHERE e.id_contratto=c.id AND e.categoria='PT'
     AND e.stato!='Cancellato' AND e.deleted_at IS NULL)                       AS crediti_usati,
  (SELECT COUNT(*) FROM agenda e WHERE e.id_contratto=c.id AND e.categoria='PT'
     AND e.stato='Programmato' AND e.deleted_at IS NULL)                       AS sedute_programmate,
  (SELECT COUNT(*) FROM rate_programmate r WHERE r.id_contratto=c.id
     AND r.deleted_at IS NULL AND r.stato!='SALDATA')                          AS rate_non_saldate
FROM contratti c
WHERE c.chiuso=1 AND c.motivo_chiusura IS NULL AND c.deleted_at IS NULL
ORDER BY c.id;
```

Comando: `python -c "..."` con `sqlite3.connect('file:data/crm.db?mode=ro', uri=True)` (mai connessione in
scrittura per la diagnostica).

---

## 5. Step 2 — Classificazione per profilo → decisione

Confronta `crediti_usati` con `crediti_totali`, lo stato di `data_scadenza`, e le due spie di inconsistenza
(`rate_non_saldate`, `sedute_programmate`). **Decidi col trainer**, mai meccanicamente.

| Profilo | Lettura | Decisione |
|---|---|---|
| `crediti_usati >= crediti_totali` **e** `versato == prezzo` (saldato), scadenza passata | **Completamento implicito**: servizio reso, soldi incassati, pacchetto esaurito. Chiuso a ragione, gli manca solo l'etichetta. | **LEAVE** (§6.A). Nessuna azione: `NULL` = COMPLETAMENTO implicito, G7.2 non lo riapre. |
| `crediti_usati < crediti_totali`, scadenza **futura**, relazione **viva** (sedute prepagate da erogare) | Lo stato chiuso **nasconde un'obbligazione**: il trainer deve ancora quelle sedute. | **R — REOPEN** (§6.B, default). Torna ATTIVO/SOSPESO, l'obbligo ridiventa visibile. |
| `crediti_usati < crediti_totali`, rapporto **finito in anticipo** (non proseguirà) | Recesso reale mai formalizzato. Va a conguaglio (rimborso o storno). | **T — TERMINAZIONE** (§6.C): reopen → terminate. |
| `rate_non_saldate > 0` su un chiuso | Inconsistenza: chiuso ma con soldi ancora dovuti. | **Investiga** col trainer → quasi sempre **R** (riapre, l'incasso/residuo ridiventa azionabile), poi gestione normale. |
| `sedute_programmate > 0` su un chiuso | Inconsistenza minore: sedute future agganciate a un chiuso. | **Investiga**: se la relazione è viva → **R**; altrimenti ripulire le sedute orfane via agenda. |

**Regola d'oro:** se hai un dubbio fra LEAVE e R, e c'è anche una sola seduta prepagata non erogata o un euro
ancora dovuto, **R è la scelta sicura** (rende visibile l'obbligazione; è reversibile).

---

## 6. Step 3 — Esecuzione (per opzione)

Per **ogni** contratto: snapshot PRE → azione → snapshot POST. Snapshot read-only (osservabili reali):
- `GET /api/dashboard/reconciliation` (audit contratti vs ledger)
- `GET /api/movements/stats` (saldo + aggregati cassa)
- dump del contratto (la query §4) + `SELECT * FROM audit_log WHERE entity='contract' AND entity_id=<id>`

### 6.A — LEAVE (completamento implicito)

**Nessuna azione.** Il `motivo NULL` è già interpretato come COMPLETAMENTO implicito (G7.2). Annota la decisione
nel registro di remediation (§7). *(Non esiste endpoint per ri-etichettare `motivo=COMPLETAMENTO` su un chiuso, ed
è inutile: il comportamento è già corretto. Un'eventuale back-label di massa sarebbe un cambiamento separato, fuori
da questo runbook.)*

### 6.B — R · REOPEN (default per relazione viva)

```
POST /api/contracts/{id}/reopen      # G7.4 — inverso esplicito state-driven
```

Inverte ciò che lo stato mostra: annulla un eventuale rimborso (qui assente), azzera lo storno (qui assente),
ripristina le rate non-saldate soft-eliminate, riporta `chiuso=False` e `motivo/data_chiusura=NULL`. Sui muti
(nessuno storno, nessun rimborso) si riduce a `chiuso=False`.

**POST atteso:** `chiuso=False`; lifecycle → ATTIVO (se scadenza futura) o SOSPESO (se scaduto con crediti
residui); `totale_versato == Σ ENTRATA` **invariato** (R non tocca le ENTRATA); rate ripristinate; audit
`UPDATE` + transizione lifecycle presenti.

### 6.C — T · TERMINAZIONE (rapporto finito in anticipo)

Il contratto è chiuso → `terminate` rifiuta un chiuso (400). Procedura in **due passi atomici**:

```
POST /api/contracts/{id}/reopen                                   # 1) riporta aperto
POST /api/contracts/{id}/terminate  { "data_chiusura": "<≤oggi>",  # 2) chiusura formale + conguaglio
                                       "metodo_rimborso": "<se RIMBORSO>" }
```

- `data_chiusura` può essere **retroattiva** ma **mai futura** (D4, G7.5c → 422).
- Il conguaglio è calcolato dal backend su `sedute_erogate` (Event `Completato`): RIMBORSO se il cliente ha
  pagato più del reso (richiede `metodo_rimborso`), SALDO_A_PERDERE (write-off del residuo) altrimenti.
- ⚠️ Se `terminate` propone un **RIMBORSO** ma **nessun rimborso reale è mai avvenuto**, è il segnale che T è la
  scelta sbagliata (o `sedute_erogate` è sottostimato): fermarsi e rivalutare → quasi sempre il caso è **R**.

**POST atteso:** `chiuso=True`, `motivo=TERMINAZIONE_*`, `data_chiusura` valorizzata; se rimborso →
`Σ USCITA RIMBORSO_CONTRATTO == totale_rimborsato`; zero rate PENDENTI; audit completo.

---

## 7. Step 4 — Registro di remediation (per-contratto)

Tieni una riga per contratto toccato (anche i LEAVE), per tracciabilità e reversibilità:

```
<data> | contratto #<id> (cliente #<id_cliente>) | profilo: <…> | decisione: LEAVE/R/T
  PRE:  chiuso=…, motivo=…, versato=…, residuo=…, lifecycle=…, saldo_cassa=…
  AZIONE: <endpoint chiamato / nessuna>
  POST: chiuso=…, motivo=…, residuo=…, lifecycle=…, Σ ENTRATA=…, Σ USCITA RIMBORSO=…
  INVERSO: <reopen / terminate per annullare>
```

---

## 8. Reversibilità

| Azione | Inverso |
|---|---|
| R (reopen) | `POST /terminate` (ri-chiude con conguaglio) **oppure** ripristino da `crm.db.bak` |
| T (terminate) | `POST /reopen` (annulla rimborso+storno, ripristina rate) |
| LEAVE | nessuna mutazione, niente da invertire |

In caso di errore non recuperabile via endpoint: **stop**, ripristino da `crm.db.bak`, analisi a freddo.

---

## Appendice A — Profilo dei muti nel crm.db di sviluppo (2026-06-25, esempio reale)

19 muti, eterogenei (a riprova che NON è una popolazione uniforme):
- **16** con `crediti_usati == crediti_totali` + saldati + scadenza passata → **LEAVE** (completamenti impliciti).
- alcuni con `sedute_programmate > 0` su chiuso (es. contratti #4 +1, #9 +1, #13 +3, #26 +1, #28 +1) → inconsistenza
  minore da investigare.
- **#29** con una rata non saldata su contratto chiuso → inconsistenza "soldi dovuti su chiuso" → investiga (→ R).

**Contrasto col caso storico di un trainer reale** (descritto in IMPL_PLAN §7): lì i muti erano `crediti_usati=0`
+ scadenza **futura** + saldati → profilo "relazione viva / sedute tutte da erogare" → **R**. Profilo opposto a
quello prevalente qui. **Conferma che il runbook deve restare profilo-based e mai per-ID.**

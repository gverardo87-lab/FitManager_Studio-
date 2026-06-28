# Audit specifico — Reopen di un contratto terminato (scenari)

> **Provenienza:** audit code-grounded read-only su `FitManager_Studio` dopo G7.9/G7.10 (terminazione bilaterale).
> **Data:** 2026-06-28 · **Modalita:** sola lettura.
> **Trigger:** osservazione del founder — riaprire un contratto terminato non e' un'operazione sola ma una
> *famiglia di scenari*; il movimento fiscale collegato non e' scontato; "tutto o niente" e' riduttivo. Un
> vero CRM aziendale gestisce gli scenari. Questo audit li enumera e ne deriva il principio.
> **Scope:** `reopen_contract` + interazione con cassa/fiscale/wallet/rinnovo. Fonda **ADR-019** e **ADR-020**.

## 1. Domanda di audit

Riaprire un contratto precedentemente terminato e' un singolo "annulla tutto", oppure ci sono scenari
distinti che richiedono trattamenti diversi — e qual e' il modello che li unifica senza casi-speciali?

## 2. Executive summary

`reopen_contract` esegue **sempre, incondizionatamente**, lo stesso reverse: soft-cancella le scritture di
cassa di terminazione (rimborso + incasso conguaglio), annulla i receivable, azzera lo storno, ripristina le
rate, riapre. Un'unica guardia (`if not chiuso -> 400`). Ma il reverse cieco e' **sbagliato in piu' scenari**:

1. **soft-cancella movimenti di cassa fiscalmente rilevanti** scavalcando la protezione del mastro
   (`delete_movement` vieta — 400 — di eliminare un movimento con `id_contratto`), mutando periodi gia'
   dichiarati;
2. **fa sparire reddito realmente incassato** (un conguaglio incassato dal cliente) come se non fosse mai entrato;
3. **ignora le dipendenze a valle** (contratto rinnovato; in futuro: wallet gia' speso).

Il finding centrale non e' un bug isolato: e' che **`reopen` e' sovraccaricato** — un solo verbo fa il lavoro
di tre operazioni distinte. La soluzione non e' "compensare ovunque" ma un **principio unico** che dissolve la
matrice: *la cassa non si tocca mai; reopen ricalcola la posizione netta del contratto; debito -> resta nel
contratto, credito -> esce in un ledger di credito (wallet cliente / receivable trainer).*

## 3. Grounding fiscale (cosa esiste oggi)

**Non esiste un layer documentale fiscale**: nessun modello fattura / nota di credito; `RatePaymentReceipt`
e' una ricevuta interna; il cliente ha `codice_fiscale`/P.IVA ma nessun documento emesso. Conseguenza: **il
`CashMovement` *e'* il movimento fiscale** — cio' che il commercialista (regime forfettario: trimestre/anno)
vede. Soft-cancellare un movimento caduto in un **periodo dichiarato** = alterare retroattivamente quel
periodo. Reverter un incasso reale non annulla il fatto che il denaro e' entrato. *Questo* e' il "movimento
fiscale non scontato": non si cancella, semmai si **storna con un evento nuovo datato**, o — meglio — **non
si tocca affatto**.

## 4. Lo stato attuale di `reopen` (code-grounded)

`api/routers/contracts.py::reopen_contract` — gambe incondizionate:
- **C** — soft-delete dei `CashMovement` USCITA `RIMBORSO_CONTRATTO` + `totale_rimborsato -=`.
- **C-bis** — soft-delete dei `CashMovement` ENTRATA `INCASSO_CONGUAGLIO_CONTRATTO` + `totale_versato -=`.
- **C-ter** — `crediti_terminazione` -> `ANNULLATO`.
- **D** — `quota_stornata = 0` (residuo ripristinato).
- **E** — ripristino rate marcate `chiusa_da_terminazione`.
- **F** — `chiuso=False`, `motivo_chiusura=None`, `data_chiusura=None`.

Guardia unica: `if not contract.chiuso -> 400`. Nessuna classificazione di scenario. Le gambe C/C-bis
**scavalcano** la protezione di `delete_movement` (`movements.py:1288`: «movimenti legati a contratti sono
protetti» -> 400), che esiste proprio perche' cancellare scritture di cassa contrattuali e' pericoloso.

`residuo()` oggi: `round(max(prezzo - versato_LORDO - quota_stornata, 0), 2)` — usa il versato **lordo** e
**clampa a 0** (vedi §6).

## 5. La matrice degli scenari

Stato di un terminato al reopen = **[cosa ha fatto il terminate] x [cosa si e' regolato dopo] x [periodo
fiscale] x [dipendenze a valle]**. Classi distinte:

| # | Scenario | Cosa fa oggi reopen | Trattamento corretto (CRM aziendale) |
|---|----------|--------------------|--------------------------------------|
| **S1** | Undo immediato, stesso periodo, nessuna cassa regolata, niente a valle | reverse | ✅ ricalcolo banale (nessuna cassa da toccare) |
| **S2** | Rimborso registrato in periodo **diverso/dichiarato** | soft-cancella la USCITA -> muta il passato | la USCITA **resta** (integrita' di periodo); ricalcolo `residuo = P - netto` |
| **S3** | Conguaglio trainer **incassato** (cassa reale entrata) | soft-cancella la ENTRATA -> reddito sparisce | la ENTRATA **resta** -> diventa pagamento sul contratto; ricalcolo |
| **S4** | **Wallet cliente speso** su un altro contratto (futuro) | — (non esiste ancora) | dipendenza a valle -> **software propone** (gestisci Y prima) |
| **S5** | Contratto **rinnovato** dopo terminazione (`rinnovo_di` figlio) | ignora il rinnovo -> due contratti attivi | conflitto strutturale -> **software propone** (annulla rinnovo / continua su quello) |
| **S6** | **RINUNCIA** o **PARI**: zero cassa | reverse | ✅ ricalcolo (residuo + rate); la rinuncia rientra come dovuto |
| **S7** | "Cliente tornato" settimane dopo (cassa mossa, periodo passato) | reverse -> finge che non sia successo | con cassa-ferma+ricalcolo, reopen e' **sicuro**; o nuovo impegno |

## 6. Il principio che unifica (la conclusione)

La posizione di un cliente su un contratto e' **sempre** una di due:
- **DEBITO** (il cliente deve ancora) -> vive **dentro il contratto**, come `residuo`. Si ricalcola.
- **CREDITO** (qualcuno e' in credito) -> vive in un **ledger di credito**: **wallet** lato cliente,
  **receivable** (`crediti_terminazione`) lato trainer. Il contratto non tiene un residuo negativo.

E la regola d'oro: **la cassa che si e' mossa non si tocca mai.** Terminate e reopen **non spostano denaro a
ritroso** — *ricalcolano la posizione netta e la instradano*: debito->contratto, credito->ledger. Reopen,
concretamente: togli lo storno, lascia ferme le scritture di cassa, ricalcola `residuo`; se resta debito ->
contratto, se emerge credito -> wallet.

Questo **dissolve** la matrice: S1/S2/S3/S6/S7 diventano uniformi (ricalcolo da netto, cassa ferma ->
integrita' di periodo automatica, **senza nemmeno bisogno di scritture compensative**). Restano genuinamente
ambigui **solo S4 e S5** (dipendenze a valle) -> §8 (software propone).

## 7. Due scoperte che ne derivano (allargamento)

**A. `residuo` deve diventare net-aware.** Oggi `P - versato_lordo - storno`: appena un rimborso "resta" su
un contratto riaperto (aperto), la formula ignora il rimborso. Corretta — e gia' nello spirito di Strada B:
**`residuo = P - netto_incassato - quota_stornata`** (`netto = versato - rimborsato`). Backward-compatible
(`rimborsato=0` -> identica).

**B. Il clamp `max(...,0)` di `residuo` butta via i sovra-pagamenti in silenzio.** Se `versato > prezzo`,
`residuo=0` e l'eccedenza **sparisce** (non tracciata). Il **wallet** e' il **sink generale degli
overpayment** — il posto dove un credito del cliente non si perde mai, non solo roba da terminazione. Bug
latente che il wallet chiude di sponda.

## 8. Software che propone (per S4/S5)

Per i soli scenari genuinamente ambigui (wallet gia' speso a valle; contratto gia' rinnovato), reopen
**classifica** lo stato e, se trova una dipendenza, **propone** l'azione corretta ("questo contratto e' stato
rinnovato: annulla il rinnovo o continua su quello?") — controllato, mai blocco cieco ne' azione silenziosa.
Coerente con il "proposta != obbligo" che attraversa gia' terminate. **Supera il "blocca".**

## 9. Best CRM aziendali (convergenza)

Il modello e' lo standard dei sistemi di billing maturi:
- **Customer credit balance / wallet** — Stripe (*customer balance*), Chargebee (*refundable credits*),
  QuickBooks/Xero (*credit memo / nota di credito* -> credito sul conto cliente). Il wallet = primitiva nota.
- **Ledger non-distruttivo** — Stripe/QuickBooks **non cancellano** una transazione: si corregge con
  refund/credit-note datati. Regola d'oro della contabilita' (audit trail). = "non toccare la cassa".
- **Reactivation ricalcola, non annulla la storia** — riattivare un abbonamento cancellato ricomputa dallo
  stato corrente + crediti, lasciando la cancellazione nella timeline. = reopen-recompute.

## 10. Output dell'audit -> governance

1. **`reopen` e' sovraccaricato:** un verbo per tre operazioni (undo / storno-correttivo / riattiva-commerciale).
   Va riportato a **un principio**: cassa-immutabile + ricalcola + instrada (debito->contratto, credito->wallet)
   + proponi per le dipendenze a valle. -> **ADR-019**.
2. **Il credito del cliente ha bisogno di una casa:** il **wallet** (customer credit balance), alimentato da
   rimborso-differito e da overpayment, spendibile su contratti futuri, rimborsabile in cassa. -> **ADR-020**.
3. **Disciplina di build (mossa da senior developer, non solo architect):** il principio si adotta **subito**
   come stella polare; il **build si stadia** — prima la fetta economica e ad alto valore (reopen sicuro dal
   ricalcolo + UX-propone + wallet *tracciato e applicato a mano*), poi il wallet **auto-spendibile
   cross-contratto** (stato distribuito, S4) su domanda reale. L'eleganza completa subito e' la trappola.

**Limite dichiarato:** audit documentale; la validazione runtime avviene in fase implementativa. Emenda la
decisione G7.4 "reopen = inverso esatto" (vedi ADR-019 §Supersedes).

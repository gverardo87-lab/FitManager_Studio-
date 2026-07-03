# Ricerca competitor — Fattore tempo su modifiche retroattive vs liquidazioni (2026-07-03)

> 📸 **Fotografia foldata** in `ADR-023` + `SPEC_TEMPORAL_FENCE_EVENTI_LIQUIDATI.md`. Fonti: help
> center e documentazione UFFICIALI, verificati via fetch diretto (3 agenti di ricerca). Conservata
> per le citazioni durevoli.

## Le 5 leggi convergenti (sintesi)

1. **L1 — Due assi, due regimi**: attendance riscrivibile all'indietro (permission-gated, nessuna
   finestra documentata in 5/5 prodotti); denaro no — confine = settlement/batch del processore
   (prima void, dopo solo refund).
2. **L2 — Mai ricalcolo incrociato automatico**: il refund non tocca i contatori sessioni, l'edit di
   una presenza non storna la fee; la giunzione è sempre una decisione umana (approve/waive, edit
   balance manuale, refund manuale).
3. **L3 — La liquidazione congela**: visite storiche restano attaccate com'erano al pass
   rimborsato/deattivato; Mindbody blocca il void finché esistono visite associate; Booker vieta il
   revert dello stato se la fee è partita.
4. **L4 — Correzione forward-only**: rettifica nuova nel presente (refund irreversibile, "vendi un
   nuovo pass con visite gratuite"), mai riscrittura del passato.
5. **L5 — La grazia sta prima del denaro**: fee pending/24h con waive (Glofox), approve/waive workflow
   (Zen Planner) — correggere costa zero pre-cassa, una transazione inversa post-cassa.

## Report 1 — Mindbody + WellnessLiving

### Mindbody (support.mindbodyonline.com)
- Late cancel retroattivo supportato ("you can late cancel the visit after the class has passed");
  permission "Cancel reservations" + "Override cancel policy" oltre la finestra.
  [Classes: early/late cancellations & no-shows](https://support.mindbodyonline.com/s/article/Classes-Early-cancellations-late-cancellations-and-no-shows) ·
  [Why can't my staff cancel a client out of a past class](https://support.mindbodyonline.com/s/article/210079847-Why-can-t-my-staff-cancel-a-client-out-of-a-past-class)
- Conversione late→early = RIMOZIONE della visita dall'Account History (non un toggle).
  [How to early cancel an appointment that has already been late cancelled](https://support.mindbodyonline.com/s/article/209435788-How-do-I-early-cancel-an-appointment-that-has-already-been-late-cancelled)
- "**Any kind of refund makes the pricing option inactive**"; le visite già registrate RESTANO attaccate
  "as a paid visit"; il **void è bloccato** finché esistono visite associate ("You cannot void pricing
  option sales that have associated visits until you early cancel the visits...").
  [Returns, refunds, and voids](https://support.mindbodyonline.com/s/article/203259303-Returns-Refunds-and-Voids) ·
  [How to fix an incorrect sale](https://support.mindbodyonline.com/s/article/203258293-How-do-I-fix-an-incorrect-sale)
- Hard-lock fiscale dichiarato (Francia/NF525): "editing a pricing option after it has been sold is not
  an option". [Add or remove sessions](https://support.mindbodyonline.com/s/article/217551288-Can-I-add-or-remove-sessions-from-a-client-s-pricing-option)
- Void solo pre-settlement ("often on the same day before batching"); refund irreversibile, uno solo per
  acquisto, stessa carta ("helps protect against fraud").
- Fee no-show: autopay il giorno DOPO (cancellabile finché pending); ramo Booker: "**No-show fees cannot
  be reverted if the fee was charged**. However... you can revert the appointment's no-show status" solo
  se la fee NON è partita. [No-Shows Overview & FAQs](https://support.mindbodyonline.com/s/article/No-Shows-Overview-FAQs)

### WellnessLiving (help.wellnessliving.com)
- Stati visita modificabili da 3 superfici incl. attendance history; fee = prompt al momento del cambio
  (decisione staff Yes/No). [Change a client's attendance status](https://help.wellnessliving.com/en/articles/9641675-change-a-client-s-attendance-status)
- Deattivazione pass = congelamento ("Upcoming booked and paid visits will stay... with the paid
  status"); rimborsare NON deattiva automaticamente (checkbox opzionale).
  [Deactivate and reactivate a session pass](https://help.wellnessliving.com/en/articles/10047084-deactivate-and-reactivate-a-client-s-session-pass) ·
  [Refunding a transaction or purchase](https://help.wellnessliving.com/en/articles/9274223-refunding-a-transaction-or-purchase)
- **Il perché più esplicito**: "manually adjusting remaining visits is restricted **in order to prevent
  payment, payroll, or revenue reporting errors**... we recommend selling them a new session pass with
  free visits included". [Modify a Purchase Option](https://help.wellnessliving.com/en/articles/10226792-modify-a-purchase-option-for-an-individual-client)
- Void entro 24h e solo pre-batch (auto-conversione refund→void se pre-batch); "**Refunds can't be
  undone, nor can they be edited**". [Transaction batches and refunds](https://help.wellnessliving.com/en/articles/9823470-transaction-batches-and-refunds)
- Late cancel: "the visit they used to pay for the session won't be returned to them".
  [Late cancels](https://help.wellnessliving.com/en/articles/10967211-late-cancels)

## Report 2 — Zen Planner (Daxko) + Glofox (ABC) + Vagaro

### Zen Planner (help.daxko.com) — il più permissivo sull'attendance
- Check-in/undo su qualsiasi data passata; "Batch Update" può riassegnare/retrocedere/**cancellare**
  record di presenza storici. [How Do I Take Attendance](https://help.daxko.com/s/article/ZEN-PLANNER-How-Do-I-Take-Attendance) ·
  [Manage Reservations](https://help.daxko.com/s/article/ZEN-PLANNER-How-Do-I-Set-Up-and-Manage-Reservations)
- Drop membership: "unpaid bills with due date **on or after** the cancel date will be automatically
  deleted... all paid bills remain" — **il tempo taglia il futuro non pagato, il passato pagato è
  intoccabile**. Undo Drop = reinstate + rigenerazione MANUALE delle bills.
  [How do I cancel a membership](https://help.daxko.com/s/article/ZEN-PLANNER-How-do-I-cancel-a-membership) ·
  [Undo a membership drop](https://help.daxko.com/s/article/ZEN-PLANNER-How-do-I-undo-a-membership-drop-cancellation)
- Refund non cancella la bill (flag esplicito separato); Void SOLO pagamenti offline ("There is NO
  UNDO"; per carta "you should REFUND instead of VOIDING"); Failed Payments = "a snapshot in time".
  [Refund/Re-allocate a Payment](https://help.daxko.com/s/article/ZEN-PLANNER-How-Do-I-Refund-Re-allocate-a-Payment)
- No-show fee non automatizzabile; Late Cancel con approve/waive workflow pending.
  [Using the Late Cancel Feature](https://help.daxko.com/s/article/ZEN-PLANNER-Using-the-Late-Cancel-Feature)

### Glofox (support.glofox.com)
- Attendance modificabile "at any time after" + Resubmit report; il credito NON torna automaticamente
  togliendo una presenza — rimedio = crediti manuali.
  [Submit an Attendance Report](https://support.glofox.com/hc/en-us/articles/46477599149204-How-to-Submit-an-Attendance-Report-for-a-Class) ·
  [Manually Add Credits](https://support.glofox.com/hc/en-us/articles/46432921673492-How-to-Manually-Add-Credits-to-a-Client-s-Profile)
- "**Canceling a membership cannot be reversed**; the membership will have to be reinstated"; niente
  pro-rata automatico; crediti emessi restano spendibili fino a scadenza (adjust manuale).
  [How to Cancel a Membership](https://support.glofox.com/hc/en-us/articles/46427393245844-How-to-Cancel-a-Membership) ·
  [Schedule a Membership Cancellation](https://support.glofox.com/hc/en-us/articles/46427878764820-How-to-Schedule-a-Membership-Cancellation)
- Fee automatiche: "**charged 24 hours after attendance is submitted**... gives staff time to waive a
  pending fee"; post-processamento solo refund dal Transactions tab.
  [Automated No-Show & Late Cancellation Fees](https://support.glofox.com/hc/en-us/articles/46433091889172-Automated-No-Show-Late-Cancellation-Fees)

### Vagaro (support.vagaro.com)
- No-show retroattivo dal calendario; Undo Checkout SOLO tender interni ("credit cards or Pay Later
  can't be undone and must be refunded") — **il rail carta è il period-lock de facto**.
  [Mark as No-Show](https://support.vagaro.com/hc/en-us/articles/360003362734-Mark-Your-Customer-s-Appointment-as-No-Show-and-Charge-a-Fee) ·
  [Undo a Checked-Out Appointment](https://support.vagaro.com/hc/en-us/articles/360013133794-Undo-a-Checked-Out-Appointment)
- "You **can't refund a membership visit**, but you can **manually increase the membership's visit
  balance**" — separazione denaro/contatore esplicita; refund mai annullabile, mai doppio, "full sale
  amount regardless of any visits already used".
  [Refund a Membership and Membership Visits](https://support.vagaro.com/hc/en-us/articles/18791547967515-Refund-a-Membership-and-Membership-Visits)
- Cancellare membership "cannot be reinstated and must be repurchased"; cancellazione ≠ rimborso (atti
  separati); se rimborsi senza cancellare i residui restano spendibili.
  [Manage Purchased Memberships](https://support.vagaro.com/hc/en-us/articles/360003530734-Manage-Purchased-Memberships-in-a-Customer-s-Profile)


## Report 3 — Pattern contabile di fondo + software PT (fonti verificate via fetch)

### QuickBooks Online — closing date + password (Intuit, verificato)
- "Lock your books to stop changes to past transactions": Closing date; oltre → warning O password
  (due gradi a scelta admin). "Only admins can make these changes."
- **Il varco è AUDITATO**: ogni violazione finisce nell'"Exceptions to Closing Date report" — pattern
  completo = fence + varco autenticato + log delle eccezioni.
  [Lock your books](https://quickbooks.intuit.com/learn-support/en-global/help-article/close-books/close-books-quickbooks-online/L59LelyPM_ROW_en) ·
  [Edit your closed books](https://quickbooks.intuit.com/learn-support/en-us/help-article/customer-company-settings/edit-closed-books/L76xHuaZ5_US_en_US)

### Xero — lock dates a due livelli (verificato: developer docs vivi + help archiviato)
- Period lock (ruolo Advisor escludibile) + end-of-year lock ("no one can make changes"). Blocca ogni
  azione datata sul mastro (approvazioni, void, edit, riconciliazioni); le BOZZE restano libere.
  "You can change and remove the lock date at any time" — solo Advisor.
  [Organisation: PeriodLockDate/EndOfYearLockDate](https://developer.xero.com/documentation/api/accounting/organisation) ·
  [Set up and work with lock dates](https://central.xero.com/s/article/Set-up-and-work-with-lock-dates)

### Stripe — Charge immutabile, Refund = oggetto nuovo (docs.stripe.com, verificato)
- [Update a charge](https://docs.stripe.com/api/charges/update): SOLO campi descrittivi (mai amount/
  currency/status). "A PaymentIntent can't be canceled after it has succeeded."
- [Refund object](https://docs.stripe.com/api/refunds/object): referenzia `charge`/`payment_intent`,
  propria `balance_transaction`; [Update a refund](https://docs.stripe.com/api/refunds/update): "only
  accepts metadata". Perfino il refund FALLITO genera una `failure_balance_transaction` (altra
  scrittura, mai una gomma). Dispute = scritture separate, il Charge resta (`disputed: true`).

### Software PT/coaching
- **Trainerize**: session credit decrementato ALLA PRENOTAZIONE (saldo persistito, non ricalcolo dalla
  storia); "Session credits... are **non-refundable and non-revocable**. It is not possible to remove
  session credits" — correzione = consumazione compensativa forward-only ("schedule → cancel → do not
  issue a refund"); alla cancellazione il credito torna solo per scelta esplicita ("with a refund, or
  with no refund"); cliente disattivato = freeze-and-retain.
  [Track Sessions](https://help.trainerize.com/hc/en-us/articles/4404677510164) ·
  [Add Credits](https://help.trainerize.com/hc/en-us/articles/20680082079764)
- **PushPress**: "Once a credit is assigned to an appointment, **it cannot be removed directly** — you
  need to cancel the appointment"; rimozione punch solo con payment-method "comp" esplicito; vista
  storica crediti dedicata.
  [Punchcard](https://help.pushpress.com/en/articles/508567-core-plans-punchcard-adding-removing-punches) ·
  [Session credits](https://help.pushpress.com/en/articles/14050890-how-can-i-manage-session-credits-in-pushpress-including-assigning-unassigning-and-handling-extra-charges)
- **TrueCoach**: archiviazione = "hold" freeze-and-retain; niente billing a pacchetti documentato.
  **Exercise.com**: KB non pubblica — nessuna affermazione possibile.

### La regola generale (sintesi del report)
Quattro invarianti convergenti: (1) **mastro append-only** — la correzione è sempre un oggetto nuovo
forward-only che referenzia l'originale; (2) **snapshot alla liquidazione** — il saldo si consuma
all'atto e resta persistito, nessun ricalcolo retroattivo dalla storia mutata; (3) **period fence**
role-gated; (4) **riapertura come varco esplicito e auditato**, mai effetto collaterale. Nota di
design: le correzioni AL RIALZO dei crediti sono ovunque facili, quelle AL RIBASSO deliberatamente
costose.

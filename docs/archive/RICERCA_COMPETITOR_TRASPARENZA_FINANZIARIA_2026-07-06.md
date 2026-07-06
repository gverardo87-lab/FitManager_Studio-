# Ricerca competitor — Presentazione finanziaria a utenti non-contabili (G8.4)

**Data:** 2026-07-06 · **Trigger:** decisioni founder D-1 (lista always-visible) e D-2 (etichetta ledger) della
`SPEC_G8.4_TRASPARENZA_FINANZIARIA_FE.md`, sospese in attesa di ri-grounding del codice + evidenza di mercato
(la spec era stata scritta il 2026-06-30, durante l'implementazione G7→G9).
**Metodo:** ricerca su fonti UFFICIALI (help center, docs, design system) di 11 vendor: QuickBooks Online, Xero,
Stripe, Square, Mindbody, WellnessLiving, Glofox, Vagaro, Trainerize, TrueCoach, PushPress. Ogni claim con URL.
Le lacune (non documentato pubblicamente) sono dichiarate, non riempite per inferenza.
**Esito:** 6 leggi convergenti (L1–L6). D-2 confermata dalla convenzione di mercato; D-1 EMENDATA da L2
(breakdown lordo−rimborsi always-visible come sub-label, non collassabile). Ratifica founder 2026-07-06.
**Precedente di metodo:** `RICERCA_COMPETITOR_TEMPORAL_FENCE_2026-07-03.md` (stesse regole di citazione).

---

## Q1 — Running balance nei ledger/statement

- **WellnessLiving** (evidenza più forte): la scheda **"Balance history"** del client profile è un ledger con
  colonne `Date, Type, Item, …, Debit, Credit, Running Balance, …`. **"Running Balance"** è definita come
  *"The amount of the account balance after the transaction"*.
  Fonte: https://help.wellnessliving.com/en/articles/9757511-manage-a-client-s-account-balance
- **QuickBooks Online**: colonna **"Balance"** nel registro conti, attivabile col checkbox **"Running Balance"**;
  il saldo progressivo appare SOLO se la lista è ordinata per data e senza filtri (altrimenti "n/a" — un running
  balance su vista filtrata sarebbe un numero falso).
  Fonte: https://quickbooks.intuit.com/learn-support/en-us/account-management/how-do-i-get-the-running-balance-to-show-in-my-register/00/248396
  Customer statement in 3 tipi: **Balance Forward** (fatture, pagamenti E saldo corrente), **Open Item**, **Transaction Statement**.
  Fonte: https://quickbooks.intuit.com/learn-support/en-us/help-article/customer-statements/create-send-customer-statements-quickbooks-online/L8bvb69Gg_US_en_US
- **Xero**: report **Account Transactions** con colonna opzionale **"Running Balance"** (convenzione contabile,
  parentesi sui negativi). Fonti: https://central.xero.com/s/article/Account-Transactions-report-New-US ·
  https://productideas.xero.com/forums/967133-reports-tax/suggestions/46681279-account-transactions-report-running-balance-calc
  Statement cliente: **Activity** / **Outstanding**. Fonte: https://central.xero.com/s/article/Send-a-customer-statement
- **Square**: House Accounts con *"a running balance of the customer's house account"* + statement PDF allegato.
  Fonte: https://squareup.com/help/us/en/article/8034-create-and-charge-square-house-accounts
- **Stripe**: il customer credit balance è calcolato **da un ledger immutabile** (lista di crediti/debiti, audit
  trail); crediti = negativi, debiti = positivi; distinto dal cash balance.
  Fonte: https://docs.stripe.com/invoicing/customer/balance

**Convergenza:** il saldo del ledger si chiama "Balance"/"Running Balance", è colonna separata dagli importi
(Debit/Credit) ed è SEMPRE distinto dal "net" della posizione (che vive altrove: money bar, KPI, header).

## Q2 — Netto vs lordo con rimborsi

- **Stripe**: Dashboard con **Gross volume** e **Net volume** come metriche SEPARATE
  (https://support.stripe.com/questions/dashboard-home-charts-overview ·
  https://docs.stripe.com/connect/supported-embedded-components/reporting-chart). In Revenue Reporting
  *"Net revenue is grouped by fees, refunds, and disputes **by default**"* — il breakdown è la vista predefinita,
  non un'opzione (https://docs.stripe.com/revenue-reporting). Nei report: gross, fee e net per ogni categoria
  (https://docs.stripe.com/reports/reporting-categories).
- **Xero/QBO**: il refund non sovrascrive il lordo — passa da documento contrario (credit note / credit memo)
  che appare come RIGA; il netto emerge dalla sequenza. Fonti: https://central.xero.com/s/article/Credit-notes ·
  https://central.xero.com/s/article/Apply-a-customer-s-credit-to-an-invoice
- **Square**: pagamenti parziali visibili come line item a saldo completato.
  Fonte: https://squareup.com/help/us/en/article/5382-square-invoices-troubleshooting

## Q3 — Statement/posizione cliente nei CRM fitness

- **Mindbody**: balance sul client account (*"Balances display with a negative sign to indicate money that you
  owe to a business"*), movimenti in drill-down; **Account Balances report** per il consolidato.
  Fonti: https://support.mindbodyonline.com/s/article/210928957 · https://support.mindbodyonline.com/s/article/203256673
- **WellnessLiving**: default = **Billing & Account Balance** (saldo + metodi di pagamento); il ledger completo
  (Balance history) è tab di drill-down. Positivo = fondi disponibili, negativo = dovuto.
  Fonti: https://help.wellnessliving.com/en/articles/9757511 · https://www.wellnessliving.com/knowledge-sharing/knowledge-base/viewing-a-clients-transactions-page/
- **Vagaro**: il debito (IOU) NON è drill-down: **red box sul profilo** + reminder automatico al checkout;
  consolidato nell'IOU Report. Fonti: https://support.vagaro.com/hc/en-us/articles/4880271580827 ·
  https://support.vagaro.com/hc/en-us/articles/360008144194

## Q4 — Segnali always-visible vs collassabili

- **QBO**: **money bar** sempre in testa alla pagina Customers, box arancione "Overdue" + "Open Invoices"
  cliccabili. Fonti: https://quickbooks.intuit.com/learn-support/en-us/help-article/journal-posting/view-sales-transactions/L2Do6c0jS_US_en_US ·
  https://quickbooks.intuit.com/learn-support/en-us/other-questions/customer-and-leads-overdue-in-orange/00/1380289
- **Glofox**: "Overdue" = stato account di primo livello (blocca booking) + filtro dedicato + Report on Money Owed.
  Fonti: https://support.glofox.com/hc/en-us/articles/360007641778 · https://support.glofox.com/hc/en-us/articles/360009650558
- **Trainerize**: stati espliciti **Failing/Failed** sugli invoice.
  Fonti: https://help.trainerize.com/hc/en-us/articles/34567770228756 · https://help.trainerize.com/hc/en-us/articles/360000800463
- **TrueCoach**: Payments Dashboard ordinabile per failed charges + alert al cliente delinquent.
  Fonti: https://help.truecoach.co/en/articles/3491682 · https://help.truecoach.co/en/articles/3491678
- **PushPress**: overdue in Control Panel → Payments e Member Profile → Billing, retry notturno.
  Fonti: https://help.pushpress.com/en/articles/508521 · https://help.pushpress.com/en/articles/2781161
- **Mindbody Client alerts** (popup staff sul profilo): esiste ma articolo non fetchabile pubblicamente —
  claim non verificato nel dettaglio (dichiarato). https://support.mindbodyonline.com/s/article/203259733

## Q5 — Raccomandare senza pre-selezionare nei dialog monetari

- **Stripe refund**: pre-compila il **VALORE** (rimborso totale = caso frequente), ma la **reason** va
  selezionata attivamente e "Other" obbliga una nota. Fonte: https://docs.stripe.com/refunds
- **Stripe cancel subscription**: scelte esplicite (quando terminare × cosa rimborsare); *"provide no refund"*
  è un'opzione da scegliere, non un silenzio; nessuna pre-selezione documentata.
  Fonte: https://docs.stripe.com/billing/subscriptions/cancel
- **Mindbody early/late cancel**: due azioni distinte con conseguenze economiche diverse; lo staff DEVE
  scegliere. Fonte: https://support.mindbodyonline.com/s/article/217574098
- **W3C ARIA APG (radiogroup)**: stato iniziale tutto-deselezionato è pattern riconosciuto — *"some
  implementations may initialize the set with all buttons in the unchecked state in order to force the user to
  check one of the buttons before moving past a certain point in the workflow"*.
  Fonte: https://www.w3.org/WAI/ARIA/apg/patterns/radio/
- **Non documentato** (dichiarato): nessun vendor documenta un badge "Recommended" dentro dialog di
  refund/cancel. Il pattern documentabile: opzioni tutte esplicite + valore sicuro pre-compilato + decisione
  all'utente.

## Q6 — Semantica del colore

- **Stripe** (design system Stripe Apps): 6 Badge semantici — neutral / info / positive / negative / warning
  ("requires immediate action; resolution optional") / urgent; palette chiusa per contrasto/a11y
  ("Stripe limits the colors you can use for each element").
  Fonti: https://docs.stripe.com/stripe-apps/components/badge · https://docs.stripe.com/stripe-apps/design ·
  https://docs.stripe.com/stripe-apps/style
- **Intuit Content Design**: sui negativi prescrive il **segno**, non il colore (*"place the minus symbol in
  front of the currency symbol"*, es. `-$25`); *"use only one treatment at a time"*; bold mai per enfasi.
  Fonti: https://contentdesign.intuit.com/style-and-usage/numbers/ · https://contentdesign.intuit.com/style-and-usage/formatting/
- Convenzioni osservate: QBO arancio=Overdue · WellnessLiving arancio=pending settlement · Vagaro rosso=IOU ·
  Mindbody segno negativo=dovuto · Xero parentesi contabili. L'arancio ricorre per "attenzione/pending",
  il rosso è riservato al debito conclamato.

---

## Leggi convergenti (L1–L6)

- **L1 — Il ledger ha una colonna "Saldo" progressivo, separata dagli importi, valida solo in ordine
  cronologico.** (QBO, Xero, WellnessLiving, Square, Stripe.) Se la vista è filtrata, il saldo si nasconde
  (pattern QBO "n/a"), mai ricalcolato sul sottoinsieme.
- **L2 — Il netto non sostituisce mai il lordo: è una derivazione esplicita, col breakdown di default.**
  (Stripe net-grouped-by-default; Xero/QBO credit note come riga; Square line item.) → il "netto" va sempre
  accompagnato da `lordo − rimborsi` visibile; il rimborso resta riga negativa, mai mutazione silenziosa.
- **L3 — Posizione ORA (header, 1-2 numeri) e storia (ledger) sono due viste separate: posizione sempre
  visibile, ledger in drill-down.** (WellnessLiving, Mindbody, Stripe, QBO, Vagaro.)
- **L4 — Il denaro dovuto/scaduto è un segnale push always-visible (badge/colore/stato di primo livello),
  MAI dietro toggle.** (Vagaro red box, QBO money bar, Glofox stato Overdue, Trainerize Failing/Failed,
  TrueCoach, PushPress.)
- **L5 — Nei dialog monetari si pre-compilano i VALORI sicuri, non le DECISIONI; ogni esito (incluso "nessun
  rimborso") è una scelta esplicita.** (Stripe refund/cancel, Mindbody early-vs-late, W3C APG radiogroup
  senza selezione iniziale.)
- **L6 — Palette chiusa e semantica: il colore è rinforzo dello stato, mai decorazione; il segnale primario
  sui numeri è il segno `−€`.** (Stripe badge semantici, Intuit segno-non-colore + one-treatment, QBO/WL/Vagaro.)

## Implicazioni ratificate (founder, 2026-07-06)

- **D-2 → CONFERMATA e RAFFORZATA (L1):** lo storico movimenti del contratto guadagna la colonna/valore
  **«Saldo»** per riga (dal campo backend `saldo_progressivo`) + footer **«Saldo movimenti del contratto»**.
  Mai "netto" come etichetta del ledger. Registrata in ADR-019 **Addendum IV**.
- **D-1 → EMENDATA (L2 + D-NESSUN-NETTO-NUDO ADR-022 Add. II):** il breakdown «lordo − rimborsi» esce dalla
  colonna "collassabile" e diventa **sub-label compatta always-visible** accanto al netto (visibile quando
  `totale_rimborsato > 0`), riusando il pattern già shippato in `/cassa` (G9.4-bis.3). Il resto della lista
  §F2 della spec è confermato.
- **F3 confermata da L5:** raccomandazione solo-visiva, nessuna pre-selezione sul ramo trainer, pre-fill solo
  dei valori (ramo cliente); radiogroup ARIA senza selezione iniziale è il pattern accessibile canonico.
- **F6 confermata da L6:** neutralizzare i tint decorativi (violet/blue/indigo) nei KPI; segno `−€` sempre
  presente accanto al colore.

## Lacune dichiarate

- Stripe non pubblica la definizione testuale del tooltip gross/net volume della home Dashboard.
- Nessun vendor documenta pre-selezioni di default nei dialog cancel/refund, né badge "Recommended".
- Intuit non prescrive il rosso per i negativi (solo il segno meno).
- Glofox/Vagaro/Trainerize/PushPress bloccano il fetch diretto (403/404): claim derivati dagli estratti
  indicizzati delle pagine ufficiali citate, non dal testo integrale.

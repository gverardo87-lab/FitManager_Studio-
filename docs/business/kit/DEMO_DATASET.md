# Demo pack — Dataset sintetico (specifica)

**Kit design partner, pezzo 2/5 — DP.1.** Stato: 🟡 specifica; il seeder (DP.2,
`tools/scripts/seed_demo_tenant.py`, via API — MAI SQL diretto) è ⏸️ CONGELATO fino al
checkpoint S1/G1. Vincolo D5: SOLO dati sintetici. I nomi sono INVENTATI — mai nomi di
collaboratori o persone reali. Decisione ambiente (tenant demo nello stesso crm.db vs
backup/restore) RINVIATA a G1 visibile; raccomandazione corrente: tenant dedicato.

> Principio: ogni personaggio esiste per accendere UN segnale del copione. Niente riempitivo.
> Tutte le date sono RELATIVE a «oggi» e calcolate al run del seeder (mai hardcoded — è il
> difetto che ha ucciso i seeder di marzo). Tutti i numeri di telefono = numero del founder
> (i deep-link wa.me devono arrivare a te, mai a estranei).

## Account

- Trainer demo dedicato (es. `demo@fitmanagerstudio.com`), password gestita dal founder.
- I dati del founder restano sotto il SUO account: l'isolamento è il multi-tenant del prodotto.

## Personaggi (6 + slot live)

| # | Nome (fantasia) | Ruolo nel copione | Stato dati richiesto |
|---|-----------------|-------------------|----------------------|
| 1 | **Marta Colombo** | B4 — Training Intelligence | Cliente da ~3 mesi: contratto attivo 20 sedute, ~14 completate CON log esecuzione (serie/rip/kg registrati), scheda attiva 3 sessioni, misurazioni mensili. È il personaggio più costoso da seminare e il più prezioso |
| 2 | **Luca Ferraro** | B3 — Safety Engine | Anamnesi con ernia lombare (+ una cautela secondaria, es. spalla). Scheda esistente SENZA esercizi controindicati (il warning scatta live quando aggiungi lo stacco) |
| 3 | **Giulia Santoro** | B1/B5 — rata scaduta + sollecito | Contratto attivo, rata scaduta da 10 giorni, importo credibile. Telefono = founder |
| 4 | **Paolo Rinaldi** | B1 — rinnovo | Contratto in scadenza entro 7 giorni con 2 crediti residui |
| 5 | **Elena Marchetti** | B1 — compleanno | Data di nascita con giorno/mese = OGGI (il seeder la ricalcola a ogni run) |
| 6 | **Sara Vitale** | Riempimento agenda | 1-2 eventi oggi/domani perché l'agenda del giorno non sia vuota |
| — | *(slot live B2)* | Nuovo cliente creato in demo | Nasce durante la conversazione; il re-run del seeder lo rimuove/ignora |

## Requisiti trasversali

- **Dashboard viva:** al login demo devono essere accesi ESATTAMENTE: rate scadute (1),
  compleanni (1), contratti in scadenza (1), sessioni oggi (≥2). Zero eventi fantasma, zero
  orfani: la dashboard demo è pulita, i segnali sono quelli voluti.
- **Cassa presentabile:** 2-3 mesi di movimenti passati (incassi rate di Marta/Paolo) così
  il Libro Mastro e i KPI non sono vuoti se il prospect chiede «fammi vedere la cassa».
- **Idempotenza:** il seeder ricrea lo stato-demo da zero a ogni run (ripristino pre-demo
  in un comando). Le date scorrono con «oggi»: la demo funziona identica tra un mese.
- **Post-G1:** il seeder gira via API su DB cifrato → ogni run è anche un collaudo del boot
  a due fasi. Da annotare in DP.2 come beneficio di collaudo, non solo come vincolo.

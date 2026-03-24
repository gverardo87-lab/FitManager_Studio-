# Video: I Primi 10 Minuti con FitManager
# Durata target: 90s (homepage hero + YouTube)
# Formato: full demo
# Voce: it-IT-DiegoNeural, rate +5%
# Musica: corporate ambient generativa (115 BPM, Am)
# Risoluzione: 1440×900

---

## Struttura narrativa

```
HOOK (8s)      → Il dolore del PT che usa Excel/WhatsApp
SOLUZIONE (5s) → FitManager in una frase
DEMO (68s)     → 8 scene, flusso reale primo cliente
CTA (9s)       → Chiusura + URL + garanzia
Totale: ~90s
```

---

## Pre-produzione: dati da creare via API

Prima della registrazione, lo script crea via API:
- **Cliente**: Giulia Martini, 27 anni, Donna, Attivo
- **Anamnesi**: ernia lombare L4-L5, instabilita' rotulea, dolori schiena+ginocchia
- **Contratto**: PT Personal 10 sedute, €450, acconto €150 POS, 3 rate mensili da €100
- **Scheda**: "Tonificazione Full Body — Giulia", 6 esercizi (2 triggerano Safety Engine)
- **Piano nutrizione**: template "Donna under 30 Attiva" 1900 kcal, standard LARN

---

## Scena 01 — HOOK: Il problema [CORE]

| VIDEO | AUDIO |
|-------|-------|
| **Schermata**: title card intro (sfondo gradiente teal scuro, logo FM, testo "I Primi 10 Minuti") | **VO**: "Schede su Excel. Pagamenti su WhatsApp. Anamnesi su carta. Ogni giorno perdi tempo su cose che non ti fanno guadagnare." |
| **Azione**: statica, fade in 1s | **Musica**: pad ambient, volume basso, entra in fade |
| **Transizione**: fade out 0.6s verso scena 02 | **Pausa**: 0.3s dopo fine VO |
| **Durata stimata**: ~8s | |

**Note regia**: il testo VO deve colpire emotivamente. Tre dolori in sequenza rapida, poi la frase di impatto. Ritmo incalzante.

---

## Scena 02 — SOLUZIONE: Cos'e' FitManager [CORE]

| VIDEO | AUDIO |
|-------|-------|
| **Schermata**: Dashboard `/` — si vede il saluto "Buongiorno, Chiara", i 3 gauge (Clienti Attivi, Rate Pendenti, Appuntamenti Oggi), il TodoCard con hero action | **VO**: "FitManager e' il gestionale che fa tutto questo per te. Vediamo come, in dieci minuti." |
| **Azione**: la pagina e' gia' caricata, nessun click. La camera resta ferma sulla dashboard per mostrare la panoramica | |
| **Transizione**: cut diretto a scena 03 | **Pausa**: 0.5s dopo fine VO |
| **Durata stimata**: ~5s | |

**Note regia**: la dashboard deve apparire gia' popolata (dati del trainer demo). Momento di respiro dopo il hook aggressivo. Il viewer vede per la prima volta l'interfaccia.

---

## Scena 03 — Nuovo Cliente [CORE]

| VIDEO | AUDIO |
|-------|-------|
| **Schermata**: pagina `/clienti` — lista clienti con KPI cards (Attivi, Inattivi, Con Crediti, Rate Scadute) | **VO**: "Inserisci il primo cliente. Nome, cognome, contatti. Trenta secondi e Giulia e' nel sistema." |
| **Azione 1**: (0.0s) la pagina e' gia' caricata, si vedono i KPI | |
| **Azione 2**: (1.0s) click su pulsante "Nuovo Cliente" (in alto a destra, primary button) | |
| **Azione 3**: (1.8s) si apre lo Sheet da destra con il form "Nuovo Cliente" | |
| **Azione 4**: (2.5s) typing nel campo Nome: "Giulia" | |
| **Azione 5**: (3.2s) typing nel campo Cognome: "Martini" | |
| **Azione 6**: (4.0s) typing nel campo Email: "giulia.martini@gmail.com" | |
| **Azione 7**: (5.5s) pausa sul form compilato, i campi sono visibili | |
| **Transizione**: Escape per chiudere sheet, cut a scena 04 | **Pausa**: 0.3s |
| **Durata stimata**: ~7s | |

**Note regia**: il typing deve essere visibile e leggibile. SlowMo sufficiente perche' il viewer legga i caratteri che appaiono. Il cliente e' gia' stato creato via API — qui mostriamo solo il form per effetto visivo.

---

## Scena 04 — Anamnesi con Condizioni [CORE]

| VIDEO | AUDIO |
|-------|-------|
| **Schermata**: pagina `/clienti/{id}/anamnesi` — AnamnesiSummary con le 6 sezioni compilate | **VO**: "L'anamnesi e' strutturata. Giulia ha un'ernia lombare e instabilita' al ginocchio. FitManager registra tutto e lo usa dopo, quando crei la scheda." |
| **Azione 1**: (0.0s) la pagina mostra il riepilogo anamnesi, sezioni visibili | |
| **Azione 2**: (2.0s) scroll lento verso il basso per mostrare le sezioni Patologie e Condizioni | |
| **Azione 3**: (4.0s) si vedono i badge rossi delle condizioni (ernia, articolari) | |
| **Azione 4**: (6.0s) scroll continua per mostrare la sezione Goals/Obiettivi | |
| **Transizione**: cut diretto a scena 05 | **Pausa**: 0.5s |
| **Durata stimata**: ~9s | |

**Note regia**: momento chiave del video. Il viewer deve VEDERE i badge rossi delle condizioni. Sono il setup per il payoff della scena 07 (Safety Engine). Scroll lento, dare tempo di leggere.

---

## Scena 05 — Contratto e Rate [CORE]

| VIDEO | AUDIO |
|-------|-------|
| **Schermata**: pagina `/contratti/{id}` — ContractFinancialHero con KPI cards | **VO**: "Crei il contratto. Dieci sedute, quattrocentocinquanta euro, tre rate. L'acconto va in cassa automaticamente." |
| **Azione 1**: (0.0s) la pagina mostra il header con tipo pacchetto + badge Attivo + date | |
| **Azione 2**: (1.0s) si vedono i 6 KPI cards: Valore, Acconto, Da Rateizzare, Versato (con progress bar), Rate Pagate, Residuo | |
| **Azione 3**: (3.5s) scroll lento verso il tab "Piano Pagamenti" | |
| **Azione 4**: (5.0s) si vede la tabella rate con 3 righe: Data Scadenza, Importo €100, Stato (da pagare) | |
| **Transizione**: cut diretto a scena 06 | **Pausa**: 0.3s |
| **Durata stimata**: ~8s | |

**Note regia**: i numeri devono essere leggibili. €450 totale, €150 acconto, 3 rate da €100. Il progress bar del "Versato" mostra gia' il 33% (acconto pagato). Concetto chiave: automatismo.

---

## Scena 06 — Cassa: Libro Mastro e Previsioni [CORE]

| VIDEO | AUDIO |
|-------|-------|
| **Schermata**: pagina `/cassa` — Saldo Hero card (grande, teal) + KPI cards + grafico giornaliero | **VO**: "Il libro cassa si aggiorna da solo. Entrate, uscite, previsioni. Nessun foglio Excel." |
| **Azione 1**: (0.0s) la pagina mostra il Saldo Attuale (card teal grande) + 4 KPI (Entrate, Uscite Variabili, Uscite Fisse, Margine Netto) | |
| **Azione 2**: (2.0s) scroll fino al grafico a barre (entrate verdi, uscite rosse, linea saldo blu) | |
| **Azione 3**: (4.0s) click sul tab "Forecast" | |
| **Azione 4**: (5.0s) si vede la proiezione a 90 giorni con curve entrate/uscite/runway | |
| **Transizione**: cut diretto a scena 07 | **Pausa**: 0.3s |
| **Durata stimata**: ~7s | |

**Note regia**: mostrare la completezza finanziaria. Dal singolo pagamento alla visione a 90 giorni. Il messaggio e': "non devi fare niente, si aggiorna da solo".

---

## Scena 07 — Scheda + Safety Engine [CORE]

| VIDEO | AUDIO |
|-------|-------|
| **Schermata**: pagina `/schede/{id}` — Workout Builder con sessioni a sinistra, esercizi al centro, panel destro | **VO**: "Crei la scheda allenamento. Il Safety Engine legge l'anamnesi di Giulia e ti avvisa: squat profondo controindicato per l'ernia. Nessun rischio dimenticato." |
| **Azione 1**: (0.0s) la pagina mostra il builder con la sessione "Full Body A" selezionata | |
| **Azione 2**: (1.5s) si vedono i 6 esercizi nella lista centrale (Squat Bodyweight, Goblet Squat, Leg Press, Lat Machine, Chest Press, Plank) | |
| **Azione 3**: (3.0s) click sul tab "Sicurezza" o "Analisi" nel panel destro | |
| **Azione 4**: (4.0s) appare il BuilderSafetyCard con gli avvisi rossi/ambra: warning per Squat legato a ernia lombare | |
| **Azione 5**: (6.0s) scroll lento nel panel per mostrare tutti gli avvisi di sicurezza | |
| **Transizione**: cut diretto a scena 08 | **Pausa**: 0.5s |
| **Durata stimata**: ~10s | |

**Note regia**: questa e' la scena WOW del video. Il payoff del setup della scena 04 (anamnesi). Il viewer vede il collegamento: condizioni inserite in anamnesi → avvisi automatici in scheda. DEVE essere chiaro visivamente. Se il SafetyCard non e' subito visibile, fare click/scroll per arrivarci.

---

## Scena 08 — Catalogo Esercizi + Muscle Map [EXTENDED]

| VIDEO | AUDIO |
|-------|-------|
| **Schermata**: pagina `/esercizi/1` — dettaglio esercizio con MuscleMap SVG + Classification Grid | **VO**: "Cinquecento esercizi con la mappa muscolare e la scienza dentro. Ogni dettaglio serve a programmare meglio." |
| **Azione 1**: (0.0s) la pagina mostra header con nome esercizio + badges | |
| **Azione 2**: (1.0s) si vede la MuscleMap SVG a sinistra (corpo umano con muscoli evidenziati in colore) e la griglia di classificazione a destra (Pattern, Difficulty, Equipment, Force Type, etc.) | |
| **Azione 3**: (3.5s) scroll per mostrare il tab Panoramica con media gallery e gruppi muscolari primari/secondari | |
| **Transizione**: cut diretto a scena 09 | **Pausa**: 0.3s |
| **Durata stimata**: ~7s | |

**Note regia**: la MuscleMap e' molto visuale e impressionante. Dare tempo al viewer di apprezzare la grafica. I badge colorati della classificazione comunicano profondita' scientifica.

---

## Scena 09 — Piano Nutrizione LARN [CORE]

| VIDEO | AUDIO |
|-------|-------|
| **Schermata**: pagina `/nutrizione/{id}` — header con titolo piano + target macro bars + griglia settimanale | **VO**: "Il piano alimentare per donna under trenta. Millenovecento calorie, standard LARN, sette giorni completi." |
| **Azione 1**: (0.0s) la pagina mostra header con "Piano LARN — Giulia Martini" + badge Attivo | |
| **Azione 2**: (1.0s) si vedono le 4 barre macro target: Proteine, Carboidrati, Grassi, Calorie con progress bar colorate | |
| **Azione 3**: (3.0s) scroll verso la griglia settimanale WeeklyPlanGrid (7 righe × slot pasto) | |
| **Azione 4**: (5.0s) si vedono le celle con i nomi dei pasti e i macro riassuntivi | |
| **Transizione**: fade out 0.5s verso scena 10 | **Pausa**: 0.5s |
| **Durata stimata**: ~8s | |

**Note regia**: mostrare la completezza del piano. 7 giorni × 5-6 pasti = griglia piena. Il messaggio e': "non e' un foglio bianco, e' un piano completo generato da template scientifico".

---

## Scena 10 — CTA: Chiusura [CORE]

| VIDEO | AUDIO |
|-------|-------|
| **Schermata**: title card outro (sfondo gradiente teal scuro, logo FM, box CTA "Diventa un PT Evoluto" + URL fitmanager.studio + 3 pill: "Dati locali, zero cloud" / "Licenza perpetua" / "Garanzia 30 giorni") | **VO**: "Dieci minuti. Un cliente completo. Zero carta. Zero Excel. FitManager Studio Plus." |
| **Azione**: statica, fade in 0.6s | **Musica**: shimmer entra, crescendo finale, fade out 1s |
| **Transizione**: fade out 1s a nero | **Pausa**: 1.5s di silenzio dopo fine VO (la card resta visibile) |
| **Durata stimata**: ~9s | |

**Note regia**: la CTA deve restare visibile DOPO che la voce finisce. Il viewer deve avere tempo di leggere l'URL e i 3 pill. Il fade out a nero e' l'ultimo frame.

---

## Riepilogo timing

| # | Scena | Tipo | Durata | VO (parole) | Cumulativo |
|---|-------|------|--------|-------------|------------|
| 01 | Hook: il problema | title card | ~8s | 26 | 8s |
| 02 | Soluzione: dashboard | app screen | ~5s | 16 | 13s |
| 03 | Nuovo cliente | app screen | ~7s | 17 | 20s |
| 04 | Anamnesi condizioni | app screen | ~9s | 27 | 29s |
| 05 | Contratto e rate | app screen | ~8s | 21 | 37s |
| 06 | Cassa e previsioni | app screen | ~7s | 16 | 44s |
| 07 | Scheda + Safety | app screen | ~10s | 28 | 54s |
| 08 | Esercizi + Muscle Map | app screen | ~7s | 17 | 61s |
| 09 | Nutrizione LARN | app screen | ~8s | 18 | 69s |
| 10 | CTA chiusura | title card | ~9s | 14 | 78s |
| | **TOTALE** | | **~78s** | **~200 parole** | |

A 150 parole/min (+5% rate), 200 parole ≈ 73s di parlato puro.
Con padding inter-scena (0.3-0.5s × 9 transizioni) ≈ +3-4s.
**Durata finale stimata: 76-82s** (dentro il target 90s con margine per respiro).

---

## Tagli multi-formato

### Export 30s (social clip)
Scene: 01 (hook, 4s) + 07 (safety, 5s) + 03 (cliente, 4s) + 06 (cassa, 4s) + 10 (CTA, 5s)
VO riscritta, piu' sintetica. Ritmo serrato.

### Export 60s (homepage hero)
Scene: 01 + 02 + 03 + 04 + 05 + 07 + 09 + 10 (skip 06 Cassa e 08 Esercizi)
VO identica, si tagliano le scene EXTENDED.

---

## Checklist pre-registrazione

- [ ] Backend dev running su porta 8001
- [ ] Frontend dev running su porta 3001
- [ ] Login con credenziali dev (chiarabassani96@gmail.com / Fitness2026!)
- [ ] Verificare che il trainer abbia almeno 2-3 clienti preesistenti (dashboard non vuota)
- [ ] Template nutrizione ID=6 disponibile ("Donna under 30 — Attiva")
- [ ] Esercizi 184, 141, 15, 9, 22, 56 presenti in catalog.db
- [ ] Playwright installato (`npm list playwright`)
- [ ] FFmpeg raggiungibile
- [ ] edge-tts raggiungibile

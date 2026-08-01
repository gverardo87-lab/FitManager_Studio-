# FitManager Studio+ — Modello Finanziario Analitico

**Versione:** 1.1 — 29 marzo 2026
**Autore:** Giacomo Verardo
**Stato:** Confidenziale
**Dipende da:** `docs/business/BUSINESS_PLAN.md` per le assunzioni pre-validazione · fonti storiche
`docs/archive/business/STRATEGY_PLAN_V3_1_2026-03-27.md` e
`docs/archive/business/DOCUMENTO_OPERATIVO_PARTNER_2026-03.md`; non governa lo scheduling pre-POC

---

## Scopo

Questo documento ricostruisce le proiezioni finanziarie del BP con un modello dove **ogni euro è tracciabile a un'assunzione dichiarata**. Sostituisce le tabelle approssimate del BP con calcoli verificabili riga per riga.

---

## 1. Assunzioni dichiarate

### Pricing (da BP §6)

| Prodotto | Prezzo | Costo vivo | Margine |
|----------|--------|------------|---------|
| Licenza software | €249 | €30 (installazione) | €219 (88%) |
| FitManager Box | €449 | €150 (hardware + setup) | €299 (67%) |
| Assistenza PRO | €79/anno | ~€0 | €79 (100%) |
| Inner Circle | €249/anno | ~€0 | €249 (100%) |

### POC (fisso, tutti gli scenari)

| | Unità | Prezzo | Totale |
|--|-------|--------|--------|
| Licenze Fondatore | 8 | €99 | €792 |
| Box Fondatore | 2 | €199 | €398 |
| **Totale POC** | **10** | | **€1.190** |

### Mix Licenze / Box (per anno, post-POC)

| Anno | Licenze | Box | Motivazione |
|------|---------|-----|-------------|
| 1 | **80%** | **20%** | Box non ancora consolidata, 3-6 mesi di sviluppo post-POC, certificazioni hardware da completare |
| 2 | **65%** | **35%** | Box disponibile, adozione graduale |
| 3 | **50%** | **50%** | Box affermata, differenziatore competitivo maturo |

### Ricorrente

| Parametro | Valore | Note |
|-----------|--------|------|
| PRO gratis | Primi 30 clienti, 12 mesi | Rinnovo al mese 13 |
| Rinnovo PRO (mese 13+) | **55%** | Assunzione A4 del BP, estremo basso |
| Adozione PRO nuovi (dal 31°) | **70%** | Pagano €79 all'acquisto |
| IC % base — conservativo | 12% | |
| IC % base — base | 20% | Assunzione A4 del BP |
| IC % base — ottimistico | 25% | |

### Fiscale

| Regime | Aliquota effettiva | Quando |
|--------|-------------------|--------|
| Forfettario | ~21% del fatturato | Fatturato ≤ ~€40K |
| Ordinario/SRL | ~35% del reddito netto | Fatturato > ~€40K |

**Nota critica**: in forfettario il compenso partner NON è deducibile (le tasse sono sul 67% del fatturato, non sul profitto reale). Questo penalizza il founder quando i costi reali superano il 33% del fatturato. Da verificare col commercialista se la transizione a ordinario conviene prima della soglia €40K.

### Partner (da Doc Operativo Partner)

| Componente | % | Applicata a |
|------------|---|-------------|
| Vendite prodotto | 20% | Tutte le licenze e Box |
| Ricorrente + contenuto | 35% | PRO + Inner Circle |

### Clienti per scenario (da BP §10, invariati)

| | Conserv | Base | Ottim |
|--|---------|------|-------|
| Nuovi A1 | 33 | 46 | 67 |
| Nuovi A2 | 35 | 58 | 97 |
| Nuovi A3 | 49 | 87 | 155 |
| Base A1 | 33 | 46 | 67 |
| Base A2 | 68 | 104 | 164 |
| Base A3 | 117 | 191 | 319 |

### Costi operativi per scenario

| | Anno 1 | Anno 2 | Anno 3 |
|--|--------|--------|--------|
| **Fissi** (tutti gli scenari) | €4.300 | €4.500 | €4.800 |
| **Collaboratore — conserv** | — | — | €4.000 |
| **Collaboratore — base** | — | €4.000 | €9.200 |
| **Collaboratore — ottim** | €600 | €7.500 | €17.200 |
| **Totale operativi — conserv** | €4.300 | €4.500 | €8.800 |
| **Totale operativi — base** | €4.300 | €8.500 | €14.000 |
| **Totale operativi — ottim** | €4.900 | €12.000 | €22.000 |

---

## 2. Formule di calcolo

### Vendite prodotto

```
Anno 1:
  POC = €1.190 (fisso)
  post_poc = nuovi - 10
  licenze = round(post_poc × mix_lic%) × €249
  box = (post_poc - round(post_poc × mix_lic%)) × €449
  vendite_prodotto = POC + licenze + box

Anno 2-3:
  licenze = round(nuovi × mix_lic%) × €249
  box = (nuovi - round(nuovi × mix_lic%)) × €449
  vendite_prodotto = licenze + box
```

### PRO

```
Anno 1:
  eligible = max(0, base - 30)
  pro_paganti = round(eligible × 70%)

Anno 2:
  rinnovi_free30 = round(30 × 55%)           # i primi 30 rinnovano
  rinnovi_paganti = round(pro_A1 × 55%)       # paganti A1 rinnovano
  nuovi_pro = round(nuovi_A2 × 70%)           # nuovi clienti comprano PRO
  pro_paganti = rinnovi_free30 + rinnovi_paganti + nuovi_pro

Anno 3:
  rinnovi = round(pro_A2 × 55%)
  nuovi_pro = round(nuovi_A3 × 70%)
  pro_paganti = rinnovi + nuovi_pro

revenue_pro = pro_paganti × €79
```

### Inner Circle

```
ic_membri = round(base_installata × ic_rate%)
revenue_ic = ic_membri × €249
```

### Costi diretti

```
costo_box = box_vendute × €150
costo_install = licenze_vendute × €30
costi_diretti = costo_box + costo_install
```

### Partner

```
partner = vendite_prodotto × 20% + (revenue_pro + revenue_ic) × 35%
```

### Tasse

```
se fatturato ≤ €40K:
  tasse = fatturato × 21%                     # forfettario
se fatturato > €40K:
  reddito = fatturato - costi_diretti - operativi - partner
  tasse = reddito × 35%                       # ordinario
```

### Netto founder

```
netto = fatturato - costi_diretti - operativi - partner - tasse
```

---

## 3. P&L — Scenario Base (46 / 58 / 87 nuovi)

### Anno 1 — 46 clienti

| Riga | Calcolo | Importo |
|------|---------|---------|
| POC Licenze | 8 × €99 | €792 |
| POC Box | 2 × €199 | €398 |
| Licenze post-POC | 80% di 36 = 29 × €249 | €7.221 |
| Box post-POC | 20% di 36 = 7 × €449 | €3.143 |
| **Vendite prodotto** | | **€11.554** |
| PRO | 16 eligible × 70% = 11 × €79 | €869 |
| IC | 46 × 20% = 9 × €249 | €2.241 |
| **Fatturato** | | **€14.664** |
| Hardware Box | 9 × €150 | −€1.350 |
| Installazione | 37 × €30 | −€1.110 |
| **Costi diretti** | | **−€2.460** |
| Operativi | Fissi | −€4.300 |
| Partner prodotto | 20% × €11.554 | −€2.311 |
| Partner ricorrente | 35% × €3.110 | −€1.089 |
| **Totale partner** | | **−€3.400** |
| Tasse (forf. 21%) | €14.664 × 21% | −€3.079 |
| **Netto founder** | | **€1.425** |

### Anno 2 — 58 nuovi

| Riga | Calcolo | Importo |
|------|---------|---------|
| Licenze | 65% di 58 = 38 × €249 | €9.462 |
| Box | 35% di 58 = 20 × €449 | €8.980 |
| **Vendite prodotto** | | **€18.442** |
| PRO rinnovi free-30 | 30 × 55% = 17 × €79 | €1.343 |
| PRO rinnovi A1 paganti | 11 × 55% = 6 × €79 | €474 |
| PRO nuovi A2 | 58 × 70% = 41 × €79 | €3.239 |
| **Totale PRO** | 64 membri | **€5.056** |
| IC | 104 × 20% = 21 × €249 | €5.229 |
| **Fatturato** | | **€28.727** |
| Costi diretti | 20×€150 + 38×€30 | −€4.140 |
| Operativi | Fissi €4.500 + collab €4.000 | −€8.500 |
| Partner | 20%×€18.442 + 35%×€10.285 | −€7.288 |
| Tasse (forf. 21%) | €28.727 × 21% | −€6.033 |
| **Netto founder** | | **€2.766** |

### Anno 3 — 87 nuovi

| Riga | Calcolo | Importo |
|------|---------|---------|
| Licenze | 50% di 87 = 44 × €249 | €10.956 |
| Box | 50% di 87 = 43 × €449 | €19.307 |
| **Vendite prodotto** | | **€30.263** |
| PRO rinnovi | 64 × 55% = 35 × €79 | €2.765 |
| PRO nuovi A3 | 87 × 70% = 61 × €79 | €4.819 |
| **Totale PRO** | 96 membri | **€7.584** |
| IC | 191 × 20% = 38 × €249 | €9.462 |
| **Fatturato** | | **€47.309** |
| Costi diretti | 43×€150 + 44×€30 | −€7.770 |
| Operativi | Fissi €4.800 + collab €9.200 | −€14.000 |
| Partner | 20%×€30.263 + 35%×€17.046 | −€12.019 |
| Reddito (ordinario) | | €13.520 |
| Tasse (ord. 35%) | €13.520 × 35% | −€4.732 |
| **Netto founder** | | **€8.788** |

### Riepilogo Base

| | Anno 1 | Anno 2 | Anno 3 | Cum. 3 anni |
|--|--------|--------|--------|-------------|
| Fatturato | €14.664 | €28.727 | €47.309 | **€90.700** |
| Costi diretti | €2.460 | €4.140 | €7.770 | €14.370 |
| Costi operativi | €4.300 | €8.500 | €14.000 | €26.800 |
| Partner | €3.400 | €7.288 | €12.019 | €22.707 |
| Tasse | €3.079 | €6.033 | €4.732 | €13.844 |
| **Netto founder** | **€1.425** | **€2.766** | **€8.788** | **€12.979** |
| **Netto partner** | **€3.400** | **€7.288** | **€12.019** | **€22.707** |
| €/mese founder | €119 | €231 | €732 | |

---

## 4. P&L — Scenario Conservativo (33 / 35 / 49 nuovi)

### Dettaglio unità vendute

| | A1 (80/20) | A2 (65/35) | A3 (50/50) |
|--|------------|------------|------------|
| POC Lic / Box | 8 / 2 | — | — |
| Licenze post-POC | 18 | 23 | 25 |
| Box post-POC | 5 | 12 | 24 |
| Totale unità | 33 | 35 | 49 |

### PRO membri paganti

| | Rinnovi | Nuovi (70%) | Totale |
|--|---------|-------------|--------|
| A1 | — | 3 eligible → 2 | 2 |
| A2 | 17 (free-30) + 1 (A1) | 25 | 43 |
| A3 | 24 (A2 × 55%) | 34 | 58 |

### P&L

| | Anno 1 | Anno 2 | Anno 3 | Cum. 3 anni |
|--|--------|--------|--------|-------------|
| Vendite prodotto | €7.917 | €11.115 | €17.001 | €36.033 |
| PRO | €158 | €3.397 | €4.582 | €8.137 |
| IC (12%) | €996 | €1.992 | €3.486 | €6.474 |
| **Fatturato** | **€9.071** | **€16.504** | **€25.069** | **€50.644** |
| Costi diretti | €1.830 | €2.490 | €4.350 | €8.670 |
| Costi operativi | €4.300 | €4.500 | €8.800 | €17.600 |
| Partner | €1.987 | €4.109 | €6.224 | €12.320 |
| Tasse (forf.) | €1.905 | €3.466 | €5.265 | €10.636 |
| **Netto founder** | **−€951** | **€1.939** | **€430** | **€1.418** |
| **Netto partner** | **€1.987** | **€4.109** | **€6.224** | **€12.320** |
| €/mese founder | −€79 | €162 | €36 | |

---

## 5. P&L — Scenario Ottimistico (67 / 97 / 155 nuovi)

### Dettaglio unità vendute

| | A1 (80/20) | A2 (65/35) | A3 (50/50) |
|--|------------|------------|------------|
| POC Lic / Box | 8 / 2 | — | — |
| Licenze post-POC | 46 | 63 | 78 |
| Box post-POC | 11 | 34 | 77 |
| Totale unità | 67 | 97 | 155 |

### PRO membri paganti

| | Rinnovi | Nuovi (70%) | Totale |
|--|---------|-------------|--------|
| A1 | — | 37 eligible → 26 | 26 |
| A2 | 17 (free-30) + 14 (A1) | 68 | 99 |
| A3 | 55 (A2 × 55%) | 109 | 164 |

### P&L

| | Anno 1 | Anno 2 | Anno 3 | Cum. 3 anni |
|--|--------|--------|--------|-------------|
| Vendite prodotto | €17.583 | €30.953 | €53.995 | €102.531 |
| PRO | €2.054 | €7.821 | €12.877 | €22.752 |
| IC (25%) | €4.233 | €10.209 | €19.920 | €34.362 |
| **Fatturato** | **€23.870** | **€48.983** | **€86.792** | **€159.645** |
| Costi diretti | €3.570 | €6.990 | €13.890 | €24.450 |
| Costi operativi | €4.900 | €12.000 | €22.000 | €38.900 |
| Partner | €5.717 | €12.502 | €22.278 | €40.497 |
| Tasse† | €5.013 | €6.122 | €10.018 | €21.153 |
| **Netto founder** | **€4.670** | **€11.369** | **€18.606** | **€34.645** |
| **Netto partner** | **€5.717** | **€12.502** | **€22.278** | **€40.497** |
| €/mese founder | €389 | €947 | €1.551 | |

†A2-A3: regime ordinario (costi deducibili, conviene sopra €40K fatturato)

---

## 6. Confronto 3 scenari — Anno 3

| | Conserv | Base | Ottim |
|--|---------|------|-------|
| Clienti (base) | 117 | 191 | 319 |
| Fatturato | €25.069 | €47.309 | €86.792 |
| % ricorrente | 32% | 36% | 38% |
| Netto founder A3 | €430 | €8.788 | €18.606 |
| €/mese founder A3 | €36 | €732 | €1.551 |
| Netto founder cumul | €1.418 | €12.979 | €34.645 |
| Netto partner cumul | €12.320 | €22.707 | €40.497 |

---

## 7. Insight strategici

### Il mix software-heavy è meglio per il cash flow del founder

Rispetto al BP originale (mix ~60% Box), il nuovo mix (80→65→50% software) produce:

| Metrica (base) | Vecchio BP | Nuovo modello | Delta |
|----------------|-----------|---------------|-------|
| Fatturato A1 | €17.150 | €14.664 | −€2.486 |
| Costi diretti A1 | €4.260 | €2.460 | **risparmi €1.800** |
| Netto founder A1 | €1.080 | €1.425 | **+€345** |
| Netto founder cumul 3 anni | €10.600 | €12.979 | **+€2.379** |

**Perche'**: in forfettario le tasse sono sul fatturato, non sul profitto. Meno fatturato = meno tasse, ma i risparmi sui costi hardware sono reali. Il margine % sulla licenza (88%) batte quello della Box (67%).

### Il regime fiscale è una leva sottovalutata

Con la struttura partner (20%+35%), i costi reali superano il 33% del fatturato già dall'Anno 1. In forfettario, questi costi non sono deducibili. L'ordinario conviene quando i costi reali (diretti + operativi + partner) superano il 33% del fatturato — cosa che accade in TUTTI gli scenari.

**Da verificare col commercialista**: la transizione a ordinario potrebbe convenire già dall'Anno 1, non dall'Anno 3.

### Il break-even personale è risolto dalla NASpI anticipata

Senza NASpI, il founder avrebbe bisogno di riserve proprie per coprire i primi 18 mesi:

| | Conserv | Base | Ottim |
|--|---------|------|-------|
| €/mese founder A1 (solo business) | −€79 | €119 | €389 |
| €/mese founder A2 (solo business) | €162 | €231 | €947 |
| Riserve necessarie (18 mesi) | €15.000+ | €12.000 | €7.000 |

Con la NASpI anticipata (vedi §8), il quadro cambia radicalmente:

| | Conserv | Base | Ottim |
|--|---------|------|-------|
| NASpI netta (stima) | €14.500 | €14.500 | €14.500 |
| + Cash founder A1 | −€951 | €1.425 | €4.670 |
| + Cash founder A2 | €1.939 | €2.766 | €11.369 |
| **Totale 24 mesi** | **€15.488** | **€18.691** | **€30.539** |
| **€/mese effettivo** | **€645** | **€779** | **€1.272** |

La NASpI anticipata copre il gap dei primi 24 mesi in tutti gli scenari. Il cash dal business si accumula come riserva aggiuntiva, non serve per vivere.

### Il partner prende più cash del founder nei primi 2 anni — ed è corretto

| | Founder cumul A1-A2 | Partner cumul A1-A2 |
|--|---------------------|---------------------|
| Conserv | €988 | €6.096 |
| Base | €4.191 | €10.688 |
| Ottim | €16.039 | €18.219 |

Il partner estrae cash, il founder costruisce equity. Pattern normale per un founder bootstrapped. Il rapporto si inverte quando il business scala (Anno 3+) o quando l'equity viene prezzata.

---

## 8. NASpI anticipata — la pista di atterraggio

### Dati del founder

| Parametro | Valore |
|-----------|--------|
| Mesi residui NASpI | 18-20 |
| Importo mensile stimato | €900-1.000 |
| **Totale lordo** | **€16.200-€20.000** |

### Normativa 2026 (Legge di Bilancio)

Dal 1 gennaio 2026, la NASpI anticipata non è più in soluzione unica ma in **due tranche**:

| Tranche | % | Importo lordo stimato | Netto (~80%) | Quando |
|---------|---|----------------------|--------------|--------|
| Prima | 70% | €11.340-€14.000 | €9.000-€11.200 | Dopo approvazione INPS |
| Seconda | 30% | €4.860-€6.000 | €3.900-€4.800 | Dopo verifica mantenimento attività |
| **Totale** | **100%** | **€16.200-€20.000** | **€13.000-€16.000** | |

### Vincoli

- Domanda entro **30 giorni** dall'avvio attività autonoma (apertura P.IVA)
- Mantenere attività per **almeno 6 mesi consecutivi** (pena restituzione)
- Niente lavoro dipendente per tutta la durata residua NASpI (~24 mesi)
- Tassazione IRPEF come redditi assimilati a lavoro dipendente (~20% effettivo)
- In caso di cessazione prima dei 6 mesi, INPS può richiedere restituzione

### Strategia di attivazione

**Opzione consigliata**: richiedere NASpI anticipata contestualmente all'apertura P.IVA (entro 30 giorni).

Motivazione:
- Il vincolo dei 30 giorni non consente di "aspettare e vedere" — la decisione va presa all'apertura P.IVA
- Il rischio downside è contenuto: se la POC fallisce (STOP al giorno 90), la perdita cash è ~€1.000. La NASpI è già incassata
- Il vincolo 24 mesi no-dipendente è irrilevante se il piano prevede 3 anni di lavoro autonomo
- La POC ha un meccanismo di protezione integrato (GO/NO-GO al giorno 90)

**Alternativa** (da verificare col patronato): ricevere NASpI mensilmente durante la POC (compatibile con P.IVA sotto soglia reddito), poi valutare anticipata per il residuo al GO della POC. Da verificare se il termine dei 30 giorni si calcola dall'apertura P.IVA o dall'effettivo avvio dell'attività generatrice di reddito.

### Impatto sul modello

Con NASpI, il break-even personale del founder non dipende più dal business nei primi 24 mesi. Il cash generato dal business si accumula come riserva per l'Anno 3+ o come capitale per investimenti (es. marketing, fiere, primo collaboratore).

---

## 9. Fondi e agevolazioni — mappa opportunità

### Strumenti identificati

| Strumento | Ente | Importo | Tipo | Requisiti chiave | Fit |
|-----------|------|---------|------|------------------|-----|
| **Smart&Start Italia** | Invitalia | €100K-€1.5M | Tasso zero 80-90% | Startup innovativa iscritta, <60 mesi | **Alto** |
| **Nuove Imprese a Tasso Zero** | Invitalia | fino €1.5M | Tasso zero + fondo perduto | Under 36 o impresa femminile | Da verificare |
| **Credito d'imposta Transizione 5.0** | MIMIT | Variabile | Credito d'imposta | Investimenti R&D/innovazione | Medio |
| **Bandi FESR Liguria** | Regione | Variabili | Mix fondo perduto + prestito | PMI liguri, bandi periodici | **Da esplorare** |
| **EIC Accelerator** | UE | €500K-€2.5M | 70% fondo perduto | Innovazione breakthrough | Futuro (FitScan/AI) |
| **Voucher Cloud & Cybersecurity** | MIMIT | fino €20K | Fondo perduto 50% | PMI/micro | Basso (local-first) |
| Resto al Sud 2.0 | Invitalia | fino €50K | Fondo perduto | 8 regioni Sud | **Non applicabile** (Liguria) |

### Candidato principale: Smart&Start Italia

**Perché è il migliore per FitManager:**
- A sportello (niente graduatorie né scadenze — presenti quando sei pronto)
- Fino a €1.5M a tasso zero, copertura 80% (90% se under 36)
- Spese ammissibili: sviluppo software, licenze, servizi digitali, consulenze, personale
- Nessun cofinanziamento richiesto per la parte agevolata

**Requisiti startup innovativa** (almeno 1 su 3):
1. Spese R&D ≥ 15% del maggiore tra costo e valore produzione — **FitManager qualifica** (100% R&D in Anno 1)
2. Team: ⅓ dottorandi/ricercatori o ⅔ con laurea magistrale — da verificare
3. Titolare di brevetto/software registrato — **FitManager qualifica** (IP proprietaria, 47K+ LOC)

**Roadmap realistica:**

| Mese | Azione |
|------|--------|
| 1 | Apertura P.IVA + NASpI anticipata |
| 1-3 | POC (validazione prodotto) |
| 4 | GO della POC → decisione di procedere |
| 4-5 | Costituzione SRL + iscrizione sezione speciale startup innovative |
| 5-6 | Preparazione business plan per Smart&Start (BP già pronto, serve adattamento formato Invitalia) |
| 6-7 | Presentazione domanda Smart&Start |
| 8-10 | Istruttoria Invitalia (~60-90 giorni) |
| 10+ | Erogazione (se approvata) |

**Importo realistico da richiedere**: €50.000-€100.000 per coprire:
- Primo collaboratore tecnico (12 mesi)
- Marketing strutturato e presenza fiere
- Sviluppo Box (hardware + certificazioni)
- Internazionalizzazione Blocchi 1-2

### Note operative

- I fondi pubblici richiedono **rendicontazione** — ogni spesa deve essere documentata e coerente col progetto approvato
- La NASpI anticipata e Smart&Start sono **cumulabili** — la NASpI copre il founder, Smart&Start copre il business
- L'iscrizione a startup innovativa porta anche altri vantaggi: agevolazioni fiscali, incentivi per investitori (detrazione 30-50%), esonero diritti camerali
- **Azione immediata**: verificare col commercialista la fattibilità di SRL startup innovativa e la compatibilità con il regime fiscale scelto

---

## 10. Come leggere questo documento

- **Ogni numero** è derivabile dalle assunzioni in §1 e dalle formule in §2.
- **Per verificare un numero**: prendi le unità dalla tabella dettaglio, moltiplica per il prezzo, confronta.
- **Se un'assunzione cambia** (es. mix, tasso PRO, pricing), ricalcola dalla formula — il modello è deterministico.
- **Questo documento** integra (non sostituisce) il BP. Il BP contiene strategia, mercato, team, rischi. Questo contiene solo i numeri e la loro derivazione.

---

*Modello Finanziario Analitico v1.0 — 29 marzo 2026*
*Tutti i numeri sono proiezioni basate su assunzioni dichiarate. Ogni assunzione critica verrà validata nella POC nei primi 90 giorni.*

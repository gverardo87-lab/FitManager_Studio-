# FitManager — Report Legale e Regolamentare

> **Versione:** 1.1  
> **Data:** 29 Marzo 2026  
> **Ultimo aggiornamento:** 29 Marzo 2026 — Integrazione EAA, open source, PSD2, anti-spam  
> **Ambito:** Lancio software FitManager in Italia  
> **Fase:** POC — primi 10 clienti (T+30/60 giorni)  
> **Stato:** Pre-apertura P.IVA  

---

## Indice

1. [Executive Summary](#1-executive-summary)
2. [Modelli di Business e Implicazioni Legali](#2-modelli-di-business-e-implicazioni-legali)
3. [Apertura P.IVA e Setup Fiscale](#3-apertura-piva-e-setup-fiscale)
4. [Documentazione Legale Obbligatoria — Software](#4-documentazione-legale-obbligatoria--software)
5. [Compliance GDPR](#5-compliance-gdpr)
6. [Accessibilità Digitale (EAA)](#6-accessibilità-digitale-eaa)
7. [Proprietà Intellettuale](#7-proprietà-intellettuale)
8. [Licenze Open Source e Dipendenze Software](#8-licenze-open-source-e-dipendenze-software)
9. [Compliance Pagamenti (PSD2 / PCI-DSS)](#9-compliance-pagamenti-psd2--pci-dss)
10. [Marketing, Comunicazioni Commerciali e Anti-Spam](#10-marketing-comunicazioni-commerciali-e-anti-spam)
11. [Vendita B2B vs B2C — Codice del Consumo](#11-vendita-b2b-vs-b2c--codice-del-consumo)
12. [Requisiti per la Vendita Hardware (Fase 2)](#12-requisiti-per-la-vendita-hardware-fase-2)
13. [Roadmap Operativa](#13-roadmap-operativa)
14. [Stima Costi di Avvio](#14-stima-costi-di-avvio)
15. [Rischi e Mitigazioni](#15-rischi-e-mitigazioni)
16. [Riferimenti Normativi](#16-riferimenti-normativi)
17. [Allegati e Template](#17-allegati-e-template)

---

## 1. Executive Summary

FitManager prevede due modalità di distribuzione: licenza software (SaaS o perpetua) e installazione su hardware dedicato (Raspberry Pi 5 box). Questo report analizza tutti gli adempimenti legali, fiscali, regolamentari e di compliance necessari per la commercializzazione in Italia, con priorità sulla componente software per il lancio della POC.

**Conclusione chiave:** per il lancio software-only è necessario aprire P.IVA (regime forfettario consigliato), predisporre 4 documenti legali fondamentali (EULA, ToS, Privacy Policy, DPA), garantire la compliance GDPR, verificare la conformità delle licenze open source utilizzate, e predisporre l'integrazione pagamenti in modo conforme a PSD2/PCI-DSS. Non servono certificazioni CE, iscrizioni RAEE né test di laboratorio. L'hardware richiederà un iter separato e più complesso (marcatura CE, registro AEE, test EMC) da affrontare in una fase successiva.

**Nota sulla deroga EAA:** come microimpresa (<10 dipendenti, <2M€ fatturato), FitManager è attualmente esente dagli obblighi dell'European Accessibility Act per i servizi. Si consiglia comunque di progettare accessibile fin da subito (WCAG 2.1 AA) per evitare refactoring costosi in fase di crescita.

---

## 2. Modelli di Business e Implicazioni Legali

### 2.1 Licenza Software (SaaS / Abbonamento)

| Aspetto | Dettaglio |
|---|---|
| **Natura fiscale** | Prestazione di servizi continuativa |
| **IVA** | Art. 7-ter DPR 633/72 (territorialità al committente) |
| **Contratto richiesto** | Licenza d'uso (EULA) + Termini di Servizio |
| **Certificazioni hardware** | Nessuna |
| **GDPR** | Obbligatorio — trattamento dati personali |

### 2.2 Licenza Software (Perpetua / One-time)

| Aspetto | Dettaglio |
|---|---|
| **Natura fiscale** | Cessione diritto d'uso (opera dell'ingegno) |
| **IVA** | Prestazione di servizi se erogata via download |
| **Contratto richiesto** | Licenza d'uso (EULA) con termini specifici |
| **Certificazioni hardware** | Nessuna |
| **GDPR** | Obbligatorio |

### 2.3 FitManager Box — Raspberry Pi 5 (Fase 2)

| Aspetto | Dettaglio |
|---|---|
| **Natura fiscale** | Vendita di bene + licenza software incorporata |
| **Certificazioni** | Marcatura CE obbligatoria (EMC, RED, eventuale LVD) |
| **Registri** | Iscrizione Registro AEE (RAEE) obbligatoria |
| **GDPR** | Obbligatorio |
| **Note** | Trattato in dettaglio alla Sezione 12 |

### 2.4 Decisione per la POC

Per la fase POC (primi 10 clienti, T+30/60 giorni) si consiglia di procedere esclusivamente con la **licenza software**, rimandando il prodotto hardware a una fase successiva. Questo consente di:

- Eliminare i costi e i tempi della certificazione CE (1.500–5.000€+, 2–4 mesi)
- Evitare l'iscrizione al Registro AEE e l'adesione a un consorzio RAEE
- Ridurre la complessità legale e fiscale
- Validare il prodotto con il mercato prima di investire nell'hardware

---

## 3. Apertura P.IVA e Setup Fiscale

### 3.1 Perché la P.IVA è necessaria

La vendita di software, anche a soli 10 clienti, si configura come attività commerciale organizzata e continuativa. La prestazione occasionale non è applicabile quando:

- Esiste un piano commerciale strutturato con clienti programmati
- L'attività è supportata da promozione e organizzazione
- Si prevede continuità nel tempo (non è un evento isolato)
- Il prodotto è offerto a una pluralità di soggetti

La vendita senza P.IVA espone a sanzioni dell'Agenzia delle Entrate per esercizio abusivo di attività commerciale.

### 3.2 Regime Forfettario — Configurazione Consigliata

| Parametro | Valore |
|---|---|
| **Codice ATECO** | 62.01.00 (Produzione di software non connesso all'edizione) |
| **Codice ATECO alternativo** | 62.02.00 (Consulenza nel settore delle tecnologie dell'informatica) |
| **Coefficiente di redditività** | 67% |
| **Imposta sostitutiva** | 5% per i primi 5 anni (poi 15%) |
| **Soglia di ricavi** | Max 85.000€/anno |
| **IVA** | Non addebitata ai clienti |
| **Contributi INPS** | Gestione Separata (~26,07% sul reddito imponibile) |
| **Fatturazione elettronica** | Obbligatoria |

### 3.3 Dicitura in Fattura (Regime Forfettario)

```
Operazione effettuata ai sensi dell'art. 1, commi da 54 a 89,
della Legge n. 190/2014 — Regime forfetario.
Si richiede la non applicazione della ritenuta alla fonte
a titolo d'acconto ai sensi dell'art. 1, comma 67,
Legge n. 190/2014.
```

### 3.4 Adempimenti Fiscali Ricorrenti

| Adempimento | Scadenza | Note |
|---|---|---|
| Fatturazione elettronica | Entro 12 giorni dall'operazione | Via SDI (Sistema di Interscambio) |
| Dichiarazione dei redditi | 30 novembre (anno successivo) | Modello Redditi PF |
| Versamento imposta sostitutiva | 30 giugno + acconto 30 novembre | F24 |
| Contributi INPS | Saldo 30 giugno + acconti | Gestione Separata |

### 3.5 Obblighi Strumentali

| Strumento | Obbligatorio | Note |
|---|---|---|
| **PEC** (Posta Elettronica Certificata) | **Sì** | Obbligatoria per ogni soggetto con P.IVA. Va comunicata al Registro Imprese / Agenzia Entrate. Costo: 10-30€/anno |
| **Fatturazione elettronica** | **Sì** | Tramite SDI. Software dedicato (Fatture in Cloud, Aruba, ecc.) |
| **Conto corrente dedicato** | **Consigliato** | Non obbligatorio in forfettario, ma fortemente raccomandato per separare finanze personali/aziendali e semplificare la contabilità. Indispensabile in caso di controlli |
| **Firma digitale** | **Consigliata** | Necessaria per alcune pratiche telematiche (Camera di Commercio, Registro AEE futuro) |

### 3.6 Tempistiche di Apertura

- Apertura P.IVA all'Agenzia delle Entrate: **1-2 giorni** (modello AA9/12)
- Iscrizione INPS Gestione Separata: **contestuale o entro 30 giorni**
- Attivazione PEC: **1 giorno**
- Iscrizione Camera di Commercio (se attività commerciale): **entro 30 giorni**
- Attivazione fatturazione elettronica: **1-2 giorni**

**Tempo totale stimato: 3–5 giorni lavorativi con commercialista.**

---

## 4. Documentazione Legale Obbligatoria — Software

### 4.1 Contratto di Licenza d'Uso (EULA)

**Riferimento normativo:** Legge 22 aprile 1941, n. 633 (Legge sul Diritto d'Autore), art. 64-bis e seguenti; art. 2575 Codice Civile.

Il contratto di licenza è lo strumento con cui il titolare dei diritti concede a terzi il diritto di utilizzare il software senza cedere la titolarità dei diritti patrimoniali.

**Clausole essenziali da includere:**

- **Definizioni** — software, licenziatario, licenziante, servizio, dati, utenti autorizzati
- **Oggetto e descrizione del software** — funzionalità concesse, moduli inclusi
- **Tipologia di licenza** — SaaS, perpetua, numero utenti/sedi
- **Ambito territoriale e temporale** — Italia, UE, durata
- **Limitazioni d'uso** — divieto di reverse engineering, decompilazione, sublicenza
- **Corrispettivo e modalità di pagamento** — canone, fatturazione, ritardi
- **Aggiornamenti e manutenzione** — inclusioni, SLA, tempi di intervento
- **Garanzie e limitazioni di responsabilità** — conformità alle specifiche, esclusione danni indiretti, limite massimo risarcimento
- **Proprietà intellettuale** — il software resta di proprietà del licenziante
- **Risoluzione e recesso** — cause, preavviso, effetti sulla licenza
- **Clausole GDPR** — rimando al DPA allegato
- **Legge applicabile e foro competente**

### 4.2 Termini e Condizioni di Servizio (ToS)

Documento separato dall'EULA che regola il rapporto commerciale.

**Contenuto minimo:**

- Identificazione del fornitore (ragione sociale, P.IVA, sede, PEC, contatti)
- Descrizione del servizio e livelli garantiti (SLA)
- Procedura di attivazione e onboarding
- Obblighi del cliente (dati corretti, utilizzo lecito, pagamenti)
- Politica di recesso e rimborsi (vedi Sezione 11 per distinzione B2B/B2C)
- Sospensione e cessazione del servizio
- Proprietà dei dati del cliente e portabilità
- Procedura di reclamo
- Modifiche ai termini (preavviso, accettazione)

### 4.3 Privacy Policy

**Riferimento normativo:** Regolamento UE 2016/679 (GDPR), D.Lgs. 196/2003 (Codice Privacy) come modificato dal D.Lgs. 101/2018.

**Informazioni obbligatorie (art. 13 e 14 GDPR):**

- Identità e dati di contatto del Titolare del trattamento
- Dati di contatto del DPO (se nominato)
- Finalità e base giuridica del trattamento
- Categorie di dati personali trattati
- Destinatari o categorie di destinatari dei dati
- Trasferimenti verso paesi terzi (es. se usi cloud provider USA)
- Periodo di conservazione dei dati
- Diritti dell'interessato (accesso, rettifica, cancellazione, portabilità, opposizione)
- Diritto di reclamo al Garante Privacy
- Natura obbligatoria o facoltativa del conferimento dei dati
- Eventuale processo decisionale automatizzato (profilazione)
- Cookie policy (se c'è un'interfaccia web)

### 4.4 Data Processing Agreement (DPA)

**Riferimento normativo:** Art. 28 GDPR.

Il DPA è obbligatorio quando FitManager tratta dati personali per conto delle palestre clienti (rapporto Titolare–Responsabile).

**Schema dei ruoli privacy in FitManager:**

```
Palestra (Cliente)       ← TITOLARE del trattamento
       │                    (decide finalità e mezzi)
       │ nomina come Responsabile
       ▼
FitManager (Tu)          ← RESPONSABILE del trattamento
       │                    (tratta dati per conto del Titolare)
       │ eventuali sub-responsabili
       ▼
Cloud Provider           ← SUB-RESPONSABILE
(es. AWS, Hetzner)          (da autorizzare nel DPA)
       │
       ▼
Payment Gateway          ← SUB-RESPONSABILE
(es. Stripe)                (da autorizzare nel DPA)
```

**Clausole obbligatorie del DPA (art. 28, par. 3 GDPR):**

- Oggetto e durata del trattamento
- Natura e finalità del trattamento
- Tipo di dati personali e categorie di interessati
- Obblighi e diritti del Titolare
- Istruzioni documentate del Titolare
- Obbligo di riservatezza del personale
- Misure di sicurezza tecniche e organizzative (art. 32 GDPR)
- Condizioni per il ricorso a sub-responsabili
- Assistenza al Titolare per i diritti degli interessati
- Assistenza per la notifica di data breach (art. 33–34 GDPR)
- Cancellazione o restituzione dei dati al termine del rapporto
- Messa a disposizione delle informazioni per audit

---

## 5. Compliance GDPR

### 5.1 Registro dei Trattamenti (Art. 30 GDPR)

Documento interno obbligatorio. Deve contenere per ogni trattamento:

| Campo | Esempio FitManager |
|---|---|
| **Finalità** | Gestione abbonamenti palestra, prenotazione corsi, gestione pagamenti |
| **Categorie di interessati** | Clienti delle palestre, dipendenti/istruttori delle palestre |
| **Categorie di dati** | Dati anagrafici, contatti, dati di pagamento, dati di frequenza, eventuali dati relativi alla salute |
| **Destinatari** | Cloud provider, eventuale gateway di pagamento |
| **Trasferimenti extra-UE** | Specificare se presenti (es. cloud USA — necessaria valutazione di adeguatezza) |
| **Termini di cancellazione** | Definire per ogni categoria |
| **Misure di sicurezza** | Cifratura, controllo accessi, backup, log |

### 5.2 Dati Relativi alla Salute — Attenzione Speciale

Se FitManager tratta dati che possono qualificarsi come "dati relativi alla salute" (art. 9 GDPR), si applicano regole più stringenti:

**Possibili dati sensibili nel contesto fitness:**

- Certificati medici di idoneità sportiva
- Condizioni fisiche, patologie, limitazioni
- Piani di allenamento personalizzati basati su condizioni fisiche
- Dati biometrici (peso, massa grassa, frequenza cardiaca)
- Intolleranze alimentari (se presente modulo nutrizione)

**Conseguenze:**

- Necessario il **consenso esplicito** dell'interessato (art. 9, par. 2, lett. a)
- Possibile obbligo di **DPIA** (Valutazione d'Impatto — art. 35 GDPR)
- Misure di sicurezza rafforzate
- Possibile obbligo di nomina **DPO** (Data Protection Officer) se il trattamento è su larga scala

**Raccomandazione:** valutare con l'avvocato se e quali dati trattati da FitManager rientrano nella definizione di "dati relativi alla salute" e agire di conseguenza. Se possibile, progettare il software per minimizzare la raccolta di questi dati (principio di minimizzazione, art. 5 GDPR).

### 5.3 Misure di Sicurezza Tecniche (Art. 32 GDPR)

Checklist minima per FitManager:

- [ ] **Cifratura in transito** — HTTPS/TLS per tutte le comunicazioni
- [ ] **Cifratura at rest** — database cifrato
- [ ] **Autenticazione sicura** — password hashing (bcrypt/argon2), 2FA consigliata
- [ ] **Controllo degli accessi** — RBAC (Role-Based Access Control)
- [ ] **Backup regolari** — con test di ripristino periodico
- [ ] **Log degli accessi** — tracciabilità delle operazioni, retention minima 6 mesi
- [ ] **Gestione diritti GDPR** — funzionalità per esportazione dati (portabilità), cancellazione dati (diritto all'oblio), rettifica dati
- [ ] **Procedura di data breach** — notifica al Garante entro 72 ore, notifica agli interessati se rischio elevato
- [ ] **Aggiornamenti di sicurezza** — patch management regolare
- [ ] **Disaster recovery** — piano documentato con RTO/RPO definiti, test periodico di restore

### 5.4 Cookie e Consenso (se interfaccia web)

Se FitManager ha un pannello web accessibile via browser:

- Cookie banner conforme (consenso preventivo per cookie non tecnici)
- Cookie policy separata o integrata nella Privacy Policy
- Registro dei consensi
- Blocco preventivo degli script di tracciamento prima del consenso

---

## 6. Accessibilità Digitale (EAA)

### 6.1 Quadro Normativo

L'European Accessibility Act (Direttiva UE 2019/882) è stato recepito in Italia con il **D.Lgs. 27 maggio 2022, n. 82** ed è in vigore dal **28 giugno 2025**. La direttiva impone che prodotti e servizi digitali siano accessibili alle persone con disabilità.

### 6.2 Applicabilità a FitManager

FitManager, in quanto piattaforma SaaS, rientra potenzialmente nell'ambito di applicazione dell'EAA. Tuttavia, esiste una **deroga per le microimprese**.

**Definizione di microimpresa (esente per i servizi):**

- Meno di 10 dipendenti **E**
- Fatturato annuo inferiore a 2 milioni di euro

**Stato attuale:** FitManager è una microimpresa → **esente dagli obblighi EAA per i servizi** nella fase di lancio.

**Attenzione:** la deroga decade non appena si superano le soglie. Inoltre, la deroga riguarda solo i servizi, non i prodotti (rilevante per la futura fase hardware).

### 6.3 Standard Tecnico di Riferimento

- **WCAG 2.1 Livello AA** (Web Content Accessibility Guidelines)
- **Norma UNI CRI EN 301549** (standard europeo di riferimento)
- Principi POUR: Perceivable, Operable, Understandable, Robust

### 6.4 Sanzioni

- Da 2.500€ a 40.000€ per non conformità
- Per soggetti già obbligati dalla Legge Stanca: fino al 5% del fatturato annuo

### 6.5 Raccomandazione Strategica

Anche se attualmente esenti, si consiglia fortemente di **progettare FitManager con accessibilità nativa** fin dalla POC:

- Il costo di rendere accessibile un prodotto in fase di progettazione è minimo
- Il costo di un retrofit di accessibilità su software esistente è 5-10x superiore
- L'accessibilità migliora la UX per tutti gli utenti, non solo quelli con disabilità
- Prepara il prodotto per la crescita oltre le soglie di microimpresa
- Rappresenta un vantaggio competitivo nel settore fitness (palestre con utenti diversamente abili)

**Checklist accessibilità minima:**

- [ ] Contrasto colori sufficiente (rapporto minimo 4.5:1)
- [ ] Navigazione completa da tastiera
- [ ] Testi alternativi per immagini
- [ ] Struttura heading semantica (h1, h2, h3...)
- [ ] Form con label associati correttamente
- [ ] Messaggi di errore chiari e accessibili
- [ ] Focus visibile sugli elementi interattivi

---

## 7. Proprietà Intellettuale

### 7.1 Tutela del Software

Il software è protetto automaticamente come opera dell'ingegno ai sensi della Legge 633/1941 (art. 2, n. 8 e art. 64-bis e seguenti). La tutela sorge con la creazione dell'opera, senza necessità di registrazione.

**Diritti esclusivi dell'autore:**

- Riproduzione permanente o temporanea del programma
- Traduzione, adattamento, trasformazione
- Distribuzione al pubblico dell'originale o di copie

### 7.2 Azioni Consigliate per Rafforzare la Tutela

| Azione | Priorità | Costo stimato |
|---|---|---|
| Deposito SIAE del software | Media | ~100-200€ |
| Registrazione marchio "FitManager" (UIBM) | Alta | ~200-400€ (classe 9 e 42) |
| Timestamp del codice sorgente (PEC o blockchain) | Alta | Gratuito/minimo |
| NDA con eventuali collaboratori | Alta | ~200-500€ (avvocato) |
| Clausole IP chiare nell'EULA | Obbligatoria | Inclusa nel costo EULA |

### 7.3 Marchio

Si consiglia di verificare la disponibilità del marchio "FitManager" presso l'UIBM (Ufficio Italiano Brevetti e Marchi) e procedere alla registrazione nelle classi:

- **Classe 9** — Software, programmi per elaboratori
- **Classe 42** — Progettazione e sviluppo di software; SaaS

Ricerca preliminare gratuita su: https://www.uibm.gov.it

---

## 8. Licenze Open Source e Dipendenze Software

### 8.1 Perché è Rilevante

FitManager utilizza quasi certamente componenti open source (framework, librerie, database, sistema operativo). Ogni componente ha una licenza con obblighi specifici. La violazione di licenze open source può comportare:

- Obbligo di rilascio del codice sorgente di FitManager (se si viola una licenza copyleft come GPL)
- Azioni legali da parte dei titolari dei diritti
- Incompatibilità con il modello di business proprietario

### 8.2 Tipologie di Licenze e Rischi

| Tipo | Licenze | Rischio per software proprietario | Azione richiesta |
|---|---|---|---|
| **Permissive** | MIT, BSD, Apache 2.0 | Basso | Mantenere notice di copyright e licenza |
| **Copyleft debole** | LGPL, MPL | Medio | OK se usate come librerie linkate dinamicamente; non modificare il codice della libreria stessa |
| **Copyleft forte** | GPL v2, GPL v3, AGPL | **Alto** | Se incorporato nel software, tutto il codice derivato deve essere rilasciato sotto la stessa licenza. **AGPL** si estende anche al software offerto via rete (SaaS) |
| **Proprietarie** | Varie | Variabile | Verificare singolarmente i termini di licenza |

### 8.3 Attenzione Specifica: AGPL e SaaS

La licenza **AGPL (Affero GPL)** è particolarmente rilevante per FitManager in quanto SaaS. A differenza della GPL standard, l'AGPL richiede la distribuzione del codice sorgente anche quando il software è offerto come servizio via rete, senza distribuzione fisica. Se FitManager incorpora componenti AGPL, l'intero codice potrebbe dover essere reso open source.

**Componenti comuni con licenza da verificare attentamente:**

- Database (MySQL è GPL, PostgreSQL è permissiva)
- Framework web (verificare la licenza specifica)
- Librerie di autenticazione, crittografia, UI
- Runtime e linguaggio (Node.js è MIT, Python è PSF permissiva)
- Sistema operativo Raspberry Pi OS (basato su Debian, mix di licenze)

### 8.4 Software Bill of Materials (SBOM)

Si consiglia di creare e mantenere un inventario completo delle dipendenze software:

```
SBOM — Struttura consigliata per ogni dipendenza:

- Nome del componente
- Versione
- Tipo di licenza
- URL della licenza
- Uso nel progetto (runtime, dev-only, opzionale)
- Compatibilità verificata con distribuzione proprietaria: Sì/No
- Note
```

**Strumenti per generare SBOM automaticamente:**

- npm audit / npm ls --all (Node.js)
- pip-licenses (Python)
- cargo license (Rust)
- SPDX / CycloneDX (formati standard)

### 8.5 Azioni Richieste

- [ ] Generare SBOM completo di tutte le dipendenze
- [ ] Verificare che nessuna dipendenza runtime abbia licenza GPL/AGPL (o sostituirla)
- [ ] Includere tutte le notice di copyright richieste dalle licenze permissive
- [ ] Documentare le licenze nella sezione "Third-party licenses" dell'applicazione
- [ ] Impostare un processo di verifica licenze per ogni nuova dipendenza aggiunta

---

## 9. Compliance Pagamenti (PSD2 / PCI-DSS)

### 9.1 Quadro Normativo

Se FitManager integra funzionalità di pagamento (abbonamenti palestra, acquisto corsi, ecc.), entrano in gioco:

- **PSD2** (Direttiva UE 2015/2366) — recepita in Italia con D.Lgs. 218/2017
- **PCI-DSS** (Payment Card Industry Data Security Standard) — standard del settore carte di pagamento
- **SCA** (Strong Customer Authentication) — autenticazione forte del cliente (art. 97 PSD2)

### 9.2 Cosa Significa per FitManager

FitManager **non** deve diventare un istituto di pagamento. La strategia corretta è delegare completamente la gestione dei pagamenti a un gateway certificato (Stripe, PayPal, SumUp, Nexi, ecc.).

**Regola fondamentale: FitManager non deve mai toccare, memorizzare, trasmettere o processare direttamente i dati delle carte di credito/debito.**

### 9.3 Requisiti Tecnici

| Requisito | Dettaglio |
|---|---|
| **Integrazione gateway** | Usare l'SDK/API del gateway. Mai form di pagamento custom che raccolgono numeri di carta |
| **Tokenizzazione** | Il gateway restituisce un token. FitManager salva solo il token, mai il PAN (numero carta) |
| **SCA / 3D Secure** | Il gateway deve gestire l'autenticazione forte (3D Secure 2.0). FitManager deve supportare il flusso di redirect/challenge |
| **PCI-DSS SAQ-A** | Se FitManager delega tutto al gateway (iframe/redirect), rientra nel livello SAQ-A (più semplice). Nessun dato carta transita sui server FitManager |
| **HTTPS obbligatorio** | Tutte le pagine che coinvolgono il pagamento devono essere su HTTPS |
| **Ricevute/Fatture** | FitManager può generare ricevute per conto della palestra, ma attenzione: se la palestra è il venditore, è lei che emette la fattura al suo cliente, non FitManager |

### 9.4 Obblighi Contrattuali con il Gateway

- Stipulare un contratto con il payment gateway (Stripe, ecc.)
- Verificare che il gateway sia autorizzato come istituto di pagamento nella UE
- Includere il gateway come sub-responsabile nel DPA (tratta dati personali)
- Mantenere aggiornata l'integrazione SDK per compliance SCA

### 9.5 Nota su Fatturazione Elettronica delle Palestre

Se FitManager offre funzionalità di emissione ricevute/fatture per conto delle palestre clienti, verificare con il commercialista i requisiti relativi a:

- Corrispettivi elettronici (se la palestra è tenuta alla trasmissione telematica)
- Numerazione e conservazione delle fatture
- Responsabilità fiscale (è della palestra, non di FitManager)

---

## 10. Marketing, Comunicazioni Commerciali e Anti-Spam

### 10.1 Quadro Normativo

- **Art. 130 D.Lgs. 196/2003** (Codice Privacy) — comunicazioni indesiderate
- **GDPR art. 6 e 7** — base giuridica e consenso
- **D.Lgs. 70/2003** — commercio elettronico (attuazione Direttiva 2000/31/CE)

### 10.2 Regole per Email Promozionali e Newsletter

| Azione | Consenso richiesto | Note |
|---|---|---|
| Email promozionali a nuovi contatti | **Consenso preventivo, specifico, libero e documentato** | Opt-in esplicito obbligatorio. No caselle pre-spuntate |
| Email a clienti esistenti su prodotti simili | **Soft opt-in ammesso** (art. 130 comma 4) | Solo per prodotti/servizi analoghi a quelli già acquistati. Deve essere data possibilità di opt-out ad ogni invio |
| Newsletter informativa | **Consenso esplicito** | Deve essere separato dal consenso al trattamento dati |
| Email transazionali (conferma ordine, scadenza, ecc.) | **Nessun consenso aggiuntivo** | Rientrano nell'esecuzione del contratto (art. 6.1.b GDPR) |

### 10.3 Requisiti per Ogni Comunicazione Commerciale

- Identificazione chiara del mittente (nome, P.IVA, indirizzo)
- Natura promozionale chiaramente indicata
- Link di disiscrizione (unsubscribe) funzionante in ogni email
- Disiscrizione effettiva entro 10 giorni lavorativi
- Registro dei consensi (chi ha acconsentito, quando, come, a cosa)

### 10.4 Sanzioni

Le sanzioni per spam/comunicazioni non richieste possono essere significative: il Garante Privacy ha comminato sanzioni da decine di migliaia a milioni di euro per violazioni dell'art. 130. Anche una piccola impresa non è esente.

---

## 11. Vendita B2B vs B2C — Codice del Consumo

### 11.1 Perché la Distinzione è Importante

FitManager potrebbe vendere sia a **palestre con P.IVA** (B2B) sia a **personal trainer privati senza P.IVA** o **singoli utenti** (B2C). La normativa cambia significativamente nei due casi.

### 11.2 Confronto Obblighi

| Aspetto | B2B (palestre con P.IVA) | B2C (personal trainer privati, utenti singoli) |
|---|---|---|
| **Normativa** | Codice Civile | Codice del Consumo (D.Lgs. 206/2005) |
| **Diritto di recesso** | Non previsto (salvo accordo) | **14 giorni** dalla conclusione del contratto, senza motivazione |
| **Informativa precontrattuale** | Buona prassi | **Obbligatoria** (art. 49 D.Lgs. 206/2005) |
| **Clausole vessatorie** | Art. 1341 C.C. (doppia sottoscrizione) | Art. 33-38 D.Lgs. 206/2005 (tutela rafforzata, clausole nulle di diritto) |
| **Garanzia legale** | Accordo tra le parti | **2 anni** obbligatori |
| **Foro competente** | Libera scelta | **Foro del consumatore** (inderogabile) |
| **ADR/ODR** | Facoltativo | Obbligo di informare sulla piattaforma ODR europea |

### 11.3 Raccomandazione

Predisporre **due set di ToS** (o un unico documento con sezioni differenziate):

- ToS per clienti business (palestre, centri sportivi con P.IVA)
- ToS per consumatori (personal trainer privati, utenti singoli)

Se per la POC i 10 clienti sono tutte palestre con P.IVA, la normativa B2C non è immediatamente urgente ma va prevista per la fase di scaling.

### 11.4 Piattaforma ODR

Se si vende a consumatori, è obbligatorio inserire nel sito/app un link alla piattaforma europea di risoluzione delle controversie online:

```
https://ec.europa.eu/consumers/odr
```

---

## 12. Requisiti per la Vendita Hardware (Fase 2)

> ⚠️ **Questa sezione è rilevante solo per la fase successiva alla POC, quando si introdurrà il FitManager Box con Raspberry Pi 5.**

### 12.1 Marcatura CE

Assemblare un Raspberry Pi 5 con alimentatore, case e software preinstallato crea un **prodotto nuovo** che richiede la propria marcatura CE, indipendentemente dal fatto che i singoli componenti siano già certificati.

**Direttive applicabili al FitManager Box:**

| Direttiva | Codice | Applicabilità |
|---|---|---|
| Compatibilità Elettromagnetica | EMC 2014/30/UE | **Sì** — il prodotto non deve generare interferenze né esserne disturbato |
| Apparecchiature Radio | RED 2014/53/UE | **Sì** — Raspberry Pi 5 ha Wi-Fi e Bluetooth integrati |
| Bassa Tensione | LVD 2014/35/UE | **Da valutare** — si applica a dispositivi 50-1000V AC; con alimentazione USB 5V potrebbe non applicarsi, ma l'alimentatore esterno potrebbe rientrarci |
| Sostanze Pericolose | RoHS 2011/65/UE | **Sì** — restrizione sostanze pericolose nei componenti |
| Sicurezza Generale Prodotti | GPSR 2023/988 | **Sì** — in vigore dal 13/12/2024, obblighi per tutti gli attori della catena |

**Iter di marcatura CE:**

1. Identificare tutte le direttive e norme armonizzate applicabili
2. Eseguire test EMC e RED presso laboratorio accreditato ISO 17025
3. Predisporre il fascicolo tecnico (schemi, descrizione, risultati test, analisi rischi)
4. Redigere la Dichiarazione di Conformità UE
5. Apporre il marchio CE sul prodotto/imballaggio/documentazione
6. Conservare il fascicolo tecnico per 10 anni

**Costo stimato:** 1.500–5.000€+ (test di laboratorio) + 500–2.000€ (consulenza tecnica)

**Tempo stimato:** 2–4 mesi

### 12.2 Registro AEE (RAEE)

L'iscrizione al Registro Nazionale dei Produttori di AEE è obbligatoria **prima** di immettere qualsiasi apparecchiatura sul mercato.

**Sanzioni per mancata iscrizione:** da 30.000 a 100.000€ (art. 38, D.Lgs. 49/2014).

**Procedura:**

1. Aderire a un sistema collettivo di gestione RAEE (es. Erion, EcoLight, Ecolamp)
2. Iscriversi al Registro AEE via portale telematico (registroaee.it)
3. Versare: tassa di concessione governativa 168€ + diritti di segreteria 30€ + bollo 16€
4. Indicare il numero di iscrizione su tutti i documenti commerciali entro 30 giorni
5. Presentare comunicazione annuale delle quantità immesse sul mercato (entro il 30 aprile)

### 12.3 Ulteriori Obblighi per l'Hardware

- **Etichettatura RAEE** — simbolo del bidoncino barrato sul prodotto
- **Garanzia legale** — 2 anni per i consumatori (D.Lgs. 206/2005)
- **Istruzioni d'uso** — in lingua italiana, con avvertenze di sicurezza
- **Informazioni al consumatore** — nome/indirizzo produttore, modello, alimentazione
- **Assicurazione RC prodotto** — fortemente consigliata
- **Conformità EAA** — la deroga microimpresa NON si applica ai prodotti; il FitManager Box dovrà essere accessibile

---

## 13. Roadmap Operativa

### Fase 0 — Setup (Settimana 1–2)

```
PRIORITÀ CRITICA — Blocca il lancio se non completato
```

| # | Azione | Responsabile | Tempo | Status |
|---|---|---|---|---|
| 0.1 | Trovare commercialista (esperto digitale) | Fondatore | 2-3 giorni | ☐ |
| 0.2 | Apertura P.IVA regime forfettario (ATECO 62.01.00) | Commercialista | 3-5 giorni | ☐ |
| 0.3 | Iscrizione INPS Gestione Separata | Commercialista | Contestuale | ☐ |
| 0.4 | Attivazione PEC | Fondatore | 1 giorno | ☐ |
| 0.5 | Attivazione fatturazione elettronica (SDI) | Commercialista | 1-2 giorni | ☐ |
| 0.6 | Apertura conto corrente dedicato | Fondatore | 1-3 giorni | ☐ |
| 0.7 | Trovare avvocato specializzato diritto digitale | Fondatore | 2-3 giorni | ☐ |

### Fase 1 — Documentazione Legale (Settimana 2–3)

```
PRIORITÀ ALTA — Necessario prima di firmare contratti con i clienti POC
```

| # | Azione | Responsabile | Tempo | Status |
|---|---|---|---|---|
| 1.1 | Redazione EULA (Contratto di Licenza d'Uso) | Avvocato | 5-10 giorni | ☐ |
| 1.2 | Redazione Termini e Condizioni di Servizio (B2B) | Avvocato | 5-10 giorni | ☐ |
| 1.3 | Redazione Privacy Policy | Avvocato | 5-7 giorni | ☐ |
| 1.4 | Redazione DPA (Data Processing Agreement) | Avvocato | 5-7 giorni | ☐ |
| 1.5 | Verifica disponibilità marchio "FitManager" | Fondatore/Avvocato | 1-2 giorni | ☐ |

### Fase 2 — Compliance Tecnica (Settimana 3–4)

```
PRIORITÀ ALTA — Necessario prima del go-live
```

| # | Azione | Responsabile | Tempo | Status |
|---|---|---|---|---|
| 2.1 | Compilazione Registro dei Trattamenti (art. 30) | Fondatore | 2-3 giorni | ☐ |
| 2.2 | Implementazione misure sicurezza GDPR nel software | Dev Team | 5-10 giorni | ☐ |
| 2.3 | Valutazione necessità DPIA (dati salute) | Avvocato | 3-5 giorni | ☐ |
| 2.4 | Setup cookie banner e consensi (se web app) | Dev Team | 1-2 giorni | ☐ |
| 2.5 | Test funzionalità diritti GDPR (export, delete) | Dev Team | 2-3 giorni | ☐ |
| 2.6 | Generazione SBOM e audit licenze open source | Dev Team | 1-2 giorni | ☐ |
| 2.7 | Integrazione payment gateway (Stripe/altro) | Dev Team | 3-5 giorni | ☐ |
| 2.8 | Verifica accessibilità base (WCAG 2.1 AA) | Dev Team | 2-3 giorni | ☐ |

### Fase 3 — Go-Live POC (Settimana 4–5)

```
PRIORITÀ MEDIA — Completamento setup commerciale
```

| # | Azione | Responsabile | Tempo | Status |
|---|---|---|---|---|
| 3.1 | Stipula assicurazione RC professionale | Fondatore | 3-5 giorni | ☐ |
| 3.2 | Registrazione marchio UIBM (classi 9 e 42) | Avvocato | 1-2 giorni (invio) | ☐ |
| 3.3 | Deposito timestamp codice sorgente | Fondatore | 1 giorno | ☐ |
| 3.4 | Predisposizione template fattura | Commercialista | 1 giorno | ☐ |
| 3.5 | Setup sistema consensi marketing (se newsletter) | Dev Team | 1-2 giorni | ☐ |
| 3.6 | Firma contratti con primi 10 clienti POC | Fondatore | Ongoing | ☐ |

### Fase 4 — Post-POC / Hardware (Mese 3–6)

```
PRIORITÀ FUTURA — Solo dopo validazione POC
```

| # | Azione | Responsabile | Tempo | Status |
|---|---|---|---|---|
| 4.1 | Redazione ToS versione B2C (se necessario) | Avvocato | — | ☐ |
| 4.2 | Contattare laboratorio accreditato per test EMC/RED | Fondatore | — | ☐ |
| 4.3 | Progettazione case/assemblaggio FitManager Box | Dev Team | — | ☐ |
| 4.4 | Esecuzione test di conformità | Laboratorio | — | ☐ |
| 4.5 | Predisposizione fascicolo tecnico CE | Consulente CE | — | ☐ |
| 4.6 | Adesione sistema collettivo RAEE | Fondatore | — | ☐ |
| 4.7 | Iscrizione Registro AEE | Commercialista | — | ☐ |
| 4.8 | Dichiarazione di Conformità UE | Fondatore | — | ☐ |
| 4.9 | Audit accessibilità completo (EAA) pre-scaling | Consulente | — | ☐ |

---

## 14. Stima Costi di Avvio

### 14.1 Costi una tantum — Fase Software

| Voce | Stima min | Stima max | Note |
|---|---|---|---|
| Avvocato (EULA + ToS + Privacy + DPA) | 1.000€ | 2.500€ | Pacchetto completo |
| Registrazione marchio UIBM | 200€ | 400€ | 2 classi, 10 anni |
| Deposito SIAE software | 100€ | 200€ | Opzionale ma consigliato |
| Assicurazione RC professionale (anno 1) | 200€ | 500€ | Dipende da massimale |
| **Totale una tantum** | **1.500€** | **3.600€** | |

### 14.2 Costi ricorrenti — Annuali

| Voce | Stima min | Stima max | Note |
|---|---|---|---|
| Commercialista (regime forfettario) | 600€ | 1.200€ | /anno |
| Fatturazione elettronica (software) | 25€ | 100€ | /anno |
| PEC | 10€ | 30€ | /anno |
| Assicurazione RC professionale | 200€ | 500€ | /anno |
| Payment gateway (commissioni) | ~1.5% | ~3% | Per transazione |
| Contributi INPS Gestione Separata | ~26% | del reddito | imponibile |
| Imposta sostitutiva | 5% | del reddito | (primi 5 anni) |
| **Totale fisso annuale (escluso INPS/imposte)** | **835€** | **1.830€** | |

### 14.3 Costi aggiuntivi — Fase Hardware (futura)

| Voce | Stima min | Stima max | Note |
|---|---|---|---|
| Test laboratorio EMC/RED | 1.500€ | 5.000€ | Per prodotto |
| Consulenza tecnica CE | 500€ | 2.000€ | Fascicolo tecnico |
| Iscrizione Registro AEE | 214€ | 214€ | Una tantum |
| Adesione consorzio RAEE | Variabile | Variabile | Eco-contributo per unità |
| Audit accessibilità EAA | 500€ | 2.000€ | Se necessario |
| **Totale hardware** | **2.714€** | **9.214€+** | |

---

## 15. Rischi e Mitigazioni

| # | Rischio | Probabilità | Impatto | Mitigazione |
|---|---|---|---|---|
| R1 | Vendita senza P.IVA → sanzioni AdE | Alta (se si procede senza) | Alto | Apertura P.IVA prima del lancio |
| R2 | Data breach → sanzioni Garante Privacy | Media | Molto alto (fino a 4% fatturato o 20M€) | Misure sicurezza art. 32, procedura breach |
| R3 | Mancanza EULA → dispute con clienti | Media | Alto | Redazione EULA professionale |
| R4 | Violazione IP da terzi | Bassa | Medio | Registrazione marchio, timestamp codice |
| R5 | Trattamento dati salute non conforme | Media | Molto alto | DPIA, consenso esplicito, misure rafforzate |
| R6 | Vendita hardware senza CE → sequestro + sanzioni penali | Alta (se si procede senza) | Molto alto | Rimandare hardware a post-certificazione |
| R7 | Vendita hardware senza iscrizione AEE → sanzione 30-100K€ | Alta (se si procede senza) | Molto alto | Iscrizione preventiva al Registro |
| R8 | Mancata portabilità dati → reclamo Garante | Media | Medio | Implementare export dati nel software |
| R9 | Cloud provider extra-UE non conforme | Media | Alto | Scegliere provider UE o con SCC/adeguatezza |
| R10 | Responsabilità civile per malfunzionamento software | Bassa | Medio | Limitazione responsabilità in EULA + RC |
| R11 | **Violazione licenza open source (GPL/AGPL)** → obbligo rilascio codice sorgente | Media | **Molto alto** | Audit SBOM, sostituire dipendenze GPL/AGPL |
| R12 | **Dati carte di credito su server FitManager** → violazione PCI-DSS | Bassa (se si usa gateway) | Molto alto | Mai memorizzare PAN; solo tokenizzazione via gateway |
| R13 | **Spam / email marketing senza consenso** → sanzione Garante | Media | Alto | Consenso esplicito separato, registro consensi, opt-out |
| R14 | **Non conformità EAA post-crescita** → sanzione fino a 40K€ | Bassa (a breve) | Medio | Progettare accessibile fin da subito |
| R15 | **Vendita B2C senza conformità Codice del Consumo** → clausole nulle | Media | Medio | ToS differenziati B2B/B2C, diritto di recesso 14gg |
| R16 | **Mancanza PEC** → irregolarità formale | Alta (se dimenticata) | Basso | Attivare PEC in fase di apertura P.IVA |

---

## 16. Riferimenti Normativi

### Fiscale e Commerciale

- **Legge 190/2014** (commi 54-89) — Regime forfettario
- **DPR 633/1972** — Disciplina IVA
- **Art. 7-ter DPR 633/72** — Territorialità prestazioni di servizi
- **D.Lgs. 206/2005** — Codice del Consumo (garanzia, recesso, clausole vessatorie)
- **D.Lgs. 70/2003** — Commercio elettronico

### Proprietà Intellettuale

- **Legge 633/1941** — Legge sul Diritto d'Autore (art. 2 n.8, art. 64-bis e ss.)
- **D.Lgs. 30/2005** — Codice della Proprietà Industriale
- **Art. 2575 Codice Civile** — Opere dell'ingegno

### Privacy e Protezione Dati

- **Regolamento UE 2016/679** (GDPR)
- **D.Lgs. 196/2003** — Codice Privacy (come modificato dal D.Lgs. 101/2018)
- **Art. 28 GDPR** — Obblighi del Responsabile del trattamento
- **Art. 30 GDPR** — Registro dei trattamenti
- **Art. 32 GDPR** — Sicurezza del trattamento
- **Art. 33-34 GDPR** — Notifica data breach
- **Art. 35 GDPR** — Valutazione d'impatto (DPIA)
- **Art. 130 D.Lgs. 196/2003** — Comunicazioni indesiderate (anti-spam)

### Accessibilità

- **Direttiva UE 2019/882** — European Accessibility Act
- **D.Lgs. 82/2022** — Recepimento italiano EAA
- **Legge 4/2004** (Legge Stanca) — Accessibilità siti PA (riferimento storico)
- **WCAG 2.1** — Web Content Accessibility Guidelines
- **UNI CRI EN 301549** — Standard europeo accessibilità ICT

### Pagamenti

- **Direttiva UE 2015/2366** (PSD2) — Servizi di pagamento
- **D.Lgs. 218/2017** — Recepimento italiano PSD2
- **PCI-DSS v4.0** — Standard sicurezza dati carte di pagamento

### Hardware (Fase 2)

- **Direttiva EMC 2014/30/UE** — Compatibilità elettromagnetica
- **Direttiva RED 2014/53/UE** — Apparecchiature radio
- **Direttiva LVD 2014/35/UE** — Bassa tensione
- **Direttiva RoHS 2011/65/UE** — Sostanze pericolose
- **Regolamento GPSR 2023/988** — Sicurezza generale prodotti
- **D.Lgs. 49/2014** — Attuazione direttiva RAEE 2012/19/UE
- **Regolamento 765/2008** — Vigilanza del mercato e marcatura CE

---

## 17. Allegati e Template

> I seguenti documenti devono essere redatti da un avvocato specializzato. Le tracce qui sotto servono come punto di partenza per la discussione con il legale.

### Allegato A — Struttura EULA (traccia)

```
1. Premesse e definizioni
2. Oggetto della licenza
3. Diritti concessi e limitazioni
4. Durata e rinnovo
5. Corrispettivo e pagamenti
6. Consegna e installazione
7. Manutenzione e aggiornamenti
8. Garanzie
9. Limitazione di responsabilità
10. Proprietà intellettuale
11. Riservatezza
12. Protezione dati personali (rinvio a DPA)
13. Risoluzione e recesso
14. Disposizioni finali
15. Legge applicabile e foro competente
```

### Allegato B — Struttura DPA (traccia)

```
1. Definizioni
2. Oggetto e durata del trattamento
3. Natura e finalità del trattamento
4. Tipo di dati e categorie di interessati
5. Obblighi del Responsabile
6. Obblighi del Titolare
7. Sub-responsabili (elenco: cloud provider, payment gateway)
8. Trasferimenti internazionali
9. Misure di sicurezza (Appendice tecnica)
10. Gestione data breach
11. Assistenza al Titolare
12. Audit e ispezioni
13. Restituzione e cancellazione dati
14. Responsabilità e indennizzo
```

### Allegato C — Checklist Pre-Lancio

```
FISCALE
☐ P.IVA aperta (ATECO 62.01.00)
☐ INPS Gestione Separata attivata
☐ PEC attivata e comunicata
☐ Fatturazione elettronica operativa
☐ Conto corrente dedicato aperto

LEGALE
☐ EULA redatto e revisionato
☐ Termini e Condizioni pronti (B2B; B2C se necessario)
☐ Privacy Policy pubblicata
☐ DPA predisposto
☐ Cookie banner implementato (se web app)

GDPR
☐ Registro dei trattamenti compilato
☐ Misure di sicurezza art. 32 implementate
☐ Funzionalità diritti GDPR operative (export, delete, rectify)
☐ Procedura data breach documentata
☐ DPIA eseguita (se necessaria)
☐ Valutazione cloud provider (localizzazione dati, SCC)

OPEN SOURCE
☐ SBOM (Software Bill of Materials) generato
☐ Audit licenze completato — nessuna dipendenza GPL/AGPL incompatibile
☐ Notice di copyright incluse per licenze permissive
☐ Sezione "Third-party licenses" nell'applicazione

PAGAMENTI
☐ Contratto con payment gateway stipulato
☐ Integrazione via SDK/iframe (nessun dato carta su server FitManager)
☐ 3D Secure / SCA supportato
☐ Payment gateway incluso come sub-responsabile nel DPA

ACCESSIBILITÀ
☐ Contrasto colori verificato (≥ 4.5:1)
☐ Navigazione da tastiera funzionante
☐ Form con label corretti
☐ Struttura heading semantica
☐ Focus visibile sugli elementi interattivi

MARKETING
☐ Sistema opt-in consenso marketing (separato da consenso dati)
☐ Link disiscrizione in ogni email promozionale
☐ Registro dei consensi marketing implementato

IP
☐ Marchio verificato su banca dati UIBM
☐ Domanda di registrazione marchio inviata
☐ Timestamp codice sorgente eseguito
☐ NDA predisposto per collaboratori

COMMERCIALE
☐ Pricing definito
☐ Template fattura pronto
☐ Assicurazione RC professionale attiva
☐ Contratti clienti POC firmati
```

### Allegato D — Struttura SBOM (traccia)

```
# Software Bill of Materials — FitManager v[X.Y.Z]
# Generato il: [DATA]

| Componente | Versione | Licenza | Tipo uso | Compatibile | Note |
|---|---|---|---|---|---|
| [nome] | [ver] | MIT | Runtime | ✅ | |
| [nome] | [ver] | Apache-2.0 | Runtime | ✅ | |
| [nome] | [ver] | GPL-3.0 | Dev-only | ⚠️ | Non incluso nel build finale |
| [nome] | [ver] | AGPL-3.0 | Runtime | ❌ | DA SOSTITUIRE |
```

---

> **Disclaimer:** Questo documento ha finalità informativa e di pianificazione interna. Non costituisce consulenza legale, fiscale o professionale. Tutti gli adempimenti descritti devono essere verificati e implementati con il supporto di professionisti qualificati (commercialista, avvocato specializzato in diritto digitale/privacy). Le informazioni sono aggiornate a marzo 2026 e potrebbero essere soggette a variazioni normative.
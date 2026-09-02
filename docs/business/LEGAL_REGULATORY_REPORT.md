# LEGAL_REGULATORY_REPORT.md

**Progetto:** FitManager (operatore: AVGV Technologies)  
**Versione:** 1.4
**Stato:** Documento operativo di riferimento per pre-launch e POC  
**Documenti correlati:**
- `TUNNEL_ARCHITECTURE.md` (architettura di accesso e tunnel; ex `CRM_ACCESS_ARCHITECTURE.md` v2.0, consolidato 2026-06-14)
- `BUSINESS_PLAN.md` (modello di business, proiezioni, partnership; il richiamo «v1.0» è d'epoca —
  oggi il BP è v4.3 baseline superseded. Verifica di merito dei passaggi legali che vi si appoggiano
  demandata alla review legale del gate E2, `SPEC_EXIT_ALESSIO.md`)
- `docs/specs/SPEC_EXIT_ALESSIO.md` (uscita partner e offboarding, ratificata 2026-08-29)

---

## Avvertenza preliminare

Questo documento è **documentazione tecnico-operativa interna** destinata a guidare le scelte di compliance e a preparare le consulenze con professionisti abilitati (commercialista, avvocato, consulente privacy). **Non costituisce parere legale né consulenza fiscale**. Ogni adempimento elencato deve essere validato da un professionista prima dell'esecuzione, con particolare riguardo a:

- Apertura e gestione P.IVA (commercialista)
- Stesura definitiva di EULA, Termini di Servizio, Privacy Policy, eventuale DPA (avvocato)
- Registrazione marchi presso UIBM/EUIPO (consulente in proprietà intellettuale)
- Accordo di partnership con soggetti terzi (avvocato societario)
- Valutazione DPIA, se richiesta (DPO o consulente privacy)

---

## Indice

1. [Executive summary](#1-executive-summary)
2. [Modelli di business e implicazioni legali](#2-modelli-di-business-e-implicazioni-legali)
3. [Modello di distribuzione del software e implicazioni di compliance](#3-modello-di-distribuzione-del-software-e-implicazioni-di-compliance) **[nuovo in v1.2]**
4. [Setup fiscale: P.IVA, regime forfettario, obblighi strumentali](#4-setup-fiscale-piva-regime-forfettario-obblighi-strumentali)
5. [Documenti legali core: EULA, ToS, Privacy Policy, DPA](#5-documenti-legali-core-eula-tos-privacy-policy-dpa)
6. [GDPR: ruoli, basi giuridiche, dati sanitari, flussi](#6-gdpr-ruoli-basi-giuridiche-dati-sanitari-flussi) **[aggiornato in v1.2]**
7. [European Accessibility Act (EAA) e WCAG 2.1](#7-european-accessibility-act-eaa-e-wcag-21)
8. [Protezione IP: marchi, software, segreti commerciali](#8-protezione-ip-marchi-software-segreti-commerciali)
9. [Open source, licenze, SBOM](#9-open-source-licenze-sbom)
10. [PSD2, PCI-DSS e gestione pagamenti](#10-psd2-pci-dss-e-gestione-pagamenti)
11. [Anti-spam e marketing: art. 130 D.Lgs. 196/2003](#11-anti-spam-e-marketing-art-130-dlgs-1962003)
12. [B2B vs B2C: Codice del Consumo](#12-b2b-vs-b2c-codice-del-consumo)
13. [Hardware: requisiti per Phase 2](#13-hardware-requisiti-per-phase-2)
14. [Roadmap operativa](#14-roadmap-operativa)
15. [Costi stimati](#15-costi-stimati)
16. [Matrice rischi e mitigazioni](#16-matrice-rischi-e-mitigazioni)
17. [Riferimenti normativi](#17-riferimenti-normativi)
18. [Appendici](#18-appendici)

---

## 1. Executive summary

FitManager è un software gestionale per trainer e professionisti del fitness, distribuito come **applicazione desktop tramite PyInstaller** installata sul hardware del trainer. L'operatore è **AVGV Technologies**, ditta individuale italiana in regime forfettario, di proprietà di Giacomo Verardo, con residenza fiscale e burocratica esclusivamente in Italia.

Il **modello distribuito** (software locale, database SQLite per trainer, esposizione pubblica via tunnel reverse data-blind operato da AVGV) ha implicazioni profondamente favorevoli sulla compliance, riducendo significativamente gli obblighi GDPR di AVGV rispetto a un modello SaaS centralizzato:

- AVGV è **fornitore di software**, non Data Processor dei dati clinici trattati dai trainer
- I dati sanitari (anamnesi, Art. 9 GDPR) non transitano e non risiedono mai su infrastruttura AVGV
- Ogni trainer è **autonomo Titolare del trattamento** dei dati dei propri clienti finali

Gli adempimenti chiave per il pre-launch (POC 10 trainer) sono:

1. Apertura P.IVA AVGV Technologies in regime forfettario, ATECO 62.01.00
2. Attivazione PEC e SPID
3. Redazione EULA, Termini di Servizio, Privacy Policy AVGV
4. Implementazione checklist WCAG 2.1 AA conforme EAA (microimpresa: esenzione applicabile, ma rispetto sostanziale raccomandato)
5. Registrazione marchi "FitManager", "FitManager Studio+", "AVGV Technologies" presso UIBM in classi 9 e 42
6. Predisposizione SBOM e verifica licenze open source utilizzate
7. Documentazione tecnica della separazione AVGV ↔ dati clinici trainer (data-blind tunnel)

Il documento si articola in 18 sezioni che dettagliano ciascun adempimento, integrate con tabelle, checklist operative e appendici.

---

## 2. Modelli di business e implicazioni legali

FitManager è offerto secondo due modelli, entrambi a regime di **licenza d'uso software**, non di servizio:

| Modello | Descrizione | Implicazioni legali principali |
|---------|-------------|-------------------------------|
| **Software-only (POC)** | Licenza d'uso del software FitManager installato sul hardware del trainer | EULA, ToS, Privacy AVGV. Nessuna fornitura hardware. Nessun obbligo CE/RAEE. |
| **Software + Hardware (Phase 2)** | Appliance preconfigurata (Raspberry Pi 5) + software FitManager incluso | Aggiunge obblighi: marcatura CE, registrazione RAEE/AEE, garanzia legale del venditore, eventualmente direttiva RED se Wi-Fi integrato. Rinviato a Phase 2. |

**Conseguenze fiscali per il modello software-only (POC):**

- Cessione di licenza d'uso software → operazione qualificata come prestazione di servizi
- Fatturazione elettronica obbligatoria (tutti i contribuenti dal 2024, anche forfettari)
- IVA in regime forfettario: non addebitata, contribuente non detraibile
- Codice fiscale del cliente (P.IVA o CF) sempre richiesto per fatturazione

**Conseguenze fiscali per fatturazione a clienti esteri (rilevante per POC italiana ma da considerare):**

- Cliente UE B2B con VAT number valido → reverse charge (operazione non imponibile)
- Cliente UE B2C → IVA italiana (ma forfettari non addebitano)
- Cliente extra-UE → operazione fuori campo IVA

Il modello POC è B2B (trainer professionisti con P.IVA o liberi professionisti), quindi la maggior parte delle fatture sarà reverse charge intra-UE o fatturazione italiana standard.

---

## 3. Modello di distribuzione del software e implicazioni di compliance

**[Sezione introdotta in v1.2, derivata da `TUNNEL_ARCHITECTURE.md` — ex `CRM_ACCESS_ARCHITECTURE.md` v2.0]**

### 3.1 Architettura di distribuzione

FitManager NON è un SaaS multi-tenant. È un'applicazione desktop:

- Distribuita come binario PyInstaller scaricabile/consegnato al trainer
- Installata sul hardware del trainer (PC, mini-PC, Raspberry Pi)
- Con database SQLite **locale** per ogni istanza
- Esposta pubblicamente tramite **tunnel reverse data-blind** operato da AVGV (TLS end-to-end: il certificato risiede sul PC del trainer; AVGV instrada per SNI senza terminare TLS)
- Aggiornata tramite rilascio di nuovi installer da parte di AVGV

### 3.2 Conseguenze GDPR del modello distribuito

| Aspetto | Modello SaaS centralizzato (NON applicabile) | Modello FitManager distribuito (effettivo) |
|---------|----------------------------------------------|--------------------------------------------|
| Ruolo AVGV sui dati clinici | Responsabile del trattamento (Data Processor) | **Fornitore di software**, mai accesso ai dati |
| Ruolo trainer sui dati clienti | Titolare | Titolare (invariato) |
| DPA AVGV ↔ trainer per dati clienti | Necessaria | **Non necessaria** per dati clinici |
| Sub-processor AVGV per dati clienti | Da dichiarare (cloud, DB, backup, ecc.) | **Nessuno** per dati clinici |
| DPIA su trattamento dati clinici | Responsabilità AVGV come Processor | **Responsabilità trainer** come Titolare; AVGV fornisce documentazione tecnica |
| Data residency dati clinici | Server AVGV | Hardware del trainer (tipicamente Italia per POC) |
| Trasferimenti extra-UE da parte di AVGV | Da gestire (SCC, ecc.) | **Non avvengono** per dati clinici |
| Notifica violazioni dati clinici al Garante | Obbligo AVGV come Processor | **Obbligo trainer** come Titolare; AVGV notifica solo per propri dati (account, infra) |
| Diritti interessati (accesso, cancellazione, ecc.) | Gestiti da AVGV via trainer | **Gestiti dal trainer direttamente** sui propri sistemi |

### 3.3 Dati per cui AVGV è Titolare autonomo

AVGV resta Titolare di un trattamento autonomo, limitato a:

| Categoria di dati | Finalità | Base giuridica |
|-------------------|----------|----------------|
| Dati account trainer (email, nome, P.IVA, indirizzo fatturazione) | Erogazione del servizio software, fatturazione, comunicazioni di servizio | Esecuzione contratto (Art. 6.1.b GDPR) |
| Dati fatturazione | Obblighi fiscali italiani | Obbligo di legge (Art. 6.1.c GDPR) |
| Metadati tunnel (timestamp, instance_id, IP sorgente cliente finale, esito routing) | Sicurezza infrastruttura, audit, troubleshooting | Legittimo interesse (Art. 6.1.f GDPR) |
| Eventuale telemetria errori applicativi anonima | Miglioramento software | Legittimo interesse, con opt-out |
| Eventuali dati di supporto raccolti durante assistenza | Erogazione supporto | Esecuzione contratto |

**Note critiche:**
- I metadati tunnel **non includono contenuto applicativo**: il traffico passa cifrato e AVGV non lo decifra. Vedi `TUNNEL_ARCHITECTURE.md` §5 (principio P2) e `TUNNEL_SECURITY_BOUNDARY.md` §5 (P2 data-blind, dimostrato e2e).
- Eventuale telemetria deve essere progettata come **anonima per default** o con opt-in esplicito se contiene identificatori.
- I log infrastrutturali devono avere retention limitata e documentata (raccomandato 30–90 giorni, poi cancellazione o anonimizzazione irreversibile).

### 3.4 Obblighi documentali da derivare dal modello distribuito

- **EULA** deve esplicitare la separazione: AVGV fornisce software; il trainer è autonomo Titolare dei dati dei propri clienti
- **Privacy Policy AVGV** deve coprire solo i trattamenti di cui AVGV è Titolare (sezione 3.3), non i trattamenti che il trainer fa coi propri clienti
- **Documento tecnico di descrizione architetturale** (referenziabile in eventuali audit o DPIA del trainer) che attesti la proprietà data-blind del tunnel: `TUNNEL_ARCHITECTURE.md` (+ `TUNNEL_SECURITY_BOUNDARY.md` §5) può fungere da riferimento
- **Trainer onboarding kit** dovrebbe includere un memo informativo che ricordi al trainer i propri obblighi come Titolare (informativa ai clienti, raccolta consensi Art. 9, ecc.)

### 3.5 Rischio residuo da gestire

Il modello distribuito è strutturalmente favorevole MA introduce un rischio specifico: se in qualunque punto futuro AVGV dovesse acquisire la possibilità tecnica di accedere ai dati clinici (es. funzione "cloud backup", "supporto remoto con accesso al DB", "telemetria che include dati clinici"), il ruolo GDPR di AVGV **cambia automaticamente** e si attivano obblighi pesanti (DPA, sub-processor, ecc.). Ogni nuova feature deve passare un **privacy review** che verifichi questa invariante.

---

## 4. Setup fiscale: P.IVA, regime forfettario, obblighi strumentali

### 4.1 Regime forfettario: parametri chiave

Il regime forfettario è la scelta consigliata per la fase pre-launch e POC di AVGV Technologies (validare con commercialista).

| Parametro | Valore |
|-----------|--------|
| Soglia massima ricavi | €85.000 annui |
| Aliquota imposta sostitutiva | 5% per i primi 5 anni di attività (startup), poi 15% |
| Coefficiente di redditività ATECO 62.01.00 | 67% (imponibile = ricavi × 67%) |
| Esempio: ricavi €50.000 → imponibile €33.500 → imposta €1.675 (primi 5 anni) |
| IVA | Non applicata in fattura |
| Ritenuta d'acconto | Non subita (esonero) |
| Contributi INPS | Gestione Separata (~26,07% del reddito imponibile) |
| Regola concentrazione clienti | Se >50% dei ricavi proviene da ex-datore di lavoro o soggetto a lui collegato, regime non applicabile |
| Verifica annuale | Soglia €85.000 + altre cause di esclusione |

**Per AVGV Technologies specificamente:** Giacomo non ha ex-datore di lavoro tra i clienti FitManager (i trainer sono terzi indipendenti), quindi la regola del 50% non è critica. Va comunque monitorata se in futuro un cliente trainer di grandi dimensioni dovesse rappresentare oltre metà del fatturato.

### 4.2 Codici ATECO

Dalla classificazione ATECO 2025 (entrata in vigore 1° aprile 2025):

| Codice | Descrizione | Ruolo per AVGV |
|--------|-------------|----------------|
| **62.01.00** | Produzione di software non connesso all'edizione | **Primario** |
| 62.02.00 | Consulenza nel settore delle tecnologie dell'informatica | Secondario (servizi di setup/supporto) |
| 63.11.11 | Elaborazione elettronica di dati | Secondario (se eventuali servizi di hosting/data processing futuri) |
| 63.11.19 | Altre attività dei servizi connessi alle tecnologie dell'informatica | Secondario (eventuale supporto tecnico avanzato) |

L'iscrizione con multiple ATECO è consentita. ATECO primario determina il coefficiente di redditività forfettario.

### 4.3 Obblighi strumentali

| Obbligo | Status | Note |
|---------|--------|------|
| **P.IVA** | Da aprire | Comunica Unica (gratuita) tramite ComUnica o commercialista |
| **PEC (Posta Elettronica Certificata)** | Da attivare | Obbligo per tutte le imprese incluse ditte individuali. Costo: ~5–25€/anno. Provider: Aruba, Poste, Legalmail, ecc. |
| **SPID** | Da recuperare/sostituire | Necessario per accessi Agenzia Entrate, INPS, SUAP. Video-identificazione possibile dall'estero. |
| **Firma digitale** | Raccomandata | Necessaria per atti registrabili (contratti con timestamp legale), comunica unica avanzata |
| **Iscrizione Camera di Commercio** | Verifica | Per attività di "produzione software" l'iscrizione è generalmente richiesta. Diritto camerale annuale (~88€ per imprese individuali). |
| **INAIL** | Verifica | Per ditta individuale senza dipendenti, generalmente non obbligatoria. Confermare con consulente. |
| **Indirizzo PEC su Registro Imprese (INI-PEC)** | Da fare | Comunicazione obbligatoria del proprio indirizzo PEC al Registro Imprese |
| **Fatturazione elettronica** | Obbligatoria | Anche per forfettari dal 2024 (regime esteso). Tramite software (Aruba FE, Fatture in Cloud, ecc.) o portale Agenzia Entrate. |
| **Conservazione sostitutiva fatture** | Obbligatoria | 10 anni. Generalmente inclusa nei servizi di fatturazione elettronica. |

### 4.4 Conversione a SRL: orizzonte Anno 3

Il business plan prevede conversione a SRL nell'Anno 3, indicativamente quando:

- Ricavi si avvicinano alla soglia €85.000
- Si vogliono assumere collaboratori
- Si vuole limitare la responsabilità patrimoniale
- Si vogliono accedere a strumenti di finanziamento o partnership societarie

Operazione consulenziale complessa (atto notarile, capitale sociale, regime ordinario, gestione magazzino e ratei, ecc.). Da pianificare con 6 mesi di anticipo con commercialista e notaio.

### 4.5 Trasferta lavorativa all'estero (nota informativa)

Il titolare di AVGV svolge attualmente parte dell'attività in trasferta a Marsiglia, **senza** che ciò comporti residenza fiscale francese, iscrizione AIRE, o legami burocratici stabili al di fuori dell'Italia. Trasferte lavorative non continuative non spostano automaticamente la residenza fiscale, che resta determinata dai criteri sostanziali italiani (iscrizione anagrafica, domicilio, centro degli interessi vitali, permanenza per la maggior parte del periodo d'imposta).

Per la fattispecie attuale:

- Residenza fiscale: **Italia**
- Regime forfettario italiano: **pienamente applicabile**, senza complicazioni transfrontaliere
- Convenzioni contro doppie imposizioni: non rilevanti finché non c'è doppia residenza o stabile organizzazione all'estero

**Punti da monitorare nel tempo** (non critici allo stato attuale, ma da rivalutare se la situazione cambia):

- Permanenza in Francia o altro Paese estero per oltre 183 giorni in un anno solare
- Apertura di sedi operative stabili all'estero
- Spostamento del centro di interessi personali ed economici all'estero
- Cambio di iscrizione anagrafica

Se in futuro uno o più di questi elementi cambiasse, riaprire la valutazione fiscale con commercialista esperto in fiscalità internazionale **prima** del verificarsi della condizione.

---

## 5. Documenti legali core: EULA, ToS, Privacy Policy, DPA

### 5.1 Quadro generale

Per il lancio della POC, AVGV deve disporre di:

| Documento | Status | Soggetti | Note |
|-----------|--------|----------|------|
| **EULA** (End User License Agreement) | Da redigere | AVGV ↔ trainer | Disciplina la licenza d'uso del software |
| **Termini di Servizio (ToS)** | Da redigere | AVGV ↔ trainer | Disciplina il servizio di tunnel/distribuzione/supporto |
| **Privacy Policy AVGV** | Da redigere | AVGV verso trainer + eventuali visitatori sito | Copre solo trattamenti di cui AVGV è Titolare |
| **DPA AVGV ↔ trainer** | **Verificare necessità** | AVGV ↔ trainer | **In modello distribuito v1.2 → NON necessaria per dati clinici**. Necessaria solo se AVGV tratta in qualche modo dati personali per conto del trainer (es. log con identificatori clienti finali). |
| **Informativa/Privacy Policy del trainer ai clienti finali** | Trainer la redige | Trainer ↔ clienti finali | AVGV può fornire template ma è responsabilità del trainer |
| **Informativa cookie/tracker (se sito promozionale)** | Da redigere | AVGV ↔ visitatori sito | Se sito raccoglie cookie analytics o marketing |

### 5.2 EULA – contenuti essenziali

Clausole minime da includere (validare con avvocato):

1. **Identificazione parti**: AVGV Technologies (denominazione, P.IVA, sede, PEC) e licenziatario (trainer)
2. **Oggetto della licenza**: licenza d'uso non esclusiva, non trasferibile, del software FitManager
3. **Durata**: a tempo indeterminato con clausola di risoluzione, oppure annuale rinnovabile
4. **Diritti e limitazioni**:
   - Diritto del licenziatario a installare e usare il software sul proprio hardware
   - Divieto di reverse engineering, decompilazione, redistribuzione, sublicenza
   - Divieto di rivendita o concessione in uso a terzi
5. **Proprietà intellettuale**: chiarire che il software, i marchi e tutto il codice restano di proprietà esclusiva di AVGV
6. **Aggiornamenti**: AVGV può rilasciare aggiornamenti; licenziatario è responsabile dell'installazione
7. **Separazione dati**: **clausola critica in modello distribuito** — il software gira sul hardware del trainer; i dati trattati con il software restano sul hardware del trainer; AVGV non ha accesso a tali dati; il trainer è autonomo Titolare del trattamento
8. **Servizio tunnel pubblico**: AVGV fornisce un servizio accessorio di tunnel reverse per esporre pubblicamente le funzioni di accesso cliente finale; il servizio è data-blind (riferimento a `TUNNEL_ARCHITECTURE.md`)
9. **Garanzia e responsabilità**: software fornito "as is" salvo le tutele minime di legge per i consumatori (se applicabili); limitazione di responsabilità nei limiti consentiti dalla legge
10. **Sospensione e cessazione**: cause di sospensione (mancato pagamento, violazione termini), preavviso, conseguenze sui dati locali (restano del trainer)
11. **Legge applicabile e foro competente**: legge italiana, foro di competenza del trainer (se B2C) o di AVGV (se B2B, salvo diversa pattuizione)
12. **Modifiche dell'EULA**: meccanismo di notifica e diritto di recesso del trainer in caso di modifiche sostanziali

### 5.3 Termini di Servizio – contenuti essenziali

Coprono il **servizio di distribuzione/tunnel/supporto** offerto da AVGV (distinto dalla mera licenza software):

1. Descrizione del servizio (distribuzione installer, tunnel pubblico, supporto)
2. SLA: livello di disponibilità del tunnel edge (target indicativo 99,5% per POC), modalità di assistenza, tempi di risposta
3. Manutenzione programmata: come e quando viene comunicata
4. Limitazioni: il servizio dipende anche dalla connettività del trainer e dal funzionamento del suo hardware
5. Tariffazione e modalità di pagamento
6. Diritto di recesso
7. Sospensione e cessazione del servizio
8. Trattamento dei dati al termine del servizio (i dati restano del trainer, AVGV fornisce eventuale supporto export se previsto)

### 5.4 Privacy Policy AVGV – contenuti essenziali

Copre solo i trattamenti di cui AVGV è Titolare (sezione 3.3 di questo documento):

1. **Titolare del trattamento**: AVGV Technologies, contatti, eventuale DPO se nominato
2. **Categorie di dati trattati**: account, fatturazione, metadati tunnel, supporto, telemetria opzionale
3. **Finalità e basi giuridiche**: una tabella esplicita per ogni categoria
4. **Destinatari**: provider servizi (hosting VPS edge, provider PEC, provider fatturazione elettronica, eventuali professionisti per consulenza)
5. **Trasferimenti extra-UE**: solo se rilevanti (es. se VPS è in altra giurisdizione); per POC con VPS UE → nessun trasferimento
6. **Periodo di conservazione**: per ogni categoria
7. **Diritti dell'interessato**: accesso, rettifica, cancellazione, limitazione, portabilità, opposizione; modalità di esercizio
8. **Reclamo al Garante**: indirizzo Autorità Garante per la protezione dei dati personali
9. **Modifiche della policy**: meccanismo di aggiornamento

### 5.5 DPA – verifica necessità nel modello distribuito

**Conclusione operativa v1.2:** la DPA AVGV ↔ trainer **non è obbligatoria** per i dati clinici dei clienti finali del trainer, perché AVGV non li tratta. Tuttavia può essere opportuno predisporre comunque una **DPA minima** che copra i pochi casi in cui AVGV tratta dati personali per conto del trainer (es. metadati tunnel che possono includere IP del cliente finale).

Decisione raccomandata: avvocato valuti se il trattamento di metadati tunnel configura un titolarità autonoma di AVGV (per legittimo interesse di sicurezza infrastruttura) oppure una contitolarità/processing. In base al risultato:
- Titolarità autonoma → solo informativa, nessuna DPA
- Contitolarità → accordo Art. 26 GDPR
- Processing → DPA Art. 28 GDPR

Posizione tecnicamente difendibile: **titolarità autonoma per legittimo interesse di sicurezza**, perché i metadati sono raccolti per finalità proprie di AVGV (operare l'infrastruttura tunnel) e non per conto del trainer.

---

## 6. GDPR: ruoli, basi giuridiche, dati sanitari, flussi

**[Sezione significativamente aggiornata in v1.2 per riflettere il modello distribuito]**

### 6.1 Schema dei ruoli (modello distribuito FitManager)

```
┌──────────────────────────────────────────────────────────────────┐
│                       CLIENTE FINALE                              │
│           (Interessato — soggetto dei dati personali)             │
│           Anamnesi, feedback schede = dati Art. 9                 │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 │ Tratta i dati direttamente
                 │ tramite software installato su hardware proprio
                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                          TRAINER                                  │
│              TITOLARE del trattamento dei propri clienti          │
│  Decide finalità e mezzi, raccoglie consensi, risponde di breach  │
│  Hardware proprio, SQLite locale, dati Art. 9 sotto suo controllo │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 │ Utilizza il software fornito da
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                    AVGV TECHNOLOGIES                              │
│                  FORNITORE DI SOFTWARE                            │
│             (NON è Titolare né Processor dei dati clinici)        │
│                                                                   │
│  È Titolare autonomo solo di:                                     │
│   - account trainer, fatturazione, supporto                       │
│   - metadati tunnel (data-blind, no contenuto)                    │
└──────────────────────────────────────────────────────────────────┘
```

### 6.2 Basi giuridiche per ogni trattamento

| Trattamento | Titolare | Base giuridica primaria | Base giuridica per dati Art. 9 |
|-------------|----------|-------------------------|-------------------------------|
| Anamnesi cliente finale | Trainer | Esecuzione contratto / consenso esplicito | Consenso esplicito (Art. 9.2.a) o finalità di assistenza sanitaria/sportiva (Art. 9.2.h) — da valutare con consulente |
| Feedback schede allenamento | Trainer | Esecuzione contratto | Idem se contiene dati sulla salute |
| Account trainer presso AVGV | AVGV | Esecuzione contratto (Art. 6.1.b) | — |
| Fatturazione trainer | AVGV | Obbligo di legge (Art. 6.1.c) | — |
| Metadati tunnel | AVGV | Legittimo interesse (Art. 6.1.f) | — (no dati sanitari) |
| Marketing AVGV verso trainer | AVGV | Consenso (Art. 6.1.a) o legittimo interesse limitato | — |

### 6.3 Dati di categoria particolare (Art. 9)

L'anamnesi del cliente finale del trainer contiene **quasi certamente** dati sulla salute (Art. 9 GDPR): patologie, infortuni pregressi, condizioni fisiche, terapie in corso.

**Obblighi del trainer come Titolare di tali dati:**

1. **Base giuridica esplicita**: consenso esplicito Art. 9.2.a (caso tipico) oppure altra base ex Art. 9.2 (es. finalità di medicina preventiva o assistenza sanitaria se il trainer è iscritto ad albo competente — kinesiologo, fisioterapista, ecc.)
2. **Informativa rafforzata**: spiegare con chiarezza quali dati sono raccolti, perché, per quanto tempo, chi vi accede
3. **Misure di sicurezza adeguate**: art. 32 GDPR; per dati Art. 9 lo standard è più alto
4. **Eventuale DPIA**: se il trattamento è su larga scala, sistematico o presenta rischi elevati
5. **Notifica violazioni**: al Garante entro 72h e agli interessati se rischio elevato
6. **Diritti rafforzati degli interessati**: accesso, rettifica, cancellazione, limitazione, portabilità, opposizione

**Cosa AVGV deve fornire al trainer:**

- Documentazione tecnica delle misure di sicurezza implementate nel software (TLS, hash password, audit log locali)
- Documentazione del modello data-blind del tunnel (per attestare che i dati non escono dal hardware del trainer)
- Template di informativa privacy che il trainer può adattare per i propri clienti
- Funzionalità di esercizio diritti: export dati cliente, cancellazione, log degli accessi

### 6.4 Flusso dati e punti di trattamento

```
┌─────────────┐    ┌─────────────────────────────────────────────┐
│Cliente final│ ─→ │  Browser: compila anamnesi via link tunnel  │
└─────────────┘    └─────────────────────────────────────────────┘
                                        │
                       HTTPS cifrato e2e (TLS terminato sul PC)
                                        │
                                        ▼
                   ┌─────────────────────────────────────────┐
                   │  VPS EDGE AVGV: routing SNI, no decifr. │
                   │  Logga: timestamp, IP, instance_id, OK  │
                   │  NON logga: contenuto anamnesi          │
                   └─────────────────────────────────────────┘
                                        │
                                        ▼
                  ┌──────────────────────────────────────────┐
                  │       PC TRAINER (suo hardware)           │
                  │  - TLS termina qui                        │
                  │  - FitManager riceve dati                 │
                  │  - SCRIVE in SQLite locale                │
                  │  - Logga accesso in audit log locale      │
                  │  - Mostra trainer la pratica aggiornata   │
                  └──────────────────────────────────────────┘
```

**Punti di trattamento (e relativi Titolari):**

1. Cliente finale digita dati nel browser → Titolare: cliente finale stesso, per autodeterminazione
2. Trasporto via tunnel cifrato → AVGV opera l'infrastruttura, ma è data-blind: nessun trattamento del contenuto
3. Ricezione e archiviazione su PC del trainer → Titolare: trainer

### 6.5 Diritti degli interessati: esercizio

Quando un cliente finale del trainer esercita un diritto GDPR:

- **Lo esercita verso il trainer**, non verso AVGV
- Il trainer risponde direttamente: estrae dati dal proprio SQLite, fornisce informazioni, cancella, rettifica
- AVGV può fornire al trainer **strumenti software** per facilitare l'esercizio (export, cancellazione assistita)
- Se il cliente finale contatta AVGV per errore, AVGV indica il riferimento al proprio trainer (Titolare)

---

## 7. European Accessibility Act (EAA) e WCAG 2.1

### 7.1 Quadro normativo

L'**European Accessibility Act** (Direttiva UE 2019/882, recepita in Italia con D.Lgs. 27 maggio 2022 n. 82, modificato dal D.Lgs. 22 settembre 2023 n. 137) si applica dal **28 giugno 2025** a una serie di prodotti e servizi, inclusi i **servizi di commercio elettronico** rivolti a consumatori.

### 7.2 Applicabilità a FitManager

FitManager è un software gestionale **B2B** (cliente = trainer professionista). Il cliente finale del trainer è un consumatore, ma **non è cliente diretto di AVGV**: usa il software del trainer.

| Aspetto | Soggetto a EAA? | Note |
|---------|-----------------|------|
| Software FitManager venduto a trainer (B2B) | Marginalmente | EAA si applica ai servizi diretti a consumatori |
| Pagina/link di compilazione anamnesi per cliente finale | **Sì, sostanzialmente** | È un servizio digitale fruito da un consumatore (cliente finale), anche se intermediato dal trainer |
| Sito istituzionale AVGV (se ha funzione di e-commerce verso consumatori) | Solo se vende a consumatori | Per POC B2B → marginale |

### 7.3 Esenzione microimpresa

L'EAA prevede esenzione per **microimprese** (meno di 10 dipendenti e fatturato/bilancio < €2M) limitatamente ai servizi. Per AVGV ditta individuale in POC → **microimpresa**.

L'esenzione **non riguarda i prodotti** (rilevante solo se Phase 2 includerà appliance hardware → da rivalutare). Per la fase software-only POC, AVGV è esentata dagli obblighi formali EAA sui servizi.

**Tuttavia:** rispettare sostanzialmente WCAG 2.1 livello AA è raccomandato anche in esenzione, perché:
- L'esenzione cessa al superamento delle soglie microimpresa (probabile nei prossimi 2–3 anni)
- L'accessibilità è un valore d'uso reale per i clienti finali
- Adeguarsi ex post è molto più costoso che progettare accessibile dall'inizio

### 7.4 Checklist WCAG 2.1 AA – livello sostanziale per POC

Da implementare sulle pagine pubbliche di anamnesi e feedback (riferimento: `link.fitmanagerstudio.com/l/:token`):

- [ ] **Testo alternativo per immagini** (`alt` per ogni `<img>`)
- [ ] **Struttura semantica HTML**: `<header>`, `<main>`, `<nav>`, `<button>` (non `<div onclick>`)
- [ ] **Gerarchia heading corretta**: H1 unico, H2/H3 in ordine logico
- [ ] **Etichette di form esplicite**: ogni `<input>` ha `<label>` collegata
- [ ] **Contrasto colori**: rapporto minimo 4.5:1 per testo normale, 3:1 per testo grande
- [ ] **Navigazione completa da tastiera**: tutti i controlli accessibili senza mouse
- [ ] **Focus visibile**: outline o equivalente su tutti gli elementi focusabili
- [ ] **Messaggi di errore chiari**: descrittivi, associati al campo
- [ ] **Lingua dichiarata**: `<html lang="it">`
- [ ] **Responsive**: usabile su mobile, tablet, desktop
- [ ] **Tempi sufficienti**: nessun timeout breve forzato
- [ ] **No autoplay multimediale**
- [ ] **Modulo di feedback per problemi di accessibilità**: link visibile, contatto

### 7.5 Dichiarazione di accessibilità

Se l'esenzione microimpresa decade, AVGV dovrà pubblicare una **dichiarazione di accessibilità** secondo schema AgID. Per POC: documentare lo status sostanziale anche se non formalmente richiesta.

---

## 8. Protezione IP: marchi, software, segreti commerciali

### 8.1 Marchi da registrare

| Denominazione | Tipo | Classi Nizza | Ente | Costo indicativo |
|---------------|------|--------------|------|------------------|
| **FitManager** | Verbale + eventuale figurativo | 9 (software), 42 (servizi software/SaaS) | UIBM (Italia) | €101 (1 classe) + €34 per ogni classe aggiuntiva (tassa governativa); + onorari consulente ~€400–800 |
| **FitManager Studio+** | Verbale | 9, 42 | UIBM | Idem |
| **AVGV Technologies** | Verbale + logo | 9, 42, eventualmente 35 (consulenza) | UIBM | Idem |

**Estensione a marchio UE (EUIPO):** dato che l'orizzonte commerciale di FitManager è potenzialmente internazionale (mercato EU del fitness B2B), valutare il deposito direttamente come **marchio UE** (€850 una classe + €50 seconda + €150 dalla terza). Copre tutti gli stati membri UE con un unico deposito. Probabilmente l'opzione più sensata strategicamente.

### 8.2 Ricerca di anteriorità

**Obbligatorio prima del deposito**: verificare che i nomi non siano già registrati o usati. Strumenti:

- **TMview** (https://www.tmdn.org/tmview): ricerca cross-database UE/internazionale
- **UIBM**: database italiano
- **EUIPO eSearch**: database UE
- Ricerca generica web e domini per verificare usi di fatto

Esiti possibili:
- Nessun conflitto → procedere
- Marchio simile in classe diversa → procedere con attenzione
- Marchio identico/simile in stessa classe → ridenominare prima di depositare

### 8.3 Protezione del software

Il software è automaticamente protetto da **diritto d'autore** dal momento della creazione (Legge 633/1941, art. 1 e 2 n. 8). Nessuna registrazione obbligatoria. Tuttavia:

- **Timestamping del codice sorgente via PEC**: invia uno snapshot a se stesso via PEC → prova di esistenza datata
- **Deposito SIAE software**: facoltativo, costo ~€129; fornisce data certa
- **Repository privato con commit history**: prova tecnica di paternità ed evoluzione
- **Copyright notice nel codice e nell'interfaccia**: `© 2026 AVGV Technologies. All rights reserved.`

### 8.4 Segreti commerciali

Il codice sorgente, le query SQL specifiche, i prompt agli AI, le metriche di adesione/volume e i metodi di calcolo possono essere protetti come **segreto industriale** (D.Lgs. 63/2018, recepimento Direttiva UE 2016/943). Requisiti:

1. Informazione non generalmente nota
2. Valore commerciale dal suo essere segreta
3. Misure ragionevoli per mantenerne la segretezza (NDA, controllo accessi, classificazione interna)

Il founder attesta che l'NDA con Alessio Crociani è stato firmato. La copia elettronica v7 esaminata
il 2026-08-29 è però un template non sottoscritto: prima di qualunque notifica o revoca va recuperata
e verificata la copia realmente eseguita, incluse data, firme e approvazioni specifiche. Il testo v7
prevede cinque anni di riservatezza da ciascuna divulgazione, tutela dei segreti industriali finché
restano segreti e sopravvivenza dopo la cessazione; non supporta quindi l'assunzione di una scadenza
generale a luglio. Stato operativo e gate: `docs/specs/SPEC_EXIT_ALESSIO.md`.

### 8.5 IP nel rapporto con Alessio Crociani

Riferimento al `BUSINESS_PLAN.md` (richiamo d'epoca «v1.0», oggi v4.3 superseded): la titolarità del
marchio FitManager e del codice sorgente è
**esclusiva di AVGV/Giacomo**. Il rapporto ipotizzato con Alessio era B2B tra entità distinte e non
co-sviluppo IP. Al 2026-08-29 nessun Partnership Agreement eseguito è censito nel repository; le
proposte economiche di marzo sono superseded e non governano l'exit.

L'offboarding deve preservare:

- nessun co-ownership IP implicito;
- verifica della disciplina dei contributi eventualmente prodotti, senza assumere che ne esistano;
- sopravvivenza dell'NDA secondo la copia eseguita;
- distinzione tra cessazione della collaborazione, licenza Software, eventuale export dati e
  riservatezza;
- comunicazione formale e disattivazioni solo nei gate E1–E3 di `SPEC_EXIT_ALESSIO.md`.

---

## 9. Open source, licenze, SBOM

### 9.1 Rischi licenze open source

L'uso di librerie open source nel codice FitManager comporta obblighi di licenza che variano per natura:

| Famiglia licenze | Esempi | Rischio per FitManager | Compatibilità |
|------------------|--------|------------------------|---------------|
| **Permissive** | MIT, BSD, Apache 2.0, ISC | Basso | Sì, generalmente sicure |
| **Weak copyleft** | LGPL, MPL 2.0 | Medio | Sì se usate come libreria dinamicamente; complicato se static linking |
| **Strong copyleft** | GPL v2/v3 | Alto | Distribuzione del prodotto richiede rilascio sorgente; **rischio** se incluso nel binario PyInstaller |
| **Network copyleft** | AGPL v3 | Massimo per SaaS, **basso per software distribuito** | In modello SaaS forzerebbe l'apertura; in modello distribuito (PyInstaller) si tratta come GPL |
| **Proprietarie/non-OSI** | "Source-available", "BSL", licenze custom | Variabile | Da leggere caso per caso |

**Punto chiave del modello distribuito FitManager:** poiché il software è **distribuito** (PyInstaller installato dal trainer), si attivano gli obblighi tipici delle licenze copyleft di distribuzione. AGPL e GPL diventano problematiche se incluse nel binario, perché la distribuzione obbliga al rilascio del sorgente di tutto il "work" derivato.

### 9.2 Audit licenze: strumenti

| Tool | Linguaggio target | Note |
|------|-------------------|------|
| **pip-licenses** | Python | Veloce, genera report tabellare |
| **pipdeptree** | Python | Albero dipendenze |
| **license-checker** | Node.js | Se eventuali componenti JS |
| **FOSSology** | Multi | Audit approfondito, self-hosted |
| **Scancode-toolkit** | Multi | Scansione codice sorgente per match |
| **Software Composition Analysis (SCA)**: Snyk, Sonatype, Mend | Multi (commerciali) | Anche security oltre licensing |

**Raccomandazione per POC**: eseguire `pip-licenses` su tutto l'environment Python, esportare in CSV, revisionare manualmente ogni licenza non MIT/BSD/Apache/ISC.

### 9.3 SBOM (Software Bill of Materials)

Strumento sempre più richiesto (e in alcuni contesti pubblici obbligatorio per appalti). Standard:

- **SPDX** (Linux Foundation)
- **CycloneDX** (OWASP)

Per Python: generabile con `cyclonedx-py` o `pip-audit --format=cyclonedx`.

**Template SBOM minimo** in appendice 18.4.

### 9.4 Compliance operativa per ogni release

Checklist da eseguire prima di ogni rilascio nuovo PyInstaller:

- [ ] Esecuzione `pip-licenses` e revisione output
- [ ] Generazione SBOM (CycloneDX)
- [ ] Audit vulnerabilità (`pip-audit` o `safety`)
- [ ] Verifica `requirements.txt` pinning delle versioni
- [ ] Inclusione `LICENSES.txt` o `THIRD_PARTY_NOTICES.txt` nel bundle distribuito al trainer (obbligo legale per molte licenze permissive)
- [ ] Aggiornamento documento di licensing nel repo

---

## 10. PSD2, PCI-DSS e gestione pagamenti

### 10.1 Modello di incasso AVGV

Per la POC, AVGV incassa dai trainer (B2B). Modalità tipiche:

| Modalità | Compliance | Note |
|----------|------------|------|
| **Bonifico bancario** | Nessun obbligo specifico oltre fattura elettronica | Semplice, gratuito, lento |
| **PayPal Business** | PayPal gestisce PSD2 e PCI-DSS | Commissioni 2,49–3,4% |
| **Stripe** | Stripe gestisce PSD2 e PCI-DSS | Commissioni ~1,4% UE + €0,25 |
| **Carta di credito direttamente** | **PCI-DSS** se AVGV processa o vede numeri carta | **Da evitare** in proprio |

**Raccomandazione**: per POC, bonifico + opzionalmente PayPal/Stripe. **Non gestire mai direttamente i dati carta**: usare sempre intermediari certificati (Stripe, PayPal, Adyen, ecc.) che si occupano di PCI-DSS.

### 10.2 PSD2: Strong Customer Authentication

PSD2 impone SCA per pagamenti online. Se AVGV usa Stripe/PayPal, l'SCA è gestita dal provider. Se l'incasso è in bonifico, non si applica.

### 10.3 Pagamenti trainer → cliente finale (Phase 2)

In Phase 2, FitManager potrebbe abilitare il trainer a ricevere pagamenti dai propri clienti finali (es. abbonamenti palestra). Questo cambia il quadro:

- AVGV diventa **piattaforma di pagamento intermediaria**? → potenziale obbligo di autorizzazione come istituto di pagamento (PSP)
- Alternativa: integrare provider esterno (Stripe Connect, PayPal Marketplace) → onere PSD2/PCI-DSS resta al provider

**Per POC non è in scope**. Da analizzare in dettaglio prima di Phase 2.

---

## 11. Anti-spam e marketing: art. 130 D.Lgs. 196/2003

### 11.1 Quadro

L'**art. 130 del Codice Privacy** (D.Lgs. 196/2003 come modificato dal D.Lgs. 101/2018) disciplina le comunicazioni commerciali non sollecitate via email, SMS, chiamate automatizzate.

### 11.2 Tipi di comunicazione e consensi richiesti

| Tipo di comunicazione | Consenso necessario | Base legale |
|----------------------|---------------------|-------------|
| Comunicazione di servizio (es. "il tuo account è stato creato") | No | Esecuzione contratto |
| Newsletter informativa con contenuti commerciali | **Sì, opt-in esplicito** | Consenso |
| Email a propri clienti esistenti su prodotti simili | Opt-out sufficiente (soft opt-in) | Art. 130 c. 4 |
| Email a leads / lista acquistata | **Sì, opt-in esplicito + verifica base legale del fornitore** | Consenso |
| Telemarketing voice (chiamata umana) | Iscrizione Registro Pubblico Opposizioni + consenso | Consenso + RPO |
| SMS marketing | **Sì, opt-in esplicito** | Consenso |

### 11.3 Operatività per FitManager

- Lista email trainer POC: comunicazioni di servizio sì, marketing solo con opt-in esplicito
- Form di contatto sito AVGV: separare consenso a essere contattato da consenso a ricevere newsletter
- Doppia conferma (double opt-in) raccomandata per newsletter
- Documentare il consenso (timestamp, IP, testo dell'informativa al momento del consenso)
- Sempre meccanismo di unsubscribe in ogni email marketing

### 11.4 Sanzioni

Le sanzioni per violazioni art. 130 possono arrivare a €20.000 per le ipotesi base, fino al massimo GDPR (€20M o 4% fatturato) per spam massivo.

---

## 12. B2B vs B2C: Codice del Consumo

### 12.1 Distinzione

| Aspetto | B2B (trainer con P.IVA) | B2C (consumatore) |
|---------|------------------------|--------------------|
| Codice del Consumo (D.Lgs. 206/2005) | Non si applica salvo casi limite | Si applica integralmente |
| Diritto di recesso 14gg | Non obbligatorio | Obbligatorio per contratti a distanza |
| Garanzia legale conformità | Solo se applicabile a software (limitata) | 2 anni |
| Clausole vessatorie | Negoziabili | Vietate o richiede approvazione specifica |
| Foro competente | Liberamente pattuibile | Foro del consumatore (inderogabile) |
| Trasparenza prezzi | Buona prassi | Obblighi precisi |
| Pre-contratto: informativa | Buona prassi | Obblighi precisi (art. 49 Codice Consumo) |

### 12.2 Posizionamento POC

I primi 10 clienti FitManager sono trainer professionisti con P.IVA o liberi professionisti (kinesiologi, personal trainer professionali, palestre): rapporto **B2B**. Codice del Consumo non si applica.

Attenzione: se in futuro AVGV decidesse di offrire FitManager a privati amatoriali (es. trainer hobbista senza P.IVA, atleti che gestiscono il proprio allenamento), il rapporto diventa B2C e si applicano tutti gli obblighi consumeristici.

---

## 13. Hardware: requisiti per Phase 2

**Rinviato a Phase 2.** Per il modello "Software + Hardware" (appliance Raspberry Pi 5 preconfigurata), si attiveranno:

- **Marcatura CE**: dichiarazione di conformità per direttive applicabili (EMC, Bassa Tensione, RED se Wi-Fi)
- **Registro RAEE/AEE**: iscrizione produttore presso il Centro di Coordinamento RAEE
- **Etichettatura RAEE**: simbolo del bidone barrato
- **Garanzia legale**: 2 anni per consumatori, contrattuale per B2B
- **Manuale d'uso**: in italiano per il mercato italiano
- **Test di conformità**: laboratorio accreditato (costo: €1.500–5.000 per round)

Da affrontare in fase di pianificazione Phase 2 con consulente prodotto/CE.

---

## 14. Roadmap operativa

### Fase 1 — Setup amministrativo (settimane 1–3)

- [ ] Consulto commercialista per setup forfettario e scelta software fatturazione
- [ ] Recupero/sostituzione SPID
- [ ] Attivazione PEC
- [ ] Apertura P.IVA AVGV Technologies + ATECO + Camera di Commercio + INI-PEC
- [ ] Setup fatturazione elettronica
- [ ] Apertura conto bancario business (anche conto online tipo Qonto/Revolut Business)

### Fase 2 — Setup legale (settimane 2–4, parallelo)

- [ ] Brief avvocato per EULA, ToS, Privacy Policy AVGV
- [ ] Privacy review modello distribuito (validare conclusione "AVGV non Data Processor")
- [ ] Ricerca anteriorità marchi (TMview + UIBM/EUIPO)
- [ ] Decisione marchio nazionale UIBM vs UE EUIPO → deposito
- [ ] Timestamping codice sorgente via PEC
- [ ] Recupero copia NDA Alessio eseguita + review legale exit/licenza/offboarding

### Fase 3 — Setup tecnico-compliance (settimane 3–6)

- [ ] Implementazione checklist WCAG 2.1 AA sulla pagina pubblica cliente finale
- [ ] Esecuzione audit licenze open source (`pip-licenses`)
- [ ] Generazione SBOM (CycloneDX)
- [ ] Audit vulnerabilità (`pip-audit`)
- [ ] Implementazione architettura `TUNNEL_ARCHITECTURE.md` (tunnel data-blind, autenticazione, token cliente, audit log)
- [ ] Predisposizione template informativa privacy per trainer
- [ ] Documento tecnico data-blind tunnel per fascicolo compliance

### Fase 4 — Pre-launch (settimane 6–8)

- [ ] Onboarding kit trainer: EULA, ToS, Privacy AVGV, template informativa trainer→cliente, guida configurazione
- [ ] Pricing finalizzato
- [ ] Sito istituzionale AVGV con privacy policy e cookie banner se applicabile
- [ ] Esecuzione checklist pre-launch (appendice 18.3)
- [ ] Soft launch primi 3 trainer pilota → feedback
- [ ] Lancio completo 10 trainer POC

---

## 15. Costi stimati

| Voce | Una tantum | Ricorrente annuo |
|------|------------|------------------|
| Consulto commercialista iniziale | €100–300 | — |
| Tenuta contabilità forfettaria | — | €300–800 |
| PEC | — | €5–25 |
| SPID (provider gratuiti disponibili) | 0 | 0 |
| Firma digitale | €25–50 (smart card) | €5–15 |
| Diritto camerale | — | €88 (ditta individuale) |
| Software fatturazione elettronica | — | €0–60 |
| Conto bancario business | €0–50 | €0–120 |
| Avvocato per EULA/ToS/Privacy (POC) | €800–2.000 | — |
| Registrazione marchio UE EUIPO (1 classe) | €850 + onorari | — (rinnovo dopo 10 anni) |
| Registrazione marchi italiani UIBM (alternativa) | €101–250 + onorari per marchio | — |
| Deposito SIAE software (opzionale) | €129 | — |
| Dominio fitmanagerstudio.com | — | €10–20 |
| VPS edge tunnel (Hetzner CX22 o eq.) | — | ~€50–80 |
| Tool SCA/license audit (POC con tool free) | 0 | 0 |
| **Totale POC indicativo** | **€2.000–4.500** | **€500–1.200** |

---

## 16. Matrice rischi e mitigazioni

| # | Rischio | Probabilità | Impatto | Mitigazione |
|---|---------|-------------|---------|-------------|
| 1 | Conflitto marchio "FitManager" già esistente | Media | Medio | Ricerca anteriorità prima del deposito; piano B nome alternativo |
| 2 | EULA non valida o squilibrata → contestazioni B2B | Bassa | Medio | Avvocato; doppia firma esplicita su clausole limitative |
| 3 | Modello distribuito mal documentato → AVGV trattata come Data Processor | Media | Alto | Documentazione tecnica accurata (questo report + `TUNNEL_ARCHITECTURE.md`); EULA esplicita |
| 4 | Trainer non rispetta GDPR coi propri clienti → reclamo Garante in cui AVGV viene coinvolta | Media | Medio | Onboarding kit con template informativa; clausola EULA che il trainer è Titolare |
| 5 | Vulnerabilità nel software causa breach dati clinici | Bassa | Alto | Audit sicurezza ricorrenti; aggiornamenti tempestivi; bug bounty informale |
| 6 | Licenza open source incompatibile (es. GPL) incorporata nel binario | Media | Alto | Audit licenze ad ogni release; SBOM; sostituzione librerie problematiche |
| 7 | EAA si applica e microimpresa decade → multe per non conformità | Bassa | Medio | Implementare WCAG 2.1 AA sostanziale anche in esenzione |
| 8 | Tunnel VPS edge AVGV down → tutti i trainer offline simultaneamente | Bassa | Medio | Monitoring; provider VPS affidabile; Phase 2 multi-region |
| 9 | VPS edge compromesso da attaccante | Bassa | Medio (TLS e2e mitiga) | Hardening; SSH key-only; fail2ban; aggiornamenti OS |
| 10 | Exit Alessio resta ambigua o conflittuale mentre licenza/tunnel risultano attivi | Media | Medio/alto | `SPEC_EXIT_ALESSIO.md`; copia eseguita; review legale; notifica formale; export/no-data; offboarding registrato |
| 11 | Sanzioni privacy per uso non conforme di marketing | Bassa | Medio | Opt-in esplicito; documentazione consensi; modello double opt-in |
| 12 | Cliente finale tronca URL e raggiunge CRM trainer (problema originario) | Bassa | Alto | Architettura `TUNNEL_ARCHITECTURE.md` risolve strutturalmente |
| 13 | Concorrente registra marchio simile in classe diversa | Media | Basso | Registrare in classi 9 e 42; monitorare nuovi depositi |
| 14 | Errore in fatturazione elettronica → sanzioni Agenzia Entrate | Bassa | Basso | Software qualificato; revisione mensile |
| 15 | Cambio di legge (es. nuova soglia forfettario, nuove regole digital services) | Media | Variabile | Iscrizione a newsletter Agenzia Entrate, Garante, commercialista aggiornato |
| 16 | Trasferte estero prolungate cambiano residenza fiscale senza rivalutazione | Bassa | Alto | Monitorare giorni di permanenza all'estero; ricalibrare con commercialista se >180 gg/anno |

---

## 17. Riferimenti normativi

**Fiscale**
- L. 23/12/2014 n. 190 (regime forfettario)
- DPR 633/1972 (IVA)
- D.Lgs. 127/2015 (fatturazione elettronica)
- TUIR (D.P.R. 22/12/1986 n. 917) — in particolare art. 2 sulla residenza fiscale delle persone fisiche

**Privacy / Protezione dati**
- Reg. UE 2016/679 (GDPR)
- D.Lgs. 196/2003 (Codice Privacy) come modificato da D.Lgs. 101/2018
- Linee guida EDPB e provvedimenti Garante italiano (in particolare su dati sanitari e consensi)

**Accessibilità**
- Direttiva UE 2019/882 (European Accessibility Act)
- D.Lgs. 27/05/2022 n. 82 (recepimento italiano)
- D.Lgs. 22/09/2023 n. 137 (modifiche)
- WCAG 2.1 (W3C)

**Consumatori**
- D.Lgs. 206/2005 (Codice del Consumo)
- Direttiva UE 2011/83 (diritti consumatori)

**Pagamenti**
- Direttiva UE 2015/2366 (PSD2)
- D.Lgs. 218/2017 (recepimento PSD2)
- PCI-DSS v4.0 (PCI Security Standards Council)

**Proprietà intellettuale**
- L. 633/1941 (diritto d'autore)
- D.Lgs. 30/2005 (Codice della Proprietà Industriale)
- D.Lgs. 63/2018 (segreti commerciali)
- Reg. UE 2017/1001 (marchio dell'Unione Europea)

**Software / Open Source**
- Licenze SPDX standard
- Direttiva UE 2009/24 (tutela software)

---

## 18. Appendici

### 18.1 Outline EULA (estratto)

**1. Definizioni**  
**2. Concessione di licenza** (non esclusiva, non trasferibile, revocabile)  
**3. Limitazioni d'uso** (no reverse engineering, no sublicenza, no rivendita)  
**4. Proprietà intellettuale** (titolarità esclusiva AVGV)  
**5. Aggiornamenti** (rilascio nuovo installer; trainer è responsabile dell'installazione)  
**6. Separazione dati e ruoli GDPR** (clausola chiave: software gira sul hardware del licenziatario; i dati trattati restano sotto il controllo esclusivo del licenziatario; AVGV è fornitore di software, non Data Processor)  
**7. Servizio tunnel data-blind** (descrizione e limitazioni)  
**8. Corrispettivo** (importo, periodicità, modalità pagamento, mora)  
**9. Durata, rinnovo, recesso**  
**10. Garanzia e limitazione responsabilità**  
**11. Sospensione e risoluzione**  
**12. Riservatezza** (eventuale incorporazione clausole NDA)  
**13. Cessione del contratto** (consenso AVGV)  
**14. Forza maggiore**  
**15. Modifiche dell'EULA**  
**16. Legge applicabile e foro competente**  
**17. Disposizioni finali** (interezza, separabilità clausole, comunicazioni)

### 18.2 Outline DPA (se necessaria — verificare)

**1. Definizioni** (allineate Art. 4 GDPR)  
**2. Oggetto e durata del trattamento**  
**3. Natura e finalità del trattamento**  
**4. Tipo di dati personali e categorie di interessati**  
**5. Obblighi del Responsabile** (riservatezza, istruzioni del Titolare, sicurezza Art. 32)  
**6. Sub-responsabili** (autorizzazione, elenco, condizioni)  
**7. Diritti degli interessati** (collaborazione)  
**8. Notifica violazioni**  
**9. Trasferimenti extra-UE**  
**10. Audit**  
**11. Restituzione/cancellazione dati a fine contratto**  
**12. Responsabilità e indennizzo**  
**13. Disposizioni finali**

### 18.3 Checklist pre-launch (riepilogo)

**Setup amministrativo**
- [ ] P.IVA AVGV aperta con ATECO 62.01.00
- [ ] PEC attivata e comunicata a INI-PEC
- [ ] SPID funzionante
- [ ] Firma digitale disponibile
- [ ] Conto business operativo
- [ ] Software fatturazione elettronica configurato

**Setup legale**
- [ ] EULA finalizzato e revisionato da avvocato
- [ ] ToS finalizzato
- [ ] Privacy Policy AVGV pubblicata
- [ ] Documento sintetico distribuzione e ruoli GDPR (riferibile in supporto)
- [ ] Marchi depositati (almeno "FitManager")
- [ ] Timestamping codice sorgente eseguito
- [ ] Exit Alessio completata: copia NDA verificata, comunicazione consegnata, dati/licenza/tunnel chiusi e registrati

**Setup tecnico-compliance**
- [ ] Architettura `TUNNEL_ARCHITECTURE.md` implementata e testata
- [ ] TLS e2e verificato (test che AVGV non vede contenuto)
- [ ] WCAG 2.1 AA implementata sulla pagina pubblica
- [ ] Audit licenze open source eseguito, OK
- [ ] SBOM generato
- [ ] Audit vulnerabilità (`pip-audit`) eseguito, OK
- [ ] LICENSES.txt incluso nel bundle
- [ ] Logging e retention configurati (locale + edge)

**Onboarding kit trainer**
- [ ] EULA + ToS + Privacy Policy AVGV in PDF
- [ ] Template informativa privacy trainer→clienti
- [ ] Memo informativo sui ruoli GDPR
- [ ] Guida installazione e primo avvio
- [ ] Riferimenti supporto

**Operativo**
- [ ] Pricing finalizzato e comunicato
- [ ] Modalità pagamento attivate
- [ ] Monitoring VPS edge attivo
- [ ] Backup configurazione VPS edge automatico
- [ ] Procedura aggiornamento PyInstaller documentata
- [ ] Procedura risposta incident (security/privacy) documentata

### 18.4 Template SBOM minimo (CycloneDX-style)

```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.5",
  "version": 1,
  "metadata": {
    "timestamp": "2026-XX-XXTXX:XX:XXZ",
    "component": {
      "type": "application",
      "name": "FitManager",
      "version": "X.Y.Z",
      "publisher": "AVGV Technologies",
      "licenses": [{ "license": { "id": "Proprietary" } }]
    }
  },
  "components": [
    {
      "type": "library",
      "name": "<nome libreria>",
      "version": "<versione esatta>",
      "purl": "pkg:pypi/<nome>@<versione>",
      "licenses": [{ "license": { "id": "<SPDX-ID>" } }]
    }
  ]
}
```

Generazione automatica suggerita:

```bash
pip install cyclonedx-bom
cyclonedx-py -o sbom.json
```

---

## 19. Changelog

| Versione | Data | Modifiche principali |
|----------|------|---------------------|
| 1.0 | (data originale) | Prima emissione |
| 1.1 | 2026-03-29 | Aggiunte sezioni: EAA, open source/SBOM, PSD2/PCI-DSS, anti-spam, B2B vs B2C, PEC tra obblighi strumentali, appendici complete |
| 1.2 | 2026-05-31 | Aggiunta §3 "Modello di distribuzione e implicazioni di compliance"; aggiornata §5 (DPA non necessaria per dati clinici); aggiornata §6 (ruoli GDPR nel modello distribuito, schema flusso dati); aggiornati riferimenti incrociati a `CRM_ACCESS_ARCHITECTURE.md` v2.0 (tunnel data-blind, isolamento per istanza); aggiunto rischio "AVGV trattata come Data Processor per mancata documentazione del modello"; ricostruzione integrale del documento (originale v1.1 non disponibile per copy-edit) |
| 1.3 | 2026-05-31 | Correzione assunzione fiscale: residenza fiscale di Giacomo è esclusivamente italiana, trasferte in Francia non comportano implicazioni fiscali transfrontaliere. Rimossa §4.4 "Apertura P.IVA dall'estero" (non applicabile); aggiunta §4.5 "Trasferta lavorativa all'estero" come nota informativa; rimossa Convenzione IT-FR dai riferimenti normativi; aggiornata matrice rischi (rimosso rischio fiscale IT-FR come critico; aggiunto monitoraggio trasferte come rischio basso); aggiornata Fase 1 roadmap |

# Business Plan — FitManager Studio+

**Versione:** 3.0 — 23 marzo 2026
**Autore:** Giacomo Verardo
**Stato:** Draft per investitori e collaboratori

---

## 1. Executive Summary

**FitManager Studio+** e' il primo CRM locale Windows progettato specificamente per chinesiologi, personal trainer e professionisti fitness a Partita IVA in Italia.

**Problema:** I professionisti fitness italiani (~120.000 operatori stimati, 75% P.IVA) gestiscono clienti, anamnesi cliniche, schede allenamento, piani alimentari e contabilita' con un mix di Excel, WhatsApp, carta e app generiche. Nessun software unisce CRM operativo, scienza dell'allenamento e privacy dei dati clinici in un unico prodotto locale.

**Soluzione:** Un software desktop installabile che integra:
- CRM completo (clienti, contratti, pagamenti, agenda, cassa)
- Motore scientifico di periodizzazione (Training Science Engine, 3.500 LOC)
- Safety Engine per condizioni cliniche (47 condizioni, 80 regole)
- Nutrition Engine con database CREA 2019 (880 alimenti, piani LARN)
- Catalogo 500 esercizi con tassonomia muscolare/articolare
- Zero cloud obbligatorio — dati sul PC del professionista

**Stadio:** Prodotto funzionante (v1.0.4), 326 test backend + 69 test frontend, installer Windows pronto. Pre-revenue, in fase di lancio.

**Modello commerciale:** Licenza perpetua singola (€149–€449) + upgrade annuale opzionale (€99/anno). Lancio a scarcita' controllata con POC strutturata: 10 licenze Fondatore (Proof of Concept 90gg), poi 20 Early Adopter, poi prezzo pieno.

**Strategia di lancio:** POC con 10 Fondatori selezionati → validazione con dati reali → crescita organica. Bootstrap puro, zero costi strutturali Anno 1 (libero professionista, regime forfettario, no ufficio, no dipendenti). Crescita sostenibile dal Anno 2 (piccolo ufficio + tirocinante).

**Approccio finanziario:** Self-funded Anno 1. Apertura a investitori dal Anno 2 solo se i dati della POC e la traction confermano il modello. Il seed non e' un prerequisito — e' un acceleratore opzionale.

---

## 2. Problema e Opportunita'

### Il dolore quotidiano del trainer a P.IVA

Il professionista fitness italiano lavora tipicamente con 15-40 clienti attivi e gestisce:

| Attivita' | Strumento attuale | Problema |
|-----------|-------------------|----------|
| Anagrafica clienti | Excel / rubrica telefono | Zero struttura, nessuna anamnesi clinica |
| Schede allenamento | PDF / app gratuite | Non collegati al cliente, nessuna progressione |
| Pagamenti e contratti | Foglio Excel / carta | Nessun tracking automatico, errori manuali |
| Anamnesi e misurazioni | Carta / moduli Word | Non digitali, non ricercabili, persi |
| Piani alimentari | Template generici | Nessun calcolo LARN, nessun scoring |
| Agenda | Google Calendar | Scollegata dal CRM, nessun reminder intelligente |

**Risultato:** 3-5 ore/settimana perse in amministrazione, rischio errori clinici, nessuna visione unificata del cliente.

### Perche' adesso

1. **Regolamentazione in arrivo:** Dal 1 luglio 2023 il Registro Nazionale delle attivita' sportive dilettantistiche e' operativo. La professionalizzazione spinge verso strumenti strutturati.
2. **Boom P.IVA fitness:** Il 75% dei trainer in Europa lavora come autonomo. In Italia la domanda di PT qualificati e' cresciuta del 35% in 2 anni (ISTAT 2023).
3. **Architettura AI-ready:** Il trend 2026 e' "AI + personalizzazione". FitManager ha l'architettura predisposta (Langchain + Ollama) — non ancora attiva, ma pronta per l'attivazione senza riscritture.
4. **Privacy post-GDPR:** I trainer gestiscono dati sanitari (anamnesi, patologie, misurazioni). Il cloud generico non offre garanzie adeguate.

### Dimensione del mercato

Il mercato di riferimento di FitManager non e' "il fitness italiano" ma una nicchia specifica: **il professionista fitness a P.IVA tech-ready che lavora in autonomia**.

| Livello | Stima | Metodologia | Nota |
|---------|-------|-------------|------|
| **SOM** (anno 3) | **€135K/anno** | 300 licenze × €449 | Obiettivo operativo reale |
| **SAM** | **€7,2M/anno** | ~15.000 trainer tech-ready × €480/anno (licenza+upgrade) | Il mercato raggiungibile |
| **TAM** (contesto) | €360M/anno | ~120.000 operatori fitness P.IVA × €250/mese | Solo contesto — non il mercato indirizzabile |

**Come si arriva al SAM di 15.000:** Il mercato fitness italiano vale €3,1 miliardi (2024), con ~8.000 centri e 23,5 trainer/struttura media. Aggiungendo freelance e chinesiologi, la stima e' 100.000-150.000 operatori totali. Di questi, ~15.000 sono il segmento tech-ready: certificati CONI, <45 anni, aree urbane, disposti a investire in strumenti professionali. FitManager punta a catturare il **2-4% del SAM entro 3 anni** (300-600 clienti).

---

## 3. Soluzione — FitManager Studio+

### Architettura del prodotto

```
┌─────────────────────────────────────────────────────┐
│                  FitManager Studio+                  │
├──────────────┬──────────────┬───────────────────────┤
│  CRM Core    │  Scienza     │  Business             │
│              │              │                       │
│  Clienti     │  500 esercizi│  Contratti            │
│  Anamnesi    │  Training    │  Pagamenti            │
│  Misurazioni │  Science     │  Cassa                │
│  Avatar 6D   │  Safety Eng. │  Agenda               │
│  Dossier     │  Nutrition   │  Licenza HW           │
│              │  Engine      │                       │
├──────────────┴──────────────┴───────────────────────┤
│  SQLite WAL (locale) │ Zero cloud │ Privacy-first   │
└─────────────────────────────────────────────────────┘
```

### Feature chiave gia' implementate (v1.0.4)

| Area | Feature | Stato |
|------|---------|-------|
| CRM | Clienti, contratti, pagamenti, agenda, cassa | Completo |
| Clinico | Anamnesi 6 step, misurazioni, avatar 6D, readiness score | Completo |
| Allenamento | Workout builder 3-tab, DnD, blocchi, export PDF | Completo |
| Scienza | Training Science Engine (periodizzazione, EMG, volume MEV/MAV/MRV) | Completo |
| Sicurezza | Safety Engine (47 condizioni cliniche, 80 regole) | Completo |
| Nutrizione | 880 alimenti CREA, 210 ricette, 12 template LARN, piano 7gg | Completo |
| Operativo | Setup wizard, licenza HW-bound, backup/restore, diagnostica | Completo |
| UX | Command palette (Ctrl+K), spotlight tour 19 passi, dark mode | Completo |
| Accesso | Portale anamnesi self-service (share token + kiosk mobile) | Completo |
| Rete | Tailscale Funnel (HTTPS pubblico per anamnesi remota) | Completo |

### Stack tecnologico

| Layer | Tecnologia | Motivazione |
|-------|-----------|-------------|
| Backend | Python 3.12 + FastAPI + SQLModel | Performance, typing, ecosistema AI |
| Frontend | Next.js 16 + React 19 + TypeScript + shadcn/ui | SSR, DX moderna, componenti accessibili |
| Database | SQLite WAL × 3 (crm + catalog + nutrition) | Zero setup, backup = copia file, locale |
| AI (futuro) | Langchain + Ollama | LLM locale, zero cloud, privacy totale |
| Distribuzione | PyInstaller + Next.js standalone + Inno Setup | Un installer Windows, 83MB |

### Differenziatori competitivi

1. **Locale-first:** Dati sul PC del trainer. Zero abbonamento cloud obbligatorio. Backup = copia file.
2. **Scienza integrata:** Unico software con Training Science Engine (periodizzazione evidence-based) e Safety Engine (47 condizioni cliniche).
3. **Nutrizione CREA:** Database ufficiale italiano (CREA 2019), non generico USDA. Piani LARN per fascia eta'/attivita'.
4. **Privacy nativa:** Dati clinici (anamnesi, patologie) mai in cloud. GDPR-compliant by design.
5. **Italiano nativo:** UI, terminologia, workflow pensati per il contesto italiano. Non una traduzione.

---

## 4. Analisi di Mercato e Competitor

### Panorama competitivo

| Software | Tipo | Prezzo | Locale | Scienza | Nutrizione IT | Target |
|----------|------|--------|--------|---------|---------------|--------|
| **FitManager Studio+** | Desktop perpetuo | **€449 una tantum** + €99/anno upgrade | **Si** | **Si** | **Si (CREA)** | PT/chinesiologo P.IVA |
| Mangofit | Cloud SaaS | €10-40/mese (€120-480/anno) | No | No | No | PT generico |
| EvolutionFit | Cloud SaaS | €30-80/mese (€360-960/anno) | No | Basica | No | Palestre + PT |
| PT Distinction | Cloud SaaS | $20-80/mese ($240-960/anno) | No | No | No | PT anglofono |
| MyPTHub | Cloud SaaS | $50-100/mese ($600-1200/anno) | No | No | No | PT anglofono |
| JEFIT | App B2C | Free-$13/mese | No | No | No | Utente finale |
| PT Software (ISSA) | Cloud | Custom | No | Basica | No | PT certificati ISSA |
| Excel/WhatsApp | Manuale | Free | Si | No | No | Tutti (default) |

**Vantaggio pricing perpetuo:** Un PT che usa Mangofit Pro (€40/mese) spende €480/anno, €960 in 2 anni. FitManager costa €449 + €99 = €548 in 2 anni, con feature scientifiche incomparabilmente superiori e dati in locale. **Dal terzo anno il risparmio e' netto.**

### Posizionamento

```
                        Scienza integrata
                              ▲
                              │
                   FitManager │
                    Studio+   │
                              │
    Locale ◄──────────────────┼──────────────────► Cloud
                              │
                              │  EvolutionFit
              Excel/WhatsApp  │  Mangofit
                              │  PT Distinction
                              ▼
                        Gestione base
```

**FitManager occupa un quadrante vuoto:** locale + scienza integrata. Nessun competitor combina queste due dimensioni.

### Vantaggi competitivi sostenibili (moat)

1. **Database scientifico proprietario:** 500 esercizi con tassonomia muscolare/articolare, 940 relazioni, scoring 14D. Costruito incrementalmente in 6 mesi.
2. **Training Science Engine:** 3.500 LOC di logica di periodizzazione evidence-based. Non replicabile in settimane.
3. **Safety Engine:** 47 condizioni cliniche × 80 regole = intelligenza che nessun competitor ha.
4. **Nutrizione CREA italiana:** 880 alimenti dal dataset ufficiale italiano, non traduzione USDA.
5. **Architettura privacy-first:** Riscrivere un SaaS in locale e' ordini di grandezza piu' costoso che partire locale.

---

## 5. Modello di Business

### Filosofia: licenza perpetua + upgrade annuale

FitManager adotta un modello **licenza perpetua** coerente con il DNA locale-first del prodotto:
- Il trainer compra una volta e possiede il software per sempre.
- Senza upgrade, il software continua a funzionare alla versione acquistata.
- L'upgrade annuale (opzionale) sblocca nuove feature, cataloghi aggiornati e supporto prioritario.

Questo elimina l'ansia da abbonamento tipica dei P.IVA e crea un messaggio chiaro: **"Il tuo software, per sempre."**

### Revenue streams

| Stream | Descrizione | Pricing |
|--------|-------------|---------|
| **Licenza perpetua** | Software completo, HW-bound, una tantum | €149–€449 (fase lancio) |
| **Upgrade annuale** | Nuove feature + cataloghi + supporto prioritario | €99/anno (opzionale) |
| **Setup & onboarding** | Installazione assistita + formazione 1:1 | €149 una tantum |
| **Moduli AI premium** | Suggerimenti allenamento/nutrizione AI (futuro) | Add-on una tantum |
| **White-label** | Personalizzazione per centri fitness (futuro) | Custom |

### Strategia di lancio a scarcita' controllata

Il lancio segue 3 fasi con scarcita' reale e prezzo crescente:

```
FASE 1 — FONDATORI (Mese 1)
┌──────────────────────────────────────────────────────┐
│  10 licenze  │  €149  │  Upgrade LIFETIME incluso    │
│              │        │  Badge "Fondatore"            │
│              │        │  Accesso diretto alla roadmap │
│              │        │  Community esclusiva           │
└──────────────────────────────────────────────────────┘
Valore reale: software €449 + upgrade a vita (€99/anno × N anni) = >€700
Chi entra ora non paghera' mai upgrade. Sono i primi evangelisti.

FASE 2 — EARLY ADOPTER (Mesi 2-4)
┌──────────────────────────────────────────────────────┐
│  20 licenze  │  €299  │  2 anni upgrade inclusi      │
│              │        │  Community                    │
│              │        │  Onboarding prioritario       │
└──────────────────────────────────────────────────────┘
Valore reale: software €449 + 2 anni upgrade (€198) = €647
Risparmio percepito: €348. Testimonial dei Fondatori come social proof.

FASE 3 — PREZZO PIENO (Mese 5+)
┌──────────────────────────────────────────────────────┐
│  Illimitate  │  €449  │  1 anno upgrade incluso      │
│              │        │  Community                    │
└──────────────────────────────────────────────────────┘
Prezzo di listino. Primo anno di aggiornamenti incluso.
Dal secondo anno: €99/anno per continuare a ricevere update.
```

### Perche' questa struttura converte

| Leva psicologica | Come agisce |
|------------------|-------------|
| **Scarcita' reale** | 10, poi 20 licenze — non "offerta limitata" finta, numeri credibili per un lancio software |
| **Price anchoring** | Il prezzo finale €449 e' visibile da subito → €149 sembra un regalo |
| **Loss aversion** | "Upgrade lifetime" solo per i Fondatori. Chi aspetta lo perde per sempre |
| **Social proof progressivo** | Fase 2 vede i Fondatori gia' attivi. Fase 3 vede entrambi i gruppi |
| **Zero rischio ricorrente** | Nessun abbonamento. Compri, possiedi. L'upgrade e' una scelta, non un obbligo |
| **Confronto favorevole** | Mangofit Pro = €480/anno, ogni anno. FitManager = €449 una volta |

### Unit economics (target Anno 2)

| Metrica | Valore | Note |
|---------|--------|------|
| **Prezzo medio licenza** | €410 | Mix fasi lancio + prezzo pieno |
| **Tasso rinnovo upgrade** | 60% | Conservativo (benchmark perpetuo: 50-70%) |
| **Ricavo medio per cliente Anno 1** | €410 | Licenza (upgrade incluso nel primo anno) |
| **Ricavo medio per cliente Anno 2+** | €99 × 60% = €59 | Solo upgrade rinnovi |
| **CAC** | €120 (stimato) | Organico + demo + community. Da validare con dati POC e prime vendite |
| **LTV** (5 anni) | €410 + (4 × €59) = €646 | Licenza + 4 anni upgrade al 60% |
| **LTV:CAC** | 5,4:1 | Target >3:1 |
| **Gross margin** | 90%+ | Zero costi cloud per utente |

### Modello di ricavo composito

Il ricavo totale e' la somma di due componenti:

```
Ricavo = (Nuove licenze × Prezzo medio) + (Base installata × Tasso rinnovo × €99)
              ▲ upfront, variabile                  ▲ ricorrente, crescente
```

Questo crea un "pavimento" di ricavi ricorrenti che cresce con la base installata, pur mantenendo la narrativa perpetua che il mercato target preferisce.

---

## 6. Strategia Go-to-Market

### Pre-lancio (Settimane -4 a 0): Segnali di domanda

Prima della POC, serve un minimo di presenza online per validare l'interesse e alimentare il funnel.

| Azione | Strumento | Costo | Target |
|--------|-----------|-------|--------|
| Landing page "Coming Soon" | Sito statico (Vercel/Netlify) | €0 | Online in 1 settimana |
| Waiting list | Form sulla landing (Tally/Google Forms) | €0 | 50+ iscritti pre-POC |
| Profilo LinkedIn attivo | Post 2-3/settimana su dolori del PT | €0 | 200+ follower in 4 settimane |
| Teaser video (60 sec) | Screen recording del software | €0 | Condivisibile, mostra il prodotto reale |

**Perche' serve:** Un investitore o un partner chiedera' "quanti sono interessati?". Anche 50 iscritti in waiting list sono un dato. Zero iscritti = zero segnale.

### Fase 0 — POC: Proof of Concept (Mesi 1-3): 10 Fondatori

**La POC e' il fondamento di tutto.** I primi 10 Fondatori non sono clienti — sono un esperimento controllato che deve rispondere a una domanda: *"Un PT che adotta FitManager migliora in modo misurabile gestione clienti, tempo operativo e crescita professionale?"*

**Selezione strategica (non casuale):**

| # | Profilo | Perche' |
|---|---------|---------|
| 3 | PT in palestra | Il contesto piu' comune |
| 2 | PT freelance con studio | Gestione autonoma completa |
| 2 | Chinesiologo con clienti clinici | Valida safety engine e anamnesi |
| 1 | PT online/ibrido | Valida portale anamnesi remoto |
| 1 | PT neoqualificato (<2 anni) | Curva di apprendimento |
| 1 | PT senior (>10 anni, 40+ clienti) | Scalabilita' e confronto prima/dopo |

**Protocollo 90 giorni:**
- **Giorni 1-14:** Installazione 1:1, questionario baseline (ore admin, clienti gestiti, strumenti usati, livello organizzazione 1-10)
- **Giorni 15-75:** Uso reale + check-in bisettimanale (15 min) + micro-survey settimanale (3 domande)
- **Giorni 75-90:** Questionario finale (stesse metriche), intervista video, NPS, sessione di gruppo

**Metriche di successo:**

| Metrica | Baseline atteso | Target post-90gg |
|---------|----------------|-------------------|
| Ore admin/settimana | 3-5h | <2h |
| Senso di organizzazione (1-10) | 4-6 | 8+ |
| NPS | N/A | >50 |
| "Lo ricompreresti a €449?" | N/A | 8/10 dicono si |

**Output della POC:** 10 case study con dati reali + 10 testimonial video + dati aggregati per marketing e investitori. Se la POC fallisce, lo scopriamo con €200 di investimento cash, non con €50.000 di marketing.

**Nota importante:** Il questionario baseline include una domanda di willingness-to-pay ("Quanto saresti disposto a pagare per uno strumento che risolve questi problemi?") posta **prima** di rivelare il prezzo. Questo dato valida il pricing €449 con evidenze reali, non con ipotesi.

**Nota fiscale:** Durante la POC (mesi 1-3) le 10 vendite a €149 possono rientrare in prestazione occasionale (sotto la soglia dei €5.000 annui). L'apertura P.IVA avviene al mese 4, quando partono le vendite Early Adopter.

### Fase 1 — Early Adopter (Mesi 4-6): 10 → 30 clienti

**Prerequisito:** POC completata con risultati positivi. Apertura P.IVA regime forfettario.

| Azione | Canale | Obiettivo |
|--------|--------|-----------|
| Testimonial dei Fondatori | Video brevi "ecco cosa e' cambiato in 90gg" | Social proof con numeri reali |
| Waiting list (senza deposito) | Landing page + social | 100+ iscritti |
| Demo 1:1 (20 min) | Zoom con screen share | 40% conversione |
| Countdown pubblico | Landing page | "12 posti rimasti su 20" (reale) |

**Messaggio Early Adopter:** *"I Fondatori hanno ridotto l'admin del 55%. 20 posti a €299 con 2 anni di aggiornamenti. Poi si chiude."*

### Fase 2 — Prezzo pieno + crescita organica (Mesi 7-12): 30 → 90 clienti

| Azione | Canale | Obiettivo |
|--------|--------|-----------|
| Webinar mensile | Demo live + Q&A, garanzia 30gg | 10-20 partecipanti/webinar |
| Referral program | Fondatore/EA porta un amico → il referrer riceve 3 mesi upgrade gratis | Viralita' organica, clienti di qualita' |
| Content marketing | Blog + LinkedIn + gruppi FB in italiano | SEO long-tail |
| Partnership formatori | ISSA, FIF, ASI, accademie | Accesso a neoqualificati |
| Calcolatore ROI | Sul sito: "quante ore perdi in admin?" | Conversione razionale |

**Messaggio prezzo pieno:** *"I tuoi dati, il tuo PC, la tua scienza. €449 una volta, per sempre. Zero abbonamenti."*

**Garanzia:** Soddisfatto o rimborsato 30 giorni — zero rischio percepito su €449.

### Fase 3 — Scala (Mesi 13-36): 90 → 570 clienti

- Tirocinante dedicato a customer success + community (dal mese 13)
- Piccolo ufficio come base operativa (dal mese 13)
- Presenza a fiere di settore (RiminiWellness, ForumClub)
- Case study e testimonial video strutturati
- Google Ads su keyword transazionali
- Affiliate program per trainer influencer
- Moduli AI attivati (differenziazione premium)
- Espansione a chinesiologi clinici e fisioterapisti
- Valutazione white-label per centri fitness

---

## 7. Operations Plan

### Struttura societaria e fiscale — evoluzione per fasi

```
MESI 1-3 (POC)          MESI 4-12 (Anno 1)        ANNO 2+
Prestazione occasionale  P.IVA forfettaria          P.IVA forfettaria
€1.490 (sotto soglia     ATECO 62.10.00             (o transizione a
 €5.000 annui)           Aliquota 5% (startup)      ordinario/SRL se
Nessun costo fisso       Coeff. redditivita' 67%    fatturato >€85K)
                         INPS gest. separata ~26%
                         Carico fiscale ~20-21%
                         del fatturato lordo
```

**Perche' il forfettario e' perfetto per Anno 1:**
- Aliquota ridotta 5% per i primi 5 anni (startup)
- Nessuna IVA da addebitare (il PT paga €449 netti, non €449+22%)
- Contabilita' semplificata (un commercialista base basta)
- Nessun obbligo di fatturazione elettronica sotto certi limiti

### Tecnologia

| Componente | Stato | Costo annuo |
|------------|-------|-------------|
| Sviluppo software | Completato (v1.0.4) | €0 (sweat equity) |
| Hosting sito/landing | Da attivare | €240/anno |
| CI/CD (GitHub Actions) | Attivo | €0 (free tier) |
| Code signing certificate | Da acquistare | €200/anno |
| Distribuzione installer | GitHub Releases / sito | €0 |
| Community (Discord) | Da attivare | €0 (free tier) |
| Survey/forms | Google Forms | €0 |
| **Totale infrastruttura** | | **~€450/anno** |

### Infrastruttura minima

- **Zero server:** il software gira in locale. Nessun costo cloud per utente.
- **Costo marginale per cliente ≈ €0:** nessun hosting, nessun DB cloud, nessun bandwidth.
- **Supporto:** knowledge base + community + email. Zero ticket system a pagamento.
- **Il vantaggio strutturale del modello locale:** ogni cliente in piu' non aumenta i costi operativi.

### Processi chiave

1. **Release pipeline:** 5 fasi automatizzate (preflight, build, verify, seal, tag) — gia' implementato.
2. **Aggiornamento cataloghi:** Seed idempotente, upgrade non distruttivo.
3. **Licenza:** RSA 2048 + JWT RS256 + hardware binding. Generazione via CLI.
4. **Backup/restore:** Un file `.db` copiabile. Recovery = rimpiazzare il file.
5. **POC management:** Check-in bisettimanali, micro-survey, sessione di chiusura al giorno 90.

---

## 8. Team

### Organigramma per fase

```
ANNO 1 (bootstrap)              ANNO 2 (primo team)            ANNO 3 (scala)
┌──────────────┐                ┌──────────────┐               ┌──────────────┐
│   Founder    │                │   Founder    │               │   Founder    │
│  (Giacomo)  │                │  (Giacomo)  │               │  (Giacomo)  │
└──────┬───────┘                └──────┬───────┘               └──────┬───────┘
       │                               │                              │
┌──────┴───────┐                ┌──────┴───────┐               ┌──────┴───────┐
│   Industry   │                │   Industry   │               │   Industry   │
│   Partner    │                │   Partner    │               │   Partner    │
│  (equity +   │                │  (equity +   │               │  (equity +   │
│  rev. share) │                │  rev. share) │               │  rev. share) │
└──────────────┘                └──────┬───────┘               └──────┬───────┘
                                       │                              │
                                ┌──────┴───────┐               ┌──────┼───────┐
                                │  Tirocinante │               │ Junior│Tirocin│
                                │  (€1.200/m)  │               │€1.500 │€1.200 │
                                └──────────────┘               └───────┴───────┘
```

### Founder

**Giacomo Verardo** — Fondatore, sviluppatore e product owner
- Ha costruito FitManager Studio+ da zero in ~6 mesi
- Stack completo: Python/FastAPI + Next.js/React + SQLite + AI
- 45.000+ LOC, 395 test, 3 database, 5 motori scientifici
- Anno 1: copre sviluppo, supporto, community, marketing, vendite

### Industry Partner — Ruolo strutturale (non opzionale)

Il progetto richiede una figura con profonda esperienza nel settore fitness, credibilita' verso i professionisti target e un network attivo ai vertici del mercato italiano. Questo ruolo e' **indispensabile** per la fase di lancio e category creation.

**Profilo richiesto:**
- 15+ anni di esperienza operativa nel settore fitness/wellness
- Network attivo tra formatori, enti (CONI, FIF, ISSA, ASI), catene, opinion leader
- Credibilita' diretta verso il target (i PT si fidano di un pari, non di un software)
- Capacita' di creare e condurre contenuti (masterclass, webinar, formazione)

**Candidato identificato:** Professionista senior con 20+ anni nel settore fitness, network attivo ai vertici. Accordo in fase di definizione.

**Piano B:** Se il candidato attuale non accetta, il ruolo viene ricercato tramite: (1) enti di formazione fitness (ISSA, FIF, ASI) — formatori senior con network attivo; (2) LinkedIn — profili ex-catena con esperienza gestionale; (3) community fitness italiane — opinion leader con following attivo. Timeline piano B: 4-6 settimane di ricerca. La POC non parte senza questo ruolo coperto.

**Responsabilita':**

| Area | Attivita' | Impatto |
|------|-----------|---------|
| **POC** | Selezione dei 10 Fondatori dal suo network | Qualita' del campione POC |
| **Go-to-market** | Introduzioni a PT, formatori, enti del settore | Pipeline vendite |
| **Community** | Conduzione masterclass e webinar mensili | Retention + valore upgrade |
| **Posizionamento** | Validazione messaggio "PT Evoluto", linguaggio | Credibilita' della categoria |
| **Product** | Feedback su feature, priorita', workflow reali | Product-market fit |

#### Modello di ingaggio: 3 opzioni

Il ruolo di Industry Partner prevede 3 possibili strutture di compenso. Lo **Scenario A e' il modello primario**, coerente con il bootstrap e con una vera partnership dove entrambe le parti guadagnano in proporzione ai risultati.

##### Scenario A — Partnership a equity + revenue share (PRIMARIO)

**Principio:** Nessun costo fisso. Il partner guadagna solo se il progetto genera ricavi. Piu' vende, piu' guadagna. Zero tetto.

| Componente | Valore | Come funziona |
|------------|--------|---------------|
| **Equity** | 5-8% | Vesting 4 anni, cliff 1 anno (*) |
| **Revenue share: Community PRO** | 25% dei ricavi upgrade €99/anno | Calcolato su tutti i rinnovi upgrade |
| **Revenue share: Inner Circle** | 25% dei ricavi €299/anno (futuro) | Calcolato su tutti gli abbonamenti IC |
| **Revenue share: Vendite da network** | 20% sulle licenze generate via referral | Tracciato con codice/link referral univoco |
| **Revenue share: Masterclass** | 30% sul ricavo delle masterclass che conduce | Sia live che registrate vendute singolarmente |
| **Licenza Fondatore** | Inclusa | Badge, upgrade lifetime, accesso roadmap |

(*) **Vesting 4 anni, cliff 1 anno:** L'equity matura progressivamente. Se il partner lascia prima di 12 mesi, non matura nulla. Dopo il cliff, matura 1/48 al mese. Dopo 4 anni, l'equity e' completamente maturata. Questo protegge entrambe le parti.

**Costo fisso per il founder: €0.** Il revenue share e' un costo variabile che esiste solo quando ci sono ricavi.

##### Scenario B — Retainer + equity ridotta (FALLBACK)

Da usare se il candidato ideale non accetta lo Scenario A, o se serve cercare un profilo diverso sul mercato che richiede compenso fisso.

| Componente | Valore |
|------------|--------|
| Retainer mensile | €500-1.000/mese |
| Equity | 1-3% (vesting 4 anni, cliff 1 anno) |
| Masterclass fee | €200-500 per sessione condotta |

**Costo fisso:** €6.000-12.000/anno. Impatta il P&L come costo operativo.

##### Scenario C — Content Partner (MINIMO)

Coinvolgimento leggero, per un profilo che non puo' o non vuole impegnarsi strategicamente.

| Componente | Valore |
|------------|--------|
| Fee per masterclass | €300-500 per sessione |
| Fee per contenuto | €100-200 per articolo/video |
| Licenza Fondatore | Inclusa |

**Costo fisso:** €2.400-6.000/anno. Nessun equity, nessun allineamento a lungo termine.

#### Proiezione guadagno Industry Partner — Scenario A

I calcoli seguenti mostrano quanto guadagna il partner in ciascun anno, assumendo lo Scenario A (equity + revenue share) e che il partner generi direttamente il 35% delle vendite totali tramite il suo network.

**Legenda calcoli:**
- `Vendite da network` = 35% delle vendite totali × prezzo medio × 20% revenue share
- `Community PRO` = ricavi upgrade totali × 25%
- `Masterclass` = 8 masterclass/anno × ricavo medio per masterclass × 30%

##### Anno 1

| Voce | Calcolo | Importo partner |
|------|---------|-----------------|
| Vendite da network (20%) | 35% di 90 licenze = 32 vendite × €382 prezzo medio (*) × 20% | **€2.445** |
| Community PRO (25%) | €0 (upgrade incluso nel primo anno) | **€0** |
| Masterclass (30%) | 6 masterclass × €0 (**) | **€0** |
| **Totale cash Anno 1** | | **€2.445** |

(*) Prezzo medio ponderato: (10×€149 + 20×€299 + 60×€449) / 90 = €382
(**) Anno 1: le masterclass sono incluse nella community base per costruire il valore. Nessun ricavo separato.

##### Anno 2

| Voce | Calcolo | Importo partner |
|------|---------|-----------------|
| Vendite da network (20%) | 35% di 180 licenze = 63 × €449 × 20% | **€5.658** |
| Community PRO (25%) | €4.356 ricavi upgrade × 25% | **€1.089** |
| Masterclass (30%) | 8 sessioni, 4 vendute singolarmente a €39 × ~30 partecipanti = €4.680 × 30% | **€1.404** |
| **Totale cash Anno 2** | | **€8.151** |

##### Anno 3

| Voce | Calcolo | Importo partner |
|------|---------|-----------------|
| Vendite da network (20%) | 35% di 300 licenze = 105 × €449 × 20% | **€9.429** |
| Community PRO (25%) | €13.600 ricavi upgrade × 25% | **€3.400** |
| Inner Circle (25%) | 30 membri × €299 × 25% | **€2.243** |
| Masterclass (30%) | 10 sessioni, 6 vendute × €39 × ~50 partecipanti = €11.700 × 30% | **€3.510** |
| **Totale cash Anno 3** | | **€18.582** |

##### Riepilogo 3 anni — Chi guadagna quanto

| | **Anno 1** | **Anno 2** | **Anno 3** | **Cumulativo** |
|---|-----------|-----------|-----------|---------------|
| **Ricavi lordi totali** | €35.910 | €94.856 | €178.970 | €309.736 |
| Revenue share Industry Partner | €2.445 | €8.151 | €18.582 | **€29.178** |
| % dei ricavi al partner | 6,8% | 8,7% | 10,4% | 9,4% |
| **Ricavi netti founder** (pre-costi e tasse) | €33.465 | €86.705 | €160.388 | €280.558 |

**Nota:** La % del partner cresce nel tempo perche' la componente Community PRO + Inner Circle + Masterclass cresce piu' velocemente delle licenze pure. Questo e' by design: il partner e' incentivato a costruire la community (valore a lungo termine), non solo a vendere licenze (valore una tantum).

##### Valore equity nel tempo (stima)

| Anno | Valutazione stimata progetto (*) | Valore equity partner (6%) |
|------|----------------------------------|---------------------------|
| 1 | €200.000-350.000 | €12.000-21.000 |
| 2 | €500.000-800.000 | €30.000-48.000 |
| 3 | €1.000.000-1.500.000 | €60.000-90.000 |

(*) Valutazione basata su multiplo 5-10x dei ricavi annuali (benchmark software perpetuo con componente ricorrente). Non e' una valutazione formale — serve solo come ordine di grandezza.

##### Guadagno totale partner (cash + equity paper value)

| | **Anno 1** | **Anno 2** | **Anno 3** |
|---|-----------|-----------|-----------|
| Cash (revenue share) | €2.445 | €8.151 | €18.582 |
| Equity paper value (6%) | €15.000 | €39.000 | €75.000 |
| **Totale** | **€17.445** | **€47.275** | **€93.582** |

> **Lettura per il partner:** "Anno 1 guadagno poco in cash, ma sto costruendo un asset. Anno 3 ho €18K di cash ricorrente + un pezzo di un'azienda che vale €75K+. E cresce ogni anno."

### Anno 2 — Primo team operativo

| Ruolo | Tipo | Costo/mese | Quando | Cosa fa |
|-------|------|-----------|--------|---------|
| **Tirocinante** | Extracurriculare | €1.200 | Mese 13 | Customer success, community, onboarding, contenuti |
| **Ufficio** | Piccolo/condiviso | €400 | Mese 13 | Base operativa, demo in presenza |

**Costo fisso aggiuntivo Anno 2:** €14.400 (tirocinante) + €4.800 (ufficio) = **€19.200/anno**

### Anno 3 — Crescita misurata

| Ruolo | Tipo | Costo/mese | Quando | Cosa fa |
|-------|------|-----------|--------|---------|
| **Tirocinante → junior** | Conferma | €1.500 | Mese 25 | Customer success + community management |
| **Secondo tirocinante** | Extracurriculare (opzionale) | €1.200 | Mese 30 | Marketing content + social |
| **Ufficio** | Continuo | €500 | Continuo | Base operativa |

### Advisory board (da costruire progressivamente)

- Commercialista specializzato in startup/forfettario
- Legale GDPR/privacy (consulenza spot, non retainer)

---

## 9. Proiezioni Finanziarie

### Ipotesi chiave

- **Licenza perpetua:** €149 (10 POC) → €299 (20 Early Adopter) → €449 (prezzo pieno)
- **Upgrade annuale:** €99/anno, incluso nel primo anno. Tasso rinnovo: 55% Anno 2, 65% Anno 3
- **Fondatori:** upgrade lifetime (mai €99/anno) — costo: mancato ricavo su 10 utenti
- **Anno 1:** Solo founder, P.IVA forfettaria, zero ufficio, zero dipendenti
- **Anno 2:** Piccolo ufficio (€400/mese) + tirocinante (€1.200/mese)
- **Anno 3:** Ufficio (€500/mese) + junior (€1.500) + eventuale 2o tirocinante (€1.200)
- **Vendite:** ~10/mese mesi 7-12, ~15/mese Anno 2, ~25/mese Anno 3 (conservativo)

### Struttura fiscale — Regime forfettario sviluppatore

| Voce | Aliquota/importo | Applicata a |
|------|-----------------|-------------|
| Coefficiente redditivita' | 67% | Fatturato lordo |
| IRPEF startup (primi 5 anni) | 5% | Reddito imponibile (67% fatt.) |
| INPS gestione separata | ~26% | Reddito imponibile (67% fatt.) |
| **Carico fiscale totale** | **~20,8%** | **Fatturato lordo** |
| Commercialista | €800-1.200/anno | Fisso |
| Limite fatturato forfettario | €85.000/anno | Oltre → regime ordinario o SRL |

**Esempio:** Su €50.000 di fatturato → reddito imponibile €33.500 → IRPEF €1.675 + INPS €8.730 = **€10.405 di tasse+contributi** → netto ~€39.600

### Dettaglio vendite Anno 1

| Periodo | Licenze | Prezzo | Ricavo | Note fiscali |
|---------|---------|--------|--------|-------------|
| Mesi 1-3 (POC Fondatori) | 10 | €149 | €1.490 | Prestazione occasionale (<€5.000) |
| Mesi 4-6 (Early Adopter) | 20 | €299 | €5.980 | P.IVA forfettaria (apertura mese 4) |
| Mesi 7-12 (Prezzo pieno) | 60 | €449 | €26.940 | P.IVA forfettaria |
| **Totale Anno 1** | **90** | | **€34.410** | **€0 upgrade (incluso)** |

> **Nota:** Stima conservativa: 10 vendite/mese a prezzo pieno (non 12-15). Le vendite POC e EA sono certe (scarcita' controllata). Le vendite a prezzo pieno sono la variabile.

### Proiezione 3 anni — P&L completo (Scenario A: partnership equity + revenue share)

| | **Anno 1** | **Anno 2** | **Anno 3** |
|---|-----------|-----------|-----------|
| **Nuove licenze** | 90 | 180 | 300 |
| **Base installata cumulativa** | 90 | 270 | 570 |
| | | | |
| **RICAVI LORDI** | | | |
| Licenze (a) | €34.410 | €80.820 | €134.700 |
| Upgrade annuale (b) | €0 | €4.356 | €13.600 |
| Inner Circle (c) ° | €0 | €0 | €8.970 |
| Masterclass singole (d) ° | €0 | €4.680 | €11.700 |
| Setup/onboarding | €1.500 | €5.000 | €10.000 |
| **Ricavi lordi totali** | **€35.910** | **€94.856** | **€178.970** |
| | | | |
| **COSTI VARIABILI — Revenue share Industry Partner** | | | |
| 20% su vendite da network (e) | €2.445 | €5.658 | €9.429 |
| 25% su Community PRO (f) | €0 | €1.089 | €3.400 |
| 25% su Inner Circle (g) | €0 | €0 | €2.243 |
| 30% su Masterclass (h) | €0 | €1.404 | €3.510 |
| **Totale revenue share partner** | **€2.445** | **€8.151** | **€18.582** |
| | | | |
| **RICAVI NETTI** (dopo revenue share) | **€33.465** | **€86.705** | **€160.388** |
| | | | |
| **COSTI FISSI OPERATIVI** | | | |
| Commercialista | €1.000 | €1.500 | €2.500 |
| Marketing (organico + ads) | €1.500 | €5.000 | €12.000 |
| Infrastruttura (hosting, tools, cert.) | €500 | €800 | €1.200 |
| Legale/admin (spot) | €1.000 | €2.000 | €3.000 |
| Ufficio | €0 | €4.800 | €6.000 |
| Tirocinante | €0 | €14.400 | €14.400 |
| Junior (tirocinante confermato) | €0 | €0 | €9.000 |
| **Totale costi fissi** | **€4.000** | **€28.500** | **€48.100** |
| | | | |
| **EBITDA** | **€29.465** | **€58.205** | **€112.288** |
| **Margine EBITDA** | **82%** | **61%** | **63%** |
| | | | |
| **TASSE + CONTRIBUTI** | | | |
| IRPEF 5% su 67% fatturato (i) | €1.203 | €3.178 | * |
| INPS ~26% su 67% fatturato (j) | €6.262 | €16.553 | * |
| **Totale fiscale** | **€7.465** | **€19.731** | * |
| | | | |
| **UTILE NETTO FOUNDER** | **€22.000** | **€38.474** | * |

#### Legenda calcoli P&L

| Riferimento | Formula |
|-------------|---------|
| (a) Licenze | N. licenze × prezzo di fase. Anno 1: 10×€149 + 20×€299 + 60×€449 = €34.410 |
| (b) Upgrade | Clienti idonei al rinnovo × €99 × tasso rinnovo (55% A2, 65% A3). Anno 1: €0 (incluso) |
| (c) Inner Circle | Membri × €299/anno. Attivo dal Anno 3: stimati 30 membri |
| (d) Masterclass | Sessioni vendute singolarmente a non-abbonati × €39 × partecipanti medi |
| (e) Rev. share vendite | 35% delle vendite totali attribuite al network partner × prezzo × 20% |
| (f) Rev. share PRO | Ricavi upgrade totali (b) × 25% |
| (g) Rev. share IC | Ricavi Inner Circle totali (c) × 25% |
| (h) Rev. share MC | Ricavi masterclass totali (d) × 30% |
| (i) IRPEF | Ricavi lordi (*) × 67% (coeff. redditivita') × 5% (aliquota startup) |
| (j) INPS | Ricavi lordi (*) × 67% × 26,07% (gestione separata 2026) |

(*) **Nota fiscale:** Nel regime forfettario, la base imponibile e' il fatturato lordo del founder. Se l'Industry Partner fattura autonomamente le sue prestazioni (masterclass, referral), quei ricavi non transitano dal P.IVA del founder e non concorrono alla base imponibile. Il P&L sopra assume prudenzialmente che tutto il fatturato transiti dal founder — il carico fiscale reale potrebbe essere leggermente inferiore. Da definire con il commercialista in base alla struttura contrattuale del rev. share.

° Inner Circle e Masterclass singole sono **stream proiettati, non ancora validati**. Senza di essi, i ricavi Anno 3 sarebbero €158.300 (anziche' €178.970) e l'EBITDA resterebbe comunque >€90K. Questi stream verranno validati durante l'Anno 2 con la community attiva.

**Anno 3 — Transizione fiscale post-forfettario:**

Se il fatturato supera €85.000 (previsto tra il mese 20 e 24), si esce dal regime forfettario. Le opzioni sono:

| Regime | Carico fiscale stimato | Pro | Contro |
|--------|----------------------|-----|--------|
| Ordinario P.IVA | ~35-40% su reddito netto | Deduzione costi, IVA a credito | Contabilita' ordinaria, costi commercialista |
| SRL | ~24% IRES + 26% dividendi | Responsabilita' limitata, credibilita' | Costi costituzione ~€2K, contabilita' |

**Stima impatto Anno 3:** Con EBITDA di €112K e carico fiscale ~35-38% (ordinario), l'utile netto stimato e' **€55.000-65.000**. Con SRL (IRES 24% + distribuzione parziale), l'utile netto disponibile e' simile ma con maggiore flessibilita' fiscale. Da pianificare con il commercialista entro il mese 18.

#### Come leggere il P&L: chi guadagna quanto

```
RICAVI LORDI = Tutto cio' che entra
      │
      ├──► Revenue share partner (costo VARIABILE: sale solo se i ricavi salgono)
      │         Anno 1: €2.445 (6,8%)    → il partner guadagna poco ma costruisce
      │         Anno 2: €8.151 (8,7%)    → la community genera ricavi, il partner cresce
      │         Anno 3: €18.582 (10,4%)  → masterclass + IC + upgrade = cash serio
      │
      ├──► Costi fissi operativi (stabili e prevedibili)
      │         Anno 1: €4.000   → solo founder, zero struttura
      │         Anno 2: €28.500  → ufficio + tirocinante
      │         Anno 3: €48.100  → team 3 persone
      │
      ├──► Tasse + contributi (proporzionali al fatturato)
      │         Anno 1: €7.465   → forfettario 5% + INPS
      │         Anno 2: €19.731  → forfettario 5% + INPS
      │
      └──► UTILE NETTO FOUNDER = cio' che resta in tasca
               Anno 1: €22.000
               Anno 2: €38.474
               Anno 3: stima €55-65K
```

### Dettaglio ricavi upgrade (componente ricorrente)

| Anno | Base installata | Idonei al rinnovo | Tasso rinnovo | Ricavo upgrade |
|------|----------------|-------------------|---------------|----------------|
| 1 | 90 | 0 (incluso nel primo anno) | — | €0 |
| 2 | 270 | 60+20 = 80* | 55% | 80 × €99 × 55% = **€4.356** |
| 3 | 570 | 260** | 65% | 260 × €99 × 65% = **€16.731** |

*Anno 2: solo le 60 licenze prezzo pieno del mese 7-12 Anno 1 + le 20 EA (scadono 2 anni inclusi solo nell'Anno 3).
**Anno 3: tutte le 180 nuove dell'Anno 2 + le 80 gia' idonee = 260 (meno i 10 Fondatori lifetime).

> La componente upgrade cresce geometricamente con la base installata. Dal Anno 4, con 570+ clienti e tasso 65-70%, il solo upgrade genera ~€37K-40K/anno di ricavo ricorrente — un "pavimento" che copre tutti i costi operativi.

### Cash flow

| Metrica | Valore | Calcolo |
|---------|--------|---------|
| Costi fissi mensili (Anno 1) | ~€330/mese | €4.000 / 12 mesi |
| Costi variabili mensili (Anno 1) | ~€200/mese | Revenue share medio su vendite |
| Break-even | **Mese 4** | Prima vendita EA a €299 > costi mensili €530 |
| Cash netto fine Anno 1 | **€22.000** | Ricavi - rev.share - costi fissi - tasse |
| Cash netto fine Anno 2 | **€60.474** cumulativo | Anno 1 + Anno 2 |
| Investimento esterno necessario | **€0** | Bootstrap autofinanziato |

**Il business e' profittevole dal primo mese di vendite reali.** Il revenue share al partner e' un costo variabile che cresce solo quando crescono i ricavi — non pesa mai su mesi a zero vendite. Non serve seed round per sopravvivere.

### Metriche chiave per milestone

| Milestone | Quando | Metrica |
|-----------|--------|---------|
| POC completata | Mese 3 | 10/10 Fondatori con dati reali, NPS >50 |
| P.IVA aperta | Mese 4 | Regime forfettario attivo |
| Early Adopter sold out | Mese 6 | 20/20 licenze, social proof doppia |
| Product-market fit | Mese 9 | 50+ clienti, NPS >40, referral organici |
| Fine Anno 1 | Mese 12 | 90 clienti, €24K netti, zero debito |
| Primo team | Mese 13 | Ufficio + tirocinante operativi |
| Upgrade validation | Mese 18 | Tasso rinnovo >50% (prova ricorrenza) |
| Soglia forfettario | Mese 20-24 | €85K fatturato → decisione SRL/ordinario |

---

## 10. Strategia Finanziaria

### Approccio: Bootstrap Anno 1, investimento opzionale dal Anno 2

FitManager non ha bisogno di un seed round per sopravvivere. Il modello perpetuo + licenza locale + zero costi cloud = **profittevole dal Mese 4**. L'Anno 1 si autofinanzia completamente.

Questo cambia radicalmente il rapporto con gli investitori: non siamo in cerca di sopravvivenza — siamo in cerca di **accelerazione**.

### Scenario A — Bootstrap puro (default)

| Anno | Ricavi lordi | Costi totali (*) | Utile netto | Crescita |
|------|-------------|-------------------|-------------|----------|
| 1 | €35.910 | €13.910 | **€22.000** | Organica, 90 clienti |
| 2 | €94.856 | €56.382 | **€38.474** | Ufficio + tirocinante |
| 3 | €178.970 | ~€115.000** | **€55-65K** | Team 3, scala |

(*) Costi totali = revenue share partner + costi fissi + tasse/contributi.
(**) Anno 3 stima con regime ordinario/SRL (carico fiscale superiore al forfettario).

**Pro:** Pieno controllo, zero diluizione, decisioni rapide.
**Contro:** Crescita piu' lenta, no budget per fiere/ads, tutto sulle spalle del founder.

### Scenario B — Bootstrap Anno 1 + investimento di accelerazione Anno 2

Se i dati della POC e dell'Anno 1 confermano il modello (90+ clienti, NPS >40, tasso rinnovo upgrade misurabile), si apre a un investimento mirato.

**Ask (dal Anno 2):** €30.000-50.000

| Uso dei fondi | Importo | Cosa accelera |
|---------------|---------|---------------|
| Marketing strutturato (ads, fiere, content) | €15.000-25.000 | Da 15 a 25-30 vendite/mese |
| Team (2o tirocinante + collaboratori contenuti) | €10.000-15.000 | Community, masterclass, supporto |
| Legale (SRL, GDPR audit, contratti) | €5.000-10.000 | Struttura societaria per la scala |

**Pro:** Accelera la crescita con dati reali gia' validati (non promesse). L'investitore entra a rischio bassissimo.
**Contro:** Diluizione (minima su un business gia' profittevole).

### Perche' un investitore dovrebbe entrare

Un investitore nel Anno 2 di FitManager non sta scommettendo su un'idea — sta investendo in:
- Un business **gia' profittevole** (€24K netti Anno 1)
- Con **90+ clienti reali** e dati di retention misurabili
- In un mercato da **€3,1 miliardi** con zero competitor nel quadrante locale+scienza
- Con un costo marginale per cliente di **€0** (modello locale)
- Dove €30-50K di investimento possono raddoppiare il tasso di crescita

### Termini suggeriti (se Scenario B)

- **Strumento:** SAFE o convertibile
- **Valuation cap:** Da definire in base alla traction Anno 1 (indicativamente €300-500K pre-money se 90 clienti e €35K ricavi validati)
- **Discount:** 20% sul prossimo round
- **Diritti investitore:** Informativa trimestrale, advisory informale

---

## 11. Analisi dei Rischi

| Rischio | Probabilita' | Impatto | Mitigazione |
|---------|-------------|---------|-------------|
| **POC non valida il modello** | Media | Alto | Lo scopriamo con 10 persone e €200, non con 100 e €50K. Pivot rapido e a basso costo. |
| **Adozione lenta post-POC** | Media | Medio | Con costi a €330/mese, anche 3 vendite/mese coprono i costi. Il business non muore. |
| **Resistenza al prezzo €449** | Media | Medio | Confronto annualizzato vs SaaS (€449 una volta < €480/anno Mangofit). Garanzia 30gg. |
| **Basso tasso rinnovo upgrade** | Media | Alto | Masterclass + template + community = valore percepito €650 per €99. Se <40%, rivedere pricing. |
| **Superamento soglia €85K forfettario** | Alta | Medio | Buon problema: pianificare transizione a ordinario/SRL con commercialista dal mese 18. |
| **Single founder risk** | Alta | Alto | Industry Partner operativo dalla POC mitiga il lato commerciale. Release pipeline automatizzata riduce il carico dev. Tirocinante dal mese 13 per operativita'. Se il founder si ferma >2 settimane, il partner puo' gestire community e vendite. Il prodotto installato continua a funzionare (locale). |
| **Tutte le proiezioni sono non validate** | Alta | Medio | Nessun PT ha ancora pagato. La POC e' progettata esattamente per trasformare ipotesi in dati entro 90 giorni. Nessuna spesa significativa avviene prima della validazione POC. |
| **Competitor SaaS aggressivo** | Media | Basso | Il quadrante locale+scienza e' vuoto. Riscrivere un SaaS in locale costa ordini di grandezza di piu'. |

### Scenario pessimistico (vendite -50%)

| | Pessimistico | Base | Formula |
|---|-------------|------|---------|
| Licenze Anno 1 | 45 | 90 | 50% delle vendite base |
| Ricavi lordi | €17.500 | €35.910 | |
| Revenue share partner | €1.200 | €2.445 | Proporzionale ai ricavi |
| Costi fissi | €4.000 | €4.000 | Invariati (zero struttura) |
| Tasse + INPS | €3.600 | €7.465 | ~20,8% del fatturato |
| **Utile netto founder** | **€8.700** | **€22.000** | |
| **Guadagno partner** | **€1.200 cash** | **€2.445 cash** | + equity |

**Il business resta profittevole anche vendendo meta'.** Con costi fissi a €330/mese, bastano 1-2 vendite/mese per coprirli. Zero debito, zero investitori da rimborsare. Il partner guadagna meno, ma il revenue share e' proporzionale — nessuno perde piu' di quanto entra.

### Scenario ottimistico (vendite +50%)

| | Ottimistico | Base | Formula |
|---|------------|------|---------|
| Licenze Anno 1 | 135 | 90 | 150% delle vendite base |
| Ricavi lordi | €54.000 | €35.910 | |
| Revenue share partner | €3.700 | €2.445 | Proporzionale ai ricavi |
| Costi fissi | €4.000 | €4.000 | Invariati |
| Tasse + INPS | €11.200 | €7.465 | ~20,8% del fatturato |
| **Utile netto founder** | **€35.100** | **€22.000** | |
| **Guadagno partner** | **€3.700 cash** | **€2.445 cash** | + equity piu' preziosa |

- Superamento soglia forfettario possibile gia' nell'Anno 1 → transizione anticipata a ordinario/SRL
- Team anticipato al mese 10 (ufficio + tirocinante)
- Partner motivato: il suo revenue share cresce con le vendite

---

## 12. Appendici

### A. Metriche prodotto attuali

| Metrica | Valore |
|---------|--------|
| Versione | 1.0.4 |
| LOC totali | ~45.000 (17K api + 18K frontend + 10K core) |
| Test | 326 pytest + 69 vitest = 395 |
| Esercizi in catalogo | 500 attivi |
| Relazioni esercizio | 940 (progressioni + regressioni + varianti) |
| Alimenti CREA | 880 attivi |
| Ricette pietanze | 210 (95% copertura) |
| Template dieta LARN | 12 (8 con dieta completa) |
| Condizioni cliniche | 47 |
| Safety rules | 80 pattern |
| Dimensione installer | 83 MB |

### B. Roadmap prodotto

| Q | Feature | Impatto |
|---|---------|---------|
| Q2 2026 | Lancio pubblico + beta program | Primi clienti |
| Q3 2026 | Mobile-responsive improvements | Usabilita' in palestra |
| Q4 2026 | AI suggestions (Ollama) | Differenziazione premium |
| Q1 2027 | Multi-operatore | Espansione a centri |
| Q2 2027 | Cloud sync opzionale (hybrid) | Richiesta mercato |
| Q3 2027 | Valutazione cross-platform (web-based) | Sblocco macOS + tablet (15-20% mercato escluso) |
| Q4 2027 | Espansione iberica | Nuovo mercato |

### C. Riferimenti di mercato

- Mercato fitness Italia: €3,1 miliardi (2024), +10% YoY
- Centri fitness: ~8.000 attivi, 5 milioni iscritti
- Media PT per struttura: 23,5
- 75% PT europei sono lavoratori autonomi
- Domanda PT qualificati: +35% in 2 anni (ISTAT 2023)
- Gym management software globale: $2,03B (2025), CAGR 10-18%
- Fitness training software globale: $12,45B (2026), CAGR 15,8%

---

### D. Glossario acronimi e termini

| Acronimo/Termine | Significato |
|-----------------|------------|
| **ARPU** | Average Revenue Per User — ricavo medio per utente |
| **ATECO** | Classificazione delle attivita' economiche (codice italiano per tipo di lavoro) |
| **B2B** | Business-to-Business — vendita tra aziende/professionisti |
| **B2C** | Business-to-Consumer — vendita al consumatore finale |
| **CAC** | Customer Acquisition Cost — costo per acquisire un nuovo cliente |
| **CAGR** | Compound Annual Growth Rate — tasso di crescita annuo composto |
| **CONI** | Comitato Olimpico Nazionale Italiano |
| **CREA** | Consiglio per la ricerca in agricoltura e l'analisi dell'economia agraria (fonte dati alimenti italiani) |
| **CRM** | Customer Relationship Management — sistema di gestione clienti |
| **DnD** | Drag and Drop — interazione trascina e rilascia nell'interfaccia |
| **EBITDA** | Earnings Before Interest, Taxes, Depreciation and Amortization — utile operativo lordo |
| **EMG** | Elettromiografia — misurazione dell'attivita' muscolare |
| **FK** | Foreign Key — chiave esterna nel database |
| **GDPR** | General Data Protection Regulation — regolamento europeo sulla privacy |
| **GTM** | Go-to-Market — strategia di lancio sul mercato |
| **HW** | Hardware |
| **IC** | Inner Circle — livello premium della community |
| **INPS** | Istituto Nazionale della Previdenza Sociale |
| **IRES** | Imposta sul Reddito delle Societa' (24% per SRL) |
| **IRPEF** | Imposta sul Reddito delle Persone Fisiche |
| **ISSA** | International Sports Sciences Association |
| **LARN** | Livelli di Assunzione di Riferimento di Nutrienti (standard nutrizionale italiano) |
| **LOC** | Lines of Code — righe di codice sorgente |
| **LTV** | Lifetime Value — valore totale di un cliente nel tempo |
| **MAV** | Maximum Adaptive Volume — volume massimo di allenamento adattivo |
| **MC** | Masterclass |
| **MEV** | Minimum Effective Volume — volume minimo efficace di allenamento |
| **MRV** | Maximum Recoverable Volume — volume massimo recuperabile |
| **NPS** | Net Promoter Score — indice di soddisfazione (-100 a +100; >50 = eccellente) |
| **P&L** | Profit & Loss — conto economico (ricavi meno costi) |
| **P.IVA** | Partita IVA — codice fiscale per lavoratori autonomi in Italia |
| **POC** | Proof of Concept — esperimento di validazione con utenti reali |
| **PRO** | Livello Community PRO (= upgrade annuale €99) |
| **PT** | Personal Trainer |
| **ROI** | Return on Investment — ritorno sull'investimento |
| **SAFE** | Simple Agreement for Future Equity — strumento di investimento pre-seed |
| **SAM** | Serviceable Available Market — mercato raggiungibile |
| **SOM** | Serviceable Obtainable Market — mercato ottenibile realisticamente |
| **SRL** | Societa' a Responsabilita' Limitata |
| **SSoT** | Single Source of Truth — fonte unica di verita' per i dati |
| **TAM** | Total Addressable Market — mercato totale indirizzabile |
| **WAL** | Write-Ahead Logging — modalita' di scrittura del database SQLite |
| **WTP** | Willingness to Pay — disponibilita' a pagare |
| **YoY** | Year over Year — confronto anno su anno |

---

*Documento v3.2, 23 marzo 2026. Modello bootstrap: licenza perpetua + upgrade annuale + POC 90gg + P.IVA forfettaria Anno 1. Dati di mercato basati su fonti pubbliche (ISTAT, Les Mills, Business Research Insights, Polaris Market Research). Dati fiscali: regime forfettario 2026 (ATECO 62.10.00, coefficiente 67%, aliquota startup 5%).*

---

**Contatti:**
Giacomo Verardo
[email da definire]
[telefono da definire]

---

Sources:
- [Analisi mercato fitness Italia 2026](https://ilmiobusinessplan.com/blogs/news/mercato-fitness)
- [Mercato fitness Italia 2025 — Les Mills](https://www.lesmills.it/il-mercato-del-fitness-in-italia-2025-tendenze-sfide-e-opportunita/)
- [Fitness Italia 2025 — Fitness Lab](https://www.fitness-lab.it/fitness-in-italia-2025-un-settore-in-corsa-tra-innovazione-community-e-nuove-sfide/)
- [Fitness Trend 2026 — Managify](https://www.managify.it/2025/12/22/fitness-trend-2026-ridisegnando-il-futuro-del-fitness/)
- [Mangofit — Software PT Italia](https://www.mangofitapp.com/)
- [Gym Management Software Market — 360iResearch](https://www.360iresearch.com/library/intelligence/gym-management-software)
- [Fitness Training Software Market — Business Research Insights](https://www.businessresearchinsights.com/market-reports/fitness-training-software-market-107349)
- [Fitness App Market — Polaris](https://www.polarismarketresearch.com/industry-analysis/fitness-app-market)
- [P.IVA Personal Trainer — Fiscozen](https://www.fiscozen.it/guide/partita-iva-personal-trainer/)
- [PT CONI — FIF](https://www.fif.it/diventare-personal-trainer-coni.html)
- [Regime Forfettario Sviluppatori — Flextax](https://flextax.it/regime-forfettario-per-sviluppatori/)
- [Regime Forfettario 2026 — Centro Fiscale](https://centrofiscale.com/regime-forfettario-2026/)
- [P.IVA Sviluppatore Software — Fidocommercialista](https://fidocommercialista.it/partita-iva-sviluppatore-software)
- [Tirocinio Extracurriculare — JetHR](https://www.jethr.com/risorse/tirocinante-come-funziona-e-quanto-pagarlo/)
- [Stipendio Stage 2026 — Money.it](https://www.money.it/stipendio-durante-stage-tirocinio-quanto-spetta-importo-indennita)

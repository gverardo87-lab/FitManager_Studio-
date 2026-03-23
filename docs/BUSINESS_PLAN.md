# Business Plan — FitManager Studio+

**Versione:** 3.0 — 23 marzo 2026
**Autore:** Gianluca Vera
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
3. **AI come moltiplicatore:** Il trend 2026 e' "AI + personalizzazione". FitManager ha gia' l'architettura pronta (Langchain + Ollama dormiente).
4. **Privacy post-GDPR:** I trainer gestiscono dati sanitari (anamnesi, patologie, misurazioni). Il cloud generico non offre garanzie adeguate.

### Dimensione del mercato

| Livello | Stima | Metodologia |
|---------|-------|-------------|
| **TAM** (Total Addressable Market) | €360M/anno | ~120.000 professionisti fitness P.IVA Italia × €250/mese software |
| **SAM** (Serviceable Available Market) | €43M/anno | ~15.000 trainer tech-ready (certificati CONI, <45 anni, urbani) × €240/anno |
| **SOM** (Serviceable Obtainable Market) | €720K/anno Anno 3 | 1.000 clienti paganti × €60/mese piano Pro |

Il TAM e' calcolato bottom-up: il mercato fitness italiano vale €3,1 miliardi (2024), con ~8.000 centri e una media di 23,5 trainer per struttura. Aggiungendo freelance e chinesiologi, la stima conservativa e' 100.000-150.000 operatori.

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
| **CAC** | €120 | Organico + demo + community |
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

### Fase 2 — Prezzo pieno + crescita organica (Mesi 7-12): 30 → 130 clienti

| Azione | Canale | Obiettivo |
|--------|--------|-----------|
| Webinar mensile | Demo live + Q&A, garanzia 30gg | 10-20 partecipanti/webinar |
| Referral program | Fondatore/EA porta un amico → sconto €50 per l'amico | Viralita' organica |
| Content marketing | Blog + LinkedIn + gruppi FB in italiano | SEO long-tail |
| Partnership formatori | ISSA, FIF, ASI, accademie | Accesso a neoqualificati |
| Calcolatore ROI | Sul sito: "quante ore perdi in admin?" | Conversione razionale |

**Messaggio prezzo pieno:** *"I tuoi dati, il tuo PC, la tua scienza. €449 una volta, per sempre. Zero abbonamenti."*

**Garanzia:** Soddisfatto o rimborsato 30 giorni — zero rischio percepito su €449.

### Fase 3 — Scala (Mesi 13-36): 130 → 800 clienti

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

### Anno 1 — Solo founder (zero costi strutturali)

**Gianluca Vera** — Fondatore, sviluppatore e product owner
- Ha costruito FitManager Studio+ da zero in ~6 mesi
- Stack completo: Python/FastAPI + Next.js/React + SQLite + AI
- 45.000+ LOC, 395 test, 3 database, 5 motori scientifici
- Copre: sviluppo, supporto, community, marketing, vendite

**Principio Anno 1:** Nessun costo fisso per personale. Il founder fa tutto. Il prodotto e' costruito, il focus e' vendere e validare. L'unico "costo" e' il tempo del founder.

### Strategic Advisor (in definizione)

Chinesiologo senior con 20+ anni di esperienza, ex dirigente TechnoGym, network ai vertici del settore fitness italiano. Ruolo:
- Validazione prodotto e posizionamento
- Selezione dei 10 Fondatori per la POC
- Masterclass e contenuti per la community
- Accesso al network per go-to-market

Compenso: equity advisor (1-3%) e/o revenue share su community, oppure fee per contenuto. Da definire in base al livello di coinvolgimento.

### Anno 2 — Primo team minimo

| Ruolo | Costo/mese | Quando | Cosa fa |
|-------|-----------|--------|---------|
| **Tirocinante** (extracurriculare) | €1.200 | Mese 13 | Customer success, community, onboarding, contenuti |
| **Ufficio** (piccolo, condiviso) | €350-500 | Mese 13 | Base operativa, demo in presenza, credibilita' |

**Costo aggiuntivo Anno 2:** ~€18.000-20.400/anno (tirocinante) + ~€4.200-6.000 (ufficio) = **~€22.200-26.400**

### Anno 3 — Crescita misurata

| Ruolo | Costo/mese | Quando | Cosa fa |
|-------|-----------|--------|---------|
| **Tirocinante → junior** (se confermato) | €1.500 | Mese 25 | Customer success + community management |
| **Secondo tirocinante** (opzionale) | €1.200 | Mese 30 | Marketing content + social |
| **Ufficio** | €500 | Continuo | Base operativa |

### Advisory board (da costruire progressivamente)

- Chinesiologo/PT senior (in definizione — validazione prodotto e network)
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

### Proiezione 3 anni (P&L realistico)

| | **Anno 1** | **Anno 2** | **Anno 3** |
|---|-----------|-----------|-----------|
| **Nuove licenze** | 90 | 180 | 300 |
| **Base installata cumulativa** | 90 | 270 | 570 |
| | | | |
| **RICAVI** | | | |
| Licenze | €34.410 | €80.820 | €134.700 |
| Upgrade annuale | €0 | €4.850 | €13.600 |
| Setup/onboarding | €1.500 | €5.000 | €10.000 |
| **Ricavi totali** | **€35.910** | **€90.670** | **€158.300** |
| | | | |
| **COSTI OPERATIVI** | | | |
| Commercialista | €1.000 | €1.500 | €2.500 |
| Marketing (organico + ads) | €1.500 | €5.000 | €12.000 |
| Infrastruttura (hosting, tools, cert.) | €500 | €800 | €1.200 |
| Legale/admin (spot) | €1.000 | €2.000 | €3.000 |
| Ufficio | €0 | €4.800 (€400×12) | €6.000 (€500×12) |
| Tirocinante | €0 | €14.400 (€1.200×12) | €14.400 |
| Junior (tirocinante confermato) | €0 | €0 | €9.000 (€1.500×6) |
| Advisor (fee/contenuti) | €0 | €2.000 | €4.000 |
| **Costi operativi totali** | **€4.000** | **€30.500** | **€52.100** |
| | | | |
| **EBITDA** | **€31.910** | **€60.170** | **€106.200** |
| **Margine EBITDA** | **89%** | **66%** | **67%** |
| | | | |
| **TASSE + CONTRIBUTI** | | | |
| IRPEF 5% su 67% fatturato | €1.203 | €3.037 | * |
| INPS ~26% su 67% fatturato | €6.262 | €15.815 | * |
| **Totale fiscale** | **€7.465** | **€18.852** | * |
| | | | |
| **UTILE NETTO** | **€24.445** | **€41.318** | * |

*Anno 3: se il fatturato supera €85.000, si esce dal forfettario. Sara' necessario valutare con il commercialista la transizione a regime ordinario o SRL. Il carico fiscale aumentera', ma il volume di utile netto resta ampiamente positivo.

### Dettaglio ricavi upgrade (componente ricorrente)

| Anno | Base installata | Idonei al rinnovo | Tasso rinnovo | Ricavo upgrade |
|------|----------------|-------------------|---------------|----------------|
| 1 | 90 | 0 (incluso nel primo anno) | — | €0 |
| 2 | 270 | 60+20 = 80* | 55% | 80 × €99 × 55% = **€4.356** |
| 3 | 570 | 260** | 65% | 260 × €99 × 65% = **€16.731** |

*Anno 2: solo le 60 licenze prezzo pieno del mese 7-12 Anno 1 + le 20 EA (scadono 2 anni inclusi solo nell'Anno 3).
**Anno 3: tutte le 180 nuove dell'Anno 2 + le 80 gia' idonee = 260 (meno i 10 Fondatori lifetime).

> La componente upgrade cresce geometricamente con la base installata. Dal Anno 4, con 570+ clienti e tasso 65-70%, il solo upgrade genera ~€37K-40K/anno di ricavo ricorrente — un "pavimento" che copre tutti i costi operativi.

### Confronto: costi v2.0 (irrealistici) vs v3.0 (reali)

| Voce | v2.0 Anno 1 | v3.0 Anno 1 | Delta |
|------|-------------|-------------|-------|
| Co-founder commerciale | €24.000 | €0 | -€24.000 |
| Customer success | €0 | €0 | €0 |
| Marketing | €10.000 | €1.500 | -€8.500 |
| Infrastruttura | €3.000 | €500 | -€2.500 |
| Legale/admin | €5.000 | €1.000 | -€4.000 |
| **Totale costi** | **€42.000** | **€4.000** | **-€38.000** |
| **EBITDA** | €15.370 | **€31.910** | **+€16.540** |

Il margine passa dal 27% al **89%** semplicemente eliminando costi che non servono nell'Anno 1.

### Cash flow

| Metrica | Valore |
|---------|--------|
| Costi fissi mensili (Anno 1) | ~€330/mese |
| Break-even | **Mese 4** (prima vendita EA a €299 copre gia' i costi mensili) |
| Cash in pocket fine Anno 1 | ~€24.000 (netto dopo tasse) |
| Cash in pocket fine Anno 2 | ~€65.000 cumulativo |
| Necessita' di investimento esterno | **€0 per Anno 1-2** (bootstrap autofinanziato) |

**Il business e' profittevole dal primo mese di vendite reali.** Non serve seed round per sopravvivere. Un eventuale investimento serve solo per accelerare (marketing, fiere, team), non per restare in vita.

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

| Anno | Ricavi | Costi | Utile netto | Crescita |
|------|--------|-------|-------------|----------|
| 1 | €35.910 | €11.465 | €24.445 | Organica, 90 clienti |
| 2 | €90.670 | €49.352 | €41.318 | Ufficio + tirocinante |
| 3 | €158.300 | ~€85.000* | ~€73.000* | Team 3, scala |

*Stima con regime ordinario/SRL (carico fiscale superiore al forfettario).

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
| **Single founder burnout** | Alta | Alto | Anno 1 lean by design. Tirocinante dal mese 13 delega operativa. Community come supporto scalabile. |
| **Competitor SaaS aggressivo** | Media | Basso | Il quadrante locale+scienza e' vuoto. Riscrivere un SaaS in locale costa ordini di grandezza di piu'. |

### Scenario pessimistico (vendite -50%)

Se l'adozione e' 50% inferiore alle proiezioni:
- Anno 1: 45 licenze → ~€17.500 ricavi, costi €4.000 → **utile netto ~€10.000**
- Il business resta profittevole anche vendendo meta'
- Con 45 clienti attivi, il tasso di rinnovo e' comunque misurabile
- Zero debito, zero investitori da rimborsare, zero runway problem

**Questo e' il vantaggio strutturale del bootstrap a costi zero:** non esiste uno scenario in cui il business "muore" per mancanza di cash nell'Anno 1. Il worst case e' crescere piu' lentamente.

### Scenario ottimistico (vendite +50%)

- Anno 1: 135 licenze → ~€54K ricavi, utile netto ~€36K
- Superamento soglia forfettario gia' nell'Anno 1 → transizione anticipata
- Team dal mese 10 (anticipo ufficio + tirocinante)
- Investitore attratto da traction forte gia' nel Anno 1

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
| Q3 2027 | Espansione iberica | Nuovo mercato |

### C. Riferimenti di mercato

- Mercato fitness Italia: €3,1 miliardi (2024), +10% YoY
- Centri fitness: ~8.000 attivi, 5 milioni iscritti
- Media PT per struttura: 23,5
- 75% PT europei sono lavoratori autonomi
- Domanda PT qualificati: +35% in 2 anni (ISTAT 2023)
- Gym management software globale: $2,03B (2025), CAGR 10-18%
- Fitness training software globale: $12,45B (2026), CAGR 15,8%

---

*Documento v3.0, 23 marzo 2026. Modello bootstrap: licenza perpetua + upgrade annuale + POC 90gg + P.IVA forfettaria Anno 1. Dati di mercato basati su fonti pubbliche (ISTAT, Les Mills, Business Research Insights, Polaris Market Research). Dati fiscali: regime forfettario 2026 (ATECO 62.10.00, coefficiente 67%, aliquota startup 5%).*

---

**Contatti:**
Gianluca Vera
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

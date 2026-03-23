# Business Plan — FitManager Studio+

**Versione:** 2.0 — 22 marzo 2026
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

**Modello commerciale:** Licenza perpetua singola (€149–€449) + upgrade annuale opzionale (€99/anno). Lancio a scarcita' controllata: 10 licenze Fondatore, poi 20 Early Adopter, poi prezzo pieno.

**Ask:** €150.000 seed round per validazione di mercato, primi 100 clienti e team minimo.

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

### Fase 1 — Fondatori + Early Adopter (Mesi 1-4): 0 → 30 clienti

**Obiettivo:** Vendere le 10 licenze Fondatore + avviare le 20 Early Adopter. Costruire community e social proof.

| Azione | Canale | Obiettivo | Conversione attesa |
|--------|--------|-----------|-------------------|
| Waiting list (senza deposito) | Landing page + social | 100+ iscritti | 10-15% → acquisto |
| Demo 1:1 (20 min) | Zoom con screen share | 5 demo/settimana | 40% → acquisto |
| Content pre-lancio | LinkedIn + gruppi Facebook PT | Awareness + autorevolezza | Brand building |
| Video "dietro le quinte" | YouTube/Instagram | Mostrare il prodotto reale | Trust building |
| Countdown pubblico | Landing page | "7 posti rimasti su 10" (reale) | Urgenza |

**Target primario:** Personal trainer 25-45 anni, P.IVA, certificato CONI, area urbana (Milano, Roma, Torino, Bologna, Firenze).

**Messaggio Fondatori:** *"10 posti per chi vuole costruire il futuro del fitness con noi. €149, upgrade a vita, accesso diretto."*

**Messaggio Early Adopter:** *"I Fondatori sono dentro. 20 posti a €299 con 2 anni di aggiornamenti. Poi si chiude."*

### Fase 2 — Prezzo pieno + crescita organica (Mesi 5-12): 30 → 130 clienti

| Azione | Canale | Obiettivo |
|--------|--------|-----------|
| Testimonial Fondatori | Video brevi "ecco come uso FitManager" | Social proof reale |
| Webinar mensile | Demo live + Q&A, CTA con garanzia 30gg | 10-20 partecipanti/webinar |
| Referral program | Fondatore porta un amico → sconto €50 per l'amico | Viralita' organica |
| Partnership formatori | ISSA, FIF, ASI, accademie | Accesso a neoqualificati |
| SEO + content | Blog tutorial in italiano | Long-tail "gestionale personal trainer" |
| Calcolatore ROI | Sul sito: "quante ore perdi in admin?" | Conversione razionale |

**Messaggio prezzo pieno:** *"I tuoi dati, il tuo PC, la tua scienza. €449 una volta, per sempre. Zero abbonamenti."*

**Garanzia:** Soddisfatto o rimborsato 30 giorni — zero rischio percepito su €449.

### Fase 3 — Scala (Mesi 13-36): 130 → 800 clienti

- Presenza a fiere di settore (RiminiWellness, ForumClub)
- Case study e testimonial video strutturati
- Google Ads su keyword transazionali
- Affiliate program per trainer influencer
- Moduli AI attivati (differenziazione premium)
- Espansione a chinesiologi clinici e fisioterapisti
- Valutazione white-label per centri fitness
- Espansione geografica (Spagna, mercati simili)

---

## 7. Operations Plan

### Tecnologia

| Componente | Stato | Costo |
|------------|-------|-------|
| Sviluppo software | Completato (v1.0.4) | Sweat equity |
| Hosting sito/landing | Da attivare | €20/mese |
| CI/CD (GitHub Actions) | Attivo | Free tier |
| Code signing certificate | Da acquistare | €200/anno |
| Distribuzione installer | GitHub Releases / sito | Free |
| Supporto | Email + ticket system | €50/mese |

### Infrastruttura minima

- **Zero server:** il software gira in locale. Nessun costo cloud per utente.
- **Costo marginale per cliente ≈ €0:** nessun hosting, nessun DB cloud, nessun bandwidth.
- **Supporto:** knowledge base + email. Scalabile con community forum.

### Processi chiave

1. **Release pipeline:** 5 fasi automatizzate (preflight, build, verify, seal, tag) — gia' implementato.
2. **Aggiornamento cataloghi:** Seed idempotente, upgrade non distruttivo.
3. **Licenza:** RSA 2048 + JWT RS256 + hardware binding. Generazione via CLI.
4. **Backup/restore:** Un file `.db` copiabile. Recovery = rimpiazzare il file.

---

## 8. Team

### Fondatore

**Gianluca Vera** — Sviluppatore e product owner
- Ha costruito FitManager Studio+ da zero in ~6 mesi
- Stack completo: Python/FastAPI + Next.js/React + SQLite + AI
- 45.000+ LOC, 395 test, 3 database, 5 motori scientifici
- Visione: rendere la scienza dell'allenamento accessibile ai professionisti

### Posizioni chiave da coprire

| Ruolo | Priorita' | Quando | Profilo |
|-------|-----------|--------|---------|
| **Co-founder commerciale** | CRITICA | Subito | Sales + marketing fitness, rete nel settore |
| **UX/UI Designer** | ALTA | Mese 3 | Design system, mobile, onboarding |
| **Customer Success** | ALTA | Mese 6 | Supporto trainer, onboarding, feedback loop |
| **Developer backend** | MEDIA | Mese 9 | Python, API, AI/ML |
| **Growth marketer** | MEDIA | Mese 12 | SEO, content, community |

### Advisory board (da costruire)

- Chinesiologo/PT con pratica attiva (validazione prodotto)
- Imprenditore fitness con esperienza di scala (go-to-market)
- Esperto SaaS/licensing italiano (modello commerciale)
- Legale GDPR/privacy (compliance dati sanitari)

---

## 9. Proiezioni Finanziarie

### Ipotesi chiave

- **Licenza perpetua:** €149 (10 Fondatori) → €299 (20 Early Adopter) → €449 (prezzo pieno)
- **Upgrade annuale:** €99/anno, incluso nel primo anno. Tasso rinnovo: 55% Anno 2, 65% Anno 3
- **Fondatori:** upgrade lifetime (mai €99/anno) — costo: mancato ricavo su 10 utenti
- **CAC:** €100 Anno 1 (organico + demo), €130 Anno 2 (+ ads), €150 Anno 3 (scala)
- **Vendite:** ~10/mese Anno 1, ~20/mese Anno 2, ~30/mese Anno 3

### Dettaglio vendite Anno 1

| Periodo | Licenze | Prezzo | Ricavo licenze | Ricavo upgrade |
|---------|---------|--------|----------------|----------------|
| Mese 1 (Fondatori) | 10 | €149 | €1.490 | €0 (lifetime) |
| Mesi 2-4 (Early Adopter) | 20 | €299 | €5.980 | €0 (2 anni inclusi) |
| Mesi 5-12 (Prezzo pieno) | 100 | €449 | €44.900 | €0 (1 anno incluso) |
| **Totale Anno 1** | **130** | | **€52.370** | **€0** |

### Proiezione 3 anni (P&L)

| | **Anno 1** | **Anno 2** | **Anno 3** |
|---|-----------|-----------|-----------|
| **Nuove licenze** | 130 | 240 | 360 |
| **Base installata cumulativa** | 130 | 370 | 730 |
| | | | |
| **Ricavi licenze** | €52.370 | €107.760 | €161.640 |
| **Ricavi upgrade** | €0 | €14.850 | €33.150 |
| Setup/onboarding | €5.000 | €12.000 | €20.000 |
| **Ricavi totali** | **€57.370** | **€134.610** | **€214.790** |
| | | | |
| **Costi** | | | |
| Sviluppo (founder) | €0 (sweat) | €36.000 | €60.000 |
| Co-founder commerciale | €24.000 | €36.000 | €48.000 |
| Marketing | €10.000 | €25.000 | €45.000 |
| Infrastruttura | €3.000 | €5.000 | €8.000 |
| Customer success | €0 | €18.000 | €30.000 |
| Legale/admin | €5.000 | €8.000 | €10.000 |
| **Costi totali** | **€42.000** | **€128.000** | **€201.000** |
| | | | |
| **EBITDA** | **€15.370** | **€6.610** | **€13.790** |
| **Margine EBITDA** | 27% | 5% | 6% |

**Nota:** Il margine si comprime in Anno 2-3 perche' i costi team crescono (assunzioni). Il ricavo upgrade cresce con la base installata e diventa significativo dal Anno 3+. Il modello diventa molto profittevole dal Anno 4 quando la base installata supera le 1.000 unita' e il "pavimento" di upgrade supera €60K/anno.

### Dettaglio ricavi upgrade (componente ricorrente)

| Anno | Base installata | Idonei al rinnovo | Tasso rinnovo | Ricavo upgrade |
|------|----------------|-------------------|---------------|----------------|
| 1 | 130 | 0 (incluso) | — | €0 |
| 2 | 370 | 150* | 55% | €14.850 × 60% = ~€8.200** |
| 3 | 730 | 370 | 65% | €33.150 × 65% = ~€21.500** |

*Solo chi ha esaurito l'anno incluso (100 licenze prezzo pieno del mese 5-12 Anno 1 + 20 Early Adopter).
**I Fondatori (10) non pagano mai upgrade.

> **Nota conservativa:** i numeri sopra usano stime prudenti. Il ricavo upgrade reale dipende dal tasso di rinnovo effettivo. Abbiamo usato il 55-65% (benchmark software perpetuo: 50-70%).

### Cash flow e runway

| Metrica | Valore |
|---------|--------|
| Burn rate mensile (Anno 1) | ~€3.500 |
| Ricavo medio mensile (Anno 1) | ~€4.780 |
| Break-even | **Mese 5-6** (dopo vendite prezzo pieno) |
| Runway con €150K seed | **36+ mesi** anche nello scenario pessimistico |
| Cash positive | **Anno 1** (il modello perpetuo genera upfront) |

**Vantaggio chiave del modello perpetuo:** il ricavo arriva subito (€449 upfront vs €29-69/mese del SaaS). Questo accelera drasticamente il break-even.

### Metriche chiave per milestone

| Milestone | Quando | Metrica |
|-----------|--------|---------|
| Fondatori venduti | Mese 1 | 10/10 licenze, community attiva |
| Early Adopter venduti | Mese 4 | 20/20 licenze, primi testimonial |
| Product-market fit | Mese 8 | 80+ clienti, NPS >40 |
| Base installata 100 | Mese 10 | Tasso rinnovo upgrade misurabile |
| Anno 2 scala | Mese 18 | 300+ clienti, primo ricavo upgrade |
| Serie A ready | Mese 24 | 370+ clienti, upgrade tasso >55%, team 4 |

---

## 10. Richiesta di Finanziamento

### L'Ask: €150.000 Seed

| Uso dei fondi | Importo | % |
|---------------|---------|---|
| **Go-to-market e marketing** | €50.000 | 33% |
| **Team (co-founder + CS)** | €45.000 | 30% |
| **Sviluppo prodotto** | €25.000 | 17% |
| **Legale e compliance** | €15.000 | 10% |
| **Buffer operativo** | €15.000 | 10% |

### Cosa abilita questo round

1. **Validazione di mercato:** Primi 100 clienti paganti in 12 mesi
2. **Team minimo:** Co-founder commerciale + customer success part-time
3. **Code signing + compliance:** Certificato, GDPR audit, contratti licenza
4. **Marketing strutturato:** Landing page, content, demo, presenza fiere
5. **Runway 40 mesi:** Tempo sufficiente per raggiungere break-even senza pressione

### Milestones per il seed

| # | Milestone | Target | Quando |
|---|-----------|--------|--------|
| 1 | Fondatori | 10/10 licenze vendute, community attiva | Mese 1 |
| 2 | Early Adopter | 20/20 licenze, primi testimonial | Mese 4 |
| 3 | Product-market fit | 80+ clienti, NPS >40 | Mese 8 |
| 4 | Base 130 | 130 clienti, primo anno completato | Mese 12 |
| 5 | Upgrade validation | Tasso rinnovo upgrade >50% | Mese 18 |
| 6 | Serie A ready | 370+ clienti, ricavo upgrade ricorrente | Mese 24 |

### Termini suggeriti

- **Strumento:** SAFE (Simple Agreement for Future Equity) o convertibile
- **Valuation cap:** €1M pre-money
- **Discount:** 20% sul prossimo round
- **Diritti investitore:** Informativa trimestrale, board observer seat

---

## 11. Analisi dei Rischi

| Rischio | Probabilita' | Impatto | Mitigazione |
|---------|-------------|---------|-------------|
| **Adozione lenta** | Media | Alto | Lancio a scarcita' controllata, demo 1:1, garanzia 30gg |
| **Competitor SaaS aggressivo** | Media | Medio | Moat scientifico + locale-first non replicabile rapidamente |
| **Resistenza al prezzo €449** | Media | Medio | Confronto annualizzato vs SaaS (€449 una volta < €480/anno Mangofit). Garanzia 30gg |
| **Basso tasso rinnovo upgrade** | Media | Alto | Aggiornamenti di valore reale (AI, nuovi esercizi, nutrizione). Se <40%, valutare pricing |
| **Supporto non scalabile** | Media | Medio | Knowledge base, community forum, video tutorial |
| **Single founder risk** | Alta | Alto | Co-founder commerciale come priorita' #1 |
| **Regolamentazione dati sanitari** | Bassa | Alto | Privacy-first by design, GDPR audit preventivo |

### Scenario pessimistico (vendite -50%)

Se l'adozione e' 50% inferiore alle proiezioni:
- Anno 1: 65 licenze → €26.185 ricavi, -€15.815 EBITDA
- Anno 2: 120 nuove + 65 base → ~€67K ricavi, ~-€61K EBITDA cumulativo
- Il seed da €150K copre comunque **36+ mesi di runway**
- Con 65 clienti attivi, il tasso di rinnovo upgrade e' comunque misurabile per decidere pivot/persevere

### Scenario ottimistico (vendite +50%)

- Anno 1: 195 licenze → €78K ricavi, EBITDA €36K
- Anno 2: 360 nuove + 195 base → €183K ricavi, EBITDA €55K
- Serie A ready anticipata a mese 18

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

*Documento v2.0, 22 marzo 2026. Modello licenza perpetua + upgrade annuale. Dati di mercato basati su fonti pubbliche (ISTAT, Les Mills, Business Research Insights, Polaris Market Research). Le proiezioni finanziarie sono stime conservative basate su benchmark di settore software perpetuo.*

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

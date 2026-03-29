# FitManager AI Studio — Roadmap 90 Giorni Post-Lancio

> Data: 2026-03-25
> Stato: attivo
> ADR di riferimento: ADR-006 (FitManager Box multi-platform)
> Prerequisito: lancio v1.0.x completato su Windows

---

## Visione

Trasformare FitManager da "software desktop per PC" a **"sistema chiavi in mano per lo studio del professionista fitness"** — dove il prodotto venduto include hardware dedicato (FitManager Box) + software + accesso da qualsiasi dispositivo, senza cloud, senza abbonamenti.

---

## Feedback fondativi (da prima utilizzatrice reale)

| Segnale | Impatto | Urgenza |
|---|---|---|
| Chiara e' soddisfatta, si sente organizzata | Il CRM core funziona. Non toccare. | — |
| Le clienti apprezzano le schede | Workout builder e' il feature killer. | — |
| Monitoraggio scientifico sottoutilizzato | UX problem, non feature problem | Media |
| Safety Engine e Analisi Scientifica mai consultati | Invisibili perche' opt-in. Devono diventare passivi. | Media-Alta |
| **"Deve funzionare dal cellulare, anche a PC spento"** | **Blocco strutturale per il target PT/kinesiologi** | **Critica** |

---

## Fase 1 — ACCESSO MOBILE (Settimana 1-3)

> Obiettivo: il trainer accede a FitManager dal telefono in palestra.
> Non richiede la Box — funziona gia' col PC acceso.

### 1.1 PWA Wrapper (3-4 giorni)

Trasformare il frontend Next.js in Progressive Web App installabile.

| Task | Dettaglio | Effort |
|---|---|---|
| `manifest.json` | Nome, icone (192+512px), theme_color teal, display standalone | 2h |
| Service Worker (Workbox) | Runtime caching stale-while-revalidate per pagine + API GET | 1d |
| Meta tags iOS/Android | apple-mobile-web-app-capable, status-bar-style | 2h |
| Icona e splash screen | Adattamento LogoIcon per formati PWA | 4h |
| Install prompt | Banner "Installa FitManager" su mobile (beforeinstallprompt) | 4h |
| Test su Android + iOS | Chrome/Safari, installazione homescreen, navigazione | 1d |

**Deliverable**: il trainer installa "FitManager" sulla home del telefono. Si apre come app a schermo intero.

### 1.2 Accesso WiFi Locale con QR (1-2 giorni)

Il backend gia' binda su `0.0.0.0`. Servono:

| Task | Dettaglio | Effort |
|---|---|---|
| Rilevamento IP locale | Endpoint `/api/system/local-access` che ritorna IP LAN | 2h |
| QR Code in Impostazioni | Sezione "Accesso da telefono" con QR dell'URL locale | 4h |
| Istruzioni contestuali | "Connettiti alla stessa rete WiFi del PC, scansiona il QR" | 2h |

**Deliverable**: in Impostazioni, il trainer vede un QR code. Lo scansiona col telefono, apre FitManager.

### 1.3 Tailscale Full-App (2-3 giorni)

Oggi Tailscale Funnel espone solo il portale anamnesi. Estendere:

| Task | Dettaglio | Effort |
|---|---|---|
| Estensione Funnel | Esporre porta 3000 completa (non solo /portale) | 4h |
| Route protection audit | Verificare che tutte le route non-pubbliche richiedano JWT | 1d |
| UI "Accesso Remoto" | Sezione in Impostazioni con URL Tailscale + stato + QR | 4h |
| Documentazione trainer | Guida: "Come accedere da fuori studio" | 2h |

**Deliverable**: il trainer accede a FitManager da qualsiasi rete, via Tailscale sul telefono. Richiede PC acceso.

### 1.4 Mobile UX Audit e Fix (3-4 giorni)

Il frontend ha gia' breakpoint responsive. Ma servono verifiche mirate:

| Task | Dettaglio | Effort |
|---|---|---|
| Audit pagine critiche @375px | Dashboard, Profilo Cliente, Workout Viewer, Agenda | 1d |
| Bottom navigation mobile | Navbar bottom per viewport < 640px (thumb zone) | 1d |
| Touch target audit | Tutti i bottoni d'azione >= 44px | 4h |
| Sidebar → drawer mobile | Sidebar collassa in drawer swipeable su mobile | 4h |
| Form usability mobile | Input, select, date picker verificati su touch | 4h |

**Deliverable**: FitManager e' usabile dal telefono senza frustrazione.

### Gate di Fase 1

- [ ] PWA installabile su Android e iOS (homescreen)
- [ ] QR code funzionante in Impostazioni (WiFi locale)
- [ ] Tailscale full-app funzionante con JWT protection
- [ ] Le 4 pagine critiche superano audit mobile @375px
- [ ] Touch target >= 44px su tutti i bottoni d'azione

---

## Fase 2 — FITMANAGER BOX (Settimana 4-8)

> Obiettivo: FitManager gira su Raspberry Pi 5 always-on. Il trainer accede da qualsiasi dispositivo, anche a PC spento.

### 2.1 Porting Linux/ARM64 (1 settimana)

Sostituire il deploy PyInstaller con deploy Linux nativo.

| Task | Dettaglio | Effort |
|---|---|---|
| Ambiente Python su Pi | venv + dipendenze (tutte pure-Python o con wheel ARM64) | 4h |
| Next.js standalone su ARM64 | Build + test `node server.js` su Pi 5 | 4h |
| Systemd services | `fitmanager-api.service` + `fitmanager-frontend.service` (auto-start, restart on failure) | 4h |
| Adattamento DATA_DIR | Gestire path Linux (`/opt/fitmanager/data/`) senza rompere Windows | 4h |
| Seed database su Pi | Verificare che crm.db + catalog.db + nutrition.db funzionino | 2h |
| Test funzionale completo | Login, CRUD clienti, workout, agenda — tutto su Pi | 1d |
| Benchmark performance | Tempi risposta API, build time, memory usage su Pi 5 4GB | 4h |

**Deliverable**: FitManager gira su Raspberry Pi 5, identico al PC.

### 2.2 Fingerprint ARM e Licenza (3 giorni)

Il sistema licenza usa SHA-256 di CPU+Board+BIOS (PowerShell). Su Linux/ARM:

| Task | Dettaglio | Effort |
|---|---|---|
| Fingerprint Linux | `cat /proc/cpuinfo` (Serial) + `/sys/firmware/devicetree/base/serial-number` | 4h |
| Unificazione fingerprint service | `get_machine_fingerprint()` con branch OS (Windows PowerShell / Linux proc) | 4h |
| Test licenza su Pi | Generare licenza per Pi, verificare enforcement | 4h |
| Documentazione admin | Aggiornare LICENSE_ACTIVATION.md con flusso Pi | 2h |

**Deliverable**: il sistema licenza funziona identicamente su Windows e Pi.

### 2.3 Provisioning Automatico (1 settimana)

Creare un'immagine Raspberry Pi replicabile e un processo di setup.

| Task | Dettaglio | Effort |
|---|---|---|
| Script provisioning | `provision-box.sh`: installa Python, Node, Tailscale, FitManager, configura systemd | 1d |
| Immagine base | Raspberry Pi OS Lite 64-bit + provisioning pre-eseguito | 4h |
| Auto-backup USB | Cron job notturno: backup crm.db su chiavetta USB (rsync + rotazione 7 giorni) | 4h |
| First-boot wizard | Script che al primo avvio chiede: nome WiFi, crea utente trainer, genera fingerprint | 1d |
| Tailscale auto-setup | `tailscale up --authkey` con chiave pre-generata o QR di pairing | 4h |
| LED/status fisico | Script che segnala stato via LED del Pi (verde = ok, rosso = errore) | 2h |
| Documentazione setup | Guida "Unboxing FitManager Box" (con foto) | 4h |

**Deliverable**: immagine Pi flashabile su SD. Tempo setup: < 15 minuti.

### 2.4 Aggiornamento OTA (3-4 giorni)

Il software sulla Box deve essere aggiornabile senza reinstallare.

| Task | Dettaglio | Effort |
|---|---|---|
| Versioning check | Endpoint `/api/system/version` gia' esiste. Aggiungere check remoto. | 4h |
| Update script | `update-fitmanager.sh`: pull nuova versione, rebuild frontend, restart services | 1d |
| Release channel | GitHub Releases (tag vX.Y.Z) come sorgente. Download asset specifico per platform. | 4h |
| Rollback | Snapshot pre-update. Se il service non parte in 60s, rollback automatico. | 4h |
| UI aggiornamento | Sezione in Impostazioni: "Versione corrente / Aggiornamento disponibile / Aggiorna" | 4h |

**Deliverable**: il trainer aggiorna la Box con un click da Impostazioni.

### Gate di Fase 2

- [ ] FitManager funziona su Pi 5 (tutti i flussi core)
- [ ] API response time < 200ms per CRUD standard su Pi
- [ ] Licenza genera/verifica correttamente su ARM
- [ ] Immagine Pi flashabile e replicabile
- [ ] Backup USB notturno funzionante
- [ ] First-boot setup completabile in < 15 minuti
- [ ] Aggiornamento OTA funzionante con rollback

---

## Fase 3 — PRODOTTO E GO-TO-MARKET (Settimana 9-12)

> Obiettivo: la FitManager Box e' un prodotto vendibile e supportabile.

### 3.1 UX Science Nudges (1 settimana)

Rendere i motori scientifici **passivi e visibili**, non opt-in.

| Task | Dettaglio | Effort |
|---|---|---|
| Safety Engine inline nel Workout Builder | Se il cliente ha condizioni in anamnesi, alert inline automatico nel builder | 1d |
| Badge "misurazioni mancanti" nel profilo | "Ultima misurazione: X giorni fa" con CTA | 4h |
| Quick-entry misurazioni | 3 campi (peso, BF%, note) accessibili dal profilo con un click | 4h |
| Nudge nel workout | "Questo cliente non ha misurazioni recenti — il calcolo progressione e' stimato" | 2h |
| Analisi scientifica auto-show | Quando il workout e' salvato, mostrare un mini-summary (non la tab completa) | 4h |

**Deliverable**: i motori scientifici sono visibili senza azione deliberata del trainer.

### 3.2 Packaging e Qualita' (3-4 giorni)

| Task | Dettaglio | Effort |
|---|---|---|
| Stress test Box | 48h di funzionamento continuo, memory leak check, SD wear | 1d |
| Thermal test | Verifica temperature sotto carico (FastAPI + Next.js) con e senza case | 4h |
| Recovery test | Simulare: stacco corrente, SD corrotta, WiFi down — verifica resilienza | 4h |
| Packaging fisico | Design scatola, istruzioni cartacee, QR per guida online | 1d |

### 3.3 Canali di Vendita (parallelo)

| Azione | Dettaglio | Quando |
|---|---|---|
| Landing page dedicata | Sezione "FitManager Box" nel sito con foto, specs, prezzo, CTA | Settimana 9 |
| Video demo | 2 minuti: unboxing, setup, accesso da telefono | Settimana 10 |
| Early adopter program | Primi 10 Fondatori: 8 licenze a EUR 99 + 2 Box a EUR 199 per testimonial | Settimana 10-11 |
| Feedback loop | Survey strutturata post-setup + call 1:1 con early adopter | Settimana 11-12 |
| Pricing ufficiale | Prezzo definitivo: EUR 449 (validato in BP v4.2) | Settimana 12 |

### 3.4 Supporto e Operazioni

| Task | Dettaglio | Effort |
|---|---|---|
| Runbook Box | Troubleshooting: WiFi, Tailscale, LED rosso, backup fallito | 1d |
| Diagnostica remota | SSH via Tailscale per supporto (con consenso trainer) | 4h |
| Monitoring leggero | Healthcheck periodico (la Box pinga un endpoint, alert se mancante) | 4h |
| FAQ e knowledge base | Risposte alle domande piu' frequenti (sito/docs) | 4h |

### Gate di Fase 3

- [ ] Box stabile 48h senza intervento
- [ ] Temperature sotto 70C sotto carico sostenuto
- [ ] Recovery da stacco corrente senza perdita dati (WAL)
- [ ] Landing page live con CTA funzionante
- [ ] Almeno 3 early adopter con setup completato
- [ ] Feedback positivo da almeno 2/3 early adopter
- [ ] Runbook supporto completo

---

## Timeline Visuale

```
LANCIO     Sett 1-3              Sett 4-8                Sett 9-12
  |━━━━━━━━━━━━━━━━━━━|━━━━━━━━━━━━━━━━━━━━━━━|━━━━━━━━━━━━━━━━━━━━━|
  |                   |                       |                     |
  |  FASE 1           |  FASE 2               |  FASE 3             |
  |  Accesso Mobile   |  FitManager Box       |  Prodotto + GTM     |
  |                   |                       |                     |
  |  - PWA            |  - Porting ARM64      |  - Science nudges   |
  |  - QR WiFi        |  - Licenza ARM        |  - Stress test      |
  |  - Tailscale full |  - Provisioning       |  - Early adopter    |
  |  - Mobile UX      |  - OTA update         |  - Landing page     |
  |                   |                       |  - Video demo       |
  |                   |                       |                     |
  v                   v                       v                     v
  PC Windows        + Telefono              + Box ready          VENDITA BOX
  (come oggi)       (WiFi/Tailscale)        (alpha)             (early adopter)
```

### Oltre i 90 giorni — FitScan (Fase 4+)

```
Mese 4-5              Mese 5-6              Mese 6-9              Mese 9-12
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FASE 4a               FASE 4b               FASE 4c               FASE 4d
FitScan L1            FitScan L2 proto      FitScan L2 scale      FitScan L3
Body Scan             Form Analysis (3 ex)  Form Analysis (20 ex) Movement Screen

- MediaPipe browser   - Profili squat/dl/bp - Top 20 compound     - Overhead squat test
- 3 pose (F/R/L)      - Rep detection       - Box Pro (Hailo)     - Single-leg test
- 12 metriche         - Tempo analyzer      - Per-exercise rules  - FMS-like scoring
- Bridge measurement  - Safety cross-ref    - Score comparison    - Smart Programming
- History chart       - Form score          - Client trends       - Clinical Analysis
```

Spec tecnica completa: `docs/product/FITSCAN_ARCHITECTURE.md`
Decisione architetturale: `docs/adr/ADR-007-fitscan-computer-vision-biomechanics.md`

---

## Pricing Strategy

### Tier Software (invariato rispetto al lancio)

| Prodotto | Prezzo | Target |
|---|---|---|
| FitManager License (PC Windows) | EUR 249 una tantum | PT con PC fisso in studio |

### Tier Hardware+Software (nuovo, da Fase 3)

| Prodotto | Costo nostro | Prezzo | Margine |
|---|---|---|---|
| FitManager Box | ~EUR 130-150 | EUR 449 | ~EUR 299-319 (67%) |
| FitManager Box Pro (+ Hailo + Camera) | ~EUR 210 | EUR 549-599 | ~EUR 340-390 |
| Box + Tablet Android 10" | ~EUR 230-250 | EUR 549-599 | ~EUR 300-350 |
| Box Pro + Tablet Android 10" | ~EUR 310 | EUR 699-749 | ~EUR 390-440 |

### Tier Servizi (opzionale)

| Servizio | Prezzo | Contenuto |
|---|---|---|
| Assistenza PRO | EUR 79/anno | Aggiornamenti, nuovi esercizi/alimenti, template, supporto prioritario |
| Setup remoto assistito | EUR 29 una tantum | Videocall 30min per configurazione |
| Migrazione da altro software | EUR 49-99 una tantum | Import dati da Excel/altro gestionale |

### Tier Community (nuovo, da Mese 4)

| Livello | Prezzo | Contenuto |
|---|---|---|
| Base (gratuita) | EUR 0 | Forum, knowledge base, networking, onboarding guidato |
| Inner Circle | EUR 249/anno | Include PRO + masterclass, webinar, mastermind, certificazione PT Evoluto |
| Mentorship (futuro, Anno 3+) | EUR 499-599/anno | 1:1, co-creazione roadmap, eventi in presenza |

---

## Rischi e Mitigazioni

| Rischio | Probabilita | Impatto | Mitigazione |
|---|---|---|---|
| Pi 5 non regge il carico | Bassa | Alto | Benchmark in Fase 2. Fallback: Pi 5 8GB (+EUR 20) |
| SD card si corrompe | Media | Alto | Backup USB notturno + SQLite WAL. Worst case: re-flash + restore |
| Trainer non riesce a configurare Tailscale | Media | Medio | First-boot wizard automatizzato + setup assistito remoto |
| Pochi ordini Box | Media | Basso | Nessun investimento inventario. Ordine on-demand. Software resta il core. |
| Supporto hardware insostenibile | Bassa | Medio | Immagine replicabile. Reset = re-flash SD. Sostituzione Pi = EUR 65. |
| Competitor copia il modello | Bassa | Basso | Vantaggio di esecuzione + motori scientifici non replicabili |

---

## Metriche di Successo (fine 90 giorni)

| Metrica | Target |
|---|---|
| PWA installata da Chiara | Si |
| Chiara usa FitManager dal telefono in palestra | Si |
| Box alpha funzionante su Pi 5 | Si |
| Tempo setup Box < 15 minuti | Si |
| Early adopter Box (ordini) | >= 5 |
| Feedback early adopter positivo | >= 80% |
| Safety Engine alert visibili senza click | Si |
| FitScan L1 prototipo funzionante | Si (se tempo permette, altrimenti mese 4) |

---

## Riferimenti

- ADR-006: `docs/adr/ADR-006-fitmanager-box-multi-platform.md`
- Security Model: `docs/technical/SECURITY_MODEL.md`
- License Activation: `docs/technical/LICENSE_ACTIVATION.md`
- Competitive Analysis: `docs/business/COMPETITIVE_ANALYSIS.md`
- Launch Scope: `LAUNCH_SCOPE.md`
- Manifesto: `MANIFESTO.md`
- ADR-007 FitScan: `docs/adr/ADR-007-fitscan-computer-vision-biomechanics.md`
- FitScan Architecture: `docs/product/FITSCAN_ARCHITECTURE.md`

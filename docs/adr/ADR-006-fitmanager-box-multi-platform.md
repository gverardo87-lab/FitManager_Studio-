# ADR-006 — FitManager Box: Strategia Multi-Platform e Modello Hardware+Software

- Date: 2026-03-25
- Status: accepted
- Deciders: gvera
- Related upgrade ID: POST-LAUNCH-ROADMAP-90D

## Context

FitManager nasce come software desktop Windows (PyInstaller + Next.js standalone + Inno Setup).
La prima utilizzatrice reale (Chiara) ha confermato che:

1. **Il CRM funziona**: e' soddisfatta, si sente organizzata, le clienti apprezzano le schede.
2. **Il monitoraggio scientifico e' sottoutilizzato**: concettualmente ostico, richiede azione deliberata.
3. **L'accesso mobile e' bloccante per il target**: PT e kinesiologi lavorano in piedi, col telefono in mano, spesso col PC spento. Un software desktop-only e' percepito come "strumento da ufficio" — e i PT non hanno un ufficio.

Il problema fondamentale: **se il PC e' spento, il server non esiste**. Tailscale, WiFi locale, PWA — tutto dipende da un server attivo.

L'analisi competitiva (docs/archive/business/COMPETITIVE_ANALYSIS_2026-03-29.md, archiviata come fotografia marzo 2026) conferma che tutti i competitor sono cloud SaaS con abbonamento mensile. Nessuno offre: hosting locale, privacy-first, motori scientifici, italiano nativo.

## Decision Drivers

1. **Il target vive sul telefono**: PT e kinesiologi hanno bisogno di consultare schede, agenda, profili clienti dal telefono in palestra — anche a PC spento.
2. **Zero cloud rimane un differenziale**: il posizionamento privacy-first e' la nicchia vuota del mercato. Non possiamo abbandonarlo.
3. **Il modello di business deve scalare senza costi ricorrenti infrastrutturali**: niente server da mantenere per ogni cliente.
4. **Il deployment deve essere "plug and play"**: il target non e' tech-savvy. Installazioni complesse = abbandono.
5. **Il time-to-market e' critico**: servono risultati visibili entro 90 giorni dal lancio.

## Considered Options

### Option A — Cloud SaaS (migrazione completa)

- Pro: accesso ovunque, mobile nativo, modello SaaS scalabile
- Contro: **tradisce il posizionamento privacy-first**, mesi di lavoro, costi server ricorrenti per noi, perdiamo il differenziale competitivo unico

### Option B — PWA con cache offline (solo software)

- Pro: zero costi hardware, funziona su qualsiasi dispositivo
- Contro: **se il PC e' spento, la cache e' stale**. Richiede che il trainer apra l'app col PC acceso (workflow innaturale). Nessuna scrittura offline. Non risolve il problema reale.

### Option C — FitManager Box: hardware dedicato always-on (scelta)

- Pro: **risolve il problema alla radice** (server sempre acceso), privacy intatta (dati in studio), costo una tantum per il trainer, ambiente controllato (zero problemi "il mio Windows 7"), margine hardware significativo, narrativa di vendita forte
- Contro: logistica hardware (stoccaggio, spedizione), supporto hardware, deploy Linux/ARM da costruire

### Option D — VPS cloud leggero per sync read-only

- Pro: sempre disponibile, nessun hardware extra
- Contro: dati su un server (anche se crittografati), costo ricorrente per il trainer, complessita' sync, perde il differenziale "zero cloud"

## Decision

**Option C — FitManager Box** come evoluzione strategica del prodotto, con rollout progressivo in 3 fasi su 90 giorni.

Il modello diventa: **vendere il sistema, non solo il software**. Il PC Windows rimane supportato (Tier 1), la FitManager Box diventa il Tier 2 premium.

### Architettura FitManager Box

```
┌─────────────────────────────────────────────┐
│  FitManager Box (sempre acceso in studio)   │
│  Raspberry Pi 5 · 4GB · case compatto      │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
│  │ FastAPI  │  │ Next.js  │  │ SQLite    │ │
│  │ :8000    │  │ :3000    │  │ 3x DB     │ │
│  └──────────┘  └──────────┘  └───────────┘ │
│  Tailscale · systemd · auto-backup USB     │
│  Consumo: ~5W (≈EUR 10/anno)               │
└──────────────┬──────────────────────────────┘
               │
    ┌──────────┴──────────────────────┐
    │     Tailscale (crittografato)   │
    ├─────────┬───────────┬───────────┤
    phone   tablet      laptop       PC
  (in gym)  (cliente)   (a casa)    (studio)
```

### Compatibilita' tecnica

| Componente | Su Raspberry Pi 5 (ARM64) | Rischio |
|---|---|---|
| Python 3.12 + FastAPI + SQLModel | Nativo ARM64, nessun porting | Nessuno |
| SQLite WAL | Nativo | Nessuno |
| Next.js 16 standalone | Node.js ARM64 maturo | Basso |
| Tailscale | Build ARM64 ufficiale | Nessuno |
| PyInstaller | Non funziona (Windows-only) | Va sostituito con systemd |
| Ollama (AI dormiente) | Build ARM64 ufficiale | Basso (non critico al lancio) |

### Modello di business

| Tier | Contenuto | Prezzo |
|---|---|---|
| Software License (PC Windows) | Licenza + installer + supporto email | EUR 249 una tantum |
| FitManager Box | Raspberry Pi preconfigurato + licenza + setup assistito | EUR 449 una tantum |
| Box + Tablet Bundle | Box + tablet Android preconfigurato | EUR 549-599 una tantum |
| Assistenza PRO (opzionale) | Aggiornamenti, nuovi esercizi/alimenti, template, supporto prioritario | EUR 79/anno |
| Inner Circle | Include PRO + masterclass, webinar, mastermind, certificazione PT Evoluto | EUR 249/anno |

### Hardware BOM (Box)

| Componente | Costo | Note |
|---|---|---|
| Raspberry Pi 5 4GB | ~EUR 75-80 | Distributore ufficiale IT (2026) |
| Case ufficiale + alimentatore 27W | ~EUR 25 | USB-C, ventola integrata |
| MicroSD 64GB A2 | ~EUR 10 | Pre-flashata con immagine |
| Cavo Ethernet Cat6 (1m) | ~EUR 3 | Opzionale, incluso |
| Chiavetta USB 32GB (backup) | ~EUR 5 | Backup notturno automatico |
| Packaging + branding | ~EUR 10-15 | Scatola, adesivi, quick-start card |
| **Totale BOM** | **~EUR 130-150** | Margine: EUR 299-319/unita (67%) |

## Consequences

### Positive

1. Risolve il problema mobile senza cloud (il server e' always-on in studio)
2. Elimina variabilita' hardware (ambiente controllato, supporto prevedibile)
3. Crea un prodotto fisico tangibile (valore percepito alto, differenziale forte)
4. Margine hardware significativo (~67% su ogni Box)
5. Narrativa di vendita unica: "Il tuo studio, il tuo server, la tua privacy"
6. Il PC Windows resta supportato — la Box e' un'opzione, non un obbligo

### Negative

1. Logistica hardware (stoccaggio, spedizione, resi) — mitigato: volumi bassi iniziali, spedizione diretta
2. Supporto hardware (guasti, networking) — mitigato: Raspberry Pi affidabile, immagine replicabile
3. Deploy Linux/ARM da costruire (~2-3 settimane) — mitigato: stack gia' compatibile ARM64
4. Licensing su hardware diverso (machine fingerprint cambia) — mitigato: fingerprint specifico per Box

### Follow-up actions

1. Creare script di provisioning Raspberry Pi (immagine replicabile)
2. Adattare sistema licenza per fingerprint ARM (CPU serial del Pi)
3. Creare meccanismo aggiornamento OTA (pull-based, non push)
4. Testare performance stack completo su Pi 5 4GB
5. Definire processo di setup assistito remoto (prima vendita)
6. PWA wrapper per esperienza "app nativa" su telefono

## Rollback / Exit Strategy

La FitManager Box e' un **canale di distribuzione aggiuntivo**, non una sostituzione. Se il mercato non risponde:
- Il software Windows continua a funzionare identicamente
- Le Box invendute hanno valore residuo (hardware generico)
- Il lavoro di porting Linux/ARM serve comunque per futuri deployment (NAS, NUC, cloud VM)
- Nessun debito tecnico: il codebase resta unico, solo il deployment cambia

## Supersedes / Superseded By

- Supersedes: nessuno (estende il modello, non lo sostituisce)
- Superseded by: eventuale ADR futura se si sceglie cloud ibrido

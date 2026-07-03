# ROADMAP_FINANCIAL_UPGRADES — Analisi e Pianificazione Miglioramenti Finanziari

> Data: 2026-07-03
> Status: 📸 **FOTOGRAFIA ARCHIVIATA** (2026-07-03) — §1.2 Late Cancel/No_Show = ✅ IMPLEMENTATO (`db322eb`, ADR-017 Add. I); §1.3 audit abbuoni = ✅ già presente nel backend (nota obbligatoria + `saldo_trainer_rinunciato`); §1.1 wallet append-only e §1.4 forecast ponderato = backlog POST-LANCIO (censiti in INDEX)
> Autore: Senior Software Engineer (Google Level)
> Riferimenti: [LAUNCH_SCOPE.md](file:///c:/Users/gvera/Projects/FitManager_AI_Studio/LAUNCH_SCOPE.md), [LAUNCH_SPRINT.md](file:///c:/Users/gvera/Projects/FitManager_AI_Studio/LAUNCH_SPRINT.md), [ADR-020](file:///c:/Users/gvera/Projects/FitManager_AI_Studio/docs/adr/ADR-020-wallet-cliente-customer-credit-balance.md), [ADR-017](file:///c:/Users/gvera/Projects/FitManager_AI_Studio/docs/adr/ADR-017-rinvio-libera-credito.md)

Questo documento contiene l'estrapolazione e l'analisi tecnica dei quattro miglioramenti finanziari proposti per FitManager, con la relativa raccomandazione strategica sul timing di inserimento (Pre-lancio vs Post-lancio).

---

## 1. Dettaglio dei Miglioramenti Proposti

### 1.1 Evoluzione del Wallet Cliente in Sotto-Ledger Transazionale
*   **Situazione Attuale**: La tabella `crediti_cliente` (introdotta in `G8.1`) gestisce il saldo in modo flat tramite due campi numerici aggiornati in-place (`importo` e `importo_erogato`).
*   **Cosa Prevede la Roadmap**: Trasformare la gestione in un modello append-only tramite una tabella transazionale (es. `movimenti_wallet_cliente`), in cui ogni deposito, prelievo o erogazione genera una riga datata immutabile.
*   **Perché è Fondamentale**: Rispetta il principio dell'immutabilità contabile di FitManager (**Strada B**), prevenendo che bug di calcolo o corruzioni modifichino il saldo storico del wallet senza lasciare una traccia auditabile.

### 1.2 Gestione del "Late Cancel" e Addebito Penale
*   **Situazione Attuale**: In [contract_state.py](file:///c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/contract_state.py), i crediti del contratto vengono occupati solo da eventi in stato `Programmato` o `Completato`. Lo stato `Cancellato` libera immediatamente il credito.
*   **Cosa Prevede la Roadmap**: Introdurre lo stato di agenda `Cancellato_Tardivo` o `No_Show` (Mancata Presentazione). Questo stato consuma finanziariamente il credito (la lezione viene scalata a titolo di penale per il tempo perso del trainer), ma contrassegna la seduta come "non eseguita" a livello atletico/scientifico.
*   **Perché è Fondamentale**: Protegge il tempo e il compenso del trainer da cancellazioni dell'ultimo minuto, una funzionalità standard nei CRM fitness maturi.

### 1.3 Registro Audit Obbligatorio per gli Abbuoni
*   **Situazione Attuale**: Nelle terminazioni bilaterali con saldo a favore del trainer (`conguaglio > 0`), l'applicazione supporta l'opzione "Rinuncia espressa", che azzera il dovuto del contratto.
*   **Cosa Prevede la Roadmap**: Rendere obbligatorio l'inserimento di una nota descrittiva di giustificazione per ogni rinuncia espressa, registrando l'evento in modo strutturato nel registro di audit (`saldo_trainer_rinunciato`).
*   **Perché è Fondamentale**: Fornisce giustificazione e trasparenza fiscale e gestionale sul perché del denaro legalmente dovuto sia stato abbuonato (es. per fidelizzazione o accordo bonario).

### 1.4 Ponderazione del Rischio di Insolvenza nel Forecast
*   **Situazione Attuale**: Il previsionale di cassa in [movements.py](file:///c:/Users/gvera/Projects/FitManager_AI_Studio/api/routers/movements.py) calcola le entrate future aggregando linearmente le rate pendenti/parziali per il loro mese di scadenza.
*   **Cosa Prevede la Roadmap**: Applicare un fattore di ponderazione probabilistico (tasso di insolvenza) basato sullo storico del cliente (es. ritardi cronici, contratti precedentemente sospesi) per mostrare una stima realistica del flusso di cassa.
*   **Perché è Fondamentale**: Evita l'ottimismo contabile del software, avvicinando FitManager ai gestionali di tesoreria enterprise.

---

## 2. Analisi e Raccomandazione Strategica (Now vs Later)

### 2.1 Sintesi delle Decisioni
| Feature | Stato Backend Attuale | Timing Consigliato | Razionale di Software Engineering |
| :--- | :--- | :--- | :--- |
| **1. Wallet Transazionale** | Flat (G8.1) | **POST-LANCIO (Later)** | Il modello flat attuale funziona e non perde dati. Riscrivere il wallet in transazionale a ridosso del lancio introduce un rischio di regressione non necessario sui flussi di terminazione e riapertura contratti. |
| **2. Late Cancel / Penale** | Non implementato | **ADESSO (Pre-launch)** | Valore utente elevatissimo (richiesta PT reale). Basso rischio tecnico: è un'estensione additiva dello stato dell'agenda che non altera gli invarianti di calcolo monetario. |
| **3. Audit Abbuoni** | Obbligatorio in API | **ADESSO (Verifica UI)** | Il backend [transitions.py](file:///c:/Users/gvera/Projects/FitManager_AI_Studio/api/services/financial/transitions.py) già impone la nota obbligatoria. Occorre solo assicurarsi che il frontend la validi correttamente prima del submit. |
| **4. Ponderazione Forecast** | Semplice / Lineare | **POST-LANCIO (Later)** | Richiede il calcolo storico del comportamento di pagamento (ritardo medio, DPD). È un add-on enterprise non bloccante per il go-live locale di trainer singoli. |

---

## 3. Strategia di Rollout e Prossimi Passi

1.  **Fase 1 (Pre-lancio)**:
    *   Verificare e forzare l'obbligatorietà della nota di abbuono nella dialog di terminazione lato frontend.
    *   Scrivere la specifica tecnica per lo stato `Cancellato_Tardivo` / `No_Show` ed implementare la logica di consumo crediti.
2.  **Fase 2 (Post-lancio / Roadmap 90 Giorni)**:
    *   Introdurre la tabella `movimenti_wallet_cliente` ed eseguire lo staging del wallet transazionale append-only.
    *   Implementare la profilazione di rischio sul forecast finanziario.

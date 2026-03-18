// ════════════════════════════════════════════════════════════
// HelpBot Data — 12 Capitoli del Journey Trainer
//
// Ogni capitolo: intro conversazionale, 5-8 azioni chiave,
// FAQ contestuali, link mini-tour. Ordinati per journey
// reale: registrazione cliente → monitoraggio progressi.
//
// File puro dati. Zero React, zero side-effect.
// ════════════════════════════════════════════════════════════

import type { BotAction, ProactiveTrigger, SpotlightTarget } from "./helpbot-types";

// ── Chapter interface ──

export interface ChapterAction {
  id: string;
  title: string;
  description: string;
  action?: BotAction;
  /** Se presente, l'azione puo' evidenziare un elemento sulla pagina */
  spotlight?: SpotlightTarget;
}

export interface ChapterFaq {
  question: string;
  answer: string;
}

export interface Chapter {
  id: string;
  title: string;
  /** Lucide icon name */
  icon: string;
  /** Route pattern per matching */
  routePattern: string;
  /** Greeting conversazionale (prima visita) */
  intro: string;
  actions: ChapterAction[];
  faqs: ChapterFaq[];
  /** Indici step nel TOUR_SCOPRI_FITMANAGER */
  miniTourSteps: number[];
}

// ═══════════════════════════════════════════════════════════
// I 12 CAPITOLI — Journey Order
// ═══════════════════════════════════════════════════════════

export const CHAPTERS: Chapter[] = [
  // ── 1. REGISTRA CLIENTI ──
  {
    id: "registra-clienti",
    title: "Registra Clienti",
    icon: "UserPlus",
    routePattern: "/clienti",
    intro: "Qui registri e gestisci i tuoi clienti. Ogni profilo diventa il punto di partenza per contratti, anamnesi e schede allenamento.",
    actions: [
      {
        id: "crea-cliente",
        title: "Crea un nuovo cliente",
        description: "Clicca \"Nuovo Cliente\" in alto a destra per aprire il form di registrazione.",
        action: { label: "Mostrami", type: "spotlight", payload: "crea-cliente" },
        spotlight: {
          target: "clienti-new-button",
          title: "Nuovo Cliente",
          description: "Clicca qui per aprire il form di registrazione. Compila nome, cognome e almeno un contatto per iniziare.",
          placement: "bottom",
          navigateTo: "/clienti",
        },
      },
      {
        id: "compila-dati",
        title: "Compila tutti i dati",
        description: "Nome, cognome, email, telefono, data di nascita, sesso, indirizzo e codice fiscale. Solo nome e cognome sono obbligatori.",
        action: { label: "Mostrami", type: "spotlight", payload: "compila-dati" },
        spotlight: {
          target: "clienti-new-button",
          title: "Form Registrazione",
          description: "Il form si apre cliccando qui. Campi: nome e cognome (obbligatori), email, telefono, data nascita, sesso, indirizzo e codice fiscale.",
          placement: "bottom",
          navigateTo: "/clienti",
        },
      },
      {
        id: "cerca-cliente",
        title: "Cerca un cliente",
        description: "La barra di ricerca in alto filtra per nome e cognome in tempo reale.",
        action: { label: "Mostrami", type: "spotlight", payload: "cerca-cliente" },
        spotlight: {
          target: "clienti-search",
          title: "Ricerca Clienti",
          description: "Digita nome, cognome o email per filtrare la lista in tempo reale. La ricerca ignora accenti e maiuscole.",
          placement: "bottom",
          navigateTo: "/clienti",
        },
      },
      {
        id: "filtra-stato",
        title: "Filtra per stato",
        description: "I chip Attivi e Inattivi filtrano la lista. Il conteggio si aggiorna dinamicamente.",
        action: { label: "Mostrami", type: "spotlight", payload: "filtra-stato" },
        spotlight: {
          target: "clienti-filter-stato",
          title: "Filtro Stato",
          description: "Clicca i chip Attivi e Inattivi per mostrare o nascondere clienti per stato. L'icona occhio indica quali filtri sono attivi.",
          placement: "bottom",
          navigateTo: "/clienti",
        },
      },
      {
        id: "filtra-situazione",
        title: "Filtra per situazione",
        description: "\"Con Rate Scadute\" evidenzia chi ha pagamenti in ritardo. \"Con Crediti\" chi ha ancora sedute disponibili.",
        action: { label: "Mostrami", type: "spotlight", payload: "filtra-situazione" },
        spotlight: {
          target: "clienti-filter-situazione",
          title: "Filtro Situazione",
          description: "\"Con Rate Scadute\" mostra chi ha pagamenti in ritardo (rosso). \"Con Crediti\" chi ha sedute disponibili (blu).",
          placement: "bottom",
          navigateTo: "/clienti",
        },
      },
      {
        id: "apri-profilo",
        title: "Apri il profilo",
        description: "Clicca sulla riga di un cliente per accedere al profilo completo con avatar, anamnesi e misurazioni.",
        action: { label: "Mostrami", type: "spotlight", payload: "apri-profilo" },
        spotlight: {
          target: "clienti-table-first-row",
          title: "Profilo Cliente",
          description: "Clicca su una riga per aprire il profilo completo: avatar con semaforo, anamnesi, misurazioni, contratti e schede.",
          placement: "bottom",
          navigateTo: "/clienti",
        },
      },
      {
        id: "leggi-avatar",
        title: "Leggi l'Avatar del cliente",
        description: "L'hero del profilo mostra 5 box interattivi: Clinica, Contratto, Scheda, Sedute PT e Corpo. Clicca ciascuno per scorrere alla tab corrispondente. Il ReadinessRing a sinistra indica la prontezza complessiva da 0 a 100.",
        action: { label: "Mostrami", type: "spotlight", payload: "leggi-avatar" },
        spotlight: {
          target: "client-avatar-hero",
          title: "Avatar Cliente",
          description: "5 box interattivi: Clinica, Contratto, Scheda, Sedute e Corpo. Clicca ciascuno per scorrere alla tab corrispondente. Il ring a sinistra e' la prontezza complessiva (0-100).",
          placement: "bottom",
        },
      },
      {
        id: "segui-5-passi",
        title: "Segui i 5 passi progressivi",
        description: "L'OnboardingChecklist ti guida nell'ordine giusto: (1) Contratto — crea il pacchetto, (2) Anamnesi — compila il questionario clinico, (3) Misurazioni — registra peso e composizione, (4) Scheda — crea il programma, (5) Prima sessione — prenota in agenda. Ogni passo ha una CTA e si completa automaticamente.",
        action: { label: "Mostrami", type: "spotlight", payload: "segui-5-passi" },
        spotlight: {
          target: "client-onboarding-checklist",
          title: "5 Passi Progressivi",
          description: "L'ordine giusto: (1) Contratto, (2) Anamnesi, (3) Misurazioni, (4) Scheda, (5) Prima sessione. Ogni passo ha la sua CTA e si completa automaticamente.",
          placement: "bottom",
        },
      },
    ],
    faqs: [
      {
        question: "Come creo il primo cliente?",
        answer: "Dalla sidebar clicca Clienti, poi \"Nuovo Cliente\" in alto a destra. Compila nome, cognome e almeno un contatto. Dopo il salvataggio accedi al profilo completo.",
      },
      {
        question: "Cosa significano i colori nell'Avatar?",
        answer: "Semaforo a 3 colori: verde = tutto ok, ambra = da verificare, rosso = azione urgente. Ogni box (Clinica, Contratto, Scheda, Sedute, Corpo) ha il suo semaforo indipendente.",
      },
      {
        question: "In che ordine devo completare i passi?",
        answer: "Contratto prima di tutto (senza contratto non puoi prenotare sedute PT). Poi anamnesi per lo Scudo Clinico, misurazioni per il tracking, scheda per il programma e infine la prima sessione in agenda.",
      },
    ],
    miniTourSteps: [1, 2, 3],
  },

  // ── 2. GESTISCI CONTRATTI ──
  // Spostato PRIMA dell'anamnesi: senza contratto non c'e' copertura assicurativa.
  {
    id: "gestisci-contratti",
    title: "Gestisci Contratti",
    icon: "FileText",
    routePattern: "/contratti",
    intro: "Il contratto e' il primo passo dopo la registrazione. Senza contratto attivo non c'e' copertura assicurativa e non puoi prenotare sedute PT.",
    actions: [
      {
        id: "crea-contratto",
        title: "Crea un nuovo contratto",
        description: "Seleziona cliente, tipo pacchetto (PT, sala, corso), prezzo, durata e crediti sessione. Il contratto attiva la copertura assicurativa.",
        action: { label: "Mostrami", type: "spotlight", payload: "crea-contratto" },
        spotlight: {
          target: "contratti-new-button",
          title: "Nuovo Contratto",
          description: "Clicca qui per creare un contratto. Seleziona cliente, tipo pacchetto, prezzo, durata e crediti. Il contratto attiva la copertura assicurativa.",
          placement: "bottom",
          navigateTo: "/contratti",
        },
      },
      {
        id: "genera-rate",
        title: "Genera il piano rateale",
        description: "Rate mensili automatiche con un click, oppure aggiungi rate manuali. Ogni rata ha data scadenza, importo e stato (pendente, parziale, saldata).",
        action: { label: "Mostrami", type: "spotlight", payload: "genera-rate" },
        spotlight: {
          target: "contratti-table-first-row",
          title: "Piano Rateale",
          description: "Apri il dettaglio contratto cliccando qui. Nella sezione Rate trovi il bottone \"Genera Piano\" per creare rate mensili automatiche.",
          placement: "bottom",
          navigateTo: "/contratti",
        },
      },
      {
        id: "registra-pagamento",
        title: "Registra un pagamento",
        description: "Dal dettaglio contratto, clicca \"Paga\" sulla rata. Importo completo o parziale, con metodo selezionabile (contanti, POS, bonifico). Il saldo Cassa si aggiorna automaticamente.",
        action: { label: "Mostrami", type: "spotlight", payload: "registra-pagamento" },
        spotlight: {
          target: "contratti-table-first-row",
          title: "Pagamento Rate",
          description: "Apri il contratto per accedere al piano rate. Clicca \"Paga\" su una rata per registrare il pagamento (completo o parziale).",
          placement: "bottom",
          navigateTo: "/contratti",
        },
      },
      {
        id: "rinnova-contratto",
        title: "Rinnova un contratto",
        description: "Dalla pagina Rinnovi & Incassi, clicca \"Rinnova\" su un contratto in scadenza. Il nuovo contratto si crea linkato all'originale con tipo, crediti e prezzo pre-compilati.",
        action: { label: "Vai a Rinnovi", type: "navigate", payload: "/rinnovi-incassi" },
      },
      {
        id: "modifica-contratto",
        title: "Modifica un contratto",
        description: "Dal dettaglio contratto puoi modificare prezzo, durata, crediti e note. Le rate gia' pagate restano intatte.",
        action: { label: "Mostrami", type: "spotlight", payload: "modifica-contratto" },
        spotlight: {
          target: "contratti-table-first-row",
          title: "Modifica Contratto",
          description: "Clicca un contratto per aprirne il dettaglio. Il bottone \"Modifica\" ti permette di aggiornare prezzo, durata, crediti e note.",
          placement: "bottom",
          navigateTo: "/contratti",
        },
      },
      {
        id: "crediti-agenda",
        title: "Crediti e agenda",
        description: "Ogni sessione PT completata in agenda scala automaticamente un credito dal contratto collegato. Quando i crediti e il saldo sono esauriti, il contratto si chiude da solo.",
        action: { label: "Vai all'Agenda", type: "navigate", payload: "/agenda" },
      },
      {
        id: "monitora-badge",
        title: "Leggi i badge di stato",
        description: "7 livelli di priorita' visiva: Chiuso (grigio), Insolvente (rosso pieno), Rate in Ritardo (rosso chiaro), Scaduto (ambra), Saldato (verde), In Corso (blu) e Nessuna Rata (grigio chiaro).",
        action: { label: "Mostrami", type: "spotlight", payload: "monitora-badge" },
        spotlight: {
          target: "contratti-table-first-row",
          title: "Badge di Stato",
          description: "La colonna Rate mostra il badge colorato. 7 livelli: da Insolvente (rosso) a Saldato (verde). Colori e icone cambiano automaticamente in base a pagamenti e scadenze.",
          placement: "bottom",
          navigateTo: "/contratti",
        },
      },
      {
        id: "vedi-kpi-finanziari",
        title: "Controlla i KPI finanziari",
        description: "4 card in alto: Contratti Attivi, Fatturato Totale, Incassato e Clienti con Rate Scadute. Aggiornamento in tempo reale.",
        action: { label: "Mostrami", type: "spotlight", payload: "vedi-kpi-finanziari" },
        spotlight: {
          target: "contratti-kpi",
          title: "KPI Finanziari",
          description: "4 card con i numeri chiave: quanti contratti attivi, fatturato totale, quanto incassato e quanti clienti hanno rate scadute.",
          placement: "bottom",
          navigateTo: "/contratti",
        },
      },
    ],
    faqs: [
      {
        question: "Come registro un pagamento?",
        answer: "Vai in Contratti, apri il dettaglio, scorri alle rate. Clicca \"Paga\" sulla rata. Puoi pagare l'intero o un parziale. Il saldo Cassa si aggiorna automaticamente.",
      },
      {
        question: "Perche' il contratto deve venire prima dell'anamnesi?",
        answer: "Senza contratto attivo non c'e' copertura assicurativa per le sedute. Il contratto definisce il pacchetto, i crediti e il piano pagamento — e' la base di tutto.",
      },
      {
        question: "I crediti si scalano automaticamente?",
        answer: "Si. Ogni sessione PT completata in agenda scala un credito dal contratto. Quando crediti e saldo sono esauriti, il contratto si chiude automaticamente.",
      },
    ],
    miniTourSteps: [4, 5, 6],
  },

  // ── 3. PROFILO & ANAMNESI ──
  {
    id: "profilo-anamnesi",
    title: "Profilo & Anamnesi",
    icon: "HeartPulse",
    routePattern: "/clienti/",
    intro: "Il profilo e' il cuore del cliente. Qui compili l'anamnesi, registri misurazioni e monitori la readiness clinica.",
    actions: [
      {
        id: "compila-anamnesi",
        title: "Compila l'anamnesi",
        description: "6 step strutturati: Stile di Vita, Obiettivo, Esperienza Sportiva, Salute, Alimentazione e Logistica. Alimenta lo Scudo Clinico.",
      },
      {
        id: "registra-misurazioni",
        title: "Registra misurazioni",
        description: "Peso, composizione corporea, circonferenze. I range normativi OMS/ACSM evidenziano valori fuori norma.",
      },
      {
        id: "imposta-obiettivi",
        title: "Imposta obiettivi",
        description: "Crea obiettivi con valore target e scadenza. Il sistema traccia il progresso automaticamente.",
      },
      {
        id: "genera-link-anamnesi",
        title: "Genera link anamnesi",
        description: "Crea un link monouso che il cliente compila da smartphone. I dati arrivano direttamente nel profilo.",
      },
      {
        id: "vedi-readiness",
        title: "Consulta la readiness",
        description: "Il ReadinessRing in alto mostra il punteggio complessivo. Sotto, i 5 box dettagliano ogni dimensione.",
      },
    ],
    faqs: [
      {
        question: "Il link anamnesi ha una scadenza?",
        answer: "Si, 48 ore. Dopo scade e va rigenerato. Il link e' monouso: una volta compilato non puo' essere riusato.",
      },
      {
        question: "Cosa significano i colori nella scheda allenamento?",
        answer: "Rosso (Evitare): esercizio controindicato. Ambra (Cautela): richiede attenzione. Blu (Adattare): modificare ROM, grip o carico. Il sistema non blocca nulla — la decisione e' sempre del professionista.",
      },
    ],
    miniTourSteps: [],
  },

  // ── 4. PIANIFICA AGENDA ──
  {
    id: "pianifica-agenda",
    title: "Pianifica Agenda",
    icon: "Calendar",
    routePattern: "/agenda",
    intro: "Il calendario interattivo con vista giorno, settimana e mese. Trascina per spostare, ridimensiona per cambiare durata.",
    actions: [
      {
        id: "crea-appuntamento",
        title: "Crea un appuntamento",
        description: "Clicca \"Pianifica\" in alto o clicca uno slot vuoto per pre-compilare data e ora.",
        action: { label: "Pianifica", type: "navigate", payload: "/agenda" },
      },
      {
        id: "trascina-evento",
        title: "Sposta un evento",
        description: "Trascina un evento per spostarlo di giorno o orario. Ridimensiona dal bordo inferiore per cambiare durata.",
      },
      {
        id: "completa-sessione",
        title: "Completa una sessione",
        description: "Hover sull'evento e clicca Completa. Il credito del contratto si scala automaticamente.",
      },
      {
        id: "filtra-categoria",
        title: "Filtra per categoria",
        description: "Chip PT, Sala, Corso, Colloquio. Attiva o disattiva per vedere solo le categorie che ti servono.",
      },
      {
        id: "usa-assistente",
        title: "Usa l'assistente",
        description: "Premi Ctrl+K, digita > e scrivi in italiano: \"Marco Rossi domani alle 18 PT\". Controlla la preview e conferma.",
      },
    ],
    faqs: [
      {
        question: "Come uso l'assistente (>)?",
        answer: "Premi Ctrl+K, digita > seguito dal tuo comando in italiano. Es: \"> Marco Rossi domani alle 18 PT\". Controlla la preview prima di confermare con Invio.",
      },
    ],
    miniTourSteps: [7, 8],
  },

  // ── 5. CONTROLLA CASSA ──
  {
    id: "controlla-cassa",
    title: "Controlla Cassa",
    icon: "Wallet",
    routePattern: "/cassa",
    intro: "Il centro di controllo finanziario: saldo, entrate, uscite e margine. Dati separati dalla dashboard per privacy.",
    actions: [
      {
        id: "registra-movimento",
        title: "Registra un movimento",
        description: "Entrate e uscite manuali. I pagamenti rate generano movimenti automatici. Il saldo si aggiorna in tempo reale.",
        action: { label: "Nuovo Movimento", type: "navigate", payload: "/cassa" },
      },
      {
        id: "conferma-spese-fisse",
        title: "Conferma le spese fisse",
        description: "Nel tab Spese Fisse trovi le spese ricorrenti in attesa. Seleziona e conferma ogni mese.",
      },
      {
        id: "consulta-libro-mastro",
        title: "Consulta il libro mastro",
        description: "Cronologia di tutti i movimenti con saldo progressivo. Filtra per mese e anno.",
      },
      {
        id: "vedi-aging-report",
        title: "Controlla le scadenze",
        description: "Il tab Scadenze mostra le rate in ritardo raggruppate per giorni di ritardo.",
      },
      {
        id: "analizza-previsioni",
        title: "Analizza le previsioni",
        description: "Il tab Previsioni proietta entrate, uscite e saldo a 3 mesi con grafici e timeline.",
      },
    ],
    faqs: [
      {
        question: "Perche' i dati economici non sono nella dashboard?",
        answer: "Per privacy. La dashboard mostra KPI operativi. I dati finanziari sono nella sezione Cassa, accessibile solo quando serve.",
      },
    ],
    miniTourSteps: [9, 10],
  },

  // ── 6. ESPLORA ESERCIZI ──
  {
    id: "esplora-esercizi",
    title: "Esplora Esercizi",
    icon: "Dumbbell",
    routePattern: "/esercizi",
    intro: "Il catalogo con oltre 390 esercizi classificati scientificamente su 14 dimensioni biomeccaniche.",
    actions: [
      {
        id: "filtra-pattern",
        title: "Filtra per pattern di movimento",
        description: "Squat, Hinge, Push, Pull, Core, Rotazione, Carry. Ogni chip mostra il conteggio degli esercizi che matchano.",
      },
      {
        id: "filtra-muscolo",
        title: "Filtra per gruppo muscolare",
        description: "Seleziona il muscolo target per vedere tutti gli esercizi che lo attivano come primario o secondario.",
      },
      {
        id: "vedi-dettaglio",
        title: "Apri il dettaglio",
        description: "Clicca un esercizio per muscoli coinvolti, classificazione completa, setup, esecuzione e note di sicurezza.",
      },
      {
        id: "consulta-scudo",
        title: "Consulta lo Scudo Clinico",
        description: "47 condizioni mediche mappate su ogni esercizio. Rosso = evitare, ambra = cautela, blu = adattare. Mai blocchi.",
      },
      {
        id: "filtra-attrezzatura",
        title: "Filtra per attrezzatura",
        description: "Corpo libero, bilanciere, manubri, kettlebell, cavi, macchina, TRX, elastici. Utile per programmare in base alla disponibilita'.",
      },
    ],
    faqs: [],
    miniTourSteps: [11, 12],
  },

  // ── 7. CREA SCHEDE ──
  {
    id: "crea-schede",
    title: "Crea Schede",
    icon: "ClipboardList",
    routePattern: "/schede",
    intro: "Il builder professionale per schede allenamento. Sessioni strutturate con avviamento, parte principale e stretching.",
    actions: [
      {
        id: "crea-scheda",
        title: "Crea una nuova scheda",
        description: "Tre opzioni: da zero, da template o con Smart Programming che suggerisce esercizi incrociando 14 dimensioni.",
        action: { label: "Nuova Scheda", type: "navigate", payload: "/schede" },
      },
      {
        id: "usa-builder",
        title: "Costruisci con il builder",
        description: "3 viste: Board (sessioni con drag & drop), Analisi (copertura muscolare e volume) e Anteprima (preview live).",
      },
      {
        id: "aggiungi-blocchi",
        title: "Usa i blocchi strutturati",
        description: "Circuito, Superset, AMRAP, EMOM, Tabata, For Time. Organizza gli esercizi in blocchi con tempi e ripetizioni.",
      },
      {
        id: "analizza-copertura",
        title: "Analizza la copertura muscolare",
        description: "Il tab Analisi mostra volume per muscolo, rapporti biomeccanici e dose-response con mappa anatomica.",
      },
      {
        id: "esporta-pdf",
        title: "Esporta in PDF clinico",
        description: "PDF professionale con foto esercizi, copertina, logo personalizzato e note per il cliente.",
      },
    ],
    faqs: [
      {
        question: "Come esporto una scheda allenamento?",
        answer: "Apri la scheda nel builder, clicca \"Esporta\" in alto. Scegli anteprima (stampa browser) o clinico (HTML ottimizzato per PDF con foto e logo).",
      },
    ],
    miniTourSteps: [13, 14],
  },

  // ── 8. MONITORA ALLENAMENTI ──
  {
    id: "monitora-allenamenti",
    title: "Monitora Allenamenti",
    icon: "Activity",
    routePattern: "/allenamenti",
    intro: "Attiva i programmi e traccia la compliance dei tuoi clienti settimana per settimana.",
    actions: [
      {
        id: "attiva-programma",
        title: "Attiva un programma",
        description: "Collega una scheda allenamento al cliente, imposta data inizio e fine. Lo stato diventa Attivo.",
      },
      {
        id: "registra-completamento",
        title: "Registra il completamento",
        description: "Per ogni sessione schedulata, segna se il cliente l'ha completata. La compliance si aggiorna in tempo reale.",
      },
      {
        id: "leggi-griglia",
        title: "Leggi la griglia compliance",
        description: "Righe = settimane, colonne = sessioni. Verde sopra l'80%, ambra sopra il 50%, rossa sotto il 50%.",
      },
      {
        id: "confronta-periodi",
        title: "Confronta periodi diversi",
        description: "Filtra per stato (Attivi, Da Attivare, Completati, Scaduti) per analizzare l'andamento nel tempo.",
      },
      {
        id: "filtra-cliente",
        title: "Filtra per cliente",
        description: "Usa il dropdown per vedere i programmi di un singolo cliente.",
      },
    ],
    faqs: [],
    miniTourSteps: [15],
  },

  // ── 9. COCKPIT GIORNALIERO ──
  {
    id: "cockpit-giornaliero",
    title: "Cockpit Giornaliero",
    icon: "Gauge",
    routePattern: "/oggi",
    intro: "La preparazione sessioni della giornata. 4 sezioni ordinate per urgenza: alert, problemi, pronti e non-cliente.",
    actions: [
      {
        id: "prepara-sessioni",
        title: "Prepara le sessioni",
        description: "Ogni cliente ha una card con stato clinico, readiness e azioni da completare prima della seduta.",
      },
      {
        id: "leggi-alert",
        title: "Leggi gli alert urgenti",
        description: "In alto: sessioni bloccate o a rischio. Colore rosso/ambra indica la priorita'.",
      },
      {
        id: "verifica-readiness",
        title: "Verifica la readiness clinica",
        description: "Il punteggio di ogni client indica se anamnesi, misurazioni e scheda sono aggiornati.",
      },
      {
        id: "lancia-azioni",
        title: "Lancia azioni rapide",
        description: "Dalla card: vai al profilo, completa anamnesi, registra misurazioni — tutto a un click.",
      },
      {
        id: "auto-refresh",
        title: "Aggiornamento automatico",
        description: "I dati si aggiornano ogni 60 secondi. Il bottone refresh in alto forza l'aggiornamento manuale.",
      },
    ],
    faqs: [],
    miniTourSteps: [],
  },

  // ── 10. RINNOVI & INCASSI ──
  {
    id: "rinnovi-incassi",
    title: "Rinnovi & Incassi",
    icon: "RefreshCw",
    routePattern: "/rinnovi-incassi",
    intro: "Una vista unica per rinnovare contratti e incassare rate scadute. Zero navigazione tra pagine.",
    actions: [
      {
        id: "incassa-rata",
        title: "Incassa una rata scaduta",
        description: "Seleziona il metodo di pagamento e clicca Incassa. 1 click, importo pre-compilato.",
      },
      {
        id: "rinnova-contratto",
        title: "Rinnova un contratto",
        description: "Il nuovo contratto si crea linkato all'originale con tipo, crediti e prezzo pre-compilati.",
      },
      {
        id: "filtra-stato-contratti",
        title: "Filtra per stato",
        description: "Tutti, Scaduti o In Scadenza. Badge con giorni residui o di ritardo.",
      },
      {
        id: "monitora-ritardi",
        title: "Monitora i ritardi",
        description: "Le rate in ritardo mostrano i giorni di ritardo con badge colorato e importo residuo.",
      },
      {
        id: "vedi-catena-rinnovi",
        title: "Consulta la catena rinnovi",
        description: "Nel dettaglio contratto vedi il contratto originale e tutti i rinnovi successivi con navigazione breadcrumb.",
      },
    ],
    faqs: [],
    miniTourSteps: [],
  },

  // ── 11. PROTEGGI I DATI ──
  {
    id: "proteggi-dati",
    title: "Proteggi i Dati",
    icon: "Shield",
    routePattern: "/impostazioni",
    intro: "Backup atomici, ripristino sicuro ed export GDPR. I tuoi dati restano sempre sul tuo computer.",
    actions: [
      {
        id: "crea-backup",
        title: "Crea un backup",
        description: "Copia atomica del database con checksum SHA-256. Verifica l'integrita' prima di archiviare.",
        action: { label: "Crea Backup", type: "navigate", payload: "/impostazioni" },
      },
      {
        id: "ripristina-backup",
        title: "Ripristina da backup",
        description: "Carica un file di backup precedente. Il sistema verifica integrita' e compatibilita' dello schema.",
      },
      {
        id: "esporta-gdpr",
        title: "Esporta in JSON (GDPR)",
        description: "Scarica tutti i dati del trainer in formato JSON per portabilita' e conformita' GDPR.",
      },
      {
        id: "verifica-sistema",
        title: "Verifica lo stato sistema",
        description: "Versione database, stato migrazioni e stato installazione in un colpo d'occhio.",
      },
      {
        id: "configura-connettivita",
        title: "Configura la connettivita'",
        description: "Tailscale per accesso da rete esterna e Funnel per link pubblici anamnesi.",
      },
    ],
    faqs: [
      {
        question: "Come faccio un backup dei dati?",
        answer: "Vai in Impostazioni, sezione Backup. Clicca \"Crea Backup\" per una copia atomica con checksum SHA-256. Per ripristinare, usa \"Ripristina\" e carica il file.",
      },
    ],
    miniTourSteps: [16],
  },

  // ── 12. DASHBOARD ──
  {
    id: "dashboard",
    title: "La tua Dashboard",
    icon: "LayoutDashboard",
    routePattern: "/",
    intro: "La panoramica operativa della giornata. Utile quando hai clienti, contratti e sessioni — torna qui ogni mattina.",
    actions: [
      {
        id: "leggi-kpi",
        title: "Leggi i KPI",
        description: "Clienti attivi, appuntamenti oggi e tasso di completamento in 3 anelli in alto.",
      },
      {
        id: "gestisci-todo",
        title: "Gestisci il riquadro Todo",
        description: "A sinistra: la CTA piu' urgente del giorno. Rate scadute, sessioni da completare, alert clinici.",
      },
      {
        id: "vedi-sessioni",
        title: "Consulta le sessioni",
        description: "A destra: lista delle sessioni di oggi con orario, cliente e stato.",
      },
      {
        id: "risolvi-alert",
        title: "Risolvi gli alert",
        description: "In basso: 4 categorie di warning. Eventi fantasma, rate scadute, contratti in scadenza, clienti inattivi. Ogni alert ha una CTA inline.",
      },
      {
        id: "usa-ctrlk",
        title: "Cerca ovunque (Ctrl+K)",
        description: "Premi Ctrl+K da qualsiasi pagina per cercare clienti, esercizi e navigare ovunque.",
      },
    ],
    faqs: [],
    miniTourSteps: [0],
  },
];

// ── Risolvi capitolo da pathname ──

export function resolveChapter(pathname: string): Chapter | null {
  // Exact match first (/, /clienti, /contratti, etc.)
  const exact = CHAPTERS.find((ch) => ch.routePattern === pathname);
  if (exact) return exact;

  // Prefix match for dynamic routes (e.g., /clienti/123 → profilo-anamnesi)
  // Sort by routePattern length descending for most-specific match
  const prefix = CHAPTERS
    .filter((ch) => ch.routePattern !== "/" && pathname.startsWith(ch.routePattern))
    .sort((a, b) => b.routePattern.length - a.routePattern.length);

  return prefix[0] ?? null;
}

// ── Resolve spotlight target by action ID ──

export function resolveSpotlight(actionId: string): SpotlightTarget | null {
  for (const chapter of CHAPTERS) {
    const action = chapter.actions.find((a) => a.id === actionId);
    if (action?.spotlight) return action.spotlight;
  }
  return null;
}

// ── Onboarding messages ──

export interface OnboardingStep {
  message: { sender: "bot"; text: string; actions?: BotAction[] };
  delayMs: number;
}

export const ONBOARDING_STEPS: OnboardingStep[] = [
  {
    delayMs: 0,
    message: {
      sender: "bot",
      text: "Ciao! Sono l'assistente di FitManager Studio+",
    },
  },
  {
    delayMs: 1200,
    message: {
      sender: "bot",
      text: "Posso mostrarti le basi in pochi minuti, oppure puoi esplorare da solo.",
      actions: [
        { label: "Mostrami le basi", type: "onboarding-choice", payload: "tour" },
        { label: "Esploro da solo", type: "onboarding-choice", payload: "skip" },
      ],
    },
  },
];

export const ONBOARDING_TOUR_RESPONSE = {
  sender: "bot" as const,
  text: "Ottimo! Ti mostro la Dashboard. Quando cambi pagina ti suggeriro' le funzionalita' principali.",
};

export const ONBOARDING_SKIP_RESPONSE = {
  sender: "bot" as const,
  text: "Nessun problema! Sono qui quando serve. Clicca su di me in qualsiasi momento.",
};

// ── Proactive triggers ──

export const PROACTIVE_TRIGGERS: ProactiveTrigger[] = [
  {
    id: "zero-clients",
    routePattern: "^/$",
    condition: "zero-clients",
    message: "Inizia registrando il tuo primo cliente!",
    action: { label: "Vai a Clienti", type: "navigate", payload: "/clienti" },
  },
  {
    id: "first-visit-schede",
    routePattern: "^/schede$",
    condition: "first-visit",
    message: "Qui crei le schede allenamento. Vuoi un tour rapido?",
    action: { label: "Mini-tour schede", type: "mini-tour", payload: "schede" },
  },
  {
    id: "first-visit-esercizi",
    routePattern: "^/esercizi$",
    condition: "first-visit",
    message: "Oltre 390 esercizi! Usa i filtri per trovare quello giusto.",
    action: { label: "Mostra filtri", type: "mini-tour", payload: "esercizi" },
  },
];

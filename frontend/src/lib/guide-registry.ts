// src/lib/guide-registry.ts
/**
 * Guide Registry — SSoT per contenuti guida adattivi al livello trainer.
 *
 * Consolida: guide-tours.ts FAQ + helpbot-data.ts chapter content.
 * Ogni pagina ha tips (filtrati per maturity level), FAQ e videoId.
 * Zero React, zero side-effect. Puro dati + lookup.
 */

import type { MaturityLevel } from "@/hooks/useTrainerMaturity";

// ── Types ──

export interface PageGuideTip {
  text: string;
  /** Mostra solo a questo livello o superiore */
  minLevel: MaturityLevel;
  /** Mostra solo fino a questo livello (incluso) */
  maxLevel: MaturityLevel;
}

export interface GuideFaq {
  question: string;
  answer: string;
}

export interface PageGuideEntry {
  /** Path pagina (es. "/clienti", "/cassa") */
  pagePath: string;
  /** Label pagina per UI */
  pageLabel: string;
  /** Tips filtrati per livello */
  tips: PageGuideTip[];
  /** FAQ contestuali */
  faqs: GuideFaq[];
  /** ID video da video-guides.ts */
  videoId?: string;
}

// ── Registry ──

const REGISTRY: PageGuideEntry[] = [
  // ── Dashboard ──
  {
    pagePath: "/",
    pageLabel: "Dashboard",
    tips: [
      { text: "Inizia registrando il tuo primo cliente dalla sidebar.", minLevel: 1, maxLevel: 1 },
      { text: "Completa l'anamnesi dei tuoi clienti per attivare lo Scudo Clinico nelle schede.", minLevel: 2, maxLevel: 2 },
      { text: "Gli alert in basso ti segnalano rate scadute, contratti in scadenza e clienti inattivi.", minLevel: 2, maxLevel: 3 },
      { text: "Usa Ctrl+K per cercare clienti, esercizi e navigare ovunque.", minLevel: 2, maxLevel: 4 },
    ],
    faqs: [
      { question: "Perche' i dati economici non sono nella dashboard?", answer: "Per privacy. La dashboard mostra KPI operativi (clienti attivi, appuntamenti, completamento). I dati finanziari sono nella sezione Cassa." },
    ],
    videoId: "panoramica",
  },

  // ── Clienti ──
  {
    pagePath: "/clienti",
    pageLabel: "Clienti",
    tips: [
      { text: "Clicca \"Nuovo Cliente\" per registrare il primo profilo. Servono solo nome e cognome.", minLevel: 1, maxLevel: 1 },
      { text: "Apri il profilo di un cliente per compilare l'anamnesi e seguire i 5 passi progressivi.", minLevel: 2, maxLevel: 2 },
      { text: "I chip filtro (Attivi, Inattivi, Con Rate Scadute) si combinano per analisi incrociate.", minLevel: 3, maxLevel: 4 },
      { text: "L'Avatar a 5 dimensioni nel profilo ti da' la situazione completa a colpo d'occhio.", minLevel: 3, maxLevel: 5 },
    ],
    faqs: [
      { question: "Come creo il primo cliente?", answer: "Clicca \"Nuovo Cliente\" in alto a destra. Compila nome, cognome e almeno un contatto. Dopo il salvataggio accedi al profilo completo con anamnesi e misurazioni." },
      { question: "Cosa significano i colori nell'Avatar?", answer: "Semaforo a 3 colori: verde = tutto ok, ambra = da verificare, rosso = azione urgente. Ogni box ha il suo semaforo indipendente." },
      { question: "In che ordine devo completare i passi?", answer: "Contratto prima di tutto (senza contratto non puoi prenotare sedute PT). Poi anamnesi, misurazioni, scheda e prima sessione." },
    ],
    videoId: "primo-cliente",
  },

  // ── Contratti ──
  {
    pagePath: "/contratti",
    pageLabel: "Contratti",
    tips: [
      { text: "Il contratto e' il primo passo dopo la registrazione: attiva copertura assicurativa e crediti sessione.", minLevel: 1, maxLevel: 2 },
      { text: "Genera rate automatiche dal dettaglio contratto: scegli numero, frequenza e data inizio.", minLevel: 2, maxLevel: 3 },
      { text: "I 7 badge colorati (da Insolvente a Saldato) mostrano lo stato finanziario a colpo d'occhio.", minLevel: 3, maxLevel: 5 },
    ],
    faqs: [
      { question: "Come registro un pagamento?", answer: "Apri il dettaglio contratto, scorri alle rate. Clicca \"Paga\" — puoi pagare l'intero o un parziale. Il saldo Cassa si aggiorna automaticamente." },
      { question: "I crediti si scalano automaticamente?", answer: "Si. Ogni sessione PT completata in agenda scala un credito. Quando crediti e saldo sono esauriti, il contratto si chiude." },
      { question: "Posso pagare una rata parzialmente?", answer: "Si. Clicca Paga, usa il quick button 50% o inserisci un importo personalizzato. Ogni pagamento e' tracciato nello storico." },
    ],
    videoId: "contratto-rate",
  },

  // ── Agenda ──
  {
    pagePath: "/agenda",
    pageLabel: "Agenda",
    tips: [
      { text: "Clicca uno slot vuoto per creare un appuntamento con data pre-compilata.", minLevel: 1, maxLevel: 2 },
      { text: "Trascina un evento per spostarlo. Ridimensiona dal bordo per cambiare durata.", minLevel: 2, maxLevel: 3 },
      { text: "I filtri per categoria (PT, Sala, Corso) e stato si combinano liberamente.", minLevel: 3, maxLevel: 5 },
    ],
    faqs: [
      { question: "Le sessioni scalano i crediti?", answer: "Si. Ogni sessione PT completata scala un credito dal contratto collegato. Il conteggio si aggiorna in tempo reale." },
    ],
    videoId: "agenda",
  },

  // ── Cassa ──
  {
    pagePath: "/cassa",
    pageLabel: "Cassa",
    tips: [
      { text: "I pagamenti delle rate generano movimenti automatici qui. Non serve registrarli a mano.", minLevel: 2, maxLevel: 2 },
      { text: "Il tab Spese Fisse ti permette di gestire affitto, assicurazione e utenze con conferma mensile.", minLevel: 2, maxLevel: 3 },
      { text: "Il tab Previsioni mostra proiezione a 3 mesi con cash runway e burn rate.", minLevel: 4, maxLevel: 5 },
    ],
    faqs: [
      { question: "Perche' devo confermare le spese fisse?", answer: "Le spese ricorrenti non vengono create automaticamente. Il sistema te le propone e tu confermi — cosi' mantieni il controllo." },
    ],
    videoId: "cassa",
  },

  // ── Esercizi ──
  {
    pagePath: "/esercizi",
    pageLabel: "Esercizi",
    tips: [
      { text: "500 esercizi con classificazione a 14 dimensioni: filtra per pattern, muscolo, attrezzatura.", minLevel: 1, maxLevel: 2 },
      { text: "Clicca un esercizio per vedere mappa muscolare, setup e note di sicurezza.", minLevel: 2, maxLevel: 3 },
      { text: "Lo Scudo Clinico colora gli esercizi in base all'anamnesi del cliente: rosso (evitare), ambra (cautela), blu (adattare).", minLevel: 3, maxLevel: 5 },
    ],
    faqs: [
      { question: "Cosa significano i colori nella scheda?", answer: "Rosso = controindicato per l'anamnesi del cliente. Ambra = richiede attenzione. Blu = modificare ROM, grip o carico. Non blocca nulla — la decisione e' tua." },
    ],
    videoId: "esercizi-safety",
  },

  // ── Schede ──
  {
    pagePath: "/schede",
    pageLabel: "Schede",
    tips: [
      { text: "Parti da un template per la prima scheda — puoi personalizzare tutto dopo.", minLevel: 1, maxLevel: 2 },
      { text: "Attiva l'analisi scientifica (icona provetta) per vedere score, copertura muscolare e safety in tempo reale.", minLevel: 3, maxLevel: 4 },
      { text: "L'export PDF clinico include foto esercizi, logo personalizzato e note di sicurezza.", minLevel: 3, maxLevel: 5 },
    ],
    faqs: [
      { question: "Come esporto una scheda?", answer: "Apri la scheda nel builder, clicca \"Esporta\" in alto a destra. Scegli anteprima rapida (stampa) o scarica clinico (PDF con foto e logo)." },
    ],
    videoId: "scheda-allenamento",
  },

  // ── Comunicazioni ──
  {
    pagePath: "/comunicazioni",
    pageLabel: "Comunicazioni",
    tips: [
      { text: "15 template WhatsApp pre-compilati: seleziona clienti, scegli il template e invia.", minLevel: 2, maxLevel: 3 },
      { text: "Ogni invio viene registrato automaticamente nel Registro per tracciare lo storico.", minLevel: 3, maxLevel: 5 },
    ],
    faqs: [
      { question: "I messaggi passano per un server?", answer: "No. FitManager apre WhatsApp direttamente sul tuo dispositivo via wa.me. Zero intermediari, privacy totale." },
    ],
  },

  // ── Impostazioni ──
  {
    pagePath: "/impostazioni",
    pageLabel: "Impostazioni",
    tips: [
      { text: "Crea un backup prima di ogni aggiornamento. Il file include checksum SHA-256 per verifica.", minLevel: 1, maxLevel: 5 },
    ],
    faqs: [
      { question: "Come faccio un backup?", answer: "Vai in Impostazioni > Backup. Clicca \"Crea Backup\". Per ripristinare, usa \"Ripristina\" e carica il file." },
    ],
    videoId: "backup-dati",
  },

  // ── Rinnovi & Incassi ──
  {
    pagePath: "/rinnovi-incassi",
    pageLabel: "Rinnovi & Incassi",
    tips: [
      { text: "Qui trovi contratti da rinnovare e rate in ritardo con pagamento 1-click.", minLevel: 2, maxLevel: 3 },
      { text: "Il badge urgenza cambia colore: rosso = scaduto, ambra = meno di 7 giorni, blu = pianificazione.", minLevel: 3, maxLevel: 5 },
    ],
    faqs: [],
  },

  // ── Monitoraggio ──
  {
    pagePath: "/allenamenti",
    pageLabel: "Monitoraggio",
    tips: [
      { text: "Attiva un programma impostando date inizio e fine per tracciare l'aderenza.", minLevel: 3, maxLevel: 4 },
      { text: "La griglia compliance mostra verde (>80%), ambra (>50%), rosso (<50%) per settimana.", minLevel: 4, maxLevel: 5 },
    ],
    faqs: [],
  },
];

// ── Lookup ──

/** Restituisce la guida per una pagina, con tips filtrati per livello. */
export function getPageGuide(
  pathname: string,
  level: MaturityLevel,
): PageGuideEntry | null {
  // Match esatto o base path (es. "/clienti/123" → "/clienti")
  const basePath = "/" + pathname.split("/").filter(Boolean)[0] || "/";
  const entry = REGISTRY.find(
    (e) => e.pagePath === pathname || e.pagePath === basePath,
  );
  if (!entry) return null;

  return {
    ...entry,
    tips: entry.tips.filter((t) => level >= t.minLevel && level <= t.maxLevel),
  };
}

/** Tutte le FAQ aggregate (per pagina /guida). */
export function getAllFaqs(): GuideFaq[] {
  const seen = new Set<string>();
  const faqs: GuideFaq[] = [];
  for (const entry of REGISTRY) {
    for (const faq of entry.faqs) {
      if (!seen.has(faq.question)) {
        seen.add(faq.question);
        faqs.push(faq);
      }
    }
  }
  return faqs;
}

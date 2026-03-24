// ════════════════════════════════════════════════════════════
// VIDEO GUIDES — Registro video-pillole per guida contestuale
// File puro dati. Zero React, zero side-effect.
//
// Ogni video ha 3 punti di accesso:
// 1. Pagina /guida — catalogo completo in griglia
// 2. Bussola (?) — popover contestuale nell'header di ogni sezione
// 3. Empty state — inline quando la lista è vuota (primo utilizzo)
// ════════════════════════════════════════════════════════════

export interface VideoGuide {
  /** ID univoco (usato come key React e per lookup) */
  id: string;
  /** Titolo breve per card e popover */
  title: string;
  /** Descrizione per la pagina guida (1-2 righe) */
  description: string;
  /** Path video relativo (servito da /videos/) */
  src: string;
  /** Path poster/thumbnail (primo frame o title card) */
  poster: string;
  /** Durata in secondi (display) */
  durationSec: number;
  /** Pagina/e dove appare la bussola (?) */
  pages: string[];
  /** Icona lucide-react (nome stringa per mapping nel componente) */
  iconName: string;
  /** true se il video è pronto (mp4 esiste), false = placeholder */
  ready: boolean;
}

// ── Registro video-pillole (ordine = ordine nella guida) ──

export const VIDEO_GUIDES: VideoGuide[] = [
  {
    id: "panoramica",
    title: "I Primi 10 Minuti",
    description:
      "Panoramica completa: dall'inserimento di un cliente alla registrazione di un pagamento.",
    src: "/videos/primi-10-minuti/primi-10-minuti.mp4",
    poster: "/videos/primi-10-minuti/cards/intro.png",
    durationSec: 78,
    pages: ["/guida"],
    iconName: "play-circle",
    ready: true,
  },
  {
    id: "primo-cliente",
    title: "Il Primo Cliente",
    description:
      "Crea un cliente, compila l'anamnesi strutturata e scopri il profilo operativo.",
    src: "/videos/01-primo-cliente/primo-cliente.mp4",
    poster: "/videos/01-primo-cliente/poster.png",
    durationSec: 45,
    pages: ["/clienti"],
    iconName: "user-plus",
    ready: false,
  },
  {
    id: "contratto-rate",
    title: "Contratto e Rate",
    description:
      "Crea un contratto, genera il piano rate automatico e registra il primo pagamento.",
    src: "/videos/02-contratto-rate/contratto-rate.mp4",
    poster: "/videos/02-contratto-rate/poster.png",
    durationSec: 60,
    pages: ["/contratti"],
    iconName: "file-text",
    ready: false,
  },
  {
    id: "agenda",
    title: "Agenda e Sessioni",
    description:
      "Pianifica appuntamenti, sposta con drag & drop e gestisci i crediti sessione.",
    src: "/videos/03-agenda/agenda.mp4",
    poster: "/videos/03-agenda/poster.png",
    durationSec: 45,
    pages: ["/agenda"],
    iconName: "calendar",
    ready: false,
  },
  {
    id: "cassa",
    title: "Cassa e Finanze",
    description:
      "Registra pagamenti, gestisci spese fisse e consulta le previsioni di bilancio.",
    src: "/videos/04-cassa/cassa.mp4",
    poster: "/videos/04-cassa/poster.png",
    durationSec: 60,
    pages: ["/cassa"],
    iconName: "wallet",
    ready: false,
  },
  {
    id: "esercizi-safety",
    title: "Esercizi e Scudo Clinico",
    description:
      "Esplora 500 esercizi con filtri biomeccanici e scopri il Safety Engine in azione.",
    src: "/videos/05-esercizi-safety/esercizi-safety.mp4",
    poster: "/videos/05-esercizi-safety/poster.png",
    durationSec: 60,
    pages: ["/esercizi"],
    iconName: "shield",
    ready: false,
  },
  {
    id: "scheda-allenamento",
    title: "Scheda Allenamento",
    description:
      "Costruisci una scheda con il builder, aggiungi blocchi e esporta il PDF clinico.",
    src: "/videos/06-scheda-allenamento/scheda-allenamento.mp4",
    poster: "/videos/06-scheda-allenamento/poster.png",
    durationSec: 60,
    pages: ["/schede"],
    iconName: "dumbbell",
    ready: false,
  },
  {
    id: "misurazioni-progressi",
    title: "Misurazioni e Progressi",
    description:
      "Registra misurazioni periodiche e visualizza i progressi con analisi clinica OMS/ACSM.",
    src: "/videos/07-misurazioni-progressi/misurazioni-progressi.mp4",
    poster: "/videos/07-misurazioni-progressi/poster.png",
    durationSec: 45,
    pages: ["/clienti"],
    iconName: "ruler",
    ready: false,
  },
  {
    id: "piano-alimentare",
    title: "Piano Alimentare LARN",
    description:
      "Genera un piano alimentare a 7 giorni basato sulle linee guida LARN italiane.",
    src: "/videos/08-piano-alimentare/piano-alimentare.mp4",
    poster: "/videos/08-piano-alimentare/poster.png",
    durationSec: 60,
    pages: ["/nutrizione"],
    iconName: "utensils",
    ready: false,
  },
  {
    id: "backup-dati",
    title: "Backup e Protezione Dati",
    description:
      "Crea backup sicuri, ripristina e esporta i tuoi dati in qualsiasi momento.",
    src: "/videos/09-backup-dati/backup-dati.mp4",
    poster: "/videos/09-backup-dati/poster.png",
    durationSec: 45,
    pages: ["/impostazioni"],
    iconName: "hard-drive",
    ready: false,
  },
];

// ── Lookup helpers ──

/** Trova un video per ID */
export function getVideoGuide(id: string): VideoGuide | undefined {
  return VIDEO_GUIDES.find((v) => v.id === id);
}

/** Trova i video contestuali per una pagina (per la bussola) */
export function getVideoGuidesForPage(pathname: string): VideoGuide[] {
  return VIDEO_GUIDES.filter((v) => v.pages.includes(pathname));
}

/** Solo video pronti (mp4 esiste) */
export function getReadyVideoGuides(): VideoGuide[] {
  return VIDEO_GUIDES.filter((v) => v.ready);
}

// src/lib/whatsapp-templates.ts
/**
 * Template messaggi WhatsApp pre-compilati.
 *
 * Tono: professionale ma caldo, come scriverebbe un PT italiano.
 * Il trainer puo' sempre modificare il testo prima di inviare.
 */

import { formatCurrency, formatShortDate } from "@/lib/format";

/** Reminder pagamento scaduto. */
export function waRateReminder(
  clientName: string,
  trainerName: string,
  importo: number,
  dataScadenza: string,
): string {
  return (
    `Ciao ${clientName}, ti scrivo per ricordarti che la rata di ${formatCurrency(importo)} ` +
    `era in scadenza il ${formatShortDate(dataScadenza)}. ` +
    `Puoi regolarizzare quando ti e' piu' comodo. ` +
    `A presto!\n— ${trainerName}`
  );
}

/** Conferma appuntamento (24h prima). */
export function waAppointmentReminder(
  clientName: string,
  trainerName: string,
  data: string,
  ora: string,
  titolo?: string,
): string {
  const sessione = titolo ? ` per "${titolo}"` : "";
  return (
    `Ciao ${clientName}, ti ricordo l'appuntamento${sessione} ` +
    `previsto per ${data} alle ${ora}. ` +
    `Se hai bisogno di spostare, scrivimi pure. ` +
    `A domani!\n— ${trainerName}`
  );
}

/** Invio scheda allenamento. */
export function waWorkoutShare(
  clientName: string,
  trainerName: string,
  schedaNome?: string,
): string {
  const nome = schedaNome ? ` "${schedaNome}"` : "";
  return (
    `Ciao ${clientName}, ho preparato la tua nuova scheda${nome}! ` +
    `La trovi gia' nel tuo programma. ` +
    `Se hai dubbi su qualche esercizio, chiedimi pure. ` +
    `Buon allenamento!\n— ${trainerName}`
  );
}

/** Benvenuto nuovo cliente + link anamnesi. */
export function waWelcome(
  clientName: string,
  trainerName: string,
  anamnesiLink?: string,
): string {
  const link = anamnesiLink
    ? `\n\nCompila il questionario iniziale qui: ${anamnesiLink}`
    : "";
  return (
    `Ciao ${clientName}, benvenuto/a! ` +
    `Sono ${trainerName}, il tuo personal trainer. ` +
    `Sono felice di iniziare questo percorso insieme.${link}` +
    `\n\nA presto!\n— ${trainerName}`
  );
}

/** Messaggio libero (solo numero pre-compilato, testo vuoto). */
export function waFreeMessage(trainerName: string): string {
  return `\n— ${trainerName}`;
}

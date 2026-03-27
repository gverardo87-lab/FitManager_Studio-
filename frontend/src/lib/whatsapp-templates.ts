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

/** Rinnovo contratto in scadenza — urgenza calibrata. */
export function waRenewalReminder(
  clientName: string,
  trainerName: string,
  pacchetto: string,
  giorniRimasti: number,
  creditiResidui: number,
): string {
  const urgenza = giorniRimasti <= 3
    ? "Il tuo pacchetto scade tra pochissimo"
    : giorniRimasti <= 7
      ? `Il tuo pacchetto "${pacchetto}" scade tra ${giorniRimasti} giorni`
      : `Il tuo pacchetto "${pacchetto}" e' in scadenza`;
  const crediti = creditiResidui > 0
    ? ` Hai ancora ${creditiResidui} ${creditiResidui === 1 ? "seduta" : "sedute"} disponibili — organizziamoci per usarle!`
    : "";
  return (
    `Ciao ${clientName}, ${urgenza}.${crediti} ` +
    `Vuoi che prepari il rinnovo? Scrivimi e troviamo la soluzione migliore per te. ` +
    `A presto!\n— ${trainerName}`
  );
}

/** Conferma contratto appena firmato. */
export function waContractConfirm(
  clientName: string,
  trainerName: string,
  pacchetto: string,
  crediti: number,
  dataScadenza: string,
): string {
  return (
    `Ciao ${clientName}, confermo l'attivazione del pacchetto "${pacchetto}" ` +
    `(${crediti} ${crediti === 1 ? "seduta" : "sedute"}, ` +
    `valido fino al ${formatShortDate(dataScadenza)}). ` +
    `Non vedo l'ora di iniziare! Se hai domande, scrivimi pure. ` +
    `A presto!\n— ${trainerName}`
  );
}

/** Re-engagement cliente inattivo — tono caldo, zero pressione. */
export function waCheckIn(
  clientName: string,
  trainerName: string,
  giorniInattivo: number,
): string {
  const tempo = giorniInattivo >= 30
    ? "E' passato un po' di tempo dall'ultima sessione"
    : `Sono ${giorniInattivo} giorni che non ci vediamo`;
  return (
    `Ciao ${clientName}! ${tempo} e volevo sapere come stai. ` +
    `Quando vuoi riprendere, sono qui. Anche solo per un allenamento di ripresa leggero. ` +
    `Fammi sapere!\n— ${trainerName}`
  );
}

/** Conferma appuntamento appena creato. */
export function waEventConfirm(
  clientName: string,
  trainerName: string,
  data: string,
  ora: string,
  titolo?: string,
): string {
  const sessione = titolo ? ` "${titolo}"` : "";
  return (
    `Ciao ${clientName}, ti confermo la sessione${sessione} ` +
    `per ${data} alle ${ora}. ` +
    `Ti aspetto! Se hai bisogno di spostare, scrivimi con anticipo. ` +
    `A presto!\n— ${trainerName}`
  );
}

/** Messaggio libero (solo numero pre-compilato, testo vuoto). */
export function waFreeMessage(trainerName: string): string {
  return `\n— ${trainerName}`;
}

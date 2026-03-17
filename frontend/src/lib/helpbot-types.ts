// ════════════════════════════════════════════════════════════
// HelpBot Types — Interfacce per il dispatcher contestuale
// Zero React, zero side-effect. Solo tipi.
// ════════════════════════════════════════════════════════════

/** Messaggio nella chat del bot */
export interface BotMessage {
  id: string;
  sender: "bot" | "user";
  text: string;
  /** Azioni inline (bottoni sotto il messaggio) */
  actions?: BotAction[];
  /** Timestamp ms */
  ts: number;
}

/** Azione eseguibile dal bot */
export interface BotAction {
  label: string;
  type: "navigate" | "mini-tour" | "dismiss" | "onboarding-choice";
  /** href per navigate, tour id per mini-tour */
  payload?: string;
}

/** Trigger proattivo basato su stato utente */
export interface ProactiveTrigger {
  id: string;
  /** Route pattern (regex string) */
  routePattern: string;
  condition: "zero-clients" | "zero-contracts" | "first-visit";
  message: string;
  action?: BotAction;
}

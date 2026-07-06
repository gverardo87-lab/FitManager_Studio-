// src/components/contracts/terminate/payment-methods.ts
// Costanti condivise dai rami del dialog Termina (config, zero logica).

export const PAYMENT_METHODS = ["CONTANTI", "POS", "BONIFICO"] as const;
export const METHOD_LABEL: Record<string, string> = {
  CONTANTI: "Contanti",
  POS: "POS",
  BONIFICO: "Bonifico",
};

/**
 * Contratto URL FE-1.0 per il focus contestuale di Rinnovi & Incassi.
 * Solo enum e ID: nessun dato personale o finanziario entra nell'URL.
 */

export const OVERDUE_RATE_FOCUS = "overdue-rate" as const;

export interface OverdueRateFocusIntent {
  focus: typeof OVERDUE_RATE_FOCUS;
  clientId: number;
  rateId: number | null;
}

function parsePositiveInteger(value: string | null): number | null {
  if (value === null || !/^\d+$/.test(value)) return null;
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) && parsed > 0 ? parsed : null;
}

function requirePositiveInteger(value: number, field: string): void {
  if (!Number.isSafeInteger(value) || value <= 0) {
    throw new TypeError(`${field} deve essere un intero positivo`);
  }
}

export function buildOverdueRateFocusHref(clientId: number, rateId?: number): string {
  requirePositiveInteger(clientId, "clientId");
  if (rateId !== undefined) requirePositiveInteger(rateId, "rateId");

  const params = new URLSearchParams({
    focus: OVERDUE_RATE_FOCUS,
    client_id: String(clientId),
  });
  if (rateId !== undefined) params.set("rate_id", String(rateId));
  return `/rinnovi-incassi?${params.toString()}`;
}

export function parseRenewalsFocus(search: string): OverdueRateFocusIntent | null {
  const params = new URLSearchParams(search);
  const focusValues = params.getAll("focus");
  const clientValues = params.getAll("client_id");
  const rateValues = params.getAll("rate_id");
  if (focusValues.length !== 1 || focusValues[0] !== OVERDUE_RATE_FOCUS) return null;
  if (clientValues.length !== 1 || rateValues.length > 1) return null;

  const clientId = parsePositiveInteger(clientValues[0]);
  if (clientId === null) return null;

  const rawRateId = rateValues[0] ?? null;
  const rateId = parsePositiveInteger(rawRateId);
  if (rawRateId !== null && rateId === null) return null;

  return {
    focus: OVERDUE_RATE_FOCUS,
    clientId,
    rateId,
  };
}

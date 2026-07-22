import { describe, expect, it } from "vitest";

import {
  buildOverdueRateFocusHref,
  parseRenewalsFocus,
} from "@/lib/renewals-focus";

describe("FE-1.0 — contratto URL Rinnovi & Incassi", () => {
  it("costruisce un href privacy-safe con soli intent e ID", () => {
    expect(buildOverdueRateFocusHref(7)).toBe(
      "/rinnovi-incassi?focus=overdue-rate&client_id=7",
    );
    expect(buildOverdueRateFocusHref(7, 41)).toBe(
      "/rinnovi-incassi?focus=overdue-rate&client_id=7&rate_id=41",
    );
  });

  it("parsa il target cliente e l'eventuale rata esatta", () => {
    expect(parseRenewalsFocus("?focus=overdue-rate&client_id=7")).toEqual({
      focus: "overdue-rate",
      clientId: 7,
      rateId: null,
    });
    expect(parseRenewalsFocus("?focus=overdue-rate&client_id=7&rate_id=41")).toEqual({
      focus: "overdue-rate",
      clientId: 7,
      rateId: 41,
    });
  });

  it.each([
    "?focus=unknown&client_id=7",
    "?focus=overdue-rate",
    "?focus=overdue-rate&client_id=0",
    "?focus=overdue-rate&client_id=-1",
    "?focus=overdue-rate&client_id=7.5",
    "?focus=overdue-rate&client_id=7&rate_id=abc",
    "?focus=overdue-rate&client_id=7&rate_id=0",
    "?focus=overdue-rate&focus=overdue-rate&client_id=7",
    "?focus=overdue-rate&client_id=7&client_id=8",
    "?focus=overdue-rate&client_id=7&rate_id=41&rate_id=42",
  ])("rifiuta parametri invalidi senza degradare a un target diverso: %s", (search) => {
    expect(parseRenewalsFocus(search)).toBeNull();
  });

  it("rifiuta ID non validi anche in costruzione", () => {
    expect(() => buildOverdueRateFocusHref(0)).toThrow(/clientId/);
    expect(() => buildOverdueRateFocusHref(7, -1)).toThrow(/rateId/);
  });
});

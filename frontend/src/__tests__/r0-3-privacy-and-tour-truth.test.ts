/** R0.3 / AC-R03-3 + tour Clienti post FE-0. */

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { TOUR_SCOPRI_FITMANAGER } from "@/lib/guide-tours";

describe("R0.3 — privacy Command Palette", () => {
  it("non legge campi monetari nel preview cliente globale", () => {
    const source = readFileSync(
      resolve(process.cwd(), "src/components/layout/CommandPalette.tsx"),
      "utf-8",
    );
    const start = source.indexOf("function ClientPreview");
    const end = source.indexOf("// PREVIEW: Exercise");

    expect(start).toBeGreaterThan(-1);
    expect(end).toBeGreaterThan(start);

    const clientPreview = source.slice(start, end);
    expect(clientPreview).not.toContain("client.totale_versato");
    expect(clientPreview).not.toContain("client.prezzo_totale_attivo");
    expect(clientPreview).not.toContain("Versato");
    expect(clientPreview).not.toContain("Totale Attivo");
  });
});

describe("R0.3 — tour Clienti aderente alla tabella reale", () => {
  it("descrive le colonne privacy-safe e i soli stati esistenti", () => {
    const clienti = TOUR_SCOPRI_FITMANAGER.steps.find(
      (step) => step.target === "clienti-header",
    );
    const description = clienti?.description ?? "";

    expect(description).toContain("Contatti");
    expect(description).toContain("Attenzioni");
    expect(description).toContain("Ultimo Evento");
    expect(description).toContain("Attivo e Inattivo");
    expect(description).not.toMatch(/crediti residui|contratti attivi|in pausa|archiviato/i);
  });
});

/**
 * AC-G84-5 (SPEC_G8.4 F2 / D-DISCLOSURE, ratifica founder 2026-07-06):
 * con Rate Scadute>0, prenotate-non-erogate>0, Residuo>0 e rimborso presente, i segnali sono
 * renderizzati SENZA alcuna interazione di disclosure; il dettaglio informativo (Acconto,
 * Crediti Sedute) è dietro «Mostra dettaglio». Fail: un segnale critico/warning dietro toggle.
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { ContractFinancialHero } from "@/components/contracts/ContractFinancialHero";
import type { ContractWithRates } from "@/types/api";

// Fixture minima: solo i campi che l'hero consuma (cast controllato).
// Cifre dal SSoT backend già "pronte" — l'hero non calcola nulla (F1).
const CONTRACT = {
  prezzo_totale: 1000,
  acconto: 200,
  totale_versato: 800,
  totale_rimborsato: 150,
  netto_incassato: 650,
  residuo: 350,
  rate_pagate: 2,
  rate_totali: 4,
  rate_scadute: 2,
  importo_da_rateizzare: 0,
  piano_allineato: true,
  crediti_totali: 10,
  sedute_programmate: 3,
  sedute_completate: 4,
  crediti_residui: 3,
  sedute_non_erogate_chiusura: 2,
} as unknown as ContractWithRates;

describe("AC-G84-5 — hero: segnali always-visible, dettaglio dietro disclosure", () => {
  it("renderizza i segnali critici/warning SENZA interazione", () => {
    render(<ContractFinancialHero contract={CONTRACT} />);

    // Residuo > 0 (con conteggio rate scadute — segnale rosso)
    expect(screen.getByText("Residuo")).toBeInTheDocument();
    expect(screen.getByText("2 scadute")).toBeInTheDocument();
    // Banner amber prenotate non erogate (unico segnale dell'azione recuperabile pre-G8.5)
    expect(screen.getByText(/sedute prenotate non erogate/)).toBeInTheDocument();
    // D-1 emendata (L2): il netto non è mai nudo — sub-label lordo − rimborsi visibile
    expect(screen.getByText("Incassato netto")).toBeInTheDocument();
    expect(screen.getByText(/lordo/)).toBeInTheDocument();
  });

  it("nasconde il dettaglio informativo di default e lo rivela col toggle", () => {
    render(<ContractFinancialHero contract={CONTRACT} />);

    // Collassati: Acconto, riga Crediti Sedute, Da Rateizzare (piano completo = informativa)
    expect(screen.queryByText("Acconto")).not.toBeInTheDocument();
    expect(screen.queryByText("Crediti Totali")).not.toBeInTheDocument();
    expect(screen.queryByText("Piano completo")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Mostra dettaglio/ }));

    expect(screen.getByText("Acconto")).toBeInTheDocument();
    expect(screen.getByText("Crediti Totali")).toBeInTheDocument();
    expect(screen.getByText("Piano completo")).toBeInTheDocument();
  });

  it("Da Rateizzare resta ALWAYS-VISIBLE quando il piano non copre (warning, non dettaglio)", () => {
    render(
      <ContractFinancialHero
        contract={{ ...CONTRACT, piano_allineato: false, importo_da_rateizzare: 350 } as unknown as ContractWithRates}
      />,
    );
    expect(screen.getByText("Da Rateizzare")).toBeInTheDocument();
  });
});

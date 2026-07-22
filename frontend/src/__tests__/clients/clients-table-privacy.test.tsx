/**
 * FE-0 / AC-FE0-1 — l'overview Clienti non espone numeri finanziari.
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ClientsTable } from "@/components/clients/ClientsTable";
import type { ClientEnriched } from "@/types/api";

const CLIENT = {
  id: 7,
  nome: "Ada",
  cognome: "Lovelace",
  email: "ada@example.test",
  telefono: "3331234567",
  stato: "Attivo",
  note_interne: null,
  ha_rate_scadute: true,
  ultimo_evento_data: null,
  contratti_attivi: 1,
  prezzo_totale_attivo: 98765,
  totale_versato: 43210,
  crediti_residui: 37,
} as unknown as ClientEnriched;

describe("FE-0 — overview Clienti privacy-safe", () => {
  it("non mostra importi o crediti e conserva solo il segnale amministrativo", () => {
    render(
      <ClientsTable
        clients={[CLIENT]}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    expect(screen.queryByRole("columnheader", { name: "Finanze" })).not.toBeInTheDocument();
    expect(screen.queryByRole("columnheader", { name: "Crediti" })).not.toBeInTheDocument();
    expect(screen.queryByText(/98[.,]?765/)).not.toBeInTheDocument();
    expect(screen.queryByText(/43[.,]?210/)).not.toBeInTheDocument();
    expect(screen.queryByText("37")).not.toBeInTheDocument();

    const action = screen.getByRole("link", { name: "Azione amministrativa" });
    expect(action).toHaveAttribute(
      "href",
      "/rinnovi-incassi?focus=overdue-rate&client_id=7",
    );
  });
});

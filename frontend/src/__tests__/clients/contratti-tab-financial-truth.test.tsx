/**
 * R0.3 / AC-R03-1..2 — il profilo cliente mostra la stessa posizione netta
 * di lista e dettaglio, con disclosure wire del rimborso e zero sottrazioni FE.
 */

import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ContrattiTab } from "@/components/clients/profile/ContrattiTab";
import { formatCurrency } from "@/lib/format";
import type { ContractListItem } from "@/types/api";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("@/hooks/useContracts", () => ({
  useClientContracts: () => ({
    data: { items: [CONTRACT], total: 1 },
    isLoading: false,
    isError: false,
    isFetching: false,
    refetch: vi.fn(),
  }),
  useClientWalletCredits: () => ({
    data: [],
    isError: false,
    isFetching: false,
    refetch: vi.fn(),
  }),
}));

const CONTRACT = {
  id: 91,
  tipo_pacchetto: "Pacchetto Rimborso",
  prezzo_totale: 1000,
  totale_versato: 800,
  totale_rimborsato: 150,
  netto_incassato: 650,
  crediti_usati: 4,
  crediti_totali: 10,
  sedute_completate: 3,
  sedute_penali: 1,
  sedute_non_erogate_chiusura: 0,
  lifecycle: "ATTIVO",
  money_substate: "PARZIALE",
  ha_rate_scadute: false,
  chiuso: false,
} as unknown as ContractListItem;

describe("R0.3 — verità finanziaria in ContrattiTab", () => {
  it("usa netto_incassato e spiega lordo/rimborso senza ricalcolarli", () => {
    render(<ContrattiTab clientId={7} />);

    const row = screen.getByRole("row", { name: /Pacchetto Rimborso/i });
    const finance = within(row).getAllByRole("cell")[1];
    const text = finance.textContent ?? "";

    expect(text).toContain(formatCurrency(650));
    expect(text).toContain(`lordo ${formatCurrency(800)}`);
    expect(text).toContain(`−${formatCurrency(150)}`);
    expect(text).not.toContain(`${formatCurrency(800)} /`);
  });
});

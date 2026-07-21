/**
 * FE-0 / AC-FE0-3/4 — il dettaglio Contratto non trasforma errori secondari in empty state.
 */

import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ContractHistoryTab } from "@/components/contracts/ContractHistoryTab";
import { ContractSessioniTab } from "@/components/contracts/ContractSessioniTab";
import type { ContractWithRates } from "@/types/api";

function failedQuery() {
  return {
    data: undefined,
    isLoading: false,
    isError: true,
    isFetching: false,
    refetch: vi.fn().mockResolvedValue({}),
  };
}

const state = {
  history: failedQuery(),
  sessions: failedQuery(),
};

vi.mock("@/hooks/useContracts", () => ({
  useContractHistory: () => state.history,
}));

vi.mock("@/hooks/useAgenda", () => ({
  useContractEvents: () => state.sessions,
}));

const CONTRACT = {
  id: 41,
  movimenti: [],
} as unknown as ContractWithRates;

describe("FE-0 — error state dettaglio Contratto", () => {
  beforeEach(() => {
    state.history = failedQuery();
    state.sessions = failedQuery();
  });

  it("Sessioni mostra errore, non un contratto senza sessioni", () => {
    render(<ContractSessioniTab contractId={41} />);

    expect(screen.getByText("Sessioni del contratto non disponibili")).toBeInTheDocument();
    expect(screen.queryByText("Nessuna sessione collegata a questo contratto")).not.toBeInTheDocument();
  });

  it("Storico mantiene il ledger vuoto ma dichiara la timeline non verificata", () => {
    render(<ContractHistoryTab contract={CONTRACT} />);

    expect(screen.getByText("Nessun movimento di cassa registrato.")).toBeInTheDocument();
    expect(screen.getByText("Attività del contratto non disponibile")).toBeInTheDocument();
    expect(screen.queryByText("Nessuna attività registrata.")).not.toBeInTheDocument();
  });
});


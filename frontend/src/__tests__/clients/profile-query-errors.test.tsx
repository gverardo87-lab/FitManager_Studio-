/**
 * FE-0 / AC-FE0-3/4 — gli errori del profilo non diventano «nessun dato».
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ContrattiTab } from "@/components/clients/profile/ContrattiTab";
import { MovimentiTab } from "@/components/clients/profile/MovimentiTab";
import { SessioniTab } from "@/components/clients/profile/SessioniTab";
import { isNotFoundError } from "@/lib/query-error";

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
  contracts: failedQuery(),
  sessions: failedQuery(),
  movements: failedQuery(),
};

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("@/hooks/useContracts", () => ({
  useClientContracts: () => state.contracts,
  useClientWalletCredits: () => ({
    data: [],
    isError: false,
    isFetching: false,
    refetch: vi.fn(),
  }),
}));

vi.mock("@/hooks/useAgenda", () => ({
  useClientEvents: () => state.sessions,
}));

vi.mock("@/hooks/useMovements", () => ({
  useMovements: () => state.movements,
}));

describe("FE-0 — error state tab profilo cliente", () => {
  beforeEach(() => {
    state.contracts = failedQuery();
    state.sessions = failedQuery();
    state.movements = failedQuery();
  });

  it("Contratti mostra errore e retry, non l'empty state", () => {
    render(<ContrattiTab clientId={7} />);

    expect(screen.getByText("Contratti non disponibili")).toBeInTheDocument();
    expect(screen.queryByText("Nessun contratto attivo")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Riprova" }));
    expect(state.contracts.refetch).toHaveBeenCalledOnce();
  });

  it("Sessioni mostra errore, non l'empty state", () => {
    render(<SessioniTab clientId={7} />);

    expect(screen.getByText("Sessioni non disponibili")).toBeInTheDocument();
    expect(screen.queryByText("Nessuna sessione registrata")).not.toBeInTheDocument();
  });

  it("Movimenti mostra indisponibilità, mai uno zero implicito", () => {
    render(<MovimentiTab clientId={7} />);

    expect(screen.getByText("Movimenti non disponibili")).toBeInTheDocument();
    expect(screen.queryByText("Nessun movimento registrato")).not.toBeInTheDocument();
  });
});

describe("FE-0 — classificazione not-found", () => {
  it("accetta soltanto una risposta HTTP 404", () => {
    expect(isNotFoundError({ isAxiosError: true, response: { status: 404 } })).toBe(true);
    expect(isNotFoundError({ isAxiosError: true, response: { status: 500 } })).toBe(false);
    expect(isNotFoundError(new Error("rete non disponibile"))).toBe(false);
  });
});


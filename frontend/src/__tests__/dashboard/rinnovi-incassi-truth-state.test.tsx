/**
 * FE-0 / AC-FE0-2 — una worklist non verificata non può diventare «Tutto in regola».
 */

import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import RinnoviIncassiPage from "@/app/(dashboard)/rinnovi-incassi/page";

function emptyQuery() {
  return {
    data: { items: [], total: 0 },
    isLoading: false,
    isError: false,
    isFetching: false,
    refetch: vi.fn().mockResolvedValue({}),
  };
}

const state = {
  overdue: emptyQuery(),
  expiring: emptyQuery(),
  recover: emptyQuery(),
  suspended: emptyQuery(),
  credits: emptyQuery(),
  refunds: emptyQuery(),
};

vi.mock("@/hooks/useDashboard", () => ({
  useOverdueRates: () => state.overdue,
  useExpiringContracts: () => state.expiring,
  useClientsToRecover: () => state.recover,
  useSuspendedContracts: () => state.suspended,
}));

vi.mock("@/hooks/useContracts", () => ({
  useCreditiDaIncassare: () => state.credits,
  useRimborsiDaErogare: () => state.refunds,
  useMarkRenewalOutcome: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateContract: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("@/hooks/useRates", () => ({
  usePayRate: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("@/hooks/useTrainerName", () => ({
  useTrainerName: () => "Trainer Test",
}));

vi.mock("@/lib/page-reveal", () => ({
  usePageReveal: () => ({
    revealClass: () => "",
    revealStyle: () => undefined,
  }),
}));

vi.mock("@/components/contracts/ContractSheet", () => ({
  ContractSheet: () => null,
}));

vi.mock("@/components/contracts/CreditiDaIncassareCard", () => ({
  CreditiDaIncassareCard: ({ items }: { items: unknown[] }) => (
    items.length > 0 ? <div>{items.length} crediti operativi</div> : null
  ),
}));

vi.mock("@/components/contracts/RimborsiDaErogareCard", () => ({
  RimborsiDaErogareCard: ({ items }: { items: unknown[] }) => (
    items.length > 0 ? <div>{items.length} rimborsi operativi</div> : null
  ),
}));

vi.mock("@/components/contracts/IncassaResiduoDialog", () => ({
  IncassaResiduoDialog: () => null,
}));

vi.mock("@/components/contracts/TerminateContractDialog", () => ({
  TerminateContractDialog: () => null,
}));

function resetQueries() {
  state.overdue = emptyQuery();
  state.expiring = emptyQuery();
  state.recover = emptyQuery();
  state.suspended = emptyQuery();
  state.credits = emptyQuery();
  state.refunds = emptyQuery();
}

describe("FE-0 — verità percettiva Rinnovi & Incassi", () => {
  beforeEach(resetQueries);

  it("mostra errore e non lo converte in stato positivo", () => {
    state.overdue = {
      ...emptyQuery(),
      data: undefined as never,
      isError: true,
    };

    render(<RinnoviIncassiPage />);

    expect(screen.getByText("Impossibile verificare tutte le azioni")).toBeInTheDocument();
    expect(screen.getByText(/rate in ritardo/)).toBeInTheDocument();
    expect(screen.queryByText("Tutto in regola")).not.toBeInTheDocument();
    expect(screen.queryByText("Nessuna azione richiesta")).not.toBeInTheDocument();
  });

  it("mostra lo stato positivo solo quando tutte le fonti sono verificate e vuote", () => {
    render(<RinnoviIncassiPage />);

    expect(screen.getByText("Tutto in regola")).toBeInTheDocument();
    expect(screen.getByText("Nessuna azione richiesta")).toBeInTheDocument();
  });

  it("include i crediti differiti nel conteggio delle azioni", () => {
    state.credits = {
      ...emptyQuery(),
      data: { items: [{ id: 1 }], total: 1 },
    };

    render(<RinnoviIncassiPage />);

    expect(screen.getByText("1 azione richiesta")).toBeInTheDocument();
    expect(screen.getByText("1 crediti operativi")).toBeInTheDocument();
    expect(screen.queryByText("Tutto in regola")).not.toBeInTheDocument();
  });
});


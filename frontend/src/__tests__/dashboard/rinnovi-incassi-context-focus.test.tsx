import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { StrictMode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import RinnoviIncassiPage from "@/app/(dashboard)/rinnovi-incassi/page";
import type { OverdueRateItem } from "@/types/api";

vi.mock("next/navigation", () => ({
  usePathname: () => window.location.pathname,
  useSearchParams: () => new URLSearchParams(window.location.search),
}));

function emptyQuery() {
  return {
    data: { items: [], total: 0 },
    isLoading: false,
    isError: false,
    isFetching: false,
    refetch: vi.fn().mockResolvedValue({}),
  };
}

function overdueRate(rateId: number, clientId = 7): OverdueRateItem {
  return {
    rate_id: rateId,
    data_scadenza: "2026-06-01",
    importo_previsto: 100,
    importo_saldato: 0,
    importo_residuo: 100,
    giorni_ritardo: 20,
    stato: "SCADUTA",
    contract_id: 90 + rateId,
    tipo_pacchetto: "PT",
    client_id: clientId,
    client_nome: clientId === 7 ? "Ada" : "Grace",
    client_cognome: clientId === 7 ? "Lovelace" : "Hopper",
    client_telefono: null,
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
const payRateMutate = vi.fn();

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
  usePayRate: () => ({ mutate: payRateMutate, isPending: false }),
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

vi.mock("@/components/ui/whatsapp-button", () => ({
  WhatsAppButton: () => null,
}));

vi.mock("@/components/contracts/ContractSheet", () => ({ ContractSheet: () => null }));
vi.mock("@/components/contracts/CreditiDaIncassareCard", () => ({
  CreditiDaIncassareCard: () => null,
}));
vi.mock("@/components/contracts/RimborsiDaErogareCard", () => ({
  RimborsiDaErogareCard: () => null,
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

function setMotionPreference(reduce: boolean) {
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    value: vi.fn().mockReturnValue({ matches: reduce }),
  });
}

describe("FE-1.0 — focus contestuale Rinnovi & Incassi", () => {
  beforeEach(() => {
    resetQueries();
    payRateMutate.mockReset();
    window.history.replaceState({}, "", "/rinnovi-incassi");
    setMotionPreference(false);
    Object.defineProperty(HTMLElement.prototype, "scrollIntoView", {
      configurable: true,
      value: vi.fn(),
    });
  });

  it("porta focus e scroll sulla rata del cliente senza eseguire pagamenti", async () => {
    state.overdue = {
      ...emptyQuery(),
      data: { items: [overdueRate(41), overdueRate(42, 8)], total: 2 },
    };
    window.history.replaceState({}, "", "/rinnovi-incassi?focus=overdue-rate&client_id=7");

    const { container } = render(<RinnoviIncassiPage />);
    const target = container.querySelector<HTMLElement>('[data-overdue-rate-id="41"]');

    await waitFor(() => expect(target).toHaveFocus());
    expect(target?.scrollIntoView).toHaveBeenCalledWith({ behavior: "smooth", block: "center" });
    expect(await screen.findByText("Aperta da Clienti")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Rata in ritardo di Ada Lovelace selezionata");
    expect(payRateMutate).not.toHaveBeenCalled();
  });

  it("apre il pagamento guidato senza incassare al primo click", () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 6, 24, 12));

    try {
      state.overdue = {
        ...emptyQuery(),
        data: { items: [overdueRate(41)], total: 1 },
      };

      render(<RinnoviIncassiPage />);

      fireEvent.click(screen.getByRole("button", { name: "Incassa" }));

      expect(payRateMutate).not.toHaveBeenCalled();
      expect(screen.getByText("Data Pagamento")).toBeInTheDocument();
      expect(screen.getByRole("combobox")).toHaveTextContent("CONTANTI");

      fireEvent.click(screen.getByRole("button", { name: /Paga.*100/ }));

      expect(payRateMutate).toHaveBeenCalledWith(
        {
          rateId: 41,
          importo: 100,
          metodo: "CONTANTI",
          data_pagamento: "2026-07-24",
        },
        { onSuccess: expect.any(Function) },
      );
    } finally {
      vi.useRealTimers();
    }
  });

  it("mantiene marker e highlight nel doppio ciclo di React StrictMode", async () => {
    state.overdue = { ...emptyQuery(), data: { items: [overdueRate(41)], total: 1 } };
    window.history.replaceState({}, "", "/rinnovi-incassi?focus=overdue-rate&client_id=7");

    const { container } = render(<StrictMode><RinnoviIncassiPage /></StrictMode>);
    const target = container.querySelector<HTMLElement>('[data-overdue-rate-id="41"]');

    await waitFor(() => expect(target).toHaveFocus());
    expect(await screen.findByText("Aperta da Clienti")).toBeInTheDocument();
    expect(target).toHaveClass("ring-2");
  });

  it("dichiara la molteplicità e mostra la prima rata nell'ordine ricevuto", async () => {
    state.overdue = {
      ...emptyQuery(),
      data: { items: [overdueRate(41), overdueRate(43)], total: 2 },
    };
    window.history.replaceState({}, "", "/rinnovi-incassi?focus=overdue-rate&client_id=7");

    const { container } = render(<RinnoviIncassiPage />);
    const first = container.querySelector<HTMLElement>('[data-overdue-rate-id="41"]');

    await waitFor(() => expect(first).toHaveFocus());
    expect(await screen.findByText("Aperta da Clienti · prima di 2 rate")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Mostrata la prima di 2 rate");
  });

  it("usa rate_id soltanto quando appartiene anche al cliente indicato", async () => {
    state.overdue = {
      ...emptyQuery(),
      data: { items: [overdueRate(41), overdueRate(42, 8)], total: 2 },
    };
    window.history.replaceState(
      {},
      "",
      "/rinnovi-incassi?focus=overdue-rate&client_id=7&rate_id=42",
    );

    render(<RinnoviIncassiPage />);

    expect(await screen.findByText("Azione non più presente")).toBeInTheDocument();
    expect(payRateMutate).not.toHaveBeenCalled();
  });

  it("seleziona la rata esatta quando rate_id e client_id sono coerenti", async () => {
    state.overdue = {
      ...emptyQuery(),
      data: { items: [overdueRate(41), overdueRate(43)], total: 2 },
    };
    window.history.replaceState(
      {},
      "",
      "/rinnovi-incassi?focus=overdue-rate&client_id=7&rate_id=43",
    );

    const { container } = render(<RinnoviIncassiPage />);
    const exactTarget = container.querySelector<HTMLElement>('[data-overdue-rate-id="43"]');

    await waitFor(() => expect(exactTarget).toHaveFocus());
    expect(await screen.findByText("Aperta da Clienti")).toBeInTheDocument();
    expect(screen.queryByText(/prima di 2 rate/)).not.toBeInTheDocument();
  });

  it("mostra il fallback stale quando l'azione è stata risolta", async () => {
    window.history.replaceState({}, "", "/rinnovi-incassi?focus=overdue-rate&client_id=7");

    render(<RinnoviIncassiPage />);

    expect(await screen.findByText("Azione non più presente")).toBeInTheDocument();
    expect(
      screen.getByText("Questa azione non è più presente; potrebbe essere già stata risolta."),
    ).toBeInTheDocument();
    expect(screen.getByText("Tutto in regola")).toBeInTheDocument();
  });

  it("riprende il focus dopo un errore e il retry", async () => {
    const refetch = vi.fn().mockResolvedValue({});
    state.overdue = { ...emptyQuery(), data: { items: [overdueRate(41)], total: 1 } };
    state.expiring = {
      ...emptyQuery(),
      isError: true,
      refetch,
    };
    window.history.replaceState({}, "", "/rinnovi-incassi?focus=overdue-rate&client_id=7");

    const view = render(<RinnoviIncassiPage />);
    const status = screen.getByRole("status");
    expect(status).toBeEmptyDOMElement();
    fireEvent.click(screen.getByRole("button", { name: "Riprova verifica" }));
    expect(refetch).toHaveBeenCalledOnce();

    state.expiring = emptyQuery();
    view.rerender(<RinnoviIncassiPage />);

    const target = view.container.querySelector<HTMLElement>('[data-overdue-rate-id="41"]');
    await waitFor(() => expect(target).toHaveFocus());
    expect(screen.getByRole("status")).toBe(status);
    expect(status).toHaveTextContent("Rata in ritardo di Ada Lovelace selezionata");
  });

  it("mantiene la live region dal loading fino al target pronto", async () => {
    state.overdue = { ...emptyQuery(), data: undefined as never, isLoading: true };
    window.history.replaceState({}, "", "/rinnovi-incassi?focus=overdue-rate&client_id=7");

    const view = render(<RinnoviIncassiPage />);
    const status = screen.getByRole("status");
    expect(status).toBeEmptyDOMElement();

    state.overdue = { ...emptyQuery(), data: { items: [overdueRate(41)], total: 1 } };
    view.rerender(<RinnoviIncassiPage />);

    await waitFor(() => expect(status).toHaveTextContent("Rata in ritardo di Ada Lovelace"));
    expect(screen.getByRole("status")).toBe(status);
  });

  it("disattiva lo scroll animato quando l'utente preferisce movimento ridotto", async () => {
    setMotionPreference(true);
    state.overdue = {
      ...emptyQuery(),
      data: { items: [overdueRate(41)], total: 1 },
    };
    window.history.replaceState({}, "", "/rinnovi-incassi?focus=overdue-rate&client_id=7");

    const { container } = render(<RinnoviIncassiPage />);
    const target = container.querySelector<HTMLElement>('[data-overdue-rate-id="41"]');

    await waitFor(() => expect(target?.scrollIntoView).toHaveBeenCalledWith({
      behavior: "auto",
      block: "center",
    }));
  });

  it("ripristina il contesto quando la browser history cambia", async () => {
    state.overdue = {
      ...emptyQuery(),
      data: { items: [overdueRate(41)], total: 1 },
    };

    const view = render(<RinnoviIncassiPage />);
    const target = view.container.querySelector<HTMLElement>('[data-overdue-rate-id="41"]');
    expect(target).not.toHaveFocus();

    act(() => {
      window.history.replaceState({}, "", "/rinnovi-incassi?focus=overdue-rate&client_id=7");
      window.dispatchEvent(new PopStateEvent("popstate"));
    });
    view.rerender(<RinnoviIncassiPage />);

    await waitFor(() => expect(target).toHaveFocus());
  });
});

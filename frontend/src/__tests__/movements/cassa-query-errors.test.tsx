/**
 * FE-0 / Cassa — un fallimento di rete non diventa zero, lista vuota o stato in regola.
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import CassaPage from "@/app/(dashboard)/cassa/page";
import { AndamentoTab } from "@/components/movements/AndamentoTab";
import { RecurringExpensesTab } from "@/components/movements/RecurringExpensesTab";
import { SplitLedgerView } from "@/components/movements/SplitLedgerView";

function failedQuery() {
  return {
    data: undefined,
    isLoading: false,
    isError: true,
    isFetching: false,
    refetch: vi.fn().mockResolvedValue({}),
  };
}

function readyQuery<T>(data: T) {
  return {
    data,
    isLoading: false,
    isError: false,
    isFetching: false,
    refetch: vi.fn().mockResolvedValue({}),
  };
}

const state = {
  movements: readyQuery({ items: [], total: 0 }),
  stats: failedQuery(),
  pending: readyQuery({ items: [] }),
  balance: readyQuery({ saldo_attuale: 1200 }),
  trend: failedQuery(),
  recurring: failedQuery(),
  splitIncome: failedQuery(),
  splitExpense: readyQuery({ items: [], total: 0 }),
  clients: readyQuery({ items: [] }),
};

vi.mock("@/hooks/useMovements", () => ({
  useMovements: (params?: { tipo?: string }) => {
    if (params?.tipo === "ENTRATA") return state.splitIncome;
    if (params?.tipo === "USCITA") return state.splitExpense;
    return state.movements;
  },
  useMovementStats: () => state.stats,
  usePendingExpenses: () => state.pending,
  useCashBalance: () => state.balance,
  useFinancialTrend: () => state.trend,
  useConfirmExpenses: () => ({ isPending: false, mutate: vi.fn() }),
  usePreviewConfirmExpenses: () => ({ isPending: false, mutate: vi.fn() }),
}));

vi.mock("@/hooks/useRecurringExpenses", () => ({
  useRecurringExpenses: () => state.recurring,
  useCreateRecurringExpense: () => ({ isPending: false, mutate: vi.fn() }),
  useUpdateRecurringExpense: () => ({ isPending: false, mutate: vi.fn() }),
  useDeleteRecurringExpense: () => ({ isPending: false, mutate: vi.fn() }),
  useCloseRecurringExpense: () => ({ isPending: false, mutate: vi.fn() }),
  useCloseRecurringExpensePreview: () => ({ isPending: false, mutate: vi.fn() }),
}));

vi.mock("@/hooks/useClients", () => ({
  useClients: () => state.clients,
}));

vi.mock("@/lib/page-reveal", () => ({
  usePageReveal: () => ({
    revealClass: (_delay: number, className = "") => className,
    revealStyle: () => ({}),
  }),
}));

vi.mock("@/components/guide/PageVideoGuide", () => ({ PageVideoGuide: () => null }));
vi.mock("@/components/movements/MovementsTable", () => ({ MovementsTable: () => <div>Mastro verificato</div> }));
vi.mock("@/components/movements/MovementSheet", () => ({ MovementSheet: () => null }));
vi.mock("@/components/movements/DeleteMovementDialog", () => ({ DeleteMovementDialog: () => null }));
vi.mock("@/components/movements/CashAuditSheet", () => ({ CashAuditSheet: () => null }));
vi.mock("@/components/movements/AgingReport", () => ({ AgingReport: () => null }));
vi.mock("@/components/movements/ForecastTab", () => ({ ForecastTab: () => null }));

describe("FE-0 — truth states finanziari della Cassa", () => {
  beforeEach(() => {
    state.movements = readyQuery({ items: [], total: 0 });
    state.stats = failedQuery();
    state.pending = readyQuery({ items: [] });
    state.balance = readyQuery({ saldo_attuale: 1200 });
    state.trend = failedQuery();
    state.recurring = failedQuery();
    state.splitIncome = failedQuery();
    state.splitExpense = readyQuery({ items: [], total: 0 });
    state.clients = readyQuery({ items: [] });
    window.history.replaceState({}, "", "/cassa");
    sessionStorage.clear();
  });

  it("blocca il riepilogo non verificato ma mantiene indipendente il libro mastro", () => {
    render(<CassaPage />);

    expect(screen.getByText("Riepilogo di cassa non disponibile")).toBeInTheDocument();
    expect(screen.getByText(/I valori non vengono mostrati come zero/)).toBeInTheDocument();
    expect(screen.getByText("Statistiche del periodo non disponibili")).toBeInTheDocument();
    expect(screen.getByText("Mastro verificato")).toBeInTheDocument();

    fireEvent.click(screen.getAllByRole("button", { name: "Riprova" })[0]);
    expect(state.balance.refetch).toHaveBeenCalledOnce();
    expect(state.stats.refetch).toHaveBeenCalledOnce();
  });

  it("mantiene KPI mensili verificati quando fallisce solo il saldo", () => {
    state.balance = failedQuery();
    state.stats = readyQuery({
      totale_entrate: 500,
      totale_uscite_variabili: 100,
      totale_uscite_fisse: 200,
      margine_netto: 200,
      saldo_inizio_mese: 1000,
      saldo_fine_mese: 1200,
      chart_data: [],
    });

    render(<CassaPage />);

    expect(screen.getByText("Riepilogo di cassa non disponibile")).toBeInTheDocument();
    expect(screen.getByText("Entrate")).toBeInTheDocument();
    expect(screen.getByText("Margine Netto")).toBeInTheDocument();
    expect(screen.queryByText("Statistiche del periodo non disponibili")).not.toBeInTheDocument();
  });

  it("Andamento dichiara la serie non verificata invece di mostrare KPI a zero", () => {
    render(<AndamentoTab />);

    expect(screen.getByText("Andamento finanziario non disponibile")).toBeInTheDocument();
    expect(screen.queryByText("Cash flow reale")).not.toBeInTheDocument();
  });

  it("Spese fisse sospende lista e mutazioni quando la configurazione fallisce", () => {
    render(<RecurringExpensesTab anno={2026} mese={7} />);

    expect(screen.getByText("Spese fisse non disponibili")).toBeInTheDocument();
    expect(screen.queryByText("Nessuna spesa ricorrente configurata")).not.toBeInTheDocument();
    expect(screen.queryByText("Aggiungi Spesa Fissa")).not.toBeInTheDocument();
  });

  it("Entrate e Uscite falliscono in modo indipendente", () => {
    render(<SplitLedgerView />);

    expect(screen.getByText("Entrate non disponibili")).toBeInTheDocument();
    expect(screen.getByText("Uscite")).toBeInTheDocument();
  });
});

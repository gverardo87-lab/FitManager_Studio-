/**
 * FE-0 / AC-FE0-6 — le dipendenze Cliente nei form non diventano menu vuoti ambigui.
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { afterAll, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

import { EventForm } from "@/components/agenda/EventForm";
import { ContractForm } from "@/components/contracts/ContractForm";
import type { CalendarEvent } from "@/components/agenda/calendar-setup";

function loadingQuery() {
  return {
    data: undefined,
    isLoading: true,
    isError: false,
    isFetching: true,
    refetch: vi.fn().mockResolvedValue({}),
  };
}

function failedQuery() {
  return {
    data: undefined,
    isLoading: false,
    isError: true,
    isFetching: false,
    refetch: vi.fn().mockResolvedValue({}),
  };
}

function emptyQuery() {
  return {
    data: { items: [], total: 0 },
    isLoading: false,
    isError: false,
    isFetching: false,
    refetch: vi.fn().mockResolvedValue({}),
  };
}

type ClientsQueryState =
  | ReturnType<typeof loadingQuery>
  | ReturnType<typeof failedQuery>
  | ReturnType<typeof emptyQuery>;

const state: { clients: ClientsQueryState } = { clients: loadingQuery() };
const originalResizeObserver = globalThis.ResizeObserver;

beforeAll(() => {
  globalThis.ResizeObserver = class ResizeObserver {
    constructor(_callback: ResizeObserverCallback) {}
    observe(_target: Element, _options?: ResizeObserverOptions) {}
    unobserve(_target: Element) {}
    disconnect() {}
  };
});

afterAll(() => {
  globalThis.ResizeObserver = originalResizeObserver;
});

vi.mock("@/hooks/useClients", () => ({
  useClients: () => state.clients,
}));

describe("FE-0 — dipendenza Cliente nei form", () => {
  beforeEach(() => {
    state.clients = loadingQuery();
  });

  it("Contratto espone il caricamento e sospende la creazione", () => {
    render(<ContractForm onSubmit={vi.fn()} isPending={false} />);

    expect(screen.getByRole("status")).toHaveTextContent("Caricamento elenco clienti");
    expect(screen.getByRole("combobox")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Crea Contratto" })).toBeDisabled();
    expect(screen.queryByText(/Nessun cliente disponibile/)).not.toBeInTheDocument();
  });

  it("Contratto dichiara l’errore, offre retry e non lo presenta come lista vuota", () => {
    state.clients = failedQuery();
    render(<ContractForm onSubmit={vi.fn()} isPending={false} />);

    expect(screen.getAllByText("Clienti non disponibili").length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText(/Nessun cliente disponibile/)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Crea Contratto" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Riprova" }));
    expect(state.clients.refetch).toHaveBeenCalledOnce();
  });

  it("Evento PT distingue la lista realmente vuota e sospende il write-path obbligatorio", () => {
    state.clients = emptyQuery();
    render(<EventForm onSubmit={vi.fn()} isPending={false} />);

    expect(screen.getAllByText(/Nessun cliente disponibile/).length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText("Clienti non disponibili")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Crea Evento" })).toBeDisabled();
  });

  it("Evento PT espone l’errore con retry senza inventare zero clienti", () => {
    state.clients = failedQuery();
    render(<EventForm onSubmit={vi.fn()} isPending={false} />);

    expect(screen.getAllByText("Clienti non disponibili").length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText(/Nessun cliente disponibile/)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Crea Evento" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Riprova" }));
    expect(state.clients.refetch).toHaveBeenCalledOnce();
  });

  it("Rinnovo Contratto conserva la relazione fissata e non viene bloccato dal lookup", () => {
    state.clients = failedQuery();
    render(
      <ContractForm
        renewalDefaults={{
          id_cliente: 42,
          tipo_pacchetto: "Percorso 10",
          crediti_totali: 10,
          prezzo_totale: 500,
        }}
        onSubmit={vi.fn()}
        isPending={false}
      />,
    );

    expect(screen.getByText(/cliente già collegato resta invariato/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Rinnova Contratto" })).toBeEnabled();
  });

  it("Evento senza dipendenza Cliente resta operativo se il lookup fallisce", () => {
    state.clients = failedQuery();
    const event = {
      id: 7,
      title: "Corso serale",
      categoria: "CORSO",
      stato: "Programmato",
      start: new Date(2026, 6, 22, 18, 0),
      end: new Date(2026, 6, 22, 19, 0),
      id_cliente: null,
      note: null,
    } as CalendarEvent;

    render(<EventForm event={event} onSubmit={vi.fn()} isPending={false} />);

    expect(screen.queryByText("Clienti non disponibili")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Salva Modifiche" })).toBeEnabled();
  });

  it("Evento PT in modifica conserva il Cliente persistito se il lookup fallisce", () => {
    state.clients = failedQuery();
    const event = {
      id: 8,
      title: "PT esistente",
      categoria: "PT",
      stato: "Programmato",
      start: new Date(2026, 6, 22, 17, 0),
      end: new Date(2026, 6, 22, 18, 0),
      id_cliente: 42,
      note: null,
    } as CalendarEvent;

    render(<EventForm event={event} onSubmit={vi.fn()} isPending={false} />);

    expect(screen.getByText(/cliente già collegato resta invariato/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Salva Modifiche" })).toBeEnabled();
  });
});

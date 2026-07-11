/**
 * AC-G97-3 / G9.7.3-D5 (ADR-024 D-DERIVATO-MAI-NUDO) — sulle worklist dashboard il
 * conteggio crediti si spiega dalla STESSA vista: lo sheet «Contratti in scadenza»
 * porta il sub-label «N svolte · M penali» letto dal wire (mai ricalcolo inline).
 * Fail della classe: un credito «sparito» a video (usati 4 con 2 svolte e nessuna spiegazione).
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { ExpiringContractsSheet } from "@/components/dashboard/ExpiringContractsSheet";
import type { ExpiringContractItem } from "@/types/api";

function renderSheet() {
  // il WhatsAppButton dentro lo sheet usa useLogCommunication → serve il provider
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <ExpiringContractsSheet open onOpenChange={() => {}} />
    </QueryClientProvider>,
  );
}

function mkItem(overrides: Partial<ExpiringContractItem>): ExpiringContractItem {
  return {
    contract_id: 39,
    tipo_pacchetto: "Pacchetto 10",
    data_inizio: "2026-06-01",
    data_scadenza: "2026-07-20",
    giorni_rimasti: 9,
    crediti_totali: 10,
    crediti_usati: 4,
    crediti_residui: 6,
    sedute_completate: 2,
    sedute_penali: 2,
    prezzo_totale: 1000,
    client_id: 1,
    client_nome: "Test",
    client_cognome: "Founder",
    client_telefono: null,
    ...overrides,
  };
}

const state = { items: [mkItem({})] };

vi.mock("@/hooks/useDashboard", () => ({
  useExpiringContracts: () => ({ data: { items: state.items, total: state.items.length }, isLoading: false }),
}));

vi.mock("@/hooks/useTrainerName", () => ({
  useTrainerName: () => "Trainer Test",
}));

describe("G9.7.3/D5 — lo sheet in-scadenza spiega l'occupazione dalla vista", () => {
  it("con penali > 0 il sub-label mostra svolte E penali (dal wire)", () => {
    state.items = [mkItem({})];
    renderSheet();
    const subLabel = screen.getByText(/2 svolte/).closest("p")!;
    expect(subLabel.textContent).toContain("2 svolte");
    expect(subLabel.textContent).toContain("2 penali");
  });

  it("con zero penali il segmento penali non esiste (segnale, non rumore)", () => {
    state.items = [mkItem({ crediti_usati: 2, crediti_residui: 8, sedute_penali: 0 })];
    renderSheet();
    expect(screen.getByText(/2 svolte/)).toBeInTheDocument();
    expect(screen.queryByText(/penali/)).not.toBeInTheDocument();
  });
});

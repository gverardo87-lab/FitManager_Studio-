/**
 * AC-G84-4 (F3.a/d — gate bilaterale intatto): all'apertura del dialog Termina su ramo
 * CREDITO_TRAINER nessun bottone è `aria-pressed` e il submit è disabilitato finché l'utente
 * non sceglie DAVVERO; la raccomandazione è SOLO visiva (badge «Consigliato», mai pre-selezione).
 * AC-G84-7 (F3.e): sedute penali visibili nel breakdown come conteggio SEPARATO dalle erogate.
 * AC-G84-8 (F3.f): RINUNCIA_ESPRESSA senza nota → submit resta disabilitato.
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { TerminateContractDialog } from "@/components/contracts/TerminateContractDialog";
import { SettlementBreakdown } from "@/components/contracts/terminate/SettlementBreakdown";
import type { ContractSettlementPreview } from "@/types/api";

const PREVIEW_TRAINER: ContractSettlementPreview = {
  esito: "CREDITO_TRAINER",
  motivo_chiusura: "TERMINAZIONE_SALDO_TRAINER",
  valore_servizio_reso: 400,
  conguaglio: 300,
  importo_rimborso: 0,
  credito_trainer: 300,
  quota_da_stornare: 900,
  sedute_erogate: 4,
  sedute_totali: 10,
  sedute_prenotate: 0,
  sedute_penali: 0,
  metodo_rimborso_richiesto: false,
  azioni_permesse: ["A_CREDITO", "INCASSA_ORA", "RINUNCIA_ESPRESSA"],
  azione_consigliata: "INCASSA_ORA",
  policy_mode: "pro_sedute",
  messaggio: "Conguaglio calcolato (pro-rata sedute): saldo a tuo favore.",
};

vi.mock("@/hooks/useContracts", () => ({
  useSettlementPreview: () => ({ data: PREVIEW_TRAINER, isLoading: false, isError: false }),
  useTerminateContract: () => ({ mutate: vi.fn(), isPending: false }),
}));

function renderDialog() {
  return render(
    <TerminateContractDialog contractId={1} clientLabel="Test" open onOpenChange={() => {}} />,
  );
}

describe("AC-G84-4 — ramo trainer: scelta esplicita, raccomandazione solo visiva", () => {
  it("all'apertura NESSUN bottone è aria-pressed e il submit è disabilitato", () => {
    renderDialog();
    const pressed = screen
      .getAllByRole("button")
      .filter((b) => b.getAttribute("aria-pressed") === "true");
    expect(pressed).toHaveLength(0);
    expect(screen.getByRole("button", { name: "Termina contratto" })).toBeDisabled();
  });

  it("il badge «Consigliato» sta su Incassa-ora (advisory dal wire) e MAI sulla rinuncia", () => {
    renderDialog();
    const incassa = screen.getByRole("button", { name: /Incassa ora e chiudi/ });
    const rinuncia = screen.getByRole("button", { name: /Rinuncia e chiudi/ });
    expect(incassa).toHaveTextContent("Consigliato");
    expect(rinuncia).not.toHaveTextContent("Consigliato");
    // il suggerito NON è selezionato: badge ≠ pre-selezione (ADR-018 D-SCELTA)
    expect(incassa.getAttribute("aria-pressed")).toBe("false");
  });

  it("la scelta reale abilita il submit e marca aria-pressed", () => {
    renderDialog();
    const aCredito = screen.getByRole("button", { name: /Metti a credito e chiudi/ });
    fireEvent.click(aCredito);
    expect(aCredito.getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByRole("button", { name: "Termina contratto" })).toBeEnabled();
  });

  it("AC-G84-8: rinuncia senza nota → submit disabilitato; con nota → abilitato", () => {
    renderDialog();
    fireEvent.click(screen.getByRole("button", { name: /Rinuncia e chiudi/ }));
    expect(screen.getByRole("button", { name: "Termina contratto" })).toBeDisabled();
    fireEvent.change(screen.getByPlaceholderText(/sconto concordato/i), {
      target: { value: "Accordo bonario a chiusura." },
    });
    expect(screen.getByRole("button", { name: "Termina contratto" })).toBeEnabled();
  });
});

describe("AC-G84-7 — sedute penali nel breakdown (conteggio separato)", () => {
  it("con sedute_penali > 0 mostra la riga dedicata, mai sommata alle erogate", () => {
    render(<SettlementBreakdown data={{ ...PREVIEW_TRAINER, sedute_penali: 2 }} />);
    expect(screen.getByText("Sedute penali (contabilizzate)")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("4 / 10")).toBeInTheDocument(); // erogate INVARIATE
  });

  it("con sedute_penali = 0 la riga non esiste", () => {
    render(<SettlementBreakdown data={PREVIEW_TRAINER} />);
    expect(screen.queryByText(/Sedute penali/)).not.toBeInTheDocument();
  });
});

/**
 * AC-G97-3 (SPEC_G9.7.3, ADR-024 D-DERIVATO-MAI-NUDO) — sul caso reale del founder
 * (12 totali · 5 svolte · 2 penali · 5 residui) l'occupazione è SPIEGABILE dalla vista:
 * - il banner penali è un SEGNALE always-visible (mai dietro toggle) con l'equazione
 *   totali = programmate + svolte + penali + residui;
 * - con zero penali il banner non esiste (niente rumore).
 * Fail della classe: un credito «sparito» a video (l'hero che mostra 0·5·5 su 12).
 */

import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { ContractFinancialHero } from "@/components/contracts/ContractFinancialHero";
import type { ContractWithRates } from "@/types/api";

function mkContract(overrides: Partial<ContractWithRates>): ContractWithRates {
  return {
    id: 39,
    id_cliente: 1,
    tipo_pacchetto: "Pacchetto 12",
    data_vendita: null,
    data_inizio: "2026-01-01",
    data_scadenza: "2026-06-30",
    crediti_totali: 12,
    crediti_usati: 7,
    prezzo_totale: 1200,
    acconto: 0,
    totale_versato: 1200,
    stato_pagamento: "SALDATO",
    note: null,
    chiuso: false,
    rinnovo_di: null,
    totale_rimborsato: 0,
    quota_stornata: 0,
    data_chiusura: null,
    motivo_chiusura: null,
    netto_incassato: 1200,
    rate: [],
    client_nome: "Test",
    client_cognome: "Founder",
    residuo: 0,
    percentuale_versata: 100,
    importo_da_rateizzare: 0,
    somma_rate_previste: 0,
    somma_rate_saldate: 0,
    somma_rate_pendenti: 0,
    piano_allineato: true,
    importo_disallineamento: 0,
    rate_totali: 0,
    rate_pagate: 0,
    rate_scadute: 0,
    sedute_programmate: 0,
    sedute_completate: 5,
    sedute_rinviate: 0,
    sedute_penali: 2,
    crediti_residui: 5,
    sedute_non_erogate_chiusura: 0,
    lifecycle: "attivo",
    money_substate: "saldato",
    contratto_originale: null,
    rinnovi_successivi: [],
    ...overrides,
  } as ContractWithRates;
}

describe("AC-G97-3 — l'occupazione si spiega dalla vista (caso founder 12·5·2)", () => {
  it("con penali > 0 il banner-segnale è visibile SENZA aprire il dettaglio, con l'equazione completa", () => {
    render(<ContractFinancialHero contract={mkContract({})} />);
    const banner = screen.getByText(/crediti occupati da penali/).closest("p")!;
    expect(banner).toBeInTheDocument();
    // L'equazione: 12 totali = 0 programmate + 5 svolte + 2 penali + 5 residui
    expect(banner.textContent).toContain("12 totali");
    expect(banner.textContent).toContain("0 programmate");
    expect(banner.textContent).toContain("5 svolte");
    expect(banner.textContent).toContain("2 penali");
    expect(banner.textContent).toContain("5 residui");
  });

  it("con zero penali il banner non esiste (segnale, non rumore)", () => {
    render(
      <ContractFinancialHero
        contract={mkContract({ sedute_penali: 0, crediti_usati: 5, crediti_residui: 7 })}
      />,
    );
    expect(screen.queryByText(/crediti occupati da penali/)).not.toBeInTheDocument();
  });

  it("le rinviate compaiono nel banner come informativo («non occupano») quando presenti", () => {
    render(<ContractFinancialHero contract={mkContract({ sedute_rinviate: 3 })} />);
    expect(screen.getByText(/3 rinviate \(non occupano\)/)).toBeInTheDocument();
  });
});

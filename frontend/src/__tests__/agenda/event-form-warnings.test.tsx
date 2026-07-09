/**
 * AC-G97-1 (SPEC_G9.7.1 + G9.7.1-bis, decisioni founder 2026-07-09) — mai-silenzio sul
 * write-path eventi, SENZA blocchi che il backend non impone:
 * - B4: cliente senza contratti attivi → warning «senza contratto» PRIMA del submit,
 *   submit PERMESSO (escape hatch legittimo e consapevole, P-D4/ADR-025).
 * - G9.7.1-bis: crediti esauriti sui contratti ATTIVI → warning soft calibrato, submit
 *   PERMESSO (il vecchio hard-block rendeva il B4 irraggiungibile per i clienti nuovi).
 * - B5 (invariante «mai 201 muto»): il predicato `isPtOrfanoCreato` decide il toast
 *   dedicato — presidiato qui perché sopravviva a P5 (la scelta a 3 vie lo riuserà).
 */

import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { EventForm } from "@/components/agenda/EventForm";
import { isPtOrfanoCreato } from "@/hooks/useAgenda";

// ── Fixture clienti: i 3 casi dell'asse (audit 2026-07-07 + verifica LIVE 2026-07-09) ──

const CLIENTS = [
  // Caso founder: soli contratti CHIUSI con crediti residui (il numero cumulativo li conta)
  { id: 1, nome: "Chiusi", cognome: "ConCrediti", stato: "Attivo", crediti_residui: 2, contratti_attivi: 0 },
  // Cliente nuovo: zero contratti, zero crediti (il caso che l'hard-block intrappolava)
  { id: 2, nome: "Nuovo", cognome: "SenzaContratti", stato: "Attivo", crediti_residui: 0, contratti_attivi: 0 },
  // Contratto attivo ma crediti esauriti
  { id: 3, nome: "Attivo", cognome: "Esaurito", stato: "Attivo", crediti_residui: 0, contratti_attivi: 1 },
  // Cliente sano: contratto attivo con crediti
  { id: 4, nome: "Attivo", cognome: "ConCrediti", stato: "Attivo", crediti_residui: 5, contratti_attivi: 1 },
];

vi.mock("@/hooks/useClients", () => ({
  useClients: () => ({ data: { items: CLIENTS, total: CLIENTS.length } }),
}));

function renderForm(clientId: number) {
  return render(
    <EventForm defaultClientId={clientId} onSubmit={vi.fn()} isPending={false} />,
  );
}

const submitButton = () => screen.getByRole("button", { name: "Crea Evento" });
const WARNING_SENZA_CONTRATTO = /non ha contratti attivi/;
const WARNING_ESAURITO = /Crediti esauriti sui contratti attivi/;

describe("AC-G97-1 — B4: warning PRIMA, mai blocco", () => {
  it("caso founder (soli chiusi, crediti residui > 0): warning «senza contratto», submit permesso", () => {
    renderForm(1);
    expect(screen.getByText(WARNING_SENZA_CONTRATTO)).toBeInTheDocument();
    expect(submitButton()).toBeEnabled();
  });

  it("cliente nuovo (zero contratti, zero crediti): warning «senza contratto», submit PERMESSO — l'hard-block è morto", () => {
    renderForm(2);
    expect(screen.getByText(WARNING_SENZA_CONTRATTO)).toBeInTheDocument();
    expect(screen.queryByText(WARNING_ESAURITO)).not.toBeInTheDocument();
    expect(submitButton()).toBeEnabled();
  });

  it("contratto attivo con crediti esauriti: warning calibrato, submit permesso (G9.7.1-bis)", () => {
    renderForm(3);
    expect(screen.getByText(WARNING_ESAURITO)).toBeInTheDocument();
    expect(screen.queryByText(WARNING_SENZA_CONTRATTO)).not.toBeInTheDocument();
    expect(submitButton()).toBeEnabled();
  });

  it("cliente sano: NESSUN warning, submit permesso", () => {
    renderForm(4);
    expect(screen.queryByText(WARNING_SENZA_CONTRATTO)).not.toBeInTheDocument();
    expect(screen.queryByText(WARNING_ESAURITO)).not.toBeInTheDocument();
    expect(submitButton()).toBeEnabled();
  });
});

describe("AC-G97-1 — B5: invariante «mai 201 muto» (predicato del toast dedicato)", () => {
  it("PT con cliente e senza contratto → orfano (toast dedicato, mai success generico)", () => {
    expect(isPtOrfanoCreato({ categoria: "PT", id_cliente: 7, id_contratto: null })).toBe(true);
  });

  it("PT agganciato a un contratto → NON orfano (success generico)", () => {
    expect(isPtOrfanoCreato({ categoria: "PT", id_cliente: 7, id_contratto: 42 })).toBe(false);
  });

  it("PT senza cliente / categorie non-PT → mai orfano", () => {
    expect(isPtOrfanoCreato({ categoria: "PT", id_cliente: null, id_contratto: null })).toBe(false);
    expect(isPtOrfanoCreato({ categoria: "SALA", id_cliente: 7, id_contratto: null })).toBe(false);
    expect(isPtOrfanoCreato({ categoria: "COLLOQUIO", id_cliente: 7, id_contratto: null })).toBe(false);
  });
});

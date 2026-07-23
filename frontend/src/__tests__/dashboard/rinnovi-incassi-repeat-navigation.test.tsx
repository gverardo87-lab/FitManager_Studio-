import { act, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { useOverdueRateContextFocus } from "@/hooks/useOverdueRateContextFocus";
import type { OverdueRateItem } from "@/types/api";

vi.mock("next/navigation", () => ({
  usePathname: () => window.location.pathname,
  useSearchParams: () => new URLSearchParams(window.location.search),
}));

const RATE: OverdueRateItem = {
  rate_id: 41,
  data_scadenza: "2026-06-01",
  importo_previsto: 100,
  importo_saldato: 0,
  importo_residuo: 100,
  giorni_ritardo: 20,
  stato: "SCADUTA",
  contract_id: 131,
  tipo_pacchetto: "PT",
  client_id: 7,
  client_nome: "Ada",
  client_cognome: "Lovelace",
  client_telefono: null,
};

function Harness({ navigation }: { navigation: number }) {
  const context = useOverdueRateContextFocus({
    items: [RATE],
    isLoading: false,
    hasError: false,
  });

  return (
    <div data-navigation={navigation}>
      <p role="status">{context.announcement}</p>
      <div
        ref={context.targetRateId === RATE.rate_id ? context.targetRef : undefined}
        data-testid="target-rate"
        tabIndex={-1}
      >
        {context.markerLabel}
      </div>
    </div>
  );
}

describe("FE-1.0 — navigazione contestuale ripetuta", () => {
  it("riesegue focus e marker tornando allo stesso deep-link dalla pagina Clienti", async () => {
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: vi.fn().mockReturnValue({ matches: false }),
    });
    const scrollIntoView = vi.fn();
    Object.defineProperty(HTMLElement.prototype, "scrollIntoView", {
      configurable: true,
      value: scrollIntoView,
    });
    window.history.replaceState({}, "", "/rinnovi-incassi?focus=overdue-rate&client_id=7");

    const view = render(<Harness navigation={1} />);
    const target = screen.getByTestId("target-rate");
    await waitFor(() => expect(target).toHaveFocus());
    await screen.findByText("Aperta da Clienti");
    expect(scrollIntoView).toHaveBeenCalledTimes(1);

    act(() => {
      target.blur();
      window.history.replaceState({}, "", "/clienti");
    });
    view.rerender(<Harness navigation={2} />);

    act(() => {
      window.history.replaceState({}, "", "/rinnovi-incassi?focus=overdue-rate&client_id=7");
    });
    view.rerender(<Harness navigation={3} />);

    await waitFor(() => expect(scrollIntoView).toHaveBeenCalledTimes(2));
    expect(target).toHaveFocus();
    expect(await screen.findByText("Aperta da Clienti")).toBeInTheDocument();
  });
});

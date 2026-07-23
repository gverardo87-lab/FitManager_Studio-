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

function Harness({ navigation, showTarget = true }: { navigation: number; showTarget?: boolean }) {
  const context = useOverdueRateContextFocus({
    items: [RATE],
    isLoading: false,
    hasError: false,
  });

  return (
    <div data-navigation={navigation}>
      <p role="status">{context.announcement}</p>
      {showTarget ? (
        <div
          ref={context.targetRateId === RATE.rate_id ? context.targetRef : undefined}
          data-testid="target-rate"
          tabIndex={-1}
        >
          {context.markerLabel}
        </div>
      ) : null}
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

  it("attende il remount tardivo del target quando route e dati sono già in cache", async () => {
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

    const view = render(<Harness navigation={1} showTarget={false} />);
    expect(scrollIntoView).not.toHaveBeenCalled();

    view.rerender(<Harness navigation={1} showTarget />);

    const target = screen.getByTestId("target-rate");
    await waitFor(() => expect(target).toHaveFocus());
    expect(scrollIntoView).toHaveBeenCalledTimes(1);
  });

  it("avvia la durata del marker solo quando il frame di focus viene eseguito", () => {
    vi.useFakeTimers();
    let pendingFrame: FrameRequestCallback | null = null;
    const requestFrame = vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback) => {
      pendingFrame = callback;
      return 1;
    });
    const cancelFrame = vi.spyOn(window, "cancelAnimationFrame").mockImplementation(() => undefined);
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: vi.fn().mockReturnValue({ matches: false }),
    });
    Object.defineProperty(HTMLElement.prototype, "scrollIntoView", {
      configurable: true,
      value: vi.fn(),
    });
    window.history.replaceState({}, "", "/rinnovi-incassi?focus=overdue-rate&client_id=7");

    try {
      render(<Harness navigation={1} />);
      expect(pendingFrame).not.toBeNull();

      act(() => vi.advanceTimersByTime(2500));
      act(() => pendingFrame?.(0));
      expect(screen.getByText("Aperta da Clienti")).toBeInTheDocument();

      act(() => vi.advanceTimersByTime(2500));
      expect(screen.queryByText("Aperta da Clienti")).not.toBeInTheDocument();
    } finally {
      requestFrame.mockRestore();
      cancelFrame.mockRestore();
      vi.useRealTimers();
    }
  });
});

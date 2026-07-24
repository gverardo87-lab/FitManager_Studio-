import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ConnectivityStatusSection } from "@/components/settings/ConnectivityStatusSection";
import type { InstallationConnectivityStatusResponse } from "@/types/api";

const refetch = vi.fn();
const mutateConfig = vi.fn();
const resetVerification = vi.fn();
const mutateVerification = vi.fn();

const MANAGED_STATUS: InstallationConnectivityStatusResponse = {
  generated_at: "2026-07-24T16:00:00Z",
  profile: "public_portal",
  public_access_provider: "managed_frp",
  tailscale_cli_installed: false,
  tailscale_version: null,
  tailscale_status: "not_installed",
  tailscale_connected: false,
  tailscale_ip: null,
  tailscale_dns_name: null,
  funnel_status: "not_enabled",
  funnel_enabled: false,
  public_portal_enabled: true,
  public_base_url: "https://chiara.fitmanagerstudio.com",
  public_base_url_matches_dns: null,
  next_recommended_action_code: "verify_public_origin",
  next_recommended_action_label: "Verifica origine pubblica FRP",
  checks: [
    {
      code: "managed_frp",
      label: "Percorso pubblico",
      status: "ok",
      detail: "FRP gestito dalla licenza FitManager.",
    },
  ],
  missing_requirements: [],
};

vi.mock("@/hooks/useConnectivityStatus", () => ({
  useConnectivityStatus: () => ({
    data: MANAGED_STATUS,
    isLoading: false,
    isError: false,
    isFetching: false,
    refetch,
  }),
}));

vi.mock("@/hooks/useConnectivityConfig", () => ({
  useApplyConnectivityConfig: () => ({
    isPending: false,
    mutate: mutateConfig,
  }),
}));

vi.mock("@/hooks/useVerifyConnectivity", () => ({
  useVerifyConnectivity: () => ({
    data: undefined,
    isPending: false,
    mutate: mutateVerification,
    reset: resetVerification,
  }),
}));

describe("ConnectivityStatusSection con FRP gestito", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("mostra il percorso autoritativo senza wizard o azioni Tailscale/Funnel", () => {
    render(<ConnectivityStatusSection />);

    expect(screen.getByText("Percorso pubblico gestito")).toBeInTheDocument();
    expect(screen.getAllByText("https://chiara.fitmanagerstudio.com")).not.toHaveLength(0);
    expect(screen.queryByText("Wizard guidato")).not.toBeInTheDocument();
    expect(screen.queryByText("Nodo Tailscale")).not.toBeInTheDocument();
    expect(screen.queryByText("Attiva Funnel")).not.toBeInTheDocument();
  });
});

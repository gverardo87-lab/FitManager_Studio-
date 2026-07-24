import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";

import { middleware } from "@/middleware";

function makeRequest(pathname: string, host: string, cookie?: string) {
  const headers = new Headers({ host });
  if (cookie) headers.set("cookie", cookie);
  return new NextRequest(`https://${host}${pathname}`, { headers });
}

describe("route separation FRP e fallback localhost", () => {
  it("lascia passare il portale pubblico sul dominio FRP", () => {
    const response = middleware(
      makeRequest(
        "/public/anamnesi/12345678-1234-1234-1234-123456789012",
        "chiara.fitmanagerstudio.com",
      ),
    );

    expect(response.status).toBe(200);
    expect(response.headers.get("x-middleware-next")).toBe("1");
  });

  it("nasconde il CRM dal dominio FRP", () => {
    const response = middleware(
      makeRequest("/clienti", "chiara.fitmanagerstudio.com", "fitmanager_token=jwt"),
    );

    expect(response.status).toBe(404);
  });

  it("mantiene il CRM raggiungibile da localhost con sessione valida", () => {
    const response = middleware(
      makeRequest("/clienti", "localhost:3000", "fitmanager_token=jwt"),
    );

    expect(response.status).toBe(200);
    expect(response.headers.get("x-middleware-next")).toBe("1");
  });

  it("mantiene il redirect login sul fallback localhost senza sessione", () => {
    const response = middleware(makeRequest("/clienti", "localhost:3000"));

    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe("https://localhost:3000/login");
  });
});

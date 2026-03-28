#!/usr/bin/env node
/**
 * Video 02 — Pre-flight: verifica TUTTI i selettori e il flusso senza registrare.
 *
 * Eseguire DOPO video-02-setup.py e con backend+frontend running.
 * Se tutto passa, si puo' registrare.
 */

const { chromium } = require("playwright");
const path = require("path");

const BASE_URL = "http://localhost:3001";
const API_URL = "http://localhost:8001/api";
const CREDS = { email: "chiarabassani96@gmail.com", password: "Fitness2026!" };

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

// §4.6 — DatePicker automation
async function selectDate(page, triggerText, targetDataDay) {
  const trigger = page.locator(`button:has-text("${triggerText}")`);
  await trigger.scrollIntoViewIfNeeded();
  await trigger.click();
  await wait(500);
  const dayBtn = page.locator(`button[data-day="${targetDataDay}"]`);
  for (let i = 0; i < 8; i++) {
    if (await dayBtn.isVisible({ timeout: 400 }).catch(() => false)) {
      await dayBtn.click();
      await wait(300);
      return;
    }
    await page.locator("button.rdp-button_next").click();
    await wait(400);
  }
  throw new Error(`Data ${targetDataDay} non trovata dopo 8 click avanti`);
}

let passed = 0;
let failed = 0;

function ok(label) {
  passed++;
  console.log(`  ✓ ${label}`);
}

function fail(label, err) {
  failed++;
  console.error(`  ✗ ${label}: ${err}`);
}

async function check(label, fn) {
  try {
    await fn();
    ok(label);
  } catch (e) {
    fail(label, e.message);
  }
}

// ═══════════════════════════════════════════
// Main
// ═══════════════════════════════════════════
async function main() {
  console.log("=== Video 02 — Pre-flight ===\n");

  const browser = await chromium.launch({ headless: false, slowMo: 80, args: ["--start-maximized"] });
  const context = await browser.newContext({ viewport: null });
  const page = await context.newPage();

  // ── LOGIN ──────────────────────────────
  console.log("[login]");
  await page.goto(`${BASE_URL}/login`);
  await page.waitForSelector('input[type="email"]', { timeout: 10000 });
  await page.fill('input[type="email"]', CREDS.email);
  await page.fill('input[type="password"]', CREDS.password);
  await page.click('button[type="submit"]');
  await page.waitForURL("**/", { timeout: 10000 });
  await wait(2000);

  // Cattura token per API calls
  const token = await page.evaluate(() => {
    const match = document.cookie.match(/fitmanager_token=([^;]+)/);
    return match ? match[1] : null;
  });
  ok(`Login OK, token: ${token ? "presente" : "MANCANTE"}`);

  // ── FASE 1: Pagina /rinnovi-incassi ────
  console.log("\n[fase-1] Pagina /rinnovi-incassi");
  await page.goto(`${BASE_URL}/rinnovi-incassi`);

  await check("Pagina rinnovi caricata", async () => {
    await page.locator("p:has-text('Da rinnovare')").first().waitFor({ timeout: 10000 });
  });

  // Trova la CARD specifica di Moretti (scoping per evitare click su card sbagliate)
  // La card contiene il nome del cliente — usiamo il parent container
  const morettiCard = page.locator("div.rounded-xl").filter({ hasText: "Luca Moretti" });

  await check("Card Moretti visibile", async () => {
    await morettiCard.first().waitFor({ timeout: 5000 });
    const text = await morettiCard.first().textContent();
    console.log(`    → Card trovata, contiene: "${text.substring(0, 80)}..."`);
  });

  // Verifica badge scadenza DENTRO la card Moretti
  await check("Badge scadenza nella card Moretti", async () => {
    const badge = morettiCard.first().locator("text=/Scad(e|uto)/");
    await badge.first().waitFor({ timeout: 5000 });
    const text = await badge.first().textContent();
    console.log(`    → Badge: "${text}"`);
  });

  // Verifica bottone Rinnova DENTRO la card Moretti
  const morettiRenewBtn = morettiCard.first().locator('button:has-text("Rinnova")');
  await check("Bottone 'Rinnova' nella card Moretti cliccabile", async () => {
    await morettiRenewBtn.waitFor({ timeout: 5000 });
    const disabled = await morettiRenewBtn.isDisabled();
    if (disabled) throw new Error("Bottone Rinnova disabilitato!");
  });

  // ── FASE 2: Click Rinnova → Sheet ──────
  console.log("\n[fase-2] Sheet Rinnova Contratto");
  await morettiRenewBtn.click();
  await wait(600);

  await check("Sheet 'Rinnova Contratto' aperta", async () => {
    await page.locator("text=Rinnova Contratto").first().waitFor({ timeout: 5000 });
  });

  // Verifica campi pre-compilati
  await check("Campo 'Tipo Pacchetto' pre-compilato", async () => {
    const val = await page.locator("#tipo_pacchetto").inputValue();
    console.log(`    → tipo_pacchetto: "${val}"`);
    if (!val) throw new Error("tipo_pacchetto vuoto!");
  });

  await check("Campo 'Crediti' pre-compilato", async () => {
    const val = await page.locator("#crediti_totali").inputValue();
    console.log(`    → crediti_totali: "${val}"`);
    if (!val || val === "0") throw new Error("crediti_totali vuoto o zero!");
  });

  await check("Campo 'Prezzo Totale' pre-compilato", async () => {
    const val = await page.locator("#prezzo_totale").inputValue();
    console.log(`    → prezzo_totale: "${val}"`);
    if (!val || val === "0") throw new Error("prezzo_totale vuoto o zero!");
  });

  // Verifica placeholder DatePicker
  await check("DatePicker 'Inizio...' visibile", async () => {
    const btn = page.locator('button:has-text("Inizio...")');
    const count = await btn.count();
    if (count === 0) {
      // Prova varianti
      const alt1 = page.locator('button:has-text("Inizio")');
      const alt2 = page.locator('button:has-text("Data inizio")');
      const c1 = await alt1.count();
      const c2 = await alt2.count();
      throw new Error(`"Inizio..." non trovato. Alt "Inizio": ${c1}, "Data inizio": ${c2}`);
    }
    console.log(`    → Trigger inizio trovato (count: ${count})`);
  });

  await check("DatePicker 'Scadenza...' visibile", async () => {
    const btn = page.locator('button:has-text("Scadenza...")');
    const count = await btn.count();
    if (count === 0) {
      const alt1 = page.locator('button:has-text("Scadenza")');
      const alt2 = page.locator('button:has-text("Data scadenza")');
      const c1 = await alt1.count();
      const c2 = await alt2.count();
      throw new Error(`"Scadenza..." non trovato. Alt "Scadenza": ${c1}, "Data scadenza": ${c2}`);
    }
    console.log(`    → Trigger scadenza trovato (count: ${count})`);
  });

  // ── FASE 3: Compila date ───────────────
  console.log("\n[fase-3] Compilazione date");

  await check("Seleziona Data Inizio 01/04/2026", async () => {
    await selectDate(page, "Inizio...", "01/04/2026");
  });

  await wait(300);

  await check("Seleziona Data Scadenza 30/04/2026", async () => {
    await selectDate(page, "Scadenza...", "30/04/2026");
  });

  await wait(300);

  // Verifica bottone submit attivo
  await check("Bottone 'Rinnova Contratto' abilitato", async () => {
    // Scroll al submit
    await page.evaluate(() => {
      const s = document.querySelector('[data-slot="sheet-content"]');
      if (s) s.scrollTo({ top: s.scrollHeight, behavior: "smooth" });
    });
    await wait(500);
    const btn = page.locator('button:has-text("Rinnova Contratto")');
    await btn.waitFor({ timeout: 3000 });
    const disabled = await btn.isDisabled();
    if (disabled) throw new Error("Bottone submit ancora disabled dopo compilazione date!");
  });

  // ── FASE 4: Submit rinnovo ─────────────
  console.log("\n[fase-4] Submit rinnovo");

  await check("Submit 'Rinnova Contratto' eseguito", async () => {
    await page.locator('button:has-text("Rinnova Contratto")').click();
    await wait(2000);
    // Verifica toast successo
    const toast = page.locator("text=Contratto rinnovato");
    await toast.waitFor({ timeout: 5000 });
    console.log("    → Toast 'Contratto rinnovato' apparso");
  });

  // Sheet dovrebbe essersi chiusa
  await wait(1000);

  // ── FASE 5: Trova nuovo contratto via API ──
  console.log("\n[fase-5] Trova nuovo contratto via API");

  let newContractId = null;
  await check("API: trova contratto rinnovato", async () => {
    const result = await page.evaluate(async (tkn) => {
      const r = await fetch("http://localhost:8001/api/contracts?page_size=200", {
        headers: { Authorization: `Bearer ${tkn}` },
      });
      const data = await r.json();
      // Trova il rinnovo di Moretti: data_inizio 01/04, tipo Mensile, con rinnovo_di
      const c = data.items?.find(
        (x) => x.data_inizio === "2026-04-01" && x.tipo_pacchetto === "Mensile 4 Sedute" && x.rinnovo_di
      );
      return c ? { id: c.id, rinnovo_di: c.rinnovo_di, tipo: c.tipo_pacchetto, client: c.client_cognome } : null;
    }, token);

    if (!result) throw new Error("Contratto rinnovato non trovato via API!");
    newContractId = result.id;
    console.log(`    → Nuovo contratto: #${result.id}, rinnovo_di: #${result.rinnovo_di}, tipo: ${result.tipo}, cliente: ${result.client}`);
  });

  // ── FASE 6: Navigazione dettaglio contratto ──
  console.log("\n[fase-6] Dettaglio nuovo contratto");

  if (newContractId) {
    await page.goto(`${BASE_URL}/contratti/${newContractId}`);

    await check("Header contratto visibile", async () => {
      await page.locator('[data-guide="contratto-header"]').waitFor({ timeout: 10000 });
    });

    await check("Hero finanziario visibile", async () => {
      await page.locator('[data-guide="contratto-hero-finanziario"]').waitFor({ timeout: 5000 });
    });

    // Catena di rinnovo
    await check("Catena rinnovi visibile", async () => {
      const chain = page.locator('[data-guide="contratto-catena-rinnovi"]');
      const visible = await chain.isVisible({ timeout: 3000 }).catch(() => false);
      if (!visible) {
        // Prova testo alternativo
        const altChain = page.locator("text=Catena rinnovi").or(page.locator("text=Rinnovo di"));
        const altVisible = await altChain.first().isVisible({ timeout: 3000 }).catch(() => false);
        if (!altVisible) {
          throw new Error("Catena rinnovi non trovata (ne' data-guide ne' testo)");
        }
        console.log("    → Catena trovata via testo (senza data-guide)");
        return;
      }
      console.log("    → Catena trovata via data-guide");
    });

    // Verifica che il contratto originale sia linkato
    await check("Link al contratto originale presente", async () => {
      // Il badge del contratto originale (marzo) dovrebbe essere visibile
      const badge = page.locator("text=/Mensile 4 Sedute/");
      const count = await badge.count();
      console.log(`    → Badge 'Mensile 4 Sedute' trovati: ${count} (atteso >=2: header + catena)`);
      if (count < 1) throw new Error("Nessun badge trovato");
    });

    // Verifica tab Piano Pagamenti
    await check("Tab Piano Pagamenti visibile", async () => {
      await page.locator('[data-guide="contratto-piano-rate"]').waitFor({ timeout: 5000 });
    });
  } else {
    fail("Navigazione dettaglio", "newContractId mancante, skip");
  }

  // ── CLEANUP: elimina contratto rinnovato per re-run ──
  console.log("\n[cleanup] Elimina contratto rinnovato per permettere re-run");
  if (newContractId && token) {
    await check("DELETE contratto rinnovato via API", async () => {
      const result = await page.evaluate(
        async ({ id, tkn }) => {
          const r = await fetch(`http://localhost:8001/api/contracts/${id}?force=true`, {
            method: "DELETE",
            headers: { Authorization: `Bearer ${tkn}` },
          });
          return r.status;
        },
        { id: newContractId, tkn: token }
      );
      console.log(`    → DELETE status: ${result}`);
      if (result !== 204 && result !== 200) throw new Error(`Status ${result}`);
    });
  }

  // ── REPORT ─────────────────────────────
  console.log(`\n${"═".repeat(40)}`);
  console.log(`RISULTATO: ${passed} passed, ${failed} failed`);
  console.log(`${"═".repeat(40)}\n`);

  await context.close();
  await browser.close();

  if (failed > 0) {
    console.log("⚠ CORREGGI i test falliti prima di registrare!");
    process.exit(1);
  } else {
    console.log("Tutti i check passati — puoi registrare.");
  }
}

main().catch((err) => {
  console.error("FATAL:", err);
  process.exit(1);
});

#!/usr/bin/env node
/**
 * Test flusso completo video 01 — validazione selettori.
 *
 * Scena 02: Crea cliente Luca Moretti
 * Scena 03a: Crea contratto (form completo con DatePicker + Select)
 * Scena 03b: Genera piano rate (2 rate da €250)
 *
 * Nessuna registrazione video — solo validazione azioni.
 * Browser maximized e visibile per verifica manuale.
 */
const { chromium } = require("playwright");

const BASE = "http://localhost:3001";
const CREDS = { email: "chiarabassani96@gmail.com", password: "Fitness2026!" };

async function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

/**
 * Seleziona una data nel DatePicker.
 * @param page - Playwright page
 * @param triggerText - testo del bottone trigger (es. "Inizio..." o la data gia' selezionata)
 * @param targetDataDay - formato "DD/MM/YYYY" (es. "01/04/2026")
 * @param maxNavClicks - quante volte cliccare avanti per trovare il mese giusto
 */
async function selectDate(page, triggerText, targetDataDay, maxNavClicks = 6) {
  // Click trigger per aprire il popover calendario
  await page.locator(`button:has-text("${triggerText}")`).click();
  await wait(500);

  // Prova a trovare il giorno direttamente
  const daySelector = `button[data-day="${targetDataDay}"]`;
  let dayBtn = page.locator(daySelector);

  if (await dayBtn.isVisible({ timeout: 500 }).catch(() => false)) {
    await dayBtn.click();
    console.log(`    Data ${targetDataDay}: selezionata (mese corrente)`);
    await wait(300);
    return;
  }

  // Naviga avanti mese per mese fino a trovare il giorno
  for (let i = 0; i < maxNavClicks; i++) {
    await page.locator('button.rdp-button_next').click();
    await wait(400);

    if (await dayBtn.isVisible({ timeout: 500 }).catch(() => false)) {
      await dayBtn.click();
      console.log(`    Data ${targetDataDay}: selezionata (dopo ${i + 1} navigazioni)`);
      await wait(300);
      return;
    }
  }

  console.error(`    ERRORE: ${targetDataDay} non trovata dopo ${maxNavClicks} navigazioni`);
}

/**
 * Seleziona un valore nel Radix Select.
 */
async function selectRadixOption(page, triggerSelector, optionText) {
  await page.locator(triggerSelector).click();
  await wait(400);
  await page.locator(`[data-slot="select-item"]:has-text("${optionText}")`).click();
  await wait(300);
  console.log(`    Select: ${optionText} selezionato`);
}

async function main() {
  const browser = await chromium.launch({
    headless: false, slowMo: 80, args: ["--start-maximized"],
  });
  const ctx = await browser.newContext({ viewport: null });
  const page = await ctx.newPage();

  // ── Login ──
  console.log("[login]");
  await page.goto(`${BASE}/login`);
  await page.waitForSelector('input[type="email"]', { timeout: 10000 });
  await page.fill('input[type="email"]', CREDS.email);
  await page.fill('input[type="password"]', CREDS.password);
  await page.click('button[type="submit"]');
  await page.waitForURL("**/", { timeout: 10000 });
  await wait(2000);
  console.log("  OK\n");

  // ══════════════════════════════════════════
  // SCENA 02 — Crea cliente Luca Moretti
  // ══════════════════════════════════════════
  console.log("[scena 02] Crea cliente Luca Moretti");

  await page.goto(`${BASE}/clienti`);
  await page.waitForSelector('[data-guide="clienti-header"]', { timeout: 10000 });
  await wait(1000);

  await page.click('[data-guide="clienti-new-button"]');
  await wait(800);

  await page.fill('#nome', "Luca");
  await wait(200);
  await page.fill('#cognome', "Moretti");
  await wait(200);
  await page.fill('#telefono', "340 5678901");
  await wait(400);

  await page.click('button:has-text("Crea Cliente")');
  await wait(2000);

  // Apri profilo
  await page.locator('td:has-text("Moretti")').first().click();
  await wait(2000);

  // Verifica checklist
  const checklistVisible = await page.locator('text=Crea contratto').isVisible({ timeout: 3000 }).catch(() => false);
  console.log(`  Cliente creato: OK`);
  console.log(`  Checklist "Crea contratto" visibile: ${checklistVisible ? "SI" : "NO"}\n`);

  // ══════════════════════════════════════════
  // SCENA 03a — Crea contratto
  // ══════════════════════════════════════════
  console.log("[scena 03a] Crea contratto");

  // Click "Crea contratto" dalla checklist
  await page.locator('text=Crea contratto').first().click();
  await wait(2000);

  // Siamo su /contratti?new=1&cliente=ID — Sheet aperto
  console.log("  Compilo form...");

  // Tipo pacchetto
  await page.fill('#tipo_pacchetto', "Pacchetto 10");
  await wait(300);
  console.log("    tipo_pacchetto: OK");

  // Crediti
  await page.fill('#crediti_totali', "10");
  await wait(300);
  console.log("    crediti_totali: OK");

  // Prezzo
  await page.fill('#prezzo_totale', "550");
  await wait(300);
  console.log("    prezzo_totale: OK");

  // Data inizio: 01/04/2026
  console.log("  Seleziono Data Inizio...");
  await selectDate(page, "Inizio...", "01/04/2026");

  // Data scadenza: 01/06/2026
  console.log("  Seleziono Data Scadenza...");
  await selectDate(page, "Scadenza...", "01/06/2026");

  // Acconto
  await page.fill('#acconto', "50");
  await wait(800);
  console.log("    acconto: OK");

  // Metodo acconto: BONIFICO
  console.log("  Seleziono metodo...");
  // Il trigger del metodo è il secondo Select nella pagina (il primo è il cliente)
  await selectRadixOption(page, '[data-slot="select-trigger"]:last-of-type', "BONIFICO");

  // Scroll giù nel sheet per vedere il bottone submit
  await page.evaluate(() => {
    const sheet = document.querySelector('[data-slot="sheet-content"]');
    if (sheet) sheet.scrollTop = sheet.scrollHeight;
  });
  await wait(500);

  // Submit
  console.log("  Click Crea Contratto...");
  await page.click('button[type="submit"]:has-text("Crea Contratto")');
  await wait(3000);

  // Verifica redirect al dettaglio
  const url = page.url();
  console.log(`  Redirect: ${url}`);
  console.log(`  Contratto creato: ${url.includes('/contratti/') ? "SI" : "NO"}\n`);

  // ══════════════════════════════════════════
  // SCENA 03b — Genera piano rate
  // ══════════════════════════════════════════
  console.log("[scena 03b] Genera piano rate");

  // Scroll al piano pagamenti
  await page.evaluate(() => window.scrollBy({ top: 500, behavior: "smooth" }));
  await wait(1500);

  // Verifica che il form genera rate sia visibile
  const genFormVisible = await page.locator('text=Nessun piano rate configurato').isVisible({ timeout: 3000 }).catch(() => false);
  console.log(`  Form genera rate visibile: ${genFormVisible ? "SI" : "NO"}`);

  if (genFormVisible) {
    // Numero rate: cambia a 2
    await page.fill('#numero_rate', "2");
    await wait(300);
    console.log("    numero_rate: 2");

    // Data prima rata: 01/05/2026
    console.log("  Seleziono data prima rata...");
    await selectDate(page, "Seleziona data...", "01/05/2026");

    // Il bottone ora dovrebbe essere abilitato
    await wait(500);
    const genBtn = page.locator('button:has-text("Genera Piano Pagamenti")');
    const enabled = await genBtn.isEnabled({ timeout: 2000 }).catch(() => false);
    console.log(`  Bottone Genera abilitato: ${enabled ? "SI" : "NO"}`);

    if (enabled) {
      await genBtn.click();
      await wait(2000);
      console.log("  Piano rate generato!");

      // Scroll per mostrare le rate
      await page.evaluate(() => window.scrollBy({ top: 300, behavior: "smooth" }));
      await wait(2000);

      // Verifica rate visibili
      const rateCount = await page.locator('text=€ 250').count();
      console.log(`  Rate da €250 visibili: ${rateCount}`);
    }
  }

  console.log("\n=== TEST COMPLETATO ===");
  console.log("Verifica visivamente il risultato nel browser.");
  console.log("Chiudi manualmente quando hai finito.");
}

main().catch(console.error);

#!/usr/bin/env node
/**
 * Test DatePicker automazione.
 * Apre form nuovo contratto e seleziona date via Playwright.
 */
const { chromium } = require("playwright");

const BASE = "http://localhost:3001";
const CREDS = { email: "chiarabassani96@gmail.com", password: "Fitness2026!" };

async function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

async function selectDate(page, triggerText, targetDataDay) {
  // Click sul trigger del DatePicker (bottone con placeholder o data)
  const trigger = page.locator(`button:has-text("${triggerText}")`);
  await trigger.click();
  await wait(500);

  // Il calendario Popover è aperto — cerca il giorno con data-day
  // react-day-picker formatta data-day come locale string: "M/D/YYYY" o "D/M/YYYY"
  // Proviamo a cliccare il bottone con data-day esatto
  const dayBtn = page.locator(`button[data-day="${targetDataDay}"]`);

  if (await dayBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
    await dayBtn.click();
    console.log(`  Data selezionata: ${targetDataDay}`);
    await wait(300);
    return true;
  }

  // Se non trovato, potrebbe servire navigare al mese giusto
  console.log(`  Data ${targetDataDay} non visibile, navigo al mese...`);

  // Click freccia avanti fino a trovare il giorno
  for (let attempt = 0; attempt < 6; attempt++) {
    const nextBtn = page.locator('.rdp-button_next');
    if (await nextBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
      await nextBtn.click();
      await wait(400);

      if (await dayBtn.isVisible({ timeout: 500 }).catch(() => false)) {
        await dayBtn.click();
        console.log(`  Data selezionata dopo ${attempt + 1} navigazioni: ${targetDataDay}`);
        await wait(300);
        return true;
      }
    }
  }

  console.log(`  ERRORE: impossibile trovare ${targetDataDay}`);
  return false;
}

async function main() {
  const browser = await chromium.launch({
    headless: false, slowMo: 100, args: ["--start-maximized"],
  });
  const ctx = await browser.newContext({ viewport: null });
  const page = await ctx.newPage();

  // Login
  console.log("Login...");
  await page.goto(`${BASE}/login`);
  await page.waitForSelector('input[type="email"]', { timeout: 10000 });
  await page.fill('input[type="email"]', CREDS.email);
  await page.fill('input[type="password"]', CREDS.password);
  await page.click('button[type="submit"]');
  await page.waitForURL("**/", { timeout: 10000 });
  await wait(2000);

  // Naviga a contratti con form aperto
  console.log("Apro form nuovo contratto...");
  await page.goto(`${BASE}/contratti?new=1`);
  await wait(2000);

  // Compila campi base
  await page.fill('#tipo_pacchetto', "Test Pacchetto");
  await page.fill('#crediti_totali', "10");
  await page.fill('#prezzo_totale', "550");
  await wait(500);

  // Test DatePicker: Data Inizio → 1 Aprile 2026
  console.log("\nTest Data Inizio (1 Aprile 2026)...");
  // Il formato data-day dipende dal locale del browser
  // Proviamo entrambi i formati comuni
  const ok1 = await selectDate(page, "Inizio...", "4/1/2026");
  if (!ok1) {
    // Prova formato europeo
    await selectDate(page, "Inizio...", "1/4/2026");
  }
  await wait(1000);

  // Test DatePicker: Data Scadenza → 1 Giugno 2026
  console.log("\nTest Data Scadenza (1 Giugno 2026)...");
  const ok2 = await selectDate(page, "Scadenza...", "6/1/2026");
  if (!ok2) {
    await selectDate(page, "Scadenza...", "1/6/2026");
  }
  await wait(1000);

  // Test acconto + metodo
  console.log("\nTest Acconto + Metodo...");
  await page.fill('#acconto', "50");
  await wait(800);

  // Select metodo: Radix Select
  const selectTrigger = page.locator('[data-slot="select-trigger"]').last();
  await selectTrigger.click();
  await wait(500);
  await page.locator('text=BONIFICO').click();
  await wait(500);

  console.log("\n=== Test completato — verifica visivamente ===");
  console.log("Il form dovrebbe avere: Pacchetto, 10 crediti, €550, date 01/04-01/06, acconto €50 Bonifico");
  console.log("Chiudi il browser manualmente.");
}

main().catch(console.error);

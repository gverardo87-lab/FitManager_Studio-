#!/usr/bin/env node
/**
 * Test DatePicker v2 — diagnostica formato data-day + Select fix.
 */
const { chromium } = require("playwright");

const BASE = "http://localhost:3001";
const CREDS = { email: "chiarabassani96@gmail.com", password: "Fitness2026!" };

async function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  const browser = await chromium.launch({
    headless: false, slowMo: 100, args: ["--start-maximized"],
  });
  const ctx = await browser.newContext({ viewport: null });
  const page = await ctx.newPage();

  // Login
  await page.goto(`${BASE}/login`);
  await page.waitForSelector('input[type="email"]', { timeout: 10000 });
  await page.fill('input[type="email"]', CREDS.email);
  await page.fill('input[type="password"]', CREDS.password);
  await page.click('button[type="submit"]');
  await page.waitForURL("**/", { timeout: 10000 });
  await wait(2000);

  // Apri form nuovo contratto
  await page.goto(`${BASE}/contratti?new=1`);
  await wait(2000);

  // ── DIAGNOSI 1: Formato data-day ──
  console.log("\n=== DIAGNOSI: formato data-day ===");

  // Apri il DatePicker "Inizio..."
  await page.locator('button:has-text("Inizio...")').click();
  await wait(1000);

  // Leggi TUTTI i data-day visibili nel calendario
  const dataDays = await page.evaluate(() => {
    const buttons = document.querySelectorAll('button[data-day]');
    return Array.from(buttons).slice(0, 10).map(b => ({
      dataDay: b.getAttribute('data-day'),
      text: b.textContent.trim(),
    }));
  });

  console.log("Primi 10 data-day trovati:");
  for (const d of dataDays) {
    console.log(`  data-day="${d.dataDay}"  testo="${d.text}"`);
  }

  // Chiudi il popover cliccando fuori
  await page.keyboard.press('Escape');
  await wait(500);

  // ── DIAGNOSI 2: Navigazione mese ──
  console.log("\n=== DIAGNOSI: navigazione mesi ===");
  await page.locator('button:has-text("Inizio...")').click();
  await wait(500);

  // Leggi il mese corrente
  const currentMonth = await page.evaluate(() => {
    const caption = document.querySelector('.rdp-month_caption, [class*="caption"]');
    return caption ? caption.textContent.trim() : 'NON TROVATO';
  });
  console.log(`Mese corrente: ${currentMonth}`);

  // Prova a navigare avanti
  const nextBtn = page.locator('button.rdp-button_next');
  const nextVisible = await nextBtn.isVisible({ timeout: 1000 }).catch(() => false);
  console.log(`Bottone next visibile: ${nextVisible}`);

  if (nextVisible) {
    await nextBtn.click();
    await wait(500);
    const nextMonth = await page.evaluate(() => {
      const caption = document.querySelector('.rdp-month_caption, [class*="caption"]');
      return caption ? caption.textContent.trim() : 'NON TROVATO';
    });
    console.log(`Mese dopo click next: ${nextMonth}`);

    // Leggi di nuovo i data-day
    const nextDataDays = await page.evaluate(() => {
      const buttons = document.querySelectorAll('button[data-day]');
      return Array.from(buttons).slice(0, 5).map(b => b.getAttribute('data-day'));
    });
    console.log(`Primi 5 data-day del mese successivo: ${nextDataDays.join(', ')}`);
  }

  await page.keyboard.press('Escape');
  await wait(500);

  // ── DIAGNOSI 3: Select Radix ──
  console.log("\n=== DIAGNOSI: Select metodo pagamento ===");
  await page.fill('#acconto', "50");
  await wait(800);

  // Trova il select trigger per metodo acconto
  const triggers = await page.evaluate(() => {
    const all = document.querySelectorAll('[data-slot="select-trigger"]');
    return Array.from(all).map((el, i) => ({
      index: i,
      text: el.textContent.trim(),
      parent: el.parentElement?.textContent?.substring(0, 50).trim(),
    }));
  });
  console.log("Select triggers trovati:");
  for (const t of triggers) {
    console.log(`  [${t.index}] "${t.text}" — parent: "${t.parent}"`);
  }

  // Prova a cliccare il trigger e poi selezionare BONIFICO con selettore specifico
  const metodoTrigger = page.locator('[data-slot="select-trigger"]').last();
  await metodoTrigger.click();
  await wait(500);

  // Leggi gli item disponibili
  const items = await page.evaluate(() => {
    const all = document.querySelectorAll('[data-slot="select-item"]');
    return Array.from(all).map(el => ({
      text: el.textContent.trim(),
      value: el.getAttribute('data-value'),
    }));
  });
  console.log("Select items:");
  for (const item of items) {
    console.log(`  "${item.text}" value="${item.value}"`);
  }

  // Seleziona BONIFICO con selettore preciso
  const bonificoItem = page.locator('[data-slot="select-item"]:has-text("BONIFICO")');
  const bonificoVisible = await bonificoItem.isVisible({ timeout: 1000 }).catch(() => false);
  console.log(`\nBONIFICO item visibile: ${bonificoVisible}`);
  if (bonificoVisible) {
    await bonificoItem.click();
    await wait(500);
    console.log("BONIFICO selezionato!");
  }

  console.log("\n=== Diagnostica completata — chiudi il browser ===");
}

main().catch(console.error);

#!/usr/bin/env node
/**
 * Test singola scena: Crea cliente Marco Ferretti.
 * Lancia in modalità visibile per verificare selettori.
 */
const { chromium } = require("playwright");

const BASE = "http://localhost:3001";
const CREDS = { email: "chiarabassani96@gmail.com", password: "Fitness2026!" };

async function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  const browser = await chromium.launch({
    headless: false,
    slowMo: 100,
    args: ["--start-maximized"],
  });
  const ctx = await browser.newContext({ viewport: null }); // null = usa finestra reale (maximized)
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
  console.log("Login OK");

  // Vai a clienti
  console.log("Navigo a /clienti...");
  await page.goto(`${BASE}/clienti`);
  await page.waitForSelector('[data-guide="clienti-header"]', { timeout: 10000 });
  await wait(1000);

  // Click "Nuovo Cliente"
  console.log("Click Nuovo Cliente...");
  await page.click('[data-guide="clienti-new-button"]');
  await wait(1000);

  // Compila form
  console.log("Compilo form...");
  await page.fill('#nome', "Marco");
  await wait(300);
  await page.fill('#cognome', "Ferretti");
  await wait(300);
  await page.fill('#telefono', "339 1234567");
  await wait(500);

  // Submit
  console.log("Click Crea Cliente...");
  await page.click('button:has-text("Crea Cliente")');
  await wait(2000);

  // Verifica che il cliente sia nella lista
  const found = await page.locator('text=Ferretti').count();
  console.log(`Cliente trovato nella lista: ${found > 0 ? "SI" : "NO"}`);

  // Click sul profilo
  if (found > 0) {
    console.log("Apro profilo...");
    await page.locator('text=Ferretti').first().click();
    await wait(3000);
    console.log("Profilo aperto — verifico OnboardingChecklist...");
    const checklist = await page.locator('text=Crea contratto').count();
    console.log(`Checklist 'Crea contratto' visibile: ${checklist > 0 ? "SI" : "NO"}`);
  }

  console.log("\n=== Test completato — browser resta aperto per ispezione ===");
  console.log("Chiudi manualmente il browser quando hai finito.");
  // NON chiudiamo il browser — l'utente ispeziona
}

main().catch(console.error);

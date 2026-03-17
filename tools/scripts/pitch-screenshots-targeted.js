const { chromium } = require("playwright");

const BASE = "http://localhost:3001";
const API = "http://localhost:8001";
const OUT = "C:/Users/gvera/Projects/FitManager_AI_Studio/data/screenshots";

async function main() {
  console.log("Getting JWT token...");
  const loginRes = await fetch(`${API}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: "chiarabassani96@gmail.com", password: "chiarabassani96" }),
  });
  const loginData = await loginRes.json();
  console.log(`Logged in as ${loginData.nome} ${loginData.cognome}`);

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
  });
  await context.addCookies([
    { name: "fitmanager_token", value: loginData.access_token, domain: "localhost", path: "/" },
    { name: "fitmanager_trainer", value: JSON.stringify({ id: loginData.trainer_id, nome: loginData.nome, cognome: loginData.cognome }), domain: "localhost", path: "/" },
  ]);
  const page = await context.newPage();

  // 1. Scheda 88 (Giacomo Verardo) — Tab Analisi Scientifica
  console.log("1/3 Scheda Analisi Scientifica (workout 88)...");
  await page.goto(`${BASE}/schede/88`, { waitUntil: "networkidle" });
  await page.waitForTimeout(3000);
  // Click "Analisi" tab
  const analisiBtn = await page.$('button:has-text("Analisi")');
  if (analisiBtn) {
    await analisiBtn.click();
    await page.waitForTimeout(2000);
    console.log("  Clicked Analisi tab");
  } else {
    // Try alternative selectors
    const tabs = await page.$$('button[role="tab"]');
    for (const tab of tabs) {
      const text = await tab.textContent();
      if (text && text.includes("Analisi")) {
        await tab.click();
        await page.waitForTimeout(2000);
        console.log("  Clicked Analisi tab (alt)");
        break;
      }
    }
  }
  await page.screenshot({ path: `${OUT}/targeted-01-scheda-analisi.png`, fullPage: false });
  console.log("  OK");

  // 2. Safety Engine — open workout builder for client 31 (Giacomo Verardo)
  // The safety card should show in the builder since Giacomo has conditions
  console.log("2/3 Safety Engine (client 31 - Verardo)...");
  // Navigate to Giacomo's profile to see safety info
  await page.goto(`${BASE}/clienti/31`, { waitUntil: "networkidle" });
  await page.waitForTimeout(3000);
  await page.screenshot({ path: `${OUT}/targeted-02a-verardo-profilo.png`, fullPage: false });
  console.log("  OK (profile)");

  // Also try the scheda builder with safety card visible
  await page.goto(`${BASE}/schede/88`, { waitUntil: "networkidle" });
  await page.waitForTimeout(3000);
  // Look for safety card / sicurezza section
  const sicurezzaBtn = await page.$('button:has-text("Sicurezza")');
  if (sicurezzaBtn) {
    await sicurezzaBtn.click();
    await page.waitForTimeout(2000);
    console.log("  Clicked Sicurezza tab");
  }
  // Try to expand safety card if collapsed
  const safetyExpand = await page.$('[data-testid="safety-card"] button, .safety-card button, button:has-text("Profilo Clinico")');
  if (safetyExpand) {
    await safetyExpand.click();
    await page.waitForTimeout(1500);
    console.log("  Expanded safety card");
  }
  await page.screenshot({ path: `${OUT}/targeted-02b-safety-builder.png`, fullPage: false });
  console.log("  OK (builder safety)");

  // 3. Nutrition plan detail — plan 5
  console.log("3/3 Piano Nutrizionale LARN (plan 5)...");
  await page.goto(`${BASE}/nutrizione`, { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);
  // Click into the plan
  const planLink = await page.$('a[href*="/nutrizione/"]');
  if (planLink) {
    await planLink.click();
    await page.waitForTimeout(3000);
  } else {
    // Try direct navigation
    await page.goto(`${BASE}/nutrizione/5`, { waitUntil: "networkidle" });
    await page.waitForTimeout(3000);
  }
  await page.screenshot({ path: `${OUT}/targeted-03-nutrizione-piano.png`, fullPage: false });
  console.log("  OK");

  // Try clicking into a day or meal for more detail
  const dayTab = await page.$('button:has-text("Lunedi"), button:has-text("Lun"), button:has-text("Mar")');
  if (dayTab) {
    await dayTab.click();
    await page.waitForTimeout(2000);
  }
  await page.screenshot({ path: `${OUT}/targeted-03b-nutrizione-dettaglio.png`, fullPage: false });
  console.log("  OK (detail)");

  await browser.close();
  console.log("\nDone! Targeted screenshots saved.");
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});

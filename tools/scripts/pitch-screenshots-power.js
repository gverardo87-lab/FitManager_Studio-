const { chromium } = require("playwright");

const BASE = "http://localhost:3001";
const API = "http://localhost:8001";
const OUT = "C:/Users/gvera/Projects/FitManager_AI_Studio/data/screenshots";

async function main() {
  // Get JWT token
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

  // 1. Cassa — financial dashboard with chart
  console.log("1/5 Cassa (financial dashboard)...");
  await page.goto(`${BASE}/cassa`, { waitUntil: "networkidle" });
  await page.waitForTimeout(4000);
  await page.screenshot({ path: `${OUT}/power-01-cassa.png`, fullPage: false });
  console.log("  OK");

  // 2. Scheda Builder — try to find a scheda with sessions and click analysis tab
  console.log("2/5 Scheda Builder (scientific analysis)...");
  await page.goto(`${BASE}/schede`, { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);
  // Click first scheda that has sessions
  const schedaLink = await page.$('a[href*="/schede/"]');
  if (schedaLink) {
    await schedaLink.click();
    await page.waitForTimeout(3000);
    // Try to click "Analisi" tab if present
    const analisiTab = await page.$('button:has-text("Analisi")');
    if (analisiTab) {
      await analisiTab.click();
      await page.waitForTimeout(2000);
    }
  }
  await page.screenshot({ path: `${OUT}/power-02-scheda-analisi.png`, fullPage: false });
  console.log("  OK");

  // 3. Monitoraggio client — try to find a client with data
  console.log("3/5 Monitoraggio (client tracking)...");
  await page.goto(`${BASE}/monitoraggio`, { waitUntil: "networkidle" });
  await page.waitForTimeout(3000);
  // Try clicking into first client
  const monLink = await page.$('a[href*="/monitoraggio/"]');
  if (monLink) {
    await monLink.click();
    await page.waitForTimeout(3000);
  }
  await page.screenshot({ path: `${OUT}/power-03-monitoraggio.png`, fullPage: false });
  console.log("  OK");

  // 4. Exercise detail with safety/muscles
  console.log("4/5 Esercizio dettaglio (safety + muscles)...");
  await page.goto(`${BASE}/esercizi`, { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);
  // Click first exercise with a photo
  const exLink = await page.$('a[href*="/esercizi/"]');
  if (exLink) {
    await exLink.click();
    await page.waitForTimeout(3000);
  }
  await page.screenshot({ path: `${OUT}/power-04-esercizio-dettaglio.png`, fullPage: false });
  console.log("  OK");

  // 5. Nutrizione page
  console.log("5/5 Nutrizione (meal plan)...");
  await page.goto(`${BASE}/nutrizione`, { waitUntil: "networkidle" });
  await page.waitForTimeout(3000);
  await page.screenshot({ path: `${OUT}/power-05-nutrizione.png`, fullPage: false });
  console.log("  OK");

  // 6. BONUS: Rinnovi & Incassi (scadenziario)
  console.log("6/6 BONUS: Rinnovi & Incassi...");
  await page.goto(`${BASE}/rinnovi-incassi`, { waitUntil: "networkidle" });
  await page.waitForTimeout(3000);
  await page.screenshot({ path: `${OUT}/power-06-rinnovi-incassi.png`, fullPage: false });
  console.log("  OK");

  // 7. BONUS: Client profile with journey path
  console.log("7/7 BONUS: Client profile hub...");
  await page.goto(`${BASE}/clienti`, { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);
  // Find a client with more data (skip first, try second)
  const clientLinks = await page.$$('a[href*="/clienti/"]');
  if (clientLinks.length > 1) {
    await clientLinks[1].click();
  } else if (clientLinks.length > 0) {
    await clientLinks[0].click();
  }
  await page.waitForTimeout(3000);
  await page.screenshot({ path: `${OUT}/power-07-profilo-cliente.png`, fullPage: false });
  console.log("  OK");

  await browser.close();
  console.log("\nDone! 7 power screenshots saved.");
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});

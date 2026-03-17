const { chromium } = require("playwright");

const BASE = "http://localhost:3001";
const API = "http://localhost:8001";
const OUT = "C:/Users/gvera/Projects/FitManager_AI_Studio/data/screenshots";

async function main() {
  // Step 1: Get JWT token via API
  console.log("Getting JWT token...");
  const loginRes = await fetch(`${API}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: "chiarabassani96@gmail.com",
      password: "chiarabassani96",
    }),
  });
  const loginData = await loginRes.json();
  console.log(`Logged in as ${loginData.nome} ${loginData.cognome}`);

  // Step 2: Launch browser with cookies pre-set
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
  });

  // Set auth cookies before navigating
  await context.addCookies([
    {
      name: "fitmanager_token",
      value: loginData.access_token,
      domain: "localhost",
      path: "/",
    },
    {
      name: "fitmanager_trainer",
      value: JSON.stringify({
        id: loginData.trainer_id,
        nome: loginData.nome,
        cognome: loginData.cognome,
      }),
      domain: "localhost",
      path: "/",
    },
  ]);

  const page = await context.newPage();

  // Screenshot 1: Dashboard
  console.log("1/5 Dashboard...");
  await page.goto(`${BASE}/`, { waitUntil: "networkidle" });
  await page.waitForTimeout(4000);
  await page.screenshot({ path: `${OUT}/01-dashboard.png`, fullPage: false });
  console.log("  OK");

  // Screenshot 2: Client Profile
  console.log("2/5 Client Profile...");
  await page.goto(`${BASE}/clienti`, { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);
  const clientLink = await page.$('a[href*="/clienti/"]');
  if (clientLink) {
    await clientLink.click();
    await page.waitForTimeout(4000);
  }
  await page.screenshot({ path: `${OUT}/02-profilo-cliente.png`, fullPage: false });
  console.log("  OK");

  // Screenshot 3: Workout Builder
  console.log("3/5 Workout Builder...");
  await page.goto(`${BASE}/schede`, { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);
  const schedaLink = await page.$('a[href*="/schede/"]');
  if (schedaLink) {
    await schedaLink.click();
    await page.waitForTimeout(4000);
  }
  await page.screenshot({ path: `${OUT}/03-schede-builder.png`, fullPage: false });
  console.log("  OK");

  // Screenshot 4: Exercise Catalog
  console.log("4/5 Exercise Catalog...");
  await page.goto(`${BASE}/esercizi`, { waitUntil: "networkidle" });
  await page.waitForTimeout(3000);
  await page.screenshot({ path: `${OUT}/04-esercizi.png`, fullPage: false });
  console.log("  OK");

  // Screenshot 5: Financial Management
  console.log("5/5 Financial Management...");
  await page.goto(`${BASE}/cassa`, { waitUntil: "networkidle" });
  await page.waitForTimeout(3000);
  await page.screenshot({ path: `${OUT}/05-cassa.png`, fullPage: false });
  console.log("  OK");

  await browser.close();
  console.log("\nDone! 5 screenshots saved to data/screenshots/");
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});

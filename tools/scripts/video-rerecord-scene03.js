#!/usr/bin/env node
/**
 * Ri-registra SOLO scena 03 — Contratto con piano rate.
 *
 * Strategia: crea contratto via API, poi registra visivamente:
 * 1. Profilo con checklist "Contratto" completato
 * 2. Dettaglio contratto con KPI
 * 3. Click "Genera Piano Pagamenti" → PAUSA WOW sulle rate
 *
 * Le date e i campi del form sono creati via API (piu' affidabile).
 * Il video mostra il risultato + il momento WOW della generazione rate.
 */

const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");
const { execSync } = require("child_process");

const BASE_URL = "http://localhost:3001";
const API_URL = "http://localhost:8001/api";
const CREDS = { email: "chiarabassani96@gmail.com", password: "Fitness2026!" };
const VIDEO_DIR = path.resolve(__dirname, "../../data/videos/01-primo-cliente");
const CLIPS_DIR = path.join(VIDEO_DIR, "clips");
const SCENES_DIR = path.join(VIDEO_DIR, "scenes");
const FF = "C:\\Users\\gvera\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-8.1-full_build\\bin\\ffprobe.exe";
const REC_SIZE = { width: 1440, height: 900 };

function getVoDuration(name) {
  return parseFloat(execSync(`"${FF}" -v quiet -show_entries format=duration -of csv=p=0 "${path.join(SCENES_DIR, name + ".mp3")}"`).toString().trim());
}

async function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

async function apiCall(method, endpoint, token, body) {
  const resp = await fetch(`${API_URL}${endpoint}`, {
    method,
    headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`API ${method} ${endpoint}: ${resp.status} — ${text}`);
  }
  return resp.json();
}

async function main() {
  const voDur = getVoDuration("03_contratto");
  const clipDur = voDur + 5.0;
  console.log(`Scena 03 — VO: ${voDur.toFixed(1)}s + pad 5s = clip ${clipDur.toFixed(1)}s\n`);

  // Login via API per ottenere token
  console.log("[setup] Login API...");
  const loginResp = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: CREDS.email, password: CREDS.password }),
  });
  const { access_token: token } = await loginResp.json();
  console.log("  Token OK");

  // Trova Marco Ferretti
  const clientsResp = await apiCall("GET", "/clients?page_size=200", token);
  const marco = clientsResp.items.find(c => c.cognome === "Ferretti" && c.nome === "Marco");
  if (!marco) throw new Error("Marco Ferretti non trovato! Lancia prima lo script completo.");
  console.log(`  Marco Ferretti: ID ${marco.id}`);

  // Crea contratto via API (se non esiste gia')
  const contractsResp = await apiCall("GET", "/contracts?page_size=200", token);
  let contract = contractsResp.items?.find(c => c.id_cliente === marco.id);

  if (!contract) {
    console.log("  Creo contratto via API...");
    contract = await apiCall("POST", "/contracts", token, {
      id_cliente: marco.id,
      tipo_pacchetto: "Pacchetto 10",
      crediti_totali: 10,
      prezzo_totale: 550,
      data_inizio: "2026-04-01",
      data_scadenza: "2026-06-01",
      acconto: 50,
      metodo_acconto: "BONIFICO",
    });
    console.log(`  Contratto creato: ID ${contract.id}`);
  } else {
    console.log(`  Contratto esistente: ID ${contract.id}`);
  }

  // Genera piano rate via API (2 rate, prima rata 01/05/2026)
  const contractDetail = await apiCall("GET", `/contracts/${contract.id}`, token);
  const hasRates = contractDetail.rate && contractDetail.rate.length > 0;
  if (!hasRates) {
    console.log("  Genero piano rate via API...");
    await apiCall("POST", `/rates/generate-plan/${contract.id}`, token, {
      importo_da_rateizzare: 500,
      numero_rate: 2,
      data_prima_rata: "2026-05-01",
      frequenza: "MENSILE",
    });
    console.log("  Piano rate generato: 2 rate da €250");
  } else {
    console.log(`  Rate esistenti: ${contractDetail.rate.length}`);
  }

  // Login browser
  const browser = await chromium.launch({
    headless: false,
    slowMo: 80,
    args: ["--start-maximized"],
  });

  const authCtx = await browser.newContext({ viewport: null });
  const authPage = await authCtx.newPage();
  await authPage.goto(`${BASE_URL}/login`);
  await authPage.waitForSelector('input[type="email"]', { timeout: 10000 });
  await authPage.fill('input[type="email"]', CREDS.email);
  await authPage.fill('input[type="password"]', CREDS.password);
  await authPage.click('button[type="submit"]');
  await authPage.waitForURL("**/", { timeout: 10000 });
  await wait(2000);
  const authStatePath = path.join(VIDEO_DIR, "auth-state.json");
  await authCtx.storageState({ path: authStatePath });
  await authPage.close();
  await authCtx.close();
  console.log("  Browser login OK\n");

  // Pulisci webm residui (mantieni le altre scene)
  for (const f of fs.readdirSync(CLIPS_DIR).filter(f => f.endsWith(".webm") && !f.match(/^0[12456]_/))) {
    fs.unlinkSync(path.join(CLIPS_DIR, f));
  }

  // Registra
  const clipPath = path.join(CLIPS_DIR, "03_contratto.webm");
  if (fs.existsSync(clipPath)) fs.unlinkSync(clipPath);

  const context = await browser.newContext({
    viewport: null,
    recordVideo: { dir: CLIPS_DIR, size: REC_SIZE },
    storageState: authStatePath,
  });

  const page = await context.newPage();
  const startTime = Date.now();

  try {
    // Mostra il dettaglio contratto con KPI + rate gia' generate
    console.log("[rec] Navigo al dettaglio contratto...");
    await page.goto(`${BASE_URL}/contratti/${contract.id}`);
    await wait(2500);

    // Mostra i KPI (Financial Hero: valore, acconto, versato, residuo)
    // VO: "La checklist dice: crea il contratto. Pacchetto dieci sedute,
    //      cinquecentocinquanta euro, acconto cinquanta."
    // Questo copre i primi ~8s — i KPI sono visibili in questo momento
    console.log("[rec] Mostro KPI contratto (8s)...");
    await wait(5500);

    // VO: "Generi il piano rate in un click:" — scroll PRIMA che dica le cifre
    // Scroll lento alle rate — il viewer vede le rate apparire
    console.log("[rec] Scroll alle rate (sincronizzato con VO)...");
    await page.evaluate(() => window.scrollBy({ top: 600, behavior: "smooth" }));
    await wait(2000);

    // VO: "due rate da duecentocinquanta, già pronte."
    // Le rate sono ora visibili — pausa per lettura
    console.log("[rec] Rate visibili — pausa lettura...");
    await wait(4000);
  } catch (err) {
    console.error("  ERRORE:", err.message);
  }

  // Attendi durata esatta
  const elapsed = Date.now() - startTime;
  const remaining = clipDur * 1000 - elapsed;
  if (remaining > 0) await wait(remaining);

  await page.close();
  await context.close();
  await wait(500);

  // Rinomina
  const files = fs.readdirSync(CLIPS_DIR)
    .filter(f => f.endsWith(".webm") && !f.match(/^0[12456]_/))
    .sort((a, b) => fs.statSync(path.join(CLIPS_DIR, b)).mtimeMs - fs.statSync(path.join(CLIPS_DIR, a)).mtimeMs);

  if (files.length > 0) {
    fs.renameSync(path.join(CLIPS_DIR, files[0]), clipPath);
    console.log(`\n  03_contratto.webm — ${(fs.statSync(clipPath).size / 1024).toFixed(0)} KB`);
  }

  await browser.close();
  console.log("\n=== Scena 03 ri-registrata ===");
}

main().catch(console.error);

#!/usr/bin/env node
/**
 * Video 01 — "Il Primo Cliente"
 *
 * Pipeline audio-first: durate clip dettate dai VO reali.
 * Ogni scena = un browser context separato con recordVideo.
 * Browser maximized per visualizzazione corretta.
 *
 * Pre-requisiti:
 *   - Backend dev su porta 8001, Frontend dev su porta 3001
 *   - Login con credenziali dev
 *   - VO gia' generati in data/videos/01-primo-cliente/scenes/
 */

const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");
const { execSync } = require("child_process");

// ── Config ──
const BASE_URL = "http://localhost:3001";
const CREDS = { email: "chiarabassani96@gmail.com", password: "Fitness2026!" };
const VIDEO_DIR = path.resolve(__dirname, "../../data/videos/01-primo-cliente");
const CLIPS_DIR = path.join(VIDEO_DIR, "clips");
const SCENES_DIR = path.join(VIDEO_DIR, "scenes");
const FF = "C:\\Users\\gvera\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-8.1-full_build\\bin\\ffprobe.exe";

// Risoluzione di registrazione video (indipendente dal viewport della finestra)
const REC_SIZE = { width: 1440, height: 900 };

// ── Helpers ──

function getVoDuration(sceneName) {
  const file = path.join(SCENES_DIR, `${sceneName}.mp3`);
  const out = execSync(`"${FF}" -v quiet -show_entries format=duration -of csv=p=0 "${file}"`).toString().trim();
  return parseFloat(out);
}

async function wait(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function typeSlowly(page, selector, text, delayMs = 80) {
  await page.click(selector);
  for (const char of text) {
    await page.keyboard.type(char, { delay: delayMs });
  }
}

/**
 * Registra una scena: apre un browser context con recordVideo,
 * esegue le azioni, attende la durata esatta, chiude e salva il clip.
 */
async function recordScene(browser, sceneName, durationSec, actionsFn, authStatePath) {
  const context = await browser.newContext({
    viewport: null, // maximized
    recordVideo: {
      dir: CLIPS_DIR,
      size: REC_SIZE,
    },
    storageState: authStatePath,
  });

  const page = await context.newPage();
  const startTime = Date.now();

  try {
    await actionsFn(page);
  } catch (err) {
    console.error(`  ERRORE in ${sceneName}:`, err.message);
  }

  // Attendi fino alla durata esatta del clip
  const elapsed = Date.now() - startTime;
  const remaining = durationSec * 1000 - elapsed;
  if (remaining > 0) await wait(remaining);

  await page.close();
  const videoPath = await context.pages()[0]?.video()?.path() ?? null;
  await context.close();

  // Rinomina il file video generato da Playwright
  await wait(500); // Attendi flush del file
  const clipPath = path.join(CLIPS_DIR, `${sceneName}.webm`);
  const files = fs.readdirSync(CLIPS_DIR)
    .filter(f => f.endsWith(".webm") && !f.startsWith("0"))
    .sort((a, b) => fs.statSync(path.join(CLIPS_DIR, b)).mtimeMs - fs.statSync(path.join(CLIPS_DIR, a)).mtimeMs);

  if (files.length > 0) {
    const latest = path.join(CLIPS_DIR, files[0]);
    if (fs.existsSync(clipPath)) fs.unlinkSync(clipPath);
    fs.renameSync(latest, clipPath);
  }

  console.log(`  ${sceneName}: ${durationSec.toFixed(1)}s → ${path.basename(clipPath)}`);
}

// ── Main ──

async function main() {
  console.log("=== Video 01: Il Primo Cliente ===\n");

  // Pulisci clip precedenti
  if (fs.existsSync(CLIPS_DIR)) {
    for (const f of fs.readdirSync(CLIPS_DIR)) {
      fs.unlinkSync(path.join(CLIPS_DIR, f));
    }
  }

  // Calcola durate reali dai VO
  const scenes = {
    "01_hook":      { vo: getVoDuration("01_hook"),      pad: 0.5 },
    "02_cliente":   { vo: getVoDuration("02_cliente"),   pad: 2.0 },
    "03_contratto": { vo: getVoDuration("03_contratto"), pad: 3.0 },
    "04_anamnesi":  { vo: getVoDuration("04_anamnesi"),  pad: 2.0 },
    "05_profilo":   { vo: getVoDuration("05_profilo"),   pad: 1.0 },
    "06_cta":       { vo: getVoDuration("06_cta"),       pad: 2.0 },
  };

  console.log("Durate clip (VO + padding per azioni UI):");
  let totalDur = 0;
  for (const [name, s] of Object.entries(scenes)) {
    s.clipDur = s.vo + s.pad;
    totalDur += s.clipDur;
    console.log(`  ${name}: ${s.vo.toFixed(1)}s + ${s.pad}s = ${s.clipDur.toFixed(1)}s`);
  }
  console.log(`  TOTALE: ${totalDur.toFixed(1)}s\n`);

  // ── Auth: login e salva stato ──
  console.log("[setup] Login...");
  const browser = await chromium.launch({
    headless: false,
    slowMo: 50,
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
  console.log("[setup] Auth state salvato\n");

  // ══════════════════════════════════════════════
  // SCENA 01 — Hook: pagina clienti
  // ══════════════════════════════════════════════
  console.log("[rec] Scena 01 — Hook");
  await recordScene(browser, "01_hook", scenes["01_hook"].clipDur, async (page) => {
    await page.goto(`${BASE_URL}/clienti`);
    await page.waitForSelector('[data-guide="clienti-header"]', { timeout: 10000 });
    await wait(1000);
  }, authStatePath);

  // ══════════════════════════════════════════════
  // SCENA 02 — Crea il cliente
  // ══════════════════════════════════════════════
  console.log("[rec] Scena 02 — Crea cliente");
  await recordScene(browser, "02_cliente", scenes["02_cliente"].clipDur, async (page) => {
    await page.goto(`${BASE_URL}/clienti`);
    await page.waitForSelector('[data-guide="clienti-new-button"]', { timeout: 10000 });
    await wait(500);

    // Click "Nuovo Cliente"
    await page.click('[data-guide="clienti-new-button"]');
    await wait(800);

    // Compila form (id= selectors verificati)
    await page.fill('#nome', "Marco");
    await wait(200);
    await page.fill('#cognome', "Ferretti");
    await wait(200);
    await page.fill('#telefono', "339 1234567");
    await wait(400);

    // Submit
    await page.click('button:has-text("Crea Cliente")');
    await wait(1500);

    // Apri profilo
    await page.locator('text=Ferretti').first().click();
    await wait(2000);
  }, authStatePath);

  // ══════════════════════════════════════════════
  // SCENA 03 — Contratto con piano rate
  // ══════════════════════════════════════════════
  console.log("[rec] Scena 03 — Contratto + piano rate");
  await recordScene(browser, "03_contratto", scenes["03_contratto"].clipDur, async (page) => {
    // Naviga al profilo Marco Ferretti
    await page.goto(`${BASE_URL}/clienti`);
    await wait(1000);
    await page.locator('text=Ferretti').first().click();
    await wait(2000);

    // Click "Crea contratto" dalla OnboardingChecklist
    await page.locator('text=Crea contratto').first().click();
    await wait(2000);

    // Compila form contratto (selettori da ContractForm.tsx)
    await page.fill('#tipo_pacchetto', "PT Personal");
    await wait(200);
    await page.fill('#crediti_totali', "10");
    await wait(200);
    await page.fill('#prezzo_totale', "550");
    await wait(200);
    await page.fill('#acconto', "50");
    await wait(500);

    // Submit contratto
    await page.click('button:has-text("Crea Contratto")');
    await wait(2000);

    // Ora siamo nel dettaglio contratto — tab Piano Pagamenti
    // Click su "Genera Piano Pagamenti"
    const genBtn = page.locator('button:has-text("Genera Piano Pagamenti")');
    if (await genBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await genBtn.click();
      await wait(2000); // PAUSA WOW: mostra le rate generate
    }
  }, authStatePath);

  // ══════════════════════════════════════════════
  // SCENA 04 — Anamnesi
  // ══════════════════════════════════════════════
  console.log("[rec] Scena 04 — Anamnesi");
  await recordScene(browser, "04_anamnesi", scenes["04_anamnesi"].clipDur, async (page) => {
    // Torna al profilo
    await page.goto(`${BASE_URL}/clienti`);
    await wait(1000);
    await page.locator('text=Ferretti').first().click();
    await wait(2000);

    // La checklist ora mostra "Anamnesi" — click sulla hero card
    const anamnesiBtn = page.locator('text=Compila').first();
    if (await anamnesiBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await anamnesiBtn.click();
      await wait(2000);
    }

    // Wizard anamnesi — mostra il primo step
    await wait(3000);

    // Naviga tra gli step per mostrare la struttura
    const avantiBtn = page.locator('button:has-text("Avanti")');
    if (await avantiBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await avantiBtn.click();
      await wait(2000);
    }
  }, authStatePath);

  // ══════════════════════════════════════════════
  // SCENA 05 — Profilo completo 2/5
  // ══════════════════════════════════════════════
  console.log("[rec] Scena 05 — Profilo completo");
  await recordScene(browser, "05_profilo", scenes["05_profilo"].clipDur, async (page) => {
    await page.goto(`${BASE_URL}/clienti`);
    await wait(1000);
    await page.locator('text=Ferretti').first().click();
    await wait(2000);

    // Scroll lento per mostrare la checklist
    await page.evaluate(() => window.scrollBy({ top: 400, behavior: "smooth" }));
    await wait(3000);
  }, authStatePath);

  // ══════════════════════════════════════════════
  // SCENA 06 — CTA (title card)
  // Per ora registriamo la pagina guida come placeholder.
  // La title card vera verra' generata come immagine statica.
  // ══════════════════════════════════════════════
  console.log("[rec] Scena 06 — CTA");
  await recordScene(browser, "06_cta", scenes["06_cta"].clipDur, async (page) => {
    await page.goto(`${BASE_URL}/guida`);
    await wait(2000);
  }, authStatePath);

  await browser.close();

  // Verifica clip generati
  console.log("\n=== Registrazione completata ===");
  const clips = fs.readdirSync(CLIPS_DIR).filter(f => f.endsWith(".webm")).sort();
  console.log(`Clip generati: ${clips.length}/6`);
  for (const clip of clips) {
    const stat = fs.statSync(path.join(CLIPS_DIR, clip));
    console.log(`  ${clip} — ${(stat.size / 1024).toFixed(0)} KB`);
  }
  console.log(`\nProssimo step: montaggio FFmpeg (clip + voce + musica)`);
}

main().catch(console.error);

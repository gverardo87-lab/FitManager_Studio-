#!/usr/bin/env node
/**
 * Registra scena 04 — Anamnesi (mancante dopo cleanup).
 */
const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");
const { execSync } = require("child_process");

const BASE_URL = "http://localhost:3001";
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

async function main() {
  const voDur = getVoDuration("04_anamnesi");
  const clipDur = voDur + 2.0;
  console.log(`Scena 04 — VO: ${voDur.toFixed(1)}s + pad 2s = clip ${clipDur.toFixed(1)}s\n`);

  const browser = await chromium.launch({
    headless: false, slowMo: 80, args: ["--start-maximized"],
  });

  // Login
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

  // Registra
  const clipPath = path.join(CLIPS_DIR, "04_anamnesi.webm");
  if (fs.existsSync(clipPath)) fs.unlinkSync(clipPath);

  const context = await browser.newContext({
    viewport: null,
    recordVideo: { dir: CLIPS_DIR, size: REC_SIZE },
    storageState: authStatePath,
  });

  const page = await context.newPage();
  const startTime = Date.now();

  try {
    // Profilo Marco Ferretti
    await page.goto(`${BASE_URL}/clienti`);
    await wait(1500);
    await page.locator('text=Ferretti').first().click();
    await wait(2000);

    // La checklist mostra "Anamnesi" come prossimo step (contratto gia' fatto)
    // Click sulla hero card anamnesi
    const compila = page.locator('text=Compila').first();
    if (await compila.isVisible({ timeout: 3000 }).catch(() => false)) {
      await compila.click();
      await wait(2000);
    }

    // Wizard anamnesi — mostra la struttura
    await wait(2000);

    // Naviga tra step se possibile
    const avanti = page.locator('button:has-text("Avanti")');
    if (await avanti.isVisible({ timeout: 2000 }).catch(() => false)) {
      await avanti.click();
      await wait(2000);
    }
  } catch (err) {
    console.error("  ERRORE:", err.message);
  }

  const elapsed = Date.now() - startTime;
  const remaining = clipDur * 1000 - elapsed;
  if (remaining > 0) await wait(remaining);

  await page.close();
  await context.close();
  await wait(500);

  // Rinomina
  const files = fs.readdirSync(CLIPS_DIR)
    .filter(f => f.endsWith(".webm") && !f.match(/^0[12356]_/))
    .sort((a, b) => fs.statSync(path.join(CLIPS_DIR, b)).mtimeMs - fs.statSync(path.join(CLIPS_DIR, a)).mtimeMs);
  if (files.length > 0) {
    fs.renameSync(path.join(CLIPS_DIR, files[0]), clipPath);
    console.log(`  04_anamnesi.webm — ${(fs.statSync(clipPath).size / 1024).toFixed(0)} KB`);
  }

  await browser.close();
  console.log("\n=== Scena 04 registrata ===");
}

main().catch(console.error);

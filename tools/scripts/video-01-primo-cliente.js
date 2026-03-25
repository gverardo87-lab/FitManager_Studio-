#!/usr/bin/env node
/**
 * Video 01 — "Il Primo Cliente" — Registrazione flusso continuo
 *
 * UN browser, UN context, UN clip.
 * Ogni selettore verificato contro docs/VIDEO_PRODUCTION.md §4.
 *
 * Pre-run: pulizia completa dati test in crm_dev.db.
 */

const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");
const { execSync } = require("child_process");
const { getSceneTiming, readManifest, writeManifest, getDuration } = require("../video/lib");

const BASE_URL = "http://localhost:3001";
const API_URL = "http://localhost:8001/api";
const CREDS = { email: "chiarabassani96@gmail.com", password: "Fitness2026!" };
const VIDEO_DIR = path.resolve(__dirname, "../../data/videos/01-primo-cliente");
const CLIPS_DIR = path.join(VIDEO_DIR, "clips");
const PYTHON = path.resolve(__dirname, "../../venv/Scripts/python.exe");

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

// ═══════════════════════════════════════════
// Selettori da VIDEO_PRODUCTION.md §4.6, §4.7
// ═══════════════════════════════════════════

async function selectDate(page, triggerText, targetDataDay) {
  // §4.6: click trigger → naviga mese → click data-day DD/MM/YYYY
  await page.locator(`button:has-text("${triggerText}")`).click();
  await wait(500);
  const dayBtn = page.locator(`button[data-day="${targetDataDay}"]`);
  for (let i = 0; i < 8; i++) {
    if (await dayBtn.isVisible({ timeout: 400 }).catch(() => false)) {
      await dayBtn.click();
      await wait(300);
      return;
    }
    await page.locator("button.rdp-button_next").click();
    await wait(400);
  }
  throw new Error(`Data ${targetDataDay} non trovata`);
}

// VO-locked wait
async function voLock(startMs, sceneName) {
  const timing = getSceneTiming(VIDEO_DIR, sceneName);
  const remaining = timing.minDuration - (Date.now() - startMs) / 1000;
  if (remaining > 0) {
    console.log(`  vo-lock: +${remaining.toFixed(1)}s`);
    await wait(remaining * 1000);
  }
}

// ═══════════════════════════════════════════
// Pre-run: pulizia completa crm_dev.db
// ═══════════════════════════════════════════

function preRunCleanup() {
  console.log("[pre-run] Pulizia DB...");
  const cleanupScript = path.resolve(__dirname, "video-cleanup-moretti.py");
  execSync(`"${PYTHON}" "${cleanupScript}"`, { stdio: "inherit" });
}

// ═══════════════════════════════════════════
// Main
// ═══════════════════════════════════════════

async function main() {
  console.log("=== Video 01: Il Primo Cliente ===\n");
  preRunCleanup();
  fs.mkdirSync(CLIPS_DIR, { recursive: true });

  // Timing
  const manifest = readManifest(VIDEO_DIR);
  let total = 0;
  for (const s of manifest.scenes) {
    if (s.vo.duration) {
      const d = s.vo.duration + s.gap;
      total += d;
      console.log(`  ${s.name}: ${s.vo.duration.toFixed(1)}s + ${s.gap}s = ${d.toFixed(1)}s`);
    }
  }
  console.log(`  TOTALE: ~${total.toFixed(0)}s\n`);

  // Login
  const browser = await chromium.launch({ headless: false, slowMo: 80, args: ["--start-maximized"] });
  const authCtx = await browser.newContext({ viewport: null });
  const authPage = await authCtx.newPage();
  await authPage.goto(`${BASE_URL}/login`);
  await authPage.waitForSelector('input[type="email"]', { timeout: 10000 });
  await authPage.fill('input[type="email"]', CREDS.email);
  await authPage.fill('input[type="password"]', CREDS.password);
  await authPage.click('button[type="submit"]');
  await authPage.waitForURL("**/", { timeout: 10000 });
  await wait(2000);

  // Prendi token API per trovare il contratto dopo
  const token = await authPage.evaluate(() => {
    const match = document.cookie.match(/fitmanager_token=([^;]+)/);
    return match ? match[1] : null;
  });

  const authStatePath = path.join(VIDEO_DIR, "auth-state.json");
  await authCtx.storageState({ path: authStatePath });
  await authPage.close();
  await authCtx.close();
  console.log("[setup] Login OK, token catturato\n");

  // ═══════════════════════════════════════════
  // REGISTRAZIONE — un context, un clip
  // ═══════════════════════════════════════════
  const clipPath = path.join(CLIPS_DIR, "full_flow.webm");
  if (fs.existsSync(clipPath)) fs.unlinkSync(clipPath);

  const context = await browser.newContext({
    viewport: null,
    recordVideo: { dir: CLIPS_DIR, size: { width: 1440, height: 900 } },
    storageState: authStatePath,
  });
  const page = await context.newPage();
  const recStart = Date.now();
  const markers = [];

  // ── SCENA 01 — Hook ──────────────────────
  // §4.1: /clienti → [data-guide="clienti-header"]
  console.log("[01] Hook");
  const s01 = Date.now();
  markers.push({ name: "01_hook", start: (s01 - recStart) / 1000 });
  await page.goto(`${BASE_URL}/clienti`);
  await page.waitForSelector('[data-guide="clienti-header"]', { timeout: 10000 });
  await wait(500);
  await voLock(s01, "01_hook");

  // ── SCENA 02 — Crea cliente ──────────────
  // §4.1: [data-guide="clienti-new-button"] → §4.2: #nome, #cognome, #telefono → submit
  // Post-submit: AUTO-REDIRECT a /clienti/[id] (§4.3: client-avatar-hero)
  console.log("[02] Crea cliente");
  const s02 = Date.now();
  markers.push({ name: "02_cliente", start: (s02 - recStart) / 1000 });
  await page.click('[data-guide="clienti-new-button"]');
  await wait(600);
  await page.fill("#nome", "Luca");
  await wait(150);
  await page.fill("#cognome", "Moretti");
  await wait(150);
  await page.fill("#telefono", "340 5678901");
  await wait(300);
  await page.click('button:has-text("Crea Cliente")');
  // AUTO-REDIRECT al profilo — NON cercare nella lista
  await page.waitForSelector('[data-guide="client-avatar-hero"]', { timeout: 15000 });
  await wait(500);
  await voLock(s02, "02_cliente");

  // ── SCENA 03 — Contratto + rate ──────────
  // §4.3: checklist → "Crea contratto" (apre ContractSheet INLINE, non naviga)
  // §4.4: form contratto nella sheet
  // §4.6: DatePicker per date
  // §4.7: Radix Select per metodo — ATTENZIONE: 2 select nella sheet (cliente + metodo)
  // Post-submit: sheet si chiude, restiamo sul profilo
  // Poi: API per trovare contractId → navigare a /contratti/[id]
  // §4.5: dettaglio contratto → genera rate
  console.log("[03] Contratto + rate");
  const s03 = Date.now();
  markers.push({ name: "03_contratto", start: (s03 - recStart) / 1000 });

  await page.waitForSelector('[data-guide="client-onboarding-checklist"]', { timeout: 10000 });
  await wait(800);

  // §4.3: CTA "Crea contratto"
  await page.locator("text=Crea contratto").first().click();
  await wait(1500);

  // §4.4: campi form
  await page.fill("#tipo_pacchetto", "Pacchetto 10");
  await wait(200);
  await page.fill("#crediti_totali", "10");
  await wait(200);
  await page.fill("#prezzo_totale", "550");
  await wait(200);

  // §4.6: DatePicker inizio e scadenza
  await selectDate(page, "Inizio...", "01/04/2026");
  await wait(300);
  await selectDate(page, "Scadenza...", "01/06/2026");
  await wait(300);

  // §4.4: acconto (deve essere PRIMA del metodo — il select appare solo se acconto > 0)
  await page.fill("#acconto", "50");
  await wait(800);

  // §4.7: Radix Select metodo — usare :has-text("Metodo") NON :last-of-type
  // (la sheet ha 2 select: cliente e metodo, :last-of-type risolve a entrambi)
  const metodoTrigger = page.locator('[data-slot="select-trigger"]:has-text("Metodo")');
  await metodoTrigger.waitFor({ state: "visible", timeout: 3000 });
  await metodoTrigger.click();
  await wait(400);
  await page.locator('[data-slot="select-item"]:has-text("BONIFICO")').click();
  await wait(300);

  // §4.4: scroll sheet al submit
  await page.evaluate(() => {
    const s = document.querySelector('[data-slot="sheet-content"]');
    if (s) s.scrollTo({ top: s.scrollHeight, behavior: "smooth" });
  });
  await wait(500);

  // §4.4: submit contratto
  await page.click('button[type="submit"]:has-text("Crea Contratto")');
  await wait(3000);

  // Sheet chiusa, siamo sul profilo. Troviamo il contratto via API backend diretta.
  const clientId = page.url().match(/\/clienti\/(\d+)/)?.[1];
  const contractResp = await page.evaluate(async (cid) => {
    const r = await fetch(`http://localhost:8001/api/contracts?page_size=200`, {
      headers: { "Authorization": `Bearer ${document.cookie.match(/fitmanager_token=([^;]+)/)?.[1] || ""}` },
    });
    const data = await r.json();
    const c = data.items?.find(x => x.id_cliente === parseInt(cid));
    return c?.id;
  }, clientId);
  const contractId = contractResp;
  console.log(`  cliente=${clientId}, contratto=${contractId}`);

  // §4.5: naviga al dettaglio contratto
  await page.goto(`${BASE_URL}/contratti/${contractId}`);
  await page.waitForSelector('[data-guide="contratto-header"]', { timeout: 10000 });
  await wait(1000);

  // §4.5: scroll a piano rate
  const pianoRate = page.locator('[data-guide="contratto-piano-rate"]');
  await pianoRate.scrollIntoViewIfNeeded();
  await wait(1000);

  // §4.5: numero rate
  await page.fill("#numero_rate", "2");
  await wait(300);

  // §4.5 + §4.6: data prima rata
  await selectDate(page, "Seleziona data...", "01/05/2026");
  await wait(500);

  // §4.5: genera piano — DISABLED se data non selezionata (gia' selezionata sopra)
  await page.click('button:has-text("Genera Piano Pagamenti")');
  await wait(1500);

  // Scroll per mostrare le rate — MOMENTO WOW
  await page.evaluate(() => window.scrollBy({ top: 300, behavior: "smooth" }));
  await wait(2500);
  await voLock(s03, "03_contratto");

  // ── SCENA 04 — Anamnesi ──────────────────
  // goBack al profilo → §4.3: "Compila" → §4.8: wizard
  console.log("[04] Anamnesi");
  const s04 = Date.now();
  markers.push({ name: "04_anamnesi", start: (s04 - recStart) / 1000 });

  await page.goBack();
  await wait(2000);
  await page.waitForSelector('[data-guide="client-avatar-hero"]', { timeout: 10000 });
  await page.waitForSelector('[data-guide="client-onboarding-checklist"]', { timeout: 10000 });
  await wait(800);

  // §4.3: CTA "Compila" (anamnesi)
  await page.locator("text=Compila").first().click();
  await wait(2000);

  // §4.8: "Compila tu" apre il wizard
  await page.click('button:has-text("Compila tu")');
  await wait(1500);

  // §4.8: Avanti x3 → step 4 "Salute"
  for (let i = 0; i < 3; i++) {
    await page.click('button:has-text("Avanti")');
    await wait(600);
  }
  await wait(500);

  // Step 4: dolori
  const schiena = page.locator('div:has-text("Schiena")').first();
  if (await schiena.isVisible({ timeout: 1000 }).catch(() => false)) {
    await schiena.click();
    await wait(300);
  }
  const ginocchia = page.locator('div:has-text("Ginocchia")').first();
  if (await ginocchia.isVisible({ timeout: 1000 }).catch(() => false)) {
    await ginocchia.click();
    await wait(300);
  }

  // Infortuni
  const infortuniSw = page.locator('text=Hai avuto infortuni importanti').locator("..").locator("button[role='switch']");
  if (await infortuniSw.isVisible({ timeout: 1000 }).catch(() => false)) {
    await infortuniSw.click();
    await wait(500);
    const ta = page.locator('textarea[placeholder*="fratture"]').first();
    if (await ta.isVisible({ timeout: 500 }).catch(() => false)) {
      await ta.fill("Ernia lombare L4-L5");
      await wait(300);
    }
  }

  // Patologie
  const patologieSw = page.locator('text=Hai patologie diagnosticate').locator("..").locator("button[role='switch']");
  if (await patologieSw.isVisible({ timeout: 1000 }).catch(() => false)) {
    await patologieSw.click();
    await wait(500);
    const ernie = page.locator('div:has-text("Ernie")').first();
    if (await ernie.isVisible({ timeout: 500 }).catch(() => false)) {
      await ernie.click();
      await wait(200);
    }
  }

  // §4.8: Avanti x2 → Salva
  for (let i = 0; i < 2; i++) {
    const av = page.locator('button:has-text("Avanti")');
    if (await av.isVisible({ timeout: 1000 }).catch(() => false)) {
      await av.click();
      await wait(500);
    }
  }
  const salva = page.locator('button:has-text("Salva")');
  if (await salva.isVisible({ timeout: 1000 }).catch(() => false)) {
    await salva.click();
    await wait(1500);
  }
  await voLock(s04, "04_anamnesi");

  // ── SCENA 05 — Profilo completo ──────────
  console.log("[05] Profilo");
  const s05 = Date.now();
  markers.push({ name: "05_profilo", start: (s05 - recStart) / 1000 });

  await page.goBack();
  await wait(2000);
  await page.waitForSelector('[data-guide="client-avatar-hero"]', { timeout: 10000 });
  await page.waitForSelector('[data-guide="client-onboarding-checklist"]', { timeout: 10000 });
  await wait(1000);
  await page.evaluate(() => window.scrollBy({ top: 400, behavior: "smooth" }));
  await wait(2000);
  await voLock(s05, "05_profilo");

  // ── SCENA 06 — CTA ──────────────────────
  // §4.9: /guida → [data-guide="guida-hero"]
  console.log("[06] CTA");
  const s06 = Date.now();
  markers.push({ name: "06_cta", start: (s06 - recStart) / 1000 });

  await page.goto(`${BASE_URL}/guida`);
  await page.waitForSelector('[data-guide="guida-hero"]', { timeout: 10000 });
  await wait(1000);
  await voLock(s06, "06_cta");

  // ═══════════════════════════════════════════
  // Fine — salva clip
  // ═══════════════════════════════════════════
  const totalDur = (Date.now() - recStart) / 1000;
  markers.push({ name: "_end", start: totalDur });

  const video = page.video();
  await page.close();
  if (fs.existsSync(clipPath)) fs.unlinkSync(clipPath);
  await video.saveAs(clipPath);
  await context.close();
  await browser.close();

  // Report
  console.log(`\n=== REGISTRAZIONE OK: ${totalDur.toFixed(1)}s ===`);
  console.log(`  ${clipPath} (${(fs.statSync(clipPath).size / 1024 / 1024).toFixed(1)} MB)`);
  console.log("\n  Scene:");
  for (let i = 0; i < markers.length - 1; i++) {
    const m = markers[i], n = markers[i + 1];
    console.log(`    ${m.name}: ${m.start.toFixed(1)}s → ${n.start.toFixed(1)}s (${(n.start - m.start).toFixed(1)}s)`);
  }

  // Aggiorna manifest
  const mf = readManifest(VIDEO_DIR);
  mf.recording_mode = "continuous";
  mf.recording_file = "clips/full_flow.webm";
  mf.recording_duration = totalDur;
  for (const marker of markers) {
    const scene = mf.scenes.find((s) => s.name === marker.name);
    if (scene) scene.recording.scene_start = parseFloat(marker.start.toFixed(3));
  }
  for (let i = 0; i < mf.scenes.length; i++) {
    const next = i < mf.scenes.length - 1 ? mf.scenes[i + 1] : null;
    mf.scenes[i].recording.scene_end = next ? next.recording.scene_start : parseFloat(totalDur.toFixed(3));
    mf.scenes[i].recording.clip_duration = mf.scenes[i].recording.scene_end - mf.scenes[i].recording.scene_start;
    mf.scenes[i].recording.trim_start = 0;
    mf.scenes[i].recording.file = "clips/full_flow.webm";
  }
  writeManifest(VIDEO_DIR, mf);
  console.log("\n  Manifest aggiornato.");
  console.log("\n  Montaggio: node tools/video/montage.js data/videos/01-primo-cliente");
}

main().catch((e) => {
  console.error(`\n[FAIL] ${e.message}`);
  process.exit(1);
});

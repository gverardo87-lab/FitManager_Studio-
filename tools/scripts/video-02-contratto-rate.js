#!/usr/bin/env node
/**
 * Video 02 — "Contratto e Rate — Il Rinnovo" — Registrazione flusso continuo
 *
 * VERSIONE 2: azioni distribuite lungo il VO, zero tempi morti.
 * Ogni secondo ha contenuto visivo. Mai piu' di 1.5s di schermo fermo.
 *
 * Pre-run: video-02-setup.py (seed contratto scaduto con rate pagate).
 */

const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");
const { execSync } = require("child_process");
const { readManifest, writeManifest } = require("../video/lib");

const BASE_URL = "http://localhost:3001";
const CREDS = { email: "chiarabassani96@gmail.com", password: "Fitness2026!" };
const VIDEO_DIR = path.resolve(__dirname, "../../data/videos/02-contratto-rate");
const CLIPS_DIR = path.join(VIDEO_DIR, "clips");
const PYTHON = path.resolve(__dirname, "../../venv/Scripts/python.exe");

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

// §4.6 — DatePicker
async function selectDate(page, triggerText, targetDataDay) {
  const trigger = page.locator(`button:has-text("${triggerText}")`);
  await trigger.scrollIntoViewIfNeeded();
  await trigger.click();
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

// Smooth scroll lento (visivamente leggibile)
async function smoothScroll(page, pixels, durationMs = 800) {
  await page.evaluate(
    ({ px, dur }) => window.scrollBy({ top: px, behavior: "smooth" }),
    { px: pixels, dur: durationMs }
  );
  await wait(durationMs);
}

// Pre-run setup
function preRunSetup() {
  console.log("[pre-run] Setup DB...");
  execSync(`"${PYTHON}" "${path.resolve(__dirname, "video-02-setup.py")}"`, {
    stdio: "inherit",
  });
}

// ═══════════════════════════════════════════
// Main
// ═══════════════════════════════════════════
async function main() {
  console.log("=== Video 02: Contratto e Rate (v2 — paced) ===\n");
  preRunSetup();
  fs.mkdirSync(CLIPS_DIR, { recursive: true });

  // Login
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

  const token = await authPage.evaluate(() => {
    const match = document.cookie.match(/fitmanager_token=([^;]+)/);
    return match ? match[1] : null;
  });
  if (!token) throw new Error("Token non trovato!");

  const authStatePath = path.join(VIDEO_DIR, "auth-state.json");
  await authCtx.storageState({ path: authStatePath });
  await authPage.close();
  await authCtx.close();
  console.log("[setup] Login OK\n");

  // ═══════════════════════════════════════════
  // REGISTRAZIONE — azioni distribuite, zero tempi morti
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

  // ══════════════════════════════════════════════════════════════
  // SCENA 01 — Hook (VO 8.4s)
  // "Il mese di Luca si chiude. Dalla pagina Rinnovi vedi subito
  //  chi sta per scadere — e rinnovi senza perdere un dato."
  //
  // Azioni distribuite:
  //  0.0  → Parto dalla Dashboard (contesto reale, non URL diretto)
  //  1.5  → Click "Rinnovi" nella sidebar
  //  3.5  → Pagina carica, KPI visibili
  //  4.5  → Scroll lento per rivelare le card
  //  6.0  → La card Moretti appare con badge "Scade tra 5g"
  //  7.5  → Hover sulla card Moretti
  // ══════════════════════════════════════════════════════════════
  console.log("[01] Hook — Dashboard → Rinnovi");
  const s01 = Date.now();
  markers.push({ name: "01_hook", start: 0 });

  // Parto dalla Dashboard (piu' naturale di un goto diretto)
  await page.goto(`${BASE_URL}/`);
  await page.locator('[data-guide="dashboard-header"]').waitFor({ timeout: 10000 });
  await wait(1200);

  // Click "Rinnovi" nella sidebar (navigazione reale)
  await page.locator('a[href="/rinnovi-incassi"]').click();
  await page.locator("p:has-text('Da rinnovare')").first().waitFor({ timeout: 10000 });
  await wait(800);

  // Scroll lento per rivelare le card sotto le KPI
  await smoothScroll(page, 250, 1000);
  await wait(600);

  // Individua card Moretti
  const morettiCard = page.locator("div.rounded-xl").filter({ hasText: "Luca Moretti" });
  await morettiCard.first().waitFor({ timeout: 5000 });

  // Hover sulla card (il mouse si muove visivamente)
  await morettiCard.first().hover();
  await wait(1200);

  console.log(`  Scena 01: ${((Date.now() - s01) / 1000).toFixed(1)}s`);

  // ══════════════════════════════════════════════════════════════
  // SCENA 02 — Rinnova (VO 9.2s)
  // "Un click su Rinnova. Il sistema propone le stesse condizioni:
  //  pacchetto, crediti, prezzo. Tu scegli solo le nuove date."
  //
  // Azioni distribuite:
  //  0.0  → Click "Rinnova" dentro card Moretti
  //  0.6  → Sheet slide-in, titolo "Rinnova Contratto"
  //  1.5  → Hover su campo Cliente (locked, grigio) — mostra che e' disabilitato
  //  3.0  → Hover su campo "Mensile 4 Sedute" — pacchetto pre-compilato
  //  4.5  → Hover su campo Crediti "4" — crediti pre-compilati
  //  6.0  → Hover su campo Prezzo "300" — prezzo pre-compilato
  //  7.5  → Scroll lento verso i DatePicker vuoti
  //  8.5  → I campi data vuoti "Inizio..." / "Scadenza..." sono visibili
  // ══════════════════════════════════════════════════════════════
  console.log("[02] Rinnova → Sheet");
  const s02 = Date.now();
  markers.push({ name: "02_rinnova", start: (s02 - recStart) / 1000 });

  // Click Rinnova nella card Moretti
  await morettiCard.first().locator('button:has-text("Rinnova")').click();
  await wait(600);

  // Sheet aperta
  await page.locator("text=Rinnova Contratto").first().waitFor({ timeout: 5000 });
  await wait(800);

  // Hover lento su ogni campo pre-compilato (il viewer legge)
  // Campo cliente (select disabilitato)
  const clientSelect = page.locator('[data-slot="select-trigger"]').first();
  await clientSelect.hover();
  await wait(1200);

  // Campo tipo pacchetto
  await page.locator("#tipo_pacchetto").hover();
  await wait(1200);

  // Campo crediti
  await page.locator("#crediti_totali").hover();
  await wait(1200);

  // Campo prezzo
  await page.locator("#prezzo_totale").hover();
  await wait(1200);

  // Scroll verso i DatePicker vuoti
  await page.evaluate(() => {
    const s = document.querySelector('[data-slot="sheet-content"]');
    if (s) s.scrollTo({ top: 200, behavior: "smooth" });
  });
  await wait(1000);

  console.log(`  Scena 02: ${((Date.now() - s02) / 1000).toFixed(1)}s`);

  // ══════════════════════════════════════════════════════════════
  // SCENA 03 — Date + conferma (VO 8.1s)
  // "Primo aprile, trenta aprile. Confermi — e il nuovo contratto
  //  è attivo. La ricevuta di rinnovo è nel Libro Mastro."
  //
  // Azioni distribuite:
  //  0.0  → Click DatePicker "Inizio..." → calendario apre
  //  1.0  → Naviga ad Aprile → click 01
  //  2.0  → Pausa (vede data selezionata)
  //  2.5  → Click DatePicker "Scadenza..." → click 30
  //  3.5  → Pausa (vede entrambe le date compilate)
  //  4.5  → Scroll al submit
  //  5.5  → Click "Rinnova Contratto"
  //  6.5  → Toast "Contratto rinnovato" appare
  //  7.0  → Sheet si chiude, card Moretti sparisce dalla lista
  // ══════════════════════════════════════════════════════════════
  console.log("[03] Date + conferma");
  const s03 = Date.now();
  markers.push({ name: "03_conferma", start: (s03 - recStart) / 1000 });

  // Data inizio
  await selectDate(page, "Inizio...", "01/04/2026");
  await wait(800); // pausa: il viewer vede "1 apr 2026" selezionato

  // Data scadenza
  await selectDate(page, "Scadenza...", "30/04/2026");
  await wait(1000); // pausa: entrambe le date visibili

  // Scroll al submit
  await page.evaluate(() => {
    const s = document.querySelector('[data-slot="sheet-content"]');
    if (s) s.scrollTo({ top: s.scrollHeight, behavior: "smooth" });
  });
  await wait(800);

  // Submit
  await page.locator('button:has-text("Rinnova Contratto")').click();
  await wait(2000); // API + toast + sheet close

  // Toast
  try {
    await page.locator("text=Contratto rinnovato").waitFor({ timeout: 5000 });
    console.log("  Toast OK");
  } catch {
    console.warn("  ⚠ Toast non trovato");
  }

  // Pausa su pagina rinnovi (card sparita — il viewer nota la differenza)
  await wait(1500);

  console.log(`  Scena 03: ${((Date.now() - s03) / 1000).toFixed(1)}s`);

  // ══════════════════════════════════════════════════════════════
  // SCENA 04 — Catena + Hero (VO 11.7s)
  // "Apriamo il nuovo contratto. In alto, la catena di rinnovo:
  //  dal contratto originale a quello di aprile. La storia del
  //  cliente resta collegata, mese dopo mese."
  //
  // Azioni distribuite:
  //  0.0  → Click sidebar "Contratti" (navigazione reale)
  //  1.5  → Lista contratti carica
  //  2.5  → Click sulla riga Moretti nella tabella
  //  4.0  → Dettaglio contratto carica: header "Mensile 4 Sedute" + badge "Attivo"
  //  5.0  → Scroll lento alla catena di rinnovo
  //  6.0  → Pausa: due badge [Marzo] → [Aprile] collegati
  //  7.5  → Hover sul badge contratto originale (Marzo)
  //  8.5  → Scroll lento al hero finanziario
  //  9.5  → Hover su KPI "Valore €300"
  // 10.5  → Hover su KPI "Residuo €300"
  // 11.5  → Pausa sull'hero completo
  // ══════════════════════════════════════════════════════════════
  console.log("[04] Catena + Hero");
  const s04 = Date.now();
  markers.push({ name: "04_catena", start: (s04 - recStart) / 1000 });

  // Trova nuovo contratto via API
  const newContractId = await page.evaluate(async (tkn) => {
    const r = await fetch("http://localhost:8001/api/contracts?page_size=200", {
      headers: { Authorization: "Bearer " + tkn },
    });
    const data = await r.json();
    const c = data.items?.find(
      (x) =>
        x.data_inizio === "2026-04-01" &&
        x.tipo_pacchetto === "Mensile 4 Sedute" &&
        x.rinnovo_di
    );
    return c?.id;
  }, token);
  if (!newContractId) throw new Error("Contratto rinnovato non trovato!");
  console.log(`  Nuovo contratto: #${newContractId}`);

  // Naviga a lista contratti (piu' naturale di goto diretto)
  await page.locator('a[href="/contratti"]').click();
  await page.locator('[data-guide="contratti-header"]').waitFor({ timeout: 10000 });
  await wait(1000);

  // Click sulla riga del contratto nella tabella
  // Il contratto Moretti di Aprile dovrebbe essere visibile
  // Navighiamo direttamente — piu' sicuro e il viewer vede il risultato
  await page.goto(`${BASE_URL}/contratti/${newContractId}`);
  await page.locator('[data-guide="contratto-header"]').waitFor({ timeout: 10000 });
  await wait(1200);

  // Scroll alla catena di rinnovo
  const chainEl = page.locator('[data-guide="contratto-catena-rinnovi"]');
  if (await chainEl.isVisible({ timeout: 2000 }).catch(() => false)) {
    await chainEl.scrollIntoViewIfNeeded();
    await wait(1000);

    // Hover sui badge della catena
    const chainBadges = chainEl.locator("a, span").filter({ hasText: /Mensile/ });
    const badgeCount = await chainBadges.count();
    for (let i = 0; i < Math.min(badgeCount, 3); i++) {
      await chainBadges.nth(i).hover();
      await wait(800);
    }
    console.log("  Catena rinnovi: hover OK");
  } else {
    console.warn("  ⚠ Catena non visibile");
    await wait(2000);
  }

  // Scroll al hero finanziario
  const hero = page.locator('[data-guide="contratto-hero-finanziario"]');
  await hero.scrollIntoViewIfNeeded();
  await wait(1000);

  // Hover sulle KPI card del hero (il viewer legge i numeri)
  // Valore contratto
  const kpiCards = hero.locator(".rounded-lg, .rounded-xl").filter({ hasText: /€/ });
  const kpiCount = await kpiCards.count();
  for (let i = 0; i < Math.min(kpiCount, 3); i++) {
    await kpiCards.nth(i).hover();
    await wait(800);
  }

  await wait(800);
  console.log(`  Scena 04: ${((Date.now() - s04) / 1000).toFixed(1)}s`);

  // ══════════════════════════════════════════════════════════════
  // SCENA 05 — CTA (VO 5.7s) — pausa finale, title card in post
  // "Rinnovi, catena, finanze. Tutto sotto controllo, tutto in un posto."
  // ══════════════════════════════════════════════════════════════
  console.log("[05] CTA");
  const s05 = Date.now();
  markers.push({ name: "05_cta", start: (s05 - recStart) / 1000 });

  // Scroll lento a inizio pagina per chiusura elegante
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: "smooth" }));
  await wait(1500);

  // Pausa sull'header con badge "Attivo"
  await wait(2000);

  // Scroll finale lento verso le tab
  await smoothScroll(page, 150, 1000);
  await wait(2000);

  console.log(`  Scena 05: ${((Date.now() - s05) / 1000).toFixed(1)}s`);

  // ═══════════════════════════════════════════
  // CHIUSURA
  // ═══════════════════════════════════════════
  const recEnd = Date.now();
  const totalDuration = (recEnd - recStart) / 1000;
  console.log(`\n[rec] Durata totale: ${totalDuration.toFixed(1)}s`);

  await page.close();
  await context.close();
  await wait(1000);

  // Rinomina clip
  const clipsFiles = fs.readdirSync(CLIPS_DIR).filter((f) => f.endsWith(".webm"));
  const latestClip = clipsFiles
    .map((f) => ({ name: f, time: fs.statSync(path.join(CLIPS_DIR, f)).mtimeMs }))
    .sort((a, b) => b.time - a.time)[0].name;

  const finalClipPath = path.join(CLIPS_DIR, "full_flow.webm");
  if (latestClip !== "full_flow.webm") {
    fs.renameSync(path.join(CLIPS_DIR, latestClip), finalClipPath);
  }
  console.log(`[rec] Clip: ${finalClipPath}`);

  // Aggiorna manifest
  const m = readManifest(VIDEO_DIR);
  m.recording_file = "clips/full_flow.webm";
  m.recording_duration = totalDuration;
  for (const marker of markers) {
    const scene = m.scenes.find((s) => s.name === marker.name);
    if (scene) {
      scene.recording.file = "clips/full_flow.webm";
      scene.recording.scene_start = marker.start;
      scene.recording.recorded_at = new Date().toISOString();
      const idx = markers.indexOf(marker);
      const nextStart =
        idx < markers.length - 1 ? markers[idx + 1].start : totalDuration;
      scene.recording.scene_end = nextStart;
      scene.recording.clip_duration = nextStart - marker.start;
      scene.recording.trim_start = 0;
    }
  }
  writeManifest(VIDEO_DIR, m);
  console.log("[rec] Manifest aggiornato");

  await browser.close();

  console.log("\n═══════════════════════════════════════════");
  console.log("REGISTRAZIONE v2 COMPLETATA");
  console.log("═══════════════════════════════════════════");
  console.log(`Durata: ${totalDuration.toFixed(1)}s`);
  for (const m of markers) console.log(`  ${m.name}: ${m.start.toFixed(1)}s`);
}

main().catch((err) => {
  console.error("\nFATAL:", err);
  process.exit(1);
});

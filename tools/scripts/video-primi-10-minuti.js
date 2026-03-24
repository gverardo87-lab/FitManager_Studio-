/**
 * FitManager Studio+ — Video "I Primi 10 Minuti"
 *
 * Metodo: Audio-First, scena per scena
 * Script editoriale: docs/videos/primi-10-minuti.md
 *
 * Pipeline:
 *   FASE 2 → Genera voiceover per scena (edge-tts + FFmpeg)
 *   FASE 3 → Registra UI scena per scena (Playwright, durata = VO + padding)
 *   FASE 4 → Montaggio finale (FFmpeg concat + sidechain mix)
 *
 * Usage: node tools/scripts/video-primi-10-minuti.js
 * Output: data/videos/primi-10-minuti/primi-10-minuti.mp4
 */

const { chromium } = require("playwright");
const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

// ══════════════════════════════════════════════════════════════
// CONFIG
// ══════════════════════════════════════════════════════════════
const ROOT = path.join(__dirname, "../..");
const OUT = path.join(ROOT, "data/videos/primi-10-minuti");
const FF = "C:/Users/gvera/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1-full_build/bin/ffmpeg.exe";
const FFP = FF.replace("ffmpeg.exe", "ffprobe.exe");
const TTS = path.join(ROOT, "venv/Scripts/edge-tts.exe");
const BASE = "http://localhost:3001";
const API = "http://localhost:8001";
const CREDS = { email: "chiarabassani96@gmail.com", password: "Fitness2026!" };
const VOICE = "it-IT-DiegoNeural";
const RATE = "+5%";
const VP = { width: 1440, height: 900 };

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════
function run(cmd) {
  const s = cmd.length > 160 ? cmd.substring(0, 157) + "..." : cmd;
  console.log(`    $ ${s}`);
  return execSync(cmd, { encoding: "utf8", stdio: "pipe", maxBuffer: 20 * 1024 * 1024 });
}

function dur(f) {
  return parseFloat(run(`"${FFP}" -v quiet -show_entries format=duration -of csv=p=0 "${f}"`).trim());
}

function ensureDir(d) { fs.mkdirSync(d, { recursive: true }); }

function fmtTime(s) { return `${Math.floor(s / 60)}:${(s % 60).toFixed(1).padStart(4, "0")}`; }

// ══════════════════════════════════════════════════════════════
// SCRIPT EDITORIALE — voiceover per scena
// ══════════════════════════════════════════════════════════════
const SCENES = [
  {
    id: "01_hook",
    type: "card",  // title card, non registrazione UI
    vo: "Schede su Excel. Pagamenti su WhatsApp. Anamnesi su carta. Ogni giorno perdi tempo invece di lavorare.",
    padding: 1.2,  // respiro dopo la frase
  },
  {
    id: "02_soluzione",
    type: "app",
    vo: "FitManager fa tutto questo per te. Vediamo come.",
    padding: 0.8,
    page: "/",  // dashboard
    actions: async (page, dur) => {
      // Dashboard statica — mostra gauge, TodoCard, alert hub
      await page.waitForTimeout(dur);
    },
  },
  {
    id: "03_cliente",
    type: "app",
    vo: "Inserisci il primo cliente. Nome, cognome, contatti. Trenta secondi.",
    padding: 0.8,
    page: "/clienti",
    actions: async (pg, dur) => {
      await pg.waitForTimeout(1000);
      // Click "Nuovo Cliente"
      const btn = pg.locator('button:has-text("Nuovo Cliente"), button:has-text("Nuovo")').first();
      if (await btn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await btn.click();
        await pg.waitForTimeout(800);
      }
      // Typing nel form
      const nome = pg.locator('input[name="nome"], input[placeholder*="Nome"]').first();
      if (await nome.isVisible({ timeout: 2000 }).catch(() => false)) {
        await nome.click();
        await pg.keyboard.type("Giulia", { delay: 80 });
        await pg.waitForTimeout(300);
        const cognome = pg.locator('input[name="cognome"], input[placeholder*="Cognome"]').first();
        await cognome.click();
        await pg.keyboard.type("Martini", { delay: 80 });
        await pg.waitForTimeout(300);
        const email = pg.locator('input[name="email"], input[type="email"]').first();
        if (await email.isVisible().catch(() => false)) {
          await email.click();
          await pg.keyboard.type("giulia.martini@gmail.com", { delay: 50 });
        }
      }
      // Pausa sul form compilato, poi chiudi
      await pg.waitForTimeout(Math.max(0, dur - 4500));
      await pg.keyboard.press("Escape");
      await pg.waitForTimeout(400);
    },
  },
  {
    id: "04_anamnesi",
    type: "app",
    vo: "L'anamnesi è strutturata. Giulia ha un'ernia lombare e instabilità al ginocchio. FitManager lo registra e lo usa dopo.",
    padding: 0.8,
    page: null, // dynamic: /clienti/{id}/anamnesi
    actions: async (pg, dur) => {
      await pg.waitForTimeout(1500);
      // Scroll lento per mostrare condizioni
      await smoothScroll(pg, 400, 1500);
      await pg.waitForTimeout(2000);
      await smoothScroll(pg, 300, 1200);
      await pg.waitForTimeout(Math.max(0, dur - 6200));
    },
  },
  {
    id: "05_contratto",
    type: "app",
    vo: "Crei il contratto. Dieci sedute, tre rate. L'acconto va in cassa da solo.",
    padding: 0.8,
    page: null, // dynamic: /contratti/{id}
    actions: async (pg, dur) => {
      await pg.waitForTimeout(2000);
      // Scroll ai KPI finanziari e rate
      await smoothScroll(pg, 500, 2000);
      await pg.waitForTimeout(Math.max(0, dur - 4000));
    },
  },
  {
    id: "06_cassa",
    type: "app",
    vo: "La cassa si aggiorna da sola. Entrate, uscite, previsioni.",
    padding: 0.8,
    page: "/cassa",
    actions: async (pg, dur) => {
      await pg.waitForTimeout(1500);
      // Scroll al grafico
      await smoothScroll(pg, 300, 1000);
      await pg.waitForTimeout(1000);
      // Click tab Forecast
      const tab = pg.locator('button:has-text("Forecast"), [role="tab"]:has-text("Forecast")').first();
      if (await tab.isVisible({ timeout: 2000 }).catch(() => false)) {
        await tab.click();
        await pg.waitForTimeout(Math.max(0, dur - 5000));
      } else {
        await pg.waitForTimeout(Math.max(0, dur - 3500));
      }
    },
  },
  {
    id: "07_safety",
    type: "app",
    vo: "Crei la scheda. Il Safety Engine legge l'anamnesi e ti avvisa: squat controindicato per l'ernia. Nessun rischio dimenticato.",
    padding: 1.0,
    page: null, // dynamic: /schede/{id}
    actions: async (pg, dur) => {
      await pg.waitForTimeout(2000);
      // Cerca tab Sicurezza o Safety
      for (const name of ["Sicurezza", "Safety", "Analisi"]) {
        const tab = pg.locator(`button:has-text("${name}"), [role="tab"]:has-text("${name}")`).first();
        if (await tab.isVisible({ timeout: 1500 }).catch(() => false)) {
          await tab.click();
          await pg.waitForTimeout(2000);
          break;
        }
      }
      // Scroll per mostrare gli avvisi
      await smoothScroll(pg, 400, 1500);
      await pg.waitForTimeout(Math.max(0, dur - 7000));
    },
  },
  {
    id: "08_esercizi",
    type: "app",
    vo: "Cinquecento esercizi con mappa muscolare e scienza dentro.",
    padding: 0.8,
    page: "/esercizi/1",
    actions: async (pg, dur) => {
      await pg.waitForTimeout(2000);
      // Scroll per mostrare MuscleMap + classification
      await smoothScroll(pg, 350, 1500);
      await pg.waitForTimeout(Math.max(0, dur - 3500));
    },
  },
  {
    id: "09_nutrizione",
    type: "app",
    vo: "Piano alimentare donna under trenta. Millenovecento calorie, standard LARN, sette giorni.",
    padding: 0.8,
    page: null, // dynamic: /nutrizione/{id}
    actions: async (pg, dur) => {
      await pg.waitForTimeout(1500);
      // Scroll per mostrare macro bars + griglia settimanale
      await smoothScroll(pg, 500, 2000);
      await pg.waitForTimeout(Math.max(0, dur - 3500));
    },
  },
  {
    id: "10_cta",
    type: "card",  // title card
    vo: "Dieci minuti. Un cliente completo. Zero carta. Zero Excel. FitManager Studio Plus.",
    padding: 2.0,  // la card resta visibile dopo la voce
  },
];

async function smoothScroll(pg, totalPx, totalMs) {
  const steps = 10;
  const pxPerStep = totalPx / steps;
  const msPerStep = totalMs / steps;
  for (let i = 0; i < steps; i++) {
    await pg.mouse.wheel(0, pxPerStep);
    await pg.waitForTimeout(msPerStep);
  }
}

// ══════════════════════════════════════════════════════════════
// DATI DEMO — creati via API
// ══════════════════════════════════════════════════════════════
const CLIENT_DATA = {
  nome: "Giulia", cognome: "Martini", email: "giulia.martini@gmail.com",
  telefono: "348-5551234", data_nascita: "1998-09-12", sesso: "Donna", stato: "Attivo",
};

const ANAMNESI_DATA = {
  professione: "Impiegata", ore_seduto: "6-8", spostamento: "auto",
  ore_sonno: "7", qualita_sonno: "Buona", livello_stress: 5,
  fumo: "no", alcol: "occasionale", passi_giornalieri: "5000-8000",
  obiettivo_principale: "Tonificazione", obiettivi_secondari: ["postura", "energia"],
  perche_adesso: "Voglio rimettermi in forma dopo un periodo sedentario", impegno: 7,
  si_allena: true, frequenza_settimanale: "2-3", luogo_allenamento: "palestra",
  tipo_preferito: ["pesi", "funzionale"], esperienza_durata: "1-3_anni", esperienza_pt: true,
  dolori_attuali: ["schiena", "ginocchia"],
  infortuni_importanti: { presente: true, dettaglio: "Ernia lombare L4-L5 diagnosticata nel 2023, trattata con fisioterapia" },
  patologie: { presente: true, dettaglio: "Ernia discale lombare, instabilità rotulea ginocchio sinistro" },
  patologie_lista: ["ernie", "articolari"],
  farmaci_risposta: "si", farmaci_dettaglio: "Antinfiammatori al bisogno (ibuprofene)",
  certificato_sportivo: "si",
  limitazioni_mediche: { presente: true, dettaglio: "Evitare carichi assiali pesanti sulla colonna, no squat profondi, no salti" },
  tipo_alimentazione: "onnivora", intolleranze: "lattosio", serenita_cibo: 7,
  preferenza_luogo: "palestra", sedute_settimana: "3", giorni_orari_preferiti: "mattina",
  consenso_privacy: true,
};

const EXERCISES = [
  { id_esercizio: 184, ordine: 1 }, // Squat Bodyweight (cautela per ginocchio)
  { id_esercizio: 141, ordine: 2 }, // Goblet Squat Kettlebell (cautela)
  { id_esercizio: 4, ordine: 3 },   // Pressa Gambe
  { id_esercizio: 85, ordine: 4 },  // Lat Machine
  { id_esercizio: 50, ordine: 5 },  // Chest Press alla Macchina
  { id_esercizio: 117, ordine: 6 }, // Plancia (Plank)
];

// ══════════════════════════════════════════════════════════════
// TITLE CARDS — HTML
// ══════════════════════════════════════════════════════════════
const CARD_STYLE = `
  *{margin:0;padding:0;box-sizing:border-box}
  body{width:1440px;height:900px;background:radial-gradient(ellipse at 30% 50%,#1a3f3f,#0c2626 50%,#071515);
    display:flex;flex-direction:column;align-items:center;justify-content:center;
    font-family:'Inter','Segoe UI',system-ui,sans-serif;position:relative}
  body::before{content:'';position:absolute;inset:0;
    background-image:linear-gradient(rgba(45,212,191,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(45,212,191,.03) 1px,transparent 1px);
    background-size:60px 60px}
  .logo{display:flex;align-items:center;gap:20px;position:relative;z-index:1;margin-bottom:32px}
  .icon{width:72px;height:72px;background:linear-gradient(135deg,#2dd4bf,#0d9488);border-radius:18px;
    display:flex;align-items:center;justify-content:center;font-size:36px;color:#fff;font-weight:800;
    box-shadow:0 0 60px rgba(45,212,191,.25)}
  .title{color:#f0fdfa;font-size:48px;font-weight:800;letter-spacing:-1.5px}
  .title span{color:#2dd4bf}
  .main{color:#f0fdfa;font-size:34px;font-weight:600;position:relative;z-index:1;text-align:center;max-width:800px;line-height:1.4}
  .sub{color:rgba(240,253,250,.45);font-size:16px;font-weight:500;letter-spacing:2px;text-transform:uppercase;
    margin-top:24px;position:relative;z-index:1}
  .pills{display:flex;gap:40px;margin-top:32px;position:relative;z-index:1}
  .pill{display:flex;align-items:center;gap:8px;color:rgba(240,253,250,.5);font-size:13px;font-weight:500;
    text-transform:uppercase;letter-spacing:1.5px}
  .dot{width:6px;height:6px;background:#2dd4bf;border-radius:50%;box-shadow:0 0 8px rgba(45,212,191,.4)}
`;

const INTRO_HTML = `<!DOCTYPE html><html><head><style>${CARD_STYLE}</style></head><body>
  <div class="logo"><div class="icon">FM</div><div class="title">FitManager <span>Studio+</span></div></div>
  <div class="main">I primi 10 minuti</div>
  <div class="sub">Da zero a cliente completo</div>
</body></html>`;

const OUTRO_HTML = `<!DOCTYPE html><html><head><style>${CARD_STYLE}
  .cta{border:1px solid rgba(45,212,191,.2);border-radius:20px;padding:36px 60px;text-align:center;
    background:rgba(13,148,136,.06);position:relative;z-index:1}
  .cta-main{color:#f0fdfa;font-size:28px;font-weight:600;margin-bottom:16px}
  .cta-url{color:#2dd4bf;font-size:32px;font-weight:800}
</style></head><body>
  <div class="logo"><div class="icon">FM</div><div class="title">FitManager <span>Studio+</span></div></div>
  <div class="cta">
    <div class="cta-main">Diventa un PT Evoluto</div>
    <div class="cta-url">fitmanager.studio</div>
  </div>
  <div class="pills">
    <div class="pill"><span class="dot"></span> Dati locali, zero cloud</div>
    <div class="pill"><span class="dot"></span> Licenza perpetua</div>
    <div class="pill"><span class="dot"></span> Garanzia 30 giorni</div>
  </div>
</body></html>`;

// ══════════════════════════════════════════════════════════════
// MAIN
// ══════════════════════════════════════════════════════════════
async function main() {
  const t0 = Date.now();

  // Directories
  for (const d of ["scenes", "clips", "cards", "music"]) ensureDir(path.join(OUT, d));

  // ┌──────────────────────────────────────────────┐
  // │  FASE 2A — VOICEOVER PER SCENA               │
  // └──────────────────────────────────────────────┘
  console.log("\n╔══════════════════════════════════════════╗");
  console.log("║  FASE 2 — GENERAZIONE AUDIO              ║");
  console.log("╚══════════════════════════════════════════╝\n");

  for (const scene of SCENES) {
    const f = path.join(OUT, "scenes", `${scene.id}.mp3`);
    const escaped = scene.vo.replace(/'/g, "\u2019").replace(/"/g, '\\"');
    run(`"${TTS}" --voice "${VOICE}" --rate="${RATE}" --text "${escaped}" --write-media "${f}"`);
    scene.voDur = dur(f);
    scene.totalDur = scene.voDur + scene.padding;
    console.log(`   ✓ ${scene.id}: VO=${scene.voDur.toFixed(1)}s + pad=${scene.padding}s → ${scene.totalDur.toFixed(1)}s`);
  }

  // Concatena VO completo (per riferimento e per il mix finale)
  const concatTxt = path.join(OUT, "scenes", "concat.txt");
  fs.writeFileSync(concatTxt, SCENES.map(s =>
    `file '${path.join(OUT, "scenes", s.id + ".mp3").replace(/\\/g, "/")}'`
  ).join("\n"));
  const fullVO = path.join(OUT, "voiceover.mp3");
  run(`"${FF}" -y -f concat -safe 0 -i "${concatTxt}" -c copy "${fullVO}"`);

  const totalVODur = dur(fullVO);
  const totalWithPad = SCENES.reduce((s, sc) => s + sc.totalDur, 0);
  console.log(`\n   Totale VO puro: ${totalVODur.toFixed(1)}s`);
  console.log(`   Totale con padding: ${totalWithPad.toFixed(1)}s`);

  // ┌──────────────────────────────────────────────┐
  // │  FASE 2B — MUSICA                             │
  // └──────────────────────────────────────────────┘
  console.log("\n   🎵 Musica generativa...\n");

  const MDUR = Math.ceil(totalWithPad) + 6;
  const beat = 60 / 115;
  const mDir = path.join(OUT, "music");

  // Pad (accordo Am: A2 + C4 + E4 + A4)
  run(`"${FF}" -y -f lavfi -i "aevalsrc='(0.3*sin(2*PI*220*t)+0.25*sin(2*PI*261.6*t)+0.2*sin(2*PI*329.6*t)+0.08*sin(2*PI*440*t))*(0.15+0.35*sin(PI*t/${MDUR}))':s=44100:d=${MDUR}" -af "lowpass=f=3000,highpass=f=80,afade=t=in:st=0:d=4,afade=t=out:st=${MDUR - 4}:d=4" "${mDir}/pad.wav"`);
  // Bass
  run(`"${FF}" -y -f lavfi -i "aevalsrc='0.4*sin(2*PI*55*t)*(0.5+0.5*sin(2*PI*${(1 / beat).toFixed(4)}*t))*min(1,(max(0,t-6)/3))':s=44100:d=${MDUR}" -af "lowpass=f=120,volume=0.4,afade=t=out:st=${MDUR - 3}:d=3" "${mDir}/bass.wav"`);
  // Kick
  run(`"${FF}" -y -f lavfi -i "aevalsrc='0.7*sin(2*PI*(180-160*(t/${beat.toFixed(6)}))*t)*exp(-10*t)':s=44100:d=${beat}" -af "aloop=loop=${Math.ceil(MDUR / beat)}:size=${Math.floor(beat * 44100)},atrim=0:${MDUR},lowpass=f=180,volume='if(lt(t,8),0,min(1,(t-8)/3))':eval=frame,volume=0.45,afade=t=out:st=${MDUR - 3}:d=3" "${mDir}/kick.wav"`);
  // Hihat
  const hh = beat / 2;
  run(`"${FF}" -y -f lavfi -i "anoisesrc=d=${hh}:c=white:a=0.15" -af "highpass=f=9000,lowpass=f=15000,volume='exp(-20*mod(t,${hh.toFixed(6)}))':eval=frame,aloop=loop=${Math.ceil(MDUR / hh)}:size=${Math.floor(hh * 44100)},atrim=0:${MDUR},volume='if(lt(t,10),0,min(1,(t-10)/3))':eval=frame,volume=0.1,afade=t=out:st=${MDUR - 3}:d=3" "${mDir}/hihat.wav"`);
  // Shimmer (ultimi 18s)
  const shimmerStart = MDUR - 18;
  run(`"${FF}" -y -f lavfi -i "aevalsrc='0.06*sin(2*PI*880*t)*sin(2*PI*0.3*t)+0.04*sin(2*PI*1320*t)*sin(2*PI*0.2*t)':s=44100:d=${MDUR}" -af "volume='if(lt(t,${shimmerStart}),0,min(1,(t-${shimmerStart})/3))':eval=frame,highpass=f=600,lowpass=f=6000,afade=t=out:st=${MDUR - 4}:d=4" "${mDir}/shimmer.wav"`);

  // Mix 5 layer
  const bgMusic = path.join(OUT, "music.wav");
  run(`"${FF}" -y -i "${mDir}/pad.wav" -i "${mDir}/bass.wav" -i "${mDir}/kick.wav" -i "${mDir}/hihat.wav" -i "${mDir}/shimmer.wav" -filter_complex "[0:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[p];[1:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[b];[2:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[k];[3:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[h];[4:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[s];[p][b][k][h][s]amix=inputs=5:duration=first:normalize=0,alimiter=limit=0.9,equalizer=f=120:t=q:w=1.5:g=2,equalizer=f=2500:t=q:w=1:g=2" -c:a pcm_f32le "${bgMusic}"`);
  console.log(`   ✓ Musica: ${dur(bgMusic).toFixed(1)}s`);

  // ┌──────────────────────────────────────────────┐
  // │  FASE 2C — TITLE CARDS                        │
  // └──────────────────────────────────────────────┘
  console.log("\n   🎨 Title cards...\n");

  const brCards = await chromium.launch({ headless: true });
  const cxCards = await brCards.newContext({ viewport: VP, deviceScaleFactor: 2 });
  const pgCards = await cxCards.newPage();

  for (const [name, html] of [["intro", INTRO_HTML], ["outro", OUTRO_HTML]]) {
    const htmlFile = path.join(OUT, "cards", `${name}.html`);
    fs.writeFileSync(htmlFile, html);
    await pgCards.goto(`file:///${htmlFile.replace(/\\/g, "/")}`);
    await pgCards.waitForTimeout(300);
    await pgCards.screenshot({ path: path.join(OUT, "cards", `${name}.png`) });
  }
  await brCards.close();

  // Intro card video = durata scena 01
  const introScene = SCENES.find(s => s.id === "01_hook");
  const introDur = introScene.totalDur;
  run(`"${FF}" -y -loop 1 -i "${OUT}/cards/intro.png" -t ${introDur.toFixed(1)} -vf "scale=1440:900,format=yuv420p,fps=30,fade=t=in:st=0:d=1,fade=t=out:st=${(introDur - 0.6).toFixed(1)}:d=0.6" -c:v libx264 -preset medium -crf 18 "${OUT}/clips/01_hook.mp4"`);

  // Outro card video = durata scena 10
  const ctaScene = SCENES.find(s => s.id === "10_cta");
  const outroDur = ctaScene.totalDur;
  run(`"${FF}" -y -loop 1 -i "${OUT}/cards/outro.png" -t ${outroDur.toFixed(1)} -vf "scale=1440:900,format=yuv420p,fps=30,fade=t=in:st=0:d=0.6,fade=t=out:st=${(outroDur - 1).toFixed(1)}:d=1" -c:v libx264 -preset medium -crf 18 "${OUT}/clips/10_cta.mp4"`);

  console.log(`   ✓ Intro card: ${introDur.toFixed(1)}s`);
  console.log(`   ✓ Outro card: ${outroDur.toFixed(1)}s`);

  // ┌──────────────────────────────────────────────┐
  // │  PRE-PRODUZIONE — DATI VIA API                │
  // └──────────────────────────────────────────────┘
  console.log("\n╔══════════════════════════════════════════╗");
  console.log("║  PRE-PROD — CREAZIONE DATI VIA API       ║");
  console.log("╚══════════════════════════════════════════╝\n");

  // Login
  const loginRes = await fetch(`${API}/api/auth/login`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(CREDS),
  });
  const ld = await loginRes.json();
  const AUTH = { Authorization: `Bearer ${ld.access_token}`, "Content-Type": "application/json" };
  console.log(`   🔑 ${ld.nome} ${ld.cognome} (trainer_id=${ld.trainer_id})`);

  // Cliente
  let clientRes = await fetch(`${API}/api/clients`, { method: "POST", headers: AUTH, body: JSON.stringify(CLIENT_DATA) });
  let client = await clientRes.json();
  if (client.detail) {
    const listRes = await fetch(`${API}/api/clients?search=Martini`, { headers: AUTH });
    const list = await listRes.json();
    client = list.items?.[0];
    if (!client) { console.error("FATAL: no client"); process.exit(1); }
    console.log(`   ♻ Cliente esistente: id=${client.id}`);
  } else {
    console.log(`   ✓ Cliente: ${client.nome} ${client.cognome} (id=${client.id})`);
  }

  // Anamnesi
  await fetch(`${API}/api/clients/${client.id}`, {
    method: "PUT", headers: AUTH, body: JSON.stringify({ anamnesi: ANAMNESI_DATA }),
  });
  console.log(`   ✓ Anamnesi aggiornata`);

  // Contratto
  const today = new Date().toISOString().split("T")[0];
  const scadenza = new Date(Date.now() + 90 * 86400000).toISOString().split("T")[0];
  const ctRes = await fetch(`${API}/api/contracts`, {
    method: "POST", headers: AUTH,
    body: JSON.stringify({
      id_cliente: client.id, tipo_pacchetto: "PT Personal 10 sedute",
      crediti_totali: 10, prezzo_totale: 450, data_inizio: today,
      data_scadenza: scadenza, acconto: 150, metodo_acconto: "POS",
    }),
  });
  const contract = await ctRes.json();
  console.log(`   ✓ Contratto: id=${contract.id} €${contract.prezzo_totale}`);

  // Rate
  await fetch(`${API}/api/rates/generate-plan/${contract.id}`, {
    method: "POST", headers: AUTH,
    body: JSON.stringify({
      importo_da_rateizzare: 300, numero_rate: 3,
      data_prima_rata: new Date(Date.now() + 30 * 86400000).toISOString().split("T")[0],
      frequenza: "MENSILE",
    }),
  });
  console.log(`   ✓ Rate generate`);

  // Scheda
  const wkRes = await fetch(`${API}/api/workouts`, {
    method: "POST", headers: AUTH,
    body: JSON.stringify({
      nome: "Tonificazione Full Body — Giulia", id_cliente: client.id,
      obiettivo: "dimagrimento", livello: "intermedio",
      sessioni: [{ nome_sessione: "Full Body A", esercizi: EXERCISES }],
    }),
  });
  const wkData = await wkRes.json();
  if (!wkRes.ok) {
    console.error("   ✗ Workout creation failed:", JSON.stringify(wkData));
    // Fallback: cerca ultima scheda del cliente
    const wkList = await fetch(`${API}/api/workouts?id_cliente=${client.id}`, { headers: AUTH });
    const wkListData = await wkList.json();
    var workout = wkListData.items?.[0];
    if (!workout) { console.error("FATAL: no workout"); process.exit(1); }
    console.log(`   ♻ Scheda esistente: id=${workout.id}`);
  } else {
    var workout = wkData;
    console.log(`   ✓ Scheda: id=${workout.id}`);
  }

  // Nutrizione
  const nuRes = await fetch(`${API}/api/nutrition/plans/from-template`, {
    method: "POST", headers: AUTH,
    body: JSON.stringify({ template_id: 6, id_cliente: client.id, nome: "Piano LARN — Giulia Martini" }),
  });
  const nuData = await nuRes.json();
  if (!nuRes.ok) {
    console.error("   ✗ Nutrition creation failed:", JSON.stringify(nuData));
    const nuList = await fetch(`${API}/api/nutrition/plans?id_cliente=${client.id}`, { headers: AUTH });
    const nuListData = await nuList.json();
    var nutriPlan = nuListData.items?.[0] || nuListData[0];
    if (!nutriPlan) { console.error("FATAL: no nutrition plan"); process.exit(1); }
    console.log(`   ♻ Piano esistente: id=${nutriPlan.id}`);
  } else {
    var nutriPlan = nuData;
    console.log(`   ✓ Nutrizione: id=${nutriPlan.id}`);
  }

  // Imposta le pagine dinamiche nello SCENES
  SCENES.find(s => s.id === "04_anamnesi").page = `/clienti/${client.id}/anamnesi`;
  SCENES.find(s => s.id === "05_contratto").page = `/contratti/${contract.id}`;
  SCENES.find(s => s.id === "07_safety").page = `/schede/${workout.id}`;
  SCENES.find(s => s.id === "09_nutrizione").page = `/nutrizione/${nutriPlan.id}`;

  // ┌──────────────────────────────────────────────┐
  // │  FASE 3 — REGISTRAZIONE UI SCENA PER SCENA   │
  // └──────────────────────────────────────────────┘
  console.log("\n╔══════════════════════════════════════════╗");
  console.log("║  FASE 3 — REGISTRAZIONE UI               ║");
  console.log("╚══════════════════════════════════════════╝\n");

  const LOAD_BUFFER = 1.5;  // secondi extra per caricamento pagina
  const XFADE_DUR = 0.4;    // durata crossfade tra scene (secondi)

  const appScenes = SCENES.filter(s => s.type === "app");

  for (const scene of appScenes) {
    const recordDur = scene.totalDur + LOAD_BUFFER;
    console.log(`   📹 ${scene.id} (record: ${recordDur.toFixed(1)}s → trim: ${scene.totalDur.toFixed(1)}s) — ${scene.page}`);

    const br = await chromium.launch({ headless: false, slowMo: 20 });
    const cx = await br.newContext({
      viewport: VP, deviceScaleFactor: 2,
      recordVideo: { dir: path.join(OUT, "clips", "_raw_" + scene.id), size: VP },
      locale: "it-IT", timezoneId: "Europe/Rome",
    });
    await cx.addCookies([
      { name: "fitmanager_token", value: ld.access_token, domain: "localhost", path: "/" },
      { name: "fitmanager_trainer", value: JSON.stringify({ id: ld.trainer_id, nome: ld.nome, cognome: ld.cognome }), domain: "localhost", path: "/" },
    ]);

    const pg = await cx.newPage();
    await pg.goto(`${BASE}${scene.page}`, { waitUntil: "networkidle", timeout: 15000 });
    // Attesa lunga: la pagina deve essere COMPLETAMENTE renderizzata
    await pg.waitForTimeout(1500);

    // Esegui le azioni della scena
    const durMs = scene.totalDur * 1000;
    await scene.actions(pg, durMs);

    await pg.close();
    const videoPath = await pg.video().path();
    await cx.close();
    await br.close();

    // Trim: salta il primo LOAD_BUFFER (frame di caricamento), prendi totalDur secondi
    const clipOut = path.join(OUT, "clips", `${scene.id}.mp4`);
    run(`"${FF}" -y -ss ${LOAD_BUFFER.toFixed(1)} -i "${videoPath}" -t ${scene.totalDur.toFixed(1)} -vf "scale=1440:900,fps=30,format=yuv420p" -c:v libx264 -preset medium -crf 20 -an "${clipOut}"`);

    const realDur = dur(clipOut);
    console.log(`      ✓ clip: ${realDur.toFixed(1)}s (target: ${scene.totalDur.toFixed(1)}s)\n`);
  }

  // ┌──────────────────────────────────────────────┐
  // │  FASE 4 — MONTAGGIO FINALE                    │
  // └──────────────────────────────────────────────┘
  console.log("\n╔══════════════════════════════════════════╗");
  console.log("║  FASE 4 — MONTAGGIO                      ║");
  console.log("╚══════════════════════════════════════════╝\n");

  // 4a. Crossfade tra clip con xfade (no concat secco)
  const clipFiles = SCENES.map(s => path.join(OUT, "clips", `${s.id}.mp4`).replace(/\\/g, "/"));
  const N = clipFiles.length;

  // Costruisci filtro xfade a catena: [0][1]xfade→[v01]; [v01][2]xfade→[v012]; ...
  const xfadeInputs = clipFiles.map((f, i) => `-i "${f}"`).join(" ");
  const xfadeParts = [];
  let offset = SCENES[0].totalDur - XFADE_DUR;

  for (let i = 1; i < N; i++) {
    const inL = i === 1 ? "[0:v]" : `[xf${i - 1}]`;
    const inR = `[${i}:v]`;
    const outLabel = i === N - 1 ? "[xfraw]" : `[xf${i}]`;
    xfadeParts.push(`${inL}${inR}xfade=transition=fade:duration=${XFADE_DUR}:offset=${offset.toFixed(2)}${outLabel}`);
    offset += SCENES[i].totalDur - XFADE_DUR;
  }

  // Forza yuv420p dopo xfade (xfade produce yuv444p, incompatibile con Windows Media Player)
  xfadeParts.push(`[xfraw]format=yuv420p[vout]`);

  const silentVideo = path.join(OUT, "silent.mp4");
  run(`"${FF}" -y ${xfadeInputs} -filter_complex "${xfadeParts.join(";")}" -map "[vout]" -c:v libx264 -preset medium -crf 20 -movflags +faststart "${silentVideo}"`);
  const vidDur = dur(silentVideo);
  console.log(`   ✓ Video crossfaded: ${vidDur.toFixed(1)}s (${N} scene, xfade=${XFADE_DUR}s)`);

  // 4b. Voiceover con padding — compensato per xfade
  // Ogni crossfade accorcia il video di XFADE_DUR, quindi le scene successive
  // iniziano prima. Calcoliamo offset reali post-xfade.
  const voGapped = path.join(OUT, "voiceover-gapped.mp3");
  const voInputs = [];
  const voFilterParts = [];

  for (let i = 0; i < SCENES.length; i++) {
    const voFile = path.join(OUT, "scenes", `${SCENES[i].id}.mp3`);
    voInputs.push(`-i "${voFile}"`);
    voFilterParts.push(`[${i}:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[v${i}]`);
  }

  // Offset reale di ogni scena nel video con xfade
  let cumMsAdj = 0;
  const voDelayParts = [];
  for (let i = 0; i < SCENES.length; i++) {
    if (cumMsAdj > 0) {
      voDelayParts.push(`[v${i}]adelay=${Math.round(cumMsAdj)}|${Math.round(cumMsAdj)}[d${i}]`);
    } else {
      voDelayParts.push(`[v${i}]acopy[d${i}]`);
    }
    // Prossima scena inizia dopo totalDur meno la crossfade con la scena successiva
    cumMsAdj += (SCENES[i].totalDur - (i < SCENES.length - 1 ? XFADE_DUR : 0)) * 1000;
  }

  const voMixLabels = SCENES.map((_, i) => `[d${i}]`).join("");
  const voFullFilter = [
    ...voFilterParts,
    ...voDelayParts,
    `${voMixLabels}amix=inputs=${SCENES.length}:duration=longest:normalize=0[out]`,
  ].join(";");

  run(`"${FF}" -y ${voInputs.join(" ")} -filter_complex "${voFullFilter}" -map "[out]" -c:a libmp3lame -b:a 192k "${voGapped}"`);
  const voGapDur = dur(voGapped);
  console.log(`   ✓ VO gapped: ${voGapDur.toFixed(1)}s (compensato xfade)`);

  // 4c. Mix finale: video + VO + musica (sidechain ducking)
  const final = path.join(OUT, "primi-10-minuti.mp4");
  run(
    `"${FF}" -y -i "${silentVideo}" -i "${voGapped}" -i "${bgMusic}" ` +
    `-filter_complex "` +
    `[1:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,volume=1.0[voice];` +
    `[2:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,atrim=0:${vidDur.toFixed(1)},asetpts=PTS-STARTPTS,volume=0.20,afade=t=out:st=${(vidDur - 3).toFixed(1)}:d=3[music];` +
    `[voice][music]sidechaincompress=threshold=0.02:ratio=4:attack=50:release=300[aout]" ` +
    `-map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "${final}"`
  );

  const finalDur = dur(final);
  const finalSize = (fs.statSync(final).size / 1024 / 1024).toFixed(1);

  // ┌──────────────────────────────────────────────┐
  // │  REPORT                                       │
  // └──────────────────────────────────────────────┘
  const elapsed = ((Date.now() - t0) / 1000).toFixed(0);

  console.log(`\n${"═".repeat(56)}`);
  console.log(`  ✅ VIDEO COMPLETATO: primi-10-minuti`);
  console.log(`${"═".repeat(56)}`);
  console.log(`  File:     data/videos/primi-10-minuti/primi-10-minuti.mp4`);
  console.log(`  Durata:   ${finalDur.toFixed(1)}s`);
  console.log(`  Peso:     ${finalSize} MB`);
  console.log(`  Tempo:    ${elapsed}s`);
  console.log(`  Scene:    ${SCENES.length}`);
  console.log();
  console.log("  Timeline (con crossfade):");
  let cum = 0;
  for (let i = 0; i < SCENES.length; i++) {
    const s = SCENES[i];
    const end = cum + s.totalDur;
    console.log(`    ${fmtTime(cum)} — ${fmtTime(end)}  ${s.id} (${s.totalDur.toFixed(1)}s)`);
    cum += s.totalDur - (i < SCENES.length - 1 ? XFADE_DUR : 0);
  }
  console.log(`\n${"═".repeat(56)}`);
}

main().catch(err => { console.error("FATAL:", err); process.exit(1); });

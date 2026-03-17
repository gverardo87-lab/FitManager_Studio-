const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

// ─── PALETTE ────────────────────────────────────────────────
const C = {
  teal:       "0D9488",
  tealDark:   "0F766E",
  mint:       "14B8A6",
  mintLight:  "5EEAD4",
  dark:       "1E293B",
  darkAlt:    "0F172A",
  light:      "F8FAFC",
  lightAlt:   "F1F5F9",
  white:      "FFFFFF",
  slate:      "64748B",
  slateDark:  "475569",
  coral:      "F97066",
  coralBg:    "FEF2F2",
  amber:      "F59E0B",
  amberBg:    "FFFBEB",
  green:      "10B981",
  greenBg:    "ECFDF5",
  blue:       "3B82F6",
  blueBg:     "EFF6FF",
  purple:     "8B5CF6",
  purpleBg:   "F5F3FF",
};

const FONT_H = "Georgia";
const FONT_B = "Calibri";

const SCREENSHOTS = "C:/Users/gvera/Projects/FitManager_AI_Studio/data/screenshots";
const OUT_DIR = "C:/Users/gvera/Projects/FitManager_AI_Studio/data";

// ─── HELPERS ────────────────────────────────────────────────
const makeShadow = () => ({ type: "outer", color: "000000", blur: 8, offset: 3, angle: 135, opacity: 0.12 });
const makeCardShadow = () => ({ type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.10 });

function addSlideNumber(slide, num, total) {
  slide.addText(`${num} / ${total}`, {
    x: 8.8, y: 5.25, w: 1, h: 0.3,
    fontSize: 9, fontFace: FONT_B, color: C.slate, align: "right",
  });
}

function addCard(slide, x, y, w, h, fillColor) {
  slide.addShape("rect", {
    x, y, w, h,
    fill: { color: fillColor || C.white },
    shadow: makeCardShadow(),
  });
}

function addAccentBar(slide, x, y, h, color) {
  slide.addShape("rect", {
    x, y, w: 0.06, h,
    fill: { color: color || C.teal },
  });
}

// ─── PRESENTATION ───────────────────────────────────────────
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "FitManager Studio+";
pres.title = "FitManager Studio+ — Pitch Deck";

const TOTAL = 26;

// ═══════════════════════════════════════════════════════════
// SLIDE 1: COVER
// ═══════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.dark };

  // Accent gradient bar top
  s.addShape("rect", { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.teal } });

  // Title block
  s.addText("FitManager Studio+", {
    x: 0.8, y: 1.2, w: 8.4, h: 1.2,
    fontSize: 48, fontFace: FONT_H, color: C.white, bold: true,
  });

  s.addText("Il CRM scientifico per professionisti fitness", {
    x: 0.8, y: 2.4, w: 8.4, h: 0.6,
    fontSize: 22, fontFace: FONT_B, color: C.mintLight,
  });

  s.addText("Privacy-first. Offline. Deterministico.", {
    x: 0.8, y: 3.1, w: 8.4, h: 0.5,
    fontSize: 16, fontFace: FONT_B, color: C.slate, italic: true,
  });

  // Bottom bar with key facts
  s.addShape("rect", { x: 0, y: 4.6, w: 10, h: 1.025, fill: { color: C.darkAlt } });

  const facts = [
    { num: "391+", label: "Esercizi" },
    { num: "47", label: "Condizioni\nMediche" },
    { num: "226", label: "Alimenti\nCREA" },
    { num: "18", label: "Fonti\nScientifiche" },
  ];
  facts.forEach((f, i) => {
    const fx = 0.8 + i * 2.3;
    s.addText(f.num, { x: fx, y: 4.7, w: 1.8, h: 0.45, fontSize: 28, fontFace: FONT_H, color: C.mint, bold: true });
    s.addText(f.label, { x: fx, y: 5.1, w: 1.8, h: 0.4, fontSize: 11, fontFace: FONT_B, color: C.slate });
  });

  addSlideNumber(s, 1, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// SLIDE 2: IL PROBLEMA
// ═══════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("Il Problema", {
    x: 0.8, y: 0.4, w: 8.4, h: 0.7,
    fontSize: 36, fontFace: FONT_H, color: C.dark, bold: true,
  });

  s.addText("Il professionista fitness oggi lavora con strumenti frammentati, costosi e insicuri.", {
    x: 0.8, y: 1.0, w: 8.4, h: 0.5,
    fontSize: 15, fontFace: FONT_B, color: C.slateDark,
  });

  const problems = [
    { icon: "X", title: "5-7 strumenti separati", desc: "WhatsApp, Excel, app note, agenda cartacea, calcolatrice, Google Drive..." },
    { icon: "X", title: "Dati su cloud stranieri", desc: "I dati clinici dei tuoi clienti su server USA/UK. GDPR? Speriamo." },
    { icon: "X", title: "Tutto in inglese", desc: "Interfacce pensate per il mercato USA, tradotte male o mai." },
    { icon: "X", title: "SaaS da 15-130 EUR/mese", desc: "Trainerize EUR 58/mese, Virtuagym EUR 65/mese, PT Distinction EUR 45/mese." },
    { icon: "X", title: "Zero scienza", desc: "Nessun competitor ha EMG matrix, volume model, o safety engine." },
    { icon: "X", title: "Nessuna privacy reale", desc: "Dati anamnesi, patologie, farmaci: tutto in cloud senza garanzie." },
  ];

  problems.forEach((p, i) => {
    const row = Math.floor(i / 2);
    const col = i % 2;
    const px = 0.8 + col * 4.4;
    const py = 1.7 + row * 1.2;

    addCard(s, px, py, 4.0, 1.0, C.coralBg);
    s.addShape("rect", { x: px, y: py, w: 0.06, h: 1.0, fill: { color: C.coral } });

    s.addText(p.title, {
      x: px + 0.2, y: py + 0.08, w: 3.6, h: 0.4,
      fontSize: 14, fontFace: FONT_B, color: C.dark, bold: true, margin: 0,
    });
    s.addText(p.desc, {
      x: px + 0.2, y: py + 0.48, w: 3.6, h: 0.45,
      fontSize: 11, fontFace: FONT_B, color: C.slateDark, margin: 0,
    });
  });

  addSlideNumber(s, 2, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// SLIDE 3: IL MERCATO
// ═══════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("Il Mercato Italiano", {
    x: 0.8, y: 0.4, w: 8.4, h: 0.7,
    fontSize: 36, fontFace: FONT_H, color: C.dark, bold: true,
  });

  s.addText("Una nicchia enorme e completamente scoperta.", {
    x: 0.8, y: 1.0, w: 8.4, h: 0.5,
    fontSize: 15, fontFace: FONT_B, color: C.slateDark,
  });

  // Big stats
  const stats = [
    { num: "30-50K", label: "Personal Trainer\ncon P.IVA in Italia", color: C.teal, bg: C.white },
    { num: "7.500+", label: "Centri Fitness\ne Palestre", color: C.tealDark, bg: C.white },
    { num: "EUR 3.1B", label: "Revenue Settore\nFitness Italia", color: C.dark, bg: C.white },
  ];

  stats.forEach((st, i) => {
    const sx = 0.8 + i * 3.0;
    addCard(s, sx, 1.7, 2.6, 1.8, st.bg);
    s.addText(st.num, {
      x: sx + 0.2, y: 1.9, w: 2.2, h: 0.7,
      fontSize: 36, fontFace: FONT_H, color: st.color, bold: true,
    });
    s.addText(st.label, {
      x: sx + 0.2, y: 2.7, w: 2.2, h: 0.6,
      fontSize: 13, fontFace: FONT_B, color: C.slateDark,
    });
  });

  // Key insight box
  addCard(s, 0.8, 3.8, 8.4, 1.4, C.white);
  addAccentBar(s, 0.8, 3.8, 1.4, C.teal);

  s.addText("La nicchia vuota", {
    x: 1.1, y: 3.9, w: 7.8, h: 0.4,
    fontSize: 18, fontFace: FONT_H, color: C.dark, bold: true,
  });
  s.addText([
    { text: "Nessun CRM in Italia", options: { bold: true } },
    { text: " combina gestione clienti + programmazione scientifica + privacy locale.\n" },
    { text: "I competitor globali (Trainerize, MyPTHub, TrueCoach) sono cloud-only, in inglese, senza motori scientifici.\n" },
    { text: "EvolutionFit (unico italiano) ha plicometria base ma zero biomeccanica, EMG, o safety engine." },
  ], {
    x: 1.1, y: 4.3, w: 7.8, h: 0.8,
    fontSize: 12, fontFace: FONT_B, color: C.slateDark,
    paraSpaceAfter: 4,
  });

  addSlideNumber(s, 3, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// SLIDE 4: LA SOLUZIONE
// ═══════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.dark };
  s.addShape("rect", { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.teal } });

  s.addText("La Soluzione", {
    x: 0.8, y: 0.5, w: 8.4, h: 0.7,
    fontSize: 36, fontFace: FONT_H, color: C.white, bold: true,
  });

  s.addText("Un CRM all-in-one pensato per chi lavora con il corpo delle persone.", {
    x: 0.8, y: 1.1, w: 8.4, h: 0.5,
    fontSize: 16, fontFace: FONT_B, color: C.mintLight, italic: true,
  });

  const pillars = [
    { title: "CRM Completo", desc: "Clienti, contratti, agenda, pagamenti, monitoraggio. Tutto in un posto.", color: C.teal },
    { title: "Scienza Integrata", desc: "EMG matrix, volume model, safety engine, periodizzazione evidence-based.", color: C.mint },
    { title: "Privacy Assoluta", desc: "Zero cloud. I dati restano sul tuo PC. Crittografia RSA 2048.", color: C.green },
    { title: "Italiano Nativo", desc: "UI, terminologia, e logica pensate per il professionista italiano P.IVA.", color: C.blue },
  ];

  pillars.forEach((p, i) => {
    const py = 1.9 + i * 0.85;
    s.addShape("rect", { x: 0.8, y: py, w: 8.4, h: 0.7, fill: { color: C.darkAlt } });
    s.addShape("rect", { x: 0.8, y: py, w: 0.06, h: 0.7, fill: { color: p.color } });
    s.addText(p.title, {
      x: 1.1, y: py + 0.05, w: 2.8, h: 0.3,
      fontSize: 16, fontFace: FONT_B, color: C.white, bold: true, margin: 0,
    });
    s.addText(p.desc, {
      x: 1.1, y: py + 0.35, w: 7.8, h: 0.3,
      fontSize: 12, fontFace: FONT_B, color: C.slate, margin: 0,
    });
  });

  addSlideNumber(s, 4, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// SLIDE 5: PRIVACY-FIRST
// ═══════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("Privacy-First: I Tuoi Dati sul Tuo PC", {
    x: 0.8, y: 0.4, w: 8.4, h: 0.7,
    fontSize: 32, fontFace: FONT_H, color: C.dark, bold: true,
  });

  const features = [
    { title: "Zero Cloud Obbligatorio", desc: "SQLite locale. Nessun dato lascia il tuo computer. Mai." },
    { title: "Crittografia RSA 2048", desc: "Licenza firmata con chiave asimmetrica. Nessun phone-home." },
    { title: "Backup Atomico", desc: "sqlite3.backup() + SHA-256 checksum + integrity check. Ripristino 1-click." },
    { title: "GDPR Nativo", desc: "Dati clinici, anamnesi, patologie, farmaci: tutto locale, zero rischio." },
    { title: "Condivisione Controllata", desc: "Tailscale VPN per accesso LAN sicuro. Funnel HTTPS per link pubblici temporanei." },
    { title: "Sopravvive agli Aggiornamenti", desc: "Cartella data/ separata dal software. Aggiorna senza perdere nulla." },
  ];

  features.forEach((f, i) => {
    const row = Math.floor(i / 2);
    const col = i % 2;
    const fx = 0.8 + col * 4.4;
    const fy = 1.3 + row * 1.3;

    addCard(s, fx, fy, 4.0, 1.1, C.white);
    addAccentBar(s, fx, fy, 1.1, C.green);

    s.addText(f.title, {
      x: fx + 0.2, y: fy + 0.1, w: 3.6, h: 0.35,
      fontSize: 14, fontFace: FONT_B, color: C.dark, bold: true, margin: 0,
    });
    s.addText(f.desc, {
      x: fx + 0.2, y: fy + 0.5, w: 3.6, h: 0.5,
      fontSize: 11, fontFace: FONT_B, color: C.slateDark, margin: 0,
    });
  });

  addSlideNumber(s, 5, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// SLIDES 6-8: CICLO DI LAVORO (3 slides)
// ═══════════════════════════════════════════════════════════

// Slide 6: Onboarding
(() => {
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("Ciclo di Lavoro — Fase 1: Onboarding", {
    x: 0.8, y: 0.4, w: 8.4, h: 0.7,
    fontSize: 30, fontFace: FONT_H, color: C.dark, bold: true,
  });

  const steps = [
    { num: "01", title: "Nuovo Cliente", desc: "Crei il profilo in 30 secondi. Nome, contatti, obiettivo.", color: C.teal },
    { num: "02", title: "Anamnesi Scientifica", desc: "Questionario 6-step: vita, obiettivi, sport, salute, alimentazione, logistica. Anche self-service via link smartphone.", color: C.mint },
    { num: "03", title: "Safety Profile", desc: "80 regole estraggono automaticamente condizioni mediche. Risk Body Map con zone a rischio.", color: C.coral },
    { num: "04", title: "Contratto", desc: "Pacchetto, crediti, prezzo, piano rate. 12 livelli di protezione finanziaria.", color: C.blue },
  ];

  steps.forEach((st, i) => {
    const sy = 1.3 + i * 1.0;
    addCard(s, 0.8, sy, 8.4, 0.85, C.white);
    s.addShape("rect", { x: 0.8, y: sy, w: 0.8, h: 0.85, fill: { color: st.color } });
    s.addText(st.num, {
      x: 0.8, y: sy, w: 0.8, h: 0.85,
      fontSize: 24, fontFace: FONT_H, color: C.white, bold: true, align: "center", valign: "middle",
    });
    s.addText(st.title, {
      x: 1.8, y: sy + 0.08, w: 7.0, h: 0.3,
      fontSize: 16, fontFace: FONT_B, color: C.dark, bold: true, margin: 0,
    });
    s.addText(st.desc, {
      x: 1.8, y: sy + 0.4, w: 7.0, h: 0.4,
      fontSize: 12, fontFace: FONT_B, color: C.slateDark, margin: 0,
    });
  });

  addSlideNumber(s, 6, TOTAL);
})();

// Slide 7: Operativo
(() => {
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("Ciclo di Lavoro — Fase 2: Operativo", {
    x: 0.8, y: 0.4, w: 8.4, h: 0.7,
    fontSize: 30, fontFace: FONT_H, color: C.dark, bold: true,
  });

  const steps = [
    { num: "05", title: "Agenda & Sessioni", desc: "Calendario drag & drop. Ogni sessione PT consuma 1 credito automaticamente. Alert contratti in scadenza.", color: C.teal },
    { num: "06", title: "Cockpit Oggi", desc: "Pagina operativa: sessioni di oggi, readiness clinica, alert, azioni rapide. Tutto in un colpo d'occhio.", color: C.mint },
    { num: "07", title: "Pagamenti & Cassa", desc: "Pagamento atomico rate, saldo cumulativo, previsioni 3 mesi, spese ricorrenti, libro mastro.", color: C.blue },
    { num: "08", title: "Rinnovi", desc: "Catena rinnovi con storico. Pre-fill automatico. Acconto atomico. Navigazione breadcrumb.", color: C.purple },
  ];

  steps.forEach((st, i) => {
    const sy = 1.3 + i * 1.0;
    addCard(s, 0.8, sy, 8.4, 0.85, C.white);
    s.addShape("rect", { x: 0.8, y: sy, w: 0.8, h: 0.85, fill: { color: st.color } });
    s.addText(st.num, {
      x: 0.8, y: sy, w: 0.8, h: 0.85,
      fontSize: 24, fontFace: FONT_H, color: C.white, bold: true, align: "center", valign: "middle",
    });
    s.addText(st.title, {
      x: 1.8, y: sy + 0.08, w: 7.0, h: 0.3,
      fontSize: 16, fontFace: FONT_B, color: C.dark, bold: true, margin: 0,
    });
    s.addText(st.desc, {
      x: 1.8, y: sy + 0.4, w: 7.0, h: 0.4,
      fontSize: 12, fontFace: FONT_B, color: C.slateDark, margin: 0,
    });
  });

  addSlideNumber(s, 7, TOTAL);
})();

// Slide 8: Scientifico
(() => {
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("Ciclo di Lavoro — Fase 3: Scientifico", {
    x: 0.8, y: 0.4, w: 8.4, h: 0.7,
    fontSize: 30, fontFace: FONT_H, color: C.dark, bold: true,
  });

  const steps = [
    { num: "09", title: "Scheda Allenamento", desc: "Builder 3-tab: sessioni board, analisi 4D scientifica, anteprima PDF. Drag & drop con blocchi strutturati.", color: C.teal },
    { num: "10", title: "Monitoraggio", desc: "Compliance grid, log allenamenti, portale 360 gradi. Avatar cliente a 6 dimensioni con semafori.", color: C.mint },
    { num: "11", title: "Misurazioni & Clinica", desc: "Composizione corporea, BMI, FFMI, WHR. Range normativi OMS/ACSM/AHA. Trend automatici.", color: C.green },
    { num: "12", title: "Nutrizione", desc: "Piano 7 giorni con scoring LARN. 226 alimenti CREA. Rotazione proteica. Validazione 3 assi.", color: C.amber },
  ];

  steps.forEach((st, i) => {
    const sy = 1.3 + i * 1.0;
    addCard(s, 0.8, sy, 8.4, 0.85, C.white);
    s.addShape("rect", { x: 0.8, y: sy, w: 0.8, h: 0.85, fill: { color: st.color } });
    s.addText(st.num, {
      x: 0.8, y: sy, w: 0.8, h: 0.85,
      fontSize: 24, fontFace: FONT_H, color: C.white, bold: true, align: "center", valign: "middle",
    });
    s.addText(st.title, {
      x: 1.8, y: sy + 0.08, w: 7.0, h: 0.3,
      fontSize: 16, fontFace: FONT_B, color: C.dark, bold: true, margin: 0,
    });
    s.addText(st.desc, {
      x: 1.8, y: sy + 0.4, w: 7.0, h: 0.4,
      fontSize: 12, fontFace: FONT_B, color: C.slateDark, margin: 0,
    });
  });

  addSlideNumber(s, 8, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// SLIDE 9: IL TEMPO CHE RISPARMI (NEW)
// ═══════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.dark };
  s.addShape("rect", { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.teal } });

  s.addText("Il Tempo che Risparmi", {
    x: 0.8, y: 0.25, w: 8.4, h: 0.5,
    fontSize: 28, fontFace: FONT_H, color: C.white, bold: true,
  });
  s.addText("Ogni ora risparmiata e un'ora in piu con i tuoi clienti.", {
    x: 0.8, y: 0.75, w: 8.4, h: 0.3,
    fontSize: 13, fontFace: FONT_B, color: C.mintLight, italic: true,
  });

  // Before/After comparison
  const tasks = [
    { task: "Anamnesi cliente", before: "20-30 min", after: "5 min", saving: "Link self-service: il cliente compila da smartphone" },
    { task: "Programmazione scheda", before: "45-60 min", after: "10-15 min", saving: "Plan Builder 4 fasi genera e analizza automaticamente" },
    { task: "Controllo controindicazioni", before: "15-20 min (manuale)", after: "Istantaneo", saving: "Safety Engine incrocia 47 condizioni x 434 esercizi" },
    { task: "Gestione pagamenti e rate", before: "30 min/settimana", after: "5 min", saving: "Pagamento atomico 1-click, scadenze automatiche" },
    { task: "Report e misurazioni", before: "20-30 min", after: "2 min", saving: "Range normativi OMS/ACSM calcolati in tempo reale" },
  ];

  // Header row
  s.addShape("rect", { x: 0.5, y: 1.15, w: 9.0, h: 0.3, fill: { color: C.darkAlt } });
  ["Attivita", "Prima", "Con FitManager", "Come"].forEach((h, i) => {
    const hx = [0.6, 3.0, 4.3, 5.8][i];
    const hw = [2.3, 1.2, 1.4, 3.5][i];
    s.addText(h, { x: hx, y: 1.15, w: hw, h: 0.3, fontSize: 9, fontFace: FONT_B, color: C.mintLight, bold: true, valign: "middle", margin: 0 });
  });

  tasks.forEach((t, i) => {
    const ty = 1.5 + i * 0.52;
    s.addShape("rect", { x: 0.5, y: ty, w: 9.0, h: 0.46, fill: { color: i % 2 === 0 ? C.darkAlt : C.dark } });

    s.addText(t.task, { x: 0.6, y: ty, w: 2.3, h: 0.46, fontSize: 10, fontFace: FONT_B, color: C.white, bold: true, valign: "middle", margin: 0 });
    s.addText(t.before, { x: 3.0, y: ty, w: 1.2, h: 0.46, fontSize: 10, fontFace: FONT_B, color: C.coral, valign: "middle", margin: 0 });
    s.addText(t.after, { x: 4.3, y: ty, w: 1.4, h: 0.46, fontSize: 10, fontFace: FONT_B, color: C.mint, bold: true, valign: "middle", margin: 0 });
    s.addText(t.saving, { x: 5.8, y: ty, w: 3.5, h: 0.46, fontSize: 9, fontFace: FONT_B, color: C.slate, valign: "middle", margin: 0 });
  });

  // Total savings callout
  s.addShape("rect", { x: 0.5, y: 4.2, w: 9.0, h: 0.85, fill: { color: C.darkAlt } });
  s.addShape("rect", { x: 0.5, y: 4.2, w: 0.06, h: 0.85, fill: { color: C.mint } });

  s.addText("~4-6 ore/settimana risparmiate", {
    x: 0.8, y: 4.25, w: 4.5, h: 0.4,
    fontSize: 22, fontFace: FONT_H, color: C.mint, bold: true, margin: 0,
  });
  s.addText("= 200+ ore/anno reinvestite nei tuoi clienti", {
    x: 0.8, y: 4.65, w: 4.5, h: 0.3,
    fontSize: 13, fontFace: FONT_B, color: C.slate, margin: 0,
  });

  s.addText("Tempo liberato\n= piu clienti\n= servizio migliore\n= tariffe piu alte", {
    x: 6.5, y: 4.25, w: 2.8, h: 0.75,
    fontSize: 11, fontFace: FONT_B, color: C.mintLight, bold: true, margin: 0,
  });

  addSlideNumber(s, 9, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// SLIDE 10: DASHBOARD SCREENSHOT (was 9)
// ═══════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.dark };
  s.addShape("rect", { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.teal } });

  s.addText("Il Tuo Cockpit Quotidiano", {
    x: 0.8, y: 0.3, w: 5, h: 0.5,
    fontSize: 24, fontFace: FONT_H, color: C.white, bold: true,
  });
  s.addText("Dashboard con agenda, promemoria, alert operativi, readiness clinica.", {
    x: 0.8, y: 0.75, w: 5, h: 0.35,
    fontSize: 12, fontFace: FONT_B, color: C.slate,
  });

  // Screenshot with shadow
  s.addShape("rect", {
    x: 0.7, y: 1.25, w: 8.6, h: 4.15,
    fill: { color: C.darkAlt },
    shadow: makeShadow(),
  });
  s.addImage({
    path: `${SCREENSHOTS}/01-dashboard.png`,
    x: 0.8, y: 1.3, w: 8.4, h: 4.0,
  });

  addSlideNumber(s, 10, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// SLIDE 10: SAFETY ENGINE
// ═══════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("Safety Engine: Protezione Clinica", {
    x: 0.8, y: 0.4, w: 8.4, h: 0.7,
    fontSize: 32, fontFace: FONT_H, color: C.dark, bold: true,
  });

  s.addText("Il sistema che nessun competitor ha. Ogni esercizio analizzato contro il profilo clinico del cliente.", {
    x: 0.8, y: 1.0, w: 8.4, h: 0.4,
    fontSize: 14, fontFace: FONT_B, color: C.slateDark,
  });

  // Flow diagram
  const flowItems = [
    { label: "Anamnesi\n6 Step", x: 0.8, color: C.teal },
    { label: "80 Pattern\nRules", x: 2.6, color: C.tealDark },
    { label: "47 Condizioni\nMediche", x: 4.4, color: C.blue },
    { label: "Safety Map\nPer Esercizio", x: 6.2, color: C.purple },
    { label: "Risk\nBody Map", x: 8.0, color: C.coral },
  ];

  flowItems.forEach((fi) => {
    s.addShape("rect", {
      x: fi.x, y: 1.6, w: 1.5, h: 0.9,
      fill: { color: fi.color },
    });
    s.addText(fi.label, {
      x: fi.x, y: 1.6, w: 1.5, h: 0.9,
      fontSize: 11, fontFace: FONT_B, color: C.white, bold: true,
      align: "center", valign: "middle",
    });
  });

  // Arrows between flow items
  [2.3, 4.1, 5.9, 7.7].forEach((ax) => {
    s.addText(">", {
      x: ax, y: 1.75, w: 0.3, h: 0.6,
      fontSize: 24, fontFace: FONT_B, color: C.slate, align: "center", valign: "middle",
    });
  });

  // Severity levels
  s.addText("3 Livelli di Severita", {
    x: 0.8, y: 2.8, w: 8.4, h: 0.4,
    fontSize: 18, fontFace: FONT_H, color: C.dark, bold: true,
  });

  const severities = [
    { level: "AVOID", desc: "Esercizio controindicato. Escludere dalla scheda.", color: C.coral, bg: C.coralBg },
    { level: "CAUTION", desc: "Cautela. Possibile con adattamenti specifici.", color: C.amber, bg: C.amberBg },
    { level: "MODIFY", desc: "Adattare ROM, grip o carico. Biomeccanica specifica.", color: C.blue, bg: C.blueBg },
  ];

  severities.forEach((sv, i) => {
    const sx = 0.8 + i * 3.0;
    addCard(s, sx, 3.3, 2.6, 1.0, sv.bg);
    s.addShape("rect", { x: sx, y: 3.3, w: 0.06, h: 1.0, fill: { color: sv.color } });
    s.addText(sv.level, {
      x: sx + 0.2, y: 3.4, w: 2.2, h: 0.3,
      fontSize: 14, fontFace: FONT_B, color: sv.color, bold: true, margin: 0,
    });
    s.addText(sv.desc, {
      x: sx + 0.2, y: 3.75, w: 2.2, h: 0.45,
      fontSize: 11, fontFace: FONT_B, color: C.slateDark, margin: 0,
    });
  });

  // Philosophy box
  addCard(s, 0.8, 4.6, 8.4, 0.7, C.white);
  addAccentBar(s, 0.8, 4.6, 0.7, C.teal);
  s.addText("Filosofia: INFORMARE, MAI LIMITARE. Il trainer decide sempre. Zero blocking, 100% informazione.", {
    x: 1.1, y: 4.7, w: 8.0, h: 0.4,
    fontSize: 13, fontFace: FONT_B, color: C.dark, italic: true, margin: 0,
  });

  addSlideNumber(s, 11, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// SLIDE 11: DATABASE TASSONOMICO
// ═══════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("Database Tassonomico Scientifico", {
    x: 0.8, y: 0.4, w: 8.4, h: 0.7,
    fontSize: 32, fontFace: FONT_H, color: C.dark, bold: true,
  });

  // Stats grid 2x3
  const dbStats = [
    { num: "434", label: "Esercizi Attivi", sub: "102 compound, 101 isolation, 54 stretching,\n50 bodyweight, 35 cardio, 30 mobilita", color: C.teal },
    { num: "52", label: "Muscoli NSCA", sub: "15 gruppi muscolari principali.\nAttivazione EMG 0-100 per esercizio.", color: C.blue },
    { num: "15", label: "Articolazioni", sub: "6 tipi giuntura (hinge, ball&socket...).\nROM in gradi per esercizio.", color: C.purple },
    { num: "47", label: "Condizioni Mediche", sub: "5 categorie: ortopediche, cardiovascolari,\nmetaboliche, neurologiche, speciali.", color: C.coral },
    { num: "7", label: "Categorie Esercizi", sub: "Composto, Isolamento, Corpo Libero,\nCardio, Stretching, Mobilita, Avviamento.", color: C.green },
    { num: "10D", label: "Vettore Biomeccanico", sub: "Skill, coordinazione, stabilita, ballistico,\nimpatto, assiale, spalla, lombare, grip, metabolico.", color: C.amber },
  ];

  dbStats.forEach((st, i) => {
    const row = Math.floor(i / 3);
    const col = i % 3;
    const sx = 0.8 + col * 3.0;
    const sy = 1.3 + row * 2.0;

    addCard(s, sx, sy, 2.7, 1.8, C.white);
    s.addText(st.num, {
      x: sx + 0.2, y: sy + 0.1, w: 2.3, h: 0.55,
      fontSize: 32, fontFace: FONT_H, color: st.color, bold: true,
    });
    s.addText(st.label, {
      x: sx + 0.2, y: sy + 0.65, w: 2.3, h: 0.3,
      fontSize: 13, fontFace: FONT_B, color: C.dark, bold: true, margin: 0,
    });
    s.addText(st.sub, {
      x: sx + 0.2, y: sy + 1.0, w: 2.3, h: 0.7,
      fontSize: 10, fontFace: FONT_B, color: C.slateDark, margin: 0,
    });
  });

  addSlideNumber(s, 12, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// SLIDE 12: TRAINING SCIENCE ARCHITECTURE
// ═══════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.dark };
  s.addShape("rect", { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.teal } });

  s.addText("Training Science Engine", {
    x: 0.8, y: 0.3, w: 8.4, h: 0.6,
    fontSize: 32, fontFace: FONT_H, color: C.white, bold: true,
  });
  s.addText("~3.500 linee di codice. 10 moduli core + 18 SMART runtime layers. Ogni numero ha una fonte scientifica.", {
    x: 0.8, y: 0.85, w: 8.4, h: 0.35,
    fontSize: 12, fontFace: FONT_B, color: C.slate,
  });

  // Architecture layers
  const layers = [
    { label: "FONDAMENTA", items: "Types (15 enum, 21 modelli) | Principles (5 obiettivi x 7 parametri)", y: 1.4, color: C.tealDark },
    { label: "MUSCOLI", items: "EMG Matrix 18x15 | Volume MEV/MAV/MRV | Balance Ratios (5)", y: 2.0, color: C.teal },
    { label: "PIANIFICAZIONE", items: "Split Logic | Session Order | Plan Builder 4 fasi | Analyzer 4D", y: 2.6, color: C.mint },
    { label: "PERIODIZZAZIONE", items: "Mesociclo a blocchi: Accumulazione > Intensificazione > Overreaching > Deload", y: 3.2, color: C.green },
    { label: "SMART RUNTIME", items: "6 Protocolli | Constraint Engine | 10D Demand | Feasibility | 6 Benchmark", y: 3.8, color: C.blue },
  ];

  layers.forEach((l) => {
    s.addShape("rect", { x: 0.8, y: l.y, w: 1.8, h: 0.45, fill: { color: l.color } });
    s.addText(l.label, {
      x: 0.8, y: l.y, w: 1.8, h: 0.45,
      fontSize: 10, fontFace: FONT_B, color: C.white, bold: true, align: "center", valign: "middle",
    });
    s.addShape("rect", { x: 2.7, y: l.y, w: 6.5, h: 0.45, fill: { color: C.darkAlt } });
    s.addText(l.items, {
      x: 2.9, y: l.y, w: 6.1, h: 0.45,
      fontSize: 11, fontFace: FONT_B, color: C.mintLight, valign: "middle",
    });
  });

  // Bottom stats
  s.addShape("rect", { x: 0, y: 4.5, w: 10, h: 1.125, fill: { color: C.darkAlt } });
  const bottomStats = [
    { num: "35+", label: "Formule" },
    { num: "18x15", label: "EMG Matrix" },
    { num: "6", label: "Protocolli" },
    { num: "22", label: "Check Functions" },
  ];
  bottomStats.forEach((bs, i) => {
    const bx = 0.8 + i * 2.3;
    s.addText(bs.num, { x: bx, y: 4.6, w: 1.8, h: 0.45, fontSize: 28, fontFace: FONT_H, color: C.mint, bold: true });
    s.addText(bs.label, { x: bx, y: 5.05, w: 1.8, h: 0.3, fontSize: 11, fontFace: FONT_B, color: C.slate });
  });

  addSlideNumber(s, 13, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// SLIDE 13: EMG MATRIX & VOLUME MODEL
// ═══════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("EMG Matrix & Volume Model", {
    x: 0.8, y: 0.25, w: 8.4, h: 0.5,
    fontSize: 28, fontFace: FONT_H, color: C.dark, bold: true,
  });

  // EMG matrix visualization (simplified heatmap) — left half
  s.addText("Matrice Contribuzione EMG", {
    x: 0.8, y: 0.75, w: 5.0, h: 0.25,
    fontSize: 12, fontFace: FONT_B, color: C.dark, bold: true,
  });

  // Compact heatmap: 7 key patterns x 8 muscles
  const patterns = ["Push H", "Push V", "Pull H", "Pull V", "Squat", "Hinge", "Curl"];
  const muscles = ["Petto", "Dorsali", "Delt A", "Bicip", "Tricip", "Quad", "Femor", "Glutei"];
  const matrix = [
    [1.0, 0, 0.7, 0, 0.7, 0, 0, 0],     // Push H
    [0.4, 0, 1.0, 0, 0.7, 0, 0, 0],     // Push V
    [0, 1.0, 0, 0.7, 0, 0, 0, 0],         // Pull H
    [0, 1.0, 0, 0.7, 0, 0, 0, 0],         // Pull V
    [0, 0, 0, 0, 0, 1.0, 0.4, 0.7],       // Squat
    [0, 0, 0, 0, 0, 0.2, 1.0, 0.7],       // Hinge
    [0, 0, 0, 1.0, 0, 0, 0, 0],           // Curl
  ];

  const cellW = 0.52;
  const cellH = 0.28;
  const startX = 1.3;
  const startY = 1.15;

  // Column headers
  muscles.forEach((m, j) => {
    s.addText(m, {
      x: startX + j * cellW, y: startY - 0.2, w: cellW, h: 0.2,
      fontSize: 7, fontFace: FONT_B, color: C.slateDark, align: "center",
    });
  });

  // Row headers + cells
  patterns.forEach((p, i) => {
    s.addText(p, {
      x: 0.3, y: startY + i * cellH, w: 0.95, h: cellH,
      fontSize: 8, fontFace: FONT_B, color: C.slateDark, align: "right", valign: "middle",
    });
    muscles.forEach((m, j) => {
      const val = matrix[i][j];
      let fillColor = C.white;
      if (val >= 1.0) fillColor = C.tealDark;
      else if (val >= 0.7) fillColor = C.teal;
      else if (val >= 0.4) fillColor = C.mint;
      else if (val >= 0.2) fillColor = C.mintLight;
      s.addShape("rect", {
        x: startX + j * cellW, y: startY + i * cellH, w: cellW - 0.02, h: cellH - 0.02,
        fill: { color: fillColor },
      });
    });
  });

  // Legend — right of heatmap
  const legendItems = [
    { label: "1.0 Primario", color: C.tealDark },
    { label: "0.7 Sinergista+", color: C.teal },
    { label: "0.4 Sinergista-", color: C.mint },
    { label: "0.2 Stabilizzatore", color: C.mintLight },
  ];
  legendItems.forEach((li, i) => {
    s.addShape("rect", { x: 5.8, y: 1.15 + i * 0.25, w: 0.18, h: 0.18, fill: { color: li.color } });
    s.addText(li.label, { x: 6.02, y: 1.15 + i * 0.25, w: 1.5, h: 0.18, fontSize: 8, fontFace: FONT_B, color: C.slateDark, margin: 0 });
  });

  // Volume Model section — right column
  s.addText("Volume Model: MEV / MAV / MRV", {
    x: 5.8, y: 2.3, w: 3.8, h: 0.25,
    fontSize: 12, fontFace: FONT_B, color: C.dark, bold: true,
  });

  const volumeData = [
    ["Muscolo", "MEV", "MAV min", "MAV max", "MRV"],
    ["Petto", "4", "8", "12", "16"],
    ["Dorsali", "4", "12", "18", "25"],
    ["Quadricipiti", "4", "10", "16", "20"],
    ["Femorali", "4", "8", "12", "16"],
  ];

  s.addTable(volumeData, {
    x: 5.8, y: 2.6, w: 3.8,
    fontSize: 9, fontFace: FONT_B,
    border: { pt: 0.5, color: "E2E8F0" },
    colW: [1.0, 0.6, 0.7, 0.7, 0.6],
    rowH: [0.2, 0.18, 0.18, 0.18, 0.18],
    autoPage: false,
  });

  // Bottom section: scaling + key insight
  addCard(s, 0.8, 3.6, 8.4, 1.6, C.white);
  addAccentBar(s, 0.8, 3.6, 1.6, C.teal);

  s.addText("Come Funziona", {
    x: 1.1, y: 3.7, w: 8.0, h: 0.25,
    fontSize: 13, fontFace: FONT_B, color: C.dark, bold: true, margin: 0,
  });

  s.addText([
    { text: "Dual Volume Calculation: ", options: { bold: true } },
    { text: "Effective Sets (lavoro meccanico) + Hypertrophy Sets (qualita stimolo).", options: { breakLine: true } },
    { text: "Dose-Response Model: ", options: { bold: true } },
    { text: "dose[muscolo] = EMG x serie x intensity_weight (normalizzato sul piano).", options: { breakLine: true } },
    { text: "Scaling Demografico: ", options: { bold: true } },
    { text: "Sesso (F=0.85, Vingren 2010) x Eta (45-59=0.85, 60+=0.75, Peterson 2011).", options: { breakLine: true } },
    { text: "Fonti: Israetel RP 2020, Schoenfeld 2017, Krieger 2010, Contreras 2010." },
  ], {
    x: 1.1, y: 4.0, w: 7.8, h: 1.1,
    fontSize: 11, fontFace: FONT_B, color: C.slateDark, paraSpaceAfter: 4,
  });

  addSlideNumber(s, 14, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// SLIDE 14: SMART ENGINE
// ═══════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("SMART Engine", {
    x: 0.8, y: 0.25, w: 8.4, h: 0.45,
    fontSize: 28, fontFace: FONT_H, color: C.dark, bold: true,
  });

  s.addText("Programmazione intelligente: profilo cliente + protocollo + vincoli biomeccanici + catalogo esercizi.", {
    x: 0.8, y: 0.7, w: 8.4, h: 0.3,
    fontSize: 12, fontFace: FONT_B, color: C.slateDark,
  });

  // LEFT COLUMN: 10D Demand Vector
  s.addText("Vettore Biomeccanico 10D", {
    x: 0.8, y: 1.1, w: 4.5, h: 0.25,
    fontSize: 12, fontFace: FONT_B, color: C.dark, bold: true,
  });

  const demands = [
    "Skill", "Coordinazione", "Stabilita", "Ballistico", "Impatto",
    "Carico Assiale", "Spalla Complex", "Carico Lombare", "Grip", "Metabolico",
  ];

  demands.forEach((d, i) => {
    const col = Math.floor(i / 5);
    const row = i % 5;
    const dx = 0.8 + col * 2.4;
    const dy = 1.45 + row * 0.28;
    const val = [2, 3, 2, 0, 1, 3, 4, 3, 2, 2][i];
    s.addText(d, { x: dx, y: dy, w: 1.2, h: 0.22, fontSize: 8, fontFace: FONT_B, color: C.slateDark, margin: 0 });
    s.addShape("rect", { x: dx + 1.2, y: dy + 0.04, w: 0.9, h: 0.14, fill: { color: "E2E8F0" } });
    s.addShape("rect", { x: dx + 1.2, y: dy + 0.04, w: (val / 4) * 0.9, h: 0.14, fill: { color: C.teal } });
  });

  // RIGHT COLUMN: Pipeline di Selezione
  s.addText("Pipeline di Selezione", {
    x: 5.8, y: 1.1, w: 3.8, h: 0.25,
    fontSize: 12, fontFace: FONT_B, color: C.dark, bold: true,
  });

  const pipeline = [
    { label: "Profilo Cliente", desc: "Livello + obiettivo + anamnesi", color: C.teal },
    { label: "Protocol Selector", desc: "6 protocolli PRT-001..006", color: C.blue },
    { label: "Constraint Engine", desc: "Ceiling biomeccanico 10D", color: C.purple },
    { label: "Exercise Ranker", desc: "Score affinita + demand fit", color: C.green },
    { label: "Feasibility Engine", desc: "Validazione finale + metadata", color: C.tealDark },
  ];

  pipeline.forEach((pp, i) => {
    const py = 1.45 + i * 0.47;
    s.addShape("rect", { x: 5.8, y: py, w: 3.6, h: 0.38, fill: { color: pp.color } });
    s.addText(pp.label, {
      x: 5.9, y: py + 0.02, w: 1.6, h: 0.18,
      fontSize: 9, fontFace: FONT_B, color: C.white, bold: true, margin: 0,
    });
    s.addText(pp.desc, {
      x: 7.5, y: py + 0.02, w: 1.8, h: 0.34,
      fontSize: 8, fontFace: FONT_B, color: C.slate, margin: 0, valign: "middle",
    });
  });

  // BOTTOM: Protocol table — full width, below both columns
  s.addText("6 Protocolli Supportati", {
    x: 0.8, y: 3.65, w: 4.0, h: 0.22,
    fontSize: 11, fontFace: FONT_B, color: C.dark, bold: true,
  });

  const protoData = [
    ["ID", "Livello", "Split", "Freq", "Status"],
    ["PRT-001", "Principiante", "Full Body", "3x", "Supportato"],
    ["PRT-002", "Intermedio", "Full Body", "3x", "Supportato"],
    ["PRT-003", "Intermedio", "Upper/Lower", "4x", "Supportato"],
    ["PRT-004", "Intermedio", "Upper/Lower", "4x", "Supportato"],
    ["PRT-005", "Avanzato", "Push/Pull/Legs", "5-6x", "Research"],
    ["PRT-006", "Clinico", "Adattato", "2-4x", "Research"],
  ];

  s.addTable(protoData, {
    x: 0.8, y: 3.9, w: 8.4,
    fontSize: 8, fontFace: FONT_B,
    border: { pt: 0.5, color: "E2E8F0" },
    colW: [1.0, 1.5, 1.8, 0.8, 1.2],
    rowH: [0.16, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15],
    autoPage: false,
  });

  addSlideNumber(s, 15, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// SLIDE 15: PLAN BUILDER & 4D ANALYZER
// ═══════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("Plan Builder & Analisi 4D", {
    x: 0.8, y: 0.3, w: 8.4, h: 0.6,
    fontSize: 30, fontFace: FONT_H, color: C.dark, bold: true,
  });

  // 4 phases
  s.addText("Generazione Piano: 4 Fasi con Feedback Loop", {
    x: 0.8, y: 0.9, w: 8.4, h: 0.3,
    fontSize: 14, fontFace: FONT_B, color: C.dark, bold: true,
  });

  const phases = [
    { num: "1", title: "Compound Base", desc: "Pattern per ruolo sessione. SNC-demanding first.", color: C.teal },
    { num: "2", title: "Boost Compound", desc: "Deficit muscoli < MAV? Boost serie compound. MAV guard.", color: C.mint },
    { num: "3", title: "Isolation Comp.", desc: "Muscoli ancora sotto MEV? Aggiungi isolamento per affinita.", color: C.blue },
    { num: "4", title: "Feedback Loop", desc: "Ricalcola volume. Deficit significativi? Ripeti fase 2+3.", color: C.purple },
  ];

  phases.forEach((ph, i) => {
    const px = 0.8 + i * 2.25;
    s.addShape("rect", { x: px, y: 1.3, w: 2.0, h: 1.4, fill: { color: C.white }, shadow: makeCardShadow() });
    s.addShape("rect", { x: px, y: 1.3, w: 2.0, h: 0.35, fill: { color: ph.color } });
    s.addText(`Fase ${ph.num}`, {
      x: px, y: 1.3, w: 2.0, h: 0.35,
      fontSize: 12, fontFace: FONT_B, color: C.white, bold: true, align: "center", valign: "middle",
    });
    s.addText(ph.title, {
      x: px + 0.1, y: 1.7, w: 1.8, h: 0.3,
      fontSize: 12, fontFace: FONT_B, color: C.dark, bold: true, margin: 0,
    });
    s.addText(ph.desc, {
      x: px + 0.1, y: 2.0, w: 1.8, h: 0.6,
      fontSize: 10, fontFace: FONT_B, color: C.slateDark, margin: 0,
    });
  });

  // 4D Analysis
  s.addText("Scoring 4D (0-100 punti)", {
    x: 0.8, y: 2.9, w: 8.4, h: 0.3,
    fontSize: 14, fontFace: FONT_B, color: C.dark, bold: true,
  });

  const dimensions = [
    { dim: "VOLUME", desc: "Ogni muscolo nella zona MEV-MAV-MRV?\nSotto MEV = zero stimolo. Sopra MRV = overtraining.", icon: "V", color: C.teal },
    { dim: "BALANCE", desc: "5 rapporti biomeccanici in tolleranza?\nPush:Pull, Quad:Ham, Ant:Post, Push H:V, Pull H:V.", icon: "B", color: C.blue },
    { dim: "FREQUENCY", desc: "Ogni muscolo stimolato 2x/settimana?\nSchoenfeld 2016: MPS ottimale a 2x.", icon: "F", color: C.green },
    { dim: "RECOVERY", desc: "No sovrapposizione su sessioni consecutive?\nFinestra recupero 48-72h (NSCA 2016).", icon: "R", color: C.purple },
  ];

  dimensions.forEach((d, i) => {
    const dx = 0.8 + i * 2.25;
    addCard(s, dx, 3.3, 2.0, 1.9, C.white);
    s.addShape("rect", { x: dx + 0.7, y: 3.4, w: 0.6, h: 0.45, fill: { color: d.color } });
    s.addText(d.icon, {
      x: dx + 0.7, y: 3.4, w: 0.6, h: 0.45,
      fontSize: 18, fontFace: FONT_H, color: C.white, bold: true, align: "center", valign: "middle",
    });
    s.addText(d.dim, {
      x: dx + 0.15, y: 3.9, w: 1.7, h: 0.3,
      fontSize: 13, fontFace: FONT_B, color: C.dark, bold: true, align: "center", margin: 0,
    });
    s.addText(d.desc, {
      x: dx + 0.15, y: 4.2, w: 1.7, h: 0.9,
      fontSize: 9, fontFace: FONT_B, color: C.slateDark, margin: 0,
    });
  });

  addSlideNumber(s, 16, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// SLIDE 16: FONTI SCIENTIFICHE
// ═══════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.dark };
  s.addShape("rect", { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.teal } });

  s.addText("18 Fonti Scientifiche Peer-Reviewed", {
    x: 0.8, y: 0.3, w: 8.4, h: 0.6,
    fontSize: 28, fontFace: FONT_H, color: C.white, bold: true,
  });
  s.addText("Ogni formula, ogni soglia, ogni coefficiente ha una fonte bibliografica verificabile.", {
    x: 0.8, y: 0.85, w: 8.4, h: 0.3,
    fontSize: 12, fontFace: FONT_B, color: C.slate, italic: true,
  });

  const refs = [
    ["Haff & Triplett", "2016", "NSCA Essentials", "Volume-load, intensita, frequenza, split"],
    ["Schoenfeld", "2010-2021", "Hypertrophy Research", "EMG, dose-response, frequenza ottimale"],
    ["Israetel (RP)", "2020", "Scientific Principles", "MEV/MAV/MRV, mesociclo, supercompensazione"],
    ["Krieger", "2010", "Single vs Multiple Sets", "Validazione soglia MEV"],
    ["Sahrmann", "2002", "Movement Impairment", "Balance ratios, sindromi crociate"],
    ["Contreras", "2010", "EMG Analysis", "Matrice contribuzione 18x15"],
    ["Zourdos", "2016", "RPE/RIR Scale", "Autoregolazione 2.5% per RIR"],
    ["Helms", "2016-2019", "RPE & Pyramid", "Protocolli deload, progressione"],
    ["Bompa", "2019", "Periodization 6th ed.", "Blocco periodizzazione"],
    ["LARN/SINU", "2014", "Livelli di Assunzione", "19 nutrienti, 8 fasce eta/sesso"],
    ["CREA", "2018-2019", "Linee Guida + Tavole", "226 alimenti, frequenze settimanali"],
    ["OMS/ACSM/AHA", "Various", "Clinical Norms", "BMI, WHR, VO2max, PA ranges"],
  ];

  const tableData = [["Autore", "Anno", "Opera", "Applicazione"], ...refs];

  s.addTable(tableData, {
    x: 0.5, y: 1.25, w: 9.0,
    fontSize: 10, fontFace: FONT_B,
    color: C.white,
    border: { pt: 0.5, color: "334155" },
    colW: [1.5, 1.0, 2.2, 4.0],
    rowH: [0.28, ...refs.map(() => 0.28)],
    autoPage: false,
  });

  // First row styling
  tableData[0] = tableData[0].map(cell => ({
    text: cell,
    options: { fill: { color: C.tealDark }, color: C.white, bold: true, fontSize: 10 },
  }));

  addSlideNumber(s, 17, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// SLIDE 17: NUTRITION SCIENCE
// ═══════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("Nutrition Science Engine", {
    x: 0.8, y: 0.3, w: 8.4, h: 0.55,
    fontSize: 28, fontFace: FONT_H, color: C.dark, bold: true,
  });

  s.addText("Basato su LARN 2014 (SINU) e Linee Guida CREA 2018. ~2.100 LOC.", {
    x: 0.8, y: 0.85, w: 8.4, h: 0.3,
    fontSize: 12, fontFace: FONT_B, color: C.slateDark,
  });

  // Stats row
  const nStats = [
    { num: "226", label: "Alimenti\nCREA + USDA", color: C.teal },
    { num: "19", label: "Nutrienti\nMonitorati", color: C.green },
    { num: "8", label: "Fasce\nEta/Sesso", color: C.blue },
    { num: "40", label: "Porzioni\nLARN", color: C.amber },
  ];

  nStats.forEach((ns, i) => {
    const nx = 0.8 + i * 2.25;
    addCard(s, nx, 1.25, 2.0, 0.9, C.white);
    s.addText(ns.num, {
      x: nx + 0.15, y: 1.3, w: 1.7, h: 0.35,
      fontSize: 24, fontFace: FONT_H, color: ns.color, bold: true,
    });
    s.addText(ns.label, {
      x: nx + 0.15, y: 1.7, w: 1.7, h: 0.35,
      fontSize: 9, fontFace: FONT_B, color: C.slateDark,
    });
  });

  // Architecture flow
  s.addText("Pipeline Generazione Piano 7 Giorni", {
    x: 0.8, y: 2.3, w: 8.4, h: 0.3,
    fontSize: 12, fontFace: FONT_B, color: C.dark, bold: true,
  });

  const nFlow = [
    { label: "Profilo\nCliente", color: C.teal },
    { label: "Food Pool\nResolver", color: C.tealDark },
    { label: "Selezione\n+ Varieta", color: C.blue },
    { label: "Ottimizzazione\n4-Step", color: C.purple },
    { label: "Validazione\nLARN 3-Assi", color: C.green },
  ];

  nFlow.forEach((nf, i) => {
    const nx = 0.6 + i * 1.9;
    s.addShape("rect", { x: nx, y: 2.65, w: 1.6, h: 0.65, fill: { color: nf.color } });
    s.addText(nf.label, {
      x: nx, y: 2.65, w: 1.6, h: 0.65,
      fontSize: 10, fontFace: FONT_B, color: C.white, bold: true, align: "center", valign: "middle",
    });
    if (i < 4) {
      s.addText(">", {
        x: nx + 1.55, y: 2.7, w: 0.4, h: 0.55,
        fontSize: 18, fontFace: FONT_B, color: C.slate, align: "center", valign: "middle",
      });
    }
  });

  // Protein rotation table
  s.addText("Rotazione Proteica Settimanale (CREA Dir. 9)", {
    x: 0.8, y: 3.5, w: 8.4, h: 0.3,
    fontSize: 12, fontFace: FONT_B, color: C.dark, bold: true,
  });

  const proteinData = [
    ["Tipo", "Min", "Max", "Note"],
    ["Pesce", "2", "3", "Pesce azzurro (omega-3)"],
    ["Carne bianca", "1", "3", "Pollo, tacchino, coniglio"],
    ["Carne rossa", "0", "2", "WCRF: limitare"],
    ["Uova", "2", "4", "2-4/settimana"],
    ["Legumi", "2", "4", "Lenticchie, ceci, tofu"],
    ["Affettati", "0", "1", "WCRF: minimizzare"],
  ];

  s.addTable(proteinData, {
    x: 0.8, y: 3.85, w: 8.4,
    fontSize: 9, fontFace: FONT_B,
    border: { pt: 0.5, color: "E2E8F0" },
    colW: [1.3, 0.5, 0.5, 5.8],
    rowH: [0.17, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15],
    autoPage: false,
  });

  addSlideNumber(s, 18, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// SLIDE 18: NUTRITION SCORING
// ═══════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("Scoring Nutrizionale 3 Assi", {
    x: 0.8, y: 0.3, w: 8.4, h: 0.6,
    fontSize: 30, fontFace: FONT_H, color: C.dark, bold: true,
  });

  s.addText("Ogni piano alimentare riceve un punteggio composito 0-100 basato su 3 dimensioni LARN/CREA.", {
    x: 0.8, y: 0.85, w: 8.4, h: 0.3,
    fontSize: 13, fontFace: FONT_B, color: C.slateDark,
  });

  // 3 scoring axes
  const axes = [
    {
      title: "Asse 1: Macro",
      weight: "25%",
      desc: "Distribuzione % kcal:\nProteine 12-20%\nCarboidrati 45-60%\nGrassi 20-35%\n\nFonte: LARN 2014",
      color: C.teal,
    },
    {
      title: "Asse 2: Micro",
      weight: "35%",
      desc: "19 nutrienti vs AR/PRI/AI/UL:\n10 vitamine (A,D,E,C,B1-B6,B9,B12)\n9 minerali (Ca,Fe,Zn,Mg,P,K,Se,Na)\n+ fibra\n\nFonte: LARN 2014",
      color: C.blue,
    },
    {
      title: "Asse 3: Frequenze",
      weight: "40%",
      desc: "Porzioni settimanali vs target CREA:\n17 sotto-gruppi alimentari\n6 sotto-frequenze proteiche\nRotazione varieta\n\nFonte: CREA 2018",
      color: C.green,
    },
  ];

  axes.forEach((ax, i) => {
    const axx = 0.8 + i * 3.0;
    addCard(s, axx, 1.3, 2.7, 3.0, C.white);
    s.addShape("rect", { x: axx, y: 1.3, w: 2.7, h: 0.5, fill: { color: ax.color } });
    s.addText(`${ax.title} (${ax.weight})`, {
      x: axx, y: 1.3, w: 2.7, h: 0.5,
      fontSize: 14, fontFace: FONT_B, color: C.white, bold: true, align: "center", valign: "middle",
    });
    s.addText(ax.desc, {
      x: axx + 0.15, y: 1.9, w: 2.4, h: 2.3,
      fontSize: 11, fontFace: FONT_B, color: C.slateDark,
    });
  });

  // Formula box
  addCard(s, 0.8, 4.5, 8.4, 0.8, C.white);
  addAccentBar(s, 0.8, 4.5, 0.8, C.teal);
  s.addText("Score Finale = Macro x 0.25 + Micro x 0.35 + Frequenze x 0.40", {
    x: 1.1, y: 4.55, w: 7.8, h: 0.35,
    fontSize: 16, fontFace: FONT_H, color: C.dark, bold: true, margin: 0,
  });
  s.addText("Peso maggiore alle frequenze (40%) perche determinano l'aderenza comportamentale a lungo termine.", {
    x: 1.1, y: 4.9, w: 7.8, h: 0.3,
    fontSize: 11, fontFace: FONT_B, color: C.slateDark, italic: true, margin: 0,
  });

  addSlideNumber(s, 19, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// SLIDE 19: NUTRITION DETAIL - SCREENSHOT ESERCIZI
// ═══════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.dark };
  s.addShape("rect", { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.teal } });

  s.addText("Il Catalogo in Azione", {
    x: 0.8, y: 0.3, w: 5, h: 0.5,
    fontSize: 24, fontFace: FONT_H, color: C.white, bold: true,
  });
  s.addText("434 esercizi con foto, muscoli target, categoria, difficolta. Filtri multipli.", {
    x: 0.8, y: 0.75, w: 5, h: 0.35,
    fontSize: 12, fontFace: FONT_B, color: C.slate,
  });

  s.addShape("rect", {
    x: 0.7, y: 1.25, w: 8.6, h: 4.15,
    fill: { color: C.darkAlt },
    shadow: makeShadow(),
  });
  s.addImage({
    path: `${SCREENSHOTS}/04-esercizi.png`,
    x: 0.8, y: 1.3, w: 8.4, h: 4.0,
  });

  addSlideNumber(s, 20, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// SLIDE 21: QUALITA DIMOSTRABILE (NEW)
// ═══════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("Qualita Dimostrabile", {
    x: 0.8, y: 0.25, w: 8.4, h: 0.5,
    fontSize: 28, fontFace: FONT_H, color: C.dark, bold: true,
  });
  s.addText("Il tuo lavoro diventa visibile. I risultati parlano con dati, non con opinioni.", {
    x: 0.8, y: 0.75, w: 8.4, h: 0.3,
    fontSize: 13, fontFace: FONT_B, color: C.slateDark,
  });

  // Before/After columns
  // LEFT: "Senza FitManager"
  addCard(s, 0.5, 1.2, 4.3, 2.6, C.coralBg);
  s.addShape("rect", { x: 0.5, y: 1.2, w: 4.3, h: 0.35, fill: { color: C.coral } });
  s.addText("Senza FitManager", {
    x: 0.5, y: 1.2, w: 4.3, h: 0.35,
    fontSize: 13, fontFace: FONT_B, color: C.white, bold: true, align: "center", valign: "middle",
  });

  const withoutItems = [
    "\"Mi sento meglio\" — feedback soggettivo",
    "Scheda su foglio Excel o app note",
    "Nessun dato su progressi misurabili",
    "Il cliente non vede il valore aggiunto",
    "Giustificare la tariffa e difficile",
    "Il PT sembra sostituibile",
  ];
  s.addText(withoutItems.map((f, i) => ({
    text: f,
    options: { bullet: true, breakLine: i < withoutItems.length - 1, fontSize: 10, color: C.slateDark },
  })), { x: 0.7, y: 1.65, w: 3.9, h: 2.0, fontFace: FONT_B, paraSpaceAfter: 4 });

  // RIGHT: "Con FitManager"
  addCard(s, 5.2, 1.2, 4.3, 2.6, C.greenBg);
  s.addShape("rect", { x: 5.2, y: 1.2, w: 4.3, h: 0.35, fill: { color: C.green } });
  s.addText("Con FitManager", {
    x: 5.2, y: 1.2, w: 4.3, h: 0.35,
    fontSize: 13, fontFace: FONT_B, color: C.white, bold: true, align: "center", valign: "middle",
  });

  const withItems = [
    "Report clinico con range OMS/ACSM",
    "Scheda con analisi 4D e score scientifico",
    "Grafici progressi: peso, composizione, forza",
    "Safety Engine: \"Ho verificato le tue condizioni\"",
    "Il cliente VEDE il metodo dietro al servizio",
    "Il PT diventa insostituibile",
  ];
  s.addText(withItems.map((f, i) => ({
    text: f,
    options: { bullet: true, breakLine: i < withItems.length - 1, fontSize: 10, color: C.slateDark },
  })), { x: 5.4, y: 1.65, w: 3.9, h: 2.0, fontFace: FONT_B, paraSpaceAfter: 4 });

  // Bottom: The insight
  addCard(s, 0.5, 4.1, 9.0, 1.2, C.white);
  s.addShape("rect", { x: 0.5, y: 4.1, w: 0.06, h: 1.2, fill: { color: C.teal } });

  s.addText("Il principio chiave", {
    x: 0.8, y: 4.15, w: 8.5, h: 0.3,
    fontSize: 14, fontFace: FONT_B, color: C.dark, bold: true, margin: 0,
  });
  s.addText([
    { text: "Quando il cliente vede i dati — ", options: {} },
    { text: "grafici, score, analisi biomeccanica, report clinico", options: { bold: true } },
    { text: " — percepisce un servizio di livello superiore.", options: { breakLine: true } },
    { text: "Non stai vendendo \"allenamento\". Stai vendendo un ", options: {} },
    { text: "metodo scientifico personalizzato", options: { bold: true } },
    { text: ". E un metodo scientifico vale di piu.", options: {} },
  ], {
    x: 0.8, y: 4.45, w: 8.5, h: 0.75,
    fontSize: 12, fontFace: FONT_B, color: C.slateDark, paraSpaceAfter: 4, margin: 0,
  });

  addSlideNumber(s, 21, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// SLIDE 22: COMPETITIVE COMPARISON
// ═══════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("Confronto Competitivo", {
    x: 0.8, y: 0.3, w: 8.4, h: 0.6,
    fontSize: 30, fontFace: FONT_H, color: C.dark, bold: true,
  });

  const compData = [
    [
      { text: "Feature", options: { bold: true, fill: { color: C.tealDark }, color: C.white, fontSize: 10 } },
      { text: "FitManager", options: { bold: true, fill: { color: C.tealDark }, color: C.white, fontSize: 10 } },
      { text: "Trainerize", options: { bold: true, fill: { color: "334155" }, color: C.white, fontSize: 10 } },
      { text: "MyPTHub", options: { bold: true, fill: { color: "334155" }, color: C.white, fontSize: 10 } },
      { text: "EvolutionFit", options: { bold: true, fill: { color: "334155" }, color: C.white, fontSize: 10 } },
    ],
    ["EMG Matrix", "18x15", "No", "No", "No"],
    ["Volume MEV/MAV/MRV", "Si", "No", "No", "No"],
    ["Safety Engine", "47 condizioni", "No", "No", "No"],
    ["Periodizzazione", "4 fasi evidence", "No", "Basica", "No"],
    ["Balance Ratios", "5 biomeccanici", "No", "No", "No"],
    ["Dati Locali", "Si, zero cloud", "Cloud only", "Cloud only", "Cloud only"],
    ["Italiano Nativo", "Si", "No", "No", "Tradotto"],
    ["Nutrizione LARN", "226 alimenti", "No", "Basica", "No"],
    ["Prezzo", "EUR 149-249 una tantum", "EUR 696/anno", "EUR 588/anno", "EUR 468/anno"],
    ["Licenza", "Perpetua", "Abbonamento", "Abbonamento", "Abbonamento"],
  ];

  s.addTable(compData, {
    x: 0.5, y: 1.0, w: 9.0,
    fontSize: 10, fontFace: FONT_B,
    border: { pt: 0.5, color: "E2E8F0" },
    colW: [2.0, 1.8, 1.5, 1.5, 1.5],
    rowH: [0.32, ...Array(10).fill(0.36)],
    autoPage: false,
  });

  addSlideNumber(s, 22, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// SLIDE 23: IL CIRCOLO VIRTUOSO (NEW)
// ═══════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.dark };
  s.addShape("rect", { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.teal } });

  s.addText("Il Circolo Virtuoso", {
    x: 0.8, y: 0.25, w: 8.4, h: 0.5,
    fontSize: 28, fontFace: FONT_H, color: C.white, bold: true,
  });
  s.addText("Come FitManager trasforma il tuo business.", {
    x: 0.8, y: 0.75, w: 8.4, h: 0.3,
    fontSize: 13, fontFace: FONT_B, color: C.slate, italic: true,
  });

  // 4-step virtuous cycle — horizontal flow
  const steps = [
    { num: "1", title: "Risparmi\nTempo", desc: "4-6 ore/settimana\nliberate da burocrazia", color: C.teal },
    { num: "2", title: "Servizio\nMigliore", desc: "Piu tempo per ogni\ncliente, piu attenzione", color: C.mint },
    { num: "3", title: "Qualita\nVisibile", desc: "Report, grafici, score:\nil cliente VEDE il valore", color: C.green },
    { num: "4", title: "Tariffe\nPiu Alte", desc: "Metodo scientifico\n= posizionamento premium", color: C.blue },
  ];

  steps.forEach((st, i) => {
    const sx = 0.5 + i * 2.4;
    // Circle with number
    s.addShape("rect", { x: sx, y: 1.3, w: 2.0, h: 2.0, fill: { color: C.darkAlt } });
    s.addShape("rect", { x: sx, y: 1.3, w: 2.0, h: 0.06, fill: { color: st.color } });

    s.addText(st.num, {
      x: sx + 0.7, y: 1.45, w: 0.6, h: 0.5,
      fontSize: 28, fontFace: FONT_H, color: st.color, bold: true, align: "center",
    });
    s.addText(st.title, {
      x: sx + 0.15, y: 2.0, w: 1.7, h: 0.5,
      fontSize: 13, fontFace: FONT_B, color: C.white, bold: true, align: "center", margin: 0,
    });
    s.addText(st.desc, {
      x: sx + 0.15, y: 2.55, w: 1.7, h: 0.6,
      fontSize: 10, fontFace: FONT_B, color: C.slate, align: "center", margin: 0,
    });

    // Arrow between steps
    if (i < 3) {
      s.addText(">", {
        x: sx + 2.0, y: 1.8, w: 0.4, h: 0.8,
        fontSize: 22, fontFace: FONT_B, color: C.slate, align: "center", valign: "middle",
      });
    }
  });

  // ROI calculation box
  s.addShape("rect", { x: 0.5, y: 3.6, w: 9.0, h: 1.6, fill: { color: C.darkAlt } });
  s.addShape("rect", { x: 0.5, y: 3.6, w: 0.06, h: 1.6, fill: { color: C.mint } });

  s.addText("L'effetto sulla tua attivita", {
    x: 0.8, y: 3.65, w: 8.5, h: 0.3,
    fontSize: 14, fontFace: FONT_B, color: C.white, bold: true, margin: 0,
  });

  const roiItems = [
    { metric: "Aumento tariffa +10-15%", detail: "Da EUR 40 a EUR 45-46/sessione grazie alla percezione di servizio clinico-scientifico" },
    { metric: "2-3 clienti in piu/mese", detail: "Tempo liberato = slot disponibili. Il passaparola cresce con la qualita visibile" },
    { metric: "ROI in 30-60 giorni", detail: "Con 20 clienti a +EUR 5/sessione x 4 sessioni/mese = +EUR 400/mese di fatturato aggiuntivo" },
  ];

  roiItems.forEach((ri, i) => {
    const ry = 4.0 + i * 0.38;
    s.addText(ri.metric, { x: 0.8, y: ry, w: 2.8, h: 0.33, fontSize: 11, fontFace: FONT_B, color: C.mint, bold: true, margin: 0 });
    s.addText(ri.detail, { x: 3.7, y: ry, w: 5.5, h: 0.33, fontSize: 10, fontFace: FONT_B, color: C.slate, margin: 0, valign: "middle" });
  });

  addSlideNumber(s, 23, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// SLIDE 24: PRICING
// ═══════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("Investimento Unico vs Abbonamento Eterno", {
    x: 0.8, y: 0.25, w: 8.4, h: 0.55,
    fontSize: 26, fontFace: FONT_H, color: C.dark, bold: true,
  });

  // Our pricing — left card
  addCard(s, 0.8, 0.95, 4.0, 3.0, C.white);
  s.addShape("rect", { x: 0.8, y: 0.95, w: 4.0, h: 0.4, fill: { color: C.teal } });
  s.addText("FitManager Studio+", {
    x: 0.8, y: 0.95, w: 4.0, h: 0.4,
    fontSize: 14, fontFace: FONT_B, color: C.white, bold: true, align: "center", valign: "middle",
  });

  s.addText("EUR 149 - 249", {
    x: 1.0, y: 1.45, w: 3.6, h: 0.55,
    fontSize: 32, fontFace: FONT_H, color: C.teal, bold: true, align: "center",
  });
  s.addText("Una tantum. Per sempre.", {
    x: 1.0, y: 1.95, w: 3.6, h: 0.25,
    fontSize: 13, fontFace: FONT_B, color: C.dark, align: "center", bold: true,
  });

  const ourFeatures = [
    "Licenza perpetua, nessun canone",
    "Aggiornamenti opzionali EUR 49/anno",
    "Tutti i motori scientifici inclusi",
    "Zero costi cloud (dati locali)",
    "ROI dal primo mese",
  ];
  s.addText(ourFeatures.map((f, i) => ({
    text: f,
    options: { bullet: true, breakLine: i < ourFeatures.length - 1, fontSize: 11, color: C.slateDark },
  })), {
    x: 1.2, y: 2.3, w: 3.2, h: 1.5,
    fontFace: FONT_B, paraSpaceAfter: 4,
  });

  // Competitor pricing — right card
  addCard(s, 5.2, 0.95, 4.0, 3.0, C.white);
  s.addShape("rect", { x: 5.2, y: 0.95, w: 4.0, h: 0.4, fill: { color: C.slateDark } });
  s.addText("Competitor SaaS (media)", {
    x: 5.2, y: 0.95, w: 4.0, h: 0.4,
    fontSize: 14, fontFace: FONT_B, color: C.white, bold: true, align: "center", valign: "middle",
  });

  s.addText("EUR 170-1.548", {
    x: 5.4, y: 1.45, w: 3.6, h: 0.55,
    fontSize: 26, fontFace: FONT_H, color: C.coral, bold: true, align: "center",
  });
  s.addText("All'anno. Ogni anno.", {
    x: 5.4, y: 1.95, w: 3.6, h: 0.25,
    fontSize: 13, fontFace: FONT_B, color: C.dark, align: "center", bold: true,
  });

  const theirFeatures = [
    "Abbonamento mensile obbligatorio",
    "Dati persi se smetti di pagare",
    "Costi cloud inclusi nel prezzo",
    "Feature scientifiche: nessuna",
    "Dopo 3 anni: EUR 500-4.600 spesi",
  ];
  s.addText(theirFeatures.map((f, i) => ({
    text: f,
    options: { bullet: true, breakLine: i < theirFeatures.length - 1, fontSize: 11, color: C.slateDark },
  })), {
    x: 5.6, y: 2.3, w: 3.2, h: 1.5,
    fontFace: FONT_B, paraSpaceAfter: 4,
  });

  // Bottom insight
  addCard(s, 0.8, 4.2, 8.4, 0.55, C.greenBg);
  addAccentBar(s, 0.8, 4.2, 0.55, C.green);
  s.addText("Un PT che guadagna EUR 20-33K/anno risparmia EUR 400-1.300/anno scegliendo FitManager.", {
    x: 1.1, y: 4.28, w: 7.8, h: 0.35,
    fontSize: 13, fontFace: FONT_B, color: C.dark, bold: true, margin: 0,
  });

  // Additional ROI detail — two columns to avoid wrapping
  addCard(s, 0.8, 4.85, 4.0, 0.4, C.white);
  addAccentBar(s, 0.8, 4.85, 0.4, C.teal);
  s.addText("Trainerize EUR 696/a | MyPTHub EUR 588/a", {
    x: 1.05, y: 4.88, w: 3.6, h: 0.3,
    fontSize: 9, fontFace: FONT_B, color: C.slateDark, margin: 0,
  });
  addCard(s, 5.2, 4.85, 4.0, 0.4, C.white);
  addAccentBar(s, 5.2, 4.85, 0.4, C.teal);
  s.addText("PT Distinction EUR 540/a | EvolutionFit EUR 468/a", {
    x: 5.45, y: 4.88, w: 3.6, h: 0.3,
    fontSize: 9, fontFace: FONT_B, color: C.slateDark, margin: 0,
  });

  addSlideNumber(s, 24, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// SLIDE 22: ROADMAP
// ═══════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("Roadmap Prodotto", {
    x: 0.8, y: 0.4, w: 8.4, h: 0.7,
    fontSize: 32, fontFace: FONT_H, color: C.dark, bold: true,
  });

  const roadmap = [
    { phase: "v1.0", period: "Q1 2026", status: "LIVE", items: "CRM completo, Training Science Engine,\nSafety Engine, Workout Builder, Cassa,\nInstaller Windows, Licenza RSA", color: C.teal },
    { phase: "v1.5", period: "Q2 2026", status: "NEXT", items: "Nutrizione completa (piano 7gg + scoring),\nExport PDF clinico avanzato,\nDashboard analytics avanzate", color: C.blue },
    { phase: "v2.0", period: "Q3 2026", status: "PLANNED", items: "AI Coach (Ollama locale, zero cloud),\nProgrammazione automatica smart,\nAssistente NLP integrato", color: C.purple },
    { phase: "v3.0", period: "2027", status: "VISION", items: "App mobile companion (offline-first),\nSync opzionale P2P (no cloud),\nMulti-operatore per palestre", color: C.amber },
  ];

  roadmap.forEach((r, i) => {
    const ry = 1.3 + i * 1.0;
    addCard(s, 0.8, ry, 8.4, 0.85, C.white);

    // Phase badge
    s.addShape("rect", { x: 0.8, y: ry, w: 1.0, h: 0.85, fill: { color: r.color } });
    s.addText(r.phase, {
      x: 0.8, y: ry, w: 1.0, h: 0.5,
      fontSize: 16, fontFace: FONT_H, color: C.white, bold: true, align: "center", valign: "middle",
    });
    s.addText(r.status, {
      x: 0.8, y: ry + 0.45, w: 1.0, h: 0.35,
      fontSize: 9, fontFace: FONT_B, color: C.white, align: "center", valign: "middle",
    });

    s.addText(r.period, {
      x: 2.0, y: ry + 0.05, w: 2.0, h: 0.3,
      fontSize: 14, fontFace: FONT_B, color: C.dark, bold: true, margin: 0,
    });
    s.addText(r.items, {
      x: 2.0, y: ry + 0.35, w: 7.0, h: 0.45,
      fontSize: 11, fontFace: FONT_B, color: C.slateDark, margin: 0,
    });
  });

  addSlideNumber(s, 25, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// SLIDE 23: CHIUSURA
// ═══════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.dark };
  s.addShape("rect", { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.teal } });

  s.addText("Il tuo studio.\nI tuoi dati.\nLa tua scienza.", {
    x: 0.8, y: 1.0, w: 8.4, h: 2.0,
    fontSize: 42, fontFace: FONT_H, color: C.white, bold: true,
  });

  s.addText("FitManager Studio+", {
    x: 0.8, y: 3.2, w: 8.4, h: 0.6,
    fontSize: 24, fontFace: FONT_B, color: C.mint,
  });

  s.addText("Contatti e demo: [da definire]", {
    x: 0.8, y: 4.0, w: 8.4, h: 0.4,
    fontSize: 14, fontFace: FONT_B, color: C.slate,
  });

  // Bottom bar
  s.addShape("rect", { x: 0, y: 4.8, w: 10, h: 0.825, fill: { color: C.darkAlt } });
  s.addText("Privacy-First  |  Offline  |  Scientifico  |  Italiano  |  Tuo per sempre", {
    x: 0.8, y: 4.9, w: 8.4, h: 0.5,
    fontSize: 14, fontFace: FONT_B, color: C.mintLight, align: "center",
  });

  addSlideNumber(s, 26, TOTAL);
})();

// ═══════════════════════════════════════════════════════════
// WRITE FILE
// ═══════════════════════════════════════════════════════════
pres.writeFile({ fileName: `${OUT_DIR}/FitManager_Pitch_Deck_v6.pptx` })
  .then(() => {
    console.log("Pitch deck generated: data/FitManager_Pitch_Deck.pptx");
    console.log(`${TOTAL} slides created.`);
  })
  .catch((err) => {
    console.error("Error:", err.message);
    process.exit(1);
  });

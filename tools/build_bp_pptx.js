// build_bp_pptx.js — FitManager Studio+ Business Plan v4.3
// Part 1: Slides 1–30 + scaffolding
// Part 2 (slides 31–58) will be appended below the marker comment.

const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const {
  FaClock, FaUserSlash, FaEyeSlash, FaMoneyBillWave, FaHeartBroken, FaEquals,
  FaUsers, FaChartLine, FaRocket, FaGlobeEurope,
  FaCheckCircle, FaDumbbell, FaShieldAlt, FaUtensils, FaFileInvoiceDollar,
  FaDesktop, FaGraduationCap, FaComments, FaWrench,
  FaMicroscope, FaBalanceScale,
  FaWhatsapp, FaMobileAlt, FaClipboardCheck, FaSearchPlus, FaHeart,
  FaLaptop, FaBoxOpen, FaLink, FaBullhorn, FaHandshake,
  FaRegNewspaper, FaTag, FaBolt, FaCode, FaStar,
  FaArrowRight, FaExclamationTriangle, FaLock,
  FaShip, FaBrain,
} = require("react-icons/fa");

// ============================================================
// PALETTE
// ============================================================
const C = {
  bg:        "0F1629",
  bgCard:    "1A2332",
  bgCard2:   "232F42",
  accent:    "00B4D8",
  accent2:   "06D6A0",
  gold:      "FFD166",
  red:       "EF476F",
  orange:    "F4A261",
  white:     "FFFFFF",
  textPri:   "FFFFFF",
  textSec:   "A0AEC0",
  textMuted: "718096",
  tableBg:   "141E30",
  tableHead: "1E2D45",
  tableRow1: "162036",
  tableRow2: "1A2540",
  border:    "2D3E56",
};

// ============================================================
// ICON HELPERS
// ============================================================
function renderIconSvg(IconComponent, color, size = 256) {
  return ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
}

async function iconB64(IconComponent, color = "#FFFFFF", size = 256) {
  const svg = renderIconSvg(IconComponent, color, size);
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

// ============================================================
// SHADOW FACTORY — always returns fresh object to avoid pptxgenjs reuse bugs
// ============================================================
function makeShadow() {
  return { type: "outer", blur: 8, offset: 3, angle: 135, color: "000000", opacity: 0.25 };
}

// ============================================================
// FOOTER
// ============================================================
function addFooter(slide, pageNum, total) {
  slide.addText("FitManager Studio+ \u2014 Business Plan v4.3", {
    x: 0.5, y: 5.2, w: 7, h: 0.28,
    fontSize: 8, color: C.textMuted, fontFace: "Calibri",
  });
  slide.addText(`${pageNum} / ${total}`, {
    x: 8.5, y: 5.2, w: 1, h: 0.28,
    fontSize: 8, color: C.textMuted, fontFace: "Calibri", align: "right",
  });
}

// ============================================================
// SECTION TITLE (top of regular slides)
// ============================================================
function addSectionTitle(slide, title, subtitle, y) {
  const yy = y || 0.35;
  slide.addText(title, {
    x: 0.6, y: yy, w: 8.8, h: 0.5, margin: 0,
    fontSize: 28, fontFace: "Trebuchet MS", bold: true, color: C.white,
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.6, y: yy + 0.5, w: 8.8, h: 0.35, margin: 0,
      fontSize: 13, fontFace: "Calibri", color: C.textSec,
    });
  }
}

// ============================================================
// CARD & ACCENT BAR
// ============================================================
function addCard(pres, slide, x, y, w, h, fillColor) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: fillColor || C.bgCard },
    shadow: makeShadow(),
  });
}

function addAccentBar(pres, slide, x, y, h, color) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 0.06, h,
    fill: { color: color || C.accent },
  });
}

// ============================================================
// SECTION DIVIDER SLIDE
// ============================================================
function addSectionDivider(pres, slide, sectionLabel, title, subtitle) {
  slide.background = { color: C.bg };

  // Full-width accent bar top
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.accent },
  });
  // Full-width accent bar bottom
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.545, w: 10, h: 0.08, fill: { color: C.accent },
  });

  // Section label pill
  if (sectionLabel) {
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: 1.55, w: 2.0, h: 0.4, fill: { color: C.accent },
    });
    slide.addText(sectionLabel, {
      x: 0.6, y: 1.55, w: 2.0, h: 0.4, margin: 0,
      fontSize: 11, fontFace: "Calibri", bold: true, color: C.bg,
      charSpacing: 3, align: "center", valign: "middle",
    });
  }

  // Big title
  slide.addText(title, {
    x: 0.6, y: 2.1, w: 8.8, h: 1.0, margin: 0,
    fontSize: 36, fontFace: "Trebuchet MS", bold: true, color: C.white,
  });

  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.6, y: 3.15, w: 8.8, h: 0.6, margin: 0,
      fontSize: 16, fontFace: "Calibri", color: C.textSec, italic: true,
    });
  }
}

// ============================================================
// TABLE ROW OPTION FACTORY
// ============================================================
function rowOpt(bg, color) {
  return { color: color || C.textPri, fill: { color: bg }, fontSize: 11, fontFace: "Calibri" };
}

function headOpt() {
  return { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 12, fontFace: "Calibri" };
}

// ============================================================
// MAIN BUILD FUNCTION
// ============================================================
async function build() {
  // ── Pre-render icon set ──────────────────────────────────
  const icons = {
    clock:     await iconB64(FaClock,       "#00B4D8"),
    userSlash: await iconB64(FaUserSlash,   "#EF476F"),
    eyeSlash:  await iconB64(FaEyeSlash,    "#FFD166"),
    money:     await iconB64(FaMoneyBillWave, "#06D6A0"),
    heart:     await iconB64(FaHeartBroken, "#EF476F"),
    equals:    await iconB64(FaEquals,      "#718096"),
    users:     await iconB64(FaUsers,       "#06D6A0"),
    chart:     await iconB64(FaChartLine,   "#00B4D8"),
    rocket:    await iconB64(FaRocket,      "#FFD166"),
    globe:     await iconB64(FaGlobeEurope, "#F4A261"),
    check:     await iconB64(FaCheckCircle, "#06D6A0"),
    dumbbell:  await iconB64(FaDumbbell,    "#00B4D8"),
    shield:    await iconB64(FaShieldAlt,   "#FFD166"),
    utensils:  await iconB64(FaUtensils,    "#F4A261"),
    invoice:   await iconB64(FaFileInvoiceDollar, "#EF476F"),
    desktop:   await iconB64(FaDesktop,    "#00B4D8"),
    grad:      await iconB64(FaGraduationCap, "#06D6A0"),
    comments:  await iconB64(FaComments,   "#FFD166"),
    wrench:    await iconB64(FaWrench,     "#F4A261"),
    microscope:await iconB64(FaMicroscope, "#06D6A0"),
    balance:   await iconB64(FaBalanceScale,"#FFD166"),
    whatsapp:  await iconB64(FaWhatsapp,   "#25D366"),
    mobile:    await iconB64(FaMobileAlt,  "#00B4D8"),
    clipboard: await iconB64(FaClipboardCheck, "#06D6A0"),
    search:    await iconB64(FaSearchPlus, "#FFD166"),
    heartFull: await iconB64(FaHeart,      "#EF476F"),
    laptop:    await iconB64(FaLaptop,     "#00B4D8"),
    box:       await iconB64(FaBoxOpen,    "#F4A261"),
    link:      await iconB64(FaLink,       "#00B4D8"),
    bullhorn:  await iconB64(FaBullhorn,   "#FFD166"),
    handshake: await iconB64(FaHandshake,  "#06D6A0"),
    news:      await iconB64(FaRegNewspaper,"#A0AEC0"),
    tag:       await iconB64(FaTag,        "#F4A261"),
    bolt:      await iconB64(FaBolt,       "#FFD166"),
    code:      await iconB64(FaCode,       "#00B4D8"),
    star:      await iconB64(FaStar,       "#FFD166"),
    arrow:     await iconB64(FaArrowRight, "#06D6A0"),
    warning:   await iconB64(FaExclamationTriangle, "#EF476F"),
    lock:      await iconB64(FaLock,       "#A0AEC0"),
    ship:      await iconB64(FaShip,       "#00B4D8"),
    brain:     await iconB64(FaBrain,      "#06D6A0"),
  };

  // ── Presentation setup ───────────────────────────────────
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Giacomo Verardo";
  pres.title = "FitManager Studio+ — Business Plan v4.3";
  pres.subject = "Business Plan Confidenziale";

  const TOTAL = 58;

  // ============================================================
  // SLIDE 1 — COPERTINA (no footer)
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };

    // Decorative corner accents — top-right
    s.addShape(pres.shapes.RECTANGLE, {
      x: 7.5, y: 0, w: 2.5, h: 0.12, fill: { color: C.accent },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 9.88, y: 0, w: 0.12, h: 2.5, fill: { color: C.accent },
    });
    // bottom-left
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 5.5, w: 2.5, h: 0.12, fill: { color: C.accent },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 3.12, w: 0.12, h: 2.5, fill: { color: C.accent },
    });

    // Top label
    s.addText("BUSINESS PLAN", {
      x: 0.8, y: 0.9, w: 8.4, h: 0.4, margin: 0,
      fontSize: 12, fontFace: "Calibri", color: C.accent, charSpacing: 6, bold: true,
    });

    // Main title
    s.addText([
      { text: "FitManager", options: { fontSize: 42, bold: true, color: C.white, fontFace: "Trebuchet MS", breakLine: false } },
      { text: " ", options: { fontSize: 42, fontFace: "Trebuchet MS" } },
      { text: "Studio+", options: { fontSize: 42, bold: true, color: C.accent, fontFace: "Trebuchet MS" } },
    ], { x: 0.8, y: 1.5, w: 8.4, h: 1.1, margin: 0 });

    // Tagline
    s.addText("Il sistema completo per il Personal Trainer Evoluto", {
      x: 0.8, y: 2.65, w: 8.4, h: 0.45, margin: 0,
      fontSize: 18, fontFace: "Calibri", color: C.textSec, italic: true,
    });

    // Separator
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.8, y: 3.25, w: 3.5, h: 0.03, fill: { color: C.accent },
    });

    // Version + author
    s.addText("Versione 4.3 \u2014 27 marzo 2026", {
      x: 0.8, y: 3.5, w: 8.4, h: 0.3, margin: 0,
      fontSize: 11, fontFace: "Calibri", color: C.textSec,
    });
    s.addText("Giacomo Verardo  |  Confidenziale", {
      x: 0.8, y: 3.82, w: 8.4, h: 0.3, margin: 0,
      fontSize: 11, fontFace: "Calibri", color: C.textMuted,
    });
  }

  // ============================================================
  // SLIDE 2 — GUIDA ALLA LETTURA
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Guida alla lettura", "Come leggere questo documento");
    addFooter(s, 2, TOTAL);

    const items = [
      { title: "Fonte di verit\u00E0", desc: "Tutti i numeri qui. Ogni altro documento (Strategy Plan, Financial Model, Partner Deck) deriva da questo." },
      { title: "Numeri tracciabili", desc: "Ogni numero tracciabile a un'assunzione dichiarata (Appendice A4). Zero magie, zero gonfiature." },
      { title: "Bottom-up", desc: "Proiezioni costruite dalla capacit\u00E0 reale di generare vendite, non da TAM top-down." },
      { title: "Tre scenari", desc: "Conservativo, base, ottimistico \u2014 la gamma completa. Non solo il caso felice." },
      { title: "Due configurazioni", desc: "Con e senza Industry Partner \u2014 il business sta in piedi in entrambi i casi." },
    ];

    const colors = [C.accent, C.accent2, C.gold, C.orange, C.red];
    items.forEach((it, i) => {
      const cy = 1.1 + i * 0.82;
      addCard(pres, s, 0.6, cy, 8.8, 0.72);
      addAccentBar(pres, s, 0.6, cy, 0.72, colors[i]);
      s.addText(it.title, {
        x: 0.85, y: cy + 0.06, w: 8.3, h: 0.28, margin: 0,
        fontSize: 13, fontFace: "Calibri", bold: true, color: C.white,
      });
      s.addText(it.desc, {
        x: 0.85, y: cy + 0.36, w: 8.3, h: 0.3, margin: 0,
        fontSize: 10.5, fontFace: "Calibri", color: C.textSec,
      });
    });
  }

  // ============================================================
  // SLIDE 3 — EXECUTIVE SUMMARY
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };

    // Section label
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: 0.32, w: 1.6, h: 0.32, fill: { color: C.accent },
    });
    s.addText("SEZIONE 1", {
      x: 0.6, y: 0.32, w: 1.6, h: 0.32, margin: 0,
      fontSize: 10, fontFace: "Calibri", bold: true, color: C.bg,
      charSpacing: 2, align: "center", valign: "middle",
    });
    addSectionTitle(s, "Executive Summary", null, 0.75);
    addFooter(s, 3, TOTAL);

    // Body paragraph
    addCard(pres, s, 0.6, 1.4, 8.8, 1.0, C.bgCard2);
    s.addText("FitManager Studio+ \u00E8 un sistema completo \u2014 software e dispositivo dedicato \u2014 che permette al personal trainer di gestire clienti, schede, pagamenti e anamnesi, con la scienza integrata e i dati locali. Si compra una volta. Non si paga ogni mese.", {
      x: 0.8, y: 1.48, w: 8.4, h: 0.85, margin: 0,
      fontSize: 13, fontFace: "Calibri", color: C.textSec,
    });

    // 4 stat boxes 2×2
    const stats = [
      { val: "Prodotto completo v1.0.5", lbl: "In uso quotidiano da una chinesiologia di Genova", color: C.accent },
      { val: "100K+ professionisti", lbl: "Personal trainer e chinesiologi in Italia", color: C.accent2 },
      { val: "POC strutturata 10/90gg", lbl: "10 Fondatori selezionati, validazione 90 giorni", color: C.gold },
      { val: "Zero debito", lbl: "Bootstrap. Nessun capitale bruciato. Prodotto gi\u00E0 vendibile.", color: C.orange },
    ];
    const gx = 0.6, gy = 2.55, cw = 4.25, ch = 1.05, gap = 0.3;
    stats.forEach((st, i) => {
      const col = i % 2, row = Math.floor(i / 2);
      const cx = gx + col * (cw + gap);
      const cy = gy + row * (ch + 0.15);
      addCard(pres, s, cx, cy, cw, ch);
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: cy, w: cw, h: 0.05, fill: { color: st.color },
      });
      s.addText(st.val, {
        x: cx + 0.15, y: cy + 0.1, w: cw - 0.3, h: 0.4, margin: 0,
        fontSize: 15, fontFace: "Trebuchet MS", bold: true, color: st.color,
      });
      s.addText(st.lbl, {
        x: cx + 0.15, y: cy + 0.52, w: cw - 0.3, h: 0.45, margin: 0,
        fontSize: 10, fontFace: "Calibri", color: C.textSec,
      });
    });

    // Footer note
    addCard(pres, s, 0.6, 4.9, 8.8, 0.42, "1E2D45");
    s.addText("Si compra una volta, non si paga ogni mese. Stiamo cercando un Industry Partner per accelerare il go-to-market.", {
      x: 0.8, y: 4.95, w: 8.4, h: 0.32, margin: 0,
      fontSize: 11, fontFace: "Calibri", bold: true, color: C.gold,
    });
  }

  // ============================================================
  // SLIDE 4 — SECTION DIVIDER: IL PROBLEMA
  // ============================================================
  {
    const s = pres.addSlide();
    addSectionDivider(pres, s, "SEZIONE 2", "Il problema", "Ogni personal trainer in Italia conosce questa storia");
    addFooter(s, 4, TOTAL);
  }

  // ============================================================
  // SLIDE 5 — LA STORIA DI MARCO
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "La storia di Marco", "Una storia vera \u2014 con variazioni di nome");
    addFooter(s, 5, TOTAL);

    addCard(pres, s, 0.6, 1.15, 8.8, 2.6, C.bgCard2);
    addAccentBar(pres, s, 0.6, 1.15, 2.6, C.textMuted);

    s.addText("\u201CMarco ha 32 clienti. Gestisce le anamnesi su fogli Word, le schede su PDF, i pagamenti su un foglio Excel. Ogni luned\u00EC perde due ore a ricostruire chi ha pagato e chi no. Un mese fa ha dimenticato che un cliente aveva un\u2019ernia lombare e gli ha assegnato stacchi da terra. Il cliente non \u00E8 tornato.\u201D", {
      x: 0.85, y: 1.28, w: 8.3, h: 2.3, margin: 0,
      fontSize: 15, fontFace: "Calibri", color: C.textPri, italic: true,
    });

    // Callout
    addCard(pres, s, 0.6, 3.95, 8.8, 0.75, C.red + "22");
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: 3.95, w: 8.8, h: 0.05, fill: { color: C.red },
    });
    s.addText("Marco non \u00E8 un caso isolato. \u00C8 la norma.", {
      x: 0.8, y: 4.05, w: 8.4, h: 0.55, margin: 0,
      fontSize: 18, fontFace: "Trebuchet MS", bold: true, color: C.red, align: "center", valign: "middle",
    });
  }

  // ============================================================
  // SLIDE 6 — I 6 PROBLEMI
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "I 6 problemi strutturali", "Perch\u00E9 il professionista fitness fatica a scalare");
    addFooter(s, 6, TOTAL);

    const problems = [
      { icon: icons.clock,    title: "Ore perse in admin",         desc: "3-5 ore/settimana in lavoro che non genera valore diretto.", color: C.accent },
      { icon: icons.userSlash,title: "Tetto ai clienti",           desc: "Oltre 25-30 clienti il sistema informale crolla.", color: C.red },
      { icon: icons.eyeSlash, title: "Nessuna visione unificata",  desc: "Anamnesi, schede, pagamenti sparsi in strumenti diversi.", color: C.gold },
      { icon: icons.money,    title: "Contabilit\u00E0 dispersa",   desc: "Rate dimenticate, nessun report finanziario, zero previsioni.", color: C.accent2 },
      { icon: icons.warning,  title: "Rischio errori clinici",     desc: "Condizioni patologiche dimenticate o ignorate nelle schede.", color: C.orange },
      { icon: icons.equals,   title: "Impossibilit\u00E0 di differenziarsi", desc: "Senza dati strutturati, tutti offrono lo stesso servizio.", color: C.textMuted },
    ];

    const gx = 0.6, gy = 1.2, cw = 2.9, ch = 1.3, gapX = 0.2, gapY = 0.18;
    problems.forEach((p, i) => {
      const col = i % 3, row = Math.floor(i / 3);
      const cx = gx + col * (cw + gapX);
      const cy = gy + row * (ch + gapY);
      addCard(pres, s, cx, cy, cw, ch);
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: cy, w: cw, h: 0.05, fill: { color: p.color },
      });
      s.addImage({ data: p.icon, x: cx + 0.15, y: cy + 0.14, w: 0.36, h: 0.36 });
      s.addText(p.title, {
        x: cx + 0.6, y: cy + 0.1, w: cw - 0.75, h: 0.35, margin: 0,
        fontSize: 12, fontFace: "Calibri", bold: true, color: C.white,
      });
      s.addText(p.desc, {
        x: cx + 0.15, y: cy + 0.55, w: cw - 0.3, h: 0.65, margin: 0,
        fontSize: 10, fontFace: "Calibri", color: C.textSec,
      });
    });
  }

  // ============================================================
  // SLIDE 7 — IL COMPETITOR VERO
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Il competitor vero", "Non \u00E8 un altro software");
    addFooter(s, 7, TOTAL);

    // Big italic quote
    addCard(pres, s, 0.6, 1.15, 8.8, 1.5, C.bgCard2);
    addAccentBar(pres, s, 0.6, 1.15, 1.5, C.textMuted);
    s.addText("\u201CNon \u00E8 un altro software. \u00C8 l\u2019abitudine.\u201D", {
      x: 0.85, y: 1.25, w: 8.3, h: 0.7, margin: 0,
      fontSize: 22, fontFace: "Trebuchet MS", bold: true, color: C.white, italic: true,
    });
    s.addText("Il trainer usa WhatsApp ed Excel perch\u00E9 \u2018ha sempre fatto cos\u00EC\u2019 e perch\u00E9 nessuno gli ha dimostrato che esiste un\u2019alternativa migliore \u2014 senza costare un abbonamento mensile.", {
      x: 0.85, y: 1.98, w: 8.3, h: 0.6, margin: 0,
      fontSize: 12, fontFace: "Calibri", color: C.textSec,
    });

    // Key insight card
    addCard(pres, s, 0.6, 2.9, 8.8, 0.95, "1E2D45");
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: 2.9, w: 8.8, h: 0.05, fill: { color: C.accent2 },
    });
    s.addText("La soluzione giusta non sostituisce WhatsApp \u2014 lo potenzia.", {
      x: 0.8, y: 2.98, w: 8.4, h: 0.72, margin: 0,
      fontSize: 18, fontFace: "Trebuchet MS", bold: true, color: C.accent2, align: "center", valign: "middle",
    });

    // 3 implications
    const implications = [
      "La funzionalit\u00E0 WhatsApp semi-automatico \u00E8 il punto di conversione emotiva nella demo.",
      "Il primo cliente non deve \u201Ccambiare tutto\u201D \u2014 parte dai contratti o dai pagamenti.",
      "Il cambio di abitudine \u00E8 graduale e guidato \u2014 non imposto.",
    ];
    implications.forEach((txt, i) => {
      s.addText([{ text: txt, options: { bullet: true, fontSize: 11, fontFace: "Calibri", color: C.textSec } }], {
        x: 0.8, y: 4.0 + i * 0.3, w: 8.4, h: 0.28, margin: 0,
      });
    });
  }

  // ============================================================
  // SLIDE 8 — SECTION DIVIDER: LA SOLUZIONE
  // ============================================================
  {
    const s = pres.addSlide();
    addSectionDivider(pres, s, "SEZIONE 3", "La soluzione", "Un sistema completo: software + dispositivo dedicato\nSi compra una volta, non si paga ogni mese.");
    addFooter(s, 8, TOTAL);
  }

  // ============================================================
  // SLIDE 9 — IL SOFTWARE (feature grid)
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };

    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: 0.32, w: 2.4, h: 0.32, fill: { color: C.accent },
    });
    s.addText("SEZIONE 3 \u2014 IL SOFTWARE", {
      x: 0.6, y: 0.32, w: 2.4, h: 0.32, margin: 0,
      fontSize: 9, fontFace: "Calibri", bold: true, color: C.bg,
      charSpacing: 1, align: "center", valign: "middle",
    });
    addSectionTitle(s, "Il software", "Un CRM operativo costruito per la professione fitness", 0.75);
    addFooter(s, 9, TOTAL);

    const features = [
      { icon: icons.users,     title: "Gestione clienti e contratti", desc: "Anagrafica, contratti, scadenze, storico completo. Profilo cliente operativo.", color: C.accent },
      { icon: icons.dumbbell,  title: "Schede di allenamento",        desc: "500 esercizi con progressioni, regressioni e varianti. Builder drag-and-drop.", color: C.accent2 },
      { icon: icons.shield,    title: "Protezione errori clinici",    desc: "Safety Engine: 47 condizioni, 80 regole automatiche. Alert in tempo reale.", color: C.gold },
      { icon: icons.utensils,  title: "Nutrizione italiana",          desc: "880 alimenti CREA 2019. Piani alimentari LARN settimanali con scoring 3 assi.", color: C.orange },
      { icon: icons.clipboard, title: "Anamnesi strutturata",         desc: "6 passaggi guidati. Compilazione dal telefono del cliente \u2014 zero app.", color: C.accent },
      { icon: icons.invoice,   title: "Pagamenti e cassa",            desc: "Rate, pagamenti, stato finanziario real-time. Break-even sempre sotto controllo.", color: C.red },
    ];

    const gx = 0.6, gy = 1.22, cw = 2.88, ch = 1.28, gapX = 0.18, gapY = 0.16;
    features.forEach((f, i) => {
      const col = i % 3, row = Math.floor(i / 3);
      const cx = gx + col * (cw + gapX);
      const cy = gy + row * (ch + gapY);
      addCard(pres, s, cx, cy, cw, ch);
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: cy, w: cw, h: 0.05, fill: { color: f.color },
      });
      s.addImage({ data: f.icon, x: cx + 0.15, y: cy + 0.14, w: 0.34, h: 0.34 });
      s.addText(f.title, {
        x: cx + 0.6, y: cy + 0.1, w: cw - 0.75, h: 0.35, margin: 0,
        fontSize: 11.5, fontFace: "Calibri", bold: true, color: C.white,
      });
      s.addText(f.desc, {
        x: cx + 0.15, y: cy + 0.54, w: cw - 0.3, h: 0.66, margin: 0,
        fontSize: 9.5, fontFace: "Calibri", color: C.textSec,
      });
    });

    s.addText("Il database \u00E8 progettato per crescere con il contributo di professionisti del settore.", {
      x: 0.6, y: 4.98, w: 8.8, h: 0.22, margin: 0,
      fontSize: 9, fontFace: "Calibri", color: C.textMuted, italic: true,
    });
  }

  // ============================================================
  // SLIDE 10 — COMUNICAZIONE INTEGRATA
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };

    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: 0.32, w: 2.4, h: 0.32, fill: { color: C.accent },
    });
    s.addText("SEZIONE 3 \u2014 IL SOFTWARE", {
      x: 0.6, y: 0.32, w: 2.4, h: 0.32, margin: 0,
      fontSize: 9, fontFace: "Calibri", bold: true, color: C.bg,
      charSpacing: 1, align: "center", valign: "middle",
    });
    addSectionTitle(s, "Comunicazione integrata con i clienti", null, 0.75);
    addFooter(s, 10, TOTAL);

    const blocks = [
      {
        icon: icons.whatsapp,
        title: "WhatsApp semi-automatico",
        desc: "15 template pre-compilati in italiano. Un click \u2192 WhatsApp si apre con il messaggio pronto. Fire-and-forget: ogni invio si logga automaticamente nel CRM.",
        color: C.accent2,
      },
      {
        icon: icons.desktop,
        title: "Email automatiche",
        desc: "SMTP integrato. Conferme appuntamento, promemoria scadenze, invio schede PDF. Il trainer configura una volta sola.",
        color: C.accent,
      },
      {
        icon: icons.bullhorn,
        title: "Centro Comunicazioni",
        desc: "2 tab: Invia (rubrica filtrata + invio multiplo sequenziale con stepper) + Registro (timeline completa). Alert compleanni dedicato sopra la dashboard.",
        color: C.gold,
      },
    ];

    blocks.forEach((b, i) => {
      const cy = 1.22 + i * 1.1;
      addCard(pres, s, 0.6, cy, 8.8, 0.98);
      addAccentBar(pres, s, 0.6, cy, 0.98, b.color);
      s.addImage({ data: b.icon, x: 0.85, y: cy + 0.27, w: 0.38, h: 0.38 });
      s.addText(b.title, {
        x: 1.4, y: cy + 0.1, w: 7.8, h: 0.32, margin: 0,
        fontSize: 14, fontFace: "Calibri", bold: true, color: C.white,
      });
      s.addText(b.desc, {
        x: 1.4, y: cy + 0.46, w: 7.8, h: 0.46, margin: 0,
        fontSize: 10.5, fontFace: "Calibri", color: C.textSec,
      });
    });

    s.addText("Il trainer non deve cambiare il modo in cui comunica con i clienti. Il sistema si adatta a lui.", {
      x: 0.6, y: 4.6, w: 8.8, h: 0.3, margin: 0,
      fontSize: 11, fontFace: "Calibri", color: C.textMuted, italic: true,
    });
  }

  // ============================================================
  // SLIDE 11 — PORTALE ALLENAMENTO CLIENTI
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };

    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: 0.32, w: 2.4, h: 0.32, fill: { color: C.accent },
    });
    s.addText("SEZIONE 3 \u2014 IL SOFTWARE", {
      x: 0.6, y: 0.32, w: 2.4, h: 0.32, margin: 0,
      fontSize: 9, fontFace: "Calibri", bold: true, color: C.bg,
      charSpacing: 1, align: "center", valign: "middle",
    });
    addSectionTitle(s, "Portale Allenamento Clienti", "Il cliente del trainer accede dal proprio telefono \u2014 nessuna app da scaricare.", 0.75);
    addFooter(s, 11, TOTAL);

    const features = [
      { icon: icons.clipboard, title: "Sessione del giorno",          desc: "Ogni esercizio con parametri prescritti, foto di partenza e fine movimento.", color: C.accent },
      { icon: icons.check,     title: "Registrazione esecuzione",     desc: "Conferma il prescritto con un tap, modifica solo se ha fatto qualcosa di diverso.", color: C.accent2 },
      { icon: icons.heartFull, title: "Feedback sessione",            desc: "Energia, soddisfazione, difficolt\u00E0 percepita al termine della sessione.", color: C.red },
      { icon: icons.mobile,    title: "Zero app",                     desc: "Link condiviso via WhatsApp. Si apre nel browser \u2014 nessuna installazione.", color: C.gold },
    ];

    const gx = 0.6, gy = 1.28, cw = 2.17, ch = 2.75, gapX = 0.2;
    features.forEach((f, i) => {
      const cx = gx + i * (cw + gapX);
      addCard(pres, s, cx, gy, cw, ch);
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: gy, w: cw, h: 0.05, fill: { color: f.color },
      });
      s.addImage({ data: f.icon, x: cx + cw / 2 - 0.28, y: gy + 0.2, w: 0.56, h: 0.56 });
      s.addText(f.title, {
        x: cx + 0.12, y: gy + 0.88, w: cw - 0.24, h: 0.5, margin: 0,
        fontSize: 12, fontFace: "Calibri", bold: true, color: C.white, align: "center",
      });
      s.addText(f.desc, {
        x: cx + 0.12, y: gy + 1.42, w: cw - 0.24, h: 1.15, margin: 0,
        fontSize: 10, fontFace: "Calibri", color: C.textSec, align: "center",
      });
    });
  }

  // ============================================================
  // SLIDE 12 — WORKOUT INTELLIGENCE
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };

    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: 0.32, w: 2.4, h: 0.32, fill: { color: C.accent },
    });
    s.addText("SEZIONE 3 \u2014 IL SOFTWARE", {
      x: 0.6, y: 0.32, w: 2.4, h: 0.32, margin: 0,
      fontSize: 9, fontFace: "Calibri", bold: true, color: C.bg,
      charSpacing: 1, align: "center", valign: "middle",
    });
    addSectionTitle(s, "Workout Intelligence", "Nessun competitor al mondo offre questo livello di analisi.", 0.75);
    addFooter(s, 12, TOTAL);

    // Diff table
    const tHead = [
      { text: "Esercizio", options: { ...headOpt() } },
      { text: "Piano", options: { ...headOpt() } },
      { text: "Fatto", options: { ...headOpt() } },
      { text: "Delta", options: { ...headOpt() } },
    ];
    const diffRows = [
      [
        { text: "Panca Piana", options: rowOpt(C.tableRow1) },
        { text: "4\u00d710 @60kg", options: rowOpt(C.tableRow1) },
        { text: "3\u00d78 @55kg", options: rowOpt(C.tableRow1) },
        { text: "\u22121s \u22122r \u22125kg \u2193", options: { ...rowOpt(C.tableRow1), color: C.red, bold: true } },
      ],
      [
        { text: "Squat", options: rowOpt(C.tableRow2) },
        { text: "4\u00d78 @80kg", options: rowOpt(C.tableRow2) },
        { text: "4\u00d710 @80kg", options: rowOpt(C.tableRow2) },
        { text: "0s +2r 0kg \u2191", options: { ...rowOpt(C.tableRow2), color: C.accent2, bold: true } },
      ],
      [
        { text: "Lat Machine", options: rowOpt(C.tableRow1) },
        { text: "3\u00d712 @40kg", options: rowOpt(C.tableRow1) },
        { text: "3\u00d712 @40kg", options: rowOpt(C.tableRow1) },
        { text: "in linea =", options: { ...rowOpt(C.tableRow1), color: C.accent, bold: true } },
      ],
    ];
    s.addTable([tHead, ...diffRows], {
      x: 0.6, y: 1.2, w: 8.8,
      colW: [2.5, 2.0, 2.0, 2.3],
      border: { type: "solid", pt: 0.5, color: C.border },
      rowH: [0.35, 0.33, 0.33, 0.33],
    });

    // Analysis cards
    const cards = [
      { title: "Compliance per sessione", desc: "Il PT vede immediatamente l\u2019aderenza al prescritto. Identifica trend di sotto-prestazione prima che diventino problemi.", color: C.accent },
      { title: "Dose-Response per muscolo", desc: "Volume effettivo vs target MEV/MAV/MRV personalizzati. Verifica scientifica del carico ogni seduta.", color: C.accent2 },
      { title: "Equilibrio biomeccanico", desc: "5 rapporti scientifici calcolati: Push:Pull, Quad:Ham, Abd:Add, Ant:Post, Dom:NonDom.", color: C.gold },
    ];
    const gx2 = 0.6, gy2 = 2.9, cw2 = 2.85, gapX2 = 0.225;
    cards.forEach((c, i) => {
      const cx = gx2 + i * (cw2 + gapX2);
      addCard(pres, s, cx, gy2, cw2, 1.9);
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: gy2, w: cw2, h: 0.05, fill: { color: c.color },
      });
      s.addText(c.title, {
        x: cx + 0.15, y: gy2 + 0.1, w: cw2 - 0.3, h: 0.42, margin: 0,
        fontSize: 12, fontFace: "Calibri", bold: true, color: C.white,
      });
      s.addText(c.desc, {
        x: cx + 0.15, y: gy2 + 0.58, w: cw2 - 0.3, h: 1.2, margin: 0,
        fontSize: 10, fontFace: "Calibri", color: C.textSec,
      });
    });
  }

  // ============================================================
  // SLIDE 13 — FITMANAGER BOX
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };

    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: 0.32, w: 2.55, h: 0.32, fill: { color: C.orange },
    });
    s.addText("SEZIONE 3 \u2014 FITMANAGER BOX", {
      x: 0.6, y: 0.32, w: 2.55, h: 0.32, margin: 0,
      fontSize: 9, fontFace: "Calibri", bold: true, color: C.bg,
      charSpacing: 1, align: "center", valign: "middle",
    });
    addSectionTitle(s, "La FitManager Box", "Lo attacca alla corrente e al WiFi \u2014 fine.", 0.75);
    addFooter(s, 13, TOTAL);

    // Specs on left
    addCard(pres, s, 0.6, 1.25, 5.2, 3.5);
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: 1.25, w: 5.2, h: 0.05, fill: { color: C.orange },
    });
    s.addText("Specifiche tecniche", {
      x: 0.8, y: 1.35, w: 4.8, h: 0.35, margin: 0,
      fontSize: 14, fontFace: "Calibri", bold: true, color: C.orange,
    });
    const specs = [
      "Raspberry Pi 5 4GB RAM",
      "SD card 64GB (OS + dati trainer)",
      "WiFi + Ethernet + Tailscale VPN",
      "Consumo: ~5W (\u20AC10/anno di corrente)",
      "Backup automatico su USB",
      "Accesso mobile via browser — nessuna app",
    ];
    const specTexts = specs.map((t, i) => ({
      text: t,
      options: { bullet: true, breakLine: i < specs.length - 1, fontSize: 11, fontFace: "Calibri", color: C.textSec, paraSpaceAfter: 6 },
    }));
    s.addText(specTexts, {
      x: 0.8, y: 1.8, w: 4.8, h: 2.7, margin: 0,
    });

    // Economics on right
    addCard(pres, s, 6.1, 1.25, 3.3, 1.6, C.bgCard2);
    s.addShape(pres.shapes.RECTANGLE, {
      x: 6.1, y: 1.25, w: 3.3, h: 0.05, fill: { color: C.accent2 },
    });
    s.addText("Economia unitaria", {
      x: 6.28, y: 1.35, w: 2.9, h: 0.3, margin: 0,
      fontSize: 13, fontFace: "Calibri", bold: true, color: C.accent2,
    });
    const econItems = [
      { label: "Costo vivo", val: "~\u20AC130-150", color: C.textSec },
      { label: "Prezzo al trainer", val: "\u20AC449", color: C.white },
      { label: "Margine lordo", val: "\u20AC299-319 (67-71%)", color: C.accent2 },
    ];
    econItems.forEach((e, i) => {
      s.addText(e.label, {
        x: 6.28, y: 1.75 + i * 0.3, w: 1.6, h: 0.28, margin: 0,
        fontSize: 11, fontFace: "Calibri", color: C.textMuted,
      });
      s.addText(e.val, {
        x: 7.9, y: 1.75 + i * 0.3, w: 1.3, h: 0.28, margin: 0,
        fontSize: 11, fontFace: "Calibri", bold: true, color: e.color, align: "right",
      });
    });

    addCard(pres, s, 6.1, 3.1, 3.3, 1.65, C.bgCard2);
    s.addShape(pres.shapes.RECTANGLE, {
      x: 6.1, y: 3.1, w: 3.3, h: 0.05, fill: { color: C.gold },
    });
    s.addText("Proposta di valore", {
      x: 6.28, y: 3.2, w: 2.9, h: 0.3, margin: 0,
      fontSize: 13, fontFace: "Calibri", bold: true, color: C.gold,
    });
    s.addText("Un piccolo dispositivo dedicato al lavoro del trainer. Sempre acceso. Sempre disponibile. I dati restano in palestra.", {
      x: 6.28, y: 3.56, w: 2.9, h: 1.05, margin: 0,
      fontSize: 10.5, fontFace: "Calibri", color: C.textSec,
    });
  }

  // ============================================================
  // SLIDE 14 — STATO DEL PRODOTTO
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Stato del prodotto", "Il prodotto \u00E8 completo e funzionante (versione 1.0.5).");
    addFooter(s, 14, TOTAL);

    addCard(pres, s, 0.6, 1.1, 8.8, 1.55, C.bgCard2);
    addAccentBar(pres, s, 0.6, 1.1, 1.55, C.accent);
    s.addText("La prima utilizzatrice reale \u2014 una chinesiologia di Genova \u2014 lo usa quotidianamente. Le sue clienti ricevono schede professionali, compilano le anamnesi dal proprio telefono e registrano l\u2019allenamento in tempo reale dal portale dedicato. Il sistema funziona. Non \u00E8 un prototipo.", {
      x: 0.85, y: 1.18, w: 8.3, h: 1.38, margin: 0,
      fontSize: 13, fontFace: "Calibri", color: C.textSec,
    });

    // 5 stat boxes in a row
    const stats = [
      { num: "47.000+", lbl: "Righe di codice", color: C.accent },
      { num: "395",     lbl: "Test automatici", color: C.accent2 },
      { num: "500",     lbl: "Esercizi con biomeccanica", color: C.gold },
      { num: "880",     lbl: "Alimenti CREA 2019", color: C.orange },
      { num: "7",       lbl: "Motori scientifici integrati", color: C.red },
    ];
    const gx = 0.6, gy = 2.85, cw = 1.68, ch = 1.5, gap = 0.2;
    stats.forEach((st, i) => {
      const cx = gx + i * (cw + gap);
      addCard(pres, s, cx, gy, cw, ch);
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: gy, w: cw, h: 0.05, fill: { color: st.color },
      });
      s.addText(st.num, {
        x: cx + 0.1, y: gy + 0.15, w: cw - 0.2, h: 0.55, margin: 0,
        fontSize: 24, fontFace: "Trebuchet MS", bold: true, color: st.color, align: "center",
      });
      s.addText(st.lbl, {
        x: cx + 0.1, y: gy + 0.75, w: cw - 0.2, h: 0.65, margin: 0,
        fontSize: 9.5, fontFace: "Calibri", color: C.textSec, align: "center",
      });
    });
  }

  // ============================================================
  // SLIDE 15 — SECTION DIVIDER: COSA LO RENDE DIVERSO
  // ============================================================
  {
    const s = pres.addSlide();
    addSectionDivider(pres, s, "SEZIONE 4", "Cosa lo rende diverso", "Non \u00E8 un altro gestionale. \u00C8 una categoria nuova.");
    addFooter(s, 15, TOTAL);
  }

  // ============================================================
  // SLIDE 16 — CONFRONTO ALTERNATIVE
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Confronto con le alternative", "Il mercato ha soluzioni parziali. FitManager le integra tutte.");
    addFooter(s, 16, TOTAL);

    const tHead = [
      { text: "Funzionalit\u00E0", options: { ...headOpt() } },
      { text: "FitManager", options: { ...headOpt(), color: C.accent } },
      { text: "Trainerize", options: { ...headOpt() } },
      { text: "MyPTHub", options: { ...headOpt() } },
      { text: "Excel+WA", options: { ...headOpt() } },
    ];
    const si = "\u2705", no = "\u274C", partial = "\u26A0";
    const rows = [
      ["CRM clienti completo",        si,      si,       si,       no],
      ["Safety Engine clinico",       si,      no,       no,       no],
      ["500 esercizi con biomeccanica",si,     partial,  partial,  no],
      ["Nutrizione italiana CREA",    si,      no,       no,       no],
      ["Dati locali (no cloud)",       si,      no,       no,       partial],
      ["Licenza perpetua",            si,      no,       no,       partial],
      ["Portale cliente zero-app",    si,      partial,  partial,  no],
      ["Workout Intelligence",        si,      no,       no,       no],
    ];
    const buildRow = (data, bg) => data.map((cell, ci) => ({
      text: cell,
      options: { ...rowOpt(bg), bold: ci === 0, color: ci === 1 ? C.accent : (ci === 0 ? C.white : C.textSec), align: ci === 0 ? "left" : "center" },
    }));
    const tableRows = rows.map((r, i) => buildRow(r, i % 2 === 0 ? C.tableRow1 : C.tableRow2));

    s.addTable([tHead, ...tableRows], {
      x: 0.6, y: 1.1, w: 8.8,
      colW: [3.0, 1.4, 1.4, 1.4, 1.6],
      border: { type: "solid", pt: 0.5, color: C.border },
      rowH: Array(9).fill(0.32),
    });
  }

  // ============================================================
  // SLIDE 17 — COSTO IN 3 ANNI
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Il costo reale in 3 anni", "Un abbonamento sembra pi\u00F9 economico \u2014 fino a quando non si calcola.");
    addFooter(s, 17, TOTAL);

    const tHead = [
      { text: "Soluzione", options: { ...headOpt() } },
      { text: "Anno 1", options: { ...headOpt() } },
      { text: "Anno 2", options: { ...headOpt() } },
      { text: "Anno 3", options: { ...headOpt() } },
      { text: "Totale 3 anni", options: { ...headOpt(), color: C.gold } },
    ];
    const costRows = [
      ["FitManager Licenza",   "\u20AC249",     "\u20AC79",     "\u20AC79",     "\u20AC407"],
      ["Trainerize Standard",  "\u20AC456",     "\u20AC456",    "\u20AC456",    "\u20AC1.368"],
      ["MyPTHub Pro",          "\u20AC600",     "\u20AC600",    "\u20AC600",    "\u20AC1.800"],
      ["Excel + Notion + WA",  "\u20AC120",     "\u20AC120",    "\u20AC120",    "\u20AC360 (+tempo)"],
    ];
    const buildCostRow = (data, bg, highlight) => data.map((cell, ci) => ({
      text: cell,
      options: {
        ...rowOpt(bg),
        bold: ci === 0 || ci === 4,
        color: ci === 0 ? (highlight ? C.accent : C.white) : (ci === 4 ? C.gold : C.textSec),
        align: ci === 0 ? "left" : "center",
      },
    }));
    const tableRows = [
      buildCostRow(costRows[0], "1E2D45", true),
      buildCostRow(costRows[1], C.tableRow2, false),
      buildCostRow(costRows[2], C.tableRow1, false),
      buildCostRow(costRows[3], C.tableRow2, false),
    ];

    s.addTable([tHead, ...tableRows], {
      x: 0.6, y: 1.1, w: 8.8,
      colW: [2.5, 1.5, 1.5, 1.5, 1.8],
      border: { type: "solid", pt: 0.5, color: C.border },
      rowH: Array(5).fill(0.42),
    });

    // Bar chart visual
    const bars = [
      { label: "FitManager", val: 407,   color: C.accent,  w: 1.48 },
      { label: "Trainerize", val: 1368,  color: C.textMuted, w: 4.96 },
      { label: "MyPTHub",    val: 1800,  color: C.textMuted, w: 6.53 },
    ];
    const barStartX = 0.6, barY = 3.3, barH = 0.38, barGap = 0.52;
    bars.forEach((b, i) => {
      const cy = barY + i * (barH + barGap);
      s.addShape(pres.shapes.RECTANGLE, {
        x: barStartX, y: cy, w: b.w, h: barH, fill: { color: b.color },
      });
      s.addText(b.label, {
        x: barStartX + b.w + 0.12, y: cy, w: 2.5, h: barH, margin: 0,
        fontSize: 11, fontFace: "Calibri", color: C.textSec, valign: "middle",
      });
      s.addText(`\u20AC${b.val.toLocaleString("it-IT")}`, {
        x: barStartX + b.w - 0.9, y: cy, w: 0.85, h: barH, margin: 0,
        fontSize: 11, fontFace: "Calibri", bold: true, color: b.color === C.accent ? C.bg : C.white, valign: "middle", align: "right",
      });
    });

    s.addText("FitManager costa ~3,4\u00d7 meno di Trainerize in 3 anni, con il doppio delle funzionalit\u00E0 e i dati in locale.", {
      x: 0.6, y: 5.05, w: 8.8, h: 0.28, margin: 0,
      fontSize: 10, fontFace: "Calibri", color: C.textMuted, italic: true,
    });
  }

  // ============================================================
  // SLIDE 18 — SECTION DIVIDER: IL MERCATO
  // ============================================================
  {
    const s = pres.addSlide();
    addSectionDivider(pres, s, "SEZIONE 5", "Il mercato", "Un mercato professionale in crescita, non ancora presidiato.");
    addFooter(s, 18, TOTAL);
  }

  // ============================================================
  // SLIDE 19 — IL MERCATO (big numbers)
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Il mercato italiano", "Professionisti fitness a Partita IVA in Italia");
    addFooter(s, 19, TOTAL);

    const bigStats = [
      { num: "100.000+", lbl: "professionisti fitness", sub: "Personal trainer, chinesiologi, istruttori P.IVA", color: C.accent },
      { num: "\u20AC3 miliardi", lbl: "mercato fitness Italia", sub: "Fatturato annuo del settore (IHRSA 2024)", color: C.gold },
      { num: "+10%", lbl: "crescita annua", sub: "Trend post-pandemia consolidato. Settore anti-ciclico.", color: C.accent2 },
    ];
    const gx = 0.6, gy = 1.35, cw = 2.85, gapX = 0.225;
    bigStats.forEach((st, i) => {
      const cx = gx + i * (cw + gapX);
      addCard(pres, s, cx, gy, cw, 2.8);
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: gy, w: cw, h: 0.06, fill: { color: st.color },
      });
      s.addText(st.num, {
        x: cx + 0.15, y: gy + 0.2, w: cw - 0.3, h: 0.9, margin: 0,
        fontSize: 28, fontFace: "Trebuchet MS", bold: true, color: st.color, align: "center",
      });
      s.addText(st.lbl, {
        x: cx + 0.15, y: gy + 1.15, w: cw - 0.3, h: 0.42, margin: 0,
        fontSize: 14, fontFace: "Calibri", bold: true, color: C.white, align: "center",
      });
      s.addText(st.sub, {
        x: cx + 0.15, y: gy + 1.6, w: cw - 0.3, h: 1.0, margin: 0,
        fontSize: 10, fontFace: "Calibri", color: C.textSec, align: "center",
      });
    });

    s.addText("Fonti: IHRSA Global Report 2024, CONI, Registro Professionisti Sportivi.", {
      x: 0.6, y: 4.95, w: 8.8, h: 0.25, margin: 0,
      fontSize: 9, fontFace: "Calibri", color: C.textMuted, italic: true,
    });
  }

  // ============================================================
  // SLIDE 20 — SEGMENTO TARGET E TREND
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Segmento target e trend", "Il sottoinsieme ad alta propensit\u00E0 all\u2019acquisto");
    addFooter(s, 20, TOTAL);

    // Left: target
    addCard(pres, s, 0.6, 1.15, 4.2, 3.65);
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: 1.15, w: 4.2, h: 0.05, fill: { color: C.accent },
    });
    s.addText("Target primario", {
      x: 0.8, y: 1.27, w: 3.8, h: 0.35, margin: 0,
      fontSize: 15, fontFace: "Calibri", bold: true, color: C.accent,
    });

    addCard(pres, s, 0.8, 1.72, 3.8, 0.85, "1E2D45");
    s.addText("10.000 \u2013 15.000", {
      x: 0.8, y: 1.78, w: 3.8, h: 0.4, margin: 0,
      fontSize: 28, fontFace: "Trebuchet MS", bold: true, color: C.accent, align: "center",
    });
    s.addText("professionisti nel segmento target", {
      x: 0.8, y: 2.22, w: 3.8, h: 0.28, margin: 0,
      fontSize: 10, fontFace: "Calibri", color: C.textSec, align: "center",
    });

    const criteria = [
      "Gi\u00E0 gestisce 10+ clienti attivi (P.IVA)",
      "Ha sperimentato Excel o app parziali",
      "Percepisce il carico admin come un problema",
    ];
    const cTexts = criteria.map((c, i) => ({
      text: c,
      options: { bullet: true, breakLine: i < criteria.length - 1, fontSize: 11, fontFace: "Calibri", color: C.textSec, paraSpaceAfter: 8 },
    }));
    s.addText(cTexts, {
      x: 0.8, y: 2.68, w: 3.8, h: 2.0, margin: 0,
    });

    // Right: trends
    addCard(pres, s, 5.1, 1.15, 4.3, 3.65);
    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.1, y: 1.15, w: 4.3, h: 0.05, fill: { color: C.gold },
    });
    s.addText("Tre trend strutturali", {
      x: 5.3, y: 1.27, w: 3.9, h: 0.35, margin: 0,
      fontSize: 15, fontFace: "Calibri", bold: true, color: C.gold,
    });
    const trends = [
      { title: "Professionalizzazione", desc: "Il PT non \u00E8 pi\u00F9 un hobbysta con fisico. Il cliente vuole competenza documentata.", color: C.gold },
      { title: "Privacy-first", desc: "GDPR applicato al fitness. I dati clinici devono restare locali, non in cloud USA.", color: C.accent2 },
      { title: "Personalizzazione", desc: "Il cliente confronta. Vuole schede su misura, non template generici.", color: C.orange },
    ];
    trends.forEach((t, i) => {
      const cy = 1.72 + i * 1.0;
      s.addText(t.title, {
        x: 5.3, y: cy, w: 3.9, h: 0.32, margin: 0,
        fontSize: 12, fontFace: "Calibri", bold: true, color: t.color,
      });
      s.addText(t.desc, {
        x: 5.3, y: cy + 0.34, w: 3.9, h: 0.52, margin: 0,
        fontSize: 10.5, fontFace: "Calibri", color: C.textSec,
      });
    });

    s.addText("Nessun prodotto combina architettura locale, scienza integrata, nutrizione italiana e modello perpetuo.", {
      x: 0.6, y: 5.02, w: 8.8, h: 0.22, margin: 0,
      fontSize: 10, fontFace: "Calibri", bold: true, color: C.accent, italic: true,
    });
  }

  // ============================================================
  // SLIDE 21 — OLTRE L'ITALIA
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Oltre l\u2019Italia", "L\u2019architettura \u00E8 gi\u00E0 pronta per l\u2019internazionale");
    addFooter(s, 21, TOTAL);

    const blocks = [
      { num: "1", title: "Interfaccia e core",         level: "BASSA",    levelColor: C.accent2, desc: "Traduzione UI, template, formati data/valuta. ~1 settimana per lingua. Blocco pronto." },
      { num: "2", title: "Esercizi e Safety Engine",   level: "MEDIA",    levelColor: C.gold,    desc: "La scienza \u00E8 universale. Serve adattamento terminologico professionale. 2-4 settimane." },
      { num: "3", title: "Nutrizione e compliance",    level: "ALTA",     levelColor: C.orange,  desc: "Database nutrizionali locali (Livsmedelsverket per Svezia, USDA per USA). 2-3 mesi." },
      { num: "4", title: "Moduli fiscali ed economici", level: "VARIABILE",levelColor: C.red,     desc: "Pagamenti, fatturazione per giurisdizione. Da definire mercato per mercato." },
    ];

    blocks.forEach((b, i) => {
      const cy = 1.2 + i * 0.92;
      addCard(pres, s, 0.6, cy, 8.8, 0.82);

      s.addShape(pres.shapes.OVAL, {
        x: 0.75, y: cy + 0.16, w: 0.5, h: 0.5, fill: { color: C.accent },
      });
      s.addText(b.num, {
        x: 0.75, y: cy + 0.16, w: 0.5, h: 0.5, margin: 0,
        fontSize: 18, fontFace: "Trebuchet MS", bold: true, color: C.bg, align: "center", valign: "middle",
      });

      s.addText(b.title, {
        x: 1.45, y: cy + 0.08, w: 5.5, h: 0.3, margin: 0,
        fontSize: 13, fontFace: "Calibri", bold: true, color: C.white,
      });
      s.addText(b.desc, {
        x: 1.45, y: cy + 0.42, w: 5.5, h: 0.34, margin: 0,
        fontSize: 10.5, fontFace: "Calibri", color: C.textSec,
      });

      addCard(pres, s, 7.8, cy + 0.2, 1.4, 0.4, b.levelColor);
      s.addText(b.level, {
        x: 7.8, y: cy + 0.2, w: 1.4, h: 0.4, margin: 0,
        fontSize: 11, fontFace: "Calibri", bold: true, color: C.bg, align: "center", valign: "middle",
      });
    });

    addCard(pres, s, 0.6, 4.9, 8.8, 0.38, C.bgCard2);
    s.addText("I Blocchi 1-2 possono essere pronti in inglese o svedese in 4-6 settimane. Il prodotto \u00E8 pienamente utilizzabile senza i Blocchi 3-4.", {
      x: 0.8, y: 4.93, w: 8.4, h: 0.32, margin: 0,
      fontSize: 10.5, fontFace: "Calibri", bold: true, color: C.accent,
    });
  }

  // ============================================================
  // SLIDE 22 — SECTION DIVIDER: MODELLO ECONOMICO
  // ============================================================
  {
    const s = pres.addSlide();
    addSectionDivider(pres, s, "SEZIONE 6", "Il modello economico", "Semplice, trasparente, sostenibile da subito.");
    addFooter(s, 22, TOTAL);
  }

  // ============================================================
  // SLIDE 23 — PRICING
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "I prodotti e il pricing", "Tre prodotti. Un principio: si compra, non si abbona.");
    addFooter(s, 23, TOTAL);

    const products = [
      {
        name: "Licenza Software",
        price: "\u20AC249",
        period: "una tantum",
        desc: "Il software completo per il PC del trainer. Tutti i moduli inclusi. Aggiornamenti a vita.",
        color: C.accent,
        badge: "PERPETUO",
      },
      {
        name: "FitManager Box",
        price: "\u20AC449",
        period: "una tantum",
        desc: "Raspberry Pi 5 preconfigurato con il software. Lo attacca. Funziona. Accesso mobile incluso.",
        color: C.orange,
        badge: "HARDWARE + SW",
      },
      {
        name: "Assistenza PRO",
        price: "\u20AC79",
        period: "anno",
        desc: "Aggiornamenti software, nuovi esercizi e alimenti, template, supporto diretto. Opzionale.",
        color: C.accent2,
        badge: "RICORRENTE",
      },
    ];

    const gx = 0.6, gy = 1.15, cw = 2.85, gapX = 0.225;
    products.forEach((p, i) => {
      const cx = gx + i * (cw + gapX);
      addCard(pres, s, cx, gy, cw, 3.4);
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: gy, w: cw, h: 0.07, fill: { color: p.color },
      });

      // Badge
      addCard(pres, s, cx + cw - 1.25, gy + 0.18, 1.15, 0.32, p.color);
      s.addText(p.badge, {
        x: cx + cw - 1.25, y: gy + 0.18, w: 1.15, h: 0.32, margin: 0,
        fontSize: 8.5, fontFace: "Calibri", bold: true, color: C.bg, align: "center", valign: "middle",
      });

      s.addText(p.name, {
        x: cx + 0.18, y: gy + 0.18, w: cw - 1.5, h: 0.35, margin: 0,
        fontSize: 14, fontFace: "Calibri", bold: true, color: C.white,
      });
      s.addText(p.price, {
        x: cx + 0.18, y: gy + 0.65, w: cw - 0.36, h: 0.8, margin: 0,
        fontSize: 42, fontFace: "Trebuchet MS", bold: true, color: p.color,
      });
      s.addText(p.period, {
        x: cx + 0.18, y: gy + 1.5, w: cw - 0.36, h: 0.3, margin: 0,
        fontSize: 12, fontFace: "Calibri", color: C.textMuted,
      });
      // Separator
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx + 0.18, y: gy + 1.88, w: cw - 0.36, h: 0.02, fill: { color: C.border },
      });
      s.addText(p.desc, {
        x: cx + 0.18, y: gy + 1.98, w: cw - 0.36, h: 1.3, margin: 0,
        fontSize: 10.5, fontFace: "Calibri", color: C.textSec,
      });
    });

    s.addText("Licenza perpetua: il trainer la compra una volta, il software \u00E8 suo. Nessun abbonamento, nessun server, nessuna dipendenza.", {
      x: 0.6, y: 4.75, w: 8.8, h: 0.3, margin: 0,
      fontSize: 11, fontFace: "Calibri", bold: true, color: C.gold, italic: true,
    });
  }

  // ============================================================
  // SLIDE 24 — MARGINI UNITARI
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Margini unitari", "Perch\u00E9 nessun server significa margini reali");
    addFooter(s, 24, TOTAL);

    const tHead = [
      { text: "Prodotto", options: { ...headOpt() } },
      { text: "Prezzo", options: { ...headOpt() } },
      { text: "Costo vivo", options: { ...headOpt() } },
      { text: "Margine lordo", options: { ...headOpt(), color: C.accent2 } },
    ];
    const marginRows = [
      ["Licenza software",  "\u20AC249",      "~\u20AC30",    "\u20AC219 (88%)"],
      ["FitManager Box",    "\u20AC449",      "~\u20AC150",   "\u20AC299 (67%)"],
      ["Assistenza PRO",    "\u20AC79/anno",  "~\u20AC0",     "\u20AC79 (100%)"],
    ];
    const buildMarginRow = (data, bg) => data.map((cell, ci) => ({
      text: cell,
      options: {
        ...rowOpt(bg),
        bold: ci === 3,
        color: ci === 3 ? C.accent2 : (ci === 0 ? C.white : C.textSec),
        align: ci === 0 ? "left" : "center",
      },
    }));
    const tableRows = [
      buildMarginRow(marginRows[0], C.tableRow1),
      buildMarginRow(marginRows[1], C.tableRow2),
      buildMarginRow(marginRows[2], C.tableRow1),
    ];

    s.addTable([tHead, ...tableRows], {
      x: 0.6, y: 1.1, w: 8.8,
      colW: [3.0, 1.8, 1.8, 2.2],
      border: { type: "solid", pt: 0.5, color: C.border },
      rowH: Array(4).fill(0.48),
    });

    // Key insight
    addCard(pres, s, 0.6, 3.2, 8.8, 0.8, "1E2D45");
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: 3.2, w: 8.8, h: 0.05, fill: { color: C.accent2 },
    });
    s.addText("Nessun costo server. I dati sono locali. Ogni vendita porta un margine reale immediato \u2014 non un margine virtuale dopo payback.", {
      x: 0.8, y: 3.3, w: 8.4, h: 0.6, margin: 0,
      fontSize: 13, fontFace: "Calibri", bold: true, color: C.accent2,
    });

    // Community tiers note
    addCard(pres, s, 0.6, 4.15, 8.8, 1.05);
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: 4.15, w: 8.8, h: 0.05, fill: { color: C.gold },
    });
    s.addText("Livelli community (post-lancio)", {
      x: 0.8, y: 4.25, w: 8.4, h: 0.3, margin: 0,
      fontSize: 12, fontFace: "Calibri", bold: true, color: C.gold,
    });
    s.addText([
      { text: "Base (gratuita)", options: { bold: true, color: C.white } },
      { text: "  \u2192  ", options: { color: C.textMuted } },
      { text: "PRO \u20AC79/anno", options: { bold: true, color: C.accent2 } },
      { text: "  \u2192  ", options: { color: C.textMuted } },
      { text: "Inner Circle \u20AC249/anno", options: { bold: true, color: C.gold } },
      { text: "  \u2192  ", options: { color: C.textMuted } },
      { text: "Mentorship \u20AC499-599/anno (Anno 3+)", options: { bold: true, color: C.orange } },
    ], {
      x: 0.8, y: 4.62, w: 8.4, h: 0.48, margin: 0,
      fontSize: 11, fontFace: "Calibri",
    });
  }

  // ============================================================
  // SLIDE 25 — BREAK-EVEN
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Break-even operativo", "Il business \u00E8 sostenibile con numeri piccoli");
    addFooter(s, 25, TOTAL);

    // Big "3" center
    addCard(pres, s, 3.5, 1.1, 3.0, 2.0, "1E2D45");
    s.addShape(pres.shapes.RECTANGLE, {
      x: 3.5, y: 1.1, w: 3.0, h: 0.06, fill: { color: C.accent2 },
    });
    s.addText("3", {
      x: 3.5, y: 1.2, w: 3.0, h: 1.2, margin: 0,
      fontSize: 96, fontFace: "Trebuchet MS", bold: true, color: C.accent2, align: "center", valign: "middle",
    });
    s.addText("vendite/mese per il break-even operativo", {
      x: 3.5, y: 2.32, w: 3.0, h: 0.6, margin: 0,
      fontSize: 11, fontFace: "Calibri", color: C.textSec, align: "center",
    });

    // 4 stat boxes
    const stats = [
      { val: "~\u20AC360/mese", lbl: "Costi fissi (SRL + dominio + tool)", color: C.red },
      { val: "~\u20AC220", lbl: "Margine medio per vendita (mix)", color: C.accent },
      { val: "1,7 vendite", lbl: "BE puramente operativo", color: C.accent2 },
      { val: "3/mese", lbl: "BE reale includendo imprevistos", color: C.gold },
    ];
    const gx = 0.6, gy = 3.35, cw = 2.05, gapX = 0.22;
    stats.forEach((st, i) => {
      const cx = gx + i * (cw + gapX);
      addCard(pres, s, cx, gy, cw, 1.32);
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: gy, w: cw, h: 0.05, fill: { color: st.color },
      });
      s.addText(st.val, {
        x: cx + 0.1, y: gy + 0.12, w: cw - 0.2, h: 0.55, margin: 0,
        fontSize: 18, fontFace: "Trebuchet MS", bold: true, color: st.color, align: "center",
      });
      s.addText(st.lbl, {
        x: cx + 0.1, y: gy + 0.7, w: cw - 0.2, h: 0.55, margin: 0,
        fontSize: 9.5, fontFace: "Calibri", color: C.textSec, align: "center",
      });
    });

    s.addText("Se raggiungiamo stabilmente 3 vendite/mese dal mese 5-6, il business \u00E8 sostenibile. Dal mese 12, redditizio.", {
      x: 0.6, y: 4.88, w: 8.8, h: 0.28, margin: 0,
      fontSize: 10.5, fontFace: "Calibri", color: C.textMuted, italic: true,
    });
  }

  // ============================================================
  // SLIDE 26 — SECTION DIVIDER: GO-TO-MARKET
  // ============================================================
  {
    const s = pres.addSlide();
    addSectionDivider(pres, s, "SEZIONE 7", "Come arriviamo ai clienti", "Fonti di lead, funnel e conversione.");
    addFooter(s, 26, TOTAL);
  }

  // ============================================================
  // SLIDE 27 — FONTI DI LEAD
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Fonti di lead qualificati", "20-33 lead/mese \u2014 realistici, non ottimistici");
    addFooter(s, 27, TOTAL);

    const sources = [
      { icon: icons.handshake, title: "Network partner",          range: "8-12/mese", desc: "Contatti diretti del fondatore e del network professionale. Alta qualit\u00E0.", color: C.accent },
      { icon: icons.link,      title: "LinkedIn founder",         range: "5-8/mese",  desc: "Contenuti settimanali su LinkedIn (Giacomo). Case study, demo clips, insight.", color: C.accent2 },
      { icon: icons.users,     title: "Referral clienti attivi",  range: "2-4/mese",  desc: "Ogni Fondatore soddisfatto porta 0,3-0,5 referral nel primo anno.", color: C.gold },
      { icon: icons.bullhorn,  title: "Webinar mensile",          range: "3-5/mese",  desc: "Demo + Q&A + caso reale. ~50-80 partecipanti, conversione 4-6%.", color: C.orange },
      { icon: icons.comments,  title: "Passaparola / community",  range: "2-4/mese",  desc: "Gruppi Facebook, Telegram e forum specializzati del settore fitness.", color: C.accent },
    ];

    sources.forEach((src, i) => {
      const cy = 1.15 + i * 0.82;
      addCard(pres, s, 0.6, cy, 7.5, 0.72);
      addAccentBar(pres, s, 0.6, cy, 0.72, src.color);
      s.addImage({ data: src.icon, x: 0.85, y: cy + 0.16, w: 0.36, h: 0.36 });
      s.addText(src.title, {
        x: 1.4, y: cy + 0.06, w: 5.8, h: 0.3, margin: 0,
        fontSize: 13, fontFace: "Calibri", bold: true, color: C.white,
      });
      s.addText(src.desc, {
        x: 1.4, y: cy + 0.4, w: 5.8, h: 0.26, margin: 0,
        fontSize: 10, fontFace: "Calibri", color: C.textSec,
      });
      addCard(pres, s, 8.25, cy + 0.15, 1.25, 0.42, src.color);
      s.addText(src.range, {
        x: 8.25, y: cy + 0.15, w: 1.25, h: 0.42, margin: 0,
        fontSize: 13, fontFace: "Trebuchet MS", bold: true, color: C.bg, align: "center", valign: "middle",
      });
    });

    addCard(pres, s, 0.6, 5.25, 8.9, 0.38, "1E2D45");
    s.addText("Totale: 20-33 lead/mese qualificati  \u2192  conversione 10-15%  \u2192  2-5 vendite/mese", {
      x: 0.8, y: 5.28, w: 8.6, h: 0.32, margin: 0,
      fontSize: 12, fontFace: "Calibri", bold: true, color: C.gold, align: "center",
    });
  }

  // ============================================================
  // SLIDE 28 — IL FUNNEL
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Il funnel di vendita", "Tre fasi. Un momento di conversione decisivo.");
    addFooter(s, 28, TOTAL);

    // Visual funnel trapezoids (simulated with stacked rectangles of decreasing width)
    const stages = [
      { label: "AWARENESS", pct: "100%", desc: "Lead entra nel funnel (LinkedIn, referral, webinar, passaparola)", color: C.accent, gy: 1.15, gx: 0.6, gw: 8.8 },
      { label: "INTERESSE",   pct: "50-60%", desc: "Vede una demo o video. Capisce il problema risolto. Si iscrive al webinar.", color: C.gold, gy: 2.1, gx: 1.4, gw: 7.2 },
      { label: "ACQUISTO",    pct: "10-15%", desc: "Prova 14 giorni o acquista diretto. Il momento WA live \u00E8 il punto di svolta.", color: C.accent2, gy: 3.05, gx: 2.6, gw: 4.8 },
    ];

    stages.forEach((st) => {
      addCard(pres, s, st.gx, st.gy, st.gw, 0.82, C.bgCard2);
      s.addShape(pres.shapes.RECTANGLE, {
        x: st.gx, y: st.gy, w: st.gw, h: 0.05, fill: { color: st.color },
      });
      s.addText(st.label, {
        x: st.gx + 0.15, y: st.gy + 0.1, w: 1.8, h: 0.3, margin: 0,
        fontSize: 11, fontFace: "Calibri", bold: true, color: st.color,
        charSpacing: 2,
      });
      s.addText(st.pct, {
        x: st.gx + 0.15, y: st.gy + 0.42, w: 1.1, h: 0.32, margin: 0,
        fontSize: 20, fontFace: "Trebuchet MS", bold: true, color: st.color,
      });
      s.addText(st.desc, {
        x: st.gx + 1.45, y: st.gy + 0.1, w: st.gw - 1.65, h: 0.65, margin: 0,
        fontSize: 11, fontFace: "Calibri", color: C.textSec, valign: "middle",
      });
    });

    // Key insight
    addCard(pres, s, 0.6, 4.1, 8.8, 0.75, "1E2D45");
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: 4.1, w: 8.8, h: 0.04, fill: { color: C.accent2 },
    });
    s.addText("\u201CLa demo include un momento WhatsApp live: il trainer vede il messaggio aprirsi sul suo telefono. Quel momento converte pi\u00F9 di qualsiasi slide.\u201D", {
      x: 0.8, y: 4.18, w: 8.4, h: 0.6, margin: 0,
      fontSize: 13, fontFace: "Calibri", italic: true, color: C.white,
    });
  }

  // ============================================================
  // SLIDE 29 — SECTION DIVIDER: MARKETING
  // ============================================================
  {
    const s = pres.addSlide();
    addSectionDivider(pres, s, "SEZIONE 8", "Strategia di marketing", "Owned first. Borrowed second. Paid solo quando ha senso.");
    addFooter(s, 29, TOTAL);
  }

  // ============================================================
  // SLIDE 30 — I TRE CANALI
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "I tre canali di marketing", "Una strategia sostenibile a zero budget iniziale");
    addFooter(s, 30, TOTAL);

    const channels = [
      {
        title: "Owned",
        sub: "Costruiamo noi",
        color: C.accent,
        items: [
          "Newsletter settimanale (audience PT)",
          "Blog / SEO su keyword fitness pro",
          "Video-pillole YouTube: demo + case study",
          "Documentazione pubblica del prodotto",
        ],
        note: "Costruisce audience permanente. ROI composto nel tempo.",
      },
      {
        title: "Borrowed",
        sub: "Distribuiamo altrui",
        color: C.gold,
        items: [
          "LinkedIn del founder (6.000+ follower target)",
          "Podcast e webinar di settore",
          "Community Facebook e Telegram PT",
          "Rete e social del partner",
        ],
        note: "Reach immediata a costo zero. Richiede contenuto autentico.",
      },
      {
        title: "Paid",
        sub: "Solo quando ha ROI",
        color: C.textMuted,
        items: [
          "Meta Ads retargeting (mese 6+)",
          "LinkedIn Sponsored solo dopo social proof",
          "Google Ads su keyword acquisto (mese 9+)",
          "Nessun paid prima della prova organica",
        ],
        note: "Solo a validazione completata. Budget iniziale: zero.",
      },
    ];

    const gx = 0.6, gy = 1.15, cw = 2.85, gapX = 0.225;
    channels.forEach((ch, i) => {
      const cx = gx + i * (cw + gapX);
      addCard(pres, s, cx, gy, cw, 3.75);
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: gy, w: cw, h: 0.06, fill: { color: ch.color },
      });
      s.addText(ch.title, {
        x: cx + 0.15, y: gy + 0.12, w: cw - 0.3, h: 0.38, margin: 0,
        fontSize: 18, fontFace: "Trebuchet MS", bold: true, color: ch.color,
      });
      s.addText(ch.sub, {
        x: cx + 0.15, y: gy + 0.52, w: cw - 0.3, h: 0.26, margin: 0,
        fontSize: 11, fontFace: "Calibri", color: C.textMuted, italic: true,
      });
      // Divider
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx + 0.15, y: gy + 0.86, w: cw - 0.3, h: 0.02, fill: { color: C.border },
      });
      const itemTexts = ch.items.map((it, j) => ({
        text: it,
        options: { bullet: true, breakLine: j < ch.items.length - 1, fontSize: 10.5, fontFace: "Calibri", color: C.textSec, paraSpaceAfter: 6 },
      }));
      s.addText(itemTexts, {
        x: cx + 0.15, y: gy + 0.98, w: cw - 0.3, h: 2.18, margin: 0,
      });
      // Note
      addCard(pres, s, cx, gy + 3.25, cw, 0.5, ch.color + "18");
      s.addText(ch.note, {
        x: cx + 0.15, y: gy + 3.3, w: cw - 0.3, h: 0.4, margin: 0,
        fontSize: 9.5, fontFace: "Calibri", color: ch.color, italic: true,
      });
    });
  }

  // === SLIDES 31-58 ===

  // ============================================================
  // SLIDE 31 — Budget marketing + asset pre-lancio
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Budget marketing Anno 1 e asset pre-lancio");
    addFooter(s, 31, TOTAL);

    // Budget table (left)
    s.addText("BUDGET", { x: 0.6, y: 1.15, w: 4.1, h: 0.3, margin: 0, fontSize: 12, fontFace: "Calibri", bold: true, color: C.accent, charSpacing: 3 });
    const budgetRows = [
      ["Dominio + hosting", "\u20AC120/anno"],
      ["Email marketing", "\u20AC0-180/anno"],
      ["Video demo/testimonial", "\u20AC0-200"],
      ["Pubblicit\u00E0 (mesi 7-12)", "\u20AC300-500"],
      ["Totale Anno 1", "\u20AC120-880"],
    ];
    const bData = budgetRows.map((r, i) => {
      const bg = i % 2 === 0 ? C.tableRow1 : C.tableRow2;
      const isTotal = i === budgetRows.length - 1;
      return [
        { text: r[0], options: { color: isTotal ? C.gold : C.textPri, fill: { color: bg }, fontSize: 11, fontFace: "Calibri", bold: isTotal } },
        { text: r[1], options: { color: isTotal ? C.gold : C.textPri, fill: { color: bg }, fontSize: 11, fontFace: "Calibri", align: "center", bold: isTotal } },
      ];
    });
    s.addTable(bData, { x: 0.6, y: 1.5, w: 4.1, colW: [2.6, 1.5], border: { type: "solid", pt: 0.5, color: C.border }, rowH: [0.35, 0.35, 0.35, 0.35, 0.38] });

    // Asset pre-lancio (right)
    s.addText("ASSET PRE-LANCIO", { x: 5.1, y: 1.15, w: 4.3, h: 0.3, margin: 0, fontSize: 12, fontFace: "Calibri", bold: true, color: C.accent2, charSpacing: 3 });
    const assetRows = [
      ["Sito web / landing page", "Da creare", "Critico"],
      ["Waiting list virale", "Da creare", "Critico"],
      ["Video demo (3 min)", "Da creare", "Alto"],
      ["Video teaser (60 sec)", "Da creare", "Alto"],
      ["Screenshot professionali", "Da creare", "Medio"],
      ["Profilo LinkedIn attivo", "Parziale", "Alto"],
    ];
    const aData = assetRows.map((r, i) => {
      const bg = i % 2 === 0 ? C.tableRow1 : C.tableRow2;
      const pColor = r[2] === "Critico" ? C.red : r[2] === "Alto" ? C.gold : C.textSec;
      return [
        { text: r[0], options: { color: C.textPri, fill: { color: bg }, fontSize: 10, fontFace: "Calibri" } },
        { text: r[1], options: { color: C.textSec, fill: { color: bg }, fontSize: 10, fontFace: "Calibri", align: "center" } },
        { text: r[2], options: { color: pColor, fill: { color: bg }, fontSize: 10, fontFace: "Calibri", align: "center", bold: true } },
      ];
    });
    s.addTable(aData, { x: 5.1, y: 1.5, w: 4.3, colW: [2.0, 1.1, 1.2], border: { type: "solid", pt: 0.5, color: C.border }, rowH: [0.33, 0.33, 0.33, 0.33, 0.33, 0.33] });

    // Viral marketing
    addCard(pres, s, 0.6, 3.9, 8.8, 0.7, C.bgCard2);
    addAccentBar(pres, s, 0.6, 3.9, 0.7, C.accent2);
    s.addText("MARKETING VIRALE NEL PRODOTTO", { x: 0.85, y: 3.95, w: 8.35, h: 0.22, margin: 0, fontSize: 10, fontFace: "Calibri", bold: true, color: C.accent2 });
    s.addText("Ogni volta che un trainer invia il link anamnesi, il cliente vede \"Powered by FitManager Studio+\" nel footer. Con 30 trainer attivi e 20 clienti ciascuno = 600+ esposizioni/mese a costo zero.", {
      x: 0.85, y: 4.2, w: 8.35, h: 0.35, margin: 0, fontSize: 10.5, fontFace: "Calibri", color: C.textSec,
    });
  }

  // ============================================================
  // SLIDE 32 — Risultati attesi per fase
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Risultati attesi per fase");
    addFooter(s, 32, TOTAL);

    const phases = [
      { period: "Pre-lancio", time: "4 sett. prima POC", leads: "50+ iscritti waiting list", sales: "0", color: C.textMuted },
      { period: "POC", time: "Mesi 1-3", leads: "Focus 10 Fondatori", sales: "10 (selezionati)", color: C.accent },
      { period: "Early Adopter", time: "Mesi 4-6", leads: "15-25/mese", sales: "2-3/mese", color: C.accent2 },
      { period: "Prezzo pieno", time: "Mesi 7-12", leads: "22-35/mese", sales: "3-5/mese", color: C.gold },
    ];
    phases.forEach((p, i) => {
      const cy = 1.15 + i * 1.0;
      addCard(pres, s, 0.6, cy, 8.8, 0.88);
      addAccentBar(pres, s, 0.6, cy, 0.88, p.color);
      s.addText(p.period, { x: 0.85, y: cy + 0.08, w: 2, h: 0.3, margin: 0, fontSize: 14, fontFace: "Trebuchet MS", bold: true, color: p.color });
      s.addText(p.time, { x: 0.85, y: cy + 0.4, w: 2, h: 0.25, margin: 0, fontSize: 10, fontFace: "Calibri", color: C.textMuted });
      s.addText("Lead: " + p.leads, { x: 3.2, y: cy + 0.15, w: 3, h: 0.25, margin: 0, fontSize: 11, fontFace: "Calibri", color: C.textSec });
      s.addText("Vendite: " + p.sales, { x: 6.5, y: cy + 0.15, w: 2.7, h: 0.25, margin: 0, fontSize: 12, fontFace: "Calibri", bold: true, color: C.white });
    });
  }

  // ============================================================
  // SLIDE 33 — Section: SEZIONE 9 / La POC
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionDivider(pres, s, "SEZIONE 9", "La Proof of Concept", "Non vendiamo subito. Prima dimostriamo \u2014 il pacchetto completo.");
    s.addText("I primi 10 non sono solo tester del software. Sono i primi studenti del Metodo PT Evoluto.\nLa comunicazione WhatsApp \u00E8 attiva dal giorno uno.", {
      x: 0.6, y: 3.6, w: 8.8, h: 0.6, margin: 0, fontSize: 11, fontFace: "Calibri", color: C.textSec,
    });
    s.addText("Se non funziona, lo scopriamo con 10 persone e ~\u20AC1.000.", {
      x: 0.6, y: 4.3, w: 8.8, h: 0.3, margin: 0, fontSize: 12, fontFace: "Calibri", bold: true, color: C.gold,
    });
    addFooter(s, 33, TOTAL);
  }

  // ============================================================
  // SLIDE 34 — Cosa ricevono i 10 Fondatori
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Cosa ricevono i 10 Fondatori", "I Fondatori non ricevono solo il software. Ricevono il percorso completo per 12 mesi.");
    addFooter(s, 34, TOTAL);
    const items = [
      { icon: icons.laptop, title: "Software o Box", desc: "8 ricevono la licenza (\u20AC99),\n2 ricevono la Box (\u20AC199)", color: C.accent },
      { icon: icons.grad, title: "Inner Circle 12 mesi", desc: "Masterclass, webinar, mastermind\n\u2014 incluso, non extra", color: C.accent2 },
      { icon: icons.comments, title: "Community Fondatori", desc: "Canale riservato per feedback,\nidee, supporto", color: C.gold },
      { icon: icons.wrench, title: "Installazione assistita", desc: "Setup 1:1 con il founder", color: C.orange },
    ];
    items.forEach((it, i) => {
      const cx = 0.6 + i * 2.28;
      addCard(pres, s, cx, 1.2, 2.08, 1.5);
      s.addShape(pres.shapes.RECTANGLE, { x: cx, y: 1.2, w: 2.08, h: 0.05, fill: { color: it.color } });
      s.addImage({ data: it.icon, x: cx + 0.75, y: 1.35, w: 0.5, h: 0.5 });
      s.addText(it.title, { x: cx + 0.1, y: 1.9, w: 1.88, h: 0.28, margin: 0, fontSize: 11, fontFace: "Calibri", bold: true, color: C.white, align: "center" });
      s.addText(it.desc, { x: cx + 0.1, y: 2.2, w: 1.88, h: 0.45, margin: 0, fontSize: 9.5, fontFace: "Calibri", color: C.textSec, align: "center" });
    });
    addCard(pres, s, 0.6, 2.95, 8.8, 0.55, C.bgCard2);
    s.addText("Valore reale del pacchetto: \u20AC498 (licenza) / \u20AC698 (Box). I Fondatori lo ottengono a \u20AC99 / \u20AC199 perch\u00E9 sono l'investimento pi\u00F9 importante del progetto.", {
      x: 0.8, y: 3.0, w: 8.4, h: 0.4, margin: 0, fontSize: 11, fontFace: "Calibri", color: C.gold,
    });
  }

  // ============================================================
  // SLIDE 35 — Il protocollo POC
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Il protocollo: prodotto + formazione");
    addFooter(s, 35, TOTAL);
    const phases = [
      { label: "Fase A", title: "Setup e baseline", period: "Giorni 1-14", desc: "10 professionisti selezionati. Questionario baseline. Installazione e inserimento primi clienti.\nKPI di attivazione: primo messaggio WhatsApp pre-compilato inviato entro 24 ore dall'installazione.", color: C.accent },
      { label: "Fase B", title: "Adozione e masterclass", period: "Giorni 15-75", desc: "Uso reale quotidiano. Check-in bisettimanale. Micro-sondaggio settimanale.\n3 masterclass condotte dal Partner.", color: C.accent2 },
      { label: "Fase C", title: "Misurazione", period: "Giorni 75-90", desc: "Questionario finale. Confronto prima/dopo. Video-intervista.\nSessione di gruppo. Decisione GO/NO-GO.", color: C.gold },
    ];
    phases.forEach((p, i) => {
      const cy = 1.1 + i * 1.05;
      addCard(pres, s, 0.6, cy, 8.8, 0.95);
      addAccentBar(pres, s, 0.6, cy, 0.95, p.color);
      s.addShape(pres.shapes.RECTANGLE, { x: 0.85, y: cy + 0.1, w: 0.85, h: 0.28, fill: { color: p.color } });
      s.addText(p.label, { x: 0.85, y: cy + 0.1, w: 0.85, h: 0.28, margin: 0, fontSize: 9, fontFace: "Calibri", bold: true, color: C.bg, align: "center", valign: "middle" });
      s.addText(p.title + "  \u2014  " + p.period, { x: 1.9, y: cy + 0.08, w: 7.3, h: 0.28, margin: 0, fontSize: 13, fontFace: "Calibri", bold: true, color: C.white });
      s.addText(p.desc, { x: 1.9, y: cy + 0.4, w: 7.3, h: 0.5, margin: 0, fontSize: 10.5, fontFace: "Calibri", color: C.textSec });
    });
    // Masterclass schedule
    s.addText("Le 3 masterclass (condotte dall'Industry Partner):", { x: 0.6, y: 4.3, w: 8.8, h: 0.25, margin: 0, fontSize: 10.5, fontFace: "Calibri", bold: true, color: C.textSec });
    const mData = [
      "Mese 1: \"Il Metodo PT Evoluto \u2014 come cambia il tuo lavoro\"",
      "Mese 2: \"Le prime 4 settimane con FitManager \u2014 risultati e domande\"",
      "Mese 3: \"Da 25 a 45 clienti \u2014 il metodo in pratica\"",
    ];
    s.addText(mData.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < 2, fontSize: 10, fontFace: "Calibri", color: C.textMuted } })), {
      x: 0.8, y: 4.55, w: 8.4, h: 0.8, margin: 0,
    });
  }

  // ============================================================
  // SLIDE 36 — Metriche POC — UPDATED with Workout Intelligence
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Le metriche della POC");
    addFooter(s, 36, TOTAL);
    const thO = { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 10, fontFace: "Calibri" };
    const trO = (bg) => ({ color: C.textPri, fill: { color: bg }, fontSize: 9.5, fontFace: "Calibri" });
    const metricRows = [
      [{ text: "Metrica", options: thO }, { text: "Prima", options: { ...thO, align: "center" } }, { text: "Target", options: { ...thO, align: "center" } }, { text: "Valida", options: thO }],
      [{ text: "Ore admin/settimana", options: trO(C.tableRow1) }, { text: "3-5 ore", options: { ...trO(C.tableRow1), align: "center" } }, { text: "< 2 ore", options: { ...trO(C.tableRow1), align: "center", bold: true } }, { text: "Prodotto", options: trO(C.tableRow1) }],
      [{ text: "Organizzazione (1-10)", options: trO(C.tableRow2) }, { text: "4-6", options: { ...trO(C.tableRow2), align: "center" } }, { text: "8+", options: { ...trO(C.tableRow2), align: "center", bold: true } }, { text: "Prodotto", options: trO(C.tableRow2) }],
      [{ text: "Dati persi/mese", options: trO(C.tableRow1) }, { text: "2-3", options: { ...trO(C.tableRow1), align: "center" } }, { text: "Zero", options: { ...trO(C.tableRow1), align: "center", bold: true } }, { text: "Prodotto", options: trO(C.tableRow1) }],
      [{ text: "NPS (-100/+100)", options: trO(C.tableRow2) }, { text: "\u2014", options: { ...trO(C.tableRow2), align: "center" } }, { text: "Sopra 50", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.accent2 } }, { text: "Prodotto + percorso", options: trO(C.tableRow2) }],
      [{ text: "\"Lo ricompreresti a prezzo pieno?\"", options: trO(C.tableRow1) }, { text: "\u2014", options: { ...trO(C.tableRow1), align: "center" } }, { text: "8/10 s\u00EC", options: { ...trO(C.tableRow1), align: "center", bold: true } }, { text: "Pricing", options: trO(C.tableRow1) }],
      [{ text: "\"Masterclass hanno cambiato approccio?\"", options: trO(C.tableRow2) }, { text: "\u2014", options: { ...trO(C.tableRow2), align: "center" } }, { text: "7+/10 s\u00EC", options: { ...trO(C.tableRow2), align: "center" } }, { text: "Percorso", options: trO(C.tableRow2) }],
      [{ text: "\"I tuoi clienti notano differenza?\"", options: trO(C.tableRow1) }, { text: "\u2014", options: { ...trO(C.tableRow1), align: "center" } }, { text: "5+/10 s\u00EC", options: { ...trO(C.tableRow1), align: "center" } }, { text: "Volano PT Evoluto", options: trO(C.tableRow1) }],
      [{ text: "\"Ti definiresti un PT Evoluto?\"", options: trO(C.tableRow2) }, { text: "\u2014", options: { ...trO(C.tableRow2), align: "center" } }, { text: "6+/10 s\u00EC", options: { ...trO(C.tableRow2), align: "center" } }, { text: "Category creation", options: trO(C.tableRow2) }],
      [{ text: "Messaggi WA pre-compilati/sett.", options: trO(C.tableRow1) }, { text: "\u2014", options: { ...trO(C.tableRow1), align: "center" } }, { text: "15+", options: { ...trO(C.tableRow1), align: "center", bold: true } }, { text: "Adozione comunicazione", options: trO(C.tableRow1) }],
      [{ text: "Tempo risparmiato comunicazione", options: trO(C.tableRow2) }, { text: "\u2014", options: { ...trO(C.tableRow2), align: "center" } }, { text: "30+ min/gg", options: { ...trO(C.tableRow2), align: "center" } }, { text: "Valore feature", options: trO(C.tableRow2) }],
      [{ text: "Clienti usano portale allenamento", options: { ...trO(C.tableRow1), color: C.accent } }, { text: "\u2014", options: { ...trO(C.tableRow1), align: "center" } }, { text: "7/10 attivi", options: { ...trO(C.tableRow1), align: "center", bold: true, color: C.accent } }, { text: "Workout Intelligence", options: { ...trO(C.tableRow1), color: C.accent } }],
    ];
    s.addTable(metricRows, { x: 0.6, y: 0.95, w: 8.8, colW: [3.2, 1.2, 1.5, 2.9], border: { type: "solid", pt: 0.5, color: C.border }, rowH: Array(12).fill(0.33) });
    s.addText("Le ultime 4 metriche validano la categoria e il volano \u2014 non solo il software.", {
      x: 0.6, y: 5.0, w: 8.8, h: 0.2, margin: 0, fontSize: 9.5, fontFace: "Calibri", color: C.textMuted, italic: true,
    });
  }

  // ============================================================
  // SLIDE 37 — Profili e decisione
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "I profili e la decisione");
    addFooter(s, 37, TOTAL);
    // Profiles (left)
    s.addText("I 10 FONDATORI", { x: 0.6, y: 1.1, w: 4.1, h: 0.3, margin: 0, fontSize: 12, fontFace: "Calibri", bold: true, color: C.accent, charSpacing: 3 });
    const profiles = ["3 trainer in palestra", "2 freelance con studio proprio", "2 chinesiologi con clienti clinici", "1 trainer online/ibrido", "1 neoqualificato", "1 senior con 40+ clienti"];
    s.addText(profiles.map((p, j) => ({ text: p, options: { bullet: true, breakLine: j < profiles.length - 1, fontSize: 11, fontFace: "Calibri", color: C.textSec, paraSpaceAfter: 4 } })), {
      x: 0.6, y: 1.5, w: 4.1, h: 2.0, margin: 0,
    });
    s.addText("Criterio: almeno 10 clienti attivi, disponibilit\u00E0 a dare feedback strutturato per 90 giorni.", {
      x: 0.6, y: 3.4, w: 4.1, h: 0.4, margin: 0, fontSize: 10, fontFace: "Calibri", color: C.textMuted, italic: true,
    });
    // Decision (right)
    s.addText("LA DECISIONE", { x: 5.3, y: 1.1, w: 4.1, h: 0.3, margin: 0, fontSize: 12, fontFace: "Calibri", bold: true, color: C.gold, charSpacing: 3 });
    const decisions = [
      { label: "GO", desc: "NPS 50+, ore dimezzate, 8+ attivi,\n5+ clienti notano differenza", color: C.accent2 },
      { label: "GO cautela", desc: "NPS 30-50, miglioramenti parziali,\ncategoria parzialmente recepita", color: C.gold },
      { label: "STOP", desc: "NPS <30, meno di 6 attivi,\ncategoria non risuona", color: C.red },
    ];
    decisions.forEach((d, i) => {
      const cy = 1.5 + i * 0.82;
      addCard(pres, s, 5.3, cy, 4.1, 0.72);
      s.addShape(pres.shapes.RECTANGLE, { x: 5.3, y: cy, w: 4.1, h: 0.05, fill: { color: d.color } });
      s.addText(d.label, { x: 5.45, y: cy + 0.08, w: 3.8, h: 0.25, margin: 0, fontSize: 13, fontFace: "Trebuchet MS", bold: true, color: d.color });
      s.addText(d.desc, { x: 5.45, y: cy + 0.35, w: 3.8, h: 0.32, margin: 0, fontSize: 10, fontFace: "Calibri", color: C.textSec });
    });
    // What we have at month 4
    s.addText("COSA ABBIAMO AL MESE 4 (se GO)", { x: 0.6, y: 3.95, w: 8.8, h: 0.25, margin: 0, fontSize: 11, fontFace: "Calibri", bold: true, color: C.accent2 });
    const m4items = ["10 storie reali con dati misurabili (prima/dopo)", "10 video-interviste testimonial", "3 masterclass registrate (libreria Inner Circle)", "Dati aggregati + community funzionante", "La prova che il percorso PT Evoluto funziona"];
    s.addText(m4items.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < m4items.length - 1, fontSize: 10, fontFace: "Calibri", color: C.textSec, paraSpaceAfter: 2 } })), {
      x: 0.8, y: 4.2, w: 8.4, h: 1.0, margin: 0,
    });
  }

  // ============================================================
  // SLIDE 38 — Costo della POC — UPDATED
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Costo della POC");
    addFooter(s, 38, TOTAL);
    const costItems = [
      { label: "8 licenze Fondatore a \u20AC99 + 2 Box a \u20AC199", value: "\u20AC1.190 (ricavo)", color: C.accent2 },
      { label: "Costo vivo hardware 2 Box test", value: "\u20AC300", color: C.orange },
      { label: "Tempo founder (check-in, supporto, analisi)", value: "~40 ore in 90 gg", color: C.textSec },
      { label: "Tempo partner (selezione, 3 masterclass)", value: "~15-20 ore in 90 gg", color: C.textSec },
      { label: "Investimento netto in cash", value: "~\u20AC300", color: C.gold },
    ];
    costItems.forEach((it, i) => {
      const cy = 1.1 + i * 0.7;
      addCard(pres, s, 0.6, cy, 8.8, 0.6);
      addAccentBar(pres, s, 0.6, cy, 0.6, it.color);
      s.addText(it.label, { x: 0.85, y: cy + 0.12, w: 5.5, h: 0.3, margin: 0, fontSize: 12, fontFace: "Calibri", color: C.white });
      s.addText(it.value, { x: 6.5, y: cy + 0.12, w: 2.7, h: 0.3, margin: 0, fontSize: 14, fontFace: "Trebuchet MS", bold: true, color: it.color, align: "right" });
    });
    addCard(pres, s, 0.6, 4.7, 8.8, 0.5, C.bgCard2);
    s.addText("Il partner viene compensato con il 20% dei ricavi POC (\u20AC238) e con la propriet\u00E0 condivisa delle registrazioni: le 3 masterclass generano il 35% di revenue share per ogni futuro membro IC.", {
      x: 0.8, y: 4.73, w: 8.4, h: 0.4, margin: 0, fontSize: 10.5, fontFace: "Calibri", color: C.textSec,
    });
  }

  // ============================================================
  // SLIDE 39 — Section: SEZIONE 10 / Proiezioni finanziarie
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionDivider(pres, s, "SEZIONE 10", "Proiezioni finanziarie", "Due strutture a confronto: il business sta in piedi indipendentemente dalla partnership");
    addFooter(s, 39, TOTAL);
  }

  // ============================================================
  // SLIDE 40 — Config A: Founder solo
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Founder solo (senza Industry Partner)", "LinkedIn organico, SEO, referral, webinar self-hosted. Lead a regime: 10-14/mese. Vendite: 1-2/mese.");
    addFooter(s, 40, TOTAL);
    s.addText("CONFIGURAZIONE A", { x: 0.6, y: 0.35, w: 3, h: 0.25, margin: 0, fontSize: 10, fontFace: "Calibri", bold: true, color: C.orange, charSpacing: 3 });
    const thO = { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 11, fontFace: "Calibri" };
    const trO = (bg) => ({ color: C.textPri, fill: { color: bg }, fontSize: 11, fontFace: "Calibri" });
    const rows = [
      [{ text: "", options: { ...thO, align: "left" } }, { text: "Anno 1", options: { ...thO, align: "center" } }, { text: "Anno 2", options: { ...thO, align: "center" } }, { text: "Anno 3", options: { ...thO, align: "center" } }],
      [{ text: "Nuovi clienti", options: trO(C.tableRow1) }, { text: "24", options: { ...trO(C.tableRow1), align: "center" } }, { text: "34", options: { ...trO(C.tableRow1), align: "center" } }, { text: "50", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Base cumulativa", options: trO(C.tableRow2) }, { text: "24", options: { ...trO(C.tableRow2), align: "center" } }, { text: "58", options: { ...trO(C.tableRow2), align: "center" } }, { text: "108", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Fatturato", options: trO(C.tableRow1) }, { text: "\u20AC7.200", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC13.500", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC22.000", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Costi totali", options: trO(C.tableRow2) }, { text: "\u20AC5.800", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC8.500", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC14.000", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Tasse", options: trO(C.tableRow1) }, { text: "\u20AC1.512", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC2.835", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC4.400", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Netto founder", options: { ...trO(C.tableRow2), bold: true } }, { text: "-\u20AC112", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.red } }, { text: "\u20AC2.165", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.accent2 } }, { text: "\u20AC3.600", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.accent2 } }],
    ];
    s.addTable(rows, { x: 0.6, y: 1.25, w: 8.8, colW: [2.6, 2, 2.1, 2.1], border: { type: "solid", pt: 0.5, color: C.border }, rowH: Array(7).fill(0.4) });
    s.addText("Il business sopravvive. Non genera debito. Ma la crescita \u00E8 lenta e il founder non si paga un vero stipendio per almeno 2 anni.", {
      x: 0.6, y: 4.2, w: 8.8, h: 0.35, margin: 0, fontSize: 11, fontFace: "Calibri", color: C.textMuted, italic: true,
    });
  }

  // ============================================================
  // SLIDE 41 — Config B Conservativo — UPDATED
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    s.addText("CONFIG. B \u2014 CONSERVATIVO", { x: 0.6, y: 0.35, w: 5, h: 0.25, margin: 0, fontSize: 10, fontFace: "Calibri", bold: true, color: C.orange, charSpacing: 3 });
    addSectionTitle(s, "Con partner \u2014 Scenario conservativo", "Partner arriva tardi, conversione 20%, IC con bassa adozione (12% della base)");
    addFooter(s, 41, TOTAL);
    const thO = { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 10, fontFace: "Calibri" };
    const trO = (bg) => ({ color: C.textPri, fill: { color: bg }, fontSize: 10, fontFace: "Calibri" });
    const rows = [
      [{ text: "", options: { ...thO, align: "left" } }, { text: "Anno 1", options: { ...thO, align: "center" } }, { text: "Anno 2", options: { ...thO, align: "center" } }, { text: "Anno 3", options: { ...thO, align: "center" } }],
      [{ text: "Nuovi clienti", options: trO(C.tableRow1) }, { text: "33", options: { ...trO(C.tableRow1), align: "center" } }, { text: "35", options: { ...trO(C.tableRow1), align: "center" } }, { text: "49", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Base cumulativa", options: trO(C.tableRow2) }, { text: "33", options: { ...trO(C.tableRow2), align: "center" } }, { text: "68", options: { ...trO(C.tableRow2), align: "center" } }, { text: "117", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Vendite prodotto", options: trO(C.tableRow1) }, { text: "\u20AC8.559", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC12.632", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC18.108", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Assistenza PRO", options: trO(C.tableRow2) }, { text: "\u20AC160", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC2.414", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC4.945", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Inner Circle", options: trO(C.tableRow1) }, { text: "\u20AC996", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC2.040", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC4.388", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Fatturato", options: { ...trO(C.tableRow2), bold: true } }, { text: "\u20AC10.715", options: { ...trO(C.tableRow2), align: "center", bold: true } }, { text: "\u20AC17.086", options: { ...trO(C.tableRow2), align: "center", bold: true } }, { text: "\u20AC27.441", options: { ...trO(C.tableRow2), align: "center", bold: true } }],
      [{ text: "Costi + operativi", options: trO(C.tableRow1) }, { text: "\u20AC6.970", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC9.330", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC12.990", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Compenso partner (20%+35%)", options: trO(C.tableRow2) }, { text: "\u20AC2.117", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC4.085", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC6.889", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Tasse", options: trO(C.tableRow1) }, { text: "\u20AC2.250", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC3.588", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC6.467", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Netto founder", options: { ...trO(C.tableRow2), bold: true } }, { text: "-\u20AC622", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.red } }, { text: "\u20AC83", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.accent2 } }, { text: "\u20AC1.095", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.accent2 } }],
      [{ text: "Netto partner", options: { ...trO(C.tableRow1), bold: true } }, { text: "\u20AC2.117", options: { ...trO(C.tableRow1), align: "center", bold: true, color: C.gold } }, { text: "\u20AC4.085", options: { ...trO(C.tableRow1), align: "center", bold: true, color: C.gold } }, { text: "\u20AC6.889", options: { ...trO(C.tableRow1), align: "center", bold: true, color: C.gold } }],
    ];
    s.addTable(rows, { x: 0.6, y: 1.25, w: 8.8, colW: [2.6, 2, 2.1, 2.1], border: { type: "solid", pt: 0.5, color: C.border }, rowH: Array(13).fill(0.3) });
  }

  // ============================================================
  // SLIDE 42 — Config B Base — UPDATED
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    s.addText("CONFIG. B \u2014 BASE", { x: 0.6, y: 0.35, w: 5, h: 0.25, margin: 0, fontSize: 10, fontFace: "Calibri", bold: true, color: C.accent, charSpacing: 3 });
    addSectionTitle(s, "Con partner \u2014 Scenario base", "Partner operativo dal mese 2, conversione 25%, IC al 20% della base");
    addFooter(s, 42, TOTAL);
    const thO = { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 10, fontFace: "Calibri" };
    const trO = (bg) => ({ color: C.textPri, fill: { color: bg }, fontSize: 10, fontFace: "Calibri" });
    const rows = [
      [{ text: "", options: { ...thO, align: "left" } }, { text: "Anno 1", options: { ...thO, align: "center" } }, { text: "Anno 2", options: { ...thO, align: "center" } }, { text: "Anno 3", options: { ...thO, align: "center" } }],
      [{ text: "Nuovi clienti", options: trO(C.tableRow1) }, { text: "46", options: { ...trO(C.tableRow1), align: "center" } }, { text: "58", options: { ...trO(C.tableRow1), align: "center" } }, { text: "87", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Base cumulativa", options: trO(C.tableRow2) }, { text: "46", options: { ...trO(C.tableRow2), align: "center" } }, { text: "104", options: { ...trO(C.tableRow2), align: "center" } }, { text: "191", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Vendite prodotto", options: trO(C.tableRow1) }, { text: "\u20AC13.950", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC21.450", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC32.850", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Assistenza PRO", options: trO(C.tableRow2) }, { text: "\u20AC950", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC3.700", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC7.300", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Inner Circle", options: trO(C.tableRow1) }, { text: "\u20AC2.250", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC4.500", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC9.500", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Fatturato", options: { ...trO(C.tableRow2), bold: true } }, { text: "\u20AC17.150", options: { ...trO(C.tableRow2), align: "center", bold: true } }, { text: "\u20AC29.650", options: { ...trO(C.tableRow2), align: "center", bold: true } }, { text: "\u20AC49.650", options: { ...trO(C.tableRow2), align: "center", bold: true } }],
      [{ text: "Costi + operativi", options: trO(C.tableRow1) }, { text: "\u20AC8.560", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC14.325", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC22.865", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Compenso partner (20%+35%)", options: trO(C.tableRow2) }, { text: "\u20AC3.910", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC7.160", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC12.450", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Tasse", options: trO(C.tableRow1) }, { text: "\u20AC3.600", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC6.230", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC6.750", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Netto founder", options: { ...trO(C.tableRow2), bold: true } }, { text: "\u20AC1.080", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.accent2 } }, { text: "\u20AC1.935", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.accent2 } }, { text: "\u20AC7.585", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.accent2 } }],
      [{ text: "Netto partner", options: { ...trO(C.tableRow1), bold: true } }, { text: "\u20AC3.910", options: { ...trO(C.tableRow1), align: "center", bold: true, color: C.gold } }, { text: "\u20AC7.160", options: { ...trO(C.tableRow1), align: "center", bold: true, color: C.gold } }, { text: "\u20AC12.450", options: { ...trO(C.tableRow1), align: "center", bold: true, color: C.gold } }],
    ];
    s.addTable(rows, { x: 0.6, y: 1.25, w: 8.8, colW: [2.6, 2, 2.1, 2.1], border: { type: "solid", pt: 0.5, color: C.border }, rowH: Array(13).fill(0.3) });
    s.addText("Dall'Anno 3, con fatturato >\u20AC40K, transizione a regime ordinario/SRL. Tasse ~35% sul reddito netto (costi deducibili).", {
      x: 0.6, y: 5.0, w: 8.8, h: 0.2, margin: 0, fontSize: 9.5, fontFace: "Calibri", color: C.textMuted, italic: true,
    });
  }

  // ============================================================
  // SLIDE 43 — Config B Ottimistico — UPDATED
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    s.addText("CONFIG. B \u2014 OTTIMISTICO", { x: 0.6, y: 0.35, w: 5, h: 0.25, margin: 0, fontSize: 10, fontFace: "Calibri", bold: true, color: C.accent2, charSpacing: 3 });
    addSectionTitle(s, "Con partner \u2014 Scenario ottimistico", "Partner forte, conversione 30%, IC al 25% della base");
    addFooter(s, 43, TOTAL);
    const thO = { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 10, fontFace: "Calibri" };
    const trO = (bg) => ({ color: C.textPri, fill: { color: bg }, fontSize: 10, fontFace: "Calibri" });
    const rows = [
      [{ text: "", options: { ...thO, align: "left" } }, { text: "Anno 1", options: { ...thO, align: "center" } }, { text: "Anno 2", options: { ...thO, align: "center" } }, { text: "Anno 3", options: { ...thO, align: "center" } }],
      [{ text: "Nuovi clienti", options: trO(C.tableRow1) }, { text: "67", options: { ...trO(C.tableRow1), align: "center" } }, { text: "97", options: { ...trO(C.tableRow1), align: "center" } }, { text: "155", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Base cumulativa", options: trO(C.tableRow2) }, { text: "67", options: { ...trO(C.tableRow2), align: "center" } }, { text: "164", options: { ...trO(C.tableRow2), align: "center" } }, { text: "319", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Vendite prodotto", options: trO(C.tableRow1) }, { text: "\u20AC23.383", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC37.330", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC57.680", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Assistenza PRO", options: trO(C.tableRow2) }, { text: "\u20AC1.600", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC4.430", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC8.620", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Inner Circle", options: trO(C.tableRow1) }, { text: "\u20AC2.990", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC7.380", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC15.200", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Fatturato", options: { ...trO(C.tableRow2), bold: true } }, { text: "\u20AC27.973", options: { ...trO(C.tableRow2), align: "center", bold: true } }, { text: "\u20AC49.140", options: { ...trO(C.tableRow2), align: "center", bold: true } }, { text: "\u20AC81.500", options: { ...trO(C.tableRow2), align: "center", bold: true } }],
      [{ text: "Costi + operativi", options: trO(C.tableRow1) }, { text: "\u20AC11.050", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC22.130", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC38.250", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Compenso partner (20%+35%)", options: trO(C.tableRow2) }, { text: "\u20AC6.284", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC11.600", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC19.873", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Tasse", options: trO(C.tableRow1) }, { text: "\u20AC5.874", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC6.620", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC10.270", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Netto founder", options: { ...trO(C.tableRow2), bold: true } }, { text: "\u20AC4.765", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.accent2 } }, { text: "\u20AC8.790", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.accent2 } }, { text: "\u20AC13.107", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.accent2 } }],
      [{ text: "Netto partner", options: { ...trO(C.tableRow1), bold: true } }, { text: "\u20AC6.284", options: { ...trO(C.tableRow1), align: "center", bold: true, color: C.gold } }, { text: "\u20AC11.600", options: { ...trO(C.tableRow1), align: "center", bold: true, color: C.gold } }, { text: "\u20AC19.873", options: { ...trO(C.tableRow1), align: "center", bold: true, color: C.gold } }],
    ];
    s.addTable(rows, { x: 0.6, y: 1.25, w: 8.8, colW: [2.6, 2, 2.1, 2.1], border: { type: "solid", pt: 0.5, color: C.border }, rowH: Array(13).fill(0.3) });
  }

  // ============================================================
  // SLIDE 44 — Confronto diretto — UPDATED
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Il confronto diretto", "Cosa cambia con il partner");
    addFooter(s, 44, TOTAL);
    const thO = { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 11, fontFace: "Calibri" };
    const trO = (bg) => ({ color: C.textPri, fill: { color: bg }, fontSize: 11, fontFace: "Calibri" });
    const rows = [
      [{ text: "", options: { ...thO, align: "left" } }, { text: "Senza partner", options: { ...thO, align: "center" } }, { text: "Con partner (base)", options: { ...thO, align: "center" } }, { text: "Moltiplicatore", options: { ...thO, align: "center" } }],
      [{ text: "Clienti Anno 1", options: trO(C.tableRow1) }, { text: "24", options: { ...trO(C.tableRow1), align: "center" } }, { text: "46", options: { ...trO(C.tableRow1), align: "center", bold: true } }, { text: "1,9x", options: { ...trO(C.tableRow1), align: "center", bold: true, color: C.accent } }],
      [{ text: "Clienti Anno 3", options: trO(C.tableRow2) }, { text: "108", options: { ...trO(C.tableRow2), align: "center" } }, { text: "191", options: { ...trO(C.tableRow2), align: "center", bold: true } }, { text: "1,8x", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.accent } }],
      [{ text: "Fatturato Anno 1", options: trO(C.tableRow1) }, { text: "\u20AC7.200", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC17.150", options: { ...trO(C.tableRow1), align: "center", bold: true } }, { text: "2,4x", options: { ...trO(C.tableRow1), align: "center", bold: true, color: C.accent2 } }],
      [{ text: "Fatturato Anno 3", options: trO(C.tableRow2) }, { text: "\u20AC22.000", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC49.650", options: { ...trO(C.tableRow2), align: "center", bold: true } }, { text: "2,3x", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.accent2 } }],
      [{ text: "Netto founder Anno 3", options: { ...trO(C.tableRow1), bold: true } }, { text: "\u20AC3.600", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC7.585", options: { ...trO(C.tableRow1), align: "center", bold: true, color: C.accent2 } }, { text: "2,1x", options: { ...trO(C.tableRow1), align: "center", bold: true, color: C.gold } }],
      [{ text: "Fatturato cum. 3 anni", options: { ...trO(C.tableRow2), bold: true } }, { text: "\u20AC42.700", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC96.450", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.accent2 } }, { text: "2,3x", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.gold } }],
    ];
    s.addTable(rows, { x: 0.6, y: 1.15, w: 8.8, colW: [2.5, 2, 2.3, 2], border: { type: "solid", pt: 0.5, color: C.border }, rowH: Array(8).fill(0.4) });
    addCard(pres, s, 0.6, 4.55, 8.8, 0.55, C.bgCard2);
    s.addText("Il moltiplicatore 2,1x sul netto riflette una struttura di compenso pi\u00F9 generosa (20% prodotto + 35% ricorrente), calibrata sul contributo diretto del partner alla crescita del ricavo ricorrente. Il partner abilita l'Inner Circle \u2014 un flusso di ricavo altrimenti impossibile.", {
      x: 0.8, y: 4.58, w: 8.4, h: 0.45, margin: 0, fontSize: 10, fontFace: "Calibri", color: C.textSec,
    });
  }

  // ============================================================
  // SLIDE 45 — Vista cumulativa — UPDATED
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Vista cumulativa (scenario base)");
    addFooter(s, 45, TOTAL);
    const thO = { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 9.5, fontFace: "Calibri" };
    const trO = (bg) => ({ color: C.textPri, fill: { color: bg }, fontSize: 9.5, fontFace: "Calibri" });
    const rows = [
      [{ text: "", options: { ...thO, align: "left" } }, { text: "Anno 1", options: { ...thO, align: "center" } }, { text: "Anno 2", options: { ...thO, align: "center" } }, { text: "Anno 3", options: { ...thO, align: "center" } }, { text: "Cumulativo", options: { ...thO, align: "center" } }],
      [{ text: "PROGETTO", options: { ...trO(C.bgCard2), bold: true, color: C.accent } }, { text: "", options: trO(C.bgCard2) }, { text: "", options: trO(C.bgCard2) }, { text: "", options: trO(C.bgCard2) }, { text: "", options: trO(C.bgCard2) }],
      [{ text: "Clienti (base installata)", options: trO(C.tableRow1) }, { text: "46", options: { ...trO(C.tableRow1), align: "center" } }, { text: "104", options: { ...trO(C.tableRow1), align: "center" } }, { text: "191", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u2014", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Di cui Inner Circle", options: trO(C.tableRow2) }, { text: "9", options: { ...trO(C.tableRow2), align: "center" } }, { text: "18", options: { ...trO(C.tableRow2), align: "center" } }, { text: "38", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u2014", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Fatturato", options: { ...trO(C.tableRow1), bold: true } }, { text: "\u20AC17.150", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC29.650", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC49.650", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC96.450", options: { ...trO(C.tableRow1), align: "center", bold: true, color: C.accent } }],
      [{ text: "Di cui ricorrente (PRO+IC)", options: trO(C.tableRow2) }, { text: "\u20AC3.200", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC8.200", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC16.800", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC28.200", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "FOUNDER", options: { ...trO(C.bgCard2), bold: true, color: C.accent2 } }, { text: "", options: trO(C.bgCard2) }, { text: "", options: trO(C.bgCard2) }, { text: "", options: trO(C.bgCard2) }, { text: "", options: trO(C.bgCard2) }],
      [{ text: "Netto cash", options: { ...trO(C.tableRow1), bold: true } }, { text: "\u20AC1.080", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC1.935", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC7.585", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC10.600", options: { ...trO(C.tableRow1), align: "center", bold: true, color: C.accent2 } }],
      [{ text: "Equity detenuta", options: trO(C.tableRow2) }, { text: "95%", options: { ...trO(C.tableRow2), align: "center" } }, { text: "88-92%", options: { ...trO(C.tableRow2), align: "center" } }, { text: "88%", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u2014", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "PARTNER", options: { ...trO(C.bgCard2), bold: true, color: C.gold } }, { text: "", options: trO(C.bgCard2) }, { text: "", options: trO(C.bgCard2) }, { text: "", options: trO(C.bgCard2) }, { text: "", options: trO(C.bgCard2) }],
      [{ text: "Cash (20% prod + 35% ric)", options: { ...trO(C.tableRow1), bold: true } }, { text: "\u20AC3.910", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC7.160", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC12.450", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC23.520", options: { ...trO(C.tableRow1), align: "center", bold: true, color: C.gold } }],
      [{ text: "Equity maturata (milestone)", options: trO(C.tableRow2) }, { text: "5%", options: { ...trO(C.tableRow2), align: "center" } }, { text: "8-12%", options: { ...trO(C.tableRow2), align: "center" } }, { text: "12%", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u2014", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Valore equity stimato (12%)", options: trO(C.tableRow1) }, { text: "\u20AC3.120", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC8.160", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC16.800", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u2014", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Totale partner (cash+equity)", options: { ...trO(C.tableRow2), bold: true } }, { text: "\u20AC7.030", options: { ...trO(C.tableRow2), align: "center", bold: true } }, { text: "\u20AC15.320", options: { ...trO(C.tableRow2), align: "center", bold: true } }, { text: "\u20AC29.250", options: { ...trO(C.tableRow2), align: "center", bold: true } }, { text: "\u20AC39.520", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.gold } }],
      [{ text: "Valore stimato progetto", options: { ...trO(C.tableRow1), bold: true, color: C.white } }, { text: "\u20AC26.000", options: { ...trO(C.tableRow1), align: "center", bold: true } }, { text: "\u20AC68.000", options: { ...trO(C.tableRow1), align: "center", bold: true } }, { text: "\u20AC140.000", options: { ...trO(C.tableRow1), align: "center", bold: true } }, { text: "\u2014", options: { ...trO(C.tableRow1), align: "center" } }],
    ];
    s.addTable(rows, { x: 0.3, y: 0.95, w: 9.4, colW: [2.4, 1.6, 1.7, 1.7, 2], border: { type: "solid", pt: 0.5, color: C.border }, rowH: Array(16).fill(0.27) });
    s.addText("Valutazione: 2x ricavo ricorrente + valore base installata + IP + community. Metodo conservativo per software B2B verticali.", {
      x: 0.6, y: 5.05, w: 8.8, h: 0.2, margin: 0, fontSize: 8.5, fontFace: "Calibri", color: C.textMuted, italic: true,
    });
  }

  // ============================================================
  // SLIDE 46 — SEZIONE 11: Se va male
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionDivider(pres, s, "SEZIONE 11", "Se va male", "Lo scenario peggiore \u2014 tutto va male contemporaneamente");
    addFooter(s, 46, TOTAL);
    const stats = [
      { num: "18-20", label: "Clienti Anno 1", color: C.red },
      { num: "~\u20AC5.500", label: "Fatturato", color: C.orange },
      { num: "~\u20AC700", label: "Perdita netta", color: C.red },
      { num: "~\u20AC2.000", label: "Perdita massima cash", color: C.gold },
    ];
    stats.forEach((st, i) => {
      const cx = 0.6 + i * 2.28;
      addCard(pres, s, cx, 3.3, 2.08, 1.0);
      s.addText(st.num, { x: cx + 0.15, y: 3.4, w: 1.78, h: 0.4, margin: 0, fontSize: 22, fontFace: "Trebuchet MS", bold: true, color: st.color, align: "center" });
      s.addText(st.label, { x: cx + 0.15, y: 3.85, w: 1.78, h: 0.3, margin: 0, fontSize: 10, fontFace: "Calibri", color: C.textSec, align: "center" });
    });
    s.addText("Il business non chiude. Non genera debito. La perdita massima \u00E8 il costo di un corso di formazione.", {
      x: 0.6, y: 4.5, w: 8.8, h: 0.3, margin: 0, fontSize: 11, fontFace: "Calibri", color: C.textMuted, italic: true,
    });
  }

  // ============================================================
  // SLIDE 47 — Rischi e mitigazioni
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Rischi specifici e mitigazioni");
    addFooter(s, 47, TOTAL);
    const risks = [
      { risk: "\"I trainer non vogliono pagare per un software.\"", mitigation: "La POC include misurazione WTP prima di rivelare il prezzo. Se il dato esce basso, lo sappiamo con 10 persone.", color: C.red },
      { risk: "\"Il partner si disimpegna.\"", mitigation: "Equity a milestone \u2014 se non raggiunge i risultati, non matura. Il business parte anche senza (Config. A).", color: C.orange },
      { risk: "\"Un competitor copia.\"", mitigation: "DB scientifico (500 esercizi, 940 relazioni, Safety Engine, CREA) = 6+ mesi di lavoro. Architettura locale non replicabile da SaaS.", color: C.gold },
      { risk: "\"I rinnovi assistenza sono bassi.\"", mitigation: "Se sotto 40%, il contenuto non ha valore percepito sufficiente. Lo misuriamo e correggiamo. Business non dipende dai rinnovi Anno 1.", color: C.accent },
    ];
    risks.forEach((r, i) => {
      const cy = 1.1 + i * 0.95;
      addCard(pres, s, 0.6, cy, 8.8, 0.85);
      addAccentBar(pres, s, 0.6, cy, 0.85, r.color);
      s.addText(r.risk, { x: 0.85, y: cy + 0.08, w: 8.35, h: 0.28, margin: 0, fontSize: 12, fontFace: "Calibri", bold: true, color: r.color });
      s.addText(r.mitigation, { x: 0.85, y: cy + 0.4, w: 8.35, h: 0.4, margin: 0, fontSize: 10.5, fontFace: "Calibri", color: C.textSec });
    });
  }

  // ============================================================
  // SLIDE 48 — SEZIONE 12: Team
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    s.addText("SEZIONE 12", { x: 0.6, y: 0.35, w: 3, h: 0.25, margin: 0, fontSize: 10, fontFace: "Calibri", bold: true, color: C.accent, charSpacing: 3 });
    addSectionTitle(s, "Anno 1: founder + Industry Partner");
    addFooter(s, 48, TOTAL);
    // Founder (left)
    addCard(pres, s, 0.6, 1.15, 4.15, 3.2);
    s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 1.15, w: 4.15, h: 0.05, fill: { color: C.accent } });
    s.addText("FOUNDER", { x: 0.8, y: 1.3, w: 3.75, h: 0.3, margin: 0, fontSize: 14, fontFace: "Trebuchet MS", bold: true, color: C.accent });
    s.addText("Giacomo Verardo", { x: 0.8, y: 1.6, w: 3.75, h: 0.25, margin: 0, fontSize: 12, fontFace: "Calibri", color: C.white });
    const fItems = ["Sviluppo prodotto", "Vendite dirette", "Supporto clienti", "Marketing organico", "Gestione operativa"];
    s.addText(fItems.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < fItems.length - 1, fontSize: 11, fontFace: "Calibri", color: C.textSec, paraSpaceAfter: 4 } })), {
      x: 0.8, y: 2.0, w: 3.75, h: 2.0, margin: 0,
    });
    // Partner (right)
    addCard(pres, s, 5.25, 1.15, 4.15, 3.2);
    s.addShape(pres.shapes.RECTANGLE, { x: 5.25, y: 1.15, w: 4.15, h: 0.05, fill: { color: C.gold } });
    s.addText("INDUSTRY PARTNER", { x: 5.45, y: 1.3, w: 3.75, h: 0.3, margin: 0, fontSize: 14, fontFace: "Trebuchet MS", bold: true, color: C.gold });
    s.addText("Professionista fitness con esperienza,\ncredibilit\u00E0 e network. Impegno: 8-10 ore/mese.", { x: 5.45, y: 1.6, w: 3.75, h: 0.4, margin: 0, fontSize: 10.5, fontFace: "Calibri", color: C.textSec });
    const pItems = ["Seleziona i Fondatori POC", "Presenta al proprio network", "Conduce masterclass/webinar", "Valida posizionamento PT Evoluto", "Contribuisce al DB esercizi"];
    s.addText(pItems.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < pItems.length - 1, fontSize: 11, fontFace: "Calibri", color: C.textSec, paraSpaceAfter: 4 } })), {
      x: 5.45, y: 2.1, w: 3.75, h: 2.0, margin: 0,
    });
    // Evolution
    s.addText("Evoluzione: Anno 2 + tirocinante part-time (\u20AC4-5K)  |  Anno 3 + junior dev + ufficio (\u20AC12-16K)", {
      x: 0.6, y: 4.6, w: 8.8, h: 0.25, margin: 0, fontSize: 10, fontFace: "Calibri", color: C.textMuted,
    });
  }

  // ============================================================
  // SLIDE 49 — Struttura compenso partner — COMPLETELY UPDATED
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Struttura di compenso del partner", "Il partner non riceve un compenso fisso. Riceve una quota dei ricavi semplificata a due percentuali.");
    addFooter(s, 49, TOTAL);
    // Revenue share table
    const thO = { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 11, fontFace: "Calibri" };
    const trO = (bg) => ({ color: C.textPri, fill: { color: bg }, fontSize: 11, fontFace: "Calibri" });
    const rsRows = [
      [{ text: "Componente", options: thO }, { text: "%", options: { ...thO, align: "center" } }, { text: "Applicata a", options: thO }],
      [{ text: "Vendite prodotto", options: trO(C.tableRow1) }, { text: "20%", options: { ...trO(C.tableRow1), align: "center", bold: true, color: C.accent, fontSize: 14 } }, { text: "Tutte le licenze e Box, senza distinguere la fonte", options: trO(C.tableRow1) }],
      [{ text: "Ricorrente + contenuto", options: trO(C.tableRow2) }, { text: "35%", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.gold, fontSize: 14 } }, { text: "PRO, Inner Circle, masterclass", options: trO(C.tableRow2) }],
    ];
    s.addTable(rsRows, { x: 0.6, y: 1.15, w: 8.8, colW: [2.2, 1, 5.6], border: { type: "solid", pt: 0.5, color: C.border }, rowH: [0.38, 0.45, 0.45] });
    // Equity milestone table
    s.addText("EQUITY \u2014 a milestone, non a tempo", { x: 0.6, y: 2.3, w: 8.8, h: 0.3, margin: 0, fontSize: 13, fontFace: "Calibri", bold: true, color: C.accent2 });
    const eqRows = [
      [{ text: "Milestone", options: thO }, { text: "Equity", options: { ...thO, align: "center" } }, { text: "Quando", options: { ...thO, align: "center" } }],
      [{ text: "Completamento POC \u2014 GO al giorno 90", options: trO(C.tableRow1) }, { text: "5%", options: { ...trO(C.tableRow1), align: "center", bold: true, color: C.accent } }, { text: "Mese 3", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "50 clienti attivi nella base installata", options: trO(C.tableRow2) }, { text: "3%", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.accent } }, { text: "~Mese 8-12", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Primo accordo internazionale firmato", options: trO(C.tableRow1) }, { text: "4%", options: { ...trO(C.tableRow1), align: "center", bold: true, color: C.accent } }, { text: "Quando accade", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "TOTALE POTENZIALE", options: { ...trO(C.tableRow2), bold: true, color: C.gold } }, { text: "12%", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.gold, fontSize: 14 } }, { text: "\u2014", options: { ...trO(C.tableRow2), align: "center" } }],
    ];
    s.addTable(eqRows, { x: 0.6, y: 2.65, w: 8.8, colW: [5, 1.5, 2.3], border: { type: "solid", pt: 0.5, color: C.border }, rowH: [0.35, 0.38, 0.38, 0.38, 0.4] });
    // ROI
    addCard(pres, s, 0.6, 4.6, 4.15, 0.55, C.bgCard2);
    addAccentBar(pres, s, 0.6, 4.6, 0.55, C.accent2);
    s.addText("Compenso triennio: \u20AC23.520\nFatturato aggiuntivo: \u20AC53.750", { x: 0.85, y: 4.63, w: 3.7, h: 0.45, margin: 0, fontSize: 10.5, fontFace: "Calibri", color: C.textSec });
    addCard(pres, s, 5.25, 4.6, 4.15, 0.55, C.bgCard2);
    s.addText("ROI: 2,3x", { x: 5.45, y: 4.63, w: 3.75, h: 0.45, margin: 0, fontSize: 22, fontFace: "Trebuchet MS", bold: true, color: C.accent2, valign: "middle" });
  }

  // ============================================================
  // SLIDE 50 — Chi è il founder — UPDATED
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Chi \u00E8 il founder", "Giacomo Verardo");
    addFooter(s, 50, TOTAL);
    const bio = [
      { icon: icons.ship, title: "Gestione sistemi complessi", desc: "Anni nella cantieristica navale e operazioni offshore (SAIPEM). Navi, cantieri, operazioni in Brasile, Africa, Cina.", color: C.accent },
      { icon: icons.brain, title: "Competenza tecnologica ereditata", desc: "Due anni a fianco del padre, pioniere AI in Italia. Sistemi di visione artificiale per l'industria.", color: C.accent2 },
      { icon: icons.laptop, title: "FitManager", desc: "6 mesi sviluppo full-time. 47.000+ LOC, 395 test, 7 motori scientifici. In uso quotidiano da una professionista reale.", color: C.gold },
      { icon: icons.dumbbell, title: "Competenza di dominio", desc: "Conoscenza diretta del fitness come praticante e istruttore. Intersezione tra competenza tecnica e dominio.", color: C.orange },
    ];
    bio.forEach((b, i) => {
      const cy = 1.15 + i * 0.92;
      addCard(pres, s, 0.6, cy, 8.8, 0.82);
      addAccentBar(pres, s, 0.6, cy, 0.82, b.color);
      s.addImage({ data: b.icon, x: 0.85, y: cy + 0.15, w: 0.4, h: 0.4 });
      s.addText(b.title, { x: 1.4, y: cy + 0.05, w: 7.8, h: 0.3, margin: 0, fontSize: 13, fontFace: "Calibri", bold: true, color: b.color });
      s.addText(b.desc, { x: 1.4, y: cy + 0.38, w: 7.8, h: 0.38, margin: 0, fontSize: 10.5, fontFace: "Calibri", color: C.textSec });
    });
  }

  // ============================================================
  // SLIDE 51 — Piano di crescita
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    s.addText("SEZIONE 13", { x: 0.6, y: 0.35, w: 3, h: 0.25, margin: 0, fontSize: 10, fontFace: "Calibri", bold: true, color: C.accent, charSpacing: 3 });
    addSectionTitle(s, "Piano di crescita");
    addFooter(s, 51, TOTAL);
    const phases = [
      { label: "Fase 1", period: "Mesi 1-3", title: "POC con percorso completo", desc: "10 Fondatori, software/Box + IC incluso 12 mesi. 3 masterclass.\nValidazione simultanea prodotto, percorso, categoria, ruolo partner.", color: C.accent },
      { label: "Fase 2", period: "Mesi 4-6", title: "Early Adopter + IC attivo", desc: "Testimonial POC come leva. Network del partner. IC disponibile.\nWebinar gratuito mensile. Target: 15-20 clienti, 30% con IC.", color: C.accent2 },
      { label: "Fase 3", period: "Mesi 7-12", title: "Prezzo pieno e scala", desc: "Tutti i canali attivi. IC consolidato con masterclass mensili.\nPT Evoluto circola nel settore. Target: 3-5 vendite/mese.", color: C.gold },
      { label: "Fase 4", period: "Anno 2+", title: "Espansione", desc: "IC a pieno regime. Fiere (RiminiWellness). Bundle Box+Tablet.\nPrimo collaboratore. Certificazione PT Evoluto. Versione inglese.", color: C.orange },
    ];
    phases.forEach((p, i) => {
      const cy = 1.15 + i * 0.92;
      addCard(pres, s, 0.6, cy, 8.8, 0.82);
      addAccentBar(pres, s, 0.6, cy, 0.82, p.color);
      s.addShape(pres.shapes.RECTANGLE, { x: 0.85, y: cy + 0.1, w: 0.75, h: 0.25, fill: { color: p.color } });
      s.addText(p.label, { x: 0.85, y: cy + 0.1, w: 0.75, h: 0.25, margin: 0, fontSize: 9, fontFace: "Calibri", bold: true, color: C.bg, align: "center", valign: "middle" });
      s.addText(p.title + "  (" + p.period + ")", { x: 1.8, y: cy + 0.05, w: 7.4, h: 0.28, margin: 0, fontSize: 12, fontFace: "Calibri", bold: true, color: C.white });
      s.addText(p.desc, { x: 1.8, y: cy + 0.38, w: 7.4, h: 0.4, margin: 0, fontSize: 10, fontFace: "Calibri", color: C.textSec });
    });
    s.addText("Il volano parte dalla POC: masterclass \u2192 PT Evoluto \u2192 clienti notano differenza \u2192 colleghi chiedono \u2192 passaparola \u2192 nuovi membri IC. I costi acquisizione scendono, il ricorrente sale.", {
      x: 0.6, y: 4.9, w: 8.8, h: 0.3, margin: 0, fontSize: 9.5, fontFace: "Calibri", color: C.textMuted, italic: true,
    });
  }

  // ============================================================
  // SLIDE 52 — Cosa cerchiamo — UPDATED
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    s.addText("SEZIONE 14", { x: 0.6, y: 0.35, w: 3, h: 0.25, margin: 0, fontSize: 10, fontFace: "Calibri", bold: true, color: C.accent, charSpacing: 3 });
    addSectionTitle(s, "Cosa cerchiamo");
    addFooter(s, 52, TOTAL);
    // Industry Partner
    addCard(pres, s, 0.6, 1.15, 8.8, 0.9);
    addAccentBar(pres, s, 0.6, 1.15, 0.9, C.gold);
    s.addText("INDUSTRY PARTNER", { x: 0.85, y: 1.2, w: 8.35, h: 0.25, margin: 0, fontSize: 12, fontFace: "Calibri", bold: true, color: C.gold, charSpacing: 3 });
    s.addText("Un professionista fitness con esperienza, credibilit\u00E0 e network attivo. Non un dipendente \u2014 un partner con incentivi allineati (equity + rev share, zero costi fissi).", {
      x: 0.85, y: 1.5, w: 8.35, h: 0.45, margin: 0, fontSize: 11, fontFace: "Calibri", color: C.textSec,
    });
    // NASpI
    addCard(pres, s, 0.6, 2.25, 4.15, 1.2);
    addAccentBar(pres, s, 0.6, 2.25, 1.2, C.accent2);
    s.addText("NASPI ANTICIPATA", { x: 0.85, y: 2.3, w: 3.7, h: 0.22, margin: 0, fontSize: 10, fontFace: "Calibri", bold: true, color: C.accent2, charSpacing: 3 });
    s.addText("\u20AC13.000-16.000 netti", { x: 0.85, y: 2.55, w: 3.7, h: 0.3, margin: 0, fontSize: 18, fontFace: "Trebuchet MS", bold: true, color: C.accent2 });
    s.addText("Copre interamente le riserve personali per i primi 24 mesi. Business avviabile senza risparmi propri.", {
      x: 0.85, y: 2.9, w: 3.7, h: 0.45, margin: 0, fontSize: 10, fontFace: "Calibri", color: C.textSec,
    });
    // Smart&Start
    addCard(pres, s, 5.25, 2.25, 4.15, 1.2);
    addAccentBar(pres, s, 5.25, 2.25, 1.2, C.accent);
    s.addText("SMART&START ITALIA", { x: 5.5, y: 2.3, w: 3.7, h: 0.22, margin: 0, fontSize: 10, fontFace: "Calibri", bold: true, color: C.accent, charSpacing: 3 });
    s.addText("\u20AC50.000-100.000", { x: 5.5, y: 2.55, w: 3.7, h: 0.3, margin: 0, fontSize: 18, fontFace: "Trebuchet MS", bold: true, color: C.accent });
    s.addText("Tasso zero, a sportello (no graduatorie). Richiede startup innovativa. Domanda al mese 6-7, erogazione al mese 10+.", {
      x: 5.5, y: 2.9, w: 3.7, h: 0.45, margin: 0, fontSize: 10, fontFace: "Calibri", color: C.textSec,
    });
    s.addText("NASpI copre il founder, Smart&Start copre il business. Cumulabili.", {
      x: 0.6, y: 3.6, w: 8.8, h: 0.25, margin: 0, fontSize: 11, fontFace: "Calibri", bold: true, color: C.gold,
    });
  }

  // ============================================================
  // SLIDES 53-58: APPENDICI + CHIUSURA
  // ============================================================
  // SLIDE 53 — A1: Dettaglio prodotto — UPDATED
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Dettaglio prodotto", "APPENDICE A1");
    addFooter(s, 53, TOTAL);
    const thO = { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 10, fontFace: "Calibri" };
    const trO = (bg) => ({ color: C.textPri, fill: { color: bg }, fontSize: 9.5, fontFace: "Calibri" });
    const rows = [
      [{ text: "Area", options: thO }, { text: "Cosa fa", options: thO }, { text: "Stato", options: { ...thO, align: "center" } }],
      [{ text: "CRM", options: trO(C.tableRow1) }, { text: "Clienti, contratti, pagamenti, agenda, cassa \u2014 profilo unico", options: trO(C.tableRow1) }, { text: "Completo", options: { ...trO(C.tableRow1), align: "center", color: C.accent2 } }],
      [{ text: "Clinico", options: trO(C.tableRow2) }, { text: "Anamnesi 6 step, misurazioni, avatar 6 viste, prontezza", options: trO(C.tableRow2) }, { text: "Completo", options: { ...trO(C.tableRow2), align: "center", color: C.accent2 } }],
      [{ text: "Allenamento", options: trO(C.tableRow1) }, { text: "Workout builder 3 modalit\u00E0, DnD, blocchi, export PDF. DB arricchimento continuo.", options: trO(C.tableRow1) }, { text: "Completo", options: { ...trO(C.tableRow1), align: "center", color: C.accent2 } }],
      [{ text: "Nutrizione", options: trO(C.tableRow2) }, { text: "880 alimenti CREA, 210 ricette, 12 template LARN, piano settimanale", options: trO(C.tableRow2) }, { text: "Completo", options: { ...trO(C.tableRow2), align: "center", color: C.accent2 } }],
      [{ text: "Operativo", options: trO(C.tableRow1) }, { text: "Setup guidato, licenza HW-bound, backup/ripristino, diagnostica", options: trO(C.tableRow1) }, { text: "Completo", options: { ...trO(C.tableRow1), align: "center", color: C.accent2 } }],
      [{ text: "Accesso", options: trO(C.tableRow2) }, { text: "Portale anamnesi self-service, accesso remoto Tailscale", options: trO(C.tableRow2) }, { text: "Completo", options: { ...trO(C.tableRow2), align: "center", color: C.accent2 } }],
      [{ text: "Comunicazione", options: trO(C.tableRow1) }, { text: "WhatsApp semi-auto (wa.me), email SMTP auto, template", options: trO(C.tableRow1) }, { text: "Completo", options: { ...trO(C.tableRow1), align: "center", color: C.accent2 } }],
      [{ text: "Portale Allenamento", options: { ...trO(C.tableRow2), color: C.accent } }, { text: "Portale cliente: sessione del giorno, registrazione esecuzione, feedback, zero app", options: trO(C.tableRow2) }, { text: "Completo", options: { ...trO(C.tableRow2), align: "center", color: C.accent2 } }],
      [{ text: "Workout Intelligence", options: { ...trO(C.tableRow1), color: C.accent } }, { text: "Compliance, dose-response muscolo\u00D7muscolo, equilibri biomeccanici, alert predittivi", options: trO(C.tableRow1) }, { text: "Completo", options: { ...trO(C.tableRow1), align: "center", color: C.accent2 } }],
    ];
    s.addTable(rows, { x: 0.6, y: 1.1, w: 8.8, colW: [1.6, 5.8, 1.4], border: { type: "solid", pt: 0.5, color: C.border }, rowH: Array(11).fill(0.35) });
    s.addText("500 esercizi, 940 relazioni, 47 condizioni cliniche, 80 regole Safety Engine.", {
      x: 0.6, y: 5.0, w: 8.8, h: 0.2, margin: 0, fontSize: 10, fontFace: "Calibri", color: C.textMuted,
    });
  }

  // SLIDE 54 — A3: P&L triennale — UPDATED
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "P&L triennale dettagliato (scenario base)", "APPENDICE A3");
    addFooter(s, 54, TOTAL);
    const thO = { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 10, fontFace: "Calibri" };
    const trO = (bg) => ({ color: C.textPri, fill: { color: bg }, fontSize: 10, fontFace: "Calibri" });
    // Ricavi
    s.addText("RICAVI", { x: 0.6, y: 1.0, w: 2, h: 0.25, margin: 0, fontSize: 10, fontFace: "Calibri", bold: true, color: C.accent2, charSpacing: 3 });
    const revRows = [
      [{ text: "", options: { ...thO, align: "left" } }, { text: "Anno 1", options: { ...thO, align: "center" } }, { text: "Anno 2", options: { ...thO, align: "center" } }, { text: "Anno 3", options: { ...thO, align: "center" } }],
      [{ text: "Licenze software", options: trO(C.tableRow1) }, { text: "\u20AC4.278", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC5.727", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC7.719", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Box", options: trO(C.tableRow2) }, { text: "\u20AC9.672", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC15.723", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC25.131", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Assistenza PRO", options: trO(C.tableRow1) }, { text: "\u20AC950", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC3.700", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC7.300", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Inner Circle", options: trO(C.tableRow2) }, { text: "\u20AC2.250", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC4.500", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC9.500", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Fatturato totale", options: { ...trO(C.tableRow1), bold: true } }, { text: "\u20AC17.150", options: { ...trO(C.tableRow1), align: "center", bold: true } }, { text: "\u20AC29.650", options: { ...trO(C.tableRow1), align: "center", bold: true } }, { text: "\u20AC49.650", options: { ...trO(C.tableRow1), align: "center", bold: true } }],
    ];
    s.addTable(revRows, { x: 0.6, y: 1.3, w: 8.8, colW: [2.6, 2, 2.1, 2.1], border: { type: "solid", pt: 0.5, color: C.border }, rowH: Array(7).fill(0.3) });
    // Riepilogo
    s.addText("RIEPILOGO", { x: 0.6, y: 3.6, w: 2, h: 0.25, margin: 0, fontSize: 10, fontFace: "Calibri", bold: true, color: C.gold, charSpacing: 3 });
    const sumRows = [
      [{ text: "", options: { ...thO, align: "left" } }, { text: "Anno 1", options: { ...thO, align: "center" } }, { text: "Anno 2", options: { ...thO, align: "center" } }, { text: "Anno 3", options: { ...thO, align: "center" } }],
      [{ text: "Margine lordo", options: trO(C.tableRow1) }, { text: "\u20AC12.890 (75%)", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC23.825 (80%)", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC40.785 (82%)", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Costi operativi", options: trO(C.tableRow2) }, { text: "\u20AC4.300", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC8.500", options: { ...trO(C.tableRow2), align: "center" } }, { text: "\u20AC14.000", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Compenso partner (20%+35%)", options: trO(C.tableRow1) }, { text: "\u20AC3.910", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC7.160", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC12.450", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "EBITDA", options: { ...trO(C.tableRow2), bold: true } }, { text: "\u20AC4.680", options: { ...trO(C.tableRow2), align: "center", bold: true } }, { text: "\u20AC8.165", options: { ...trO(C.tableRow2), align: "center", bold: true } }, { text: "\u20AC14.335", options: { ...trO(C.tableRow2), align: "center", bold: true } }],
      [{ text: "Tasse", options: trO(C.tableRow1) }, { text: "\u20AC3.600", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC6.230", options: { ...trO(C.tableRow1), align: "center" } }, { text: "\u20AC6.750", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Netto founder", options: { ...trO(C.tableRow2), bold: true } }, { text: "\u20AC1.080", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.accent2 } }, { text: "\u20AC1.935", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.accent2 } }, { text: "\u20AC7.585", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.accent2 } }],
    ];
    s.addTable(sumRows, { x: 0.6, y: 3.85, w: 8.8, colW: [2.6, 2, 2.1, 2.1], border: { type: "solid", pt: 0.5, color: C.border }, rowH: Array(8).fill(0.22) });
  }

  // SLIDE 55 — A4: Assunzioni — UPDATED (fix duplicates, add new)
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Le assunzioni chiave", "APPENDICE A4");
    addFooter(s, 55, TOTAL);
    const thO = { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 9, fontFace: "Calibri" };
    const trO = (bg) => ({ color: C.textPri, fill: { color: bg }, fontSize: 8.5, fontFace: "Calibri" });
    const rows = [
      [{ text: "Cod.", options: { ...thO, align: "center" } }, { text: "Assunzione", options: thO }, { text: "Stato", options: { ...thO, align: "center" } }, { text: "Validazione", options: thO }],
      [{ text: "P4", options: { ...trO(C.tableRow1), align: "center" } }, { text: "PT perde 3-5h/sett in admin", options: trO(C.tableRow1) }, { text: "Ipotesi", options: { ...trO(C.tableRow1), align: "center" } }, { text: "Questionario baseline POC", options: trO(C.tableRow1) }],
      [{ text: "B7", options: { ...trO(C.tableRow2), align: "center" } }, { text: "PT disposto a pagare \u20AC249-449", options: trO(C.tableRow2) }, { text: "Ipotesi critica", options: { ...trO(C.tableRow2), align: "center", color: C.red } }, { text: "WTP POC", options: trO(C.tableRow2) }],
      [{ text: "S4", options: { ...trO(C.tableRow1), align: "center" } }, { text: "La Box risolve il problema mobile", options: trO(C.tableRow1) }, { text: "Ipotesi forte", options: { ...trO(C.tableRow1), align: "center" } }, { text: "Test 2 Fondatori POC", options: trO(C.tableRow1) }],
      [{ text: "G3", options: { ...trO(C.tableRow2), align: "center" } }, { text: "Partner genera 8-12 lead/mese", options: trO(C.tableRow2) }, { text: "Ipotesi", options: { ...trO(C.tableRow2), align: "center" } }, { text: "Primo trim. partnership", options: trO(C.tableRow2) }],
      [{ text: "G4", options: { ...trO(C.tableRow1), align: "center" } }, { text: "Conversione demo-acquisto 20-25%", options: trO(C.tableRow1) }, { text: "Ipotesi cons.", options: { ...trO(C.tableRow1), align: "center" } }, { text: "Dati reali mesi 4-6", options: trO(C.tableRow1) }],
      [{ text: "B5", options: { ...trO(C.tableRow2), align: "center" } }, { text: "Rinnovo assistenza 55-60%", options: trO(C.tableRow2) }, { text: "Ipotesi", options: { ...trO(C.tableRow2), align: "center" } }, { text: "Dato reale Anno 2", options: trO(C.tableRow2) }],
      [{ text: "M2", options: { ...trO(C.tableRow1), align: "center" } }, { text: "Segmento target 10-15K PT", options: trO(C.tableRow1) }, { text: "Stima", options: { ...trO(C.tableRow1), align: "center" } }, { text: "Primi 6 mesi vendita", options: trO(C.tableRow1) }],
      [{ text: "IC1", options: { ...trO(C.tableRow2), align: "center" } }, { text: "IC raggiunge 20% base (base)", options: trO(C.tableRow2) }, { text: "Ipotesi", options: { ...trO(C.tableRow2), align: "center" } }, { text: "Dato reale mesi 7-12", options: trO(C.tableRow2) }],
      [{ text: "IC2", options: { ...trO(C.tableRow1), align: "center" } }, { text: "Masterclass generano adozione categoria", options: trO(C.tableRow1) }, { text: "Ipotesi forte", options: { ...trO(C.tableRow1), align: "center" } }, { text: "Metriche POC", options: trO(C.tableRow1) }],
      [{ text: "WA1", options: { ...trO(C.tableRow2), align: "center" } }, { text: "WhatsApp semi-auto riduce frizione iniziale", options: trO(C.tableRow2) }, { text: "Ipotesi forte", options: { ...trO(C.tableRow2), align: "center" } }, { text: "KPI attivazione POC", options: trO(C.tableRow2) }],
      [{ text: "WA2", options: { ...trO(C.tableRow1), align: "center" } }, { text: "Trainer usano 15+ msg pre-compilati/sett", options: trO(C.tableRow1) }, { text: "Ipotesi", options: { ...trO(C.tableRow1), align: "center" } }, { text: "Dato reale POC gg 15-75", options: trO(C.tableRow1) }],
      [{ text: "DB1", options: { ...trO(C.tableRow2), align: "center", color: C.accent } }, { text: "Professionisti disponibili a contribuire DB esercizi", options: { ...trO(C.tableRow2), color: C.accent } }, { text: "Ipotesi forte", options: { ...trO(C.tableRow2), align: "center" } }, { text: "Primo contributo partnership/POC", options: trO(C.tableRow2) }],
      [{ text: "INT1", options: { ...trO(C.tableRow1), align: "center", color: C.accent } }, { text: "Versione inglese core completabile entro 6 mesi", options: { ...trO(C.tableRow1), color: C.accent } }, { text: "Ipotesi", options: { ...trO(C.tableRow1), align: "center" } }, { text: "Valutazione tecnica in corso", options: trO(C.tableRow1) }],
      [{ text: "WI1", options: { ...trO(C.tableRow2), align: "center", color: C.accent } }, { text: "Clienti usano portale allenamento (7/10 attivi)", options: { ...trO(C.tableRow2), color: C.accent } }, { text: "Ipotesi forte", options: { ...trO(C.tableRow2), align: "center" } }, { text: "Dato reale POC gg 15-75", options: trO(C.tableRow2) }],
      [{ text: "WI2", options: { ...trO(C.tableRow1), align: "center", color: C.accent } }, { text: "Workout Intelligence differenzia da competitor", options: { ...trO(C.tableRow1), color: C.accent } }, { text: "Ipotesi forte", options: { ...trO(C.tableRow1), align: "center" } }, { text: "Feedback POC + analisi competitor", options: trO(C.tableRow1) }],
    ];
    s.addTable(rows, { x: 0.3, y: 0.95, w: 9.4, colW: [0.6, 4, 1.2, 3.6], border: { type: "solid", pt: 0.5, color: C.border }, rowH: Array(17).fill(0.26) });
  }

  // SLIDE 56 — Grafici: Fatturato triennale (bar chart)
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Fatturato triennale \u2014 3 scenari", "APPENDICE \u2014 GRAFICI");
    addFooter(s, 56, TOTAL);
    s.addChart(pres.charts.BAR, [
      { name: "Conservativo", labels: ["Anno 1", "Anno 2", "Anno 3"], values: [10715, 17086, 27441] },
      { name: "Base", labels: ["Anno 1", "Anno 2", "Anno 3"], values: [17150, 29650, 49650] },
      { name: "Ottimistico", labels: ["Anno 1", "Anno 2", "Anno 3"], values: [27973, 49140, 81500] },
    ], {
      x: 0.6, y: 1.2, w: 8.8, h: 3.8, barDir: "col",
      chartColors: [C.orange, C.accent, C.accent2],
      chartArea: { fill: { color: C.bgCard }, roundedCorners: true },
      catAxisLabelColor: C.textSec, valAxisLabelColor: C.textSec,
      valGridLine: { color: C.border, size: 0.5 }, catGridLine: { style: "none" },
      showValue: true, dataLabelPosition: "outEnd", dataLabelColor: C.textPri,
      legendPos: "b", legendColor: C.textSec,
    });
  }

  // SLIDE 57 — Grafici: Netto founder — UPDATED
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Netto founder triennale \u2014 confronto", "APPENDICE \u2014 GRAFICI");
    addFooter(s, 57, TOTAL);
    s.addChart(pres.charts.BAR, [
      { name: "Senza partner", labels: ["Anno 1", "Anno 2", "Anno 3"], values: [-112, 2165, 3600] },
      { name: "Con partner (base)", labels: ["Anno 1", "Anno 2", "Anno 3"], values: [1080, 1935, 7585] },
      { name: "Con partner (ottim.)", labels: ["Anno 1", "Anno 2", "Anno 3"], values: [4765, 8790, 13107] },
    ], {
      x: 0.6, y: 1.2, w: 8.8, h: 3.8, barDir: "col",
      chartColors: [C.orange, C.accent, C.accent2],
      chartArea: { fill: { color: C.bgCard }, roundedCorners: true },
      catAxisLabelColor: C.textSec, valAxisLabelColor: C.textSec,
      valGridLine: { color: C.border, size: 0.5 }, catGridLine: { style: "none" },
      showValue: true, dataLabelPosition: "outEnd", dataLabelColor: C.textPri,
      legendPos: "b", legendColor: C.textSec,
    });
  }

  // SLIDE 58 — Chiusura
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    // Corner accents
    s.addShape(pres.shapes.RECTANGLE, { x: 7.5, y: 0, w: 2.5, h: 0.12, fill: { color: C.accent } });
    s.addShape(pres.shapes.RECTANGLE, { x: 9.88, y: 0, w: 0.12, h: 2.5, fill: { color: C.accent } });
    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.5, w: 2.5, h: 0.12, fill: { color: C.accent } });
    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 3.12, w: 0.12, h: 2.5, fill: { color: C.accent } });

    s.addText([
      { text: "FitManager", options: { fontSize: 42, bold: true, color: C.white, fontFace: "Trebuchet MS", breakLine: true } },
      { text: "Studio+", options: { fontSize: 42, bold: true, color: C.accent, fontFace: "Trebuchet MS" } },
    ], { x: 0.8, y: 1.2, w: 8.4, h: 1.2, margin: 0 });

    s.addText("Il sistema completo per il Personal Trainer Evoluto", {
      x: 0.8, y: 2.4, w: 8.4, h: 0.4, margin: 0, fontSize: 18, fontFace: "Calibri", color: C.textSec, italic: true,
    });
    s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 3.0, w: 3, h: 0.03, fill: { color: C.accent } });
    s.addText("Il prodotto \u00E8 completo. La prima utilizzatrice reale lo usa ogni giorno.\nCerchiamo un partner per accelerare \u2014 il business parte anche senza.", {
      x: 0.8, y: 3.3, w: 8.4, h: 0.6, margin: 0, fontSize: 13, fontFace: "Calibri", color: C.textSec,
    });
    s.addText("Giacomo Verardo", { x: 0.8, y: 4.5, w: 4, h: 0.25, margin: 0, fontSize: 11, fontFace: "Calibri", color: C.textMuted });
    s.addText("Business Plan v4.3 \u2014 27 marzo 2026 | Confidenziale", { x: 0.8, y: 4.75, w: 5, h: 0.25, margin: 0, fontSize: 10, fontFace: "Calibri", color: C.textMuted });
    s.addText("58 / 58", { x: 8.5, y: 5.2, w: 1, h: 0.3, fontSize: 8, color: C.textMuted, fontFace: "Calibri", align: "right" });
  }

  // ============================================================
  // WRITE FILE
  // ============================================================
  await pres.writeFile({ fileName: "FitManager_Business_Plan_2026.pptx" });
  console.log("Done: FitManager_Business_Plan_2026.pptx (58 slides)");

}

build().catch(err => { console.error(err); process.exit(1); });

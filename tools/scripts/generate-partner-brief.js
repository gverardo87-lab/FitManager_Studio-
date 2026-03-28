const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");

// --- Icon rendering ---
function renderIconSvg(IconComponent, color = "#000000", size = 256) {
  return ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
}

async function iconToBase64Png(IconComponent, color, size = 256) {
  const svg = renderIconSvg(IconComponent, color, size);
  const pngBuffer = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + pngBuffer.toString("base64");
}

// --- Palette: Dark premium fitness ---
const C = {
  bg:       "0F1117",   // near-black
  bgCard:   "1A1D27",   // dark card
  bgLight:  "F7F8FA",   // light slide bg
  accent:   "00C896",   // emerald green (fitness energy)
  accent2:  "0891B2",   // teal
  accent3:  "F59E0B",   // amber warning
  white:    "FFFFFF",
  gray:     "94A3B8",
  grayDark: "64748B",
  grayLine: "2A2D3A",
  text:     "E2E8F0",
  textDark: "1E293B",
  red:      "EF4444",
  green:    "22C55E",
};

const FONT_H = "Trebuchet MS";
const FONT_B = "Calibri";

function makeShadow() {
  return { type: "outer", blur: 8, offset: 3, angle: 135, color: "000000", opacity: 0.25 };
}

function makeCardShadow() {
  return { type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.18 };
}

// Helper: add a subtle bottom bar
function addFooter(slide, text) {
  slide.addShape(slide._slideLayout ? "rect" : "rect", {}); // noop
  slide.addText(text, {
    x: 0, y: 5.25, w: 10, h: 0.375,
    fontSize: 8, fontFace: FONT_B, color: C.grayDark,
    align: "center", valign: "middle"
  });
}

// Helper: dark slide base with thin accent line
function darkSlide(pres, opts = {}) {
  const slide = pres.addSlide();
  slide.background = { color: C.bg };
  // thin accent line at top
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.04, fill: { color: C.accent }
  });
  if (opts.footer !== false) {
    slide.addText("FitManager Studio+ — Partner Brief  |  AVGV Technologies  |  Marzo 2026", {
      x: 0, y: 5.25, w: 10, h: 0.375,
      fontSize: 7.5, fontFace: FONT_B, color: C.grayDark, align: "center", valign: "middle"
    });
  }
  return slide;
}

// Helper: light slide
function lightSlide(pres) {
  const slide = pres.addSlide();
  slide.background = { color: C.bgLight };
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.04, fill: { color: C.accent }
  });
  slide.addText("FitManager Studio+ — Partner Brief  |  AVGV Technologies  |  Marzo 2026", {
    x: 0, y: 5.25, w: 10, h: 0.375,
    fontSize: 7.5, fontFace: FONT_B, color: C.grayDark, align: "center", valign: "middle"
  });
  return slide;
}

// Helper: section title (left-aligned)
function addTitle(slide, title, opts = {}) {
  slide.addText(title, {
    x: opts.x || 0.6, y: opts.y || 0.25, w: opts.w || 8.8, h: 0.55,
    fontSize: opts.fontSize || 28, fontFace: FONT_H, color: opts.color || C.white,
    bold: true, margin: 0
  });
}

// Helper: subtitle / tagline
function addSubtitle(slide, text, opts = {}) {
  slide.addText(text, {
    x: opts.x || 0.6, y: opts.y || 0.85, w: opts.w || 8.8, h: 0.4,
    fontSize: opts.fontSize || 13, fontFace: FONT_B, color: opts.color || C.gray,
    italic: true, margin: 0
  });
}

// Helper: card shape
function addCard(slide, pres, x, y, w, h, fillColor) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: fillColor || C.bgCard },
    shadow: makeCardShadow()
  });
}

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Giacomo Verardo — AVGV Technologies";
  pres.title = "FitManager Studio+ — Partner Brief";

  // --- Pre-render icons ---
  const { FaShieldAlt, FaDumbbell, FaUsers, FaWhatsapp, FaChartLine, FaServer,
          FaLock, FaAppleAlt, FaBrain, FaRocket, FaHandshake, FaCheckCircle,
          FaExclamationTriangle, FaClock, FaUserMd, FaMoneyBillWave, FaHeart,
          FaStar, FaTimes, FaCheck, FaMicrochip, FaLaptop, FaBolt, FaGlobe,
          FaEnvelope, FaPhone } = require("react-icons/fa");

  const icons = {};
  const iconList = [
    ["shield", FaShieldAlt, C.accent],
    ["dumbbell", FaDumbbell, C.accent],
    ["users", FaUsers, C.accent],
    ["whatsapp", FaWhatsapp, "25D366"],
    ["chart", FaChartLine, C.accent],
    ["server", FaServer, C.accent2],
    ["lock", FaLock, C.accent],
    ["apple", FaAppleAlt, C.accent],
    ["brain", FaBrain, C.accent2],
    ["rocket", FaRocket, C.accent],
    ["handshake", FaHandshake, C.accent],
    ["check", FaCheckCircle, C.green],
    ["warning", FaExclamationTriangle, C.accent3],
    ["clock", FaClock, C.accent],
    ["usermd", FaUserMd, C.accent],
    ["money", FaMoneyBillWave, C.accent],
    ["heart", FaHeart, C.red],
    ["star", FaStar, C.accent3],
    ["times", FaTimes, C.red],
    ["checkG", FaCheck, C.green],
    ["chip", FaMicrochip, C.accent2],
    ["laptop", FaLaptop, C.accent],
    ["bolt", FaBolt, C.accent3],
    ["globe", FaGlobe, C.accent],
  ];
  for (const [key, comp, color] of iconList) {
    icons[key] = await iconToBase64Png(comp, `#${color}`);
  }

  // =============================================
  // SLIDE 1 — Cover
  // =============================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    // Large accent rectangle left side
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 0.12, h: 5.625, fill: { color: C.accent }
    });
    // Title block
    s.addText("PARTNER BRIEF", {
      x: 0.8, y: 0.8, w: 8, h: 0.5,
      fontSize: 14, fontFace: FONT_B, color: C.accent,
      bold: true, charSpacing: 6, margin: 0
    });
    s.addText("FitManager Studio+", {
      x: 0.8, y: 1.4, w: 8.5, h: 1.0,
      fontSize: 44, fontFace: FONT_H, color: C.white, bold: true, margin: 0
    });
    s.addText("Il sistema completo per il\nPersonal Trainer Evoluto", {
      x: 0.8, y: 2.5, w: 8, h: 0.8,
      fontSize: 20, fontFace: FONT_B, color: C.text, margin: 0
    });
    // Separator line
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.8, y: 3.5, w: 2.5, h: 0.035, fill: { color: C.accent }
    });
    // Meta info
    s.addText([
      { text: "Destinatario: ", options: { bold: true, color: C.gray } },
      { text: "Alessio Crociani — Winning Tribe", options: { color: C.text } },
      { text: "\n", options: { breakLine: true } },
      { text: "Versione 1.0 — Marzo 2026  |  Giacomo Verardo  |  AVGV Technologies", options: { color: C.gray } }
    ], {
      x: 0.8, y: 3.75, w: 8, h: 0.7,
      fontSize: 11, fontFace: FONT_B, margin: 0, paraSpaceAfter: 4
    });
    // Confidential note
    s.addText("Questo documento è una sintesi orientata al partner. I dettagli completi sono disponibili nel Business Plan v4.3 e nello Strategy Plan v3.1, condivisibili previa intesa di riservatezza.", {
      x: 0.8, y: 4.55, w: 7.5, h: 0.45,
      fontSize: 9, fontFace: FONT_B, color: C.grayDark, italic: true, margin: 0
    });
    // Icon cluster bottom-right
    s.addImage({ data: icons.dumbbell, x: 8.5, y: 3.8, w: 0.5, h: 0.5 });
    s.addImage({ data: icons.chart, x: 9.1, y: 4.1, w: 0.4, h: 0.4 });
  }

  // =============================================
  // SLIDE 2 — Il problema
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "Il problema che ogni trainer conosce");

    // Story block
    addCard(s, pres, 0.6, 1.0, 8.8, 1.2, "1E2130");
    s.addText("Marco ha 32 clienti. Gestisce le anamnesi su fogli Word, le schede su PDF, i pagamenti su Excel. Ogni lunedì perde due ore a ricostruire chi ha pagato e chi no. Un mese fa ha dimenticato che un cliente aveva un'ernia lombare e gli ha assegnato stacchi da terra. Il cliente non è tornato.", {
      x: 0.85, y: 1.1, w: 8.3, h: 1.0,
      fontSize: 11.5, fontFace: FONT_B, color: C.text, italic: true, margin: 0
    });

    s.addText("Marco non è un caso isolato. È la norma.", {
      x: 0.6, y: 2.35, w: 8.8, h: 0.35,
      fontSize: 12, fontFace: FONT_B, color: C.accent, bold: true, margin: 0
    });

    // 6 problems as 2x3 grid
    const problems = [
      ["clock", "3-5 ore/settimana", "perse in amministrazione"],
      ["users", "Tetto ai clienti", "oltre 25-30 il sistema crolla"],
      ["warning", "Nessuna visione unificata", "anamnesi, schede, pagamenti sparsi"],
      ["money", "Contabilità dispersa", "rate dimenticate, nessun report"],
      ["heart", "Rischio errori clinici", "condizioni patologiche ignorate"],
      ["chart", "Impossibilità di differenziarsi", "senza dati, tutti uguali"],
    ];
    const startY = 2.9;
    problems.forEach((p, i) => {
      const col = i % 3;
      const row = Math.floor(i / 3);
      const cx = 0.6 + col * 3.1;
      const cy = startY + row * 1.15;
      addCard(s, pres, cx, cy, 2.85, 0.95, C.bgCard);
      s.addImage({ data: icons[p[0]], x: cx + 0.15, y: cy + 0.22, w: 0.35, h: 0.35 });
      s.addText(p[1], {
        x: cx + 0.6, y: cy + 0.12, w: 2.0, h: 0.35,
        fontSize: 11, fontFace: FONT_H, color: C.white, bold: true, margin: 0
      });
      s.addText(p[2], {
        x: cx + 0.6, y: cy + 0.48, w: 2.0, h: 0.35,
        fontSize: 9.5, fontFace: FONT_B, color: C.gray, margin: 0
      });
    });
  }

  // =============================================
  // SLIDE 3 — Il competitor vero
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "Il competitor vero");
    addSubtitle(s, "Non è un altro software. È l'abitudine.");

    addCard(s, pres, 0.6, 1.5, 8.8, 1.6, "1E2130");
    s.addText("Il trainer usa WhatsApp ed Excel perché \"ha sempre fatto così\" — non perché funzioni, ma perché nessuno gli ha offerto qualcosa di meglio che rispetti il suo modo di lavorare.", {
      x: 0.85, y: 1.65, w: 8.3, h: 0.7,
      fontSize: 13, fontFace: FONT_B, color: C.text, margin: 0
    });
    s.addText("WhatsApp è il centro del workflow. Qualunque soluzione che chieda di abbandonarlo parte sconfitta.", {
      x: 0.85, y: 2.4, w: 8.3, h: 0.5,
      fontSize: 12, fontFace: FONT_B, color: C.gray, margin: 0
    });

    // Big statement
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: 3.5, w: 8.8, h: 0.8, fill: { color: C.accent }, shadow: makeShadow()
    });
    s.addText("La soluzione giusta non sostituisce WhatsApp — lo potenzia.", {
      x: 0.6, y: 3.5, w: 8.8, h: 0.8,
      fontSize: 18, fontFace: FONT_H, color: C.bg, bold: true,
      align: "center", valign: "middle", margin: 0
    });

    s.addImage({ data: icons.whatsapp, x: 4.5, y: 4.6, w: 0.6, h: 0.6 });
  }

  // =============================================
  // SLIDE 4 — FitManager Studio+
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "FitManager Studio+");
    addSubtitle(s, "Software + dispositivo dedicato. Si compra una volta, non si paga ogni mese.");

    const areas = [
      ["users",    "CRM completo",        "Clienti, contratti, pagamenti,\nagenda, cassa"],
      ["usermd",   "Clinico",             "Anamnesi guidata, misurazioni,\navatar, prontezza"],
      ["dumbbell", "Allenamento",         "500 esercizi con progressioni.\nScheda in 5 minuti"],
      ["shield",   "Protezione errori",   "Safety Engine: condizioni cliniche,\nregole automatiche"],
      ["apple",    "Nutrizione",          "Database CREA ufficiale italiano,\npiani settimanali LARN"],
      ["whatsapp", "Comunicazione",       "WhatsApp semi-automatico +\nemail SMTP integrata"],
    ];

    areas.forEach((a, i) => {
      const col = i % 3;
      const row = Math.floor(i / 3);
      const cx = 0.6 + col * 3.1;
      const cy = 1.5 + row * 1.8;
      addCard(s, pres, cx, cy, 2.85, 1.55, C.bgCard);
      // accent left border
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: cy, w: 0.06, h: 1.55, fill: { color: C.accent }
      });
      s.addImage({ data: icons[a[0]], x: cx + 0.2, y: cy + 0.2, w: 0.4, h: 0.4 });
      s.addText(a[1], {
        x: cx + 0.7, y: cy + 0.18, w: 1.95, h: 0.35,
        fontSize: 12, fontFace: FONT_H, color: C.white, bold: true, margin: 0
      });
      s.addText(a[2], {
        x: cx + 0.2, y: cy + 0.75, w: 2.45, h: 0.65,
        fontSize: 10, fontFace: FONT_B, color: C.gray, margin: 0
      });
    });
  }

  // =============================================
  // SLIDE 5 — WhatsApp come ponte di adozione
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "WhatsApp come ponte di adozione");
    addSubtitle(s, "La prima feature che il trainer usa — valore dal primo giorno.");

    // Left: description
    s.addText("15 template pre-compilati", {
      x: 0.6, y: 1.4, w: 4.5, h: 0.4,
      fontSize: 16, fontFace: FONT_H, color: C.accent, bold: true, margin: 0
    });
    s.addText("Sollecito rata, conferma appuntamento, scheda pronta, benvenuto, auguri, rinnovo.", {
      x: 0.6, y: 1.85, w: 4.5, h: 0.5,
      fontSize: 11, fontFace: FONT_B, color: C.gray, margin: 0
    });

    // Flow: 3 steps
    const steps = [
      ["1", "Un click", "WhatsApp si apre con il\nmessaggio già pronto"],
      ["2", "Il trainer rivede", "Nome, data, importo\ngià compilati"],
      ["3", "Invia", "Nessun bot, nessun\nautomatismo impersonale"],
    ];
    steps.forEach((st, i) => {
      const cy = 2.6 + i * 0.85;
      addCard(s, pres, 0.6, cy, 4.5, 0.7, C.bgCard);
      // Step number circle
      s.addShape(pres.shapes.OVAL, {
        x: 0.75, y: cy + 0.12, w: 0.45, h: 0.45, fill: { color: C.accent }
      });
      s.addText(st[0], {
        x: 0.75, y: cy + 0.12, w: 0.45, h: 0.45,
        fontSize: 16, fontFace: FONT_H, color: C.bg, bold: true,
        align: "center", valign: "middle", margin: 0
      });
      s.addText(st[1], {
        x: 1.35, y: cy + 0.08, w: 1.8, h: 0.3,
        fontSize: 12, fontFace: FONT_H, color: C.white, bold: true, margin: 0
      });
      s.addText(st[2], {
        x: 3.1, y: cy + 0.08, w: 1.85, h: 0.55,
        fontSize: 9.5, fontFace: FONT_B, color: C.gray, margin: 0
      });
    });

    // Right side: big WhatsApp icon + statement
    s.addImage({ data: icons.whatsapp, x: 6.8, y: 1.8, w: 1.2, h: 1.2 });
    addCard(s, pres, 5.5, 3.2, 4.1, 1.6, "1E2130");
    s.addText("Zero curva di apprendimento", {
      x: 5.7, y: 3.35, w: 3.7, h: 0.35,
      fontSize: 14, fontFace: FONT_H, color: C.accent, bold: true, margin: 0
    });
    s.addText("Non serve imparare il sistema per trarne valore immediato. È la porta d'ingresso naturale.", {
      x: 5.7, y: 3.8, w: 3.7, h: 0.8,
      fontSize: 11, fontFace: FONT_B, color: C.text, margin: 0
    });
  }

  // =============================================
  // SLIDE 6 — La FitManager Box
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "La FitManager Box");
    addSubtitle(s, "Un piccolo dispositivo dedicato che il trainer mette nel suo studio.");

    // Left: description
    s.addText("Lo attacca alla corrente e al WiFi — fine.", {
      x: 0.6, y: 1.4, w: 5, h: 0.4,
      fontSize: 14, fontFace: FONT_B, color: C.text, margin: 0
    });
    s.addText("Da quel momento accede a FitManager da qualunque dispositivo: telefono, tablet, PC.", {
      x: 0.6, y: 1.85, w: 5, h: 0.45,
      fontSize: 12, fontFace: FONT_B, color: C.gray, margin: 0
    });

    // 4 features
    const feats = [
      ["lock",   "I dati non vanno mai in cloud"],
      ["server", "Sempre acceso, non dipende dal PC"],
      ["shield", "Backup automatico notturno"],
      ["bolt",   "Consumo: ~€10/anno di elettricità"],
    ];
    feats.forEach((f, i) => {
      const cy = 2.55 + i * 0.6;
      s.addImage({ data: icons[f[0]], x: 0.8, y: cy + 0.05, w: 0.35, h: 0.35 });
      s.addText(f[1], {
        x: 1.3, y: cy, w: 4.5, h: 0.4,
        fontSize: 12, fontFace: FONT_B, color: C.text, margin: 0
      });
    });

    // Right: highlight card
    addCard(s, pres, 5.8, 1.4, 3.8, 3.4, C.bgCard);
    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.8, y: 1.4, w: 3.8, h: 0.06, fill: { color: C.accent }
    });
    s.addImage({ data: icons.server, x: 7.3, y: 1.7, w: 0.8, h: 0.8 });
    s.addText("Trasforma la debolezza in punto di forza", {
      x: 6.0, y: 2.65, w: 3.4, h: 0.7,
      fontSize: 14, fontFace: FONT_H, color: C.accent, bold: true,
      align: "center", margin: 0
    });
    s.addText("I dati sono tuoi,\nnel tuo studio.", {
      x: 6.0, y: 3.4, w: 3.4, h: 0.6,
      fontSize: 16, fontFace: FONT_H, color: C.white, bold: true,
      align: "center", margin: 0
    });
    s.addText("€449 una tantum", {
      x: 6.0, y: 4.15, w: 3.4, h: 0.35,
      fontSize: 12, fontFace: FONT_B, color: C.gray,
      align: "center", margin: 0
    });
  }

  // =============================================
  // SLIDE 7 — Stato del prodotto
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "Stato del prodotto");
    addSubtitle(s, "Non è un prototipo. È un prodotto in uso reale.");

    s.addText("Il prodotto è completo e funzionante (v1.0.5). La prima utilizzatrice reale — una chinesiologia di Genova — lo usa quotidianamente.", {
      x: 0.6, y: 1.4, w: 8.8, h: 0.5,
      fontSize: 12, fontFace: FONT_B, color: C.text, margin: 0
    });

    // Big stats — 5 across
    const stats = [
      ["45.000+", "Righe di codice"],
      ["395", "Test automatici"],
      ["500", "Esercizi"],
      ["880", "Alimenti CREA"],
      ["5", "Motori scientifici"],
    ];
    stats.forEach((st, i) => {
      const cx = 0.6 + i * 1.88;
      addCard(s, pres, cx, 2.2, 1.7, 1.6, C.bgCard);
      s.addText(st[0], {
        x: cx, y: 2.35, w: 1.7, h: 0.7,
        fontSize: 28, fontFace: FONT_H, color: C.accent, bold: true,
        align: "center", margin: 0
      });
      s.addText(st[1], {
        x: cx, y: 3.1, w: 1.7, h: 0.4,
        fontSize: 10, fontFace: FONT_B, color: C.gray,
        align: "center", margin: 0
      });
    });

    // Motori list
    s.addText("5 Motori Scientifici", {
      x: 0.6, y: 4.1, w: 3, h: 0.35,
      fontSize: 12, fontFace: FONT_H, color: C.accent, bold: true, margin: 0
    });
    const engines = ["Training Science (~3500 LOC)", "Safety Engine (47 condizioni)", "Nutrition Science (~2100 LOC)", "Clinical Analysis", "Smart Programming"];
    s.addText(engines.map((e, i) => ({
      text: e,
      options: { bullet: true, breakLine: i < engines.length - 1, color: C.gray, fontSize: 9.5 }
    })), {
      x: 0.6, y: 4.45, w: 9, h: 0.7,
      fontFace: FONT_B, margin: 0
    });
  }

  // =============================================
  // SLIDE 8 — Nessun competitor diretto
  // =============================================
  {
    const s = lightSlide(pres);
    s.addText("Nessun competitor diretto", {
      x: 0.6, y: 0.25, w: 8.8, h: 0.55,
      fontSize: 28, fontFace: FONT_H, color: C.textDark, bold: true, margin: 0
    });
    s.addText("Nessun prodotto combina architettura locale, scienza integrata e assenza di abbonamento.", {
      x: 0.6, y: 0.85, w: 8.8, h: 0.35,
      fontSize: 12, fontFace: FONT_B, color: C.grayDark, italic: true, margin: 0
    });

    // Comparison table
    const hdr = [
      { text: "Caratteristica", options: { bold: true, color: C.white, fill: { color: C.textDark } } },
      { text: "FitManager", options: { bold: true, color: C.white, fill: { color: C.accent.replace("00C896", "00A87A") } } },
      { text: "Mangofit", options: { bold: true, color: C.white, fill: { color: C.grayDark } } },
      { text: "EvolutionFit", options: { bold: true, color: C.white, fill: { color: C.grayDark } } },
      { text: "Excel+WA", options: { bold: true, color: C.white, fill: { color: C.grayDark } } },
    ];
    const rows = [
      ["Dati nel tuo studio",      "✓", "✗", "✗", "✓"],
      ["Segnala errori patologie",  "✓", "✗", "✗", "✗"],
      ["Nutrizione italiana",       "✓", "✗", "✗", "✗"],
      ["Scienza allenamento",       "✓", "✗", "Base", "✗"],
      ["Pagamento una tantum",      "✓", "✗", "✗", "✓ (€0)"],
      ["Comunicazione WA",          "✓", "Parziale", "Parziale", "Manuale"],
    ];

    const tableData = [hdr];
    rows.forEach(r => {
      tableData.push(r.map((cell, ci) => {
        let color = C.textDark;
        if (ci >= 1) {
          if (cell === "✓") color = "16A34A";
          else if (cell === "✗") color = C.red;
          else color = C.grayDark;
        }
        return { text: cell, options: { color, align: ci === 0 ? "left" : "center", fontSize: 11 } };
      }));
    });

    s.addTable(tableData, {
      x: 0.6, y: 1.4, w: 8.8,
      colW: [2.4, 1.6, 1.6, 1.6, 1.6],
      rowH: 0.42,
      border: { pt: 0.5, color: "E2E8F0" },
      fontFace: FONT_B,
      fontSize: 11
    });
  }

  // =============================================
  // SLIDE 9 — Il mercato
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "Il mercato");

    // Big stats
    const mktStats = [
      ["100.000+", "professionisti fitness\nP.IVA in Italia"],
      ["€3 MLD", "mercato fitness\nItalia"],
      ["+10%", "crescita\nanno su anno"],
      ["10-15K", "segmento target\naperto a strumenti"],
    ];
    mktStats.forEach((st, i) => {
      const cx = 0.6 + i * 2.35;
      addCard(s, pres, cx, 1.1, 2.15, 1.4, C.bgCard);
      s.addText(st[0], {
        x: cx, y: 1.2, w: 2.15, h: 0.6,
        fontSize: 26, fontFace: FONT_H, color: C.accent, bold: true,
        align: "center", margin: 0
      });
      s.addText(st[1], {
        x: cx, y: 1.85, w: 2.15, h: 0.5,
        fontSize: 10, fontFace: FONT_B, color: C.gray,
        align: "center", margin: 0
      });
    });

    // Trends
    s.addText("Trend che favoriscono l'adozione", {
      x: 0.6, y: 2.8, w: 8.8, h: 0.35,
      fontSize: 14, fontFace: FONT_H, color: C.accent, bold: true, margin: 0
    });

    const trends = [
      "Registro CONI (luglio 2023) — obbligo professionalizzazione",
      "GDPR rende il cloud problematico per dati sensibili",
      "Clienti più esigenti: vogliono progressioni misurabili",
    ];
    trends.forEach((t, i) => {
      const cy = 3.3 + i * 0.45;
      s.addImage({ data: icons.check, x: 0.8, y: cy + 0.05, w: 0.25, h: 0.25 });
      s.addText(t, {
        x: 1.2, y: cy, w: 8, h: 0.35,
        fontSize: 11, fontFace: FONT_B, color: C.text, margin: 0
      });
    });

    // Globe
    addCard(s, pres, 0.6, 4.55, 8.8, 0.5, "1E2130");
    s.addImage({ data: icons.globe, x: 0.75, y: 4.6, w: 0.3, h: 0.3 });
    s.addText("L'architettura è progettata per l'internazionalizzazione. La scienza dell'allenamento è universale.", {
      x: 1.2, y: 4.55, w: 7.8, h: 0.5,
      fontSize: 11, fontFace: FONT_B, color: C.accent, bold: true, valign: "middle", margin: 0
    });
  }

  // =============================================
  // SLIDE 10 — La visione: il PT Evoluto
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "La visione: il PT Evoluto");
    addSubtitle(s, "Non vendiamo un software. Creiamo una categoria professionale nuova.");

    const ptTraits = [
      ["chart",    "Traccia tutto",          "Anamnesi, misurazioni, progressione, pagamenti"],
      ["brain",    "Usa la scienza",         "Periodizzazione evidence-based, biomeccanica"],
      ["shield",   "Protegge i clienti",     "Condizioni cliniche, regole automatiche, zero errori"],
      ["users",    "Scala il business",      "40-60 clienti senza perdere qualità"],
      ["star",     "Dimostra i risultati",   "Report, grafici, score scientifici"],
    ];
    ptTraits.forEach((t, i) => {
      const cy = 1.35 + i * 0.6;
      s.addImage({ data: icons[t[0]], x: 0.8, y: cy + 0.05, w: 0.35, h: 0.35 });
      s.addText(t[1], {
        x: 1.3, y: cy, w: 2.5, h: 0.35,
        fontSize: 12, fontFace: FONT_H, color: C.white, bold: true, margin: 0
      });
      s.addText(t[2], {
        x: 3.8, y: cy, w: 5.5, h: 0.35,
        fontSize: 11, fontFace: FONT_B, color: C.gray, margin: 0
      });
    });

    // ROI card
    addCard(s, pres, 0.6, 4.0, 8.8, 1.0, "1A2A1F");
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: 4.0, w: 0.06, h: 1.0, fill: { color: C.accent }
    });
    s.addText("Il PT Evoluto guadagna di più", {
      x: 0.85, y: 4.1, w: 4.5, h: 0.35,
      fontSize: 14, fontFace: FONT_H, color: C.accent, bold: true, margin: 0
    });
    s.addText("Aumento tariffa 10-15% (da €40 a €45-46) con 20 clienti = +€400/mese", {
      x: 0.85, y: 4.5, w: 5, h: 0.35,
      fontSize: 11, fontFace: FONT_B, color: C.text, margin: 0
    });
    s.addText("FitManager si ripaga\nin 30-60 giorni", {
      x: 7.2, y: 4.1, w: 2, h: 0.8,
      fontSize: 16, fontFace: FONT_H, color: C.white, bold: true,
      align: "center", valign: "middle", margin: 0
    });
  }

  // =============================================
  // SLIDE 11 — Perché serve un Industry Partner
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "Perché serve un Industry Partner");
    addSubtitle(s, "Il prodotto è pronto. Il mercato non lo è.");

    s.addText("I trainer non cercano un gestionale — non sanno di averne bisogno. Per questo serve una voce credibile dal settore.", {
      x: 0.6, y: 1.35, w: 8.8, h: 0.5,
      fontSize: 12, fontFace: FONT_B, color: C.text, margin: 0
    });

    // Two columns
    const colW = 4.15;
    // Left: Founder
    addCard(s, pres, 0.6, 2.1, colW, 2.8, C.bgCard);
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: 2.1, w: colW, h: 0.06, fill: { color: C.accent2 }
    });
    s.addText("Il founder porta", {
      x: 0.8, y: 2.25, w: 3.7, h: 0.35,
      fontSize: 14, fontFace: FONT_H, color: C.accent2, bold: true, margin: 0
    });
    const founderItems = [
      "Prodotto completo e funzionante",
      "Competenza tecnica e di dominio",
      "Sviluppo continuo",
      "Supporto e operazioni",
    ];
    s.addText(founderItems.map((item, i) => ({
      text: item,
      options: { bullet: true, breakLine: i < founderItems.length - 1, color: C.text, fontSize: 11 }
    })), {
      x: 0.8, y: 2.7, w: 3.7, h: 1.8,
      fontFace: FONT_B, margin: 0, paraSpaceAfter: 6
    });

    // Right: Partner
    addCard(s, pres, 0.6 + colW + 0.5, 2.1, colW, 2.8, C.bgCard);
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6 + colW + 0.5, y: 2.1, w: colW, h: 0.06, fill: { color: C.accent }
    });
    s.addText("Il partner porta", {
      x: 0.6 + colW + 0.7, y: 2.25, w: 3.7, h: 0.35,
      fontSize: 14, fontFace: FONT_H, color: C.accent, bold: true, margin: 0
    });
    const partnerItems = [
      "Credibilità nel settore fitness",
      "Network attivo di professionisti",
      "Capacità di condurre formazione",
      "Validazione del posizionamento",
    ];
    s.addText(partnerItems.map((item, i) => ({
      text: item,
      options: { bullet: true, breakLine: i < partnerItems.length - 1, color: C.text, fontSize: 11 }
    })), {
      x: 0.6 + colW + 0.7, y: 2.7, w: 3.7, h: 1.8,
      fontFace: FONT_B, margin: 0, paraSpaceAfter: 6
    });

    // Quote
    s.addText("\"Io posso costruire lo strumento. Tu puoi costruire il percorso.\nInsieme creiamo qualcosa che nessuno dei due può creare da solo.\"", {
      x: 1.2, y: 4.7, w: 7.6, h: 0.55,
      fontSize: 11, fontFace: FONT_B, color: C.accent, italic: true,
      align: "center", margin: 0
    });
  }

  // =============================================
  // SLIDE 12 — Il piano: validare prima di scalare
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "Il piano: validare prima di scalare");

    const phases = [
      ["1", "Mesi 1-3", "Proof of Concept", "10 professionisti selezionati\n3 masterclass condotte dal partner\nValidazione: prodotto, categoria, community"],
      ["2", "Mesi 4-6", "Early Adopter", "Testimonial POC come leva\nNetwork del partner + community attiva\nTarget: 15-20 clienti"],
      ["3", "Mesi 7-12", "Scale", "Prezzo pieno, tutti i canali\nCertificazione PT Evoluto in costruzione\nTarget: 3-5 vendite/mese"],
      ["4", "Anno 2+", "Espansione", "Fiere, partnership enti formazione\nLancio versione inglese\nPrimi clienti internazionali"],
    ];

    phases.forEach((p, i) => {
      const cy = 1.0 + i * 1.05;
      addCard(s, pres, 0.6, cy, 8.8, 0.9, C.bgCard);
      // Phase number
      s.addShape(pres.shapes.OVAL, {
        x: 0.75, y: cy + 0.2, w: 0.5, h: 0.5, fill: { color: C.accent }
      });
      s.addText(p[0], {
        x: 0.75, y: cy + 0.2, w: 0.5, h: 0.5,
        fontSize: 18, fontFace: FONT_H, color: C.bg, bold: true,
        align: "center", valign: "middle", margin: 0
      });
      // Timeline label
      s.addText(p[1], {
        x: 1.45, y: cy + 0.08, w: 1.2, h: 0.3,
        fontSize: 10, fontFace: FONT_B, color: C.gray, margin: 0
      });
      s.addText(p[2], {
        x: 1.45, y: cy + 0.38, w: 1.5, h: 0.35,
        fontSize: 13, fontFace: FONT_H, color: C.white, bold: true, margin: 0
      });
      s.addText(p[3], {
        x: 3.3, y: cy + 0.1, w: 5.8, h: 0.7,
        fontSize: 10, fontFace: FONT_B, color: C.gray, margin: 0
      });
    });

    // Risk callout
    addCard(s, pres, 0.6, 5.0, 8.8, 0.15, "1A2A1F");
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: 4.55, w: 8.8, h: 0.55, fill: { color: "1A2A1F" }
    });
    s.addText("Se la POC non funziona, lo scopriamo con 10 persone e ~€1.000. Zero debito, rischio controllato.", {
      x: 0.6, y: 4.55, w: 8.8, h: 0.55,
      fontSize: 12, fontFace: FONT_B, color: C.accent, bold: true,
      align: "center", valign: "middle", margin: 0
    });
  }

  // =============================================
  // SLIDE 13 — L'ecosistema community
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "L'ecosistema community");
    addSubtitle(s, "Il software è lo strumento operativo. L'ecosistema dà valore al software e al professionista.");

    // 4 tiers as horizontal cards
    const tiers = [
      ["Base", "Gratuita", "Forum, knowledge base, networking", C.gray],
      ["PRO", "Annuale", "Aggiornamenti, esercizi, template, supporto", C.accent2],
      ["Inner Circle", "Annuale", "Masterclass, webinar, mastermind, certificazione", C.accent],
      ["Mentorship", "Futuro", "1:1, roadmap personalizzata, max 15-20", C.accent3],
    ];
    tiers.forEach((t, i) => {
      const cy = 1.3 + i * 0.95;
      addCard(s, pres, 0.6, cy, 8.8, 0.8, C.bgCard);
      s.addShape(pres.shapes.RECTANGLE, {
        x: 0.6, y: cy, w: 0.06, h: 0.8, fill: { color: t[3] }
      });
      s.addText(t[0], {
        x: 0.85, y: cy + 0.1, w: 2, h: 0.3,
        fontSize: 14, fontFace: FONT_H, color: t[3], bold: true, margin: 0
      });
      s.addText(t[1], {
        x: 0.85, y: cy + 0.42, w: 2, h: 0.25,
        fontSize: 10, fontFace: FONT_B, color: C.gray, margin: 0
      });
      s.addText(t[2], {
        x: 3.0, y: cy + 0.15, w: 6.2, h: 0.5,
        fontSize: 11, fontFace: FONT_B, color: C.text, valign: "middle", margin: 0
      });
    });

    // Partner role
    addCard(s, pres, 0.6, 5.15, 8.8, 0.0, C.bgCard); // noop for spacing
    s.addText("Il partner è il cuore dell'Inner Circle — conduce masterclass, facilita mastermind, definisce la certificazione.", {
      x: 0.6, y: 4.7, w: 8.8, h: 0.4,
      fontSize: 11.5, fontFace: FONT_B, color: C.accent, bold: true,
      align: "center", margin: 0
    });
  }

  // =============================================
  // SLIDE 14 — Il modello economico
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "Il modello economico in sintesi");
    addSubtitle(s, "Licenza perpetua — il trainer compra una volta, il software è suo per sempre.");

    // Pricing grid — 2x2
    const prices = [
      ["Licenza software", "€249", "una tantum"],
      ["FitManager Box", "€449", "una tantum"],
      ["Assistenza PRO", "€79", "/anno"],
      ["Inner Circle", "€249", "/anno"],
    ];
    prices.forEach((p, i) => {
      const col = i % 2;
      const row = Math.floor(i / 2);
      const cx = 0.6 + col * 4.6;
      const cy = 1.35 + row * 1.2;
      addCard(s, pres, cx, cy, 4.2, 1.0, C.bgCard);
      s.addText(p[0], {
        x: cx + 0.2, y: cy + 0.12, w: 2.5, h: 0.35,
        fontSize: 12, fontFace: FONT_H, color: C.white, bold: true, margin: 0
      });
      s.addText(p[1], {
        x: cx + 2.5, y: cy + 0.08, w: 1.5, h: 0.45,
        fontSize: 24, fontFace: FONT_H, color: C.accent, bold: true,
        align: "right", margin: 0
      });
      s.addText(p[2], {
        x: cx + 0.2, y: cy + 0.55, w: 3.8, h: 0.3,
        fontSize: 10, fontFace: FONT_B, color: C.gray, margin: 0
      });
    });

    // Key points
    const keyPoints = [
      ["Margini alti", "Nessun costo server (dati locali). Ogni vendita aggiuntiva è quasi interamente margine."],
      ["Break-even", "~3 vendite/mese. Raggiungibile dal mese 5-6."],
      ["3 scenari nel BP", "Conservativo, base, ottimistico — il business sta in piedi in tutti e tre."],
    ];
    keyPoints.forEach((kp, i) => {
      const cy = 3.85 + i * 0.45;
      s.addImage({ data: icons.check, x: 0.8, y: cy + 0.05, w: 0.25, h: 0.25 });
      s.addText([
        { text: kp[0] + "  ", options: { bold: true, color: C.white } },
        { text: kp[1], options: { color: C.gray } }
      ], {
        x: 1.2, y: cy, w: 8, h: 0.35,
        fontSize: 11, fontFace: FONT_B, margin: 0
      });
    });
  }

  // =============================================
  // SLIDE 15 — Con / Senza partner
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "Cosa cambia con il partner: il confronto");

    // Table
    const compHdr = [
      { text: "", options: { fill: { color: C.bgCard } } },
      { text: "Senza partner", options: { bold: true, color: C.white, fill: { color: C.grayDark } } },
      { text: "Con partner", options: { bold: true, color: C.bg, fill: { color: C.accent } } },
    ];
    const compRows = [
      ["Clienti Anno 3", "~100", "~190+"],
      ["Inner Circle", "Non parte", "Attivo dal mese 4"],
      ["PT Evoluto nel mercato", "Resta un'idea", "Inizia a vivere"],
      ["Community", "Non parte", "Parte dalla POC"],
      ["Fatturato cumulativo 3 anni", "Sostenibile", "2x+"],
    ];
    const compTable = [compHdr];
    compRows.forEach(r => {
      compTable.push([
        { text: r[0], options: { bold: true, color: C.white, fontSize: 11 } },
        { text: r[1], options: { color: C.gray, align: "center", fontSize: 11 } },
        { text: r[2], options: { color: C.accent, bold: true, align: "center", fontSize: 11 } },
      ]);
    });
    s.addTable(compTable, {
      x: 0.6, y: 1.2, w: 8.8,
      colW: [3.2, 2.8, 2.8],
      rowH: 0.5,
      border: { pt: 0.5, color: C.grayLine },
      fontFace: FONT_B, fontSize: 11,
      fill: { color: C.bgCard }
    });

    // Statement
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: 4.2, w: 8.8, h: 0.7, fill: { color: "1A2A1F" }
    });
    s.addText("Il business funziona senza partner — più lentamente.\nCon il partner, decolla.", {
      x: 0.6, y: 4.2, w: 8.8, h: 0.7,
      fontSize: 14, fontFace: FONT_H, color: C.accent, bold: true,
      align: "center", valign: "middle", margin: 0
    });
  }

  // =============================================
  // SLIDE 16 — La proposta per il partner
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "La proposta per il partner");
    addSubtitle(s, "Struttura a performance: il partner guadagna solo se il progetto genera ricavi.");

    const props = [
      ["money",     "Revenue share differenziato", "Su vendite, rinnovi, masterclass"],
      ["chart",     "Equity minoritaria",          "Maturazione 4 anni con cliff 12 mesi"],
      ["star",      "Proprietà condivisa",         "Registrazioni masterclass (ricavo passivo)"],
    ];
    props.forEach((p, i) => {
      const cy = 1.5 + i * 1.0;
      addCard(s, pres, 0.6, cy, 8.8, 0.85, C.bgCard);
      s.addShape(pres.shapes.RECTANGLE, {
        x: 0.6, y: cy, w: 0.06, h: 0.85, fill: { color: C.accent }
      });
      s.addImage({ data: icons[p[0]], x: 0.85, y: cy + 0.2, w: 0.4, h: 0.4 });
      s.addText(p[1], {
        x: 1.45, y: cy + 0.12, w: 3.5, h: 0.35,
        fontSize: 13, fontFace: FONT_H, color: C.white, bold: true, margin: 0
      });
      s.addText(p[2], {
        x: 1.45, y: cy + 0.48, w: 7.5, h: 0.3,
        fontSize: 11, fontFace: FONT_B, color: C.gray, margin: 0
      });
    });

    // Commitment
    addCard(s, pres, 0.6, 4.55, 4.2, 0.6, "1A2A1F");
    s.addImage({ data: icons.clock, x: 0.8, y: 4.65, w: 0.3, h: 0.3 });
    s.addText("Impegno: 8-10 ore/mese", {
      x: 1.25, y: 4.6, w: 3.3, h: 0.5,
      fontSize: 12, fontFace: FONT_H, color: C.text, bold: true, valign: "middle", margin: 0
    });

    // NDA pointer
    addCard(s, pres, 5.2, 4.55, 4.2, 0.6, "1A2A1F");
    s.addImage({ data: icons.lock, x: 5.4, y: 4.65, w: 0.3, h: 0.3 });
    s.addText("Dettagli nel BP previa NDA", {
      x: 5.85, y: 4.6, w: 3.3, h: 0.5,
      fontSize: 12, fontFace: FONT_H, color: C.accent, bold: true, valign: "middle", margin: 0
    });
  }

  // =============================================
  // SLIDE 17 — Cosa cerchiamo
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "Cosa cerchiamo");

    // Two cards side by side
    // Industry Partner
    addCard(s, pres, 0.6, 1.1, 4.2, 3.0, C.bgCard);
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: 1.1, w: 4.2, h: 0.06, fill: { color: C.accent }
    });
    s.addImage({ data: icons.handshake, x: 2.2, y: 1.35, w: 0.7, h: 0.7 });
    s.addText("INDUSTRY PARTNER", {
      x: 0.8, y: 2.15, w: 3.8, h: 0.35,
      fontSize: 14, fontFace: FONT_H, color: C.accent, bold: true,
      align: "center", margin: 0
    });
    s.addText("Un professionista fitness con esperienza, credibilità e network attivo.\n\nNon un dipendente — un partner con incentivi allineati.", {
      x: 0.8, y: 2.55, w: 3.8, h: 1.2,
      fontSize: 11, fontFace: FONT_B, color: C.text, align: "center", margin: 0
    });

    // Finanziamento
    addCard(s, pres, 5.2, 1.1, 4.2, 3.0, C.bgCard);
    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.2, y: 1.1, w: 4.2, h: 0.06, fill: { color: C.accent3 }
    });
    s.addImage({ data: icons.money, x: 6.8, y: 1.35, w: 0.7, h: 0.7 });
    s.addText("FINANZIAMENTO", {
      x: 5.4, y: 2.15, w: 3.8, h: 0.35,
      fontSize: 14, fontFace: FONT_H, color: C.accent3, bold: true,
      align: "center", margin: 0
    });
    s.addText("€20.000-40.000 dopo validazione POC, con dati reali.\n\nPer marketing strutturato, fiere, primo collaboratore.", {
      x: 5.4, y: 2.55, w: 3.8, h: 1.2,
      fontSize: 11, fontFace: FONT_B, color: C.text, align: "center", margin: 0
    });

    s.addText("Post-POC — solo con dati reali.", {
      x: 0.6, y: 4.3, w: 8.8, h: 0.4,
      fontSize: 12, fontFace: FONT_B, color: C.gray, align: "center", margin: 0
    });
  }

  // =============================================
  // SLIDE 18 — Chi è il founder
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "Chi è il founder");

    s.addText("Giacomo Verardo", {
      x: 0.6, y: 0.9, w: 8.8, h: 0.45,
      fontSize: 20, fontFace: FONT_H, color: C.accent, bold: true, margin: 0
    });

    const bio = [
      ["ship",     "Gestione sistemi complessi", "Anni nella cantieristica navale e operazioni offshore (SAIPEM). Navi, cantieri, operazioni internazionali."],
      ["chip",     "Competenza tecnologica ereditata", "Due anni a fianco del padre, pioniere dell'AI in Italia. Sistemi di visione artificiale per l'industria."],
      ["laptop",   "FitManager", "6 mesi di sviluppo full-time. 45.000 LOC, 395 test, 5 motori scientifici. In uso quotidiano."],
      ["dumbbell", "Competenza di dominio", "Conoscenza diretta del fitness come praticante e istruttore."],
    ];
    // Use available icons (no ship icon, use rocket)
    const bioIcons = [icons.rocket, icons.chip, icons.laptop, icons.dumbbell];
    bio.forEach((b, i) => {
      const cy = 1.55 + i * 0.85;
      addCard(s, pres, 0.6, cy, 8.8, 0.72, C.bgCard);
      s.addImage({ data: bioIcons[i], x: 0.8, y: cy + 0.15, w: 0.4, h: 0.4 });
      s.addText(b[1], {
        x: 1.4, y: cy + 0.08, w: 3.5, h: 0.3,
        fontSize: 12, fontFace: FONT_H, color: C.white, bold: true, margin: 0
      });
      s.addText(b[2], {
        x: 1.4, y: cy + 0.38, w: 7.8, h: 0.3,
        fontSize: 10.5, fontFace: FONT_B, color: C.gray, margin: 0
      });
    });
  }

  // =============================================
  // SLIDE 19 — Prossimi passi
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "Prossimi passi");

    const steps = [
      ["Intesa di riservatezza", "Per condividere BP e Strategy Plan completi"],
      ["Demo live", "15 minuti: dal nuovo cliente al messaggio WhatsApp al Safety Engine"],
      ["Definizione ruoli e struttura", "Sulla base dei documenti completi"],
      ["Identificazione dei 10 Fondatori", "Insieme, dal network combinato"],
      ["Lancio POC", "90 giorni per validare tutto"],
    ];
    steps.forEach((st, i) => {
      const cy = 1.1 + i * 0.85;
      addCard(s, pres, 0.6, cy, 8.8, 0.72, C.bgCard);
      // Number
      s.addShape(pres.shapes.OVAL, {
        x: 0.8, y: cy + 0.12, w: 0.48, h: 0.48, fill: { color: C.accent }
      });
      s.addText(String(i + 1), {
        x: 0.8, y: cy + 0.12, w: 0.48, h: 0.48,
        fontSize: 18, fontFace: FONT_H, color: C.bg, bold: true,
        align: "center", valign: "middle", margin: 0
      });
      s.addText(st[0], {
        x: 1.5, y: cy + 0.08, w: 4, h: 0.3,
        fontSize: 13, fontFace: FONT_H, color: C.white, bold: true, margin: 0
      });
      s.addText(st[1], {
        x: 1.5, y: cy + 0.38, w: 7.5, h: 0.3,
        fontSize: 11, fontFace: FONT_B, color: C.gray, margin: 0
      });
    });
  }

  // =============================================
  // SLIDE 20 — Chiusura
  // =============================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    // Full-width accent at top
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.accent }
    });
    // Left accent bar
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 0.12, h: 5.625, fill: { color: C.accent }
    });

    s.addText("FitManager Studio+", {
      x: 0.8, y: 1.0, w: 8.5, h: 0.8,
      fontSize: 38, fontFace: FONT_H, color: C.white, bold: true, margin: 0
    });
    s.addText("Il sistema completo per il Personal Trainer Evoluto", {
      x: 0.8, y: 1.85, w: 8, h: 0.5,
      fontSize: 16, fontFace: FONT_B, color: C.text, margin: 0
    });

    // Separator
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.8, y: 2.55, w: 2.5, h: 0.035, fill: { color: C.accent }
    });

    s.addText("Il prodotto è completo. La prima utilizzatrice reale lo usa ogni giorno.\nLa strategia è chiara. Serve un partner per attivare il volano.", {
      x: 0.8, y: 2.8, w: 8, h: 0.8,
      fontSize: 13, fontFace: FONT_B, color: C.gray, margin: 0
    });

    // Contact
    s.addText("Giacomo Verardo", {
      x: 0.8, y: 3.9, w: 8, h: 0.4,
      fontSize: 18, fontFace: FONT_H, color: C.accent, bold: true, margin: 0
    });
    s.addText("AVGV Technologies", {
      x: 0.8, y: 4.3, w: 8, h: 0.3,
      fontSize: 13, fontFace: FONT_B, color: C.text, margin: 0
    });
    s.addText("Partner Brief v1.0 — Marzo 2026", {
      x: 0.8, y: 4.65, w: 8, h: 0.3,
      fontSize: 11, fontFace: FONT_B, color: C.grayDark, margin: 0
    });

    // Icons cluster
    s.addImage({ data: icons.dumbbell, x: 8.2, y: 4.0, w: 0.5, h: 0.5 });
    s.addImage({ data: icons.heart, x: 8.8, y: 4.3, w: 0.4, h: 0.4 });
  }

  // --- Write file ---
  const path = require("path");
  const outPath = path.join(__dirname, "..", "..", "docs", "FitManager_PartnerBrief.pptx");
  await pres.writeFile({ fileName: outPath });
  console.log("DONE:", outPath);
}

main().catch(err => { console.error(err); process.exit(1); });

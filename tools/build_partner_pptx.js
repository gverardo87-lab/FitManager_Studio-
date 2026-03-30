const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const {
  FaLink, FaUsers, FaMicrophone, FaGlobeEurope,
  FaCheckCircle, FaDumbbell, FaShieldAlt, FaUtensils, FaFileInvoiceDollar,
  FaDesktop, FaGraduationCap, FaComments, FaWrench,
  FaChartLine, FaMicroscope, FaBalanceScale,
  FaWhatsapp, FaMobileAlt, FaClipboardCheck, FaSearchPlus, FaHeart,
  FaLaptop
} = require("react-icons/fa");

// ============================================================
// PALETTE
// ============================================================
const C = {
  bg:        "0F1629",   // very dark navy
  bgCard:    "1A2332",   // card background
  bgCard2:   "232F42",   // lighter card
  accent:    "00B4D8",   // cyan
  accent2:   "06D6A0",   // green
  gold:      "FFD166",   // gold
  red:       "EF476F",   // coral red
  orange:    "F4A261",   // warm orange
  white:     "FFFFFF",
  textPri:   "FFFFFF",
  textSec:   "A0AEC0",   // muted blue-gray
  textMuted: "718096",
  tableBg:   "141E30",
  tableHead: "1E2D45",
  tableRow1: "162036",
  tableRow2: "1A2540",
  border:    "2D3E56",
};

// ============================================================
// ICON HELPER
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
// REUSABLE HELPERS
// ============================================================
function makeShadow() {
  return { type: "outer", blur: 8, offset: 3, angle: 135, color: "000000", opacity: 0.25 };
}

function addFooter(slide, pageNum, totalPages) {
  slide.addText(`FitManager Studio+ \u2014 Documento Operativo Partner`, {
    x: 0.5, y: 5.2, w: 7, h: 0.3,
    fontSize: 8, color: C.textMuted, fontFace: "Calibri",
  });
  slide.addText(`${pageNum} / ${totalPages}`, {
    x: 8.5, y: 5.2, w: 1, h: 0.3,
    fontSize: 8, color: C.textMuted, fontFace: "Calibri", align: "right",
  });
}

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

function card(slide, x, y, w, h, fillColor) {
  slide.addShape(slide._slideLayout ? "rect" : "rect", {
    x, y, w, h, fill: { color: fillColor || C.bgCard },
    shadow: makeShadow(),
  });
}

// since pptxgenjs needs pres.shapes reference, we pass pres
function addCard(pres, slide, x, y, w, h, fillColor) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h, fill: { color: fillColor || C.bgCard },
    shadow: makeShadow(),
  });
}

function addAccentBar(pres, slide, x, y, h, color) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 0.06, h, fill: { color: color || C.accent },
  });
}

// ============================================================
// MAIN
// ============================================================
async function build() {
  // Pre-render all icons
  const icons = {
    link:       await iconB64(FaLink, "#00B4D8"),
    users:      await iconB64(FaUsers, "#06D6A0"),
    mic:        await iconB64(FaMicrophone, "#FFD166"),
    globe:      await iconB64(FaGlobeEurope, "#F4A261"),
    desktop:    await iconB64(FaDesktop, "#00B4D8"),
    grad:       await iconB64(FaGraduationCap, "#06D6A0"),
    comments:   await iconB64(FaComments, "#FFD166"),
    wrench:     await iconB64(FaWrench, "#F4A261"),
    check:      await iconB64(FaCheckCircle, "#06D6A0"),
    dumbbell:   await iconB64(FaDumbbell, "#00B4D8"),
    shield:     await iconB64(FaShieldAlt, "#FFD166"),
    utensils:   await iconB64(FaUtensils, "#F4A261"),
    invoice:    await iconB64(FaFileInvoiceDollar, "#EF476F"),
    chart:      await iconB64(FaChartLine, "#00B4D8"),
    microscope: await iconB64(FaMicroscope, "#06D6A0"),
    balance:    await iconB64(FaBalanceScale, "#FFD166"),
    whatsapp:   await iconB64(FaWhatsapp, "#25D366"),
    mobile:     await iconB64(FaMobileAlt, "#00B4D8"),
    clipboard:  await iconB64(FaClipboardCheck, "#06D6A0"),
    search:     await iconB64(FaSearchPlus, "#FFD166"),
    heart:      await iconB64(FaHeart, "#EF476F"),
    laptop:     await iconB64(FaLaptop, "#00B4D8"),
  };

  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Giacomo Verardo";
  pres.title = "FitManager Studio+ - Documento Operativo Partner";

  const TOTAL = 22;

  // ============================================================
  // SLIDE 1 — COPERTINA
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    // accent shape top-right
    s.addShape(pres.shapes.RECTANGLE, {
      x: 7.5, y: 0, w: 2.5, h: 0.12, fill: { color: C.accent },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 9.88, y: 0, w: 0.12, h: 2.5, fill: { color: C.accent },
    });
    // accent shape bottom-left
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 5.5, w: 2.5, h: 0.12, fill: { color: C.accent },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 3.12, w: 0.12, h: 2.5, fill: { color: C.accent },
    });

    s.addText("DOCUMENTO OPERATIVO PARTNER", {
      x: 0.8, y: 0.9, w: 8.4, h: 0.4, margin: 0,
      fontSize: 12, fontFace: "Calibri", color: C.accent, charSpacing: 6, bold: true,
    });
    s.addText([
      { text: "FitManager", options: { fontSize: 42, bold: true, color: C.white, fontFace: "Trebuchet MS", breakLine: true } },
      { text: "Studio+", options: { fontSize: 42, bold: true, color: C.accent, fontFace: "Trebuchet MS" } },
    ], { x: 0.8, y: 1.5, w: 8.4, h: 1.2, margin: 0 });

    s.addText("Struttura, numeri e piano di lancio", {
      x: 0.8, y: 2.7, w: 8.4, h: 0.4, margin: 0,
      fontSize: 18, fontFace: "Calibri", color: C.textSec, italic: true,
    });

    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.8, y: 3.3, w: 3, h: 0.03, fill: { color: C.accent },
    });

    s.addText("Hai visto il prodotto dal vivo. Sai cosa fa.\nQuesto documento ti mostra la struttura operativa, economica\ne di lancio \u2014 calibrata su quello che possiamo costruire insieme.", {
      x: 0.8, y: 3.55, w: 8.4, h: 0.8, margin: 0,
      fontSize: 12, fontFace: "Calibri", color: C.textSec,
    });

    s.addText("I termini della partnership sono la mia proposta di partenza \u2014 negoziabile.", {
      x: 0.8, y: 4.3, w: 8.4, h: 0.3, margin: 0,
      fontSize: 12, fontFace: "Calibri", color: C.gold, italic: true,
    });

    s.addText("NDA formale entro la settimana (03 Aprile).", {
      x: 0.8, y: 4.6, w: 8.4, h: 0.3, margin: 0,
      fontSize: 11, fontFace: "Calibri", color: C.textMuted,
    });

    s.addText("30 Marzo 2026  |  Giacomo Verardo \u2192 Alessio Crociani", {
      x: 0.8, y: 5.05, w: 8.4, h: 0.25, margin: 0,
      fontSize: 10, fontFace: "Calibri", color: C.textMuted,
    });
  }

  // ============================================================
  // SLIDE 2 — DOVE SIAMO OGGI
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Dove siamo oggi", "Il prodotto \u00E8 completo. In uso quotidiano.");
    addFooter(s, 2, TOTAL);

    // 6 stat cards in 3x2 grid
    const stats = [
      { num: "47.000+", label: "Righe di codice", color: C.accent },
      { num: "395", label: "Test automatici", color: C.accent2 },
      { num: "500", label: "Esercizi con biomeccanica", color: C.gold },
      { num: "880", label: "Alimenti CREA", color: C.orange },
      { num: "7", label: "Motori scientifici", color: C.accent },
      { num: "47", label: "Condizioni cliniche\n(80 regole)", color: C.red },
    ];
    const gx = 0.6, gy = 1.25, cw = 2.9, ch = 1.2, gapX = 0.15, gapY = 0.15;
    stats.forEach((st, i) => {
      const col = i % 3, row = Math.floor(i / 3);
      const cx = gx + col * (cw + gapX);
      const cy = gy + row * (ch + gapY);
      addCard(pres, s, cx, cy, cw, ch);
      // accent top bar
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: cy, w: cw, h: 0.05, fill: { color: st.color },
      });
      s.addText(st.num, {
        x: cx + 0.15, y: cy + 0.15, w: cw - 0.3, h: 0.5, margin: 0,
        fontSize: 30, fontFace: "Trebuchet MS", bold: true, color: st.color,
      });
      s.addText(st.label, {
        x: cx + 0.15, y: cy + 0.7, w: cw - 0.3, h: 0.4, margin: 0,
        fontSize: 11, fontFace: "Calibri", color: C.textSec,
      });
    });

    // body text
    s.addText("La prima utilizzatrice reale (chinesiologa e nutrizionista, Genova) lo usa ogni giorno da 4 settimana.\nLe sue clienti ricevono schede professionali, compilano anamnesi dal telefono e da questa settimana registrano l\u2019allenamento in tempo reale dalla nuova Workout Intelligence.", {
      x: 0.6, y: 3.85, w: 8.8, h: 0.6, margin: 0,
      fontSize: 11, fontFace: "Calibri", color: C.textSec,
    });

    addCard(pres, s, 0.6, 4.5, 8.8, 0.55, "1E2D45");
    s.addText("Cosa manca: non il prodotto. La leva commerciale per portarlo al mercato \u2014 in Italia e (sopratutto) fuori.", {
      x: 0.8, y: 4.55, w: 8.4, h: 0.4, margin: 0,
      fontSize: 13, fontFace: "Calibri", bold: true, color: C.gold,
    });
  }

  // ============================================================
  // SLIDE 3 — IL PRICING
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Il pricing");
    addFooter(s, 3, TOTAL);

    const tHead = [
      { text: "Prodotto", options: { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 12, fontFace: "Calibri" } },
      { text: "Prezzo", options: { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 12, fontFace: "Calibri" } },
      { text: "Costo vivo", options: { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 12, fontFace: "Calibri" } },
      { text: "Margine lordo", options: { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 12, fontFace: "Calibri" } },
    ];
    const rowOpt = (bg) => ({ color: C.textPri, fill: { color: bg }, fontSize: 11, fontFace: "Calibri" });
    const tRows = [
      [
        { text: "Licenza software", options: rowOpt(C.tableRow1) },
        { text: "\u20AC249", options: rowOpt(C.tableRow1) },
        { text: "~\u20AC30", options: rowOpt(C.tableRow1) },
        { text: "\u20AC219 (88%)", options: { ...rowOpt(C.tableRow1), color: C.accent2, bold: true } },
      ],
      [
        { text: "FitManager Box", options: rowOpt(C.tableRow2) },
        { text: "\u20AC449", options: rowOpt(C.tableRow2) },
        { text: "~\u20AC150", options: rowOpt(C.tableRow2) },
        { text: "\u20AC299 (67%)", options: { ...rowOpt(C.tableRow2), color: C.accent2, bold: true } },
      ],
      [
        { text: "Assistenza PRO", options: rowOpt(C.tableRow1) },
        { text: "\u20AC79/anno", options: rowOpt(C.tableRow1) },
        { text: "~\u20AC0", options: rowOpt(C.tableRow1) },
        { text: "\u20AC79 (100%)", options: { ...rowOpt(C.tableRow1), color: C.accent2, bold: true } },
      ],
      [
        { text: "Inner Circle", options: rowOpt(C.tableRow2) },
        { text: "\u20AC249/anno", options: rowOpt(C.tableRow2) },
        { text: "~\u20AC0", options: rowOpt(C.tableRow2) },
        { text: "\u20AC249 (100%)", options: { ...rowOpt(C.tableRow2), color: C.accent2, bold: true } },
      ],
    ];

    s.addTable([tHead, ...tRows], {
      x: 0.6, y: 1.1, w: 8.8,
      colW: [2.8, 1.8, 1.6, 2.6],
      border: { type: "solid", pt: 0.5, color: C.border },
      rowH: [0.4, 0.4, 0.4, 0.4, 0.4],
    });

    s.addText("Licenza perpetua: il trainer compra una volta, il software \u00E8 suo. Nessun server \u2014 i dati sono locali.", {
      x: 0.6, y: 3.3, w: 8.8, h: 0.35, margin: 0,
      fontSize: 12, fontFace: "Calibri", color: C.textSec,
    });

    // Two stat boxes
    addCard(pres, s, 0.6, 3.85, 4.15, 1.1);
    addAccentBar(pres, s, 0.6, 3.85, 1.1, C.accent);
    s.addText("~3 vendite/mese", {
      x: 0.85, y: 3.95, w: 3.8, h: 0.4, margin: 0,
      fontSize: 22, fontFace: "Trebuchet MS", bold: true, color: C.accent,
    });
    s.addText("Break-even operativo", {
      x: 0.85, y: 4.4, w: 3.8, h: 0.3, margin: 0,
      fontSize: 11, fontFace: "Calibri", color: C.textSec,
    });

    addCard(pres, s, 5.25, 3.85, 4.15, 1.1);
    addAccentBar(pres, s, 5.25, 3.85, 1.1, C.gold);
    s.addText("Pricing internazionale", {
      x: 5.5, y: 3.95, w: 3.8, h: 0.4, margin: 0,
      fontSize: 22, fontFace: "Trebuchet MS", bold: true, color: C.gold,
    });
    s.addText("Margine per posizionarsi pi\u00F9 in alto in Scandinavia e mercati maturi", {
      x: 5.5, y: 4.4, w: 3.8, h: 0.4, margin: 0,
      fontSize: 11, fontFace: "Calibri", color: C.textSec,
    });
  }

  // ============================================================
  // SLIDE 4 — COSA PORTA ALESSIO
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Cosa porti tu al tavolo", "Per muovere un mercato che non sa di avere un problema servono asset specifici. Questi sono i tuoi.");
    addFooter(s, 4, TOTAL);

    const items = [
      { icon: icons.link, title: "Credibilit\u00E0 istituzionale nel mercato nordico", desc: "5 anni miglior PT nazionale Nordic Wellness. Insegnante alla Nordic Academy of Sweden.\nNon \u00E8 un contatto commerciale \u2014 \u00E8 un posizionamento costruito in anni.", accent: C.accent },
      { icon: icons.users, title: "Gestione di reti di professionisti", desc: "Coordinatore nazionale rete PT Technogym. Sai costruire, gestire\ne far crescere network di trainer su scala nazionale.", accent: C.accent2 },
      { icon: icons.mic, title: "Corporate wellness per brand internazionali", desc: "Ferrari, Vodafone, Philip Morris, Volvo, Barilla, Marriott.\nUn verticale che FitManager non copre ancora \u2014 e che tu puoi aprire.", accent: C.gold },
      { icon: icons.globe, title: "18.000+ ore di metodo testato sul campo", desc: "27 anni di pratica 1-to-1, mental coaching, chinesiologia.\nUna base metodologica reale per costruire insieme il percorso Inner Circle.", accent: C.orange },
    ];

    items.forEach((it, i) => {
      const cy = 1.2 + i * 0.92;
      addCard(pres, s, 0.6, cy, 8.8, 0.82);
      addAccentBar(pres, s, 0.6, cy, 0.82, it.accent);
      s.addImage({ data: it.icon, x: 0.85, y: cy + 0.15, w: 0.4, h: 0.4 });
      s.addText(it.title, {
        x: 1.4, y: cy + 0.05, w: 7.8, h: 0.32, margin: 0,
        fontSize: 13, fontFace: "Calibri", bold: true, color: C.white,
      });
      s.addText(it.desc, {
        x: 1.4, y: cy + 0.38, w: 7.8, h: 0.38, margin: 0,
        fontSize: 10.5, fontFace: "Calibri", color: C.textSec,
      });
    });

    s.addText("FitManager \u00E8 il motore. Quello che porti tu \u00E8 la leva per metterlo in moto \u2014 in Italia e fuori.", {
      x: 0.6, y: 4.95, w: 8.8, h: 0.25, margin: 0,
      fontSize: 11, fontFace: "Calibri", color: C.textSec, italic: true,
    });
  }

  // ============================================================
  // SLIDE 5 — ARCHITETTURA INTERNAZIONALE
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "L'architettura \u00E8 pronta per l'internazionale", "Progettato con l'internazionalizzazione nell'architettura, non come adattamento.");
    // Footer removed per user preference on this slide

    const blocks = [
      { num: "1", title: "Interfaccia e core", level: "BASSA", levelColor: C.accent2, desc: "Traduzione UI, template, formati data/valuta. ~1 settimana per lingua.", icon: icons.desktop },
      { num: "2", title: "Esercizi e Safety Engine", level: "MEDIA", levelColor: C.gold, desc: "La scienza \u00E8 universale. Serve adattamento terminologico professionale. 2-4 settimane.", icon: icons.dumbbell },
      { num: "3", title: "Nutrizione e compliance", level: "ALTA", levelColor: C.orange, desc: "Database nutrizionali locali (Livsmedelsverket per Svezia, USDA per USA). 2-3 mesi.", icon: icons.utensils },
      { num: "4", title: "Moduli fiscali ed economici", level: "VARIABILE", levelColor: C.red, desc: "Pagamenti, fatturazione per giurisdizione. Da definire per mercato.", icon: icons.invoice },
    ];

    blocks.forEach((b, i) => {
      const cy = 1.2 + i * 0.92;
      addCard(pres, s, 0.6, cy, 8.8, 0.82);

      // number circle
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
        x: 1.45, y: cy + 0.4, w: 5.5, h: 0.35, margin: 0,
        fontSize: 10.5, fontFace: "Calibri", color: C.textSec,
      });

      // complexity badge
      addCard(pres, s, 7.8, cy + 0.2, 1.4, 0.4, b.levelColor);
      s.addText(b.level, {
        x: 7.8, y: cy + 0.2, w: 1.4, h: 0.4, margin: 0,
        fontSize: 11, fontFace: "Calibri", bold: true, color: C.bg, align: "center", valign: "middle",
      });
    });

    addCard(pres, s, 0.6, 4.95, 8.8, 0.4, C.bgCard2);
    s.addText("I Blocchi 1-2 possono essere pronti in svedese in 4-6 settimane. Il prodotto \u00E8 pienamente utilizzabile senza i Blocchi 3-4.", {
      x: 0.8, y: 4.98, w: 8.4, h: 0.35, margin: 0,
      fontSize: 11, fontFace: "Calibri", bold: true, color: C.accent,
    });
  }

  // ============================================================
  // SLIDE 6 — ITALIA PRIMA, INTERNAZIONALE DOPO
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Italia prima, internazionale subito dopo");
    addFooter(s, 6, TOTAL);

    // Timeline vertical
    const phases = [
      { period: "MESI 1-6", title: "Italia. Focus totale.", desc: "POC 10 Fondatori. Consolidamento tecnico con utenti reali.\nSocial proof. Validazione pricing e categoria.", color: C.accent },
      { period: "MESI 4-6", title: "Preparazione internazionale in parallelo", desc: "Blocchi 1-2 tradotti. Primi contatti dalla tua rete.\nPricing e posizionamento mercato target.", color: C.accent2 },
      { period: "MESI 7-12", title: "Pilota internazionale", desc: "5-10 utenti pilota nel mercato target (es. Svezia/Nordic).\nStessa metodologia POC, scala ridotta.", color: C.gold },
      { period: "ANNO 2+", title: "Due mercati attivi", desc: "Italia consolidata + lancio internazionale strutturato.\nTeam, SRL, brand riconosciuto.", color: C.orange },
    ];

    // vertical line
    s.addShape(pres.shapes.RECTANGLE, {
      x: 1.55, y: 1.15, w: 0.04, h: 3.55, fill: { color: C.border },
    });

    phases.forEach((p, i) => {
      const cy = 1.1 + i * 0.92;
      // dot on timeline
      s.addShape(pres.shapes.OVAL, {
        x: 1.39, y: cy + 0.12, w: 0.36, h: 0.36, fill: { color: p.color },
      });
      // period label
      s.addText(p.period, {
        x: 0.1, y: cy + 0.12, w: 1.2, h: 0.36, margin: 0,
        fontSize: 9, fontFace: "Calibri", bold: true, color: p.color, align: "right", valign: "middle",
      });
      // card
      addCard(pres, s, 2.05, cy, 7.35, 0.82);
      addAccentBar(pres, s, 2.05, cy, 0.82, p.color);
      s.addText(p.title, {
        x: 2.25, y: cy + 0.05, w: 7, h: 0.3, margin: 0,
        fontSize: 13, fontFace: "Calibri", bold: true, color: C.white,
      });
      s.addText(p.desc, {
        x: 2.25, y: cy + 0.38, w: 7, h: 0.38, margin: 0,
        fontSize: 10.5, fontFace: "Calibri", color: C.textSec,
      });
    });

    s.addText("Esportare prima di aver consolidato = portare problemi dove non hai credibilit\u00E0. 6 mesi Italia non sono un freno \u2014 sono la base per partire forti fuori.", {
      x: 0.6, y: 4.88, w: 8.8, h: 0.3, margin: 0,
      fontSize: 10.5, fontFace: "Calibri", color: C.textMuted, italic: true,
    });
  }

  // ============================================================
  // SLIDE 7 — CHI GUIDA COSA
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Chi guida cosa", "Una partnership funziona se i ruoli decisionali sono chiari.");
    addFooter(s, 7, TOTAL);

    const colW = 2.8, colGap = 0.2, startX = 0.6;
    const cols = [
      { title: "Tu guidi", color: C.accent2, items: [
        "Selezione dei Fondatori POC",
        "Strategia di ingresso nelle catene e nel mercato internazionale",
        "Strategia corporate wellness",
      ]},
      { title: "Giacomo guida", color: C.accent, items: [
        "Prodotto, roadmap tecnica, architettura",
        "Supporto operativo, sviluppo e manutenzione",
        "Pricing del prodotto base (licenza, Box, PRO)",
      ]},
      { title: "Decidiamo insieme", color: C.gold, items: [
        "Direzione strategica e marketing complessivo",
        "Struttura, contenuti e pricing dell\u2019Inner Circle",
        "Timeline di espansione internazionale",
        "Criteri GO/NO-GO della POC",
      ]},
    ];

    cols.forEach((col, i) => {
      const cx = startX + i * (colW + colGap);
      addCard(pres, s, cx, 1.2, colW, 3.4);
      // top accent
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: 1.2, w: colW, h: 0.06, fill: { color: col.color },
      });
      s.addText(col.title, {
        x: cx + 0.2, y: 1.35, w: colW - 0.4, h: 0.35, margin: 0,
        fontSize: 15, fontFace: "Trebuchet MS", bold: true, color: col.color,
      });
      // items
      const itemTexts = col.items.map((item, j) => ({
        text: item,
        options: { bullet: true, breakLine: j < col.items.length - 1, fontSize: 11, fontFace: "Calibri", color: C.textSec, paraSpaceAfter: 8 },
      }));
      s.addText(itemTexts, {
        x: cx + 0.2, y: 1.85, w: colW - 0.4, h: 2.5, margin: 0,
      });
    });

    s.addText("Non \u00E8 \"il tuo input \u00E8 benvenuto.\" \u00C8 chi ha l'ultima parola su cosa.", {
      x: 0.6, y: 4.85, w: 8.8, h: 0.3, margin: 0,
      fontSize: 12, fontFace: "Calibri", bold: true, color: C.textSec, italic: true,
    });
  }

  // ============================================================
  // SLIDE 8 — PARTNERSHIP A FASI
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "La partnership a fasi", "Nessuno dei due sa ancora come funzioner\u00E0 lavorare insieme.");
    addFooter(s, 8, TOTAL);

    const phases = [
      { label: "FASE 1", title: "POC (mesi 1-3): testiamo la partnership", desc: "Revenue share solo sulle vendite POC (20%). Nessuna equity ancora.\nImpegno: ~15-20 ore in 90 giorni.\nAl giorno 90: decisione GO/NO-GO basata sui dati.", color: C.accent },
      { label: "FASE 2", title: "Post-validazione (mesi 4-12): partnership piena", desc: "Revenue share completo attivo. Prima tranche equity matura.\nInner Circle co-progettato e operativo.\nPreparazione internazionale.\nImpegno stimato: ~8-12 ore/mese.", color: C.accent2 },
      { label: "FASE 3", title: "Internazionale (Anno 2+): espansione", desc: "Termini per i mercati internazionali definiti alla luce\ndei risultati. Potenzialmente con revenue pool dedicato\no percentuali pi\u00F9 alte. A questi volumi, il progetto\ndiventa un asset con opzioni \u2014 crescita autonoma\no interesse da parte di player pi\u00F9 grandi del settore.\nImpegno: da definire insieme sulla base dei mercati aperti.", color: C.gold },
    ];

    phases.forEach((p, i) => {
      const cy = 1.15 + i * 1.15;
      addCard(pres, s, 0.6, cy, 8.8, 1.05);
      addAccentBar(pres, s, 0.6, cy, 1.05, p.color);
      // badge
      s.addShape(pres.shapes.RECTANGLE, {
        x: 0.85, y: cy + 0.12, w: 0.9, h: 0.32, fill: { color: p.color },
      });
      s.addText(p.label, {
        x: 0.85, y: cy + 0.12, w: 0.9, h: 0.32, margin: 0,
        fontSize: 10, fontFace: "Calibri", bold: true, color: C.bg, align: "center", valign: "middle",
      });
      s.addText(p.title, {
        x: 1.95, y: cy + 0.08, w: 7.2, h: 0.3, margin: 0,
        fontSize: 13, fontFace: "Calibri", bold: true, color: C.white,
      });
      s.addText(p.desc, {
        x: 1.95, y: cy + 0.4, w: 7.2, h: 0.6, margin: 0,
        fontSize: 10.5, fontFace: "Calibri", color: C.textSec,
      });
    });

    addCard(pres, s, 0.6, 4.7, 8.8, 0.4, C.bgCard2);
    s.addText("Se la POC non funziona, ci fermiamo. Costo: 3 mesi di tempo e ~\u20AC1.000. Nessuna equity emessa, nessun debito.", {
      x: 0.8, y: 4.73, w: 8.4, h: 0.35, margin: 0,
      fontSize: 11, fontFace: "Calibri", bold: true, color: C.accent2,
    });
  }

  // ============================================================
  // SLIDE 9 — REVENUE SHARE
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Il revenue share", "Due logiche diverse per due cose diverse.");
    addFooter(s, 9, TOTAL);

    // Two big cards side by side
    const cardW = 4.25;

    // Left: 20%
    addCard(pres, s, 0.6, 1.2, cardW, 2.8);
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: 1.2, w: cardW, h: 0.06, fill: { color: C.accent },
    });
    s.addText("20%", {
      x: 0.8, y: 1.4, w: 3.85, h: 0.65, margin: 0,
      fontSize: 48, fontFace: "Trebuchet MS", bold: true, color: C.accent,
    });
    s.addText("Prodotto e PRO", {
      x: 0.8, y: 2.1, w: 3.85, h: 0.3, margin: 0,
      fontSize: 16, fontFace: "Calibri", bold: true, color: C.white,
    });
    s.addText("Licenze, Box, assistenza annuale", {
      x: 0.8, y: 2.4, w: 3.85, h: 0.25, margin: 0,
      fontSize: 11, fontFace: "Calibri", color: C.textMuted,
    });
    s.addText("Il prodotto e la sua manutenzione. Su tutte le vendite, senza distinguere la fonte.", {
      x: 0.8, y: 2.75, w: 3.85, h: 0.9, margin: 0,
      fontSize: 10.5, fontFace: "Calibri", color: C.textSec,
    });

    // Right: 50%
    addCard(pres, s, 5.15, 1.2, cardW, 2.8);
    s.addShape(pres.shapes.RECTANGLE, {
      x: 5.15, y: 1.2, w: cardW, h: 0.06, fill: { color: C.gold },
    });
    s.addText("50%", {
      x: 5.35, y: 1.4, w: 3.85, h: 0.65, margin: 0,
      fontSize: 48, fontFace: "Trebuchet MS", bold: true, color: C.gold,
    });
    s.addText("Inner Circle + Masterclass", {
      x: 5.35, y: 2.1, w: 3.85, h: 0.3, margin: 0,
      fontSize: 16, fontFace: "Calibri", bold: true, color: C.white,
    });
    s.addText("Il progetto congiunto", {
      x: 5.35, y: 2.4, w: 3.85, h: 0.25, margin: 0,
      fontSize: 11, fontFace: "Calibri", color: C.textMuted,
    });
    s.addText("Il metodo e lo strumento sono inseparabili. L\u2019IC funziona perch\u00E9 entrambi ci siamo dentro.", {
      x: 5.35, y: 2.75, w: 3.85, h: 0.9, margin: 0,
      fontSize: 10.5, fontFace: "Calibri", color: C.textSec,
    });

    // Bottom notes
    s.addText("Per accordi istituzionali o corporate con volumi significativi, i termini specifici saranno definiti caso per caso.", {
      x: 0.6, y: 4.2, w: 8.8, h: 0.3, margin: 0,
      fontSize: 10, fontFace: "Calibri", color: C.textSec,
    });
    s.addText("La struttura vale per Italia e internazionale. Le percentuali sono la mia proposta \u2014 il primo punto di cui parlare nella call operativa.", {
      x: 0.6, y: 4.55, w: 8.8, h: 0.35, margin: 0,
      fontSize: 11, fontFace: "Calibri", color: C.textMuted, italic: true,
    });
  }

  // ============================================================
  // SLIDE 10 — EQUITY A MILESTONE
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "L'equity: a milestone, non a tempo", "L'equity con i risultati, non con la permanenza.");
    addFooter(s, 10, TOTAL);

    const tHead = [
      { text: "Milestone", options: { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 12, fontFace: "Calibri" } },
      { text: "Equity", options: { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 12, fontFace: "Calibri", align: "center" } },
      { text: "Quando", options: { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 12, fontFace: "Calibri", align: "center" } },
    ];
    const r1 = (bg) => ({ color: C.textPri, fill: { color: bg }, fontSize: 11, fontFace: "Calibri" });
    const tRows = [
      [
        { text: "Completamento POC \u2014 decisione GO al giorno 90", options: r1(C.tableRow1) },
        { text: "3%", options: { ...r1(C.tableRow1), bold: true, color: C.accent, align: "center" } },
        { text: "Mese 3", options: { ...r1(C.tableRow1), align: "center" } },
      ],
      [
        { text: "50 clienti attivi nella base installata", options: r1(C.tableRow2) },
        { text: "4%", options: { ...r1(C.tableRow2), bold: true, color: C.accent, align: "center" } },
        { text: "Quando accade", options: { ...r1(C.tableRow2), align: "center" } },
      ],
      [
        { text: "Primo deployment internazionale operativo", options: r1(C.tableRow1) },
        { text: "8%", options: { ...r1(C.tableRow1), bold: true, color: C.accent, align: "center" } },
        { text: "Quando accade", options: { ...r1(C.tableRow1), align: "center" } },
      ],
      [
        { text: "TOTALE POTENZIALE", options: { ...r1(C.tableRow2), bold: true, color: C.gold } },
        { text: "15%", options: { ...r1(C.tableRow2), bold: true, color: C.gold, fontSize: 14, align: "center" } },
        { text: "\u2014", options: { ...r1(C.tableRow2), align: "center" } },
      ],
    ];

    s.addTable([tHead, ...tRows], {
      x: 0.6, y: 1.2, w: 8.8,
      colW: [5, 1.5, 2.3],
      border: { type: "solid", pt: 0.5, color: C.border },
      rowH: [0.4, 0.45, 0.45, 0.45, 0.45],
    });

    // Two boxes
    addCard(pres, s, 0.6, 3.55, 4.15, 1.2);
    addAccentBar(pres, s, 0.6, 3.55, 1.2, C.accent2);
    s.addText("Se la POC fallisce:", {
      x: 0.85, y: 3.6, w: 3.7, h: 0.3, margin: 0,
      fontSize: 12, fontFace: "Calibri", bold: true, color: C.accent2,
    });
    s.addText("0% equity, 0 costi.\nStruttura imprenditoriale,\nnon dipendentistica.", {
      x: 0.85, y: 3.95, w: 3.7, h: 0.7, margin: 0,
      fontSize: 11, fontFace: "Calibri", color: C.textSec,
    });

    addCard(pres, s, 5.25, 3.55, 4.15, 1.2);
    addAccentBar(pres, s, 5.25, 3.55, 1.2, C.accent);
    s.addText("Giacomo mantiene l\u201985%", {
      x: 5.5, y: 3.6, w: 3.7, h: 0.3, margin: 0,
      fontSize: 12, fontFace: "Calibri", bold: true, color: C.accent,
    });
    s.addText("Il 15% riflette un partner che porta credibilit\u00E0, rete e competenze \u2014 non solo tempo.", {
      x: 5.5, y: 3.95, w: 3.7, h: 0.7, margin: 0,
      fontSize: 11, fontFace: "Calibri", color: C.textSec,
    });

    // LOI reference
    s.addText("Le condizioni specifiche di ogni milestone saranno definite nella Lettera di Intenti.", {
      x: 0.6, y: 4.85, w: 8.8, h: 0.25, margin: 0,
      fontSize: 10, fontFace: "Calibri", color: C.textMuted, italic: true,
    });
  }

  // ============================================================
  // SLIDE 11 — COSA PRODUCONO QUESTI NUMERI
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Cosa producono questi numeri", "Compenso calcolato con la struttura proposta (20% prodotto e PRO / 50% Inner Circle / equity 15% a milestone).");
    addFooter(s, 11, TOTAL);

    // SCENARIO CALIBRATO (top)
    addCard(pres, s, 0.6, 1.15, 8.8, 0.35, C.accent);
    s.addText("SCENARIO CALIBRATO \u2014 Italia + internazionale, con la tua leva", {
      x: 0.8, y: 1.18, w: 8.4, h: 0.3, margin: 0,
      fontSize: 12, fontFace: "Calibri", bold: true, color: C.bg,
    });

    const hOpt = { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 10, fontFace: "Calibri", align: "center" };
    const cOpt = (bg) => ({ color: C.textPri, fill: { color: bg }, fontSize: 10, fontFace: "Calibri", align: "center" });

    const cal = [
      [
        { text: "", options: { ...hOpt, align: "left" } },
        { text: "Anno 1", options: hOpt },
        { text: "Anno 2", options: hOpt },
        { text: "Anno 3", options: hOpt },
        { text: "Cum. 3 anni", options: hOpt },
      ],
      [
        { text: "Clienti IT / INT", options: { ...cOpt(C.tableRow1), align: "left" } },
        { text: "80-100 / \u2014", options: cOpt(C.tableRow1) },
        { text: "150-200 / 30-60", options: cOpt(C.tableRow1) },
        { text: "250-350 / 100-200+", options: cOpt(C.tableRow1) },
        { text: "\u2014", options: cOpt(C.tableRow1) },
      ],
      [
        { text: "Fatturato", options: { ...cOpt(C.tableRow2), align: "left" } },
        { text: "\u20AC29-37K", options: cOpt(C.tableRow2) },
        { text: "\u20AC55-85K", options: cOpt(C.tableRow2) },
        { text: "\u20AC100-165K", options: cOpt(C.tableRow2) },
        { text: "\u20AC185-290K", options: { ...cOpt(C.tableRow2), bold: true, color: C.accent } },
      ],
      [
        { text: "Cash Alessio", options: { ...cOpt(C.tableRow1), align: "left", bold: true } },
        { text: "\u20AC7-10K", options: { ...cOpt(C.tableRow1), color: C.accent2, bold: true } },
        { text: "\u20AC15-22K", options: { ...cOpt(C.tableRow1), color: C.accent2, bold: true } },
        { text: "\u20AC26-44K", options: { ...cOpt(C.tableRow1), color: C.accent2, bold: true } },
        { text: "\u20AC48-76K", options: { ...cOpt(C.tableRow1), color: C.accent2, bold: true } },
      ],
      [
        { text: "Equity (15%)", options: { ...cOpt(C.tableRow2), align: "left" } },
        { text: "\u20AC3-4K", options: cOpt(C.tableRow2) },
        { text: "\u20AC10-14K", options: cOpt(C.tableRow2) },
        { text: "\u20AC28-43K", options: cOpt(C.tableRow2) },
        { text: "\u2014", options: cOpt(C.tableRow2) },
      ],
    ];

    s.addTable(cal, {
      x: 0.6, y: 1.55, w: 8.8,
      colW: [2, 1.6, 1.8, 1.8, 1.6],
      border: { type: "solid", pt: 0.5, color: C.border },
      rowH: [0.32, 0.32, 0.32, 0.32, 0.32],
    });

    // FLOOR CONSERVATIVO (bottom)
    addCard(pres, s, 0.6, 3.25, 8.8, 0.35, C.bgCard2);
    s.addText("FLOOR CONSERVATIVO \u2014 solo Italia, crescita organica (la rete di sicurezza)", {
      x: 0.8, y: 3.28, w: 8.4, h: 0.3, margin: 0,
      fontSize: 12, fontFace: "Calibri", bold: true, color: C.textSec,
    });

    const floor = [
      [
        { text: "", options: { ...hOpt, align: "left" } },
        { text: "Anno 1", options: hOpt },
        { text: "Anno 2", options: hOpt },
        { text: "Anno 3", options: hOpt },
        { text: "Cum. 3 anni", options: hOpt },
      ],
      [
        { text: "Fatturato", options: { ...cOpt(C.tableRow1), align: "left" } },
        { text: "\u20AC17.150", options: cOpt(C.tableRow1) },
        { text: "\u20AC29.650", options: cOpt(C.tableRow1) },
        { text: "\u20AC49.650", options: cOpt(C.tableRow1) },
        { text: "\u20AC96.450", options: cOpt(C.tableRow1) },
      ],
      [
        { text: "Cash Alessio", options: { ...cOpt(C.tableRow2), align: "left", bold: true } },
        { text: "\u20AC4.100", options: { ...cOpt(C.tableRow2), color: C.textSec } },
        { text: "\u20AC7.300", options: { ...cOpt(C.tableRow2), color: C.textSec } },
        { text: "\u20AC12.800", options: { ...cOpt(C.tableRow2), color: C.textSec } },
        { text: "\u20AC24.200", options: { ...cOpt(C.tableRow2), color: C.textSec } },
      ],
      [
        { text: "Equity maturata", options: { ...cOpt(C.tableRow1), align: "left" } },
        { text: "3%", options: cOpt(C.tableRow1) },
        { text: "7%", options: cOpt(C.tableRow1) },
        { text: "7-15%", options: cOpt(C.tableRow1) },
        { text: "\u2014", options: cOpt(C.tableRow1) },
      ],
      [
        { text: "Valore equity", options: { ...cOpt(C.tableRow2), align: "left" } },
        { text: "\u20AC1.600", options: cOpt(C.tableRow2) },
        { text: "\u20AC6.800", options: cOpt(C.tableRow2) },
        { text: "\u20AC14.000-21.000", options: cOpt(C.tableRow2) },
        { text: "\u2014", options: cOpt(C.tableRow2) },
      ],
    ];

    s.addTable(floor, {
      x: 0.6, y: 3.65, w: 8.8,
      colW: [2, 1.6, 1.8, 1.8, 1.6],
      border: { type: "solid", pt: 0.5, color: C.border },
      rowH: [0.32, 0.32, 0.32, 0.32, 0.32],
    });

    s.addText("La differenza tra i due scenari \u00E8 la leva di rete. Il calibrato \u00E8 il piano realistico con i tuoi asset. Il floor \u00E8 la rete di sicurezza.", {
      x: 0.6, y: 5.0, w: 8.8, h: 0.2, margin: 0,
      fontSize: 10, fontFace: "Calibri", color: C.textMuted, italic: true,
    });
  }

  // ============================================================
  // SLIDE 12 — LEVA INTERNAZIONALE: NORDIC WELLNESS
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "La leva internazionale: Nordic Wellness", "Centinaia di sedi, migliaia di trainer. Un esempio per dimensionare il potenziale.");
    addFooter(s, 12, TOTAL);

    const tHead = [
      { text: "Parametro", options: { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 12, fontFace: "Calibri" } },
      { text: "Ipotesi conservativa", options: { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 12, fontFace: "Calibri", align: "center" } },
    ];
    const r = (bg) => ({ color: C.textPri, fill: { color: bg }, fontSize: 11, fontFace: "Calibri" });
    const tRows = [
      [{ text: "Trainer contattabili tramite accordo", options: r(C.tableRow1) }, { text: "100-200", options: { ...r(C.tableRow1), align: "center", bold: true } }],
      [{ text: "Tasso adozione (conservativo)", options: r(C.tableRow2) }, { text: "15-20%", options: { ...r(C.tableRow2), align: "center", bold: true } }],
      [{ text: "Vendite da un singolo accordo", options: r(C.tableRow1) }, { text: "15-40", options: { ...r(C.tableRow1), align: "center", bold: true, color: C.accent } }],
      [{ text: "Ricavo (pricing nordico \u20AC349-549)", options: r(C.tableRow2) }, { text: "\u20AC5.000-22.000", options: { ...r(C.tableRow2), align: "center", bold: true, color: C.accent2 } }],
      [{ text: "Inner Circle (25% dei nuovi)", options: r(C.tableRow1) }, { text: "+\u20AC1.000-2.500/anno", options: { ...r(C.tableRow1), align: "center", bold: true, color: C.gold } }],
    ];

    s.addTable([tHead, ...tRows], {
      x: 0.6, y: 1.2, w: 8.8,
      colW: [5.2, 3.6],
      border: { type: "solid", pt: 0.5, color: C.border },
      rowH: [0.42, 0.42, 0.42, 0.42, 0.42, 0.42],
    });

    addCard(pres, s, 0.6, 3.85, 8.8, 0.7, C.bgCard2);
    addAccentBar(pres, s, 0.6, 3.85, 0.7, C.gold);
    s.addText("Lo hai visto subito.", {
      x: 0.85, y: 3.9, w: 8.35, h: 0.2, margin: 0,
      fontSize: 12, fontFace: "Calibri", bold: true, color: C.gold,
    });
    s.addText("Un singolo accordo con una catena internazionale vale quanto 3-6 mesi di vendita organica in Italia.\nQuesto accordo \u00E8 anche la milestone che fa maturare l\u2019ultimo 4% di equity.", {
      x: 0.85, y: 4.12, w: 8.35, h: 0.38, margin: 0,
      fontSize: 11, fontFace: "Calibri", color: C.textSec,
    });

    s.addText("Nordic Wellness \u00E8 un esempio \u2014 il primo di una serie.\nOgni mercato internazionale aperto aggiunge valore strutturale al progetto \u2014 non solo fatturato, ma base installata multi-paese. \u00C8 il tipo di asset che attira l\u2019attenzione di chi acquisisce nel settore.", {
      x: 0.6, y: 4.6, w: 8.8, h: 0.55, margin: 0,
      fontSize: 10, fontFace: "Calibri", color: C.textMuted, italic: true,
    });
  }

  // ============================================================
  // SLIDE 13 — INNER CIRCLE COME PROGETTO CONGIUNTO
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "PT Evoluto \u2014 il progetto congiunto", "Oggi un trainer che vuole evolversi studia il metodo ma torna in palestra con Excel e WhatsApp. Oppure compra un gestionale ma non ha il metodo per usarlo davvero. Il gap tra \"so cosa dovrei fare\" e \"riesco a farlo\" resta. PT Evoluto \u00E8 la prima volta che metodo e strumento nascono insieme.");
    addFooter(s, 13, TOTAL);

    // 3 key points
    const points = [
      { text: "Il metodo e lo strumento sono inseparabili. L\u2019IC funziona perch\u00E9 entrambi ci siamo dentro.", color: C.accent },
      { text: "50/50 \u2014 perch\u00E9 nessuno dei due pu\u00F2 farlo da solo", color: C.accent2 },
      { text: "Formato, contenuti e pricing dell\u2019IC li definiamo insieme. Se la partnership si dissolve, il contenuto creato da te resta tuo (il brand e la piattaforma restano di Giacomo)", color: C.gold },
    ];
    points.forEach((p, i) => {
      const cy = 1.15 + i * 0.4;
      s.addImage({ data: icons.check, x: 0.6, y: cy + 0.05, w: 0.25, h: 0.25 });
      s.addText(p.text, {
        x: 0.95, y: cy, w: 8.45, h: 0.35, margin: 0,
        fontSize: 11.5, fontFace: "Calibri", color: p.color, bold: true,
      });
    });

    // Community table
    s.addText("4 livelli community", {
      x: 0.6, y: 2.45, w: 8.8, h: 0.3, margin: 0,
      fontSize: 14, fontFace: "Trebuchet MS", bold: true, color: C.white,
    });

    const thO = { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 10.5, fontFace: "Calibri" };
    const trO = (bg) => ({ color: C.textPri, fill: { color: bg }, fontSize: 10, fontFace: "Calibri" });
    const communityRows = [
      [{ text: "Livello", options: thO }, { text: "Prezzo", options: { ...thO, align: "center" } }, { text: "Cosa include", options: thO }],
      [{ text: "Base", options: trO(C.tableRow1) }, { text: "\u20AC0", options: { ...trO(C.tableRow1), align: "center" } }, { text: "Forum, knowledge base, networking, onboarding", options: trO(C.tableRow1) }],
      [{ text: "PRO", options: { ...trO(C.tableRow2), bold: true, color: C.accent } }, { text: "\u20AC79/anno", options: { ...trO(C.tableRow2), align: "center" } }, { text: "Aggiornamenti, esercizi trimestrali, template, supporto <24h", options: trO(C.tableRow2) }],
      [{ text: "Inner Circle", options: { ...trO(C.tableRow1), bold: true, color: C.gold } }, { text: "\u20AC249/anno", options: { ...trO(C.tableRow1), align: "center" } }, { text: "Masterclass (Alessio), webinar, mastermind, certificazione PT Evoluto", options: trO(C.tableRow1) }],
      [{ text: "Mentorship", options: { ...trO(C.tableRow2), bold: true, color: C.orange } }, { text: "\u20AC499-599", options: { ...trO(C.tableRow2), align: "center" } }, { text: "1:1, roadmap, eventi in presenza. Max 15-20. Anno 3+", options: trO(C.tableRow2) }],
    ];

    s.addTable(communityRows, {
      x: 0.6, y: 2.8, w: 8.8,
      colW: [1.5, 1.4, 5.9],
      border: { type: "solid", pt: 0.5, color: C.border },
      rowH: [0.35, 0.35, 0.35, 0.35, 0.35],
    });

    s.addText("Ogni masterclass ha 3 vite: live \u2192 registrazione \u2192 asset marketing.\nI termini sulle registrazioni saranno definiti nella Lettera di Intenti.\nCon l\u2019internazionale, stesso contenuto, doppio bacino.", {
      x: 0.6, y: 4.65, w: 8.8, h: 0.45, margin: 0,
      fontSize: 10.5, fontFace: "Calibri", color: C.textSec, italic: true,
    });
  }

  // ============================================================
  // SLIDE 14 — POC: 10 FONDATORI
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "La POC: 10 Fondatori, 90 giorni", "Non vendiamo subito. Prima dimostriamo \u2014 il pacchetto completo.");
    addFooter(s, 14, TOTAL);

    // 4 items
    const pocItems = [
      { icon: icons.laptop, title: "Licenza o Box", desc: "8 a \u20AC99 + 2 a \u20AC199", color: C.accent },
      { icon: icons.grad, title: "Inner Circle 12 mesi", desc: "Incluso nel prezzo Fondatore", color: C.accent2 },
      { icon: icons.comments, title: "Community Fondatori", desc: "Canale riservato", color: C.gold },
      { icon: icons.wrench, title: "Installazione 1:1", desc: "Setup guidato con il founder", color: C.orange },
    ];

    pocItems.forEach((it, i) => {
      const cx = 0.6 + i * 2.28;
      addCard(pres, s, cx, 1.15, 2.08, 1.3);
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: 1.15, w: 2.08, h: 0.05, fill: { color: it.color },
      });
      s.addImage({ data: it.icon, x: cx + 0.75, y: 1.3, w: 0.5, h: 0.5 });
      s.addText(it.title, {
        x: cx + 0.1, y: 1.85, w: 1.88, h: 0.28, margin: 0,
        fontSize: 11, fontFace: "Calibri", bold: true, color: C.white, align: "center",
      });
      s.addText(it.desc, {
        x: cx + 0.1, y: 2.12, w: 1.88, h: 0.25, margin: 0,
        fontSize: 9.5, fontFace: "Calibri", color: C.textSec, align: "center",
      });
    });

    // 3 stat boxes
    const statItems = [
      { num: "\u20AC1.190", label: "Ricavo POC", color: C.accent },
      { num: "~\u20AC300", label: "Costo vivo (2 Box)", color: C.orange },
      { num: "~\u20AC300", label: "Investimento netto in cash", color: C.accent2 },
    ];
    statItems.forEach((st, i) => {
      const cx = 0.6 + i * 3.1;
      addCard(pres, s, cx, 2.7, 2.8, 0.85);
      s.addText(st.num, {
        x: cx + 0.15, y: 2.75, w: 2.5, h: 0.4, margin: 0,
        fontSize: 24, fontFace: "Trebuchet MS", bold: true, color: st.color,
      });
      s.addText(st.label, {
        x: cx + 0.15, y: 3.18, w: 2.5, h: 0.25, margin: 0,
        fontSize: 10, fontFace: "Calibri", color: C.textSec,
      });
    });

    s.addText("Valore reale per ogni Fondatore: \u20AC498-698. Lo ottengono a \u20AC99-199 perch\u00E9 sono l'investimento pi\u00F9 importante del progetto.", {
      x: 0.6, y: 3.75, w: 8.8, h: 0.3, margin: 0,
      fontSize: 11, fontFace: "Calibri", color: C.textSec,
    });

    s.addText("Selezioni tu i Fondatori dalla tua rete. Professionisti scelti, con influenza nel proprio circolo \u2014 non i primi che capitano.", {
      x: 0.6, y: 4.1, w: 8.8, h: 0.3, margin: 0,
      fontSize: 11, fontFace: "Calibri", color: C.gold, italic: true,
    });
  }

  // ============================================================
  // SLIDE 15 — RUOLI NELLA POC
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "I ruoli nella POC");
    addFooter(s, 15, TOTAL);

    const thO = { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 11, fontFace: "Calibri" };
    const trO = (bg, isAlessio) => {
      const base = { color: C.textPri, fill: { color: bg }, fontSize: 10.5, fontFace: "Calibri" };
      if (isAlessio) return { ...base, color: C.accent2 };
      return base;
    };

    const rows = [
      [{ text: "Attivit\u00E0", options: thO }, { text: "Chi", options: { ...thO, align: "center" } }, { text: "Ore", options: { ...thO, align: "center" } }],
      [{ text: "Selezione 10 Fondatori dal network", options: trO(C.tableRow1, true) }, { text: "Alessio + Giacomo", options: { ...trO(C.tableRow1, true), align: "center" } }, { text: "3-4", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Installazione, setup, config template WA", options: trO(C.tableRow2) }, { text: "Giacomo", options: { ...trO(C.tableRow2), align: "center" } }, { text: "15-20", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Check-in bisettimanali con ogni Fondatore", options: trO(C.tableRow1) }, { text: "Giacomo", options: { ...trO(C.tableRow1), align: "center" } }, { text: "20", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Masterclass mese 1", options: trO(C.tableRow2, true) }, { text: "Insieme \u2014 Alessio guida, Giacomo demo live", options: { ...trO(C.tableRow2, true), align: "center" } }, { text: "2-3", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Webinar mese 2", options: trO(C.tableRow1, true) }, { text: "Alessio + Giacomo", options: { ...trO(C.tableRow1, true), align: "center" } }, { text: "2", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Masterclass mese 3", options: trO(C.tableRow2, true) }, { text: "Insieme \u2014 Alessio guida, Giacomo demo live", options: { ...trO(C.tableRow2, true), align: "center" } }, { text: "2-3", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Sessione di gruppo finale (giorno 90)", options: trO(C.tableRow1, true) }, { text: "Alessio + Giacomo", options: { ...trO(C.tableRow1, true), align: "center" } }, { text: "2", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Micro-sondaggi e analisi dati", options: trO(C.tableRow2) }, { text: "Giacomo", options: { ...trO(C.tableRow2), align: "center" } }, { text: "5", options: { ...trO(C.tableRow2), align: "center" } }],
    ];

    s.addTable(rows, {
      x: 0.6, y: 1.0, w: 8.8,
      colW: [5.2, 2.2, 1.4],
      border: { type: "solid", pt: 0.5, color: C.border },
      rowH: [0.38, 0.38, 0.38, 0.38, 0.38, 0.38, 0.38, 0.38, 0.38],
    });

    // Totals
    addCard(pres, s, 0.6, 4.5, 4.15, 0.55, C.bgCard2);
    addAccentBar(pres, s, 0.6, 4.5, 0.55, C.accent2);
    s.addText("Totale Alessio: ~15-20 ore in 90gg", {
      x: 0.85, y: 4.55, w: 3.7, h: 0.35, margin: 0,
      fontSize: 13, fontFace: "Calibri", bold: true, color: C.accent2,
    });

    addCard(pres, s, 5.25, 4.5, 4.15, 0.55, C.bgCard2);
    addAccentBar(pres, s, 5.25, 4.5, 0.55, C.accent);
    s.addText("Totale Giacomo: ~40-45 ore in 90gg", {
      x: 5.5, y: 4.55, w: 3.7, h: 0.35, margin: 0,
      fontSize: 13, fontFace: "Calibri", bold: true, color: C.accent,
    });
  }

  // ============================================================
  // SLIDE 16 — METRICHE E DECISIONE GIORNO 90
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Le metriche e la decisione al giorno 90");
    addFooter(s, 16, TOTAL);

    const thO = { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 10.5, fontFace: "Calibri" };
    const trO = (bg) => ({ color: C.textPri, fill: { color: bg }, fontSize: 10, fontFace: "Calibri" });

    const metricRows = [
      [{ text: "Metrica", options: thO }, { text: "Target", options: { ...thO, align: "center" } }, { text: "Cosa valida", options: thO }],
      [{ text: "Ore admin risparmiate", options: trO(C.tableRow1) }, { text: "Da 3-5h a <2h/sett.", options: { ...trO(C.tableRow1), align: "center" } }, { text: "Il prodotto", options: trO(C.tableRow1) }],
      [{ text: "Messaggi WA pre-compilati/sett.", options: trO(C.tableRow2) }, { text: "15+", options: { ...trO(C.tableRow2), align: "center", bold: true } }, { text: "Adozione comunicazione", options: trO(C.tableRow2) }],
      [{ text: "Clienti usano portale allenamento", options: trO(C.tableRow1) }, { text: "7/10 attivi", options: { ...trO(C.tableRow1), align: "center", bold: true } }, { text: "Workout Intelligence", options: trO(C.tableRow1) }],
      [{ text: "NPS", options: trO(C.tableRow2) }, { text: "Sopra 50", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.accent2 } }, { text: "Prodotto + percorso", options: trO(C.tableRow2) }],
      [{ text: "\"Lo ricomprerei a prezzo pieno\"", options: trO(C.tableRow1) }, { text: "8/10 s\u00EC", options: { ...trO(C.tableRow1), align: "center", bold: true } }, { text: "Modello economico", options: trO(C.tableRow1) }],
      [{ text: "\"I miei clienti notano differenza\"", options: trO(C.tableRow2) }, { text: "5/10 s\u00EC", options: { ...trO(C.tableRow2), align: "center" } }, { text: "Volano PT Evoluto", options: trO(C.tableRow2) }],
      [{ text: "\"Mi definirei un PT Evoluto\"", options: trO(C.tableRow1) }, { text: "6/10 s\u00EC", options: { ...trO(C.tableRow1), align: "center" } }, { text: "Category creation", options: trO(C.tableRow1) }],
    ];

    s.addTable(metricRows, {
      x: 0.6, y: 0.9, w: 8.8,
      colW: [3.8, 2, 3],
      border: { type: "solid", pt: 0.5, color: C.border },
      rowH: [0.35, 0.35, 0.35, 0.35, 0.35, 0.35, 0.35, 0.35],
    });

    // 3 outcome boxes
    const outcomes = [
      { label: "GO", color: C.accent2, desc: "NPS 50+, ore dimezzate,\n8+ attivi. Partnership piena.\nEquity prima tranche matura." },
      { label: "GO con cautela", color: C.gold, desc: "NPS 30-50.\nSi aggiusta, si riparte\ncon 5 nuovi." },
      { label: "STOP", color: C.red, desc: "NPS <30, <6 attivi.\nCosto: 3 mesi e ~\u20AC1.000.\nZero equity." },
    ];

    outcomes.forEach((o, i) => {
      const cx = 0.6 + i * 3.1;
      addCard(pres, s, cx, 3.85, 2.8, 1.2);
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: 3.85, w: 2.8, h: 0.06, fill: { color: o.color },
      });
      s.addText(o.label, {
        x: cx + 0.15, y: 3.95, w: 2.5, h: 0.3, margin: 0,
        fontSize: 14, fontFace: "Trebuchet MS", bold: true, color: o.color,
      });
      s.addText(o.desc, {
        x: cx + 0.15, y: 4.3, w: 2.5, h: 0.65, margin: 0,
        fontSize: 10, fontFace: "Calibri", color: C.textSec,
      });
    });
  }

  // ============================================================
  // SLIDE 17 — DOPO LA POC: IL VOLANO
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Dopo la POC: il volano");
    addFooter(s, 17, TOTAL);

    const volanoPhases = [
      { period: "MESI 4-6", title: "Early Adopter + preparazione internazionale", desc: "Testimonial POC come leva. Inner Circle attivo (tu conduci masterclass e mastermind).\nWebinar gratuito mensile. In parallelo: Blocchi 1-2 tradotti, primi contatti nordico.\nTarget Italia: 15-20 clienti.", color: C.accent },
      { period: "MESI 7-12", title: "Scala Italia + pilota internazionale", desc: "Italia: tutti i canali attivi + salti da accordi catene. Internazionale: 5-10 utenti pilota.\nCertificazione PT Evoluto in costruzione. Pricing internazionale definito.", color: C.accent2 },
      { period: "ANNO 2+", title: "Due mercati attivi", desc: "Italia consolidata + lancio internazionale strutturato. Inner Circle bilingue \u2014\nstesso tuo sforzo, doppio bacino. Team dedicato, SRL, brand riconosciuto.", color: C.gold },
    ];

    // vertical line
    s.addShape(pres.shapes.RECTANGLE, {
      x: 1.55, y: 1.05, w: 0.04, h: 3.6, fill: { color: C.border },
    });

    volanoPhases.forEach((p, i) => {
      const cy = 1.0 + i * 1.3;
      // dot
      s.addShape(pres.shapes.OVAL, {
        x: 1.39, y: cy + 0.15, w: 0.36, h: 0.36, fill: { color: p.color },
      });
      s.addText(p.period, {
        x: 0.1, y: cy + 0.15, w: 1.2, h: 0.36, margin: 0,
        fontSize: 9, fontFace: "Calibri", bold: true, color: p.color, align: "right", valign: "middle",
      });
      addCard(pres, s, 2.05, cy, 7.35, 1.15);
      addAccentBar(pres, s, 2.05, cy, 1.15, p.color);
      s.addText(p.title, {
        x: 2.25, y: cy + 0.05, w: 7, h: 0.3, margin: 0,
        fontSize: 13, fontFace: "Calibri", bold: true, color: C.white,
      });
      s.addText(p.desc, {
        x: 2.25, y: cy + 0.4, w: 7, h: 0.7, margin: 0,
        fontSize: 10.5, fontFace: "Calibri", color: C.textSec,
      });
    });
  }

  // ============================================================
  // SLIDE 18 — IL CICLO COMPLETO (NEW)
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Il ciclo completo: dal trainer al passaparola", "WhatsApp apre il ciclo. Il portale lo chiude. Il passaparola lo moltiplica.");
    addFooter(s, 18, TOTAL);

    const steps = [
      { num: "\u2460", title: "Il trainer crea la scheda", desc: "Workout Builder con Science Panel: volume per muscolo, bilanciamento biomeccanico, Safety Engine.", color: C.accent },
      { num: "\u2461", title: "Invia via WhatsApp", desc: "Un click, template pre-compilato. \"La tua scheda \u00E8 pronta, aprila qui.\"", color: C.accent2 },
      { num: "\u2462", title: "Il cliente apre il portale", desc: "Dal telefono, nessuna app. Vede la sessione del giorno con foto start/end.", color: C.gold },
      { num: "\u2463", title: "Esegue e registra in palestra", desc: "Conferma il prescritto con un tap, modifica solo se diverso. RPE e note. 30 sec per esercizio.", color: C.orange },
      { num: "\u2464", title: "Il sistema analizza", desc: "Compliance, volume per muscolo vs target scientifici, equilibri biomeccanici, alert predittivi.", color: C.accent },
      { num: "\u2465", title: "Il cliente percepisce", desc: "Non \u00E8 il solito trainer. \u00C8 un professionista con un metodo. Il passaparola parte da qui.", color: C.red },
    ];

    // 3x2 grid of step cards
    steps.forEach((st, i) => {
      const col = i % 3, row = Math.floor(i / 3);
      const cx = 0.6 + col * 3.1;
      const cy = 1.2 + row * 1.65;
      addCard(pres, s, cx, cy, 2.8, 1.5);
      s.addShape(pres.shapes.RECTANGLE, {
        x: cx, y: cy, w: 2.8, h: 0.05, fill: { color: st.color },
      });
      // step number
      s.addShape(pres.shapes.OVAL, {
        x: cx + 0.1, y: cy + 0.15, w: 0.4, h: 0.4, fill: { color: st.color },
      });
      s.addText(String(i + 1), {
        x: cx + 0.1, y: cy + 0.15, w: 0.4, h: 0.4, margin: 0,
        fontSize: 16, fontFace: "Trebuchet MS", bold: true, color: C.bg, align: "center", valign: "middle",
      });
      s.addText(st.title, {
        x: cx + 0.6, y: cy + 0.15, w: 2.05, h: 0.35, margin: 0,
        fontSize: 11.5, fontFace: "Calibri", bold: true, color: C.white,
      });
      s.addText(st.desc, {
        x: cx + 0.15, y: cy + 0.65, w: 2.5, h: 0.75, margin: 0,
        fontSize: 9.5, fontFace: "Calibri", color: C.textSec,
      });
    });

    s.addText("In Scandinavia il canale dominante potrebbe non essere WhatsApp. L'architettura \u00E8 la stessa \u2014 cambia il canale.", {
      x: 0.6, y: 4.85, w: 8.8, h: 0.25, margin: 0,
      fontSize: 9.5, fontFace: "Calibri", color: C.textMuted, italic: true,
    });
  }

  // ============================================================
  // SLIDE 19 — WORKOUT INTELLIGENCE (NEW)
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Workout Intelligence: quello che nessuno ha", "Nessun software al mondo fa questo. \u00C8 la feature che separa FitManager da qualsiasi competitor.");
    addFooter(s, 19, TOTAL);

    // Transparency note
    s.addText("Quando hai visto FitManager, questa feature non esisteva ancora. Hai identificato il potenziale \u2014 il cliente che registra i dati reali, il trainer che vede l\u2019aderenza in automatico. L\u2019avevo in progetto da tempo. Adesso c\u2019\u00E8. Funziona. \u00C8 quello che hai visto tradotto in sistema.", {
      x: 0.6, y: 0.95, w: 8.8, h: 0.42, margin: 0,
      fontSize: 9.5, fontFace: "Calibri", color: C.textMuted, italic: true,
    });

    // Key moment box
    addCard(pres, s, 0.6, 1.45, 8.8, 0.9, C.bgCard2);
    addAccentBar(pres, s, 0.6, 1.45, 0.9, C.gold);
    s.addText("Il momento che cambia tutto:", {
      x: 0.85, y: 1.5, w: 8.35, h: 0.25, margin: 0,
      fontSize: 11, fontFace: "Calibri", bold: true, color: C.gold,
    });
    s.addText("Il trainer siede con il cliente e gli mostra: \"Sulla panca hai fatto 3\u00D78 invece di 4\u00D710. Il tuo petto \u00E8 in zona blu \u2014 sotto la soglia minima di stimolo. La prossima settimana partiamo da 3\u00D710 e monitoriamo.\" Il cliente sta vivendo qualcosa che non ha mai sperimentato con nessun altro trainer.", {
      x: 0.85, y: 1.75, w: 8.35, h: 0.55, margin: 0,
      fontSize: 10.5, fontFace: "Calibri", color: C.textSec, italic: true,
    });

    // Diff table
    const thO = { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 10.5, fontFace: "Calibri" };
    const trO = (bg) => ({ color: C.textPri, fill: { color: bg }, fontSize: 10.5, fontFace: "Calibri" });

    const diffRows = [
      [{ text: "Esercizio", options: thO }, { text: "Piano", options: { ...thO, align: "center" } }, { text: "Fatto", options: { ...thO, align: "center" } }, { text: "Delta", options: { ...thO, align: "center" } }],
      [{ text: "Panca Piana", options: trO(C.tableRow1) }, { text: "4\u00D710 @60kg", options: { ...trO(C.tableRow1), align: "center" } }, { text: "3\u00D78 @55kg", options: { ...trO(C.tableRow1), align: "center" } }, { text: "-1s -2r -5kg \u2193", options: { ...trO(C.tableRow1), align: "center", bold: true, color: C.red } }],
      [{ text: "Squat", options: trO(C.tableRow2) }, { text: "4\u00D78 @80kg", options: { ...trO(C.tableRow2), align: "center" } }, { text: "4\u00D710 @80kg", options: { ...trO(C.tableRow2), align: "center" } }, { text: "0s +2r 0kg \u2191", options: { ...trO(C.tableRow2), align: "center", bold: true, color: C.accent2 } }],
      [{ text: "Lat Machine", options: trO(C.tableRow1) }, { text: "3\u00D712 @40kg", options: { ...trO(C.tableRow1), align: "center" } }, { text: "3\u00D712 @40kg", options: { ...trO(C.tableRow1), align: "center" } }, { text: "in linea =", options: { ...trO(C.tableRow1), align: "center", bold: true, color: C.accent } }],
    ];

    s.addTable(diffRows, {
      x: 0.6, y: 2.45, w: 8.8,
      colW: [2.5, 2, 2, 2.3],
      border: { type: "solid", pt: 0.5, color: C.border },
      rowH: [0.32, 0.32, 0.32, 0.32],
    });

    // 3 analysis levels
    const levels = [
      { icon: icons.chart, title: "Compliance per sessione", desc: "Il PT vede subito se il cliente ha fatto l'80% o il 110% di quanto prescritto.", color: C.accent },
      { icon: icons.microscope, title: "Dose-Response per muscolo", desc: "Volume effettivo vs target scientifici (MEV/MAV/MRV), personalizzati.", color: C.accent2 },
      { icon: icons.balance, title: "Equilibrio biomeccanico", desc: "5 rapporti scientifici calcolati da dati reali. Corregge gli squilibri.", color: C.gold },
    ];

    levels.forEach((l, i) => {
      const cx = 0.6 + i * 3.1;
      addCard(pres, s, cx, 3.85, 2.8, 0.8);
      s.addImage({ data: l.icon, x: cx + 0.1, y: 3.92, w: 0.32, h: 0.32 });
      s.addText(l.title, {
        x: cx + 0.5, y: 3.9, w: 2.15, h: 0.25, margin: 0,
        fontSize: 10, fontFace: "Calibri", bold: true, color: l.color,
      });
      s.addText(l.desc, {
        x: cx + 0.1, y: 4.22, w: 2.6, h: 0.35, margin: 0,
        fontSize: 9, fontFace: "Calibri", color: C.textSec,
      });
    });

    s.addText("Ogni competitor tracka volume totale. Nessuno incrocia il piano con l'esecuzione muscolo per muscolo con target NSCA personalizzati.", {
      x: 0.6, y: 4.78, w: 8.8, h: 0.25, margin: 0,
      fontSize: 10, fontFace: "Calibri", bold: true, color: C.gold,
    });
  }

  // ============================================================
  // SLIDE 20 — LE 5 DOMANDE
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Le 5 domande");
    addFooter(s, 20, TOTAL);

    const questions = [
      { q: "Come vedi la struttura a fasi e i termini economici?", sub: "I numeri sono sul tavolo \u2014 dimmi dove non ti tornano.", color: C.accent },
      { q: "La sequenza di ingresso in Italia:", sub: "Prima i singoli, prima le catene, in parallelo? Il pricing regge per il mercato che conosci?", color: C.accent2 },
      { q: "Nordic Wellness e l'internazionale:", sub: "Qual \u00E8 il percorso realistico? Chi sono i referenti? Che timeline vedi?", color: C.gold },
      { q: "I 10 Fondatori:", sub: "Hai gi\u00E0 qualche idea? Che profili dalla tua rete?", color: C.orange },
      { q: "Cosa aggiungeresti? Cosa vedi che io non vedo?", sub: "", color: C.red },
    ];

    questions.forEach((qq, i) => {
      const cy = 1.0 + i * 0.82;
      addCard(pres, s, 0.6, cy, 8.8, 0.72);
      // number circle
      s.addShape(pres.shapes.OVAL, {
        x: 0.8, y: cy + 0.16, w: 0.4, h: 0.4, fill: { color: qq.color },
      });
      s.addText(String(i + 1), {
        x: 0.8, y: cy + 0.16, w: 0.4, h: 0.4, margin: 0,
        fontSize: 16, fontFace: "Trebuchet MS", bold: true, color: C.bg, align: "center", valign: "middle",
      });
      s.addText(qq.q, {
        x: 1.4, y: cy + 0.08, w: 7.8, h: 0.3, margin: 0,
        fontSize: 13, fontFace: "Calibri", bold: true, color: C.white,
      });
      if (qq.sub) {
        s.addText(qq.sub, {
          x: 1.4, y: cy + 0.4, w: 7.8, h: 0.25, margin: 0,
          fontSize: 11, fontFace: "Calibri", color: C.textSec,
        });
      }
    });
  }

  // ============================================================
  // SLIDE 21 — PROSSIMI PASSI
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    addSectionTitle(s, "Prossimi passi");
    addFooter(s, 21, TOTAL);

    const thO = { bold: true, color: C.white, fill: { color: C.tableHead }, fontSize: 10, fontFace: "Calibri" };
    const trO = (bg, highlight) => {
      const base = { color: C.textPri, fill: { color: bg }, fontSize: 10, fontFace: "Calibri" };
      if (highlight) return { ...base, bold: true, color: C.accent };
      return base;
    };

    const rows = [
      [{ text: "Cosa", options: thO }, { text: "Quando", options: { ...thO, align: "center" } }, { text: "Chi", options: { ...thO, align: "center" } }],
      [{ text: "NDA formale", options: trO(C.tableRow1) }, { text: "1a sett. aprile", options: { ...trO(C.tableRow1), align: "center" } }, { text: "Giacomo \u2192 Alessio", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Consegna software + BP + Strategy Plan", options: trO(C.tableRow2) }, { text: "Post-firma NDA", options: { ...trO(C.tableRow2), align: "center" } }, { text: "Giacomo", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Test hands-on \u2014 una settimana con il prodotto", options: trO(C.tableRow1, true) }, { text: "1a-2a sett. aprile", options: { ...trO(C.tableRow1, true), align: "center" } }, { text: "Alessio", options: { ...trO(C.tableRow1, true), align: "center" } }],
      [{ text: "Call feedback (1h): analisi prodotto e idee", options: trO(C.tableRow2) }, { text: "2a sett. aprile", options: { ...trO(C.tableRow2), align: "center" } }, { text: "Insieme", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Call: struttura partnership e termini economici", options: trO(C.tableRow1) }, { text: "3a sett. aprile", options: { ...trO(C.tableRow1), align: "center" } }, { text: "Insieme", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Formalizzazione termini (Lettera di Intenti)", options: trO(C.tableRow2) }, { text: "Entro aprile", options: { ...trO(C.tableRow2), align: "center" } }, { text: "Insieme", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Lista Fondatori (nomi)", options: trO(C.tableRow1) }, { text: "Fine aprile", options: { ...trO(C.tableRow1), align: "center" } }, { text: "Alessio + Giacomo", options: { ...trO(C.tableRow1), align: "center" } }],
      [{ text: "Demo live candidati Fondatori", options: trO(C.tableRow2) }, { text: "Fine aprile", options: { ...trO(C.tableRow2), align: "center" } }, { text: "Giacomo (Alessio presenta)", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Lancio Fase 1 \u2014 POC", options: trO(C.tableRow1, true) }, { text: "Maggio 2026", options: { ...trO(C.tableRow1, true), align: "center" } }, { text: "Insieme", options: { ...trO(C.tableRow1, true), align: "center" } }],
      [{ text: "Blocchi 1-2 pronti lingua target", options: trO(C.tableRow2) }, { text: "Luglio-Agosto 2026", options: { ...trO(C.tableRow2), align: "center" } }, { text: "Giacomo", options: { ...trO(C.tableRow2), align: "center" } }],
      [{ text: "Go-to-market nazionale & Primi contatti mercato internazionale", options: trO(C.tableRow1) }, { text: "Settembre 2026", options: { ...trO(C.tableRow1), align: "center" } }, { text: "Insieme", options: { ...trO(C.tableRow1), align: "center" } }],
    ];

    s.addTable(rows, {
      x: 0.6, y: 0.9, w: 8.8,
      colW: [4.2, 2.2, 2.4],
      border: { type: "solid", pt: 0.5, color: C.border },
      rowH: [0.28, 0.28, 0.28, 0.30, 0.28, 0.28, 0.28, 0.28, 0.28, 0.30, 0.28, 0.28],
    });

    // --- Nota timeline + stagionalità ---
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.6, y: 4.42, w: 8.8, h: 0.03, fill: { color: C.border },
    });

    s.addText([
      { text: "Nota sulla timeline", options: { bold: true, fontSize: 9.5, color: C.accent, fontFace: "Trebuchet MS", breakLine: true } },
      { text: "Le date sopra sono la scaletta di massima \u2014 non scadenze rigide. La sequenza \u00E8 intenzionale: prima metti le mani sul prodotto, poi parliamo di numeri.", options: { fontSize: 9, color: C.textSec, fontFace: "Calibri", breakLine: true } },
      { text: "\nUna considerazione sulla finestra temporale: se la stagionalit\u00E0 del settore \u00E8 quella che immagino \u2014 meno afflusso clienti in estate, ripartenza a settembre \u2014 allora la POC in questo periodo potrebbe essere un vantaggio. Il professionista avrebbe il tempo di imparare il sistema senza la pressione dell\u2019agenda piena, per arrivare operativo alla ripresa. Ma tu conosci il mercato meglio di me \u2014 \u00E8 una delle cose di cui parlare nella prima call.", options: { fontSize: 9, color: C.textMuted, fontFace: "Calibri", italic: true } },
    ], {
      x: 0.6, y: 4.49, w: 8.8, h: 0.72, margin: [0, 0, 0, 0],
      valign: "top",
    });
  }

  // ============================================================
  // SLIDE 22 — CHIUSURA
  // ============================================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };

    // Decorative accents (mirror of slide 1)
    s.addShape(pres.shapes.RECTANGLE, {
      x: 7.5, y: 0, w: 2.5, h: 0.12, fill: { color: C.accent },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 9.88, y: 0, w: 0.12, h: 2.5, fill: { color: C.accent },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 5.5, w: 2.5, h: 0.12, fill: { color: C.accent },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 3.12, w: 0.12, h: 2.5, fill: { color: C.accent },
    });

    s.addText([
      { text: "Il prodotto c'\u00E8.", options: { fontSize: 28, bold: true, color: C.white, fontFace: "Trebuchet MS", breakLine: true } },
      { text: "La strategia c'\u00E8.", options: { fontSize: 28, bold: true, color: C.accent, fontFace: "Trebuchet MS", breakLine: true } },
      { text: "I termini sono sul tavolo.", options: { fontSize: 28, bold: true, color: C.gold, fontFace: "Trebuchet MS" } },
    ], { x: 0.8, y: 0.55, w: 8.4, h: 1.5, margin: 0 });

    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.8, y: 2.15, w: 3, h: 0.03, fill: { color: C.accent },
    });

    s.addText("La struttura \u00E8 a fasi \u2014 iniziamo dalla POC, vediamo come lavoriamo insieme, e costruiamo da l\u00EC.", {
      x: 0.8, y: 2.3, w: 8.4, h: 0.4, margin: 0,
      fontSize: 14, fontFace: "Calibri", color: C.textSec,
    });

    s.addText("Questo progetto non \u00E8 nato per caso. \u00C8 nato da un sogno che avevamo con mio padre \u2014 pioniere dell\u2019intelligenza artificiale in Italia \u2014 e da 15+ anni passati a gestire sistemi complessi, dai cantieri navali alle operazioni offshore. FitManager porta avanti quella visione: la tecnologia al servizio del lavoro reale delle persone.", {
      x: 0.8, y: 2.8, w: 8.4, h: 0.75, margin: 0,
      fontSize: 12, fontFace: "Calibri", color: C.textMuted, italic: true,
    });

    s.addText("Domani parto per Marsiglia per un paio di settimane. Ma la testa \u00E8 qui \u2014 su questo progetto, su questa partnership, su quello che possiamo costruire insieme.", {
      x: 0.8, y: 3.65, w: 8.4, h: 0.65, margin: 0,
      fontSize: 12, fontFace: "Calibri", color: C.textSec,
    });

    addCard(pres, s, 0.8, 4.4, 3.2, 0.4, C.accent);
    s.addText("Che ne dici?", {
      x: 0.8, y: 4.4, w: 3.2, h: 0.4, margin: 0,
      fontSize: 16, fontFace: "Trebuchet MS", bold: true, color: C.bg, align: "center", valign: "middle",
    });

    s.addText("Giacomo", {
      x: 0.8, y: 4.85, w: 5, h: 0.25, margin: 0,
      fontSize: 11, fontFace: "Calibri", color: C.textMuted,
    });
    s.addText("Documento Operativo Partner \u2014 30 Marzo 2026", {
      x: 5.5, y: 4.85, w: 4, h: 0.25, margin: 0,
      fontSize: 11, fontFace: "Calibri", color: C.textMuted, align: "right",
    });

    s.addText(`${TOTAL} / ${TOTAL}`, {
      x: 8.5, y: 5.1, w: 1, h: 0.25,
      fontSize: 8, color: C.textMuted, fontFace: "Calibri", align: "right",
    });
  }

  // ============================================================
  // WRITE FILE
  // ============================================================
  await pres.writeFile({ fileName: "docs/FitManager_DocOperativo_Partner.pptx" });
  console.log("Done: docs/FitManager_DocOperativo_Partner.pptx (22 slides)");
}

build().catch(err => { console.error(err); process.exit(1); });

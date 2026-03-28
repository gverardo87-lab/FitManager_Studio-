const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const path = require("path");

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

// Same palette as Partner Brief — visual family
const C = {
  bg:       "0F1117",
  bgCard:   "1A1D27",
  bgLight:  "F7F8FA",
  accent:   "00C896",
  accent2:  "0891B2",
  accent3:  "F59E0B",
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

function darkSlide(pres) {
  const s = pres.addSlide();
  s.background = { color: C.bg };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.04, fill: { color: C.accent } });
  s.addText("FitManager Studio+ — Documento Operativo Partner  |  AVGV Technologies  |  Marzo 2026", {
    x: 0, y: 5.25, w: 10, h: 0.375,
    fontSize: 7.5, fontFace: FONT_B, color: C.grayDark, align: "center", valign: "middle"
  });
  return s;
}

function lightSlide(pres) {
  const s = pres.addSlide();
  s.background = { color: C.bgLight };
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.04, fill: { color: C.accent } });
  s.addText("FitManager Studio+ — Documento Operativo Partner  |  AVGV Technologies  |  Marzo 2026", {
    x: 0, y: 5.25, w: 10, h: 0.375,
    fontSize: 7.5, fontFace: FONT_B, color: C.grayDark, align: "center", valign: "middle"
  });
  return s;
}

function addCard(slide, pres, x, y, w, h, fillColor) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h, fill: { color: fillColor || C.bgCard }, shadow: makeCardShadow()
  });
}

function addTitle(s, title, opts = {}) {
  s.addText(title, {
    x: opts.x || 0.6, y: opts.y || 0.25, w: opts.w || 8.8, h: 0.55,
    fontSize: opts.fontSize || 26, fontFace: FONT_H, color: opts.color || C.white,
    bold: true, margin: 0
  });
}

function addSubtitle(s, text, opts = {}) {
  s.addText(text, {
    x: opts.x || 0.6, y: opts.y || 0.85, w: opts.w || 8.8, h: 0.4,
    fontSize: opts.fontSize || 12, fontFace: FONT_B, color: opts.color || C.gray,
    italic: true, margin: 0
  });
}

// Table helper for dark slides
function addDarkTable(s, headers, rows, opts = {}) {
  const hdrRow = headers.map(h => ({
    text: h, options: { bold: true, color: C.white, fill: { color: "1E2130" }, fontSize: 10.5 }
  }));
  const dataRows = rows.map(r => r.map((cell, ci) => {
    const isFirst = ci === 0;
    return {
      text: cell,
      options: {
        color: isFirst ? C.white : C.text,
        bold: isFirst,
        fontSize: 10.5,
        align: opts.alignCenter && ci > 0 ? "center" : "left"
      }
    };
  }));
  s.addTable([hdrRow, ...dataRows], {
    x: opts.x || 0.6, y: opts.y || 1.3, w: opts.w || 8.8,
    colW: opts.colW,
    rowH: opts.rowH || 0.38,
    border: { pt: 0.5, color: C.grayLine },
    fontFace: FONT_B, fontSize: 10.5,
    fill: { color: C.bgCard }
  });
}

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Giacomo Verardo — AVGV Technologies";
  pres.title = "FitManager Studio+ — Documento Operativo Partner";

  // Icons
  const { FaShieldAlt, FaDumbbell, FaUsers, FaWhatsapp, FaChartLine, FaServer,
    FaLock, FaAppleAlt, FaBrain, FaRocket, FaHandshake, FaCheckCircle,
    FaExclamationTriangle, FaClock, FaUserMd, FaMoneyBillWave, FaHeart,
    FaStar, FaTimes, FaCheck, FaMicrochip, FaLaptop, FaBolt, FaGlobe,
    FaFlag, FaComments, FaQuestion, FaArrowRight, FaCalendarAlt, FaCrown,
    FaNetworkWired, FaBuilding, FaMapMarkerAlt, FaBullseye, FaChartBar } = require("react-icons/fa");

  const icons = {};
  const iconList = [
    ["shield", FaShieldAlt, C.accent], ["dumbbell", FaDumbbell, C.accent],
    ["users", FaUsers, C.accent], ["whatsapp", FaWhatsapp, "25D366"],
    ["chart", FaChartLine, C.accent], ["server", FaServer, C.accent2],
    ["lock", FaLock, C.accent], ["apple", FaAppleAlt, C.accent],
    ["brain", FaBrain, C.accent2], ["rocket", FaRocket, C.accent],
    ["handshake", FaHandshake, C.accent], ["check", FaCheckCircle, C.green],
    ["warning", FaExclamationTriangle, C.accent3], ["clock", FaClock, C.accent],
    ["usermd", FaUserMd, C.accent], ["money", FaMoneyBillWave, C.accent],
    ["heart", FaHeart, C.red], ["star", FaStar, C.accent3],
    ["times", FaTimes, C.red], ["checkG", FaCheck, C.green],
    ["chip", FaMicrochip, C.accent2], ["laptop", FaLaptop, C.accent],
    ["bolt", FaBolt, C.accent3], ["globe", FaGlobe, C.accent],
    ["flag", FaFlag, C.accent], ["comments", FaComments, C.accent],
    ["question", FaQuestion, C.accent3], ["arrow", FaArrowRight, C.accent],
    ["calendar", FaCalendarAlt, C.accent], ["crown", FaCrown, C.accent3],
    ["network", FaNetworkWired, C.accent2], ["building", FaBuilding, C.accent2],
    ["mapMarker", FaMapMarkerAlt, C.accent], ["bullseye", FaBullseye, C.red],
    ["chartBar", FaChartBar, C.accent],
  ];
  for (const [key, comp, color] of iconList) {
    icons[key] = await iconToBase64Png(comp, `#${color}`);
  }

  // =============================================
  // SLIDE 1 — Copertina
  // =============================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.12, h: 5.625, fill: { color: C.accent } });

    s.addText("DOCUMENTO OPERATIVO PARTNER", {
      x: 0.8, y: 0.6, w: 8, h: 0.45,
      fontSize: 13, fontFace: FONT_B, color: C.accent, bold: true, charSpacing: 5, margin: 0
    });
    s.addText("FitManager Studio+", {
      x: 0.8, y: 1.2, w: 8.5, h: 0.9,
      fontSize: 42, fontFace: FONT_H, color: C.white, bold: true, margin: 0
    });
    s.addText("Struttura, numeri e piano di lancio", {
      x: 0.8, y: 2.15, w: 8, h: 0.5,
      fontSize: 18, fontFace: FONT_B, color: C.text, margin: 0
    });
    s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 2.85, w: 2.5, h: 0.035, fill: { color: C.accent } });

    s.addText("Marzo 2026  |  Giacomo Verardo → Alessio Crociani", {
      x: 0.8, y: 3.1, w: 8, h: 0.35,
      fontSize: 12, fontFace: FONT_B, color: C.gray, margin: 0
    });

    // Personal note card
    addCard(s, pres, 0.8, 3.65, 7.8, 1.4, "1E2130");
    s.addText("Alessio, hai visto il prodotto dal vivo. Sai cosa fa. Questo documento ti mostra la struttura operativa, economica e di lancio — calibrata su quello che possiamo costruire insieme.\n\nLeggilo come una proposta aperta: dove la vedi diversamente, parliamone.\n\nNDA formale lunedì. Intanto, questo è il livello di dettaglio con cui lavoro.", {
      x: 1.0, y: 3.75, w: 7.4, h: 1.2,
      fontSize: 10.5, fontFace: FONT_B, color: C.gray, italic: true, margin: 0
    });
  }

  // =============================================
  // SLIDE 2 — Dove siamo oggi
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "Dove siamo oggi");
    addSubtitle(s, "Il prodotto è completo (v1.0.5). Non è un prototipo — è in uso quotidiano.");

    // Stats grid — 3x2
    const stats = [
      ["45.000+", "Righe di codice"],
      ["395", "Test automatici"],
      ["500", "Esercizi + biomeccanica"],
      ["880", "Alimenti CREA"],
      ["5", "Motori scientifici"],
      ["47", "Condizioni cliniche\n(80 regole)"],
    ];
    stats.forEach((st, i) => {
      const col = i % 3;
      const row = Math.floor(i / 3);
      const cx = 0.6 + col * 3.1;
      const cy = 1.3 + row * 1.3;
      addCard(s, pres, cx, cy, 2.85, 1.1, C.bgCard);
      s.addText(st[0], {
        x: cx, y: cy + 0.12, w: 2.85, h: 0.5,
        fontSize: 28, fontFace: FONT_H, color: C.accent, bold: true,
        align: "center", margin: 0
      });
      s.addText(st[1], {
        x: cx, y: cy + 0.65, w: 2.85, h: 0.35,
        fontSize: 10, fontFace: FONT_B, color: C.gray,
        align: "center", margin: 0
      });
    });

    // Context line
    s.addText("La prima utilizzatrice reale (chinesiologia, Genova) lo usa ogni giorno. Le sue clienti ricevono schede professionali e compilano anamnesi dal telefono.", {
      x: 0.6, y: 3.95, w: 8.8, h: 0.4,
      fontSize: 10.5, fontFace: FONT_B, color: C.gray, margin: 0
    });

    // Key statement
    s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 4.5, w: 8.8, h: 0.55, fill: { color: "1A2A1F" } });
    s.addText("Cosa manca: non il prodotto. La leva per portarlo al mercato — in Italia e fuori.", {
      x: 0.6, y: 4.5, w: 8.8, h: 0.55,
      fontSize: 13, fontFace: FONT_H, color: C.accent, bold: true,
      align: "center", valign: "middle", margin: 0
    });
  }

  // =============================================
  // SLIDE 3 — Il pricing
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "Il pricing");
    addSubtitle(s, "Licenza perpetua: il trainer compra una volta, il software è suo.");

    // Pricing table with margins
    const pricingRows = [
      ["Licenza software", "€249", "~€30", "€219 (88%)"],
      ["FitManager Box", "€449", "~€150", "€299 (67%)"],
      ["Assistenza PRO", "€79/anno", "~€0", "€79 (100%)"],
      ["Inner Circle", "€249/anno", "~€0", "€249 (100%)"],
    ];
    pricingRows.forEach((r, i) => {
      const cy = 1.3 + i * 0.7;
      addCard(s, pres, 0.6, cy, 8.8, 0.58, C.bgCard);
      s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: cy, w: 0.06, h: 0.58, fill: { color: C.accent } });
      // Product
      s.addText(r[0], {
        x: 0.85, y: cy + 0.1, w: 2.5, h: 0.38,
        fontSize: 12, fontFace: FONT_H, color: C.white, bold: true, valign: "middle", margin: 0
      });
      // Price
      s.addText(r[1], {
        x: 3.5, y: cy + 0.1, w: 1.5, h: 0.38,
        fontSize: 14, fontFace: FONT_H, color: C.accent, bold: true, valign: "middle", margin: 0
      });
      // Cost
      s.addText(r[2], {
        x: 5.2, y: cy + 0.1, w: 1.3, h: 0.38,
        fontSize: 11, fontFace: FONT_B, color: C.gray, valign: "middle", margin: 0
      });
      // Margin
      s.addText(r[3], {
        x: 6.8, y: cy + 0.1, w: 2.4, h: 0.38,
        fontSize: 12, fontFace: FONT_H, color: C.green, bold: true, valign: "middle", margin: 0
      });
    });

    // Headers for columns
    s.addText("Prodotto", { x: 0.85, y: 1.08, w: 2, h: 0.22, fontSize: 8.5, fontFace: FONT_B, color: C.grayDark, margin: 0 });
    s.addText("Prezzo", { x: 3.5, y: 1.08, w: 1.5, h: 0.22, fontSize: 8.5, fontFace: FONT_B, color: C.grayDark, margin: 0 });
    s.addText("Costo vivo", { x: 5.2, y: 1.08, w: 1.3, h: 0.22, fontSize: 8.5, fontFace: FONT_B, color: C.grayDark, margin: 0 });
    s.addText("Margine lordo", { x: 6.8, y: 1.08, w: 2, h: 0.22, fontSize: 8.5, fontFace: FONT_B, color: C.grayDark, margin: 0 });

    // Break-even + international
    addCard(s, pres, 0.6, 4.15, 4.2, 0.8, "1A2A1F");
    s.addImage({ data: icons.bullseye, x: 0.8, y: 4.3, w: 0.35, h: 0.35 });
    s.addText("Break-even operativo", {
      x: 1.25, y: 4.2, w: 3.3, h: 0.25,
      fontSize: 10, fontFace: FONT_B, color: C.gray, margin: 0
    });
    s.addText("~3 vendite/mese", {
      x: 1.25, y: 4.48, w: 3.3, h: 0.35,
      fontSize: 16, fontFace: FONT_H, color: C.accent, bold: true, margin: 0
    });

    addCard(s, pres, 5.2, 4.15, 4.2, 0.8, "1A2A1F");
    s.addImage({ data: icons.globe, x: 5.4, y: 4.3, w: 0.35, h: 0.35 });
    s.addText("Pricing internazionale", {
      x: 5.85, y: 4.2, w: 3.3, h: 0.25,
      fontSize: 10, fontFace: FONT_B, color: C.gray, margin: 0
    });
    s.addText("Margine per prezzo più alto", {
      x: 5.85, y: 4.48, w: 3.3, h: 0.35,
      fontSize: 12, fontFace: FONT_H, color: C.accent2, bold: true, margin: 0
    });
  }

  // =============================================
  // SLIDE 4 — Perché questo progetto ha bisogno di Alessio
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "Perché questo progetto ha bisogno di Alessio", { fontSize: 24 });

    s.addText("Il prodotto è pronto. Il mercato no. Per muovere questo mercato servono asset specifici che non si comprano.", {
      x: 0.6, y: 0.85, w: 8.8, h: 0.4,
      fontSize: 11, fontFace: FONT_B, color: C.gray, margin: 0
    });

    const assets = [
      ["building", "Rete diretta catene e centri", "Un singolo accordo con una catena = 5-15 vendite.\nCambia l'ordine di grandezza."],
      ["users",    "Community e seguito social", "I Fondatori POC sono professionisti selezionati dalla rete.\nLa qualità della POC cambia radicalmente."],
      ["crown",    "Formazione ed eventi",       "Le masterclass Inner Circle sono sessioni condotte da una voce\nriconosciuta. Valore percepito e conversione raddoppiano."],
      ["globe",    "Connessioni internazionali", "La versione internazionale non parte da zero — parte da\ncontatti reali, in mercati dove si paga di più."],
    ];
    assets.forEach((a, i) => {
      const cy = 1.4 + i * 0.95;
      addCard(s, pres, 0.6, cy, 8.8, 0.82, C.bgCard);
      s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: cy, w: 0.06, h: 0.82, fill: { color: C.accent } });
      s.addImage({ data: icons[a[0]], x: 0.85, y: cy + 0.2, w: 0.38, h: 0.38 });
      s.addText(a[1], {
        x: 1.4, y: cy + 0.08, w: 3, h: 0.3,
        fontSize: 12, fontFace: FONT_H, color: C.white, bold: true, margin: 0
      });
      s.addText(a[2], {
        x: 4.5, y: cy + 0.08, w: 4.7, h: 0.65,
        fontSize: 10, fontFace: FONT_B, color: C.gray, margin: 0
      });
    });
  }

  // =============================================
  // SLIDE 5 — Architettura pronta per l'internazionale
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "L'architettura è pronta per l'internazionale", { fontSize: 24 });
    addSubtitle(s, "Progettato con l'internazionalizzazione nell'architettura, non come adattamento.");

    // 4 blocks
    const blocks = [
      ["1", "Interfaccia e core",        "Bassa",     "~1 settimana/lingua", "Traduzione UI, template, formati data/valuta"],
      ["2", "Esercizi + Safety Engine",   "Media",     "2-4 settimane",       "Scienza universale — serve adattamento terminologico"],
      ["3", "Nutrizione e compliance",    "Alta",      "2-3 mesi",            "DB nutrizionali locali (Livsmedelsverket, USDA, etc.)"],
      ["4", "Moduli fiscali/economici",   "Variabile", "Da definire",         "Pagamenti, fatturazione per giurisdizione"],
    ];
    blocks.forEach((b, i) => {
      const cy = 1.35 + i * 0.78;
      addCard(s, pres, 0.6, cy, 8.8, 0.65, C.bgCard);
      // Block number
      s.addShape(pres.shapes.OVAL, { x: 0.75, y: cy + 0.1, w: 0.42, h: 0.42, fill: { color: C.accent } });
      s.addText(b[0], {
        x: 0.75, y: cy + 0.1, w: 0.42, h: 0.42,
        fontSize: 16, fontFace: FONT_H, color: C.bg, bold: true, align: "center", valign: "middle", margin: 0
      });
      s.addText(b[1], {
        x: 1.35, y: cy + 0.06, w: 2.6, h: 0.25,
        fontSize: 11, fontFace: FONT_H, color: C.white, bold: true, margin: 0
      });
      // Complexity badge
      const compColor = b[2] === "Bassa" ? C.green : b[2] === "Media" ? C.accent3 : b[2] === "Alta" ? C.red : C.gray;
      s.addText(b[2], {
        x: 1.35, y: cy + 0.32, w: 0.8, h: 0.22,
        fontSize: 9, fontFace: FONT_B, color: compColor, bold: true, margin: 0
      });
      s.addText(b[3], {
        x: 2.3, y: cy + 0.32, w: 1.6, h: 0.22,
        fontSize: 9, fontFace: FONT_B, color: C.gray, margin: 0
      });
      s.addText(b[4], {
        x: 4.3, y: cy + 0.1, w: 5, h: 0.45,
        fontSize: 10, fontFace: FONT_B, color: C.gray, valign: "middle", margin: 0
      });
    });

    // Takeaway
    addCard(s, pres, 0.6, 4.6, 8.8, 0.5, "1A2A1F");
    s.addText("Blocchi 1-2 pronti in 4-6 settimane per qualsiasi lingua. Il prodotto è pienamente utilizzabile senza i Blocchi 3-4.", {
      x: 0.8, y: 4.6, w: 8.4, h: 0.5,
      fontSize: 11, fontFace: FONT_B, color: C.accent, bold: true, valign: "middle", margin: 0
    });
  }

  // =============================================
  // SLIDE 6 — Italia prima, internazionale subito dopo
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "Italia prima, internazionale subito dopo", { fontSize: 24 });

    // Timeline — 4 phases vertical
    const phases = [
      [C.accent, "Mesi 1-6", "Italia — Focus totale", "POC 10 Fondatori, consolidamento tecnico, social proof, validazione pricing e categoria PT Evoluto"],
      [C.accent2, "Mesi 4-6", "Prep. internazionale (parallelo)", "Blocchi 1-2 tradotti, primi contatti dalla rete di Alessio, pricing e landing page in lingua"],
      [C.accent3, "Mesi 7-12", "Pilota internazionale", "5-10 utenti pilota nel mercato target, feedback loop, Blocco 3 in sviluppo parallelo"],
      [C.accent, "Anno 2+", "Due mercati attivi", "Italia consolidata + lancio strutturato con social proof locale, pricing specifico"],
    ];
    phases.forEach((p, i) => {
      const cy = 1.0 + i * 1.02;
      addCard(s, pres, 0.6, cy, 8.8, 0.88, C.bgCard);
      s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: cy, w: 0.06, h: 0.88, fill: { color: p[0] } });
      s.addText(p[1], {
        x: 0.85, y: cy + 0.08, w: 1.5, h: 0.25,
        fontSize: 10, fontFace: FONT_B, color: p[0], bold: true, margin: 0
      });
      s.addText(p[2], {
        x: 0.85, y: cy + 0.35, w: 2.5, h: 0.3,
        fontSize: 12, fontFace: FONT_H, color: C.white, bold: true, margin: 0
      });
      s.addText(p[3], {
        x: 3.5, y: cy + 0.1, w: 5.7, h: 0.65,
        fontSize: 10, fontFace: FONT_B, color: C.gray, valign: "middle", margin: 0
      });
    });

    // Why 6 months
    s.addText("Perché 6 mesi: il contatto con 10-30 utenti reali farà emergere edge case che non esistono in laboratorio. Esportare prima = portare problemi dove non hai credibilità.", {
      x: 0.6, y: 5.0, w: 8.8, h: 0.2,
      fontSize: 9, fontFace: FONT_B, color: C.grayDark, italic: true, margin: 0
    });
  }

  // =============================================
  // SLIDE 7 — La struttura di compenso
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "La struttura di compenso");
    addSubtitle(s, "Zero costi fissi. Compenso interamente legato ai ricavi generati.");

    // Revenue share components
    const comp = [
      ["25%", "Ricavi POC",              "Licenze e Box dei 10 Fondatori"],
      ["20%", "Vendite dal network",      "Licenze e Box via referral tracciato — Italia e internazionale"],
      ["25%", "PRO + Inner Circle",       "Tutti i rinnovi e abbonamenti"],
      ["30%", "Masterclass condotte",     "Sessioni live + registrate (revenue share perpetuo in libreria)"],
    ];
    comp.forEach((c, i) => {
      const cy = 1.35 + i * 0.68;
      addCard(s, pres, 0.6, cy, 8.8, 0.55, C.bgCard);
      s.addText(c[0], {
        x: 0.75, y: cy + 0.05, w: 0.9, h: 0.45,
        fontSize: 22, fontFace: FONT_H, color: C.accent, bold: true, valign: "middle", margin: 0
      });
      s.addText(c[1], {
        x: 1.75, y: cy + 0.05, w: 2.5, h: 0.22,
        fontSize: 12, fontFace: FONT_H, color: C.white, bold: true, margin: 0
      });
      s.addText(c[2], {
        x: 1.75, y: cy + 0.3, w: 6.5, h: 0.2,
        fontSize: 10, fontFace: FONT_B, color: C.gray, margin: 0
      });
    });

    // Equity + Masterclass ownership
    const cy2 = 4.15;
    addCard(s, pres, 0.6, cy2, 4.2, 0.85, C.bgCard);
    s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: cy2, w: 4.2, h: 0.06, fill: { color: C.accent3 } });
    s.addText("Equity: 5-8%", {
      x: 0.8, y: cy2 + 0.15, w: 3.8, h: 0.3,
      fontSize: 14, fontFace: FONT_H, color: C.accent3, bold: true, margin: 0
    });
    s.addText("Maturazione 4 anni, cliff 12 mesi", {
      x: 0.8, y: cy2 + 0.48, w: 3.8, h: 0.25,
      fontSize: 10, fontFace: FONT_B, color: C.gray, margin: 0
    });

    addCard(s, pres, 5.2, cy2, 4.2, 0.85, C.bgCard);
    s.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: cy2, w: 4.2, h: 0.06, fill: { color: C.accent } });
    s.addText("Masterclass: proprietà condivisa", {
      x: 5.4, y: cy2 + 0.15, w: 3.8, h: 0.3,
      fontSize: 12, fontFace: FONT_H, color: C.accent, bold: true, margin: 0
    });
    s.addText("30% rev share perpetuo per ogni registrazione", {
      x: 5.4, y: cy2 + 0.48, w: 3.8, h: 0.25,
      fontSize: 10, fontFace: FONT_B, color: C.gray, margin: 0
    });
  }

  // =============================================
  // SLIDE 8 — Due scenari: floor e calibrato
  // =============================================
  {
    const s = lightSlide(pres);
    s.addText("Due scenari: il floor e il realistico", {
      x: 0.6, y: 0.2, w: 8.8, h: 0.5,
      fontSize: 24, fontFace: FONT_H, color: C.textDark, bold: true, margin: 0
    });

    // Floor table
    s.addText("FLOOR CONSERVATIVO — solo Italia, crescita organica", {
      x: 0.6, y: 0.75, w: 8.8, h: 0.3,
      fontSize: 10, fontFace: FONT_B, color: C.grayDark, bold: true, margin: 0
    });
    const floorHdr = ["", "Anno 1", "Anno 2", "Anno 3", "Cumulativo"].map(h => ({
      text: h, options: { bold: true, color: C.white, fill: { color: C.textDark }, fontSize: 9.5, align: "center" }
    }));
    const floorRows = [
      ["Clienti", "46", "104", "191", "—"],
      ["Fatturato", "€17.150", "€29.650", "€49.650", "€96.450"],
      ["Compenso Alessio (cash)", "€2.375", "€4.200", "€7.500", "€14.075"],
      ["Equity (6%)", "€1.600", "€4.100", "€8.400", "—"],
      ["Totale Alessio", "€3.975", "€8.300", "€15.900", "€28.175"],
    ].map(r => r.map((c, ci) => ({
      text: c, options: {
        color: ci === 0 ? C.textDark : (r[0] === "Totale Alessio" ? "16A34A" : C.grayDark),
        bold: ci === 0 || r[0] === "Totale Alessio",
        fontSize: 9.5, align: ci === 0 ? "left" : "center"
      }
    })));
    s.addTable([floorHdr, ...floorRows], {
      x: 0.6, y: 1.05, w: 8.8, colW: [2.6, 1.55, 1.55, 1.55, 1.55],
      rowH: 0.3, border: { pt: 0.5, color: "E2E8F0" }, fontFace: FONT_B
    });

    // Calibrated table
    s.addText("SCENARIO CALIBRATO — Italia + internazionale, leva catene e rete Alessio", {
      x: 0.6, y: 2.7, w: 8.8, h: 0.3,
      fontSize: 10, fontFace: FONT_B, color: "16A34A", bold: true, margin: 0
    });
    const calHdr = ["", "Anno 1", "Anno 2", "Anno 3", "Cumulativo"].map(h => ({
      text: h, options: { bold: true, color: C.white, fill: { color: "16A34A" }, fontSize: 9.5, align: "center" }
    }));
    const calRows = [
      ["Clienti Italia", "80-100", "150-200", "250-350", "—"],
      ["Clienti internazionali", "—", "30-60", "100-200+", "—"],
      ["Inner Circle", "20-30", "50-80", "100-150", "—"],
      ["Fatturato", "€35-50K", "€80-130K", "€170-300K+", "€285-480K"],
      ["Compenso Alessio (cash)", "€6-9K", "€15-28K", "€35-60K", "€56-97K"],
      ["Equity Alessio", "€3-5K", "€10-20K", "€30-55K", "—"],
    ].map(r => r.map((c, ci) => ({
      text: c, options: {
        color: ci === 0 ? C.textDark : (r[0].startsWith("Compenso") || r[0].startsWith("Equity") ? "16A34A" : C.grayDark),
        bold: ci === 0 || r[0].startsWith("Compenso") || r[0].startsWith("Equity"),
        fontSize: 9.5, align: ci === 0 ? "left" : "center"
      }
    })));
    s.addTable([calHdr, ...calRows], {
      x: 0.6, y: 3.0, w: 8.8, colW: [2.6, 1.55, 1.55, 1.55, 1.55],
      rowH: 0.3, border: { pt: 0.5, color: "E2E8F0" }, fontFace: FONT_B
    });

    // Takeaway
    s.addText("La variabile chiave tra floor e calibrato è la leva di rete — in Italia e fuori. Il floor non è il piano: è la rete di sicurezza.", {
      x: 0.6, y: 4.95, w: 8.8, h: 0.25,
      fontSize: 10, fontFace: FONT_B, color: C.grayDark, bold: true, italic: true, margin: 0
    });
  }

  // =============================================
  // SLIDE 9 — Leva internazionale: Nordic Wellness
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "Cosa cambia con la leva internazionale");
    addSubtitle(s, "Un esempio concreto: Nordic Wellness — centinaia di sedi, migliaia di trainer.");

    // Nordic Wellness card
    addCard(s, pres, 0.6, 1.4, 8.8, 2.6, C.bgCard);
    s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 1.4, w: 8.8, h: 0.06, fill: { color: C.accent2 } });

    s.addText("Nordic Wellness — ipotesi conservativa", {
      x: 0.85, y: 1.55, w: 5, h: 0.3,
      fontSize: 14, fontFace: FONT_H, color: C.accent2, bold: true, margin: 0
    });

    const nwData = [
      ["Trainer contattabili tramite accordo", "100-200"],
      ["Tasso adozione (conservativo)", "15-20%"],
      ["Vendite da un singolo accordo", "15-40"],
      ["Ricavo (pricing nordico, €349-549)", "€5.000-22.000"],
      ["Inner Circle (25% dei nuovi)", "+€1.000-2.500/anno"],
    ];
    nwData.forEach((d, i) => {
      const cy = 2.0 + i * 0.38;
      s.addText(d[0], {
        x: 0.85, y: cy, w: 5.5, h: 0.3,
        fontSize: 11, fontFace: FONT_B, color: C.gray, margin: 0
      });
      s.addText(d[1], {
        x: 6.5, y: cy, w: 2.7, h: 0.3,
        fontSize: 12, fontFace: FONT_H, color: C.accent, bold: true, align: "right", margin: 0
      });
    });

    // Comparison statement
    s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 4.25, w: 8.8, h: 0.8, fill: { color: "1A2A1F" } });
    s.addText("Un singolo accordo con una catena internazionale\nvale quanto 3-6 mesi di vendita organica in Italia.", {
      x: 0.6, y: 4.25, w: 8.8, h: 0.55,
      fontSize: 14, fontFace: FONT_H, color: C.accent, bold: true,
      align: "center", valign: "middle", margin: 0
    });
    s.addText("E Nordic Wellness non è l'unica catena. È un esempio — il primo di una serie.", {
      x: 0.6, y: 4.75, w: 8.8, h: 0.3,
      fontSize: 11, fontFace: FONT_B, color: C.gray, align: "center", margin: 0
    });
  }

  // =============================================
  // SLIDE 10 — La POC: 10 Fondatori
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "La POC: 10 Fondatori, 90 giorni");
    addSubtitle(s, "Non vendiamo subito. Prima dimostriamo — il pacchetto completo.");

    // What founders receive
    s.addText("Cosa ricevono i Fondatori", {
      x: 0.6, y: 1.35, w: 5, h: 0.3,
      fontSize: 13, fontFace: FONT_H, color: C.accent, bold: true, margin: 0
    });
    const fItems = [
      "8 ricevono licenza software (€99) + 2 ricevono la Box (€199)",
      "Inner Circle 12 mesi incluso",
      "Community Fondatori riservata",
      "Installazione 1:1 con il founder",
    ];
    fItems.forEach((f, i) => {
      const cy = 1.75 + i * 0.35;
      s.addImage({ data: icons.check, x: 0.8, y: cy + 0.03, w: 0.22, h: 0.22 });
      s.addText(f, {
        x: 1.15, y: cy, w: 5, h: 0.28,
        fontSize: 11, fontFace: FONT_B, color: C.text, margin: 0
      });
    });

    // Right side: economics
    addCard(s, pres, 5.5, 1.35, 4.0, 2.0, C.bgCard);
    s.addShape(pres.shapes.RECTANGLE, { x: 5.5, y: 1.35, w: 4.0, h: 0.06, fill: { color: C.accent } });
    s.addText("Valore reale: €498-698", {
      x: 5.7, y: 1.5, w: 3.6, h: 0.3,
      fontSize: 11, fontFace: FONT_B, color: C.gray, margin: 0
    });
    s.addText("Lo ottengono a\n€99-199", {
      x: 5.7, y: 1.85, w: 3.6, h: 0.6,
      fontSize: 20, fontFace: FONT_H, color: C.accent, bold: true, margin: 0
    });
    s.addText("Ricavo POC: €1.190\nCosto vivo: ~€300 (2 Box)\nInvestimento netto: ~€300", {
      x: 5.7, y: 2.55, w: 3.6, h: 0.65,
      fontSize: 10, fontFace: FONT_B, color: C.gray, margin: 0
    });

    // Bottom: Alessio's role
    addCard(s, pres, 0.6, 3.65, 8.8, 0.7, "1A2A1F");
    s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 3.65, w: 0.06, h: 0.7, fill: { color: C.accent } });
    s.addText("Con la rete di Alessio, i 10 Fondatori sono professionisti scelti che rappresentano i profili giusti e che hanno influenza nel proprio circolo.", {
      x: 0.85, y: 3.7, w: 8.3, h: 0.55,
      fontSize: 11.5, fontFace: FONT_B, color: C.accent, bold: true, valign: "middle", margin: 0
    });

    // Note on POC cost
    s.addText("Se la POC non funziona, lo scopriamo con 10 persone e ~€1.000. Zero debito.", {
      x: 0.6, y: 4.55, w: 8.8, h: 0.35,
      fontSize: 10, fontFace: FONT_B, color: C.grayDark, italic: true, align: "center", margin: 0
    });
  }

  // =============================================
  // SLIDE 11 — I ruoli nella POC
  // =============================================
  {
    const s = lightSlide(pres);
    s.addText("I ruoli nella POC", {
      x: 0.6, y: 0.2, w: 8.8, h: 0.5,
      fontSize: 24, fontFace: FONT_H, color: C.textDark, bold: true, margin: 0
    });
    s.addText("I temi delle masterclass nel BP sono una traccia — la struttura la definiamo insieme.", {
      x: 0.6, y: 0.7, w: 8.8, h: 0.3,
      fontSize: 10.5, fontFace: FONT_B, color: C.grayDark, italic: true, margin: 0
    });

    const roleHdr = ["Attività", "Chi", "Ore"].map(h => ({
      text: h, options: { bold: true, color: C.white, fill: { color: C.textDark }, fontSize: 10, align: "center" }
    }));
    roleHdr[0].options.align = "left";
    const roleRows = [
      ["Selezione 10 Fondatori dal network", "Alessio + Giacomo", "3-4"],
      ["Installazione, setup, template WA", "Giacomo", "15-20"],
      ["Check-in bisettimanali", "Giacomo", "20"],
      ["Masterclass mese 1", "Alessio", "2-3"],
      ["Webinar mese 2", "Alessio + Giacomo", "2"],
      ["Masterclass mese 3", "Alessio", "2-3"],
      ["Sessione di gruppo finale (giorno 90)", "Alessio + Giacomo", "2"],
      ["Micro-sondaggi e analisi dati", "Giacomo", "5"],
    ].map(r => r.map((c, ci) => {
      const isAlessio = c.includes("Alessio") && ci === 1;
      return {
        text: c, options: {
          color: isAlessio ? "16A34A" : C.textDark,
          bold: isAlessio,
          fontSize: 10, align: ci === 0 ? "left" : "center"
        }
      };
    }));

    // Total rows
    const totalRows = [
      ["Totale Alessio", "", "~15-20 ore / 90gg"],
      ["Totale Giacomo", "", "~40-45 ore / 90gg"],
    ].map(r => r.map((c, ci) => ({
      text: c, options: {
        color: r[0].includes("Alessio") ? "16A34A" : C.textDark,
        bold: true, fontSize: 10, align: ci === 0 ? "left" : "center",
        fill: ci === 0 ? { color: "F0FDF4" } : undefined
      }
    })));

    s.addTable([roleHdr, ...roleRows, ...totalRows], {
      x: 0.6, y: 1.05, w: 8.8, colW: [4.8, 2.2, 1.8],
      rowH: 0.35, border: { pt: 0.5, color: "E2E8F0" }, fontFace: FONT_B
    });
  }

  // =============================================
  // SLIDE 12 — Le metriche che decidono tutto
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "Le metriche che decidono tutto");

    // Metrics table
    const metrics = [
      ["Ore admin risparmiate",          "Da 3-5h a <2h/sett.", "Il prodotto"],
      ["Messaggi WA pre-compilati/sett.", "15+",                "Adozione comunicazione"],
      ["Tempo risparmiato comunicazione", "30+ min/giorno",     "Valore feature chiave"],
      ["NPS",                             "Sopra 50",           "Prodotto + percorso"],
      ["\"Lo ricomprerei a prezzo pieno\"","8/10 sì",           "Modello economico"],
      ["\"I clienti notano differenza\"",  "5/10 sì",           "Volano PT Evoluto"],
      ["\"Mi definirei PT Evoluto\"",      "6/10 sì",           "Category creation"],
    ];
    metrics.forEach((m, i) => {
      const cy = 1.0 + i * 0.47;
      addCard(s, pres, 0.6, cy, 8.8, 0.38, C.bgCard);
      s.addText(m[0], {
        x: 0.8, y: cy + 0.03, w: 3.8, h: 0.32,
        fontSize: 10.5, fontFace: FONT_B, color: C.white, valign: "middle", margin: 0
      });
      s.addText(m[1], {
        x: 4.8, y: cy + 0.03, w: 2, h: 0.32,
        fontSize: 11, fontFace: FONT_H, color: C.accent, bold: true, valign: "middle", margin: 0
      });
      s.addText(m[2], {
        x: 7.0, y: cy + 0.03, w: 2.3, h: 0.32,
        fontSize: 9.5, fontFace: FONT_B, color: C.gray, valign: "middle", margin: 0
      });
    });

    // Decision at day 90
    s.addText("La decisione al giorno 90:", {
      x: 0.6, y: 4.4, w: 8.8, h: 0.3,
      fontSize: 12, fontFace: FONT_H, color: C.white, bold: true, margin: 0
    });
    // GO / GO cautela / STOP
    const decisions = [
      [C.green, "GO", "NPS 50+, ore dimezzate, 8+ attivi, 5+ clienti notano"],
      [C.accent3, "GO cautela", "NPS 30-50 — si aggiusta e si riparte con 5 nuovi"],
      [C.red, "STOP", "NPS <30, <6 attivi — costo totale: 3 mesi e ~€1.000"],
    ];
    decisions.forEach((d, i) => {
      const cx = 0.6 + i * 3.1;
      s.addShape(pres.shapes.RECTANGLE, { x: cx, y: 4.75, w: 2.85, h: 0.06, fill: { color: d[0] } });
      s.addText(d[1], {
        x: cx, y: 4.82, w: 2.85, h: 0.2,
        fontSize: 11, fontFace: FONT_H, color: d[0], bold: true, margin: 0
      });
      s.addText(d[2], {
        x: cx, y: 5.02, w: 2.85, h: 0.2,
        fontSize: 8.5, fontFace: FONT_B, color: C.gray, margin: 0
      });
    });
  }

  // =============================================
  // SLIDE 13 — Dopo la POC: il volano
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "Dopo la POC: il volano Italia + internazionale", { fontSize: 22 });

    const volanoPhases = [
      [C.accent, "Mesi 4-6", "Early Adopter + prep. internazionale",
        "Testimonial POC come leva\nInner Circle attivo (masterclass Alessio)\nBlocchi 1-2 tradotti, primi contatti nordico\nTarget IT: 15-20 clienti, 30% Inner Circle"],
      [C.accent2, "Mesi 7-12", "Scala Italia + pilota internazionale",
        "IT: tutti i canali, 3-5 vendite/mese + catene\nINT: 5-10 utenti pilota mercato target\nCertificazione PT Evoluto in costruzione\nPricing internazionale definito"],
      [C.accent3, "Anno 2+", "Due mercati attivi",
        "Italia: fiere, enti formazione, community matura\nINT: lancio con social proof locale\nInner Circle bilingue — stesso sforzo, doppio bacino\nTeam, SRL, brand riconosciuto"],
    ];
    volanoPhases.forEach((p, i) => {
      const cy = 1.0 + i * 1.4;
      addCard(s, pres, 0.6, cy, 8.8, 1.25, C.bgCard);
      s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: cy, w: 0.06, h: 1.25, fill: { color: p[0] } });
      s.addText(p[1], {
        x: 0.85, y: cy + 0.08, w: 1.5, h: 0.22,
        fontSize: 10, fontFace: FONT_B, color: p[0], bold: true, margin: 0
      });
      s.addText(p[2], {
        x: 0.85, y: cy + 0.32, w: 3, h: 0.28,
        fontSize: 12, fontFace: FONT_H, color: C.white, bold: true, margin: 0
      });
      s.addText(p[3], {
        x: 4.2, y: cy + 0.08, w: 5.0, h: 1.05,
        fontSize: 10, fontFace: FONT_B, color: C.gray, margin: 0
      });
    });
  }

  // =============================================
  // SLIDE 14 — La community: i 4 livelli
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "La community: i 4 livelli");

    const tiers = [
      [C.gray,    "Base",         "€0",       "Forum, knowledge base, networking, onboarding guidato"],
      [C.accent2, "PRO",          "€79/anno",  "Aggiornamenti, esercizi trimestrali, template mensili, supporto <24h"],
      [C.accent,  "Inner Circle", "€249/anno", "Masterclass mensile (Alessio), webinar, mastermind, early access, certificazione"],
      [C.accent3, "Mentorship",   "€499-599",  "1:1, roadmap, eventi in presenza. Max 15-20 (Anno 3+)"],
    ];
    tiers.forEach((t, i) => {
      const cy = 1.0 + i * 0.82;
      addCard(s, pres, 0.6, cy, 8.8, 0.7, C.bgCard);
      s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: cy, w: 0.06, h: 0.7, fill: { color: t[0] } });
      s.addText(t[1], {
        x: 0.85, y: cy + 0.08, w: 1.5, h: 0.25,
        fontSize: 13, fontFace: FONT_H, color: t[0], bold: true, margin: 0
      });
      s.addText(t[2], {
        x: 0.85, y: cy + 0.38, w: 1.5, h: 0.22,
        fontSize: 10, fontFace: FONT_B, color: C.gray, margin: 0
      });
      s.addText(t[3], {
        x: 2.5, y: cy + 0.1, w: 6.7, h: 0.5,
        fontSize: 11, fontFace: FONT_B, color: C.text, valign: "middle", margin: 0
      });
    });

    // Alessio's role + masterclass 3 lives
    addCard(s, pres, 0.6, 4.35, 4.2, 0.7, "1A2A1F");
    s.addText("Alessio è il cuore dell'Inner Circle", {
      x: 0.8, y: 4.4, w: 3.8, h: 0.25,
      fontSize: 11, fontFace: FONT_H, color: C.accent, bold: true, margin: 0
    });
    s.addText("Masterclass, mastermind, ospiti dalla rete, certificazione PT Evoluto.", {
      x: 0.8, y: 4.68, w: 3.8, h: 0.3,
      fontSize: 9.5, fontFace: FONT_B, color: C.gray, margin: 0
    });

    addCard(s, pres, 5.2, 4.35, 4.2, 0.7, "1A2A1F");
    s.addText("Ogni masterclass ha 3 vite", {
      x: 5.4, y: 4.4, w: 3.8, h: 0.25,
      fontSize: 11, fontFace: FONT_H, color: C.accent3, bold: true, margin: 0
    });
    s.addText("Live → registrazione (30% perpetuo) → 5-10 asset marketing derivati.", {
      x: 5.4, y: 4.68, w: 3.8, h: 0.3,
      fontSize: 9.5, fontFace: FONT_B, color: C.gray, margin: 0
    });
  }

  // =============================================
  // SLIDE 15 — WhatsApp come primo ingranaggio
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "WhatsApp come primo ingranaggio");

    // Template count + gesture
    s.addImage({ data: icons.whatsapp, x: 0.6, y: 1.0, w: 0.5, h: 0.5 });
    s.addText("15 template pre-compilati", {
      x: 1.25, y: 1.0, w: 5, h: 0.25,
      fontSize: 14, fontFace: FONT_H, color: "25D366", bold: true, margin: 0
    });
    s.addText("Sollecito rata, conferma appuntamento, scheda pronta, benvenuto, auguri, rinnovo.", {
      x: 1.25, y: 1.3, w: 7, h: 0.25,
      fontSize: 10.5, fontFace: FONT_B, color: C.gray, margin: 0
    });

    // The gesture
    addCard(s, pres, 0.6, 1.8, 8.8, 0.8, C.bgCard);
    s.addText("Il gesto:", {
      x: 0.85, y: 1.85, w: 1, h: 0.3,
      fontSize: 12, fontFace: FONT_H, color: C.white, bold: true, margin: 0
    });
    s.addText("un click → WhatsApp si apre con nome, data, importo già compilati → il trainer rivede → invia.", {
      x: 1.8, y: 1.85, w: 7.4, h: 0.3,
      fontSize: 12, fontFace: FONT_B, color: C.text, margin: 0
    });
    s.addText("KPI di attivazione POC: primo messaggio WA inviato entro 24 ore dall'installazione.", {
      x: 0.85, y: 2.2, w: 8, h: 0.25,
      fontSize: 10, fontFace: FONT_B, color: C.accent, bold: true, margin: 0
    });

    // Viral loop
    addCard(s, pres, 0.6, 2.9, 8.8, 0.8, "1A2A1F");
    s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 2.9, w: 0.06, h: 0.8, fill: { color: "25D366" } });
    s.addText("Il Fondatore che mostra questo gesto a un collega è il venditore più efficace — non vende software, mostra un gesto quotidiano fatto meglio.", {
      x: 0.85, y: 2.95, w: 8.3, h: 0.65,
      fontSize: 12, fontFace: FONT_B, color: C.text, valign: "middle", margin: 0
    });

    // International note
    addCard(s, pres, 0.6, 4.0, 8.8, 0.7, C.bgCard);
    s.addImage({ data: icons.globe, x: 0.8, y: 4.15, w: 0.3, h: 0.3 });
    s.addText("Nota internazionale:", {
      x: 1.25, y: 4.05, w: 2, h: 0.25,
      fontSize: 10, fontFace: FONT_H, color: C.accent2, bold: true, margin: 0
    });
    s.addText("WhatsApp è dominante in Italia. In Scandinavia il canale equivalente potrebbe essere diverso (SMS, app palestra). Da validare — l'architettura dei template è la stessa, cambia il canale.", {
      x: 1.25, y: 4.32, w: 7.8, h: 0.35,
      fontSize: 9.5, fontFace: FONT_B, color: C.gray, margin: 0
    });
  }

  // =============================================
  // SLIDE 16 — Le cose su cui ho bisogno della tua visione
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "Ho bisogno della tua visione", { fontSize: 24 });

    // 3 groups of questions
    const groups = [
      [C.accent, "Strategia e mercato", [
        "La sequenza di ingresso Italia — singoli, catene, o parallelo?",
        "Il concetto PT Evoluto — il nome funziona? Come lo posizioni?",
        "Il pricing — 3 motivi per cui un PT direbbe NO anche a €99.",
      ]],
      [C.accent2, "I 10 Fondatori", [
        "Hai già nomi in mente? Che profili dalla tua rete?",
        "I temi delle masterclass — mindset, prime 4 settimane, scalare. Cosa cambieresti?",
      ]],
      [C.accent3, "L'internazionale", [
        "Nordic Wellness — percorso realistico? Accordo catena, singoli, ente formazione?",
        "Quali altri mercati? UK, DACH, Spagna?",
        "Timeline — 6 mesi IT + pilota dal mese 7. Compatibile coi tuoi tempi?",
      ]],
    ];

    let yPos = 0.9;
    groups.forEach((g) => {
      s.addText(g[1], {
        x: 0.6, y: yPos, w: 8.8, h: 0.3,
        fontSize: 12, fontFace: FONT_H, color: g[0], bold: true, margin: 0
      });
      yPos += 0.32;
      g[2].forEach((q, qi) => {
        s.addShape(pres.shapes.RECTANGLE, {
          x: 0.6, y: yPos, w: 8.8, h: 0.32, fill: { color: C.bgCard }
        });
        s.addText(`${qi + 1}.`, {
          x: 0.7, y: yPos, w: 0.3, h: 0.32,
          fontSize: 10, fontFace: FONT_H, color: g[0], bold: true, valign: "middle", margin: 0
        });
        s.addText(q, {
          x: 1.0, y: yPos, w: 8.2, h: 0.32,
          fontSize: 10.5, fontFace: FONT_B, color: C.text, valign: "middle", margin: 0
        });
        yPos += 0.35;
      });
      yPos += 0.12;
    });

    // 9th question — direction
    addCard(s, pres, 0.6, yPos, 8.8, 0.55, "1A2A1F");
    s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: yPos, w: 0.06, h: 0.55, fill: { color: C.accent } });
    s.addText("9.  So che hai idee precise di direzione e marketing. Questo è la mia struttura — adesso serve la tua. Dove la vedi diversamente?", {
      x: 0.85, y: yPos, w: 8.3, h: 0.55,
      fontSize: 11, fontFace: FONT_B, color: C.accent, bold: true, valign: "middle", margin: 0
    });
  }

  // =============================================
  // SLIDE 17 — Prossimi passi
  // =============================================
  {
    const s = darkSlide(pres);
    addTitle(s, "Prossimi passi");

    const steps = [
      ["Lun 31 marzo",    "NDA formale",                          "Giacomo → Alessio"],
      ["Post-firma NDA",  "BP v4.3 + Strategy Plan v3.1 completi","Giacomo"],
      ["Sett. 1 aprile",  "Call operativa: visione, le 9 domande","Insieme"],
      ["Entro 15 aprile", "Lista Fondatori (nomi)",               "Alessio + Giacomo"],
      ["Aprile",          "Demo live per candidati Fondatori",     "Giacomo (Alessio presenta)"],
      ["Maggio 2026",     "Lancio POC Italia",                    "Insieme"],
      ["Lug-Ago 2026",    "Blocchi 1-2 pronti lingua target",     "Giacomo"],
      ["Settembre 2026",  "Primi contatti mercato internazionale", "Alessio"],
    ];
    steps.forEach((st, i) => {
      const cy = 0.95 + i * 0.53;
      addCard(s, pres, 0.6, cy, 8.8, 0.42, C.bgCard);
      // Date
      s.addText(st[0], {
        x: 0.75, y: cy + 0.03, w: 1.6, h: 0.36,
        fontSize: 9.5, fontFace: FONT_B, color: C.accent, bold: true, valign: "middle", margin: 0
      });
      // What
      s.addText(st[1], {
        x: 2.5, y: cy + 0.03, w: 4.3, h: 0.36,
        fontSize: 11, fontFace: FONT_H, color: C.white, bold: true, valign: "middle", margin: 0
      });
      // Who
      s.addText(st[2], {
        x: 7.0, y: cy + 0.03, w: 2.3, h: 0.36,
        fontSize: 9.5, fontFace: FONT_B, color: C.gray, valign: "middle", align: "right", margin: 0
      });
    });
  }

  // =============================================
  // SLIDE 18 — Chiusura
  // =============================================
  {
    const s = pres.addSlide();
    s.background = { color: C.bg };
    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.accent } });
    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.12, h: 5.625, fill: { color: C.accent } });

    const statements = [
      "Il prodotto è completo. La prima utente lo usa ogni giorno.",
      "La strategia è costruita. I numeri reggono in ogni scenario.",
      "L'architettura è pronta per uscire dall'Italia.",
    ];
    statements.forEach((st, i) => {
      const cy = 0.8 + i * 0.55;
      s.addText(st, {
        x: 0.8, y: cy, w: 8.5, h: 0.45,
        fontSize: 15, fontFace: FONT_B, color: C.text, margin: 0
      });
    });

    // The key line
    s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 2.65, w: 2.5, h: 0.035, fill: { color: C.accent } });
    s.addText("Quello che cambia tutto è la leva — e la leva sei tu.", {
      x: 0.8, y: 2.9, w: 8.5, h: 0.6,
      fontSize: 20, fontFace: FONT_H, color: C.accent, bold: true, margin: 0
    });

    s.addText("Io costruisco lo strumento. Tu costruisci il percorso.\nInsieme lo portiamo dove deve andare.", {
      x: 0.8, y: 3.65, w: 8, h: 0.7,
      fontSize: 14, fontFace: FONT_B, color: C.gray, margin: 0
    });

    s.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 4.55, w: 2.5, h: 0.035, fill: { color: C.accent } });
    s.addText("Giacomo Verardo — AVGV Technologies  |  Documento Operativo Partner v3.0 — Marzo 2026", {
      x: 0.8, y: 4.75, w: 8, h: 0.3,
      fontSize: 10, fontFace: FONT_B, color: C.grayDark, margin: 0
    });
  }

  // --- Write ---
  const outPath = path.join(__dirname, "..", "..", "docs", "FitManager_DocOperativo_Partner.pptx");
  await pres.writeFile({ fileName: outPath });
  console.log("DONE:", outPath);
}

main().catch(err => { console.error(err); process.exit(1); });

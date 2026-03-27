/**
 * FitManager Studio+ — Business Plan v4.2 Complete Presentation
 * Generates a comprehensive PPTX from BUSINESS_PLAN.md content
 */

const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const {
  FaUsers, FaClock, FaShieldAlt, FaAppleAlt, FaClipboardList, FaCashRegister,
  FaDumbbell, FaChartLine, FaLaptop, FaServer, FaMobileAlt, FaHandshake,
  FaLinkedin, FaBullhorn, FaUserFriends, FaVideo, FaComments, FaCheckCircle,
  FaExclamationTriangle, FaRocket, FaSearch, FaMoneyBillWave, FaFileContract,
  FaUserMd, FaCalendarAlt, FaBoxOpen, FaWifi, FaBolt, FaDatabase,
  FaLock, FaArrowRight, FaStar, FaGraduationCap, FaCertificate, FaTools,
  FaChartBar, FaChartPie, FaBalanceScale, FaFlag, FaTrophy, FaLightbulb,
  FaQuoteLeft, FaUserTie, FaIndustry, FaGlobe, FaHeartbeat, FaBrain
} = require("react-icons/fa");

// ─── Color Palette ───────────────────────────────────────────────
const C = {
  darkBg:    "0F1923",   // premium dark
  darkBg2:   "162536",   // slightly lighter dark
  teal:      "0D9488",   // primary teal
  tealDark:  "0A7A70",   // darker teal
  tealLight: "14B8A6",   // lighter teal
  mint:      "99F6E4",   // light mint
  coral:     "F96167",   // accent coral/energy
  gold:      "F59E0B",   // warm gold
  cream:     "F8F6F0",   // warm cream bg
  white:     "FFFFFF",
  offWhite:  "F1F5F9",   // cool light bg
  text:      "1E293B",   // near-black text
  textMid:   "475569",   // medium gray text
  textLight: "94A3B8",   // light gray text
  green:     "22C55E",   // success green
  red:       "EF4444",   // danger red
  navy:      "1E3A5F",   // navy accent
  orange:    "FB923C",   // orange
};

// ─── Icon Rendering ──────────────────────────────────────────────
function renderIconSvg(IconComponent, color = "#000000", size = 256) {
  return ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
}

async function iconToBase64Png(IconComponent, color, size = 256) {
  const svg = renderIconSvg(IconComponent, "#" + color, size);
  const pngBuffer = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + pngBuffer.toString("base64");
}

// ─── Helpers ─────────────────────────────────────────────────────
const makeShadow = () => ({ type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.12 });
const makeCardShadow = () => ({ type: "outer", blur: 8, offset: 3, angle: 135, color: "000000", opacity: 0.10 });

function addSlideNumber(slide, num, total) {
  slide.addText(`${num} / ${total}`, {
    x: 8.5, y: 5.2, w: 1.2, h: 0.3,
    fontSize: 9, color: C.textLight, align: "right", fontFace: "Calibri"
  });
}

function addSectionLabel(slide, label) {
  slide.addText(label.toUpperCase(), {
    x: 0.5, y: 0.25, w: 4, h: 0.3,
    fontSize: 8, color: C.teal, fontFace: "Calibri", bold: true,
    charSpacing: 3
  });
}

function addDarkTitle(slide, title, subtitle, sectionLabel) {
  slide.background = { color: C.darkBg };
  // Decorative teal bar left
  slide.addShape("rect", { x: 0, y: 0, w: 0.06, h: 5.625, fill: { color: C.teal } });
  if (sectionLabel) {
    slide.addText(sectionLabel.toUpperCase(), {
      x: 0.5, y: 0.4, w: 5, h: 0.3,
      fontSize: 9, color: C.tealLight, fontFace: "Calibri", bold: true, charSpacing: 4
    });
  }
  slide.addText(title, {
    x: 0.5, y: 1.5, w: 9, h: 1.2,
    fontSize: 40, color: C.white, fontFace: "Georgia", bold: true, margin: 0
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.5, y: 2.8, w: 8, h: 0.8,
      fontSize: 16, color: C.textLight, fontFace: "Calibri", margin: 0
    });
  }
}

function addLightTitle(slide, title, y) {
  const yPos = y || 0.35;
  slide.addText(title, {
    x: 0.5, y: yPos, w: 9, h: 0.55,
    fontSize: 28, color: C.text, fontFace: "Georgia", bold: true, margin: 0
  });
  // Teal underline
  slide.addShape("rect", { x: 0.5, y: yPos + 0.6, w: 1.2, h: 0.04, fill: { color: C.teal } });
}

// ─── MAIN ────────────────────────────────────────────────────────
async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Giacomo Verardo";
  pres.title = "FitManager Studio+ — Business Plan v4.2";

  const TOTAL_SLIDES = 54;
  let slideNum = 0;

  // Pre-render all icons
  const icons = {};
  const iconMap = {
    users: [FaUsers, C.teal], clock: [FaClock, C.coral], shield: [FaShieldAlt, C.teal],
    apple: [FaAppleAlt, C.green], clipboard: [FaClipboardList, C.teal], cash: [FaCashRegister, C.gold],
    dumbbell: [FaDumbbell, C.coral], chart: [FaChartLine, C.teal], laptop: [FaLaptop, C.teal],
    server: [FaServer, C.navy], mobile: [FaMobileAlt, C.teal], handshake: [FaHandshake, C.teal],
    linkedin: [FaLinkedin, C.navy], bullhorn: [FaBullhorn, C.coral], friends: [FaUserFriends, C.teal],
    video: [FaVideo, C.coral], comments: [FaComments, C.teal], check: [FaCheckCircle, C.green],
    warning: [FaExclamationTriangle, C.gold], rocket: [FaRocket, C.coral], search: [FaSearch, C.teal],
    money: [FaMoneyBillWave, C.green], contract: [FaFileContract, C.teal], doctor: [FaUserMd, C.teal],
    calendar: [FaCalendarAlt, C.teal], box: [FaBoxOpen, C.teal], wifi: [FaWifi, C.teal],
    bolt: [FaBolt, C.gold], database: [FaDatabase, C.teal], lock: [FaLock, C.navy],
    arrow: [FaArrowRight, C.teal], star: [FaStar, C.gold], grad: [FaGraduationCap, C.teal],
    cert: [FaCertificate, C.gold], tools: [FaTools, C.textMid], chartBar: [FaChartBar, C.teal],
    chartPie: [FaChartPie, C.coral], balance: [FaBalanceScale, C.teal], flag: [FaFlag, C.coral],
    trophy: [FaTrophy, C.gold], lightbulb: [FaLightbulb, C.gold], quote: [FaQuoteLeft, C.textLight],
    userTie: [FaUserTie, C.navy], industry: [FaIndustry, C.textMid], globe: [FaGlobe, C.teal],
    heartbeat: [FaHeartbeat, C.coral], brain: [FaBrain, C.teal],
    // White variants for dark slides
    usersW: [FaUsers, C.white], rocketW: [FaRocket, C.white], checkW: [FaCheckCircle, C.mint],
    starW: [FaStar, C.gold], chartW: [FaChartLine, C.mint], handshakeW: [FaHandshake, C.mint],
    tealCheck: [FaCheckCircle, C.teal], coralStar: [FaStar, C.coral],
  };
  for (const [key, [Icon, color]] of Object.entries(iconMap)) {
    icons[key] = await iconToBase64Png(Icon, color);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 1 — TITLE
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.darkBg };
    // Decorative teal gradient bar top
    s.addShape("rect", { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.teal } });
    // Decorative shapes
    s.addShape("rect", { x: 7.5, y: 0.5, w: 2.2, h: 2.2, fill: { color: C.teal, transparency: 8 } });
    s.addShape("rect", { x: 8, y: 1, w: 1.5, h: 1.5, fill: { color: C.tealLight, transparency: 12 } });

    s.addText("BUSINESS PLAN", {
      x: 0.7, y: 0.5, w: 7, h: 0.4,
      fontSize: 11, color: C.tealLight, fontFace: "Calibri", bold: true, charSpacing: 6
    });
    s.addText("FitManager Studio+", {
      x: 0.7, y: 1.4, w: 8, h: 1.2,
      fontSize: 44, color: C.white, fontFace: "Georgia", bold: true, margin: 0
    });
    s.addText("Il sistema completo per il Personal Trainer Evoluto", {
      x: 0.7, y: 2.7, w: 7, h: 0.6,
      fontSize: 18, color: C.tealLight, fontFace: "Calibri", italic: true
    });
    s.addShape("rect", { x: 0.7, y: 3.5, w: 2, h: 0.04, fill: { color: C.teal } });
    s.addText([
      { text: "Versione 4.2 — 26 marzo 2026", options: { breakLine: true, color: C.textLight } },
      { text: "Giacomo Verardo", options: { breakLine: true, color: C.white, bold: true } },
      { text: "Confidenziale", options: { color: C.coral } },
    ], {
      x: 0.7, y: 3.8, w: 5, h: 1.2,
      fontSize: 13, fontFace: "Calibri"
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 2 — GUIDA ALLA LETTURA
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Guida alla lettura");
    addLightTitle(s, "Come leggere questo documento");

    const items = [
      ["Fonte di verità", "Tutti i numeri, le assunzioni e le proiezioni sono qui. Ogni altro documento deriva da questo."],
      ["Numeri tracciabili", "Ogni numero è tracciabile a un'assunzione dichiarata (Appendice A4)."],
      ["Bottom-up", "Proiezioni costruite dalla capacità reale di generare vendite, non da TAM top-down."],
      ["Tre scenari", "Conservativo, base, ottimistico — la gamma completa di risultati possibili."],
      ["Due configurazioni", "Con e senza Industry Partner — il business sta in piedi in entrambi i casi."],
    ];

    for (let i = 0; i < items.length; i++) {
      const y = 1.3 + i * 0.8;
      s.addShape("rect", { x: 0.5, y, w: 9, h: 0.7, fill: { color: C.white }, shadow: makeCardShadow() });
      s.addShape("rect", { x: 0.5, y, w: 0.06, h: 0.7, fill: { color: C.teal } });
      s.addText(items[i][0], {
        x: 0.8, y, w: 2.2, h: 0.7,
        fontSize: 13, color: C.teal, fontFace: "Calibri", bold: true, valign: "middle", margin: 0
      });
      s.addText(items[i][1], {
        x: 3.0, y, w: 6.3, h: 0.7,
        fontSize: 12, color: C.text, fontFace: "Calibri", valign: "middle", margin: 0
      });
    }
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 3 — EXECUTIVE SUMMARY
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 1");
    addLightTitle(s, "Executive Summary");

    s.addText("FitManager Studio+ è un sistema completo — software e dispositivo dedicato — che permette al personal trainer di gestire clienti, schede di allenamento, pagamenti e anamnesi da qualunque dispositivo, con la scienza integrata e i dati che restano nel suo studio.", {
      x: 0.5, y: 1.15, w: 9, h: 0.8,
      fontSize: 13, color: C.text, fontFace: "Calibri", italic: true
    });

    // 4 key facts as cards
    const facts = [
      [icons.check, "Prodotto completo", "v1.0.4 in uso\nquotidiano"],
      [icons.users, "100K+ professionisti", "Mercato target\nin Italia"],
      [icons.rocket, "POC strutturata", "10 professionisti\n90 giorni"],
      [icons.money, "Zero debito", "Business sostenibile\nin ogni scenario"],
    ];
    for (let i = 0; i < 4; i++) {
      const x = 0.5 + i * 2.35;
      s.addShape("rect", { x, y: 2.2, w: 2.1, h: 1.9, fill: { color: C.white }, shadow: makeCardShadow() });
      s.addImage({ data: facts[i][0], x: x + 0.75, y: 2.35, w: 0.5, h: 0.5 });
      s.addText(facts[i][1], {
        x, y: 2.95, w: 2.1, h: 0.4,
        fontSize: 12, color: C.text, fontFace: "Calibri", bold: true, align: "center", margin: 0
      });
      s.addText(facts[i][2], {
        x, y: 3.35, w: 2.1, h: 0.6,
        fontSize: 11, color: C.textMid, fontFace: "Calibri", align: "center", margin: 0
      });
    }

    s.addText("Si compra una volta, non si paga ogni mese. Cerchiamo un Industry Partner per accelerare la crescita.", {
      x: 0.5, y: 4.4, w: 9, h: 0.5,
      fontSize: 12, color: C.tealDark, fontFace: "Calibri", bold: true
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 4 — IL PROBLEMA: LA STORIA DI MARCO
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    addDarkTitle(s, "Il problema", "Ogni personal trainer in Italia conosce questa storia", "Sezione 2");

    s.addImage({ data: icons.quote, x: 0.5, y: 3.7, w: 0.4, h: 0.4 });
    s.addText("Marco ha 32 clienti. Gestisce le anamnesi su fogli Word, le schede su PDF, i pagamenti su un foglio Excel. Ogni lunedì perde due ore a ricostruire chi ha pagato e chi no. Un mese fa ha dimenticato che un cliente aveva un'ernia lombare e gli ha assegnato stacchi da terra. Il cliente non è tornato.", {
      x: 1.1, y: 3.7, w: 8, h: 1.1,
      fontSize: 13, color: C.mint, fontFace: "Georgia", italic: true, margin: 0
    });
    s.addText("Marco non è un caso isolato. È la norma.", {
      x: 1.1, y: 4.85, w: 8, h: 0.3,
      fontSize: 14, color: C.coral, fontFace: "Calibri", bold: true, margin: 0
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 5 — I 6 PROBLEMI
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 2");
    addLightTitle(s, "I 6 problemi che ogni trainer riconosce");

    const problems = [
      [icons.clock, "Ore perse in admin", "3-5h/settimana in lavoro che non genera valore"],
      [icons.users, "Tetto ai clienti", "Oltre 25-30 clienti il sistema artigianale crolla"],
      [icons.search, "Nessuna visione unificata", "Anamnesi, schede, pagamenti sparsi ovunque"],
      [icons.money, "Contabilità dispersa", "Rate dimenticate, nessun report finanziario"],
      [icons.warning, "Rischio errori clinici", "Condizioni patologiche dimenticate o ignorate"],
      [icons.chartBar, "Impossibilità di differenziarsi", "Senza dati, tutti offrono lo stesso servizio"],
    ];

    for (let i = 0; i < 6; i++) {
      const col = i % 2;
      const row = Math.floor(i / 2);
      const x = 0.5 + col * 4.7;
      const y = 1.15 + row * 1.3;
      s.addShape("rect", { x, y, w: 4.4, h: 1.15, fill: { color: C.white }, shadow: makeCardShadow() });
      s.addImage({ data: problems[i][0], x: x + 0.2, y: y + 0.25, w: 0.45, h: 0.45 });
      s.addText(problems[i][1], {
        x: x + 0.8, y: y + 0.1, w: 3.3, h: 0.35,
        fontSize: 13, color: C.text, fontFace: "Calibri", bold: true, margin: 0
      });
      s.addText(problems[i][2], {
        x: x + 0.8, y: y + 0.55, w: 3.3, h: 0.5,
        fontSize: 11, color: C.textMid, fontFace: "Calibri", margin: 0
      });
    }
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 6 — IL COMPETITOR VERO
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.darkBg };
    s.addShape("rect", { x: 0, y: 0, w: 0.06, h: 5.625, fill: { color: C.coral } });

    s.addText("IL COMPETITOR VERO", {
      x: 0.5, y: 0.5, w: 9, h: 0.4,
      fontSize: 10, color: C.coral, fontFace: "Calibri", bold: true, charSpacing: 4
    });
    s.addText("Non è un altro software.", {
      x: 0.5, y: 1.3, w: 9, h: 0.7,
      fontSize: 36, color: C.white, fontFace: "Georgia", bold: true, margin: 0
    });
    s.addText("È l'abitudine.", {
      x: 0.5, y: 2.0, w: 9, h: 0.7,
      fontSize: 36, color: C.coral, fontFace: "Georgia", bold: true, margin: 0
    });
    s.addText("Il trainer usa WhatsApp ed Excel perché \"ha sempre fatto così\" — non perché funzioni, ma perché nessuno gli ha offerto qualcosa di meglio che rispetti il suo modo di lavorare.", {
      x: 0.5, y: 3.2, w: 8, h: 1.2,
      fontSize: 16, color: C.textLight, fontFace: "Calibri", margin: 0
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 7 — LA SOLUZIONE: OVERVIEW
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    addDarkTitle(s, "La soluzione", "Un sistema completo: software + dispositivo dedicato", "Sezione 3");

    s.addText("Un unico strumento che permette al personal trainer di gestire clienti, schede di allenamento, pagamenti e anamnesi da qualunque dispositivo, con la scienza integrata e i dati che restano nel suo studio.", {
      x: 0.5, y: 3.7, w: 8.5, h: 0.7,
      fontSize: 13, color: C.mint, fontFace: "Calibri", margin: 0
    });
    s.addText("Si compra una volta, non si paga ogni mese.", {
      x: 0.5, y: 4.5, w: 8, h: 0.5,
      fontSize: 18, color: C.white, fontFace: "Georgia", bold: true, margin: 0
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 8 — IL SOFTWARE
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 3 — Il Software");
    addLightTitle(s, "Il software");

    const features = [
      [icons.users, "Gestione clienti e contratti", "Anagrafica, contratti, scadenze, storico. Ogni lunedì sai chi ha pagato, chi deve rinnovare."],
      [icons.dumbbell, "Schede di allenamento", "500 esercizi con progressioni, regressioni e varianti. Scheda professionale in 5 minuti."],
      [icons.shield, "Protezione errori clinici", "Safety Engine: 47 condizioni cliniche, 80 regole automatiche. Avvisa se un esercizio è controindicato."],
      [icons.apple, "Nutrizione italiana", "880 alimenti CREA. Piani alimentari LARN settimanali. Database ufficiale italiano."],
      [icons.clipboard, "Anamnesi strutturata", "6 passaggi guidati. Il cliente compila dal proprio telefono via portale web sicuro."],
      [icons.cash, "Pagamenti e cassa", "Rate, pagamenti, stato finanziario di ogni cliente e del business in tempo reale."],
    ];

    for (let i = 0; i < 6; i++) {
      const col = i % 2;
      const row = Math.floor(i / 2);
      const x = 0.5 + col * 4.7;
      const y = 1.15 + row * 1.3;
      s.addImage({ data: features[i][0], x: x + 0.1, y: y + 0.2, w: 0.4, h: 0.4 });
      s.addText(features[i][1], {
        x: x + 0.65, y: y + 0.05, w: 3.6, h: 0.3,
        fontSize: 13, color: C.text, fontFace: "Calibri", bold: true, margin: 0
      });
      s.addText(features[i][2], {
        x: x + 0.65, y: y + 0.35, w: 3.6, h: 0.75,
        fontSize: 11, color: C.textMid, fontFace: "Calibri", margin: 0
      });
    }
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 9 — LA FITMANAGER BOX
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 3 — FitManager Box");
    addLightTitle(s, "La FitManager Box");

    // Left: description
    s.addText("Un piccolo dispositivo dedicato che il trainer mette nel suo studio. Lo attacca alla corrente e al WiFi — fine.", {
      x: 0.5, y: 1.2, w: 5, h: 0.6,
      fontSize: 13, color: C.text, fontFace: "Calibri"
    });
    s.addText("Da quel momento accede a FitManager da qualunque dispositivo: il computer a casa, il telefono in palestra, il tablet durante le sessioni.", {
      x: 0.5, y: 1.85, w: 5, h: 0.6,
      fontSize: 13, color: C.text, fontFace: "Calibri"
    });

    const boxFeatures = [
      [icons.lock, "I dati non vanno mai in cloud"],
      [icons.bolt, "Sempre acceso, non dipende dal PC"],
      [icons.mobile, "Accesso da qualunque dispositivo"],
      [icons.wifi, "WiFi + Ethernet + Tailscale"],
    ];
    for (let i = 0; i < 4; i++) {
      const y = 2.7 + i * 0.55;
      s.addImage({ data: boxFeatures[i][0], x: 0.7, y: y + 0.05, w: 0.3, h: 0.3 });
      s.addText(boxFeatures[i][1], {
        x: 1.15, y, w: 4, h: 0.45,
        fontSize: 12, color: C.text, fontFace: "Calibri", valign: "middle", margin: 0
      });
    }

    // Right: specs card
    s.addShape("rect", { x: 5.8, y: 1.2, w: 3.8, h: 3.5, fill: { color: C.white }, shadow: makeCardShadow() });
    s.addShape("rect", { x: 5.8, y: 1.2, w: 3.8, h: 0.5, fill: { color: C.teal } });
    s.addText("SPECIFICHE", {
      x: 5.8, y: 1.2, w: 3.8, h: 0.5,
      fontSize: 11, color: C.white, fontFace: "Calibri", bold: true, align: "center", valign: "middle"
    });
    const specs = [
      ["Hardware", "Raspberry Pi 5, 4GB RAM"],
      ["Storage", "SD 64GB"],
      ["Connessione", "WiFi + Ethernet + Tailscale"],
      ["Consumo", "~5W (~€10/anno)"],
      ["Backup", "Automatico su USB (notturno)"],
      ["Costo unitario", "~€130-150"],
      ["Prezzo vendita", "€449"],
      ["Margine lordo", "€299-319 (67-71%)"],
    ];
    for (let i = 0; i < specs.length; i++) {
      const y = 1.85 + i * 0.35;
      s.addText(specs[i][0], {
        x: 6.0, y, w: 1.6, h: 0.3,
        fontSize: 10, color: C.textMid, fontFace: "Calibri", bold: true, margin: 0
      });
      s.addText(specs[i][1], {
        x: 7.6, y, w: 1.8, h: 0.3,
        fontSize: 10, color: C.text, fontFace: "Calibri", margin: 0
      });
    }
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 10 — STATO DEL PRODOTTO
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 3");
    addLightTitle(s, "Stato del prodotto");

    s.addText("Il prodotto è completo e funzionante (versione 1.0.4).", {
      x: 0.5, y: 1.15, w: 9, h: 0.4,
      fontSize: 16, color: C.teal, fontFace: "Calibri", bold: true
    });
    s.addText("La prima utilizzatrice reale — una chinesiologia di Genova — lo usa quotidianamente per gestire i propri clienti. Le sue clienti ricevono schede professionali e compilano le anamnesi dal proprio telefono.", {
      x: 0.5, y: 1.65, w: 9, h: 0.7,
      fontSize: 13, color: C.text, fontFace: "Calibri"
    });

    // Stats
    const stats = [
      ["45.000", "righe di codice"],
      ["395", "test automatici"],
      ["500", "esercizi"],
      ["880", "alimenti CREA"],
      ["5", "motori scientifici"],
    ];
    for (let i = 0; i < 5; i++) {
      const x = 0.5 + i * 1.85;
      s.addShape("rect", { x, y: 2.7, w: 1.65, h: 1.4, fill: { color: C.white }, shadow: makeCardShadow() });
      s.addText(stats[i][0], {
        x, y: 2.85, w: 1.65, h: 0.6,
        fontSize: 28, color: C.teal, fontFace: "Georgia", bold: true, align: "center", margin: 0
      });
      s.addText(stats[i][1], {
        x, y: 3.5, w: 1.65, h: 0.4,
        fontSize: 11, color: C.textMid, fontFace: "Calibri", align: "center", margin: 0
      });
    }
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 11 — CONFRONTO COMPETITOR
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 4");
    addLightTitle(s, "Confronto con le alternative");

    const headers = [
      { text: "", options: { fill: { color: C.teal } } },
      { text: "FitManager", options: { fill: { color: C.teal }, color: C.white, bold: true, align: "center", fontSize: 11 } },
      { text: "Mangofit", options: { fill: { color: C.teal }, color: C.white, bold: true, align: "center", fontSize: 11 } },
      { text: "EvolutionFit", options: { fill: { color: C.teal }, color: C.white, bold: true, align: "center", fontSize: 11 } },
      { text: "Excel+WhatsApp", options: { fill: { color: C.teal }, color: C.white, bold: true, align: "center", fontSize: 11 } },
    ];
    const rows = [
      ["Dati nel tuo studio", "Sì", "No (cloud)", "No (cloud)", "Sì"],
      ["Accesso mobile/tablet", "Sì", "Sì", "Sì", "Parziale"],
      ["Segnala errori patologie", "Sì (47 cond.)", "No", "No", "No"],
      ["Nutrizione italiana", "Sì (880 alim.)", "No", "No", "No"],
      ["Scienza allenamento", "Sì", "No", "Base", "No"],
      ["Pagamento una tantum", "Sì", "No (abb.)", "No (abb.)", "Sì (€0)"],
    ];
    const tableData = [headers];
    for (const row of rows) {
      tableData.push(row.map((cell, idx) => ({
        text: cell,
        options: {
          fontSize: 10, fontFace: "Calibri",
          color: idx === 0 ? C.text : (cell.startsWith("Sì") ? "0D9488" : (cell === "No" || cell.startsWith("No") ? C.coral : C.textMid)),
          bold: idx === 0 || cell.startsWith("Sì"),
          align: idx === 0 ? "left" : "center",
          fill: { color: tableData.length % 2 === 0 ? C.white : C.offWhite },
        }
      })));
    }
    s.addTable(tableData, {
      x: 0.5, y: 1.15, w: 9,
      colW: [2.2, 1.7, 1.7, 1.7, 1.7],
      border: { pt: 0.5, color: "E2E8F0" },
      rowH: [0.4, 0.35, 0.35, 0.35, 0.35, 0.35, 0.35],
    });

    s.addText("Nessun prodotto sul mercato combina accesso locale, scienza integrata e assenza di abbonamento.", {
      x: 0.5, y: 4.0, w: 9, h: 0.4,
      fontSize: 12, color: C.tealDark, fontFace: "Calibri", bold: true, italic: true
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 12 — COSTO IN 3 ANNI
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 4");
    addLightTitle(s, "Quanto costa in 3 anni");

    const headers = [
      { text: "Software", options: { fill: { color: C.navy }, color: C.white, bold: true, fontSize: 11 } },
      { text: "Anno 1", options: { fill: { color: C.navy }, color: C.white, bold: true, align: "center", fontSize: 11 } },
      { text: "Anno 2", options: { fill: { color: C.navy }, color: C.white, bold: true, align: "center", fontSize: 11 } },
      { text: "Anno 3", options: { fill: { color: C.navy }, color: C.white, bold: true, align: "center", fontSize: 11 } },
      { text: "Totale 3 anni", options: { fill: { color: C.navy }, color: C.white, bold: true, align: "center", fontSize: 11 } },
    ];
    const costRows = [
      ["FitManager (licenza)", "€249", "€79", "€79", "€407"],
      ["FitManager Box", "€449", "€79", "€79", "€607"],
      ["Mangofit Pro", "€480", "€480", "€480", "€1.440"],
      ["EvolutionFit", "€720", "€720", "€720", "€2.160"],
    ];
    const tableData = [headers];
    for (let r = 0; r < costRows.length; r++) {
      const isFM = r < 2;
      tableData.push(costRows[r].map((cell, idx) => ({
        text: cell,
        options: {
          fontSize: 11, fontFace: "Calibri",
          color: isFM ? C.tealDark : C.textMid,
          bold: idx === 0 || idx === 4,
          align: idx === 0 ? "left" : "center",
          fill: { color: isFM ? "E6FAF5" : C.offWhite },
        }
      })));
    }
    s.addTable(tableData, {
      x: 0.5, y: 1.15, w: 9,
      colW: [2.5, 1.5, 1.5, 1.5, 2],
      border: { pt: 0.5, color: "E2E8F0" },
      rowH: [0.42, 0.42, 0.42, 0.42, 0.42],
    });

    // Bar chart comparison
    s.addChart(pres.charts.BAR, [{
      name: "Totale 3 anni",
      labels: ["FitManager\n(licenza)", "FitManager\nBox", "Mangofit\nPro", "EvolutionFit"],
      values: [407, 607, 1440, 2160],
    }], {
      x: 1, y: 3.4, w: 8, h: 1.6,
      barDir: "col",
      chartColors: [C.teal],
      showValue: true,
      dataLabelPosition: "outEnd",
      dataLabelColor: C.text,
      dataLabelFontSize: 10,
      catAxisLabelColor: C.textMid,
      catAxisLabelFontSize: 9,
      valAxisHidden: true,
      valGridLine: { style: "none" },
      catGridLine: { style: "none" },
      showLegend: false,
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 13 — IL MERCATO: DIMENSIONE
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    addDarkTitle(s, "Il mercato", null, "Sezione 5");

    // Big number
    s.addText("100.000+", {
      x: 0.5, y: 2.8, w: 5, h: 1,
      fontSize: 60, color: C.tealLight, fontFace: "Georgia", bold: true, margin: 0
    });
    s.addText("professionisti fitness P.IVA in Italia", {
      x: 0.5, y: 3.8, w: 5, h: 0.5,
      fontSize: 18, color: C.white, fontFace: "Calibri", margin: 0
    });

    // Right: market details
    s.addText("€3 miliardi", {
      x: 6, y: 2.9, w: 3.5, h: 0.5,
      fontSize: 28, color: C.gold, fontFace: "Georgia", bold: true, margin: 0
    });
    s.addText("mercato fitness Italia", {
      x: 6, y: 3.4, w: 3.5, h: 0.3,
      fontSize: 13, color: C.textLight, fontFace: "Calibri", margin: 0
    });
    s.addText("+10%", {
      x: 6, y: 4.0, w: 1.5, h: 0.5,
      fontSize: 28, color: C.green, fontFace: "Georgia", bold: true, margin: 0
    });
    s.addText("crescita anno su anno", {
      x: 7.3, y: 4.05, w: 2.5, h: 0.4,
      fontSize: 13, color: C.textLight, fontFace: "Calibri", margin: 0, valign: "middle"
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 14 — SEGMENTO TARGET + TREND
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 5");
    addLightTitle(s, "Segmento target e trend");

    // Target segment
    s.addShape("rect", { x: 0.5, y: 1.15, w: 4.3, h: 2.6, fill: { color: C.white }, shadow: makeCardShadow() });
    s.addText("SEGMENTO TARGET", {
      x: 0.7, y: 1.3, w: 3.8, h: 0.3,
      fontSize: 10, color: C.teal, fontFace: "Calibri", bold: true, charSpacing: 2
    });
    s.addText("10.000 – 15.000", {
      x: 0.7, y: 1.7, w: 3.8, h: 0.5,
      fontSize: 28, color: C.teal, fontFace: "Georgia", bold: true, margin: 0
    });
    s.addText("professionisti", {
      x: 0.7, y: 2.2, w: 3.8, h: 0.3,
      fontSize: 14, color: C.text, fontFace: "Calibri", margin: 0
    });
    s.addText([
      { text: "15-20 clienti attivi (soglia problema)", options: { bullet: true, breakLine: true } },
      { text: "Aree urbane/peri-urbane", options: { bullet: true, breakLine: true } },
      { text: "Aperti a strumenti professionali", options: { bullet: true } },
    ], {
      x: 0.7, y: 2.7, w: 3.8, h: 0.9,
      fontSize: 11, color: C.textMid, fontFace: "Calibri"
    });

    // Trend
    s.addShape("rect", { x: 5.2, y: 1.15, w: 4.3, h: 2.6, fill: { color: C.white }, shadow: makeCardShadow() });
    s.addText("TREND CHE FAVORISCONO L'ADOZIONE", {
      x: 5.4, y: 1.3, w: 3.8, h: 0.3,
      fontSize: 10, color: C.teal, fontFace: "Calibri", bold: true, charSpacing: 2
    });
    const trends = [
      ["Professionalizzazione", "Registro CONI attivo dal 1 luglio 2023, ATECO 85.51.09"],
      ["Privacy", "GDPR rende il cloud problematico per dati sensibili"],
      ["Personalizzazione", "Clienti più esigenti, vogliono progressioni misurabili"],
    ];
    for (let i = 0; i < 3; i++) {
      const y = 1.7 + i * 0.65;
      s.addText(trends[i][0], {
        x: 5.4, y, w: 3.8, h: 0.25,
        fontSize: 12, color: C.text, fontFace: "Calibri", bold: true, margin: 0
      });
      s.addText(trends[i][1], {
        x: 5.4, y: y + 0.25, w: 3.8, h: 0.35,
        fontSize: 10, color: C.textMid, fontFace: "Calibri", margin: 0
      });
    }

    // Why market is empty
    s.addShape("rect", { x: 0.5, y: 3.95, w: 9, h: 1.1, fill: { color: C.tealDark } });
    s.addText("PERCHÉ IL MERCATO È VUOTO", {
      x: 0.7, y: 4.0, w: 8.5, h: 0.3,
      fontSize: 10, color: C.mint, fontFace: "Calibri", bold: true, charSpacing: 2
    });
    s.addText("Nessun prodotto combina architettura locale, scienza dell'allenamento integrata, nutrizione italiana e modello perpetuo. Questo posizionamento richiede competenze di dominio profonde combinate con competenze tecniche specifiche. FitManager è l'unico prodotto costruito all'intersezione.", {
      x: 0.7, y: 4.3, w: 8.5, h: 0.65,
      fontSize: 11, color: C.white, fontFace: "Calibri"
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 15 — PRICING
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 6 — Il modello economico");
    addLightTitle(s, "Pricing");

    // 3 pricing cards
    const plans = [
      { name: "Licenza Software", price: "€249", color: C.teal, items: ["Software completo sul PC", "Accesso da telefono/tablet (Tailscale)", "Installazione assistita"] },
      { name: "FitManager Box", price: "€449", color: C.navy, items: ["Dispositivo dedicato + software", "Accesso ovunque, dati locali", "Plug & play"] },
      { name: "Assistenza Annuale", price: "€79/anno", color: C.tealDark, items: ["Aggiornamenti software", "Nuovi esercizi e alimenti", "Supporto — inclusa 12 mesi per i primi 30"] },
    ];
    for (let i = 0; i < 3; i++) {
      const x = 0.5 + i * 3.15;
      s.addShape("rect", { x, y: 1.15, w: 2.9, h: 3.5, fill: { color: C.white }, shadow: makeCardShadow() });
      s.addShape("rect", { x, y: 1.15, w: 2.9, h: 0.7, fill: { color: plans[i].color } });
      s.addText(plans[i].name, {
        x, y: 1.2, w: 2.9, h: 0.6,
        fontSize: 13, color: C.white, fontFace: "Calibri", bold: true, align: "center", valign: "middle"
      });
      s.addText(plans[i].price, {
        x, y: 2.0, w: 2.9, h: 0.7,
        fontSize: 30, color: plans[i].color, fontFace: "Georgia", bold: true, align: "center", margin: 0
      });
      s.addText(plans[i].items.map((item, idx) => ({
        text: item,
        options: { bullet: true, breakLine: idx < plans[i].items.length - 1 }
      })), {
        x: x + 0.2, y: 2.8, w: 2.5, h: 1.5,
        fontSize: 10, color: C.textMid, fontFace: "Calibri"
      });
    }

    s.addText("Licenza perpetua: il trainer compra una volta e il software è suo per sempre. Nessun abbonamento obbligatorio.", {
      x: 0.5, y: 4.85, w: 9, h: 0.4,
      fontSize: 12, color: C.tealDark, fontFace: "Calibri", bold: true
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 16 — MARGINI UNITARI
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 6");
    addLightTitle(s, "Margini unitari");

    const headers = [
      { text: "Prodotto", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 11 } },
      { text: "Prezzo", options: { fill: { color: C.teal }, color: C.white, bold: true, align: "center", fontSize: 11 } },
      { text: "Costo vivo", options: { fill: { color: C.teal }, color: C.white, bold: true, align: "center", fontSize: 11 } },
      { text: "Margine lordo", options: { fill: { color: C.teal }, color: C.white, bold: true, align: "center", fontSize: 11 } },
    ];
    const rows = [
      ["Licenza software", "€249", "~€30", "€219 (88%)"],
      ["FitManager Box", "€449", "~€150", "€299 (67%)"],
      ["Assistenza annuale", "€79", "~€0", "€79 (100%)"],
    ];
    const tableData = [headers];
    for (const row of rows) {
      tableData.push(row.map((cell, idx) => ({
        text: cell,
        options: {
          fontSize: 12, fontFace: "Calibri",
          color: idx === 3 ? C.tealDark : C.text,
          bold: idx === 0 || idx === 3,
          align: idx === 0 ? "left" : "center",
          fill: { color: C.white },
        }
      })));
    }
    s.addTable(tableData, {
      x: 0.5, y: 1.3, w: 9,
      colW: [2.5, 2, 2, 2.5],
      border: { pt: 0.5, color: "E2E8F0" },
      rowH: [0.45, 0.45, 0.45, 0.45],
    });

    s.addText("Nessun costo server. I dati sono locali. Ogni vendita aggiuntiva è quasi interamente margine.", {
      x: 0.5, y: 3.3, w: 9, h: 0.4,
      fontSize: 13, color: C.tealDark, fontFace: "Calibri", bold: true
    });

    // Pie chart margins
    s.addChart(pres.charts.DOUGHNUT, [{
      name: "Margine",
      labels: ["Margine Licenza", "Margine Box", "Margine Assist."],
      values: [88, 67, 100],
    }], {
      x: 2.5, y: 3.8, w: 5, h: 1.2,
      chartColors: [C.teal, C.navy, C.tealLight],
      showPercent: true,
      showLegend: true, legendPos: "b", legendFontSize: 10,
      dataLabelColor: C.white,
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 17 — BREAK-EVEN
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.darkBg };
    s.addShape("rect", { x: 0, y: 0, w: 0.06, h: 5.625, fill: { color: C.gold } });

    s.addText("BREAK-EVEN", {
      x: 0.5, y: 0.5, w: 9, h: 0.3,
      fontSize: 10, color: C.gold, fontFace: "Calibri", bold: true, charSpacing: 4
    });

    // Big number
    s.addText("3", {
      x: 1, y: 1.2, w: 3, h: 2,
      fontSize: 120, color: C.tealLight, fontFace: "Georgia", bold: true, align: "center", margin: 0
    });
    s.addText("vendite al mese", {
      x: 1, y: 3.0, w: 3, h: 0.5,
      fontSize: 20, color: C.white, fontFace: "Calibri", align: "center"
    });

    // Details right
    const beItems = [
      ["Costi fissi mensili", "~€360"],
      ["Margine medio per vendita", "~€220"],
      ["Vendite break-even operativo", "1,7/mese"],
      ["Vendite break-even reale", "3/mese"],
    ];
    for (let i = 0; i < beItems.length; i++) {
      const y = 1.4 + i * 0.7;
      s.addText(beItems[i][0], {
        x: 5, y, w: 3.5, h: 0.3,
        fontSize: 12, color: C.textLight, fontFace: "Calibri", margin: 0
      });
      s.addText(beItems[i][1], {
        x: 5, y: y + 0.3, w: 3.5, h: 0.3,
        fontSize: 18, color: C.white, fontFace: "Georgia", bold: true, margin: 0
      });
    }

    s.addText("Se lo raggiungiamo stabilmente dal mese 5-6, il business è sostenibile.", {
      x: 0.5, y: 4.6, w: 9, h: 0.4,
      fontSize: 13, color: C.mint, fontFace: "Calibri", italic: true
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 18 — FONTI DI LEAD
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 7 — Come arriviamo ai clienti");
    addLightTitle(s, "Le fonti di lead");

    const sources = [
      [icons.handshake, "Network del partner", "Contatti diretti, presentazioni, eventi", "8-12"],
      [icons.linkedin, "LinkedIn del founder", "Contenuti settimanali, post educativi", "5-8"],
      [icons.friends, "Referral dai clienti", "Passaparola + programma referral", "2-4"],
      [icons.video, "Webinar mensile", "Formazione gratuita + demo integrata", "3-5"],
      [icons.comments, "Passaparola e community", "Crescita organica", "2-4"],
    ];
    for (let i = 0; i < sources.length; i++) {
      const y = 1.15 + i * 0.72;
      s.addShape("rect", { x: 0.5, y, w: 9, h: 0.62, fill: { color: i % 2 === 0 ? C.white : C.offWhite }, shadow: i % 2 === 0 ? makeCardShadow() : undefined });
      s.addImage({ data: sources[i][0], x: 0.65, y: y + 0.1, w: 0.35, h: 0.35 });
      s.addText(sources[i][1], {
        x: 1.2, y, w: 2.5, h: 0.62,
        fontSize: 12, color: C.text, fontFace: "Calibri", bold: true, valign: "middle", margin: 0
      });
      s.addText(sources[i][2], {
        x: 3.7, y, w: 3.5, h: 0.62,
        fontSize: 11, color: C.textMid, fontFace: "Calibri", valign: "middle", margin: 0
      });
      s.addText(sources[i][3], {
        x: 7.5, y, w: 1.8, h: 0.62,
        fontSize: 14, color: C.teal, fontFace: "Georgia", bold: true, valign: "middle", align: "center", margin: 0
      });
    }
    // Header for last column
    s.addText("Lead/mese", {
      x: 7.5, y: 0.85, w: 1.8, h: 0.3,
      fontSize: 9, color: C.textLight, fontFace: "Calibri", align: "center"
    });

    // Total
    s.addShape("rect", { x: 5.5, y: 4.85, w: 4, h: 0.5, fill: { color: C.teal } });
    s.addText("Totale a regime (mesi 7-12): 20-33 lead/mese", {
      x: 5.5, y: 4.85, w: 4, h: 0.5,
      fontSize: 12, color: C.white, fontFace: "Calibri", bold: true, align: "center", valign: "middle"
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 19 — IL FUNNEL
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 7");
    addLightTitle(s, "Il funnel");

    // Funnel visualization
    const funnelSteps = [
      { label: "Potenziale", rate: "100%", w: 7, color: C.tealLight },
      { label: "Demo", rate: "50-60%", w: 5, color: C.teal },
      { label: "Cliente", rate: "10-15%", w: 2.5, color: C.tealDark },
    ];
    for (let i = 0; i < funnelSteps.length; i++) {
      const step = funnelSteps[i];
      const x = (10 - step.w) / 2;
      const y = 1.3 + i * 1.2;
      s.addShape("rect", {
        x, y, w: step.w, h: 0.8,
        fill: { color: step.color },
        shadow: makeCardShadow()
      });
      s.addText(step.label, {
        x, y, w: step.w, h: 0.4,
        fontSize: 16, color: C.white, fontFace: "Calibri", bold: true, align: "center", valign: "middle"
      });
      s.addText(step.rate, {
        x, y: y + 0.35, w: step.w, h: 0.4,
        fontSize: 14, color: C.white, fontFace: "Georgia", align: "center", valign: "middle"
      });
    }

    // Conversion logic
    s.addShape("rect", { x: 0.5, y: 4.3, w: 9, h: 1.0, fill: { color: C.white }, shadow: makeCardShadow() });
    s.addText([
      { text: "Da potenziale a demo: 50-60%", options: { breakLine: true, bold: true } },
      { text: " — Lead già qualificati (network, referral)", options: { breakLine: true } },
      { text: "Da demo ad acquisto: 20-25%", options: { breakLine: true, bold: true } },
      { text: " — Benchmark B2B early stage con prodotto funzionante", options: {} },
    ], {
      x: 0.7, y: 4.35, w: 8.5, h: 0.9,
      fontSize: 11, color: C.text, fontFace: "Calibri"
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 20 — STRATEGIA MARKETING: CANALI
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 8 — Strategia Marketing");
    addLightTitle(s, "I tre canali");

    s.addText("FitManager opera in un mercato da educare. I trainer non cercano un gestionale — non sanno di averne bisogno.", {
      x: 0.5, y: 1.1, w: 9, h: 0.4,
      fontSize: 12, color: C.textMid, fontFace: "Calibri", italic: true
    });

    const channels = [
      { title: "Canali propri (owned)", desc: "Sito web, blog SEO, email automatizzate, community clienti. Costano tempo, non denaro. Risultati crescenti.", color: C.teal },
      { title: "Canali del partner (borrowed)", desc: "Network personale, masterclass, podcast settore, enti formazione. Impatto immediato, dipendono dalla relazione.", color: C.navy },
      { title: "Canali a pagamento (paid)", desc: "Solo dalla Fase 3 (mesi 7-12), budget €500-1.200/anno. Non il motore — un acceleratore.", color: C.coral },
    ];
    for (let i = 0; i < 3; i++) {
      const x = 0.5 + i * 3.15;
      s.addShape("rect", { x, y: 1.7, w: 2.9, h: 2.8, fill: { color: C.white }, shadow: makeCardShadow() });
      s.addShape("rect", { x, y: 1.7, w: 2.9, h: 0.06, fill: { color: channels[i].color } });
      s.addText(channels[i].title, {
        x: x + 0.15, y: 1.9, w: 2.6, h: 0.5,
        fontSize: 13, color: channels[i].color, fontFace: "Calibri", bold: true, margin: 0
      });
      s.addText(channels[i].desc, {
        x: x + 0.15, y: 2.5, w: 2.6, h: 1.5,
        fontSize: 11, color: C.textMid, fontFace: "Calibri", margin: 0
      });
    }
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 21 — BUDGET MARKETING + ASSET
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 8");
    addLightTitle(s, "Budget marketing Anno 1 e asset pre-lancio");

    // Budget table left
    s.addText("BUDGET", {
      x: 0.5, y: 1.15, w: 2, h: 0.3,
      fontSize: 10, color: C.teal, fontFace: "Calibri", bold: true, charSpacing: 2
    });
    const budgetRows = [
      ["Dominio + hosting", "€120/anno"],
      ["Email marketing", "€0-180/anno"],
      ["Video demo/testimonial", "€0-200"],
      ["Pubblicità (mesi 7-12)", "€300-500"],
      ["Totale Anno 1", "€120-880"],
    ];
    for (let i = 0; i < budgetRows.length; i++) {
      const y = 1.5 + i * 0.4;
      const isTotal = i === 4;
      s.addText(budgetRows[i][0], {
        x: 0.5, y, w: 2.5, h: 0.35,
        fontSize: 11, color: isTotal ? C.teal : C.text, fontFace: "Calibri", bold: isTotal, margin: 0
      });
      s.addText(budgetRows[i][1], {
        x: 3, y, w: 1.5, h: 0.35,
        fontSize: 11, color: isTotal ? C.teal : C.text, fontFace: "Calibri", bold: isTotal, align: "right", margin: 0
      });
    }

    // Asset table right
    s.addText("ASSET PRE-LANCIO", {
      x: 5.3, y: 1.15, w: 4.5, h: 0.3,
      fontSize: 10, color: C.teal, fontFace: "Calibri", bold: true, charSpacing: 2
    });
    const assets = [
      ["Sito web / landing page", "Da creare", "Critico"],
      ["Waiting list virale", "Da creare", "Critico"],
      ["Video demo (3 min)", "Da creare", "Alto"],
      ["Video teaser (60 sec)", "Da creare", "Alto"],
      ["Screenshot professionali", "Da creare", "Medio"],
      ["Profilo LinkedIn attivo", "Parziale", "Alto"],
    ];
    for (let i = 0; i < assets.length; i++) {
      const y = 1.5 + i * 0.4;
      s.addText(assets[i][0], {
        x: 5.3, y, w: 2.2, h: 0.35,
        fontSize: 10, color: C.text, fontFace: "Calibri", margin: 0
      });
      s.addText(assets[i][1], {
        x: 7.5, y, w: 1.1, h: 0.35,
        fontSize: 10, color: assets[i][1] === "Parziale" ? C.gold : C.coral, fontFace: "Calibri", align: "center", margin: 0
      });
      s.addText(assets[i][2], {
        x: 8.6, y, w: 0.9, h: 0.35,
        fontSize: 10, color: assets[i][2] === "Critico" ? C.coral : C.textMid, fontFace: "Calibri", bold: assets[i][2] === "Critico", align: "center", margin: 0
      });
    }

    // Marketing virale
    s.addShape("rect", { x: 0.5, y: 4.0, w: 9, h: 1.3, fill: { color: C.white }, shadow: makeCardShadow() });
    s.addShape("rect", { x: 0.5, y: 4.0, w: 0.06, h: 1.3, fill: { color: C.teal } });
    s.addText("MARKETING VIRALE NEL PRODOTTO", {
      x: 0.8, y: 4.1, w: 8.5, h: 0.25,
      fontSize: 10, color: C.teal, fontFace: "Calibri", bold: true, charSpacing: 2
    });
    s.addText("Ogni volta che un trainer invia il link anamnesi, il cliente vede \"Powered by FitManager Studio+\" nel footer. Con 30 trainer attivi e 20 clienti ciascuno = 600+ esposizioni/mese a costo zero. Il meccanismo cresce automaticamente.", {
      x: 0.8, y: 4.4, w: 8.5, h: 0.8,
      fontSize: 11, color: C.text, fontFace: "Calibri"
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 22 — RISULTATI ATTESI PER FASE
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 8");
    addLightTitle(s, "Risultati attesi per fase");

    const phases = [
      { phase: "Pre-lancio", period: "4 sett. prima POC", leads: "50+ iscritti waiting list", sales: "0", color: C.textMid },
      { phase: "POC", period: "Mesi 1-3", leads: "Focus 10 Fondatori", sales: "10 (selezionati)", color: C.teal },
      { phase: "Early Adopter", period: "Mesi 4-6", leads: "15-25/mese", sales: "2-3/mese", color: C.tealDark },
      { phase: "Prezzo pieno", period: "Mesi 7-12", leads: "22-35/mese", sales: "3-5/mese", color: C.navy },
    ];
    for (let i = 0; i < 4; i++) {
      const y = 1.2 + i * 1.0;
      s.addShape("rect", { x: 0.5, y, w: 9, h: 0.85, fill: { color: C.white }, shadow: makeCardShadow() });
      s.addShape("rect", { x: 0.5, y, w: 0.06, h: 0.85, fill: { color: phases[i].color } });
      s.addText(phases[i].phase, {
        x: 0.8, y, w: 1.8, h: 0.85,
        fontSize: 14, color: phases[i].color, fontFace: "Calibri", bold: true, valign: "middle", margin: 0
      });
      s.addText(phases[i].period, {
        x: 2.6, y, w: 2, h: 0.85,
        fontSize: 11, color: C.textMid, fontFace: "Calibri", valign: "middle", margin: 0
      });
      s.addText(phases[i].leads, {
        x: 4.6, y, w: 2.5, h: 0.85,
        fontSize: 11, color: C.text, fontFace: "Calibri", valign: "middle", margin: 0
      });
      s.addText(phases[i].sales, {
        x: 7.3, y, w: 2, h: 0.85,
        fontSize: 14, color: phases[i].color, fontFace: "Georgia", bold: true, valign: "middle", align: "center", margin: 0
      });
    }
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 23 — POC OVERVIEW (section divider)
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    addDarkTitle(s, "La Proof of Concept", "Non vendiamo subito. Prima dimostriamo — il pacchetto completo.", "Sezione 9");

    s.addText("I primi 10 non sono solo tester del software. Sono i primi studenti del Metodo PT Evoluto. La POC valida simultaneamente il prodotto, la categoria professionale, la community, e il ruolo dell'Industry Partner.", {
      x: 0.5, y: 3.7, w: 8.5, h: 0.7,
      fontSize: 13, color: C.textLight, fontFace: "Calibri"
    });
    s.addText("Se non funziona, lo scopriamo con 10 persone e ~€1.000.", {
      x: 0.5, y: 4.5, w: 8, h: 0.4,
      fontSize: 14, color: C.coral, fontFace: "Calibri", bold: true
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 24 — COSA RICEVONO I FONDATORI
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 9");
    addLightTitle(s, "Cosa ricevono i 10 Fondatori");

    s.addText("I Fondatori non ricevono solo il software. Ricevono il percorso completo per 12 mesi:", {
      x: 0.5, y: 1.1, w: 9, h: 0.4,
      fontSize: 12, color: C.textMid, fontFace: "Calibri", italic: true
    });

    const included = [
      [icons.laptop, "Software o Box", "8 ricevono la licenza (€99), 2 ricevono la Box (€199)"],
      [icons.grad, "Inner Circle 12 mesi", "Masterclass, webinar, mastermind — incluso, non extra"],
      [icons.friends, "Community Fondatori", "Canale riservato per feedback, idee, supporto"],
      [icons.tools, "Installazione assistita", "Setup 1:1 con il founder"],
    ];
    for (let i = 0; i < 4; i++) {
      const y = 1.6 + i * 0.75;
      s.addShape("rect", { x: 0.5, y, w: 9, h: 0.65, fill: { color: C.white }, shadow: makeCardShadow() });
      s.addImage({ data: included[i][0], x: 0.7, y: y + 0.12, w: 0.35, h: 0.35 });
      s.addText(included[i][1], {
        x: 1.3, y, w: 2.5, h: 0.65,
        fontSize: 12, color: C.text, fontFace: "Calibri", bold: true, valign: "middle", margin: 0
      });
      s.addText(included[i][2], {
        x: 3.8, y, w: 5.5, h: 0.65,
        fontSize: 11, color: C.textMid, fontFace: "Calibri", valign: "middle", margin: 0
      });
    }

    // Value comparison
    s.addShape("rect", { x: 0.5, y: 4.55, w: 9, h: 0.8, fill: { color: "E6FAF5" } });
    s.addText("Valore reale del pacchetto: €498 (licenza) / €698 (Box). I Fondatori lo ottengono a €99 / €199 perché sono l'investimento più importante del progetto.", {
      x: 0.7, y: 4.6, w: 8.5, h: 0.7,
      fontSize: 12, color: C.tealDark, fontFace: "Calibri", bold: true
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 25 — PROTOCOLLO POC
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 9");
    addLightTitle(s, "Il protocollo: prodotto + formazione");

    const phases = [
      {
        title: "Fase A — Setup e baseline",
        period: "Giorni 1-14",
        desc: "10 professionisti selezionati. Questionario baseline. Installazione e inserimento primi clienti.",
        color: C.tealLight,
      },
      {
        title: "Fase B — Adozione e masterclass",
        period: "Giorni 15-75",
        desc: "Uso reale quotidiano. Check-in bisettimanale. Micro-sondaggio settimanale. 3 masterclass condotte dal Partner.",
        color: C.teal,
      },
      {
        title: "Fase C — Misurazione",
        period: "Giorni 75-90",
        desc: "Questionario finale. Confronto prima/dopo. Video-intervista. Sessione di gruppo. Decisione GO/NO-GO.",
        color: C.tealDark,
      },
    ];
    for (let i = 0; i < 3; i++) {
      const y = 1.15 + i * 1.0;
      s.addShape("rect", { x: 0.5, y, w: 9, h: 0.85, fill: { color: C.white }, shadow: makeCardShadow() });
      s.addShape("rect", { x: 0.5, y, w: 0.08, h: 0.85, fill: { color: phases[i].color } });
      s.addText(phases[i].title, {
        x: 0.8, y: y + 0.05, w: 5, h: 0.3,
        fontSize: 13, color: phases[i].color, fontFace: "Calibri", bold: true, margin: 0
      });
      s.addText(phases[i].period, {
        x: 7, y: y + 0.05, w: 2.3, h: 0.3,
        fontSize: 10, color: C.textMid, fontFace: "Calibri", align: "right", margin: 0
      });
      s.addText(phases[i].desc, {
        x: 0.8, y: y + 0.4, w: 8.5, h: 0.4,
        fontSize: 10, color: C.text, fontFace: "Calibri", margin: 0
      });
    }

    // Masterclass detail
    s.addText("Le 3 masterclass (condotte dall'Industry Partner):", {
      x: 0.5, y: 4.25, w: 9, h: 0.25,
      fontSize: 10, color: C.teal, fontFace: "Calibri", bold: true
    });
    s.addText([
      { text: "Mese 1: \"Il Metodo PT Evoluto — come cambia il tuo lavoro\"", options: { bullet: true, breakLine: true } },
      { text: "Mese 2: \"Le prime 4 settimane con FitManager — risultati e domande\"", options: { bullet: true, breakLine: true } },
      { text: "Mese 3: \"Da 25 a 45 clienti — il metodo in pratica\"", options: { bullet: true } },
    ], {
      x: 0.7, y: 4.5, w: 8.5, h: 0.6,
      fontSize: 9, color: C.text, fontFace: "Calibri"
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 26 — METRICHE POC
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 9");
    addLightTitle(s, "Le metriche della POC");

    const metrics = [
      ["Ore admin/settimana", "3-5 ore", "< 2 ore", "Prodotto"],
      ["Organizzazione (1-10)", "4-6", "8+", "Prodotto"],
      ["Dati persi/mese", "2-3", "Zero", "Prodotto"],
      ["NPS (-100/+100)", "—", "Sopra 50", "Prodotto + percorso"],
      ["\"Lo ricompreresti a prezzo pieno?\"", "—", "8/10 sì", "Pricing"],
      ["\"Masterclass hanno cambiato approccio?\"", "—", "7+/10 sì", "Percorso"],
      ["\"I tuoi clienti notano differenza?\"", "—", "5+/10 sì", "Volano PT Evoluto"],
      ["\"Ti definiresti un PT Evoluto?\"", "—", "6+/10 sì", "Category creation"],
    ];
    const hdr = [
      { text: "Metrica", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 10 } },
      { text: "Prima", options: { fill: { color: C.teal }, color: C.white, bold: true, align: "center", fontSize: 10 } },
      { text: "Target", options: { fill: { color: C.teal }, color: C.white, bold: true, align: "center", fontSize: 10 } },
      { text: "Valida", options: { fill: { color: C.teal }, color: C.white, bold: true, align: "center", fontSize: 10 } },
    ];
    const tableData = [hdr];
    for (let r = 0; r < metrics.length; r++) {
      tableData.push(metrics[r].map((cell, idx) => ({
        text: cell,
        options: {
          fontSize: 9, fontFace: "Calibri",
          color: idx === 2 ? C.tealDark : C.text,
          bold: idx === 2,
          align: idx === 0 ? "left" : "center",
          fill: { color: r % 2 === 0 ? C.white : C.offWhite },
        }
      })));
    }
    s.addTable(tableData, {
      x: 0.5, y: 1.1, w: 9,
      colW: [3.5, 1.5, 1.5, 2.5],
      border: { pt: 0.5, color: "E2E8F0" },
      rowH: [0.38, 0.38, 0.38, 0.38, 0.38, 0.38, 0.38, 0.38, 0.38],
    });

    s.addText("Le ultime 3 metriche validano la categoria e il volano — non solo il software.", {
      x: 0.5, y: 4.7, w: 9, h: 0.4,
      fontSize: 11, color: C.coral, fontFace: "Calibri", bold: true, italic: true
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 27 — PROFILI FONDATORI + DECISIONE
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 9");
    addLightTitle(s, "I profili e la decisione");

    s.addText("I 10 FONDATORI", { x: 0.5, y: 1.15, w: 4, h: 0.3, fontSize: 10, color: C.teal, fontFace: "Calibri", bold: true, charSpacing: 2 });
    s.addText([
      { text: "3 trainer in palestra", options: { bullet: true, breakLine: true } },
      { text: "2 freelance con studio proprio", options: { bullet: true, breakLine: true } },
      { text: "2 chinesiologi con clienti clinici", options: { bullet: true, breakLine: true } },
      { text: "1 trainer online/ibrido", options: { bullet: true, breakLine: true } },
      { text: "1 neoqualificato", options: { bullet: true, breakLine: true } },
      { text: "1 senior con 40+ clienti", options: { bullet: true } },
    ], { x: 0.5, y: 1.5, w: 4.5, h: 1.7, fontSize: 10, color: C.text, fontFace: "Calibri" });
    s.addText("Criterio: almeno 10 clienti attivi, disponibilità a dare feedback strutturato per 90 giorni.", {
      x: 0.5, y: 3.25, w: 4.5, h: 0.5, fontSize: 9, color: C.textMid, fontFace: "Calibri", italic: true
    });

    s.addText("LA DECISIONE", { x: 5.5, y: 1.15, w: 4, h: 0.3, fontSize: 10, color: C.teal, fontFace: "Calibri", bold: true, charSpacing: 2 });
    const decisions = [
      { result: "NPS 50+, ore dimezzate, 8+ attivi, 5+ clienti notano", decision: "GO", color: C.green },
      { result: "NPS 30-50, miglioramenti parziali, categoria parziale", decision: "GO cautela", color: C.gold },
      { result: "NPS <30, meno di 6 attivi, categoria non risuona", decision: "STOP", color: C.coral },
    ];
    for (let i = 0; i < 3; i++) {
      const y = 1.6 + i * 0.9;
      s.addShape("rect", { x: 5.5, y, w: 4, h: 0.75, fill: { color: C.white }, shadow: makeCardShadow() });
      s.addShape("rect", { x: 5.5, y, w: 0.06, h: 0.75, fill: { color: decisions[i].color } });
      s.addText(decisions[i].decision, {
        x: 5.7, y, w: 1.2, h: 0.75,
        fontSize: 14, color: decisions[i].color, fontFace: "Georgia", bold: true, valign: "middle", margin: 0
      });
      s.addText(decisions[i].result, {
        x: 6.9, y, w: 2.4, h: 0.75,
        fontSize: 9, color: C.textMid, fontFace: "Calibri", valign: "middle", margin: 0
      });
    }

    s.addShape("rect", { x: 0.5, y: 4.2, w: 9, h: 0.9, fill: { color: C.tealDark } });
    s.addText("COSA ABBIAMO AL MESE 4 (se GO)", { x: 0.7, y: 4.22, w: 8.5, h: 0.2, fontSize: 9, color: C.mint, fontFace: "Calibri", bold: true, charSpacing: 2 });
    s.addText([
      { text: "10 storie reali con dati misurabili (prima/dopo)", options: { bullet: true, breakLine: true } },
      { text: "10 video-interviste testimonial", options: { bullet: true, breakLine: true } },
      { text: "3 masterclass registrate (libreria Inner Circle)", options: { bullet: true, breakLine: true } },
      { text: "Dati aggregati + community funzionante", options: { bullet: true, breakLine: true } },
      { text: "La prova che il percorso PT Evoluto funziona — non solo il software", options: { bullet: true } },
    ], { x: 0.7, y: 4.42, w: 8.5, h: 0.65, fontSize: 9, color: C.white, fontFace: "Calibri" });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 28 — COSTO POC
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 9");
    addLightTitle(s, "Costo della POC");

    const costItems = [
      ["8 licenze Fondatore a €99 + 2 Box a €199", "€1.190 (ricavo)"],
      ["Costo vivo hardware 2 Box test", "€300"],
      ["Tempo founder (check-in, supporto, analisi)", "~40 ore in 90 gg"],
      ["Tempo partner (selezione, 3 masterclass)", "~15-20 ore in 90 gg"],
      ["Investimento netto in cash", "~€300"],
    ];
    for (let i = 0; i < costItems.length; i++) {
      const y = 1.2 + i * 0.55;
      const isLast = i === 4;
      s.addShape("rect", { x: 0.5, y, w: 9, h: 0.45, fill: { color: isLast ? "E6FAF5" : (i % 2 === 0 ? C.white : C.offWhite) } });
      s.addText(costItems[i][0], { x: 0.7, y, w: 6, h: 0.45, fontSize: 12, color: C.text, fontFace: "Calibri", bold: isLast, valign: "middle", margin: 0 });
      s.addText(costItems[i][1], { x: 6.7, y, w: 2.6, h: 0.45, fontSize: 12, color: isLast ? C.tealDark : C.text, fontFace: "Calibri", bold: isLast, align: "right", valign: "middle", margin: 0 });
    }

    s.addText("Il partner viene compensato con il 25% dei ricavi POC (€298) e con la proprietà condivisa delle registrazioni: le 3 masterclass entrano nella libreria Inner Circle e generano il 30% di revenue share per ogni futuro membro.", {
      x: 0.5, y: 4.2, w: 9, h: 0.65, fontSize: 10, color: C.textMid, fontFace: "Calibri"
    });
    s.addText("Costo totale se ci fermiamo al giorno 90: 3 mesi di tempo e circa €1.000.", {
      x: 0.5, y: 4.95, w: 9, h: 0.3, fontSize: 12, color: C.coral, fontFace: "Calibri", bold: true
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 29 — PROIEZIONI: SECTION DIVIDER
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    addDarkTitle(s, "Proiezioni finanziarie", "Due strutture a confronto: il business sta in piedi indipendentemente dalla partnership", "Sezione 10");
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 30 — CONFIG A: FOUNDER SOLO
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 10 — Configurazione A");
    addLightTitle(s, "Founder solo (senza Industry Partner)");

    s.addText("LinkedIn organico, SEO, referral, webinar self-hosted. Lead a regime: 10-14/mese. Vendite a regime: 1-2/mese.", {
      x: 0.5, y: 1.1, w: 9, h: 0.35, fontSize: 11, color: C.textMid, fontFace: "Calibri", italic: true
    });

    const hdr = [
      { text: "", options: { fill: { color: C.textMid }, fontSize: 10 } },
      { text: "Anno 1", options: { fill: { color: C.textMid }, color: C.white, bold: true, align: "center", fontSize: 11 } },
      { text: "Anno 2", options: { fill: { color: C.textMid }, color: C.white, bold: true, align: "center", fontSize: 11 } },
      { text: "Anno 3", options: { fill: { color: C.textMid }, color: C.white, bold: true, align: "center", fontSize: 11 } },
    ];
    const rows = [
      ["Nuovi clienti", "24", "34", "50"],
      ["Base cumulativa", "24", "58", "108"],
      ["Fatturato", "€7.200", "€13.500", "€22.000"],
      ["Costi totali", "€5.800", "€8.500", "€14.000"],
      ["Tasse", "€1.512", "€2.835", "€4.400"],
      ["Netto founder", "-€112", "€2.165", "€3.600"],
    ];
    const tableData = [hdr];
    for (const row of rows) {
      const isNet = row[0] === "Netto founder";
      tableData.push(row.map((cell, idx) => ({
        text: cell,
        options: {
          fontSize: 11, fontFace: "Calibri",
          color: isNet ? (cell.startsWith("-") ? C.coral : C.tealDark) : C.text,
          bold: isNet || idx === 0,
          align: idx === 0 ? "left" : "center",
          fill: { color: isNet ? "E6FAF5" : C.white },
        }
      })));
    }
    s.addTable(tableData, {
      x: 0.5, y: 1.6, w: 9, colW: [3, 2, 2, 2],
      border: { pt: 0.5, color: "E2E8F0" },
      rowH: [0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.45],
    });

    s.addText("Il business sopravvive. Non genera debito. Ma la crescita è lenta e il founder non si paga un vero stipendio per almeno 2 anni.", {
      x: 0.5, y: 4.6, w: 9, h: 0.5, fontSize: 12, color: C.textMid, fontFace: "Calibri", italic: true
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 31-33 — CONFIG B: 3 SCENARI
  // ══════════════════════════════════════════════════════════════
  const scenarios = [
    {
      label: "Config. B Conservativo", title: "Con partner — Scenario conservativo",
      subtitle: "Partner arriva tardi, conversione 20%, Inner Circle con bassa adozione (12% della base)",
      headerColor: C.navy,
      rows: [
        ["Nuovi clienti", "33", "35", "49"], ["Base cumulativa", "33", "68", "117"],
        ["Vendite prodotto", "€8.559", "€12.632", "€18.108"], ["Assistenza PRO", "€160", "€2.414", "€4.945"],
        ["Inner Circle", "€996", "€2.040", "€4.388"], ["Fatturato", "€10.715", "€17.086", "€27.441"],
        ["Costi + operativi", "€6.970", "€9.330", "€12.990"], ["Compenso partner", "€1.735", "€2.782", "€4.590"],
        ["Tasse", "€2.250", "€3.588", "€6.467"], ["Netto founder", "-€240", "€1.386", "€3.394"],
        ["Netto partner", "€1.735", "€2.782", "€4.590"],
      ]
    },
    {
      label: "Config. B Base", title: "Con partner — Scenario base",
      subtitle: "Partner operativo dal mese 2, conversione 25%, Inner Circle al 20% della base",
      headerColor: C.teal,
      rows: [
        ["Nuovi clienti", "46", "58", "87"], ["Base cumulativa", "46", "104", "191"],
        ["Vendite prodotto", "€13.950", "€21.450", "€32.850"], ["Assistenza PRO", "€950", "€3.700", "€7.300"],
        ["Inner Circle", "€2.250", "€4.500", "€9.500"], ["Fatturato", "€17.150", "€29.650", "€49.650"],
        ["Costi + operativi", "€8.560", "€14.325", "€22.865"], ["Compenso partner", "€2.375", "€4.200", "€7.500"],
        ["Tasse", "€3.600", "€6.230", "€6.750"], ["Netto founder", "€2.615", "€4.895", "€12.535"],
        ["Netto partner", "€2.375", "€4.200", "€7.500"],
      ],
      footnote: "Dall'Anno 3, con fatturato >€40K, transizione a regime ordinario/SRL. Tasse ~35% sul reddito netto (costi deducibili)."
    },
    {
      label: "Config. B Ottimistico", title: "Con partner — Scenario ottimistico",
      subtitle: "Partner forte, conversione 30%, Inner Circle al 25% della base",
      headerColor: C.gold,
      rows: [
        ["Nuovi clienti", "67", "97", "155"], ["Base cumulativa", "67", "164", "319"],
        ["Vendite prodotto", "€23.383", "€37.330", "€57.680"], ["Assistenza PRO", "€1.600", "€4.430", "€8.620"],
        ["Inner Circle", "€2.990", "€7.380", "€15.200"], ["Fatturato", "€27.973", "€49.140", "€81.500"],
        ["Costi + operativi", "€11.050", "€22.130", "€38.250"], ["Compenso partner", "€4.500", "€8.100", "€13.900"],
        ["Tasse", "€5.874", "€6.620", "€10.270"], ["Netto founder", "€6.549", "€12.290", "€19.080"],
        ["Netto partner", "€4.500", "€8.100", "€13.900"],
      ]
    },
  ];

  for (const sc of scenarios) {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, `Sezione 10 — ${sc.label}`);
    addLightTitle(s, sc.title);
    s.addText(sc.subtitle, { x: 0.5, y: 1.1, w: 9, h: 0.3, fontSize: 11, color: C.textMid, fontFace: "Calibri", italic: true });

    const hdr = [
      { text: "", options: { fill: { color: sc.headerColor }, fontSize: 10 } },
      { text: "Anno 1", options: { fill: { color: sc.headerColor }, color: C.white, bold: true, align: "center", fontSize: 10 } },
      { text: "Anno 2", options: { fill: { color: sc.headerColor }, color: C.white, bold: true, align: "center", fontSize: 10 } },
      { text: "Anno 3", options: { fill: { color: sc.headerColor }, color: C.white, bold: true, align: "center", fontSize: 10 } },
    ];
    const tableData = [hdr];
    for (const row of sc.rows) {
      const isBold = ["Fatturato", "Netto founder", "Netto partner"].includes(row[0]);
      const highlightColor = sc.headerColor === C.gold ? "FFF7ED" : "E6FAF5";
      tableData.push(row.map((cell, idx) => ({
        text: cell,
        options: {
          fontSize: 9, fontFace: "Calibri",
          color: row[0] === "Netto founder" ? (cell.startsWith("-") ? C.coral : C.tealDark) : (row[0] === "Netto partner" ? C.navy : C.text),
          bold: isBold || idx === 0,
          align: idx === 0 ? "left" : "center",
          fill: { color: isBold ? highlightColor : C.white },
        }
      })));
    }
    s.addTable(tableData, {
      x: 0.3, y: 1.5, w: 9.4, colW: [2.8, 2.2, 2.2, 2.2],
      border: { pt: 0.5, color: "E2E8F0" },
      rowH: new Array(12).fill(0.29),
    });
    if (sc.footnote) {
      s.addText(sc.footnote, { x: 0.3, y: 4.95, w: 8, h: 0.2, fontSize: 7.5, color: C.textMid, fontFace: "Calibri", italic: true });
    }
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 34 — CONFRONTO CON/SENZA PARTNER
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.darkBg };
    s.addShape("rect", { x: 0, y: 0, w: 0.06, h: 5.625, fill: { color: C.teal } });

    s.addText("IL CONFRONTO DIRETTO", { x: 0.5, y: 0.4, w: 9, h: 0.3, fontSize: 10, color: C.teal, fontFace: "Calibri", bold: true, charSpacing: 4 });
    s.addText("Cosa cambia con il partner", { x: 0.5, y: 0.8, w: 9, h: 0.6, fontSize: 30, color: C.white, fontFace: "Georgia", bold: true, margin: 0 });

    const comparison = [
      ["Clienti Anno 1", "24", "46", "1,9x"],
      ["Clienti Anno 3", "108", "191", "1,8x"],
      ["Fatturato Anno 1", "€7.200", "€17.150", "2,4x"],
      ["Fatturato Anno 3", "€22.000", "€49.650", "2,3x"],
      ["Netto founder Anno 3", "€3.600", "€12.535", "3,5x"],
      ["Fatturato cumulativo 3 anni", "€42.700", "€96.450", "2,3x"],
    ];
    const hdr = [
      { text: "", options: { fill: { color: C.tealDark } } },
      { text: "Senza partner", options: { fill: { color: C.tealDark }, color: C.white, bold: true, align: "center", fontSize: 10 } },
      { text: "Con partner (base)", options: { fill: { color: C.tealDark }, color: C.white, bold: true, align: "center", fontSize: 10 } },
      { text: "Moltiplicatore", options: { fill: { color: C.tealDark }, color: C.gold, bold: true, align: "center", fontSize: 10 } },
    ];
    const tableData = [hdr];
    for (const row of comparison) {
      tableData.push(row.map((cell, idx) => ({
        text: cell,
        options: {
          fontSize: 10, fontFace: "Calibri",
          color: idx === 3 ? C.gold : (idx === 2 ? C.tealLight : C.white),
          bold: idx === 0 || idx === 3,
          align: idx === 0 ? "left" : "center",
          fill: { color: C.darkBg2 },
        }
      })));
    }
    s.addTable(tableData, {
      x: 0.5, y: 1.6, w: 9, colW: [3, 2, 2, 2],
      border: { pt: 0.5, color: "2A3A4E" },
      rowH: [0.38, 0.38, 0.38, 0.38, 0.38, 0.38, 0.38],
    });

    s.addText("Il partner non solo raddoppia le vendite — abilita un intero flusso di ricavo (Inner Circle) che non esiste senza partner. Moltiplicatore 3,5x sul netto: l'IC è ad alto margine e cresce con la base.", {
      x: 0.5, y: 4.35, w: 9, h: 0.55, fontSize: 10, color: C.textLight, fontFace: "Calibri"
    });
    s.addText("Il business funziona senza partner. Con il partner, decolla.", {
      x: 0.5, y: 4.85, w: 9, h: 0.3, fontSize: 13, color: C.mint, fontFace: "Calibri", bold: true
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 35 — VISTA CUMULATIVA
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 10");
    addLightTitle(s, "Vista cumulativa (scenario base)");

    const hdr = [
      { text: "", options: { fill: { color: C.teal }, fontSize: 9 } },
      { text: "Anno 1", options: { fill: { color: C.teal }, color: C.white, bold: true, align: "center", fontSize: 9 } },
      { text: "Anno 2", options: { fill: { color: C.teal }, color: C.white, bold: true, align: "center", fontSize: 9 } },
      { text: "Anno 3", options: { fill: { color: C.teal }, color: C.white, bold: true, align: "center", fontSize: 9 } },
      { text: "Cumulativo", options: { fill: { color: C.teal }, color: C.white, bold: true, align: "center", fontSize: 9 } },
    ];
    const rows = [
      ["PROGETTO", "", "", "", ""], ["Clienti (base installata)", "46", "104", "191", "—"],
      ["Di cui Inner Circle", "9", "18", "38", "—"], ["Fatturato", "€17.150", "€29.650", "€49.650", "€96.450"],
      ["Di cui ricorrente (PRO+IC)", "€3.200", "€8.200", "€16.800", "€28.200"],
      ["FOUNDER", "", "", "", ""], ["Netto cash", "€2.615", "€4.895", "€12.535", "€20.045"],
      ["Equity detenuta", "92-95%", "92-95%", "92-95%", "—"],
      ["PARTNER", "", "", "", ""], ["Cash (compenso diff.)", "€2.375", "€4.200", "€7.500", "€14.075"],
      ["Equity detenuta", "5-8%", "5-8%", "5-8%", "—"], ["Valore equity stimato", "€1.600", "€4.100", "€8.400", "—"],
      ["Totale partner (cash+eq.)", "€3.975", "€8.300", "€15.900", "€28.175"],
      ["Valore stimato progetto", "€26.000", "€68.000", "€140.000", "—"],
    ];
    const tableData = [hdr];
    for (const row of rows) {
      const isHeader = ["PROGETTO", "FOUNDER", "PARTNER"].includes(row[0]);
      const isHighlight = ["Fatturato", "Netto cash", "Totale partner (cash+eq.)", "Valore stimato progetto"].includes(row[0]);
      tableData.push(row.map((cell, idx) => ({
        text: cell,
        options: {
          fontSize: 8.5, fontFace: "Calibri",
          color: isHeader ? C.teal : (isHighlight ? C.tealDark : C.text),
          bold: isHeader || isHighlight || idx === 0,
          align: idx === 0 ? "left" : "center",
          fill: { color: isHeader ? "E6FAF5" : (isHighlight ? "F0FDF9" : C.white) },
        }
      })));
    }
    s.addTable(tableData, {
      x: 0.3, y: 1.1, w: 9.4, colW: [2.6, 1.6, 1.6, 1.6, 2],
      border: { pt: 0.5, color: "E2E8F0" },
      rowH: new Array(15).fill(0.25),
    });

    s.addText("Valutazione: 2x ricavo ricorrente annualizzato + valore base installata + IP + community. Metodo conservativo per software B2B verticali.", {
      x: 0.3, y: 4.9, w: 9.4, h: 0.25, fontSize: 7.5, color: C.textMid, fontFace: "Calibri", italic: true
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 36 — SE VA MALE
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    addDarkTitle(s, "Se va male", "Lo scenario peggiore — tutto va male contemporaneamente", "Sezione 11");

    const worstCase = [
      ["Clienti Anno 1", "18-20"], ["Fatturato", "~€5.500"], ["Perdita netta", "~€700"], ["Perdita massima cash", "~€2.000"],
    ];
    for (let i = 0; i < 4; i++) {
      const x = 0.5 + i * 2.3;
      s.addShape("rect", { x, y: 3.7, w: 2.1, h: 0.9, fill: { color: C.darkBg2 } });
      s.addText(worstCase[i][1], { x, y: 3.72, w: 2.1, h: 0.45, fontSize: 20, color: C.coral, fontFace: "Georgia", bold: true, align: "center", margin: 0 });
      s.addText(worstCase[i][0], { x, y: 4.2, w: 2.1, h: 0.35, fontSize: 10, color: C.textLight, fontFace: "Calibri", align: "center", margin: 0 });
    }

    s.addText("Il business non chiude. Non genera debito. La perdita massima è il costo di un corso di formazione.", {
      x: 0.5, y: 4.75, w: 9, h: 0.4, fontSize: 13, color: C.mint, fontFace: "Calibri", bold: true
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 37 — RISCHI SPECIFICI
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 11");
    addLightTitle(s, "Rischi specifici e mitigazioni");

    const risks = [
      { risk: "\"I trainer non vogliono pagare per un software.\"", mitigation: "La POC include misurazione WTP prima di rivelare il prezzo. Se il dato esce basso, lo sappiamo con 10 persone." },
      { risk: "\"Il partner si disimpegna.\"", mitigation: "Equity con cliff 12 mesi. Il business parte anche senza partner — più lentamente (Config. A)." },
      { risk: "\"Un competitor copia.\"", mitigation: "DB scientifico (500 esercizi, 940 relazioni, Safety Engine, CREA) = 6+ mesi di lavoro. Architettura locale non replicabile da SaaS." },
      { risk: "\"I rinnovi assistenza sono bassi.\"", mitigation: "Se sotto 40%, il contenuto non ha valore percepito sufficiente. Lo misuriamo e correggiamo. Business non dipende dai rinnovi Anno 1." },
    ];
    for (let i = 0; i < 4; i++) {
      const y = 1.15 + i * 0.97;
      s.addShape("rect", { x: 0.5, y, w: 9, h: 0.85, fill: { color: C.white }, shadow: makeCardShadow() });
      s.addShape("rect", { x: 0.5, y, w: 0.06, h: 0.85, fill: { color: C.coral } });
      s.addText(risks[i].risk, { x: 0.8, y: y + 0.05, w: 8.5, h: 0.3, fontSize: 11, color: C.coral, fontFace: "Calibri", bold: true, italic: true, margin: 0 });
      s.addText(risks[i].mitigation, { x: 0.8, y: y + 0.37, w: 8.5, h: 0.42, fontSize: 10, color: C.text, fontFace: "Calibri", margin: 0 });
    }
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 38 — TEAM ANNO 1
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 12 — Team");
    addLightTitle(s, "Anno 1: founder + Industry Partner");

    s.addShape("rect", { x: 0.5, y: 1.15, w: 4.3, h: 3.2, fill: { color: C.white }, shadow: makeCardShadow() });
    s.addImage({ data: icons.userTie, x: 0.7, y: 1.3, w: 0.4, h: 0.4 });
    s.addText("FOUNDER", { x: 1.2, y: 1.3, w: 3, h: 0.4, fontSize: 12, color: C.teal, fontFace: "Calibri", bold: true, charSpacing: 2, valign: "middle" });
    s.addText("Giacomo Verardo", { x: 0.7, y: 1.8, w: 3.8, h: 0.35, fontSize: 14, color: C.text, fontFace: "Calibri", bold: true, margin: 0 });
    s.addText([
      { text: "Sviluppo prodotto", options: { bullet: true, breakLine: true } },
      { text: "Vendite dirette", options: { bullet: true, breakLine: true } },
      { text: "Supporto clienti", options: { bullet: true, breakLine: true } },
      { text: "Marketing organico", options: { bullet: true, breakLine: true } },
      { text: "Gestione operativa", options: { bullet: true } },
    ], { x: 0.7, y: 2.2, w: 3.8, h: 1.8, fontSize: 11, color: C.text, fontFace: "Calibri" });

    s.addShape("rect", { x: 5.2, y: 1.15, w: 4.3, h: 3.2, fill: { color: C.white }, shadow: makeCardShadow() });
    s.addImage({ data: icons.handshake, x: 5.4, y: 1.3, w: 0.4, h: 0.4 });
    s.addText("INDUSTRY PARTNER", { x: 5.9, y: 1.3, w: 3, h: 0.4, fontSize: 12, color: C.navy, fontFace: "Calibri", bold: true, charSpacing: 2, valign: "middle" });
    s.addText("Professionista fitness con esperienza, credibilità, network attivo. Impegno: 8-10 ore/mese.", {
      x: 5.4, y: 1.8, w: 3.8, h: 0.5, fontSize: 10, color: C.textMid, fontFace: "Calibri", margin: 0
    });
    s.addText([
      { text: "Seleziona i Fondatori POC", options: { bullet: true, breakLine: true } },
      { text: "Presenta al proprio network", options: { bullet: true, breakLine: true } },
      { text: "Conduce masterclass/webinar", options: { bullet: true, breakLine: true } },
      { text: "Valida posizionamento PT Evoluto", options: { bullet: true } },
    ], { x: 5.4, y: 2.4, w: 3.8, h: 1.5, fontSize: 11, color: C.text, fontFace: "Calibri" });

    s.addShape("rect", { x: 0.5, y: 4.55, w: 9, h: 0.55, fill: { color: C.offWhite } });
    s.addText("Evoluzione: Anno 2 + tirocinante part-time (€4-5K)  |  Anno 3 + junior dev + ufficio (€12-16K)", {
      x: 0.7, y: 4.55, w: 8.5, h: 0.55, fontSize: 10, color: C.textMid, fontFace: "Calibri", valign: "middle"
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 39 — STRUTTURA COMPENSO PARTNER
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 12");
    addLightTitle(s, "Struttura di compenso del partner");

    s.addText("Il partner non riceve un compenso fisso. Riceve una quota dei ricavi con struttura differenziata:", {
      x: 0.5, y: 1.1, w: 9, h: 0.35, fontSize: 12, color: C.textMid, fontFace: "Calibri", italic: true
    });

    const compHdr = [
      { text: "Componente", options: { fill: { color: C.navy }, color: C.white, bold: true, fontSize: 10 } },
      { text: "%", options: { fill: { color: C.navy }, color: C.white, bold: true, align: "center", fontSize: 10 } },
      { text: "Applicata a", options: { fill: { color: C.navy }, color: C.white, bold: true, fontSize: 10 } },
    ];
    const compRows = [
      ["Ricavi POC", "25%", "Licenze e Box Fondatori"],
      ["Vendite dal suo network", "20%", "Licenze e Box via referral tracciato"],
      ["Assistenza PRO e Inner Circle", "25%", "Tutti i rinnovi e abbonamenti"],
      ["Masterclass condotte", "30%", "Sessioni live e registrate"],
    ];
    const tableData = [compHdr];
    for (const row of compRows) {
      tableData.push(row.map((cell, idx) => ({
        text: cell,
        options: { fontSize: 11, fontFace: "Calibri", color: idx === 1 ? C.navy : C.text, bold: idx === 1, align: idx === 1 ? "center" : "left", fill: { color: C.white } }
      })));
    }
    s.addTable(tableData, { x: 0.5, y: 1.6, w: 9, colW: [2.5, 1, 5.5], border: { pt: 0.5, color: "E2E8F0" }, rowH: [0.38, 0.38, 0.38, 0.38, 0.38] });

    s.addShape("rect", { x: 0.5, y: 3.6, w: 4.3, h: 1.5, fill: { color: C.white }, shadow: makeCardShadow() });
    s.addText("EQUITY", { x: 0.7, y: 3.7, w: 3.8, h: 0.25, fontSize: 9, color: C.teal, fontFace: "Calibri", bold: true, charSpacing: 2 });
    s.addText("5-8%", { x: 0.7, y: 3.95, w: 2, h: 0.5, fontSize: 28, color: C.teal, fontFace: "Georgia", bold: true, margin: 0 });
    s.addText("Maturazione 4 anni\nCliff 12 mesi", { x: 2.7, y: 3.95, w: 2, h: 0.5, fontSize: 11, color: C.textMid, fontFace: "Calibri", margin: 0 });
    s.addText("+ proprietà condivisa delle 3 masterclass POC\n(revenue share per ogni futuro membro IC)", { x: 0.7, y: 4.5, w: 3.8, h: 0.5, fontSize: 10, color: C.textMid, fontFace: "Calibri", margin: 0 });

    s.addShape("rect", { x: 5.2, y: 3.6, w: 4.3, h: 1.5, fill: { color: C.white }, shadow: makeCardShadow() });
    s.addText("ROI PER IL PROGETTO", { x: 5.4, y: 3.7, w: 3.8, h: 0.25, fontSize: 9, color: C.teal, fontFace: "Calibri", bold: true, charSpacing: 2 });
    s.addText("3,8x", { x: 5.4, y: 3.95, w: 2, h: 0.5, fontSize: 28, color: C.teal, fontFace: "Georgia", bold: true, margin: 0 });
    s.addText("Compenso triennio: €14.075\nFatturato aggiuntivo: €53.750", { x: 5.4, y: 4.5, w: 3.8, h: 0.5, fontSize: 10, color: C.textMid, fontFace: "Calibri", margin: 0 });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 40 — CHI È IL FOUNDER
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.darkBg };
    s.addShape("rect", { x: 0, y: 0, w: 0.06, h: 5.625, fill: { color: C.teal } });
    s.addText("CHI È IL FOUNDER", { x: 0.5, y: 0.4, w: 9, h: 0.3, fontSize: 10, color: C.teal, fontFace: "Calibri", bold: true, charSpacing: 4 });
    s.addText("Giacomo Verardo", { x: 0.5, y: 0.9, w: 9, h: 0.6, fontSize: 32, color: C.white, fontFace: "Georgia", bold: true, margin: 0 });

    const cv = [
      { icon: icons.industry, title: "Gestione sistemi complessi", desc: "Anni nella cantieristica navale e operazioni offshore (SAIPEM). Navi, cantieri, operazioni in Brasile, Africa, Cina." },
      { icon: icons.brain, title: "Competenza tecnologica ereditata", desc: "Due anni a fianco del padre, pioniere AI in Italia. Sistemi di visione artificiale per l'industria." },
      { icon: icons.laptop, title: "FitManager", desc: "6 mesi sviluppo full-time. 45.000 LOC, 395 test, 5 motori scientifici. In uso quotidiano da una professionista reale." },
      { icon: icons.heartbeat, title: "Competenza di dominio", desc: "Conoscenza diretta del fitness come praticante e istruttore. Intersezione tra competenza tecnica e dominio." },
    ];
    for (let i = 0; i < 4; i++) {
      const y = 1.7 + i * 0.85;
      s.addImage({ data: cv[i].icon, x: 0.5, y: y + 0.08, w: 0.35, h: 0.35 });
      s.addText(cv[i].title, { x: 1.1, y, w: 8, h: 0.3, fontSize: 13, color: C.tealLight, fontFace: "Calibri", bold: true, margin: 0 });
      s.addText(cv[i].desc, { x: 1.1, y: y + 0.3, w: 8, h: 0.45, fontSize: 10, color: C.textLight, fontFace: "Calibri", margin: 0 });
    }
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 41 — PIANO DI CRESCITA
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Sezione 13");
    addLightTitle(s, "Piano di crescita");

    const phases = [
      { phase: "Fase 1", period: "Mesi 1-3", title: "POC con percorso completo", desc: "10 Fondatori, software/Box + IC incluso 12 mesi. 3 masterclass. Validazione simultanea prodotto, percorso, categoria, ruolo partner.", color: C.tealLight },
      { phase: "Fase 2", period: "Mesi 4-6", title: "Early Adopter + Inner Circle attivo", desc: "Testimonial POC come leva. Network del partner. IC disponibile. Webinar gratuito mensile. Target: 15-20 clienti, 30% con IC.", color: C.teal },
      { phase: "Fase 3", period: "Mesi 7-12", title: "Prezzo pieno e scala", desc: "Tutti i canali attivi. IC consolidato con masterclass mensili. PT Evoluto circola nel settore. Target: 3-5 vendite/mese.", color: C.tealDark },
      { phase: "Fase 4", period: "Anno 2+", title: "Espansione", desc: "IC a pieno regime. Fiere (RiminiWellness). Partnership enti formazione. Bundle Box+Tablet. Primo collaboratore. Certificazione PT Evoluto.", color: C.navy },
    ];
    for (let i = 0; i < 4; i++) {
      const y = 1.15 + i * 0.95;
      s.addShape("rect", { x: 0.5, y, w: 9, h: 0.82, fill: { color: C.white }, shadow: makeCardShadow() });
      s.addShape("rect", { x: 0.5, y, w: 0.08, h: 0.82, fill: { color: phases[i].color } });
      s.addText(phases[i].phase, { x: 0.75, y: y + 0.05, w: 0.8, h: 0.3, fontSize: 11, color: phases[i].color, fontFace: "Georgia", bold: true, margin: 0 });
      s.addText(phases[i].period, { x: 1.5, y: y + 0.05, w: 1.2, h: 0.3, fontSize: 10, color: C.textMid, fontFace: "Calibri", margin: 0 });
      s.addText(phases[i].title, { x: 2.7, y: y + 0.05, w: 6.5, h: 0.3, fontSize: 12, color: C.text, fontFace: "Calibri", bold: true, margin: 0 });
      s.addText(phases[i].desc, { x: 2.7, y: y + 0.37, w: 6.5, h: 0.4, fontSize: 9, color: C.textMid, fontFace: "Calibri", margin: 0 });
    }

    s.addText("Il volano parte dalla POC: masterclass → PT Evoluto → clienti notano differenza → colleghi chiedono → passaparola → nuovi membri IC → community cresce → contenuto → ciclo. I costi acquisizione scendono, il ricorrente sale.", {
      x: 0.5, y: 4.9, w: 9, h: 0.25, fontSize: 8, color: C.tealDark, fontFace: "Calibri", italic: true
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 42 — COSA CERCHIAMO
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    addDarkTitle(s, "Cosa cerchiamo", null, "Sezione 14");

    s.addShape("rect", { x: 0.5, y: 3.0, w: 4.3, h: 2.0, fill: { color: C.darkBg2 } });
    s.addShape("rect", { x: 0.5, y: 3.0, w: 4.3, h: 0.06, fill: { color: C.teal } });
    s.addText("INDUSTRY PARTNER", { x: 0.7, y: 3.2, w: 3.8, h: 0.3, fontSize: 11, color: C.teal, fontFace: "Calibri", bold: true, charSpacing: 2 });
    s.addText("Un professionista fitness con esperienza, credibilità e network attivo. Non un dipendente — un partner con incentivi allineati (equity + rev share, zero costi fissi).", {
      x: 0.7, y: 3.6, w: 3.8, h: 1.2, fontSize: 11, color: C.textLight, fontFace: "Calibri"
    });

    s.addShape("rect", { x: 5.2, y: 3.0, w: 4.3, h: 2.0, fill: { color: C.darkBg2 } });
    s.addShape("rect", { x: 5.2, y: 3.0, w: 4.3, h: 0.06, fill: { color: C.gold } });
    s.addText("FINANZIAMENTO (post-POC)", { x: 5.4, y: 3.2, w: 3.8, h: 0.3, fontSize: 11, color: C.gold, fontFace: "Calibri", bold: true, charSpacing: 2 });
    s.addText("€20.000-40.000", { x: 5.4, y: 3.6, w: 3.8, h: 0.5, fontSize: 24, color: C.gold, fontFace: "Georgia", bold: true, margin: 0 });
    s.addText("Dopo validazione POC (NPS, WTP, adozione). Per marketing strutturato, fiere, primo collaboratore. Con 46+ clienti e dati reali.", {
      x: 5.4, y: 4.1, w: 3.8, h: 0.8, fontSize: 10, color: C.textLight, fontFace: "Calibri"
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 43 — APPENDICE A1
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Appendice A1");
    addLightTitle(s, "Dettaglio prodotto");

    const areas = [
      ["CRM", "Clienti, contratti, pagamenti, agenda, cassa — tutto in un profilo unico", "Completo"],
      ["Clinico", "Anamnesi guidata 6 step, misurazioni, avatar 6 viste, prontezza", "Completo"],
      ["Allenamento", "Workout builder 3 modalità, drag & drop, blocchi, export PDF", "Completo"],
      ["Nutrizione", "880 alimenti CREA, 210 ricette, 12 template LARN, piano settimanale", "Completo"],
      ["Operativo", "Setup guidato, licenza HW-bound, backup/ripristino, diagnostica", "Completo"],
      ["Accesso", "Portale anamnesi self-service, accesso remoto Tailscale", "Completo"],
    ];
    const hdr = [
      { text: "Area", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 11 } },
      { text: "Cosa fa", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 11 } },
      { text: "Stato", options: { fill: { color: C.teal }, color: C.white, bold: true, align: "center", fontSize: 11 } },
    ];
    const tableData = [hdr];
    for (const row of areas) {
      tableData.push(row.map((cell, idx) => ({
        text: cell, options: { fontSize: 10, fontFace: "Calibri", color: idx === 2 ? C.green : C.text, bold: idx === 0 || idx === 2, align: idx === 2 ? "center" : "left", fill: { color: C.white } }
      })));
    }
    s.addTable(tableData, { x: 0.5, y: 1.1, w: 9, colW: [1.5, 6, 1.5], border: { pt: 0.5, color: "E2E8F0" }, rowH: [0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4] });
    s.addText("500 esercizi, 940 relazioni (progressioni, regressioni, varianti), 47 condizioni cliniche, 80 regole Safety Engine.", {
      x: 0.5, y: 4.1, w: 9, h: 0.4, fontSize: 11, color: C.tealDark, fontFace: "Calibri", bold: true
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 44 — APPENDICE A3: P&L
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Appendice A3");
    addLightTitle(s, "P&L triennale dettagliato (scenario base)");

    s.addText("RICAVI", { x: 0.5, y: 1.05, w: 2, h: 0.25, fontSize: 9, color: C.teal, fontFace: "Calibri", bold: true, charSpacing: 2 });
    const mkHdr = () => [
      { text: "", options: { fill: { color: C.teal }, fontSize: 9 } },
      { text: "Anno 1", options: { fill: { color: C.teal }, color: C.white, bold: true, align: "center", fontSize: 9 } },
      { text: "Anno 2", options: { fill: { color: C.teal }, color: C.white, bold: true, align: "center", fontSize: 9 } },
      { text: "Anno 3", options: { fill: { color: C.teal }, color: C.white, bold: true, align: "center", fontSize: 9 } },
    ];
    const revRows = [
      ["Licenze software", "€4.278", "€5.727", "€7.719"], ["Box", "€9.672", "€15.723", "€25.131"],
      ["Assistenza PRO", "€950", "€3.700", "€7.300"], ["Inner Circle", "€2.250", "€4.500", "€9.500"],
      ["Fatturato totale", "€17.150", "€29.650", "€49.650"],
    ];
    const rt = [mkHdr()];
    for (const row of revRows) {
      const isTotal = row[0] === "Fatturato totale";
      rt.push(row.map((cell, idx) => ({ text: cell, options: { fontSize: 9, fontFace: "Calibri", color: isTotal ? C.tealDark : C.text, bold: isTotal || idx === 0, align: idx === 0 ? "left" : "center", fill: { color: isTotal ? "E6FAF5" : C.white } } })));
    }
    s.addTable(rt, { x: 0.3, y: 1.3, w: 9.4, colW: [2.4, 2.3, 2.3, 2.4], border: { pt: 0.5, color: "E2E8F0" }, rowH: new Array(6).fill(0.27) });

    s.addText("RIEPILOGO", { x: 0.5, y: 2.95, w: 2, h: 0.25, fontSize: 9, color: C.teal, fontFace: "Calibri", bold: true, charSpacing: 2 });
    const sumRows = [
      ["Fatturato", "€17.150", "€29.650", "€49.650"], ["Margine lordo", "€12.890 (75%)", "€23.825 (80%)", "€40.785 (82%)"],
      ["Costi operativi", "€4.300", "€8.500", "€20.000"], ["Compenso partner", "€2.375", "€4.200", "€7.500"],
      ["EBITDA", "€6.215", "€11.125", "€13.285"], ["Tasse", "€3.600", "€6.230", "€6.750"],
      ["Netto founder", "€2.615", "€4.895", "€12.535"],
    ];
    const st = [mkHdr()];
    for (const row of sumRows) {
      const isNet = row[0] === "Netto founder"; const isEBITDA = row[0] === "EBITDA";
      st.push(row.map((cell, idx) => ({ text: cell, options: { fontSize: 9, fontFace: "Calibri", color: isNet ? C.tealDark : (isEBITDA ? C.navy : C.text), bold: isNet || isEBITDA || idx === 0, align: idx === 0 ? "left" : "center", fill: { color: isNet ? "E6FAF5" : C.white } } })));
    }
    s.addTable(st, { x: 0.3, y: 3.2, w: 9.4, colW: [2.4, 2.3, 2.3, 2.4], border: { pt: 0.5, color: "E2E8F0" }, rowH: new Array(8).fill(0.24) });
    s.addText("Il margine lordo migliora nel tempo: il ricavo ricorrente (PRO + IC) ha margine 100% e cresce in % del fatturato.", { x: 0.3, y: 5.0, w: 9.4, h: 0.2, fontSize: 7.5, color: C.textMid, fontFace: "Calibri", italic: true });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 45 — APPENDICE A4: ASSUNZIONI
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Appendice A4");
    addLightTitle(s, "Le assunzioni chiave");

    const assHdr = [
      { text: "Cod.", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 9, align: "center" } },
      { text: "Assunzione", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 9 } },
      { text: "Stato", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 9, align: "center" } },
      { text: "Validazione", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 9 } },
    ];
    const assRows = [
      ["P4", "PT perde 3-5h/sett in admin", "Ipotesi", "Questionario baseline POC"],
      ["B7", "PT disposto a pagare €249-449", "Ipotesi critica", "Willingness-to-pay POC"],
      ["S4", "La Box risolve il problema mobile", "Ipotesi forte", "Test 2 Fondatori POC"],
      ["G3", "Partner genera 8-12 lead/mese", "Ipotesi", "Primo trim. partnership"],
      ["G4", "Conversione demo-acquisto 20-25%", "Ipotesi conserv.", "Dati reali mesi 4-6"],
      ["B5", "Rinnovo assistenza 55-60%", "Ipotesi", "Dato reale Anno 2"],
      ["M2", "Segmento target 10-15K PT", "Stima", "Primi 6 mesi vendita"],
      ["IC1", "IC raggiunge 20% base (base)", "Ipotesi", "Dato reale mesi 7-12"],
      ["IC2", "Masterclass generano adozione cat.", "Ipotesi forte", "Metriche POC"],
    ];
    const at = [assHdr];
    for (let r = 0; r < assRows.length; r++) {
      at.push(assRows[r].map((cell, idx) => ({
        text: cell,
        options: { fontSize: 8.5, fontFace: "Calibri", color: cell === "Ipotesi critica" ? C.coral : (cell.includes("forte") ? C.gold : C.text), bold: idx === 0 || cell === "Ipotesi critica", align: idx === 0 || idx === 2 ? "center" : "left", fill: { color: r % 2 === 0 ? C.white : C.offWhite } }
      })));
    }
    s.addTable(at, { x: 0.3, y: 1.1, w: 9.4, colW: [0.7, 3.5, 1.6, 3.6], border: { pt: 0.5, color: "E2E8F0" }, rowH: new Array(10).fill(0.32) });
    s.addText("Ogni proiezione è conservativa. I ricavi Inner Circle inclusi dal mese 4 (post-POC) nelle config. con partner.", { x: 0.3, y: 4.5, w: 9.4, h: 0.3, fontSize: 9, color: C.textMid, fontFace: "Calibri", italic: true });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 46 — APPENDICE A5: COMMUNITY (1/3) — Overview + Livello 1 & 2
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Appendice A5");
    addLightTitle(s, "Ecosistema community");

    // Intro text
    s.addText("PRO mantiene il software vivo. Inner Circle fa crescere il professionista.\nLe masterclass e i webinar del partner sono esclusivi Inner Circle, non PRO.", {
      x: 0.5, y: 1.05, w: 9, h: 0.4, fontSize: 10, color: C.textMid, fontFace: "Calibri", italic: true, margin: 0
    });

    // --- Livello 1 — Base ---
    const y1 = 1.55;
    s.addShape("rect", { x: 0.5, y: y1, w: 9, h: 0.75, fill: { color: C.white }, shadow: makeCardShadow() });
    s.addShape("rect", { x: 0.5, y: y1, w: 0.08, h: 0.75, fill: { color: C.textMid } });
    s.addText("Livello 1 — Base (gratuita, inclusa nella licenza)", { x: 0.8, y: y1 + 0.03, w: 6, h: 0.3, fontSize: 13, color: C.textMid, fontFace: "Calibri", bold: true, margin: 0 });
    s.addText("€0", { x: 7.5, y: y1 + 0.03, w: 1.8, h: 0.3, fontSize: 16, color: C.textMid, fontFace: "Georgia", bold: true, align: "right", margin: 0 });
    s.addText("Forum, knowledge base, annunci versioni, networking tra PT, onboarding guidato in 5 passi.", { x: 0.8, y: y1 + 0.38, w: 8.5, h: 0.3, fontSize: 9, color: C.textMid, fontFace: "Calibri", margin: 0 });

    // --- Livello 2 — PRO ---
    const y2 = 2.5;
    s.addShape("rect", { x: 0.5, y: y2, w: 9, h: 2.55, fill: { color: C.white }, shadow: makeCardShadow() });
    s.addShape("rect", { x: 0.5, y: y2, w: 0.08, h: 2.55, fill: { color: C.teal } });
    s.addText("Livello 2 — PRO  \"Il tuo software resta vivo\"", { x: 0.8, y: y2 + 0.05, w: 6, h: 0.3, fontSize: 13, color: C.teal, fontFace: "Calibri", bold: true, margin: 0 });
    s.addText("€79/anno", { x: 7.5, y: y2 + 0.05, w: 1.8, h: 0.3, fontSize: 16, color: C.teal, fontFace: "Georgia", bold: true, align: "right", margin: 0 });

    // PRO table
    const proHdr = [
      { text: "Contenuto", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 9 } },
      { text: "Frequenza", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 9 } },
    ];
    const proRows = [
      ["Aggiornamenti software (bugfix, miglioramenti)", "Continui"],
      ["Nuovi esercizi nel catalogo", "Trimestrale (30-50 nuovi)"],
      ["Nuovi alimenti nel database", "Semestrale"],
      ["Template schede scaricabili", "Mensile (1-2 template)"],
      ["Supporto prioritario (risposta <24h)", "Sempre"],
      ["Badge PRO nella community", "Permanente"],
    ];
    const proTable = [proHdr];
    proRows.forEach((r, idx) => {
      proTable.push(r.map(cell => ({ text: cell, options: { fontSize: 8.5, fontFace: "Calibri", color: C.text, fill: { color: idx % 2 === 0 ? C.white : C.offWhite } } })));
    });
    s.addTable(proTable, { x: 0.8, y: y2 + 0.42, w: 8.5, colW: [5.5, 3], border: { pt: 0.5, color: "E2E8F0" }, rowH: new Array(7).fill(0.22) });

    // PRO notes
    s.addText([
      { text: "Valore percepito: ~€300/anno per €79 (rapporto 3,8:1).", options: { bold: true, breakLine: true } },
      { text: "Non rinnovi? Il software funziona ma smette di aggiornarsi.", options: { breakLine: true } },
      { text: "Primi 30 clienti: 12 mesi inclusi. Dal 31°: €79 parte all'acquisto. Primi rinnovi: mese 13.", options: {} },
    ], { x: 0.8, y: y2 + 2.05, w: 8.5, h: 0.65, fontSize: 8.5, color: C.textMid, fontFace: "Calibri", margin: 0 });

    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // SLIDE 47 — APPENDICE A5: COMMUNITY (2/3) — Livello 3 & 4
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Appendice A5");
    addLightTitle(s, "Ecosistema community — Inner Circle & Mentorship");

    // --- Livello 3 — Inner Circle ---
    const y3 = 1.0;
    s.addShape("rect", { x: 0.5, y: y3, w: 9, h: 3.05, fill: { color: C.white }, shadow: makeCardShadow() });
    s.addShape("rect", { x: 0.5, y: y3, w: 0.08, h: 3.05, fill: { color: C.gold } });
    s.addText("Livello 3 — Inner Circle  \"Diventa un PT Evoluto\"", { x: 0.8, y: y3 + 0.05, w: 6, h: 0.3, fontSize: 13, color: C.gold, fontFace: "Calibri", bold: true, margin: 0 });
    s.addText("€249/anno", { x: 7.5, y: y3 + 0.05, w: 1.8, h: 0.3, fontSize: 16, color: C.gold, fontFace: "Georgia", bold: true, align: "right", margin: 0 });

    // IC table
    const icHdr = [
      { text: "Contenuto", options: { fill: { color: C.gold }, color: C.white, bold: true, fontSize: 9 } },
      { text: "Frequenza", options: { fill: { color: C.gold }, color: C.white, bold: true, fontSize: 9 } },
      { text: "Conduce", options: { fill: { color: C.gold }, color: C.white, bold: true, fontSize: 9 } },
    ];
    const icRows = [
      ["Masterclass tematiche (45-60 min + Q&A)", "Mensile", "Industry Partner"],
      ["Webinar \"Chiedi all'esperto\"", "Mensile (alternato)", "Partner + ospiti"],
      ["Mastermind group (max 30-50)", "Mensile (60-90 min)", "Industry Partner"],
      ["Casi studio dalla community", "Mensile", "Peer"],
      ["Early access nuove feature", "Ad ogni major release", "Founder"],
      ["Certificazione PT Evoluto", "Annuale", "Industry Partner"],
    ];
    const icTable = [icHdr];
    icRows.forEach((r, idx) => {
      icTable.push(r.map(cell => ({ text: cell, options: { fontSize: 8.5, fontFace: "Calibri", color: C.text, fill: { color: idx % 2 === 0 ? C.white : C.offWhite } } })));
    });
    s.addTable(icTable, { x: 0.8, y: y3 + 0.42, w: 8.5, colW: [4.2, 2.3, 2], border: { pt: 0.5, color: "E2E8F0" }, rowH: new Array(7).fill(0.22) });

    // IC notes
    s.addText([
      { text: "Valore percepito: ~€800-900/anno per €249 (rapporto 3,4:1).", options: { bold: true, breakLine: true } },
      { text: "Attivo dal mese 4. Masterclass partono durante POC per i 10 Fondatori.", options: { breakLine: true } },
    ], { x: 0.8, y: y3 + 2.1, w: 8.5, h: 0.45, fontSize: 8.5, color: C.textMid, fontFace: "Calibri", margin: 0 });

    // Webinar gratuito note
    s.addText([
      { text: "Webinar gratuito mensile: ", options: { bold: true } },
      { text: "strumento di acquisizione (Touch 5 del funnel). Non compete con IC — lo alimenta." },
    ], { x: 0.8, y: y3 + 2.55, w: 8.5, h: 0.3, fontSize: 8.5, color: C.tealDark, fontFace: "Calibri", margin: 0 });

    // --- Livello 4 — Mentorship ---
    const y4 = 4.25;
    s.addShape("rect", { x: 0.5, y: y4, w: 9, h: 0.75, fill: { color: C.white }, shadow: makeCardShadow() });
    s.addShape("rect", { x: 0.5, y: y4, w: 0.08, h: 0.75, fill: { color: C.coral } });
    s.addText("Livello 4 — Mentorship (futuro, Anno 3+, max 15-20)", { x: 0.8, y: y4 + 0.03, w: 6, h: 0.3, fontSize: 13, color: C.coral, fontFace: "Calibri", bold: true, margin: 0 });
    s.addText("€499-599/anno", { x: 7.0, y: y4 + 0.03, w: 2.3, h: 0.3, fontSize: 16, color: C.coral, fontFace: "Georgia", bold: true, align: "right", margin: 0 });
    s.addText("Mentorship 1:1, co-creazione roadmap, eventi in presenza. Da definire con base IC >30 membri.", { x: 0.8, y: y4 + 0.38, w: 8.5, h: 0.3, fontSize: 9, color: C.textMid, fontFace: "Calibri", margin: 0 });

    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // SLIDE 48 — APPENDICE A5: COMMUNITY (3/3) — Proiezione ricavi
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Appendice A5");
    addLightTitle(s, "Community — Proiezione ricavi (scenario base)");

    // Revenue table
    const revHdr = [
      { text: "", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 10 } },
      { text: "Anno 1", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 10, align: "right" } },
      { text: "Anno 2", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 10, align: "right" } },
      { text: "Anno 3", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 10, align: "right" } },
    ];
    const revData = [
      ["Membri PRO (paganti)", "12", "47", "92", false],
      ["Membri Inner Circle", "9", "18", "38", false],
      ["Ricavo PRO", "€950", "€3.700", "€7.300", false],
      ["Ricavo Inner Circle", "€2.250", "€4.500", "€9.500", false],
      ["Totale ricorrente", "€3.200", "€8.200", "€16.800", true],
      ["% del fatturato totale", "19%", "28%", "34%", true],
    ];
    const revTable = [revHdr];
    revData.forEach((r, idx) => {
      const isHighlight = r[4];
      revTable.push([
        { text: r[0], options: { fontSize: 10, fontFace: "Calibri", color: isHighlight ? C.tealDark : C.text, bold: isHighlight, fill: { color: isHighlight ? C.mint : (idx % 2 === 0 ? C.white : C.offWhite) } } },
        { text: r[1], options: { fontSize: 10, fontFace: "Georgia", color: isHighlight ? C.tealDark : C.text, bold: isHighlight, align: "right", fill: { color: isHighlight ? C.mint : (idx % 2 === 0 ? C.white : C.offWhite) } } },
        { text: r[2], options: { fontSize: 10, fontFace: "Georgia", color: isHighlight ? C.tealDark : C.text, bold: isHighlight, align: "right", fill: { color: isHighlight ? C.mint : (idx % 2 === 0 ? C.white : C.offWhite) } } },
        { text: r[3], options: { fontSize: 10, fontFace: "Georgia", color: isHighlight ? C.tealDark : C.text, bold: isHighlight, align: "right", fill: { color: isHighlight ? C.mint : (idx % 2 === 0 ? C.white : C.offWhite) } } },
      ]);
    });
    s.addTable(revTable, { x: 1.0, y: 1.2, w: 8, colW: [3, 1.5, 1.5, 1.5], border: { pt: 0.5, color: "E2E8F0" }, rowH: new Array(7).fill(0.35) });

    // Key insight
    s.addShape("rect", { x: 1.0, y: 3.9, w: 8, h: 0.9, fill: { color: C.white }, shadow: makeCardShadow() });
    s.addShape("rect", { x: 1.0, y: 3.9, w: 0.08, h: 0.9, fill: { color: C.teal } });
    s.addText([
      { text: "Il ricorrente cresce dal 19% al 34% del fatturato in 3 anni.", options: { bold: true, breakLine: true } },
      { text: "Questo è il pavimento che copre i costi operativi e rende il business\nprogressivamente indipendente dalle nuove vendite.", options: {} },
    ], { x: 1.3, y: 3.95, w: 7.5, h: 0.8, fontSize: 11, color: C.text, fontFace: "Calibri", margin: 0 });

    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 47 — APPENDICE A6: PIANO B
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Appendice A6");
    addLightTitle(s, "Piano B senza partner");
    s.addText([
      { text: "POC ridotta a 5 Fondatori", options: { bold: true, breakLine: true } },
      { text: "Reclutati via LinkedIn e community fitness online", options: { breakLine: true } },
      { text: "", options: { breakLine: true } },
      { text: "Go-to-market organico", options: { bold: true, breakLine: true } },
      { text: "Impatto: -40% volume vendite rispetto allo scenario base", options: { breakLine: true } },
      { text: "", options: { breakLine: true } },
      { text: "~24 clienti Anno 1  —  Fatturato ~€7.200", options: { bold: true, breakLine: true } },
      { text: "", options: { breakLine: true } },
      { text: "Il business non genera debito.", options: { bold: true, color: C.tealDark, breakLine: true } },
      { text: "Il partner accelera, non abilita.", options: { bold: true, color: C.tealDark } },
    ], { x: 0.5, y: 1.2, w: 9, h: 3.5, fontSize: 14, color: C.text, fontFace: "Calibri" });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 48 — APPENDICE A7: FISCALE
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Appendice A7");
    addLightTitle(s, "Struttura fiscale");

    s.addShape("rect", { x: 0.5, y: 1.15, w: 4.3, h: 2.8, fill: { color: C.white }, shadow: makeCardShadow() });
    s.addText("ANNI 1-2: FORFETTARIO", { x: 0.7, y: 1.3, w: 3.8, h: 0.25, fontSize: 10, color: C.teal, fontFace: "Calibri", bold: true, charSpacing: 2 });
    s.addText([
      { text: "ATECO 62.10.00", options: { bold: true, breakLine: true } },
      { text: "Coefficiente redditività: 67%", options: { breakLine: true } },
      { text: "IRPEF: 5%  |  INPS: 26%", options: { breakLine: true } },
      { text: "Carico effettivo: ~21% del fatturato", options: { bold: true, breakLine: true } },
      { text: "Limite: €85.000", options: { breakLine: true } },
      { text: "", options: { breakLine: true } },
      { text: "Nota: costi hardware Box non deducibili nel forfettario. Aliquota effettiva Box ~31% vs licenza ~24%.", options: { italic: true } },
    ], { x: 0.7, y: 1.65, w: 3.8, h: 2.2, fontSize: 10, color: C.text, fontFace: "Calibri" });

    s.addShape("rect", { x: 5.2, y: 1.15, w: 4.3, h: 2.8, fill: { color: C.white }, shadow: makeCardShadow() });
    s.addText("ANNO 3+: ORDINARIO / SRL", { x: 5.4, y: 1.3, w: 3.8, h: 0.25, fontSize: 10, color: C.navy, fontFace: "Calibri", bold: true, charSpacing: 2 });
    s.addText([
      { text: "Transizione se fatturato >€30-40K", options: { bold: true, breakLine: true } },
      { text: "Costi deducibili", options: { breakLine: true } },
      { text: "Aliquota effettiva: ~35%", options: { breakLine: true } },
      { text: "", options: { breakLine: true } },
      { text: "Vantaggi:", options: { bold: true, breakLine: true } },
      { text: "Hardware deducibile", options: { bullet: true, breakLine: true } },
      { text: "Costi operativi deducibili", options: { bullet: true, breakLine: true } },
      { text: "Struttura per collaboratori", options: { bullet: true } },
    ], { x: 5.4, y: 1.65, w: 3.8, h: 2.2, fontSize: 10, color: C.text, fontFace: "Calibri" });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 49 — APPENDICE A8: GLOSSARIO
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Appendice A8");
    addLightTitle(s, "Glossario");

    const glossary = [
      ["ATECO", "Classificazione attività economiche italiane"], ["Box", "Dispositivo dedicato basato su Raspberry Pi 5"],
      ["CONI", "Comitato Olimpico Nazionale Italiano"], ["CREA", "Ente tabelle nutrizionali ufficiali italiane"],
      ["Cliff", "Periodo minimo prima che l'equity maturi (12 mesi)"], ["EBITDA", "Utile prima di interessi, tasse e ammortamenti"],
      ["Forfettario", "Regime fiscale agevolato per P.IVA sotto €85K"], ["LARN", "Livelli di Assunzione Riferimento Nutrienti"],
      ["NPS", "Net Promoter Score (-100/+100)"], ["POC", "Proof of Concept — test con 10 utenti"],
      ["PT Evoluto", "Categoria: trainer con scienza + dati + strumenti"], ["Revenue share", "% ricavi condivisa con il partner"],
      ["Safety Engine", "Motore 47 condizioni cliniche"], ["SaaS", "Software as a Service (abbonamento + cloud)"],
      ["Tailscale", "Connessione sicura per accesso remoto"], ["Vesting", "Maturazione progressiva dell'equity"],
      ["WTP", "Willingness to Pay"],
    ];
    const glossHdr = [
      { text: "Termine", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 10 } },
      { text: "Significato", options: { fill: { color: C.teal }, color: C.white, bold: true, fontSize: 10 } },
    ];
    const gt = [glossHdr];
    for (let r = 0; r < glossary.length; r++) {
      gt.push(glossary[r].map((cell, idx) => ({ text: cell, options: { fontSize: 9, fontFace: "Calibri", color: C.text, bold: idx === 0, fill: { color: r % 2 === 0 ? C.white : C.offWhite } } })));
    }
    s.addTable(gt, { x: 0.5, y: 1.1, w: 9, colW: [2, 7], border: { pt: 0.5, color: "E2E8F0" }, rowH: new Array(18).fill(0.24) });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 50 — FATTURATO CHART
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Appendice — Grafici");
    addLightTitle(s, "Fatturato triennale — 3 scenari");
    s.addChart(pres.charts.BAR, [
      { name: "Conservativo", labels: ["Anno 1", "Anno 2", "Anno 3"], values: [10715, 17086, 27441] },
      { name: "Base", labels: ["Anno 1", "Anno 2", "Anno 3"], values: [17150, 29650, 49650] },
      { name: "Ottimistico", labels: ["Anno 1", "Anno 2", "Anno 3"], values: [27973, 49140, 81500] },
    ], {
      x: 0.5, y: 1.2, w: 9, h: 4.0, barDir: "col", barGrouping: "clustered",
      chartColors: [C.textMid, C.teal, C.gold],
      showValue: true, dataLabelPosition: "outEnd", dataLabelColor: C.text, dataLabelFontSize: 8,
      catAxisLabelColor: C.textMid, valAxisLabelColor: C.textMid,
      valGridLine: { color: "E2E8F0", size: 0.5 }, catGridLine: { style: "none" },
      showLegend: true, legendPos: "b", legendFontSize: 10,
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 51 — NETTO FOUNDER CHART
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.cream };
    addSectionLabel(s, "Appendice — Grafici");
    addLightTitle(s, "Netto founder triennale — confronto");
    s.addChart(pres.charts.LINE, [
      { name: "Senza partner", labels: ["Anno 1", "Anno 2", "Anno 3"], values: [-112, 2165, 3600] },
      { name: "Con partner (base)", labels: ["Anno 1", "Anno 2", "Anno 3"], values: [2615, 4895, 12535] },
      { name: "Con partner (ottim.)", labels: ["Anno 1", "Anno 2", "Anno 3"], values: [6549, 12290, 19080] },
    ], {
      x: 0.5, y: 1.2, w: 9, h: 4.0, lineSize: 3, lineSmooth: true,
      chartColors: [C.textMid, C.teal, C.gold],
      showValue: true, dataLabelPosition: "t", dataLabelColor: C.text, dataLabelFontSize: 9,
      catAxisLabelColor: C.textMid, valAxisLabelColor: C.textMid,
      valGridLine: { color: "E2E8F0", size: 0.5 }, catGridLine: { style: "none" },
      showLegend: true, legendPos: "b", legendFontSize: 10,
      showMarker: true, markerSize: 8,
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ══════════════════════════════════════════════════════════════
  // SLIDE 52 — CLOSING
  // ══════════════════════════════════════════════════════════════
  {
    slideNum++;
    const s = pres.addSlide();
    s.background = { color: C.darkBg };
    s.addShape("rect", { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.teal } });
    s.addShape("rect", { x: 0, y: 5.565, w: 10, h: 0.06, fill: { color: C.teal } });

    s.addText("FitManager Studio+", { x: 0.5, y: 1.2, w: 9, h: 0.8, fontSize: 40, color: C.white, fontFace: "Georgia", bold: true, align: "center", margin: 0 });
    s.addText("Il sistema completo per il Personal Trainer Evoluto", { x: 0.5, y: 2.1, w: 9, h: 0.5, fontSize: 16, color: C.tealLight, fontFace: "Calibri", italic: true, align: "center" });
    s.addShape("rect", { x: 3.5, y: 2.8, w: 3, h: 0.04, fill: { color: C.teal } });
    s.addText("Giacomo Verardo", { x: 0.5, y: 3.2, w: 9, h: 0.4, fontSize: 16, color: C.white, fontFace: "Calibri", bold: true, align: "center" });
    s.addText("Business Plan v4.2 — 26 marzo 2026\nConfidenziale", { x: 0.5, y: 3.7, w: 9, h: 0.6, fontSize: 12, color: C.textLight, fontFace: "Calibri", align: "center" });
    s.addText("Il prodotto è completo. La prima utilizzatrice reale lo usa ogni giorno.\nCerchiamo un partner per accelerare — il business parte anche senza.", {
      x: 1, y: 4.4, w: 8, h: 0.8, fontSize: 13, color: C.mint, fontFace: "Calibri", align: "center", italic: true
    });
    addSlideNumber(s, slideNum, TOTAL_SLIDES);
  }

  // ─── WRITE FILE ────────────────────────────────────────────────
  const outputPath = "FitManager_Business_Plan_2026.pptx";
  await pres.writeFile({ fileName: outputPath });
  console.log(`Presentazione generata: ${outputPath} (${slideNum} slide)`);
}

main().catch(err => { console.error("Errore:", err); process.exit(1); });

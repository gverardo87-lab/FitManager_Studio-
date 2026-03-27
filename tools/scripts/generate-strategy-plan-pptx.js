/**
 * FitManager Studio+ — Strategy Plan v3.1 Complete Presentation
 * Generates 47-slide PPTX from STRATEGY_PLAN content
 * Style matched to Business Plan PPTX (dark/light alternating, same palette)
 */

const pptxgen = require("pptxgenjs");

// ─── Color Palette ───────────────────────────────────────────────
const C = {
  darkBg:    "1A1F36",
  darkBg2:   "252B48",
  lightBg:   "F5F6FA",
  white:     "FFFFFF",
  blue:      "3B82F6",
  blueDark:  "2563EB",
  blueLight: "60A5FA",
  bluePale:  "DBEAFE",
  green:     "10B981",
  greenDark: "059669",
  greenPale: "D1FAE5",
  amber:     "F59E0B",
  amberDark: "D97706",
  amberPale: "FEF3C7",
  coral:     "EF4444",
  coralPale: "FEE2E2",
  text:      "1E293B",
  textMid:   "475569",
  textLight: "94A3B8",
  textPale:  "CBD5E1",
};

// ─── Factory helpers (fresh each call — PptxGenJS mutates) ───────
const makeShadow = () => ({ type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.12 });
const makeCardShadow = () => ({ type: "outer", blur: 8, offset: 3, angle: 135, color: "000000", opacity: 0.10 });
const makeBorder = (color) => ({ type: "solid", pt: 1, color: color || C.textPale });

const TOTAL = 47;
let slideNum = 0;

// ─── Reusable slide helpers ──────────────────────────────────────
function addSlideNumber(slide, num) {
  slide.addText(`${num} / ${TOTAL}`, {
    x: 8.5, y: 5.2, w: 1.2, h: 0.3,
    fontSize: 9, color: C.textLight, align: "right", fontFace: "Calibri"
  });
}

function addSectionLabel(slide, label) {
  slide.addText(label.toUpperCase(), {
    x: 0.5, y: 0.2, w: 6, h: 0.3,
    fontSize: 8, color: C.blue, fontFace: "Calibri", bold: true, charSpacing: 3
  });
}

function makeLightSlide(pres, sectionLabel) {
  slideNum++;
  const s = pres.addSlide();
  s.background = { color: C.lightBg };
  if (sectionLabel) addSectionLabel(s, sectionLabel);
  return s;
}

function makeDarkSlide(pres) {
  slideNum++;
  const s = pres.addSlide();
  s.background = { color: C.darkBg };
  // Decorative blue bar left
  s.addShape("rect", { x: 0, y: 0, w: 0.06, h: 5.625, fill: { color: C.blue } });
  return s;
}

function addLightTitle(slide, title, yPos) {
  const y = yPos || 0.45;
  slide.addText(title, {
    x: 0.5, y, w: 9, h: 0.55,
    fontSize: 26, color: C.text, fontFace: "Calibri", bold: true, margin: 0
  });
  slide.addShape("rect", { x: 0.5, y: y + 0.58, w: 1.2, h: 0.04, fill: { color: C.blue } });
}

function addDividerContent(slide, sectionNum, sectionTitle, subtitle) {
  slide.addText(`SEZIONE ${sectionNum}`, {
    x: 0.5, y: 1.0, w: 5, h: 0.35,
    fontSize: 11, color: C.blueLight, fontFace: "Calibri", bold: true, charSpacing: 5
  });
  slide.addText(sectionTitle, {
    x: 0.5, y: 1.8, w: 9, h: 1.0,
    fontSize: 36, color: C.white, fontFace: "Calibri", bold: true, margin: 0
  });
  if (subtitle) {
    slide.addShape("rect", { x: 0.5, y: 3.1, w: 2, h: 0.03, fill: { color: C.blue } });
    slide.addText(subtitle, {
      x: 0.5, y: 3.4, w: 8, h: 0.6,
      fontSize: 14, color: C.textPale, fontFace: "Calibri", italic: true
    });
  }
  // Decorative shapes
  slide.addShape("rect", { x: 8.0, y: 0.3, w: 1.8, h: 1.8, fill: { color: C.blue }, transparency: 90 });
  slide.addShape("rect", { x: 8.5, y: 0.8, w: 1.3, h: 1.3, fill: { color: C.blueLight }, transparency: 92 });
}

function addFooter(slide, text, y) {
  const yPos = y || 5.0;
  slide.addShape("rect", { x: 0.5, y: yPos - 0.05, w: 9, h: 0.03, fill: { color: C.textPale } });
  slide.addText(text, {
    x: 0.5, y: yPos, w: 9, h: 0.3,
    fontSize: 9, color: C.textMid, fontFace: "Calibri", italic: true
  });
}

function addCard(slide, x, y, w, h, accentColor) {
  slide.addShape("roundRect", {
    x, y, w, h, rectRadius: 0.06,
    fill: { color: C.white }, shadow: makeCardShadow()
  });
  if (accentColor) {
    slide.addShape("rect", { x, y, w: 0.06, h, fill: { color: accentColor } });
  }
}

function addStatBox(slide, x, y, w, value, label, bgColor, textColor) {
  slide.addShape("roundRect", {
    x, y, w, h: 0.9, rectRadius: 0.06,
    fill: { color: bgColor || C.bluePale }
  });
  slide.addText(value, {
    x, y, w, h: 0.55,
    fontSize: 22, color: textColor || C.blueDark, fontFace: "Calibri", bold: true, align: "center", margin: 0
  });
  slide.addText(label, {
    x, y: y + 0.5, w, h: 0.35,
    fontSize: 9, color: C.textMid, fontFace: "Calibri", align: "center", margin: 0
  });
}

// Standard table style
function makeTableOpts(x, y, w, extraOpts) {
  return {
    x: x || 0.5, y: y || 1.5, w: w || 9,
    fontSize: 10, fontFace: "Calibri",
    border: { type: "solid", pt: 0.5, color: C.textPale },
    colW: extraOpts?.colW,
    autoPage: false,
    ...extraOpts
  };
}

function headerRow(cells) {
  return cells.map(c => ({
    text: c, options: {
      bold: true, color: C.white, fill: { color: C.darkBg2 },
      fontSize: 10, fontFace: "Calibri", align: "center", valign: "middle"
    }
  }));
}

function dataRow(cells, opts) {
  return cells.map((c, i) => ({
    text: String(c),
    options: {
      color: C.text, fill: { color: (opts?.rowIdx || 0) % 2 === 0 ? C.white : C.lightBg },
      fontSize: 10, fontFace: "Calibri",
      bold: opts?.bold || false,
      align: i === 0 ? "left" : "center",
      valign: "middle",
      ...(opts?.cellOpts?.[i] || {})
    }
  }));
}


// ══════════════════════════════════════════════════════════════════
// MAIN
// ══════════════════════════════════════════════════════════════════
function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Giacomo Verardo";
  pres.title = "FitManager Studio+ — Strategy Plan v3.1";

  // ════════════════════════════════════════════════════════════════
  // SLIDE 1 — Title (dark bg)
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeDarkSlide(pres);
    // Accent bar top
    s.addShape("rect", { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.blue } });
    // Decorative shapes
    s.addShape("rect", { x: 7.5, y: 0.5, w: 2.2, h: 2.2, fill: { color: C.blue }, transparency: 92 });
    s.addShape("rect", { x: 8, y: 1, w: 1.5, h: 1.5, fill: { color: C.blueLight }, transparency: 90 });

    s.addText("STRATEGY PLAN", {
      x: 0.7, y: 0.6, w: 7, h: 0.4,
      fontSize: 11, color: C.blueLight, fontFace: "Calibri", bold: true, charSpacing: 6
    });
    s.addText("FitManager Studio+", {
      x: 0.7, y: 1.5, w: 8, h: 1.0,
      fontSize: 44, color: C.white, fontFace: "Calibri", bold: true, margin: 0
    });
    s.addText("Piano operativo di lancio, category creation e partnership", {
      x: 0.7, y: 2.6, w: 7, h: 0.6,
      fontSize: 18, color: C.blueLight, fontFace: "Calibri", italic: true
    });
    s.addShape("rect", { x: 0.7, y: 3.5, w: 2, h: 0.04, fill: { color: C.blue } });
    s.addText([
      { text: "Versione 3.1 \u2014 27 marzo 2026", options: { breakLine: true, color: C.textLight } },
      { text: "Giacomo Verardo", options: { breakLine: true, color: C.white, bold: true } },
      { text: "Confidenziale", options: { color: C.coral } },
    ], {
      x: 0.7, y: 3.8, w: 5, h: 1.2,
      fontSize: 13, fontFace: "Calibri"
    });
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 2 — Premessa (light bg)
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "Premessa");
    addLightTitle(s, "PREMESSA");

    const items = [
      ["Piano operativo", "Questo documento \u00e8 il piano operativo di FitManager"],
      ["Dal BP alle azioni", "Traduce il Business Plan in azioni concrete"],
      ["Pubblico interno", "Documento interno: lo leggono il founder e il partner"],
      ["Non ripete i numeri", "Non ripete i numeri del BP (referenziati dove servono)"],
      ["Focus", "Si concentra su: strategia di lancio, ruolo del partner, percorso ecosistema PT Evoluto"],
      ["Riferimento", "Business Plan v4.3"],
    ];

    for (let i = 0; i < items.length; i++) {
      const y = 1.3 + i * 0.62;
      addCard(s, 0.5, y, 9, 0.55, C.blue);
      s.addText(items[i][0], {
        x: 0.75, y, w: 2.2, h: 0.55,
        fontSize: 12, color: C.blue, fontFace: "Calibri", bold: true, valign: "middle"
      });
      s.addText(items[i][1], {
        x: 3.0, y, w: 6.3, h: 0.55,
        fontSize: 11, color: C.text, fontFace: "Calibri", valign: "middle"
      });
    }
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 3 — Section divider: Sezione 1
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeDarkSlide(pres);
    addDividerContent(s, 1, "Il progetto oggi \u2014\ne cosa \u00e8 cambiato");
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 4 — Cosa c'è (light bg)
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 1");
    addLightTitle(s, "Cosa c\u2019\u00e8");

    // Big stats row
    const stats = [
      ["v1.0.5", "In uso quotidiano", C.bluePale, C.blueDark],
      ["5", "Motori scientifici", C.greenPale, C.greenDark],
      ["500", "Esercizi", C.amberPale, C.amberDark],
      ["880", "Alimenti CREA", C.bluePale, C.blueDark],
      ["47", "Condizioni\nSafety Engine", C.coralPale, C.coral],
    ];
    for (let i = 0; i < stats.length; i++) {
      const x = 0.3 + i * 1.9;
      addStatBox(s, x, 1.3, 1.7, stats[i][0], stats[i][1], stats[i][2], stats[i][3]);
    }

    // Body text card
    addCard(s, 0.5, 2.6, 9, 1.0, C.green);
    s.addText("Prodotto completo e funzionante. In uso quotidiano dalla prima utilizzatrice reale. Installer pronto, licenza funzionante.", {
      x: 0.8, y: 2.7, w: 8.5, h: 0.8,
      fontSize: 14, color: C.text, fontFace: "Calibri", valign: "middle"
    });
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 5 — Le 4 evoluzioni, part 1
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 1 \u2014 LE 4 EVOLUZIONI");
    addLightTitle(s, "Comunicazione integrata + FitManager Box");

    // LEFT column
    addCard(s, 0.3, 1.3, 4.5, 3.8, C.blue);
    s.addText("La comunicazione integrata", {
      x: 0.55, y: 1.4, w: 4.0, h: 0.35,
      fontSize: 14, color: C.blue, fontFace: "Calibri", bold: true
    });
    const leftItems = [
      "Il trainer vive su WhatsApp \u2014 FitManager si inserisce nel workflow invece di sostituirlo",
      "Un click: messaggio WhatsApp con nome, data, orario, importo pre-compilati",
      "Email automatiche via SMTP: conferme, promemoria, notifiche",
      "Risultato: valore dal primo giorno, zero curva di apprendimento",
      "Risolve il problema della complessit\u00e0 percepita",
    ];
    for (let i = 0; i < leftItems.length; i++) {
      const y = 1.85 + i * 0.6;
      s.addShape("ellipse", { x: 0.6, y: y + 0.08, w: 0.12, h: 0.12, fill: { color: C.blue } });
      s.addText(leftItems[i], {
        x: 0.85, y, w: 3.8, h: 0.55,
        fontSize: 10, color: C.text, fontFace: "Calibri", valign: "top"
      });
    }

    // RIGHT column
    addCard(s, 5.2, 1.3, 4.5, 3.8, C.amber);
    s.addText("La FitManager Box", {
      x: 5.45, y: 1.4, w: 4.0, h: 0.35,
      fontSize: 14, color: C.amberDark, fontFace: "Calibri", bold: true
    });
    const rightItems = [
      "Dispositivo dedicato nello studio del trainer",
      "Accesso da qualunque dispositivo: telefono, tablet, PC",
      "Dati nel suo studio, mai in cloud",
      "Costo: ~\u20AC150 \u2192 Prezzo: \u20AC449 \u2192 Margine: 67%",
      "Trasforma debolezza (offline) in punto di forza",
    ];
    for (let i = 0; i < rightItems.length; i++) {
      const y = 1.85 + i * 0.6;
      s.addShape("ellipse", { x: 5.5, y: y + 0.08, w: 0.12, h: 0.12, fill: { color: C.amber } });
      s.addText(rightItems[i], {
        x: 5.75, y, w: 3.8, h: 0.55,
        fontSize: 10, color: C.text, fontFace: "Calibri", valign: "top"
      });
    }
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 6 — Le 4 evoluzioni, part 2
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 1 \u2014 LE 4 EVOLUZIONI");
    addLightTitle(s, "Ricavo ricorrente + Ecosistema");

    // LEFT column
    addCard(s, 0.3, 1.3, 4.5, 3.8, C.green);
    s.addText("Il modello di ricavo ricorrente", {
      x: 0.55, y: 1.4, w: 4.0, h: 0.35,
      fontSize: 14, color: C.greenDark, fontFace: "Calibri", bold: true
    });
    const leftItems = [
      "Pagamento una tantum resta (leva commerciale pi\u00f9 forte)",
      "Assistenza PRO \u20AC79/anno: aggiornamenti, esercizi, alimenti, template, supporto",
      "Inner Circle \u20AC249/anno: masterclass, webinar, mastermind, certificazione",
      "Ricorrente: dal 19% al 34% del fatturato in 3 anni",
      "Copre progressivamente i costi operativi",
    ];
    for (let i = 0; i < leftItems.length; i++) {
      const y = 1.85 + i * 0.6;
      s.addShape("ellipse", { x: 0.6, y: y + 0.08, w: 0.12, h: 0.12, fill: { color: C.green } });
      s.addText(leftItems[i], {
        x: 0.85, y, w: 3.8, h: 0.55,
        fontSize: 10, color: C.text, fontFace: "Calibri", valign: "top"
      });
    }

    // RIGHT column
    addCard(s, 5.2, 1.3, 4.5, 3.8, C.blue);
    s.addText("L\u2019ecosistema e la community", {
      x: 5.45, y: 1.4, w: 4.0, h: 0.35,
      fontSize: 14, color: C.blue, fontFace: "Calibri", bold: true
    });
    const rightItems = [
      "Percorso professionale completo: formazione, community, certificazione, contenuti",
      "Il software \u00e8 lo strumento operativo",
      "L\u2019ecosistema d\u00e0 valore al software e al professionista",
      "Switching costs, referral, contenuto peer-to-peer",
    ];
    for (let i = 0; i < rightItems.length; i++) {
      const y = 1.85 + i * 0.6;
      s.addShape("ellipse", { x: 5.5, y: y + 0.08, w: 0.12, h: 0.12, fill: { color: C.blue } });
      s.addText(rightItems[i], {
        x: 5.75, y, w: 3.8, h: 0.55,
        fontSize: 10, color: C.text, fontFace: "Calibri", valign: "top"
      });
    }
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 7 — Section divider: Sezione 2
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeDarkSlide(pres);
    addDividerContent(s, 2, "La visione: il Personal\nTrainer Evoluto");
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 8 — Il problema di fondo
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 2");
    addLightTitle(s, "Il problema di fondo");

    const paragraphs = [
      "Il prodotto \u00e8 pronto. Il mercato non lo \u00e8. I PT non cercano un gestionale \u2014 la maggior parte non sa di averne bisogno. Usano WhatsApp ed Excel perch\u00e9 \u2018ha sempre fatto cos\u00ec.\u2019 Non percepiscono il problema.",
      "Per questo FitManager non chiede di smettere di usare WhatsApp. Lo potenzia. Il PT Evoluto non abbandona i suoi strumenti \u2014 li evolve. L\u2019adozione non \u00e8 una rivoluzione spaventosa ma un\u2019evoluzione naturale.",
      "Questo non \u00e8 un limite \u2014 \u00e8 l\u2019opportunit\u00e0 pi\u00f9 grande. Un mercato poco evoluto \u00e8 un mercato dove chi arriva primo e definisce le regole lo possiede.",
    ];
    const colors = [C.blue, C.green, C.amber];

    for (let i = 0; i < paragraphs.length; i++) {
      const y = 1.3 + i * 1.2;
      addCard(s, 0.5, y, 9, 1.05, colors[i]);
      s.addText(paragraphs[i], {
        x: 0.8, y: y + 0.1, w: 8.5, h: 0.85,
        fontSize: 12, color: C.text, fontFace: "Calibri", valign: "middle"
      });
    }
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 9 — La categoria PT Evoluto
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 2");
    addLightTitle(s, "La categoria: PT Evoluto");

    s.addText("Non vendiamo un software. Creiamo una categoria professionale nuova.", {
      x: 0.5, y: 1.15, w: 9, h: 0.4,
      fontSize: 13, color: C.blue, fontFace: "Calibri", italic: true, bold: true
    });

    const blocks = [
      ["01", "Traccia tutto", "Anamnesi, misurazioni, progressione, pagamenti", C.blue],
      ["02", "Usa la scienza", "Periodizzazione evidence-based, volume MEV/MAV/MRV, biomeccanica", C.green],
      ["03", "Protegge i clienti", "47 condizioni, 80 regole automatiche, zero errori evitabili", C.coral],
      ["04", "Scala il business", "40-60 clienti senza perdere qualit\u00e0", C.amber],
      ["05", "Dimostra i risultati", "Report, grafici, score scientifici", C.blueDark],
    ];

    for (let i = 0; i < blocks.length; i++) {
      const y = 1.7 + i * 0.72;
      addCard(s, 0.5, y, 9, 0.65, blocks[i][3]);
      // Number badge
      s.addShape("roundRect", {
        x: 0.7, y: y + 0.1, w: 0.45, h: 0.45, rectRadius: 0.06,
        fill: { color: blocks[i][3] }
      });
      s.addText(blocks[i][0], {
        x: 0.7, y: y + 0.1, w: 0.45, h: 0.45,
        fontSize: 14, color: C.white, fontFace: "Calibri", bold: true, align: "center", valign: "middle"
      });
      s.addText(blocks[i][1], {
        x: 1.35, y, w: 2.5, h: 0.65,
        fontSize: 13, color: C.text, fontFace: "Calibri", bold: true, valign: "middle"
      });
      s.addText(blocks[i][2], {
        x: 3.8, y, w: 5.5, h: 0.65,
        fontSize: 11, color: C.textMid, fontFace: "Calibri", valign: "middle"
      });
    }
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 10 — L'angolo economico
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 2");
    addLightTitle(s, "Il PT Evoluto guadagna di pi\u00f9");

    s.addText("Il PT Evoluto non solo lavora meglio \u2014 giustifica tariffe pi\u00f9 alte.", {
      x: 0.5, y: 1.15, w: 9, h: 0.35,
      fontSize: 13, color: C.text, fontFace: "Calibri", bold: true
    });

    addCard(s, 0.5, 1.6, 9, 1.0, C.green);
    s.addText("Circolo virtuoso: risparmio tempo \u2192 servizio migliore \u2192 qualit\u00e0 visibile \u2192 tariffe pi\u00f9 alte \u2192 pi\u00f9 clienti per passaparola", {
      x: 0.8, y: 1.65, w: 8.5, h: 0.45,
      fontSize: 11, color: C.text, fontFace: "Calibri"
    });
    s.addText("La comunicazione integrata aggiunge: il cliente riceve promemoria professionali, conferme puntuali via WhatsApp. Percepisce un servizio superiore prima ancora di entrare in palestra.", {
      x: 0.8, y: 2.1, w: 8.5, h: 0.45,
      fontSize: 11, color: C.text, fontFace: "Calibri"
    });

    // Big stat
    s.addShape("roundRect", {
      x: 2.5, y: 2.9, w: 5, h: 1.3, rectRadius: 0.1,
      fill: { color: C.greenPale }, shadow: makeShadow()
    });
    s.addText("+\u20AC400/mese", {
      x: 2.5, y: 2.95, w: 5, h: 0.75,
      fontSize: 36, color: C.greenDark, fontFace: "Calibri", bold: true, align: "center"
    });
    s.addText("Aumento tariffa 10-15% (da \u20AC40 a \u20AC45-46) con 20 clienti", {
      x: 2.5, y: 3.65, w: 5, h: 0.45,
      fontSize: 11, color: C.textMid, fontFace: "Calibri", align: "center"
    });

    addFooter(s, "FitManager si ripaga in 30-60 giorni. Non \u2018quanto costa FitManager\u2019 ma \u2018quanto ti costa NON averlo.\u2019", 4.6);
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 11 — Mental coaching
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 2");
    addLightTitle(s, "Il collegamento con il mental coaching");

    const paras = [
      { text: "Il PT Evoluto non \u00e8 solo strumenti e dati. \u00c8 un mindset.", bold: true, color: C.blue },
      { text: "Il coaching lavora sul mindset del professionista. FitManager rende quel mindset operativo: lo traduce in strumenti, dati, risultati misurabili.", bold: false, color: C.text },
      { text: "L\u2019uno senza l\u2019altro \u00e8 incompleto: il mindset senza strumenti resta teoria, gli strumenti senza mindset restano software inutilizzato.", bold: false, color: C.text },
      { text: "L\u2019Inner Circle \u00e8 il luogo dove questi due mondi si incontrano. Il partner non vende software \u2014 guida un percorso di trasformazione che il software rende possibile.", bold: false, color: C.text },
    ];

    for (let i = 0; i < paras.length; i++) {
      const y = 1.3 + i * 1.0;
      const accent = i === 0 ? C.blue : i === 3 ? C.amber : C.textPale;
      addCard(s, 0.5, y, 9, 0.85, accent);
      s.addText(paras[i].text, {
        x: 0.8, y: y + 0.05, w: 8.5, h: 0.75,
        fontSize: 12, color: paras[i].color, fontFace: "Calibri", bold: paras[i].bold, valign: "middle"
      });
    }
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 12 — Section divider: Sezione 3
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeDarkSlide(pres);
    addDividerContent(s, 3, "I primi 90 giorni:\nla Proof of Concept", "Non vendiamo subito. Prima dimostriamo \u2014 il pacchetto completo.");
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 13 — Ruoli nella POC (table)
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 3 \u2014 LA POC");
    addLightTitle(s, "I ruoli nella POC");

    const rows = [
      headerRow(["Attivit\u00e0", "Chi", "Impegno"]),
      dataRow(["Selezione 10 Fondatori dal network", "Partner (con founder)", "3-4 ore"], { rowIdx: 0 }),
      dataRow(["Installazione, setup tecnico e config template WhatsApp", "Founder", "15-20 ore"], { rowIdx: 1 }),
      dataRow(["Check-in bisettimanali con ogni Fondatore", "Founder", "20 ore in 90gg"], { rowIdx: 0 }),
      dataRow(["Masterclass mese 1: \u201cIl Metodo PT Evoluto\u201d", "Partner", "2-3 ore"], { rowIdx: 1 }),
      dataRow(["Webinar mese 2: \u201cLe prime 4 settimane\u201d", "Partner + Founder", "2 ore"], { rowIdx: 0 }),
      dataRow(["Masterclass mese 3: \u201cDa 25 a 45 clienti\u201d", "Partner", "2-3 ore"], { rowIdx: 1 }),
      dataRow(["Sessione di gruppo finale (giorno 90)", "Partner + Founder", "2 ore"], { rowIdx: 0 }),
      dataRow(["Micro-sondaggi e analisi dati", "Founder", "5 ore"], { rowIdx: 1 }),
      dataRow(["Totale partner", "", "~15-20 ore"], { rowIdx: 0, bold: true }),
      dataRow(["Totale founder", "", "~40-45 ore"], { rowIdx: 1, bold: true }),
    ];

    s.addTable(rows, makeTableOpts(0.5, 1.3, 9, { colW: [5.0, 2.0, 2.0] }));
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 14 — Cosa ricevono i Fondatori
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 3");
    addLightTitle(s, "Cosa ricevono i 10 Fondatori");

    s.addText("Software o Box + Inner Circle 12 mesi \u2014 tutto incluso nel prezzo Fondatore", {
      x: 0.5, y: 1.2, w: 9, h: 0.35,
      fontSize: 13, color: C.text, fontFace: "Calibri", bold: true
    });

    // Big stat pair
    addStatBox(s, 1.5, 1.7, 3.0, "\u20AC99", "Licenza software", C.bluePale, C.blueDark);
    addStatBox(s, 5.5, 1.7, 3.0, "\u20AC199", "FitManager Box", C.amberPale, C.amberDark);

    addCard(s, 0.5, 2.9, 9, 0.6, C.green);
    s.addText("Valore reale: \u20AC498-698. Investimento strategico del progetto.", {
      x: 0.8, y: 2.95, w: 8.5, h: 0.5,
      fontSize: 12, color: C.greenDark, fontFace: "Calibri", bold: true, valign: "middle"
    });

    addCard(s, 0.5, 3.65, 9, 0.7, C.blue);
    s.addText("La comunicazione WhatsApp \u00e8 operativa dal giorno dell\u2019installazione. Inserisci un cliente, clicca \u2018manda promemoria\u2019, WhatsApp si apre col messaggio pronto.", {
      x: 0.8, y: 3.7, w: 8.5, h: 0.6,
      fontSize: 11, color: C.text, fontFace: "Calibri", valign: "middle"
    });

    s.addShape("roundRect", {
      x: 2.0, y: 4.5, w: 6.0, h: 0.55, rectRadius: 0.06,
      fill: { color: C.amberPale }
    });
    s.addText("KPI di attivazione: primo messaggio WhatsApp inviato entro 24 ore dall\u2019installazione.", {
      x: 2.0, y: 4.5, w: 6.0, h: 0.55,
      fontSize: 11, color: C.amberDark, fontFace: "Calibri", bold: true, align: "center", valign: "middle"
    });
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 15 — Le 3 masterclass
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 3");
    addLightTitle(s, "Le 3 masterclass durante la POC");

    s.addText("Non sono un accessorio. Sono il test della categoria PT Evoluto.", {
      x: 0.5, y: 1.15, w: 9, h: 0.35,
      fontSize: 12, color: C.blue, fontFace: "Calibri", italic: true, bold: true
    });

    const mc = [
      ["Mese 1", "Il Metodo PT Evoluto: come cambia il tuo lavoro.", "Il partner presenta la visione. Sessione sul mindset professionale.", C.blue],
      ["Mese 2", "Le prime 4 settimane: risultati e domande.", "Sessione pratica, i Fondatori raccontano. I contenuti emergono dalla realt\u00e0.", C.green],
      ["Mese 3", "Da 25 a 45 clienti senza lavorare pi\u00f9 ore.", "Il partner mostra come scala. Si chiude con: \u201cvi riconoscete come PT Evoluti?\u201d", C.amber],
    ];

    for (let i = 0; i < mc.length; i++) {
      const y = 1.65 + i * 1.05;
      addCard(s, 0.5, y, 9, 0.95, mc[i][3]);
      // Month badge
      s.addShape("roundRect", {
        x: 0.7, y: y + 0.2, w: 1.0, h: 0.5, rectRadius: 0.06,
        fill: { color: mc[i][3] }
      });
      s.addText(mc[i][0], {
        x: 0.7, y: y + 0.2, w: 1.0, h: 0.5,
        fontSize: 12, color: C.white, fontFace: "Calibri", bold: true, align: "center", valign: "middle"
      });
      s.addText(mc[i][1], {
        x: 1.9, y: y + 0.05, w: 7.4, h: 0.4,
        fontSize: 12, color: C.text, fontFace: "Calibri", bold: true
      });
      s.addText(mc[i][2], {
        x: 1.9, y: y + 0.45, w: 7.4, h: 0.45,
        fontSize: 10, color: C.textMid, fontFace: "Calibri"
      });
    }

    addFooter(s, "Le 3 sessioni vengono registrate \u2192 nucleo libreria Inner Circle. Partner: 30% revenue share su ogni fruizione.", 4.85);
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 16 — Metriche POC (table)
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 3");
    addLightTitle(s, "Le metriche che decidono tutto");

    const rows = [
      headerRow(["Metrica", "Target", "Cosa valida"]),
      dataRow(["Ore admin risparmiate", "Da 3-5h a <2h", "Il prodotto"], { rowIdx: 0 }),
      dataRow(["Messaggi WA pre-compilati/settimana", "15+", "Adozione comunicazione"], { rowIdx: 1 }),
      dataRow(["Tempo risparmiato comunicazione", "30+ min/giorno", "Valore feature chiave"], { rowIdx: 0 }),
      dataRow(["NPS", "Sopra 50", "Prodotto + percorso"], { rowIdx: 1 }),
      dataRow(["\u201cLo ricomprerei a prezzo pieno\u201d", "8/10 s\u00ec", "Modello economico"], { rowIdx: 0 }),
      dataRow(["\u201cI miei clienti notano differenza\u201d", "5/10 s\u00ec", "Volano PT Evoluto"], { rowIdx: 1 }),
      dataRow(["\u201cMi definirei un PT Evoluto\u201d", "6/10 s\u00ec", "Category creation"], { rowIdx: 0 }),
    ];

    s.addTable(rows, makeTableOpts(0.5, 1.3, 9, { colW: [3.8, 2.2, 3.0] }));

    addFooter(s, "Se i Fondatori usano massicciamente i link wa.me \u2192 WhatsApp \u00e8 il gancio d\u2019adozione. La demo per Early Adopter aprir\u00e0 con il momento WhatsApp.", 4.4);
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 17 — Cosa abbiamo al mese 4
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 3");
    addLightTitle(s, "Cosa abbiamo al mese 4");

    const items = [
      ["10 storie reali con numeri", C.blue],
      ["10 video testimonial", C.green],
      ["3 masterclass registrate", C.amber],
      ["Dati aggregati", C.blueDark],
      ["Una community di 10 che funziona", C.green],
      ["La prova che il PT Evoluto \u00e8 una realt\u00e0 misurabile", C.coral],
    ];

    for (let i = 0; i < items.length; i++) {
      const y = 1.3 + i * 0.6;
      addCard(s, 0.5, y, 9, 0.52, items[i][1]);
      s.addShape("roundRect", {
        x: 0.7, y: y + 0.08, w: 0.36, h: 0.36, rectRadius: 0.06,
        fill: { color: items[i][1] }
      });
      s.addText("\u2713", {
        x: 0.7, y: y + 0.08, w: 0.36, h: 0.36,
        fontSize: 14, color: C.white, fontFace: "Calibri", bold: true, align: "center", valign: "middle"
      });
      s.addText(items[i][0], {
        x: 1.25, y, w: 8.0, h: 0.52,
        fontSize: 13, color: C.text, fontFace: "Calibri", bold: true, valign: "middle"
      });
    }

    addFooter(s, "Non vendiamo \u2018un software.\u2019 Vendiamo: \u2018guarda cosa hanno ottenuto questi 10 in 3 mesi.\u2019", 4.95);
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 18 — Section divider: Sezione 4
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeDarkSlide(pres);
    addDividerContent(s, 4, "Da mese 4 in poi:\nil volano");
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 19 — Mesi 4-6 Early Adopter
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 4");
    addLightTitle(s, "Mesi 4-6 \u2014 Early Adopter con Inner Circle attivo");

    s.addShape("roundRect", {
      x: 0.5, y: 1.2, w: 9, h: 0.55, rectRadius: 0.06,
      fill: { color: C.bluePale }
    });
    s.addText("Il pitch ha un hook concreto: \u2018un click e il promemoria parte su WhatsApp. Vuoi vedere cos\u2019altro fa?\u2019", {
      x: 0.7, y: 1.2, w: 8.6, h: 0.55,
      fontSize: 12, color: C.blueDark, fontFace: "Calibri", bold: true, valign: "middle"
    });

    addCard(s, 0.5, 1.9, 9, 0.55, C.green);
    s.addText("Il Fondatore che mostra questo gesto a un collega \u00e8 il venditore pi\u00f9 efficace \u2014 non vende software, mostra un gesto quotidiano fatto meglio.", {
      x: 0.8, y: 1.95, w: 8.5, h: 0.45,
      fontSize: 11, color: C.text, fontFace: "Calibri", valign: "middle"
    });

    s.addText("Il ritmo:", {
      x: 0.5, y: 2.6, w: 3, h: 0.3,
      fontSize: 13, color: C.text, fontFace: "Calibri", bold: true
    });

    const rhythm = [
      "Webinar gratuito mensile (partner). Tema educativo + demo. Touch 5 del funnel.",
      "Inner Circle attivo: masterclass esclusiva, mastermind, contenuti POC",
      "Vendite da: referral Fondatori (2-3 ciascuno), network partner, webinar, LinkedIn",
    ];
    for (let i = 0; i < rhythm.length; i++) {
      const y = 2.95 + i * 0.5;
      s.addShape("ellipse", { x: 0.7, y: y + 0.1, w: 0.12, h: 0.12, fill: { color: C.blue } });
      s.addText(rhythm[i], {
        x: 1.0, y, w: 8.5, h: 0.45,
        fontSize: 11, color: C.text, fontFace: "Calibri", valign: "middle"
      });
    }

    s.addShape("roundRect", {
      x: 2.5, y: 4.5, w: 5, h: 0.55, rectRadius: 0.06,
      fill: { color: C.amberPale }
    });
    s.addText("Target: 15-20 clienti, 30% con Inner Circle", {
      x: 2.5, y: 4.5, w: 5, h: 0.55,
      fontSize: 12, color: C.amberDark, fontFace: "Calibri", bold: true, align: "center", valign: "middle"
    });
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 20 — Mesi 7-12
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 4");
    addLightTitle(s, "Mesi 7-12 \u2014 Prezzo pieno e scala");

    s.addText("Tutti i canali attivi. Target: 3-5 vendite/mese.", {
      x: 0.5, y: 1.15, w: 9, h: 0.35,
      fontSize: 13, color: C.blue, fontFace: "Calibri", bold: true
    });

    s.addText("Calendario mensile tipo", {
      x: 0.5, y: 1.55, w: 4, h: 0.3,
      fontSize: 11, color: C.textMid, fontFace: "Calibri", italic: true
    });

    const rows = [
      headerRow(["Settimana", "Contenuto", "Pubblico", "Conduce"]),
      dataRow(["1", "Webinar gratuito (educativo + demo)", "Tutti", "Partner"], { rowIdx: 0 }),
      dataRow(["2", "Masterclass esclusiva Inner Circle", "Solo IC", "Partner"], { rowIdx: 1 }),
      dataRow(["3", "Template + aggiornamento catalogo", "PRO + IC", "Founder"], { rowIdx: 0 }),
      dataRow(["4", "Mastermind group", "Solo IC", "Partner"], { rowIdx: 1 }),
    ];

    s.addTable(rows, makeTableOpts(0.5, 1.9, 9, { colW: [1.2, 3.8, 2.0, 2.0] }));
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 21 — Il volano completo
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 4");
    addLightTitle(s, "Il volano completo");

    s.addText("Il meccanismo \u00e8 circolare e si autoalimenta:", {
      x: 0.5, y: 1.15, w: 9, h: 0.3,
      fontSize: 12, color: C.text, fontFace: "Calibri", italic: true
    });

    // Flow steps as connected boxes
    const steps = [
      "Partner\nwebinar", "PT vedono\nvalore", "Comprano", "Primo giorno:\nWA promemoria",
      "Capiscono\nil valore", "Scoprono\nil resto", "Inner\nCircle", "Masterclass\nli trasformano",
      "Clienti notano\ndifferenza", "Colleghi\nchiedono", "Tornano al\nwebinar"
    ];
    const stepColors = [C.blue, C.blue, C.green, C.amber, C.green, C.blue, C.amber, C.blue, C.green, C.amber, C.blue];

    // Arrange in a flow: 4 across top, 3 across middle, 4 across bottom
    const rows_layout = [
      { start: 0, count: 4, y: 1.55 },
      { start: 4, count: 3, y: 2.65 },
      { start: 7, count: 4, y: 3.75 },
    ];

    for (const row of rows_layout) {
      const totalW = row.count * 2.0 + (row.count - 1) * 0.15;
      const startX = (10 - totalW) / 2;
      for (let i = 0; i < row.count; i++) {
        const idx = row.start + i;
        const x = startX + i * 2.15;
        s.addShape("roundRect", {
          x, y: row.y, w: 2.0, h: 0.85, rectRadius: 0.08,
          fill: { color: stepColors[idx] }, shadow: makeShadow()
        });
        s.addText(steps[idx], {
          x, y: row.y, w: 2.0, h: 0.85,
          fontSize: 9, color: C.white, fontFace: "Calibri", bold: true,
          align: "center", valign: "middle"
        });
        // Arrow to next (within same row)
        if (i < row.count - 1) {
          s.addText("\u2192", {
            x: x + 1.85, y: row.y + 0.2, w: 0.45, h: 0.45,
            fontSize: 16, color: C.textMid, fontFace: "Calibri", align: "center", valign: "middle"
          });
        }
      }
    }
    // Down arrows between rows
    s.addText("\u2193", { x: 7.6, y: 2.4, w: 0.5, h: 0.3, fontSize: 16, color: C.textMid, align: "center" });
    s.addText("\u2193", { x: 7.2, y: 3.5, w: 0.5, h: 0.3, fontSize: 16, color: C.textMid, align: "center" });

    addFooter(s, "WhatsApp \u00e8 il primo ingranaggio del volano dopo l\u2019acquisto. Ogni giro rafforza il precedente. Il punto critico \u00e8 il primo giro \u2014 la POC.", 4.85);
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 22 — Section divider: Sezione 5
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeDarkSlide(pres);
    addDividerContent(s, 5, "La community come\nmotore di continuit\u00e0");
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 23 — I 4 livelli
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 5");
    addLightTitle(s, "I quattro livelli della community");

    const levels = [
      ["Base", "\u20AC0, inclusa", "Forum, knowledge base, networking, onboarding guidato", C.textMid, C.lightBg],
      ["PRO", "\u20AC79/anno", "Aggiornamenti, esercizi, alimenti, template, supporto. Rapporto 3,8:1", C.blue, C.bluePale],
      ["Inner Circle", "\u20AC249/anno", "PRO + masterclass, webinar, mastermind, certificazione. Rapporto 3,4:1", C.amber, C.amberPale],
      ["Mentorship", "\u20AC499-599, futuro Anno 3+, max 15-20", "1:1, roadmap, eventi in presenza", C.greenDark, C.greenPale],
    ];

    for (let i = 0; i < levels.length; i++) {
      const y = 1.3 + i * 1.0;
      // Card background
      s.addShape("roundRect", {
        x: 0.5, y, w: 9, h: 0.9, rectRadius: 0.06,
        fill: { color: levels[i][4] }, shadow: makeCardShadow()
      });
      s.addShape("rect", { x: 0.5, y, w: 0.06, h: 0.9, fill: { color: levels[i][3] } });
      // Level name badge
      s.addShape("roundRect", {
        x: 0.7, y: y + 0.15, w: 1.5, h: 0.35, rectRadius: 0.04,
        fill: { color: levels[i][3] }
      });
      s.addText(levels[i][0], {
        x: 0.7, y: y + 0.15, w: 1.5, h: 0.35,
        fontSize: 11, color: C.white, fontFace: "Calibri", bold: true, align: "center", valign: "middle"
      });
      s.addText(levels[i][1], {
        x: 0.7, y: y + 0.52, w: 1.5, h: 0.3,
        fontSize: 9, color: levels[i][3], fontFace: "Calibri", bold: true, align: "center"
      });
      s.addText(levels[i][2], {
        x: 2.4, y, w: 6.9, h: 0.9,
        fontSize: 11, color: C.text, fontFace: "Calibri", valign: "middle"
      });
    }
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 24 — Ruolo partner + certificazione
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 5");
    addLightTitle(s, "Il ruolo del partner e la certificazione");

    // LEFT column
    addCard(s, 0.3, 1.3, 4.5, 3.5, C.blue);
    s.addText("Il partner \u00e8 il cuore dell\u2019Inner Circle", {
      x: 0.55, y: 1.4, w: 4.0, h: 0.35,
      fontSize: 13, color: C.blue, fontFace: "Calibri", bold: true
    });
    const leftItems = [
      "Conduce masterclass, facilita mastermind, porta ospiti, definisce certificazione",
      "Un\u2019ora di masterclass \u2192 5-10 asset marketing",
      "Contenuto ha 3 vite: live, registrazione, derivato",
    ];
    for (let i = 0; i < leftItems.length; i++) {
      const y = 1.9 + i * 0.7;
      s.addShape("ellipse", { x: 0.6, y: y + 0.1, w: 0.12, h: 0.12, fill: { color: C.blue } });
      s.addText(leftItems[i], {
        x: 0.85, y, w: 3.8, h: 0.6,
        fontSize: 10, color: C.text, fontFace: "Calibri", valign: "top"
      });
    }

    // RIGHT column
    addCard(s, 5.2, 1.3, 4.5, 3.5, C.amber);
    s.addText("La certificazione PT Evoluto", {
      x: 5.45, y: 1.4, w: 4.0, h: 0.35,
      fontSize: 13, color: C.amberDark, fontFace: "Calibri", bold: true
    });
    const rightItems = [
      "12 masterclass + assessment pratico + badge verificabile",
      "Per il PT: differenziazione e tariffe pi\u00f9 alte",
      "Per FitManager: lock-in",
      "Possibile dall\u2019Anno 2, annunciata dal mese 1",
    ];
    for (let i = 0; i < rightItems.length; i++) {
      const y = 1.9 + i * 0.6;
      s.addShape("ellipse", { x: 5.5, y: y + 0.1, w: 0.12, h: 0.12, fill: { color: C.amber } });
      s.addText(rightItems[i], {
        x: 5.75, y, w: 3.8, h: 0.55,
        fontSize: 10, color: C.text, fontFace: "Calibri", valign: "top"
      });
    }
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 25 — Proiezione ricavi community (table)
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 5");
    addLightTitle(s, "Proiezione ricavi community (scenario base)");

    const rows = [
      headerRow(["", "Anno 1", "Anno 2", "Anno 3"]),
      dataRow(["Membri PRO (paganti)", "12", "47", "92"], { rowIdx: 0 }),
      dataRow(["Membri Inner Circle", "9", "18", "38"], { rowIdx: 1 }),
      dataRow(["Ricavo PRO", "\u20AC950", "\u20AC3.700", "\u20AC7.300"], { rowIdx: 0 }),
      dataRow(["Ricavo Inner Circle", "\u20AC2.250", "\u20AC4.500", "\u20AC9.500"], { rowIdx: 1 }),
      dataRow(["Totale ricorrente", "\u20AC3.200", "\u20AC8.200", "\u20AC16.800"], { rowIdx: 0, bold: true }),
      dataRow(["% del fatturato", "19%", "28%", "34%"], { rowIdx: 1, bold: true }),
    ];

    s.addTable(rows, makeTableOpts(0.5, 1.3, 9, { colW: [3.5, 1.8, 1.8, 1.9] }));

    addFooter(s, "Il ricorrente cresce e copre progressivamente i costi operativi.");
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 26 — Section divider: Sezione 6
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeDarkSlide(pres);
    addDividerContent(s, 6, "Cosa cambia con il partner:\ni 3 scenari");
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 27 — Scenario 1 Founder solo
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 6");
    addLightTitle(s, "Scenario 1 \u2014 Founder solo");

    addCard(s, 0.5, 1.2, 9, 0.55, C.coral);
    s.addText("Il business sta in piedi. Crescita lenta. Nessun Inner Circle. Il concept PT Evoluto resta un\u2019idea.", {
      x: 0.8, y: 1.25, w: 8.5, h: 0.45,
      fontSize: 12, color: C.text, fontFace: "Calibri", valign: "middle"
    });

    const rows = [
      headerRow(["", "Anno 1", "Anno 2", "Anno 3"]),
      dataRow(["Clienti", "24", "58", "108"], { rowIdx: 0 }),
      dataRow(["Fatturato", "\u20AC7.200", "\u20AC13.500", "\u20AC22.000"], { rowIdx: 1 }),
      dataRow(["Netto founder", "-\u20AC112", "\u20AC2.165", "\u20AC3.600"], { rowIdx: 0, bold: true }),
    ];

    s.addTable(rows, makeTableOpts(0.5, 2.0, 9, { colW: [3.5, 1.8, 1.8, 1.9] }));
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 28 — Scenario 2 Con partner
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 6");
    addLightTitle(s, "Scenario 2 \u2014 Founder + Partner");

    addCard(s, 0.5, 1.2, 9, 0.55, C.green);
    s.addText("Network, credibilit\u00e0, masterclass. Inner Circle dal mese 4. Community dalla POC. PT Evoluto inizia a vivere.", {
      x: 0.8, y: 1.25, w: 8.5, h: 0.45,
      fontSize: 12, color: C.text, fontFace: "Calibri", valign: "middle"
    });

    const rows = [
      headerRow(["", "Anno 1", "Anno 2", "Anno 3"]),
      dataRow(["Clienti", "46", "104", "191"], { rowIdx: 0 }),
      dataRow(["Di cui Inner Circle", "9", "18", "38"], { rowIdx: 1 }),
      dataRow(["Fatturato", "\u20AC17.150", "\u20AC29.650", "\u20AC49.650"], { rowIdx: 0, bold: true }),
      dataRow(["Netto founder", "\u20AC2.615", "\u20AC4.895", "\u20AC12.535"], { rowIdx: 1 }),
      dataRow(["Netto partner (cash)", "\u20AC2.375", "\u20AC4.200", "\u20AC7.500"], { rowIdx: 0, bold: true }),
    ];

    s.addTable(rows, makeTableOpts(0.5, 2.0, 9, { colW: [3.5, 1.8, 1.8, 1.9] }));
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 29 — Scenario 3 Con leva
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 6");
    addLightTitle(s, "Scenario 3 \u2014 Partner con leva network alto");

    addCard(s, 0.5, 1.2, 9, 0.7, C.amber);
    s.addText("Il partner apre porte a catene di palestre, enti di formazione. Un centro con 30 trainer dove 30% adotta = 9 vendite. La certificazione diventa credenziale citata.", {
      x: 0.8, y: 1.25, w: 8.5, h: 0.6,
      fontSize: 11, color: C.text, fontFace: "Calibri", valign: "middle"
    });

    const rows = [
      headerRow(["", "Anno 1", "Anno 2", "Anno 3"]),
      dataRow(["Clienti", "80-120", "200-300", "400-600+"], { rowIdx: 0 }),
      dataRow(["Inner Circle", "20-30", "50-80", "100-150"], { rowIdx: 1 }),
      dataRow(["Fatturato", "\u20AC35-50K", "\u20AC80-120K", "\u20AC150-250K+"], { rowIdx: 0, bold: true }),
      dataRow(["Partner cash", "\u20AC6-9K", "\u20AC15-25K", "\u20AC30-50K+"], { rowIdx: 1, bold: true }),
    ];

    s.addTable(rows, makeTableOpts(0.5, 2.1, 9, { colW: [3.5, 1.8, 1.8, 1.9] }));

    addFooter(s, "A questi volumi, FitManager \u00e8 un\u2019azienda con team e brand riconosciuto.", 4.2);
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 30 — Confronto visivo (table)
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 6");
    addLightTitle(s, "Il confronto visivo");

    const rows = [
      headerRow(["", "Solo", "Con partner", "Con leva"]),
      dataRow(["Inner Circle possibile", "No", "S\u00ec", "S\u00ec, su scala"], { rowIdx: 0 }),
      dataRow(["PT Evoluto nel mercato", "Teoria", "Inizia a vivere", "Standard di settore"], { rowIdx: 1 }),
      dataRow(["Community", "Non parte", "Parte dalla POC", "Hub del settore"], { rowIdx: 0 }),
      dataRow(["Fatturato Anno 3", "\u20AC22.000", "\u20AC49.650", "\u20AC150-250K"], { rowIdx: 1, bold: true }),
      dataRow(["Partner cash Anno 3", "\u20AC0", "\u20AC7.500", "\u20AC30-50K"], { rowIdx: 0, bold: true }),
    ];

    s.addTable(rows, makeTableOpts(0.5, 1.3, 9, { colW: [2.8, 2.0, 2.2, 2.0] }));

    addFooter(s, "La differenza tra Scenario 2 e 3 \u00e8 esponenziale. Dipende da quanto network il partner pu\u00f2 attivare.", 4.2);
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 31 — Section divider: Sezione 7
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeDarkSlide(pres);
    addDividerContent(s, 7, "La proposta economica");
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 32 — Struttura compenso (table)
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 7");
    addLightTitle(s, "Struttura del compenso");

    const rows = [
      headerRow(["Componente", "%", "Su cosa", "Logica"]),
      dataRow(["Ricavi POC", "25%", "Licenze e Box Fondatori", "Co-seleziona e co-conduce"], { rowIdx: 0 }),
      dataRow(["Vendite da network", "20%", "Licenza/Box da referral", "Apre la porta"], { rowIdx: 1 }),
      dataRow(["PRO + Inner Circle", "25%", "Rinnovi e abbonamenti", "Crea il contenuto"], { rowIdx: 0 }),
      dataRow(["Masterclass condotte", "30%", "Sessioni live e registrate", "Autore e volto"], { rowIdx: 1 }),
      dataRow(["Equity", "5-8%", "Valore del progetto", "4 anni, cliff 12 mesi"], { rowIdx: 0 }),
    ];

    s.addTable(rows, makeTableOpts(0.5, 1.3, 9, { colW: [2.5, 0.8, 2.8, 2.9] }));

    addFooter(s, "Zero costo fisso. Il partner guadagna solo se il progetto genera ricavi.", 4.0);
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 33 — Proiezione guadagno partner
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 7");
    addLightTitle(s, "Proiezione guadagno partner");

    // LEFT table — Scenario base
    s.addText("Scenario base (BP v4.3)", {
      x: 0.3, y: 1.2, w: 4.5, h: 0.3,
      fontSize: 12, color: C.blue, fontFace: "Calibri", bold: true
    });

    const rowsL = [
      headerRow(["", "Anno 1", "Anno 2", "Anno 3", "Cum."]),
      dataRow(["Cash", "\u20AC2.375", "\u20AC4.200", "\u20AC7.500", "\u20AC14.075"], { rowIdx: 0 }),
      dataRow(["Equity (6%)", "\u20AC1.600", "\u20AC4.100", "\u20AC8.400", "\u2014"], { rowIdx: 1 }),
      dataRow(["Totale", "\u20AC3.975", "\u20AC8.300", "\u20AC15.900", "\u20AC28.175"], { rowIdx: 0, bold: true }),
    ];
    s.addTable(rowsL, makeTableOpts(0.3, 1.55, 4.5, { colW: [1.1, 0.85, 0.85, 0.85, 0.85], fontSize: 9 }));

    // RIGHT table — Scenario con leva
    s.addText("Scenario con leva network", {
      x: 5.2, y: 1.2, w: 4.5, h: 0.3,
      fontSize: 12, color: C.amber, fontFace: "Calibri", bold: true
    });

    const rowsR = [
      headerRow(["", "Anno 1", "Anno 2", "Anno 3", "Cum."]),
      dataRow(["Cash", "\u20AC6-9K", "\u20AC15-25K", "\u20AC30-50K", "\u20AC51-84K"], { rowIdx: 0 }),
      dataRow(["Equity", "\u20AC3-5K", "\u20AC10-18K", "\u20AC25-45K", "\u2014"], { rowIdx: 1 }),
    ];
    s.addTable(rowsR, makeTableOpts(5.2, 1.55, 4.5, { colW: [1.1, 0.85, 0.85, 0.85, 0.85], fontSize: 9 }));
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 34 — Masterclass come asset + investimento
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 7");
    addLightTitle(s, "Le masterclass come asset + investimento del partner");

    // LEFT column
    addCard(s, 0.3, 1.3, 4.5, 2.2, C.green);
    s.addText("Asset a ricavo perpetuo", {
      x: 0.55, y: 1.4, w: 4.0, h: 0.35,
      fontSize: 13, color: C.greenDark, fontFace: "Calibri", bold: true
    });
    const leftItems = [
      "Registrazioni in libreria IC \u2192 30% revenue share",
      "38 membri IC Anno 3 \u2192 \u20AC50-80/anno per masterclass",
      "20 masterclass = \u20AC1.000-1.600/anno ricavo passivo",
    ];
    for (let i = 0; i < leftItems.length; i++) {
      const y = 1.85 + i * 0.5;
      s.addShape("ellipse", { x: 0.6, y: y + 0.08, w: 0.12, h: 0.12, fill: { color: C.green } });
      s.addText(leftItems[i], {
        x: 0.85, y, w: 3.8, h: 0.45,
        fontSize: 10, color: C.text, fontFace: "Calibri", valign: "top"
      });
    }

    // RIGHT column — Investment table
    addCard(s, 5.2, 1.3, 4.5, 2.8, C.blue);
    s.addText("Investimento Anno 1", {
      x: 5.45, y: 1.4, w: 4.0, h: 0.35,
      fontSize: 13, color: C.blue, fontFace: "Calibri", bold: true
    });

    const invRows = [
      headerRow(["Voce", "Ore"]),
      dataRow(["Selezione Fondatori", "3-4"], { rowIdx: 0 }),
      dataRow(["3 masterclass POC", "6-9"], { rowIdx: 1 }),
      dataRow(["Webinar gratuiti (9 mesi)", "18-27"], { rowIdx: 0 }),
      dataRow(["Masterclass IC (6 mesi)", "12-18"], { rowIdx: 1 }),
      dataRow(["Mastermind IC (6 mesi)", "6-9"], { rowIdx: 0 }),
      dataRow(["Rete e referral", "20-30"], { rowIdx: 1 }),
      dataRow(["Totale", "~80-110 (~8-10/mese)"], { rowIdx: 0, bold: true }),
    ];
    s.addTable(invRows, makeTableOpts(5.35, 1.8, 4.2, { colW: [2.6, 1.6], fontSize: 9 }));

    addFooter(s, "In cambio di 8-10 ore/mese: \u20AC2.375-9.000 cash Anno 1, equity in crescita, asset di contenuto ricorrente.", 4.5);
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 35 — Section divider: Sezione 8
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeDarkSlide(pres);
    addDividerContent(s, 8, "Il piano marketing\noperativo");
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 36 — Pre-lancio
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 8");
    addLightTitle(s, "Pre-lancio (4 settimane prima della POC)");

    // LEFT — Asset table
    s.addText("Asset da creare (founder)", {
      x: 0.3, y: 1.2, w: 4.5, h: 0.3,
      fontSize: 12, color: C.blue, fontFace: "Calibri", bold: true
    });

    const assetRows = [
      headerRow(["Asset", "Priorit\u00e0", "Tempo"]),
      dataRow(["Landing page + waiting list", "Critico", "1 sett."], { rowIdx: 0 }),
      dataRow(["Referral virale waiting list", "Critico", "2 ore"], { rowIdx: 1 }),
      dataRow(["Video teaser 60 secondi", "Alto", "4 ore"], { rowIdx: 0 }),
      dataRow(["LinkedIn attivo (2-3 post/sett)", "Alto", "1h/sett"], { rowIdx: 1 }),
      dataRow(["6 screenshot professionali", "Medio", "2 ore"], { rowIdx: 0 }),
    ];
    s.addTable(assetRows, makeTableOpts(0.3, 1.5, 4.6, { colW: [2.5, 1.0, 1.1], fontSize: 9 }));

    // RIGHT — Azioni del partner
    addCard(s, 5.2, 1.2, 4.5, 2.8, C.amber);
    s.addText("Azioni del partner", {
      x: 5.45, y: 1.3, w: 4.0, h: 0.35,
      fontSize: 12, color: C.amberDark, fontFace: "Calibri", bold: true
    });
    const rightItems = [
      "Condividere video teaser nel network",
      "Identificare i 10 Fondatori",
      "Parlare di PT Evoluto nei suoi canali",
      "Non vendere \u2014 seminare",
    ];
    for (let i = 0; i < rightItems.length; i++) {
      const y = 1.8 + i * 0.55;
      s.addShape("ellipse", { x: 5.5, y: y + 0.08, w: 0.12, h: 0.12, fill: { color: C.amber } });
      s.addText(rightItems[i], {
        x: 5.75, y, w: 3.8, h: 0.45,
        fontSize: 10, color: C.text, fontFace: "Calibri", valign: "top"
      });
    }

    s.addShape("roundRect", {
      x: 5.2, y: 4.0, w: 4.5, h: 0.45, rectRadius: 0.06,
      fill: { color: C.amberPale }
    });
    s.addText("Target: 50+ iscritti waiting list", {
      x: 5.2, y: 4.0, w: 4.5, h: 0.45,
      fontSize: 11, color: C.amberDark, fontFace: "Calibri", bold: true, align: "center", valign: "middle"
    });
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 37 — Marketing durante POC
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 8");
    addLightTitle(s, "Durante la POC (mesi 1-3)");

    s.addText("Marketing interno \u2014 focalizzato sui 10 Fondatori. Ma genera materiale per il futuro.", {
      x: 0.5, y: 1.15, w: 9, h: 0.35,
      fontSize: 12, color: C.textMid, fontFace: "Calibri", italic: true
    });

    const blocks = [
      {
        title: "Customer language mining",
        text: "Annotare frasi esatte dei Fondatori. \u201cFinalmente so chi ha pagato senza aprire Excel.\u201d Annotare specificamente reazioni WhatsApp: \u201cnon devo pi\u00f9 riscrivere il messaggio\u201d sono gli asset di copy pi\u00f9 potenti.",
        color: C.blue
      },
      {
        title: "Behind-the-scenes",
        text: "Post LinkedIn settimanali: \u201cSettimana 3 della POC, ecco cosa stiamo scoprendo...\u201d Autentico, non promozionale.",
        color: C.green
      },
      {
        title: "Powered-by",
        text: "10 trainer \u00d7 15 clienti = 150 esposizioni/mese a costo zero nel portale anamnesi.",
        color: C.amber
      },
    ];

    for (let i = 0; i < blocks.length; i++) {
      const y = 1.6 + i * 1.1;
      addCard(s, 0.5, y, 9, 1.0, blocks[i].color);
      s.addShape("roundRect", {
        x: 0.7, y: y + 0.15, w: 2.5, h: 0.3, rectRadius: 0.04,
        fill: { color: blocks[i].color }
      });
      s.addText(blocks[i].title, {
        x: 0.7, y: y + 0.15, w: 2.5, h: 0.3,
        fontSize: 10, color: C.white, fontFace: "Calibri", bold: true, align: "center", valign: "middle"
      });
      s.addText(blocks[i].text, {
        x: 0.7, y: y + 0.5, w: 8.5, h: 0.45,
        fontSize: 10, color: C.text, fontFace: "Calibri"
      });
    }
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 38 — Marketing mesi 4-6
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 8");
    addLightTitle(s, "Mesi 4-6 \u2014 Early Adopter");

    s.addText("Da ogni Fondatore, 6 asset:", {
      x: 0.5, y: 1.15, w: 5, h: 0.3,
      fontSize: 12, color: C.text, fontFace: "Calibri", bold: true
    });

    const assets = [
      "Pagina caso studio (problema \u2192 soluzione \u2192 numeri)",
      "Video 60 secondi (racconto in prima persona)",
      "3 post LinkedIn",
      "1 email sequenza nurturing",
      "1 dato pagina \u201crisultati aggregati\u201d",
      "Screenshot/screen recording WhatsApp pre-compilato in azione",
    ];
    for (let i = 0; i < assets.length; i++) {
      const y = 1.5 + i * 0.38;
      s.addShape("roundRect", {
        x: 0.6, y: y + 0.05, w: 0.28, h: 0.28, rectRadius: 0.04,
        fill: { color: C.blue }
      });
      s.addText(String(i + 1), {
        x: 0.6, y: y + 0.05, w: 0.28, h: 0.28,
        fontSize: 10, color: C.white, fontFace: "Calibri", bold: true, align: "center", valign: "middle"
      });
      s.addText(assets[i], {
        x: 1.05, y, w: 8.5, h: 0.35,
        fontSize: 10, color: C.text, fontFace: "Calibri", valign: "middle"
      });
    }

    // Additional items
    const extras = [
      ["Pagine confronto competitor", "(FitManager vs Mangofit/EvolutionFit/Excel). SEO keyword.", C.green],
      ["Webinar gratuito mensile", "20-30 partecipanti, 15-25% conversione demo.", C.amber],
      ["Blog SEO 1 post/settimana", "10-15 post per dominare SERP long-tail.", C.blue],
    ];
    for (let i = 0; i < extras.length; i++) {
      const y = 3.9 + i * 0.5;
      s.addShape("ellipse", { x: 0.7, y: y + 0.1, w: 0.12, h: 0.12, fill: { color: extras[i][2] } });
      s.addText(extras[i][0], {
        x: 0.95, y, w: 3.0, h: 0.4,
        fontSize: 10, color: C.text, fontFace: "Calibri", bold: true, valign: "middle"
      });
      s.addText(extras[i][1], {
        x: 4.0, y, w: 5.5, h: 0.4,
        fontSize: 10, color: C.textMid, fontFace: "Calibri", valign: "middle"
      });
    }
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 39 — Marketing mesi 7-12
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 8");
    addLightTitle(s, "Mesi 7-12 \u2014 Prezzo pieno");

    const blocks = [
      {
        title: "Comment marketing",
        text: "15 min/giorno nei gruppi Facebook/LinkedIn. Valore, non spam.",
        color: C.blue
      },
      {
        title: "Calcolatore ROI",
        text: "\u201cQuanto ti costa Excel?\u201d + dimensione WhatsApp: \u201cQuanti messaggi WA/giorno \u00d7 3 min = ore perse\u201d",
        color: C.green
      },
      {
        title: "Podcast tour",
        text: "Partner ospite su podcast fitness. 1 episodio/mese. 50-100 visite.",
        color: C.amber
      },
      {
        title: "Programma affiliato",
        text: "Link personale. Per ogni vendita: 3 mesi PRO gratis.",
        color: C.blueDark
      },
    ];

    for (let i = 0; i < blocks.length; i++) {
      const y = 1.3 + i * 0.95;
      addCard(s, 0.5, y, 9, 0.85, blocks[i].color);
      s.addShape("roundRect", {
        x: 0.7, y: y + 0.2, w: 2.2, h: 0.35, rectRadius: 0.04,
        fill: { color: blocks[i].color }
      });
      s.addText(blocks[i].title, {
        x: 0.7, y: y + 0.2, w: 2.2, h: 0.35,
        fontSize: 11, color: C.white, fontFace: "Calibri", bold: true, align: "center", valign: "middle"
      });
      s.addText(blocks[i].text, {
        x: 3.1, y, w: 6.2, h: 0.85,
        fontSize: 11, color: C.text, fontFace: "Calibri", valign: "middle"
      });
    }
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 40 — Budget marketing (table)
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 8");
    addLightTitle(s, "Budget marketing Anno 1");

    const rows = [
      headerRow(["Voce", "Importo"]),
      dataRow(["Dominio + hosting", "\u20AC120"], { rowIdx: 0 }),
      dataRow(["Email marketing", "\u20AC0-180"], { rowIdx: 1 }),
      dataRow(["Video demo/testimonial", "\u20AC0-80"], { rowIdx: 0 }),
      dataRow(["Ads (mesi 7-12)", "\u20AC0-500"], { rowIdx: 1 }),
      dataRow(["Totale", "\u20AC120-880"], { rowIdx: 0, bold: true }),
    ];

    s.addTable(rows, makeTableOpts(1.5, 1.3, 7, { colW: [4.0, 3.0] }));

    addFooter(s, "Quasi interamente organico. Il marketing a pagamento parte solo quando la social proof \u00e8 consolidata.", 4.0);
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 41 — Section divider: Sezione 9
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeDarkSlide(pres);
    addDividerContent(s, 9, "Rischi e risposte");
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 42 — Rischi e risposte (table)
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 9");
    addLightTitle(s, "Rischi e risposte");

    const rows = [
      headerRow(["Rischio", "Risposta", "Quando"]),
      dataRow(["Trainer non percepiscono problema", "POC misura. 8/10 confermano \u2192 mercato c\u2019\u00e8", "Giorno 14"], { rowIdx: 0 }),
      dataRow(["Complessit\u00e0 percepita", "Progressive disclosure + WhatsApp primo valore al primo click", "Mesi 1-3"], { rowIdx: 1 }),
      dataRow(["Prezzo percepito alto", "WTP misurata prima di rivelare prezzo. Frame: \u20AC1,23/giorno", "Giorno 14"], { rowIdx: 0 }),
      dataRow(["Box non convince", "2 Fondatori testano. Se no \u2192 Tailscale resta base", "Mese 2-3"], { rowIdx: 1 }),
      dataRow(["PT Evoluto non risuona", "Metrica: \u201cti definiresti PT Evoluto?\u201d Se <5/10 \u2192 ripensare", "Giorno 90"], { rowIdx: 0 }),
      dataRow(["Partner non genera lead", "Primo trim = test. Se <5/mese \u2192 ripensare modello", "Mesi 4-6"], { rowIdx: 1 }),
      dataRow(["Rinnovi bassi", "Rapporto 3,8:1 e 3,4:1. Se <40% \u2192 rivedere contenuto", "Mese 13"], { rowIdx: 0 }),
    ];

    s.addTable(rows, makeTableOpts(0.5, 1.2, 9, { colW: [2.8, 4.0, 2.2], fontSize: 9 }));

    addFooter(s, "La POC rivela ogni rischio prima che sia costoso. 90 giorni e ~\u20AC300.", 4.6);
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 43 — Section divider: Sezione 10
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeDarkSlide(pres);
    addDividerContent(s, 10, "Le 3 azioni immediate");
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 44 — 3 azioni immediate
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres, "SEZIONE 10");
    addLightTitle(s, "Le 3 azioni immediate");

    s.addText("Implementabili questa settimana, prima di formalizzare la partnership.", {
      x: 0.5, y: 1.15, w: 9, h: 0.3,
      fontSize: 12, color: C.textMid, fontFace: "Calibri", italic: true
    });

    const actions = [
      {
        num: "1", title: "Powered-by nel portale anamnesi",
        text: "\u201cPowered by FitManager Studio+\u201d con link. 10 min. 150+ esposizioni/mese gratuite.",
        color: C.blue
      },
      {
        num: "2", title: "Landing page con waiting list + referral virale",
        text: "Pagina singola: problema, soluzione, pricing, CTA. 1 settimana.",
        color: C.green
      },
      {
        num: "3", title: "Video teaser 60 secondi",
        text: "Apre con il momento WhatsApp (un click, il promemoria parte), poi mostra il resto. Screen recording, voce del founder. 4 ore.",
        color: C.amber
      },
    ];

    for (let i = 0; i < actions.length; i++) {
      const y = 1.6 + i * 1.1;
      addCard(s, 0.5, y, 9, 1.0, actions[i].color);
      // Big number
      s.addShape("roundRect", {
        x: 0.7, y: y + 0.15, w: 0.65, h: 0.65, rectRadius: 0.08,
        fill: { color: actions[i].color }
      });
      s.addText(actions[i].num, {
        x: 0.7, y: y + 0.15, w: 0.65, h: 0.65,
        fontSize: 26, color: C.white, fontFace: "Calibri", bold: true, align: "center", valign: "middle"
      });
      s.addText(actions[i].title, {
        x: 1.55, y: y + 0.05, w: 7.7, h: 0.4,
        fontSize: 14, color: C.text, fontFace: "Calibri", bold: true
      });
      s.addText(actions[i].text, {
        x: 1.55, y: y + 0.45, w: 7.7, h: 0.5,
        fontSize: 11, color: C.textMid, fontFace: "Calibri"
      });
    }
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 45 — Checklist partner, part 1
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres);
    addLightTitle(s, "Checklist primo incontro con il partner");

    // LEFT — Da mostrare
    addCard(s, 0.3, 1.2, 4.5, 3.8, C.blue);
    s.addText("Da mostrare", {
      x: 0.55, y: 1.3, w: 4.0, h: 0.35,
      fontSize: 13, color: C.blue, fontFace: "Calibri", bold: true
    });
    const showItems = [
      "Demo live (5 min: nuovo cliente \u2192 manda promemoria WhatsApp [wow immediato] \u2192 anamnesi \u2192 scheda \u2192 pagamento \u2192 Safety Engine)",
      "La FitManager Box (concept/prototipo)",
      "I numeri del BP: 3 scenari, confronto, vista cumulativa",
      "La struttura community (3 livelli, ruolo nell\u2019Inner Circle)",
    ];
    for (let i = 0; i < showItems.length; i++) {
      const y = 1.8 + i * 0.75;
      s.addShape("ellipse", { x: 0.6, y: y + 0.08, w: 0.12, h: 0.12, fill: { color: C.blue } });
      s.addText(showItems[i], {
        x: 0.85, y, w: 3.8, h: 0.7,
        fontSize: 9.5, color: C.text, fontFace: "Calibri", valign: "top"
      });
    }

    // RIGHT — Da chiedere
    addCard(s, 5.2, 1.2, 4.5, 3.8, C.amber);
    s.addText("Da chiedere", {
      x: 5.45, y: 1.3, w: 4.0, h: 0.35,
      fontSize: 13, color: C.amberDark, fontFace: "Calibri", bold: true
    });
    const askItems = [
      "\u201cPer i 10 Fondatori, chi metteresti nella lista?\u201d",
      "\u201cIl concetto PT Evoluto: come lo chiameresti tu?\u201d",
      "\u201c3 motivi per cui un PT direbbe NO anche a \u20AC99?\u201d",
      "\u201cConosci catene, centri, enti dove entrare come gruppo?\u201d",
      "\u201cLe masterclass: che temi per i primi 3 mesi?\u201d",
      "\u201cQuanto investirebbe un PT all\u2019anno in formazione?\u201d",
      "\u201cQuanti messaggi WhatsApp mandano al giorno ai clienti?\u201d",
    ];
    for (let i = 0; i < askItems.length; i++) {
      const y = 1.75 + i * 0.45;
      s.addShape("ellipse", { x: 5.5, y: y + 0.08, w: 0.12, h: 0.12, fill: { color: C.amber } });
      s.addText(askItems[i], {
        x: 5.75, y, w: 3.8, h: 0.4,
        fontSize: 9, color: C.text, fontFace: "Calibri", valign: "top"
      });
    }
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 46 — Checklist partner, part 2
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeLightSlide(pres);
    addLightTitle(s, "Il messaggio");

    // Da non fare (top section)
    addCard(s, 0.5, 1.2, 9, 1.6, C.coral);
    s.addText("Da non fare", {
      x: 0.75, y: 1.25, w: 3, h: 0.35,
      fontSize: 13, color: C.coral, fontFace: "Calibri", bold: true
    });
    const dontItems = [
      "Non parlare di codice, architettura, stack",
      "Non proporre i termini economici troppo presto",
      "Non promettere feature non implementate",
      "Non trattare i 10 Fondatori come \u201ci primi che capitano\u201d",
    ];
    for (let i = 0; i < dontItems.length; i++) {
      const y = 1.65 + i * 0.27;
      s.addText("\u2717  " + dontItems[i], {
        x: 0.75, y, w: 8.5, h: 0.25,
        fontSize: 10, color: C.text, fontFace: "Calibri"
      });
    }

    // The message (bottom section)
    s.addShape("roundRect", {
      x: 0.5, y: 3.1, w: 9, h: 2.0, rectRadius: 0.1,
      fill: { color: C.darkBg2 }, shadow: makeShadow()
    });
    s.addText("Il messaggio", {
      x: 0.7, y: 3.2, w: 3, h: 0.3,
      fontSize: 11, color: C.blueLight, fontFace: "Calibri", bold: true, charSpacing: 2
    });
    s.addText("\u201cHo costruito il prodotto. Funziona. La prima utente lo usa ogni giorno. Ma il mercato non si educa con un software \u2014 si educa con una voce credibile. Io posso costruire lo strumento. Tu puoi costruire il percorso. Insieme creiamo qualcosa che nessuno dei due pu\u00f2 creare da solo.\u201d", {
      x: 0.8, y: 3.55, w: 8.4, h: 1.4,
      fontSize: 14, color: C.white, fontFace: "Calibri", italic: true, valign: "middle", align: "center"
    });
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SLIDE 47 — Closing slide (dark bg)
  // ════════════════════════════════════════════════════════════════
  {
    const s = makeDarkSlide(pres);
    // Accent bar top
    s.addShape("rect", { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.blue } });
    // Decorative shapes
    s.addShape("rect", { x: 7.5, y: 0.5, w: 2.2, h: 2.2, fill: { color: C.blue }, transparency: 92 });
    s.addShape("rect", { x: 8, y: 1, w: 1.5, h: 1.5, fill: { color: C.blueLight }, transparency: 90 });

    s.addText("FitManager Studio+", {
      x: 0.7, y: 1.0, w: 8, h: 0.9,
      fontSize: 40, color: C.white, fontFace: "Calibri", bold: true
    });
    s.addText("Piano operativo di lancio, category creation e partnership", {
      x: 0.7, y: 1.9, w: 7, h: 0.5,
      fontSize: 15, color: C.blueLight, fontFace: "Calibri", italic: true
    });
    s.addShape("rect", { x: 0.7, y: 2.6, w: 2, h: 0.04, fill: { color: C.blue } });

    s.addText([
      { text: "Giacomo Verardo", options: { breakLine: true, color: C.white, bold: true } },
      { text: "Strategy Plan v3.1 \u2014 27 marzo 2026", options: { breakLine: true, color: C.textLight } },
      { text: "Confidenziale", options: { breakLine: true, color: C.coral } },
    ], {
      x: 0.7, y: 2.9, w: 5, h: 1.0,
      fontSize: 13, fontFace: "Calibri"
    });

    // Closing quote
    s.addShape("roundRect", {
      x: 0.7, y: 4.1, w: 8.6, h: 0.7, rectRadius: 0.06,
      fill: { color: C.darkBg2 }
    });
    s.addText("\u201cIl prodotto \u00e8 completo. La strategia \u00e8 chiara. Serve un partner per attivare il volano.\u201d", {
      x: 0.9, y: 4.1, w: 8.2, h: 0.7,
      fontSize: 13, color: C.blueLight, fontFace: "Calibri", italic: true, valign: "middle", align: "center"
    });
    addSlideNumber(s, slideNum);
  }

  // ════════════════════════════════════════════════════════════════
  // SAVE
  // ════════════════════════════════════════════════════════════════
  const outPath = "C:\\Users\\gvera\\Projects\\FitManager_AI_Studio\\FitManager_Strategy_Plan_2026.pptx";
  return pres.writeFile({ fileName: outPath }).then(() => {
    console.log(`Done! ${slideNum} slides written to ${outPath}`);
  });
}

main().catch(err => { console.error(err); process.exit(1); });

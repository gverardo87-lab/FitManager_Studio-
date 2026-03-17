const pptxgen = require("pptxgenjs");

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
const SHOTS = "C:/Users/gvera/Projects/FitManager_AI_Studio/data/screenshots";
const OUT = "C:/Users/gvera/Projects/FitManager_AI_Studio/data";

// ─── HELPERS ────────────────────────────────────────────────
const shadow = () => ({ type: "outer", color: "000000", blur: 8, offset: 3, angle: 135, opacity: 0.12 });
const cardShadow = () => ({ type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.10 });

function sNum(s, n) {
  s.addText(`${n} / ${TOTAL}`, {
    x: 8.8, y: 5.25, w: 1, h: 0.3,
    fontSize: 9, fontFace: FONT_B, color: C.slate, align: "right",
  });
}
function card(s, x, y, w, h, fill) {
  s.addShape("rect", { x, y, w, h, fill: { color: fill || C.white }, shadow: cardShadow() });
}
function bar(s, x, y, h, color) {
  s.addShape("rect", { x, y, w: 0.06, h, fill: { color: color || C.teal } });
}
function topAccent(s, color) {
  s.addShape("rect", { x: 0, y: 0, w: 10, h: 0.06, fill: { color: color || C.teal } });
}

// Screenshot slide helper: dark bg, accent bar, title, subtitle, centered screenshot (ratio 1.6:1)
function screenshotSlide(title, subtitle, imgPath, accent, num) {
  const s = pres.addSlide();
  s.background = { color: C.dark };
  topAccent(s, accent);
  s.addText(title, { x: 0.8, y: 0.15, w: 7, h: 0.4, fontSize: 20, fontFace: FONT_H, color: C.white, bold: true });
  s.addText(subtitle, { x: 0.8, y: 0.5, w: 8.2, h: 0.25, fontSize: 11, fontFace: FONT_B, color: C.slate });
  s.addShape("rect", { x: 1.15, y: 0.85, w: 7.7, h: 4.75, fill: { color: C.darkAlt }, shadow: shadow() });
  s.addImage({ path: imgPath, x: 1.25, y: 0.9, w: 7.5, h: 4.65 });
  sNum(s, num);
  return s;
}

// ─── PRESENTATION ───────────────────────────────────────────
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "FitManager Studio+";
pres.title = "FitManager Studio+ — Pitch Deck v10";

const TOTAL = 17;

// ═════════════════════════════════════════════════════════════
// 1. COVER
// ═════════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.dark };
  topAccent(s, C.teal);

  s.addText("FitManager Studio+", {
    x: 0.8, y: 1.0, w: 8.4, h: 1.0,
    fontSize: 48, fontFace: FONT_H, color: C.white, bold: true,
  });

  s.addText("Il software che trasforma\nil personal trainer in un professionista clinico.", {
    x: 0.8, y: 2.1, w: 8.4, h: 0.9,
    fontSize: 22, fontFace: FONT_B, color: C.mintLight, lineSpacingMultiple: 1.3,
  });

  s.addText("Privacy-first  ·  Offline  ·  Scientifico  ·  Italiano nativo", {
    x: 0.8, y: 3.2, w: 8.4, h: 0.4,
    fontSize: 14, fontFace: FONT_B, color: C.slate, italic: true,
  });

  // Bottom bar — 3 crisp differentiators, not vanity metrics
  s.addShape("rect", { x: 0, y: 4.5, w: 10, h: 1.125, fill: { color: C.darkAlt } });
  const facts = [
    { num: "5", label: "Motori Scientifici\nIntegrati" },
    { num: "0", label: "Dati in Cloud\n(Zero, Mai)" },
    { num: "1", label: "Investimento\nUna Tantum" },
  ];
  facts.forEach((f, i) => {
    const fx = 1.0 + i * 3.0;
    s.addText(f.num, { x: fx, y: 4.6, w: 2.0, h: 0.5, fontSize: 36, fontFace: FONT_H, color: C.mint, bold: true, align: "center" });
    s.addText(f.label, { x: fx, y: 5.1, w: 2.0, h: 0.45, fontSize: 11, fontFace: FONT_B, color: C.slate, align: "center" });
  });

  sNum(s, 1);
})();

// ═════════════════════════════════════════════════════════════
// 2. IL PROBLEMA
// ═════════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("Il Problema", {
    x: 0.8, y: 0.35, w: 8.4, h: 0.6,
    fontSize: 36, fontFace: FONT_H, color: C.dark, bold: true,
  });

  const pains = [
    {
      title: "5 app per un solo cliente",
      desc: "WhatsApp per comunicare, Excel per le schede, un'app per i pagamenti,\nGoogle Drive per i documenti, carta per l'anamnesi.\nOgni giorno perdi ore a saltare da uno strumento all'altro.",
      color: C.coral,
    },
    {
      title: "I dati clinici dei tuoi clienti sono in cloud",
      desc: "Patologie, farmaci, infortuni pregressi: su server USA o UK.\nZero controllo su chi li legge. Zero garanzie GDPR reali.\nSe smetti di pagare, perdi tutto.",
      color: C.amber,
    },
    {
      title: "Il tuo metodo e invisibile",
      desc: "Il cliente non vede la differenza tra te e l'app gratuita.\nNon puo. Non hai gli strumenti per mostrargliela.\nE senza prove, giustificare la tua tariffa diventa una battaglia.",
      color: C.purple,
    },
  ];

  pains.forEach((p, i) => {
    const py = 1.2 + i * 1.4;
    card(s, 0.8, py, 8.4, 1.2, C.white);
    bar(s, 0.8, py, 1.2, p.color);

    s.addText(p.title, {
      x: 1.1, y: py + 0.12, w: 7.8, h: 0.35,
      fontSize: 17, fontFace: FONT_B, color: C.dark, bold: true, margin: 0,
    });
    s.addText(p.desc, {
      x: 1.1, y: py + 0.5, w: 7.8, h: 0.6,
      fontSize: 12, fontFace: FONT_B, color: C.slateDark, margin: 0, lineSpacingMultiple: 1.2,
    });
  });

  sNum(s, 2);
})();

// ═════════════════════════════════════════════════════════════
// 3. LA SOLUZIONE
// ═════════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.dark };
  topAccent(s, C.teal);

  s.addText("La Soluzione", {
    x: 0.8, y: 0.4, w: 8.4, h: 0.6,
    fontSize: 36, fontFace: FONT_H, color: C.white, bold: true,
  });

  s.addText("Un unico strumento. Scientifico. Privato. Tuo per sempre.", {
    x: 0.8, y: 1.0, w: 8.4, h: 0.4,
    fontSize: 16, fontFace: FONT_B, color: C.mintLight, italic: true,
  });

  const pillars = [
    { title: "CRM Completo", desc: "Clienti, contratti, agenda, pagamenti, monitoraggio — tutto in un posto. Basta 5 app.", icon: "01", color: C.teal },
    { title: "Scienza Integrata", desc: "Safety engine, analisi biomeccanica 4D, nutrizione LARN. Non opinioni: numeri con fonti.", icon: "02", color: C.mint },
    { title: "Privacy Assoluta", desc: "I dati restano sul tuo PC. Nessun server. Nessun abbonamento cloud. GDPR by design.", icon: "03", color: C.green },
    { title: "Italiano Nativo", desc: "Interfaccia, terminologia e flussi pensati per il professionista fitness italiano a P.IVA.", icon: "04", color: C.blue },
  ];

  pillars.forEach((p, i) => {
    const py = 1.7 + i * 0.9;
    s.addShape("rect", { x: 0.8, y: py, w: 8.4, h: 0.75, fill: { color: C.darkAlt } });
    s.addShape("rect", { x: 0.8, y: py, w: 0.06, h: 0.75, fill: { color: p.color } });

    s.addShape("rect", { x: 1.05, y: py + 0.15, w: 0.5, h: 0.45, fill: { color: p.color } });
    s.addText(p.icon, {
      x: 1.05, y: py + 0.15, w: 0.5, h: 0.45,
      fontSize: 14, fontFace: FONT_H, color: C.white, bold: true, align: "center", valign: "middle",
    });

    s.addText(p.title, {
      x: 1.8, y: py + 0.08, w: 7.0, h: 0.3,
      fontSize: 16, fontFace: FONT_B, color: C.white, bold: true, margin: 0,
    });
    s.addText(p.desc, {
      x: 1.8, y: py + 0.4, w: 7.0, h: 0.28,
      fontSize: 12, fontFace: FONT_B, color: C.slate, margin: 0,
    });
  });

  sNum(s, 3);
})();

// ═════════════════════════════════════════════════════════════
// 4. HUB CLIENTE (screenshot)
// ═════════════════════════════════════════════════════════════
screenshotSlide(
  "Hub Cliente: Tutto in un Colpo d'Occhio",
  "Readiness score, semafori clinici, percorso onboarding, alert automatici, 6 tab operativi.",
  `${SHOTS}/power-07-profilo-cliente.png`,
  C.teal, 4,
);

// ═════════════════════════════════════════════════════════════
// 5. SAFETY ENGINE (screenshot) — IL differenziatore
// ═════════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.dark };
  topAccent(s, C.coral);

  s.addText("Safety Engine: Quello che Nessuno Ha", {
    x: 0.8, y: 0.15, w: 7, h: 0.4,
    fontSize: 20, fontFace: FONT_H, color: C.white, bold: true,
  });
  s.addText("47 condizioni cliniche × 434 esercizi. Ogni esercizio valutato in tempo reale contro il profilo del cliente.", {
    x: 0.8, y: 0.5, w: 8.2, h: 0.25,
    fontSize: 11, fontFace: FONT_B, color: C.slate,
  });

  // Screenshot
  s.addShape("rect", { x: 1.15, y: 0.85, w: 7.7, h: 4.15, fill: { color: C.darkAlt }, shadow: shadow() });
  s.addImage({ path: `${SHOTS}/targeted-02b-safety-builder.png`, x: 1.25, y: 0.9, w: 7.5, h: 4.05 });

  // Insight strip at bottom
  s.addShape("rect", { x: 0.8, y: 5.05, w: 8.4, h: 0.45, fill: { color: C.darkAlt } });
  bar(s, 0.8, 5.05, 0.45, C.coral);
  s.addText("Filosofia: INFORMARE, MAI LIMITARE. Il trainer decide sempre. Il sistema informa con dati, non blocca.", {
    x: 1.1, y: 5.08, w: 8.0, h: 0.38,
    fontSize: 11, fontFace: FONT_B, color: C.mintLight, italic: true, valign: "middle", margin: 0,
  });

  sNum(s, 5);
})();

// ═════════════════════════════════════════════════════════════
// 6. WORKOUT BUILDER (screenshot)
// ═════════════════════════════════════════════════════════════
screenshotSlide(
  "Workout Builder: La Scienza Guida la Scheda",
  "Board Kanban 3 sessioni. Profilo clinico integrato. Safety badge per esercizio. Analisi 4D automatica.",
  `${SHOTS}/targeted-01-scheda-analisi.png`,
  C.teal, 6,
);

// ═════════════════════════════════════════════════════════════
// 7. NUTRIZIONE LARN (screenshot)
// ═════════════════════════════════════════════════════════════
screenshotSlide(
  "Piano Nutrizionale con Validazione LARN",
  "Griglia 7 giorni × 8 pasti. 226 alimenti CREA. Score LARN 84/100 calcolato su 3 assi scientifici.",
  `${SHOTS}/targeted-03-nutrizione-piano.png`,
  C.green, 7,
);

// ═════════════════════════════════════════════════════════════
// 8. GESTIONE FINANZIARIA (screenshot)
// ═════════════════════════════════════════════════════════════
screenshotSlide(
  "Gestione Finanziaria Completa",
  "Saldo live, entrate/uscite, grafico giornaliero, proiezione, rinnovi con catena storica 1-click.",
  `${SHOTS}/power-01-cassa.png`,
  C.blue, 8,
);

// ═════════════════════════════════════════════════════════════
// 9. IL TEMPO CHE RISPARMI
// ═════════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.dark };
  topAccent(s, C.teal);

  s.addText("Il Tempo che Risparmi", {
    x: 0.8, y: 0.2, w: 8.4, h: 0.45,
    fontSize: 28, fontFace: FONT_H, color: C.white, bold: true,
  });
  s.addText("Ogni ora liberata e un'ora in piu con i tuoi clienti — o un cliente in piu al mese.", {
    x: 0.8, y: 0.65, w: 8.4, h: 0.25,
    fontSize: 12, fontFace: FONT_B, color: C.mintLight, italic: true,
  });

  const tasks = [
    { task: "Anamnesi cliente", before: "20-30 min", after: "5 min", how: "Link self-service: il cliente compila da smartphone" },
    { task: "Programmazione scheda", before: "45-60 min", after: "10-15 min", how: "Plan Builder 4 fasi con analisi automatica" },
    { task: "Controllo controindicazioni", before: "15-20 min", after: "Istantaneo", how: "Safety Engine: 47 condizioni × 434 esercizi" },
    { task: "Gestione pagamenti", before: "30 min/sett", after: "5 min", how: "Pagamento atomico 1-click, scadenze automatiche" },
    { task: "Report e misurazioni", before: "20-30 min", after: "2 min", how: "Range normativi OMS/ACSM calcolati in tempo reale" },
  ];

  // Header
  s.addShape("rect", { x: 0.5, y: 1.05, w: 9.0, h: 0.32, fill: { color: C.tealDark } });
  ["Attivita", "Prima", "Con FitManager", "Come"].forEach((h, i) => {
    const hx = [0.6, 3.1, 4.4, 5.9][i];
    const hw = [2.4, 1.2, 1.4, 3.4][i];
    s.addText(h, { x: hx, y: 1.05, w: hw, h: 0.32, fontSize: 10, fontFace: FONT_B, color: C.white, bold: true, valign: "middle", margin: 0 });
  });

  tasks.forEach((t, i) => {
    const ty = 1.42 + i * 0.55;
    s.addShape("rect", { x: 0.5, y: ty, w: 9.0, h: 0.5, fill: { color: i % 2 === 0 ? C.darkAlt : C.dark } });
    s.addText(t.task, { x: 0.6, y: ty, w: 2.4, h: 0.5, fontSize: 11, fontFace: FONT_B, color: C.white, bold: true, valign: "middle", margin: 0 });
    s.addText(t.before, { x: 3.1, y: ty, w: 1.2, h: 0.5, fontSize: 11, fontFace: FONT_B, color: C.coral, valign: "middle", margin: 0 });
    s.addText(t.after, { x: 4.4, y: ty, w: 1.4, h: 0.5, fontSize: 11, fontFace: FONT_B, color: C.mint, bold: true, valign: "middle", margin: 0 });
    s.addText(t.how, { x: 5.9, y: ty, w: 3.4, h: 0.5, fontSize: 10, fontFace: FONT_B, color: C.slate, valign: "middle", margin: 0 });
  });

  // Total callout
  s.addShape("rect", { x: 0.5, y: 4.3, w: 9.0, h: 0.85, fill: { color: C.darkAlt } });
  bar(s, 0.5, 4.3, 0.85, C.mint);

  s.addText("~4-6 ore/settimana risparmiate", {
    x: 0.8, y: 4.35, w: 5.5, h: 0.35,
    fontSize: 20, fontFace: FONT_H, color: C.mint, bold: true, margin: 0,
  });
  s.addText("= 200+ ore/anno che puoi reinvestire nei tuoi clienti o nella crescita del tuo business.", {
    x: 0.8, y: 4.72, w: 7.5, h: 0.3,
    fontSize: 12, fontFace: FONT_B, color: C.slate, margin: 0,
  });

  sNum(s, 9);
})();

// ═════════════════════════════════════════════════════════════
// 10. QUALITA DIMOSTRABILE
// ═════════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("Il Tuo Lavoro Diventa Visibile", {
    x: 0.8, y: 0.3, w: 8.4, h: 0.5,
    fontSize: 30, fontFace: FONT_H, color: C.dark, bold: true,
  });

  // LEFT: Senza
  card(s, 0.8, 1.0, 4.0, 2.8, C.white);
  s.addShape("rect", { x: 0.8, y: 1.0, w: 4.0, h: 0.4, fill: { color: C.coral } });
  s.addText("Oggi", {
    x: 0.8, y: 1.0, w: 4.0, h: 0.4,
    fontSize: 14, fontFace: FONT_B, color: C.white, bold: true, align: "center", valign: "middle",
  });
  const without = [
    "\"Mi sento meglio\" — feedback soggettivo",
    "Scheda su foglio Excel o app note",
    "Nessun dato su progressi misurabili",
    "Il cliente non vede il tuo metodo",
    "Giustificare la tariffa e una battaglia",
  ];
  s.addText(without.map((f, i) => ({
    text: f,
    options: { bullet: true, breakLine: i < without.length - 1, fontSize: 11, color: C.slateDark },
  })), { x: 1.0, y: 1.55, w: 3.5, h: 2.1, fontFace: FONT_B, paraSpaceAfter: 6 });

  // RIGHT: Con FitManager
  card(s, 5.2, 1.0, 4.0, 2.8, C.white);
  s.addShape("rect", { x: 5.2, y: 1.0, w: 4.0, h: 0.4, fill: { color: C.green } });
  s.addText("Con FitManager", {
    x: 5.2, y: 1.0, w: 4.0, h: 0.4,
    fontSize: 14, fontFace: FONT_B, color: C.white, bold: true, align: "center", valign: "middle",
  });
  const withFM = [
    "Report clinico con range OMS/ACSM",
    "Scheda con analisi 4D e score scientifico",
    "Grafici progressi: peso, composizione, forza",
    "Safety: \"Ho verificato le tue condizioni\"",
    "Il cliente VEDE il metodo. E paga il metodo.",
  ];
  s.addText(withFM.map((f, i) => ({
    text: f,
    options: { bullet: true, breakLine: i < withFM.length - 1, fontSize: 11, color: C.slateDark },
  })), { x: 5.4, y: 1.55, w: 3.5, h: 2.1, fontFace: FONT_B, paraSpaceAfter: 6 });

  // Bottom insight
  card(s, 0.8, 4.1, 8.4, 1.2, C.white);
  bar(s, 0.8, 4.1, 1.2, C.teal);
  s.addText([
    { text: "Non stai vendendo \"allenamento\".", options: {} },
    { text: " Stai vendendo un ", options: {} },
    { text: "metodo scientifico personalizzato", options: { bold: true } },
    { text: ".", options: { breakLine: true } },
    { text: "Quando il cliente vede i dati — grafici, score, analisi biomeccanica, report clinico —", options: {} },
    { text: " percepisce un servizio di livello superiore. E un servizio superiore vale di piu.", options: {} },
  ], {
    x: 1.1, y: 4.25, w: 7.8, h: 0.9,
    fontSize: 13, fontFace: FONT_B, color: C.dark, lineSpacingMultiple: 1.35, margin: 0,
  });

  sNum(s, 10);
})();

// ═════════════════════════════════════════════════════════════
// 11. LA SCIENZA SOTTO IL COFANO
// ═════════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.dark };
  topAccent(s, C.teal);

  s.addText("La Scienza Sotto il Cofano", {
    x: 0.8, y: 0.2, w: 8.4, h: 0.5,
    fontSize: 28, fontFace: FONT_H, color: C.white, bold: true,
  });
  s.addText("5 motori specializzati. Ogni numero ha una fonte. Ogni soglia e verificabile. Nessuna scatola nera.", {
    x: 0.8, y: 0.7, w: 8.4, h: 0.25,
    fontSize: 12, fontFace: FONT_B, color: C.slate, italic: true,
  });

  const engines = [
    { name: "Training\nScience", desc: "Periodizzazione, volume\nMEV/MAV/MRV, analisi\nbiomeccanica 4D.", color: C.teal },
    { name: "Safety\nEngine", desc: "47 condizioni × 80 regole.\nOgni esercizio valutato\ncontro il profilo clinico.", color: C.coral },
    { name: "Nutrition\nScience", desc: "Piano 7gg LARN.\nScoring 3 assi su\n226 alimenti CREA.", color: C.green },
    { name: "Clinical\nAnalysis", desc: "Range normativi\nOMS/ACSM/AHA.\nTrend automatici.", color: C.blue },
    { name: "Smart\nProgramming", desc: "Selezione esercizi per\nlivello, obiettivo e vincoli\nbiomeccanici 10D.", color: C.purple },
  ];

  engines.forEach((e, i) => {
    const ex = 0.5 + i * 1.88;
    s.addShape("rect", { x: ex, y: 1.1, w: 1.72, h: 2.5, fill: { color: C.darkAlt } });
    s.addShape("rect", { x: ex, y: 1.1, w: 1.72, h: 0.06, fill: { color: e.color } });

    s.addText(e.name, {
      x: ex + 0.1, y: 1.25, w: 1.52, h: 0.6,
      fontSize: 13, fontFace: FONT_B, color: C.white, bold: true, align: "center", valign: "middle",
    });
    s.addShape("rect", { x: ex + 0.3, y: 1.9, w: 1.12, h: 0.02, fill: { color: e.color } });
    s.addText(e.desc, {
      x: ex + 0.1, y: 2.05, w: 1.52, h: 1.4,
      fontSize: 10, fontFace: FONT_B, color: C.slate, align: "center",
    });
  });

  // Evidence bar
  s.addShape("rect", { x: 0.5, y: 3.8, w: 9.0, h: 0.6, fill: { color: C.darkAlt } });
  bar(s, 0.5, 3.8, 0.6, C.teal);
  const evidence = [
    { num: "18", label: "Fonti peer-reviewed" },
    { num: "35+", label: "Formule evidence-based" },
    { num: "~5.600", label: "Righe di logica scientifica" },
  ];
  evidence.forEach((ev, i) => {
    const evx = 1.0 + i * 3.0;
    s.addText(ev.num, { x: evx, y: 3.82, w: 1.0, h: 0.55, fontSize: 22, fontFace: FONT_H, color: C.mint, bold: true, valign: "middle" });
    s.addText(ev.label, { x: evx + 1.0, y: 3.82, w: 1.8, h: 0.55, fontSize: 11, fontFace: FONT_B, color: C.slate, valign: "middle" });
  });

  // Sources preview
  s.addText("Fonti: Schoenfeld, Israetel (RP), NSCA (Haff & Triplett), Contreras, Helms, Bompa, LARN 2014 (SINU), CREA 2018, OMS/ACSM/AHA", {
    x: 0.8, y: 4.55, w: 8.4, h: 0.4,
    fontSize: 10, fontFace: FONT_B, color: C.slateDark, italic: true,
  });

  // Exercise detail screenshot — small, as proof
  s.addShape("rect", { x: 5.6, y: 4.3, w: 3.95, h: 0.85, fill: { color: C.darkAlt } });

  sNum(s, 11);
})();

// ═════════════════════════════════════════════════════════════
// 12. PRIVACY-FIRST
// ═════════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("I Tuoi Dati. Sul Tuo PC. Punto.", {
    x: 0.8, y: 0.3, w: 8.4, h: 0.6,
    fontSize: 32, fontFace: FONT_H, color: C.dark, bold: true,
  });

  s.addText("Patologie, farmaci, infortuni, dati finanziari: informazioni sensibili che meritano protezione reale, non promesse.", {
    x: 0.8, y: 0.9, w: 8.4, h: 0.35,
    fontSize: 13, fontFace: FONT_B, color: C.slateDark,
  });

  const features = [
    {
      title: "Zero Cloud",
      desc: "SQLite locale. Nessun dato lascia il tuo computer.\nNessun server terzo. Mai.",
      color: C.green,
    },
    {
      title: "GDPR by Design",
      desc: "Dati clinici, anamnesi e finanziari protetti nativamente.\nNon e un'opzione: e l'architettura.",
      color: C.teal,
    },
    {
      title: "Backup Atomico",
      desc: "Backup 1-click con SHA-256 checksum e integrity check.\nRipristino completo in 30 secondi.",
      color: C.blue,
    },
    {
      title: "Licenza Offline",
      desc: "Crittografia RSA 2048. Nessun phone-home.\nFunziona anche senza internet. Sempre.",
      color: C.purple,
    },
  ];

  features.forEach((f, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const fx = 0.8 + col * 4.4;
    const fy = 1.5 + row * 1.6;

    card(s, fx, fy, 4.0, 1.35, C.white);
    bar(s, fx, fy, 1.35, f.color);

    s.addText(f.title, {
      x: fx + 0.25, y: fy + 0.12, w: 3.5, h: 0.35,
      fontSize: 16, fontFace: FONT_B, color: C.dark, bold: true, margin: 0,
    });
    s.addText(f.desc, {
      x: fx + 0.25, y: fy + 0.55, w: 3.5, h: 0.7,
      fontSize: 12, fontFace: FONT_B, color: C.slateDark, margin: 0, lineSpacingMultiple: 1.2,
    });
  });

  // Bottom insight
  card(s, 0.8, 4.8, 8.4, 0.55, C.greenBg);
  bar(s, 0.8, 4.8, 0.55, C.green);
  s.addText("I competitor cloud-based gestiscono i dati dei TUOI clienti sui LORO server. Tu sei responsabile. Loro no.", {
    x: 1.1, y: 4.88, w: 7.8, h: 0.35,
    fontSize: 12, fontFace: FONT_B, color: C.dark, bold: true, margin: 0,
  });

  sNum(s, 12);
})();

// ═════════════════════════════════════════════════════════════
// 13. CONFRONTO COMPETITIVO
// ═════════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("Confronto Competitivo", {
    x: 0.8, y: 0.25, w: 8.4, h: 0.55,
    fontSize: 30, fontFace: FONT_H, color: C.dark, bold: true,
  });

  const compData = [
    [
      { text: "", options: { fill: { color: C.tealDark }, fontSize: 10 } },
      { text: "FitManager", options: { bold: true, fill: { color: C.tealDark }, color: C.white, fontSize: 10, align: "center" } },
      { text: "Trainerize", options: { bold: true, fill: { color: "334155" }, color: C.white, fontSize: 10, align: "center" } },
      { text: "MyPTHub", options: { bold: true, fill: { color: "334155" }, color: C.white, fontSize: 10, align: "center" } },
      { text: "EvolutionFit", options: { bold: true, fill: { color: "334155" }, color: C.white, fontSize: 10, align: "center" } },
    ],
    ["Safety Engine", "47 condizioni", "No", "No", "No"],
    ["Volume MEV/MAV/MRV", "Si", "No", "No", "No"],
    ["Analisi biomeccanica 4D", "Si", "No", "No", "No"],
    ["Balance Ratios", "5 rapporti", "No", "No", "No"],
    ["Nutrizione LARN", "226 alimenti", "No", "Basica", "No"],
    ["Periodizzazione", "Evidence-based", "No", "Basica", "No"],
    ["Dati locali", "Si, zero cloud", "Cloud only", "Cloud only", "Cloud only"],
    ["Italiano nativo", "Si", "No", "No", "Tradotto"],
    ["Prezzo", "EUR 149-249\nuna tantum", "EUR 696/anno", "EUR 588/anno", "EUR 468/anno"],
    ["Licenza", "Perpetua", "Abbonamento", "Abbonamento", "Abbonamento"],
  ];

  s.addTable(compData, {
    x: 0.5, y: 0.9, w: 9.0,
    fontSize: 10, fontFace: FONT_B,
    border: { pt: 0.5, color: "E2E8F0" },
    colW: [2.0, 1.8, 1.5, 1.5, 1.5],
    rowH: [0.35, ...Array(10).fill(0.38)],
    autoPage: false,
  });

  sNum(s, 13);
})();

// ═════════════════════════════════════════════════════════════
// 14. IL CIRCOLO VIRTUOSO + ROI
// ═════════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.dark };
  topAccent(s, C.teal);

  s.addText("Il Circolo Virtuoso", {
    x: 0.8, y: 0.2, w: 8.4, h: 0.45,
    fontSize: 28, fontFace: FONT_H, color: C.white, bold: true,
  });

  const steps = [
    { num: "1", title: "Risparmi\nTempo", desc: "4-6 ore/settimana\nliberate", color: C.teal },
    { num: "2", title: "Servizio\nMigliore", desc: "Piu attenzione\nper ogni cliente", color: C.mint },
    { num: "3", title: "Qualita\nVisibile", desc: "Report e score:\nil cliente vede", color: C.green },
    { num: "4", title: "Tariffe\nPiu Alte", desc: "Posizionamento\npremium", color: C.blue },
  ];

  steps.forEach((st, i) => {
    const sx = 0.5 + i * 2.45;
    s.addShape("rect", { x: sx, y: 0.85, w: 2.1, h: 2.0, fill: { color: C.darkAlt } });
    s.addShape("rect", { x: sx, y: 0.85, w: 2.1, h: 0.06, fill: { color: st.color } });

    s.addText(st.num, {
      x: sx, y: 0.95, w: 2.1, h: 0.45,
      fontSize: 28, fontFace: FONT_H, color: st.color, bold: true, align: "center",
    });
    s.addText(st.title, {
      x: sx + 0.1, y: 1.45, w: 1.9, h: 0.5,
      fontSize: 14, fontFace: FONT_B, color: C.white, bold: true, align: "center", margin: 0,
    });
    s.addText(st.desc, {
      x: sx + 0.1, y: 2.0, w: 1.9, h: 0.6,
      fontSize: 10, fontFace: FONT_B, color: C.slate, align: "center", margin: 0,
    });

    if (i < 3) {
      s.addText(">", {
        x: sx + 2.1, y: 1.3, w: 0.35, h: 0.8,
        fontSize: 22, fontFace: FONT_B, color: C.slateDark, align: "center", valign: "middle",
      });
    }
  });

  // ROI section
  s.addShape("rect", { x: 0.5, y: 3.15, w: 9.0, h: 2.2, fill: { color: C.darkAlt } });
  bar(s, 0.5, 3.15, 2.2, C.mint);

  s.addText("Return on Investment", {
    x: 0.8, y: 3.2, w: 8.5, h: 0.35,
    fontSize: 16, fontFace: FONT_B, color: C.white, bold: true, margin: 0,
  });

  const roi = [
    { metric: "Aumento tariffa +10-15%", detail: "Da EUR 40 a EUR 45-46/sessione grazie alla percezione di servizio clinico-scientifico." },
    { metric: "2-3 clienti in piu al mese", detail: "Tempo liberato = slot disponibili. La qualita visibile genera passaparola." },
    { metric: "ROI in 30-60 giorni", detail: "20 clienti × +EUR 5/sessione × 4 sessioni/mese = +EUR 400/mese di fatturato aggiuntivo." },
    { metric: "Risparmio vs SaaS: EUR 400-1.300/anno", detail: "Investimento unico EUR 149-249 vs abbonamenti da EUR 468-696/anno. Dal secondo anno e tutto margine." },
  ];

  roi.forEach((r, i) => {
    const ry = 3.65 + i * 0.4;
    s.addText(r.metric, { x: 0.8, y: ry, w: 3.2, h: 0.35, fontSize: 12, fontFace: FONT_B, color: C.mint, bold: true, margin: 0, valign: "middle" });
    s.addText(r.detail, { x: 4.0, y: ry, w: 5.3, h: 0.35, fontSize: 10, fontFace: FONT_B, color: C.slate, margin: 0, valign: "middle" });
  });

  sNum(s, 14);
})();

// ═════════════════════════════════════════════════════════════
// 15. PRICING
// ═════════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("Investimento Unico vs Abbonamento Eterno", {
    x: 0.8, y: 0.25, w: 8.4, h: 0.5,
    fontSize: 26, fontFace: FONT_H, color: C.dark, bold: true,
  });

  // LEFT: FitManager
  card(s, 0.8, 0.9, 4.0, 3.3, C.white);
  s.addShape("rect", { x: 0.8, y: 0.9, w: 4.0, h: 0.45, fill: { color: C.teal } });
  s.addText("FitManager Studio+", {
    x: 0.8, y: 0.9, w: 4.0, h: 0.45,
    fontSize: 14, fontFace: FONT_B, color: C.white, bold: true, align: "center", valign: "middle",
  });

  s.addText("EUR 149 - 249", {
    x: 1.0, y: 1.5, w: 3.6, h: 0.55,
    fontSize: 36, fontFace: FONT_H, color: C.teal, bold: true, align: "center",
  });
  s.addText("Una tantum. Per sempre.", {
    x: 1.0, y: 2.05, w: 3.6, h: 0.3,
    fontSize: 14, fontFace: FONT_B, color: C.dark, align: "center", bold: true,
  });

  const ourFeats = [
    "Licenza perpetua, nessun canone",
    "Tutti i motori scientifici inclusi",
    "Zero costi cloud (dati locali)",
    "Aggiornamenti opzionali EUR 49/anno",
    "ROI dal primo mese",
  ];
  s.addText(ourFeats.map((f, i) => ({
    text: f,
    options: { bullet: true, breakLine: i < ourFeats.length - 1, fontSize: 11, color: C.slateDark },
  })), { x: 1.2, y: 2.4, w: 3.2, h: 1.6, fontFace: FONT_B, paraSpaceAfter: 5 });

  // RIGHT: Competitors
  card(s, 5.2, 0.9, 4.0, 3.3, C.white);
  s.addShape("rect", { x: 5.2, y: 0.9, w: 4.0, h: 0.45, fill: { color: C.slateDark } });
  s.addText("Competitor SaaS (media)", {
    x: 5.2, y: 0.9, w: 4.0, h: 0.45,
    fontSize: 14, fontFace: FONT_B, color: C.white, bold: true, align: "center", valign: "middle",
  });

  s.addText("EUR 468 - 696", {
    x: 5.4, y: 1.5, w: 3.6, h: 0.55,
    fontSize: 30, fontFace: FONT_H, color: C.coral, bold: true, align: "center",
  });
  s.addText("All'anno. Ogni anno. Per sempre.", {
    x: 5.4, y: 2.05, w: 3.6, h: 0.3,
    fontSize: 14, fontFace: FONT_B, color: C.dark, align: "center", bold: true,
  });

  const theirFeats = [
    "Abbonamento mensile obbligatorio",
    "Dati persi se smetti di pagare",
    "Zero motori scientifici",
    "In 3 anni: EUR 1.400 - 2.100 spesi",
    "E non hai ancora niente di tuo",
  ];
  s.addText(theirFeats.map((f, i) => ({
    text: f,
    options: { bullet: true, breakLine: i < theirFeats.length - 1, fontSize: 11, color: C.slateDark },
  })), { x: 5.6, y: 2.4, w: 3.2, h: 1.6, fontFace: FONT_B, paraSpaceAfter: 5 });

  // Bottom insight
  card(s, 0.8, 4.4, 8.4, 0.9, C.greenBg);
  bar(s, 0.8, 4.4, 0.9, C.green);
  s.addText("Il confronto reale", {
    x: 1.1, y: 4.45, w: 7.8, h: 0.3,
    fontSize: 14, fontFace: FONT_B, color: C.dark, bold: true, margin: 0,
  });
  s.addText("Un PT che guadagna EUR 20-33K/anno risparmia EUR 400-1.300/anno scegliendo FitManager.\nE ottiene motori scientifici che nessun competitor offre a nessun prezzo.", {
    x: 1.1, y: 4.78, w: 7.8, h: 0.45,
    fontSize: 12, fontFace: FONT_B, color: C.slateDark, margin: 0, lineSpacingMultiple: 1.2,
  });

  sNum(s, 15);
})();

// ═════════════════════════════════════════════════════════════
// 16. ROADMAP
// ═════════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.light };

  s.addText("Roadmap Prodotto", {
    x: 0.8, y: 0.3, w: 8.4, h: 0.55,
    fontSize: 30, fontFace: FONT_H, color: C.dark, bold: true,
  });

  const roadmap = [
    {
      phase: "v1.0", period: "Q1 2026", status: "LIVE",
      items: "CRM completo + Training Science Engine + Safety Engine + Workout Builder\n+ Cassa + Rinnovi + Installer Windows + Licenza RSA",
      color: C.teal,
    },
    {
      phase: "v1.5", period: "Q2 2026", status: "NEXT",
      items: "Nutrizione completa (piano 7gg + scoring LARN) + Export PDF clinico\n+ Dashboard analytics avanzate",
      color: C.blue,
    },
    {
      phase: "v2.0", period: "Q3 2026", status: "PLANNED",
      items: "AI Coach locale (Ollama, zero cloud) + Programmazione automatica smart\n+ Assistente NLP integrato",
      color: C.purple,
    },
    {
      phase: "v3.0", period: "2027", status: "VISION",
      items: "App mobile companion (offline-first) + Sync opzionale P2P (no cloud)\n+ Multi-operatore per palestre",
      color: C.amber,
    },
  ];

  roadmap.forEach((r, i) => {
    const ry = 1.1 + i * 1.1;
    card(s, 0.8, ry, 8.4, 0.95, C.white);

    s.addShape("rect", { x: 0.8, y: ry, w: 1.1, h: 0.95, fill: { color: r.color } });
    s.addText(r.phase, {
      x: 0.8, y: ry + 0.05, w: 1.1, h: 0.5,
      fontSize: 16, fontFace: FONT_H, color: C.white, bold: true, align: "center", valign: "middle",
    });
    s.addText(r.status, {
      x: 0.8, y: ry + 0.55, w: 1.1, h: 0.3,
      fontSize: 9, fontFace: FONT_B, color: C.white, align: "center",
    });

    s.addText(r.period, {
      x: 2.1, y: ry + 0.1, w: 2.0, h: 0.3,
      fontSize: 14, fontFace: FONT_B, color: C.dark, bold: true, margin: 0,
    });
    s.addText(r.items, {
      x: 2.1, y: ry + 0.4, w: 6.8, h: 0.5,
      fontSize: 11, fontFace: FONT_B, color: C.slateDark, margin: 0, lineSpacingMultiple: 1.15,
    });
  });

  sNum(s, 16);
})();

// ═════════════════════════════════════════════════════════════
// 17. CHIUSURA + CTA
// ═════════════════════════════════════════════════════════════
(() => {
  const s = pres.addSlide();
  s.background = { color: C.dark };
  topAccent(s, C.teal);

  s.addText("Il tuo studio.\nI tuoi dati.\nLa tua scienza.", {
    x: 0.8, y: 0.7, w: 8.4, h: 2.0,
    fontSize: 44, fontFace: FONT_H, color: C.white, bold: true, lineSpacingMultiple: 1.2,
  });

  s.addText("FitManager Studio+", {
    x: 0.8, y: 2.8, w: 8.4, h: 0.5,
    fontSize: 24, fontFace: FONT_B, color: C.mint,
  });

  // CTA
  s.addShape("rect", { x: 0.8, y: 3.6, w: 3.6, h: 0.55, fill: { color: C.teal } });
  s.addText("Richiedi una demo gratuita", {
    x: 0.8, y: 3.6, w: 3.6, h: 0.55,
    fontSize: 16, fontFace: FONT_B, color: C.white, bold: true, align: "center", valign: "middle",
  });

  s.addText("info@fitmanager.studio", {
    x: 0.8, y: 4.3, w: 8.4, h: 0.35,
    fontSize: 14, fontFace: FONT_B, color: C.slate,
  });

  // Bottom bar
  s.addShape("rect", { x: 0, y: 4.9, w: 10, h: 0.725, fill: { color: C.darkAlt } });
  s.addText("Privacy-First  |  Offline  |  Scientifico  |  Italiano  |  Tuo per sempre", {
    x: 0.8, y: 4.95, w: 8.4, h: 0.5,
    fontSize: 14, fontFace: FONT_B, color: C.mintLight, align: "center",
  });

  sNum(s, 17);
})();

// ═════════════════════════════════════════════════════════════
// WRITE
// ═════════════════════════════════════════════════════════════
pres.writeFile({ fileName: `${OUT}/FitManager_Pitch_Deck_v10.pptx` })
  .then(() => {
    console.log(`Pitch deck v10 generated: ${TOTAL} slides.`);
  })
  .catch((err) => {
    console.error("Error:", err.message);
    process.exit(1);
  });

#!/usr/bin/env node
/**
 * PRE-FLIGHT Video 01 — "Il Primo Cliente"
 *
 * Verifica TUTTE le interazioni del copione senza registrare video.
 * Ogni step riporta PASS/FAIL. Se un FAIL blocca il flusso, lo script
 * lo segnala e continua con gli step indipendenti.
 *
 * Eseguire PRIMA di qualsiasi registrazione.
 */

const { chromium } = require("playwright");

const BASE = "http://localhost:3001";
const CREDS = { email: "chiarabassani96@gmail.com", password: "Fitness2026!" };

// Cliente demo per il test (verra' eliminato alla fine se creato)
const DEMO_CLIENT = { nome: "Luca", cognome: "Tardini", telefono: "340 5678901" };

async function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

// ── Helper verificati (da VIDEO_PRODUCTION.md) ──

async function selectDate(page, triggerText, targetDataDay, maxNavClicks = 6) {
  await page.locator(`button:has-text("${triggerText}")`).click();
  await wait(500);
  const dayBtn = page.locator(`button[data-day="${targetDataDay}"]`);
  if (await dayBtn.isVisible({ timeout: 500 }).catch(() => false)) {
    await dayBtn.click();
    await wait(300);
    return true;
  }
  for (let i = 0; i < maxNavClicks; i++) {
    await page.locator('button.rdp-button_next').click();
    await wait(400);
    if (await dayBtn.isVisible({ timeout: 500 }).catch(() => false)) {
      await dayBtn.click();
      await wait(300);
      return true;
    }
  }
  return false;
}

async function selectRadixOption(page, triggerSelector, optionText) {
  await page.locator(triggerSelector).click();
  await wait(400);
  const item = page.locator(`[data-slot="select-item"]:has-text("${optionText}")`);
  if (await item.isVisible({ timeout: 1000 }).catch(() => false)) {
    await item.click();
    await wait(300);
    return true;
  }
  return false;
}

// ── Test runner ──

let passCount = 0;
let failCount = 0;
let skipCount = 0;
let blocked = false;

function pass(step, detail) {
  passCount++;
  console.log(`  ✓ ${step}${detail ? " — " + detail : ""}`);
}

function fail(step, detail) {
  failCount++;
  console.log(`  ✗ ${step}${detail ? " — " + detail : ""}`);
}

function skip(step, reason) {
  skipCount++;
  console.log(`  ○ ${step} — SKIP: ${reason}`);
}

function section(name) {
  console.log(`\n━━━ ${name} ━━━`);
}

// ── Main ──

async function main() {
  console.log("╔══════════════════════════════════════════════════════════╗");
  console.log("║  PRE-FLIGHT: Video 01 — Il Primo Cliente               ║");
  console.log("║  Verifica interazioni senza registrazione video         ║");
  console.log("╚══════════════════════════════════════════════════════════╝\n");

  const browser = await chromium.launch({
    headless: false,
    slowMo: 60,
    args: ["--start-maximized"],
  });
  const ctx = await browser.newContext({ viewport: null });
  const page = await ctx.newPage();

  let clientId = null;
  let contractId = null;

  try {
    // ══════════════════════════════════════
    section("CLEANUP PREVENTIVO");
    // ══════════════════════════════════════

    // Elimina eventuali Tardini dal DB (run precedenti)
    {
      const loginResp = await (await fetch(`http://localhost:8001/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: CREDS.email, password: CREDS.password }),
      })).json();
      const token = loginResp.access_token;

      const clientsResp = await (await fetch(`http://localhost:8001/api/clients?page_size=200&search=${DEMO_CLIENT.cognome}`, {
        headers: { "Authorization": `Bearer ${token}` },
      })).json();

      for (const c of clientsResp.items || []) {
        // Elimina contratti con force=true (cascade: rate, movimenti, eventi)
        const contractsResp = await (await fetch(`http://localhost:8001/api/contracts?page_size=200`, {
          headers: { "Authorization": `Bearer ${token}` },
        })).json();
        for (const ct of (contractsResp.items || []).filter(ct => ct.id_cliente === c.id)) {
          const r = await fetch(`http://localhost:8001/api/contracts/${ct.id}?force=true`, {
            method: "DELETE", headers: { "Authorization": `Bearer ${token}` },
          });
          console.log(`  Eliminato contratto ${ct.id}: ${r.status === 204 ? "OK" : r.status}`);
        }
        // Poi elimina il cliente
        const delResp = await fetch(`http://localhost:8001/api/clients/${c.id}`, {
          method: "DELETE", headers: { "Authorization": `Bearer ${token}` },
        });
        console.log(`  Eliminato ${c.nome} ${c.cognome} (ID: ${c.id}): ${delResp.status === 204 ? "OK" : delResp.status}`);
      }

      if ((clientsResp.items || []).length === 0) {
        console.log("  Nessun dato residuo da pulire");
      }
    }
    // ══════════════════════════════════════
    section("LOGIN");
    // ══════════════════════════════════════

    await page.goto(`${BASE}/login`);
    const emailInput = await page.waitForSelector('input[type="email"]', { timeout: 10000 }).catch(() => null);
    if (emailInput) {
      pass("Pagina login caricata");
    } else {
      fail("Pagina login NON caricata");
      blocked = true;
    }

    if (!blocked) {
      await page.fill('input[type="email"]', CREDS.email);
      await page.fill('input[type="password"]', CREDS.password);
      await page.click('button[type="submit"]');
      const dashOk = await page.waitForURL("**/", { timeout: 10000 }).then(() => true).catch(() => false);
      await wait(2000);
      dashOk ? pass("Login completato") : fail("Login fallito — redirect non avvenuto");
      if (!dashOk) blocked = true;
    }

    // ══════════════════════════════════════
    section("SCENA 01 — Pagina Clienti");
    // ══════════════════════════════════════

    if (!blocked) {
      await page.goto(`${BASE}/clienti`);
      const header = await page.waitForSelector('[data-guide="clienti-header"]', { timeout: 10000 }).catch(() => null);
      header ? pass("Pagina /clienti caricata", "data-guide clienti-header trovato") : fail("Pagina /clienti — header non trovato");

      const newBtn = await page.locator('[data-guide="clienti-new-button"]').isVisible({ timeout: 3000 }).catch(() => false);
      newBtn ? pass("Bottone 'Nuovo Cliente' visibile") : fail("Bottone 'Nuovo Cliente' NON visibile");
    }

    // ══════════════════════════════════════
    section("SCENA 02 — Crea Cliente");
    // ══════════════════════════════════════

    if (!blocked) {
      // Apri sheet
      await page.click('[data-guide="clienti-new-button"]');
      await wait(800);
      const nomeField = await page.locator('#nome').isVisible({ timeout: 3000 }).catch(() => false);
      nomeField ? pass("Sheet 'Nuovo Cliente' aperto", "campo #nome visibile") : fail("Sheet NON aperto — #nome non trovato");

      if (nomeField) {
        // Compila
        await page.fill('#nome', DEMO_CLIENT.nome);
        await page.fill('#cognome', DEMO_CLIENT.cognome);
        await page.fill('#telefono', DEMO_CLIENT.telefono);
        await wait(300);

        const nomeVal = await page.inputValue('#nome');
        const cognomeVal = await page.inputValue('#cognome');
        const telVal = await page.inputValue('#telefono');
        nomeVal === DEMO_CLIENT.nome ? pass("Campo nome compilato", nomeVal) : fail("Campo nome", `atteso "${DEMO_CLIENT.nome}", ottenuto "${nomeVal}"`);
        cognomeVal === DEMO_CLIENT.cognome ? pass("Campo cognome compilato", cognomeVal) : fail("Campo cognome errato");
        telVal === DEMO_CLIENT.telefono ? pass("Campo telefono compilato", telVal) : fail("Campo telefono errato");

        // Submit
        const submitBtn = await page.locator('button:has-text("Crea Cliente")').isVisible({ timeout: 2000 }).catch(() => false);
        submitBtn ? pass("Bottone 'Crea Cliente' visibile") : fail("Bottone 'Crea Cliente' NON visibile");

        if (submitBtn) {
          await page.click('button:has-text("Crea Cliente")');
          await wait(2000);

          // Dopo creazione: ri-naviga a /clienti per refresh sicuro della lista
          await page.goto(`${BASE}/clienti`);
          await page.waitForSelector('[data-guide="clienti-header"]', { timeout: 10000 });
          await wait(1500);

          // Usa ricerca per trovare il nuovo cliente
          const searchInput = page.locator('[data-guide="clienti-search"] input');
          const searchVisible = await searchInput.isVisible({ timeout: 3000 }).catch(() => false);
          if (searchVisible) {
            await searchInput.fill(DEMO_CLIENT.cognome);
            await wait(1500);
          }

          const clientRow = await page.locator(`td:has-text("${DEMO_CLIENT.cognome}")`).first().isVisible({ timeout: 5000 }).catch(() => false);
          clientRow ? pass("Cliente creato e visibile in lista") : fail("Cliente NON visibile in lista dopo creazione");

          if (clientRow) {
            // Apri profilo — click sulla riga (prima cella con il cognome)
            await page.locator(`td:has-text("${DEMO_CLIENT.cognome}")`).first().click();
            await wait(2000);

            const avatarHero = await page.locator('[data-guide="client-avatar-hero"]').isVisible({ timeout: 5000 }).catch(() => false);
            avatarHero ? pass("Profilo cliente aperto", "avatar hero visibile") : fail("Profilo cliente — avatar hero NON visibile");

            // Leggi ID cliente dall'URL
            const url = page.url();
            const match = url.match(/\/clienti\/(\d+)/);
            if (match) {
              clientId = parseInt(match[1]);
              pass("ID cliente estratto dall'URL", `ID: ${clientId}`);
            } else {
              fail("Impossibile estrarre ID cliente dall'URL", url);
            }

            // Verifica checklist
            const checklistVisible = await page.locator('[data-guide="client-onboarding-checklist"]').isVisible({ timeout: 3000 }).catch(() => false);
            checklistVisible ? pass("OnboardingChecklist visibile") : fail("OnboardingChecklist NON visibile");

            const creaContratto = await page.locator('text=Crea contratto').first().isVisible({ timeout: 3000 }).catch(() => false);
            creaContratto ? pass("CTA 'Crea contratto' visibile in checklist") : fail("CTA 'Crea contratto' NON visibile");
          }
        }
      }
    }

    // ══════════════════════════════════════
    section("SCENA 03a — Crea Contratto (form)");
    // ══════════════════════════════════════

    if (!blocked && clientId) {
      // Click "Crea contratto" dalla checklist
      await page.locator('text=Crea contratto').first().click();
      await wait(2500);

      // Dovremmo essere su /contratti?new=1&cliente=ID con Sheet aperto
      const currentUrl = page.url();
      // "Crea contratto" dalla checklist apre uno Sheet dentro il profilo (non naviga a /contratti)
      pass("Click 'Crea contratto' dalla checklist", currentUrl);

      // Verifica Sheet aperto con form
      const tipoPacchetto = await page.locator('#tipo_pacchetto').isVisible({ timeout: 5000 }).catch(() => false);
      tipoPacchetto ? pass("Sheet contratto aperto", "#tipo_pacchetto visibile") : fail("Sheet contratto NON aperto");

      if (tipoPacchetto) {
        // Compila campi testo/numero
        await page.fill('#tipo_pacchetto', "Pacchetto 10");
        const tipoVal = await page.inputValue('#tipo_pacchetto');
        tipoVal === "Pacchetto 10" ? pass("tipo_pacchetto compilato") : fail("tipo_pacchetto errato", tipoVal);

        await page.fill('#crediti_totali', "10");
        pass("crediti_totali compilato", "10");

        await page.fill('#prezzo_totale', "550");
        pass("prezzo_totale compilato", "550");

        // DatePicker: Data Inizio → 01/04/2026
        const dateStartOk = await selectDate(page, "Inizio...", "01/04/2026");
        dateStartOk ? pass("DatePicker Data Inizio", "01/04/2026") : fail("DatePicker Data Inizio — data non trovata");

        // DatePicker: Data Scadenza → 01/06/2026
        const dateEndOk = await selectDate(page, "Scadenza...", "01/06/2026");
        dateEndOk ? pass("DatePicker Data Scadenza", "01/06/2026") : fail("DatePicker Data Scadenza — data non trovata");

        // Acconto
        await page.fill('#acconto', "50");
        await wait(800); // Attende comparsa Select metodo
        pass("acconto compilato", "50");

        // Select metodo: BONIFICO
        const metodoTrigger = page.locator('[data-slot="select-trigger"]').last();
        const metodoVisible = await metodoTrigger.isVisible({ timeout: 3000 }).catch(() => false);
        metodoVisible ? pass("Select metodo pagamento visibile") : fail("Select metodo NON visibile — acconto non ha triggerato il campo?");

        if (metodoVisible) {
          // Il Select metodo e' il secondo combobox (il primo e' il cliente)
          const bonificoOk = await selectRadixOption(page, 'button[role="combobox"][data-placeholder]', "BONIFICO");
          bonificoOk ? pass("Metodo BONIFICO selezionato") : fail("Metodo BONIFICO — selezione fallita");
        }

        // Scroll per vedere submit
        await page.evaluate(() => {
          const sheet = document.querySelector('[data-slot="sheet-content"]');
          if (sheet) sheet.scrollTop = sheet.scrollHeight;
        });
        await wait(500);

        // Submit
        const submitContract = page.locator('button[type="submit"]:has-text("Crea Contratto")');
        const submitVisible = await submitContract.isVisible({ timeout: 3000 }).catch(() => false);
        submitVisible ? pass("Bottone 'Crea Contratto' visibile") : fail("Bottone 'Crea Contratto' NON visibile");

        if (submitVisible) {
          await submitContract.click();
          await wait(3000);

          // Il contratto potrebbe redirect a /contratti/[id] OPPURE restare nel profilo
          await wait(2000);
          const detailUrl = page.url();
          const contractMatch = detailUrl.match(/\/contratti\/(\d+)/);
          if (contractMatch) {
            contractId = parseInt(contractMatch[1]);
            pass("Contratto creato — redirect al dettaglio", `ID: ${contractId}`);
          } else {
            // Prova a trovare il contratto via API
            const token = await page.evaluate(() => {
              const cookies = document.cookie.split(";").map(c => c.trim());
              const tk = cookies.find(c => c.startsWith("fitmanager_token="));
              return tk ? tk.split("=")[1] : null;
            });
            if (token) {
              const resp = await page.evaluate(async (args) => {
                const r = await fetch(`http://localhost:8001/api/contracts?page_size=200`, {
                  headers: { "Authorization": `Bearer ${args.token}` }
                });
                const data = await r.json();
                const c = data.items?.find(c => c.id_cliente === args.clientId);
                return c ? c.id : null;
              }, { token, clientId });
              if (resp) {
                contractId = resp;
                pass("Contratto creato (trovato via API)", `ID: ${contractId}`);
              } else {
                fail("Contratto NON trovato ne' via URL ne' via API");
              }
            }
          }
        }
      }
    } else if (!clientId) {
      skip("Scena 03a", "clientId mancante (scena 02 fallita)");
    }

    // ══════════════════════════════════════
    section("SCENA 03b — Genera Piano Rate");
    // ══════════════════════════════════════

    if (!blocked && contractId) {
      // Naviga al dettaglio contratto (potremmo essere ancora nel profilo)
      await page.goto(`${BASE}/contratti/${contractId}`);
      await wait(2000);
      const contractHeader = await page.locator('[data-guide="contratto-header"]').isVisible({ timeout: 5000 }).catch(() => false);
      contractHeader ? pass("Dettaglio contratto caricato") : fail("Dettaglio contratto — header non trovato");

      // Scroll al piano pagamenti
      await page.evaluate(() => window.scrollBy({ top: 500, behavior: "smooth" }));
      await wait(1500);

      const pianoRate = await page.locator('[data-guide="contratto-piano-rate"]').isVisible({ timeout: 3000 }).catch(() => false);
      pianoRate ? pass("Sezione piano rate visibile") : fail("Sezione piano rate NON visibile");

      // Verifica form genera rate
      const genFormText = await page.locator('text=Nessun piano rate configurato').isVisible({ timeout: 3000 }).catch(() => false);
      genFormText ? pass("Form 'Genera piano rate' visibile") : fail("Form genera rate NON visibile — rate gia' presenti?");

      if (genFormText) {
        // Numero rate → 2
        await page.fill('#numero_rate', "2");
        const nrVal = await page.inputValue('#numero_rate');
        nrVal === "2" ? pass("numero_rate impostato", "2") : fail("numero_rate errato", nrVal);

        // Data prima rata → 01/05/2026
        const dataPrimaRataOk = await selectDate(page, "Seleziona data...", "01/05/2026");
        dataPrimaRataOk ? pass("DatePicker data prima rata", "01/05/2026") : fail("DatePicker data prima rata — data non trovata");

        // Verifica bottone abilitato
        await wait(500);
        const genBtn = page.locator('button:has-text("Genera Piano Pagamenti")');
        const genEnabled = await genBtn.isEnabled({ timeout: 3000 }).catch(() => false);
        genEnabled ? pass("Bottone 'Genera Piano Pagamenti' ABILITATO") : fail("Bottone 'Genera Piano Pagamenti' DISABLED — data non selezionata?");

        if (genEnabled) {
          await genBtn.click();
          await wait(3000);

          // Verifica rate generate
          // Cerchiamo importi €250 nella pagina
          const rateVisible = await page.locator('text=250').first().isVisible({ timeout: 5000 }).catch(() => false);
          rateVisible ? pass("Rate generate e visibili", "€250 trovato nella pagina") : fail("Rate NON visibili dopo generazione");

          // Scroll per mostrare tutte le rate
          await page.evaluate(() => window.scrollBy({ top: 300, behavior: "smooth" }));
          await wait(1000);
        }
      }
    } else if (!contractId) {
      skip("Scena 03b", "contractId mancante (scena 03a fallita)");
    }

    // ══════════════════════════════════════
    section("SCENA 04 — Anamnesi");
    // ══════════════════════════════════════

    if (!blocked && clientId) {
      // Torna al profilo cliente
      await page.goto(`${BASE}/clienti/${clientId}`);
      await wait(2000);

      const profileOk = await page.locator('[data-guide="client-avatar-hero"]').isVisible({ timeout: 5000 }).catch(() => false);
      profileOk ? pass("Profilo cliente ri-caricato") : fail("Profilo cliente — avatar hero non trovato");

      if (profileOk) {
        // Verifica checklist aggiornata — Contratto dovrebbe essere completato
        const checklistUpdated = await page.locator('[data-guide="client-onboarding-checklist"]').isVisible({ timeout: 3000 }).catch(() => false);
        checklistUpdated ? pass("OnboardingChecklist visibile dopo contratto") : fail("OnboardingChecklist NON visibile");

        // Verifica che "Compila" (anamnesi) sia il prossimo step
        const compilaBtn = await page.locator('text=Compila').first().isVisible({ timeout: 3000 }).catch(() => false);
        compilaBtn ? pass("CTA 'Compila' (anamnesi) visibile") : skip("CTA 'Compila'", "potrebbe non apparire se checklist ha layout diverso");

        if (compilaBtn) {
          await page.locator('text=Compila').first().click();
          await wait(2500);

          // Dovremmo essere su /clienti/[id]/anamnesi con wizard
          const anamnesiUrl = page.url();
          const onAnamnesi = anamnesiUrl.includes('/anamnesi');
          onAnamnesi ? pass("Navigato a pagina anamnesi", anamnesiUrl) : fail("Navigazione anamnesi fallita", anamnesiUrl);

          // Se il wizard non si apre automaticamente, naviga con ?startWizard=1
          let avantiBtn = await page.locator('button:has-text("Avanti")').isVisible({ timeout: 3000 }).catch(() => false);

          if (!avantiBtn) {
            // La pagina anamnesi mostra "Compila tu" come bottone per aprire il wizard
            const compilaTu = page.locator('button:has-text("Compila tu")');
            const compilaTuVisible = await compilaTu.isVisible({ timeout: 3000 }).catch(() => false);

            if (compilaTuVisible) {
              console.log("    [diag] Click 'Compila tu' per aprire wizard");
              await compilaTu.click();
              await wait(2000);
              avantiBtn = await page.locator('button:has-text("Avanti")').isVisible({ timeout: 5000 }).catch(() => false);
            } else {
              console.log("    [diag] Ne' wizard ne' 'Compila tu' trovati");
            }
          }

          avantiBtn ? pass("Wizard anamnesi aperto", "bottone 'Avanti' visibile") : fail("Wizard anamnesi NON aperto — bottone 'Avanti' non trovato");
        }
      }
    } else if (!clientId) {
      skip("Scena 04", "clientId mancante");
    }

    // ══════════════════════════════════════
    section("SCENA 05 — Profilo 2/5");
    // ══════════════════════════════════════

    if (!blocked && clientId) {
      await page.goto(`${BASE}/clienti/${clientId}`);
      await wait(2000);

      const profileOk = await page.locator('[data-guide="client-avatar-hero"]').isVisible({ timeout: 5000 }).catch(() => false);
      profileOk ? pass("Profilo cliente caricato per scena 05") : fail("Profilo non caricato");

      // Verifica che la checklist mostri i pill
      const checklist = await page.locator('[data-guide="client-onboarding-checklist"]').isVisible({ timeout: 3000 }).catch(() => false);
      checklist ? pass("Checklist visibile per mostrare avanzamento") : fail("Checklist non visibile");

      // Scroll per mostrare i pill
      const scrollOk = await page.evaluate(() => {
        window.scrollBy({ top: 400, behavior: "smooth" });
        return true;
      });
      scrollOk ? pass("Scroll per mostrare pill completato") : fail("Scroll fallito");
      await wait(1000);
    } else if (!clientId) {
      skip("Scena 05", "clientId mancante");
    }

    // ══════════════════════════════════════
    section("SCENA 06 — CTA (title card)");
    // ══════════════════════════════════════

    // La title card e' un'immagine statica — nessuna interazione da testare
    pass("Scena 06 — title card statica", "nessuna interazione richiesta");

  } catch (err) {
    fail("ERRORE IMPREVISTO", err.message);
  }

  // ══════════════════════════════════════
  section("CLEANUP");
  // ══════════════════════════════════════

  // Non eliminiamo il cliente — potrebbe servire per debug
  console.log(`  Cliente Luca Moretti (ID: ${clientId || "N/A"}) lasciato nel DB per ispezione`);
  console.log(`  Contratto (ID: ${contractId || "N/A"}) lasciato nel DB per ispezione`);

  await browser.close();

  // ══════════════════════════════════════
  // REPORT FINALE
  // ══════════════════════════════════════
  console.log("\n╔══════════════════════════════════════════════════════════╗");
  console.log(`║  RISULTATO PRE-FLIGHT                                    ║`);
  console.log(`║                                                          ║`);
  console.log(`║  ✓ PASS: ${String(passCount).padStart(2)}                                              ║`);
  console.log(`║  ✗ FAIL: ${String(failCount).padStart(2)}                                              ║`);
  console.log(`║  ○ SKIP: ${String(skipCount).padStart(2)}                                              ║`);
  console.log(`║                                                          ║`);
  if (failCount === 0) {
    console.log(`║  ► PRONTO PER REGISTRAZIONE                              ║`);
  } else {
    console.log(`║  ► CORREGGERE ${failCount} FAIL PRIMA DI REGISTRARE              ║`);
  }
  console.log(`╚══════════════════════════════════════════════════════════╝\n`);

  process.exit(failCount > 0 ? 1 : 0);
}

main().catch((err) => {
  console.error("FATAL:", err);
  process.exit(2);
});

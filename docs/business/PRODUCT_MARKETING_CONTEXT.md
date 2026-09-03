# Product Marketing Context — FitManager AI Studio

**Stato:** 🟢 RATIFICATO — gate A0 chiuso col founder il 2026-09-03 (righe gialle percorse una a
una: attestazione uso reale, pricing differito, email declassata a rossa su evidenza di codice).
Casa: `docs/business/` (contratto di specie G-DOC.3). Solo le righe 🟢 della claims matrix sono
claim esterni autorizzati.
**Data draft:** 2026-09-01 · **Ratifica:** 2026-09-03
**Fonti:** `MANIFESTO.md`, `CLAUDE.md`, `docs/business/BUSINESS_PLAN.md` (baseline marzo 2026,
superseded su claim e calendario), `docs/specs/SPEC_PRE_POC.md`, `docs/specs/SPEC_EXIT_ALESSIO.md`.
**Regola sovrana (D8):** nessun claim esterno non sostenuto da evidenza. In dubbio → riga GIALLA o
ROSSA della claims matrix, mai "verde per ottimismo".

---

## 1. Prodotto in una frase

FitManager è il CRM locale per chinesiologi, personal trainer e professionisti fitness a P.IVA:
clienti, schede, pagamenti e anamnesi in un unico strumento, con la scienza dell'allenamento
integrata e i dati che restano fisicamente sul computer del professionista. Si compra una volta,
non si paga ogni mese.

## 2. Cliente ideale (ICP)

- Chinesiologo o personal trainer italiano a P.IVA, 1:1 o piccoli gruppi, 15–40 clienti attivi.
- Oggi gestisce tutto con WhatsApp + Excel + PDF + carta. Perde 3–5 ore/settimana in amministrazione.
- Sensibile a: professionalità percepita dai clienti, errori clinici, incassi persi, GDPR.
- NON è l'ICP: palestre multi-sede, coach online puri senza rapporto 1:1, chi cerca app consumer.

**Persona di riferimento ("Marco"):** 32 clienti, anamnesi su Word, pagamenti su Excel, ogni lunedì
due ore per ricostruire chi ha pagato. Ha assegnato stacchi a un cliente con ernia perché il dato
era su un foglio dimenticato.

## 3. Il competitor vero

Non un altro software: **l'abitudine** (WhatsApp + Excel). Qualunque soluzione che chieda di
abbandonare WhatsApp parte sconfitta. FitManager non sostituisce WhatsApp — lo potenzia
(deep-link `wa.me`, messaggi pre-compilati, registro comunicazioni).

## 4. Posizionamento

Non "un altro SaaS per coach". L'unione — mai trovata insieme negli 11 vendor internazionali
esaminati (`LEGGI_COMPETITOR.md`); i competitor italiani restano da censire (lacuna N-1) — di:

1. **Locale e privato**: dati sul PC del professionista, zero cloud obbligatorio, privacy-first.
2. **Scienza deterministica e dimostrabile**: Safety Engine, volume MEV/MAV/MRV, analisi
   post-esecuzione muscolo per muscolo. Spiegabile, mai black-box.
3. **Finanza coerente**: contratti, rate, cassa, saldo — ricostruibile e auditabile.
4. **Italiano nativo**: lingua, workflow e contesto normativo italiani, non una traduzione.
5. **Si compra una volta**: licenza perpetua, non l'ennesimo abbonamento.

Tono: professionale, sobrio, italiano curato. Fiducia prima di feature density (MANIFESTO).
Mai hype, mai claim AI generici.

## 5. Claims matrix

Legenda: 🟢 dichiarabile oggi (evidenza nel repo o sul campo) · 🟡 gated (vero ma condizionato:
verificare o attendere un gate prima dell'uso esterno) · 🔴 non dichiarabile.

| Claim | Stato | Evidenza / gate |
|---|---|---|
| Dati in locale sul PC del trainer, zero cloud obbligatorio | 🟢 | Architettura (3 DB SQLite locali) |
| Il cliente compila l'anamnesi dal proprio telefono, senza app | 🟢 | Portale pubblico + tunnel, verificato in campo 2026-06-18 |
| Portale allenamento: il cliente vede la sessione e registra l'eseguito dal telefone | 🟢 | Feature attiva |
| Safety Engine: 47 condizioni cliniche, 80 regole automatiche | 🟢 | `condition_rules.py` |
| Catalogo esercizi con tassonomia muscoli/articolazioni (466 esercizi attivi) | 🟢 | catalog.db — usare 466, NON "500" del BP |
| WhatsApp semi-automatico: messaggi pre-compilati, un click e parte | 🟢 | 15 template, `communication_log` |
| Analisi post-esecuzione: compliance, volume vs target MEV/MAV/MRV, balance ratios | 🟢 | Training Intelligence + Workout Diff |
| CRM invisibile da Internet, solo il portale è esposto | 🟢 | Route separation middleware, testata |
| "Si compra una volta, non si paga ogni mese" (senza cifre) | 🟢 | Modello ratificato nel MANIFESTO/BP |
| "In uso quotidiano da una professionista reale dal 2026" | 🟢 | Attestazione founder 2026-09-03 (in campo su v1.0.10; la consegna v1.0.14 resta gate aperto della regia) |
| Prezzi specifici (€249 licenza, €79/anno PRO, €449 Box) | 🟡 | Pricing in HOLD fino a nuova strategia commerciale (E4). Decisione founder 2026-09-03: il kit design partner NON espone prezzi |
| "Nessun competitor (italiano) offre questa combinazione" | 🟡 | Ricerca su 11 vendor internazionali (`LEGGI_COMPETITOR.md`); competitor italiani MAI censiti (lacuna N-1). Vietato l'assoluto finché N-1 non chiude |
| Email automatiche (conferme, promemoria) | 🔴 | NON esiste nel prodotto (verificato 2026-09-03: zero SMTP/invio email in `api/`). Claim BP marzo superato; la comunicazione è WhatsApp |
| Funziona su Mac | 🔴 | C0/G-MAC non chiusi; canary con RED aperti. Nessun claim finché non consegnabile |
| Nutrizione italiana (880 alimenti CREA, piani LARN) | 🔴 | UI rimossa dal prodotto; backend dormiente. Non è una feature vendibile oggi |
| FitManager Box (dispositivo dedicato) | 🔴 | Strategia post-lancio, nessun artefatto consegnabile |
| FitScan / computer vision / analisi biomeccanica video | 🔴 | Visione di prodotto, non feature esistente |
| Numeri POC, clienti acquisiti, pipeline | 🔴 | Nessuna Wave 0 attiva; zero evidenza commerciale dichiarabile |

Regola d'uso: ogni materiale promozionale cita SOLO righe 🟢. Le righe 🟡 richiedono la verifica
indicata; le 🔴 non compaiono in nessuna forma, nemmeno come "coming soon", senza nuovo GO founder.

## 6. Obiezioni ricorrenti e risposte oneste

| Obiezione | Risposta |
|---|---|
| "E se mi si rompe il PC?" | Backup/restore integrato dei dati (`data/`). [Verificare wording finale post-G1] |
| "Devo pagare ogni mese?" | No. Licenza perpetua. L'assistenza con aggiornamenti è opzionale. |
| "I dati dei miei clienti dove finiscono?" | Sul tuo PC. Non esiste un nostro server con i tuoi dati. |
| "Devo cambiare come lavoro con WhatsApp?" | No. FitManager prepara i messaggi, li mandi dal tuo WhatsApp. |
| "Funziona senza Internet?" | Il CRM core sì, è locale. Serve la rete solo per il portale clienti. |
| "Ho un Mac" | Oggi Windows. [Riga 🔴: nessuna promessa Mac finché G-MAC non è consegnabile] |

## 7. Canali (dottrina ORB, post-exit)

- **Owned (prioritari):** dominio `fitmanagerstudio.com`, lista contatti founder, demo dal vivo.
  Ogni materiale e ogni contatto generato deve ricondurre QUI. Asset che sopravvivono a qualunque
  partner.
- **Borrowed (il partner commerciale, chiunque sarà):** amplificatore, mai proprietario del canale,
  del claim o della relazione. Il kit è partner-agnostic per costruzione: nessun materiale nomina
  il partner, nessun lead vive solo nella sua rubrica.
- **Rented (social):** non prioritari pre-POC. Nessun account/post prima della nuova strategia
  commerciale.

## 8. Vincoli non negoziabili sul materiale

1. Demo e preview SOLO con dati sintetici (SPEC_PRE_POC D5). Mai dati reali di clienti o trainer.
2. Nessun claim esterno nuovo prima della ratifica A0 (D8).
3. Privacy-first anche nel marketing: mai screenshot con dati riconoscibili.
4. Palette e identità visiva dal MANIFESTO: teal (oklch hue 170) + neutri stone/zinc, Inter +
   JetBrains Mono, tono professionale. Il materiale deve sembrare il prodotto.
5. Italiano curato. Zero anglicismi gratuiti, zero gergo growth-hacking.

## 9. Registro di ratifica (gate A0 — 2026-09-03)

- [x] Claims matrix percorsa col founder: uso reale ATTESTATO (🟢, wording onesto) · pricing
      DIFFERITO (kit senza prezzi; resta solo il claim qualitativo «si compra una volta») · email
      automatiche DECLASSATE a 🔴 su evidenza di codice · riga competitor gated su lacuna N-1.
- [x] Conoscenza competitor viva estratta in `LEGGI_COMPETITOR.md` (W1-W11, L1-L6, lacune N).
- [x] Tono/posizionamento approvati con la ratifica del documento.
- [ ] Pricing comunicabile: riapre con la nuova strategia commerciale (E4).
- [ ] Lacuna N-1 (competitor italiani): ricerca da pianificare prima di ogni claim assoluto.

# Leggi competitor — conoscenza viva del mercato

**Specie:** verità commerciale corrente (contratto di specie `docs/business/`, G-DOC.3).
**Provenienza:** estrazione sanzionata (A0, 2026-09-03) dalle ricerche archiviate
`docs/archive/RICERCA_COMPETITOR_WALLET_SEDUTE_SINGOLE_2026-07-07.md` (11 vendor, leggi W) e
`docs/archive/RICERCA_COMPETITOR_TRASPARENZA_FINANZIARIA_2026-07-06.md` (leggi L). L'evidenza
vendor-per-vendor resta negli archivi; qui vivono le LEGGI e le LACUNE, citabili come contesto di
lavoro. Aggiornare QUESTO file se nuova ricerca conferma/smentisce una legge.

## Leggi W — wallet, sedute singole, insoluto (W1–W11)

- **W1** — Pack e seduta singola sono due semantiche distinte che convivono: il pack è un'entità a
  scalare a catalogo, la singola è un prezzo contestuale all'atto, mai un prodotto a listino.
- **W2** — Prenotare senza pagare è una scelta esplicita che genera un insoluto TRACCIATO, mai un
  default silenzioso né un blocco muto.
- **W3** — Il pack esaurito/scaduto degrada in modo esplicito e recuperabile (fallback a prezzo
  pieno, eccedenze marcate unpaid, estensione manuale) — mai cancellazione silenziosa del valore.
- **W4** — Il wallet è un ledger immutabile con segno e semantica dichiarata: ogni rettifica è una
  transazione inversa, ogni movimento ha una riga.
- **W5** — Wallet e insoluto sono grandezze SEPARATE: il credito non riduce il dovuto finché non è
  APPLICATO con un atto; la compensazione è un evento registrato, non uno stato implicito.
- **W6** — L'applicazione del credito per operatore umano è un PROMPT con controllo totale su
  importo e destinazione (auto-apply solo opt-in; mai silente).
- **W7** — L'insoluto vive su DUE livelli insieme: entità per-visita riconciliabile + aggregato
  per-cliente, con reminder al contatto successivo.
- **W8** — La penale è un evento economico di prima classe; il condono (waive/write-off) è
  un'azione esplicita e tracciata, mai un'omissione.
- **W9** — Nessun vendor ha un listino per-cliente né un prezzo SUGGERITO dallo storico: l'importo
  libero è la norma. **Il «consigliato dallo storico» non esiste in nessuna documentazione
  esaminata = unicità FitManager** (innovazione senza benchmark: lacuna N-6).
- **W10** — Il residuo (sedute rimanenti, saldo, scadenza) è visibile BILATERALMENTE, trainer e
  cliente, come standard di trasparenza.
- **W11** — L'acconto ha due contabilizzazioni possibili e dichiarate (part-payment del documento o
  liability finché non applicato); le rate sono milestone dello STESSO documento.

## Leggi L — presentazione finanziaria a non-contabili (L1–L6)

- **L1** — Il ledger ha una colonna «Saldo» progressivo, separata dagli importi, valida solo in
  ordine cronologico; su vista filtrata si nasconde, mai ricalcolata sul sottoinsieme.
- **L2** — Il netto non sostituisce mai il lordo: è una derivazione esplicita col breakdown
  `lordo − rimborsi` visibile; il rimborso resta riga negativa.
- **L3** — Posizione ORA (header, 1-2 numeri, sempre visibile) e storia (ledger, drill-down) sono
  due viste separate.
- **L4** — Il denaro dovuto/scaduto è un segnale push always-visible, MAI dietro toggle.
- **L5** — Nei dialog monetari si pre-compilano i VALORI sicuri, non le DECISIONI; ogni esito è una
  scelta esplicita.
- **L6** — Palette chiusa e semantica: il colore è rinforzo dello stato; il segnale primario sui
  numeri è il segno `−€`.

## Lacune dichiarate (guardrail sui claim commerciali)

- **N-1 — Competitor ITALIANI mai censiti** (TeamSystem Wellness, Sportclubby, Wansport,
  Sportrick/EGO, Gym-Up): la ricerca è al 100% su vendor anglofoni. **Conseguenza commerciale:
  vietato il claim assoluto «nessun competitor italiano offre X» finché N-1 non chiude.**
- **N-2** — Gestionali sanitari/parasanitari italiani (GipoNext, MioDottore, Fisiotools) non
  ricercati: per fatturazione e percorsi il chinesiologo è più vicino a loro che a Mindbody.
- **N-3** — Quadro normativo italiano (contanti, POS, bollo, forfettari, recesso 14gg, penali) non
  ricercato.
- **N-4** — Rail di pagamento italiani (Satispay, SumUp, Nexi) non ricercati.
- **N-5** — Aggregatori welfare (Wellhub, Fitprime, Edenred) solo lato doc estero.
- **N-6** — Suggested pricing dallo storico: zero benchmark (vedi W9 — è l'unicità, senza rete).
- **N-7** — Dunning relazionale manuale 1:1 (solleciti WhatsApp) non ricercato.
- **N-8** — Netting wallet↔insoluto stesso cliente: nessuna sintesi comparata.

## Consumatori di questo documento

Product: ADR-025 + `docs/specs/hold/SPEC_P_*` (W1-W11) · G8.4/FT (L1-L6) · Commerciale:
`PRODUCT_MARKETING_CONTEXT.md` (claims matrix, riga competitor gated su N-1) e kit design partner.

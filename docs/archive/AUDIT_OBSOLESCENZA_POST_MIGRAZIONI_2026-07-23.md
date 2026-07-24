# AUDIT OBSOLESCENZA POST-MIGRAZIONI — 2026-07-23

**Stato:** ✅ CONCLUSO, VERIFICATO E FOLDATO — fotografia del codice al 2026-07-23
**Trigger:** richiesta founder — dopo le migrazioni recenti (tunnel FRP su VPS Hetzner, filone economico-finanziario G7-G9, rimozione Nutrition UI, dismissione dual-env) alcune sezioni sono obsolete: confondono l'utente e generano rumore nel codice.
**Metodo:** workflow multi-agente contenuto (budget-aware): 6 auditor read-only in parallelo (tunnel, finanza BE, finanza FE, drift docs, dead-code FE, dead-code BE/tools) + 1 critico adversariale che ha ri-verificato nel codice tutti i finding ALTA e i MEDIA user-facing. 54 finding grezzi → **42 verificati: 41 CONFERMATI, 1 RIDIMENSIONATO (DOC-4), 0 falsi positivi**; i 12 BASSA sono fuori campione di verifica (dichiarato). Il critico ha aggiunto 5 aree che nessun auditor aveva censito (§9). Regola di prova: ogni finding ha evidenza file:riga e/o grep zero-consumatori rifatto dal critico.

**Esito operativo (founder 2026-07-24):** i blocker release-critical sono foldati in
`docs/specs/SPEC_R0_PROTEZIONE_RELEASE_V1_0_15.md`; la bonifica massiva è differita dopo la candidate
v1.0.15 e richiederà una SPEC dedicata. Sequenza ratificata: R0.1→R0.4 → P1..P6 → candidate → G-MAC.

**Errata della verifica indipendente 2026-07-24:** il verdetto originario «0 falsi positivi» e le
stime restano parte della fotografia, ma non governano il lavoro vivo. I sorgenti tracciati con
`crm_dev` sono 34, non 63 (29 match erano `.pyc` ignorati); `workspace_engine.py` non è morto perché
`/workspace/today` ne consuma il nucleo, quindi solo i rami list/detail sono candidati; Nutrition è
autenticato e non esposto dal tunnel pubblico corrente; la dismissione completa Tailscale resta Fase 3.

> Documento storico: non è contesto di lavoro e non prescrive l'implementazione. La posizione in
> `docs/archive/` dichiara l'audit concluso; decisioni, scope e criteri vivi sono nella SPEC R0.

---

## 1. Sintesi esecutiva

Quattro macro-temi, in ordine di danno:

1. **Il prodotto spinge ancora verso Tailscale mentre FRP è in produzione** (TN-1, TN-2, TN-8, MB-1, MF-3 — convergono sullo stesso sottosistema). Il sottosistema «Connettività» (card in dashboard, wizard in Impostazioni, 4 endpoint diagnostici) conosce solo Tailscale: su un'installazione FRP classifica il profilo `local_only` e propone al trainer «Installa Tailscale». Peggio: `launcher.bat` shipped in v1.0.14 ri-avvia `tailscale funnel` a ogni boot se `PUBLIC_PORTAL_ENABLED=true` — il doppio percorso di esposizione che TUNNEL_SECURITY_BOUNDARY vieta «a regime». La Fase 3 (dismissione Tailscale) è pianificata nei doc ma NON ha una spec aperta in `docs/specs/`.
2. **Finanza: superfici legacy che contraddicono il netto SSoT** (FF-1, FF-2, FB-1..FB-4). ContrattiTab del profilo cliente mostra il versato LORDO mentre /contratti mostra il netto (AC-G84-1 dichiarato chiuso, superficie mancata dal gemello); il dropdown EventForm mostra «(N crediti)» includendo i contratti CHIUSI (l'esatto caso-panico founder del 2026-07-07, già gated su SPEC_P P4/P5); doppie vie di calcolo raw-SQL sopravvissute al SSoT (`expiring_contracts`, `workspace_engine`); campi wire morti calcolati con query costose a ogni load dashboard (`ledger_alerts`, `saldo_attuale`).
3. **~6.800 LOC morte nel frontend + gemelli backend** (MF-1..MF-9, CR-1, CR-4). Cluster ProgressiTab (~3.070 LOC), cluster workspace FE (~1.170 LOC) col gemello backend `workspace_engine` (~3.000 LOC, endpoint montati ma con zero consumatori), Smart Programming client-side (~1.070 LOC), export Excel (900 LOC), OverdueRatesSheet (264 LOC, superseded dal deep-link FE-1.0), più l'alert `overdue_rates` che il backend calcola a ogni poll e la UI scarta sempre. Residui dual-env: `migrate-all.sh` («REGOLA BLINDATA») oggi RICREA il crm_dev.db dismesso; **63 file** in tools/ citano ancora `crm_dev` (il censimento iniziale ne aveva visti 8).
4. **Doc operative che guidano verso azioni sbagliate** (TN-3, TN-4, DOC-1..DOC-3, FF-3, CR-3, CR-5). RELEASE_CHECKLIST istruisce verifiche di release su Tailscale/Funnel (con checkbox aperta sul sistema superato) e contiene numeri catalogo pre-ADR-003; i 3 CLAUDE.md documentano come attivi pattern rimossi (OverdueRatesSheet, colonna Finanze, ProgressiTab, dual-DB, `proxy.ts` inesistente, «14 vs 15 template»); il tour in-app (`guide-tours.ts`) descrive una pagina Clienti che non esiste più (colonne crediti/contratti rimosse da FE-0 privacy, stati «in pausa/archiviato» mai esistiti).

## 2. Piano d'azione raccomandato

Nessuna modifica è stata applicata: le fasce sotto sono la proposta di sequenza.

### Fascia A — Quick win (rimozione secca / correzione doc, zero dipendenze da spec)

1. **`launcher.bat` righe 76-101** (TN-2): rimuovere l'auto-avvio Tailscale Funnel. Il più urgente: shipped in v1.0.14, riattiva il percorso vietato dal security boundary. Da fare PRIMA della consegna a Chiara.
2. **`tools/scripts/migrate-all.sh`** (MB-2): rimozione + fix `api/CLAUDE.md:321` (un solo `alembic upgrade head` su crm.db).
3. **Cluster FE morti** (MF-1, MF-2, MF-4..MF-9 + CR-1, CR-4): rimozione in commit dedicati con build verde; insieme al FE cadono gli endpoint workspace backend e l'alert `overdue_rates` mai consumato.
4. **Correzioni doc** (TN-3..TN-7, TN-9, DOC-1..DOC-3, FF-3, FF-7, FB-5, FB-8, FB-11, FB-12, CR-3, CR-5): RELEASE_CHECKLIST (sezione rete su FRP + numeri catalogo), CLAUDE.md root (WhatsApp 14/15, stato Fase 1 FRP), frontend/CLAUDE.md, api/CLAUDE.md, guide-tours.ts, SUPPORT_RUNBOOK, LAUNCH_SCOPE, POST_LAUNCH_ROADMAP_90D, TUNNEL_ARCHITECTURE (`https2https`→`https2http`).
5. **`live-01-dashboard.png`** dalla root (MF-10): spostare o eliminare.

### Fascia B — Decisione founder (merita mini-spec o scelta esplicita)

1. **Dismissione sottosistema Connettività** (TN-1, MB-1, MF-3, TN-8) = anticipo del punto 3.7 della Fase 3: card dashboard + wizard + endpoint `connectivity-*` + regex CORS 100.x + copy «o Tailscale». La Fase 3 non ha spec aperta: da aprire. Interim minimo: neutralizzare i prompt Tailscale quando `GET /system/tunnel-status` riporta tunnel attivo.
2. **Router nutrition montato e scrivente senza UI** (MB-3): 26 endpoint raggiungibili, anche CRUD su crm.db — dormiente ESPOSTO. Decidere se smontarlo in compiled mode (il backend resta preservato).
3. **Endpoint Training Science / methodology senza consumatori** (MB-5, MB-6): tenere per roadmap o smontare.
4. **Bonifica tools/ su crm_dev** (MB-4 + CR-2): il perimetro reale è 63 file (molti anche pre-ADR-003) — pianificare archiviazione in blocco, non spot-fix sugli 8 censiti.
5. **Campi wire morti costosi** (FB-2, FB-6): `ledger_alerts`/`saldo_attuale` e `percentuale_versata` & co. — rimuovere dal wire o dare un consumatore. Il PIN `posizione_netta_contratto` (FB-10) resta per scelta founder dichiarata.

### Fascia C — GIÀ gated su spec aperte (non toccare fuori sequenza)

1. **`crediti_residui_attivi` + dropdown onesto** (FB-1, FF-2, FF-4) → SPEC_P **P4/P5**. Confermato che il campo non esiste ancora nel codice.
2. **ContrattiTab a netto SSoT** (FF-1) → riaprire **SPEC_G8.4 F1.a** + estendere il gemello anti-vacuità in `test_semantic_guards.py`: AC-G84-1 dichiarato chiuso con superficie mancata è anche un finding di processo (il gemello non copriva tutte le superfici che la spec elenca).
3. **`signed_contractual_amount`** (FB-7): zero caller oggi, ma ADR-022/SPEC_G9 la descrivono come posting-rule della penna — verificare se P1 (blocco P) la attende prima di rimuoverla.

---

## 3. Tunnel e infrastruttura (Tailscale -> FRP)

### TN-1 — Sottosistema 'Connettivita' interamente Tailscale-based ancora attivo e visibile: con tunnel FRP attivo classifica il profilo 'local_only' e guida il trainer a installare Tailscale

- **Severita:** ALTA · **User-facing:** SI · **Verdetto critico:** CONFERMATO
- **File:** `api/services/connectivity_runtime.py`, `api/services/connectivity_verify.py`, `api/services/connectivity_config.py`, `api/schemas/system.py`, `frontend/src/components/dashboard/ConnectivityOnboardingCard.tsx`, `frontend/src/components/dashboard/connectivity-onboarding.ts`, `frontend/src/components/settings/ConnectivitySetupWizard.tsx`, `frontend/src/components/settings/connectivity-wizard-panels.tsx`, `frontend/src/app/(dashboard)/page.tsx`, `frontend/src/app/(dashboard)/impostazioni/page.tsx`
- **Evidenza:** connectivity_runtime.py:202-218 `_resolve_profile` conosce SOLO tailscale_connected/funnel_enabled, ignora il TunnelManager FRP: su un'installazione FRP (Tailscale assente) il profilo e' 'local_only' e `_resolve_next_action` (righe 229-240) ritorna ('install_tailscale', 'Installa Tailscale sul PC'). La card e' montata in dashboard page.tsx:150 (prompt 'Configura l'accesso da tablet...' per profilo local_only, connectivity-onboarding.ts:18-25) e in impostazioni/page.tsx:126; il wizard mostra 'Scarica Tailscale' (connectivity-wizard-panels.tsx:47-49) e il comando `tailscale funnel --bg <porta>` (ConnectivitySetupWizard.tsx:88). Conflitto env (punto d del mandato): connectivity_config.py:20-22+94 scrive PUBLIC_BASE_URL/PUBLIC_PORTAL_ENABLED manuali (anche ts.net) in data/.env e in os.environ, sovrascrivendo a runtime l'auto-set FRP di main.py:335-341. Coesistenza pianificata (Fase 3 non eseguita) ma il prodotto attivo spinge verso il sistema superato.
- **Superseded da:** Tunnel FRP auto-start (api/main.py lifespan step 6) + GET /system/tunnel-status (api/routers/system.py:28)
- **Azione raccomandata:** gated su spec aperta (NESSUNA esiste in docs/specs/ per la Fase 3: da aprire; nel frattempo minimo intervento = neutralizzare i prompt Tailscale quando GET /system/tunnel-status riporta tunnel attivo)
- **Tracciato in:** docs/technical/TUNNEL_ARCHITECTURE.md §8.5 Fase 3 (3.1 UI diagnostica tunnel, 3.7 dismissione) + TUNNEL_SECURITY_BOUNDARY.md §7 — non in una spec aperta

### TN-2 — launcher.bat (shipped nell'installer v1.0.14) auto-avvia ancora Tailscale Funnel a ogni boot se PUBLIC_PORTAL_ENABLED=true in data/.env — doppio percorso di esposizione vietato 'a regime' dal security boundary

- **Severita:** ALTA · **User-facing:** SI · **Verdetto critico:** CONFERMATO
- **File:** `installer/launcher.bat`, `installer/fitmanager.iss`
- **Evidenza:** launcher.bat:76-101: se data/.env contiene PUBLIC_PORTAL_ENABLED=true (scritto dal wizard Connettivita, connectivity_config.py:21) esegue `tailscale funnel --bg %FRONTEND_PORT%` (righe 89 e 95, con fallback su C:\Program Files\Tailscale). fitmanager.iss:67 conferma che launcher.bat e' installato ed e' l'entry point (icone righe 93-94). Su installazioni pre-FRP con Tailscale ancora presente il vecchio funnel ts.net viene riattivato in parallelo al tunnel FRP. TUNNEL_SECURITY_BOUNDARY.md:12-13: 'Le due strategie NON devono coesistere a regime. FRP e' l'unico percorso target'; §7:197 acceptance 'una richiesta al vecchio endpoint Tailscale non deve raggiungere il CRM'.
- **Superseded da:** TunnelManager frpc auto-start (api/services/tunnel_manager.py + main.py lifespan step 6)
- **Azione raccomandata:** rimozione secca (blocco righe 76-101 di launcher.bat; il tunnel FRP e' gia' auto-avviato dal backend)
- **Tracciato in:** docs/technical/TUNNEL_SECURITY_BOUNDARY.md §7 (dismissione Tailscale) — non in una spec aperta

### TN-3 — RELEASE_CHECKLIST.md sezione 'Rete e Accesso' guida la release su verifiche Tailscale/Funnel (con URL ts.net reale) e non contiene alcuna verifica del tunnel FRP

- **Severita:** ALTA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `docs/operations/RELEASE_CHECKLIST.md`
- **Evidenza:** Righe 60-68: '[x] Backend binding: --host 0.0.0.0 (LAN + Tailscale)', '[x] CORS ... Tailscale (100.x.x.x)', '[x] Tailscale Funnel: https://giacomo.tail8a3bc3.ts.net/', '[x] Test Tailscale VPN da rete esterna', '[ ] Test anamnesi self-service da smartphone via Funnel' (checkbox APERTA che chiede un test sul sistema superato). Zero menzioni di frpc/edge.fitmanagerstudio.com/tunnel-status, mentre il tunnel FRP e' in produzione dal 2026-06-18 (validato live con Alessio). Doc operativa che a ogni release indirizza verifiche sul percorso legacy.
- **Superseded da:** Tunnel FRP in produzione (v1.0.13, TUNNEL_ARCHITECTURE.md §8.1 Fase 0+1 completate)
- **Azione raccomandata:** correzione doc (sostituire la sezione 5 con verifiche FRP: tunnel-status, https://<instance_id>.fitmanagerstudio.com, route separation 404)

### TN-4 — LAUNCH_SCOPE.md e POST_LAUNCH_ROADMAP_90D.md (doc vivi di governance/prodotto) pianificano l'accesso mobile su 'Tailscale full-app' — architettura superata da FRP + Strada B

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `LAUNCH_SCOPE.md`, `docs/product/POST_LAUNCH_ROADMAP_90D.md`
- **Evidenza:** LAUNCH_SCOPE.md:37 'validazione reale LAN / Tailscale / Funnel' e :52 'strategia di accesso mobile (PWA + Tailscale full-app)'. POST_LAUNCH_ROADMAP_90D.md:60-71 intera sezione '1.3 Tailscale Full-App' ('Estensione Funnel: esporre porta 3000 completa', 'UI Accesso Remoto con URL Tailscale + QR'), :91 milestone '[ ] Tailscale full-app funzionante con JWT protection', :136-140 provisioning Box basato su `tailscale up --authkey`, :214 'SSH via Tailscale per supporto'. L'apertura del CRM da remoto e' oggi progettata come 'Strada B' sul tunnel FRP (TUNNEL_SECURITY_BOUNDARY.md:12-13: FRP unico percorso target). Doc di pianificazione che orienterebbero lavoro futuro sul sistema da dismettere.
- **Superseded da:** FRP self-hosted + Strada B (docs/technical/TUNNEL_SECURITY_BOUNDARY.md, approvata non implementata)
- **Azione raccomandata:** correzione doc (riscrivere le sezioni accesso remoto/Box su FRP + Strada B; per LAUNCH_SCOPE basta aggiornare le 2 righe)

### TN-5 — CLAUDE.md root: la sezione FRP dichiara ancora pendenti 'bundle frpc in Nuitka, script provisioning DNS, health endpoint' — tutti e tre superati nel codice

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `CLAUDE.md`
- **Evidenza:** CLAUDE.md sezione 'Fase di sviluppo': 'Fase 1: CORE COMPLETATA ... Rimangono: bundle frpc in Nuitka, script provisioning DNS, health endpoint'. Realta' verificata: (1) frpc.exe e' staged nel bundle da tools/build/build-installer.sh:125-134 con gate d'errore se assente; (2) GET /system/tunnel-status esiste (api/routers/system.py:28-38); (3) il provisioning DNS per-istanza e' dichiarato 'NON NECESSARIO (wildcard DNS)' in TUNNEL_ARCHITECTURE.md §8.2 gap G12. La stessa TUNNEL_ARCHITECTURE.md §8.1 (v3.0, 2026-06-14) marca Fase 1 COMPLETATA inclusi frpc bundle e health endpoint. L'entry point di contesto contraddice la SSoT e il codice.
- **Superseded da:** tools/build/build-installer.sh:125-134 + api/routers/system.py:28 + TUNNEL_ARCHITECTURE.md §8.2 G12
- **Azione raccomandata:** correzione doc (allineare la riga Fase 1 a TUNNEL_ARCHITECTURE §8.1: completata, restano solo Fase 2/3)

### TN-6 — TUNNEL_ARCHITECTURE.md §8.3: esempio config frpc con plugin `https2https` mentre il codice genera `https2http` (e path cert relativi vs assoluti)

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `docs/technical/TUNNEL_ARCHITECTURE.md`, `api/services/tunnel_manager.py`
- **Evidenza:** TUNNEL_ARCHITECTURE.md:252 blocco 'Config FRP client (generata automaticamente da tunnel_manager.py)' mostra `type = "https2https"` e `crtPath = "data/tunnel/cert.pem"`; il codice reale genera `type = "https2http"` (tunnel_manager.py:240, frpc termina TLS e inoltra HTTP in chiaro a 127.0.0.1:3000) e path assoluti (`config.cert_path.as_posix()`, riga 242). CLAUDE.md root e il docstring di generate_frpc_toml descrivono correttamente https2http. Nota positiva del mandato (c): il resto del doc e' verificato coerente col mondo reale — Cloudflare registrar/DNS wildcard 'nuvola grigia' (righe 292-297), Hetzner CPX22 128.140.91.39 (§9.2), frps v0.61.1 (riga 339) = CLAUDE.md.
- **Azione raccomandata:** correzione doc (allineare l'esempio §8.3 all'output reale di generate_frpc_toml)

### TN-7 — SUPPORT_RUNBOOK.md §3: la scaletta diagnostica del portale pubblico instrada verso il wizard Connettivita (Tailscale) e i 'comandi Tailscale/Funnel' come escalation finale

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `docs/operations/SUPPORT_RUNBOOK.md`
- **Evidenza:** Righe 97-102: per problemi al portale pubblico prescrive '1. Aprire Impostazioni -> Connettivita. 2. Completare o ricontrollare il wizard fino allo step finale. ... 5. Solo dopo passare al test manuale da smartphone o ai comandi Tailscale/Funnel'. Su un'installazione FRP (Alessio, produzione) il wizard chiederebbe di installare Tailscale (vedi finding 1) e i comandi Funnel non c'entrano: il percorso corretto e' GET /system/tunnel-status + log frpc + TUNNEL_ARCHITECTURE §11. La riga 36-38 del runbook e' invece gia' corretta (rimanda a FRP con legacy in archive) — doc aggiornato a meta'.
- **Superseded da:** GET /system/tunnel-status + docs/technical/TUNNEL_ARCHITECTURE.md §11 (operations)
- **Azione raccomandata:** correzione doc (riscrivere gli step 1-5 di §3 sul percorso FRP)

### TN-8 — Copy UI visibile al trainer suggerisce ancora 'o Tailscale' come rimedio nei dialog di condivisione link (scheda e anamnesi)

- **Severita:** MEDIA · **User-facing:** SI · **Verdetto critico:** CONFERMATO
- **File:** `frontend/src/components/workouts/BuilderHeader.tsx`, `frontend/src/app/(dashboard)/clienti/[id]/anamnesi/page.tsx`
- **Evidenza:** BuilderHeader.tsx:353-357: warning amber quando hostname=localhost — 'Per inviare il link al cliente, accedi al CRM tramite IP LAN (es. 192.168.1.23:3000) o Tailscale.' Stesso copy in clienti/[id]/anamnesi/page.tsx:354 (') o Tailscale.'). Con licenza FRP i link pubblici usano gia' PUBLIC_BASE_URL auto-settato dal tunnel (main.py:335-341): il consiglio Tailscale e' superato e puo' spingere il trainer a installare un client inutile. Residuo attivo che confonde, non coesistenza pianificata (e' copy di prodotto, non infrastruttura).
- **Superseded da:** PUBLIC_BASE_URL auto da tunnel FRP (api/main.py:335-341)
- **Azione raccomandata:** correzione doc (aggiornare il copy: rimuovere 'o Tailscale'; se tunnel attivo il warning localhost e' spesso superfluo)

### TN-9 — e2e_distribution_rehearsal.py: la checklist manuale pre-consegna stampa ancora 'Access via Tailscale VPN from external network' e nessun passo sul tunnel FRP

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `tools/admin_scripts/e2e_distribution_rehearsal.py`
- **Evidenza:** Riga 485: 'print(f"  [ ] Access via Tailscale VPN from external network")' dentro la checklist finale del rehearsal di distribuzione (righe 482-488). Nessuna occorrenza di 'frp'/'fitmanagerstudio' nello script (grep frpc su tools/ trova solo tools/build/build-installer.sh). Lo script guida la prova pre-consegna al cliente su un canale superato invece del test tunnel FRP (aprire https://<instance_id>.fitmanagerstudio.com/public/... da rete esterna).
- **Azione raccomandata:** correzione doc (aggiornare le voci checklist dello script al percorso FRP)

### TN-10 — Config dev e commenti residui ts.net/Tailscale Funnel sparsi in frontend e backend (allowedDevOrigins '*.ts.net' incluso)

- **Severita:** BASSA · **User-facing:** no · **Verdetto critico:** non verificato (fuori campione critico)
- **File:** `frontend/next.config.ts`, `frontend/src/lib/api-client.ts`, `frontend/src/lib/media.ts`, `frontend/src/app/public/anamnesi/[token]/page.tsx`, `api/routers/public_portal.py`
- **Evidenza:** next.config.ts:8-10 `allowedDevOrigins: ["*.ts.net"]` ('Consenti richieste cross-origin da Tailscale Funnel in dev') — in FRP il dominio dev e' *.fitmanagerstudio.com, la entry ts.net e' morta; commenti stale anche a :33 ('Security headers per HTTPS (Tailscale Funnel)'), :51, :71. api-client.ts:7,40, media.ts:9 ('falliscono via Tailscale Funnel'), app/public/anamnesi/[token]/page.tsx:19, public_portal.py:170 ('es. https://nome.ts.net'). Solo commenti/config dev: nessun effetto runtime in produzione, ma tramandano il modello mentale superato a chi manutiene.
- **Azione raccomandata:** rimozione secca (entry '*.ts.net' e riferimenti nei commenti; sostituire gli esempi con *.fitmanagerstudio.com)

## 4. Finanza backend (superseded da G7-G9)

### FB-1 — crediti_residui client-level non filtra i contratti chiusi — il dropdown EventForm e i filtri 'con crediti' mostrano crediti di contratti CHIUSI

- **Severita:** ALTA · **User-facing:** SI · **Verdetto critico:** CONFERMATO
- **File:** `C:/Users/gvera/Projects/FitManager_AI_Studio/api/routers/clients.py`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/agenda/EventForm.tsx`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/app/(dashboard)/clienti/page.tsx`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/app/(dashboard)/comunicazioni/page.tsx`
- **Evidenza:** Stato verificato al 2026-07-23: `_calc_credits_batch` (clients.py:286-338) — Query 1 (righe 307-315) somma `crediti_totali` di TUTTI i contratti non eliminati con commento deliberato riga 306 «chiuso NON filtrato». L'interim fix G9.7.1-bis c'è (riga 327: `Event.id_contratto != None`, le orfane non consumano), ma il gap chiuso resta. Consumo UI: EventForm.tsx:293 rende «({client.crediti_residui} crediti)» nel dropdown — l'esatto caso panico founder («(2 crediti)» da contratto CHIUSO accanto a warning «nessun contratto attivo», riga 183-188); clienti/page.tsx:227 e comunicazioni/page.tsx:102 filtrano «con crediti» sullo stesso campo. `crediti_residui_attivi` non esiste ancora nel codice (grep api/ e frontend/src: zero occorrenze fuori da SPEC_P).
- **Azione raccomandata:** gated su spec aperta (docs/specs/SPEC_P_PRESTAZIONI_SINGOLE_E_PORTAFOGLIO.md — P4 aggiunge `crediti_residui_attivi` su ClientResponse, P5 il dropdown onesto)
- **Tracciato in:** docs/specs/SPEC_P_PRESTAZIONI_SINGOLE_E_PORTAFOGLIO.md §P4 (riga 199) + §P5 (riga 223); root cause in docs/operations/AUDIT_FE_SEGNALI_E_SELETTORI_2026-07-07.md

### FB-2 — DashboardSummary.ledger_alerts + saldo_attuale: campi wire morti calcolati con query costose, e il raw SQL di divergenza è un TERZO interprete one-sided dell'àncora ledger

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `C:/Users/gvera/Projects/FitManager_AI_Studio/api/routers/dashboard.py`, `C:/Users/gvera/Projects/FitManager_AI_Studio/api/schemas/financial.py`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/types/api.ts`
- **Evidenza:** Zero consumatori FE provato: grep `ledger_alerts` in frontend/src → SOLO types/api.ts:1114 (definizione tipo, nessun componente lo legge); grep `saldo_attuale` → la dashboard non lo usa mai (cassa/page.tsx:419 legge `balance.saldo_attuale` da GET /movements/balance, tipo diverso a api.ts:1131). Eppure ogni GET /dashboard/summary esegue: (a) raw SQL divergenza versato-vs-ledger su TUTTI i contratti (dashboard.py:145-156) e (b) `_compute_saldo` full-ledger (riga 159). Il raw SQL (a) verifica SOLO il lato versato — interprete pre-G9.0b superseded da `/reconciliation` bidirezionale (dashboard.py:186-211, I5 raffinata con wallet riassorbito) e da `project_columns_from_ledger` (ledger.py:159, «derivazione UNICA»). Coerente con la scelta privacy (guide-tours.ts:267: «dati finanziari solo in Cassa»).
- **Superseded da:** G9.0b /reconciliation bidirezionale + ledger.project_columns_from_ledger (ADR-022)
- **Azione raccomandata:** rimozione secca (i 2 campi da DashboardSummary + le 2 query in get_dashboard_summary; il presidio divergenze resta in /reconciliation e nel sensore invariant_gate)

### FB-3 — Alert expiring_contracts in /dashboard/alerts: raw SQL che riconta l'occupazione crediti per conto suo, sopravvissuto alla ritirata G9.7.3 accanto all'«UNICO interprete» _occupazione_breakdown_map

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `C:/Users/gvera/Projects/FitManager_AI_Studio/api/routers/dashboard.py`
- **Evidenza:** dashboard.py:1214-1243: subquery scalare `SELECT COUNT(*) FROM agenda ... stato IN :stati_occupazione` + NOT EXISTS rinnovo — duplica nello STESSO file l'interprete `_occupazione_breakdown_map` (righe 630-660, docstring «UNICO interprete... mai due query divergibili») che il gemello `get_expiring_contracts` usa (riga 482). SPEC_G9.7 riga 103 dichiara «la raw-SQL COUNT dell'expiring RITIRATA» — vero solo per la worklist, non per l'alert: due implementazioni dello stesso predicato che possono divergere (il pattern dichiarato in api/CLAUDE.md è helper condiviso → count == len(items)). Nota: anche contracts.py:438-454 ha una copia gemella del group-by (dichiarata «stesso interprete», ma è codice duplicato, non delegato).
- **Azione raccomandata:** rimozione secca (del raw SQL dell'alert, delegando a _occupazione_breakdown_map come già fatto per la worklist)
- **Tracciato in:** parzialmente: docs/specs/SPEC_G9.7_SEMANTICA_PER_CLASSE.md riga 103 (fold-back D5 che dichiara la ritirata — il sito alert non è censito)

### FB-4 — workspace_engine: 3 conteggi raw-SQL dell'occupazione crediti + crediti_residui inline — l'ultimo debito Giro 2 rimasto vivo

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `C:/Users/gvera/Projects/FitManager_AI_Studio/api/services/workspace_engine.py`
- **Evidenza:** Tre raw SQL che ricontano l'occupazione (righe 1240-1256 `_load_expiring_contract_rows`, 1400, 2157 — grep STATI_OCCUPAZIONE_CREDITO) invece di delegare all'interprete batch, più `residual = max(total - used, 0)` inline a riga 1264 che duplica `contract_state.crediti_residui()` (contract_state.py:96). Consumano il frozenset SSoT (parametrizzato) quindi non violano il test semantico, ma restano interpreti paralleli di dashboard._occupazione_breakdown_map. Da notare: gli altri siti che la spec censiva sono GIÀ delegati (righe 1151 e 1341 usano `cstate.residuo()`).
- **Azione raccomandata:** gated su spec aperta (docs/specs/SPEC_VOCABOLARIO_E_CLASSIFICAZIONE_CONTRATTI.md — Giro 2 §3.2, AC-G2-2)
- **Tracciato in:** docs/specs/SPEC_VOCABOLARIO_E_CLASSIFICAZIONE_CONTRATTI.md §3.2 (Stato: «Giro 2 PENDENTE»)

### FB-5 — SPEC_VOCABOLARIO §3.2: censimento inline-residuo STALE — 3 dei 4 siti elencati sono già stati migrati, il work-queue guida verso lavoro già fatto

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `C:/Users/gvera/Projects/FitManager_AI_Studio/docs/specs/SPEC_VOCABOLARIO_E_CLASSIFICAZIONE_CONTRATTI.md`
- **Evidenza:** La spec (righe 310-328, 353-356) elenca come debito: `_build_payment_due_soon_cases` e `_build_contract_renewal_cases` con formula inline `prezzo−versato` → OGGI delegano a `cstate.residuo()` (workspace_engine.py:1151 e 1341, commento «SSoT (SPEC_REVISIONE_PRE_G7 §A)»); `dashboard.py:497` inline-residuo senza clamp → NON esiste più (grep `prezzo_totale -` su dashboard.py: zero match fuori dal SQL reconciliation); `rates.py:525/734` → oggi è `_cap_rateizzabile` net-aware legittimo (rates.py:107, G8.1.1/F3). Il debito reale residuo è solo workspace_engine.py:1264 + i 3 raw-SQL count (finding precedente) + le label FE. docs/specs/ = work-queue: un censimento stale in spec aperta fa ripartire da siti già chiusi.
- **Azione raccomandata:** correzione doc (aggiornare il censimento §3.2 alla realtà del codice, restringendo AC-G2-2 ai siti davvero rimasti)
- **Tracciato in:** la spec stessa (aperta, Giro 2 pendente)

### FB-6 — percentuale_versata + somma_rate_previste + somma_rate_saldate: campi wire serializzati a ogni GET dettaglio contratto che NESSUN componente FE legge — e percentuale_versata è una metrica LORDO-based pre-net-aware

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `C:/Users/gvera/Projects/FitManager_AI_Studio/api/routers/contracts.py`, `C:/Users/gvera/Projects/FitManager_AI_Studio/api/schemas/financial.py`
- **Evidenza:** Zero consumatori provato: grep in frontend/src → `percentuale_versata` solo types/api.ts:866 + fixture di test; `somma_rate_previste` solo api.ts:868 + fixture; `somma_rate_saldate` solo api.ts:869 + fixture (nessun componente; `somma_rate_pendenti` invece È consumato da FinancialBreakdown.tsx:23). Calcolo: contracts.py:174 `percentuale = round((versato / prezzo) * 100)` — usa `totale_versato` LORDO, semantica superseded da G8.1 net-aware (`residuo()` sottrae `netto_incassato`; su un contratto con rimborso la percentuale mente) e dal breakdown G8.4 D-1 (lordo−rimborsi) che l'hero rende direttamente. Schema: financial.py:555-558.
- **Superseded da:** G8.1 residuo net-aware (ADR-019) + G8.4 D-1 breakdown lordo−rimborsi (ADR-019 Addendum IV)
- **Azione raccomandata:** rimozione secca (i 3 campi da ContractWithRatesResponse + i calcoli; se un giorno serve una % di avanzamento, derivarla dal netto SSoT)

### FB-7 — signed_contractual_amount: zero caller di produzione — ADR-022 e SPEC_G9 la descrivono come la posting-rule della penna, ma ledger.py applica i delta inline senza usarla

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `C:/Users/gvera/Projects/FitManager_AI_Studio/api/services/cash_categories.py`, `C:/Users/gvera/Projects/FitManager_AI_Studio/api/services/financial/ledger.py`
- **Evidenza:** Grep repo-wide `signed_contractual_amount`: definizione (cash_categories.py:53-62) + SOLO tests (test_cash_categories.py:51-56, test_contract_terminate.py:780-784) + docs. Nessun sito di produzione. ADR-022 riga 106 e SPEC_G9 riga 135 affermano che la penna G9.1 «applica il delta-colonna mappato via cash_categories.signed_contractual_amount» — ma post_inflow/post_outflow (ledger.py:77 e 116) fanno `contract.totale_versato/totale_rimborsato += importo` hardcoded. Doc-vs-codice: la funzione è rimasta un'intenzione mai cablata.
- **Azione raccomandata:** rimozione secca (della funzione e dei suoi test, oppure cablarla nella penna) + correzione doc (allineare la frase in ADR-022/SPEC_G9 alla realtà)

### FB-8 — api/CLAUDE.md: albero architettura stale sul filone finanziario — mancano services/financial/ (penna, transitions, invariant_gate), il modello rettifica_contratto e il conteggio modelli è fermo a 22

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `C:/Users/gvera/Projects/FitManager_AI_Studio/api/CLAUDE.md`
- **Evidenza:** L'albero (righe 20-110 circa) elenca «models/ — 22 modelli» senza `rettifica_contratto.py` (terzo ledger G9.2b, esiste da luglio: api/models/rettifica_contratto.py, tabella `rettifiche_contratto`), né `nutrition.py`/`workout_schedule.py` (la dir reale ha 28 moduli). In services/ mancano `financial/` (ledger.py, transitions.py, invariant_gate.py — il cuore della migrazione G9), `contract_settlement.py`, `schema_sync.py`, `db_crypto.py`, `tunnel_config/manager.py`. Grep `financial/` in api/CLAUDE.md: zero match nell'albero (compare solo nel testo della convenzione eccezioni, riga 319). Il prose finanziario si ferma a G8.3 («Prossimo: G1 cifratura») — G9.0→G9.7 assenti. È il doc caricato ogni volta che si tocca api/.
- **Azione raccomandata:** correzione doc (albero + paragrafo pattern finanziari aggiornati a G9.7)

### FB-9 — client_engagement + ClientEngagement (LAPSED_CALDO/FREDDO): funzione SSoT senza alcun caller di produzione

- **Severita:** BASSA · **User-facing:** no · **Verdetto critico:** non verificato (fuori campione critico)
- **File:** `C:/Users/gvera/Projects/FitManager_AI_Studio/api/services/contract_state.py`
- **Evidenza:** Grep repo-wide `client_engagement|ClientEngagement|LAPSED_FREDDO`: definizione (contract_state.py:79-83 e 217-234) + SOLO tests (test_contract_state.py:313-329) + BUILD_LOG. La worklist reale `_lapsed_client_candidates` (dashboard.py:682-731) usa solo `is_engaged` (riga 724) e il proprio criterio recency+esito_rinnovo; la distinzione caldo/freddo non è mai esposta sul wire né consumata dal FE (grep `lapsed` in frontend/src: zero). Rametto del Blocco 0 FDM §4.1 mai agganciato.
- **Azione raccomandata:** rimozione secca (funzione + enum + 4 test; `is_engaged` resta — oppure dichiararla esplicitamente in panchina come fatto per posizione_netta_contratto)

### FB-10 — posizione_netta_contratto + PosizioneContrattoCliente: zero caller di produzione — PIN deliberato del founder, da non toccare ma da tenere censito

- **Severita:** BASSA · **User-facing:** no · **Verdetto critico:** non verificato (fuori campione critico)
- **File:** `C:/Users/gvera/Projects/FitManager_AI_Studio/api/services/contract_state.py`
- **Evidenza:** Grep repo-wide `posizione_netta_contratto`: definizione (contract_state.py:324-367) + SOLO unit-oracle (test_contract_state.py:176-184) + docs. Nessun router/servizio la chiama. NON è un residuo da rimuovere: decisione founder esplicita R1.5 = PIN (AUDIT_PRE_RELEASE_2026-07-16, righe 148-201: «resta in panchina ma ha ora un oracolo») come gradino per G8.2 posizione-cliente. Lo segnalo perché è l'unico simbolo money volutamente in panchina: se G8.2 non aprirà mai, andrà rivalutato.
- **Azione raccomandata:** gated su spec aperta (destino legato a G8.2 — richiamato da SPEC_P P-D6/Q9 «differita a G8.2+G8.5»; nessuna azione ora)
- **Tracciato in:** docs/operations/AUDIT_PRE_RELEASE_2026-07-16.md §R1.5 (decisione PIN) + docs/specs/SPEC_P_PRESTAZIONI_SINGOLE_E_PORTAFOGLIO.md (P-D6/Q9)

### FB-11 — rates.py: docstring di modulo con la formula LORDO superseded «totale_versato >= prezzo_totale -> SALDATO»

- **Severita:** BASSA · **User-facing:** no · **Verdetto critico:** non verificato (fuori campione critico)
- **File:** `C:/Users/gvera/Projects/FitManager_AI_Studio/api/routers/rates.py`
- **Evidenza:** rates.py:18 (docstring modulo): «E) Se totale_versato >= prezzo_totale -> stato_pagamento = SALDATO» — è la semantica lorda che G8.1.1/F4 ha esplicitamente vietato (contract_state.is_saldato, righe 138-143: «NON versato ≥ prezzo... SALDATO/auto-close prematuro»). Il codice è corretto (rates.py:582 e 670 delegano a `cstate.recompute_stato_pagamento`; il commento locale a riga 518 è già aggiornato), ma la testata del file insegna la formula sbagliata a chi lo apre.
- **Superseded da:** G8.1.1/F4 — is_saldato net-aware (ADR-019)
- **Azione raccomandata:** correzione doc (allineare il passo E della docstring a residuo()==0 net-aware)

### FB-12 — TASSONOMIA_FINANZIARIA.md (SSoT evergreen): righe 288-289 dichiarano 'futuro' lavori già shippati (leg rimborso della reconciliation G9.0b, contra-line financial-trend G7.5b)

- **Severita:** BASSA · **User-facing:** no · **Verdetto critico:** non verificato (fuori campione critico)
- **File:** `C:/Users/gvera/Projects/FitManager_AI_Studio/docs/technical/TASSONOMIA_FINANZIARIA.md`
- **Evidenza:** Riga 289 (voce 6): «La leg totale_rimborsato vs Σ USCITA RIMBORSO è additiva (futuro, non must-fix)» — implementata da G9.0b: dashboard.py:186-211 (reconciliation bidirezionale con I5 raffinata) + test_reconciliation.py:75-90. Riga 288 (voce 5): `get_financial_trend` marcata «⏳ G7.5b» — fatta: schema `rimborsi_contratti` (financial.py:826, `tot_rimborsi_contratti`:855) + endpoint movements.py:1630 e api/CLAUDE.md la dichiara «✅ G7.5». docs/technical/ = com'è FATTO il sistema: due righe che negano lo stato reale.
- **Azione raccomandata:** correzione doc (aggiornare le voci 5 e 6 della tabella a ✅ con puntatore a G7.5b/G9.0b)

## 5. Finanza frontend (contraddizioni col netto SSoT)

### FF-1 — Profilo cliente ContrattiTab mostra il versato LORDO come «Finanze» — contraddice il netto SSoT di /contratti (AC-G84-1 dichiarato chiuso ma superficie mancata)

- **Severita:** ALTA · **User-facing:** SI · **Verdetto critico:** CONFERMATO
- **File:** `frontend/src/components/clients/profile/ContrattiTab.tsx`, `tests/test_semantic_guards.py`, `docs/specs/SPEC_G8.4_TRASPARENZA_FINANZIARIA_FE.md`
- **Evidenza:** ContrattiTab.tsx:100 rende la cella Finanze come `{formatCurrency(c.totale_versato)} / {formatCurrency(prezzo)}` — versato LORDO. `grep -n "netto" ContrattiTab.tsx` = zero risultati. SPEC_G8.4 F1.a (riga 107) impone «hero, ContractsTable, PaymentPlanTab, ContrattiTab consumano contract.netto_incassato» e AC-G84-1 (riga 180) «il netto mostrato da hero, lista contratti e profilo è identico»; la spec dichiara F1 ✅ COMPLETATA. ContractRow.tsx:211+232 mostra invece netto + sub-label «lordo X · −Y»: su un contratto con rimborsi il profilo mostra una cifra DIVERSA (più alta) dalla lista /contratti per lo stesso contratto. Il gemello anti-vacuità test_g84_fe_consuma_ssot_netto_e_saldo (test_semantic_guards.py:157-177) asserisce solo hero/ContractRow/ContractHistoryTab, NON ContrattiTab → il guard è verde mentre la superficie è off-SSoT (nessun ricalcolo inline, quindi anche il pattern-guard non scatta).
- **Superseded da:** D-1 emendata G8.4 (netto SSoT + sub-label lordo−rimborsi always-visible)
- **Azione raccomandata:** gated su spec aperta (SPEC_G8.4: riaprire F1.a per ContrattiTab + estendere il gemello anti-vacuità in test_semantic_guards.py)
- **Tracciato in:** SPEC_G8.4 F1.a/AC-G84-1 — ma dichiarato ✅ chiuso, quindi di fatto NON tracciato come pendente

### FF-2 — Dropdown clienti EventForm mostra «(N crediti)» dal campo client-level che include i contratti CHIUSI (caso panico founder 2026-07-07)

- **Severita:** ALTA · **User-facing:** SI · **Verdetto critico:** CONFERMATO
- **File:** `frontend/src/components/agenda/EventForm.tsx`, `api/routers/clients.py`
- **Evidenza:** EventForm.tsx:293 `({client.crediti_residui} crediti)` nel SelectItem. Il campo è calcolato da `_calc_credits_batch` (clients.py:286-315) che per scelta deliberata NON filtra `chiuso` («chiuso NON filtrato — chiuso blocca nuove operazioni, non invalida crediti», riga 295): un cliente con solo contratti chiusi appare con «(2 crediti)» accanto al warning B4 «nessun contratto attivo» (EventForm.tsx:180-183) — i due segnali sullo stesso schermo si contraddicono. È l'esatto caso censito come P1 in AUDIT_FE_SEGNALI_E_SELETTORI_2026-07-07 (righe 18-20).
- **Azione raccomandata:** gated su spec aperta (SPEC_P P4 wire `crediti_residui_attivi` + P5 «dropdown onesto»)
- **Tracciato in:** docs/specs/SPEC_P_PRESTAZIONI_SINGOLE_E_PORTAFOGLIO.md righe 199, 214, 223 (P4: crediti_residui_attivi; AC-P4 caso founder; P5 dropdown onesto) + operations/AUDIT_FE_SEGNALI_E_SELETTORI_2026-07-07.md P1

### FF-3 — Copy della guida interattiva (guide-tours.ts) descrive una pagina Clienti che non esiste più: colonne crediti/contratti rimosse da FE-0 privacy e stati «in pausa / archiviato» mai esistiti

- **Severita:** ALTA · **User-facing:** SI · **Verdetto critico:** CONFERMATO
- **File:** `frontend/src/lib/guide-tours.ts`, `frontend/src/components/clients/ClientsTable.tsx`
- **Evidenza:** guide-tours.ts:52 «Ogni riga mostra a colpo d'occhio crediti residui, contratti attivi e ultima sessione. Filtra per stato (attivo, in pausa, archiviato)» — ma ClientsTable.tsx (commit 88a77bc, AC-FE0-1 chiuso in SPEC_FRONTEND_CORE_INTUITIVITA riga 95: «lista Clienti senza importi/prezzo/crediti») ha colonne Nome/Contatti/Attenzioni/Ultimo Evento/Stato, zero crediti e zero contratti; gli stati reali sono solo Attivo/Inattivo (ClientForm.tsx:61 `z.enum(["Attivo", "Inattivo"])`). guide-tours.ts:66 ripete «clienti attivi, in pausa» (i KPI reali: Attivi/Inattivi/Con Crediti/Con Rate Scadute, clienti/page.tsx:54-96). guide-tours.ts:77 «stato finanziario: attivi, in scadenza, saldati» — vocabolario pre-SPEC_VOCABOLARIO (oggi due assi: lifecycle Attivo/Sospeso/Esaurito/Chiuso + money Saldato/Pianificato/Parziale/Da pianificare). `grep -i "tour|guida"` su SPEC_FRONTEND_CORE_INTUITIVITA.md = zero: il fold-back del copy guida non è tracciato.
- **Azione raccomandata:** correzione doc (aggiornare il copy di guide-tours.ts righe 52, 66, 77 alla UI reale)

### FF-4 — Filtri/KPI «Con Crediti» (clienti, comunicazioni) e preview CommandPalette usano crediti_residui client-level che include i contratti chiusi, affiancato a «Contratti attivi»

- **Severita:** MEDIA · **User-facing:** SI · **Verdetto critico:** CONFERMATO
- **File:** `frontend/src/app/(dashboard)/clienti/page.tsx`, `frontend/src/app/(dashboard)/comunicazioni/page.tsx`, `frontend/src/components/layout/CommandPalette.tsx`
- **Evidenza:** clienti/page.tsx:227 `activeSituazioni.has("con_crediti") && c.crediti_residui > 0` + KPI «Con Crediti» (righe 76-84); comunicazioni/page.tsx:102 `match: (c) => c.crediti_residui > 0` (chip «Con crediti»); CommandPalette.tsx:149-165 stats grid: «Crediti» = `client.crediti_residui` (incl. chiusi) accanto a «Contratti» = `contratti_attivi` (solo attivi) — stessa cella, due semantiche (incoerenza I3 dell'audit: «cliente=somma multi-contratto incl. chiusi vs contratto=singolo»). Un trainer filtra «Con crediti» e trova clienti i cui crediti sono tutti su contratti chiusi (non scalabili).
- **Azione raccomandata:** gated su spec aperta (SPEC_P P4: `crediti_residui_attivi` su ClientResponse + etichette oneste, «chiude P1-P5 audit»)
- **Tracciato in:** docs/specs/SPEC_P_PRESTAZIONI_SINGOLE_E_PORTAFOGLIO.md P4 riga 199 + operations/AUDIT_FE_SEGNALI_E_SELETTORI_2026-07-07.md I3

### FF-5 — Money-math inline in ExpiringContractsSheet: «valore ~» delle sedute residue calcolato client-side, fuori dai pattern del guard FE-no-money-math e fuori allowlist

- **Severita:** MEDIA · **User-facing:** SI · **Verdetto critico:** CONFERMATO
- **File:** `frontend/src/components/dashboard/ExpiringContractsSheet.tsx`, `tests/test_semantic_guards.py`
- **Evidenza:** ExpiringContractsSheet.tsx:196-198 `formatCurrency((item.prezzo_totale / item.crediti_totali) * item.crediti_residui)` — cifra di denaro derivata nel FE. I 4 pattern forbidden di test_g84_fe_no_money_math (test_semantic_guards.py:128-133: versato-rimborsato, totale_versato-, segno*importo, reduce importo) non la intercettano e il file NON è nell'allowlist (righe 138-142: solo rinnovi-incassi, LedgerColumn, RecurringExpensesTab) — viola la dottrina «le eccezioni entrano SOLO per allowlist esplicita, mai in silenzio». In più usa prezzo_totale LORDO: su un contratto con rimborsi il «valore ~» sovrastima (post D-2 il netto è il SSoT del denaro reale).
- **Azione raccomandata:** rimozione secca del calcolo inline (servire il valore dal wire come gli altri derivati G9.7.3, oppure censirlo nell'allowlist con dottrina esplicita + pattern dedicato nel guard)

### FF-6 — Tre hook finanziari esportati con ZERO consumatori: useReopenRenewalOutcome, useCreditiTerminazione, useCashAuditLog

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `frontend/src/hooks/useContracts.ts`, `frontend/src/hooks/useMovements.ts`
- **Evidenza:** `grep -rn` su tutto frontend/src (inclusi __tests__): useReopenRenewalOutcome (useContracts.ts:206, DELETE /contracts/{id}/renewal-outcome — l'esito rinnovo marcato da rinnovi-incassi:360 non è riapribile da nessuna UI) → solo la definizione; useCreditiTerminazione (useContracts.ts:275, GET /contracts/{id}/crediti-terminazione — superseded dalla worklist G7.10 `useCreditiDaIncassare` → /dashboard/crediti-da-incassare consumata da CreditiDaIncassareCard) → solo la definizione; useCashAuditLog (useMovements.ts:208 — CashAuditSheet.tsx:33 importa SOLO la variante useCashAuditLogInfinite) → solo la definizione. Gli endpoint backend restano validi; è il layer FE a essere morto. Viola la checklist frontend/CLAUDE.md «Zero codice morto (componenti/funzioni non importati)». Nessun componente finanziario orfano invece: tutti i file di components/movements e components/contracts hanno importer verificati.
- **Azione raccomandata:** rimozione secca dei tre export (decidendo esplicitamente se l'azione «riapri esito rinnovo» debba avere una UI prima di eliminare il primo)

### FF-7 — frontend/CLAUDE.md descrive la «Colonna Finanze» della lista Clienti rimossa da FE-0 privacy — doc di sviluppo che guida verso un pattern abolito

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `frontend/CLAUDE.md`, `docs/specs/SPEC_FRONTEND_CORE_INTUITIVITA.md`
- **Evidenza:** frontend/CLAUDE.md:262 «Colonna Finanze: progress bar compatta `versato / prezzo_totale_attivo` (emerald >= 80%, amber >= 40%, red < 40%)» — la colonna non esiste più: ClientsTable.tsx (HEAD, commit 88a77bc «chiudi privacy e verita worklist FE-0.1») ha solo Nome/Contatti/Attenzioni/Ultimo Evento/Stato/Azioni e l'header del file dichiara «Attenzioni — solo segnale amministrativo non monetario». SPEC_FRONTEND_CORE_INTUITIVITA riga 95: «AC-FE0-1 chiuso: lista Clienti senza importi/prezzo/crediti». Un dev (o un agente) che segue CLAUDE.md reintrodurrebbe denaro in una vista resa privacy-safe di proposito.
- **Azione raccomandata:** correzione doc (aggiornare la sezione «FilterBar Clienti» di frontend/CLAUDE.md alla tabella privacy-safe post FE-0)
- **Tracciato in:** SPEC_FRONTEND_CORE_INTUITIVITA AC-FE0-1 (chiuso senza fold-back su frontend/CLAUDE.md)

### FF-8 — Etichetta KPI «Fatturato» (pagina Contratti + copy tour) usa vocabolario fiscale su un sistema dichiarato «registro operativo» (ADR-025 D-REGISTRO-OPERATIVO)

- **Severita:** BASSA · **User-facing:** SI · **Verdetto critico:** non verificato (fuori campione critico)
- **File:** `frontend/src/app/(dashboard)/contratti/page.tsx`, `frontend/src/lib/guide-tours.ts`, `docs/adr/ADR-025-prestazione-singola-portafoglio-cliente.md`
- **Evidenza:** contratti/page.tsx:71-72 KPI `label: "Fatturato"` + guide-tours.ts:91 «fatturato totale». Il valore è `kpi_fatturato = Σ prezzo_totale` (contracts.py:307, «venduto» cumulativo — il commento in page.tsx:111 lo chiama esplicitamente «storico/Fatturato» ma la stessa riga ammette che il concetto è «Venduto»). ADR-025 D-REGISTRO-OPERATIVO (righe 58-61): «vocabolario UI mai fiscale (mai "fattura" — "riepilogo", "registrazione")... NON emette documenti fiscali», con validazione nella call tributarista pendente. Onestà sul perimetro: la lettera della decisione vieta «fattura», non «fatturato» — ma il termine implica un fatturato fiscale che il sistema non traccia (nessuna fattura esiste in FitManager), su un KPI che è in realtà il venduto contrattuale.
- **Azione raccomandata:** gated su spec aperta (SPEC_P — esito call tributarista D-REGISTRO-OPERATIVO; candidata rinomina «Venduto» coerente col commento inline già presente)
- **Tracciato in:** ADR-025 D-REGISTRO-OPERATIVO (call tributarista unica pendente)

## 6. Drift documentale

### DOC-1 — CLAUDE.md root: la sezione WhatsApp dichiara sia '14 template' sia '15 template' e la tabella ne enumera solo 14 (manca waWorkoutPortal)

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `CLAUDE.md`, `frontend/src/lib/whatsapp-templates.ts`
- **Evidenza:** grep 'export function wa' whatsapp-templates.ts = 15 funzioni (waRateReminder, waAppointmentReminder, waWorkoutShare, waWelcome, waRenewalReminder, waContractConfirm, waCheckIn, waEventConfirm, waBirthday, waMilestone, waClassReminder, waClassCancelled, waProgressUpdate, waWorkoutPortal, waFreeMessage). CLAUDE.md dice in un punto '(14 template)' nel diagramma WhatsAppButton e nella riga tabella 'UI component | 3 varianti', ma altrove '15 template pre-compilati' e titolo tabella '### 15 template WhatsApp'. La tabella dei 15 elenca solo 14 righe: manca waWorkoutPortal (portale scheda interattiva). Anche frontend/CLAUDE.md riga whatsapp-templates.ts dice '15 template'. Numero da derivare, non enumerare a mano.
- **Azione raccomandata:** correzione doc: uniformare a 15 e aggiungere la riga waWorkoutPortal nella tabella template

### DOC-2 — frontend/CLAUDE.md cita 'src/proxy.ts' / 'proxy.ts' come edge boundary, ma il file NON esiste: il boundary reale e' frontend/src/middleware.ts

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `frontend/CLAUDE.md`, `frontend/src/middleware.ts`
- **Evidenza:** ls frontend/src/proxy.ts => 'No such file or directory'; ls frontend/src/middleware.ts => esiste. frontend/CLAUDE.md riga 14 ('proxy.ts  Next.js proxy (PUBLIC_ROUTES...)'), riga 352 ('Edge Proxy (src/proxy.ts): intercetta route prima del render'), riga 373 (pitfall 'Proxy intercetta fetch /api/public/*'). Il root CLAUDE.md invece cita correttamente 'frontend/src/middleware.ts' in 4 punti (righe 150, 258, 271, 373). Regressione tracciata: UPG-2026-03-10-16 ('la terminologia residuale middleware.ts dove il boundary reale e ormai src/proxy.ts') ha rinominato al contrario rispetto al codice attuale.
- **Azione raccomandata:** correzione doc: sostituire proxy.ts -> middleware.ts in frontend/CLAUDE.md (righe 14, 352, 373) per allineare al codice e al root CLAUDE.md

### DOC-3 — RELEASE_CHECKLIST.md descrive Tailscale Funnel come step di release attivo e verificato, ma il sistema e' migrato a FRP self-hosted

- **Severita:** ALTA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `docs/operations/RELEASE_CHECKLIST.md`
- **Evidenza:** grep tailscale RELEASE_CHECKLIST.md: righe 60-67 con checkbox [x] spuntati: '[x] Backend binding --host 0.0.0.0 (LAN + Tailscale)', '[x] CORS configurato per ... Tailscale (100.x.x.x)', '[x] Tailscale Funnel: https://giacomo.tail8a3bc3.ts.net/', '[x] Test Tailscale VPN da rete esterna'. Il root CLAUDE.md riga 236 dichiara 'Tunnel self-hosted ... Sostituisce Tailscale Funnel' e ADR-011 (tunnel FRP) e' accepted+shipped v1.0.10-1.0.13. Doc operativa che guida azioni di release verso un'infrastruttura dismessa/in dismissione (dominio giacomo.tail8a3bc3.ts.net e' l'endpoint Tailscale personale).
- **Azione raccomandata:** correzione doc: aggiornare gli step di release Tailscale->FRP (edge.fitmanagerstudio.com, frps :443) o annotarli come storici; la dismissione Tailscale e' Fase 3 non ancora eseguita, ma il funnel di verifica release e' gia' FRP

### DOC-4 — docs/INDEX.md: la tabella specs/ (fronte di lavoro APERTO) elenca SPEC_TERMINAZIONE_BILATERALE gia' archiviata e omette 2 spec aperte reali (SPEC_FINGERPRINT_CROSSPLATFORM, SPEC_G-MAC)

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** RIDIMENSIONATO
- **File:** `docs/INDEX.md`, `docs/specs/SPEC_FINGERPRINT_CROSSPLATFORM.md`, `docs/specs/SPEC_G-MAC_CONSEGNA_MACOS.md`, `docs/archive/specs/SPEC_TERMINAZIONE_BILATERALE_E_TUTELA_TRAINER.md`
- **Evidenza:** grep SPEC_ in INDEX.md tabella specs elenca SPEC_TERMINAZIONE_BILATERALE_E_TUTELA_TRAINER.md (riga 101, sezione operations audit) e nella work-queue; ma ls docs/specs/ NON la contiene, mentre ls docs/archive/specs/ SI (archiviata batch 2026-07-03, come dichiarato dalla stessa INDEX riga 168). Inversamente, docs/specs/ contiene SPEC_FINGERPRINT_CROSSPLATFORM.md (Stato: CODICE FATTO E SIGILLATO) e SPEC_G-MAC_CONSEGNA_MACOS.md (Stato: IN CODA #3) che NON compaiono nella tabella specs dell'INDEX (grep -c = 0 per entrambe). INDEX.md diverge dal filesystem reale della work-queue.
- **Azione raccomandata:** correzione doc: rimuovere SPEC_TERMINAZIONE dalla tabella specs aperte dell'INDEX e aggiungere SPEC_FINGERPRINT_CROSSPLATFORM + SPEC_G-MAC con il loro Stato
- **Nota critico:** Metà del claim non regge: la tabella specs/ di INDEX.md (righe 79-88) NON elenca SPEC_TERMINAZIONE_BILATERALE — le 2 occorrenze sono a riga 101 (sezione operations, riferimento storico legittimo all'audit che l'ha fondata) e riga 168 (voce archive, correttamente marcata come archiviata). Regge invece l'omissione: docs/specs/ contiene 9 file, la tabella ne elenca 7 — SPEC_FINGERPRINT_CROSSPLATFORM.md e SPEC_G-MAC_CONSEGNA_MACOS.md assenti (grep = 0). Resta MEDIA solo per la parte omissione.

### DOC-5 — CLAUDE.md root: numeri catalogo 'esercizi/relazioni/media' divergenti dal DB reale (894 relazioni vs 868; 750 media vs 738)

- **Severita:** BASSA · **User-facing:** no · **Verdetto critico:** non verificato (fuori campione critico)
- **File:** `CLAUDE.md`, `data/catalog.db`
- **Evidenza:** SELECT COUNT su data/catalog.db: esercizi in_subset=1 = 466 (OK, CLAUDE.md corretto); esercizi_relazioni = 868 (CLAUDE.md sezione Cross-layer Seed data dice '894 relazioni'); esercizi_media = 738 (CLAUDE.md dice '750 media'). CLAUDE.md riga Seed: 'In DB dopo filtro FK orfane: 466 attivi, 894 relazioni, 750 media'. La memory riporta '894 relazioni, 738 media' — quindi anche il numero relazioni (894) e' stale rispetto al DB (868). Nota metodologica: il catalog.db letto e' lo stato dev locale in plain (in compiled mode e' cifrato); e' l'unico ground-truth disponibile e va usato come tale, non ipotizzato.
- **Azione raccomandata:** correzione doc: derivare i conteggi dal DB/seed (868 relazioni, 738 media) invece di enumerare a memoria; oppure annotare che i numeri si riferiscono al seed shipped e non al DB dopo filtro FK

### DOC-6 — frontend/CLAUDE.md: conteggio moduli hook incoerente internamente (28 vs 24) e disallineato dal filesystem (33 file)

- **Severita:** BASSA · **User-facing:** no · **Verdetto critico:** non verificato (fuori campione critico)
- **File:** `frontend/CLAUDE.md`, `frontend/src/hooks`
- **Evidenza:** frontend/CLAUDE.md riga 69 dichiara 'hooks/ ... 28 moduli', ma righe 105-106 sezione 'Hook per dominio' dicono '24 moduli hook, uno per dominio' e l'elenco che segue enumera ~21 nomi. ls frontend/src/hooks/*.ts | wc -l = 33 file .ts reali. Tre valori diversi (24/28/33) per la stessa quantita'. Non e' un drift post-migrazione specifico ma rumore di conteggio manuale che aumenta il rischio manutenzione.
- **Azione raccomandata:** correzione doc: derivare il conteggio (ls hooks) e uniformare i due punti del documento

## 7. Codice morto frontend

### MF-1 — Cluster ProgressiTab morto (~3.070 LOC): 6 componenti clienti irraggiungibili, e frontend/CLAUDE.md li documenta ancora come attivi

- **Severita:** ALTA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/clients/ProgressiTab.tsx`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/clients/GoalsSummary.tsx`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/clients/InteractiveBodyMap.tsx`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/clients/ClinicalAnalysisPanel.tsx`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/clients/ProjectionPanel.tsx`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/clients/CompositionInsights.tsx`
- **Evidenza:** Grep su tutto frontend/src (path assoluti @/ e relativi, escl. __tests__): ProgressiTab ha ZERO import; il profilo cliente (app/(dashboard)/clienti/[id]/page.tsx:29-35) monta solo Panoramica/Contratti/Sessioni/Movimenti/Schede/Allenamento. GoalsSummary, InteractiveBodyMap (796 LOC, recharts+SVG), ClinicalAnalysisPanel (509 LOC) e ProjectionPanel (415 LOC) hanno come UNICO consumatore il morto ProgressiTab (grep: solo ProgressiTab.tsx:62-67). CompositionInsights: zero import, il suo stesso sostituto lo dichiara (ClinicalAnalysisPanel.tsx:14 'Sostituisce CompositionInsights'). Il contenuto vive ora in /monitoraggio/[id] via components/portal (ProgressiSection, CompositionSection, ProjectionChart, GoalsSection). Doc drift: frontend/CLAUDE.md:42 elenca ProgressiTab tra i componenti attivi e frontend/CLAUDE.md:701 raccomanda il dynamic-import di 'InteractiveBodyMap (tab ProgressiTab)' come ottimizzazione futura — su codice morto.
- **Superseded da:** app/(dashboard)/monitoraggio/[id]/page.tsx + components/portal/* (ProgressiSection, CompositionSection, ProjectionChart, GoalsSection)
- **Azione raccomandata:** rimozione secca dei 6 componenti + correzione doc (frontend/CLAUDE.md righe 42 e 701; anche i commenti header stale in lib/metric-correlations.ts:10 e lib/measurement-analytics.ts:5 che citano CompositionInsights/ProgressiTab)

### MF-2 — OverdueRatesSheet morto (264 LOC), superseded dal deep-link contestuale FE-1.0, ma i CLAUDE.md lo documentano come pattern attivo dell'Alert Panel

- **Severita:** ALTA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/dashboard/OverdueRatesSheet.tsx`
- **Evidenza:** Grep 'OverdueRatesSheet' su frontend/src: zero import (unico file che lo nomina è se stesso). La dashboard oggi esclude la categoria dagli alert e usa il deep-link: app/(dashboard)/page.tsx:102 `alerts?.items.filter((item) => item.category !== "overdue_rates")` + CTA verso /rinnovi-incassi?focus=overdue-rate (SPEC_FRONTEND_CORE_INTUITIVITA.md:200-236, commit f678292/d382a4b). L'hook useOverdueRates resta vivo (rinnovi-incassi/page.tsx:62,617). Doc operativa fuorviante: frontend/CLAUDE.md:411 documenta 'OverdueRatesSheet | useOverdueRates | Pagamento con metodo selezionabile | usePayRate' come sheet inline attivo e CLAUDE.md:210 lo cita come contesto d'uso di waRateReminder — chi sviluppa sulla dashboard seguirebbe un pattern rimosso.
- **Superseded da:** Deep-link contestuale /rinnovi-incassi?focus=overdue-rate + useOverdueRateContextFocus (FE-1.0)
- **Azione raccomandata:** rimozione secca del componente + correzione doc (frontend/CLAUDE.md:55,411 e CLAUDE.md:210)
- **Tracciato in:** docs/specs/SPEC_FRONTEND_CORE_INTUITIVITA.md (FE-1.0, AC-FE1-0a)

### MF-3 — UI Tailscale ancora visibile al trainer (wizard 'Prepara Tailscale', onboarding, copy) mentre il tunnel FRP è in produzione

- **Severita:** MEDIA · **User-facing:** SI · **Verdetto critico:** CONFERMATO
- **File:** `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/settings/connectivity-wizard-panels.tsx`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/settings/connectivity-status-ui.tsx`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/dashboard/ConnectivityOnboardingCard.tsx`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/dashboard/connectivity-onboarding.ts`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/workouts/BuilderHeader.tsx`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/app/(dashboard)/clienti/[id]/anamnesi/page.tsx`
- **Evidenza:** Grep -i 'tailscale' su frontend/src: connectivity-wizard-panels.tsx:22 pannello 'Prepara Tailscale' ('Installa Tailscale sul PC del trainer...'), connectivity-status-ui.tsx:117 'Tailscale e Funnel restano gestiti dal client ufficiale', ConnectivityOnboardingCard.tsx:66 mostra tailscale_dns_name, connectivity-onboarding.ts:31 copy 'senza Tailscale', BuilderHeader.tsx:356 e anamnesi/page.tsx:354 suggeriscono 'IP LAN o Tailscale' per condividere link. Realtà: il tunnel FRP self-hosted è in produzione dal v1.0.13 (PUBLIC_BASE_URL auto da instance_id) e la dismissione Tailscale è pianificata ma NON eseguita (docs/technical/TUNNEL_ARCHITECTURE.md:199 e §8.5 'Fase 3 — dismissione Tailscale: PIANIFICATA'). Un trainer con tunnel FRP attivo vede in Impostazioni un wizard che lo guida a installare Tailscale.
- **Azione raccomandata:** gated su Fase 3 tunnel (docs/technical/TUNNEL_ARCHITECTURE.md §8.5 — dismissione Tailscale); nel frattempo valutare correzione del solo copy nei punti dove il tunnel FRP è già la via primaria (BuilderHeader:356, anamnesi:354)
- **Tracciato in:** docs/technical/TUNNEL_ARCHITECTURE.md §8.5 (Fase 3 — Onboarding zero-touch + dismissione Tailscale)

### MF-4 — Motore Smart Programming client-side morto (~1.070 LOC): useSmartProgramming + index/plan-generator/scorers/selection/analysis senza consumatori dal 2026-03-16

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/hooks/useSmartProgramming.ts`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/lib/smart-programming/index.ts`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/lib/smart-programming/plan-generator.ts`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/lib/smart-programming/scorers.ts`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/lib/smart-programming/selection.ts`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/lib/smart-programming/analysis.ts`
- **Evidenza:** Grep 'useSmartProgramming' su frontend/src: zero consumatori (solo il file stesso, un commento in smart-programming/helpers.ts:195 e frontend/CLAUDE.md). L'unico consumatore storico SmartAnalysisPanel (708 LOC) fu rimosso nel commit f9a04a1 ('performance quick wins — eliminati 3 componenti orfani'), lasciando orfana l'intera catena: index.ts è importato SOLO dal hook morto; plan-generator/scorers/selection/analysis sono raggiungibili SOLO via index (grep 'smart-programming/<nome>' e dei simboli generateSmartPlan/analyzePlan/scoreExercisesForSlot: zero hit esterni). Restano VIVI solo types.ts, blueprints.ts, helpers.ts (consumati da lib/template-registry.ts:23,25 e lib/template-emphasis.ts:19). L'analisi scientifica reale passa dal backend: SciencePanel.tsx:23 e ScientificAnalysisTab.tsx:20 usano useAnalyzePlan da hooks/useTrainingScience. Doc drift: CLAUDE.md tabella Motori cita 'Smart Programming frontend/src/lib/smart-programming/ Scoring 14D' e frontend/CLAUDE.md:73,118 elenca useSmartProgramming tra i moduli attivi.
- **Superseded da:** Backend Training Science Engine via hooks/useTrainingScience.ts (useAnalyzePlan, plan-package TSPlanPackage + lib/smart-plan-package-cache)
- **Azione raccomandata:** rimozione secca di hook + 5 file (conservando types/blueprints/helpers, che vanno riorganizzati o lasciati con index snellito) + correzione doc (CLAUDE.md tabella motori, frontend/CLAUDE.md:73,118 e sezione lib/smart-programming)

### MF-5 — Cluster workspace morto (~1.170 LOC): WorkspaceCaseCard/DetailPanel/AgendaPanel + workspace-ui + workspace-visuals + 2 hook e 5 tipi orfani

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/workspace/WorkspaceCaseCard.tsx`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/workspace/WorkspaceDetailPanel.tsx`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/workspace/WorkspaceAgendaPanel.tsx`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/workspace/workspace-ui.ts`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/workspace/workspace-visuals.ts`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/hooks/useWorkspace.ts`
- **Evidenza:** Grep dei 3 nomi componente su frontend/src: zero import. workspace-ui.ts (231 LOC) e workspace-visuals.ts (179 LOC) sono importati SOLO dai 3 componenti morti (grep 'workspace-ui'/'workspace-visuals': unici hit = WorkspaceCaseCard/DetailPanel/AgendaPanel). La pagina /oggi importa solo OggiHero, OggiTimeline, OggiCommandCenter (oggi/page.tsx:8-14) e da useWorkspace solo useClientAvatars/useSessionPrep/useWorkspaceToday (riga 19). Gli export useWorkspaceCases (useWorkspace.ts:56) e useWorkspaceCaseDetail (riga 98) hanno zero consumatori (grep con exit 1). Tipi orfani correlati in types/api.ts:1564-1594 (WorkspaceCaseSortBy, WorkspaceCaseListFilters, WorkspaceCaseListResponse, WorkspaceCaseActivityItem, WorkspaceCaseDetailResponse). Superseded dal redesign P0 pagina Oggi (commit 906cf60).
- **Superseded da:** Redesign pagina Oggi (OggiHero + OggiCommandCenter + OggiTimeline, commit 906cf60)
- **Azione raccomandata:** rimozione secca dei 5 file + dei 2 export morti in useWorkspace.ts + dei tipi WorkspaceCase* in types/api.ts (verificando l'endpoint backend corrispondente in un audit separato)

### MF-6 — lib/export-workout.ts morto (900 LOC, export Excel) — superseded dall'export PDF

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/lib/export-workout.ts`
- **Evidenza:** Il file esporta una sola funzione, exportWorkoutExcel (riga 643). Grep 'export-workout"' (copre @/lib e relativo ./) e grep 'exportWorkoutExcel' su frontend/src: zero consumatori. Il fratello lib/export-workout-pdf.ts ha 3 consumatori vivi. Ultimo tocco: 139ae60 (audit pre-delivery) e 1ff655d (restyling export workout) — l'export scheda è passato al PDF clinico HTML (frontend/CLAUDE.md cita 'export-workout.ts, export-workout-pdf.ts (clinico HTML→PDF)' come coppia, ma solo il PDF è usato).
- **Superseded da:** lib/export-workout-pdf.ts (3 consumatori: ExportButtons e correlati)
- **Azione raccomandata:** rimozione secca + correzione doc (frontend/CLAUDE.md riga che cita export-workout.ts)

### MF-7 — SmartProtocolSection.tsx morto (268 LOC) — sezione analisi SMART mai più montata

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** non verificato (fuori campione critico)
- **File:** `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/workouts/SmartProtocolSection.tsx`
- **Evidenza:** Grep 'SmartProtocolSection' su frontend/src: zero import (unico hit = il file stesso). Nato con 17dcebc 'add SMART protocol/feasibility/constraint sections to analysis panel' — il pannello ospite (SmartAnalysisPanel, 708 LOC) è stato eliminato in f9a04a1 come componente orfano, ma questa sezione figlia è rimasta. I feasibility_details oggi arrivano dal backend via builder.smartPlanPackage (schede/[id]/page.tsx:232) e sono renderizzati dalle 6 sezioni della ScientificAnalysisTab.
- **Superseded da:** ScientificAnalysisTab + SciencePanel (backend Training Science, useAnalyzePlan)
- **Azione raccomandata:** rimozione secca

### MF-8 — workout-preview-block-metrics.ts tenuto in vita SOLO dal proprio test Vitest — coverage su codice che nessuno usa

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/lib/workout-preview-block-metrics.ts`, `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/__tests__/workouts/workout-preview-block-metrics.test.ts`
- **Evidenza:** Grep 'buildBlockMetrics' e 'workout-preview-block-metrics' su frontend: unici consumatori = il file stesso e __tests__/workouts/workout-preview-block-metrics.test.ts. Il consumatore reale WorkoutPreview.tsx (644 LOC) è stato rimosso in f9a04a1 come componente orfano; il commit successivo d8b7629 ha persino 'hardened' la lib orfana. Il test verde in suite dà falsa sicurezza: presidia una funzione che nessun componente monta.
- **Superseded da:** WorkoutPreview rimosso in f9a04a1; nessun sostituto consuma la funzione
- **Azione raccomandata:** rimozione secca di lib + test (oppure, se le metriche blocco servono al preview pubblico futuro, ricablarla — ma oggi zero consumatori)

### MF-9 — VideoGuideInline.tsx morto (70 LOC) — terzo componente dell'infra video mai cablato

- **Severita:** BASSA · **User-facing:** no · **Verdetto critico:** non verificato (fuori campione critico)
- **File:** `C:/Users/gvera/Projects/FitManager_AI_Studio/frontend/src/components/guide/VideoGuideInline.tsx`
- **Evidenza:** Grep 'VideoGuideInline' su frontend/src: zero import. Nato con 99ac7c3 'guida: infrastruttura video guide — 10 pillole, 3 componenti, registro'. Gli altri due vivono: VideoGuideCard è montato in guida/page.tsx:176, VideoGuidePopover via PageVideoGuide (PageVideoGuide.tsx:15) usato in 7 pagine. Inline non è mai stato montato da nessuno.
- **Azione raccomandata:** rimozione secca

### MF-10 — live-01-dashboard.png (200KB) untracked alla root del repo — screenshot fuori posto

- **Severita:** BASSA · **User-facing:** no · **Verdetto critico:** non verificato (fuori campione critico)
- **File:** `C:/Users/gvera/Projects/FitManager_AI_Studio/live-01-dashboard.png`
- **Evidenza:** git ls-files --others --exclude-standard: unico untracked = live-01-dashboard.png (200.376 byte, datato 21 lug, verosimile residuo delle verifiche LIVE Playwright). La casa naturale esiste ed è già gitignorata (.gitignore:140 'screenshots/'; esiste anche il pattern .gitignore:224 'verify-*.png' per gli screenshot di verifica, che questo nome non rispetta).
- **Azione raccomandata:** rimozione secca (o spostamento in screenshots/, già ignorata); in prospettiva usare il naming verify-*.png per gli screenshot di verifica così restano auto-ignorati

## 8. Codice morto backend + tools + config

### MB-1 — UI e backend 'Connettivita'' era-Tailscale ancora attivi e visibili al trainer (wizard 'Prepara Tailscale', onboarding card in dashboard, 4 endpoint diagnostici, regex CORS CGNAT)

- **Severita:** ALTA · **User-facing:** SI · **Verdetto critico:** CONFERMATO
- **File:** `frontend/src/app/(dashboard)/page.tsx`, `frontend/src/app/(dashboard)/impostazioni/page.tsx`, `frontend/src/components/settings/connectivity-wizard-panels.tsx`, `frontend/src/components/dashboard/ConnectivityOnboardingCard.tsx`, `frontend/src/app/(dashboard)/clienti/[id]/anamnesi/page.tsx`, `api/services/connectivity_runtime.py`, `api/routers/system.py`, `api/main.py`
- **Evidenza:** Il tunnel FRP e' in produzione (main.py:319-345 auto-setta PUBLIC_BASE_URL dal tunnel), ma tutta la superficie Tailscale e' viva: (dashboard)/page.tsx:150 monta ConnectivityOnboardingCard che mostra 'nodo {tailscale_dns_name}' (riga 66) e il prompt 'Se vuoi inviare link anamnesi ai clienti senza Tailscale...' (connectivity-onboarding.ts:31); impostazioni/page.tsx:126 monta ConnectivityStatusSection con wizard 'Prepara Tailscale' / 'Scarica Tailscale' (link tailscale.com/download, connectivity-wizard-panels.tsx:22-49) e pannello 'Abilita Funnel' (righe 163-199); anamnesi/page.tsx:354 dice al trainer di accedere 'via IP LAN o Tailscale'. Lato backend: connectivity_runtime.py:17-18 proba i path hardcoded 'C:\Program Files\Tailscale\tailscale.exe' ed esegue subprocess tailscale a ogni caricamento dashboard; system.py:47-79 espone 4 endpoint connectivity-* consumati da 5 hook FE; il POST /system/connectivity-config puo' sovrascrivere a mano il PUBLIC_BASE_URL che il tunnel FRP setta in automatico al boot. Bonus: main.py:416 la regex CORS ammette 100.x.x.x = range CGNAT Tailscale.
- **Superseded da:** Tunnel FRP self-hosted (lifespan step 6 api/main.py + tunnel_manager.py, in produzione da v1.0.13)
- **Azione raccomandata:** rimozione secca (anticipare il punto 3.7 della Fase 3: smontare wizard+card FE, endpoint connectivity-* e connectivity_runtime; ripulire regex CORS 100.x e copy anamnesi)
- **Tracciato in:** docs/technical/TUNNEL_ARCHITECTURE.md §8.5 — Fase 3 'dismissione Tailscale', punto 3.7 (PIANIFICATA, non eseguita)

### MB-2 — migrate-all.sh migra ancora crm_dev.db (rimosso 2026-06-09) e si autodefinisce 'REGOLA BLINDATA'; api/CLAUDE.md ribadisce la regola obsoleta

- **Severita:** ALTA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `tools/scripts/migrate-all.sh`, `api/CLAUDE.md`
- **Evidenza:** migrate-all.sh esegue DATABASE_URL='sqlite:///data/crm_dev.db' alembic upgrade head con header 'REGOLA BLINDATA: ogni volta che crei una migrazione Alembic, esegui questo script. Mai alembic upgrade head da solo' — eseguirlo oggi RICREA il crm_dev.db dismesso (alembic crea il file SQLite se assente) e fallisce il confronto versioni. Ultima modifica: commit ed85744 'ops: dual-env workflow' (era dual-env). api/CLAUDE.md:321: 'Ogni migrazione va applicata a ENTRAMBI i DB (prod + dev)' contraddice il CLAUDE.md root ('UN SOLO database crm.db', dual-DB rimosso 2026-06-09) e il fix definitivo 408a682 del 2026-06-20. Doc operativa che guida azioni sbagliate.
- **Azione raccomandata:** rimozione secca di migrate-all.sh + correzione doc di api/CLAUDE.md:321 (un solo alembic upgrade head su crm.db)

### MB-3 — Router nutrition montato e raggiungibile (26 endpoint, anche CRUD scriventi su crm.db) con zero consumatori frontend — dormiente esposto

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `api/main.py`, `api/routers/nutrition.py`
- **Evidenza:** main.py:466 app.include_router(nutrition_router) monta 26 endpoint (grep -c '@router.' api/routers/nutrition.py = 26), inclusi POST/PUT/DELETE su piani_alimentari/pasti/componenti in crm.db (nutrition.py:658-1107) e generazione piani da template (1448). Grep 'nutrition' (case-insensitive) su frontend/src *.ts/*.tsx = 0 occorrenze totali: nessuna pagina, hook o tipo consuma questi endpoint dalla rimozione della UI nutrition. Restano raggiungibili con JWT valido senza alcuna UI. Il servizio api/services/nutrition_science e' keep-list (preservato per futuro prodotto): la questione e' SOLO il mount del router = superficie API attiva senza consumatori.
- **Azione raccomandata:** gated su decisione founder: smontare il solo include_router in main.py (servizio e router preservati su disco per il futuro prodotto nutrizionisti) oppure lasciarlo documentando la scelta
- **Tracciato in:** CLAUDE.md root, tabella Motori scientifici: 'Nutrition Science — UI RIMOSSA (backend preservato)'

### MB-4 — Script seed/demo/rehearsal ancora cablati su crm_dev.db: seminano un DB che nulla legge; il rehearsal di distribuzione marca FAIL su ambiente sano

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `tools/admin_scripts/seed_dev.py`, `tools/admin_scripts/seed_dev_complete.py`, `tools/admin_scripts/e2e_distribution_rehearsal.py`, `tools/scripts/seed_demo_crm.py`, `tools/scripts/seed_demo_direct.py`, `tools/scripts/seed_demo_full.py`, `tools/scripts/video-02-setup.py`, `tools/scripts/video-cleanup-moretti.py`
- **Evidenza:** seed_dev.py:21 e seed_dev_complete.py:55 forzano os.environ['DATABASE_URL'] = 'sqlite:///.../crm_dev.db' e seed_dev_complete.py:716-737 'copia esercizi da crm.db a crm_dev.db' — eseguirli oggi ricrea e popola un DB che nessun runtime legge (un solo crm.db dal 2026-06-09). e2e_distribution_rehearsal.py:376 asserisce _log((data_dir/'crm_dev.db').exists(), 'Development DB (crm_dev.db) exists') → la Phase 7 del rehearsal di distribuzione segna FALLITO su ogni ambiente corretto. Stesso target crm_dev nei 5 script demo/video di tools/scripts. Nota: restart-backend.sh e build-installer.sh sono gia' stati bonificati (menzioni solo negative/guard).
- **Azione raccomandata:** correzione doc/script: rimuovere il check crm_dev.db da e2e_distribution_rehearsal.py e ripuntare (o archiviare) gli script seed/demo su data/crm.db o su un path esplicito da CLI

### MB-5 — Endpoint GET /training-methodology/worklist senza alcun consumatore frontend + tipo TS e import orfani

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `api/routers/training_methodology.py`, `frontend/src/types/api.ts`, `frontend/src/hooks/useDashboard.ts`
- **Evidenza:** training_methodology.py:619 espone GET /training-methodology/worklist (analisi metodologica pesante: analyze_plan() su ogni piano del trainer). Grep 'training-methodology' su frontend/src: l'unica fetch e' useDashboard.ts:255 verso /training-methodology/projection/{clientId} (viva, usata da AllenamentoTab). Nessuna fetch verso /worklist in tutto frontend/src. Il tipo TrainingMethodologyWorklistResponse (types/api.ts:1819) e' importato in useDashboard.ts:31 ma mai usato nel file (unica altra occorrenza = la definizione). Endpoint montato, costoso e mai chiamato dalla UI.
- **Azione raccomandata:** rimozione secca dell'endpoint worklist (+ helper _filter_items/_sort_items se restano orfani) e del tipo/import TS orfani; il gemello /projection resta

### MB-6 — 4 endpoint Training Science su 6 senza consumatori UI: gli hook wrapper esistono ma nessun componente li importa

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `api/routers/training_science.py`, `frontend/src/hooks/useTrainingScience.ts`
- **Evidenza:** training_science.py espone 6 endpoint (righe 82-186). Consumati dalla UI solo 2: POST /analyze (useAnalyzePlan → SciencePanel.tsx:124, ScientificAnalysisTab.tsx:153) e POST /plan-package (useGeneratePlanPackage → TemplateSelector.tsx:206). Gli altri 4 — POST /plan, POST /mesocycle, GET /parameters/{obiettivo}, GET /volume-targets — sono chiamati SOLO dentro i wrapper useGenerateScientificPlan/useGenerateMesocycle/useLoadParameters/useVolumeTargets di useTrainingScience.ts (righe 41-141), e il grep di questi 4 nomi su frontend/src *.tsx restituisce zero import da componenti. Nessun path letterale alternativo nel FE (verificato).
- **Superseded da:** POST /training-science/plan-package (SMART runtime, TemplateSelector) + POST /analyze
- **Azione raccomandata:** rimozione secca dei 4 hook orfani; per i 4 endpoint backend decisione contestuale (restano test pytest del motore SSoT) — se si tengono, annotare in api/CLAUDE.md che /plan-package li ha superseded lato UI

### MB-7 — PyMuPDF==1.24.1 dichiarata in pyproject.toml ma mai importata da nessun modulo del repo

- **Severita:** MEDIA · **User-facing:** no · **Verdetto critico:** CONFERMATO
- **File:** `pyproject.toml`
- **Evidenza:** pyproject.toml sezione 'RAG & ML' pinna 'PyMuPDF==1.24.1'. Grep 'import fitz', 'from fitz' e 'PyMuPDF' su api/, core/, tools/, tests/ (esclusi tools/spikes) = 0 file. A differenza di torch/scikit-learn/joblib/numpy (dipendenze transitive dello stack core/ dormiente: sentence-transformers e' importata da core/knowledge_chain.py), PyMuPDF non e' richiesta da nessun altro pin: orfana al 100%. Le altre pesanti della sezione (langchain*, chromadb via langchain_community, ollama via langchain_ollama) sono consumate da core/ = keep-list, non flaggate.
- **Azione raccomandata:** rimozione secca del pin da pyproject.toml

### MB-8 — API_VERSION in api/config.py definita e mai letta da nessuno

- **Severita:** BASSA · **User-facing:** no · **Verdetto critico:** non verificato (fuori campione critico)
- **File:** `api/config.py`
- **Evidenza:** config.py:112 definisce API_VERSION: str = 'v1'. Grep 'API_VERSION' su api/, tools/, tests/ = zero consumatori (unico match estraneo: un template Nuitka dentro la venv dello spike sqlcipher, non tracciata). Il versioning reale passa da api/__init__.py __version__ (usato in main.py:361). Le altre chiavi env di config.py (APP_LOG_*, JWT_*, DATABASE_URL, CATALOG/NUTRITION_DATABASE_URL) hanno tutte consumatori verificati.
- **Azione raccomandata:** rimozione secca della costante

## 9. Aree scoperte aggiunte dal critico (nessun auditor le aveva censite)

### CR-1

Endpoint backend GET /workspace/cases e GET /workspace/cases/{case_id} (api/routers/workspace.py:37 e :68) montati ma di fatto MORTI: i loro unici consumatori sono useWorkspaceCases/useWorkspaceCaseDetail (useWorkspace.ts:71,106), che ho verificato avere zero import in tutto frontend/src. Con loro resta orfana la macchina cases/ranking/dominance in workspace_engine.py (~3000 LOC totali del modulo). Il finding FE sul cluster workspace rimandava esplicitamente il lato backend 'a un audit separato' e nessun auditor l'ha coperto.

### CR-2

Portata reale di crm_dev.db in tools/: grep -rl 'crm_dev' su tools/admin_scripts + tools/scripts = 63 file, contro gli 8 censiti dal finding seed/demo. Esempi verificati: build_catalog.py (opzione --source crm_dev, righe 11/28/160/306) e fdb_diagnostic.py:23 con DB_PATH di DEFAULT = data/crm_dev.db (eseguito oggi punta a un DB inesistente). Molti sono anche pre-ADR-003 (toccano esercizi in crm.db, ora in catalog.db): la bonifica/archiviazione va pianificata su tutto il gruppo, non sugli 8 citati.

### CR-3

RELEASE_CHECKLIST.md righe 52-54 (sezione 4, fuori dalla sezione Rete già flaggata): '[x] data/media/exercises/ - 1788 foto esercizi' e '[x] Freeze reality 2026-03-10: catalog.db canonico = 400 ID esercizio, crm.db locale = 396 attivi' — numeri pre-ADR-003 e pre-potatura media superati dai canonici 522 esercizi/466 attivi/738-750 media e dalla rimozione della copia esercizi in crm.db (ADR-003 chiusa al 100%). La checklist di release contiene ground-truth vecchio anche sul catalogo, non solo sul tunnel.

### CR-4

Alert 'overdue_rates' calcolato da GET /dashboard/alerts (dashboard.py:1289, categoria documentata a riga 1124) ma scartato da ENTRAMBI i consumatori FE: (dashboard)/page.tsx:102 e components/dashboard/AlertHub.tsx:97 filtrano via la categoria. Il backend esegue la query a ogni poll per un alert che la UI butta sempre — residuo del passaggio a deep-link FE-1.0, gemello backend del morto OverdueRatesSheet, non censito da nessun auditor.

### CR-5

api/CLAUDE.md sezione Test documenta 'Legacy (tests/legacy/): Rotti — referenziano moduli eliminati... Da non eseguire' ma la directory tests/legacy NON esiste più (ls: no such file or directory). Ulteriore drift del doc backend oltre l'albero modelli/servizi già flaggato: la voce va rimossa insieme all'aggiornamento G9 dello stesso file.


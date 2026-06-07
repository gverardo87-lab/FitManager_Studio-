# LEARNING_FASE1_BASI_TEORICHE.md

**Progetto:** FitManager
**Tipo:** Materiale di studio PRE-implementazione (da leggere prima di toccare codice)
**Quando:** preparazione tra mer 03/06 e sab 06/06; esecuzione Fase 1 sab-dom
**Metodo:** vedi `LEARNING_METHOD.md` — Principio 4 (macro prima del micro) applicato alla pianificazione: costruire le basi teoriche prima di iniziare.
**Macro di riferimento:** `ARCHITECTURE_OVERVIEW.md`, `TUNNEL_MIGRATION_STRATEGY.md` sez. 4 Fase 1, `LEARNING_NETWORKING.md` §FRP.
**Nota:** questo file e' di STUDIO, non un diario. Le decisioni e l'esecuzione reale andranno nel `BUILD_LOG.md`. I concetti consolidati confluiranno nei file `LEARNING_*.md` per dominio dopo averli visti dal vivo.

---

## 0. Dove siamo e cosa fa la Fase 1 (il macro)

**Fase 0 (fatta):** costruito il VPS = il centralino con `frps` (FRP server) sempre acceso, in attesa di connessioni. Ma e' un centralino che non riceve ancora telefonate: manca l'altra meta'.

**Fase 1 (in arrivo):** far si' che il `frpc` (FRP client) parta DA SOLO dentro l'app che il trainer installa, aprendo il tunnel verso il centralino senza che il trainer faccia nulla. Vincolo cardine: **zero configurazione per il trainer**.

**Il problema centrale della Fase 1, in una domanda:**
Distribuisco UN SOLO programma identico a tutti i trainer. Ma ogni trainer ha bisogno di un tunnel SUO, con un indirizzo SUO (`alessio.fitmanagerstudio.com`). Come fa lo stesso identico software, installato su 100 PC diversi, a sapere "chi e'" e quindi quale tunnel aprire?

La risposta e' il filo conduttore di tutta la Fase 1 (sezione 2).

---

## 1. Concetto fondante: cos'e' una licenza JWT (e perche' e' firmata)

**Contesto:** la strategia (D3) usa la licenza come "carta d'identita'" di ogni installazione. Per capire la Fase 1 devo capire prima cos'e' un JWT.

**Livello 1 — Cosa fa:**
Un JWT (JSON Web Token) e' un pacchetto di dati (es. `{"instance_id": "alessio-crociani", "scadenza": "..."}`) accompagnato da una **firma** che ne garantisce autenticita' e integrita'. Chi lo riceve puo' verificare due cose: che l'ha emesso davvero chi dice di averlo emesso, e che nessuno l'ha modificato dopo.

**Livello 2 — Perche' mi importa:**
La licenza FitManager e' un JWT che IO (AVGV) genero e firmo, e consegno al trainer. Il software del trainer la legge e si fida dei dati dentro PERCHE' la firma e' valida. E' il modo per mettere un'identita' unica (`instance_id`) dentro un software altrimenti identico per tutti: l'identita' non sta nel software, sta nella licenza.

**Livello 3 — Perche' funziona cosi' sotto (ed e' un concetto che gia' conosco!):**
La firma del JWT usa la **stessa crittografia asimmetrica** delle chiavi SSH (vedi LEARNING_LINUX_SYSADMIN §Crittografia asimmetrica). Io firmo la licenza con una chiave PRIVATA che custodisco solo io (AVGV). Il software del trainer verifica la firma con la chiave PUBBLICA, che posso distribuire liberamente dentro il programma. La proprieta' magica e' la stessa: con la pubblica puoi VERIFICARE la firma ma non puoi RICREARLA, quindi nessuno puo' falsificare una licenza senza la mia chiave privata. Vedo come il fondamentale ritorna: SSH, TLS, e ora le licenze sono tutti la stessa famiglia (asimmetria: facile verificare, impossibile falsificare).

Struttura di un JWT (tre parti separate da punti): `header.payload.signature`
- header: che algoritmo di firma
- payload: i dati veri (incluso `instance_id`)
- signature: la firma che lega header+payload alla mia chiave privata

**Failure mode da capire:**
Se la chiave privata di firma di AVGV trapelasse, chiunque potrebbe generare licenze false. E' un segreto critico (come la chiave SSH privata): non va mai nel repo, mai distribuita, custodita con la massima cura.

**Verificato nel codebase (07/06):**
- [x] Generazione licenza: `tools/admin_scripts/generate_license.py` — CLI argparse con `sign`, `verify`, `fingerprint`, `generate-keys`
- [x] Verifica licenza: `api/services/license.py` — `check_license()` con 4-tier key resolution, embedded key in frozen mode
- [x] Algoritmo: RS256 (RSA 2048 + SHA-256) — stessa famiglia crittografia asimmetrica di SSH Ed25519 ma con RSA

---

## 2. Il filo conduttore: instance_id (la risposta al problema centrale)

**Livello 1 — Cosa fa:**
`instance_id` e' un nuovo dato (claim) dentro la licenza JWT, es. `"instance_id": "alessio-crociani"`. Identifica univocamente l'installazione di QUEL trainer. Al primo avvio il software legge l'instance_id dalla licenza e sa "chi e'".

**Livello 2 — Perche' risolve il problema centrale:**
Software identico per tutti + licenza unica per ciascuno = ogni installazione sa quale tunnel aprire. L'instance_id determina il sottodominio (`alessio-crociani.fitmanagerstudio.com`) e quindi quale tunnel il `frpc` deve stabilire. L'identita' viaggia nella licenza, non nel codice: cosi' non devo compilare un software diverso per ogni trainer (sarebbe ingestibile).

**Livello 3 — Perche' funziona cosi' sotto (il flusso completo):**
1. AVGV vende a un trainer -> genera una licenza con dentro `instance_id: "alessio-crociani"`, firmata con la chiave privata AVGV.
2. AVGV (script di provisioning) crea il record DNS `alessio-crociani.fitmanagerstudio.com -> IP del VPS` PRIMA della consegna.
3. Il trainer installa il software (identico a quello di tutti) e inserisce la licenza.
4. Al primo avvio: il software verifica la firma della licenza (chiave pubblica), legge `instance_id`, e configura il `frpc` per aprire il tunnel `alessio-crociani.fitmanagerstudio.com`.
5. Il `frpc` si connette al `frps` sul VPS -> tunnel attivo -> il trainer e' online sul suo sottodominio.

Punto elegante: nessuna chiamata di rete per "registrarsi" al primo avvio. L'identita' e' gia' nella licenza, il DNS e' gia' pronto. Il software deve solo leggere e connettere.

**Verificato nel codebase (07/06) — Step 1 completato:**
- [x] Claim `instance_id` aggiunto a `generate_license.py sign --instance-id <slug>`
- [x] Campo `instance_id: str | None = None` in `LicenseClaims` (Pydantic, backward-compat via Optional)
- [x] Property `LicenseCheckResult.instance_id` espone lo slug per tunnel_manager
- [x] Backward compatibility confermata: licenze senza instance_id restano valide (campo = None)

---

## 3. Il gestore del tunnel: tunnel_manager.py (componente nuovo)

**Livello 1 — Cosa fa:**
Un nuovo componente del backend che gestisce il ciclo di vita del `frpc`: lo avvia all'accensione dell'app, lo tiene vivo, lo riavvia se cade, controlla che sia connesso. E' il "babysitter" del processo tunnel.

**Livello 2 — Perche' mi serve:**
Il `frpc` e' un programma esterno (un eseguibile separato). Qualcuno deve avviarlo quando parte FitManager, assicurarsi che resti su, e rilanciarlo se crasha o se la connessione cade. Senza un gestore, il tunnel sarebbe fragile: basta un'interruzione e il trainer va offline senza recupero.

**Livello 3 — Perche' funziona cosi' sotto (concetto: processo figlio):**
Il `tunnel_manager` avvia il `frpc` come **processo figlio** di FitManager: un programma che ne lancia un altro e ne mantiene il controllo (puo' vederne lo stato, fermarlo, riavviarlo). Concetto Unix/sistema che incontrero': un processo puo' generare altri processi e diventarne il "genitore". Se il figlio muore, il genitore se ne accorge e puo' rilanciarlo. E' lo stesso pattern con cui systemd gestisce i servizi sul VPS (vedi LEARNING_LINUX_SYSADMIN §systemd), ma qui dentro l'app invece che a livello di sistema operativo.

NOTA collegamento: sul VPS e' systemd a fare da babysitter a `frps`. Sul PC del trainer e' il `tunnel_manager` (dentro FitManager) a fare da babysitter a `frpc`. Stesso ruolo, contesti diversi.

**Verificato nel codebase (07/06):**
- [x] Entry point: `tools/build/entry_point.py` — avvia solo uvicorn, nessuna logica di boot aggiuntiva. Il tunnel_manager si innesta qui.
- [x] Config layer creato: `api/services/tunnel_config.py` — `TunnelConfig` dataclass con instance_id, server, path frpc. Separa identita' (licenza) da esecuzione (tunnel_manager).
- [x] frpc.exe gia' presente in `tools/bin/` (~15MB, scaricato in Fase 0). Path risolto da `_resolve_frpc_path()`.

---

## 4. Il packaging: il frpc dentro l'installer

**Livello 1 — Cosa fa:**
L'eseguibile `frpc` (un file, ~15MB) va incluso DENTRO l'installer di FitManager, cosi' arriva sul PC del trainer insieme al resto, senza che il trainer lo scarichi o installi separatamente.

**Livello 2 — Perche' mi serve (vincolo cardine):**
Zero configurazione per il trainer. Se il trainer dovesse scaricare FRP a parte, sarebbe lo stesso attrito che avevo con Tailscale (4 step manuali). Bundlando `frpc` nell'installer, il trainer installa una cosa sola e ha gia' tutto.

**Livello 3 — Perche' funziona cosi' sotto (concetto: bundling):**
Il prodotto e' impacchettato con uno strumento (PyInstaller o Nuitka — DA CHIARIRE, la strategia li nomina entrambi in punti diversi: incongruenza da risolvere sabato con Claude Code) che raccoglie codice Python + dipendenze + risorse in un pacchetto installabile. Il `frpc.exe` viene incluso come "risorsa" nel pacchetto: il build lo copia dentro, e a runtime il software sa dove trovarlo per lanciarlo. ~15MB in piu' su un installer gia' grande (~100MB+) = impatto trascurabile.

**Verificato nel codebase (07/06):**
- [x] **INCONGRUENZA RISOLTA:** Nuitka e' il build primario (ADR-007). PyInstaller preservato come fallback (`fitmanager.spec`). `is_compiled()` in `api/config.py` rileva entrambi (`sys.frozen` per PyInstaller, `__compiled__` per Nuitka).
- [x] `_resolve_frpc_path()` in `tunnel_config.py` gestisce entrambi i casi: dev (`tools/bin/frpc.exe`) e compiled (accanto all'exe).

---

## 5. Mappa dei pezzi della Fase 1 (riepilogo macro)

Tre fronti di lavoro:

| Fronte | Cosa | Dove |
|--------|------|------|
| **Lato AVGV (io)** | aggiungere instance_id alla licenza; script provisioning (DNS + config) | `generate_license.py`, `provision_instance.py` (nuovo) |
| **Lato prodotto** | leggere instance_id; tunnel_manager che gestisce frpc; auto-start al boot | `license.py`, `tunnel_manager.py` (nuovo), `entry_point.py` |
| **Lato packaging** | bundlare frpc.exe nell'installer | `build-release.sh` |

Ordine logico (dipendenze): prima l'identita' (instance_id nella licenza + lettura), poi il gestore (tunnel_manager), poi il bundling, infine il test e2e verso `slug.fitmanagerstudio.com`.

---

## 6. I concetti-chiave da padroneggiare PRIMA di sabato

Checklist di comprensione (test: so spiegarli a fonte chiusa?):

- [ ] **JWT e firma asimmetrica:** so spiegare perche' una licenza firmata non e' falsificabile? (collegamento con SSH gia' fatto)
- [ ] **instance_id:** so spiegare come lo stesso software sa "chi e'" su PC diversi?
- [ ] **Processo figlio / babysitter:** so spiegare cosa fa il tunnel_manager e perche' serve?
- [ ] **Bundling:** so spiegare perche' frpc va dentro l'installer e non scaricato a parte?
- [ ] **Il flusso completo:** so raccontare i 5 passi dalla vendita al trainer-online (sezione 2 livello 3)?

Se a sabato rispondo SI a tutti a fonte chiusa, entro nel codice da consapevole, non da scopritore.

---

## 7. Faro da non perdere (dalla Fase 0)

La Fase 1 rende il tunnel automatico, ma usa ancora il trasporto base. **"Data-blind" (P2) NON e' ancora dimostrato** — dipende dal TLS e2e della Fase 2 (cert sul PC trainer + SNI passthrough). P2 e' il pilastro della semplificazione GDPR. Mentre lavoro alla Fase 1 tengo presente che la cecita' del VPS sul contenuto e' un traguardo della Fase 2, non della Fase 1.

---

## 8. Disciplina del ponte con Claude Code (CRITICA in Fase 1)

La Fase 1 e' il primo blocco dove lavoro MOLTO con Claude Code (codice vero nel repo). E' lo scenario di massimo rischio per il "debito di comprensione": Claude Code scrive il tunnel_manager, funziona, vado avanti senza capire.

**Regola operativa per sabato:**
- Pezzi piccoli, un concetto alla volta.
- Ogni pezzo non banale che Claude Code produce -> cattura grezza -> digerito a mente fredda (qui in chat o nei file learning).
- Prima di accettare codice: "saprei spiegare cosa fa questa riga?". Se no -> cattura, non accettazione passiva.
- Claude (chat) e' un punto cieco: posso sbagliare in modi non verificabili. Validazione reale = il sistema (gira davvero?) + idealmente occhio umano esperto.

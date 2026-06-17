# LEARNING_GIT_VERSIONAMENTO.md

**Progetto:** FitManager
**Ambito:** Git — modello dei rami, fast-forward, cosa significa un branch "stabile", strategia di versionamento
**Origine:** Sessione 2026-06-17 — allineamento di `main` rimasto 24 commit indietro durante il lavoro sul gate G1

---

## Allineamento di `main`, fast-forward e a cosa serve un ramo stabile — 17/06/2026
**Contesto:** lavorando sul gate di sicurezza su `FitManager_Studio`, mi accorgo che `main` è fermo all'era v1.0.10: **24 commit indietro, 0 avanti**. Non contiene neanche le release v1.0.11 e v1.0.12 già spedite. Domanda: un esperto allinea `main` adesso?

**Livello 1 — Cosa fa:** un *branch* in git non è una copia di file: è solo un **puntatore mobile a un commit** (un'etichetta). `main` "24 indietro, 0 avanti" significa che il commit puntato da `main` è un **antenato diretto** di quello puntato da `FitManager_Studio`, sulla stessa linea, senza biforcazioni. Allinearlo è un **fast-forward**: si fa scivolare l'etichetta `main` in avanti fino al commit di `FitManager_Studio`. Nessun nuovo commit, nessun merge, nessun conflitto possibile — si sposta solo un puntatore.

**Livello 2 — Perché lo voglio:** un ramo chiamato `main`/`stable` ha valore *solo se dice la verità*. Qui `main` mentiva: chi lo prendesse come riferimento (io tra sei mesi, un collaboratore, una pipeline CI, un ripristino d'emergenza "torna a main") otterrebbe v1.0.10 — senza il fix installer critico di v1.0.12 e senza tutto il lavoro recente. **Un ramo stabile che mente è peggio di non averlo.** La decisione "allineo o no" dipende da *cosa significa `main` nel progetto*, e ci sono due modelli coerenti:
- **A — Trunk-based:** `main` *è* il tronco, ci lavori sopra e tagghi lì le release. Adatto a un solo sviluppatore: zero cerimonia.
- **B — `main` = linea di release protetta:** `main` riflette sempre l'ultimo stabile rilasciato; un ramo di integrazione (qui `FitManager_Studio`) raccoglie il lavoro e fa avanzare `main` *a ogni release*, via merge/PR.

Quello che **non** esiste è un terzo modello in cui "main 24 indietro + release non su main" sia corretto: era debito, non design. Tempismo: si allinea il tronco a un **confine pulito e rilasciabile**, mai a metà di codice instabile — e oggi era pulito (tutto docs + v1.0.12 spedita, zero codice G1 ancora scritto), finestra che si chiude appena parte il refactor.

**Livello 3 — Perché funziona così sotto:** git è un **DAG** (grafo orientato aciclico) di commit; ogni commit punta al suo genitore. Un branch è un `ref` — un file di testo che contiene l'hash di un commit. Tre modi di far avanzare un ramo:
1. **Fast-forward** — possibile *solo* quando il ramo da spostare è un antenato del target (nessuna divergenza). Sposta il ref in avanti senza creare nulla. È un'operazione **non distruttiva** e non riscrive storia → per questo `git push` non richiede `--force`: il remoto vede che il nuovo commit *contiene* il vecchio, è una pura estensione.
2. **Merge commit** — quando i due rami sono divergiti (entrambi hanno commit che l'altro non ha): git crea un nuovo commit con *due* genitori che unisce le due linee. Necessario quando c'è divergenza reale.
3. **Rebase** — riscrive i commit di un ramo come se fossero partiti da un'altra base. Riscrive storia → richiede `--force` sul push e va evitato su rami condivisi.
`git branch -f main FitManager_Studio` sposta il ref `main` senza fare checkout: legittimo *perché* è un fast-forward (main è antenato). Se i rami fossero divergiti, lo stesso comando sarebbe **distruttivo** (perderei i commit unici di main) — la sicurezza non sta nel comando, sta nell'aver verificato prima "0 avanti".

**Comando/config reale:**
```bash
# Verifica PRIMA (la sicurezza del FF sta qui, non nel comando):
git rev-list --count main..FitManager_Studio   # quanti commit main è indietro → 24
git rev-list --count FitManager_Studio..main    # quanti avanti (divergenza) → 0  ← dev'essere 0
# Fast-forward senza checkout (sposta solo il ref), poi push non-forzato:
git branch -f main FitManager_Studio
git push origin main                             # 262218f..45774dc, niente --force
```

**Failure mode:** se `main` resta indietro e un giorno serve come fonte di verità (ripristino, CI, onboarding) → si parte da codice vecchio senza accorgersene, e il danno emerge nel momento peggiore (durante un recovery). Failure opposto: allineare `main` a metà di una feature → `main` contiene codice rotto/incompleto e smette di essere "stabile". La disciplina è: allinea **solo** a un confine rilasciabile, e **solo** dopo aver verificato `0 avanti` (FF garantito, nessuna perdita).

**Modello scelto (2026-06-17): B — linea di release.** `FitManager_Studio` = sviluppo attivo (tutti i commit); `main` = **backup solido**, avanzato in fast-forward **dopo ogni release verificata** (non a ogni commit). Scoperta: questo modello era **già** la policy in `AGENTS.md` §5 — la decisione non lo introduce, **lo fa rispettare**. La deriva (main 24 indietro) è nata perché lo *step 6 "allineare main"* della procedura Release è stato **saltato** dopo v1.0.11 e v1.0.12. Lezione: una regola scritta ma non eseguita produce esattamente lo stato che vuole evitare → l'aderenza va resa difficile da dimenticare (reminder nel flusso di release), non solo documentata.

**Regola operativa (affinata 2026-06-17):** `main` va allineato **obbligatoriamente dopo ogni release verificata** (trigger non negoziabile) e **può** essere tenuto al passo a confini puliti (docs, unità completate). L'**unico divieto assoluto**: `main` non deve mai contenere codice **in-progress / non rilasciabile**. Conseguenza pratica: durante l'implementazione G1 (refactor `database.py` a metà, boot a due fasi incompleto) `main` **resta congelato** all'ultimo punto pulito finché G1 non è verificata. Così `main` è sempre un backup **solido** (mai rotto) senza diventare una reliquia stantia. Non è il "balletto a ogni commit": è "allinea quando è pulito, congela quando è in lavorazione".

**Domande aperte:** [ ] rami zombie `codex_02` e `fit_launch_01` — archiviare o cancellare per non lasciare ref morti; [ ] valutare un reminder/automazione dell'allineamento `main` in `build-release.sh` (la deriva dimostra che il solo "step 6 a memoria" non basta).

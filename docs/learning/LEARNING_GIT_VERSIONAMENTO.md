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

**Domande aperte:** [x] rami zombie `codex_02` e `fit_launch_01` — **cancellati 2026-06-18** (locale + remoto): entrambi 0 commit unici vs `FitManager_Studio` (interamente contenuti) e fermi da 3 mesi → `git branch -d` (sicuro) + `git push origin --delete`. Repo ora a 2 rami; [ ] valutare un reminder/automazione dell'allineamento `main` in `build-release.sh` (la deriva dimostra che il solo "step 6 a memoria" non basta).

---

## `git add`, commit atomico e fold-back — 05/08/2026

**Contesto:** prima di aprire la remediation Financial Truth, voglio capire perché selezionare i file
con `git add`, creare un commit atomico e fare il fold-back non sono tre modi diversi di fare la
stessa cosa.

**Analogia — una spedizione verificabile:** il working tree è il laboratorio; `git add` sceglie cosa
mettere nella scatola; il fold-back aggiorna distinta, manuale e registro; `git commit` sigilla la
scatola come una consegna identificabile.

```text
working tree
    │
    ├── git add <path/hunk> ──► indice: contenuto scelto
    │                               │
    ├── fold-back docs ─────────────┤  stesso significato del gate
    │                               │
    └── review staged ──────────────┴──► commit atomico ─► push ─► checkpoint pulito
```

### Livello 1 — Cosa fa ciascuno

- **`git add` prepara, non salva nella storia.** Copia nell'indice la versione selezionata di un
  file o di un hunk. Posso cambiare ancora il working tree; il commit userà ciò che è staged.
- **Il commit atomico salva una decisione completa.** “Atomico” non significa “piccolo”: significa
  che il commit fa una sola cosa coerente, passa le verifiche richieste e può essere compreso,
  revisionato o revertito senza trascinare modifiche indipendenti.
- **Il fold-back sincronizza la verità documentale.** Non è un comando Git. Consuntiva nelle sole
  fonti previste cosa è stato realmente deciso, implementato e verificato. Normalmente entra nello
  stesso commit del gate perché ne completa il significato.

### Livello 2 — Pro, contro e criterio senior

| Pratica | Pro | Contro/failure mode | Criterio |
|---|---|---|---|
| stage di path/hunk espliciti | evita di inglobare file del founder o lavoro estraneo; rende visibile lo scope reale | si può dimenticare un file necessario o creare incoerenza tra staged e working tree | controllare `git status`, `git diff` e poi `git diff --cached`; mai assumere che “file per file” significhi già atomico |
| commit atomico | storia leggibile; review, revert e `git bisect` affidabili; handoff netto | un mega-commit nasconde cause diverse; troppi micro-commit possono lasciare stati non pubblicabili | scegliere il gate minimo che conserva tutti i suoi invarianti e lascia il branch rilasciabile per lo scope |
| fold-back nello stesso gate | documenti e codice non divergono; il perché resta accanto al cosa | se diventa rituale può gonfiare il diff o anticipare decisioni non implementate | aggiornare solo SPEC/SSoT/INDEX/log realmente richiesti, descrivendo evidenze già ottenute |

### Livello 3 — Sequenza reale

```text
1. implemento un microstep e lo verifico
2. completo il gate e le verifiche proporzionate al rischio
3. faccio il fold-back delle sole fonti toccate
4. controllo diff, stato e lista esatta dei file attribuiti
5. eseguo git add sui path/hunk intenzionali
6. controllo diff e stat staged
7. creo un commit atomico e lo pusho
8. verifico remoto 0/0 e nessun residuo tracked del gate
```

**Gotcha:** `git add file1 file2` non prova che il commit sia atomico. Lo staging è una proprietà
meccanica dell'indice; l'atomicità è una proprietà semantica del risultato. Due file possono essere
un solo cambiamento indivisibile, mentre due hunk dello stesso file possono appartenere a due gate
diversi.

**Eccezione controllata:** se il fold-back deve citare l'hash esatto dell'implementazione, il gate può
avere due commit coesi — implementazione verificata, poi consuntivo — pushati insieme e senza aprire
altro lavoro nel mezzo. Un gate docs-only non crea un commit vuoto per citare sé stesso.

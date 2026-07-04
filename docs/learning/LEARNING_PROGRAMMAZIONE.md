# LEARNING_PROGRAMMAZIONE.md

**Progetto:** FitManager
**Data:** 2026-06-05
**Stato:** Roadmap attiva
**Obiettivo:** Padroneggiare i fondamenti di programmazione e informatica necessari a comprendere, modificare e mantenere autonomamente il proprio software.
**Metodo:** Ogni concetto insegnato con esempi dal codebase FitManager. Nessun esercizio astratto.

---

## 0. La mappa (Principio 4: macro prima del micro)

Il percorso ha 5 layer, ognuno costruito sul precedente. Non si salta.

```
Layer 4 — IL TUO CODEBASE (trace & rebuild di ogni dominio)
   ^  richiede: saper leggere codice Python e React, capire HTTP e API
   |
Layer 3 — I FRAMEWORK (FastAPI, SQLModel, React, Next.js)
   ^  richiede: saper programmare in Python/JS, capire il web
   |
Layer 2 — COME FUNZIONA IL WEB (HTTP, JSON, API, client-server)
   ^  richiede: concetti base di programmazione
   |
Layer 1 — PYTHON E JAVASCRIPT (i due linguaggi del tuo software)
   ^  richiede: il modello mentale di come ragiona un programma
   |
Layer 0 — FONDAMENTI (variabili, funzioni, logica, strutture dati)
```

**Dove sei ora:** hai i rudimenti di Layer 0 e l'intuizione del macro (sai COSA fa il prodotto). Il gap e' tra il macro e il codice che lo realizza.

**Dove devi arrivare:** Layer 4 — leggere un file qualsiasi del tuo codebase e capire cosa fa, perche', e come modificarlo.

---

## Layer 0 — Fondamenti: come ragiona un programma

Questo layer e' il vocabolario minimo. Senza questi concetti non puoi leggere nemmeno il file piu' semplice del codebase.

### 0.1 Variabili e tipi

**Cosa sono:** contenitori con un nome che tengono un valore. Il tipo dice CHE GENERE di valore.

**Tipi fondamentali:**
- `str` — testo: `"Alessio"`, `"Bench Press"`
- `int` — numero intero: `42`, `500`
- `float` — numero decimale: `79.99`, `3.14`
- `bool` — vero/falso: `True`, `False`
- `None` — assenza di valore (il campo e' vuoto)

**Dove li vedi nel tuo codice:**
```python
# api/models/todo.py — riga 21
titolo: str = Field(max_length=200)         # str: il titolo e' testo
completato: bool = Field(default=False)     # bool: completato o no
data_scadenza: Optional[date] = None        # Optional = puo' essere None (vuoto)
```

**Failure mode:** confondere il tipo produce errori. `"42"` (stringa) non e' `42` (numero). Se provi a sommare `"42" + 1` Python si rifiuta.

- [ ] So spiegare la differenza tra `str`, `int`, `bool` e `None`?

---

### 0.2 Strutture dati: liste e dizionari

**Lista (`list`):** sequenza ordinata di valori. Come un elenco numerato.
```python
esercizi = ["Bench Press", "Squat", "Deadlift"]
esercizi[0]  # "Bench Press" (si conta da 0, non da 1)
```

**Dizionario (`dict`):** coppie chiave-valore. Come una rubrica: cerchi per nome, trovi il dato.
```python
cliente = {"nome": "Alessio", "cognome": "Crociani", "attivo": True}
cliente["nome"]  # "Alessio"
```

**Dove li vedi nel tuo codice:** ogni risposta JSON dell'API e' un dizionario. Ogni lista di clienti e' una lista di dizionari. L'intero frontend riceve e manipola queste strutture.

- [ ] So spiegare quando uso una lista vs un dizionario?

---

### 0.3 Funzioni

**Cosa sono:** blocchi di codice con un nome, che ricevono input (parametri) e producono output (return). Definisci una volta, usi quante volte vuoi.

**Struttura:**
```python
def calcola_residuo(prezzo, versato):    # "def" = definisco una funzione
    residuo = prezzo - versato           # logica interna
    return residuo                        # output

# Uso:
r = calcola_residuo(249, 100)  # r = 149
```

**Dove lo vedi nel tuo codice:**
```python
# api/routers/todos.py — riga 62 (semplificato)
def _bouncer_todo(session, todo_id, trainer_id):
    """Verifica che il todo appartenga al trainer."""
    todo = session.exec(select(Todo).where(Todo.id == todo_id, Todo.trainer_id == trainer_id)).first()
    if not todo:
        raise HTTPException(404, "Todo non trovato")
    return todo
```
Questa funzione riceve 3 input (session, todo_id, trainer_id), cerca nel database, e restituisce il todo trovato. Se non lo trova, segnala errore.

- [ ] So spiegare cos'e' un parametro, cos'e' un return, e perche' le funzioni esistono?

---

### 0.4 Condizioni (if / elif / else)

**Cosa sono:** il programma prende decisioni. "SE questa condizione e' vera, fai questo. ALTRIMENTI fai quest'altro."

```python
if completato:
    stato = "Fatto"
elif data_scadenza < oggi:
    stato = "Scaduto"
else:
    stato = "Da fare"
```

**Dove lo vedi nel tuo codice:** il Bouncer Pattern e' un grande `if`:
```python
if not todo:                                    # SE non trovato
    raise HTTPException(404, "Non trovato")     # → errore
return todo                                      # ALTRIMENTI → restituiscilo
```

- [ ] So spiegare come funziona if/elif/else e cosa significa "condizione vera"?

---

### 0.5 Cicli (for)

**Cosa sono:** ripetere un'azione per ogni elemento di una lista.

```python
for esercizio in esercizi:       # per ogni esercizio nella lista
    print(esercizio)             # stampalo
```

**Dove lo vedi nel tuo codice:** ogni volta che il backend costruisce una lista di risposte (clienti, rate, esercizi), c'e' un ciclo che trasforma ogni record del database in un oggetto di risposta.

- [ ] So spiegare cosa fa un ciclo for e quando serve?

---

### 0.6 Import e moduli

**Cosa sono:** un programma grande e' diviso in file. Ogni file e' un "modulo". Per usare codice da un altro file, lo importi.

```python
# api/routers/todos.py — righe 9-19
from fastapi import APIRouter, Depends, HTTPException     # da fastapi, prendi questi strumenti
from api.database import get_session                       # dal TUO database.py, prendi la funzione
from api.models.todo import Todo                           # dal TUO todo.py, prendi il modello
```

**Il concetto:** `from X import Y` = "dal modulo X, dammi Y". I moduli sono file `.py`. Le cartelle con file dentro sono "pacchetti".

**Dove lo vedi:** le prime 10 righe di OGNI file del backend sono import. Dicono "di cosa ho bisogno per funzionare".

- [ ] So spiegare cosa fa una riga `from ... import ...`?

---

### 0.7 Classi e oggetti (il concetto piu' importante)

**Cosa sono:** una classe e' uno "stampo" che definisce la forma di un dato. Un oggetto e' una copia concreta fatta con quello stampo.

**Analogia:** la classe `Todo` e' il modulo cartaceo "Promemoria" (campi: titolo, scadenza, completato). Ogni singolo promemoria compilato e' un oggetto — un'istanza di quel modulo.

```python
# api/models/todo.py — la CLASSE (lo stampo)
class Todo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    trainer_id: int
    titolo: str
    completato: bool = Field(default=False)

# Da qualche parte nel codice — l'OGGETTO (la copia concreta)
mio_todo = Todo(trainer_id=1, titolo="Chiamare Alessio")
# mio_todo.titolo → "Chiamare Alessio"
# mio_todo.completato → False
```

**Perche' e' il concetto piu' importante:** TUTTO il backend e' costruito su classi.
- Ogni tabella del database e' una classe (SQLModel)
- Ogni schema di validazione e' una classe (Pydantic/BaseModel)
- Ogni errore, ogni risposta, ogni configurazione — classi

**Dove lo vedi:** apri un qualsiasi file in `api/models/` — ogni file definisce una classe che rappresenta una tabella del database.

**Il file piu' semplice per capirlo:**
```
api/models/todo.py          — 27 righe, 7 campi, zero complessita'
api/models/exercise_media.py — 26 righe, 5 campi, ancora piu' semplice
```

- [ ] So spiegare la differenza tra una classe e un oggetto con un esempio mio?

---

### 0.8 Errori e eccezioni

**Cosa sono:** quando qualcosa va storto, Python "lancia" un errore (eccezione). Il codice puo' "catturarlo" e gestirlo invece di crashare.

```python
# Lanciare un errore (nel tuo codice: il bouncer)
raise HTTPException(404, "Todo non trovato")   # "lancia" un errore HTTP 404

# Catturare un errore
try:
    risultato = operazione_rischiosa()
except Exception as e:
    logger.error(f"Errore: {e}")               # logga l'errore senza crashare
```

**Dove lo vedi:** ogni bouncer del tuo backend "lancia" un 404 se il dato non appartiene al trainer. E' il meccanismo di protezione.

- [ ] So spiegare la differenza tra "lanciare" e "catturare" un errore?

> #### ⚠️ Sfumatura senior — quando `except Exception` è un ERRORE (lezione G9.0, 2026-06-30)
>
> L'esempio sopra (`except Exception as e: logger.error(...)`) è ottimo per **imparare il meccanismo**, ma
> nel codice del progetto è un **anti-pattern** se usato per il controllo di flusso. Lezione emersa
> progettando il sensore di invarianti di G9.0 (avevo scritto un `try/except` largo; era sbagliato).
>
> **1) Cosa.** Nel backend si cattura **solo l'eccezione specifica attesa**, mai `Exception` in generale.
> Prova: l'**unico** `try/except` in tutto `contracts.py` (~2.600 righe) è
> `except (ValueError, TypeError)` su un `json.loads` — cattura esattamente cosa può rompersi nel parsing,
> niente di più.
>
> **2) Perché.** Un `except Exception: logger.warning(...)` largo trasforma un errore **duro** in una riga di
> log che nessuno legge → è il **"fallimento silenzioso"** che la regola non-negoziabile #6 (Determinismo) e i
> pitfall #2/#7 ("422 silenzioso", "500 mascherato") vietano. Caso emblematico: un *sensore* nato per
> **chiudere** i fallimenti silenziosi, se lo avvolgi in un catch largo, **ne diventa uno** — un suo bug di
> refactor verrebbe inghiottito invece che surfacato.
>
> **3) Come si applica (il principio).** Non "gestisci l'eccezione" ma **"rendi il codice incapace di
> sollevarla"** (*correctness by construction*): una funzione pura con `getattr(..., 0)` non solleva; se
> solleva è un bug che **deve** fallire rumoroso (la CI lo cattura). Per l'**osservabilità/instrumentation**
> che non deve toccare la transazione, la mossa pulita è **disaccoppiarla** (eseguirla *dopo* il commit, sulla
> verità persistita), **non** avvolgerla in un catch. Solo se serve davvero un guard di confine: fail-loud in
> CI + flag, **mai** uno swallow. Dettaglio: `docs/specs/SPEC_G9_FINANCIAL_COMMAND_LAYER.md` §A.1-bis.

---

## Layer 1 — Python e JavaScript specifici

Costruito su Layer 0. Concetti che sono specifici dei linguaggi usati nel tuo software.

### Python (backend)

| Concetto | Cosa fa | Dove lo vedi nel codebase | Priorita' |
|----------|---------|---------------------------|-----------|
| **Type hints** | `titolo: str` — annota il tipo atteso | Ogni modello, ogni schema, ogni funzione | ALTA |
| **Optional** | `Optional[str] = None` — puo' essere vuoto | Campi non obbligatori in modelli e schema | ALTA |
| **Decoratori** | `@router.get("/")` — modifica il comportamento di una funzione | Ogni endpoint FastAPI | ALTA |
| **async/await** | `async def get_todos(...)` — funzione che puo' "aspettare" | Ogni endpoint FastAPI | MEDIA |
| **f-string** | `f"Errore: {detail}"` — testo con variabili dentro | Log, messaggi errore, audit | BASSA |
| **List comprehension** | `[r.id for r in rates]` — lista in una riga | Query batch, trasformazioni dati | MEDIA |
| **Generatori (yield)** | `yield session` — produce un valore e "si mette in pausa" | `get_session()` in database.py | MEDIA |
| **Context manager (with)** | `with open(file) as f:` — apri, usa, chiudi automaticamente | File I/O, alcune transazioni | BASSA |

### JavaScript/TypeScript (frontend)

| Concetto | Cosa fa | Dove lo vedi nel codebase | Priorita' |
|----------|---------|---------------------------|-----------|
| **Componenti React** | Funzioni che restituiscono HTML (JSX) | Ogni file in `frontend/src/` | ALTA |
| **Props** | Dati passati a un componente dal genitore | `function Button({ label, onClick })` | ALTA |
| **useState** | Variabile che, quando cambia, aggiorna la UI | Form, toggle, selezioni | ALTA |
| **useEffect** | "Fai qualcosa quando il componente appare/cambia" | Caricamento dati, setup | ALTA |
| **TypeScript tipi** | `name: string`, `id: number` — come Python type hints | Ogni file `.ts` e `.tsx` | MEDIA |
| **interface/type** | Definizione di una "forma" di dato | `types/api.ts` — contratto col backend | MEDIA |
| **Arrow function** | `(x) => x + 1` — funzione compatta | Callback, handler eventi | MEDIA |
| **Destructuring** | `const { nome, cognome } = cliente` — estrai campi | Ogni componente React | MEDIA |
| **async/await (JS)** | Come Python — aspetta una risposta | Chiamate API (`fetch`, `axios`) | MEDIA |

---

## Layer 2 — Come funziona il web

Come frontend e backend comunicano. Senza questo layer, il codice funziona "per magia".

### 2.1 Il modello client-server

```
┌──────────────┐           ┌──────────────┐           ┌──────────────┐
│  BROWSER     │  ──HTTP──>│  BACKEND     │  ──SQL──> │  DATABASE    │
│  (frontend)  │           │  (FastAPI)   │           │  (SQLite)    │
│  porta 3000  │  <──JSON──│  porta 8000  │  <──rows──│  crm.db      │
└──────────────┘           └──────────────┘           └──────────────┘
     CLIENT                    SERVER                     STORAGE
```

Il browser (client) CHIEDE. Il server RISPONDE. Il database CONSERVA. E' un dialogo a turni, mai simultaneo: il client chiede, aspetta, riceve.

### 2.2 HTTP: il linguaggio del dialogo

**Cos'e':** il protocollo (le regole della conversazione) tra client e server.

**I 4 verbi fondamentali (CRUD):**

| Verbo HTTP | Significato | Esempio nel tuo software |
|------------|------------|--------------------------|
| `GET` | Dammi un dato (leggere) | `GET /todos` → lista promemoria |
| `POST` | Crea qualcosa di nuovo | `POST /todos` → nuovo promemoria |
| `PUT` | Sostituisci/aggiorna tutto | `PUT /todos/5` → aggiorna promemoria 5 |
| `DELETE` | Elimina | `DELETE /todos/5` → elimina promemoria 5 |

**Status code (la risposta in un numero):**

| Codice | Significato | Quando lo vedi |
|--------|------------|----------------|
| `200` | OK, tutto bene | Risposta normale |
| `201` | Creato con successo | Dopo un POST |
| `400` | Richiesta sbagliata | Dati mancanti o invalidi |
| `404` | Non trovato | Il bouncer non trova il dato (o non e' tuo) |
| `422` | Validazione fallita | Campo sbagliato nel payload (Pydantic `extra: forbid`) |
| `500` | Errore interno del server | Bug nel backend |

### 2.3 JSON: il formato di scambio

**Cos'e':** il modo in cui client e server si scambiano dati. E' un dizionario Python scritto come testo.

```json
{
  "titolo": "Chiamare Alessio",
  "completato": false,
  "data_scadenza": "2026-06-10"
}
```

Il frontend manda JSON al backend (payload). Il backend risponde con JSON. TUTTO passa come JSON.

### 2.4 API: il contratto

**Cos'e':** l'insieme di tutti gli endpoint (URL + verbo + payload atteso + risposta). E' il "contratto" tra frontend e backend: se il frontend manda i dati nel formato giusto, il backend risponde nel formato promesso.

**Nel tuo software:** il contratto e' definito dagli schema Pydantic (backend) e dai tipi TypeScript (frontend). Se non coincidono, qualcosa si rompe.

### 2.5 Autenticazione (JWT)

**Il flusso nel tuo software:**
1. Il trainer inserisce email + password → `POST /auth/login`
2. Il backend verifica le credenziali → se OK, genera un **token JWT** (come la licenza, ma per la sessione)
3. Il frontend salva il token in un cookie
4. Ogni richiesta successiva include il token → il backend sa chi sta chiedendo (`trainer_id`)
5. Il token scade → il trainer deve rifare il login

**Perche' ti importa:** `get_current_trainer()` in `dependencies.py` e' la funzione che legge il token da ogni richiesta e dice "questo e' il trainer con id=1". Ogni endpoint la usa. Senza di lei, il bouncer non saprebbe CHI sta chiedendo.

- [ ] So spiegare il flusso completo: login → token → richiesta autenticata → bouncer?

---

## Layer 3 — I framework del tuo software

Come Python e JavaScript diventano un'applicazione web vera. Ogni framework e' una "struttura predefinita" che ti da' regole e strumenti.

### 3.1 FastAPI (backend)

**Cos'e':** il framework che trasforma le tue funzioni Python in endpoint HTTP.

**Il pattern base (il tuo file piu' semplice da leggere: `api/routers/todos.py`):**
```python
@router.get("/")                                         # 1. DECORATORE: "questa funzione risponde a GET /todos"
async def list_todos(                                     # 2. FUNZIONE: la logica
    trainer: Trainer = Depends(get_current_trainer),       # 3. DIPENDENZA: "dammi il trainer dal JWT"
    session: Session = Depends(get_session),               # 4. DIPENDENZA: "dammi una connessione al DB"
):
    todos = session.exec(select(Todo).where(...)).all()    # 5. QUERY: cerca nel database
    return TodoListResponse(items=..., total=...)          # 6. RISPOSTA: restituisci JSON
```

**I concetti chiave:**
- **Decoratore** (`@router.get`) → collega una URL a una funzione
- **Dependency Injection** (`Depends(...)`) → FastAPI "inietta" automaticamente il trainer e la sessione DB
- **Schema Pydantic** → valida input e output (se il payload e' sbagliato, 422 automatico)

### 3.2 SQLModel (database)

**Cos'e':** il ponte tra classi Python e tabelle SQL. Scrivi una classe, SQLModel crea la tabella. Scrivi una query Python, SQLModel la traduce in SQL.

**Il pattern base (il tuo file piu' semplice: `api/models/todo.py`):**
```python
class Todo(SQLModel, table=True):          # "questa classe E' una tabella del database"
    __tablename__ = "todos"                 # nome della tabella in SQLite
    id: Optional[int] = Field(primary_key=True)  # chiave primaria auto-generata
    trainer_id: int = Field(foreign_key="trainers.id")  # collegamento alla tabella trainers
    titolo: str                             # colonna di testo
```

**Perche' e' potente:** non scrivi SQL a mano. Scrivi Python e SQLModel fa la traduzione.

### 3.3 Pydantic (validazione)

**Cos'e':** lo "stampo" che verifica che i dati in arrivo siano corretti PRIMA di toccare il database.

**Il pattern base (schema in `api/routers/todos.py`):**
```python
class TodoCreate(BaseModel):
    model_config = {"extra": "forbid"}           # se mandi un campo che non esiste → 422
    titolo: str = Field(min_length=1, max_length=200)  # obbligatorio, tra 1 e 200 caratteri
    descrizione: Optional[str] = None            # opzionale, default vuoto
```

**Perche' ti importa:** `extra: "forbid"` e' la regola che causa il pitfall #2 del CLAUDE.md. Se rinomini un campo nello schema ma il frontend manda ancora il vecchio nome → 422 silenzioso.

### 3.4 React (frontend)

**Cos'e':** la libreria che costruisce l'interfaccia. Ogni pezzo della UI e' un "componente" — una funzione che restituisce HTML.

**Il pattern base:**
```tsx
function TodoCard({ todo }: { todo: Todo }) {     // componente: riceve un todo come prop
  const [checked, setChecked] = useState(false)    // stato locale: il checkbox

  return (
    <div>
      <h3>{todo.titolo}</h3>                       {/* mostra il titolo */}
      <input type="checkbox"
        checked={checked}
        onChange={() => setChecked(!checked)}       {/* al click, inverti lo stato */}
      />
    </div>
  )
}
```

### 3.5 TanStack Query (comunicazione frontend-backend)

**Cos'e':** la libreria che gestisce le chiamate API dal frontend. Si occupa di: fare la richiesta, cachare la risposta, aggiornarla quando serve, mostrare errori.

**Il pattern base (il tuo file piu' semplice: `frontend/src/hooks/useTodos.ts`):**
```typescript
// LEGGERE dati (query)
export function useTodos() {
  return useQuery({
    queryKey: ["todos"],                    // identificatore cache
    queryFn: () => api.get("/todos"),       // la chiamata HTTP
  })
}

// SCRIVERE dati (mutation)
export function useCreateTodo() {
  return useMutation({
    mutationFn: (data) => api.post("/todos", data),   // la chiamata HTTP
    onSuccess: () => {
      queryClient.invalidateQueries(["todos"])          // "ricarica la lista"
      toast.success("Promemoria creato")                // feedback utente
    }
  })
}
```

**Il concetto chiave:** `invalidateQueries` = "i dati in cache sono vecchi, ricaricali". E' il meccanismo che tiene la UI sincronizzata col database dopo ogni modifica.

### 3.6 Next.js (struttura frontend)

**Cos'e':** il framework sopra React che gestisce pagine, routing, e rendering.

**Il concetto fondamentale:** le cartelle in `frontend/src/app/` SONO le pagine.
```
app/
├── page.tsx              → la dashboard (URL: /)
├── login/page.tsx        → il login (URL: /login)
├── (dashboard)/
│   ├── clienti/page.tsx  → lista clienti (URL: /clienti)
│   ├── agenda/page.tsx   → agenda (URL: /agenda)
│   └── esercizi/page.tsx → catalogo esercizi (URL: /esercizi)
└── public/
    └── anamnesi/page.tsx → portale pubblico (URL: /public/anamnesi)
```

---

## Layer 4 — Il tuo codebase (trace & rebuild)

Quando i Layer 0-3 sono solidi, si entra nel software vero. Ogni dominio segue il metodo Trace & Rebuild:

1. **Trace** — seguiamo una richiesta reale dall'inizio alla fine
2. **Map** — scrivi la mappa del dominio con parole tue
3. **Modify** — fai una piccola modifica da solo

### Ordine dei domini (dal piu' semplice al piu' complesso)

| # | Dominio | File chiave | Perche' in quest'ordine |
|---|---------|-------------|------------------------|
| 1 | **Todo** (CRUD completo) | `models/todo.py`, `routers/todos.py`, `hooks/useTodos.ts` | Il piu' semplice. Copre l'intero ciclo frontend→backend→DB→risposta |
| 2 | **Clienti** | `models/client.py`, `routers/clients.py`, `hooks/useClients.ts` | Aggiunge complessita' (piu' campi, anamnesi, avatar) |
| 3 | **Autenticazione** | `auth/router.py`, `auth/service.py`, `dependencies.py` | Come il sistema sa "chi sei" |
| 4 | **Database e config** | `database.py`, `config.py` | Come il software si avvia e si connette ai 3 DB |
| 5 | **Contratti + Rate** | `models/contract.py`, `routers/contracts.py`, `routers/rates.py` | Il cuore business. Bouncer deep, integrity engine |
| 6 | **Agenda + Crediti** | `routers/agenda.py` | Credit guard, auto-close, sync contratti |
| 7 | **Cassa + Ledger** | `routers/movements.py`, `models/movement.py` | Movimenti finanziari, forecast, spese ricorrenti |
| 8 | **Esercizi + Catalogo** | `models/exercise.py`, `routers/exercises.py`, seed | Dual-session (catalog.db vs crm.db) |
| 9 | **Schede allenamento** | `models/workout.py`, `routers/workouts.py` | Deep IDOR, cascade FK, builder |
| 10 | **Safety Engine** | `services/safety_engine.py`, `services/condition_rules.py` | Logica scientifica, dual-session critica |
| 11 | **Training Science** | `services/training_science/` | Il motore piu' complesso (~3500 LOC) |
| 12 | **Dashboard** | `routers/dashboard.py` | 9 endpoint, query aggregate, KPI |
| 13 | **Comunicazioni** | `routers/communications.py` | WhatsApp integration, template engine |
| 14 | **Portale pubblico** | `routers/public_portal.py` | Token share, rate limiting, sicurezza |
| 15 | **Licenza + Build** | `services/license.py`, `tools/build/` | Anti-tampering, Nuitka, encryption |

---

## Principi operativi

### Il file di riferimento per ogni layer

| Layer | Il file piu' semplice da leggere per primo |
|-------|---------------------------------------------|
| 0-1 | `api/models/todo.py` (27 righe, tutti i concetti base) |
| 2 | `api/routers/todos.py` (201 righe, CRUD completo con HTTP) |
| 3 | `frontend/src/hooks/useTrainerName.ts` (19 righe, hook minimale) |
| 4 | Dipende dal dominio (vedi tabella sopra) |

### Calibrazione della profondita' (dal LEARNING_METHOD)

- **Layer 0-1:** Livello 3 pieno. Sono i fondamentali trasversali. Senza di loro niente ha senso.
- **Layer 2:** Livello 2-3. HTTP e JSON li devi padroneggiare. I dettagli dei status code li consulti.
- **Layer 3:** Livello 2. Sai come funzionano i framework, consulti la documentazione per i dettagli.
- **Layer 4:** Livello 2-3 sui domini critici (contratti, safety, auth). Livello 1-2 sul resto.

### Il test di comprensione

Per ogni concetto: "saprei spiegarlo a fonte chiusa a qualcuno che non programma?"
- Se SI → acquisito
- Se NI → rileggere il codice di esempio nel codebase
- Se NO → sessione dedicata con Claude Code

### Ritmo consigliato

- Una sessione = un concetto (o un gruppo di concetti collegati)
- Ogni sessione produce materiale nel file learning appropriato
- Non avanzare se il concetto precedente non e' chiaro — il debito si accumula

---

## Concetti dal campo

Concetti trasferibili emersi durante il lavoro reale (non roadmap, ma lezioni di data-modeling/architettura colte sul codice vero).

### Campo "cablato ma vuoto" e semantica dei flag — `is_fondamentale` (2026-06-13)

**Contesto:** la strategia libreria esercizi chiede un marcatore dei ~50-80 esercizi fondamentali (`is_fondamentale`) per guidare il tuning del contenuto e la metrica di copertura del bundle animazioni.

**Livello 1 — Cosa fa.** È un campo booleano su `Exercise`. Verificato dall'interno: è **presente in tutti gli strati** (modello SQLModel, schema Pydantic, `types/api.ts`, e `seed_exercises.py` lo legge con `ex.get("is_fondamentale", False)`) — ma il seed JSON ha **zero esercizi marcati** e nessuna UI lo usa. È uno **scheletro**: cablato ovunque, semanticamente vuoto, funzionalmente morto.

**Livello 2 — Perché lo voglio (la distinzione che conta).** Esisteva già un flag che *sembra* dire "fondamentale": `in_subset`. Ma `in_subset` significa "esercizio **attivo/visibile**" (466 su 500), **non** "fondamentale". Sono due flag con due semantiche diverse: uno è un **flag di visibilità**, l'altro un **flag di curation**. Confonderli (come accaduto in una stesura precedente della strategia) fa puntare il tuning e la metrica di copertura su 466 esercizi invece che su ~50-80.

**Livello 3 — Perché funziona così sotto (la lezione trasferibile).** Tre verità di data-modeling:
1. **Il nome di un campo non è il suo significato.** `in_subset` suona come "sottoinsieme dei fondamentali"; significa "attivo". Si verifica la semantica sul codice/dati, non sul nome.
2. **Schema ≠ dati ≠ uso.** Un campo può esistere a *tutti* i layer ed essere comunque vuoto (nessun dato) e inutilizzato (nessun consumer). "Il campo c'è" non implica "la feature funziona".
3. **Cablare è economico, popolare è il lavoro vero.** Aggiungere un campo attraverso gli strati è meccanico e veloce. Riempirlo richiede una **decisione di dominio** (quali 50-80 esercizi?) che il codice non può inventare. Il collo di bottiglia non è tecnico.

**Failure mode:** se assumo "il campo esiste → la feature è pronta", spedisco un badge/filtro che non mostra nulla (zero marcati); oppure, peggio, riuso `in_subset` come se fossero i fondamentali → la metrica di copertura del bundle e il focus del tuning puntano sull'insieme sbagliato. Me ne accorgo solo quando la UI è vuota o i numeri non tornano.

**Domande aperte:** [ ] criterio di selezione dei ~50-80 fondamentali (pattern, frequenza di prescrizione, copertura muscolare) da decidere col founder, eventualmente validato da Alessio.

### Semantica nuova, interpreti sparsi — il falso allarme come sintomo strutturale (2026-07-03)

**Contesto:** la card "Entrate" della Cassa segnava −140,42 € a luglio; il Mastro filtrato "Solo entrate" non mostrava nulla di negativo. Allarme rosso del founder ("bug nelle logiche di rimborso"), investigazione d'emergenza → zero bug: era il contra-ricavo G7.5 applicato correttamente (375 incassati − 515,42 rimborsati dalle terminazioni di test). INC: `INC-2026-07-03-falso-allarme-entrate-negative-cassa.md`.

**Livello 1 — Cosa fa.** Quando il sistema introduce una *semantica nuova* (una categoria di cassa come `RIMBORSO_CONTRATTO`, uno stato come `Cancellato_Tardivo`, una causale), quella semantica nasce in UN punto (chi la scrive) ma deve essere *interpretata* in N punti (chi la legge: KPI, liste, grafici, forecast, burn rate). Se gli N interpreti sono query inline sparse, ognuno decide da se' il trattamento — e nessuna struttura elenca chi deve ancora decidere.

**Livello 2 — Perche' lo voglio (riconoscere la classe).** Tutte le "rincorse" del progetto hanno questa stessa anatomia: `crediti_usati` prodotto da 5 siti (blind-spot ADR-017), colonne contratto scritte a mano in 7 siti (ADR-022), cascade FK dimenticati (pitfall #10), cache non invalidate (pitfall #8), query-cassa da riallineare a ogni categoria (G7.5). Riconoscere che sono UNA classe di problema — e non N problemi diversi — cambia il rimedio: non serve "pensarci di piu' la prossima volta", serve rendere strutturalmente impossibile *non* pensarci.

**Livello 3 — Perche' funziona cosi' sotto (il metodo in 4 regole).** L'anticipazione non e' una virtu' cognitiva, e' una proprieta' del codice:
1. **Chiudi l'insieme** — l'asse di variabilita' e' un set chiuso enumerato in un modulo solo (`CONTRACT_CASH_IN/OUT`, `STATI_OCCUPAZIONE_CREDITO`, `CAUSALI_RETTIFICA`);
2. **Un solo interprete per asse** — i consumer chiamano la funzione pura del SSoT (`contract_state`, la penna di `ledger.py`), mai logica re-inlineata;
3. **Totalita' per costruzione** — l'interprete su valore ignoto fa errore rumoroso (la penna G9.1 fa `ValueError`), MAI default implicito (le query-aggregato di lettura oggi classificano "per esclusione": fail-silent, il gemello cattivo);
4. **Il gemello che vigila** — un test di esaustivita' fallisce quando nasce un membro senza trattamento dichiarato (`test_occupazione_ssot.py`): la rincorsa la fa la CI, non l'umano in produzione.
Quando le 4 regole valgono, "aggiungere uno scenario" = aggiungere un membro all'enum, e il sistema stesso elenca i punti che devono decidere (perche' falliscono finche' non decidi).

**Corollario di trasparenza:** un KPI che e' un NETTO (lordo − contra) non si mostra mai nudo: espone i componenti in API e in UI. Un numero giusto ma inspiegabile dalla UI stessa e' un difetto di prodotto — genera falsi allarmi, e i falsi allarmi sono incident reali (costano investigazione e fiducia).

**Failure mode:** se introduco una categoria/stato nuovo e verifico solo "il flusso che lo crea funziona", gli interpreti non aggiornati lo classificano in silenzio col default sbagliato → il sintomo emerge settimane dopo come "numero strano" in una superficie lontana, e lo scopre un utente (o il founder in panico) invece di un test rosso il giorno della nascita.

**Domande aperte:** [ ] gate G9 per il read-model della cassa (addendum ADR-022 + SPEC) — [ ] agente auditor "nascita di una semantica" che rilevi nel diff interpreti impliciti non totali (in discussione).

---

## Stato avanzamento

### Layer 0 — Fondamenti
- [ ] 0.1 Variabili e tipi
- [ ] 0.2 Strutture dati (liste, dizionari)
- [ ] 0.3 Funzioni (def, parametri, return)
- [ ] 0.4 Condizioni (if/elif/else)
- [ ] 0.5 Cicli (for)
- [ ] 0.6 Import e moduli
- [ ] 0.7 Classi e oggetti
- [ ] 0.8 Errori e eccezioni

### Layer 1 — Python e JavaScript specifici
- [ ] 1.1 Type hints e Optional
- [ ] 1.2 Decoratori
- [ ] 1.3 async/await
- [ ] 1.4 f-string e list comprehension
- [ ] 1.5 Generatori e yield
- [ ] 1.6 Componenti React e JSX
- [ ] 1.7 Props e State (useState)
- [ ] 1.8 useEffect
- [ ] 1.9 TypeScript tipi e interface
- [ ] 1.10 Destructuring e arrow function

### Layer 2 — Come funziona il web
- [ ] 2.1 Modello client-server
- [ ] 2.2 HTTP verbi e status code
- [ ] 2.3 JSON
- [ ] 2.4 API come contratto
- [ ] 2.5 Autenticazione JWT

### Layer 3 — I framework
- [ ] 3.1 FastAPI (decoratori, DI, endpoint)
- [ ] 3.2 SQLModel (ORM, modelli, query)
- [ ] 3.3 Pydantic (validazione, schema)
- [ ] 3.4 React (componenti, stato, rendering)
- [ ] 3.5 TanStack Query (useQuery, useMutation, invalidation)
- [ ] 3.6 Next.js (routing, pagine, middleware)

### Layer 4 — Codebase (Trace & Rebuild)
- [ ] 4.1 Todo (CRUD completo)
- [ ] 4.2 Clienti
- [ ] 4.3 Autenticazione
- [ ] 4.4 Database e config
- [ ] 4.5 Contratti + Rate
- [ ] 4.6 Agenda + Crediti
- [ ] 4.7 Cassa + Ledger
- [ ] 4.8 Esercizi + Catalogo
- [ ] 4.9 Schede allenamento
- [ ] 4.10 Safety Engine
- [ ] 4.11 Training Science
- [ ] 4.12 Dashboard
- [ ] 4.13 Comunicazioni
- [ ] 4.14 Portale pubblico
- [ ] 4.15 Licenza + Build

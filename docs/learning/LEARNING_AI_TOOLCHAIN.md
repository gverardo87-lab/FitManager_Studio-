# LEARNING_AI_TOOLCHAIN.md

**Dominio:** toolchain AI di sviluppo — Claude Code, MCP, skills, agenti.
**Regola README:** materiale didattico personale, NON vincolante per il codice.

---

## MCP (Model Context Protocol) — 02/07/2026
**Contesto:** sessione didattica esplicita ("insegnami cosa sono gli MCP e come integrarli nel progetto"). Scoperta chiave: il progetto li usava già senza saperlo (`.mcp.json` con Playwright — è il motore dei gate "Playwright LIVE" usati in G8.1/G8.1.1).

**Livello 1 — Cosa fa:** MCP è un protocollo aperto (Anthropic, fine 2024, oggi standard di settore) che standardizza il modo in cui un'applicazione basata su LLM si collega a sistemi esterni. Un **server MCP** espone tre primitive: **tools** (azioni che il modello può invocare: "clicca questo bottone", "esegui questa query"), **resources** (dati leggibili) e **prompts** (template riusabili). Un **host** (Claude Code, Claude Desktop, l'IDE) si connette a N server e presenta i loro tool al modello come se fossero tool nativi.

**Livello 2 — Perche' lo voglio:** senza MCP ogni integrazione LLM↔sistema esterno è codice ad-hoc (il pattern "un connettore per ogni coppia app×servizio" = N×M integrazioni). Con MCP è N+M: chi costruisce un server lo costruisce una volta, qualsiasi host lo consuma. Analogia: quello che REST ha fatto per le API web, o USB-C per le periferiche. Per FitManager: (a) lato sviluppo, dà a Claude Code occhi e mani su browser (Playwright), design (Figma), diagnostica IDE; (b) lato prodotto, è il candidato naturale per il futuro strato AI di `core/` — invece di cablare Langchain sui router FastAPI, si esporrebbero gli endpoint business come tool MCP standard consumabili da qualunque modello.

**Livello 3 — Perche' funziona cosi' sotto:** il protocollo è **JSON-RPC 2.0** sopra due trasporti: **stdio** (l'host lancia il server come processo figlio e parla via stdin/stdout — è quello che succede con `npx @playwright/mcp`) e **HTTP** (server remoto, auth via header o OAuth). All'avvio c'è un handshake `initialize` con negoziazione delle capability, poi l'host chiama `tools/list` per scoprire i tool e `tools/call` per eseguirli. In Claude Code i tool arrivano al modello col nome `mcp__<server>__<tool>` (es. `mcp__playwright__browser_click`); con molti server le definizioni non vengono caricate tutte in contesto ma "deferred" e cercate on-demand (tool search) — stesso principio del lazy loading.

**Comando/config reale (dal progetto):**
```json
// .mcp.json (root del repo, scope "project", versionato in git)
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest", "--headless"]
    }
  }
}
```
```bash
claude mcp list                                  # stato server configurati
claude mcp add --transport stdio nome -- cmd arg # aggiunge server locale (nota il --)
claude mcp add --transport http nome https://url # aggiunge server remoto
/mcp                                             # pannello in-sessione (auth, reconnect)
```
Tre scope: `local` (default, `~/.claude.json`, solo io in questo progetto), `project` (`.mcp.json`, versionato, tutto il team), `user` (`~/.claude.json` globale, tutti i miei progetti). Precedenza: local > project > user. Espansione env var supportata: `${VAR}` e `${VAR:-default}` in url/headers/command/args/env — i segreti stanno nell'ambiente, mai in git.

**Failure mode:**
- Server di terze parti che legge contenuto esterno → **prompt injection**: il testo che il server ritorna entra nel contesto del modello come qualsiasi altro input. Se aggiungo un server che fetcha pagine web/issue/email, un contenuto ostile può tentare di manipolare l'agente. Me ne accorgo... difficilmente: la difesa è a monte (aggiungere solo server fidati; Claude Code chiede approvazione esplicita per i server in `.mcp.json` di repo clonati).
- Token statico scritto in `.mcp.json` → finisce in git → segreto pubblicato. Difesa: `${VAR}` dall'ambiente o OAuth.
- Server stdio = processo figlio dell'host (lo gestisce Claude Code, non il backend → il problema Job Object del pitfall #16 qui non si applica, ma il modello mentale è lo stesso: un processo spawnato ha un ciclo di vita da governare).
- Troppi server attivi → contesto eroso dalle definizioni tool (mitigato dal deferred loading, ma la regola resta: aggiungere solo ciò che serve davvero, un server MCP non usato è superficie di rischio gratuita).

**Domande aperte:**
- [ ] Vale la pena un server SQLite **read-only** su crm.db/catalog.db per gli audit (`/audit-db` oggi passa da Bash+python)? Vincolo non negoziabile: mai write-access via MCP ai DB sacri.
- [ ] Quando si risveglia `core/` (moduli AI dormenti): FastAPI → MCP server (es. `fastapi_mcp`) come interfaccia standard per l'assistente AI di prodotto? Da valutare contro il principio determinismo (regola 6).

# INC-2026-03-29 — Portal URL Origin Mismatch

- **Data**: 2026-03-29
- **Gravita'**: ALTA (P1)
- **Impatto**: Link portale clienti inaccessibili da smartphone — ciclo completo workout portal bloccato
- **Scope**: URL generation in ShareWorkoutDialog + ShareAnamnesiDialog
- **Durata disservizio**: da introduzione ADR-009 (2026-03-29) a fix (2026-03-29) = stesso giorno
- **Rilevato da**: Giacomo Vera durante test end-to-end portale clienti da cellulare

---

## Executive Summary

I link generati per il portale clienti (workout e anamnesi) risultavano inaccessibili da smartphone. Il backend costruiva l'URL usando `PUBLIC_BASE_URL` (Tailscale Funnel, puntante a prod 3000/8000) ma i token erano in `crm_dev.db` (dev 3001/8001). Il client aprendo il link Tailscale interrogava il backend prod dove il token non esisteva, ricevendo "Link non valido — Contatta il tuo trainer".

Il bug era strutturale: l'URL hardcoded nel backend non rifletteva l'origine da cui il trainer stava lavorando.

---

## Cronologia

| Ora | Evento |
|-----|--------|
| 2026-03-29 mattina | Generati 3 link per Giacomo Verardo su dev (porta 8001/3001) |
| 2026-03-29 mattina | Tentativo apertura link da smartphone → "Link non valido" |
| 2026-03-29 mattina | Root cause: URL con `PUBLIC_BASE_URL` (Tailscale → prod) ma token in `crm_dev.db` |
| 2026-03-29 sera | Fix: URL costruito con `window.location.origin` nel frontend |

---

## Root Cause Analysis

### Bug — URL hardcoded da PUBLIC_BASE_URL ignorava contesto di esecuzione

**File backend**: `api/routers/public_portal.py:413-418`

```python
# Il backend costruiva l'URL con PUBLIC_BASE_URL (env fisso)
base_url = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
path = f"/public/scheda/{share.token}"
url = f"{base_url}{path}" if base_url else path
# → https://giacomo.tail8a3bc3.ts.net/public/scheda/TOKEN
# Ma Tailscale Funnel punta a porta 3000 (prod) → crm.db → token non trovato!
```

**File frontend**: `frontend/src/components/workouts/BuilderHeader.tsx:242`

```typescript
// PRIMA (BUG): usava l'URL dal backend (PUBLIC_BASE_URL fisso)
setShareUrl(res.data.url);
// → https://giacomo.tail8a3bc3.ts.net/public/scheda/TOKEN (punta a prod, token in dev)
```

**Perche' falliva**: Il `PUBLIC_BASE_URL` e' un valore singleton condiviso tra dev e prod (salvato in `data/.env`). Quando il trainer lavora su dev (3001), il link generato puntava comunque a Tailscale (3000/prod) dove il token non esisteva.

---

## Fix applicato

**Principio**: l'URL deve riflettere l'origine da cui il trainer sta lavorando, non un valore env fisso.

### ShareWorkoutDialog (BuilderHeader.tsx)

```typescript
// DOPO (FIX): costruisce URL con l'origin del browser
const origin = typeof window !== "undefined" ? window.location.origin : "";
setShareUrl(`${origin}/public/scheda/${res.data.token}`);
```

### ShareAnamnesiDialog (anamnesi/page.tsx)

```typescript
// PRIMA (BUG): usava result.url dal backend, fallback su origin solo se relativo
const fullUrl = result
  ? result.url.startsWith("http") ? result.url
    : `${window.location.origin}${result.url}`
  : "";

// DOPO (FIX): sempre origin del browser + path dal token
const fullUrl = result
  ? `${window.location.origin}/public/anamnesi/${result.token}`
  : "";
```

### Risultato

| Scenario trainer | URL generato | Flusso |
|------------------|-------------|--------|
| Dev LAN (`192.168.x.x:3001`) | `http://192.168.x.x:3001/public/scheda/TOKEN` | → dev frontend (3001) → dev backend (8001) → crm_dev.db |
| Prod Tailscale (`name.ts.net`) | `https://name.ts.net/public/scheda/TOKEN` | → prod frontend (3000) → prod backend (8000) → crm.db |
| Localhost | Warning "stai usando localhost" | Link inaccessibile da altri device |

---

## Lezioni

1. **Mai costruire URL client-facing con env fissi del backend**: l'origine deve provenire dal contesto del browser (`window.location.origin`) perche' riflette l'effettivo punto di accesso del trainer.
2. **Dev/Prod condividono `data/.env`**: `PUBLIC_BASE_URL` e' lo stesso per entrambi. Qualsiasi logica che dipende da questo valore per costruire URL accessibili dall'esterno e' fragile quando dev e prod coesistono.
3. **Test portale da smartphone**: verificare sempre il ciclo completo (generazione link → apertura da device esterno) dopo modifiche all'infrastruttura di condivisione.

---

## Azioni follow-up

- [ ] Aggiungere test E2E: generazione link + validazione token nello stesso contesto (dev o prod)
- [ ] Valutare rimozione di `url` dalla `ShareTokenResponse` backend (il frontend lo costruisce, il campo backend e' ridondante)
- [ ] Aggiornare ADR-009 sezione URL generation con nota su `window.location.origin`

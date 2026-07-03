#!/usr/bin/env bash
# tools/scripts/check-all.sh
#
# Quality gate: backend lint + frontend production build.
# Run before each release-oriented commit.

set -euo pipefail

cd "$(dirname "$0")/../.."

FAIL=0

resolve_ruff() {
    if [ -x "venv/Scripts/ruff.exe" ]; then
        printf '%s\n' "venv/Scripts/ruff.exe"
        return 0
    fi

    if command -v ruff >/dev/null 2>&1; then
        command -v ruff
        return 0
    fi

    echo "ERRORE: ruff non trovato. Attiva la venv o installa ruff." >&2
    exit 1
}

RUFF_BIN="$(resolve_ruff)"

echo "=== Backend: ruff check ==="
if "$RUFF_BIN" check api/; then
    echo "  OK"
else
    echo "  FAIL - correggi gli errori ruff prima di committare."
    FAIL=1
fi

echo ""

echo "=== Backend: grep-guard invarianti finanziarie (ADR-016 / ADR-017 / ADR-018 / ADR-019) ==="
GUARD_FAIL=0

# ADR-016 — barriera "euro-da-crediti": il modulo di conguaglio NON deve leggere l'occupazione/crediti.
#   Il denaro del recesso deriva SOLO dalle sedute Completate + prezzo/versato/residuo; mai da
#   crediti_residui/crediti_usati/sedute_rinviate/sedute_prenotate (asse occupazione/display).
#   Anti-vacuita' (stessa lezione del guard ADR-019, G9.3): il file sorvegliato DEVE contenere ancora
#   la logica (compute_settlement) — un positive-fail su file svuotato/rilocato passerebbe in silenzio.
if ! grep -q 'def compute_settlement' api/services/contract_settlement.py; then
    echo "  FAIL [ADR-016]: compute_settlement non trovato in contract_settlement.py (guard vacuo dopo un refactor?) — ripuntare il guard."
    GUARD_FAIL=1
elif grep -nE 'crediti_residui|crediti_usati|sedute_rinviate|sedute_prenotate' api/services/contract_settlement.py; then
    echo "  FAIL [ADR-016]: contract_settlement.py riferisce l'occupazione/crediti — il conguaglio usa solo le sedute Completate + prezzo/versato/residuo."
    GUARD_FAIL=1
fi

# ADR-017 (bidirezionale) — il credit_breakdown (GROUP BY stato, contracts.py) DEVE restare
#   '!= Cancellato' per contare i Rinviato e alimentare `sedute_rinviate` (DISPLAY-EXEMPT §3.2): NON
#   "armonizzarlo" a IN(...), manderebbe sedute_rinviate a zero in silenzio. (La direzione opposta —
#   Rinviato NON deve occupare il credito — e' presidiata dai test AC-2/AC-3 di test_rinvio_libera_credito.)
if ! grep -A5 'select(Event.stato, func.count' api/routers/contracts.py | grep -q 'Event.stato != "Cancellato"'; then
    echo "  FAIL [ADR-017]: il credit_breakdown non conta piu' Rinviato (display) — mantieni '!= \"Cancellato\"' sul SOLO sito GROUP BY."
    GUARD_FAIL=1
fi

# ADR-018 — l'incasso di conguaglio (INCASSA_ORA / credito differito G7.10) DEVE restare un inflow
#   contrattuale: se esce da CONTRACT_CASH_IN, `is_contract_inflow` lo perde e il conguaglio sparisce
#   silenziosamente dai ricavi (gli aggregati cassa che usano il predicato lo escluderebbero).
if ! grep -A4 'CONTRACT_CASH_IN = frozenset' api/services/cash_categories.py | grep -q 'CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO'; then
    echo "  FAIL [ADR-018]: INCASSO_CONGUAGLIO_CONTRATTO non e' piu' in CONTRACT_CASH_IN — l'incasso di conguaglio sparirebbe dai ricavi."
    GUARD_FAIL=1
fi

# ADR-019 — reopen NON-distruttivo "ricalcola-e-instrada": la cassa mossa non si tocca. execute_reopen
#   NON deve soft-cancellare un CashMovement (reintrodurre `m.deleted_at = now` muterebbe periodi gia'
#   dichiarati e farebbe sparire reddito incassato). G9.3b: il corpo vive in transitions.py (executor) —
#   si estrae execute_reopen (fino a sync_contract_chiuso) e si verifica che non compaiano insieme
#   `select(CashMovement` (query CODE, non la prosa dei docstring) + soft-delete `deleted_at = now`.
#   Anti-vacuita': il corpo estratto DEVE contenere il marker R1 della cassa immutabile — se sparisce
#   (funzione rinominata/rilocata di nuovo) il guard FALLISCE invece di passare a vuoto (lezione G9.3:
#   il verifier ha trovato questo guard vacuo dopo la rilocazione contracts.py->transitions.py).
REOPEN_BODY=$(awk '/^def execute_reopen\(/{f=1} f&&/^def sync_contract_chiuso\(/{f=0} f' api/services/financial/transitions.py)
if ! printf '%s\n' "$REOPEN_BODY" | grep -q 'Cassa IMMUTABILE'; then
    echo "  FAIL [ADR-019]: corpo di execute_reopen non trovato in transitions.py (guard vacuo dopo un refactor?) — ripuntare il guard."
    GUARD_FAIL=1
elif printf '%s\n' "$REOPEN_BODY" | grep -q 'select(CashMovement' && printf '%s\n' "$REOPEN_BODY" | grep -qE 'deleted_at *= *now'; then
    echo "  FAIL [ADR-019]: execute_reopen interroga e soft-cancella un CashMovement — la cassa non si tocca (ricalcola-e-instrada, ADR-019)."
    GUARD_FAIL=1
fi

if [ "$GUARD_FAIL" -eq 0 ]; then
    echo "  OK"
else
    echo "  FAIL - guardia finanziaria violata (ADR-016/ADR-017/ADR-018/ADR-019)."
    FAIL=1
fi

echo ""

echo "=== Docs: guard ciclo-di-vita (AGENTS.md par.7, riordino 2026-07-03) ==="
DOCS_FAIL=0
# La POSIZIONE e' lo STATO: technical/ = solo SSoT evergreen, mai spec/piani.
# NB: compgen -G, non `ls glob1 glob2` (ls torna nonzero se UN glob non matcha -> guard cieco).
if compgen -G "docs/technical/SPEC_*.md" >/dev/null || compgen -G "docs/technical/IMPL_PLAN_*.md" >/dev/null; then
    echo "  FAIL [docs]: SPEC_*/IMPL_PLAN_* in docs/technical/ - le spec vivono in docs/specs/ (aperte) o docs/archive/specs/ (chiuse)."
    DOCS_FAIL=1
fi
# Una spec IMPLEMENTATA non resta tra le vive (fold-back + archiviazione nello stesso commit del gate).
if grep -l "^\*\*Stato:\*\* ✅" docs/specs/*.md >/dev/null 2>&1; then
    echo "  FAIL [docs]: spec con Stato IMPLEMENTATA in docs/specs/ - consuntiva e archivia (AGENTS.md par.7)."
    grep -l "^\*\*Stato:\*\* ✅" docs/specs/*.md | sed 's/^/         /'
    DOCS_FAIL=1
fi
if [ "$DOCS_FAIL" -eq 0 ]; then
    echo "  OK"
else
    FAIL=1
fi

echo ""

echo "=== Frontend: next build ==="
if (cd frontend && npx next build); then
    echo "  OK"
else
    echo "  FAIL - correggi gli errori TypeScript/build prima di committare."
    FAIL=1
fi

echo ""

if [ "$FAIL" -eq 0 ]; then
    echo "=== TUTTO OK - pronto per il commit. ==="
else
    echo "=== ERRORI TROVATI - correggi prima di committare. ==="
    exit 1
fi

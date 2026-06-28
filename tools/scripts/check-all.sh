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
if grep -nE 'crediti_residui|crediti_usati|sedute_rinviate|sedute_prenotate' api/services/contract_settlement.py; then
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

# ADR-019 — reopen NON-distruttivo "ricalcola-e-instrada": la cassa mossa non si tocca. reopen_contract
#   NON deve soft-cancellare un CashMovement (reintrodurre `m.deleted_at = now` muterebbe periodi gia'
#   dichiarati e farebbe sparire reddito incassato). Si estrae il corpo di reopen_contract (fino a
#   reopen_preview) e si verifica che non compaia insieme `CashMovement` + soft-delete `deleted_at = now`.
#   ('select(CashMovement' = query CODE, non la prosa del docstring che cita CashMovement legittimamente).
REOPEN_BODY=$(awk '/^def reopen_contract\(/{f=1} f&&/^def reopen_preview\(/{f=0} f' api/routers/contracts.py)
if printf '%s\n' "$REOPEN_BODY" | grep -q 'select(CashMovement' && printf '%s\n' "$REOPEN_BODY" | grep -qE 'deleted_at *= *now'; then
    echo "  FAIL [ADR-019]: reopen_contract interroga e soft-cancella un CashMovement — la cassa non si tocca (ricalcola-e-instrada, ADR-019)."
    GUARD_FAIL=1
fi

if [ "$GUARD_FAIL" -eq 0 ]; then
    echo "  OK"
else
    echo "  FAIL - guardia finanziaria violata (ADR-016/ADR-017/ADR-018/ADR-019)."
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

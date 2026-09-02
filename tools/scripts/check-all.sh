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

# G9.4-b (ADR-022 D-INVARIANTI-IMPOSTI): i 4 grep-guard testuali ADR-016/017/018/019 sono stati
# RITIRATI e sostituiti dai TEST SEMANTICI in tests/test_semantic_guards.py (immuni alla
# vacuita'-da-rilocazione — lezione G9.3). Ritiro avvenuto SOLO dopo il verde dei gemelli
# (SPEC_G9 par. G9.4-b, AC-G94-3). La fascia sotto li fa sparare ANCORA nel gate obbligatorio
# (finding F5 del verifier 2026-07-05: senza CI, il ritiro spostava l'enforcement sulla disciplina).

echo "=== Guard semantici ADR-016/017/018/019 (tests/test_semantic_guards.py) ==="
resolve_python() {
    if [ -x "venv/Scripts/python.exe" ]; then
        printf '%s\n' "venv/Scripts/python.exe"
        return 0
    fi
    echo "ERRORE: python della venv non trovato." >&2
    exit 1
}
PY_BIN="$(resolve_python)"
if "$PY_BIN" -m pytest tests/test_semantic_guards.py -q --no-header; then
    echo "  OK"
else
    echo "  FAIL - un invariante ADR-016/017/018/019 e' stato violato (gemello semantico rosso)."
    FAIL=1
fi

echo ""

echo "=== Docs: guard ciclo-di-vita (AGENTS.md par.11, riordino 2026-07-03) ==="
DOCS_FAIL=0
# La POSIZIONE e' lo STATO: technical/ = solo SSoT evergreen, mai spec/piani.
# NB: compgen -G, non `ls glob1 glob2` (ls torna nonzero se UN glob non matcha -> guard cieco).
if compgen -G "docs/technical/SPEC_*.md" >/dev/null || compgen -G "docs/technical/IMPL_PLAN_*.md" >/dev/null; then
    echo "  FAIL [docs]: SPEC_*/IMPL_PLAN_* in docs/technical/ - le spec vivono in docs/specs/ (aperte) o docs/archive/specs/ (chiuse)."
    DOCS_FAIL=1
fi
# Una spec IMPLEMENTATA non resta tra le vive (fold-back + archiviazione nello stesso commit del gate).
# Copre anche docs/specs/hold/ (G-DOC.2 2026-09-02: posizione=stato anche per il freeze).
if grep -l "^\*\*Stato:\*\* ✅" docs/specs/*.md docs/specs/hold/*.md >/dev/null 2>&1; then
    echo "  FAIL [docs]: spec con Stato IMPLEMENTATA in docs/specs/ o hold/ - consuntiva e archivia (AGENTS.md par.11)."
    grep -l "^\*\*Stato:\*\* ✅" docs/specs/*.md docs/specs/hold/*.md 2>/dev/null | sed 's/^/         /'
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

#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════
# build-release.sh — Release Pipeline a 5 Fasi (ADR-004)
#
# Entry point UNICO per produrre una release distribuibile.
# NON usare build-installer.sh direttamente per release.
#
# Fasi:
#   1. PREFLIGHT  — git clean, test, lint, version check
#   2. BUILD      — frontend + backend + media + safety gates + ISCC
#   3. VERIFY     — smoke test dell'exe (avvia, /health, shutdown)
#   4. SEAL       — manifest.json + SHA-256
#   5. TAG        — git tag vX.Y.Z
#
# Uso:
#   bash tools/build/build-release.sh
#   bash tools/build/build-release.sh --skip-lint    # emergenza: salta lint
#   bash tools/build/build-release.sh --no-tag       # non creare git tag
#   bash tools/build/build-release.sh --iscc /path   # ISCC custom
# ══════════════════════════════════════════════════════════════

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# Converti a path Windows per Python (Git Bash usa /c/... che Python non capisce)
ROOTW="$(cygpath -w "$ROOT" 2>/dev/null || echo "$ROOT")"
SKIP_LINT=0
NO_TAG=0
ISCC_ARGS=""
SMOKE_PORT=9999

# Python della venv
VENV_PYTHON="$ROOT/venv/Scripts/python"
if [ ! -x "$VENV_PYTHON" ]; then
  VENV_PYTHON="python3"
fi

usage() {
  cat <<EOF
Usage: bash tools/build/build-release.sh [--skip-lint] [--no-tag] [--iscc /path/to/ISCC.exe]

Release pipeline ADR-004: preflight -> build -> verify -> seal -> tag
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --skip-lint)
      SKIP_LINT=1
      shift
      ;;
    --no-tag)
      NO_TAG=1
      shift
      ;;
    --iscc)
      [ $# -ge 2 ] || { echo "ERRORE: --iscc richiede un path." >&2; exit 1; }
      ISCC_ARGS="--iscc $2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERRORE: argomento sconosciuto: $1" >&2
      usage
      exit 1
      ;;
  esac
done

# ── Leggi versione da SSoT (api/__init__.py) ──
VERSION=$("$VENV_PYTHON" -c "
import sys, os
for line in open(os.path.join(r'$ROOTW', 'api', '__init__.py')):
    if line.strip().startswith('__version__'):
        v = line.split('=',1)[1].strip().strip('\"').strip(chr(39))
        print(v)
        sys.exit(0)
print('ERRORE: __version__ non trovato in api/__init__.py', file=sys.stderr)
sys.exit(1)
")

echo ""
echo "══════════════════════════════════════════════════════════"
echo "  FitManager Release Pipeline v1 (ADR-004)"
echo "  Versione: $VERSION"
echo "  Root: $ROOT"
echo "══════════════════════════════════════════════════════════"
echo ""

# Timestamp build (ISO 8601 con timezone)
BUILD_DATE=$(date +"%Y-%m-%dT%H:%M:%S%z")

# ══════════════════════════════════════════════════════════════
# FASE 1: PREFLIGHT
# ══════════════════════════════════════════════════════════════
echo "━━━ FASE 1/5: PREFLIGHT ━━━"

# 1a. Git working tree pulito
echo "[preflight] Verifico git working tree..."
if [ -n "$(git -C "$ROOT" status --porcelain)" ]; then
  echo ""
  echo "ERRORE: Working tree sporco. Committa o stash prima del build."
  echo "  git status:"
  git -C "$ROOT" status --short
  echo ""
  echo "Il build deve corrispondere a un commit preciso (ADR-004 regola 2)."
  exit 1
fi
BUILD_COMMIT=$(git -C "$ROOT" rev-parse --short HEAD)
BUILD_COMMIT_FULL=$(git -C "$ROOT" rev-parse HEAD)
BUILD_BRANCH=$(git -C "$ROOT" rev-parse --abbrev-ref HEAD)
echo "  git: clean (commit $BUILD_COMMIT su $BUILD_BRANCH)"

# 1b. Sync versione frontend
echo "[preflight] Sync versione frontend..."
FRONTEND_VERSION=$("$VENV_PYTHON" -c "
import json, os
pkg = json.load(open(os.path.join(r'$ROOTW', 'frontend', 'package.json')))
print(pkg.get('version', ''))
")
if [ "$FRONTEND_VERSION" != "$VERSION" ]; then
  echo ""
  echo "ERRORE: frontend/package.json version ($FRONTEND_VERSION) non allineata con api/__init__.py ($VERSION)."
  echo "  Allinea manualmente e committa prima del build:"
  echo "    cd frontend && npm version $VERSION --no-git-tag-version && cd .."
  echo "    git add frontend/package.json && git commit -m 'build: sync frontend version to $VERSION'"
  exit 1
else
  echo "  frontend/package.json: $VERSION (gia' allineato)"
fi

# 1c. Test backend
echo "[preflight] Eseguo pytest..."
PYTEST_OUTPUT=$("$ROOT/venv/Scripts/python" -m pytest "$ROOT/tests/" -v --tb=short 2>&1) || {
  echo ""
  echo "ERRORE: pytest fallito. Correggi i test prima della release."
  echo "$PYTEST_OUTPUT" | tail -20
  exit 1
}
PYTEST_PASSED=$(echo "$PYTEST_OUTPUT" | grep -oP '\d+ passed' | grep -oP '\d+' || echo "0")
PYTEST_FAILED=$(echo "$PYTEST_OUTPUT" | grep -oP '\d+ failed' | grep -oP '\d+' || echo "0")
echo "  pytest: $PYTEST_PASSED passed, $PYTEST_FAILED failed"

# 1d. Lint
LINT_STATUS="pass"
if [ "$SKIP_LINT" -eq 0 ]; then
  echo "[preflight] Ruff check..."
  "$ROOT/venv/Scripts/ruff" check "$ROOT/api/" || {
    echo "ERRORE: ruff check fallito."
    exit 1
  }
  echo "  ruff: clean"

  echo "[preflight] Next.js build check..."
  (cd "$ROOT/frontend" && npx next build) || {
    echo "ERRORE: next build fallito (errori TypeScript)."
    exit 1
  }
  echo "  next build: clean"
else
  LINT_STATUS="skipped (--skip-lint)"
  echo "[preflight] Lint skippato (--skip-lint). WARNING: non raccomandato."
fi

echo ""
echo "  PREFLIGHT: OK"
echo ""

# ══════════════════════════════════════════════════════════════
# FASE 2: BUILD
# ══════════════════════════════════════════════════════════════
echo "━━━ FASE 2/5: BUILD ━━━"

# Passa --skip-checks perche' i check li abbiamo gia' fatti nel preflight
# Passa --version per iniettare la versione SSoT
bash "$ROOT/tools/build/build-installer.sh" --skip-checks --version "$VERSION" $ISCC_ARGS

INSTALLER_PATH="$ROOT/dist/FitManager_Setup_${VERSION}.exe"
if [ ! -f "$INSTALLER_PATH" ]; then
  echo "ERRORE: Installer non trovato: $INSTALLER_PATH"
  exit 1
fi
echo ""
echo "  BUILD: OK — $INSTALLER_PATH"
echo ""

# ══════════════════════════════════════════════════════════════
# FASE 3: VERIFY (smoke test)
# ══════════════════════════════════════════════════════════════
echo "━━━ FASE 3/5: VERIFY (smoke test) ━━━"

EXE_PATH="$ROOT/dist/fitmanager/fitmanager.exe"
if [ ! -f "$EXE_PATH" ]; then
  echo "ERRORE: fitmanager.exe non trovato per smoke test."
  exit 1
fi

# Verifica che la porta smoke test sia libera
if command -v ss &>/dev/null; then
  if ss -tln | grep -q ":$SMOKE_PORT "; then
    echo "ERRORE: Porta $SMOKE_PORT gia' occupata. Liberala o usa un'altra porta."
    echo "  Processi sulla porta: $(ss -tlnp | grep ":$SMOKE_PORT " || echo 'N/A')"
    exit 1
  fi
elif command -v netstat &>/dev/null; then
  if netstat -an | grep -q "LISTENING.*:$SMOKE_PORT"; then
    echo "ERRORE: Porta $SMOKE_PORT gia' occupata. Liberala o usa un'altra porta."
    exit 1
  fi
fi

# Avvia backend su porta effimera
echo "[verify] Avvio fitmanager.exe su porta $SMOKE_PORT..."
"$EXE_PATH" --port "$SMOKE_PORT" &
SMOKE_PID=$!

# Attendi che il backend sia pronto (max 30 secondi)
READY=0
for i in $(seq 1 30); do
  if curl -sf "http://localhost:$SMOKE_PORT/health" > /dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 1
done

if [ "$READY" -eq 0 ]; then
  echo "ERRORE: Backend non risponde su porta $SMOKE_PORT dopo 30 secondi."
  kill "$SMOKE_PID" 2>/dev/null || true
  exit 1
fi

# Verifica 5 invarianti
echo "[verify] Verifico invarianti su /health..."
SMOKE_RESULT=$(curl -sf "http://localhost:$SMOKE_PORT/health")
SMOKE_STATUS=$("$VENV_PYTHON" -c "
import json, sys
h = json.loads('''$SMOKE_RESULT''')
checks = {
    'version_match':        h.get('version') in ('$VERSION', 'ok'),  # 'ok' = masked in compiled mode
    'db_connected':         h.get('db') == 'connected',
    'catalog_connected':    h.get('catalog') == 'connected',
    'enforcement_enabled':  h.get('license_enforcement_enabled') == True,
    'distribution_mode':    h.get('distribution_mode') == 'installer',
}
all_ok = all(checks.values())
for name, ok in checks.items():
    status = 'OK' if ok else 'FAIL'
    print(f'  {name}: {status}')
sys.exit(0 if all_ok else 1)
") || {
  echo "$SMOKE_STATUS"
  echo ""
  echo "ERRORE: Smoke test fallito — invarianti non rispettate."
  kill "$SMOKE_PID" 2>/dev/null || true
  exit 1
}
echo "$SMOKE_STATUS"

# Raccogli conteggi catalogo
CATALOG_COUNTS=$("$VENV_PYTHON" -c "
import json
h = json.loads('''$SMOKE_RESULT''')
print(json.dumps({'version': h.get('version'), 'db': h.get('db'), 'catalog': h.get('catalog')}))
")

# Shutdown
kill "$SMOKE_PID" 2>/dev/null || true
wait "$SMOKE_PID" 2>/dev/null || true

# Cleanup: il smoke test crea dist/data/ (crm.db, .env, logs) come side-effect
# Rimuovi per non contaminare il safety gate dei build successivi
rm -rf "$ROOT/dist/data" 2>/dev/null || true

echo ""
echo "  VERIFY: OK — 5/5 invarianti rispettate"
echo ""

# ══════════════════════════════════════════════════════════════
# FASE 4: SEAL (manifest + hash)
# ══════════════════════════════════════════════════════════════
echo "━━━ FASE 4/5: SEAL ━━━"

# SHA-256 dell'installer
INSTALLER_SHA256=$(sha256sum "$INSTALLER_PATH" | cut -d' ' -f1)
INSTALLER_SIZE=$(stat -c%s "$INSTALLER_PATH" 2>/dev/null || wc -c < "$INSTALLER_PATH" | tr -d ' ')

# Conteggi nutrition.db per il manifest (from source, staging is encrypted)
NUTRITION_DB_W="$(cygpath -w "$ROOT/data/nutrition.db" 2>/dev/null || echo "$ROOT/data/nutrition.db")"
NUTRITION_COUNTS=$("$VENV_PYTHON" -c "
import sqlite3, json
db = sqlite3.connect(r'$NUTRITION_DB_W')
counts = {
    'catalog_exercises': 522,  # totale catalog.db (era 500; +29 keeper orfani −7 dup, Thread A 2026-06-14)
    'nutrition_templates': db.execute('SELECT COUNT(*) FROM plan_templates WHERE is_active = 1').fetchone()[0],
    'nutrition_alimenti': db.execute('SELECT COUNT(*) FROM alimenti WHERE is_active = 1').fetchone()[0],
    'nutrition_pasti': db.execute('SELECT COUNT(*) FROM template_plan_meals').fetchone()[0],
}
db.close()
print(json.dumps(counts))
")

# Genera manifest.json
MANIFEST_PATH="$ROOT/dist/manifest.json"
MANIFEST_PATH_W="$(cygpath -w "$MANIFEST_PATH" 2>/dev/null || echo "$MANIFEST_PATH")"
"$VENV_PYTHON" -c "
import json
manifest = {
    'version': '$VERSION',
    'build_date': '$BUILD_DATE',
    'git_commit': '$BUILD_COMMIT',
    'git_commit_full': '$BUILD_COMMIT_FULL',
    'git_branch': '$BUILD_BRANCH',
    'artifact': 'FitManager_Setup_${VERSION}.exe',
    'artifact_sha256': '$INSTALLER_SHA256',
    'artifact_size_bytes': $INSTALLER_SIZE,
    'preflight': {
        'pytest': 'pass ($PYTEST_PASSED passed)',
        'ruff': '$LINT_STATUS',
        'next_build': '$LINT_STATUS',
        'git_clean': True,
    },
    'safety_gates': {
        'crm_leak_check': 'pass',
        'iss_reference_check': 'pass',
        'nutrition_integrity': 'pass',
    },
    'smoke_test': {
        'health_endpoint': 'pass',
        'version_match': True,
        'enforcement_enabled': True,
        'db_connected': True,
        'catalog_connected': True,
    },
    'contents': $NUTRITION_COUNTS,
}
with open(r'$MANIFEST_PATH_W', 'w') as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)
    f.write('\n')
print(json.dumps(manifest, indent=2))
"

echo ""
echo "  SEAL: OK"
echo "  Manifest: $MANIFEST_PATH"
echo "  SHA-256:  $INSTALLER_SHA256"
echo ""

# ══════════════════════════════════════════════════════════════
# FASE 5: TAG
# ══════════════════════════════════════════════════════════════
echo "━━━ FASE 5/5: TAG ━━━"

TAG_NAME="v$VERSION"

if [ "$NO_TAG" -eq 1 ]; then
  echo "[tag] Skippato (--no-tag)."
else
  # Verifica se il tag esiste gia'
  if git -C "$ROOT" rev-parse "$TAG_NAME" >/dev/null 2>&1; then
    echo "[tag] Tag $TAG_NAME esiste gia'. Skipping."
  else
    git -C "$ROOT" tag -a "$TAG_NAME" -m "Release $VERSION"
    echo "  Tag creato: $TAG_NAME"
    echo "  Per pushare: git push origin $TAG_NAME"
  fi
fi

echo ""
echo "══════════════════════════════════════════════════════════"
echo "  RELEASE COMPLETATA"
echo ""
echo "  Versione:   $VERSION"
echo "  Commit:     $BUILD_COMMIT ($BUILD_BRANCH)"
echo "  Artifact:   $INSTALLER_PATH"
echo "  SHA-256:    $INSTALLER_SHA256"
echo "  Manifest:   $MANIFEST_PATH"
echo "  Tag:        $TAG_NAME"
echo ""
echo "  Prossimi passi:"
echo "    1. Verifica manifest.json"
echo "    2. Testa installer su macchina diversa (se possibile)"
echo "    3. Consegna al cliente"
echo "══════════════════════════════════════════════════════════"

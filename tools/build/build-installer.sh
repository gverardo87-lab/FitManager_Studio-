#!/usr/bin/env bash
# build-installer.sh -- Rebuild frontend, backend, media staging and Inno Setup installer.
#
# Per release complete usare: build-release.sh (ADR-004)
# Questo script e' il sub-step BUILD, chiamato da build-release.sh.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# Converti a path Windows per Python (Git Bash usa /c/... che Python non capisce)
ROOTW="$(cygpath -w "$ROOT" 2>/dev/null || echo "$ROOT")"
INSTALLER_VERSION=""
ISCC_PATH=""
SKIP_CHECKS=0

# Python della venv (ha tutte le dipendenze incluso cryptography)
VENV_PYTHON="$ROOT/venv/Scripts/python"
if [ ! -x "$VENV_PYTHON" ]; then
  VENV_PYTHON="python3"
fi

# ── Leggi versione da SSoT (api/__init__.py) ──
read_version_from_ssot() {
  "$VENV_PYTHON" -c "
import sys, os
for line in open(os.path.join(r'$ROOTW', 'api', '__init__.py')):
    if line.strip().startswith('__version__'):
        v = line.split('=',1)[1].strip().strip('\"').strip(chr(39))
        print(v)
        sys.exit(0)
print('ERRORE: __version__ non trovato in api/__init__.py', file=sys.stderr)
sys.exit(1)
"
}

usage() {
  cat <<EOF
Usage: bash tools/build/build-installer.sh [--skip-checks] [--version X.Y.Z] [--iscc /path/to/ISCC.exe]

Build order:
  1. check-all.sh (unless --skip-checks)
  2. build-frontend.sh
  3. build-backend.sh
  4. build-media.sh
  5. Inno Setup compilation

La versione viene letta da api/__init__.py (SSoT) se --version non e' specificato.
Per release complete usare: build-release.sh (ADR-004)
EOF
}

resolve_iscc() {
  if [ -n "$ISCC_PATH" ]; then
    printf '%s\n' "$ISCC_PATH"
    return 0
  fi

  local candidates=(
    "C:/Program Files (x86)/Inno Setup 6/ISCC.exe"
    "C:/Program Files/Inno Setup 6/ISCC.exe"
    "C:/Users/gvera/AppData/Local/Programs/Inno Setup 6/ISCC.exe"
  )

  local candidate
  for candidate in "${candidates[@]}"; do
    if [ -f "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  echo "ERRORE: ISCC.exe non trovato. Usa --iscc per indicare il path." >&2
  exit 1
}

while [ $# -gt 0 ]; do
  case "$1" in
    --skip-checks)
      SKIP_CHECKS=1
      shift
      ;;
    --version)
      [ $# -ge 2 ] || { echo "ERRORE: --version richiede un valore." >&2; exit 1; }
      INSTALLER_VERSION="$2"
      shift 2
      ;;
    --iscc)
      [ $# -ge 2 ] || { echo "ERRORE: --iscc richiede un path." >&2; exit 1; }
      ISCC_PATH="$2"
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

# Se la versione non e' stata passata, leggila da SSoT
if [ -z "$INSTALLER_VERSION" ]; then
  INSTALLER_VERSION="$(read_version_from_ssot)"
fi

echo "=== build-installer.sh ==="
echo "Project root: $ROOT"
echo "Installer version: $INSTALLER_VERSION"

RELEASE_DATA_DIR="$ROOT/dist/release-data"

if [ "$SKIP_CHECKS" -eq 0 ]; then
  bash "$ROOT/tools/scripts/check-all.sh"
else
  echo "Skipping quality gate (--skip-checks)."
fi

bash "$ROOT/tools/build/build-frontend.sh"
bash "$ROOT/tools/build/build-backend.sh"
bash "$ROOT/tools/build/build-media.sh"

# ── Stage frpc binary (tunnel FRP) into backend bundle ──
FRPC_SRC="$ROOT/tools/bin/frpc.exe"
FRPC_DEST="$ROOT/dist/fitmanager/frpc.exe"
if [ ! -f "$FRPC_SRC" ]; then
  echo "ERRORE CRITICO: frpc.exe non trovato in tools/bin/."
  echo "  Scaricare da https://github.com/fatedier/frp/releases e copiare in tools/bin/"
  exit 1
fi
cp "$FRPC_SRC" "$FRPC_DEST"
echo "frpc.exe staged in dist/fitmanager/ ($(du -h "$FRPC_DEST" | cut -f1))"

echo "Staging immutable release data..."
mkdir -p "$RELEASE_DATA_DIR"
cp "$ROOT/data/catalog.db" "$RELEASE_DATA_DIR/catalog.db"
cp "$ROOT/data/nutrition.db" "$RELEASE_DATA_DIR/nutrition.db"
cp "$ROOT/data/license_public.pem" "$RELEASE_DATA_DIR/license_public.pem"
RELEASE_DATA_DIR_W="$(cygpath -w "$RELEASE_DATA_DIR" 2>/dev/null || echo "$RELEASE_DATA_DIR")"

# ── Safety Gate 1: CRM data leak prevention ──
echo "Safety gate: verifico assenza crm.db in dist/..."
if find "$ROOT/dist" -name "crm.db" -o -name "crm_dev.db" | grep -q .; then
  echo "ERRORE CRITICO: crm.db trovato in dist/ — dati trainer reali!"
  exit 1
fi

# ── Safety Gate 2: fitmanager.iss non deve referenziare crm.db ──
if grep -qi 'crm\.db\|crm_dev\.db' "$ROOT/installer/fitmanager.iss"; then
  echo "ERRORE CRITICO: fitmanager.iss referenzia crm.db!"
  exit 1
fi

# ── Safety Gate 3: nutrition.db integrity check ──
echo "Safety gate: verifico integrita' nutrition.db..."
NUTRITION_DB="$(cygpath -w "$RELEASE_DATA_DIR/nutrition.db" 2>/dev/null || echo "$RELEASE_DATA_DIR/nutrition.db")"
"$VENV_PYTHON" -c "
import sqlite3, sys
db = sqlite3.connect(r'$NUTRITION_DB')
checks = {
    'template attivi': ('SELECT COUNT(*) FROM plan_templates WHERE is_active = 1', 8),
    'pasti template': ('SELECT COUNT(*) FROM template_plan_meals', 200),
    'componenti template': ('SELECT COUNT(*) FROM template_plan_components', 500),
    'alimenti attivi': ('SELECT COUNT(*) FROM alimenti WHERE is_active = 1', 800),
}
failed = False
for label, (query, threshold) in checks.items():
    count = db.execute(query).fetchone()[0]
    status = 'OK' if count >= threshold else 'FAIL'
    print(f'  {label}: {count} (soglia >= {threshold}) [{status}]')
    if count < threshold:
        failed = True
db.close()
if failed:
    print('ERRORE CRITICO: nutrition.db non supera le soglie minime!')
    sys.exit(1)
print('nutrition.db integrity: OK')
"
if [ $? -ne 0 ]; then
  echo "ERRORE CRITICO: nutrition.db integrity check fallito!"
  exit 1
fi

# ── Encrypt catalog databases (AES-256-GCM) ──
echo "Encrypting catalog databases..."
"$VENV_PYTHON" -c "
import sys; sys.path.insert(0, r'$ROOTW')
from pathlib import Path
from api.services.db_crypto import encrypt_db
encrypt_db(Path(r'$RELEASE_DATA_DIR_W/catalog.db'), Path(r'$RELEASE_DATA_DIR_W/catalog.db.enc'))
encrypt_db(Path(r'$RELEASE_DATA_DIR_W/nutrition.db'), Path(r'$RELEASE_DATA_DIR_W/nutrition.db.enc'))
print('  catalog.db.enc + nutrition.db.enc created')
"
rm "$RELEASE_DATA_DIR/catalog.db" "$RELEASE_DATA_DIR/nutrition.db"
echo "  Plain .db files removed from staging"

echo "Tutti i safety gate superati."

ISCC_BIN="$(resolve_iscc)"
echo "Using ISCC: $ISCC_BIN"

# //D (doppio slash) impedisce a MSYS/Git Bash di convertire /D in un path Windows
"$ISCC_BIN" "//DMyAppVersion=$INSTALLER_VERSION" "$ROOT/installer/fitmanager.iss"

echo "Installer atteso: $ROOT/dist/FitManager_Setup_${INSTALLER_VERSION}.exe"
echo "=== build-installer.sh completato ==="

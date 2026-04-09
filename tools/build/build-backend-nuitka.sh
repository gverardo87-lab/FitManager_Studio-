#!/usr/bin/env bash
# tools/build/build-backend-nuitka.sh
# Produce the Nuitka standalone bundle for the backend API.
# Python -> C -> native x86-64. Zero .pyc decompilable.
#
# Prerequisiti:
#   pip install nuitka
#   Nuitka scarica MinGW64 automaticamente al primo build.
#   Build time: 10-30 min (vs 1-2 min PyInstaller).
#
# Rollback: usa build-backend.sh (PyInstaller) se bloccante.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

resolve_python() {
  if [ -x "$ROOT/venv/Scripts/python.exe" ]; then
    printf '%s\n' "$ROOT/venv/Scripts/python.exe"
    return 0
  fi

  if command -v python >/dev/null 2>&1; then
    command -v python
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi

  echo "ERRORE: Python non trovato. Attiva la venv o installa Python." >&2
  exit 1
}

PYTHON_BIN="$(resolve_python)"

echo "=========================================="
echo "  FitManager - Backend Nuitka Build"
echo "=========================================="

if ! "$PYTHON_BIN" -m nuitka --version > /dev/null 2>&1; then
  echo "ERRORE: Nuitka non installato."
  echo "  pip install nuitka"
  exit 1
fi

echo "-> Nuitka $("$PYTHON_BIN" -m nuitka --version | head -1)"

echo "-> Avvio build (10-30 minuti)..."
cd "$ROOT"

"$PYTHON_BIN" -m nuitka \
    --standalone \
    --mingw64 \
    --output-dir="$ROOT/dist" \
    --output-filename=fitmanager.exe \
    --include-package=api \
    --include-package=uvicorn \
    --include-package=uvicorn.logging \
    --include-package=uvicorn.loops \
    --include-package=uvicorn.protocols \
    --include-package=uvicorn.lifespan \
    --include-package=fastapi \
    --include-package=starlette \
    --include-package=pydantic \
    --include-package=pydantic_core \
    --include-package=sqlmodel \
    --include-package=sqlalchemy \
    --include-package=sqlalchemy.dialects.sqlite \
    --include-package=jose \
    --include-package=bcrypt \
    --include-package=cryptography \
    --include-package=multipart \
    --include-package=email_validator \
    --include-package=openpyxl \
    --include-package=dotenv \
    --include-module=difflib \
    --include-module=sqlite3 \
    --nofollow-import-to=torch \
    --nofollow-import-to=torchvision \
    --nofollow-import-to=torchaudio \
    --nofollow-import-to=transformers \
    --nofollow-import-to=sentence_transformers \
    --nofollow-import-to=chromadb \
    --nofollow-import-to=langchain \
    --nofollow-import-to=langchain_community \
    --nofollow-import-to=langchain_core \
    --nofollow-import-to=langchain_chroma \
    --nofollow-import-to=langchain_ollama \
    --nofollow-import-to=langchain_text_splitters \
    --nofollow-import-to=sklearn \
    --nofollow-import-to=scikit-learn \
    --nofollow-import-to=joblib \
    --nofollow-import-to=ollama \
    --nofollow-import-to=streamlit \
    --nofollow-import-to=plotly \
    --nofollow-import-to=matplotlib \
    --nofollow-import-to=PIL \
    --nofollow-import-to=tkinter \
    --nofollow-import-to=pytest \
    --nofollow-import-to=IPython \
    --nofollow-import-to=notebook \
    --nofollow-import-to=jupyterlab \
    --nofollow-import-to=alembic \
    --enable-plugin=anti-bloat \
    --assume-yes-for-downloads \
    --windows-console-mode=force \
    "$ROOT/tools/build/entry_point.py"

# Nuitka produces entry_point.dist/ — rename to match PyInstaller layout
NUITKA_DIST="$ROOT/dist/entry_point.dist"
TARGET_DIR="$ROOT/dist/fitmanager"

if [ ! -d "$NUITKA_DIST" ]; then
  echo "ERRORE: Nuitka output non trovato: $NUITKA_DIST"
  exit 1
fi

# Remove old PyInstaller output if present
rm -rf "$TARGET_DIR" 2>/dev/null || true
mv "$NUITKA_DIST" "$TARGET_DIR"

# Rename exe to expected name
if [ -f "$TARGET_DIR/entry_point.exe" ]; then
  mv "$TARGET_DIR/entry_point.exe" "$TARGET_DIR/fitmanager.exe"
fi

EXE_PATH="$TARGET_DIR/fitmanager.exe"
if [ ! -f "$EXE_PATH" ]; then
  echo "ERRORE: fitmanager.exe non trovato dopo rename!"
  exit 1
fi

SIZE=$(du -sh "$TARGET_DIR/" | cut -f1)
echo ""
echo "=========================================="
echo "  Build Nuitka completata!"
echo ""
echo "  Bundle: $TARGET_DIR/ ($SIZE)"
echo "  Exe:    $EXE_PATH"
echo ""
echo "  Test:"
echo "    dist/fitmanager/fitmanager.exe --port 8002"
echo "    curl http://localhost:8002/health"
echo "=========================================="

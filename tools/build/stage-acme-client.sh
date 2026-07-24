#!/usr/bin/env bash
# Verifica e stagea il client ACME pinato nel bundle backend.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LEGO_VERSION="5.2.1"
LEGO_SHA256="e2d5f33c26032197db5953f8cfd93aa960f08cf2014c887b79ba950cb5b525e5"
LEGO_LICENSE_SHA256="bf12923e71046c564f4163c00c3aa6b3581b51858f099a035f5baf2216addf6e"

SOURCE="$ROOT/tools/bin/lego.exe"
DESTINATION_DIR="$ROOT/dist/fitmanager"
LICENSE_SOURCE="$ROOT/tools/licenses/lego-MIT.txt"

usage() {
  cat <<EOF
Usage: bash tools/build/stage-acme-client.sh [--source PATH] [--destination-dir PATH] [--license-source PATH]

Verifica il client lego v$LEGO_VERSION windows/amd64 e la licenza MIT, poi li copia
nel bundle. Non effettua download.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --source)
      [ $# -ge 2 ] || { echo "ERRORE: --source richiede un path." >&2; exit 1; }
      SOURCE="$2"
      shift 2
      ;;
    --destination-dir)
      [ $# -ge 2 ] || { echo "ERRORE: --destination-dir richiede un path." >&2; exit 1; }
      DESTINATION_DIR="$2"
      shift 2
      ;;
    --license-source)
      [ $# -ge 2 ] || { echo "ERRORE: --license-source richiede un path." >&2; exit 1; }
      LICENSE_SOURCE="$2"
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

if ! command -v sha256sum >/dev/null 2>&1; then
  echo "ERRORE CRITICO: sha256sum non disponibile; verifica lego impossibile." >&2
  exit 1
fi

if [ ! -f "$SOURCE" ]; then
  echo "ERRORE CRITICO: lego.exe non trovato: $SOURCE" >&2
  echo "  Eseguire: powershell -ExecutionPolicy Bypass -File tools/build/fetch-lego.ps1" >&2
  exit 1
fi

ACTUAL_SHA256="$(sha256sum "$SOURCE" | cut -d' ' -f1 | tr '[:upper:]' '[:lower:]')"
if [ "$ACTUAL_SHA256" != "$LEGO_SHA256" ]; then
  echo "ERRORE CRITICO: lego.exe hash mismatch." >&2
  echo "  atteso: $LEGO_SHA256" >&2
  echo "  trovato: $ACTUAL_SHA256" >&2
  exit 1
fi

VERSION_OUTPUT="$({ "$SOURCE" --version; } 2>&1 | tr -d '\r')" || {
  echo "ERRORE CRITICO: lego.exe non eseguibile dopo hash valido." >&2
  exit 1
}
EXPECTED_VERSION="lego version $LEGO_VERSION windows/amd64"
if [ "$VERSION_OUTPUT" != "$EXPECTED_VERSION" ]; then
  echo "ERRORE CRITICO: lego.exe versione/target inattesi." >&2
  echo "  atteso: $EXPECTED_VERSION" >&2
  echo "  trovato: $VERSION_OUTPUT" >&2
  exit 1
fi

if [ ! -f "$LICENSE_SOURCE" ]; then
  echo "ERRORE CRITICO: licenza third-party lego assente: $LICENSE_SOURCE" >&2
  exit 1
fi
ACTUAL_LICENSE_SHA256="$(sha256sum "$LICENSE_SOURCE" | cut -d' ' -f1 | tr '[:upper:]' '[:lower:]')"
if [ "$ACTUAL_LICENSE_SHA256" != "$LEGO_LICENSE_SHA256" ]; then
  echo "ERRORE CRITICO: licenza lego hash mismatch." >&2
  echo "  atteso: $LEGO_LICENSE_SHA256" >&2
  echo "  trovato: $ACTUAL_LICENSE_SHA256" >&2
  exit 1
fi

mkdir -p "$DESTINATION_DIR/THIRD_PARTY_LICENSES"
cp "$SOURCE" "$DESTINATION_DIR/lego.exe"
cp "$LICENSE_SOURCE" "$DESTINATION_DIR/THIRD_PARTY_LICENSES/lego-MIT.txt"

STAGED_SHA256="$(sha256sum "$DESTINATION_DIR/lego.exe" | cut -d' ' -f1 | tr '[:upper:]' '[:lower:]')"
if [ "$STAGED_SHA256" != "$LEGO_SHA256" ]; then
  echo "ERRORE CRITICO: lego.exe corrotto durante lo staging." >&2
  exit 1
fi

echo "lego.exe v$LEGO_VERSION verificato e staged in dist/fitmanager/"
echo "Licenza MIT staged in dist/fitmanager/THIRD_PARTY_LICENSES/"

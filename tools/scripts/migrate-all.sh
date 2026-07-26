#!/usr/bin/env bash
# tools/scripts/migrate-all.sh
#
# Applica le migrazioni Alembic all'unico database business configurato.
# Uso: bash tools/scripts/migrate-all.sh
#
# REGOLA BLINDATA: ogni volta che crei una migrazione Alembic, esegui questo
# script. DATABASE_URL ha priorita'; il fallback canonico e' data/crm.db.

set -euo pipefail

cd "$(dirname "$0")/../.."

TARGET_DB="${DATABASE_URL:-sqlite:///data/crm.db}"

if [[ "${TARGET_DB,,}" == *"crm_dev.db"* ]]; then
    echo "ERRORE: crm_dev.db e' legacy e non puo' essere un target di migrazione." >&2
    exit 1
fi

export DATABASE_URL="$TARGET_DB"

echo "=== Migrazione database business configurato ==="
alembic upgrade head
echo "  OK - database business aggiornato a head."

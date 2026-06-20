#!/usr/bin/env bash
# tools/scripts/restart-backend.sh
#
# Restart pulito di un backend uvicorn su Windows.
# Killa il vecchio (inclusi worker figli), poi rilancia.
#
# Uso:
#   bash tools/scripts/restart-backend.sh dev     → porta 8001 (reload),  crm.db
#   bash tools/scripts/restart-backend.sh prod    → porta 8000 (no reload), crm.db
#
# UN SOLO DATABASE (crm.db). L'offset di porta dev(8001)/prod(8000) serve solo a
# far coesistere lo sviluppo con un'eventuale app installata di produzione sulla
# stessa macchina. Nessun crm_dev.db: il dual-DB e' stato rimosso (2026-06-09).

set -euo pipefail

cd "$(dirname "$0")/../.."

ENV="${1:?Uso: restart-backend.sh <dev|prod>}"

case "$ENV" in
    dev)
        PORT=8001
        DB_URL="sqlite:///data/crm.db"
        ;;
    prod)
        PORT=8000
        DB_URL="sqlite:///data/crm.db"
        ;;
    *)
        echo "Errore: usa 'dev' o 'prod'"
        exit 1
        ;;
esac

echo "=== Restart backend $ENV (porta $PORT) ==="

# Step 1: Kill vecchio processo
bash tools/scripts/kill-port.sh "$PORT"

# Step 2: Avvia nuovo uvicorn
# PROD: senza --reload (dati reali, zero downtime durante sviluppo)
# DEV:  con --reload (hot reload per sviluppo)
echo ""
if [ "$ENV" = "prod" ]; then
    echo "  Avvio uvicorn PROD su porta $PORT (no reload)..."
    DATABASE_URL="$DB_URL" venv/Scripts/uvicorn api.main:app \
        --host 0.0.0.0 --port "$PORT" &
else
    echo "  Avvio uvicorn DEV su porta $PORT (reload attivo)..."
    DATABASE_URL="$DB_URL" venv/Scripts/uvicorn api.main:app \
        --reload --host 0.0.0.0 --port "$PORT" &
fi

# Step 3: Attendi e verifica
sleep 3
HEALTH=$(curl -s "http://localhost:${PORT}/health" 2>/dev/null || echo "FAIL")

if echo "$HEALTH" | grep -q '"ok"'; then
    echo "  Backend $ENV attivo su porta $PORT"
else
    echo "  ERRORE: backend non risponde su porta $PORT"
    echo "  Response: $HEALTH"
    exit 1
fi

#!/usr/bin/env bash
# R0.1.5: abilita vhostHTTPPort=80 su FRPS con backup, verifica e rollback.

set -euo pipefail
umask 077

MODE=""
INPUT_CONFIG=""
OUTPUT_CONFIG=""
FRP_ROOT=""
SERVICE_NAME="frps"

usage() {
  cat <<'EOF'
Uso:
  bash tools/operations/apply-frps-http01.sh --render-only --config INPUT --output OUTPUT
  sudo bash tools/operations/apply-frps-http01.sh --apply --frp-root FRP_ROOT

--render-only  Produce una candidate idempotente, senza modificare servizi o firewall.
--apply        Verifica FRPS, conserva un backup, apre UFW 80/tcp, applica e riavvia.

Lo script non legge né stampa password/dashboard token presenti in frps.toml.
EOF
}

render_config() {
  local input_path="$1"
  local output_path="$2"

  awk '
    BEGIN { in_top = 1; seen = 0; fatal = 0 }
    in_top && /^[[:space:]]*\[/ {
      if (!seen) {
        print "vhostHTTPPort = 80"
      }
      in_top = 0
    }
    in_top && /^[[:space:]]*vhostHTTPPort[[:space:]]*=/ {
      normalized = $0
      sub(/\r$/, "", normalized)
      if (seen) {
        print "ERRORE: vhostHTTPPort duplicato nel top-level" > "/dev/stderr"
        fatal = 43
        exit fatal
      }
      if (normalized !~ /^[[:space:]]*vhostHTTPPort[[:space:]]*=[[:space:]]*80([[:space:]]*(#.*)?)?$/) {
        print "ERRORE: vhostHTTPPort esistente ma diverso da 80" > "/dev/stderr"
        fatal = 42
        exit fatal
      }
      seen = 1
    }
    { print }
    END {
      if (fatal) {
        exit fatal
      }
      if (in_top && !seen) {
        print "vhostHTTPPort = 80"
      }
    }
  ' "$input_path" > "$output_path"
}

while [ $# -gt 0 ]; do
  case "$1" in
    --render-only)
      MODE="render"
      shift
      ;;
    --apply)
      MODE="apply"
      shift
      ;;
    --config)
      [ $# -ge 2 ] || { echo "ERRORE: --config richiede un path." >&2; exit 1; }
      INPUT_CONFIG="$2"
      shift 2
      ;;
    --output)
      [ $# -ge 2 ] || { echo "ERRORE: --output richiede un path." >&2; exit 1; }
      OUTPUT_CONFIG="$2"
      shift 2
      ;;
    --frp-root)
      [ $# -ge 2 ] || { echo "ERRORE: --frp-root richiede un path." >&2; exit 1; }
      FRP_ROOT="$2"
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

if [ "$MODE" = "render" ]; then
  [ -n "$INPUT_CONFIG" ] || { echo "ERRORE: --config obbligatorio." >&2; exit 1; }
  [ -n "$OUTPUT_CONFIG" ] || { echo "ERRORE: --output obbligatorio." >&2; exit 1; }
  [ -f "$INPUT_CONFIG" ] || { echo "ERRORE: config non trovata: $INPUT_CONFIG" >&2; exit 1; }
  [ "$INPUT_CONFIG" != "$OUTPUT_CONFIG" ] || {
    echo "ERRORE: input e output devono essere distinti." >&2
    exit 1
  }
  render_config "$INPUT_CONFIG" "$OUTPUT_CONFIG"
  exit 0
fi

if [ "$MODE" != "apply" ] || [ -z "$FRP_ROOT" ]; then
  usage
  exit 1
fi
if [ "${EUID:-$(id -u)}" -ne 0 ]; then
  echo "ERRORE: --apply richiede root." >&2
  exit 1
fi

for required_command in awk chmod chown cmp cp date grep install mktemp mv readlink rm ss systemctl ufw; do
  command -v "$required_command" >/dev/null 2>&1 || {
    echo "ERRORE: comando richiesto assente: $required_command" >&2
    exit 1
  }
done

FRP_ROOT_REAL="$(readlink -f "$FRP_ROOT")"
[ -d "$FRP_ROOT_REAL" ] || { echo "ERRORE: FRP root non trovata: $FRP_ROOT" >&2; exit 1; }
CONFIG_PATH="$FRP_ROOT_REAL/frps.toml"
FRPS_BIN="$FRP_ROOT_REAL/frps"
BACKUP_DIR="$FRP_ROOT_REAL/backups"
[ -f "$CONFIG_PATH" ] || { echo "ERRORE: config FRPS non trovata." >&2; exit 1; }
[ -x "$FRPS_BIN" ] || { echo "ERRORE: binario FRPS non eseguibile." >&2; exit 1; }

if ! ufw status | grep -q '^Status: active'; then
  echo "ERRORE: UFW non attivo; abilitazione automatica rifiutata per non rischiare SSH." >&2
  exit 1
fi
systemctl is-active --quiet "$SERVICE_NAME" || {
  echo "ERRORE: servizio $SERVICE_NAME non attivo prima del change." >&2
  exit 1
}

CANDIDATE_PATH="$(mktemp "$FRP_ROOT_REAL/.frps.toml.r015.XXXXXX")"
BACKUP_PATH=""
FIREWALL_ADDED=0
CONFIG_APPLIED=0

cleanup_candidate() {
  if [ -n "$CANDIDATE_PATH" ] && [ -f "$CANDIDATE_PATH" ]; then
    rm -f -- "$CANDIDATE_PATH"
  fi
}

rollback() {
  local rollback_status=0
  echo "ROLLBACK R0.1.5 in corso..." >&2
  if [ "$CONFIG_APPLIED" -eq 1 ] && [ -f "$BACKUP_PATH" ]; then
    local restore_path
    local restored=0
    restore_path="$(mktemp "$FRP_ROOT_REAL/.frps.toml.rollback.XXXXXX")"
    if cp -p -- "$BACKUP_PATH" "$restore_path" && mv -f -- "$restore_path" "$CONFIG_PATH"; then
      restored=1
    else
      rollback_status=1
      rm -f -- "$restore_path"
    fi
    if [ "$restored" -eq 1 ]; then
      systemctl restart "$SERVICE_NAME" || rollback_status=1
    fi
  fi
  if [ "$FIREWALL_ADDED" -eq 1 ]; then
    ufw --force delete allow 80/tcp >/dev/null || rollback_status=1
  fi
  if [ "$rollback_status" -ne 0 ]; then
    echo "ROLLBACK INCOMPLETO: intervento manuale richiesto; backup $BACKUP_PATH" >&2
  else
    echo "Rollback completato; backup preservato in $BACKUP_PATH" >&2
  fi
}

on_exit() {
  local status=$?
  if [ "$status" -ne 0 ] && { [ "$CONFIG_APPLIED" -eq 1 ] || [ "$FIREWALL_ADDED" -eq 1 ]; }; then
    rollback
  fi
  cleanup_candidate
  exit "$status"
}
trap on_exit EXIT

render_config "$CONFIG_PATH" "$CANDIDATE_PATH"
"$FRPS_BIN" verify -c "$CANDIDATE_PATH"

CONFIG_CHANGED=0
if ! cmp -s -- "$CONFIG_PATH" "$CANDIDATE_PATH"; then
  CONFIG_CHANGED=1
  if ss -H -ltn 'sport = :80' | grep -q .; then
    echo "ERRORE: porta 80 già occupata prima del change FRPS." >&2
    exit 1
  fi
fi

install -d -m 700 -- "$BACKUP_DIR"
BACKUP_PATH="$(mktemp "$BACKUP_DIR/frps.toml.$(date -u +%Y%m%dT%H%M%SZ).XXXXXX.r015.bak")"
cp -p -- "$CONFIG_PATH" "$BACKUP_PATH"
cmp -s -- "$CONFIG_PATH" "$BACKUP_PATH" || {
  echo "ERRORE: verifica backup frps.toml fallita." >&2
  exit 1
}
echo "Backup verificato: $BACKUP_PATH"

if ! ufw status | grep -Eq '^80/tcp[[:space:]]+ALLOW'; then
  ufw allow 80/tcp comment 'ACME HTTP-01 via FRP'
  FIREWALL_ADDED=1
fi

if [ "$CONFIG_CHANGED" -eq 1 ]; then
  chown --reference="$CONFIG_PATH" "$CANDIDATE_PATH"
  chmod --reference="$CONFIG_PATH" "$CANDIDATE_PATH"
  mv -f -- "$CANDIDATE_PATH" "$CONFIG_PATH"
  CANDIDATE_PATH=""
  CONFIG_APPLIED=1
fi

systemctl restart "$SERVICE_NAME"
systemctl is-active --quiet "$SERVICE_NAME"
"$FRPS_BIN" verify -c "$CONFIG_PATH"
ss -H -ltn 'sport = :80' | grep -q . || {
  echo "ERRORE: FRPS attivo ma nessun listener su 80/tcp." >&2
  exit 1
}

CONFIG_APPLIED=0
FIREWALL_ADDED=0
echo "R0.1.5 edge apply completato: FRPS attivo, config valida, listener 80/tcp presente."
echo "Backup preservato: $BACKUP_PATH"
echo "Eseguire ora il probe esterno strict; non considerare il live chiuso senza i suoi esiti."

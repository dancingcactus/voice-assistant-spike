#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIDFILE="$ROOT/.tool_logs/server_pids"
LOGDIR="$ROOT/.tool_logs"
mkdir -p "$LOGDIR"

log() { echo "[$(date +'%T')] $*"; }

start_backend() {
  log "Starting backend..."
  pushd "$ROOT/backend" >/dev/null
  if [ -d ".venv" ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
    log "Ensuring Python requirements are installed..."
    pip install -r requirements.txt requests python-dateutil filelock || true
  else
    python -m venv .venv
    # shellcheck disable=SC1091
    source .venv/bin/activate
    pip install -r requirements.txt requests python-dateutil filelock
  fi
  nohup python -m uvicorn src.main:app --reload --port 8000 >"$LOGDIR/backend.log" 2>&1 &
  echo $! >> "$PIDFILE"
  popd >/dev/null
}

start_frontend() {
  log "Starting frontend..."
  pushd "$ROOT/frontend" >/dev/null
  nohup npm run dev >"$LOGDIR/frontend.log" 2>&1 &
  echo $! >> "$PIDFILE"
  popd >/dev/null
}

start_all() {
  rm -f "$PIDFILE" || true
  start_backend
  start_frontend
  log "All servers started. Logs: $LOGDIR"
}

stop_all() {
  if [ ! -f "$PIDFILE" ]; then
    log "No pidfile found ($PIDFILE). Nothing to stop."
    return
  fi
  while read -r pid; do
    if [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1; then
      log "Stopping PID $pid"
      kill -TERM "$pid" || true
      sleep 1
      if kill -0 "$pid" >/dev/null 2>&1; then
        kill -KILL "$pid" || true
      fi
    else
      log "PID $pid not running"
    fi
  done < "$PIDFILE"
  rm -f "$PIDFILE"
  log "Stopped all servers."
}

status() {
  if [ ! -f "$PIDFILE" ]; then
    echo "No servers running (no $PIDFILE)"
    return
  fi
  while read -r pid; do
    if [ -n "$pid" ]; then
      if kill -0 "$pid" >/dev/null 2>&1; then
        echo "PID $pid: running"
      else
        echo "PID $pid: not running"
      fi
    fi
  done < "$PIDFILE"
}

case ${1-} in
  start)
    start_all
    ;;
  stop)
    stop_all
    ;;
  status)
    status
    ;;
  restart)
    stop_all
    start_all
    ;;
  *)
    echo "Usage: $0 {start|stop|status|restart}"
    exit 1
    ;;
esac

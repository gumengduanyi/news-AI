#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

read_env_var() {
  local key="$1"
  local file="$2"
  local line

  [[ -f "${file}" ]] || return 0
  line="$(grep -E "^${key}=" "${file}" | tail -n 1 || true)"
  [[ -n "${line}" ]] || return 0
  line="${line#*=}"

  if [[ "${line}" == \"*\" && "${line}" == *\" ]]; then
    line="${line:1:-1}"
  elif [[ "${line}" == \'*\' && "${line}" == *\' ]]; then
    line="${line:1:-1}"
  fi

  printf '%s' "${line}"
}

HOST="$(read_env_var "OPENCLAW_HOST" "${ENV_FILE}")"
USER="$(read_env_var "OPENCLAW_USER" "${ENV_FILE}")"
PASSWORD="$(read_env_var "OPENCLAW_PASSWORD" "${ENV_FILE}")"
LOCAL_PORT="$(read_env_var "OPENCLAW_LOCAL_GATEWAY_PORT" "${ENV_FILE}")"
REMOTE_PORT="$(read_env_var "OPENCLAW_REMOTE_GATEWAY_PORT" "${ENV_FILE}")"

HOST="${HOST:-43.160.192.130}"
USER="${USER:-root}"
LOCAL_PORT="${LOCAL_PORT:-10720}"
REMOTE_PORT="${REMOTE_PORT:-10720}"

if [[ -z "${PASSWORD}" ]]; then
  echo "Error: OPENCLAW_PASSWORD is empty in .env"
  exit 1
fi

if ! command -v sshpass >/dev/null 2>&1; then
  echo "Error: sshpass is not installed."
  echo "Install: brew install hudochenkov/sshpass/sshpass"
  exit 1
fi

# Prefer autossh for persistent tunnel if available
AUTOSSH_AVAILABLE=0
if command -v autossh >/dev/null 2>&1; then
  AUTOSSH_AVAILABLE=1
fi

if lsof -nP -iTCP:"${LOCAL_PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Error: local port ${LOCAL_PORT} is already in use."
  echo "Stop existing process or change OPENCLAW_LOCAL_GATEWAY_PORT in .env"
  exit 1
fi

cd "${SCRIPT_DIR}"

echo "Opening SSH tunnel: localhost:${LOCAL_PORT} -> ${HOST}:127.0.0.1:${REMOTE_PORT}"
if [[ "$AUTOSSH_AVAILABLE" -eq 1 ]]; then
  echo "autossh detected: using autossh for persistent tunnel"
  if [[ -n "${PASSWORD}" ]]; then
    # Use sshpass to supply password to autossh; recommend switching to key auth for security
    sshpass -p "${PASSWORD}" autossh -M 0 \
      -o ExitOnForwardFailure=yes \
      -o ServerAliveInterval=30 \
      -o ServerAliveCountMax=3 \
      -N -L "${LOCAL_PORT}:127.0.0.1:${REMOTE_PORT}" "${USER}@${HOST}" &
  else
    autossh -M 0 \
      -o ExitOnForwardFailure=yes \
      -o ServerAliveInterval=30 \
      -o ServerAliveCountMax=3 \
      -N -L "${LOCAL_PORT}:127.0.0.1:${REMOTE_PORT}" "${USER}@${HOST}" &
  fi
else
  # Fallback to original sshpass+ssh behavior
  sshpass -p "${PASSWORD}" ssh \
    -o ExitOnForwardFailure=yes \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -N -L "${LOCAL_PORT}:127.0.0.1:${REMOTE_PORT}" "${USER}@${HOST}" &
fi

TUNNEL_PID=$!

cleanup() {
  if kill -0 "${TUNNEL_PID}" >/dev/null 2>&1; then
    kill "${TUNNEL_PID}" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

sleep 1
if ! kill -0 "${TUNNEL_PID}" >/dev/null 2>&1; then
  echo "Error: tunnel failed to start."
  exit 1
fi

echo "Tunnel is up. Starting web bridge..."

# Start the web bridge in the background and keep this script running
# so the EXIT/INT/TERM trap can clean up the SSH tunnel when the web bridge exits.
npm start &
WEB_PID=$!

wait "$WEB_PID"
EXIT_STATUS=$?

# When the web bridge process exits, allow cleanup trap to run then exit
exit "$EXIT_STATUS"

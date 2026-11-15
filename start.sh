#!/usr/bin/env bash
#
# CareNest dev launcher
#
#   ./start.sh -b 8000 -f 8080
#
# Validates the backend environment, syncs Python deps with uv, boots the
# API on the -b port, then builds the web app with that backend port baked
# in and serves it on the -f port.
#
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
APP_DIR="$ROOT_DIR/App"

BACKEND_PORT=""
FRONTEND_PORT=""
API_PREFIX=""
API_PREFIX_SET=0
BACKEND_HOST="0.0.0.0"
BACKEND_PID=""

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------
if [ -t 1 ]; then
    C_RESET=$'\033[0m'; C_BOLD=$'\033[1m'
    C_RED=$'\033[31m'; C_GREEN=$'\033[32m'; C_YELLOW=$'\033[33m'; C_CYAN=$'\033[36m'
else
    C_RESET=""; C_BOLD=""; C_RED=""; C_GREEN=""; C_YELLOW=""; C_CYAN=""
fi

info()  { printf '%s==>%s %s\n' "$C_CYAN" "$C_RESET" "$*"; }
ok()    { printf '%s  ok%s %s\n' "$C_GREEN" "$C_RESET" "$*"; }
warn()  { printf '%swarn%s %s\n' "$C_YELLOW" "$C_RESET" "$*"; }
step()  { printf '\n%s%s%s\n' "$C_BOLD" "$*" "$C_RESET"; }
die()   { printf '%serror%s %s\n' "$C_RED" "$C_RESET" "$*" >&2; exit 1; }

usage() {
    cat <<EOF
${C_BOLD}Usage:${C_RESET} ./start.sh -b <backend-port> -f <frontend-port> [-p <api-prefix>]

  -b <port>     Port for the FastAPI backend  (default: 8000)
  -f <port>     Port for the web frontend    (default: 8081)
  -p <prefix>   Public path prefix the API is served under, e.g. /api
                (default: none — the web app calls host:port directly).
                You will be prompted when this is omitted.

  -h            Show this help

Examples:
  ./start.sh -b 8000 -f 8081
  ./start.sh -b 8000 -f 3000 -p /api     # behind nginx /api -> backend
EOF
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while getopts ":b:f:p:h" opt; do
    case "$opt" in
        b) BACKEND_PORT="$OPTARG" ;;
        f) FRONTEND_PORT="$OPTARG" ;;
        p) API_PREFIX="$OPTARG"; API_PREFIX_SET=1 ;;
        h) usage; exit 0 ;;
        :) die "option -$OPTARG requires a value" ;;
        \?) die "unknown option -$OPTARG (use -h for help)" ;;
    esac
done

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-8081}"

validate_port() {
    local name="$1" value="$2"
    [[ "$value" =~ ^[0-9]+$ ]] || die "$name must be a number, got '$value'"
    if [ "$value" -lt 1 ] || [ "$value" -gt 65535 ]; then
        die "$name must be between 1 and 65535, got '$value'"
    fi
}

validate_port "backend port (-b)" "$BACKEND_PORT"
validate_port "frontend port (-f)" "$FRONTEND_PORT"

[ "$BACKEND_PORT" != "$FRONTEND_PORT" ] \
    || die "backend and frontend ports must differ (both are $BACKEND_PORT)"

# ---------------------------------------------------------------------------
# API path prefix (for reverse proxies such as nginx `location /api/`)
# ---------------------------------------------------------------------------
normalise_prefix() {
    local p="$1"
    p="$(printf '%s' "$p" | tr -d '[:space:]')"
    case "$p" in
        ""|"/"|none|NONE|None) printf '' ; return ;;
    esac
    case "$p" in
        /*) ;;
        *) p="/$p" ;;
    esac
    printf '%s' "${p%/}"
}

# Ask when not supplied and we have a terminal; otherwise default to none.
if [ "$API_PREFIX_SET" -eq 0 ]; then
    if [ -t 0 ]; then
        printf '%s' "API path prefix for the web app (e.g. /api, blank for none): "
        read -r API_PREFIX_INPUT || API_PREFIX_INPUT=""
        API_PREFIX="$API_PREFIX_INPUT"
    else
        API_PREFIX=""
    fi
fi

API_PREFIX="$(normalise_prefix "$API_PREFIX")"
if [ -n "$API_PREFIX" ]; then
    ok "API will be served under the prefix: $API_PREFIX"
else
    ok "API path prefix: none (web app calls the backend port directly)"
fi

port_in_use() {
    local port="$1"
    if command -v ss >/dev/null 2>&1; then
        ss -ltn "sport = :$port" 2>/dev/null | tail -n +2 | grep -q .
    elif command -v lsof >/dev/null 2>&1; then
        lsof -iTCP:"$port" -sTCP:LISTEN -t >/dev/null 2>&1
    else
        return 1
    fi
}

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------
cleanup() {
    local code=$?
    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        info "stopping backend (pid $BACKEND_PID)"
        kill "$BACKEND_PID" 2>/dev/null || true
        wait "$BACKEND_PID" 2>/dev/null || true
    fi
    exit "$code"
}
trap cleanup EXIT INT TERM

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
step "Checking prerequisites"

command -v uv >/dev/null 2>&1 || die "uv is not installed. Install it: https://docs.astral.sh/uv/getting-started/installation/"
ok "uv $(uv --version 2>/dev/null | awk '{print $2}')"

command -v node >/dev/null 2>&1 || die "node is not installed (need Node 18+)"
ok "node $(node --version)"

command -v npm >/dev/null 2>&1 || die "npm is not installed"
ok "npm $(npm --version)"

[ -d "$BACKEND_DIR" ] || die "backend directory not found at $BACKEND_DIR"
[ -d "$APP_DIR" ] || die "App directory not found at $APP_DIR"

if port_in_use "$BACKEND_PORT"; then
    die "port $BACKEND_PORT is already in use — pick another with -b"
fi
if port_in_use "$FRONTEND_PORT"; then
    die "port $FRONTEND_PORT is already in use — pick another with -f"
fi
ok "ports $BACKEND_PORT (backend) and $FRONTEND_PORT (frontend) are free"

# ---------------------------------------------------------------------------
# Backend: validate .env
# ---------------------------------------------------------------------------
step "Validating backend environment"

ENV_FILE="$BACKEND_DIR/.env"
ENV_EXAMPLE="$BACKEND_DIR/.env.example"

if [ ! -f "$ENV_FILE" ]; then
    if [ -f "$ENV_EXAMPLE" ]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        warn "created backend/.env from .env.example — fill in your keys, then re-run"
    else
        die "backend/.env is missing and no .env.example to copy from"
    fi
    die "backend/.env needs a real GROQ_API_KEY"
fi
ok "backend/.env found"

# Read a value without exporting the whole file.
env_value() {
    local key="$1"
    grep -E "^[[:space:]]*${key}[[:space:]]*=" "$ENV_FILE" 2>/dev/null \
        | tail -n1 \
        | sed -E "s/^[[:space:]]*${key}[[:space:]]*=[[:space:]]*//" \
        | tr -d '\r' \
        | sed -E 's/^"(.*)"$/\1/' \
        | sed -E "s/^'(.*)'\$/\\1/" \
        | sed -E 's/[[:space:]]+$//'
}

GROQ_KEY="$(env_value GROQ_API_KEY)"
if [ -z "$GROQ_KEY" ]; then
    die "GROQ_API_KEY is not set in backend/.env"
fi
case "$GROQ_KEY" in
    your_groq_api_key_here|your_groq_api_key|changeme|"")
        die "GROQ_API_KEY in backend/.env is still the placeholder value"
        ;;
esac
ok "GROQ_API_KEY is set"

FIREBASE_CREDS="$(env_value FIREBASE_CREDENTIALS)"
if [ -z "$FIREBASE_CREDS" ]; then
    FIREBASE_CREDS="./care-45426-firebase-adminsdk-fbsvc-3c8cacde10.json"
    warn "FIREBASE_CREDENTIALS not set in backend/.env — defaulting to $FIREBASE_CREDS"
fi

# Relative paths in .env are resolved against backend/.
case "$FIREBASE_CREDS" in
    /*) FIREBASE_PATH="$FIREBASE_CREDS" ;;
    *)  FIREBASE_PATH="$BACKEND_DIR/${FIREBASE_CREDS#./}" ;;
esac

[ -f "$FIREBASE_PATH" ] || die "Firebase service account not found at $FIREBASE_PATH"
ok "Firebase service account found"

# ---------------------------------------------------------------------------
# Backend: uv sync
# ---------------------------------------------------------------------------
step "Syncing backend dependencies (uv)"

[ -f "$BACKEND_DIR/pyproject.toml" ] || die "backend/pyproject.toml is missing"
( cd "$BACKEND_DIR" && uv sync )
ok "Python environment is up to date"

# ---------------------------------------------------------------------------
# Backend: boot the API
# ---------------------------------------------------------------------------
step "Starting backend on port $BACKEND_PORT"

BACKEND_LOG="$ROOT_DIR/.backend.log"
(
    cd "$BACKEND_DIR"
    # API_PREFIX keeps docs/redirects correct when served behind a proxy path.
    export API_PREFIX
    exec uv run uvicorn main:app \
        --host "$BACKEND_HOST" \
        --port "$BACKEND_PORT" \
        --root-path "$API_PREFIX" \
        --log-level info
) >"$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

info "backend pid $BACKEND_PID, logging to .backend.log"

# Wait for it to answer.
BACKEND_READY=0
for _ in $(seq 1 60); do
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        printf '\n'
        tail -n 30 "$BACKEND_LOG" >&2 || true
        die "backend exited during startup (see .backend.log)"
    fi
    if command -v curl >/dev/null 2>&1; then
        if curl -fsS -m 2 "http://127.0.0.1:$BACKEND_PORT/" >/dev/null 2>&1; then
            BACKEND_READY=1
            break
        fi
    elif command -v wget >/dev/null 2>&1; then
        if wget -q -T 2 -O /dev/null "http://127.0.0.1:$BACKEND_PORT/" 2>/dev/null; then
            BACKEND_READY=1
            break
        fi
    else
        sleep 5
        BACKEND_READY=1
        break
    fi
    sleep 1
done

[ "$BACKEND_READY" -eq 1 ] || {
    tail -n 30 "$BACKEND_LOG" >&2 || true
    die "backend did not become ready on port $BACKEND_PORT (see .backend.log)"
}
ok "backend responding at http://localhost:$BACKEND_PORT"

# ---------------------------------------------------------------------------
# Frontend: install deps if needed
# ---------------------------------------------------------------------------
step "Preparing web frontend"

if [ ! -d "$APP_DIR/node_modules" ]; then
    info "installing npm dependencies (first run)"
    ( cd "$APP_DIR" && npm install --no-audit --no-fund )
fi
ok "node_modules present"

# ---------------------------------------------------------------------------
# Frontend: build with the backend port/prefix injected
# ---------------------------------------------------------------------------
if [ -n "$API_PREFIX" ]; then
    step "Building web bundle (API via $API_PREFIX)"
else
    step "Building web bundle (API port $BACKEND_PORT)"
fi

(
    cd "$APP_DIR"
    # --clear matters: these values are inlined into the bundle at build time
    # and Metro caches transforms, so without it a rebuild can keep a stale
    # port/prefix from a previous run.
    if [ -n "$API_PREFIX" ]; then
        EXPO_PUBLIC_API_PREFIX="$API_PREFIX" \
            npx expo export --platform web --output-dir dist --clear
    else
        EXPO_PUBLIC_API_PORT="$BACKEND_PORT" \
            npx expo export --platform web --output-dir dist --clear
    fi
)
[ -f "$APP_DIR/dist/index.html" ] || die "web build did not produce dist/index.html"
ok "web build complete"

# ---------------------------------------------------------------------------
# Frontend: serve
# ---------------------------------------------------------------------------
step "Serving frontend on port $FRONTEND_PORT"

if [ -n "$API_PREFIX" ]; then
    API_PUBLIC_URL="http://localhost:$FRONTEND_PORT$API_PREFIX"
    DOCS_PUBLIC_URL="http://localhost:$BACKEND_PORT/docs"
else
    API_PUBLIC_URL="http://localhost:$BACKEND_PORT"
    DOCS_PUBLIC_URL="http://localhost:$BACKEND_PORT/docs"
fi

printf '%s\n' \
    "" \
    "  ${C_BOLD}CareNest is running${C_RESET}" \
    "" \
    "  Frontend   http://localhost:$FRONTEND_PORT" \
    "  Backend    http://localhost:$BACKEND_PORT" \
    "  API path   ${API_PREFIX:-/ (no prefix)}" \
    "  API base   $API_PUBLIC_URL" \
    "  API docs   $DOCS_PUBLIC_URL" \
    "" \
    "  Press Ctrl-C to stop both servers." \
    ""

cd "$APP_DIR"
# Run in the foreground (not exec) so the EXIT trap still stops the backend.
# The helper server rewrites unknown paths to index.html so deep links such as
# /chat survive a refresh.
node scripts/serve-web.js dist "$FRONTEND_PORT"

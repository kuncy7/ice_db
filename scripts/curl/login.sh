#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${1:-http://127.0.0.1:8000}"
USER="${2:-admin}"
PASS="${3:-admin123}"

RESP="$(curl -s -X POST "$BASE_URL/api/auth/login" -H "Content-Type: application/json" -d "{"username":"$USER","password":"$PASS"}")"
ACCESS=$(echo "$RESP" | python - <<'PY'
import sys, json
print(json.load(sys.stdin)["data"]["access_token"])
PY
)
REFRESH=$(echo "$RESP" | python - <<'PY'
import sys, json
print(json.load(sys.stdin)["data"]["refresh_token"])
PY
)
echo "export ACCESS='$ACCESS'" > tokens.env
echo "export REFRESH='$REFRESH'" >> tokens.env
echo "Tokens zapisane do tokens.env. Użyj: source ./tokens.env"

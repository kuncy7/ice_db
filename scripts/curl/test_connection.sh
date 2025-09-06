#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${1:-http://127.0.0.1:8000}"
: "${RINK_ID:?Ustaw RINK_ID=...}"
curl -s -X POST "$BASE_URL/api/ice-rinks/$RINK_ID/test-connection"   -H "Authorization: Bearer $ACCESS" | jq .

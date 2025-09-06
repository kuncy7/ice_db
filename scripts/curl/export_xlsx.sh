#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${1:-http://127.0.0.1:8000}"
: "${RINK_ID:?Ustaw RINK_ID=...}"
curl -s -D - "$BASE_URL/api/ice-rinks/$RINK_ID/measurements/export?format=xlsx"   -H "Authorization: Bearer $ACCESS" -o measurements.xlsx
echo "Zapisano: measurements.xlsx"

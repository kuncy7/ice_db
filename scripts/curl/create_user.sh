#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${1:-http://127.0.0.1:8000}"
: "${ORG_ID:?Ustaw ORG_ID=...}"
curl -s -X POST "$BASE_URL/api/users"   -H "Authorization: Bearer $ACCESS" -H "Content-Type: application/json"   -d "{
    \"username\": \"operator1\",
    \"email\": \"operator1@example.com\",
    \"password\": \"Oper@123\",
    \"first_name\": \"Ola\",
    \"last_name\": \"Nowak\",
    \"role\": \"operator\",
    \"organization_id\": \"$ORG_ID\"
  }" | jq .

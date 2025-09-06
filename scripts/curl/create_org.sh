#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${1:-http://127.0.0.1:8000}"
curl -s -X POST "$BASE_URL/api/organizations"   -H "Authorization: Bearer $ACCESS" -H "Content-Type: application/json"   -d '{
    "name": "MOSiR Kraków",
    "type": "client",
    "address": "ul. Sportowa 1, Kraków",
    "contact_person": "Jan Kowalski",
    "contact_email": "biuro@mosir.example",
    "contact_phone": "+48 12 123 45 67",
    "tax_id": "PL678-123-45-67"
  }' | jq .

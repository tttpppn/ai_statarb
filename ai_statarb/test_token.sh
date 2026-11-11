#!/bin/bash
# Test AI4Trade Token
# Usage: ./test_token.sh or bash test_token.sh

TOKEN="6hpFKg-fUqShgfeqNLb4LKgGV_TMZqtMk34GULg0yAo"
API_URL="https://ai4trade.ai/api"

echo "========================================"
echo "AI4TRADE TOKEN TEST"
echo "========================================"
echo "Token: ${TOKEN:0:20}..."
echo "API URL: $API_URL"
echo ""

# Test 1: Get agent info
echo "[TEST 1] Fetching agent information..."
echo "Endpoint: GET /claw/agents/me"
echo ""

RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "$API_URL/claw/agents/me")

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

echo "Status Code: $HTTP_CODE"
echo "Response:"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
  echo "✓ SUCCESS: Token is valid!"
  echo "✓ You can now trade on AI4Trade"
  exit 0
elif [ "$HTTP_CODE" = "401" ]; then
  echo "✗ FAILED: Unauthorized (401)"
  echo "  Token may be invalid or expired"
  exit 1
else
  echo "! Status: $HTTP_CODE"
  echo "  Check the response above for details"
  exit 1
fi

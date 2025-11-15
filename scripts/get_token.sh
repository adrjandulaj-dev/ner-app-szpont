#!/bin/bash

# Script to get Keycloak access token for testing

KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
REALM="${REALM:-ner-app}"
CLIENT_ID="${CLIENT_ID:-ner-backend}"
CLIENT_SECRET="${CLIENT_SECRET:-}"
USERNAME="${USERNAME:-testuser}"
PASSWORD="${PASSWORD:-testpass123}"

if [ -z "$CLIENT_SECRET" ]; then
    echo "❌ Error: CLIENT_SECRET not set"
    echo "Usage: CLIENT_SECRET=your-secret $0"
    exit 1
fi

echo "🔑 Getting access token from Keycloak..."
echo "  URL: $KEYCLOAK_URL/realms/$REALM/protocol/openid-connect/token"
echo "  User: $USERNAME"
echo ""

RESPONSE=$(curl -s -X POST "$KEYCLOAK_URL/realms/$REALM/protocol/openid-connect/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$USERNAME" \
    -d "password=$PASSWORD" \
    -d "grant_type=password" \
    -d "client_id=$CLIENT_ID" \
    -d "client_secret=$CLIENT_SECRET")

ACCESS_TOKEN=$(echo "$RESPONSE" | jq -r '.access_token')

if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" = "null" ]; then
    echo "❌ Failed to get access token"
    echo "Response:"
    echo "$RESPONSE" | jq .
    exit 1
fi

echo "✅ Access token obtained!"
echo ""
echo "Token (first 50 chars): ${ACCESS_TOKEN:0:50}..."
echo ""
echo "Full token:"
echo "$ACCESS_TOKEN"
echo ""
echo "Export to use in other commands:"
echo "export TOKEN='$ACCESS_TOKEN'"

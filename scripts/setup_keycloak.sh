#!/bin/bash

# Keycloak Setup Script
# This script automates the basic setup of Keycloak for the NER application

set -e

KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
ADMIN_USER="${ADMIN_USER:-admin}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin}"
REALM_NAME="${REALM_NAME:-ner-app}"
CLIENT_ID="${CLIENT_ID:-ner-backend}"

echo "🔐 Setting up Keycloak for NER Application..."
echo "Keycloak URL: $KEYCLOAK_URL"
echo "Realm: $REALM_NAME"
echo "Client: $CLIENT_ID"
echo ""

# Wait for Keycloak to be ready
echo "⏳ Waiting for Keycloak to be ready..."
until curl -sf "$KEYCLOAK_URL/health/ready" > /dev/null; do
    echo "  Keycloak not ready yet, waiting..."
    sleep 5
done
echo "✅ Keycloak is ready!"
echo ""

# Get admin access token
echo "🔑 Getting admin access token..."
ADMIN_TOKEN=$(curl -s -X POST "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$ADMIN_USER" \
    -d "password=$ADMIN_PASSWORD" \
    -d "grant_type=password" \
    -d "client_id=admin-cli" | jq -r '.access_token')

if [ -z "$ADMIN_TOKEN" ] || [ "$ADMIN_TOKEN" = "null" ]; then
    echo "❌ Failed to get admin token. Check credentials."
    exit 1
fi
echo "✅ Got admin token"
echo ""

# Create realm
echo "🏗️  Creating realm '$REALM_NAME'..."
curl -s -X POST "$KEYCLOAK_URL/admin/realms" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"realm\": \"$REALM_NAME\",
        \"enabled\": true,
        \"displayName\": \"NER Application\",
        \"accessTokenLifespan\": 3600
    }" || echo "  (Realm may already exist)"
echo "✅ Realm created/exists"
echo ""

# Create client
echo "🔧 Creating client '$CLIENT_ID'..."
CLIENT_CREATE_RESPONSE=$(curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/clients" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"clientId\": \"$CLIENT_ID\",
        \"enabled\": true,
        \"protocol\": \"openid-connect\",
        \"publicClient\": false,
        \"directAccessGrantsEnabled\": true,
        \"serviceAccountsEnabled\": true,
        \"authorizationServicesEnabled\": false,
        \"redirectUris\": [\"*\"],
        \"webOrigins\": [\"*\"]
    }") || echo "  (Client may already exist)"
echo "✅ Client created/exists"
echo ""

# Get client secret
echo "🔐 Retrieving client secret..."
CLIENT_UUID=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM_NAME/clients" \
    -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r ".[] | select(.clientId==\"$CLIENT_ID\") | .id")

if [ -z "$CLIENT_UUID" ] || [ "$CLIENT_UUID" = "null" ]; then
    echo "❌ Failed to get client UUID"
    exit 1
fi

CLIENT_SECRET=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM_NAME/clients/$CLIENT_UUID/client-secret" \
    -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.value')

echo "✅ Client secret retrieved"
echo ""

# Create test user
echo "👤 Creating test user..."
curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/users" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "testuser",
        "enabled": true,
        "emailVerified": true,
        "email": "testuser@example.com",
        "firstName": "Test",
        "lastName": "User",
        "credentials": [{
            "type": "password",
            "value": "testpass123",
            "temporary": false
        }]
    }' || echo "  (User may already exist)"
echo "✅ Test user created/exists"
echo ""

# Print summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Keycloak setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Configuration Summary:"
echo "  Keycloak URL:    $KEYCLOAK_URL"
echo "  Realm:           $REALM_NAME"
echo "  Client ID:       $CLIENT_ID"
echo "  Client Secret:   $CLIENT_SECRET"
echo ""
echo "👤 Test User Credentials:"
echo "  Username:        testuser"
echo "  Password:        testpass123"
echo ""
echo "⚙️  Add this to your .env file:"
echo "  KEYCLOAK_CLIENT_SECRET=$CLIENT_SECRET"
echo ""
echo "🧪 Test token endpoint:"
echo "  curl -X POST '$KEYCLOAK_URL/realms/$REALM_NAME/protocol/openid-connect/token' \\"
echo "    -H 'Content-Type: application/x-www-form-urlencoded' \\"
echo "    -d 'username=testuser' \\"
echo "    -d 'password=testpass123' \\"
echo "    -d 'grant_type=password' \\"
echo "    -d 'client_id=$CLIENT_ID' \\"
echo "    -d 'client_secret=$CLIENT_SECRET'"
echo ""

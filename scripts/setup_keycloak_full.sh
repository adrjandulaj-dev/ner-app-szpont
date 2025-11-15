#!/bin/bash

# Complete Keycloak Setup Script including Frontend Client
# This script sets up both backend and frontend clients

set -e

KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
ADMIN_USER="${ADMIN_USER:-admin}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin}"
REALM_NAME="${REALM_NAME:-ner-app}"
BACKEND_CLIENT_ID="${BACKEND_CLIENT_ID:-ner-backend}"
FRONTEND_CLIENT_ID="${FRONTEND_CLIENT_ID:-ner-frontend}"

echo "🔐 Setting up Keycloak for NER Application (Backend + Frontend)..."
echo "Keycloak URL: $KEYCLOAK_URL"
echo "Realm: $REALM_NAME"
echo "Backend Client: $BACKEND_CLIENT_ID"
echo "Frontend Client: $FRONTEND_CLIENT_ID"
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
        \"accessTokenLifespan\": 3600,
        \"ssoSessionIdleTimeout\": 7200,
        \"ssoSessionMaxLifespan\": 36000
    }" || echo "  (Realm may already exist)"
echo "✅ Realm created/exists"
echo ""

# Create backend client (confidential)
echo "🔧 Creating backend client '$BACKEND_CLIENT_ID'..."
curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/clients" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"clientId\": \"$BACKEND_CLIENT_ID\",
        \"enabled\": true,
        \"protocol\": \"openid-connect\",
        \"publicClient\": false,
        \"directAccessGrantsEnabled\": true,
        \"serviceAccountsEnabled\": true,
        \"authorizationServicesEnabled\": false,
        \"redirectUris\": [\"*\"],
        \"webOrigins\": [\"*\"]
    }" || echo "  (Client may already exist)"
echo "✅ Backend client created/exists"
echo ""

# Create frontend client (public)
echo "🎨 Creating frontend client '$FRONTEND_CLIENT_ID'..."
curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/clients" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"clientId\": \"$FRONTEND_CLIENT_ID\",
        \"enabled\": true,
        \"protocol\": \"openid-connect\",
        \"publicClient\": true,
        \"directAccessGrantsEnabled\": true,
        \"standardFlowEnabled\": true,
        \"implicitFlowEnabled\": false,
        \"redirectUris\": [
            \"http://localhost:3000/*\",
            \"http://localhost/*\",
            \"http://127.0.0.1:3000/*\"
        ],
        \"webOrigins\": [
            \"http://localhost:3000\",
            \"http://localhost\",
            \"http://127.0.0.1:3000\"
        ],
        \"attributes\": {
            \"pkce.code.challenge.method\": \"S256\"
        }
    }" || echo "  (Client may already exist)"
echo "✅ Frontend client created/exists"
echo ""

# Get backend client secret
echo "🔐 Retrieving backend client secret..."
BACKEND_CLIENT_UUID=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM_NAME/clients" \
    -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r ".[] | select(.clientId==\"$BACKEND_CLIENT_ID\") | .id")

if [ -z "$BACKEND_CLIENT_UUID" ] || [ "$BACKEND_CLIENT_UUID" = "null" ]; then
    echo "❌ Failed to get backend client UUID"
    exit 1
fi

BACKEND_CLIENT_SECRET=$(curl -s -X GET "$KEYCLOAK_URL/admin/realms/$REALM_NAME/clients/$BACKEND_CLIENT_UUID/client-secret" \
    -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.value')

echo "✅ Backend client secret retrieved"
echo ""

# Configure CORS
echo "🌐 Configuring CORS settings..."
curl -s -X PUT "$KEYCLOAK_URL/admin/realms/$REALM_NAME" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"realm\": \"$REALM_NAME\",
        \"browserSecurityHeaders\": {
            \"contentSecurityPolicy\": \"frame-src 'self'; frame-ancestors 'self'; object-src 'none';\",
            \"xContentTypeOptions\": \"nosniff\",
            \"xRobotsTag\": \"none\",
            \"xFrameOptions\": \"SAMEORIGIN\",
            \"xXSSProtection\": \"1; mode=block\",
            \"strictTransportSecurity\": \"max-age=31536000; includeSubDomains\"
        }
    }" || echo "  (CORS may already be configured)"
echo "✅ CORS configured"
echo ""

# Create test users
echo "👤 Creating test users..."

# Admin user
curl -s -X POST "$KEYCLOAK_URL/admin/realms/$REALM_NAME/users" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "admin",
        "enabled": true,
        "emailVerified": true,
        "email": "admin@example.com",
        "firstName": "Admin",
        "lastName": "User",
        "credentials": [{
            "type": "password",
            "value": "admin123",
            "temporary": false
        }]
    }' || echo "  (Admin user may already exist)"

# Test user
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
    }' || echo "  (Test user may already exist)"

echo "✅ Test users created/exist"
echo ""

# Print summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Keycloak setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Configuration Summary:"
echo "  Keycloak URL:           $KEYCLOAK_URL"
echo "  Realm:                  $REALM_NAME"
echo "  Backend Client ID:      $BACKEND_CLIENT_ID"
echo "  Backend Client Secret:  $BACKEND_CLIENT_SECRET"
echo "  Frontend Client ID:     $FRONTEND_CLIENT_ID (public)"
echo ""
echo "👤 Test User Credentials:"
echo "  Admin:    admin / admin123"
echo "  User:     testuser / testpass123"
echo ""
echo "⚙️  Add this to your .env file:"
echo "  KEYCLOAK_CLIENT_SECRET=$BACKEND_CLIENT_SECRET"
echo ""
echo "🌐 Access Points:"
echo "  Frontend:        http://localhost:3000"
echo "  Backend API:     http://localhost:8000/docs"
echo "  Keycloak Admin:  http://localhost:8080"
echo ""
echo "🧪 Test authentication:"
echo "  1. Open http://localhost:3000"
echo "  2. Click 'Sign In with Keycloak'"
echo "  3. Login with testuser / testpass123"
echo ""

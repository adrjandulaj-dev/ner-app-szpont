#!/bin/bash

# Script to test the NER API end-to-end

set -e

API_URL="${API_URL:-http://localhost:8000}"
KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
REALM="${REALM:-ner-app}"
CLIENT_ID="${CLIENT_ID:-ner-backend}"
CLIENT_SECRET="${CLIENT_SECRET:-}"
TEST_FILE="${TEST_FILE:-test.txt}"

if [ -z "$CLIENT_SECRET" ]; then
    echo "❌ Error: CLIENT_SECRET not set"
    echo "Usage: CLIENT_SECRET=your-secret $0"
    exit 1
fi

echo "🧪 Testing NER API..."
echo ""

# Step 1: Get access token
echo "1️⃣  Getting access token..."
TOKEN=$(curl -s -X POST "$KEYCLOAK_URL/realms/$REALM/protocol/openid-connect/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=testuser" \
    -d "password=testpass123" \
    -d "grant_type=password" \
    -d "client_id=$CLIENT_ID" \
    -d "client_secret=$CLIENT_SECRET" | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "❌ Failed to get token"
    exit 1
fi
echo "✅ Token obtained"
echo ""

# Step 2: Create test file if it doesn't exist
if [ ! -f "$TEST_FILE" ]; then
    echo "2️⃣  Creating test file..."
    echo "The FBI has opened an investigation. John Doe works at Microsoft in New York. The conference will be held on July 20, 2025." > "$TEST_FILE"
    echo "✅ Test file created: $TEST_FILE"
else
    echo "2️⃣  Using existing test file: $TEST_FILE"
fi
echo ""

# Step 3: Upload document
echo "3️⃣  Uploading document..."
UPLOAD_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/documents/upload" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@$TEST_FILE")

DOCUMENT_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.document_id')

if [ -z "$DOCUMENT_ID" ] || [ "$DOCUMENT_ID" = "null" ]; then
    echo "❌ Failed to upload document"
    echo "Response: $UPLOAD_RESPONSE"
    exit 1
fi
echo "✅ Document uploaded: $DOCUMENT_ID"
echo ""

# Step 4: Create analysis
echo "4️⃣  Creating analysis..."
ANALYSIS_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/analysis" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"document_id\": \"$DOCUMENT_ID\", \"use_sentence_tokenizer\": true}")

ANALYSIS_ID=$(echo "$ANALYSIS_RESPONSE" | jq -r '.analysis_id')

if [ -z "$ANALYSIS_ID" ] || [ "$ANALYSIS_ID" = "null" ]; then
    echo "❌ Failed to create analysis"
    echo "Response: $ANALYSIS_RESPONSE"
    exit 1
fi
echo "✅ Analysis created: $ANALYSIS_ID"
echo ""

# Step 5: Wait for analysis to complete
echo "5️⃣  Waiting for analysis to complete..."
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    sleep 2
    ATTEMPT=$((ATTEMPT + 1))

    STATUS_RESPONSE=$(curl -s -X GET "$API_URL/api/v1/analysis/$ANALYSIS_ID/status" \
        -H "Authorization: Bearer $TOKEN")

    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')

    echo "  Attempt $ATTEMPT/$MAX_ATTEMPTS - Status: $STATUS"

    if [ "$STATUS" = "completed" ]; then
        echo "✅ Analysis completed!"
        break
    elif [ "$STATUS" = "failed" ]; then
        echo "❌ Analysis failed"
        echo "Response: $STATUS_RESPONSE"
        exit 1
    fi

    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        echo "❌ Timeout waiting for analysis"
        exit 1
    fi
done
echo ""

# Step 6: Get results
echo "6️⃣  Getting analysis results..."
RESULTS=$(curl -s -X GET "$API_URL/api/v1/analysis/$ANALYSIS_ID" \
    -H "Authorization: Bearer $TOKEN")

echo "✅ Results retrieved!"
echo ""

# Display results
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Analysis Results"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Total sentences: $(echo "$RESULTS" | jq -r '.total_sentences')"
echo "Total tokens: $(echo "$RESULTS" | jq -r '.total_tokens')"
echo "Processing time: $(echo "$RESULTS" | jq -r '.processing_time_seconds')s"
echo ""
echo "Named Entities Found:"
echo "$RESULTS" | jq -r '.all_entities[] | "  \(.human_readable_tag) (\(.count)): \(.entities | join(", "))"'
echo ""
echo "Full results saved to: analysis_results.json"
echo "$RESULTS" | jq . > analysis_results.json

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Test completed successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

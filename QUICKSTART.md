# Quick Start Guide

Get the NER Document Analysis Service running in 5 minutes!

## Prerequisites

- Docker and Docker Compose installed
- OpenAI or Anthropic API key

## Steps

### 1. Clone and Configure

```bash
git clone <repo-url>
cd ner-app-szpont

# Copy environment file
cp .env.example .env

# Edit .env and add your API key
nano .env
```

Add your LLM API key:
```bash
OPENAI_API_KEY=sk-your-key-here
# OR
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 2. Start Services

```bash
docker-compose up -d
```

Wait about 30 seconds for all services to start.

### 3. Setup Keycloak

```bash
# Make sure jq is installed (for JSON parsing)
# Ubuntu/Debian: sudo apt-get install jq
# macOS: brew install jq

# Run setup script
./scripts/setup_keycloak.sh
```

This will:
- Create the `ner-app` realm
- Create the `ner-backend` client
- Create a test user (username: `testuser`, password: `testpass123`)
- Display your client secret

**Important**: Copy the `KEYCLOAK_CLIENT_SECRET` from the output and add it to your `.env` file:

```bash
echo "KEYCLOAK_CLIENT_SECRET=your-secret-here" >> .env
```

Then restart the backend:
```bash
docker-compose restart backend
```

### 4. Test the API

```bash
# Set your client secret
export CLIENT_SECRET="your-secret-from-step-3"

# Run the test script
./scripts/test_api.sh
```

This will:
1. Get an authentication token
2. Upload a test document
3. Create an analysis task
4. Wait for completion
5. Display the results

### 5. Explore the API

Open the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Management Consoles

- **RabbitMQ**: http://localhost:15672 (guest/guest)
- **MinIO**: http://localhost:9001 (minioadmin/minioadmin)
- **Keycloak**: http://localhost:8080 (admin/admin)

## Manual API Testing

### Get a Token

```bash
export CLIENT_SECRET="your-client-secret"

curl -X POST "http://localhost:8080/realms/ner-app/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser" \
  -d "password=testpass123" \
  -d "grant_type=password" \
  -d "client_id=ner-backend" \
  -d "client_secret=$CLIENT_SECRET" | jq -r '.access_token'
```

Save the token:
```bash
export TOKEN="your-access-token"
```

### Upload a Document

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.pdf" | jq .
```

Save the `document_id` from the response.

### Create Analysis

```bash
curl -X POST "http://localhost:8000/api/v1/analysis" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "your-document-id",
    "use_sentence_tokenizer": true
  }' | jq .
```

Save the `analysis_id` from the response.

### Check Status

```bash
curl -X GET "http://localhost:8000/api/v1/analysis/your-analysis-id/status" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### Get Results

```bash
curl -X GET "http://localhost:8000/api/v1/analysis/your-analysis-id" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

## Supported Document Types

- **PDF**: Text extraction via LLM vision
- **Images**: PNG, JPG, JPEG (OCR via LLM)
- **Text**: TXT files (direct processing)

## Troubleshooting

### Services not starting

```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs backend
docker-compose logs keycloak
```

### Can't get token

1. Make sure Keycloak is running: `docker-compose ps keycloak`
2. Verify realm exists: http://localhost:8080
3. Check client secret is correct in `.env`

### Analysis stuck in "queued"

```bash
# Check RabbitMQ
docker-compose logs rabbitmq

# Check backend worker
docker-compose logs backend

# Check RabbitMQ management console
# http://localhost:15672
```

### Out of memory

Increase Docker memory limit to at least 8GB.

## Next Steps

- Read the full [README](README_NEW.md)
- Explore the [API documentation](http://localhost:8000/docs)
- Check the [CHANGELOG](CHANGELOG.md)
- Configure for production deployment

## Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```

## Support

For issues and questions, please check:
- API Documentation: http://localhost:8000/docs
- Logs: `docker-compose logs [service-name]`
- GitHub Issues: [repo-url]/issues

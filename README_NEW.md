# NER Document Analysis Service v2.0

Nowoczesny system analizy dokumentów z rozpoznawaniem nazwanych encji (NER), przepisany z wykorzystaniem FastAPI i mikrousług.

## 🚀 Nowe funkcje w wersji 2.0

- **FastAPI Backend** - Nowoczesny, asynchroniczny framework API
- **Keycloak Authentication** - Profesjonalne zarządzanie tożsamością i dostępem
- **MinIO Storage** - Skalowalny obiektowy system przechowywania dokumentów
- **MongoDB** - Przechowywanie wyników analiz i metadanych
- **RabbitMQ** - Asynchroniczne przetwarzanie zadań
- **LLM Integration** - Automatyczna ekstrakcja tekstu z PDF i obrazów przy użyciu modeli językowych
- **Docker Compose** - Łatwe wdrażanie wszystkich serwisów

## 📋 Architektura

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│         FastAPI Backend             │
│  ┌──────────┐  ┌────────────────┐  │
│  │ Auth     │  │ API Endpoints  │  │
│  │(Keycloak)│  │  - Documents   │  │
│  └──────────┘  │  - Analysis    │  │
│                └────────────────┘  │
└────┬────────────────┬──────────────┘
     │                │
     ▼                ▼
┌─────────┐    ┌──────────────┐
│  MinIO  │    │   MongoDB    │
│(Storage)│    │  (Results)   │
└─────────┘    └──────────────┘
     │
     ▼
┌──────────────────────────────┐
│        RabbitMQ Queue        │
└──────────────┬───────────────┘
               │
               ▼
      ┌────────────────┐
      │  Task Worker   │
      │  - LLM Extract │
      │  - NER Analyze │
      └────────────────┘
```

## 🔧 Wymagania

- Docker & Docker Compose
- Klucz API OpenAI lub Anthropic (dla ekstrakcji tekstu z PDF/obrazów)
- 8GB RAM (zalecane)
- 10GB wolnego miejsca na dysku

## 🚀 Szybki start

### 1. Sklonuj repozytorium

```bash
git clone <repo-url>
cd ner-app-szpont
```

### 2. Skonfiguruj zmienne środowiskowe

```bash
cp .env.example .env
```

Edytuj plik `.env` i ustaw wymagane zmienne:

```bash
# Konfiguracja LLM (wybierz jeden)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-api-key

# lub

LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key
```

### 3. Uruchom usługi

```bash
docker-compose up -d
```

To uruchomi:
- **Keycloak** na `http://localhost:8080` (admin/admin)
- **MinIO Console** na `http://localhost:9001` (minioadmin/minioadmin)
- **RabbitMQ Management** na `http://localhost:15672` (guest/guest)
- **FastAPI Backend** na `http://localhost:8000`
- **MongoDB** na `localhost:27017`

### 4. Skonfiguruj Keycloak

Po uruchomieniu serwisów, skonfiguruj Keycloak:

1. Zaloguj się do Keycloak: `http://localhost:8080`
2. Utwórz nowy realm o nazwie `ner-app`
3. Utwórz klienta `ner-backend`:
   - Client Protocol: openid-connect
   - Access Type: confidential
   - Valid Redirect URIs: `*`
4. Skopiuj Client Secret i zaktualizuj zmienną `KEYCLOAK_CLIENT_SECRET` w `.env`
5. Utwórz testowego użytkownika w Keycloak

Możesz też użyć skryptu automatyzującego (dostępny w `scripts/setup_keycloak.sh`)

### 5. Testuj API

Dokumentacja API jest dostępna pod adresem: `http://localhost:8000/docs`

#### Przykład: Upload dokumentu

```bash
# 1. Uzyskaj token z Keycloak
TOKEN=$(curl -X POST "http://localhost:8080/realms/ner-app/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser" \
  -d "password=testpass" \
  -d "grant_type=password" \
  -d "client_id=ner-backend" \
  -d "client_secret=YOUR_CLIENT_SECRET" | jq -r '.access_token')

# 2. Upload pliku
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf"

# 3. Uruchom analizę
curl -X POST "http://localhost:8000/api/v1/analysis" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "YOUR_DOCUMENT_ID", "use_sentence_tokenizer": true}'

# 4. Sprawdź status
curl -X GET "http://localhost:8000/api/v1/analysis/YOUR_ANALYSIS_ID/status" \
  -H "Authorization: Bearer $TOKEN"

# 5. Pobierz wyniki
curl -X GET "http://localhost:8000/api/v1/analysis/YOUR_ANALYSIS_ID" \
  -H "Authorization: Bearer $TOKEN"
```

## 📚 API Endpoints

### Authentication
Wszystkie endpointy wymagają tokenu Bearer z Keycloak.

### Documents

- `POST /api/v1/documents/upload` - Upload dokumentu (PDF, obraz, tekst)
- `GET /api/v1/documents/{document_id}` - Pobranie metadanych dokumentu
- `GET /api/v1/documents` - Lista dokumentów użytkownika
- `DELETE /api/v1/documents/{document_id}` - Usunięcie dokumentu

### Analysis

- `POST /api/v1/analysis` - Utworzenie nowej analizy (asynchroniczne)
- `GET /api/v1/analysis/{analysis_id}` - Pobranie wyników analizy
- `GET /api/v1/analysis/{analysis_id}/status` - Status analizy
- `GET /api/v1/analysis/document/{document_id}` - Wszystkie analizy dokumentu
- `GET /api/v1/analysis` - Lista analiz użytkownika

### Health

- `GET /api/v1/health` - Health check
- `GET /api/v1/health/ready` - Readiness check

## 🔄 Proces przetwarzania

1. **Upload dokumentu**
   - Użytkownik uploaduje dokument przez API
   - Plik jest zapisywany w MinIO
   - Metadata zapisywane w MongoDB

2. **Żądanie analizy**
   - Użytkownik tworzy zadanie analizy
   - Zadanie jest dodawane do kolejki RabbitMQ
   - API zwraca analysis_id

3. **Przetwarzanie asynchroniczne**
   - Worker pobiera zadanie z kolejki
   - Dla PDF/obrazów: LLM ekstraktuje tekst
   - Model NER analizuje tekst
   - Wyniki zapisywane w MongoDB

4. **Pobranie wyników**
   - Użytkownik sprawdza status analizy
   - Po zakończeniu pobiera wyniki

## 🧪 Wspierane formaty dokumentów

- **PDF** - Ekstrakcja tekstu przez LLM (GPT-4 Vision lub Claude Vision)
- **Obrazy** - PNG, JPG, JPEG (OCR przez LLM)
- **Tekst** - TXT, zwykły tekst

## 🔐 Bezpieczeństwo

- Autentykacja przez Keycloak (OAuth 2.0 / OpenID Connect)
- Izolacja danych użytkowników
- HTTPS ready (skonfiguruj reverse proxy)
- Tokeny JWT z weryfikacją podpisu

## 📊 Monitorowanie

- **RabbitMQ Management**: http://localhost:15672
- **MinIO Console**: http://localhost:9001
- **FastAPI Docs**: http://localhost:8000/docs
- **Keycloak Admin**: http://localhost:8080

## 🛠 Rozwój lokalny

### Bez Dockera

```bash
# Zainstaluj zależności
pip install -r requirements.txt

# Ustaw zmienne środowiskowe
export MONGODB_URL=mongodb://localhost:27017
export RABBITMQ_HOST=localhost
# ... inne zmienne

# Uruchom backend
python -m backend.app.main
```

### Testowanie

```bash
# Uruchom testy
pytest tests/

# Coverage
pytest --cov=backend tests/
```

## 📦 Struktura projektu

```
ner-app-szpont/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI app
│       ├── config.py            # Konfiguracja
│       ├── auth/                # Keycloak auth
│       ├── storage/             # MinIO, MongoDB
│       ├── queue/               # RabbitMQ
│       ├── services/            # LLM, NER, Document
│       ├── api/
│       │   └── v1/              # API endpoints
│       └── models/              # Pydantic models
├── models/                      # Modele NER
├── predictor.py                 # NER predictor
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## 🐛 Troubleshooting

### Keycloak nie startuje
```bash
# Sprawdź logi
docker-compose logs keycloak

# Restart
docker-compose restart keycloak
```

### Problemy z MinIO
```bash
# Sprawdź czy bucket został utworzony
docker-compose exec minio mc ls local/
```

### RabbitMQ nie przetwarza zadań
```bash
# Sprawdź kolejkę
docker-compose logs rabbitmq

# Sprawdź workera
docker-compose logs backend
```

## 📝 TODO / Roadmap

- [ ] Testy jednostkowe i integracyjne
- [ ] CI/CD pipeline
- [ ] Kubernetes deployment manifesty
- [ ] Monitoring (Prometheus/Grafana)
- [ ] Rate limiting
- [ ] Webhooks dla powiadomień o zakończeniu analizy
- [ ] Frontend (React/Vue)
- [ ] Batch processing dla wielu dokumentów

## 📄 Licencja

MIT

## 👥 Autorzy

- Wersja 1.0: [Original Author]
- Wersja 2.0: Przepisane na FastAPI z mikrousługami

# Jak uruchomić NER Document Analysis Service

Kompletny przewodnik uruchomienia całego stosu (Frontend + Backend + Wszystkie serwisy).

## 🚀 Szybkie uruchomienie (5 minut)

### 1. Wymagania wstępne

Upewnij się, że masz:
- ✅ Docker Desktop zainstalowany i uruchomiony
- ✅ Docker Compose (zwykle wbudowany w Docker Desktop)
- ✅ Klucz API OpenAI lub Anthropic
- ✅ 8GB RAM dostępne dla Dockera
- ✅ jq zainstalowane (dla skryptów)
  - macOS: `brew install jq`
  - Ubuntu/Debian: `sudo apt-get install jq`
  - Windows: pobierz z https://stedolan.github.io/jq/

### 2. Konfiguracja

```bash
# Sklonuj repozytorium (jeśli jeszcze nie masz)
git clone <repo-url>
cd ner-app-szpont

# Skopiuj plik środowiskowy
cp .env.example .env

# Edytuj .env i dodaj swój klucz API
nano .env  # lub vim, code, notepad++
```

W pliku `.env` dodaj:
```bash
# Dla OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-actual-openai-key-here

# LUB dla Anthropic
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here
```

### 3. Uruchom wszystkie serwisy

```bash
# Uruchom Docker Compose w tle
docker-compose up -d

# Sprawdź status
docker-compose ps
```

Poczekaj około 30-60 sekund aż wszystkie serwisy się uruchomią.

### 4. Skonfiguruj Keycloak

```bash
# Uruchom skrypt automatycznej konfiguracji
./scripts/setup_keycloak_full.sh
```

Skrypt utworzy:
- ✅ Realm `ner-app`
- ✅ Backend client `ner-backend` (confidential)
- ✅ Frontend client `ner-frontend` (public)
- ✅ Użytkowników testowych:
  - `admin` / `admin123`
  - `testuser` / `testpass123`

**WAŻNE:** Skopiuj `KEYCLOAK_CLIENT_SECRET` z wyniku skryptu!

```bash
# Dodaj client secret do .env
echo "KEYCLOAK_CLIENT_SECRET=paste-secret-here" >> .env

# Zrestartuj backend aby zastosować zmiany
docker-compose restart backend
```

### 5. Gotowe! Użyj aplikacji

Otwórz przeglądarkę i przejdź do:

#### **🖥️ Frontend (Zalecane)**
**http://localhost:3000**

1. Kliknij "Sign In with Keycloak"
2. Zaloguj się: `testuser` / `testpass123`
3. Upload dokument (PDF, obraz, lub txt)
4. Kliknij "Analyze"
5. Zobacz wyniki!

#### **📡 API (dla deweloperów)**
**http://localhost:8000/docs**

Interaktywna dokumentacja API (Swagger UI)

---

## 📊 Konsole zarządzania

Wszystkie dostępne interfejsy:

| Serwis | URL | Login | Opis |
|--------|-----|-------|------|
| **Frontend** | http://localhost:3000 | testuser/testpass123 | Główny interfejs użytkownika |
| **API Docs** | http://localhost:8000/docs | - | Dokumentacja Swagger |
| **Keycloak** | http://localhost:8080 | admin/admin | Zarządzanie użytkownikami |
| **MinIO Console** | http://localhost:9001 | minioadmin/minioadmin | Przeglądanie plików |
| **RabbitMQ** | http://localhost:15672 | guest/guest | Kolejka zadań |
| **MongoDB** | localhost:27017 | - | Baza danych (Compass/Studio) |

---

## 🧪 Testowanie

### Test frontendu

1. Otwórz http://localhost:3000
2. Zaloguj się
3. Upload testowy plik
4. Uruchom analizę
5. Sprawdź wyniki

### Test API

```bash
# Użyj skryptu testowego
export CLIENT_SECRET="your-client-secret-from-step-4"
./scripts/test_api.sh
```

### Ręczny test API

```bash
# 1. Pobierz token
export CLIENT_SECRET="your-secret"

TOKEN=$(curl -s -X POST "http://localhost:8080/realms/ner-app/protocol/openid-connect/token" \
  -d "username=testuser" \
  -d "password=testpass123" \
  -d "grant_type=password" \
  -d "client_id=ner-backend" \
  -d "client_secret=$CLIENT_SECRET" | jq -r '.access_token')

echo "Token: $TOKEN"

# 2. Upload pliku
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.txt"

# 3. Lista dokumentów
curl -X GET "http://localhost:8000/api/v1/documents" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔧 Zarządzanie serwisami

### Sprawdzenie statusu

```bash
# Status wszystkich kontenerów
docker-compose ps

# Logi wszystkich serwisów
docker-compose logs

# Logi konkretnego serwisu
docker-compose logs frontend
docker-compose logs backend
docker-compose logs keycloak
```

### Restart serwisów

```bash
# Restart wszystkich
docker-compose restart

# Restart konkretnego
docker-compose restart backend
docker-compose restart frontend
```

### Zatrzymanie i usunięcie

```bash
# Zatrzymaj wszystkie serwisy
docker-compose down

# Zatrzymaj i usuń wszystkie dane (UWAGA: usuwa bazę!)
docker-compose down -v
```

### Rebuild po zmianach w kodzie

```bash
# Rebuild backendu
docker-compose build backend
docker-compose up -d backend

# Rebuild frontendu
docker-compose build frontend
docker-compose up -d frontend

# Rebuild wszystkiego
docker-compose build
docker-compose up -d
```

---

## 🐛 Troubleshooting

### Problem: Kontener nie startuje

```bash
# Sprawdź logi
docker-compose logs <service-name>

# Przykłady
docker-compose logs backend
docker-compose logs keycloak
```

### Problem: Keycloak nie jest dostępny

```bash
# Sprawdź czy działa
docker-compose ps keycloak

# Jeśli nie, zrestartuj
docker-compose restart keycloak

# Poczekaj 30 sekund i spróbuj ponownie
curl http://localhost:8080/health/ready
```

### Problem: Frontend nie łączy się z backendem

1. Sprawdź czy backend działa:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

2. Sprawdź logi frontendu:
   ```bash
   docker-compose logs frontend
   ```

3. Sprawdź konfigurację CORS w backend

### Problem: "401 Unauthorized" w frontend

1. Sprawdź czy Keycloak działa
2. Upewnij się, że frontend client jest poprawnie skonfigurowany
3. Wyloguj się i zaloguj ponownie
4. Sprawdź czy redirect URIs zawierają http://localhost:3000/*

### Problem: Analiza nie działa

1. Sprawdź RabbitMQ:
   ```bash
   docker-compose logs rabbitmq
   docker-compose logs backend
   ```

2. Sprawdź czy klucz LLM jest poprawny:
   ```bash
   # Sprawdź logi backendu
   docker-compose logs backend | grep -i "llm\|openai\|anthropic"
   ```

3. Sprawdź MinIO:
   ```bash
   docker-compose logs minio
   ```

### Problem: Brak pamięci

```bash
# Sprawdź użycie pamięci
docker stats

# Zwiększ limit pamięci w Docker Desktop:
# Settings → Resources → Memory → 8GB+
```

### Problem: Port już zajęty

```bash
# Zmień porty w docker-compose.yml
# Przykład: zmień "3000:80" na "3001:80"

# Albo zatrzymaj konfliktujący proces
lsof -i :3000  # macOS/Linux
netstat -ano | findstr :3000  # Windows
```

---

## 📦 Development lokalny (bez Dockera)

### Backend

```bash
# Zainstaluj dependencje
pip install -r requirements.txt

# Ustaw zmienne środowiskowe
export MONGODB_URL=mongodb://localhost:27017
export RABBITMQ_HOST=localhost
export MINIO_ENDPOINT=localhost:9000
export KEYCLOAK_URL=http://localhost:8080
# ... (pozostałe z .env)

# Uruchom
python -m backend.app.main
```

### Frontend

```bash
cd frontend

# Zainstaluj dependencje
npm install

# Skopiuj .env
cp .env.example .env

# Uruchom dev server
npm start

# Build produkcyjny
npm run build
```

---

## 🔄 Aktualizacja

```bash
# Pobierz najnowszy kod
git pull

# Rebuild i restart
docker-compose build
docker-compose up -d

# Sprawdź czy wszystko działa
docker-compose ps
```

---

## 🎯 Następne kroki

1. ✅ Zapoznaj się z interfejsem frontendu
2. ✅ Przetestuj różne typy dokumentów (PDF, obrazy, tekst)
3. ✅ Sprawdź dokumentację API: http://localhost:8000/docs
4. ✅ Przejrzyj kod w `frontend/src` i `backend/app`
5. ✅ Dostosuj konfigurację do swoich potrzeb

---

## 📞 Pomoc

- **Dokumentacja**: Zobacz README_NEW.md
- **Quick Start**: Zobacz QUICKSTART.md
- **Frontend**: Zobacz frontend/README.md
- **Issues**: Zgłoś na GitHub

---

**Miłego korzystania z NER Document Analysis Service! 🚀**

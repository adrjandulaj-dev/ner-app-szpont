# Changelog

All notable changes to the NER Document Analysis Service will be documented in this file.

## [2.0.0] - 2025-11-15

### 🎉 Major Rewrite

Complete backend rewrite from Flask to FastAPI with microservices architecture.

### Added

- **FastAPI Backend**: Modern, async-first web framework
- **Keycloak Authentication**: Enterprise-grade authentication and authorization (OAuth 2.0 / OpenID Connect)
- **MinIO Object Storage**: Scalable document storage
- **MongoDB**: NoSQL database for analysis results and metadata
- **RabbitMQ**: Asynchronous task queue for background processing
- **LLM Integration**: Automatic text extraction from PDFs and images using:
  - OpenAI GPT-4 Vision
  - Anthropic Claude Vision
- **Docker Compose**: Complete orchestration of all services
- **Comprehensive API Documentation**: Interactive Swagger/OpenAPI docs
- **Health Checks**: Monitoring endpoints for all services
- **Helper Scripts**:
  - Keycloak setup automation
  - Token retrieval
  - End-to-end API testing

### Architecture

```
├── Keycloak (Authentication)
├── MinIO (Document Storage)
├── MongoDB (Analysis Results)
├── RabbitMQ (Task Queue)
└── FastAPI (API Layer)
    ├── Document Management
    ├── Analysis Processing
    └── User Management
```

### API Endpoints

#### Documents
- `POST /api/v1/documents/upload` - Upload document
- `GET /api/v1/documents/{id}` - Get document metadata
- `GET /api/v1/documents` - List user documents
- `DELETE /api/v1/documents/{id}` - Delete document

#### Analysis
- `POST /api/v1/analysis` - Create analysis task (async)
- `GET /api/v1/analysis/{id}` - Get analysis result
- `GET /api/v1/analysis/{id}/status` - Check analysis status
- `GET /api/v1/analysis/document/{id}` - Get document analyses
- `GET /api/v1/analysis` - List user analyses

#### Health
- `GET /api/v1/health` - Health check
- `GET /api/v1/health/ready` - Readiness check

### Changed

- Moved from synchronous Flask to asynchronous FastAPI
- Replaced local file storage with MinIO object storage
- Replaced in-memory processing with RabbitMQ queue
- Added proper authentication instead of simple sessions
- Separated document upload from analysis processing

### Technical Details

#### Dependencies
- FastAPI 0.115.5
- python-keycloak 4.2.2
- minio 7.2.9
- motor 3.6.0 (async MongoDB)
- aio-pika 9.4.3 (async RabbitMQ)
- openai 1.54.3
- anthropic 0.39.0
- PyPDF2, pdf2image, pillow (PDF/image processing)

#### Infrastructure
- Keycloak 23.0
- MinIO latest
- MongoDB 7.0
- RabbitMQ 3.12
- PostgreSQL 15 (for Keycloak)

### Migration Guide

For users of v1.x:

1. **Authentication**: Instead of session-based auth, use Keycloak tokens
2. **Document Upload**: New endpoint with multipart/form-data
3. **Analysis**: Now asynchronous - poll for status instead of waiting
4. **Results**: Stored in MongoDB with improved structure
5. **Deployment**: Use Docker Compose instead of manual setup

### Breaking Changes

- All API endpoints now require Bearer token authentication
- Analysis is asynchronous - immediate response with analysis_id
- Document upload returns document_id instead of inline processing
- New response schemas with improved structure
- Different port allocation (8000 for API, 8080 for Keycloak, etc.)

---

## [1.0.0] - 2025-07-13

### Initial Release

- Basic Flask web application
- Simple FastAPI endpoint
- TensorFlow NER model
- Local file processing
- Session-based authentication

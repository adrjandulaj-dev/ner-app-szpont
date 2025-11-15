# NER Frontend

React-based frontend for the NER Document Analysis Service.

## Features

- 🔐 **Keycloak Authentication** - Secure OAuth 2.0 / OpenID Connect login
- 📤 **Document Upload** - Drag & drop or click to upload PDF, images, or text files
- 📊 **Real-time Analysis** - Watch your document being analyzed in real-time
- 🏷️ **Entity Visualization** - Beautiful visualization of named entities
- 📱 **Responsive Design** - Works on desktop and mobile devices

## Tech Stack

- **React 18** with TypeScript
- **Keycloak JS** for authentication
- **Axios** for API calls
- **React Router** for navigation
- **Nginx** for production serving

## Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Setup

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Edit .env and configure:
# - REACT_APP_API_URL
# - REACT_APP_KEYCLOAK_URL
# - REACT_APP_KEYCLOAK_REALM
# - REACT_APP_KEYCLOAK_CLIENT_ID

# Start development server
npm start
```

The app will open at http://localhost:3000

### Build for Production

```bash
npm run build
```

## Docker

### Build Image

```bash
docker build -t ner-frontend .
```

### Run Container

```bash
docker run -p 3000:80 ner-frontend
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REACT_APP_API_URL` | Backend API URL | `http://localhost:8000` |
| `REACT_APP_KEYCLOAK_URL` | Keycloak server URL | `http://localhost:8080` |
| `REACT_APP_KEYCLOAK_REALM` | Keycloak realm name | `ner-app` |
| `REACT_APP_KEYCLOAK_CLIENT_ID` | Keycloak client ID | `ner-frontend` |

## Project Structure

```
frontend/
├── public/              # Static files
│   ├── index.html
│   └── silent-check-sso.html
├── src/
│   ├── components/      # React components
│   │   ├── DocumentUpload.tsx
│   │   ├── DocumentList.tsx
│   │   └── AnalysisResults.tsx
│   ├── contexts/        # React contexts
│   │   └── AuthContext.tsx
│   ├── pages/           # Page components
│   │   ├── Dashboard.tsx
│   │   └── Login.tsx
│   ├── services/        # API services
│   │   └── api.ts
│   ├── types/           # TypeScript types
│   │   └── index.ts
│   ├── App.tsx          # Main app component
│   ├── App.css          # Styles
│   └── index.tsx        # Entry point
├── nginx.conf           # Nginx configuration
├── Dockerfile           # Docker build file
└── package.json         # Dependencies
```

## Features Detail

### Authentication

The app uses Keycloak for authentication:

1. User clicks "Sign In"
2. Redirected to Keycloak login
3. After login, redirected back with token
4. Token is automatically included in all API requests

### Document Upload

Supports multiple upload methods:
- Click to browse files
- Drag and drop
- Supported formats: PDF, TXT, PNG, JPG, JPEG
- Max size: 50MB

### Analysis Flow

1. Upload document → stored in MinIO
2. Request analysis → queued in RabbitMQ
3. Poll for status every 2 seconds
4. Display results when complete

### Entity Visualization

- Color-coded by entity type
- Grouped by category
- Detailed sentence-by-sentence breakdown
- Tagged token view

## API Integration

The frontend communicates with the backend through these endpoints:

- `POST /api/v1/documents/upload` - Upload document
- `GET /api/v1/documents` - List documents
- `POST /api/v1/analysis` - Create analysis
- `GET /api/v1/analysis/{id}` - Get results
- `GET /api/v1/analysis/{id}/status` - Check status

See `src/services/api.ts` for full API client.

## Troubleshooting

### Keycloak Connection Issues

Make sure:
1. Keycloak is running
2. Realm `ner-app` exists
3. Client `ner-frontend` is configured as public client
4. Redirect URIs include your frontend URL

### CORS Errors

Check that:
1. Backend CORS is configured to allow frontend origin
2. Keycloak web origins include frontend URL

### Build Errors

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

## License

MIT

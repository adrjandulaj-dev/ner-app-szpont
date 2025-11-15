# Frontend Information

## Overview
React-based frontend with Keycloak authentication, document upload, and real-time analysis visualization.

## Quick Access
- **URL**: http://localhost:3000
- **Login**: testuser / testpass123

## Features
✅ Keycloak OAuth 2.0 authentication
✅ Drag & drop document upload
✅ Real-time analysis status
✅ Beautiful entity visualization
✅ Responsive design

## Setup
Frontend is automatically built and served via Docker Compose on port 3000.

For local development:
```bash
cd frontend
npm install
npm start
```

## Configuration
Environment variables in `frontend/.env`:
- REACT_APP_API_URL
- REACT_APP_KEYCLOAK_URL
- REACT_APP_KEYCLOAK_REALM
- REACT_APP_KEYCLOAK_CLIENT_ID

See `frontend/README.md` for more details.

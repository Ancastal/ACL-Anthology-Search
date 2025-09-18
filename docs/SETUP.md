# Setup Guide

## Quick Start

### 1. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the API server
python -m uvicorn src.acl_search.ui.api_server:app --reload --port 8000
```

### 2. Frontend Setup
```bash
# Install Node.js dependencies
cd frontend/react-app
npm install

# Start the development server
npm run dev
```

### 3. Access the Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Using Make Commands

```bash
# Setup everything
make install
make setup-frontend

# Start both backend and frontend (recommended)
make run

# Or run individually:
make run-backend   # Start API server only
make run-frontend  # Start frontend only

# Other commands
make dev          # Alias for 'make run'
```

## Environment Variables

Create a `.env.local` file in the root directory:

```env
# Optional: Metadata provider configuration
METADATA_PROVIDER=openalex,crossref,semanticscholar
OPENALEX_UA=your-app-name/1.0 (+mailto:your-email@example.com)
CROSSREF_UA=your-app-name/1.0 (+mailto:your-email@example.com)
S2_API_KEY=your-semantic-scholar-api-key

# Optional: Cache settings
METADATA_CACHE_DIR=.cache/metadata
METADATA_OFFLINE=false
```

## Troubleshooting

### Backend Issues
- Ensure Python 3.8+ is installed
- Check that uvicorn is installed: `pip install uvicorn`
- Verify the API is running at http://localhost:8000/docs

### Frontend Issues
- Ensure Node.js 18+ is installed
- Clear npm cache: `npm cache clean --force`
- Delete node_modules and reinstall: `rm -rf node_modules && npm install`

### CORS Issues
- Ensure the frontend is configured to connect to the correct backend URL
- Check that the API server allows CORS from the frontend origin
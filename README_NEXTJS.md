# ACL Anthology Search - NextJS Application

A modern, responsive web application for searching and filtering papers from the ACL Anthology using boolean keywords. Built with NextJS frontend and FastAPI backend.

## 🚀 Features

### Advanced Search Capabilities
- **Boolean operators**: AND, OR, NOT with parentheses support
- **Exact phrase matching**: Use quotes for precise searches
- **Multi-field search**: Search across titles, abstracts, and authors
- **Real-time search**: Instant results as you type

### Smart Filtering
- **Year range filtering**: Filter papers by publication year (1952-2025)
- **Venue filtering**: Filter by conferences and workshops
- **Results limiting**: Control number of displayed results
- **Quick filter presets**: Recent papers, reset filters

### Modern UI/UX
- **Responsive design**: Works on desktop, tablet, and mobile
- **Clean interface**: Modern design with Tailwind CSS
- **Loading states**: Smooth loading indicators
- **Error handling**: User-friendly error messages

### Data Export
- **CSV download**: Export search results with full metadata
- **Complete paper info**: Title, authors, year, venue, URL, abstract

## 🏗️ Architecture

### Frontend (NextJS + TypeScript)
- **Framework**: Next.js 15 with TypeScript
- **Styling**: Tailwind CSS for responsive design
- **Icons**: Lucide React for consistent iconography
- **State Management**: React hooks for local state

### Backend (FastAPI + Python)
- **API Framework**: FastAPI for high-performance REST API
- **Search Engine**: Custom boolean search implementation
- **Data Source**: ACL Anthology Python library
- **CORS**: Configured for frontend integration

## 📁 Project Structure

```
ACL-Anthology-Search/
├── acl-search-frontend/          # NextJS frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx          # Main search page
│   │   │   └── globals.css       # Global styles
│   │   └── components/
│   │       ├── SearchBar.tsx     # Search input component
│   │       ├── SearchFilters.tsx # Filter sidebar
│   │       ├── SearchResults.tsx # Results display
│   │       └── LoadingSpinner.tsx# Loading component
│   ├── package.json
│   └── tailwind.config.js
├── api_server.py                 # FastAPI backend
├── search_engine.py              # Boolean search engine
└── README_NEXTJS.md             # This file
```

## 🚀 Getting Started

### Prerequisites
- **Node.js** 18+ and npm
- **Python** 3.10+ 
- **pip** package manager

### 1. Install Backend Dependencies
```bash
pip install fastapi uvicorn acl-anthology python-multipart
```

### 2. Install Frontend Dependencies
```bash
cd acl-search-frontend
npm install
```

### 3. Start the Backend Server
```bash
# From project root
python api_server.py
```
The API will be available at `http://127.0.0.1:8000`

### 4. Start the Frontend Development Server
```bash
cd acl-search-frontend
npm run dev
```
The application will be available at `http://localhost:3000`

## 🔍 Search Examples

### Basic Searches
- `attention` - Find papers containing "attention"
- `machine translation` - Find papers with both words
- `"neural machine translation"` - Exact phrase search

### Boolean Operations
- `attention AND mechanism` - Both terms required
- `BERT OR GPT OR T5` - Any of these models
- `attention NOT model` - Contains "attention" but not "model"

### Advanced Queries
- `"transformer architecture" AND attention`
- `(BERT OR GPT) AND "question answering"`
- `machine translation AND (attention OR transformer)`

## 🛠️ API Endpoints

### Health Check
```
GET /health
```
Returns API status and search engine readiness.

### Search Papers
```
POST /search
Content-Type: application/json

{
  "query": "attention mechanism",
  "fields": ["title", "abstract", "authors"],
  "year_range": [2020, 2023],
  "venues": ["acl", "emnlp"],
  "limit": 100
}
```

### Get Statistics
```
GET /stats
```
Returns dataset statistics (total papers, year range, venues).

## 📊 Performance

- **Dataset**: 113,129+ research papers
- **Search Speed**: < 0.1 seconds for most queries
- **Data Loading**: ~6 seconds initial load
- **Memory Usage**: Optimized with caching

## 🎨 UI Components

### SearchBar
- Input field with search suggestions
- Help panel with example queries
- Submit and clear buttons

### SearchFilters
- Field selection (title, abstract, authors)
- Year range slider
- Venue checkboxes
- Results limit selector
- Quick action buttons

### SearchResults
- Results summary with statistics
- Paper cards with metadata
- Expandable abstracts
- CSV export functionality

## 🚀 Deployment

### Production Build
```bash
# Frontend
cd acl-search-frontend
npm run build
npm start

# Backend
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

### Environment Variables
```bash
# Backend
PYTHONPATH=/path/to/project
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
NEXT_PUBLIC_API_URL=http://your-api-url:8000
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project uses data from the ACL Anthology. Please respect the original licensing terms of the research papers.

## 🔗 Related Links

- [ACL Anthology](https://aclanthology.org/)
- [ACL Anthology Python Library](https://github.com/acl-org/acl-anthology)
- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Tailwind CSS](https://tailwindcss.com/)
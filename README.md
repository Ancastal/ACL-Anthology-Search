# ACL Anthology Search

A modern web application for searching and filtering papers from the ACL Anthology using boolean keywords across multiple fields. Features a Next.js frontend with Python backend API.

<center><img width="700" height="600" alt="image" src="https://github.com/user-attachments/assets/af86f620-da21-4d22-bd04-5e8f305745cd" /></center>

## Features

### 🔍 Advanced Search
- **Boolean operators**: AND, OR, NOT
- **Grouping with parentheses**
- **Exact phrase search**: Use quotes to match whole words or phrases only
- **Multi-field search**: Search across titles, abstracts, and authors
- **Case-insensitive**: All searches are case-insensitive
- **Fuzzy matching**: Optional approximate matches using RapidFuzz

### 🏷️ Filtering Options
- **Year range**: Filter papers by publication year
- **Venue selection**: Filter by conferences and venues
- **Results limit**: Control the number of results displayed

### 📊 Results Display
- **Rich metadata**: Title, authors, year, venue, and abstracts
- **Match highlights**: Shows which fields matched your query
- **Modern UI**: Clean, responsive design with Next.js
- **Real-time search**: Fast, interactive search experience
- **External enrichment**: Citation counts and related works via OpenAlex/Crossref/Semantic Scholar

## Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm or yarn

### Backend Setup
1. Clone this repository
2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

### Frontend Setup
1. Navigate to the frontend directory:
```bash
cd frontend/react-app
```
2. Install Node.js dependencies:
```bash
npm install
```

## Usage

### Development Mode

**Option 1: One Command (Recommended)**
```bash
make run
```
This starts both backend (port 8000) and frontend (port 3000) automatically.

**Option 2: Manual Setup**
1. **Start the Backend API Server**:
```bash
python -m uvicorn src.acl_search.ui.api_server:app --reload --port 8000
```

2. **Start the Frontend Development Server**:
```bash
cd frontend/react-app
npm run dev
```

3. **Open your browser** to `http://localhost:3000`

### Production Mode

1. **Build the frontend**:
```bash
cd frontend/react-app
npm run build
npm start
```

2. **Start the backend**:
```bash
python -m uvicorn src.acl_search.ui.api_server:app --host 0.0.0.0 --port 8000
```

### Testing
```bash
make test
# or
python -m pytest tests/
```

## Search Examples

### Basic Search
- `attention` - Find papers containing "attention"
- `machine translation` - Find papers with both words
- `"neural machine translation"` - Exact phrase search

### Boolean Operations
- `attention AND mechanism` - Both terms must be present
- `BERT OR GPT OR T5` - Any of these terms
- `attention NOT model` - Contains "attention" but not "model"

### Complex Queries
- `"transformer architecture" AND attention`
- `(BERT OR GPT) AND "question answering"`
- `machine translation AND (attention OR transformer)`

## Data Source

This application uses data from the [ACL Anthology](https://aclanthology.org/), which contains over 113,000 computational linguistics and NLP research papers.

## Technical Details

- **Backend**: Python FastAPI with acl-anthology library
- **Frontend**: Next.js 15 with React 19 and TypeScript
- **Search Engine**: Custom boolean search implementation
- **Styling**: Tailwind CSS v4
- **API**: RESTful API with automatic documentation
- **Data Loading**: Automatically downloads ACL Anthology data on first run
- **External Metadata**: Integration with OpenAlex, Crossref, and Semantic Scholar (with local caching)

## Project Structure

```
├── src/acl_search/              # Main Python package
│   ├── core/                    # Search engine logic
│   ├── providers/               # Metadata providers (OpenAlex, Crossref, Semantic Scholar)
│   └── ui/                      # FastAPI backend server
├── frontend/react-app/          # Next.js frontend application
├── tests/                       # Test suite (unit & integration)
├── docs/                        # Documentation
└── scripts/                     # Utility scripts
```

## Performance

- **Data loading**: ~6 seconds initial load
- **Search speed**: < 0.1 seconds for most queries
- **Memory usage**: Efficient caching and processing
- **Data size**: 113,129+ papers from ACL Anthology
 - **Metadata caching**: External metadata is cached in `.cache/metadata` to speed up repeats

## Configuration (optional)

Set environment variables to control metadata enrichment:
- `METADATA_PROVIDER` (default `openalex,crossref,semanticscholar`)
- `METADATA_MAX_RESULTS` (default `10` per search)
- `METADATA_CACHE_DIR` (default `.cache/metadata`)
- `METADATA_OFFLINE` (`true` to disable network calls)
- `OPENALEX_UA` (identify your app to OpenAlex)
- `CROSSREF_UA` (identify your app to Crossref)
- `S2_API_KEY` (Semantic Scholar API key)

## License

This project uses data from the ACL Anthology. Please respect the original licensing terms of the research papers.

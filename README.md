# ACL Anthology Search

A comprehensive Streamlit web application for searching and filtering papers from the ACL Anthology using boolean keywords across multiple fields.

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
- **CSV export**: Download search results as CSV
- **Author management**: Smart display for papers with many authors
 - **External enrichment (optional)**: Citation counts and related works via OpenAlex/Semantic Scholar

## Installation

1. Clone or download this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Run the Streamlit App
```bash
streamlit run app.py
```

Tip: Toggle "Show citation counts and related works" to enrich results (may be slower on first fetch).

### Command Line Testing
```bash
python test_search.py
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

- **Backend**: Python with acl-anthology library
- **Frontend**: Streamlit
- **Search Engine**: Custom boolean search implementation
- **Caching**: Streamlit resource caching for performance
- **Data Loading**: Automatically downloads ACL Anthology data on first run
 - **External Metadata**: Optional integration with OpenAlex and Semantic Scholar (with local caching)

## Files

- `app.py` - Main Streamlit application
- `search_engine.py` - Core search functionality with boolean operations
- `test_search.py` - Test script for search engine
- `explore_acl.py` - Data exploration script
- `requirements.txt` - Python dependencies
 - `metadata_providers.py` - External metadata (OpenAlex/Semantic Scholar) with local caching

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

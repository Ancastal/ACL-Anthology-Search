# ACL Anthology Search

A comprehensive Streamlit web application for searching and filtering papers from the ACL Anthology using boolean keywords across multiple fields.

## Features

### 🔍 Advanced Search
- **Boolean operators**: AND, OR, NOT
- **Exact phrase search**: Use quotes for exact matches
- **Multi-field search**: Search across titles, abstracts, and authors
- **Case-insensitive**: All searches are case-insensitive

### 🏷️ Filtering Options
- **Year range**: Filter papers by publication year
- **Venue selection**: Filter by conferences and venues
- **Results limit**: Control the number of results displayed

### 📊 Results Display
- **Rich metadata**: Title, authors, year, venue, and abstracts
- **Match highlights**: Shows which fields matched your query
- **CSV export**: Download search results as CSV
- **Author management**: Smart display for papers with many authors

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

## Files

- `app.py` - Main Streamlit application
- `search_engine.py` - Core search functionality with boolean operations
- `test_search.py` - Test script for search engine
- `explore_acl.py` - Data exploration script
- `requirements.txt` - Python dependencies

## Performance

- **Data loading**: ~6 seconds initial load
- **Search speed**: < 0.1 seconds for most queries
- **Memory usage**: Efficient caching and processing
- **Data size**: 113,129+ papers from ACL Anthology

## License

This project uses data from the ACL Anthology. Please respect the original licensing terms of the research papers.
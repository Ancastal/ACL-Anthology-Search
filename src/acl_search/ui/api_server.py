"""
FastAPI backend for ACL Anthology search
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import threading
import os
from acl_search.core.search_engine import BooleanSearchEngine, SearchResult
from acl_search.core.semantic import SemanticEmbedder
from acl_search.core.arxiv_search import ArxivSearchEngine
from acl_search.providers.metadata_providers import ExternalMetadataProvider

# Import experimental search engine
try:
    from acl_search.core.experimental_search import ExperimentalSearchEngine
    EXPERIMENTAL_AVAILABLE = True
except ImportError as e:
    EXPERIMENTAL_AVAILABLE = False
    print(f"⚠️  Experimental search engine not available: {e}")
    print("Install dependencies with: pip install pyspellchecker rank-bm25 sentence-transformers transformers torch")

# OpenAI integration
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI not available. Install with: pip install openai")

# Pydantic models
class SearchRequest(BaseModel):
    query: str
    fields: List[str] = ["title", "abstract", "authors"]
    year_range: Optional[tuple[int, int]] = None
    venues: Optional[List[str]] = None
    limit: int = 100
    fuzzy: bool = False
    fuzzy_threshold: int = 80
    sort: str = "relevance"  # "relevance" | "year"
    # Semantic search options
    semantic: bool = False
    semantic_mode: str = "rerank"  # "rerank" | "hybrid"
    semantic_top_k: int = 200  # for rerank/hybrid
    embedding_model: str | None = None
    include_metadata: bool = False
    max_related: int = 3
    sources: List[str] = ["acl"]  # "acl", "arxiv", or both
    # Experimental search pipeline
    experimental: bool = False  # Use experimental IR pipeline

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_count: int
    search_time: float
    stats: Dict[str, Any]
    semantic_method: Optional[str] = None

class ConvertQueryRequest(BaseModel):
    natural_query: str

class ConvertQueryResponse(BaseModel):
    converted_query: str
    explanation: str

class PaperMetadataRequest(BaseModel):
    doi: Optional[str] = None
    title: Optional[str] = None
    authors: Optional[List[str]] = []
    year: Optional[int] = None
    max_related: int = 3

class PaperMetadataResponse(BaseModel):
    metadata: Dict[str, Any]

class AuthorResponse(BaseModel):
    name: str
    total_papers: int
    coauthors: List[Dict[str, Any]]
    venues: List[Dict[str, Any]]
    years: List[Dict[str, Any]]
    papers: List[Dict[str, Any]]

# Global search engine instances
search_engine = None
experimental_engine = None
arxiv_engine = None
metadata_provider: Optional[ExternalMetadataProvider] = None

# FastAPI app
app = FastAPI(
    title="ACL Anthology Search API",
    description="Search API for ACL Anthology papers with boolean keywords",
    version="1.0.0"
)

# CORS middleware to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize the search engine on startup"""
    global search_engine
    print("🚀 Starting up ACL Anthology Search API...")
    
    def load_engine():
        global search_engine, experimental_engine, arxiv_engine
        search_engine = BooleanSearchEngine()
        print("✅ ACL search engine loaded successfully!")

        # Initialize arXiv engine first (faster loading)
        try:
            arxiv_engine = ArxivSearchEngine()
            print("✅ arXiv search engine loaded successfully!")
        except Exception as e:
            print(f"⚠️  arXiv search engine failed to load: {e}")
            arxiv_engine = None

        # Initialize experimental search engine (slower loading)
        if EXPERIMENTAL_AVAILABLE:
            try:
                experimental_engine = ExperimentalSearchEngine(search_engine.anthology)
                print("✅ Experimental search engine loaded successfully!")
            except Exception as e:
                print(f"⚠️  Experimental search engine failed to load: {e}")
                experimental_engine = None
        else:
            experimental_engine = None

        # Initialize metadata provider after search engine to avoid import side effects
        global metadata_provider
        metadata_provider = ExternalMetadataProvider()
    
    # Load search engine in a separate thread to avoid blocking
    thread = threading.Thread(target=load_engine)
    thread.start()
    
    print("🔄 Search engine loading in background...")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "ACL Anthology Search API",
        "status": "ready" if search_engine else "loading",
        "version": "1.0.0",
        "search_engine": "boolean+bm25"
    }

@app.get("/health")
async def health_check():
    """Health check with search engine status"""
    return {
        "status": "healthy" if search_engine else "initializing",
        "search_engine_ready": search_engine is not None
    }

@app.get("/stats")
async def get_stats():
    """Get general statistics about the dataset"""
    if not search_engine:
        raise HTTPException(status_code=503, detail="Search engine not ready")
    
    try:
        year_range = search_engine.get_year_range()
        venues = search_engine.get_available_venues()
        
        stats = {
            "total_papers": len(search_engine.papers),
            "year_range": year_range,
            "total_venues": len(venues),
            "common_venues": sorted([v.upper() for v in venues if any(cv in v.lower() for cv in ["acl", "emnlp", "naacl", "eacl", "coling"])])[:20],
            "experimental_search_available": experimental_engine is not None
        }

        # Add experimental engine stats if available
        if experimental_engine:
            stats["experimental_features"] = experimental_engine.get_stats()

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

@app.post("/search", response_model=SearchResponse)
async def search_papers(request: SearchRequest):
    """Search papers with boolean keywords"""
    if not search_engine:
        raise HTTPException(status_code=503, detail="Search engine not ready")
    
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        import time
        start_time = time.time()
        
        # Build filters
        filters = {}
        if request.year_range:
            filters["year_range"] = request.year_range
        if request.venues:
            filters["venues"] = request.venues
        
        # Perform search based on selected sources
        all_results = []

        # Search ACL Anthology if requested
        if "acl" in request.sources:
            # Route to experimental or standard engine
            if request.experimental and experimental_engine:
                print("🔬 Using experimental search pipeline")
                acl_results = experimental_engine.search(
                    query=request.query,
                    fields=request.fields,
                    filters=filters,
                    limit=request.limit
                )
            elif request.experimental and not experimental_engine:
                raise HTTPException(status_code=503, detail="Experimental search engine not available")
            else:
                acl_results = search_engine.search(
                    query=request.query,
                    fields=request.fields,
                    filters=filters,
                    limit=request.limit,
                    fuzzy=request.fuzzy,
                    fuzzy_threshold=request.fuzzy_threshold,
                    sort=request.sort
                )
            all_results.extend(acl_results)

        # Search arXiv if requested and available
        if "arxiv" in request.sources:
            if arxiv_engine is None:
                print("arXiv search engine not available - skipping arXiv search")
            else:
                try:
                    arxiv_results = arxiv_engine.search(
                        query=request.query,
                        fields=request.fields,
                        filters=filters,
                        limit=request.limit
                    )
                    all_results.extend(arxiv_results)
                    print(f"arXiv search returned {len(arxiv_results)} results")
                except Exception as e:
                    print(f"arXiv search failed: {e}")

        # Sort combined results if multiple sources
        if len(request.sources) > 1:
            if request.sort == "year":
                all_results.sort(key=lambda r: int(r.year) if r.year and r.year.isdigit() else 0, reverse=True)
            else:  # relevance
                all_results.sort(key=lambda r: r.score or 0.0, reverse=True)

        # Apply limit to combined results
        results = all_results[:request.limit]

        # Optional semantic rerank or hybrid
        semantic_method_used = None
        if request.semantic and results:
            try:
                embedder = SemanticEmbedder(model_name=request.embedding_model)
                # Compose query text
                qtext = request.query
                # Take top-K by BM25 for reranking to control cost
                top_k = max(1, min(request.semantic_top_k, len(results)))
                subset = results[:top_k]

                # Compute semantic similarity against title+abstract
                sims: list[float] = []
                semantic_methods = set()
                for r in subset:
                    t = r.title or ""
                    a = r.abstract or ""
                    txt = f"{t}. {a}".strip()
                    sim_score, method = embedder.similarity(qtext, txt)
                    sims.append(sim_score)
                    semantic_methods.add(method)

                # Track which method was primarily used
                semantic_method_used = list(semantic_methods)[0] if len(semantic_methods) == 1 else "mixed"

                # Normalize BM25 and semantic to 0..1
                bm25_scores = [float(r.score or 0.0) for r in subset]
                def normalize(arr: list[float]) -> list[float]:
                    if not arr:
                        return arr
                    mn = min(arr)
                    mx = max(arr)
                    if mx - mn < 1e-9:
                        return [0.0 for _ in arr]
                    return [(x - mn) / (mx - mn) for x in arr]
                bm25_n = normalize(bm25_scores)
                sims_n = normalize(sims)

                # Combine (simple average); could expose weight later
                combined = [0.5 * b + 0.5 * s for b, s in zip(bm25_n, sims_n)]
                # Attach a temporary attribute for sorting
                for r, c in zip(subset, combined):
                    r.score = (r.score or 0.0)  # keep original
                    setattr(r, "_combined_score", c)

                # Sort the subset by combined score desc, then append the rest
                subset_sorted = sorted(subset, key=lambda r: getattr(r, "_combined_score", 0.0), reverse=True)
                # Remove temp attr
                for r in subset_sorted:
                    if hasattr(r, "_combined_score"):
                        delattr(r, "_combined_score")
                results = subset_sorted + results[top_k:]
            except Exception as e:
                # Non-fatal: proceed without semantic rerank
                print(f"Semantic rerank failed: {e}")
        
        search_time = time.time() - start_time
        
        # Convert results to dictionaries
        result_dicts = []
        for result in results:
            # Handle both ACL SearchResult and arXiv ArxivSearchResult
            if hasattr(result, 'source'):
                # arXiv result
                rd = {
                    "paper_id": result.paper_id,
                    "title": result.title,
                    "authors": result.authors,
                    "year": result.year,
                    "abstract": result.abstract,
                    "venue": result.venue if result.venue else [],  # arXiv categories
                    "url": result.url,
                    "match_fields": result.match_fields or [],
                    "doi": getattr(result, "doi", None),
                    "score": getattr(result, "score", None),
                    "source": result.source
                }
            else:
                # ACL result
                rd = {
                    "paper_id": result.paper_id,
                    "title": result.title,
                    "authors": result.authors,
                    "year": result.year,
                    "abstract": result.abstract,
                    "venue": [v.upper() for v in result.venue],
                    "url": result.url,
                    "match_fields": result.match_fields,
                    "doi": getattr(result, "doi", None),
                    "score": getattr(result, "score", None),
                    "source": "ACL Anthology"
                }
            result_dicts.append(rd)

        # Optionally enrich with external metadata (bounded)
        if request.include_metadata and result_dicts:
            max_to_enrich = int(os.getenv("METADATA_MAX_RESULTS", "10"))
            provider = metadata_provider or ExternalMetadataProvider()

            for rd in result_dicts[:max_to_enrich]:
                try:
                    # Parse year to int if needed
                    year_int = None
                    if rd.get("year"):
                        try:
                            year_int = int(rd.get("year"))
                        except (ValueError, TypeError):
                            pass

                    meta = provider.fetch(
                        doi=rd.get("doi"),
                        title=rd.get("title"),
                        authors=rd.get("authors") or [],
                        year=year_int,
                        max_related=request.max_related,
                    )
                    rd["metadata"] = meta
                except Exception as e:
                    rd["metadata"] = {"error": str(e)}
        
        # Calculate stats
        years = [r["year"] for r in result_dicts if r["year"]]
        venues = set()
        authors = set()
        for r in result_dicts:
            venues.update(r["venue"])
            authors.update(r["authors"])
        
        stats = {
            "year_range": [min(years), max(years)] if years else None,
            "unique_venues": len(venues),
            "unique_authors": len(authors)
        }
        
        return SearchResponse(
            results=result_dicts,
            total_count=len(results),
            search_time=search_time,
            stats=stats,
            semantic_method=semantic_method_used
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/search")
async def search_papers_get(
    q: str = Query(..., description="Search query"),
    fields: str = Query("title,abstract,authors", description="Comma-separated search fields"),
    year_min: Optional[int] = Query(None, description="Minimum year"),
    year_max: Optional[int] = Query(None, description="Maximum year"),
    venues: Optional[str] = Query(None, description="Comma-separated venues"),
    limit: int = Query(100, description="Maximum results"),
    fuzzy: bool = Query(False, description="Enable fuzzy matching"),
    fuzzy_threshold: int = Query(80, description="Fuzzy matching threshold"),
    sort: str = Query("relevance", description="Sort by 'relevance' or 'year'"),
    semantic: bool = Query(False, description="Enable semantic reranking"),
    semantic_mode: str = Query("rerank", description="Semantic mode: rerank|hybrid"),
    semantic_top_k: int = Query(200, description="Top-K for semantic rerank"),
    include_metadata: bool = Query(False, description="Include external metadata"),
    max_related: int = Query(3, description="Related works per item")
):
    """GET endpoint for search (for easy testing)"""
    
    # Parse parameters
    fields_list = [f.strip() for f in fields.split(",")]
    venues_list = [v.strip() for v in venues.split(",")] if venues else None
    year_range = (year_min, year_max) if year_min and year_max else None
    
    # Create request object
    request = SearchRequest(
        query=q,
        fields=fields_list,
        year_range=year_range,
        venues=venues_list,
        limit=limit,
        fuzzy=fuzzy,
        fuzzy_threshold=fuzzy_threshold,
        sort=sort,
        semantic=semantic,
        semantic_mode=semantic_mode,
        semantic_top_k=semantic_top_k,
        include_metadata=include_metadata,
        max_related=max_related
    )
    
    return await search_papers(request)

@app.post("/metadata", response_model=PaperMetadataResponse)
async def fetch_metadata(req: PaperMetadataRequest):
    """Fetch external metadata for a single paper on demand"""
    try:
        provider = metadata_provider or ExternalMetadataProvider()
        meta = provider.fetch(
            doi=req.doi,
            title=req.title,
            authors=req.authors or [],
            year=req.year,
            max_related=req.max_related,
        )
        return PaperMetadataResponse(metadata=meta)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metadata fetch error: {str(e)}")

@app.post("/convert-query", response_model=ConvertQueryResponse)
async def convert_natural_language_query(request: ConvertQueryRequest):
    """Convert natural language query to boolean search syntax"""
    try:
        natural_query = request.natural_query.strip()
        if not natural_query:
            raise HTTPException(status_code=400, detail="Natural query cannot be empty")
        
        # Use AI-powered conversion with fallback
        converted_query, explanation = await convert_to_boolean_query_ai(natural_query)
        
        return ConvertQueryResponse(
            converted_query=converted_query,
            explanation=explanation
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion error: {str(e)}")

async def convert_to_boolean_query_ai(natural_query: str) -> tuple[str, str]:
    """Convert natural language to boolean query using OpenAI"""
    if not OPENAI_AVAILABLE:
        # Fallback to simple rule-based conversion
        return convert_to_boolean_query_simple(natural_query)
    
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        fallback_query, _ = convert_to_boolean_query_simple(natural_query)
        return fallback_query, "Used rule-based conversion (OpenAI API key not configured)"
    
    try:
        client = OpenAI(api_key=api_key)
        
        prompt = f"""Convert natural language queries to boolean search for academic papers.

When users ask about "topics", "keywords", "concepts" etc. in a field, they want papers in that field, NOT papers about the word "topics" or "keywords".

Examples:
"papers about machine learning" → machine learning
"research on BERT or GPT" → (BERT OR GPT)
"what are main topics in NLP?" → NLP OR "natural language processing" OR embeddings OR tokenization OR transformers
"important keywords related to LLMs" → LLM OR "large language model" OR "foundation model" OR "generative AI"
"key concepts in transformers" → transformer OR transformers OR "self-attention" OR "multi-head attention" OR "positional encoding" OR "encoder-decoder"
"find deep learning papers" → "deep learning"

Convert to search query (focus on the subject field mentioned):
"{natural_query}" →"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Convert natural language to boolean search. When users ask about 'topics', 'keywords', or 'concepts' in a field, they want papers about that FIELD, not papers about the words 'topics' or 'keywords'. Ignore meta-language. Return only the search query."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.1
        )
        converted_query = response.choices[0].message.content.strip()
        explanation = "Converted using OpenAI GPT-4o for optimal boolean search syntax"
        
        return converted_query, explanation
        
    except Exception as e:
        print(f"OpenAI conversion failed: {e}")
        # Fallback to rule-based
        fallback_query, _ = convert_to_boolean_query_simple(natural_query)
        return fallback_query, f"Used rule-based conversion (OpenAI error: {str(e)})"

def convert_to_boolean_query_simple(natural_query: str) -> tuple[str, str]:
    """Simple rule-based conversion as fallback"""
    import re
    
    query = natural_query.strip()
    
    # Simple replacements
    replacements = [
        (r'\bpapers?\s+about\s+', ''),
        (r'\bresearch\s+on\s+', ''),
        (r'\bstudies\s+on\s+', ''), 
        (r'\beither\s+(.+?)\s+or\s+(.+)', r'\1 OR \2'),
        (r'\bboth\s+(.+?)\s+and\s+(.+)', r'\1 AND \2'),
        (r'\b(.+?)\s+but\s+not\s+(.+)', r'\1 NOT \2'),
        (r'\bor\b', ' OR '),
        (r'\band\b', ' AND '),
        (r'\bnot\s+', 'NOT '),
        (r'\s+', ' ')
    ]
    
    for pattern, replacement in replacements:
        query = re.sub(pattern, replacement, query, flags=re.IGNORECASE)
    
    query = query.strip()
    
    # If no operators and multiple words, quote it
    if not any(op in query.upper() for op in ['AND', 'OR', 'NOT']) and len(query.split()) > 1:
        if len(query.split()) <= 3:
            query = f'"{query}"'
    
    explanation = "Used rule-based conversion with pattern matching and operator recognition"
    return query, explanation

@app.get("/author", response_model=AuthorResponse)
async def get_author(name: str = Query(..., description="Author full or partial name")):
    """Return author page data: publications, co-authors, venues, years."""
    if not search_engine:
        raise HTTPException(status_code=503, detail="Search engine not ready")
    target = name.strip().lower()
    if not target:
        raise HTTPException(status_code=400, detail="Author name required")

    papers = []
    coauthor_counts: Dict[str, int] = {}
    venue_counts: Dict[str, int] = {}
    year_counts: Dict[str, int] = {}

    for p in search_engine.papers:
        authors = [f"{a.name.first} {a.name.last}".strip() for a in getattr(p, 'authors', [])] if getattr(p, 'authors', None) else []
        # Match if any author contains the target (case-insensitive)
        if any(target in a.lower() for a in authors):
            paper_dict = {
                "paper_id": p.id,
                "title": str(p.title) if p.title else "",
                "authors": authors,
                "year": p.year,
                "venue": [v.upper() for v in (p.venue_ids or [])],
                "url": p.web_url,
            }
            papers.append(paper_dict)
            # Co-authors (exclude self matches)
            for a in authors:
                if target not in a.lower():
                    coauthor_counts[a] = coauthor_counts.get(a, 0) + 1
            # Venue counts
            for v in (p.venue_ids or []):
                venue_counts[v.upper()] = venue_counts.get(v.upper(), 0) + 1
            # Year counts
            y = str(p.year)
            year_counts[y] = year_counts.get(y, 0) + 1

    # Build response lists
    coauthors = sorted(
        [{"name": n, "count": c} for n, c in coauthor_counts.items()],
        key=lambda x: x["count"], reverse=True
    )
    venues = sorted(
        [{"venue": v, "count": c} for v, c in venue_counts.items()],
        key=lambda x: x["count"], reverse=True
    )
    years = sorted(
        [{"year": int(y), "count": c} for y, c in year_counts.items()],
        key=lambda x: x["year"]
    )

    return AuthorResponse(
        name=name,
        total_papers=len(papers),
        coauthors=coauthors,
        venues=venues,
        years=years,
        papers=papers
    )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting ACL Anthology Search API server...")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

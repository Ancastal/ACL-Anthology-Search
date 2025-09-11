"""
FastAPI backend for ACL Anthology search
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import threading
from search_engine import BooleanSearchEngine, SearchResult

# Pydantic models
class SearchRequest(BaseModel):
    query: str
    fields: List[str] = ["title", "abstract", "authors"]
    year_range: Optional[tuple[int, int]] = None
    venues: Optional[List[str]] = None
    limit: int = 100

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_count: int
    search_time: float
    stats: Dict[str, Any]

# Global search engine instance
search_engine = None

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
        global search_engine
        search_engine = BooleanSearchEngine()
        print("✅ Search engine loaded successfully!")
    
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
        "version": "1.0.0"
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
        
        return {
            "total_papers": len(search_engine.papers),
            "year_range": year_range,
            "total_venues": len(venues),
            "common_venues": sorted([v for v in venues if any(cv in v for cv in ["acl", "emnlp", "naacl", "eacl", "coling"])])[:20]
        }
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
        
        # Perform search
        results = search_engine.search(
            query=request.query,
            fields=request.fields,
            filters=filters,
            limit=request.limit
        )
        
        search_time = time.time() - start_time
        
        # Convert results to dictionaries
        result_dicts = []
        for result in results:
            result_dicts.append({
                "paper_id": result.paper_id,
                "title": result.title,
                "authors": result.authors,
                "year": result.year,
                "abstract": result.abstract,
                "venue": result.venue,
                "url": result.url,
                "match_fields": result.match_fields
            })
        
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
            stats=stats
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
    limit: int = Query(100, description="Maximum results")
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
        limit=limit
    )
    
    return await search_papers(request)

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting ACL Anthology Search API server...")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
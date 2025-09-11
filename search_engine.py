"""
Search engine for ACL Anthology papers with boolean keyword support
"""
import re
from typing import List, Dict, Any, Set, Optional
from dataclasses import dataclass
from acl_anthology import Anthology
import time


@dataclass
class SearchResult:
    """Represents a search result"""
    paper_id: str
    title: str
    authors: List[str]
    year: str
    abstract: Optional[str]
    venue: List[str]
    url: str
    match_fields: List[str]  # Fields where matches were found


class BooleanSearchEngine:
    """Search engine with boolean keyword support for ACL Anthology"""
    
    def __init__(self):
        self.anthology = None
        self.papers = None
        self._load_data()
    
    def _load_data(self):
        """Load ACL Anthology data"""
        print("Loading ACL Anthology data...")
        start_time = time.time()
        self.anthology = Anthology.from_repo()
        self.papers = list(self.anthology.papers())
        load_time = time.time() - start_time
        print(f"Loaded {len(self.papers)} papers in {load_time:.2f} seconds")
    
    def _parse_boolean_query(self, query: str) -> Dict[str, Any]:
        """Parse boolean query into structured format
        
        Supports:
        - AND, OR, NOT operators
        - Parentheses for grouping
        - Quotes for exact phrases
        """
        # Simple implementation - can be enhanced
        # For now, split by AND/OR and handle NOT
        
        query = query.strip()
        if not query:
            return {"terms": [], "operators": []}
        
        # Handle quoted phrases
        phrases = re.findall(r'"([^"]*)"', query)
        for i, phrase in enumerate(phrases):
            query = query.replace(f'"{phrase}"', f"__PHRASE_{i}__")
        
        # Split by boolean operators (case insensitive)
        parts = re.split(r'\s+(AND|OR|NOT)\s+', query, flags=re.IGNORECASE)
        
        terms = []
        operators = []
        
        for i, part in enumerate(parts):
            part = part.strip()
            if part.upper() in ['AND', 'OR', 'NOT']:
                operators.append(part.upper())
            elif part:
                # Replace phrase placeholders back
                for j, phrase in enumerate(phrases):
                    part = part.replace(f"__PHRASE_{j}__", phrase)
                terms.append(part.lower())
        
        return {"terms": terms, "operators": operators, "phrases": phrases}
    
    def _extract_text_from_paper(self, paper, fields: List[str]) -> Dict[str, str]:
        """Extract text from specified fields of a paper"""
        text_data = {}
        
        if "title" in fields:
            text_data["title"] = str(paper.title).lower() if paper.title else ""
        
        if "abstract" in fields:
            text_data["abstract"] = str(paper.abstract).lower() if paper.abstract else ""
        
        if "author" in fields or "authors" in fields:
            authors = [f"{author.name.first} {author.name.last}".strip() for author in paper.authors] if paper.authors else []
            text_data["authors"] = " ".join(authors).lower()
        
        return text_data
    
    def _matches_query(self, text_data: Dict[str, str], parsed_query: Dict[str, Any]) -> tuple:
        """Check if paper matches the boolean query"""
        terms = parsed_query["terms"]
        operators = parsed_query["operators"]
        
        if not terms:
            return False, []
        
        match_results = []
        match_fields = []
        
        # Evaluate each term against all specified fields
        for term in terms:
            term_match = False
            term_fields = []
            
            for field, text in text_data.items():
                if term in text:
                    term_match = True
                    term_fields.append(field)
            
            match_results.append(term_match)
            if term_match:
                match_fields.extend(term_fields)
        
        # Apply boolean logic
        if not operators:
            # Single term or implicitly AND
            result = all(match_results)
        else:
            # Handle operators sequentially (left to right)
            result = match_results[0]
            for i, op in enumerate(operators):
                if i + 1 < len(match_results):
                    next_result = match_results[i + 1]
                    if op == "AND":
                        result = result and next_result
                    elif op == "OR":
                        result = result or next_result
                    elif op == "NOT":
                        result = result and not next_result
        
        return result, list(set(match_fields))
    
    def search(self, 
               query: str, 
               fields: List[str] = ["title", "abstract", "authors"],
               filters: Optional[Dict[str, Any]] = None,
               limit: Optional[int] = None) -> List[SearchResult]:
        """
        Search papers using boolean keywords
        
        Args:
            query: Boolean search query
            fields: Fields to search in (title, abstract, authors)
            filters: Additional filters (year_range, venue, etc.)
            limit: Maximum number of results
            
        Returns:
            List of SearchResult objects
        """
        if not query.strip():
            return []
        
        parsed_query = self._parse_boolean_query(query)
        results = []
        
        for paper in self.papers:
            # Apply filters first
            if filters:
                if not self._apply_filters(paper, filters):
                    continue
            
            # Extract text from specified fields
            text_data = self._extract_text_from_paper(paper, fields)
            
            # Check if paper matches query
            matches, match_fields = self._matches_query(text_data, parsed_query)
            
            if matches:
                result = SearchResult(
                    paper_id=paper.id,
                    title=str(paper.title),
                    authors=[f"{author.name.first} {author.name.last}".strip() for author in paper.authors] if paper.authors else [],
                    year=paper.year,
                    abstract=str(paper.abstract) if paper.abstract else None,
                    venue=paper.venue_ids if paper.venue_ids else [],
                    url=paper.web_url,
                    match_fields=match_fields
                )
                results.append(result)
                
                if limit and len(results) >= limit:
                    break
        
        return results
    
    def _apply_filters(self, paper, filters: Dict[str, Any]) -> bool:
        """Apply additional filters to paper"""
        if "year_range" in filters:
            year_min, year_max = filters["year_range"]
            try:
                paper_year = int(paper.year)
                if paper_year < year_min or paper_year > year_max:
                    return False
            except (ValueError, TypeError):
                pass
        
        if "venues" in filters and filters["venues"]:
            if not any(venue in paper.venue_ids for venue in filters["venues"]):
                return False
        
        return True
    
    def get_available_venues(self) -> Set[str]:
        """Get all available venues"""
        venues = set()
        for paper in self.papers:
            if paper.venue_ids:
                venues.update(paper.venue_ids)
        return venues
    
    def get_year_range(self) -> tuple:
        """Get the range of available years"""
        years = []
        for paper in self.papers:
            try:
                years.append(int(paper.year))
            except (ValueError, TypeError):
                pass
        return (min(years), max(years)) if years else (1950, 2025)
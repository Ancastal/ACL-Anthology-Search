
"""

Search engine for ACL Anthology papers with boolean keyword support

"""

import re

from typing import List, Dict, Any, Set, Optional

from dataclasses import dataclass

from acl_anthology import Anthology

import time

from rapidfuzz import fuzz





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
        """Parse a boolean query into postfix notation.

        Supports:
        - AND, OR, NOT operators
        - Parentheses for grouping
        - Quotes for exact phrases
        - Implicit AND between consecutive terms
        """

        query = query.strip()
        if not query:
            return {"postfix": [], "terms": [], "quoted_terms": set()}

        # Handle quoted phrases/terms for exact matching
        phrases = re.findall(r'"([^"]*)"', query)
        for i, phrase in enumerate(phrases):
            query = query.replace(f'"{phrase}"', f"__PHRASE_{i}__")
        phrase_set = {p.lower() for p in phrases}

        # Tokenize: ensure parentheses separated, then split by whitespace
        query = query.replace('(', ' ( ').replace(')', ' ) ')
        raw_tokens = [tok for tok in query.split() if tok]

        tokens: List[str] = []
        terms: List[str] = []
        quoted_terms: Set[str] = set()
        operators = {"AND", "OR", "NOT"}

        for tok in raw_tokens:
            if tok.upper() in operators:
                tokens.append(tok.upper())
            elif tok in ['(', ')']:
                tokens.append(tok)
            else:
                for j, phrase in enumerate(phrases):
                    tok = tok.replace(f"__PHRASE_{j}__", phrase)
                term = tok.lower()
                tokens.append(term)
                if term not in terms:
                    terms.append(term)
                if term in phrase_set:
                    quoted_terms.add(term)

        # Insert implicit AND between consecutive terms/parentheses
        final_tokens: List[str] = []
        prev_was_term = False
        for tok in tokens:
            if tok == '(':
                if prev_was_term:
                    final_tokens.append('AND')
                final_tokens.append(tok)
                prev_was_term = False
            elif tok == ')':
                final_tokens.append(tok)
                prev_was_term = True
            elif tok in operators:
                final_tokens.append(tok)
                prev_was_term = tok == ')'
                if tok == 'NOT':
                    prev_was_term = False
            else:
                if prev_was_term:
                    final_tokens.append('AND')
                final_tokens.append(tok)
                prev_was_term = True

        # Convert to postfix using shunting-yard algorithm
        precedence = {'NOT': 3, 'AND': 2, 'OR': 1}
        output: List[str] = []
        op_stack: List[str] = []
        for tok in final_tokens:
            if tok in operators:
                while op_stack and op_stack[-1] != '(' and precedence[op_stack[-1]] >= precedence[tok]:
                    output.append(op_stack.pop())
                op_stack.append(tok)
            elif tok == '(':
                op_stack.append(tok)
            elif tok == ')':
                while op_stack and op_stack[-1] != '(':
                    output.append(op_stack.pop())
                if op_stack and op_stack[-1] == '(':
                    op_stack.pop()
            else:
                output.append(tok)
        while op_stack:
            output.append(op_stack.pop())

        return {"postfix": output, "terms": terms, "quoted_terms": quoted_terms}

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

    


    def _matches_query(self,
                        text_data: Dict[str, str],
                        parsed_query: Dict[str, Any],
                        fuzzy: bool = False,
                        fuzzy_threshold: int = 80) -> tuple:
        """Check if paper matches the boolean query"""

        terms = parsed_query["terms"]
        postfix = parsed_query["postfix"]
        quoted_terms = parsed_query.get("quoted_terms", set())

        if not postfix:
            return False, []

        # Evaluate each unique term against provided fields
        term_results: Dict[str, tuple] = {}
        for term in terms:
            term_match = False
            term_fields: Set[str] = set()
            exact = term in quoted_terms

            for field, text in text_data.items():
                if fuzzy and not exact:
                    try:
                        if fuzz.partial_ratio(term, text) >= fuzzy_threshold:
                            term_match = True
                            term_fields.add(field)
                    except Exception:
                        pass
                else:
                    if exact:
                        pattern = rf"\b{re.escape(term)}\b"
                        if re.search(pattern, text):
                            term_match = True
                            term_fields.add(field)
                    else:
                        if term in text:
                            term_match = True
                            term_fields.add(field)

            term_results[term] = (term_match, term_fields)

        # Evaluate postfix expression
        stack: List[tuple] = []  # Each item is (bool, set(fields))
        for token in postfix:
            if token in {"AND", "OR", "NOT"}:
                if token == "NOT":
                    val, _fields = stack.pop() if stack else (False, set())
                    stack.append((not val, set()))
                else:
                    right = stack.pop() if stack else (False, set())
                    left = stack.pop() if stack else (False, set())
                    if token == "AND":
                        result = left[0] and right[0]
                        fields = left[1] | right[1] if result else set()
                    else:  # OR
                        result = left[0] or right[0]
                        fields = set()
                        if left[0]:
                            fields |= left[1]
                        if right[0]:
                            fields |= right[1]
                    stack.append((result, fields))
            else:
                stack.append(term_results.get(token, (False, set())))

        final = stack.pop() if stack else (False, set())
        return final[0], list(final[1])

    def search(self,

               query: str,

               fields: List[str] = ["title", "abstract", "authors"],

               filters: Optional[Dict[str, Any]] = None,

               limit: Optional[int] = None,

               fuzzy: bool = False,

               fuzzy_threshold: int = 80) -> List[SearchResult]:

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

            matches, match_fields = self._matches_query(

                text_data, parsed_query, fuzzy=fuzzy, fuzzy_threshold=fuzzy_threshold

            )

            

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

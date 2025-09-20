"""
arXiv search engine for academic pre-prints and papers.
Provides search functionality using the arXiv API.
"""

import time
import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import urlencode
import requests


# arXiv category code to human-readable name mapping
ARXIV_CATEGORIES = {
    # Computer Science
    'cs.AI': 'Computer Science - Artificial Intelligence',
    'cs.CL': 'Computer Science - Computation and Language',
    'cs.CV': 'Computer Science - Computer Vision and Pattern Recognition',
    'cs.LG': 'Computer Science - Machine Learning',
    'cs.NE': 'Computer Science - Neural and Evolutionary Computing',
    'cs.IR': 'Computer Science - Information Retrieval',
    'cs.HC': 'Computer Science - Human-Computer Interaction',
    'cs.RO': 'Computer Science - Robotics',
    'cs.SE': 'Computer Science - Software Engineering',
    'cs.DB': 'Computer Science - Databases',
    'cs.DS': 'Computer Science - Data Structures and Algorithms',
    'cs.CR': 'Computer Science - Cryptography and Security',
    'cs.DC': 'Computer Science - Distributed, Parallel, and Cluster Computing',
    'cs.CC': 'Computer Science - Computational Complexity',
    'cs.GT': 'Computer Science - Computer Science and Game Theory',
    'cs.IT': 'Computer Science - Information Theory',
    'cs.DM': 'Computer Science - Discrete Mathematics',
    'cs.FL': 'Computer Science - Formal Languages and Automata Theory',
    'cs.GL': 'Computer Science - General Literature',
    'cs.GR': 'Computer Science - Graphics',
    'cs.AR': 'Computer Science - Hardware Architecture',
    'cs.ET': 'Computer Science - Emerging Technologies',
    'cs.LO': 'Computer Science - Logic in Computer Science',
    'cs.MS': 'Computer Science - Mathematical Software',
    'cs.MA': 'Computer Science - Multiagent Systems',
    'cs.MM': 'Computer Science - Multimedia',
    'cs.NI': 'Computer Science - Networking and Internet Architecture',
    'cs.OH': 'Computer Science - Other Computer Science',
    'cs.OS': 'Computer Science - Operating Systems',
    'cs.PF': 'Computer Science - Performance',
    'cs.PL': 'Computer Science - Programming Languages',
    'cs.SC': 'Computer Science - Symbolic Computation',
    'cs.SD': 'Computer Science - Sound',
    'cs.SY': 'Computer Science - Systems and Control',

    # Statistics
    'stat.AP': 'Statistics - Applications',
    'stat.CO': 'Statistics - Computation',
    'stat.ML': 'Statistics - Machine Learning',
    'stat.ME': 'Statistics - Methodology',
    'stat.OT': 'Statistics - Other Statistics',
    'stat.TH': 'Statistics - Theory',

    # Mathematics
    'math.CO': 'Mathematics - Combinatorics',
    'math.LO': 'Mathematics - Logic',
    'math.PR': 'Mathematics - Probability',
    'math.ST': 'Mathematics - Statistics Theory',
    'math.IT': 'Mathematics - Information Theory',
    'math.NA': 'Mathematics - Numerical Analysis',
    'math.OC': 'Mathematics - Optimization and Control',
    'math.DS': 'Mathematics - Dynamical Systems',
    'math.GT': 'Mathematics - Geometric Topology',
    'math.GR': 'Mathematics - Group Theory',
    'math.AC': 'Mathematics - Commutative Algebra',
    'math.AG': 'Mathematics - Algebraic Geometry',
    'math.AT': 'Mathematics - Algebraic Topology',
    'math.CT': 'Mathematics - Category Theory',
    'math.CV': 'Mathematics - Complex Variables',
    'math.DG': 'Mathematics - Differential Geometry',
    'math.FA': 'Mathematics - Functional Analysis',
    'math.GM': 'Mathematics - General Mathematics',
    'math.HO': 'Mathematics - History and Overview',
    'math.KT': 'Mathematics - K-Theory and Homology',
    'math.MG': 'Mathematics - Metric Geometry',
    'math.MP': 'Mathematics - Mathematical Physics',
    'math.NT': 'Mathematics - Number Theory',
    'math.QA': 'Mathematics - Quantum Algebra',
    'math.RA': 'Mathematics - Rings and Algebras',
    'math.RT': 'Mathematics - Representation Theory',
    'math.SG': 'Mathematics - Symplectic Geometry',
    'math.SP': 'Mathematics - Spectral Theory',

    # Physics
    'physics.comp-ph': 'Physics - Computational Physics',
    'physics.data-an': 'Physics - Data Analysis, Statistics and Probability',
    'physics.ed-ph': 'Physics - Physics Education',
    'physics.soc-ph': 'Physics - Physics and Society',

    # Economics
    'econ.EM': 'Economics - Econometrics',
    'econ.GN': 'Economics - General Economics',
    'econ.TH': 'Economics - Theoretical Economics',

    # Quantitative Biology
    'q-bio.BM': 'Quantitative Biology - Biomolecules',
    'q-bio.CB': 'Quantitative Biology - Cell Behavior',
    'q-bio.GN': 'Quantitative Biology - Genomics',
    'q-bio.MN': 'Quantitative Biology - Molecular Networks',
    'q-bio.NC': 'Quantitative Biology - Neurons and Cognition',
    'q-bio.OT': 'Quantitative Biology - Other Quantitative Biology',
    'q-bio.PE': 'Quantitative Biology - Populations and Evolution',
    'q-bio.QM': 'Quantitative Biology - Quantitative Methods',
    'q-bio.SC': 'Quantitative Biology - Subcellular Processes',
    'q-bio.TO': 'Quantitative Biology - Tissues and Organs',

    # Quantitative Finance
    'q-fin.CP': 'Quantitative Finance - Computational Finance',
    'q-fin.EC': 'Quantitative Finance - Economics',
    'q-fin.GN': 'Quantitative Finance - General Finance',
    'q-fin.MF': 'Quantitative Finance - Mathematical Finance',
    'q-fin.PM': 'Quantitative Finance - Portfolio Management',
    'q-fin.PR': 'Quantitative Finance - Pricing of Securities',
    'q-fin.RM': 'Quantitative Finance - Risk Management',
    'q-fin.ST': 'Quantitative Finance - Statistical Finance',
    'q-fin.TR': 'Quantitative Finance - Trading and Market Microstructure',

    # Legacy categories (some older arXiv papers still use these)
    'cmp-lg': 'Computation and Language',
    'cs': 'Computer Science',
    'math': 'Mathematics',
    'physics': 'Physics',
    'astro-ph': 'Astrophysics',
    'cond-mat': 'Condensed Matter',
    'gr-qc': 'General Relativity and Quantum Cosmology',
    'hep-ex': 'High Energy Physics - Experiment',
    'hep-lat': 'High Energy Physics - Lattice',
    'hep-ph': 'High Energy Physics - Phenomenology',
    'hep-th': 'High Energy Physics - Theory',
    'math-ph': 'Mathematical Physics',
    'nlin': 'Nonlinear Sciences',
    'nucl-ex': 'Nuclear Experiment',
    'nucl-th': 'Nuclear Theory',
    'quant-ph': 'Quantum Physics',

    # Condensed Matter subcategories
    'cond-mat.dis-nn': 'Condensed Matter - Disordered Systems and Neural Networks',
    'cond-mat.mes-hall': 'Condensed Matter - Mesoscale and Nanoscale Physics',
    'cond-mat.mtrl-sci': 'Condensed Matter - Materials Science',
    'cond-mat.other': 'Condensed Matter - Other Condensed Matter',
    'cond-mat.quant-gas': 'Condensed Matter - Quantum Gases',
    'cond-mat.soft': 'Condensed Matter - Soft Condensed Matter',
    'cond-mat.stat-mech': 'Condensed Matter - Statistical Mechanics',
    'cond-mat.str-el': 'Condensed Matter - Strongly Correlated Electrons',
    'cond-mat.supr-con': 'Condensed Matter - Superconductivity',

    # General categories as fallbacks
    'q-bio': 'Quantitative Biology',
    'q-fin': 'Quantitative Finance',
}


@dataclass
class ArxivSearchResult:
    """Represents an arXiv search result"""
    paper_id: str  # arXiv ID
    title: str
    authors: List[str]
    year: str
    abstract: Optional[str]
    venue: List[str]  # arXiv categories
    url: str
    match_fields: List[str] = None
    doi: Optional[str] = None
    score: Optional[float] = None
    source: str = "arXiv"


def convert_arxiv_categories(categories: List[str]) -> List[str]:
    """Convert arXiv category codes to human-readable names"""
    converted = []
    for cat in categories:
        readable_name = ARXIV_CATEGORIES.get(cat, cat)  # Fall back to original code if not found
        converted.append(readable_name)
    return converted


class ArxivSearchEngine:
    """Search engine for arXiv with rate limiting"""

    def __init__(self, request_delay: float = 1.0, max_results_per_query: int = 100):
        self.request_delay = request_delay
        self.max_results_per_query = max_results_per_query
        self.last_request_time = 0.0
        self.base_url = "http://export.arxiv.org/api/query"

    def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        self.last_request_time = time.time()

    def search(self, query: str, fields: List[str] = None, filters: Dict[str, Any] = None,
               limit: int = 20, **kwargs) -> List[ArxivSearchResult]:
        """
        Search arXiv for papers

        Args:
            query: Search query string
            fields: Search fields (title, abstract, authors, all)
            filters: Search filters (year_range, categories)
            limit: Maximum number of results
            **kwargs: Additional search options

        Returns:
            List of ArxivSearchResult objects
        """
        if not query.strip():
            return []

        try:
            self._rate_limit()

            # Build arXiv search query
            arxiv_query = self._build_arxiv_query(query, fields, filters)

            # Set up request parameters
            params = {
                'search_query': arxiv_query,
                'start': 0,
                'max_results': min(limit, self.max_results_per_query),
                'sortBy': 'relevance',
                'sortOrder': 'descending'
            }

            # Make request to arXiv API
            url = f"{self.base_url}?{urlencode(params)}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Parse XML response
            results = self._parse_arxiv_response(response.text, query)
            return results[:limit]

        except Exception as e:
            print(f"arXiv search failed: {e}")
            return []

    def _build_arxiv_query(self, query: str, fields: List[str] = None, filters: Dict[str, Any] = None) -> str:
        """Build arXiv API search query"""
        # Convert boolean query to arXiv format (but don't URL encode yet)
        arxiv_query = self._convert_boolean_to_arxiv_logical(query)

        # Default to searching all fields if none specified
        if not fields or "all" in fields:
            search_query = f"all:({arxiv_query})"
        else:
            # Map our field names to arXiv field names
            field_mapping = {
                'title': 'ti',
                'abstract': 'abs',
                'authors': 'au'
            }

            # Build query for specific fields
            field_queries = []
            for field in fields:
                if field in field_mapping:
                    field_queries.append(f"{field_mapping[field]}:({arxiv_query})")

            if field_queries:
                search_query = " OR ".join(field_queries)
            else:
                search_query = f"all:({arxiv_query})"

        # Add filters - wrap main query in parentheses if we have filters and multiple field queries
        if filters:
            # Check if we need to wrap the main query
            has_filters = False

            # Add category filter
            categories = filters.get('categories', [])
            if categories:
                cat_queries = [f"cat:{cat}" for cat in categories]
                if " OR " in search_query:  # Multiple field queries
                    search_query = f"({search_query})"
                search_query += " AND (" + " OR ".join(cat_queries) + ")"
                has_filters = True

            # Add year filter (arXiv uses date ranges)
            year_range = filters.get('year_range')
            if year_range and len(year_range) == 2:
                start_year, end_year = year_range
                if " OR " in search_query and not has_filters:  # Multiple field queries, first filter
                    search_query = f"({search_query})"
                # arXiv date format: YYYYMMDD
                search_query += f" AND submittedDate:[{start_year}0101 TO {end_year}1231]"

        return search_query

    def _convert_boolean_to_arxiv_logical(self, query: str) -> str:
        """Convert boolean query syntax to arXiv logical format (no URL encoding)"""
        # Clean up extra spaces first
        query = re.sub(r'\s+', ' ', query.strip())

        # Convert NOT to ANDNOT
        query = re.sub(r'\bNOT\s+', 'ANDNOT ', query, flags=re.IGNORECASE)

        # Ensure operators are uppercase
        query = re.sub(r'\band\b', 'AND', query, flags=re.IGNORECASE)
        query = re.sub(r'\bor\b', 'OR', query, flags=re.IGNORECASE)
        query = re.sub(r'\bandnot\b', 'ANDNOT', query, flags=re.IGNORECASE)

        # Clean up spaces around parentheses
        query = re.sub(r'\(\s+', '(', query)
        query = re.sub(r'\s+\)', ')', query)

        return query.strip()

    def _parse_arxiv_response(self, xml_content: str, original_query: str) -> List[ArxivSearchResult]:
        """Parse arXiv API XML response"""
        results = []

        try:
            # Parse XML
            root = ET.fromstring(xml_content)

            # Define namespaces
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }

            # Find all entry elements
            entries = root.findall('atom:entry', namespaces)

            for entry in entries:
                try:
                    result = self._parse_entry(entry, namespaces, original_query)
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"Error parsing arXiv entry: {e}")
                    continue

        except Exception as e:
            print(f"Error parsing arXiv XML: {e}")

        return results

    def _parse_entry(self, entry: ET.Element, namespaces: Dict[str, str], original_query: str) -> Optional[ArxivSearchResult]:
        """Parse a single arXiv entry"""
        try:
            # Extract ID
            id_elem = entry.find('atom:id', namespaces)
            if id_elem is None:
                return None

            paper_id = id_elem.text.split('/')[-1]  # Extract arXiv ID from URL

            # Extract title
            title_elem = entry.find('atom:title', namespaces)
            title = title_elem.text.strip() if title_elem is not None else ""
            if not title:
                return None

            # Extract authors
            authors = []
            author_elems = entry.findall('atom:author', namespaces)
            for author_elem in author_elems:
                name_elem = author_elem.find('atom:name', namespaces)
                if name_elem is not None:
                    authors.append(name_elem.text.strip())

            # Extract abstract
            summary_elem = entry.find('atom:summary', namespaces)
            abstract = summary_elem.text.strip() if summary_elem is not None else None

            # Extract publication date and year
            published_elem = entry.find('atom:published', namespaces)
            year = ""
            if published_elem is not None:
                # Format: 2023-10-15T17:59:59Z
                date_str = published_elem.text
                year_match = re.search(r'(\d{4})', date_str)
                if year_match:
                    year = year_match.group(1)

            # Extract categories (subjects)
            categories = []
            category_elems = entry.findall('atom:category', namespaces)
            for cat_elem in category_elems:
                term = cat_elem.get('term')
                if term:
                    categories.append(term)

            # Extract DOI if available
            doi = None
            arxiv_doi_elem = entry.find('arxiv:doi', namespaces)
            if arxiv_doi_elem is not None:
                doi = arxiv_doi_elem.text.strip()

            # Build URL
            url = f"https://arxiv.org/abs/{paper_id}"

            # Calculate relevance score
            score = self._calculate_relevance_score(title, abstract or '', original_query)

            return ArxivSearchResult(
                paper_id=paper_id,
                title=title,
                authors=authors,
                year=year,
                abstract=abstract,
                venue=convert_arxiv_categories(categories),
                url=url,
                match_fields=['title', 'abstract'],  # arXiv searches both by default
                doi=doi,
                score=score,
                source="arXiv"
            )

        except Exception as e:
            print(f"Error parsing arXiv entry: {e}")
            return None

    def _calculate_relevance_score(self, title: str, abstract: str, query: str) -> float:
        """Calculate simple relevance score based on query term matches"""
        if not query:
            return 0.0

        # Normalize text
        title_norm = title.lower()
        abstract_norm = abstract.lower() if abstract else ''
        query_norm = query.lower()

        # Extract query terms (simple tokenization)
        query_terms = []
        for term in re.findall(r'\b\w+\b', query_norm):
            if len(term) > 2:  # Skip very short terms
                query_terms.append(term)

        if not query_terms:
            return 0.0

        # Count matches
        title_matches = sum(1 for term in query_terms if term in title_norm)
        abstract_matches = sum(1 for term in query_terms if term in abstract_norm)

        # Weight title matches higher than abstract matches
        score = (title_matches * 2.0 + abstract_matches * 1.0) / len(query_terms)

        # Normalize to 0-1 range
        return min(score, 1.0)

    def get_stats(self) -> Dict[str, Any]:
        """Get search engine statistics"""
        return {
            "engine": "arXiv",
            "total_papers": "2M+ (Dynamic)",
            "year_range": [1991, 2024],
            "coverage": "Physics, Mathematics, Computer Science, Biology, Finance, Statistics",
            "source": "arXiv.org"
        }
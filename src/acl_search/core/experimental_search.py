"""
Experimental Search Pipeline

A modern IR pipeline with:
1. Spell correction & query expansion
2. BM25 + fuzzy matching retrieval
3. Embedding-based semantic retrieval
4. Neural re-ranking

This is an experimental alternative to the standard boolean search,
designed to showcase state-of-the-art information retrieval techniques.
"""

import re
import time
from typing import List, Dict, Any, Set, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import math

from acl_anthology import Anthology
from rapidfuzz import fuzz
from .search_engine import SearchResult

# Optional imports for experimental features
try:
    from spellchecker import SpellChecker
    SPELLCHECKER_AVAILABLE = True
except ImportError:
    SPELLCHECKER_AVAILABLE = False
    print("⚠️  SpellChecker not available. Install with: pip install pyspellchecker")

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    print("⚠️  BM25 not available. Install with: pip install rank-bm25")

try:
    from sentence_transformers import SentenceTransformer
    import torch
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("⚠️  SentenceTransformers not available. Install with: pip install sentence-transformers")

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    RERANKING_AVAILABLE = True
except ImportError:
    RERANKING_AVAILABLE = False
    print("⚠️  Transformers not available for re-ranking. Install with: pip install transformers")


@dataclass
class ExperimentalSearchResult(SearchResult):
    """Extended search result with experimental features"""
    bm25_score: Optional[float] = None
    semantic_score: Optional[float] = None
    rerank_score: Optional[float] = None
    pipeline_stage: Optional[str] = None  # Which stage found this result


class ExperimentalSearchEngine:
    """
    Experimental search engine implementing modern IR techniques:

    Pipeline:
    1. Query preprocessing (spell correction, expansion)
    2. BM25 + fuzzy retrieval
    3. Semantic embedding retrieval
    4. Neural re-ranking
    """

    def __init__(self, anthology: Anthology):
        self.anthology = anthology
        self.papers = []
        self._initialize_index()

        # Initialize components
        self.spell_checker = None
        self.bm25_index = None
        self.embedding_model = None
        self.rerank_model = None
        self.rerank_tokenizer = None

        # Query expansion vocabulary
        self.acronym_expansions = {
            'ml': 'machine learning',
            'nlp': 'natural language processing',
            'ai': 'artificial intelligence',
            'llm': 'large language model',
            'llms': 'large language models',
            'bert': 'bidirectional encoder representations transformers',
            'gpt': 'generative pre-trained transformer',
            'rnn': 'recurrent neural network',
            'cnn': 'convolutional neural network',
            'lstm': 'long short-term memory',
            'gan': 'generative adversarial network',
            'rl': 'reinforcement learning',
            'cv': 'computer vision',
            'asr': 'automatic speech recognition',
            'tts': 'text to speech',
            'mt': 'machine translation',
            'qa': 'question answering',
            'ner': 'named entity recognition',
            'pos': 'part of speech',
            'ir': 'information retrieval'
        }

        self._load_models()

    def _initialize_index(self):
        """Initialize paper index for search"""
        print("🔄 Initializing experimental search index...")

        for paper in self.anthology.papers():
            # Extract paper data
            title = str(paper.title) if paper.title else ""
            abstract = str(paper.abstract) if paper.abstract else ""
            authors = [f"{author.name.first} {author.name.last}".strip() for author in paper.authors] if paper.authors else []
            venue_names = paper.venue_ids if paper.venue_ids else []
            year = str(paper.year) if paper.year else ""

            self.papers.append({
                'id': paper.full_id,
                'title': title,
                'abstract': abstract,
                'authors': authors,
                'venue': venue_names,
                'year': year,
                'url': paper.web_url,
                'text_content': f"{title} {abstract} {' '.join(authors)}".lower()
            })

        print(f"✅ Indexed {len(self.papers)} papers for experimental search")

    def _load_models(self):
        """Load ML models for experimental features"""
        print("🔄 Loading experimental search models...")

        # Load spell checker
        if SPELLCHECKER_AVAILABLE:
            try:
                self.spell_checker = SpellChecker()
                print("✅ Spell checker loaded")
            except Exception as e:
                print(f"⚠️  Could not load spell checker: {e}")

        # Initialize BM25 index
        if BM25_AVAILABLE:
            try:
                corpus = [paper['text_content'].split() for paper in self.papers]
                self.bm25_index = BM25Okapi(corpus)
                print("✅ BM25 index created")
            except Exception as e:
                print(f"⚠️  Could not create BM25 index: {e}")

        # Load embedding model
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                print("✅ Embedding model loaded")
            except Exception as e:
                print(f"⚠️  Could not load embedding model: {e}")

        # Load re-ranking model
        if RERANKING_AVAILABLE:
            try:
                model_name = 'cross-encoder/ms-marco-MiniLM-L-6-v2'
                self.rerank_tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.rerank_model = AutoModelForSequenceClassification.from_pretrained(model_name)
                print("✅ Re-ranking model loaded")
            except Exception as e:
                print(f"⚠️  Could not load re-ranking model: {e}")

    def spell_correct_and_expand(self, query: str) -> str:
        """
        Step 1: Spell correction and query expansion
        """
        if not query.strip():
            return query

        expanded_terms = []
        words = re.findall(r'\b\w+\b', query.lower())

        for word in words:
            # Check for acronym expansion
            if word in self.acronym_expansions:
                expanded_terms.append(f"({word} OR {self.acronym_expansions[word]})")
                continue

            # Spell correction
            if self.spell_checker and word not in self.spell_checker:
                corrected = self.spell_checker.correction(word)
                if corrected and corrected != word:
                    expanded_terms.append(f"({word} OR {corrected})")
                    continue

            expanded_terms.append(word)

        # Preserve original query structure while expanding
        expanded_query = query
        for i, word in enumerate(words):
            if i < len(expanded_terms) and expanded_terms[i] != word:
                expanded_query = expanded_query.replace(word, expanded_terms[i], 1)

        return expanded_query

    def bm25_fuzzy_retrieve(self, query: str, limit: int = 100) -> List[Tuple[int, float]]:
        """
        Step 2: BM25 + fuzzy matching retrieval
        Returns list of (paper_index, score) tuples
        """
        candidates = []

        # BM25 retrieval
        if self.bm25_index:
            query_tokens = query.lower().split()
            bm25_scores = self.bm25_index.get_scores(query_tokens)

            for idx, score in enumerate(bm25_scores):
                if score > 0:
                    candidates.append((idx, score, 'bm25'))

        # Fuzzy matching fallback/enhancement
        query_lower = query.lower()
        for idx, paper in enumerate(self.papers):
            # Skip if already found by BM25
            if any(cand[0] == idx for cand in candidates):
                continue

            # Fuzzy match against title and abstract
            title_score = fuzz.partial_ratio(query_lower, paper['title'].lower())
            abstract_score = fuzz.partial_ratio(query_lower, paper['abstract'].lower()) if paper['abstract'] else 0

            # Combined fuzzy score
            fuzzy_score = max(title_score, abstract_score * 0.8)

            if fuzzy_score > 60:  # Threshold for fuzzy matching
                candidates.append((idx, fuzzy_score / 100.0, 'fuzzy'))

        # Sort by score and return top candidates
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:limit]

    def embedding_retrieve(self, query: str, limit: int = 50) -> List[Tuple[int, float]]:
        """
        Step 3: Semantic embedding retrieval
        Returns list of (paper_index, similarity_score) tuples
        """
        if not self.embedding_model:
            return []

        try:
            # Encode query
            query_embedding = self.embedding_model.encode([query])

            # For efficiency, we'll compute embeddings on-demand for a subset
            # In production, these would be pre-computed and stored
            candidates = []

            # Sample papers for semantic search (can be optimized with vector DB)
            for idx, paper in enumerate(self.papers[:1000]):  # Limit for demo
                text = f"{paper['title']} {paper['abstract'][:200]}"  # Truncate abstract
                paper_embedding = self.embedding_model.encode([text])

                # Cosine similarity
                similarity = torch.cosine_similarity(
                    torch.tensor(query_embedding),
                    torch.tensor(paper_embedding)
                )[0].item()

                if similarity > 0.3:  # Threshold for semantic similarity
                    candidates.append((idx, similarity, 'semantic'))

            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[:limit]

        except Exception as e:
            print(f"Embedding retrieval failed: {e}")
            return []

    def neural_rerank(self, candidates: List[Tuple[int, float, str]], query: str, limit: int = 20) -> List[ExperimentalSearchResult]:
        """
        Step 4: Neural re-ranking of candidates
        """
        if not self.rerank_model or not candidates:
            # Fallback to original ranking
            return self._convert_candidates_to_results(candidates[:limit])

        try:
            # Prepare inputs for re-ranking
            rerank_inputs = []
            candidate_papers = []

            for idx, score, stage in candidates[:50]:  # Re-rank top 50
                paper = self.papers[idx]
                text = f"{paper['title']} {paper['abstract'][:300]}"  # Limit text length
                rerank_inputs.append([query, text])
                candidate_papers.append((idx, score, stage))

            # Get re-ranking scores
            with torch.no_grad():
                inputs = self.rerank_tokenizer(
                    rerank_inputs,
                    padding=True,
                    truncation=True,
                    return_tensors='pt',
                    max_length=512
                )
                outputs = self.rerank_model(**inputs)
                rerank_scores = torch.softmax(outputs.logits, dim=-1)[:, 1].tolist()

            # Combine with original scores and re-sort
            reranked = []
            for i, (idx, orig_score, stage) in enumerate(candidate_papers):
                final_score = rerank_scores[i] * 0.7 + orig_score * 0.3  # Weighted combination
                reranked.append((idx, final_score, stage, rerank_scores[i]))

            reranked.sort(key=lambda x: x[1], reverse=True)

            # Convert to results
            results = []
            for idx, final_score, stage, rerank_score in reranked[:limit]:
                paper = self.papers[idx]
                result = ExperimentalSearchResult(
                    paper_id=paper['id'],
                    title=paper['title'],
                    authors=paper['authors'],
                    year=paper['year'],
                    abstract=paper['abstract'],
                    venue=paper['venue'],
                    url=paper['url'],
                    match_fields=['title', 'abstract'],
                    score=final_score,
                    rerank_score=rerank_score,
                    pipeline_stage=stage
                )
                results.append(result)

            return results

        except Exception as e:
            print(f"Neural re-ranking failed: {e}")
            return self._convert_candidates_to_results(candidates[:limit])

    def _convert_candidates_to_results(self, candidates: List[Tuple[int, float, str]]) -> List[ExperimentalSearchResult]:
        """Convert candidate tuples to SearchResult objects"""
        results = []
        for idx, score, stage in candidates:
            paper = self.papers[idx]
            result = ExperimentalSearchResult(
                paper_id=paper['id'],
                title=paper['title'],
                authors=paper['authors'],
                year=paper['year'],
                abstract=paper['abstract'],
                venue=paper['venue'],
                url=paper['url'],
                match_fields=['title', 'abstract'],
                score=score,
                pipeline_stage=stage
            )
            results.append(result)
        return results

    def search(self, query: str, fields: List[str] = None, filters: Dict[str, Any] = None,
               limit: int = 20, **kwargs) -> List[ExperimentalSearchResult]:
        """
        Main experimental search method implementing the 4-stage pipeline
        """
        if not query.strip():
            return []

        start_time = time.time()

        # Stage 1: Spell correction and query expansion
        expanded_query = self.spell_correct_and_expand(query)

        # Stage 2: BM25 + fuzzy retrieval
        bm25_candidates = self.bm25_fuzzy_retrieve(expanded_query, limit * 3)

        # Stage 3: Embedding-based retrieval
        semantic_candidates = self.embedding_retrieve(query, limit * 2)

        # Merge candidates (avoid duplicates)
        all_candidates = {}

        # Add BM25/fuzzy candidates
        for idx, score, stage in bm25_candidates:
            all_candidates[idx] = (score, stage)

        # Add semantic candidates (boost score if already present)
        for idx, score, stage in semantic_candidates:
            if idx in all_candidates:
                # Combine scores if found by multiple methods
                orig_score, orig_stage = all_candidates[idx]
                combined_score = orig_score * 0.6 + score * 0.4
                all_candidates[idx] = (combined_score, f"{orig_stage}+{stage}")
            else:
                all_candidates[idx] = (score, stage)

        # Convert to candidate list
        merged_candidates = [(idx, score, stage) for idx, (score, stage) in all_candidates.items()]

        # Stage 4: Neural re-ranking
        final_results = self.neural_rerank(merged_candidates, query, limit)

        # Apply filters if provided
        if filters:
            final_results = self._apply_filters(final_results, filters)

        search_time = time.time() - start_time
        print(f"🔬 Experimental search completed in {search_time:.3f}s")

        return final_results[:limit]

    def _apply_filters(self, results: List[ExperimentalSearchResult], filters: Dict[str, Any]) -> List[ExperimentalSearchResult]:
        """Apply search filters to results"""
        filtered = results

        # Year range filter
        if 'year_range' in filters and filters['year_range']:
            start_year, end_year = filters['year_range']
            filtered = [r for r in filtered if start_year <= int(r.year or 0) <= end_year]

        # Venue filter
        if 'venues' in filters and filters['venues']:
            venue_set = set(v.lower() for v in filters['venues'])
            filtered = [r for r in filtered if any(v.lower() in venue_set for v in r.venue)]

        return filtered

    def get_stats(self) -> Dict[str, Any]:
        """Get search engine statistics"""
        return {
            "engine": "Experimental IR Pipeline",
            "total_papers": len(self.papers),
            "features": {
                "spell_correction": SPELLCHECKER_AVAILABLE,
                "bm25_retrieval": BM25_AVAILABLE,
                "semantic_search": EMBEDDINGS_AVAILABLE,
                "neural_reranking": RERANKING_AVAILABLE
            },
            "pipeline_stages": 4
        }
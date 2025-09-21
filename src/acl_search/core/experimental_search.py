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

# Language detection
try:
    from langdetect import detect, LangDetectError
    LANGUAGE_DETECTION_AVAILABLE = True
except ImportError:
    LANGUAGE_DETECTION_AVAILABLE = False
    print("⚠️  Language detection not available. Install with: pip install langdetect")

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

    def _is_english_or_italian(self, text: str) -> bool:
        """
        Check if text is primarily in English or Italian
        """
        if not LANGUAGE_DETECTION_AVAILABLE or not text or len(text.strip()) < 10:
            return True  # Default to include if we can't detect or text is too short

        try:
            # Clean text for language detection
            clean_text = re.sub(r'[^\w\s]', ' ', text)
            clean_text = ' '.join(clean_text.split()[:100])  # Limit to first 100 words for speed

            if len(clean_text.strip()) < 5:
                return True

            detected_lang = detect(clean_text)
            return detected_lang in ['en', 'it']
        except (LangDetectError, Exception):
            return True  # Default to include if detection fails

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
        Step 2: BM25 + fuzzy matching retrieval (optimized)
        Returns list of (paper_index, score) tuples
        """
        import random
        candidates = []
        found_indices = set()  # O(1) lookup for candidate tracking

        # BM25 retrieval - only extract top scoring papers
        if self.bm25_index:
            query_tokens = query.lower().split()
            bm25_scores = self.bm25_index.get_scores(query_tokens)

            # Create list of (index, score) pairs and sort by score
            scored_papers = [(idx, score) for idx, score in enumerate(bm25_scores) if score > 0]
            scored_papers.sort(key=lambda x: x[1], reverse=True)

            # Take only top BM25 results (much faster than processing all)
            top_bm25_limit = min(limit * 2, len(scored_papers))  # At most 2x the final limit
            for idx, score in scored_papers[:top_bm25_limit]:
                candidates.append((idx, score, 'bm25'))
                found_indices.add(idx)

        # Early termination check
        if len(candidates) >= limit:
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[:limit]

        # Fuzzy matching on a sample - much faster than checking all papers
        query_lower = query.lower()
        remaining_needed = limit - len(candidates)

        # Sample papers for fuzzy matching (instead of checking all 113k papers)
        sample_size = min(3000, len(self.papers))  # Only check 3k papers max
        paper_indices = list(range(len(self.papers)))
        sampled_indices = random.sample(paper_indices, sample_size)

        fuzzy_candidates_found = 0
        max_fuzzy_candidates = remaining_needed * 3  # Allow some buffer

        for idx in sampled_indices:
            # Skip if already found by BM25
            if idx in found_indices:
                continue

            # Early termination for fuzzy matching
            if fuzzy_candidates_found >= max_fuzzy_candidates:
                break

            paper = self.papers[idx]

            # Fuzzy match against title and abstract
            title_score = fuzz.partial_ratio(query_lower, paper['title'].lower())
            abstract_score = fuzz.partial_ratio(query_lower, paper['abstract'].lower()) if paper['abstract'] else 0

            # Combined fuzzy score
            fuzzy_score = max(title_score, abstract_score * 0.8)

            if fuzzy_score > 60:  # Threshold for fuzzy matching
                candidates.append((idx, fuzzy_score / 100.0, 'fuzzy'))
                found_indices.add(idx)
                fuzzy_candidates_found += 1

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
            for idx, paper in enumerate(self.papers[:200]):  # Further reduced for performance
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

            for idx, score, stage in candidates[:20]:  # Re-rank top 20 for performance
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

        total_start = time.time()
        print(f"🔬 Starting experimental search for: '{query}'")

        # Stage 1: Spell correction and query expansion
        stage1_start = time.time()
        expanded_query = self.spell_correct_and_expand(query)
        stage1_time = time.time() - stage1_start
        print(f"  📝 Stage 1 (Spell correction & expansion): {stage1_time:.3f}s")
        if expanded_query != query:
            print(f"     Query expanded: '{query}' → '{expanded_query}'")

        # Stage 2: BM25 + fuzzy retrieval
        stage2_start = time.time()
        bm25_candidates = self.bm25_fuzzy_retrieve(expanded_query, limit * 3)
        stage2_time = time.time() - stage2_start
        print(f"  🔍 Stage 2 (BM25 + fuzzy retrieval): {stage2_time:.3f}s → {len(bm25_candidates)} candidates")

        # Stage 3: Embedding-based retrieval
        stage3_start = time.time()
        semantic_candidates = self.embedding_retrieve(query, limit * 2)
        stage3_time = time.time() - stage3_start
        print(f"  🧠 Stage 3 (Semantic embedding retrieval): {stage3_time:.3f}s → {len(semantic_candidates)} candidates")

        # Merge candidates (avoid duplicates)
        merge_start = time.time()
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
        merge_time = time.time() - merge_start
        print(f"  🔗 Candidate merging: {merge_time:.3f}s → {len(merged_candidates)} total candidates")

        # Stage 4: Neural re-ranking
        stage4_start = time.time()
        final_results = self.neural_rerank(merged_candidates, query, limit * 2)  # Get more for language filtering
        stage4_time = time.time() - stage4_start
        print(f"  🎯 Stage 4 (Neural re-ranking): {stage4_time:.3f}s → {len(final_results)} final results")

        # Apply filters if provided
        if filters:
            filter_start = time.time()
            final_results = self._apply_filters(final_results, filters)
            filter_time = time.time() - filter_start
            print(f"  🔧 Filter application: {filter_time:.3f}s → {len(final_results)} filtered results")

        # Language filtering - exclude non-English/Italian papers
        lang_filter_start = time.time()
        before_lang_filter = len(final_results)
        language_filtered_results = []
        excluded_count = 0

        for result in final_results:
            title_text = result.title or ""
            abstract_text = result.abstract or ""

            # Check if title or abstract is primarily English or Italian
            title_ok = self._is_english_or_italian(title_text)
            abstract_ok = self._is_english_or_italian(abstract_text) if abstract_text else True

            if title_ok and abstract_ok:
                language_filtered_results.append(result)
            else:
                excluded_count += 1

        lang_filter_time = time.time() - lang_filter_start
        print(f"  🌐 Language filtering: {lang_filter_time:.3f}s → {len(language_filtered_results)} results, {excluded_count} excluded (non-English/Italian)")

        total_time = time.time() - total_start
        print(f"🔬 Experimental search completed in {total_time:.3f}s")

        return language_filtered_results[:limit]

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
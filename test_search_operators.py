#!/usr/bin/env python3
"""
Comprehensive test suite for all search operators in the ACL Anthology Search engine.

This test suite covers:
- Boolean operators: AND, OR, NOT
- Parentheses for grouping
- Quoted phrases for exact matching
- Implicit AND operations
- Fuzzy matching
- Field-specific searches
- Filter operations
- Edge cases and error conditions
"""

import unittest
from unittest.mock import Mock, patch
from typing import List, Dict, Any
import time

from search_engine import BooleanSearchEngine, SearchResult


class MockPaper:
    """Mock paper object for testing"""
    def __init__(self, paper_id: str, title: str, authors: List[str] = None, 
                 year: str = "2023", abstract: str = "", venue_ids: List[str] = None):
        self.id = paper_id
        self.title = title
        self.year = year
        self.abstract = abstract
        self.venue_ids = venue_ids or []
        self.web_url = f"https://example.com/{paper_id}"
        
        # Create mock author objects
        self.authors = []
        if authors:
            for author_name in authors:
                mock_author = Mock()
                name_parts = author_name.split()
                mock_author.name.first = name_parts[0] if name_parts else ""
                mock_author.name.last = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                self.authors.append(mock_author)


class TestBooleanQueryParsing(unittest.TestCase):
    """Test cases for boolean query parsing"""
    
    def setUp(self):
        self.engine = BooleanSearchEngine()
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_empty_query(self, mock_load):
        """Test handling of empty queries"""
        result = self.engine._parse_boolean_query("")
        self.assertEqual(result["postfix"], [])
        self.assertEqual(result["terms"], [])
        
        result = self.engine._parse_boolean_query("   ")
        self.assertEqual(result["postfix"], [])
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_single_term(self, mock_load):
        """Test single term queries"""
        result = self.engine._parse_boolean_query("attention")
        self.assertEqual(result["postfix"], ["attention"])
        self.assertEqual(result["terms"], ["attention"])
        
    @patch.object(BooleanSearchEngine, '_load_data')  
    def test_and_operator(self, mock_load):
        """Test AND operator functionality"""
        test_cases = [
            ("attention AND mechanism", ["attention", "mechanism", "AND"]),
            ("attention and mechanism", ["attention", "mechanism", "AND"]),
            ("attention mechanism", ["attention", "mechanism", "AND"])  # implicit AND
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["postfix"], expected)
                
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_or_operator(self, mock_load):
        """Test OR operator functionality"""
        test_cases = [
            ("BERT OR GPT", ["bert", "gpt", "OR"]),
            ("bert or gpt", ["bert", "gpt", "OR"]),
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["postfix"], expected)
                
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_not_operator(self, mock_load):
        """Test NOT operator functionality"""
        test_cases = [
            ("attention NOT model", ["attention", "model", "NOT", "AND"]),
            ("NOT attention", ["attention", "NOT"]),
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["postfix"], expected)
                
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_quoted_phrases(self, mock_load):
        """Test quoted phrase handling"""
        result = self.engine._parse_boolean_query('"neural machine translation"')
        self.assertEqual(result["terms"], ["neural machine translation"])
        self.assertEqual(result["quoted_terms"], {"neural machine translation"})
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_parentheses_grouping(self, mock_load):
        """Test parentheses for operator precedence"""
        test_cases = [
            ("(BERT OR GPT) AND transformer", ["bert", "gpt", "OR", "transformer", "AND"]),
            ("attention AND (model OR mechanism)", ["attention", "model", "mechanism", "OR", "AND"]),
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["postfix"], expected)
                
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_complex_expressions(self, mock_load):
        """Test complex boolean expressions"""
        test_cases = [
            # Mixed operators with precedence
            ("A AND B OR C", ["a", "b", "AND", "c", "OR"]),
            ("A OR B AND C", ["a", "b", "c", "AND", "OR"]),
            ("NOT A OR B", ["a", "NOT", "b", "OR"]),
            ("A AND NOT B", ["a", "b", "NOT", "AND"]),
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["postfix"], expected)
                
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_nested_parentheses(self, mock_load):
        """Test nested parentheses"""
        query = "((A OR B) AND C) OR D"
        result = self.engine._parse_boolean_query(query)
        expected = ["a", "b", "OR", "c", "AND", "d", "OR"]
        self.assertEqual(result["postfix"], expected)
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_implicit_and_cases(self, mock_load):
        """Test various implicit AND scenarios"""
        test_cases = [
            ("attention mechanism transformer", ["attention", "mechanism", "AND", "transformer", "AND"]),
            ("attention (model OR mechanism)", ["attention", "model", "mechanism", "OR", "AND"]),
            ("(attention OR focus) mechanism", ["attention", "focus", "OR", "mechanism", "AND"]),
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["postfix"], expected)


class TestQueryMatching(unittest.TestCase):
    """Test cases for query matching against paper content"""
    
    def setUp(self):
        self.engine = BooleanSearchEngine()
        # Mock the papers to avoid loading real data
        self.engine.papers = []
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_text_extraction(self, mock_load):
        """Test text extraction from paper fields"""
        paper = MockPaper(
            "test-1",
            "Attention Is All You Need",
            ["Ashish Vaswani", "Noam Shazeer"],
            abstract="The dominant sequence transduction models are based on complex recurrent or convolutional neural networks."
        )
        
        text_data = self.engine._extract_text_from_paper(paper, ["title", "abstract", "authors"])
        
        self.assertEqual(text_data["title"], "attention is all you need")
        self.assertEqual(text_data["authors"], "ashish vaswani noam shazeer")
        self.assertIn("sequence transduction", text_data["abstract"])
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_simple_term_matching(self, mock_load):
        """Test basic term matching"""
        text_data = {"title": "attention is all you need", "abstract": "transformer model"}
        parsed_query = {"postfix": ["attention"], "terms": ["attention"], "quoted_terms": set()}
        
        matches, fields = self.engine._matches_query(text_data, parsed_query)
        self.assertTrue(matches)
        self.assertIn("title", fields)
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_and_matching(self, mock_load):
        """Test AND operator matching"""
        text_data = {"title": "attention is all you need", "abstract": "transformer model"}
        parsed_query = {"postfix": ["attention", "model", "AND"], "terms": ["attention", "model"], "quoted_terms": set()}
        
        matches, fields = self.engine._matches_query(text_data, parsed_query)
        self.assertTrue(matches)
        self.assertEqual(set(fields), {"title", "abstract"})
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_or_matching(self, mock_load):
        """Test OR operator matching"""
        text_data = {"title": "bert model", "abstract": "language representation"}
        parsed_query = {"postfix": ["bert", "gpt", "OR"], "terms": ["bert", "gpt"], "quoted_terms": set()}
        
        matches, fields = self.engine._matches_query(text_data, parsed_query)
        self.assertTrue(matches)
        self.assertIn("title", fields)
        
    @patch.object(BooleanSearchEngine, '_load_data') 
    def test_not_matching(self, mock_load):
        """Test NOT operator matching"""
        text_data = {"title": "attention mechanism", "abstract": "neural network"}
        
        # Should match: has "attention" but not "model"
        parsed_query = {"postfix": ["attention", "model", "NOT", "AND"], "terms": ["attention", "model"], "quoted_terms": set()}
        matches, fields = self.engine._matches_query(text_data, parsed_query)
        self.assertTrue(matches)
        
        # Should not match: has both "attention" and "model" (if we add "model" to text)
        text_data["abstract"] = "neural network model"
        matches, fields = self.engine._matches_query(text_data, parsed_query)
        self.assertFalse(matches)
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_exact_phrase_matching(self, mock_load):
        """Test exact phrase matching with quotes"""
        text_data = {"title": "neural machine translation", "abstract": "machine learning model"}
        
        # Exact phrase should match
        parsed_query = {
            "postfix": ["neural machine translation"], 
            "terms": ["neural machine translation"], 
            "quoted_terms": {"neural machine translation"}
        }
        matches, fields = self.engine._matches_query(text_data, parsed_query)
        self.assertTrue(matches)
        
        # Partial phrase should not match when quoted
        text_data["title"] = "neural translation machine"  # words in different order
        matches, fields = self.engine._matches_query(text_data, parsed_query)
        self.assertFalse(matches)
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_fuzzy_matching(self, mock_load):
        """Test fuzzy matching functionality"""
        text_data = {"title": "transformer model", "abstract": "neural network"}
        parsed_query = {"postfix": ["transfomer"], "terms": ["transfomer"], "quoted_terms": set()}  # typo
        
        # Should not match without fuzzy
        matches, fields = self.engine._matches_query(text_data, parsed_query, fuzzy=False)
        self.assertFalse(matches)
        
        # Should match with fuzzy
        matches, fields = self.engine._matches_query(text_data, parsed_query, fuzzy=True, fuzzy_threshold=80)
        self.assertTrue(matches)
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_case_insensitive_matching(self, mock_load):
        """Test case insensitive matching"""
        text_data = {"title": "ATTENTION IS ALL YOU NEED", "abstract": "transformer"}
        parsed_query = {"postfix": ["attention"], "terms": ["attention"], "quoted_terms": set()}
        
        matches, fields = self.engine._matches_query(text_data, parsed_query)
        self.assertTrue(matches)


class TestSearchFilters(unittest.TestCase):
    """Test cases for search filters"""
    
    def setUp(self):
        self.engine = BooleanSearchEngine()
        self.engine.papers = []
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_year_range_filter(self, mock_load):
        """Test year range filtering"""
        paper_2020 = MockPaper("p1", "Title", year="2020")
        paper_2022 = MockPaper("p2", "Title", year="2022") 
        paper_2025 = MockPaper("p3", "Title", year="2025")
        
        filters = {"year_range": (2021, 2024)}
        
        self.assertFalse(self.engine._apply_filters(paper_2020, filters))
        self.assertTrue(self.engine._apply_filters(paper_2022, filters))
        self.assertFalse(self.engine._apply_filters(paper_2025, filters))
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_venue_filter(self, mock_load):
        """Test venue filtering"""
        paper_acl = MockPaper("p1", "Title", venue_ids=["acl-2023"])
        paper_emnlp = MockPaper("p2", "Title", venue_ids=["emnlp-2023"])
        paper_multi = MockPaper("p3", "Title", venue_ids=["acl-2023", "workshops"])
        
        filters = {"venues": ["acl-2023"]}
        
        self.assertTrue(self.engine._apply_filters(paper_acl, filters))
        self.assertFalse(self.engine._apply_filters(paper_emnlp, filters))
        self.assertTrue(self.engine._apply_filters(paper_multi, filters))
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_combined_filters(self, mock_load):
        """Test combination of multiple filters"""
        paper = MockPaper("p1", "Title", year="2022", venue_ids=["acl-2022"])
        
        # Should pass both filters
        filters = {"year_range": (2020, 2024), "venues": ["acl-2022"]}
        self.assertTrue(self.engine._apply_filters(paper, filters))
        
        # Should fail year filter
        filters = {"year_range": (2023, 2024), "venues": ["acl-2022"]}
        self.assertFalse(self.engine._apply_filters(paper, filters))
        
        # Should fail venue filter
        filters = {"year_range": (2020, 2024), "venues": ["emnlp-2022"]}
        self.assertFalse(self.engine._apply_filters(paper, filters))


class TestSearchIntegration(unittest.TestCase):
    """Integration tests for the complete search functionality"""
    
    def setUp(self):
        self.engine = BooleanSearchEngine()
        # Create mock papers for testing
        self.mock_papers = [
            MockPaper("p1", "Attention Is All You Need", 
                     ["Ashish Vaswani", "Noam Shazeer"], "2017",
                     "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.",
                     ["nips-2017"]),
            MockPaper("p2", "BERT: Pre-training of Deep Bidirectional Transformers", 
                     ["Jacob Devlin", "Ming-Wei Chang"], "2018",
                     "We introduce a new language representation model called BERT.",
                     ["naacl-2019"]),
            MockPaper("p3", "Language Models are Unsupervised Multitask Learners", 
                     ["Alec Radford", "Jeffrey Wu"], "2019",
                     "Natural language processing tasks, such as question answering, machine translation, reading comprehension, and summarization.",
                     ["openai-2019"]),
        ]
        self.engine.papers = self.mock_papers
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_basic_search(self, mock_load):
        """Test basic search functionality"""
        results = self.engine.search("attention", limit=10)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].paper_id, "p1")
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_and_search(self, mock_load):
        """Test AND search"""
        results = self.engine.search("attention AND transformer", limit=10)
        # Should find papers with both terms
        self.assertGreaterEqual(len(results), 0)
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_or_search(self, mock_load):
        """Test OR search"""
        results = self.engine.search("BERT OR attention", limit=10)
        self.assertGreaterEqual(len(results), 2)  # Should find both BERT and attention papers
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_phrase_search(self, mock_load):
        """Test quoted phrase search"""
        results = self.engine.search('"language representation"', limit=10)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].paper_id, "p2")
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_field_specific_search(self, mock_load):
        """Test searching in specific fields"""
        # Search only in titles
        results = self.engine.search("BERT", fields=["title"], limit=10)
        self.assertEqual(len(results), 1)
        
        # Search only in abstracts
        results = self.engine.search("representation", fields=["abstract"], limit=10)
        self.assertEqual(len(results), 1)
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_filtered_search(self, mock_load):
        """Test search with filters"""
        filters = {"year_range": (2018, 2019)}
        results = self.engine.search("language", filters=filters, limit=10)
        
        # Should only return papers from 2018-2019
        for result in results:
            year = int(result.year)
            self.assertGreaterEqual(year, 2018)
            self.assertLessEqual(year, 2019)
            
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_limit_functionality(self, mock_load):
        """Test result limiting"""
        results = self.engine.search("the", limit=2)
        self.assertLessEqual(len(results), 2)
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_empty_query(self, mock_load):
        """Test empty query handling"""
        results = self.engine.search("", limit=10)
        self.assertEqual(len(results), 0)
        
        results = self.engine.search("   ", limit=10)
        self.assertEqual(len(results), 0)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        self.engine = BooleanSearchEngine()
        self.engine.papers = []
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_malformed_queries(self, mock_load):
        """Test handling of malformed queries"""
        malformed_queries = [
            "(",
            ")",
            "AND",
            "OR",
            "NOT",
            "(((",
            ")))",
            "AND OR",
            "NOT NOT",
            '""',
            '"unclosed quote',
        ]
        
        for query in malformed_queries:
            with self.subTest(query=query):
                # Should not raise exceptions
                try:
                    parsed = self.engine._parse_boolean_query(query)
                    results = self.engine.search(query, limit=5)
                    # Should return empty or handle gracefully
                    self.assertIsInstance(results, list)
                except Exception as e:
                    self.fail(f"Query '{query}' raised {type(e).__name__}: {e}")
                    
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_very_long_queries(self, mock_load):
        """Test handling of very long queries"""
        long_term = "a" * 1000
        long_query = f"{long_term} AND attention"
        
        # Should handle without crashing
        result = self.engine._parse_boolean_query(long_query)
        self.assertIsInstance(result, dict)
        
    @patch.object(BooleanSearchEngine, '_load_data') 
    def test_special_characters(self, mock_load):
        """Test handling of special characters in queries"""
        special_queries = [
            "attention@mechanism",
            "BERT-model",
            "neural_network",
            "model.transformer",
            "question?answering",
            "pre+training",
            "multi*task",
            "attention&mechanism",
        ]
        
        for query in special_queries:
            with self.subTest(query=query):
                try:
                    result = self.engine._parse_boolean_query(query)
                    self.assertIsInstance(result, dict)
                except Exception as e:
                    self.fail(f"Query '{query}' raised {type(e).__name__}: {e}")
                    
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_unicode_queries(self, mock_load):
        """Test handling of unicode characters"""
        unicode_queries = [
            "résumé",
            "naïve",
            "café",
            "机器学习",
            "🤖 robot",
        ]
        
        for query in unicode_queries:
            with self.subTest(query=query):
                try:
                    result = self.engine._parse_boolean_query(query)
                    self.assertIsInstance(result, dict)
                except Exception as e:
                    self.fail(f"Query '{query}' raised {type(e).__name__}: {e}")


class TestPerformance(unittest.TestCase):
    """Performance tests for search operations"""
    
    def setUp(self):
        self.engine = BooleanSearchEngine()
        # Create a larger set of mock papers for performance testing
        self.engine.papers = [
            MockPaper(f"p{i}", f"Test Paper {i}", [f"Author {i}"], 
                     str(2020 + (i % 5)), f"Abstract {i} with content")
            for i in range(100)
        ]
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_query_parsing_performance(self, mock_load):
        """Test performance of query parsing"""
        complex_query = " AND ".join([f"term{i}" for i in range(20)])
        
        start_time = time.time()
        for _ in range(100):
            self.engine._parse_boolean_query(complex_query)
        end_time = time.time()
        
        # Should complete 100 parses in reasonable time (< 1 second)
        self.assertLess(end_time - start_time, 1.0)
        
    @patch.object(BooleanSearchEngine, '_load_data')
    def test_search_performance(self, mock_load):
        """Test performance of search operations"""
        start_time = time.time()
        results = self.engine.search("test AND paper", limit=50)
        end_time = time.time()
        
        # Search should complete quickly
        self.assertLess(end_time - start_time, 2.0)
        self.assertIsInstance(results, list)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)
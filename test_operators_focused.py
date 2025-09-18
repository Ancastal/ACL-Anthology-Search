#!/usr/bin/env python3
"""
Focused test suite specifically for each search operator with clear test cases.

This file provides targeted tests for each individual operator to ensure 
comprehensive coverage and easy debugging.
"""

import unittest
from unittest.mock import Mock, patch
from search_engine import BooleanSearchEngine


class TestANDOperator(unittest.TestCase):
    """Dedicated tests for the AND operator"""
    
    @patch.object(BooleanSearchEngine, '_load_data')
    def setUp(self, mock_load_data):
        mock_load_data.return_value = None
        self.engine = BooleanSearchEngine()
        self.engine.papers = []  # Prevent loading real data
        
    def test_explicit_and(self):
        """Test explicit AND operator"""
        test_cases = [
            ("A AND B", ["a", "b", "AND"]),
            ("term1 AND term2 AND term3", ["term1", "term2", "AND", "term3", "AND"]),
            ("machine AND learning", ["machine", "learning", "AND"]),
        ]
        
        for query, expected_postfix in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["postfix"], expected_postfix)
                
    def test_implicit_and(self):
        """Test implicit AND between consecutive terms"""
        test_cases = [
            ("A B", ["a", "b", "AND"]),
            ("neural network model", ["neural", "network", "AND", "model", "AND"]),
            ("machine learning algorithm", ["machine", "learning", "AND", "algorithm", "AND"]),
        ]
        
        for query, expected_postfix in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["postfix"], expected_postfix)
                
    def test_and_with_parentheses(self):
        """Test AND operator with parentheses"""
        test_cases = [
            ("(A AND B)", ["a", "b", "AND"]),
            ("A AND (B C)", ["a", "b", "c", "AND", "AND"]),
        ]
        
        for query, expected_postfix in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["postfix"], expected_postfix)
                
    def test_and_matching_logic(self):
        """Test AND operator matching logic"""
        text_data = {
            "title": "machine learning model",
            "abstract": "neural network architecture"
        }
        
        # Both terms present - should match
        query = {"postfix": ["machine", "learning", "AND"], "terms": ["machine", "learning"], "quoted_terms": set()}
        matches, fields = self.engine._matches_query(text_data, query)
        self.assertTrue(matches)
        self.assertIn("title", fields)
        
        # One term missing - should not match
        query = {"postfix": ["machine", "missing", "AND"], "terms": ["machine", "missing"], "quoted_terms": set()}
        matches, fields = self.engine._matches_query(text_data, query)
        self.assertFalse(matches)


class TestOROperator(unittest.TestCase):
    """Dedicated tests for the OR operator"""
    
    @patch.object(BooleanSearchEngine, '_load_data')
    def setUp(self, mock_load_data):
        mock_load_data.return_value = None
        self.engine = BooleanSearchEngine()
        self.engine.papers = []
        
    def test_explicit_or(self):
        """Test explicit OR operator"""
        test_cases = [
            ("A OR B", ["a", "b", "OR"]),
            ("term1 OR term2 OR term3", ["term1", "term2", "OR", "term3", "OR"]),
            ("BERT OR GPT", ["bert", "gpt", "OR"]),
        ]
        
        for query, expected_postfix in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["postfix"], expected_postfix)
                
    def test_or_precedence(self):
        """Test OR operator precedence (lower than AND)"""
        test_cases = [
            ("A AND B OR C", ["a", "b", "AND", "c", "OR"]),
            ("A OR B AND C", ["a", "b", "c", "AND", "OR"]),
        ]
        
        for query, expected_postfix in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["postfix"], expected_postfix)
                
    def test_or_matching_logic(self):
        """Test OR operator matching logic"""
        text_data = {
            "title": "transformer model",
            "abstract": "attention mechanism"
        }
        
        # One term present - should match
        query = {"postfix": ["transformer", "missing", "OR"], "terms": ["transformer", "missing"], "quoted_terms": set()}
        matches, fields = self.engine._matches_query(text_data, query)
        self.assertTrue(matches)
        self.assertIn("title", fields)
        
        # Both terms present - should match
        query = {"postfix": ["transformer", "attention", "OR"], "terms": ["transformer", "attention"], "quoted_terms": set()}
        matches, fields = self.engine._matches_query(text_data, query)
        self.assertTrue(matches)
        
        # No terms present - should not match
        query = {"postfix": ["missing1", "missing2", "OR"], "terms": ["missing1", "missing2"], "quoted_terms": set()}
        matches, fields = self.engine._matches_query(text_data, query)
        self.assertFalse(matches)


class TestNOTOperator(unittest.TestCase):
    """Dedicated tests for the NOT operator"""
    
    @patch.object(BooleanSearchEngine, '_load_data')
    def setUp(self, mock_load_data):
        mock_load_data.return_value = None
        self.engine = BooleanSearchEngine()
        self.engine.papers = []
        
    def test_explicit_not(self):
        """Test explicit NOT operator"""
        test_cases = [
            ("NOT A", ["a", "NOT"]),
            ("A NOT B", ["a", "b", "NOT"]),  # NOT binds to B only, no implicit AND
            ("NOT A AND B", ["a", "NOT", "b", "AND"]),
        ]
        
        for query, expected_postfix in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["postfix"], expected_postfix)
                
    def test_not_precedence(self):
        """Test NOT operator precedence (highest)"""
        test_cases = [
            ("NOT A OR B", ["a", "NOT", "b", "OR"]),
            ("NOT A AND B", ["a", "NOT", "b", "AND"]),
            ("A AND NOT B", ["a", "b", "NOT", "AND"]),
        ]
        
        for query, expected_postfix in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["postfix"], expected_postfix)
                
    def test_not_matching_logic(self):
        """Test NOT operator matching logic"""
        text_data = {
            "title": "transformer model",
            "abstract": "attention mechanism"
        }
        
        # NOT with present term - should not match
        query = {"postfix": ["transformer", "NOT"], "terms": ["transformer"], "quoted_terms": set()}
        matches, fields = self.engine._matches_query(text_data, query)
        self.assertFalse(matches)
        
        # NOT with absent term - should match
        query = {"postfix": ["missing", "NOT"], "terms": ["missing"], "quoted_terms": set()}
        matches, fields = self.engine._matches_query(text_data, query)
        self.assertTrue(matches)
        
        # Complex: A AND NOT B where A present, B absent - should match
        query = {"postfix": ["transformer", "missing", "NOT", "AND"], "terms": ["transformer", "missing"], "quoted_terms": set()}
        matches, fields = self.engine._matches_query(text_data, query)
        self.assertTrue(matches)


class TestParenthesesOperator(unittest.TestCase):
    """Dedicated tests for parentheses grouping"""
    
    @patch.object(BooleanSearchEngine, '_load_data')
    def setUp(self, mock_load_data):
        mock_load_data.return_value = None
        self.engine = BooleanSearchEngine()
        self.engine.papers = []
        
    def test_simple_parentheses(self):
        """Test simple parentheses grouping"""
        test_cases = [
            ("(A)", ["a"]),
            ("(A B)", ["a", "b", "AND"]),
            ("(A OR B)", ["a", "b", "OR"]),
        ]
        
        for query, expected_postfix in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["postfix"], expected_postfix)
                
    def test_precedence_override(self):
        """Test parentheses overriding operator precedence"""
        test_cases = [
            ("(A OR B) AND C", ["a", "b", "OR", "c", "AND"]),
            ("A AND (B OR C)", ["a", "b", "c", "OR", "AND"]),
            ("(A AND B) OR (C AND D)", ["a", "b", "AND", "c", "d", "AND", "OR"]),
        ]
        
        for query, expected_postfix in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["postfix"], expected_postfix)
                
    def test_nested_parentheses(self):
        """Test nested parentheses"""
        test_cases = [
            ("((A))", ["a"]),
            ("((A OR B) AND C)", ["a", "b", "OR", "c", "AND"]),
            ("(A AND (B OR C))", ["a", "b", "c", "OR", "AND"]),
        ]
        
        for query, expected_postfix in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["postfix"], expected_postfix)
                
    def test_implicit_and_with_parentheses(self):
        """Test implicit AND with parentheses"""
        test_cases = [
            ("A (B OR C)", ["a", "b", "c", "OR", "AND"]),
            ("(A OR B) C", ["a", "b", "OR", "c", "AND"]),
            ("(A B) (C D)", ["a", "b", "AND", "c", "d", "AND", "AND"]),
        ]
        
        for query, expected_postfix in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["postfix"], expected_postfix)


class TestQuotedPhraseOperator(unittest.TestCase):
    """Dedicated tests for quoted phrase matching"""
    
    @patch.object(BooleanSearchEngine, '_load_data')
    def setUp(self, mock_load_data):
        mock_load_data.return_value = None
        self.engine = BooleanSearchEngine()
        self.engine.papers = []
        
    def test_simple_phrases(self):
        """Test simple quoted phrases"""
        test_cases = [
            ('"hello world"', ["hello world"], {"hello world"}),
            ('"machine learning"', ["machine learning"], {"machine learning"}),
            ('"natural language processing"', ["natural language processing"], {"natural language processing"}),
        ]
        
        for query, expected_terms, expected_quoted in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["terms"], expected_terms)
                self.assertEqual(result["quoted_terms"], expected_quoted)
                
    def test_phrases_with_operators(self):
        """Test quoted phrases combined with operators"""
        test_cases = [
            ('"machine learning" AND "deep learning"', 
             ["machine learning", "deep learning"], 
             {"machine learning", "deep learning"}),
            ('"neural network" OR transformer', 
             ["neural network", "transformer"], 
             {"neural network"}),
        ]
        
        for query, expected_terms, expected_quoted in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(set(result["terms"]), set(expected_terms))
                self.assertEqual(result["quoted_terms"], expected_quoted)
                
    def test_phrase_matching_logic(self):
        """Test exact phrase matching behavior"""
        text_data = {
            "title": "machine learning algorithm",
            "abstract": "artificial intelligence systems"
        }
        
        # Exact phrase match - should match
        query = {"postfix": ["machine learning"], "terms": ["machine learning"], "quoted_terms": {"machine learning"}}
        matches, fields = self.engine._matches_query(text_data, query)
        self.assertTrue(matches)
        
        # Words in different order - should not match exact phrase
        query = {"postfix": ["learning machine"], "terms": ["learning machine"], "quoted_terms": {"learning machine"}}
        matches, fields = self.engine._matches_query(text_data, query)
        self.assertFalse(matches)  # No "learning machine" phrase in the text
        
    def test_empty_phrases(self):
        """Test handling of empty or malformed phrases"""
        test_cases = [
            '""',
            '" "',
            '"',
            'unclosed "phrase',
        ]
        
        for query in test_cases:
            with self.subTest(query=query):
                # Should not crash
                result = self.engine._parse_boolean_query(query)
                self.assertIsInstance(result, dict)


class TestFuzzyOperator(unittest.TestCase):
    """Tests for fuzzy matching functionality"""
    
    @patch.object(BooleanSearchEngine, '_load_data')
    def setUp(self, mock_load_data):
        mock_load_data.return_value = None
        self.engine = BooleanSearchEngine()
        self.engine.papers = []
        
    def test_fuzzy_matching(self):
        """Test fuzzy string matching"""
        text_data = {
            "title": "transformer neural network",
            "abstract": "attention mechanism"
        }
        
        # Typo should match with fuzzy
        query = {"postfix": ["transfomer"], "terms": ["transfomer"], "quoted_terms": set()}
        matches, fields = self.engine._matches_query(text_data, query, fuzzy=True, fuzzy_threshold=80)
        self.assertTrue(matches)
        
        # Typo should not match without fuzzy
        matches, fields = self.engine._matches_query(text_data, query, fuzzy=False)
        self.assertFalse(matches)
        
    def test_fuzzy_threshold(self):
        """Test fuzzy matching threshold sensitivity"""
        text_data = {"title": "transformer"}
        query = {"postfix": ["elephant"], "terms": ["elephant"], "quoted_terms": set()}  # Very different word
        
        # High threshold - should not match
        matches, fields = self.engine._matches_query(text_data, query, fuzzy=True, fuzzy_threshold=90)
        self.assertFalse(matches)
        
        # Lower threshold with more similar word - should match
        query_similar = {"postfix": ["transform"], "terms": ["transform"], "quoted_terms": set()}
        matches, fields = self.engine._matches_query(text_data, query_similar, fuzzy=True, fuzzy_threshold=60)
        self.assertTrue(matches)
        
    def test_fuzzy_with_exact_phrases(self):
        """Test that quoted phrases are not fuzzily matched"""
        text_data = {"title": "transformer model"}
        query = {"postfix": ["transfomer model"], "terms": ["transfomer model"], "quoted_terms": {"transfomer model"}}
        
        # Exact phrase with typo should not match even with fuzzy enabled
        matches, fields = self.engine._matches_query(text_data, query, fuzzy=True)
        self.assertFalse(matches)


class TestOperatorCombinations(unittest.TestCase):
    """Tests for complex combinations of multiple operators"""
    
    @patch.object(BooleanSearchEngine, '_load_data')
    def setUp(self, mock_load_data):
        mock_load_data.return_value = None
        self.engine = BooleanSearchEngine()
        self.engine.papers = []
        
    def test_all_operators_combined(self):
        """Test complex queries using all operators"""
        complex_queries = [
            '("machine learning" OR "deep learning") AND transformer NOT "old model"',
            '(A AND B) OR (C AND NOT D)',
            '"exact phrase" AND (term1 OR term2) AND NOT excluded',
        ]
        
        for query in complex_queries:
            with self.subTest(query=query):
                # Should parse without error
                result = self.engine._parse_boolean_query(query)
                self.assertIsInstance(result, dict)
                self.assertIn("postfix", result)
                self.assertIn("terms", result)
                self.assertIn("quoted_terms", result)
                
    def test_operator_precedence_complex(self):
        """Test complex operator precedence scenarios"""
        test_cases = [
            # NOT has highest precedence
            ("A AND NOT B OR C", ["a", "b", "NOT", "AND", "c", "OR"]),
            # Parentheses override precedence
            ("NOT (A OR B)", ["a", "b", "OR", "NOT"]),
            # Multiple precedence levels
            ("A OR B AND NOT C OR D", ["a", "b", "c", "NOT", "AND", "OR", "d", "OR"]),
        ]
        
        for query, expected_postfix in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["postfix"], expected_postfix)
                
    def test_realistic_queries(self):
        """Test realistic research paper queries"""
        realistic_queries = [
            'attention AND (transformer OR "self attention")',
            '"neural machine translation" AND BERT NOT "old approach"',
            '(GPT OR BERT) AND "language model" AND (2019 OR 2020)',
            '"question answering" AND (BERT OR "bidirectional encoder")',
        ]
        
        for query in realistic_queries:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertIsInstance(result, dict)
                # Should have reasonable number of terms
                self.assertGreaterEqual(len(result["terms"]), 1)
                self.assertLessEqual(len(result["terms"]), 10)


if __name__ == '__main__':
    # Create test suite with specific order
    suite = unittest.TestSuite()
    
    # Add tests in logical order
    suite.addTest(unittest.makeSuite(TestANDOperator))
    suite.addTest(unittest.makeSuite(TestOROperator))
    suite.addTest(unittest.makeSuite(TestNOTOperator))
    suite.addTest(unittest.makeSuite(TestParenthesesOperator))
    suite.addTest(unittest.makeSuite(TestQuotedPhraseOperator))
    suite.addTest(unittest.makeSuite(TestFuzzyOperator))
    suite.addTest(unittest.makeSuite(TestOperatorCombinations))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
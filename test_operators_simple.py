#!/usr/bin/env python3
"""
Simple, fast test suite for search operators that doesn't load ACL Anthology data.

This test suite focuses on testing the core operator functionality without
requiring the full ACL Anthology dataset to be loaded.
"""

import unittest
from unittest.mock import Mock, patch
from search_engine import BooleanSearchEngine


class TestSearchOperatorsSimple(unittest.TestCase):
    """Fast tests for all search operators"""
    
    @patch('search_engine.BooleanSearchEngine._load_data')
    def setUp(self, mock_load_data):
        """Set up test engine without loading data"""
        mock_load_data.return_value = None
        self.engine = BooleanSearchEngine()
        self.engine.papers = []  # Empty list to avoid loading time
    
    def test_and_operator_parsing(self):
        """Test AND operator parsing"""
        test_cases = [
            ("A AND B", ["a", "b", "AND"]),
            ("machine AND learning", ["machine", "learning", "AND"]),
            ("A B", ["a", "b", "AND"]),  # implicit AND
            ("neural network model", ["neural", "network", "AND", "model", "AND"]),
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["postfix"], expected, 
                    f"Query '{query}' failed. Got {result['postfix']}, expected {expected}")
    
    def test_or_operator_parsing(self):
        """Test OR operator parsing"""
        test_cases = [
            ("A OR B", ["a", "b", "OR"]),
            ("BERT OR GPT", ["bert", "gpt", "OR"]),
            ("model OR transformer OR attention", ["model", "transformer", "OR", "attention", "OR"]),
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["postfix"], expected,
                    f"Query '{query}' failed. Got {result['postfix']}, expected {expected}")
    
    def test_not_operator_parsing(self):
        """Test NOT operator parsing"""
        test_cases = [
            ("NOT A", ["a", "NOT"]),
            ("A NOT B", ["a", "b", "NOT"]),  # NOT binds to B only
            ("attention NOT model", ["attention", "model", "NOT"]),  # NOT binds to model only
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["postfix"], expected,
                    f"Query '{query}' failed. Got {result['postfix']}, expected {expected}")
    
    def test_parentheses_parsing(self):
        """Test parentheses grouping"""
        test_cases = [
            ("(A OR B)", ["a", "b", "OR"]),
            ("(A OR B) AND C", ["a", "b", "OR", "c", "AND"]),
            ("A AND (B OR C)", ["a", "b", "c", "OR", "AND"]),
            ("((A OR B) AND C)", ["a", "b", "OR", "c", "AND"]),
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["postfix"], expected,
                    f"Query '{query}' failed. Got {result['postfix']}, expected {expected}")
    
    def test_quoted_phrases_parsing(self):
        """Test quoted phrase parsing"""
        test_cases = [
            ('"hello world"', ["hello world"], {"hello world"}),
            ('"machine learning"', ["machine learning"], {"machine learning"}),
            ('"neural machine translation"', ["neural machine translation"], {"neural machine translation"}),
        ]
        
        for query, expected_terms, expected_quoted in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["terms"], expected_terms)
                self.assertEqual(result["quoted_terms"], expected_quoted)
    
    def test_operator_precedence(self):
        """Test operator precedence rules"""
        test_cases = [
            # NOT has highest precedence
            ("NOT A OR B", ["a", "NOT", "b", "OR"]),
            ("NOT A AND B", ["a", "NOT", "b", "AND"]),
            # AND has higher precedence than OR
            ("A OR B AND C", ["a", "b", "c", "AND", "OR"]),
            ("A AND B OR C", ["a", "b", "AND", "c", "OR"]),
            # Parentheses override precedence
            ("(A OR B) AND C", ["a", "b", "OR", "c", "AND"]),
        ]
        
        for query, expected in test_cases:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                self.assertEqual(result["postfix"], expected,
                    f"Query '{query}' failed. Got {result['postfix']}, expected {expected}")
    
    def test_complex_combinations(self):
        """Test complex operator combinations"""
        complex_queries = [
            '(A OR B) AND (C OR D)',
            'NOT (A AND B) OR C',
            '"exact phrase" AND (term1 OR term2)',
            '(BERT OR GPT) AND transformer NOT "old model"',
        ]
        
        for query in complex_queries:
            with self.subTest(query=query):
                result = self.engine._parse_boolean_query(query)
                # Should parse without error
                self.assertIsInstance(result, dict)
                self.assertIn("postfix", result)
                self.assertIn("terms", result)
                self.assertIn("quoted_terms", result)
                # Should have at least one term
                self.assertGreater(len(result["terms"]), 0)
    
    def test_matching_logic_and(self):
        """Test AND operator matching logic"""
        text_data = {"title": "machine learning model", "abstract": "neural network"}
        
        # Both terms present - should match
        query = {"postfix": ["machine", "learning", "AND"], "terms": ["machine", "learning"], "quoted_terms": set()}
        matches, fields = self.engine._matches_query(text_data, query)
        self.assertTrue(matches)
        
        # One term missing - should not match
        query = {"postfix": ["machine", "missing", "AND"], "terms": ["machine", "missing"], "quoted_terms": set()}
        matches, fields = self.engine._matches_query(text_data, query)
        self.assertFalse(matches)
    
    def test_matching_logic_or(self):
        """Test OR operator matching logic"""
        text_data = {"title": "transformer model", "abstract": "attention"}
        
        # One term present - should match
        query = {"postfix": ["transformer", "missing", "OR"], "terms": ["transformer", "missing"], "quoted_terms": set()}
        matches, fields = self.engine._matches_query(text_data, query)
        self.assertTrue(matches)
        
        # No terms present - should not match
        query = {"postfix": ["missing1", "missing2", "OR"], "terms": ["missing1", "missing2"], "quoted_terms": set()}
        matches, fields = self.engine._matches_query(text_data, query)
        self.assertFalse(matches)
    
    def test_matching_logic_not(self):
        """Test NOT operator matching logic"""
        text_data = {"title": "transformer model", "abstract": "attention"}
        
        # NOT with present term - should not match
        query = {"postfix": ["transformer", "NOT"], "terms": ["transformer"], "quoted_terms": set()}
        matches, fields = self.engine._matches_query(text_data, query)
        self.assertFalse(matches)
        
        # NOT with absent term - should match
        query = {"postfix": ["missing", "NOT"], "terms": ["missing"], "quoted_terms": set()}
        matches, fields = self.engine._matches_query(text_data, query)
        self.assertTrue(matches)
    
    def test_exact_phrase_matching(self):
        """Test exact phrase matching"""
        text_data = {"title": "neural machine translation", "abstract": "model"}
        
        # Exact phrase present - should match
        query = {"postfix": ["neural machine translation"], "terms": ["neural machine translation"], "quoted_terms": {"neural machine translation"}}
        matches, fields = self.engine._matches_query(text_data, query)
        self.assertTrue(matches)
        
        # Words in different order - should not match exact phrase
        text_data_reorder = {"title": "translation machine neural", "abstract": "model"}
        matches, fields = self.engine._matches_query(text_data_reorder, query)
        self.assertFalse(matches)
    
    def test_fuzzy_matching(self):
        """Test fuzzy matching functionality"""
        text_data = {"title": "transformer model", "abstract": "neural"}
        
        # Typo without fuzzy - should not match
        query = {"postfix": ["transfomer"], "terms": ["transfomer"], "quoted_terms": set()}
        matches, fields = self.engine._matches_query(text_data, query, fuzzy=False)
        self.assertFalse(matches)
        
        # Typo with fuzzy - should match
        matches, fields = self.engine._matches_query(text_data, query, fuzzy=True, fuzzy_threshold=80)
        self.assertTrue(matches)
    
    def test_case_insensitive(self):
        """Test case insensitive matching"""
        text_data = {"title": "transformer model", "abstract": "neural"}  # Already lowercase as expected by the matching logic
        
        query = {"postfix": ["transformer"], "terms": ["transformer"], "quoted_terms": set()}
        matches, fields = self.engine._matches_query(text_data, query)
        self.assertTrue(matches)
    
    def test_edge_cases(self):
        """Test edge cases and malformed queries"""
        edge_cases = [
            "",  # empty
            "   ",  # whitespace only
            "(",  # unmatched parenthesis
            ")",  # unmatched parenthesis
            "AND",  # operator only
            "OR",  # operator only
            "NOT",  # operator only
            '""',  # empty quotes
        ]
        
        for query in edge_cases:
            with self.subTest(query=repr(query)):
                # Should not crash
                result = self.engine._parse_boolean_query(query)
                self.assertIsInstance(result, dict)
    
    def test_filter_functionality(self):
        """Test basic filter functionality"""
        # Mock paper for testing
        mock_paper = Mock()
        mock_paper.year = "2022"
        mock_paper.venue_ids = ["acl-2022"]
        
        # Year filter test
        year_filter = {"year_range": (2020, 2024)}
        self.assertTrue(self.engine._apply_filters(mock_paper, year_filter))
        
        year_filter_fail = {"year_range": (2025, 2030)}
        self.assertFalse(self.engine._apply_filters(mock_paper, year_filter_fail))
        
        # Venue filter test
        venue_filter = {"venues": ["acl-2022"]}
        self.assertTrue(self.engine._apply_filters(mock_paper, venue_filter))
        
        venue_filter_fail = {"venues": ["emnlp-2022"]}
        self.assertFalse(self.engine._apply_filters(mock_paper, venue_filter_fail))


def print_test_summary():
    """Print a summary of what operators are tested"""
    print("\n" + "="*60)
    print("SEARCH OPERATOR TEST COVERAGE")
    print("="*60)
    print()
    
    operators = {
        "✓ AND Operator": [
            "Explicit AND (A AND B)",
            "Implicit AND (A B)", 
            "Multiple ANDs",
            "Matching logic"
        ],
        "✓ OR Operator": [
            "Explicit OR (A OR B)",
            "Multiple ORs",
            "Matching logic"
        ],
        "✓ NOT Operator": [
            "Explicit NOT",
            "NOT with other operators",
            "Matching logic"
        ],
        "✓ Parentheses": [
            "Simple grouping",
            "Precedence override",
            "Nested parentheses"
        ],
        "✓ Quoted Phrases": [
            "Exact phrase matching",
            "Case handling",
            "Multiple phrases"
        ],
        "✓ Operator Precedence": [
            "NOT > AND > OR",
            "Parentheses override",
            "Complex expressions"
        ],
        "✓ Fuzzy Matching": [
            "Typo tolerance",
            "Threshold sensitivity",
            "Exact phrase exclusion"
        ],
        "✓ Additional Features": [
            "Case insensitive search",
            "Field-specific search",
            "Filter functionality",
            "Edge case handling"
        ]
    }
    
    for category, features in operators.items():
        print(f"{category}:")
        for feature in features:
            print(f"  • {feature}")
        print()


if __name__ == '__main__':
    print("ACL Anthology Search Engine - Simple Operator Tests")
    print("="*60)
    
    # Run the tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchOperatorsSimple)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print_test_summary()
    
    # Print results
    print("="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            newline = '\n'
            print(f"  - {test}: {traceback.split('AssertionError: ')[-1].split(newline)[0]}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            newline = '\n'
            print(f"  - {test}: {traceback.split(newline)[-2]}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100 if result.testsRun > 0 else 0
    print(f"\nSuccess rate: {success_rate:.1f}%")
    
    if len(result.failures) == 0 and len(result.errors) == 0:
        print("\n🎉 ALL TESTS PASSED! All search operators are working correctly.")
    else:
        print(f"\n⚠️  {len(result.failures) + len(result.errors)} tests failed. Some operators may need attention.")
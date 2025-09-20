#!/usr/bin/env python3

import sys
sys.path.insert(0, 'src')

from acl_search.core.search_engine import BooleanSearchEngine

def test_parsing(query):
    engine = BooleanSearchEngine()
    parsed = engine._parse_boolean_query(query)
    print(f"Query: {query}")
    print(f"Terms: {parsed['terms']}")
    print(f"Postfix: {parsed['postfix']}")
    print(f"Quoted: {parsed['quoted_terms']}")
    print()

# Test the problematic queries
test_parsing('("LLMs" OR large language models) AND translation')
test_parsing('(large language models) AND translation')
test_parsing('large language models AND translation')
test_parsing('"LLMs" OR large language models')
test_parsing('LLMs OR "large language models"')
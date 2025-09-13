#!/usr/bin/env python3
"""
Test script for the search engine
"""

from search_engine import BooleanSearchEngine
import time


def test_search_engine():
    """Test the search engine with various queries"""
    
    print("Initializing search engine...")
    engine = BooleanSearchEngine()
    
    # Test queries
    test_queries = [
        "attention",
        "attention AND mechanism",
        "attention OR transformer",
        '"neural machine translation"',
        "BERT OR GPT",
        "(BERT OR GPT) AND transformer",
        "attention NOT model"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing query: {query}")
        print('='*60)
        
        start_time = time.time()
        results = engine.search(
            query=query,
            fields=["title", "abstract", "authors"],
            limit=5
        )
        search_time = time.time() - start_time
        
        print(f"Found {len(results)} results in {search_time:.2f} seconds")
        print()
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.title}")
            print(f"   Authors: {', '.join(result.authors[:3])}{'...' if len(result.authors) > 3 else ''}")
            print(f"   Year: {result.year}, Venue: {', '.join(result.venue)}")
            print(f"   Matches: {', '.join(result.match_fields)}")
            print()

    # Test filters
    print(f"\n{'='*60}")
    print("Testing filters: attention + year 2020-2023")
    print('='*60)
    
    filtered_results = engine.search(
        query="attention",
        fields=["title"],
        filters={"year_range": (2020, 2023)},
        limit=5
    )
    
    print(f"Found {len(filtered_results)} results")
    for result in filtered_results:
        print(f"- {result.title} ({result.year})")

    # Fuzzy search test
    print(f"\n{'='*60}")
    print("Testing fuzzy search: 'transfomer'")
    print('='*60)
    fuzzy_results = engine.search(
        query="transfomer",
        fields=["title"],
        limit=5,
        fuzzy=True
    )
    print(f"Found {len(fuzzy_results)} results with fuzzy matching")

    # Exact word match test
    print(f"\n{'='*60}")
    print('Testing exact word match: lingu vs "lingu"')
    print('='*60)
    unquoted = engine.search(
        query="lingu",
        fields=["title"],
        limit=5
    )
    quoted = engine.search(
        query='"lingu"',
        fields=["title"],
        limit=5
    )
    print(f"Unquoted results: {len(unquoted)}; Quoted results: {len(quoted)}")


if __name__ == "__main__":
    test_search_engine()
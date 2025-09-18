#!/usr/bin/env python3
"""
Interactive Test Suite for ACL Anthology Search Engine

This tool allows you to:
- Enter custom queries and see how they're parsed
- Test queries against sample data 
- Experiment with different operators and settings
- Understand the search engine behavior in real-time
"""

import sys
import json
from typing import Dict, Any, List
from unittest.mock import patch
from acl_search.core.search_engine import BooleanSearchEngine


class InteractiveTestSuite:
    def __init__(self):
        """Initialize the test suite with mock data to avoid loading ACL dataset"""
        with patch.object(BooleanSearchEngine, '_load_data'):
            self.engine = BooleanSearchEngine()
            self.engine.papers = []  # Prevent actual data loading
        
        # Sample test documents
        self.test_documents = {
            "doc1": {
                "title": "attention is all you need transformer neural network",
                "abstract": "we present a new simple network architecture the transformer based solely on attention mechanisms dispensing with recurrence and convolutions entirely",
                "authors": "ashish vaswani noam shazeer"
            },
            "doc2": {
                "title": "bert pre-training of deep bidirectional transformers for language understanding",
                "abstract": "we introduce a new language representation model called bert which stands for bidirectional encoder representations from transformers",
                "authors": "jacob devlin ming-wei chang"
            },
            "doc3": {
                "title": "language models are unsupervised multitask learners gpt",
                "abstract": "natural language processing tasks such as question answering machine translation reading comprehension and summarization",
                "authors": "alec radford jeffrey wu"
            },
            "doc4": {
                "title": "neural machine translation by jointly learning to align and translate",
                "abstract": "neural machine translation is a recently proposed approach to machine translation unlike the traditional statistical machine translation",
                "authors": "dzmitry bahdanau kyunghyun cho"
            },
            "doc5": {
                "title": "deep learning book artificial intelligence",
                "abstract": "this book provides a comprehensive introduction to the field of machine learning from linear models to deep reinforcement learning",
                "authors": "ian goodfellow yoshua bengio aaron courville"
            }
        }
        
    def print_header(self):
        """Print the welcome header"""
        print("\n" + "="*80)
        print("🔍 INTERACTIVE ACL ANTHOLOGY SEARCH ENGINE TEST SUITE")
        print("="*80)
        print("Test your queries against sample academic papers!")
        print("Available commands: help, docs, settings, fields, query, exit")
        print("="*80 + "\n")
    
    def print_help(self):
        """Print help information"""
        print("\n📚 HELP - Available Commands:")
        print("-" * 40)
        print("🔍 query <your_query>     - Test a search query")
        print("📄 docs                   - Show sample documents")
        print("⚙️  settings              - Show/modify search settings") 
        print("🏷️  fields                - Show available search fields")
        print("📊 examples               - Show example queries")
        print("🔧 parse <query>          - Show only query parsing (no matching)")
        print("❌ exit                   - Exit the test suite")
        print("❓ help                   - Show this help")
        print("\n🔍 SEARCH OPERATORS:")
        print("• AND: machine AND learning (or just: machine learning)")
        print("• OR: BERT OR GPT") 
        print("• NOT: attention NOT model")
        print("• Parentheses: (BERT OR GPT) AND transformer")
        print("• Quotes: \"neural machine translation\"")
        print("• Fuzzy: Enable with settings command")
        print()
    
    def print_examples(self):
        """Print example queries"""
        print("\n📊 EXAMPLE QUERIES:")
        print("-" * 40)
        print("Basic:")
        print('  query attention')
        print('  query machine learning') 
        print('  query BERT OR GPT')
        print()
        print("Advanced:")
        print('  query "neural machine translation"')
        print('  query (BERT OR GPT) AND transformer')
        print('  query attention NOT model')
        print('  query "deep learning" AND (neural OR network)')
        print()
        print("With fuzzy matching (enable via settings):")
        print('  query transfomer  # matches "transformer"')
        print('  query machien learning  # matches "machine learning"')
        print()
    
    def show_documents(self):
        """Show the sample documents"""
        print("\n📄 SAMPLE DOCUMENTS:")
        print("-" * 40)
        for doc_id, doc in self.test_documents.items():
            print(f"\n{doc_id.upper()}:")
            print(f"  Title: {doc['title'][:60]}{'...' if len(doc['title']) > 60 else ''}")
            print(f"  Authors: {doc['authors']}")
            print(f"  Abstract: {doc['abstract'][:80]}{'...' if len(doc['abstract']) > 80 else ''}")
        print()
    
    def show_fields(self):
        """Show available search fields"""
        print("\n🏷️ AVAILABLE SEARCH FIELDS:")
        print("-" * 40)
        print("• title     - Paper titles")
        print("• abstract  - Paper abstracts") 
        print("• authors   - Author names")
        print("• all       - Search in all fields (default)")
        print("\nUsage: When prompted, specify fields like: title,abstract")
        print()
    
    def show_settings(self):
        """Show and allow modification of search settings"""
        print("\n⚙️ CURRENT SEARCH SETTINGS:")
        print("-" * 40)
        print(f"Fuzzy matching: {getattr(self, 'fuzzy_enabled', False)}")
        print(f"Fuzzy threshold: {getattr(self, 'fuzzy_threshold', 80)}%")
        print(f"Default fields: {getattr(self, 'default_fields', ['title', 'abstract', 'authors'])}")
        print()
        
        change = input("Change settings? (y/n): ").strip().lower()
        if change == 'y':
            # Fuzzy settings
            fuzzy = input("Enable fuzzy matching? (y/n): ").strip().lower()
            self.fuzzy_enabled = fuzzy == 'y'
            
            if self.fuzzy_enabled:
                try:
                    threshold = input("Fuzzy threshold (60-100, default 80): ").strip()
                    self.fuzzy_threshold = int(threshold) if threshold else 80
                    self.fuzzy_threshold = max(60, min(100, self.fuzzy_threshold))
                except ValueError:
                    self.fuzzy_threshold = 80
            
            # Field settings
            fields_input = input("Default fields (title,abstract,authors or 'all'): ").strip()
            if fields_input == 'all' or not fields_input:
                self.default_fields = ['title', 'abstract', 'authors']
            else:
                self.default_fields = [f.strip() for f in fields_input.split(',')]
            
            print("✅ Settings updated!")
    
    def parse_query_only(self, query: str):
        """Show only the query parsing without matching"""
        print(f"\n🔍 PARSING QUERY: '{query}'")
        print("-" * 60)
        
        try:
            result = self.engine._parse_boolean_query(query)
            
            print("✅ PARSING SUCCESSFUL")
            print(f"📝 Original query: {query}")
            print(f"🏗️  Postfix notation: {result['postfix']}")
            print(f"📋 Extracted terms: {result['terms']}")
            print(f"📖 Quoted terms: {list(result['quoted_terms'])}")
            print(f"📊 Term count: {len(result['terms'])}")
            
            if result['quoted_terms']:
                print("⚠️  Note: Quoted terms will be matched exactly (no fuzzy matching)")
            
            # Show parsing steps for complex queries
            if len(result['postfix']) > 2:
                print(f"\n🔧 EVALUATION ORDER:")
                self._explain_postfix_evaluation(result['postfix'])
                
        except Exception as e:
            print(f"❌ PARSING FAILED: {e}")
    
    def _explain_postfix_evaluation(self, postfix: List[str]):
        """Explain how the postfix expression will be evaluated"""
        operators = {"AND", "OR", "NOT"}
        stack = []
        step = 1
        
        for token in postfix:
            if token in operators:
                if token == "NOT":
                    if stack:
                        operand = stack.pop()
                        result = f"NOT({operand})"
                        stack.append(result)
                        print(f"  Step {step}: {result}")
                        step += 1
                else:
                    if len(stack) >= 2:
                        right = stack.pop()
                        left = stack.pop()
                        result = f"({left} {token} {right})"
                        stack.append(result)
                        print(f"  Step {step}: {result}")
                        step += 1
            else:
                stack.append(token)
        
        if stack:
            print(f"  Final: {stack[0]}")
    
    def test_query(self, query: str):
        """Test a query against the sample documents"""
        print(f"\n🔍 TESTING QUERY: '{query}'")
        print("=" * 60)
        
        # Parse the query
        try:
            parsed_query = self.engine._parse_boolean_query(query)
            print("✅ PARSING SUCCESSFUL")
            print(f"📝 Original: {query}")
            print(f"🏗️  Postfix: {parsed_query['postfix']}")
            print(f"📋 Terms: {parsed_query['terms']}")
            if parsed_query['quoted_terms']:
                print(f"📖 Quoted: {list(parsed_query['quoted_terms'])}")
        except Exception as e:
            print(f"❌ PARSING FAILED: {e}")
            return
        
        # Get search settings
        fuzzy = getattr(self, 'fuzzy_enabled', False)
        fuzzy_threshold = getattr(self, 'fuzzy_threshold', 80)
        fields = getattr(self, 'default_fields', ['title', 'abstract', 'authors'])
        
        print(f"\n⚙️ SEARCH SETTINGS:")
        print(f"   Fields: {', '.join(fields)}")
        print(f"   Fuzzy: {'Enabled' if fuzzy else 'Disabled'}")
        if fuzzy:
            print(f"   Threshold: {fuzzy_threshold}%")
        
        # Test against each document
        matches = []
        print(f"\n📊 TESTING AGAINST {len(self.test_documents)} DOCUMENTS:")
        print("-" * 60)
        
        for doc_id, doc_data in self.test_documents.items():
            # Extract text from specified fields
            text_data = {}
            for field in fields:
                if field in doc_data:
                    text_data[field] = doc_data[field].lower()
            
            # Test matching
            try:
                matches_doc, match_fields = self.engine._matches_query(
                    text_data, parsed_query, fuzzy=fuzzy, fuzzy_threshold=fuzzy_threshold
                )
                
                status = "✅ MATCH" if matches_doc else "❌ NO MATCH"
                print(f"{doc_id.upper()}: {status}")
                
                if matches_doc:
                    matches.append(doc_id)
                    print(f"   📍 Matched in: {', '.join(match_fields)}")
                    print(f"   📄 Title: {doc_data['title'][:50]}{'...' if len(doc_data['title']) > 50 else ''}")
                
                # Show why it matched/didn't match
                self._explain_matching(parsed_query, text_data, fuzzy, fuzzy_threshold)
                print()
                
            except Exception as e:
                print(f"{doc_id.upper()}: ❌ ERROR - {e}")
        
        # Summary
        print("=" * 60)
        print(f"📈 SUMMARY: {len(matches)}/{len(self.test_documents)} documents matched")
        if matches:
            print(f"✅ Matching documents: {', '.join(matches).upper()}")
        else:
            print("💡 Try different terms or enable fuzzy matching in settings")
        print()
    
    def _explain_matching(self, parsed_query: Dict[str, Any], text_data: Dict[str, str], fuzzy: bool, fuzzy_threshold: int):
        """Explain why a document matched or didn't match"""
        terms = parsed_query.get('terms', [])
        quoted_terms = parsed_query.get('quoted_terms', set())
        
        print("   🔍 Term analysis:")
        for term in terms:
            found_in = []
            is_quoted = term in quoted_terms
            
            for field, text in text_data.items():
                if is_quoted:
                    # Exact phrase matching
                    if term in text:
                        found_in.append(field)
                else:
                    # Regular or fuzzy matching
                    if term in text:
                        found_in.append(field)
                    elif fuzzy:
                        try:
                            from rapidfuzz import fuzz
                            if fuzz.partial_ratio(term, text) >= fuzzy_threshold:
                                found_in.append(f"{field}(fuzzy)")
                        except:
                            pass
            
            status = "✅" if found_in else "❌"
            quote_info = " (exact)" if is_quoted else ""
            fuzzy_info = " (fuzzy enabled)" if fuzzy and not is_quoted else ""
            print(f"      {status} '{term}'{quote_info}{fuzzy_info}: {', '.join(found_in) if found_in else 'not found'}")
    
    def run_interactive_session(self):
        """Run the main interactive session"""
        self.print_header()
        
        while True:
            try:
                user_input = input("🔍 Enter command (help for options): ").strip()
                
                if not user_input:
                    continue
                
                # Parse command
                parts = user_input.split(' ', 1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if command == 'exit':
                    print("👋 Goodbye!")
                    break
                
                elif command == 'help':
                    self.print_help()
                
                elif command == 'docs':
                    self.show_documents()
                
                elif command == 'fields':
                    self.show_fields()
                
                elif command == 'settings':
                    self.show_settings()
                
                elif command == 'examples':
                    self.print_examples()
                
                elif command == 'parse':
                    if args:
                        self.parse_query_only(args)
                    else:
                        print("❌ Please provide a query to parse. Example: parse attention AND transformer")
                
                elif command == 'query':
                    if args:
                        self.test_query(args)
                    else:
                        print("❌ Please provide a query to test. Example: query machine learning")
                
                else:
                    # Assume it's a query if no command matches
                    if user_input:
                        self.test_query(user_input)
                    else:
                        print("❌ Unknown command. Type 'help' for available commands.")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                print("Type 'help' for available commands.")


def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Interactive Test Suite for ACL Anthology Search Engine")
        print("Usage: python interactive_test.py")
        print()
        print("This tool provides an interactive interface to test search queries")
        print("against sample academic papers without loading the full ACL dataset.")
        return
    
    suite = InteractiveTestSuite()
    suite.run_interactive_session()


if __name__ == '__main__':
    main()
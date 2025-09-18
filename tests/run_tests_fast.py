#!/usr/bin/env python3
"""
Fast test runner that avoids loading ACL Anthology data.

This runner only executes lightweight tests that don't require loading
the full ACL Anthology dataset, making it suitable for quick validation.
"""

import unittest
import sys
import time
from io import StringIO


def main():
    """Main fast test runner function"""
    print("ACL Anthology Search Engine - Fast Test Runner")
    print("="*60)
    print("🚀 Running lightweight tests (no ACL data loading)")
    print("="*60)
    
    # Import and run only the fast test suite
    try:
        import test_operators_simple
    except ImportError as e:
        print(f"❌ Error importing test_operators_simple: {e}")
        print("Make sure test_operators_simple.py exists in the current directory.")
        return 1
    
    # Run the tests
    start_time = time.time()
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(test_operators_simple)
    
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    end_time = time.time()
    
    # Print results
    print("\n" + "="*60)
    print("FAST TEST RESULTS")
    print("="*60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    successes = total_tests - failures - errors
    success_rate = (successes / total_tests * 100) if total_tests > 0 else 0
    
    print(f"⏱️  Execution time: {end_time - start_time:.2f} seconds")
    print(f"📊 Tests run: {total_tests}")
    print(f"✅ Successes: {successes}")
    print(f"❌ Failures: {failures}")
    print(f"💥 Errors: {errors}")
    print(f"📈 Success rate: {success_rate:.1f}%")
    
    if failures == 0 and errors == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("All search operators are working correctly.")
        print("\nOperators tested:")
        print("  ✓ AND (explicit and implicit)")
        print("  ✓ OR")  
        print("  ✓ NOT")
        print("  ✓ Parentheses grouping")
        print("  ✓ Quoted phrases")
        print("  ✓ Operator precedence")
        print("  ✓ Fuzzy matching")
        print("  ✓ Field filtering")
        print("  ✓ Case insensitive search")
        print("  ✓ Edge cases")
    else:
        print(f"\n⚠️  {failures + errors} TESTS FAILED")
        
        if failures:
            print("\n❌ Failures:")
            for test, traceback in result.failures:
                print(f"  • {test}")
                
        if errors:
            print("\n💥 Errors:")
            for test, traceback in result.errors:
                print(f"  • {test}")
    
    print("\n" + "="*60)
    print("💡 ADDITIONAL TEST OPTIONS")
    print("="*60)
    print("For more comprehensive testing (loads ACL data):")
    print("  python -m unittest test_operators_focused -v")
    print("  python -m unittest test_search_operators -v")
    print()
    print("⚠️  Note: Comprehensive tests will load ~113k papers (takes ~5-10 seconds)")
    
    return 0 if (failures == 0 and errors == 0) else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
#!/usr/bin/env python3
"""
Test runner for the comprehensive search operator test suite.

This script runs all tests and provides detailed reporting on test coverage
and results for each search operator.
"""

import unittest
import sys
import time
from io import StringIO


def run_test_suite(test_file_name, suite_name):
    """Run a specific test suite and return results"""
    print(f"\n{'='*60}")
    print(f"Running {suite_name}")
    print('='*60)
    
    # Import the test module
    try:
        if test_file_name == 'test_search_operators':
            import test_search_operators as test_module
        elif test_file_name == 'test_operators_focused':
            import test_operators_focused as test_module
        elif test_file_name == 'test_operators_simple':
            import test_operators_simple as test_module
        else:
            raise ImportError(f"Unknown test module: {test_file_name}")
    except ImportError as e:
        print(f"Error importing {test_file_name}: {e}")
        return False, 0, 0, []
    
    # Create test loader and discover tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(test_module)
    
    # Run tests with detailed output capture
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # Print the output
    print(stream.getvalue())
    
    # Print summary
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    success_count = total_tests - failures - errors
    success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\nSummary for {suite_name}:")
    print(f"  Tests run: {total_tests}")
    print(f"  Successes: {success_count}")
    print(f"  Failures: {failures}")
    print(f"  Errors: {errors}")
    print(f"  Success rate: {success_rate:.1f}%")
    print(f"  Time taken: {end_time - start_time:.2f} seconds")
    
    # List any failures or errors
    issues = []
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}")
            issues.append(("FAIL", test, traceback))
            
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}")
            issues.append(("ERROR", test, traceback))
    
    success = failures == 0 and errors == 0
    return success, total_tests, success_count, issues


def print_operator_coverage_report():
    """Print a report of which operators are tested"""
    print(f"\n{'='*60}")
    print("OPERATOR COVERAGE REPORT")
    print('='*60)
    
    operators = {
        "AND Operator": [
            "Explicit AND (A AND B)",
            "Implicit AND (A B)", 
            "Multiple ANDs (A AND B AND C)",
            "AND with parentheses",
            "AND matching logic"
        ],
        "OR Operator": [
            "Explicit OR (A OR B)",
            "Multiple ORs (A OR B OR C)",
            "OR precedence vs AND",
            "OR matching logic"
        ],
        "NOT Operator": [
            "Explicit NOT (NOT A)",
            "NOT with AND/OR (A NOT B)",
            "NOT precedence (highest)",
            "NOT matching logic"
        ],
        "Parentheses": [
            "Simple grouping (A OR B)",
            "Precedence override",
            "Nested parentheses",
            "Implicit AND with parentheses"
        ],
        "Quoted Phrases": [
            "Simple phrases (\"hello world\")",
            "Phrases with operators",
            "Exact matching behavior",
            "Empty/malformed phrases"
        ],
        "Fuzzy Matching": [
            "Basic fuzzy matching",
            "Threshold sensitivity",
            "Fuzzy vs exact phrases",
            "Performance with fuzzy"
        ],
        "Complex Combinations": [
            "All operators combined",
            "Complex precedence scenarios",
            "Realistic research queries",
            "Edge cases and malformed input"
        ],
        "Additional Features": [
            "Field-specific search (title, abstract, authors)",
            "Year range filters",
            "Venue filters", 
            "Result limiting",
            "Case insensitive matching",
            "Unicode and special characters"
        ]
    }
    
    for operator, features in operators.items():
        print(f"\n{operator}:")
        for feature in features:
            print(f"  ✓ {feature}")


def main():
    """Main test runner function"""
    print("ACL Anthology Search Engine - Comprehensive Test Suite")
    print("="*60)
    
    print("⚠️  WARNING: This runner may load ACL Anthology data multiple times!")
    print("For faster testing, use: python run_tests_fast.py")
    print("="*60)
    
    all_success = True
    total_tests_run = 0
    total_successes = 0
    all_issues = []
    
    # Test suites to run
    test_suites = [
        ('test_operators_simple', 'Fast Operator Tests (No data loading)'),
        ('test_operators_focused', '⚠️  Focused Tests (Loads ACL data per test)'),
        ('test_search_operators', '⚠️  Integration Tests (Loads ACL data per test)'),
    ]
    
    # Ask user which tests to run
    print("Available test suites:")
    for i, (_, name) in enumerate(test_suites, 1):
        print(f"  {i}. {name}")
    print("  a. All tests")
    print("  f. Fast tests only (recommended)")
    
    choice = input("\nEnter your choice (1-3, a, f) [f]: ").strip().lower()
    
    if choice == '' or choice == 'f':
        # Fast tests only
        test_suites = [('test_operators_simple', 'Fast Operator Tests')]
    elif choice == 'a':
        # All tests - keep the full list
        pass
    elif choice.isdigit() and 1 <= int(choice) <= len(test_suites):
        # Single test suite
        idx = int(choice) - 1
        test_suites = [test_suites[idx]]
    else:
        print("Invalid choice. Running fast tests only.")
        test_suites = [('test_operators_simple', 'Fast Operator Tests')]
    
    # Run each test suite
    for test_file, suite_name in test_suites:
        success, tests_run, successes, issues = run_test_suite(test_file, suite_name)
        all_success = all_success and success
        total_tests_run += tests_run
        total_successes += successes
        all_issues.extend(issues)
    
    # Print overall summary
    print(f"\n{'='*60}")
    print("OVERALL TEST SUMMARY")
    print('='*60)
    
    overall_success_rate = (total_successes / total_tests_run * 100) if total_tests_run > 0 else 0
    
    print(f"Total tests run: {total_tests_run}")
    print(f"Total successes: {total_successes}")
    print(f"Total failures/errors: {total_tests_run - total_successes}")
    print(f"Overall success rate: {overall_success_rate:.1f}%")
    
    if all_success:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("All search operators are working correctly.")
    else:
        print(f"\n⚠️  {len(all_issues)} TEST ISSUES FOUND")
        print("Some operators may need attention.")
    
    # Print operator coverage report
    print_operator_coverage_report()
    
    # Print detailed issues if any
    if all_issues:
        print(f"\n{'='*60}")
        print("DETAILED ISSUE REPORT")
        print('='*60)
        
        for issue_type, test_name, traceback in all_issues:
            print(f"\n{issue_type}: {test_name}")
            print("-" * 40)
            # Print first few lines of traceback
            lines = traceback.split('\n')[:10]
            print('\n'.join(lines))
            if len(traceback.split('\n')) > 10:
                print("... (truncated)")
    
    # Return appropriate exit code
    return 0 if all_success else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
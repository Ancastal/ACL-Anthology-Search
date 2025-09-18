# Search Operator Tests - Quick Start Guide

## 🚀 Fast Testing (Recommended)
For quick validation of all search operators without loading ACL data:

```bash
python run_tests_fast.py
```
- ⏱️ **Speed**: < 1 second
- 📊 **Tests**: 15 comprehensive tests
- 💾 **Data**: No ACL data loading
- ✅ **Coverage**: All operators (AND, OR, NOT, parentheses, quotes, fuzzy)

## 🔧 Interactive Testing
For choosing specific test suites:

```bash
python run_tests.py
```
Choose from:
1. Fast tests only (recommended)
2. Focused tests (loads ACL data per test class)
3. Integration tests (loads full ACL dataset)

## 📋 Test Coverage

| Operator | Examples | Status |
|----------|----------|---------|
| **AND** | `machine AND learning`, `neural network` | ✅ |
| **OR** | `BERT OR GPT`, `transformer OR attention` | ✅ |
| **NOT** | `attention NOT model`, `NOT outdated` | ✅ |
| **Parentheses** | `(BERT OR GPT) AND transformer` | ✅ |
| **Quotes** | `"machine learning"`, `"exact phrase"` | ✅ |
| **Fuzzy** | `transfomer` → `transformer` | ✅ |
| **Fields** | Search in title/abstract/authors | ✅ |
| **Filters** | Year ranges, venue filtering | ✅ |
| **Edge Cases** | Malformed queries, special chars | ✅ |

## 🎯 When to Use Each Test

- **Daily development**: `python run_tests_fast.py`
- **Before commits**: `python run_tests_fast.py`
- **Testing YOUR queries**: `python interactive_test.py` 🔍✨
- **Full validation**: `python run_tests.py` → choose "All tests"
- **Specific debugging**: Run individual test files

## 📁 Test Files

- `test_operators_simple.py` - Fast unit tests ⚡
- `test_operators_focused.py` - Detailed operator tests 🔍
- `test_search_operators.py` - Integration tests 🔗
- `run_tests_fast.py` - Fast runner (recommended) 🚀
- `run_tests.py` - Interactive runner 🎛️
- `interactive_test.py` - **Test YOUR queries interactively!** 🔍✨
- `test_my_queries.py` - Quick launcher for interactive testing 🚀

## 🔍 Sample Test Run

```bash
$ python run_tests_fast.py

ACL Anthology Search Engine - Fast Test Runner
============================================================
🚀 Running lightweight tests (no ACL data loading)
============================================================

✅ Tests run: 15
✅ Successes: 15  
✅ Success rate: 100.0%
⏱️  Execution time: 0.00 seconds

🎉 ALL TESTS PASSED!
```

## 🔍 Interactive Query Testing

Want to test your own search queries? Use the interactive test suite!

```bash
python interactive_test.py
```

### Features:
- ✅ Test any query against sample academic papers  
- ✅ See exactly how queries are parsed
- ✅ Understand why documents match or don't match
- ✅ Enable fuzzy matching for typos
- ✅ Configure search fields (title/abstract/authors)
- ✅ Learn with built-in examples and help

### Quick Example:
```bash
$ python interactive_test.py

🔍 Enter command: query (BERT OR GPT) AND transformer

🔍 TESTING QUERY: '(BERT OR GPT) AND transformer'
============================================================
✅ PARSING SUCCESSFUL
📝 Original: (BERT OR GPT) AND transformer
🏗️  Postfix: ['bert', 'gpt', 'OR', 'transformer', 'AND']

📊 TESTING AGAINST 5 DOCUMENTS:
DOC1: ✅ MATCH - Contains "transformer"
DOC2: ✅ MATCH - Contains "BERT" and "transformer"
📈 SUMMARY: 2/5 documents matched
```

**See `INTERACTIVE_GUIDE.md` for detailed usage instructions!**

---

**Pro tip**: Bookmark `python run_tests_fast.py` for daily use!
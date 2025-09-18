# 🔍 Interactive Test Suite Guide

Test your own search queries against sample academic papers!

## 🚀 Quick Start

```bash
# Launch the interactive test suite
python interactive_test.py

# Or use the simple launcher
python test_my_queries.py
```

## 📋 Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `query <search>` | Test a search query | `query machine learning` |
| `parse <query>` | Show only parsing (no matching) | `parse (BERT OR GPT) AND transformer` |
| `docs` | Show sample documents | `docs` |
| `settings` | Configure search settings | `settings` |
| `fields` | Show available search fields | `fields` |
| `examples` | Show example queries | `examples` |
| `help` | Show all commands | `help` |
| `exit` | Exit the tool | `exit` |

## 🔍 Sample Documents

The test suite includes 5 academic papers:

- **DOC1**: "Attention Is All You Need" (Transformer paper)
- **DOC2**: "BERT: Pre-training of Deep Bidirectional Transformers"  
- **DOC3**: "Language Models are Unsupervised Multitask Learners" (GPT)
- **DOC4**: "Neural Machine Translation by Jointly Learning to Align and Translate"
- **DOC5**: "Deep Learning Book"

## 🎯 Example Session

```
🔍 Enter command: query attention

🔍 TESTING QUERY: 'attention'
============================================================
✅ PARSING SUCCESSFUL
📝 Original: attention
🏗️  Postfix: ['attention']
📋 Terms: ['attention']

⚙️ SEARCH SETTINGS:
   Fields: title, abstract, authors
   Fuzzy: Disabled

📊 TESTING AGAINST 5 DOCUMENTS:
------------------------------------------------------------
DOC1: ✅ MATCH
   📍 Matched in: title, abstract
   📄 Title: attention is all you need transformer neural...

DOC2: ❌ NO MATCH
   🔍 Term analysis:
      ❌ 'attention': not found

============================================================
📈 SUMMARY: 1/5 documents matched
✅ Matching documents: DOC1
```

## 🔧 Advanced Features

### Fuzzy Matching
Enable typo tolerance in settings:
```
🔍 Enter command: settings
Enable fuzzy matching? (y/n): y
Fuzzy threshold (60-100, default 80): 80
```

Then test:
```
🔍 Enter command: query transfomer
# Will match "transformer" with fuzzy enabled
```

### Field-Specific Search
Configure which fields to search:
```
🔍 Enter command: settings  
Default fields (title,abstract,authors or 'all'): title
```

### Complex Queries
Test advanced boolean queries:
```
🔍 Enter command: query (BERT OR GPT) AND "language model"
🔍 Enter command: query attention NOT model
🔍 Enter command: query "neural machine translation"
```

## 📊 Understanding Results

### Query Parsing
```
✅ PARSING SUCCESSFUL
📝 Original: (BERT OR GPT) AND transformer  
🏗️  Postfix: ['bert', 'gpt', 'OR', 'transformer', 'AND']
📋 Terms: ['bert', 'gpt', 'transformer']

🔧 EVALUATION ORDER:
  Step 1: (bert OR gpt)
  Step 2: ((bert OR gpt) AND transformer)
```

### Document Matching
```
DOC2: ✅ MATCH
   📍 Matched in: title, abstract
   📄 Title: bert pre-training of deep bidirectional...
   🔍 Term analysis:
      ✅ 'bert': title, abstract
      ❌ 'gpt': not found
      ✅ 'transformer': abstract
```

## 🎓 Learning Examples

### Basic Operators
```
query machine learning          # Implicit AND
query BERT OR GPT              # OR operator  
query attention NOT model      # NOT operator
```

### Grouping & Precedence
```
query A OR B AND C             # Parsed as: A OR (B AND C)
query (A OR B) AND C           # Override precedence
query NOT A OR B               # Parsed as: (NOT A) OR B
```

### Exact Phrases
```
query "machine learning"       # Exact phrase match
query "neural machine translation"
query machine learning         # Individual words (implicit AND)
```

### Complex Combinations
```
query "deep learning" AND (neural OR network) NOT "old approach"
query (BERT OR GPT OR transformer) AND attention
query "language model" AND (2019 OR 2020 OR recent)
```

## 🔍 Operator Reference

| Operator | Syntax | Example | Precedence |
|----------|--------|---------|------------|
| **AND** | `A AND B` or `A B` | `machine learning` | Medium |
| **OR** | `A OR B` | `BERT OR GPT` | Low |
| **NOT** | `NOT A` or `A NOT B` | `attention NOT old` | High |
| **Quotes** | `"exact phrase"` | `"machine learning"` | N/A |
| **Parentheses** | `(A OR B) AND C` | `(BERT OR GPT) AND transformer` | Override |

## 💡 Pro Tips

1. **Start simple**: Test individual terms first, then build complexity
2. **Use parse command**: Understand how queries are interpreted
3. **Check term analysis**: See exactly why documents match/don't match
4. **Enable fuzzy**: Helpful for handling typos in real searches
5. **Try different fields**: Sometimes terms appear in abstracts but not titles
6. **Use quotes carefully**: Exact phrases are strict - word order matters

## 🐛 Troubleshooting

**Query doesn't parse?**
- Check parentheses balance: `(A OR B` → `(A OR B)`
- Avoid lone operators: `AND` → `A AND B`

**No matches found?**
- Try simpler terms first
- Enable fuzzy matching for typos
- Check if terms exist in sample docs with `docs` command
- Try different field combinations in settings

**Unexpected results?**
- Use `parse` command to understand query interpretation  
- Check operator precedence: `A OR B AND C` ≠ `(A OR B) AND C`
- Remember NOT has highest precedence: `NOT A OR B` = `(NOT A) OR B`

---

**Happy testing! 🎉**
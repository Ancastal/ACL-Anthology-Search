'use client'

import { useState } from 'react'
import { Search, HelpCircle, Wand2, Loader } from 'lucide-react'

interface SearchBarProps {
  query: string
  onQueryChange: (query: string) => void
  onSearch: (query: string) => void
  loading: boolean
}

export default function SearchBar({ query, onQueryChange, onSearch, loading }: SearchBarProps) {
  const [showHelp, setShowHelp] = useState(false)
  const [isConverting, setIsConverting] = useState(false)
  const [convertedQuery, setConvertedQuery] = useState<string | null>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSearch(query)
  }

  const handleNaturalLanguageConversion = async () => {
    if (!query.trim()) return
    
    setIsConverting(true)
    try {
      const response = await fetch('http://127.0.0.1:8000/convert-query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          natural_query: query
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      setConvertedQuery(data.converted_query)
      onQueryChange(data.converted_query)
      
    } catch (error) {
      console.error('Error converting query:', error)
      // Simple fallback conversion
      const fallbackQuery = query.replace(/\band\b/gi, ' AND ').replace(/\bor\b/gi, ' OR ')
      onQueryChange(fallbackQuery)
    } finally {
      setIsConverting(false)
    }
  }

  const exampleQueries = [
    'attention mechanism',
    '"neural machine translation"',
    '("BERT" OR "GPT") AND "transformer"',
    'attention NEAR/3 mechanism',
    '(transformer OR attention) AND "question answering"',
    'question answering NOT conversational'
  ]

  return (
    <div>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            placeholder="Enter your search query (e.g., attention mechanism AND transformer)"
            className="w-full pl-12 pr-16 py-4 text-lg border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
            disabled={loading}
          />
          <button
            type="button"
            onClick={() => setShowHelp(!showHelp)}
            className="absolute right-12 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
            title="Show search help"
          >
            <HelpCircle className="w-5 h-5" />
          </button>
        </div>
        
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <Search className="w-4 h-4" />
            {loading ? 'Searching...' : 'Search'}
          </button>
          
          <button
            type="button"
            onClick={handleNaturalLanguageConversion}
            disabled={isConverting || !query.trim()}
            className="px-6 py-3 bg-purple-600 text-white font-semibold rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            title="Convert natural language to boolean query using AI"
          >
            {isConverting ? (
              <Loader className="w-4 h-4 animate-spin" />
            ) : (
              <Wand2 className="w-4 h-4" />
            )}
            {isConverting ? 'Converting...' : 'AI Convert'}
          </button>
          
          <button
            type="button"
            onClick={() => onQueryChange('')}
            className="px-6 py-3 text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Clear
          </button>
        </div>
      </form>

      {showHelp && (
        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="font-semibold text-blue-900 mb-2">Search Help</h3>
          <div className="space-y-2 text-sm text-blue-800">
            <div>
              <strong>Boolean operators:</strong> Use AND, OR, NOT to combine terms
            </div>
            <div>
              <strong>Exact phrases:</strong> Use quotes for exact matches: "neural machine translation"
            </div>
            <div>
              <strong>Parentheses:</strong> Group terms for complex logic: ("BERT" OR "GPT") AND "transformer"
            </div>
            <div>
              <strong>Proximity operators:</strong> NEAR/n (within n words), WITHIN/sentence, WITHIN/paragraph
            </div>
            <div>
              <strong>AI Convert:</strong> Use the purple button to convert natural language to boolean queries
            </div>
            <div>
              <strong>Fuzzy Matching:</strong> Find word variations (e.g., "classify" ↔ "classification")
            </div>
            <div>
              <strong>Example searches:</strong>
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              {exampleQueries.map((example, index) => (
                <button
                  key={index}
                  onClick={() => {
                    onQueryChange(example)
                    setShowHelp(false)
                  }}
                  className="px-3 py-1 bg-white border border-blue-300 rounded-full text-xs hover:bg-blue-100 transition-colors"
                >
                  {example}
                </button>
              ))}
            </div>
            <div className="mt-4 pt-3 border-t border-blue-200">
              <strong>Adding to Zotero:</strong>
              <div className="text-xs mt-1 space-y-1">
                <div>📁 <strong>Bulk save:</strong> Look for folder icon in browser toolbar - click to select multiple papers</div>
                <div>📚 <strong>BibTeX file:</strong> Download BibTeX file and import to Zotero</div>
                <div>📋 <strong>Copy citation:</strong> Click copy icon for manual paste</div>
                <div>💡 <strong>COinS metadata:</strong> Same technology as ACL Anthology website</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
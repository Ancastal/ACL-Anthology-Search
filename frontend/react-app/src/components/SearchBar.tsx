'use client'

import { useState, useEffect } from 'react'
import { Search, HelpCircle, Wand2, Loader, Bookmark, BookmarkPlus, Trash2, Play, Copy, Calendar } from 'lucide-react'

interface SearchBarProps {
  query: string
  onQueryChange: (query: string) => void
  onSearch: (query: string) => void
  loading: boolean
}

interface SavedQuery {
  id: string
  name: string
  query: string
  timestamp: number
}

export default function SearchBar({ query, onQueryChange, onSearch, loading }: SearchBarProps) {
  const [showHelp, setShowHelp] = useState(false)
  const [isConverting, setIsConverting] = useState(false)
  const [convertedQuery, setConvertedQuery] = useState<string | null>(null)
  const [savedQueries, setSavedQueries] = useState<SavedQuery[]>([])
  const [showSaved, setShowSaved] = useState(false)
  const [saveDialogOpen, setSaveDialogOpen] = useState(false)
  const [saveName, setSaveName] = useState('')

  // Load saved queries from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem('acl-saved-queries')
      if (stored) {
        setSavedQueries(JSON.parse(stored))
      }
    } catch (error) {
      console.error('Error loading saved queries:', error)
    }
  }, [])

  // Save queries to localStorage
  const updateStoredQueries = (queries: SavedQuery[]) => {
    try {
      localStorage.setItem('acl-saved-queries', JSON.stringify(queries))
      setSavedQueries(queries)
    } catch (error) {
      console.error('Error saving queries:', error)
    }
  }

  const saveQuery = () => {
    if (!query.trim() || !saveName.trim()) return

    const newQuery: SavedQuery = {
      id: Date.now().toString(),
      name: saveName.trim(),
      query: query.trim(),
      timestamp: Date.now()
    }

    const updated = [...savedQueries, newQuery]
    updateStoredQueries(updated)
    setSaveDialogOpen(false)
    setSaveName('')
  }

  const loadQuery = (savedQuery: SavedQuery) => {
    onQueryChange(savedQuery.query)
    setShowSaved(false)
  }

  const deleteQuery = (id: string) => {
    const updated = savedQueries.filter(q => q.id !== id)
    updateStoredQueries(updated)
  }

  const copyQueryToClipboard = async (query: string) => {
    try {
      await navigator.clipboard.writeText(query)
    } catch (err) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea')
      textArea.value = query
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
    }
  }

  const loadAndSearch = (savedQuery: SavedQuery) => {
    onQueryChange(savedQuery.query)
    setShowSaved(false)
    onSearch(savedQuery.query)
  }

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
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center gap-1">
            <button
              type="button"
              onClick={() => setShowSaved(!showSaved)}
              className="text-gray-400 hover:text-gray-600 transition-colors p-1"
              title="Saved queries"
            >
              <Bookmark className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => setShowHelp(!showHelp)}
              className="text-gray-400 hover:text-gray-600 transition-colors p-1"
              title="Show search help"
            >
              <HelpCircle className="w-4 h-4" />
            </button>
          </div>
        </div>
        
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-4 py-2 text-sm bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5"
          >
            <Search className="w-3.5 h-3.5" />
            {loading ? 'Searching...' : 'Search'}
          </button>

          <button
            type="button"
            onClick={handleNaturalLanguageConversion}
            disabled={isConverting || !query.trim()}
            className="px-4 py-2 text-sm bg-purple-600 text-white font-medium rounded-md hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5"
            title="Convert natural language to boolean query using AI"
          >
            {isConverting ? (
              <Loader className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Wand2 className="w-3.5 h-3.5" />
            )}
            {isConverting ? 'Converting...' : 'AI Convert'}
          </button>

          <button
            type="button"
            onClick={() => setSaveDialogOpen(true)}
            disabled={!query.trim()}
            className="px-4 py-2 text-sm text-green-600 border border-green-200 rounded-md hover:bg-green-50 disabled:bg-gray-100 disabled:text-gray-400 disabled:border-gray-200 transition-colors flex items-center gap-1.5"
            title="Save this query"
          >
            <BookmarkPlus className="w-3.5 h-3.5" />
            Save
          </button>

          <button
            type="button"
            onClick={() => onQueryChange('')}
            className="px-4 py-2 text-sm text-gray-600 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
          >
            Clear
          </button>
        </div>
      </form>

      {/* Save Query Dialog */}
      {saveDialogOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Save Query</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Query Name
                </label>
                <input
                  type="text"
                  value={saveName}
                  onChange={(e) => setSaveName(e.target.value)}
                  placeholder="Enter a name for this query"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Query
                </label>
                <div className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-md text-sm font-mono">
                  {query}
                </div>
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => {
                    setSaveDialogOpen(false)
                    setSaveName('')
                  }}
                  className="px-4 py-2 text-sm text-gray-600 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={saveQuery}
                  disabled={!saveName.trim()}
                  className="px-4 py-2 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-300 transition-colors"
                >
                  Save
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Saved Queries Panel */}
      {showSaved && (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-green-900">Saved Queries</h3>
            <span className="text-sm text-green-700">{savedQueries.length} saved</span>
          </div>
          {savedQueries.length === 0 ? (
            <p className="text-sm text-green-700">No saved queries yet. Save your current query to get started!</p>
          ) : (
            <div className="space-y-3">
              {savedQueries.map((savedQuery) => (
                <div key={savedQuery.id} className="group bg-white border border-green-200 rounded-xl p-4 hover:border-green-300 hover:shadow-sm transition-all">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-green-100 text-green-600 rounded-lg flex items-center justify-center">
                      <Bookmark className="w-4 h-4" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <h4 className="font-semibold text-gray-900 text-sm leading-tight">{savedQuery.name}</h4>
                        <div className="flex items-center gap-1 text-xs text-gray-500">
                          <Calendar className="w-3 h-3" />
                          <span>{new Date(savedQuery.timestamp).toLocaleDateString()}</span>
                        </div>
                      </div>

                      <div className="mb-3 p-2 bg-gray-50 rounded-lg border border-gray-200">
                        <code className="text-xs text-gray-700 break-all leading-relaxed">{savedQuery.query}</code>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => loadAndSearch(savedQuery)}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                          title="Load and search immediately"
                        >
                          <Play className="w-3.5 h-3.5" />
                          Search
                        </button>

                        <button
                          onClick={() => loadQuery(savedQuery)}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors"
                          title="Load query into search bar"
                        >
                          <Search className="w-3.5 h-3.5" />
                          Load
                        </button>

                        <button
                          onClick={() => copyQueryToClipboard(savedQuery.query)}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                          title="Copy query to clipboard"
                        >
                          <Copy className="w-3.5 h-3.5" />
                          Copy
                        </button>

                        <button
                          onClick={() => deleteQuery(savedQuery.id)}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50 transition-colors ml-auto"
                          title="Delete saved query"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

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
'use client'

import { useState, useEffect } from 'react'
import SearchBar from '@/components/SearchBar'
import SearchFilters from '@/components/SearchFilters'
import SearchResults from '@/components/SearchResults'
import QueryBuilder from '@/components/QueryBuilder'
import LoadingSpinner from '@/components/LoadingSpinner'
import { Search, BookOpen, Database, Clock, ChevronDown, ChevronUp } from 'lucide-react'

interface SearchFilters {
  fields: string[]
  yearRange: [number, number] | null
  venues: string[]
  limit: number
}

interface SearchResult {
  paper_id: string
  title: string
  authors: string[]
  year: string
  abstract: string | null
  venue: string[]
  url: string
  match_fields: string[]
  doi?: string | null
  score?: number | null
  source?: string
  metadata?: {
    provider?: string | null
    citations_count?: number | null
    references_count?: number | null
    related_works?: {
      title?: string
      year?: number
      authors?: string[]
      url?: string
      doi?: string
    }[]
    source_url?: string | null
  }
}

interface SearchResponse {
  results: SearchResult[]
  total_count: number
  search_time: number
  stats: {
    year_range?: [number, number]
    unique_venues: number
    unique_authors: number
  }
}

interface ApiStats {
  total_papers: number
  year_range: [number, number]
  total_venues: number
  common_venues: string[]
}

export default function Home() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [apiStats, setApiStats] = useState<ApiStats | null>(null)
  const [apiReady, setApiReady] = useState(false)
  const [fuzzyEnabled, setFuzzyEnabled] = useState(false)
  const [sortBy, setSortBy] = useState<'relevance' | 'year'>('relevance')
  const [semanticEnabled, setSemanticEnabled] = useState(false)
  const [semanticMode, setSemanticMode] = useState<'rerank' | 'hybrid'>('rerank')
  const [semanticTopK, setSemanticTopK] = useState<number>(200)
  const [searchEngine, setSearchEngine] = useState<string>('unknown')
  const [queryBuilderOpen, setQueryBuilderOpen] = useState(false)
  const [searchSources, setSearchSources] = useState<string[]>(['acl'])
  const [experimentalMode, setExperimentalMode] = useState<boolean>(false)

  const [filters, setFilters] = useState<SearchFilters>({
    fields: ['title', 'abstract', 'authors'],
    yearRange: null,
    venues: [],
    limit: 100
  })

  // Check API health and load stats
  useEffect(() => {
    const checkApi = async () => {
      try {
        const healthResponse = await fetch('http://127.0.0.1:8000/health')
        const healthData = await healthResponse.json()
        setApiReady(healthData.search_engine_ready)
        
        // Get search engine type from root endpoint
        const rootResponse = await fetch('http://127.0.0.1:8000/')
        const rootData = await rootResponse.json()
        setSearchEngine(rootData.search_engine || 'unknown')
        
        if (healthData.search_engine_ready) {
          const statsResponse = await fetch('http://127.0.0.1:8000/stats')
          const statsData = await statsResponse.json()
          setApiStats(statsData)
        }
      } catch (error) {
        console.error('API connection error:', error)
        setApiReady(false)
      }
    }

    checkApi()
    
    // Poll every 5 seconds until API is ready
    const interval = setInterval(() => {
      if (!apiReady) {
        checkApi()
      } else {
        clearInterval(interval)
      }
    }, 5000)

    return () => clearInterval(interval)
  }, [apiReady])

  // Generate COinS (ContextObjects in Spans) for Zotero detection
  const generateCOinS = (result: SearchResult): string => {
    // Create OpenURL ContextObject for COinS
    const params = new URLSearchParams()
    
    // Basic bibliographic data
    params.append('ctx_ver', 'Z39.88-2004')
    params.append('rft_val_fmt', 'info:ofi/fmt:kev:mtx:journal')
    params.append('rfr_id', 'info:sid/aclanthology-search')
    
    // Paper details
    params.append('rft.genre', 'proceeding')
    params.append('rft.atitle', result.title)
    params.append('rft.date', result.year)
    
    // Authors (first author as primary, rest as additional)
    if (result.authors.length > 0) {
      params.append('rft.aulast', result.authors[0].split(' ').pop() || '')
      params.append('rft.aufirst', result.authors[0].split(' ').slice(0, -1).join(' '))
      
      // Add all authors
      result.authors.forEach((author, index) => {
        params.append(`rft.au`, author)
      })
    }
    
    // Conference/venue information
    if (result.venue.length > 0) {
      params.append('rft.btitle', result.venue.join(', '))
    }
    
    // URL to paper
    params.append('rft_id', result.url)
    
    return params.toString()
  }

  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery.trim() || !apiReady) return

    setLoading(true)
    setError(null)

    try {
      const requestBody = {
        query: searchQuery,
        fields: filters.fields,
        year_range: filters.yearRange,
        venues: filters.venues.length > 0 ? filters.venues : null,
        limit: filters.limit,
        fuzzy: fuzzyEnabled,
        sort: sortBy,
        semantic: semanticEnabled,
        semantic_mode: semanticMode,
        semantic_top_k: semanticTopK,
        sources: searchSources,
        experimental: experimentalMode
      }

      const response = await fetch('http://127.0.0.1:8000/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Search failed')
      }

      const data: SearchResponse = await response.json()
      setResults(data)
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  if (!apiReady) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="large" />
          <h2 className="text-2xl font-bold text-gray-800 mt-4 mb-2">Loading ACL Anthology</h2>
          <p className="text-gray-600">Initializing search engine with 113,000+ papers...</p>
          <div className="mt-4 text-sm text-gray-500">
            This may take a few moments on first load
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="text-center">
            <div className="flex justify-center items-center gap-3 mb-2">
              <BookOpen className="w-8 h-8 text-blue-600" />
              <h1 className="text-3xl font-bold text-gray-900">ACL Anthology Search</h1>
            </div>
            <p className="text-lg text-gray-600">
              Search {apiStats?.total_papers.toLocaleString() || '113,000+'} computational linguistics and NLP papers
            </p>
            
            {apiStats && (
              <div className="flex justify-center gap-8 mt-4 text-sm text-gray-500">
                <div className="flex items-center gap-1">
                  <Database className="w-4 h-4" />
                  <span>{apiStats.total_papers.toLocaleString()} papers</span>
                </div>
                <div className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  <span>{apiStats.year_range[0]} - {apiStats.year_range[1]}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Search className="w-4 h-4" />
                  <span>{apiStats.total_venues} venues</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar with filters */}
          <div className="lg:col-span-1">
            <SearchFilters
              filters={filters}
              onFiltersChange={setFilters}
              apiStats={apiStats}
            />
          </div>

          {/* Main content */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
              <SearchBar
                query={query}
                onQueryChange={setQuery}
                onSearch={handleSearch}
                loading={loading}
              />
              {/* Query Builder Toggle */}
              <div className="mt-4">
                <button
                  type="button"
                  onClick={() => setQueryBuilderOpen(!queryBuilderOpen)}
                  className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-800 transition-colors"
                >
                  {queryBuilderOpen ? (
                    <ChevronUp className="w-4 h-4" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                  Query Builder
                </button>

                {queryBuilderOpen && (
                  <div className="mt-3 relative z-10">
                    <QueryBuilder onChange={setQuery} initialQuery={query} />
                  </div>
                )}
              </div>
              
              {/* Fuzzy matching toggle */}
              <div className="mt-4 pt-4 border-t border-gray-100">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={fuzzyEnabled}
                    onChange={(e) => setFuzzyEnabled(e.target.checked)}
                    className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500 focus:ring-2"
                  />
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-700">
                      Fuzzy Matching
                    </span>
                    <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full font-medium">
                      EXPERIMENTAL
                    </span>
                  </div>
                </label>
                <p className="text-xs text-gray-500 mt-1 ml-7">
                  Find word variations and similar terms using basic fuzzy matching.
                </p>
                {/* Semantic search */}
                <div className="mt-4">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={semanticEnabled}
                      onChange={(e) => setSemanticEnabled(e.target.checked)}
                      className="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500 focus:ring-2"
                    />
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-700">
                        Semantic Search
                      </span>
                      <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full font-medium">
                        EXPERIMENTAL
                      </span>
                    </div>
                  </label>
                  <p className="text-xs text-gray-500 mt-1 ml-7">
                    Find semantically similar papers using embedding-based similarity.
                  </p>
                  {semanticEnabled && (
                    <div className="mt-2 ml-7 flex flex-wrap items-center gap-3">
                      <label className="text-sm text-gray-700">Mode</label>
                      <select
                        value={semanticMode}
                        onChange={(e) => setSemanticMode(e.target.value as 'rerank' | 'hybrid')}
                        className="px-2 py-1 text-sm border border-gray-300 rounded"
                      >
                        <option value="rerank">Re-rank top-K</option>
                        <option value="hybrid">Hybrid (combine)</option>
                      </select>
                      <label className="text-sm text-gray-700">Top-K</label>
                      <input
                        type="number"
                        min={10}
                        max={1000}
                        value={semanticTopK}
                        onChange={(e) => setSemanticTopK(parseInt(e.target.value) || 200)}
                        className="w-24 px-2 py-1 text-sm border border-gray-300 rounded"
                      />
                    </div>
                  )}
                </div>
                {/* Search Sources Selection */}
                <div className="mt-4">
                  <label className="text-sm font-medium text-gray-700 mb-3 block">
                    Search Sources
                  </label>
                  <div className="space-y-2">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={searchSources.includes('acl')}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSearchSources([...searchSources, 'acl'])
                          } else {
                            const newSources = searchSources.filter(s => s !== 'acl')
                            if (newSources.length > 0) {
                              setSearchSources(newSources)
                            }
                          }
                        }}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
                      />
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-700">ACL Anthology</span>
                        <div className="relative group">
                          <div className="w-4 h-4 bg-gray-100 rounded-full flex items-center justify-center cursor-help border border-gray-300 hover:bg-gray-200 transition-colors duration-200">
                            <span className="text-xs text-gray-600 font-bold">?</span>
                          </div>
                          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 scale-95 group-hover:opacity-100 group-hover:scale-100 transition-all duration-200 ease-out bg-gray-900 text-white text-sm rounded py-2 px-3 z-50 shadow-xl pointer-events-none">
                            <div className="w-80 text-center">
                              Official repository of computational linguistics papers (113,000+ papers)
                            </div>
                            <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                          </div>
                        </div>
                      </div>
                    </label>
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={searchSources.includes('arxiv')}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSearchSources([...searchSources, 'arxiv'])
                          } else {
                            const newSources = searchSources.filter(s => s !== 'arxiv')
                            if (newSources.length > 0) {
                              setSearchSources(newSources)
                            }
                          }
                        }}
                        className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500 focus:ring-2"
                      />
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-700">arXiv</span>
                        <div className="relative group">
                          <div className="w-4 h-4 bg-gray-100 rounded-full flex items-center justify-center cursor-help border border-gray-300 hover:bg-gray-200 transition-colors duration-200">
                            <span className="text-xs text-gray-600 font-bold">?</span>
                          </div>
                          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 scale-95 group-hover:opacity-100 group-hover:scale-100 transition-all duration-200 ease-out bg-gray-900 text-white text-sm rounded py-2 px-3 z-50 shadow-xl pointer-events-none">
                            <div className="w-80 text-center">
                              Pre-print repository covering all scientific fields (2M+ papers)
                            </div>
                            <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                          </div>
                        </div>
                      </div>
                    </label>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    Select one or both sources. arXiv includes pre-prints from all scientific fields.
                  </p>
                </div>
                {/* Experimental Search Toggle */}
                <div className="mt-4">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={experimentalMode}
                      onChange={(e) => setExperimentalMode(e.target.checked)}
                      className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500 focus:ring-2"
                    />
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-700">Experimental Search Pipeline</span>
                      <div className="relative group">
                        <div className="w-4 h-4 bg-gray-100 rounded-full flex items-center justify-center cursor-help border border-gray-300 hover:bg-gray-200 transition-colors duration-200">
                          <span className="text-xs text-gray-600 font-bold">?</span>
                        </div>
                        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 scale-95 group-hover:opacity-100 group-hover:scale-100 transition-all duration-200 ease-out bg-gray-900 text-white text-sm rounded py-2 px-3 z-50 shadow-xl pointer-events-none">
                          <div className="w-96 text-center">
                            Advanced IR pipeline with spell correction, query expansion, BM25 + fuzzy matching, semantic embeddings, and neural re-ranking
                          </div>
                          <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                        </div>
                      </div>
                      {experimentalMode && (
                        <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full font-medium">
                          EXPERIMENTAL
                        </span>
                      )}
                    </div>
                  </label>
                  <p className="text-xs text-gray-500 mt-1 ml-7">
                    Uses advanced AI techniques for improved search accuracy (ACL only)
                  </p>
                </div>

                {/* Sort controls */}
                <div className="mt-4 flex items-center gap-3 ml-1">
                  <label className="text-sm text-gray-700">Sort by</label>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as 'relevance' | 'year')}
                    className="px-2 py-1 text-sm border border-gray-300 rounded"
                  >
                    <option value="relevance">Relevance</option>
                    <option value="year">Year (desc)</option>
                  </select>
                </div>
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                <h3 className="text-red-800 font-semibold">Search Error</h3>
                <p className="text-red-600 mt-1">{error}</p>
              </div>
            )}

            {loading && (
              <div className="flex justify-center py-12">
                <LoadingSpinner />
              </div>
            )}

            {results && !loading && (
              <SearchResults results={results} />
            )}

            {!results && !loading && !error && (
              <div className="text-center py-12">
                <Search className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-600 mb-2">Ready to search</h3>
                <p className="text-gray-500">
                  Enter a query above to search through computational linguistics papers
                </p>
                <div className="mt-6 text-sm text-gray-400">
                  <p>Try searches like:</p>
                  <div className="flex flex-wrap justify-center gap-2 mt-2">
                    <span className="bg-gray-100 px-3 py-1 rounded-full">attention mechanism</span>
                    <span className="bg-gray-100 px-3 py-1 rounded-full">&quot;neural machine translation&quot;</span>
                    <span className="bg-gray-100 px-3 py-1 rounded-full">BERT OR GPT</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

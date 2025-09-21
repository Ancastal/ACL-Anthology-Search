'use client'

import { useState, useEffect } from 'react'
import { ExternalLink, Users, Calendar, MapPin, FileText, Tag, Download, Eye, EyeOff, Copy, BookMarked, Info, Loader } from 'lucide-react'
import ResultsViz from './ResultsViz'

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

interface SearchResultsProps {
  results: SearchResponse
}

function formatAuthors(authors: string[], maxDisplay: number = 3): string {
  if (authors.length <= maxDisplay) {
    return authors.join(', ')
  }
  return `${authors.slice(0, maxDisplay).join(', ')} et al. (${authors.length} total)`
}

function ResultCard({ result, index, showAbstract, onAuthorClick }: { 
  result: SearchResult, 
  index: number, 
  showAbstract: boolean,
  onAuthorClick: (name: string) => void,
}) {
  const [abstractExpanded, setAbstractExpanded] = useState(false)
  const [metadata, setMetadata] = useState<SearchResult['metadata'] | null>(null)
  const [loadingMd, setLoadingMd] = useState(false)
  const [mdError, setMdError] = useState<string | null>(null)

  // Generate COinS (ContextObjects in Spans) for Zotero detection
  const generateCOinS = (result: SearchResult): string => {
    // Create proper COinS format according to Zotero requirements
    const coins: { [key: string]: string } = {}
    
    // Required COinS parameters
    coins['url_ver'] = 'Z39.88-2004'
    coins['ctx_ver'] = 'Z39.88-2004'
    coins['rfr_id'] = 'info:sid/aclanthology-search'
    coins['rft_val_fmt'] = 'info:ofi/fmt:kev:mtx:book'
    
    // Document type - use 'proceeding' for conference papers
    coins['rft.genre'] = 'proceeding'
    coins['rft.atitle'] = result.title
    coins['rft.date'] = result.year
    
    // Authors
    if (result.authors.length > 0) {
      // First author name parsing
      const firstAuthor = result.authors[0].trim()
      const nameParts = firstAuthor.split(' ')
      if (nameParts.length >= 2) {
        coins['rft.aulast'] = nameParts[nameParts.length - 1]
        coins['rft.aufirst'] = nameParts.slice(0, -1).join(' ')
      }
      
      // All authors
      result.authors.forEach((author, index) => {
        coins[`rft.au${index > 0 ? index + 1 : ''}`] = author.trim()
      })
    }
    
    // Conference/venue information
    if (result.venue.length > 0) {
      coins['rft.btitle'] = result.venue.join(', ')
    }
    
    // URL to paper
    coins['rft_id'] = result.url
    
    // Abstract if available - provide full abstract for Zotero
    if (result.abstract) {
      coins['rft.description'] = result.abstract
    }
    
    // Manual URL encoding to ensure proper format
    return Object.entries(coins)
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
      .join('&')
  }

  // Generate BibTeX citation
  const generateBibTeX = (result: SearchResult) => {
    const authors = result.authors.map(author => {
      const parts = author.trim().split(' ')
      if (parts.length >= 2) {
        const lastName = parts[parts.length - 1]
        const firstNames = parts.slice(0, -1).join(' ')
        return `${lastName}, ${firstNames}`
      }
      return author
    }).join(' and ')

    const venue = result.venue.length > 0 ? result.venue[0] : 'Unknown'
    const bibKey = `${result.authors[0]?.split(' ')[0]?.toLowerCase() || 'unknown'}${result.year}${result.title.split(' ')[0]?.toLowerCase() || ''}`

    return `@inproceedings{${bibKey},
  title={${result.title}},
  author={${authors}},
  booktitle={${venue}},
  year={${result.year}},
  url={${result.url}}${result.abstract ? `,
  abstract={${result.abstract.replace(/[{}]/g, '')}}` : ''}
}`
  }

  // Copy BibTeX to clipboard
  const copyBibTeX = async (result: SearchResult) => {
    const bibTeX = generateBibTeX(result)
    try {
      await navigator.clipboard.writeText(bibTeX)
    } catch (err) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea')
      textArea.value = bibTeX
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
    }
  }


  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
      {/* COinS span for Zotero detection - hidden from users */}
      <span className="Z3988" title={generateCOinS(result)} style={{ display: 'none' }}></span>
      
      {/* Header */}
      <div className="flex items-start gap-3 mb-3">
        <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-semibold">
          {index}
        </div>
        <div className="flex-grow">
          <div className="flex items-start justify-between gap-3 mb-2">
            <h3 className="text-lg font-semibold text-gray-900 leading-tight flex-1">
              <a
                href={result.url}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-blue-600 transition-colors"
              >
                {result.title}
              </a>
            </h3>
            <div className="flex items-center gap-2 flex-shrink-0">
              {/* Source badge */}
              {result.source && (
                <div className={`flex items-center gap-1 p-2 rounded text-sm font-medium ${
                  result.source === 'arXiv'
                    ? 'bg-green-50 text-green-600'
                    : 'bg-blue-50 text-blue-600'
                }`}>
                  <span>{result.source === 'arXiv' ? 'arXiv' : 'ACL'}</span>
                </div>
              )}

              {/* Year badge */}
              <div className="flex items-center gap-1 p-2 bg-gray-50 text-gray-600 rounded text-sm font-medium">
                <Calendar className="w-4 h-4" />
                <span>{result.year}</span>
              </div>
            </div>
          </div>
          
          {/* Metadata */}
          <div className="space-y-2">
            <div className="flex items-center gap-1 text-sm text-gray-600">
              <Users className="w-4 h-4 flex-shrink-0" />
              <div className="min-w-0 flex-1">
                {result.authors.length <= 3 ? (
                  <span className="truncate block">
                    {result.authors.map((a, i) => (
                      <span key={`${a}-${i}`}>
                        <button onClick={() => onAuthorClick(a)} className="text-blue-600 hover:text-blue-800 hover:underline">
                          {a}
                        </button>{i < result.authors.length - 1 ? ', ' : ''}
                      </span>
                    ))}
                  </span>
                ) : (
                  <span className="truncate block">
                    {result.authors.slice(0, 2).map((a, i) => (
                      <span key={`${a}-${i}`}>
                        <button onClick={() => onAuthorClick(a)} className="text-blue-600 hover:text-blue-800 hover:underline">
                          {a}
                        </button>{i < 1 ? ', ' : ''}
                      </span>
                    ))}
                    <span className="text-gray-500"> et al. ({result.authors.length} total)</span>
                  </span>
                )}
              </div>
            </div>
            
            {result.venue.length > 0 && (
              <div className="flex items-center gap-1 text-sm text-gray-600">
                <MapPin className="w-4 h-4" />
                <span>{result.venue.join(', ')}</span>
              </div>
            )}
          </div>
        </div>
        
        <div className="flex-shrink-0 flex items-center gap-2">
          <button
            onClick={() => copyBibTeX(result)}
            className="p-2 text-gray-400 hover:text-purple-600 transition-colors"
            title="Copy BibTeX"
          >
            <Copy className="w-5 h-5" />
          </button>
          <a
            href={result.url}
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
            title="Open paper"
          >
            <ExternalLink className="w-5 h-5" />
          </a>
        </div>
      </div>

      {/* Match indicators */}
      {result.match_fields.length > 0 && (
        <div className="flex items-center gap-2 mb-3">
          <Tag className="w-4 h-4 text-gray-400" />
          <div className="flex flex-wrap gap-1">
            {result.match_fields.map((field) => (
              <span
                key={field}
                className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full capitalize"
              >
                {field}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Abstract */}
      {showAbstract && result.abstract && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="flex items-center gap-2 mb-2">
            <FileText className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">Abstract</span>
            <button
              onClick={() => setAbstractExpanded(!abstractExpanded)}
              className="ml-auto text-gray-400 hover:text-gray-600 transition-colors"
            >
              {abstractExpanded ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
          <p className={`text-sm text-gray-600 leading-relaxed ${
            !abstractExpanded ? 'line-clamp-3' : ''
          }`}>
            {result.abstract}
          </p>
          {!abstractExpanded && result.abstract.length > 300 && (
            <button
              onClick={() => setAbstractExpanded(true)}
              className="mt-1 text-sm text-blue-600 hover:text-blue-800 transition-colors"
            >
              Show more
            </button>
          )}
        </div>
      )}

      {/* On-demand metadata fetch */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="flex items-center gap-2 mb-2">
          <Info className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">More details</span>
          <button
            onClick={async () => {
              if (metadata || loadingMd) return
              setMdError(null)
              setLoadingMd(true)
              try {
                const body = {
                  doi: result.doi || null,
                  title: result.title,
                  authors: result.authors,
                  year: parseInt(result.year) || undefined,
                  max_related: 3
                }
                const resp = await fetch('http://127.0.0.1:8000/metadata', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify(body)
                })
                if (!resp.ok) {
                  const err = await resp.json().catch(() => ({}))
                  throw new Error(err.detail || `HTTP ${resp.status}`)
                }
                const data = await resp.json()
                setMetadata(data.metadata)
              } catch (e: any) {
                setMdError(e?.message || 'Failed to load metadata')
              } finally {
                setLoadingMd(false)
              }
            }}
            className={`ml-auto px-3 py-1 text-sm rounded border ${metadata ? 'text-gray-400 border-gray-200 cursor-default' : 'text-blue-600 border-blue-200 hover:bg-blue-50'}`}
            disabled={!!metadata || loadingMd}
          >
            {loadingMd ? (
              <span className="inline-flex items-center gap-1"><Loader className="w-3 h-3 animate-spin" /> Loading…</span>
            ) : metadata ? 'Loaded' : 'Load metadata'}
          </button>
        </div>
        {mdError && (
          <div className="text-sm text-red-600">{mdError}</div>
        )}
        {metadata && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="text-sm text-gray-700">
                <div><span className="font-medium">Citations:</span> {metadata.citations_count ?? 'N/A'}</div>
                {typeof metadata.references_count === 'number' && (
                  <div><span className="font-medium">References:</span> {metadata.references_count}</div>
                )}
                {result.doi && (
                  <div className="truncate"><span className="font-medium">DOI:</span> {result.doi}</div>
                )}
              </div>
              <div className="md:col-span-2 text-sm text-gray-700">
                {(metadata.related_works && metadata.related_works.length > 0) ? (
                  <div>
                    <div className="font-medium mb-1">Related works</div>
                    <ul className="list-disc ml-5 space-y-1">
                      {metadata.related_works.slice(0,3).map((rw, i) => (
                        <li key={i} className="truncate">
                          {rw.url ? (
                            <a href={rw.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800">
                              {rw.title || 'Untitled'}
                            </a>
                          ) : (
                            <span>{rw.title || 'Untitled'}</span>
                          )}
                          {rw.year ? <span className="text-gray-500"> ({rw.year})</span> : null}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <div className="text-gray-500">No related works available</div>
                )}
              </div>
          </div>
          {(metadata.provider || metadata.note) && (
            <div className="mt-2 text-xs text-gray-400">
              {metadata.provider ? `Metadata: ${metadata.provider}` : ''}
              {metadata.note ? `${metadata.provider ? ' • ' : ''}${metadata.note}` : ''}
            </div>
          )}
          </>
        )}
      </div>
    </div>
  )
}

export default function SearchResults({ results }: SearchResultsProps) {
  const [showAbstracts, setShowAbstracts] = useState(true)
  const [authorModal, setAuthorModal] = useState<string | null>(null)

  // Trigger Zotero detection after results load
  useEffect(() => {
    // Dispatch a custom event to notify Zotero of new content
    const event = new CustomEvent('ZoteroItemUpdated', {
      bubbles: true,
      detail: { results: results.results }
    })
    document.dispatchEvent(event)

    // Also try triggering a DOM change event that Zotero might listen for
    setTimeout(() => {
      const metaEvent = new Event('DOMContentLoaded', { bubbles: true })
      document.dispatchEvent(metaEvent)
    }, 100)

    // Try to trigger Zotero's page scanning
    setTimeout(() => {
      // Trigger a custom event that might cause Zotero to rescan
      window.postMessage({ type: 'ZoteroScanPage' }, '*')
      
      // Try dispatching a mutation observer-like event
      const mutationEvent = new Event('DOMSubtreeModified', { bubbles: true })
      document.dispatchEvent(mutationEvent)
    }, 200)
  }, [results])

  // Generate BibTeX for a single result (helper function)
  const generateSingleBibTeX = (result: SearchResult) => {
    const authors = result.authors.map(author => {
      const parts = author.trim().split(' ')
      if (parts.length >= 2) {
        const lastName = parts[parts.length - 1]
        const firstNames = parts.slice(0, -1).join(' ')
        return `${lastName}, ${firstNames}`
      }
      return author
    }).join(' and ')

    const venue = result.venue.length > 0 ? result.venue[0] : 'Unknown'
    const bibKey = `${result.authors[0]?.split(' ')[0]?.toLowerCase() || 'unknown'}${result.year}${result.title.split(' ')[0]?.toLowerCase() || ''}`

    return `@inproceedings{${bibKey},
  title={${result.title}},
  author={${authors}},
  booktitle={${venue}},
  year={${result.year}},
  url={${result.url}}${result.abstract ? `,
  abstract={${result.abstract.replace(/[{}]/g, '')}}` : ''}
}`
  }

  const downloadCSV = () => {
    const headers = ['ID', 'Title', 'Authors', 'Year', 'Venue', 'URL', 'Abstract']
    const csvContent = [
      headers.join(','),
      ...results.results.map(result => [
        result.paper_id,
        `"${result.title.replace(/"/g, '""')}"`,
        `"${result.authors.join('; ')}"`,
        result.year,
        `"${result.venue.join('; ')}"`,
        result.url,
        `"${(result.abstract || '').replace(/"/g, '""')}"`
      ].join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `acl_search_results_${Date.now()}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  }

  const downloadBibTeX = () => {
    const bibTexContent = results.results.map(result => generateSingleBibTeX(result)).join('\n\n')
    
    const blob = new Blob([bibTexContent], { type: 'text/plain' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `acl_search_results_${Date.now()}.bib`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  }

  return (
    <div>
      {/* Results header with stats */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold">{results.total_count}</div>
            <div className="text-blue-100">Papers Found</div>
          </div>
          <div>
            <div className="text-2xl font-bold">{results.search_time.toFixed(2)}s</div>
            <div className="text-blue-100">Search Time</div>
          </div>
          <div>
            <div className="text-2xl font-bold">{results.stats.unique_venues}</div>
            <div className="text-blue-100">Venues</div>
          </div>
          <div>
            <div className="text-2xl font-bold">
              {results.stats.year_range 
                ? `${results.stats.year_range[0]}-${results.stats.year_range[1]}`
                : 'N/A'
              }
            </div>
            <div className="text-blue-100">Year Range</div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="mb-6">
        {/* Zotero bulk save notice */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
          <div className="flex items-center gap-2 mb-2">
            <BookMarked className="w-5 h-5 text-green-600" />
            <span className="font-semibold text-green-800">Bulk Save to Zotero</span>
          </div>
          <p className="text-sm text-green-700">
            This page uses <strong>COinS metadata</strong> (same as ACL Anthology). Look for the <strong>folder icon</strong> 📁 in your browser's address bar, then click it to select and save multiple papers at once!
          </p>
          <div className="mt-2 text-xs text-green-600">
            💡 If you see a folder icon instead of a single paper icon, you can bulk import all results
          </div>
        </div>
        
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={showAbstracts}
                onChange={(e) => setShowAbstracts(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Show abstracts</span>
            </label>
          </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={downloadBibTeX}
            className="flex items-center gap-2 px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors"
            title="Download BibTeX file for Zotero import"
          >
            <BookMarked className="w-4 h-4" />
            Download BibTeX
          </button>
          <button
            onClick={downloadCSV}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <Download className="w-4 h-4" />
            Download CSV
          </button>
          </div>
        </div>
      </div>

      {/* Visualizations */}
      <div className="mb-6">
        <ResultsViz results={results.results} />
      </div>

      {/* Results list */}
      <div className="space-y-4">
        {results.results.map((result, index) => (
          <ResultCard
            key={`${result.paper_id}-${index}`}
            result={result}
            index={index + 1}
            showAbstract={showAbstracts}
            onAuthorClick={(name) => setAuthorModal(name)}
          />
        ))}
      </div>
      {authorModal && (
        <div>
          {(() => {
            const AuthorModal = require('./AuthorModal').default
            return <AuthorModal name={authorModal} onClose={() => setAuthorModal(null)} />
          })()}
        </div>
      )}

      {/* Footer info */}
      {results.total_count >= 1000 && (
        <div className="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            <strong>Note:</strong> Showing first {results.results.length} results of {results.total_count} total matches.
            Consider refining your search or using filters to narrow down the results.
          </p>
        </div>
      )}
    </div>
  )
}

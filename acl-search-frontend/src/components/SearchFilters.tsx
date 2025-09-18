'use client'

import { Filter, Calendar, Building2, Settings } from 'lucide-react'

interface SearchFilters {
  fields: string[]
  yearRange: [number, number] | null
  venues: string[]
  limit: number
}

interface ApiStats {
  total_papers: number
  year_range: [number, number]
  total_venues: number
  common_venues: string[]
}

interface SearchFiltersProps {
  filters: SearchFilters
  onFiltersChange: (filters: SearchFilters) => void
  apiStats: ApiStats | null
}

export default function SearchFiltersComponent({ filters, onFiltersChange, apiStats }: SearchFiltersProps) {
  const updateFilters = (updates: Partial<SearchFilters>) => {
    onFiltersChange({ ...filters, ...updates })
  }

  const fieldOptions = [
    { value: 'title', label: 'Title' },
    { value: 'abstract', label: 'Abstract' },
    { value: 'authors', label: 'Authors' }
  ]

  const limitOptions = [50, 100, 200, 500, 1000]

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-4 border-b bg-gray-50 rounded-t-lg">
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-600" />
            <h2 className="font-semibold text-gray-800">Search Filters</h2>
          </div>
        </div>
        
        <div className="p-4 space-y-6">
          {/* Search Fields */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
              <Settings className="w-4 h-4" />
              Search Fields
            </h3>
            <div className="space-y-2">
              {fieldOptions.map((field) => (
                <label key={field.value} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filters.fields.includes(field.value)}
                    onChange={(e) => {
                      const newFields = e.target.checked
                        ? [...filters.fields, field.value]
                        : filters.fields.filter(f => f !== field.value)
                      updateFilters({ fields: newFields })
                    }}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-600">{field.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Year Range */}
          {apiStats && (
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                Publication Year
              </h3>
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={filters.yearRange !== null}
                    onChange={(e) => {
                      updateFilters({
                        yearRange: e.target.checked ? apiStats.year_range : null
                      })
                    }}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-600">Enable year filter</span>
                </div>
                
                {filters.yearRange && (
                  <div className="space-y-2">
                    <div className="flex gap-2 items-center">
                      <input
                        type="number"
                        min={apiStats.year_range[0]}
                        max={apiStats.year_range[1]}
                        value={filters.yearRange[0]}
                        onChange={(e) => {
                          const newMin = parseInt(e.target.value)
                          updateFilters({
                            yearRange: [newMin, filters.yearRange![1]]
                          })
                        }}
                        className="w-20 px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
                      />
                      <span className="text-xs text-gray-500">to</span>
                      <input
                        type="number"
                        min={apiStats.year_range[0]}
                        max={apiStats.year_range[1]}
                        value={filters.yearRange[1]}
                        onChange={(e) => {
                          const newMax = parseInt(e.target.value)
                          updateFilters({
                            yearRange: [filters.yearRange![0], newMax]
                          })
                        }}
                        className="w-20 px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
                      />
                    </div>
                    <div className="text-xs text-gray-500">
                      Available: {apiStats.year_range[0]} - {apiStats.year_range[1]}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Venues */}
          {apiStats && (
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
                <Building2 className="w-4 h-4" />
                Venues
              </h3>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {apiStats.common_venues.map((venue) => (
                  <label key={venue} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={filters.venues.includes(venue)}
                      onChange={(e) => {
                        const newVenues = e.target.checked
                          ? [...filters.venues, venue]
                          : filters.venues.filter(v => v !== venue)
                        updateFilters({ venues: newVenues })
                      }}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-600">{venue}</span>
                  </label>
                ))}
              </div>
              {filters.venues.length > 0 && (
                <button
                  onClick={() => updateFilters({ venues: [] })}
                  className="mt-2 text-xs text-blue-600 hover:text-blue-800"
                >
                  Clear all venues
                </button>
              )}
            </div>
          )}

          {/* Results Limit */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-3">Results Limit</h3>
            <select
              value={filters.limit}
              onChange={(e) => updateFilters({ limit: parseInt(e.target.value) })}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
            >
              {limitOptions.map((limit) => (
                <option key={limit} value={limit}>
                  {limit} results
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Quick Actions</h3>
        <div className="space-y-2">
          <button
            onClick={() => updateFilters({
              fields: ['title', 'abstract', 'authors'],
              yearRange: null,
              venues: [],
              limit: 100
            })}
            className="w-full text-left px-3 py-2 text-xs text-gray-600 hover:bg-gray-50 rounded transition-colors"
          >
            Reset all filters
          </button>
          <button
            onClick={() => updateFilters({
              yearRange: apiStats ? [2020, apiStats.year_range[1]] : null
            })}
            className="w-full text-left px-3 py-2 text-xs text-gray-600 hover:bg-gray-50 rounded transition-colors"
          >
            Recent papers (2020+)
          </button>
        </div>
      </div>
    </div>
  )
}
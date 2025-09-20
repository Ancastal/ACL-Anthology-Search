'use client'

import { useMemo } from 'react'
import { BarChart2, Users, Building2 } from 'lucide-react'

interface SearchResult {
  paper_id: string
  title: string
  authors: string[]
  year: string
  venue: string[]
}

interface Props {
  results: SearchResult[]
}

export default function ResultsViz({ results }: Props) {
  const { years, venues, authors } = useMemo(() => {
    const y: Record<string, number> = {}
    const v: Record<string, number> = {}
    const a: Record<string, number> = {}
    for (const r of results) {
      if (r.year) y[r.year] = (y[r.year] || 0) + 1
      for (const ve of r.venue || []) v[ve] = (v[ve] || 0) + 1
      for (const au of r.authors || []) a[au] = (a[au] || 0) + 1
    }
    const years = Object.entries(y).map(([year, count]) => ({ year: parseInt(year, 10), count })).sort((a, b) => a.year - b.year)
    const venues = Object.entries(v).map(([venue, count]) => ({ venue, count })).sort((a, b) => b.count - a.count).slice(0, 12)
    const authors = Object.entries(a).map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count).slice(0, 12)
    return { years, venues, authors }
  }, [results])

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full">
      <div className="bg-white border rounded-lg p-3 w-full min-w-0 flex flex-col">
        <div className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2"><BarChart2 className="w-4 h-4"/>Year histogram</div>
        {years.length > 0 ? (
          <div className="flex-1 flex flex-col w-full min-h-0">
            <div className="flex items-end flex-1 w-full">
              {years.map((y) => {
                const maxCount = Math.max(...years.map(yr => yr.count))
                return (
                  <div key={y.year} className="flex items-end flex-1 min-w-0 px-px h-full group relative" title={`${y.year}: ${y.count}`}>
                    <div className="bg-indigo-500 w-full min-h-[2px] group-hover:bg-indigo-600 transition-colors" style={{ height: `${(y.count / maxCount) * 100}%` }}></div>
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-1 px-2 py-1 bg-gray-800 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity z-10">
                      {y.year}: {y.count}
                    </div>
                  </div>
                )
              })}
            </div>
            <div className="flex mt-1 h-5 w-full flex-shrink-0">
              {years.map((y, index) => {
                let showLabel = false
                let labelText = ''

                if (years.length <= 6) {
                  showLabel = true
                  labelText = String(y.year)
                } else if (years.length <= 12) {
                  showLabel = index % 2 === 0
                  labelText = String(y.year).slice(-2)
                } else if (years.length <= 20) {
                  showLabel = index % 3 === 0 || index === years.length - 1
                  labelText = String(y.year).slice(-2)
                } else {
                  const step = Math.max(1, Math.floor(years.length / 8))
                  showLabel = index % step === 0 || index === years.length - 1
                  labelText = String(y.year).slice(-2)
                }

                return (
                  <div key={y.year} className="flex justify-center text-[10px] text-gray-600 flex-1 min-w-0 px-px leading-tight">
                    {showLabel ? labelText : ''}
                  </div>
                )
              })}
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center flex-1 text-xs text-gray-500">No data</div>
        )}
      </div>
      <div className="bg-white border rounded-lg p-3 w-full min-w-0">
        <div className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2"><Building2 className="w-4 h-4"/>Top venues</div>
        <div className="space-y-1">
          {venues.map(v => (
            <div key={v.venue} className="flex items-center gap-2 text-xs">
              <div className="w-28 truncate" title={v.venue}>{v.venue}</div>
              <div className="flex-1 bg-gray-100 rounded h-2">
                <div className="bg-blue-500 h-2 rounded" style={{ width: `${Math.min(100, (v.count / (venues[0]?.count || 1)) * 100)}%` }}></div>
              </div>
              <div className="w-6 text-right">{v.count}</div>
            </div>
          ))}
          {venues.length === 0 && <div className="text-xs text-gray-500">No data</div>}
        </div>
      </div>
      <div className="bg-white border rounded-lg p-3 w-full min-w-0">
        <div className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2"><Users className="w-4 h-4"/>Top authors</div>
        <div className="space-y-1">
          {authors.map(a => (
            <div key={a.name} className="flex items-center gap-2 text-xs">
              <div className="w-40 truncate" title={a.name}>{a.name}</div>
              <div className="flex-1 bg-gray-100 rounded h-2">
                <div className="bg-green-500 h-2 rounded" style={{ width: `${Math.min(100, (a.count / (authors[0]?.count || 1)) * 100)}%` }}></div>
              </div>
              <div className="w-6 text-right">{a.count}</div>
            </div>
          ))}
          {authors.length === 0 && <div className="text-xs text-gray-500">No data</div>}
        </div>
      </div>
    </div>
  )
}


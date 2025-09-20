'use client'

import { useEffect, useState } from 'react'
import { X, Users, BarChart2 } from 'lucide-react'

interface AuthorData {
  name: string
  total_papers: number
  coauthors: { name: string, count: number }[]
  venues: { venue: string, count: number }[]
  years: { year: number, count: number }[]
  papers: { paper_id: string, title: string, year: string, url: string, venue: string[], authors: string[] }[]
}

interface AuthorModalProps {
  name: string
  onClose: () => void
}

export default function AuthorModal({ name, onClose }: AuthorModalProps) {
  const [data, setData] = useState<AuthorData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchAuthor = async () => {
      setLoading(true)
      setError(null)
      try {
        const resp = await fetch(`http://127.0.0.1:8000/author?name=${encodeURIComponent(name)}`)
        if (!resp.ok) {
          const err = await resp.json().catch(() => ({} as any))
          throw new Error(err.detail || `HTTP ${resp.status}`)
        }
        const json = await resp.json()
        setData(json)
      } catch (e: any) {
        setError(e?.message || 'Failed to load author data')
      } finally {
        setLoading(false)
      }
    }
    fetchAuthor()
  }, [name])

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[85vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="p-4 border-b flex items-center justify-between">
          <div>
            <div className="text-lg font-semibold">{name}</div>
            {!loading && data && (
              <div className="text-sm text-gray-500">{data.total_papers} publications</div>
            )}
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700"><X className="w-5 h-5"/></button>
        </div>
        <div className="p-4">
          {loading && <div className="text-gray-500">Loading…</div>}
          {error && <div className="text-red-600">{error}</div>}
          {data && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="md:col-span-1">
                  <div className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2"><Users className="w-4 h-4"/>Top co-authors</div>
                  <div className="space-y-1">
                    {data.coauthors.slice(0,10).map((c) => (
                      <div key={c.name} className="flex items-center justify-between text-sm">
                        <span className="truncate mr-2">{c.name}</span>
                        <span className="text-gray-500">{c.count}</span>
                      </div>
                    ))}
                    {data.coauthors.length === 0 && <div className="text-xs text-gray-500">No co-authors found.</div>}
                  </div>
                </div>
                <div className="md:col-span-2">
                  <div className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2"><BarChart2 className="w-4 h-4"/>Publications by year</div>
                  <div className="flex items-end gap-1 h-28 border p-2 rounded bg-gray-50">
                    {data.years.map((y) => (
                      <div key={y.year} className="flex flex-col items-center" title={`${y.year}: ${y.count}`}>
                        <div className="bg-blue-500 w-3" style={{ height: `${Math.max(4, y.count * 8)}px` }}></div>
                        <div className="text-[10px] text-gray-500 mt-1">{y.year}</div>
                      </div>
                    ))}
                    {data.years.length === 0 && <div className="text-xs text-gray-500">No publications.</div>}
                  </div>
                </div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-700 mb-2">Venues</div>
                <div className="flex flex-wrap gap-2">
                  {data.venues.slice(0,20).map(v => (
                    <span key={v.venue} className="px-2 py-1 text-xs bg-gray-100 rounded border">{v.venue} <span className="text-gray-500">({v.count})</span></span>
                  ))}
                  {data.venues.length === 0 && <div className="text-xs text-gray-500">No venues.</div>}
                </div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-700 mb-2">Publications</div>
                <ul className="space-y-2">
                  {data.papers.slice(0,50).map(p => (
                    <li key={p.paper_id} className="text-sm">
                      <a href={p.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800">{p.title}</a> <span className="text-gray-500">({p.year})</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}


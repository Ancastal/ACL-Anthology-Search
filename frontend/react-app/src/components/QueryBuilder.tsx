'use client'

import { useState, useEffect } from 'react'
import { PlusCircle, MinusCircle, Brackets, Quote } from 'lucide-react'

type ClauseOp = 'AND' | 'OR'

interface Clause {
  op: ClauseOp
  not: boolean
  text: string
  exact: boolean
}

interface Group {
  op: ClauseOp // operator connecting this group with previous group (ignored for first)
  not: boolean
  wrap: boolean // whether to wrap this group's expression in parentheses
  clauses: Clause[]
}

interface QueryBuilderProps {
  onChange: (query: string) => void
  initialQuery?: string
}

export default function QueryBuilder({ onChange, initialQuery }: QueryBuilderProps) {
  const [groups, setGroups] = useState<Group[]>([{
    op: 'AND', not: false, wrap: false,
    clauses: [{ op: 'AND', not: false, text: '', exact: false }]
  }])

  // Parse a query string into groups and clauses
  const parseQuery = (queryString: string): Group[] => {
    if (!queryString.trim()) {
      return [{
        op: 'AND', not: false, wrap: false,
        clauses: [{ op: 'AND', not: false, text: '', exact: false }]
      }]
    }

    // Simple tokenizer - handles basic boolean logic
    const tokens = queryString
      .replace(/\(/g, ' ( ')
      .replace(/\)/g, ' ) ')
      .split(/\s+/)
      .filter(token => token.length > 0)

    const groups: Group[] = []
    let currentGroup: Group = { op: 'AND', not: false, wrap: false, clauses: [] }
    let currentClause: Partial<Clause> = { op: 'AND', not: false, text: '', exact: false }
    let expectingTerm = true
    let groupLevel = 0

    const finishClause = () => {
      if (currentClause.text && currentClause.text.trim()) {
        currentGroup.clauses.push(currentClause as Clause)
        currentClause = { op: 'AND', not: false, text: '', exact: false }
      }
    }

    const finishGroup = () => {
      finishClause()
      if (currentGroup.clauses.length > 0) {
        groups.push(currentGroup)
        currentGroup = { op: 'AND', not: false, wrap: false, clauses: [] }
      }
    }

    for (let i = 0; i < tokens.length; i++) {
      const token = tokens[i]
      const upperToken = token.toUpperCase()

      if (upperToken === 'AND' || upperToken === 'OR') {
        if (!expectingTerm && currentClause.text) {
          finishClause()
          if (i + 1 < tokens.length) {
            currentClause.op = upperToken as ClauseOp
          }
          expectingTerm = true
        }
      } else if (upperToken === 'NOT') {
        if (expectingTerm) {
          currentClause.not = true
        }
      } else if (token === '(') {
        if (groupLevel === 0 && currentGroup.clauses.length > 0) {
          finishGroup()
        }
        currentGroup.wrap = true
        groupLevel++
      } else if (token === ')') {
        groupLevel--
        if (groupLevel === 0) {
          finishGroup()
        }
      } else {
        // Regular term
        if (currentClause.text) {
          currentClause.text += ' ' + token
        } else {
          currentClause.text = token
        }

        // Check if it's a quoted phrase
        if (token.startsWith('"') && token.endsWith('"')) {
          currentClause.exact = true
          currentClause.text = token.slice(1, -1) // Remove quotes
        } else if (token.startsWith('"')) {
          currentClause.exact = true
          currentClause.text = token.slice(1) // Remove opening quote
          // Continue collecting until closing quote
          let j = i + 1
          while (j < tokens.length && !tokens[j].endsWith('"')) {
            currentClause.text += ' ' + tokens[j]
            j++
          }
          if (j < tokens.length && tokens[j].endsWith('"')) {
            currentClause.text += ' ' + tokens[j].slice(0, -1) // Remove closing quote
            i = j // Skip to end of phrase
          }
        }

        expectingTerm = false
      }
    }

    finishGroup()

    // Ensure we have at least one group with one clause
    if (groups.length === 0) {
      groups.push({
        op: 'AND', not: false, wrap: false,
        clauses: [{ op: 'AND', not: false, text: '', exact: false }]
      })
    }

    return groups
  }

  // Load initial query when provided
  useEffect(() => {
    if (initialQuery && initialQuery.trim()) {
      const parsedGroups = parseQuery(initialQuery)
      setGroups(parsedGroups)
    }
  }, [initialQuery])

  const buildQuery = (): string => {
    const groupStrings: string[] = []
    groups.forEach((g, gIdx) => {
      const clauseParts: string[] = []
      g.clauses.forEach((c, idx) => {
        const op = idx === 0 ? '' : ` ${c.op} `
        const termRaw = c.text.trim()
        const term = c.exact && termRaw.length > 0 ? `"${termRaw}"` : termRaw
        if (!term) return
        const neg = c.not ? 'NOT ' : ''
        clauseParts.push(`${op}${neg}${term}`.trim())
      })
      let expr = clauseParts.join(' ')
      if (g.wrap && expr) expr = `(${expr})`
      if (!expr) return
      const groupNeg = g.not ? 'NOT ' : ''
      const groupOp = gIdx === 0 ? '' : ` ${g.op} `
      groupStrings.push(`${groupOp}${groupNeg}${expr}`.trim())
    })
    return groupStrings.join(' ')
  }

  useEffect(() => {
    onChange(buildQuery())
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [groups])

  const updateClause = (groupIndex: number, clauseIndex: number, update: Partial<Clause>) => {
    setGroups(prev => prev.map((g, gi) => (
      gi === groupIndex
        ? { ...g, clauses: g.clauses.map((c, ci) => (ci === clauseIndex ? { ...c, ...update } : c)) }
        : g
    )))
  }

  const addClause = (groupIndex: number) => {
    setGroups(prev => prev.map((g, gi) => (
      gi === groupIndex
        ? { ...g, clauses: [...g.clauses, { op: 'AND', not: false, text: '', exact: false }] }
        : g
    )))
  }

  const removeClause = (groupIndex: number, clauseIndex: number) => {
    setGroups(prev => prev.map((g, gi) => (
      gi === groupIndex
        ? { ...g, clauses: g.clauses.filter((_, ci) => ci !== clauseIndex) }
        : g
    )))
  }

  const updateGroup = (groupIndex: number, update: Partial<Group>) => {
    setGroups(prev => prev.map((g, gi) => (gi === groupIndex ? { ...g, ...update } : g)))
  }

  const addGroup = () => {
    setGroups(prev => ([
      ...prev,
      { op: 'AND', not: false, wrap: true, clauses: [{ op: 'AND', not: false, text: '', exact: false }] },
    ]))
  }

  const removeGroup = (groupIndex: number) => {
    setGroups(prev => prev.filter((_, gi) => gi !== groupIndex))
  }

  const preview = buildQuery()

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 relative z-10">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Brackets className="w-4 h-4 text-blue-600" />
          <h3 className="text-sm font-semibold text-gray-900">Query Builder</h3>
        </div>
        <button
          onClick={addGroup}
          className="px-2 py-1 text-xs bg-blue-50 hover:bg-blue-100 text-blue-700 rounded border border-blue-200 flex items-center gap-1 transition-colors"
          title="Add a new group of search terms"
        >
          <PlusCircle className="w-3 h-3"/>
          Add Group
        </button>
      </div>

      <div className="space-y-3">
        {groups.map((g, gi) => (
          <div key={gi} className="relative">
            {gi > 0 && (
              <div className="flex items-center justify-center mb-2">
                <div className="flex items-center gap-2 px-3 py-1 bg-gray-100 rounded-full text-xs">
                  <select
                    value={g.op}
                    onChange={(e) => updateGroup(gi, { op: e.target.value as ClauseOp })}
                    className="px-2 py-1 text-xs border border-gray-300 bg-white text-gray-700 rounded relative z-50 font-medium"
                    title="Operator between groups"
                  >
                    <option value="AND">AND</option>
                    <option value="OR">OR</option>
                  </select>
                </div>
              </div>
            )}

            <div className="bg-white rounded-lg border-2 border-blue-200 overflow-hidden">
              <div className="bg-blue-50 px-3 py-2 border-b border-blue-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-medium text-blue-700">GROUP {gi + 1}</span>
                    <div className="flex items-center gap-3">
                      <label className="flex items-center gap-1 text-xs text-gray-600 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={g.not}
                          onChange={(e) => updateGroup(gi, { not: e.target.checked })}
                          className="w-3 h-3 text-red-600 border-gray-300 rounded focus:ring-red-500"
                        />
                        NOT
                      </label>
                      <label className="flex items-center gap-1 text-xs text-gray-600 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={g.wrap}
                          onChange={(e) => updateGroup(gi, { wrap: e.target.checked })}
                          className="w-3 h-3 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                        ( )
                      </label>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    {groups.length > 1 && (
                      <button
                        onClick={() => removeGroup(gi)}
                        className="p-1 text-red-500 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                        title="Remove this group"
                      >
                        <MinusCircle className="w-3 h-3"/>
                      </button>
                    )}
                    <button
                      onClick={() => addClause(gi)}
                      className="px-2 py-1 text-xs bg-green-50 hover:bg-green-100 text-green-700 rounded border border-green-200 flex items-center gap-1 transition-colors"
                      title="Add a search term to this group"
                    >
                      <PlusCircle className="w-3 h-3"/>
                      Term
                    </button>
                  </div>
                </div>
              </div>

              <div className="p-3 space-y-2 bg-gray-50">
                {g.clauses.map((c, ci) => (
                  <div key={ci} className="flex items-center gap-2 p-3 bg-white rounded-lg border border-gray-300">
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {ci > 0 && (
                        <select
                          value={c.op}
                          onChange={(e) => updateClause(gi, ci, { op: e.target.value as ClauseOp })}
                          className="px-2 py-1 text-xs border border-blue-300 bg-blue-50 text-blue-700 rounded relative z-50 font-medium"
                          title="Operator with previous term"
                        >
                          <option value="AND">AND</option>
                          <option value="OR">OR</option>
                        </select>
                      )}
                      <label className="flex items-center gap-1 text-xs text-gray-600 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={c.not}
                          onChange={(e) => updateClause(gi, ci, { not: e.target.checked })}
                          className="w-3 h-3 text-red-600 border-gray-300 rounded focus:ring-red-500"
                        />
                        NOT
                      </label>
                    </div>

                    <input
                      type="text"
                      value={c.text}
                      onChange={(e) => updateClause(gi, ci, { text: e.target.value })}
                      placeholder='search term or "exact phrase"'
                      className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                    />

                    <label className="flex items-center gap-1 text-xs text-gray-600 cursor-pointer" title="Wrap this term in quotes for exact phrase matching">
                      <input
                        type="checkbox"
                        checked={c.exact}
                        onChange={(e) => updateClause(gi, ci, { exact: e.target.checked })}
                        className="w-3 h-3 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      <Quote className="w-3 h-3"/>
                    </label>

                    {g.clauses.length > 1 && (
                      <button
                        onClick={() => removeClause(gi, ci)}
                        className="p-1 text-red-500 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                        title="Remove this search term"
                      >
                        <MinusCircle className="w-3 h-3"/>
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
          <span className="text-xs font-medium text-gray-700">Preview</span>
        </div>
        <div className="font-mono text-xs bg-white px-3 py-2 rounded border border-blue-200 text-gray-800">
          {preview || <span className="text-gray-400 italic">Build your query above...</span>}
        </div>
      </div>
    </div>
  )
}

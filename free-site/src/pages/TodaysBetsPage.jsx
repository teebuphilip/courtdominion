import { useEffect, useMemo, useState } from 'react'

const parseNumber = (value) => {
  const n = Number(value)
  return Number.isFinite(n) ? n : 0
}

const TodaysBetsPage = () => {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const res = await fetch('/today_data.json', { cache: 'no-store' })
        if (!res.ok) throw new Error(`Failed to load today's data (${res.status})`)
        const data = await res.json()
        if (mounted) setRows(Array.isArray(data) ? data : [])
      } catch (err) {
        if (mounted) setError(err.message || "Failed to load today's bets")
      } finally {
        if (mounted) setLoading(false)
      }
    }
    load()
    return () => {
      mounted = false
    }
  }, [])

  const summary = useMemo(() => {
    const units = rows.reduce((acc, r) => acc + parseNumber(r.units), 0)
    const pnl = rows.reduce((acc, r) => acc + parseNumber(r.pnl), 0)
    return { units, pnl }
  }, [rows])

  return (
    <div className="min-h-screen bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-6">
          <h1 className="text-4xl font-bold text-white mb-2">Today's Bets</h1>
          <p className="text-xl text-gray-400">Current-day bet slate across sportsbook, Kalshi, and exchange.</p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-3"><div className="text-xs text-gray-400">Bets</div><div className="text-2xl font-semibold text-white">{rows.length}</div></div>
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-3"><div className="text-xs text-gray-400">Units</div><div className="text-2xl font-semibold text-white">{summary.units.toFixed(2)}</div></div>
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-3"><div className="text-xs text-gray-400">P/L</div><div className="text-2xl font-semibold text-white">{summary.pnl.toFixed(2)}</div></div>
        </div>

        <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
          {loading && <div className="p-4 text-gray-300">Loading today's bets...</div>}
          {!loading && error && <div className="p-4 text-red-400">{error}</div>}
          {!loading && !error && rows.length === 0 && <div className="p-4 text-gray-300">No bets published for today.</div>}
          {!loading && !error && rows.length > 0 && (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm text-left">
                <thead className="bg-gray-900 text-gray-300">
                  <tr>
                    <th className="px-3 py-2">Engine</th>
                    <th className="px-3 py-2">Player</th>
                    <th className="px-3 py-2">Prop</th>
                    <th className="px-3 py-2">Dir</th>
                    <th className="px-3 py-2">Proj</th>
                    <th className="px-3 py-2">Line</th>
                    <th className="px-3 py-2">Units</th>
                    <th className="px-3 py-2">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700 text-gray-200">
                  {rows.map((row, i) => (
                    <tr key={`${row.player_name || 'row'}-${i}`}>
                      <td className="px-3 py-2">{row.engine}</td>
                      <td className="px-3 py-2">{row.player_name}</td>
                      <td className="px-3 py-2">{row.prop_type}</td>
                      <td className="px-3 py-2">{row.direction}</td>
                      <td className="px-3 py-2">{row.dbb2_projection}</td>
                      <td className="px-3 py-2">{row.sportsbook_line}</td>
                      <td className="px-3 py-2">{row.units}</td>
                      <td className="px-3 py-2">{row.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default TodaysBetsPage

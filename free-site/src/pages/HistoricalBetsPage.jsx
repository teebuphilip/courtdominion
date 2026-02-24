import { useEffect, useMemo, useState } from 'react'

const parseNumber = (value) => {
  const n = Number(value)
  return Number.isFinite(n) ? n : 0
}

const HistoricalBetsPage = () => {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const res = await fetch('/history_data.json', { cache: 'no-store' })
        if (!res.ok) throw new Error(`Failed to load history data (${res.status})`)
        const data = await res.json()
        if (mounted) setRows(Array.isArray(data) ? data : [])
      } catch (err) {
        if (mounted) setError(err.message || 'Failed to load history data')
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
    const wins = rows.filter((r) => String(r.status).toUpperCase() === 'WIN').length
    const losses = rows.filter((r) => String(r.status).toUpperCase() === 'LOSS').length
    const pushes = rows.filter((r) => String(r.status).toUpperCase() === 'PUSH').length
    const pnl = rows.reduce((acc, r) => acc + parseNumber(r.pnl), 0)
    return { wins, losses, pushes, pnl }
  }, [rows])

  return (
    <div className="min-h-screen bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-6">
          <h1 className="text-4xl font-bold text-white mb-2">Historical Bets</h1>
          <p className="text-xl text-gray-400">Archived graded results from sportsbook and exchange runs.</p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-3"><div className="text-xs text-gray-400">All Bets</div><div className="text-2xl font-semibold text-white">{rows.length}</div></div>
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-3"><div className="text-xs text-gray-400">Wins</div><div className="text-2xl font-semibold text-green-400">{summary.wins}</div></div>
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-3"><div className="text-xs text-gray-400">Losses</div><div className="text-2xl font-semibold text-red-400">{summary.losses}</div></div>
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-3"><div className="text-xs text-gray-400">Pushes</div><div className="text-2xl font-semibold text-yellow-400">{summary.pushes}</div></div>
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-3"><div className="text-xs text-gray-400">P/L</div><div className="text-2xl font-semibold text-white">{summary.pnl.toFixed(2)}</div></div>
        </div>

        <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
          {loading && <div className="p-4 text-gray-300">Loading historical bets...</div>}
          {!loading && error && <div className="p-4 text-red-400">{error}</div>}
          {!loading && !error && rows.length === 0 && (
            <div className="p-4 text-gray-300">No historical bets published yet.</div>
          )}
          {!loading && !error && rows.length > 0 && (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm text-left">
                <thead className="bg-gray-900 text-gray-300">
                  <tr>
                    <th className="px-3 py-2">Date</th>
                    <th className="px-3 py-2">Player</th>
                    <th className="px-3 py-2">Prop</th>
                    <th className="px-3 py-2">Dir</th>
                    <th className="px-3 py-2">Proj</th>
                    <th className="px-3 py-2">Line</th>
                    <th className="px-3 py-2">Edge%</th>
                    <th className="px-3 py-2">Source</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2">P/L</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700 text-gray-200">
                  {rows.map((row, i) => (
                    <tr key={`${row.bet_id || row.player_name || 'row'}-${i}`}>
                      <td className="px-3 py-2">{row.date}</td>
                      <td className="px-3 py-2">{row.player_name}</td>
                      <td className="px-3 py-2">{row.prop_type}</td>
                      <td className="px-3 py-2">{row.direction}</td>
                      <td className="px-3 py-2">{row.dbb2_projection}</td>
                      <td className="px-3 py-2">{row.sportsbook_line}</td>
                      <td className="px-3 py-2">{row.edge_pct}</td>
                      <td className="px-3 py-2">{row.source}</td>
                      <td className="px-3 py-2">{row.status}</td>
                      <td className="px-3 py-2">{row.pnl}</td>
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

export default HistoricalBetsPage

import { useParams, Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { usePlayer } from '../hooks/usePlayer'
import { useContent } from '../hooks/useContent'
import PlayerCard from '../components/player/PlayerCard'
import StatRow from '../components/player/StatRow'
import RiskIndicator from '../components/player/RiskIndicator'
import { formatNumber, formatPercentage } from '../utils/formatters'

const PlayerDetailPage = () => {
  const { playerId } = useParams()
  const { data: player, isLoading, error } = usePlayer(playerId)
  const { data: content } = useContent()

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    )
  }

  if (error || !player) {
    return (
      <div className="min-h-screen bg-gray-900 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-white mb-4">Player Not Found</h1>
            <Link
              to="/projections"
              className="inline-flex items-center text-primary-400 hover:text-primary-300"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Projections
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Back Button */}
        <Link
          to="/projections"
          className="inline-flex items-center text-gray-400 hover:text-white mb-6 transition-colors"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Projections
        </Link>

        {/* Player Header Card */}
        <div className="mb-8">
          <PlayerCard player={player} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Season Statistics */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-xl font-bold text-white mb-4">
              {content?.player_detail?.stats_title || 'Season Averages'}
            </h3>
            
            <div className="space-y-0">
              {player.projection && (
                <>
                  <StatRow label="Fantasy Points" value={formatNumber(player.projection.fantasy_points, 1)} />
                  <StatRow label="Minutes" value={formatNumber(player.projection.minutes, 1)} />
                  <StatRow label="Points" value={formatNumber(player.projection.points, 1)} />
                  <StatRow label="Rebounds" value={formatNumber(player.projection.rebounds, 1)} />
                  <StatRow label="Assists" value={formatNumber(player.projection.assists, 1)} />
                  <StatRow label="Steals" value={formatNumber(player.projection.steals, 1)} />
                  <StatRow label="Blocks" value={formatNumber(player.projection.blocks, 1)} />
                  <StatRow label="Turnovers" value={formatNumber(player.projection.turnovers, 1)} />
                  <StatRow label="FG%" value={formatPercentage(player.projection.fg_pct, 1)} />
                  <StatRow label="FT%" value={formatPercentage(player.projection.ft_pct, 1)} />
                  <StatRow label="3-Pointers Made" value={formatNumber(player.projection.three_pointers, 1)} />
                </>
              )}
            </div>
          </div>

          {/* Risk Analysis */}
          <div>
            <RiskIndicator risk={player.risk} />
            
            {/* Insight/Recommendation */}
            {player.insight && (
              <div className="mt-6 bg-gray-800 rounded-lg p-6 border border-gray-700">
                <h3 className="text-xl font-bold text-white mb-4">Fantasy Outlook</h3>
                
                <div className="space-y-3">
                  {player.insight.value_score && (
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">Value Score</span>
                      <span className="text-2xl font-bold text-primary-400">
                        {player.insight.value_score.toFixed(1)}
                        <span className="text-lg text-gray-400">/10</span>
                      </span>
                    </div>
                  )}
                  
                  {player.insight.recommendation && (
                    <div className="p-4 bg-primary-500/10 border border-primary-500/20 rounded-lg">
                      <div className="text-sm font-semibold text-primary-400 mb-1">
                        Recommendation
                      </div>
                      <div className="text-white">
                        {player.insight.recommendation}
                      </div>
                    </div>
                  )}
                  
                  {player.insight.trending && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-400">Trend</span>
                      <span className={`font-semibold capitalize ${
                        player.insight.trending === 'up' ? 'text-green-400' :
                        player.insight.trending === 'down' ? 'text-red-400' :
                        'text-gray-400'
                      }`}>
                        {player.insight.trending}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default PlayerDetailPage

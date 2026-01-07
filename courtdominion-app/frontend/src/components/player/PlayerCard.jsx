import { formatNumber } from '../../utils/formatters'
import RiskBadge from '../projections/RiskBadge'

const PlayerCard = ({ player }) => {
  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">{player.name}</h1>
          <div className="flex items-center space-x-4 text-gray-400">
            <span className="text-lg">{player.team}</span>
            <span>•</span>
            <span className="text-lg">{player.position}</span>
            {player.age && (
              <>
                <span>•</span>
                <span>Age {player.age}</span>
              </>
            )}
          </div>
        </div>
        
        <div className="text-right">
          <div className="text-sm text-gray-400 mb-1">Projected FPTS</div>
          <div className="text-4xl font-bold text-primary-400">
            {formatNumber(player.projection?.fantasy_points, 1)}
          </div>
        </div>
      </div>

      {player.risk && (
        <div className="mt-4">
          <RiskBadge riskData={player.risk} />
        </div>
      )}
    </div>
  )
}

export default PlayerCard

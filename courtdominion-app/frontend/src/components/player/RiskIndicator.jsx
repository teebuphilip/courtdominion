import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { formatNumber } from '../../utils/formatters'

const RiskIndicator = ({ risk }) => {
  if (!risk) return null

  const getConsistencyColor = (consistency) => {
    if (consistency >= 80) return 'text-green-500'
    if (consistency >= 60) return 'text-yellow-500'
    return 'text-red-500'
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <h3 className="text-xl font-bold text-white mb-4">Risk Analysis</h3>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Consistency */}
        <div className="bg-gray-900 rounded-lg p-4">
          <div className="text-sm text-gray-400 mb-1">Consistency Score</div>
          <div className={`text-3xl font-bold ${getConsistencyColor(risk.consistency)}`}>
            {risk.consistency}
            <span className="text-lg text-gray-400">/100</span>
          </div>
        </div>

        {/* Injury Risk */}
        <div className="bg-gray-900 rounded-lg p-4">
          <div className="text-sm text-gray-400 mb-1">Injury Risk</div>
          <div className="text-2xl font-bold text-white capitalize">
            {risk.injury_risk}
          </div>
        </div>

        {/* Ceiling */}
        <div className="bg-gray-900 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-1">
            <TrendingUp className="h-4 w-4 text-green-500" />
            <span className="text-sm text-gray-400">Ceiling (Best Case)</span>
          </div>
          <div className="text-3xl font-bold text-green-400">
            {formatNumber(risk.ceiling, 1)}
          </div>
        </div>

        {/* Floor */}
        <div className="bg-gray-900 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-1">
            <TrendingDown className="h-4 w-4 text-red-500" />
            <span className="text-sm text-gray-400">Floor (Worst Case)</span>
          </div>
          <div className="text-3xl font-bold text-red-400">
            {formatNumber(risk.floor, 1)}
          </div>
        </div>
      </div>

      {/* Volatility */}
      {risk.volatility !== undefined && (
        <div className="mt-4 p-4 bg-gray-900 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">Volatility Index</span>
            <span className="text-lg font-semibold text-white">
              {formatNumber(risk.volatility, 2)}
            </span>
          </div>
        </div>
      )}

      {/* Recommendation */}
      {risk.recommendation && (
        <div className="mt-4 p-4 bg-primary-500/10 border border-primary-500/20 rounded-lg">
          <p className="text-sm text-primary-400">
            <span className="font-semibold">Assessment:</span> {risk.recommendation}
          </p>
        </div>
      )}
    </div>
  )
}

export default RiskIndicator

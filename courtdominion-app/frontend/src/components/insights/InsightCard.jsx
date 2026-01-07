import { Link } from 'react-router-dom'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

const InsightCard = ({ insight }) => {
  const getTrendIcon = () => {
    if (insight.trending === 'up') return <TrendingUp className="w-6 h-6 text-green-400" />
    if (insight.trending === 'down') return <TrendingDown className="w-6 h-6 text-red-400" />
    return <Minus className="w-6 h-6 text-gray-400" />
  }

  const getRecommendationColor = () => {
    const rec = insight.recommendation?.toLowerCase()
    if (rec?.includes('add immediately') || rec?.includes('must add')) return 'bg-green-500/20 text-green-400 border-green-500/20'
    if (rec?.includes('strong')) return 'bg-blue-500/20 text-blue-400 border-blue-500/20'
    if (rec?.includes('consider') || rec?.includes('stream')) return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/20'
    return 'bg-primary-500/20 text-primary-400 border-primary-500/20'
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 hover:bg-gray-750 transition border border-gray-700">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <Link 
            to={`/player/${insight.player_id}`}
            className="text-xl font-semibold text-white hover:text-primary-400 transition-colors"
          >
            {insight.name}
          </Link>
          <div className="flex items-center space-x-3 text-sm text-gray-400 mt-1">
            <span>{insight.team}</span>
            <span>•</span>
            <span>{insight.position}</span>
            {insight.ownership_estimate && (
              <>
                <span>•</span>
                <span>{insight.ownership_estimate} owned</span>
              </>
            )}
          </div>
        </div>
        
        <div className="flex items-center space-x-3 ml-4">
          <div className="text-right">
            <div className="text-sm text-gray-400">Value Score</div>
            <div className="text-2xl font-bold text-primary-400">
              {insight.value_score?.toFixed(1)}
            </div>
          </div>
          {getTrendIcon()}
        </div>
      </div>
      
      <div className="mb-3">
        <span className={`inline-block px-3 py-1 rounded text-sm font-medium border ${getRecommendationColor()}`}>
          {insight.recommendation}
        </span>
      </div>
      
      <p className="text-gray-300 text-sm leading-relaxed">
        {insight.reasoning}
      </p>
    </div>
  )
}

export default InsightCard

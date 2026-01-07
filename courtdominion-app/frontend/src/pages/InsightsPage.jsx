import { useState } from 'react'
import { useInsights } from '../hooks/useInsights'
import { useContent } from '../hooks/useContent'
import InsightCard from '../components/insights/InsightCard'

const InsightsPage = () => {
  const [category, setCategory] = useState('all')
  const { data: insightsData, isLoading } = useInsights({ category })
  const { data: content } = useContent()

  const categories = [
    { value: 'all', label: 'All Insights' },
    { value: 'waiver_wire', label: 'Waiver Wire' },
    { value: 'sleepers', label: 'Sleepers' },
    { value: 'streaming', label: 'Streaming Options' },
  ]

  return (
    <div className="min-h-screen bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            {content?.insights_page?.title || 'Waiver Wire Insights'}
          </h1>
          <p className="text-xl text-gray-400">
            {content?.insights_page?.subtitle || 'Deep sleepers and value plays for your league'}
          </p>
        </div>

        {/* Category Filter */}
        <div className="mb-6">
          <div className="flex flex-wrap gap-2">
            {categories.map((cat) => (
              <button
                key={cat.value}
                onClick={() => setCategory(cat.value)}
                className={`px-4 py-2 rounded-md font-medium transition-colors ${
                  category === cat.value
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* Insights List */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
          </div>
        ) : (
          <div className="space-y-4">
            {insightsData?.insights && insightsData.insights.length > 0 ? (
              insightsData.insights.map((insight, idx) => (
                <InsightCard key={idx} insight={insight} />
              ))
            ) : (
              <div className="text-center py-12 bg-gray-800 rounded-lg border border-gray-700">
                <p className="text-gray-400">No insights available for this category</p>
              </div>
            )}
          </div>
        )}

        {/* Footer Note */}
        {insightsData?.insights && insightsData.insights.length > 0 && (
          <div className="mt-8 text-center text-sm text-gray-400">
            Showing {insightsData.insights.length} insights
            {insightsData.count && insightsData.insights.length !== insightsData.count && (
              <span> of {insightsData.count} total</span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default InsightsPage

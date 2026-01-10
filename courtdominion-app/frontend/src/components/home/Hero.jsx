import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'

const Hero = ({ content }) => {
  return (
    <div className="relative overflow-hidden bg-gradient-to-b from-gray-900 to-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 sm:py-32">
        <div className="text-center">
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight mb-6">
            <span className="block text-white">
              {content?.headline || 'NBA Fantasy Projections Built Different'}
            </span>
          </h1>
          
          <p className="mt-6 text-xl sm:text-2xl text-gray-300 max-w-3xl mx-auto">
            {content?.subheadline || 'Risk analysis, volatility metrics, and waiver wire intelligence'}
          </p>

          <div className="mt-10 flex justify-center">
            <Link
              to="/projections"
              className="inline-flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 transition-colors"
            >
              {content?.cta_primary || 'View Today\'s Projections'}
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Hero

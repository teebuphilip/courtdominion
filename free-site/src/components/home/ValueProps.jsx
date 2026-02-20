import { TrendingUp, Shield, Target } from 'lucide-react'

const ValueProps = ({ content }) => {
  const defaultProps = [
    "Risk-adjusted projections you can trust",
    "Volatility indicators for every player", 
    "Daily waiver wire insights"
  ]

  const props = content?.value_props || defaultProps

  const icons = [Shield, TrendingUp, Target]

  return (
    <div className="py-16 bg-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {props.map((prop, index) => {
            const Icon = icons[index % icons.length]
            return (
              <div key={index} className="text-center">
                <div className="flex justify-center mb-4">
                  <div className="p-3 bg-primary-500/20 rounded-lg">
                    <Icon className="h-8 w-8 text-primary-500" />
                  </div>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">
                  {prop}
                </h3>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default ValueProps

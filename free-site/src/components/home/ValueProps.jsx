import { TrendingUp, Shield, Target } from 'lucide-react'
import { SITE_CONTENT } from '../../content/siteContent'

const ValueProps = () => {
  const icons = [Shield, TrendingUp, Target]

  return (
    <div className="py-16 bg-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {SITE_CONTENT.features.map((feature, index) => {
            const Icon = icons[index % icons.length]
            return (
              <div key={index} className="text-center">
                <div className="flex justify-center mb-4">
                  <div className="p-3 bg-primary-500/20 rounded-lg">
                    <Icon className="h-8 w-8 text-primary-500" />
                  </div>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-gray-400">{feature.description}</p>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default ValueProps

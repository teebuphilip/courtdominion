import { Users, TrendingUp, Award } from 'lucide-react'

const SocialProof = () => {
  const stats = [
    {
      icon: Users,
      value: '398',
      label: 'NBA Players Tracked'
    },
    {
      icon: TrendingUp,
      value: 'Daily',
      label: 'Updated Projections'
    },
    {
      icon: Award,
      value: '95%',
      label: 'Confidence Score'
    }
  ]

  return (
    <div className="py-12 bg-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {stats.map((stat, index) => {
            const Icon = stat.icon
            return (
              <div key={index} className="text-center">
                <div className="flex justify-center mb-3">
                  <Icon className="h-10 w-10 text-primary-500" />
                </div>
                <div className="text-3xl font-bold text-white mb-1">
                  {stat.value}
                </div>
                <div className="text-sm text-gray-400">
                  {stat.label}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default SocialProof

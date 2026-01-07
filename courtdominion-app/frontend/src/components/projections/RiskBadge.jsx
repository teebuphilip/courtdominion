import { RISK_LEVELS } from '../../utils/constants'
import { getRiskLevel } from '../../utils/formatters'

const RiskBadge = ({ riskData }) => {
  const riskLevel = getRiskLevel(riskData)
  const riskConfig = RISK_LEVELS[riskLevel]

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${riskConfig.bgColor} ${riskConfig.color}`}>
      {riskConfig.label}
    </span>
  )
}

export default RiskBadge

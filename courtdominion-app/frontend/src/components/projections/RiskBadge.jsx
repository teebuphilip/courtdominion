import { RISK_LEVELS } from '../../utils/constants'
import { getRiskLevel } from '../../utils/formatters'

const RiskBadge = ({ riskData, risk }) => {
  // Support both string risk prop and riskData object
  let riskLevel
  if (risk) {
    // Direct string prop (for tests and simple usage)
    riskLevel = risk.toUpperCase()
  } else {
    // Object with injury_risk property (for API data)
    riskLevel = getRiskLevel(riskData)
  }

  const riskConfig = RISK_LEVELS[riskLevel]

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${riskConfig.bgColor} ${riskConfig.color}`}>
      {riskConfig.label}
    </span>
  )
}

export default RiskBadge

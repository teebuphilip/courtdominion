/**
 * Format a number to specified decimal places
 */
export const formatNumber = (num, decimals = 1) => {
  if (num === null || num === undefined) return '-'
  return Number(num).toFixed(decimals)
}

/**
 * Format percentage (0.583 -> 58.3%)
 */
export const formatPercentage = (num, decimals = 1) => {
  if (num === null || num === undefined) return '0.0%'
  return `${(Number(num) * 100).toFixed(decimals)}%`
}

/**
 * Format decimal (27.456 -> 27.5)
 */
export const formatDecimal = (num, decimals = 1) => {
  if (num === null || num === undefined) return '0.0'
  return Number(num).toFixed(decimals)
}

/**
 * Determine risk level based on injury risk string
 */
export const getRiskLevel = (riskData) => {
  if (!riskData || !riskData.injury_risk) return 'MEDIUM'
  
  const risk = riskData.injury_risk.toLowerCase()
  if (risk === 'low') return 'LOW'
  if (risk === 'high') return 'HIGH'
  return 'MEDIUM'
}

/**
 * Format player position
 */
export const formatPosition = (position) => {
  if (!position) return '-'
  // Convert "Forward" to "F", "Guard" to "G", etc.
  if (position.includes('Forward')) return 'F'
  if (position.includes('Guard')) return 'G'
  if (position.includes('Center')) return 'C'
  return position
}

/**
 * Truncate text with ellipsis
 */
export const truncate = (text, maxLength = 100) => {
  if (!text || text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

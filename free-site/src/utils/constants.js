// Risk level thresholds and colors
export const RISK_LEVELS = {
  LOW: {
    label: 'Low Risk',
    color: 'text-green-500',
    bgColor: 'bg-green-500/20',
    borderColor: 'border-green-500'
  },
  MEDIUM: {
    label: 'Medium Risk',
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500/20',
    borderColor: 'border-yellow-500'
  },
  HIGH: {
    label: 'High Risk',
    color: 'text-red-500',
    bgColor: 'bg-red-500/20',
    borderColor: 'border-red-500'
  }
}

// Pagination
export const ITEMS_PER_PAGE = 300

// Sort options for projections
export const SORT_OPTIONS = [
  { value: 'fantasy_points', label: 'Fantasy Points' },
  { value: 'points', label: 'Points' },
  { value: 'rebounds', label: 'Rebounds' },
  { value: 'assists', label: 'Assists' },
  { value: 'steals', label: 'Steals' },
  { value: 'blocks', label: 'Blocks' }
]

// Position filters
export const POSITIONS = ['All', 'G', 'F', 'C', 'F-G', 'F-C', 'G-F']

const StatRow = ({ label, value }) => {
  return (
    <div className="flex justify-between items-center py-3 border-b border-gray-700 last:border-b-0">
      <span className="text-sm font-medium text-gray-400">{label}</span>
      <span className="text-lg font-semibold text-white">{value}</span>
    </div>
  )
}

export default StatRow

import { Link } from 'react-router-dom'
import { ArrowUpDown } from 'lucide-react'
import { formatNumber, formatPercentage } from '../../utils/formatters'
import RiskBadge from './RiskBadge'

const ProjectionsTable = ({ projections, onSort, currentSort }) => {
  const handleSort = (field) => {
    onSort(field)
  }

  const SortableHeader = ({ field, children }) => (
    <th
      scope="col"
      className="px-3 py-3.5 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider cursor-pointer hover:text-white transition-colors"
      onClick={() => handleSort(field)}
    >
      <div className="flex items-center space-x-1">
        <span>{children}</span>
        <ArrowUpDown className="h-4 w-4" />
      </div>
    </th>
  )

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-700">
        <thead className="bg-gray-800">
          <tr>
            <th scope="col" className="px-3 py-3.5 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">
              Rank
            </th>
            <SortableHeader field="name">Player</SortableHeader>
            <th scope="col" className="px-3 py-3.5 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">
              Team
            </th>
            <th scope="col" className="px-3 py-3.5 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">
              Pos
            </th>
            <SortableHeader field="fantasy_points">FPTS</SortableHeader>
            <SortableHeader field="minutes">MIN</SortableHeader>
            <SortableHeader field="points">PTS</SortableHeader>
            <SortableHeader field="rebounds">REB</SortableHeader>
            <SortableHeader field="assists">AST</SortableHeader>
            <SortableHeader field="steals">STL</SortableHeader>
            <SortableHeader field="blocks">BLK</SortableHeader>
            <SortableHeader field="turnovers">TO</SortableHeader>
            <SortableHeader field="fg_pct">FG%</SortableHeader>
            <SortableHeader field="three_pointers">3PM</SortableHeader>
            <th scope="col" className="px-3 py-3.5 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">
              Risk
            </th>
          </tr>
        </thead>
        <tbody className="bg-gray-900 divide-y divide-gray-800">
          {projections && projections.length > 0 ? (
            projections.map((player, index) => (
              <tr key={player.player_id} className="hover:bg-gray-800 transition-colors">
                <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-400">
                  {index + 1}
                </td>
                <td className="px-3 py-4 whitespace-nowrap">
                  <Link
                    to={`/player/${player.player_id}`}
                    className="text-sm font-medium text-primary-400 hover:text-primary-300 transition-colors"
                  >
                    {player.name}
                  </Link>
                </td>
                <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-300">
                  {player.team}
                </td>
                <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-300">
                  {player.position}
                </td>
                <td className="px-3 py-4 whitespace-nowrap text-sm font-semibold text-white">
                  {formatNumber(player.fantasy_points, 1)}
                </td>
                <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-300">
                  {formatNumber(player.minutes, 1)}
                </td>
                <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-300">
                  {formatNumber(player.points, 1)}
                </td>
                <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-300">
                  {formatNumber(player.rebounds, 1)}
                </td>
                <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-300">
                  {formatNumber(player.assists, 1)}
                </td>
                <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-300">
                  {formatNumber(player.steals, 1)}
                </td>
                <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-300">
                  {formatNumber(player.blocks, 1)}
                </td>
                <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-300">
                  {formatNumber(player.turnovers, 1)}
                </td>
                <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-300">
                  {formatPercentage(player.fg_pct, 1)}
                </td>
                <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-300">
                  {formatNumber(player.three_pointers, 1)}
                </td>
                <td className="px-3 py-4 whitespace-nowrap text-sm">
                  <RiskBadge riskData={{ injury_risk: 'low' }} />
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="15" className="px-3 py-8 text-center text-sm text-gray-500">
                No projections found
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

export default ProjectionsTable

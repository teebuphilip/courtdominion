import { useState, useMemo, useEffect } from 'react'
import { useContent } from '../hooks/useContent'
import { useProjections } from '../hooks/useProjections'
import ProjectionsTable from '../components/projections/ProjectionsTable'
import SearchBar from '../components/projections/SearchBar'
import Pagination from '../components/projections/Pagination'
import EmailCapture from '../components/home/EmailCapture'
import { ITEMS_PER_PAGE, SORT_OPTIONS } from '../utils/constants'

const ProjectionsPage = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [sortBy, setSortBy] = useState('fantasy_points')
  const [sortOrder, setSortOrder] = useState('desc')
  const [hasAccess, setHasAccess] = useState(false)

  // Check localStorage for email capture flag
  useEffect(() => {
    const captured = localStorage.getItem('cd_email_captured')
    setHasAccess(captured === 'true')
  }, [])

  const { data: content } = useContent()
  
  // Fetch projections with current params
  const offset = (currentPage - 1) * ITEMS_PER_PAGE
  const { data: projectionsData, isLoading } = useProjections({
    limit: ITEMS_PER_PAGE,
    offset,
    sort_by: sortBy,
    order: sortOrder
  })

  // Filter projections based on search
  const filteredProjections = useMemo(() => {
    if (!projectionsData?.projections) return []
    if (!searchQuery) return projectionsData.projections

    const query = searchQuery.toLowerCase()
    return projectionsData.projections.filter(
      (p) =>
        p.name.toLowerCase().includes(query) ||
        p.team.toLowerCase().includes(query) ||
        p.position.toLowerCase().includes(query)
    )
  }, [projectionsData, searchQuery])

  const totalPages = Math.ceil((projectionsData?.total || 0) / ITEMS_PER_PAGE)

  const handleSort = (field) => {
    if (sortBy === field) {
      // Toggle order if clicking same field
      setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')
    } else {
      // New field, default to descending
      setSortBy(field)
      setSortOrder('desc')
    }
    setCurrentPage(1) // Reset to first page on sort change
  }

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleUnlock = () => {
    setHasAccess(true)
  }

  // Show email gate if no access
  if (!hasAccess) {
    return (
      <div className="min-h-screen bg-gray-900 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="mb-8 text-center">
            <h1 className="text-4xl font-bold text-white mb-2">
              {content?.projections_page?.title || 'Daily Projections'}
            </h1>
            <p className="text-xl text-gray-400 mb-4">
              {content?.projections_page?.subtitle || '398 NBA players with risk-adjusted fantasy points'}
            </p>
            <p className="text-lg text-gray-300">
              Enter your email below to unlock access
            </p>
          </div>

          {/* Email gate */}
          <EmailCapture onUnlock={handleUnlock} />
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            {content?.projections_page?.title || 'Daily Projections'}
          </h1>
          <p className="text-xl text-gray-400">
            {content?.projections_page?.subtitle || '398 NBA players with risk-adjusted fantasy points'}
          </p>
        </div>

        {/* Search and Filters */}
        <div className="mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <SearchBar
                value={searchQuery}
                onChange={setSearchQuery}
                placeholder="Search by player name, team, or position..."
              />
            </div>
            <div>
              <select
                value={sortBy}
                onChange={(e) => {
                  setSortBy(e.target.value)
                  setCurrentPage(1)
                }}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-md text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {SORT_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    Sort by {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Projections Table */}
        <div className="bg-gray-800 rounded-lg shadow-xl overflow-hidden border border-gray-700">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
            </div>
          ) : (
            <>
              <ProjectionsTable
                projections={filteredProjections}
                onSort={handleSort}
                currentSort={{ field: sortBy, order: sortOrder }}
              />
              
              {!searchQuery && totalPages > 1 && (
                <Pagination
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={handlePageChange}
                />
              )}

              {searchQuery && filteredProjections.length === 0 && (
                <div className="text-center py-12">
                  <p className="text-gray-400">No players found matching "{searchQuery}"</p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Stats Summary */}
        {projectionsData && (
          <div className="mt-6 text-center text-sm text-gray-400">
            Showing {filteredProjections.length} of {projectionsData.total} players
            {projectionsData.last_updated && (
              <span className="ml-2">
                • Last updated: {new Date(projectionsData.last_updated).toLocaleString()}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default ProjectionsPage

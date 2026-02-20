import { ChevronLeft, ChevronRight } from 'lucide-react'

const Pagination = ({ currentPage, totalPages, onPageChange }) => {
  const canGoPrevious = currentPage > 1
  const canGoNext = currentPage < totalPages

  return (
    <div className="flex items-center justify-between border-t border-gray-700 bg-gray-800 px-4 py-3 sm:px-6 rounded-b-lg">
      <div className="flex flex-1 justify-between sm:hidden">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={!canGoPrevious}
          className={`relative inline-flex items-center rounded-md px-4 py-2 text-sm font-medium ${
            canGoPrevious
              ? 'text-gray-300 bg-gray-700 hover:bg-gray-600'
              : 'text-gray-500 bg-gray-800 cursor-not-allowed'
          }`}
        >
          Previous
        </button>
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={!canGoNext}
          className={`relative ml-3 inline-flex items-center rounded-md px-4 py-2 text-sm font-medium ${
            canGoNext
              ? 'text-gray-300 bg-gray-700 hover:bg-gray-600'
              : 'text-gray-500 bg-gray-800 cursor-not-allowed'
          }`}
        >
          Next
        </button>
      </div>
      
      <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
        <div>
          <p className="text-sm text-gray-400">
            Page <span className="font-medium text-white">{currentPage}</span> of{' '}
            <span className="font-medium text-white">{totalPages}</span>
          </p>
        </div>
        <div>
          <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={!canGoPrevious}
              className={`relative inline-flex items-center rounded-l-md px-2 py-2 ${
                canGoPrevious
                  ? 'text-gray-400 hover:bg-gray-700 hover:text-white'
                  : 'text-gray-600 cursor-not-allowed'
              } ring-1 ring-inset ring-gray-700`}
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            
            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={!canGoNext}
              className={`relative inline-flex items-center rounded-r-md px-2 py-2 ${
                canGoNext
                  ? 'text-gray-400 hover:bg-gray-700 hover:text-white'
                  : 'text-gray-600 cursor-not-allowed'
              } ring-1 ring-inset ring-gray-700`}
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </nav>
        </div>
      </div>
    </div>
  )
}

export default Pagination

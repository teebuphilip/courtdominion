import { useQuery } from '@tanstack/react-query'
import { fetchProjections } from '../services/api'

export const useProjections = (params = {}) => {
  return useQuery({
    queryKey: ['projections', params],
    queryFn: async () => {
      const response = await fetchProjections(params)
      const data = response.data

      // Backend returns raw array, transform to expected format
      if (Array.isArray(data)) {
        return {
          projections: data,
          total: data.length,
          limit: params.limit || 100,
          offset: params.offset || 0,
          last_updated: new Date().toISOString()
        }
      }

      // If already in correct format (mock data or future backend change)
      return data
    },
    keepPreviousData: true, // Keep showing old data while fetching new
  })
}

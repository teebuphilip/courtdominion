import { useQuery } from '@tanstack/react-query'
import { fetchProjections } from '../services/api'

export const useProjections = (params = {}) => {
  return useQuery({
    queryKey: ['projections', params],
    queryFn: async () => {
      const response = await fetchProjections(params)
      return response.data
    },
    keepPreviousData: true, // Keep showing old data while fetching new
  })
}

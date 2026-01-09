import { useQuery } from '@tanstack/react-query'
import { fetchInsights } from '../services/api'

export const useInsights = (params = {}) => {
  return useQuery({
    queryKey: ['insights', params],
    queryFn: async () => {
      const response = await fetchInsights(params)
      const data = response.data

      // Backend returns raw array, transform to expected format
      if (Array.isArray(data)) {
        return {
          insights: data,
          count: data.length,
          category: params.category || 'all'
        }
      }

      // If already in correct format (mock data or future backend change)
      return data
    },
    staleTime: 0, // Always refetch to get fresh data
    cacheTime: 5 * 60 * 1000, // Keep in cache for 5 minutes
  })
}

import { useQuery } from '@tanstack/react-query'
import { fetchInsights } from '../services/api'

export const useInsights = (params = {}) => {
  return useQuery({
    queryKey: ['insights', params],
    queryFn: async () => {
      const response = await fetchInsights(params)
      return response.data
    },
  })
}

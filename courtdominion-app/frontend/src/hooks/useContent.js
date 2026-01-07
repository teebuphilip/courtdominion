import { useQuery } from '@tanstack/react-query'
import { fetchContent } from '../services/api'

export const useContent = () => {
  return useQuery({
    queryKey: ['content'],
    queryFn: async () => {
      const response = await fetchContent()
      return response.data
    },
    staleTime: 30 * 60 * 1000, // 30 minutes - content doesn't change often
  })
}

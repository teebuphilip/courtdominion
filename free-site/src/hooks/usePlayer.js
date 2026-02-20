import { useQuery } from '@tanstack/react-query'
import { fetchPlayer } from '../services/api'

export const usePlayer = (playerId) => {
  return useQuery({
    queryKey: ['player', playerId],
    queryFn: async () => {
      const response = await fetchPlayer(playerId)
      return response.data
    },
    enabled: !!playerId, // Only run query if playerId exists
  })
}

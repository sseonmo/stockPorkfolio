import { useQuery } from '@tanstack/react-query'
import * as holdingsApi from '../api/holdings'
import type { MarketType } from '../types'

export function useHoldings(market?: MarketType) {
  return useQuery({
    queryKey: ['holdings', market],
    queryFn: () => holdingsApi.getHoldings(market),
  })
}

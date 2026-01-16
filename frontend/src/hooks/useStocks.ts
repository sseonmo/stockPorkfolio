import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as stocksApi from '../api/stocks'
import type { MarketType } from '../types'

export function useStockSearch(query: string, market?: MarketType) {
  return useQuery({
    queryKey: ['stocks', 'search', query, market],
    queryFn: () => stocksApi.searchStocks(query, market),
    enabled: query.length >= 1,
  })
}

export function useExchangeRate() {
  return useQuery({
    queryKey: ['exchange-rate'],
    queryFn: stocksApi.getExchangeRate,
    staleTime: 5 * 60 * 1000,
  })
}

export function useCreateStock() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: stocksApi.createStock,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stocks'] })
    },
  })
}

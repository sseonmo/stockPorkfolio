import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as dividendsApi from '../api/dividends'
import type { DividendCreate, DividendUpdate } from '../types'

export function useDividends(params?: {
  stock_id?: number
  year?: string
}) {
  return useQuery({
    queryKey: ['dividends', params],
    queryFn: () => dividendsApi.getDividends(params),
  })
}

export function useCreateDividend() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: DividendCreate) =>
      dividendsApi.createDividend(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dividends'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] }) // 배당금이 대시보드에 반영될 수 있음
    },
  })
}

export function useUpdateDividend() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: DividendUpdate }) =>
      dividendsApi.updateDividend(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dividends'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export function useDeleteDividend() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => dividendsApi.deleteDividend(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dividends'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

import { useQuery } from '@tanstack/react-query'
import * as analyticsApi from '../api/analytics'

export function useSectorAllocation() {
  return useQuery({
    queryKey: ['analytics', 'sectors'],
    queryFn: analyticsApi.getSectorAllocation,
  })
}

export function useBenchmarkComparison(
  benchmark: string = 'SP500',
  days: number = 90
) {
  return useQuery({
    queryKey: ['analytics', 'benchmark', benchmark, days],
    queryFn: () => analyticsApi.getBenchmarkComparison(benchmark, days),
  })
}

export function useRiskMetrics(days: number = 90) {
  return useQuery({
    queryKey: ['analytics', 'risk', days],
    queryFn: () => analyticsApi.getRiskMetrics(days),
  })
}

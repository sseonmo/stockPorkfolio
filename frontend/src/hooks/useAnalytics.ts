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

export function usePeriodReturns() {
  return useQuery({
    queryKey: ['analytics', 'period-returns'],
    queryFn: analyticsApi.getPeriodReturns,
  })
}

export function useMonthlyReturns() {
  return useQuery({
    queryKey: ['analytics', 'monthly-returns'],
    queryFn: analyticsApi.getMonthlyReturns,
  })
}

export function useWinLossStats(days: number = 365) {
  return useQuery({
    queryKey: ['analytics', 'win-loss', days],
    queryFn: () => analyticsApi.getWinLossStats(days),
  })
}

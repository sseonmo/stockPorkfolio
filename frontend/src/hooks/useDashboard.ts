import { useQuery } from '@tanstack/react-query'
import * as dashboardApi from '../api/dashboard'
import type { AssetTrendParams } from '../api/dashboard'

export function usePortfolioSummary() {
  return useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: dashboardApi.getPortfolioSummary,
    refetchInterval: 60 * 1000,
  })
}

export function useMarketBreakdown() {
  return useQuery({
    queryKey: ['dashboard', 'market-breakdown'],
    queryFn: dashboardApi.getMarketBreakdown,
  })
}

export function useAssetTrend(params: AssetTrendParams = {}) {
  return useQuery({
    queryKey: ['dashboard', 'trend', params],
    queryFn: () => dashboardApi.getAssetTrend(params),
  })
}

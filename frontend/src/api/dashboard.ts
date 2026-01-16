import api from '../lib/api'
import type {
  PortfolioSummary,
  MarketBreakdown,
  AssetTrendResponse,
  DailyPnlHistoryResponse,
} from '../types'
import qs from 'qs'

export async function getPortfolioSummary(): Promise<PortfolioSummary> {
  const response = await api.get('/dashboard/summary')
  return response.data
}

export async function getMarketBreakdown(): Promise<MarketBreakdown[]> {
  const response = await api.get('/dashboard/market-breakdown')
  return response.data
}

export interface AssetTrendParams {
  start_date?: string
  end_date?: string
  stock_ids?: number[]
}

export async function getAssetTrend(params: AssetTrendParams = {}): Promise<AssetTrendResponse> {
  const response = await api.get('/dashboard/trend', {
    params,
    paramsSerializer: (p) => qs.stringify(p, { arrayFormat: 'repeat' }),
  })
  return response.data
}

export async function getDailyPnlHistory(
  start_date?: string,
  end_date?: string,
  stock_ids?: number[]
): Promise<DailyPnlHistoryResponse> {
  const response = await api.get('/dashboard/daily-pnl', {
    params: {
      start_date,
      end_date,
      stock_ids,
    },
    paramsSerializer: (params) => {
      return qs.stringify(params, { arrayFormat: 'repeat' })
    }
  })
  return response.data
}

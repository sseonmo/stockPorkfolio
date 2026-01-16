import api from '../lib/api'
import type { Stock, StockSearchResult, MarketType } from '../types'

export async function searchStocks(
  query: string,
  market?: MarketType
): Promise<StockSearchResult[]> {
  const params: Record<string, string> = { q: query }
  if (market) params.market = market
  const response = await api.get('/stocks/search', { params })
  return response.data
}

export async function getExchangeRate(): Promise<{ usd_krw: number }> {
  const response = await api.get('/stocks/exchange-rate')
  return response.data
}

export async function createStock(data: {
  ticker: string
  name: string
  market_type: MarketType
  exchange: string
  sector?: string
}): Promise<Stock> {
  const response = await api.post('/stocks', data)
  return response.data
}

export async function getStock(stockId: number): Promise<Stock> {
  const response = await api.get(`/stocks/${stockId}`)
  return response.data
}

export async function getStockPrice(stockId: number): Promise<{
  ticker: string
  current_price: number
}> {
  const response = await api.get(`/stocks/${stockId}/price`)
  return response.data
}

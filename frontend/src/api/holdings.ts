import api from '../lib/api'
import type { Holding, MarketType } from '../types'

export async function getHoldings(market?: MarketType): Promise<Holding[]> {
  const params = market ? { market } : undefined
  const response = await api.get('/holdings', { params })
  return response.data
}

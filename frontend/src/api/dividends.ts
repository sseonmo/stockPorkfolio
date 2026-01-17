import api from '../lib/api'
import type { Dividend, DividendCreate, DividendUpdate } from '../types'

export async function getDividends(params?: {
  stock_id?: number
  year?: string
  limit?: number
  skip?: number
}): Promise<Dividend[]> {
  const response = await api.get('/dividends', { params })
  return response.data
}

export async function createDividend(
  data: DividendCreate
): Promise<Dividend> {
  const response = await api.post('/dividends', data)
  return response.data
}

export async function updateDividend(
  id: number,
  data: DividendUpdate
): Promise<Dividend> {
  const response = await api.put(`/dividends/${id}`, data)
  return response.data
}

export async function deleteDividend(id: number): Promise<void> {
  await api.delete(`/dividends/${id}`)
}

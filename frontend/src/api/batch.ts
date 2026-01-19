import api from '../lib/api'

export interface BatchResponse {
  status: string
  message: string
  task: string
  target_date?: string
}

export async function updateKrPrices(targetDate?: string): Promise<BatchResponse> {
  const params = targetDate ? { target_date: targetDate } : {}
  const response = await api.post('/batch/update-kr-prices', null, { params })
  return response.data
}

export async function updateUsPrices(targetDate?: string): Promise<BatchResponse> {
  const params = targetDate ? { target_date: targetDate } : {}
  const response = await api.post('/batch/update-us-prices', null, { params })
  return response.data
}

export async function createSnapshot(targetDate?: string): Promise<BatchResponse> {
  const params = targetDate ? { target_date: targetDate } : {}
  const response = await api.post('/batch/create-snapshot', null, { params })
  return response.data
}

export async function refreshAll(targetDate?: string): Promise<BatchResponse> {
  const params = targetDate ? { target_date: targetDate } : {}
  const response = await api.post('/batch/refresh-all', null, { params })
  return response.data
}

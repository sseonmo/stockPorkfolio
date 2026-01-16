import api from '../lib/api'

export interface BatchResponse {
  status: string
  message: string
  task: string
}

export async function updateKrPrices(): Promise<BatchResponse> {
  const response = await api.post('/batch/update-kr-prices')
  return response.data
}

export async function updateUsPrices(): Promise<BatchResponse> {
  const response = await api.post('/batch/update-us-prices')
  return response.data
}

export async function createSnapshot(): Promise<BatchResponse> {
  const response = await api.post('/batch/create-snapshot')
  return response.data
}

export async function refreshAll(): Promise<BatchResponse> {
  const response = await api.post('/batch/refresh-all')
  return response.data
}

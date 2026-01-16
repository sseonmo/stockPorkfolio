import api from '../lib/api'
import type { Transaction, TransactionCreate, TransactionType } from '../types'

export async function getTransactions(params?: {
  stock_id?: number
  transaction_type?: TransactionType
  start_date?: string
  end_date?: string
  limit?: number
  offset?: number
}): Promise<Transaction[]> {
  const response = await api.get('/transactions', { params })
  return response.data
}

export async function getTransaction(id: number): Promise<Transaction> {
  const response = await api.get(`/transactions/${id}`)
  return response.data
}

export async function createTransaction(
  data: TransactionCreate
): Promise<Transaction> {
  const response = await api.post('/transactions', data)
  return response.data
}

export async function updateTransaction(
  id: number,
  data: Partial<TransactionCreate>
): Promise<Transaction> {
  const response = await api.put(`/transactions/${id}`, data)
  return response.data
}

export async function deleteTransaction(id: number): Promise<void> {
  await api.delete(`/transactions/${id}`)
}

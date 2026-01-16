import api from '../lib/api'
import type {
  SectorAllocation,
  BenchmarkComparison,
  RiskMetrics,
} from '../types'

export async function getSectorAllocation(): Promise<SectorAllocation[]> {
  const response = await api.get('/analytics/sectors')
  return response.data
}

export async function getBenchmarkComparison(
  benchmark: string = 'SP500',
  days: number = 90
): Promise<BenchmarkComparison> {
  const response = await api.get('/analytics/benchmark', {
    params: { benchmark, days },
  })
  return response.data
}

export async function getRiskMetrics(days: number = 90): Promise<RiskMetrics> {
  const response = await api.get('/analytics/risk', { params: { days } })
  return response.data
}

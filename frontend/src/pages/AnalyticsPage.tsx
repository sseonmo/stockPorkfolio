import { SectorPieChart } from '../components/analytics/SectorPieChart'
import { BenchmarkChart } from '../components/analytics/BenchmarkChart'
import { RiskMetrics } from '../components/analytics/RiskMetrics'

export function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">분석</h1>
        <p className="text-sm text-gray-500">포트폴리오 성과 상세 분석</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <BenchmarkChart />
        <SectorPieChart />
      </div>

      <div className="mt-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">위험 분석</h2>
        <RiskMetrics />
      </div>
    </div>
  )
}

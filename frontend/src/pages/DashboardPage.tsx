import { SummaryCards } from '../components/dashboard/SummaryCards'
import { AssetTrendChart } from '../components/dashboard/AssetTrendChart'
import { MarketBreakdownChart } from '../components/dashboard/MarketBreakdownChart'
import { BatchActions } from '../components/dashboard/BatchActions'

export function DashboardPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">대시보드</h1>
          <p className="text-sm text-gray-500">포트폴리오에 오신 것을 환영합니다</p>
        </div>
        <BatchActions />
      </div>

      <SummaryCards />

      <div className="grid gap-6 lg:grid-cols-4">
        <AssetTrendChart />
        <div className="lg:col-span-1">
          <MarketBreakdownChart />
        </div>
      </div>
    </div>
  )
}

import { usePeriodReturns } from '../../hooks/useAnalytics'
import { Card } from '../ui/Card'
import { Loading } from '../ui/Loading'
import { formatPercent } from '../../lib/utils'
import { Calendar, BarChart3 } from 'lucide-react'

export function WidgetPeriodReturn({ type }: { type: 'short' | 'long' }) {
  const { data: returns, isLoading } = usePeriodReturns()

  if (isLoading) return <Card className="h-full flex items-center justify-center"><Loading /></Card>
  if (!returns) return null

  if (type === 'short') {
    return (
      <Card className="h-full p-4 flex flex-col overflow-hidden">
        <div className="flex items-center gap-2 mb-3 shrink-0">
          <div className="p-1.5 bg-blue-50 rounded text-blue-600">
            <Calendar className="h-4 w-4" />
          </div>
          <span className="text-sm font-medium text-gray-600">단기 성과</span>
        </div>
        <div className="flex-1 flex flex-col justify-around min-h-0 space-y-1">
          <div>
            <span className="text-xs text-gray-500 block mb-0.5">최근 1개월</span>
            <span className={`text-lg font-bold ${returns.one_month >= 0 ? 'text-red-600' : 'text-blue-600'}`}>
              {formatPercent(returns.one_month)}
            </span>
          </div>
          <div className="pt-2 border-t border-gray-50">
            <span className="text-xs text-gray-500 block mb-0.5">최근 3개월</span>
            <span className={`text-lg font-bold ${returns.three_months >= 0 ? 'text-red-600' : 'text-blue-600'}`}>
              {formatPercent(returns.three_months)}
            </span>
          </div>
        </div>
      </Card>
    )
  }

  return (
    <Card className="h-full p-4 flex flex-col overflow-hidden">
      <div className="flex items-center gap-2 mb-3 shrink-0">
        <div className="p-1.5 bg-purple-50 rounded text-purple-600">
          <BarChart3 className="h-4 w-4" />
        </div>
        <span className="text-sm font-medium text-gray-600">장기 성과</span>
      </div>
      <div className="flex-1 flex flex-col justify-around min-h-0 space-y-1">
        <div>
          <span className="text-xs text-gray-500 block mb-0.5">연초 대비 (YTD)</span>
          <span className={`text-lg font-bold ${returns.ytd >= 0 ? 'text-red-600' : 'text-blue-600'}`}>
            {formatPercent(returns.ytd)}
          </span>
        </div>
        <div className="pt-2 border-t border-gray-50">
          <span className="text-xs text-gray-500 block mb-0.5">최근 1년</span>
          <span className={`text-lg font-bold ${returns.one_year >= 0 ? 'text-red-600' : 'text-blue-600'}`}>
            {formatPercent(returns.one_year)}
          </span>
        </div>
      </div>
    </Card>
  )
}

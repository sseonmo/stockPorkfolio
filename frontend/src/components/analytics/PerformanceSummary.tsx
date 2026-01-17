import { usePeriodReturns, useWinLossStats } from '../../hooks/useAnalytics'
import { Card } from '../ui/Card'
import { Loading } from '../ui/Loading'
import { formatPercent, formatDate } from '../../lib/utils'
import { Trophy, TrendingDown, Calendar, BarChart3 } from 'lucide-react'

export function PerformanceSummary() {
  const { data: returns, isLoading: isLoadingReturns } = usePeriodReturns()
  const { data: stats, isLoading: isLoadingStats } = useWinLossStats(365)

  if (isLoadingReturns || isLoadingStats) return <Card className="h-[200px] flex items-center justify-center"><Loading /></Card>
  if (!returns || !stats) return null

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {/* 1 Month & 3 Months */}
      <Card className="p-4 bg-white border-gray-200">
        <div className="flex items-center gap-3 mb-3">
          <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
            <Calendar className="h-5 w-5" />
          </div>
          <span className="text-sm font-medium text-gray-600">단기 성과</span>
        </div>
        <div className="space-y-2">
          <div className="flex justify-between items-baseline">
            <span className="text-xs text-gray-500">최근 1개월</span>
            <span className={`text-sm font-bold ${returns.one_month >= 0 ? 'text-red-600' : 'text-blue-600'}`}>
              {formatPercent(returns.one_month)}
            </span>
          </div>
          <div className="flex justify-between items-baseline pt-2 border-t border-gray-100">
            <span className="text-xs text-gray-500">최근 3개월</span>
            <span className={`text-sm font-bold ${returns.three_months >= 0 ? 'text-red-600' : 'text-blue-600'}`}>
              {formatPercent(returns.three_months)}
            </span>
          </div>
        </div>
      </Card>

      {/* 1 Year & YTD */}
      <Card className="p-4 bg-white border-gray-200">
        <div className="flex items-center gap-3 mb-3">
          <div className="p-2 bg-purple-50 rounded-lg text-purple-600">
            <BarChart3 className="h-5 w-5" />
          </div>
          <span className="text-sm font-medium text-gray-600">중장기 성과</span>
        </div>
        <div className="space-y-2">
          <div className="flex justify-between items-baseline">
            <span className="text-xs text-gray-500">올해 수익률 (YTD)</span>
            <span className={`text-sm font-bold ${returns.ytd >= 0 ? 'text-red-600' : 'text-blue-600'}`}>
              {formatPercent(returns.ytd)}
            </span>
          </div>
          <div className="flex justify-between items-baseline pt-2 border-t border-gray-100">
            <span className="text-xs text-gray-500">최근 1년</span>
            <span className={`text-sm font-bold ${returns.one_year >= 0 ? 'text-red-600' : 'text-blue-600'}`}>
              {formatPercent(returns.one_year)}
            </span>
          </div>
        </div>
      </Card>

      {/* Best Day */}
      <Card className="p-4 bg-gradient-to-br from-amber-50 to-white border-amber-100">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-amber-100 rounded-lg text-amber-600">
            <Trophy className="h-5 w-5" />
          </div>
          <span className="text-sm font-medium text-gray-600">최고의 날</span>
        </div>
        <div>
          <h3 className="text-xl font-bold text-red-600">+{formatPercent(stats.best_day_return)}</h3>
          <p className="text-xs text-gray-500 mt-1">
            {stats.best_day ? formatDate(stats.best_day) : '-'}
          </p>
        </div>
      </Card>

      {/* Worst Day */}
      <Card className="p-4 bg-gradient-to-br from-gray-50 to-white border-gray-100">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-gray-100 rounded-lg text-gray-600">
            <TrendingDown className="h-5 w-5" />
          </div>
          <span className="text-sm font-medium text-gray-600">최악의 날</span>
        </div>
        <div>
          <h3 className="text-xl font-bold text-blue-600">{formatPercent(stats.worst_day_return)}</h3>
          <p className="text-xs text-gray-500 mt-1">
            {stats.worst_day ? formatDate(stats.worst_day) : '-'}
          </p>
        </div>
      </Card>
    </div>
  )
}

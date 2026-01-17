import { useWinLossStats } from '../../hooks/useAnalytics'
import { Card } from '../ui/Card'
import { Loading } from '../ui/Loading'
import { formatPercent, formatDate } from '../../lib/utils'
import { Trophy, TrendingUp, TrendingDown, Target } from 'lucide-react'

export function TradingStats() {
  const { data: stats, isLoading } = useWinLossStats(365)

  if (isLoading) return <Card className="h-[200px] flex items-center justify-center"><Loading /></Card>
  if (!stats) return null

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {/* Win Rate */}
      <Card className="p-4 bg-gradient-to-br from-blue-50 to-white border-blue-100">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
            <Target className="h-5 w-5" />
          </div>
          <span className="text-sm font-medium text-gray-600">승률 (Win Rate)</span>
        </div>
        <div className="flex items-baseline gap-2">
          <h3 className="text-2xl font-bold text-gray-900">{stats.win_rate.toFixed(1)}%</h3>
          <span className="text-xs text-gray-500">
            ({stats.up_days}승 {stats.down_days}패)
          </span>
        </div>
        <div className="mt-2 text-xs text-gray-500">
          총 {stats.total_days}거래일 중
        </div>
      </Card>

      {/* Avg Profit/Loss */}
      <Card className="p-4 bg-gradient-to-br from-green-50 to-white border-green-100">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-green-100 rounded-lg text-green-600">
            <TrendingUp className="h-5 w-5" />
          </div>
          <span className="text-sm font-medium text-gray-600">평균 손익비</span>
        </div>
        <div className="flex flex-col gap-1">
          <div className="flex justify-between items-center">
            <span className="text-xs text-gray-500">평균 수익</span>
            <span className="text-sm font-bold text-red-600">+{stats.avg_win_percent.toFixed(2)}%</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-xs text-gray-500">평균 손실</span>
            <span className="text-sm font-bold text-blue-600">{stats.avg_loss_percent.toFixed(2)}%</span>
          </div>
          <div className="mt-1 pt-1 border-t border-green-100 flex justify-between">
            <span className="text-xs font-medium text-gray-600">Profit Factor</span>
            <span className="text-xs font-bold text-green-700">{stats.profit_factor.toFixed(2)}</span>
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

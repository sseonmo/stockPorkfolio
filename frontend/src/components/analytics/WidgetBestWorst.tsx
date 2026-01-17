import { useWinLossStats } from '../../hooks/useAnalytics'
import { Card } from '../ui/Card'
import { Loading } from '../ui/Loading'
import { formatPercent, formatDate } from '../../lib/utils'
import { Trophy, TrendingDown } from 'lucide-react'

export function WidgetBestWorst({ type }: { type: 'best' | 'worst' }) {
  const { data: stats, isLoading } = useWinLossStats(365)

  if (isLoading) return <Card className="h-full flex items-center justify-center"><Loading /></Card>
  if (!stats) return null

  if (type === 'best') {
    return (
      <Card className="h-full p-4 bg-gradient-to-br from-amber-50 to-white border-amber-100 flex flex-col justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-amber-100 rounded text-amber-600">
            <Trophy className="h-4 w-4" />
          </div>
          <span className="text-sm font-medium text-gray-600">최고의 날</span>
        </div>
        <div>
          <h3 className="text-2xl font-bold text-red-600">{formatPercent(stats.best_day_return)}</h3>
          <p className="text-xs text-gray-500 mt-1">
            {stats.best_day ? formatDate(stats.best_day) : '-'}
          </p>
        </div>
      </Card>
    )
  }

  return (
    <Card className="h-full p-4 bg-gradient-to-br from-gray-50 to-white border-gray-100 flex flex-col justify-between">
      <div className="flex items-center gap-2">
        <div className="p-1.5 bg-gray-100 rounded text-gray-600">
          <TrendingDown className="h-4 w-4" />
        </div>
        <span className="text-sm font-medium text-gray-600">최악의 날</span>
      </div>
      <div>
        <h3 className="text-2xl font-bold text-blue-600">{formatPercent(stats.worst_day_return)}</h3>
        <p className="text-xs text-gray-500 mt-1">
          {stats.worst_day ? formatDate(stats.worst_day) : '-'}
        </p>
      </div>
    </Card>
  )
}

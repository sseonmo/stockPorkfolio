import { useRiskMetrics } from '../../hooks/useAnalytics'
import { Card } from '../ui/Card'
import { Loading } from '../ui/Loading'
import { formatPercent, formatDate } from '../../lib/utils'
import { TrendingDown, ShieldCheck } from 'lucide-react'

export function WidgetRisk({ type }: { type: 'mdd' | 'score' }) {
  const { data: risk, isLoading } = useRiskMetrics()

  if (isLoading) return <Card className="h-full flex items-center justify-center"><Loading /></Card>
  if (!risk) return null

  if (type === 'mdd') {
    return (
      <Card className="h-full p-4 bg-red-50 border-red-100 flex flex-col justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-red-100 rounded text-red-600">
            <TrendingDown className="h-4 w-4" />
          </div>
          <span className="text-sm font-medium text-red-600/80">최대 낙폭 (MDD)</span>
        </div>
        <div>
          <h3 className="text-2xl font-bold text-red-700">{formatPercent(risk.max_drawdown_percent)}</h3>
          {risk.max_drawdown_start && (
            <p className="text-xs text-red-600/60 mt-1">
              {formatDate(risk.max_drawdown_start)} ~ {risk.max_drawdown_end ? formatDate(risk.max_drawdown_end) : '현재'}
            </p>
          )}
        </div>
      </Card>
    )
  }

  return (
    <Card className="h-full p-4 bg-blue-50 border-blue-100 flex flex-col justify-between">
      <div className="flex items-center gap-2">
        <div className="p-1.5 bg-blue-100 rounded text-blue-600">
          <ShieldCheck className="h-4 w-4" />
        </div>
        <span className="text-sm font-medium text-blue-600/80">분산투자 점수</span>
      </div>
      <div>
        <h3 className="text-2xl font-bold text-blue-700">{risk.diversification_score}/100</h3>
        <p className="text-xs text-blue-600/60 mt-1">
          섹터 및 종목 분산도 기반
        </p>
      </div>
    </Card>
  )
}

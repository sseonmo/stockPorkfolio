import { useRiskMetrics } from '../../hooks/useAnalytics'
import { Card } from '../ui/Card'
import { Loading } from '../ui/Loading'
import { formatPercent, formatDate } from '../../lib/utils'
import { AlertTriangle, ShieldCheck, TrendingDown } from 'lucide-react'

export function RiskMetrics() {
  const { data: risk, isLoading } = useRiskMetrics()

  if (isLoading) return <Card className="p-8"><Loading /></Card>
  if (!risk) return null

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="bg-red-50 border-red-100">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-red-100 rounded-lg">
              <TrendingDown className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-red-600/80">최대 손실폭 (MDD)</p>
              <h3 className="text-2xl font-bold text-red-700">{formatPercent(risk.max_drawdown_percent)}</h3>
              {risk.max_drawdown_start && (
                <p className="text-xs text-red-600/60 mt-1">
                  {formatDate(risk.max_drawdown_start)} - {risk.max_drawdown_end ? formatDate(risk.max_drawdown_end) : '현재'}
                </p>
              )}
            </div>
          </div>
        </Card>

        <Card className="bg-blue-50 border-blue-100">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <ShieldCheck className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-blue-600/80">분산투자 점수</p>
              <h3 className="text-2xl font-bold text-blue-700">{risk.diversification_score}/100</h3>
              <p className="text-xs text-blue-600/60 mt-1">
                섹터 분산도 기반
              </p>
            </div>
          </div>
        </Card>

        <Card className="bg-amber-50 border-amber-100">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-amber-100 rounded-lg">
              <AlertTriangle className="h-6 w-6 text-amber-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-amber-600/80">상위 5개 집중도</p>
              <h3 className="text-2xl font-bold text-amber-700">{formatPercent(risk.top_5_weight_percent)}</h3>
              <p className="text-xs text-amber-600/60 mt-1">
                상위 5개 종목 비중
              </p>
            </div>
          </div>
        </Card>
      </div>

      {risk.concentration_warnings.length > 0 && (
        <Card className="border-amber-200 bg-amber-50/50">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            <h3 className="font-semibold text-amber-900">집중 투자 경고</h3>
          </div>
          <div className="space-y-2">
            {risk.concentration_warnings.map((warning) => (
              <div key={warning.ticker} className="flex items-center justify-between text-sm p-2 bg-white rounded border border-amber-100">
                <div className="font-medium text-amber-900">
                  {warning.name} ({warning.ticker})
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-amber-700">
                    비중: {formatPercent(warning.weight_percent)}
                  </span>
                  <span className="text-xs text-amber-600 bg-amber-100 px-2 py-0.5 rounded-full">
                    &gt; {warning.threshold_percent}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}

import { useRiskMetrics } from '../../hooks/useAnalytics'
import { Card } from '../ui/Card'
import { Loading } from '../ui/Loading'
import { formatPercent } from '../../lib/utils'
import { AlertTriangle } from 'lucide-react'

export function WidgetConcentration() {
  const { data: risk, isLoading } = useRiskMetrics()

  if (isLoading) return <Card className="h-full flex items-center justify-center"><Loading /></Card>
  if (!risk) return null

  return (
    <Card className="h-full p-4 border-amber-200 bg-amber-50/50 flex flex-col">
      <div className="flex items-center gap-2 mb-3">
        <AlertTriangle className="h-5 w-5 text-amber-500" />
        <h3 className="font-semibold text-amber-900">집중 투자 경고</h3>
      </div>
      <div className="flex-1 overflow-y-auto space-y-2 pr-1">
        {risk.concentration_warnings.length === 0 ? (
          <div className="text-sm text-amber-800/60 text-center py-4">
            특이사항 없음
          </div>
        ) : (
          risk.concentration_warnings.map((warning) => (
            <div key={warning.ticker} className="flex items-center justify-between text-sm p-2 bg-white rounded border border-amber-100">
              <div className="font-medium text-amber-900 truncate mr-2">
                {warning.name}
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <span className="text-amber-700 font-medium">
                  {formatPercent(warning.weight_percent)}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  )
}

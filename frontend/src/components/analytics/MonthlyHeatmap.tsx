import { useMonthlyReturns } from '../../hooks/useAnalytics'
import { Card } from '../ui/Card'
import { Loading } from '../ui/Loading'
import { formatPercent, formatCurrency, cn } from '../../lib/utils'

export function MonthlyHeatmap() {
  const { data: returns, isLoading } = useMonthlyReturns()

  if (isLoading) return <Card className="h-[400px] flex items-center justify-center"><Loading /></Card>
  if (!returns || returns.length === 0) return null

  // Group by year
  const years = Array.from(new Set(returns.map(r => r.year))).sort((a, b) => b - a)
  const months = Array.from({ length: 12 }, (_, i) => i + 1)

  const getReturn = (year: number, month: number) => {
    return returns.find(r => r.year === year && r.month === month)
  }

  const getColorClass = (value: number) => {
    if (value > 0) {
      if (value > 10) return "bg-red-600 text-white"
      if (value > 5) return "bg-red-500 text-white"
      if (value > 3) return "bg-red-400 text-white"
      if (value > 1) return "bg-red-300 text-red-900"
      return "bg-red-100 text-red-800"
    } else if (value < 0) {
      if (value < -10) return "bg-blue-600 text-white"
      if (value < -5) return "bg-blue-500 text-white"
      if (value < -3) return "bg-blue-400 text-white"
      if (value < -1) return "bg-blue-300 text-blue-900"
      return "bg-blue-100 text-blue-800"
    }
    return "bg-gray-50 text-gray-400"
  }

  // Calculate YTD
  const getYtd = (year: number) => {
    const yearReturns = returns.filter(r => r.year === year).sort((a, b) => a.month - b.month)
    if (yearReturns.length === 0) return 0
    
    // Simple sum for now, or could link geometrically if we had proper return data
    // Assuming return_percent is simple return
    let ytd = 1
    for (const r of yearReturns) {
        ytd *= (1 + r.return_percent / 100)
    }
    return (ytd - 1) * 100
  }

  return (
    <Card className="h-full p-6 flex flex-col overflow-hidden">
      <div className="mb-4 shrink-0">
        <h3 className="text-lg font-semibold text-gray-900">월별 수익률</h3>
        <p className="text-sm text-gray-500">연도별/월별 포트폴리오 성과</p>
      </div>

      <div className="flex-1 overflow-auto min-h-0">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr>
              <th className="p-2 text-left font-medium text-gray-500 w-16">연도</th>
              {months.map(m => (
                <th key={m} className="p-2 text-center font-medium text-gray-500 w-16">{m}월</th>
              ))}
              <th className="p-2 text-right font-medium text-gray-900 w-20">YTD</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {years.map(year => {
              const ytd = getYtd(year)
              return (
                <tr key={year}>
                  <td className="p-2 font-medium text-gray-900">{year}</td>
                  {months.map(month => {
                    const data = getReturn(year, month)
                    return (
                      <td key={month} className="p-1">
                        {data ? (
                          <div 
                            className={cn(
                              "w-full h-10 flex items-center justify-center rounded text-xs font-medium transition-colors cursor-default",
                              getColorClass(data.return_percent)
                            )}
                            title={`${year}년 ${month}월\n수익률: ${formatPercent(data.return_percent)}\n시작: ${formatCurrency(data.starting_value, 'KRW')}\n종료: ${formatCurrency(data.ending_value, 'KRW')}`}
                          >
                            {data.return_percent > 0 ? '+' : ''}{data.return_percent.toFixed(1)}%
                          </div>
                        ) : (
                          <div className="w-full h-10 bg-gray-50 rounded" />
                        )}
                      </td>
                    )
                  })}
                  <td className={cn(
                    "p-2 text-right font-bold",
                    ytd >= 0 ? "text-red-600" : "text-blue-600"
                  )}>
                    {ytd > 0 ? '+' : ''}{ytd.toFixed(1)}%
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </Card>
  )
}

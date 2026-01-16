import { useHoldings } from '../../hooks/useHoldings'
import { MarketType } from '../../types'
import { Card } from '../ui/Card'
import { Loading } from '../ui/Loading'
import { formatCurrency, formatPercent, cn } from '../../lib/utils'
import { ArrowUpRight, ArrowDownRight } from 'lucide-react'

interface HoldingsTableProps {
  market: MarketType | 'ALL'
}

export function HoldingsTable({ market }: HoldingsTableProps) {
  const queryMarket = market === 'ALL' ? undefined : market
  const { data: holdings, isLoading } = useHoldings(queryMarket)

  if (isLoading) return <Card className="p-12"><Loading /></Card>

  if (!holdings || holdings.length === 0) {
    return (
      <Card className="flex flex-col items-center justify-center py-12 text-center">
        <div className="rounded-full bg-gray-100 p-3">
          <ArrowUpRight className="h-6 w-6 text-gray-400" />
        </div>
        <h3 className="mt-4 text-lg font-medium text-gray-900">보유 종목이 없습니다</h3>
        <p className="mt-1 text-sm text-gray-500">
          아직 이 시장에 보유한 주식이 없습니다.
        </p>
      </Card>
    )
  }

  return (
    <Card className="overflow-hidden" noPadding>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-gray-500 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 font-medium">종목</th>
              <th className="px-6 py-3 font-medium text-right">현재가</th>
              <th className="px-6 py-3 font-medium text-right">평단가</th>
              <th className="px-6 py-3 font-medium text-right">보유수량</th>
              <th className="px-6 py-3 font-medium text-right">평가금액</th>
              <th className="px-6 py-3 font-medium text-right">손익</th>
              <th className="px-6 py-3 font-medium text-right">비중</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {holdings.map((holding) => {
              const isGain = holding.unrealized_gain >= 0
              return (
                <tr key={holding.id} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <div>
                        <div className="font-medium text-gray-900">{holding.stock.name}</div>
                        <div className="text-xs text-gray-500">{holding.stock.ticker}</div>
                      </div>
                      <span className={cn(
                        "ml-2 text-[10px] px-1.5 py-0.5 rounded font-medium",
                        holding.stock.market_type === 'KR' ? "bg-blue-50 text-blue-600" : "bg-violet-50 text-violet-600"
                      )}>
                        {holding.stock.market_type}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    {formatCurrency(holding.stock.current_price || 0, holding.stock.currency)}
                  </td>
                  <td className="px-6 py-4 text-right text-gray-500">
                    {formatCurrency(holding.average_cost, holding.stock.currency)}
                  </td>
                  <td className="px-6 py-4 text-right font-medium">
                    {holding.quantity.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-right font-medium text-gray-900">
                    {formatCurrency(holding.current_value_krw, 'KRW')}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className={cn("flex items-center justify-end font-medium", isGain ? "text-green-600" : "text-red-600")}>
                      {isGain ? <ArrowUpRight className="w-3 h-3 mr-1" /> : <ArrowDownRight className="w-3 h-3 mr-1" />}
                      {formatPercent(holding.unrealized_gain_percent)}
                    </div>
                    <div className={cn("text-xs", isGain ? "text-green-600/70" : "text-red-600/70")}>
                      {formatCurrency(holding.unrealized_gain, 'KRW')}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right text-gray-500">
                    {formatPercent(holding.weight_percent)}
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

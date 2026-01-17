import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { useSectorAllocation } from '../../hooks/useAnalytics'
import { Card } from '../ui/Card'
import { formatCurrency, formatPercent } from '../../lib/utils'
import { Loading } from '../ui/Loading'

const COLORS = [
  '#3B82F6', '#10B981', '#F59E0B', '#EF4444',
  '#8B5CF6', '#EC4899', '#6366F1', '#14B8A6',
  '#F43F5E', '#A855F7', '#06B6D4', '#22C55E'
]

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload
    return (
      <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg text-sm max-w-xs">
        <div className="font-bold text-gray-900 mb-1">{data.sector}</div>
        <div className="text-gray-600 mb-2">
          총액: <span className="font-mono font-medium text-gray-900">{formatCurrency(data.value_krw, 'KRW')}</span> ({formatPercent(data.weight_percent)})
        </div>
        
        {data.stocks && data.stocks.length > 0 && (
          <div className="border-t border-gray-100 pt-2 mt-2">
            <div className="text-xs font-medium text-gray-500 mb-1">구성 종목</div>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {data.stocks.map((stock: any) => (
                <div key={stock.ticker} className="flex justify-between text-xs">
                  <span className="text-gray-700 truncate mr-2">{stock.name}</span>
                  <span className="text-gray-500 whitespace-nowrap">
                    {formatCurrency(stock.value_krw, 'KRW')} ({formatPercent(stock.weight_percent)})
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }
  return null
}

export function SectorPieChart() {
  const { data: sectors, isLoading } = useSectorAllocation()

  if (isLoading) return <Card className="h-full flex items-center justify-center"><Loading /></Card>
  if (!sectors) return null

  const data = sectors.map((item) => ({
    name: item.sector,
    value: item.value_krw,
    ...item
  }))

  return (
    <Card className="h-full flex flex-col p-4">
      <div className="mb-2 shrink-0">
        <h3 className="text-lg font-semibold text-gray-900">섹터 비중</h3>
        <p className="text-sm text-gray-500">산업별 분산 현황</p>
      </div>
      <div className="flex-1 w-full min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="45%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={2}
              dataKey="value"
            >
              {data.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} strokeWidth={0} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend
              layout="vertical"
              verticalAlign="bottom"
              align="center"
              height={100}
              wrapperStyle={{ overflowY: 'auto' }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}

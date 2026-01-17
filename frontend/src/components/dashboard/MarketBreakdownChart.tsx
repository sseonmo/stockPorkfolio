import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { useMarketBreakdown } from '../../hooks/useDashboard'
import { Card } from '../ui/Card'
import { formatCurrency } from '../../lib/utils'
import { Loading } from '../ui/Loading'

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444']

export function MarketBreakdownChart() {
  const { data: breakdown, isLoading } = useMarketBreakdown()

  if (isLoading) return <Card className="h-full"><div className="h-full flex items-center justify-center"><Loading /></div></Card>
  if (!breakdown || breakdown.length === 0) return (
    <Card className="h-full flex flex-col">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">시장별 비중</h3>
        <p className="text-sm text-gray-500">시장 지역별 노출</p>
      </div>
      <div className="flex-1 flex items-center justify-center text-gray-500">
        보유 종목이 없습니다
      </div>
    </Card>
  )

  // Transform data for PieChart
  const data = breakdown.map((item) => ({
    name: item.market_type === 'KR' ? '국내 (KR)' : '해외 (US)',
    value: item.value_krw,
    original: item,
  }))

  return (
    <Card className="h-full flex flex-col">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">시장별 비중</h3>
        <p className="text-sm text-gray-500">시장 지역별 노출</p>
      </div>
      <div className="w-full flex-1" style={{ minHeight: 200 }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={90}
              paddingAngle={5}
              dataKey="value"
            >
              {data.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} strokeWidth={0} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #E5E7EB',
                borderRadius: '0.5rem',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
              }}
              formatter={(value: number) => formatCurrency(value, 'KRW')}
            />
            <Legend verticalAlign="bottom" height={36} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}

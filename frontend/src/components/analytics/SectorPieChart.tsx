import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { useSectorAllocation } from '../../hooks/useAnalytics'
import { Card } from '../ui/Card'
import { formatCurrency } from '../../lib/utils'
import { Loading } from '../ui/Loading'

const COLORS = [
  '#3B82F6', '#10B981', '#F59E0B', '#EF4444',
  '#8B5CF6', '#EC4899', '#6366F1', '#14B8A6',
  '#F43F5E', '#A855F7', '#06B6D4', '#22C55E'
]

export function SectorPieChart() {
  const { data: sectors, isLoading } = useSectorAllocation()

  if (isLoading) return <Card className="h-[400px] flex items-center justify-center"><Loading /></Card>
  if (!sectors) return null

  const data = sectors.map((item) => ({
    name: item.sector || '미분류',
    value: item.value_krw,
    ...item
  }))

  return (
    <Card className="h-[500px] flex flex-col">
      <div className="mb-4">
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
              innerRadius={80}
              outerRadius={120}
              paddingAngle={2}
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
            <Legend
              layout="vertical"
              verticalAlign="bottom"
              align="center"
              height={120}
              wrapperStyle={{ overflowY: 'auto' }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}

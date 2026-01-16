import {
  Line,
  LineChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from 'recharts'
import { useBenchmarkComparison } from '../../hooks/useAnalytics'
import { Card } from '../ui/Card'
import { formatShortDate, formatPercent } from '../../lib/utils'
import { Loading } from '../ui/Loading'
import { useState } from 'react'

export function BenchmarkChart() {
  const [benchmark, setBenchmark] = useState('SP500')
  const { data: comparison, isLoading } = useBenchmarkComparison(benchmark, 90)

  if (isLoading) return <Card className="h-[400px] flex items-center justify-center"><Loading /></Card>
  if (!comparison?.data) return null

  return (
    <Card className="col-span-1 md:col-span-2 h-[400px]">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">벤치마크 비교</h3>
          <p className="text-sm text-gray-500">포트폴리오 vs {comparison.benchmark_name} (지난 90일)</p>
        </div>
        <div className="flex space-x-2">
          {['SP500', 'NASDAQ', 'KOSPI'].map((b) => (
            <button
              key={b}
              onClick={() => setBenchmark(b)}
              className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${benchmark === b
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
            >
              {b}
            </button>
          ))}
        </div>
      </div>

      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={comparison.data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
            <XAxis
              dataKey="date"
              tickFormatter={formatShortDate}
              stroke="#9CA3AF"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              dy={10}
            />
            <YAxis
              tickFormatter={(val) => `${val}%`}
              stroke="#9CA3AF"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              dx={-10}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #E5E7EB',
                borderRadius: '0.5rem',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
              }}
              formatter={(value: number) => formatPercent(value)}
              labelFormatter={formatShortDate}
            />
            <Legend verticalAlign="top" height={36} />
            <Line
              name="내 포트폴리오"
              type="monotone"
              dataKey="portfolio_return_percent"
              stroke="#3B82F6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6 }}
            />
            <Line
              name={comparison.benchmark_name}
              type="monotone"
              dataKey="benchmark_return_percent"
              stroke="#9CA3AF"
              strokeWidth={2}
              strokeDasharray="4 4"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}

import { useState, useMemo } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Calendar, ChevronDown, Settings2 } from 'lucide-react'
import { useAssetTrend } from '../../hooks/useDashboard'
import { useHoldings } from '../../hooks/useHoldings'
import { Card } from '../ui/Card'
import { formatCurrency, formatShortDate, cn } from '../../lib/utils'
import { Loading } from '../ui/Loading'

type DatePreset = 'today' | 'week' | 'month'

function formatDate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function getDateRange(preset: DatePreset): { start: string; end: string } {
  const end = new Date()
  const start = new Date()
  
  switch (preset) {
    case 'today':
      start.setDate(start.getDate() - 1)
      break
    case 'week':
      start.setDate(start.getDate() - 7)
      break
    case 'month':
      start.setMonth(start.getMonth() - 1)
      break
  }
  
  return {
    start: formatDate(start),
    end: formatDate(end),
  }
}

export function AssetTrendChart() {
  const initialRange = getDateRange('week')
  const [datePreset, setDatePreset] = useState<DatePreset>('week')
  
  // UI 입력 상태 (실시간 변경)
  const [customStartDate, setCustomStartDate] = useState(initialRange.start)
  const [customEndDate, setCustomEndDate] = useState(initialRange.end)

  // API 요청 상태 (조회 시점에만 변경)
  const [appliedStartDate, setAppliedStartDate] = useState(initialRange.start)
  const [appliedEndDate, setAppliedEndDate] = useState(initialRange.end)

  const [selectedStockIds, setSelectedStockIds] = useState<number[]>([])
  const [showStockDropdown, setShowStockDropdown] = useState(false)
  const [yAxisMode, setYAxisMode] = useState<'auto' | 'manual'>('auto')
  const [yAxisPadding, setYAxisPadding] = useState(10)

  const queryClient = useQueryClient()
  const { data: holdings } = useHoldings()

  const { data: trend, isLoading, isFetching } = useAssetTrend({
    start_date: appliedStartDate,
    end_date: appliedEndDate,
    stock_ids: selectedStockIds.length > 0 ? selectedStockIds : undefined,
  })

  const chartData = useMemo(() => {
    if (!trend?.data) return []
    
    // appliedStartDate부터 EndDate까지의 모든 날짜를 생성하여 데이터 채우기
    const start = new Date(appliedStartDate)
    const end = new Date(appliedEndDate)
    
    if (isNaN(start.getTime()) || isNaN(end.getTime())) return trend.data
    
    const dataMap = new Map(trend.data.map(item => [item.date, item]))
    const filledData = []
    const currentDate = new Date(start)
    
    // 시작일이 종료일보다 늦으면 빈 배열 반환 (에러 방지)
    if (start > end) return []

    while (currentDate <= end) {
      const dateStr = formatDate(currentDate)
      const item = dataMap.get(dateStr)
      
      if (item) {
        filledData.push(item)
      } else {
        // 데이터가 없는 날짜는 null 값으로 채움 (차트에서 끊겨 보이거나 빈 공간 처리)
        filledData.push({
          date: dateStr,
          total_value_krw: null as unknown as number, // 타입 우회: recharts는 null 처리 가능
          daily_pnl: 0,
          daily_pnl_percent: 0,
          cumulative_return_percent: 0
        })
      }
      currentDate.setDate(currentDate.getDate() + 1)
    }
    
    return filledData
  }, [trend?.data, appliedStartDate, appliedEndDate])

  const yAxisDomain = useMemo(() => {
    if (chartData.length === 0) return [0, 'auto'] as const
    
    // null이 아닌 값만 필터링
    const values = chartData
      .map(d => d.total_value_krw)
      .filter((v): v is number => v !== null && v !== undefined)
      
    if (values.length === 0) return [0, 'auto'] as const
    
    const min = Math.min(...values)
    const max = Math.max(...values)
    const range = max - min
    
    if (yAxisMode === 'auto') {
      const padding = range * (yAxisPadding / 100)
      const paddedMin = Math.max(0, min - padding)
      const paddedMax = max + padding
      return [paddedMin, paddedMax]
    }
    
    return [0, 'auto'] as const
  }, [chartData, yAxisMode, yAxisPadding])

  const handlePresetClick = (preset: DatePreset) => {
    setDatePreset(preset)
    const range = getDateRange(preset)
    
    // UI 상태 업데이트
    setCustomStartDate(range.start)
    setCustomEndDate(range.end)
    
    // API 상태 업데이트 (즉시 조회)
    setAppliedStartDate(range.start)
    setAppliedEndDate(range.end)
    
    queryClient.invalidateQueries({ queryKey: ['dashboard', 'trend'] })
  }

  const handleDateBlur = () => {
    setAppliedStartDate(customStartDate)
    setAppliedEndDate(customEndDate)
    queryClient.invalidateQueries({ queryKey: ['dashboard', 'trend'] })
  }

  const handleDateKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleDateBlur()
    }
  }

  const handleStockToggle = (stockId: number) => {
    setSelectedStockIds(prev => 
      prev.includes(stockId) 
        ? prev.filter(id => id !== stockId)
        : [...prev, stockId]
    )
  }

  const clearStockFilter = () => {
    setSelectedStockIds([])
  }

  if (isLoading) {
    return (
      <Card className="col-span-4 lg:col-span-3">
        <div className="h-[500px] flex items-center justify-center">
          <Loading />
        </div>
      </Card>
    )
  }

  return (
    <Card className="col-span-4 lg:col-span-3">
      <div className="space-y-4">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              포트폴리오 성장
              {isFetching && !isLoading && <Loading className="h-4 w-4" />}
            </h3>
            <p className="text-sm text-gray-500">
              {selectedStockIds.length > 0 
                ? `선택된 ${selectedStockIds.length}개 종목의 자산 가치 추이`
                : '전체 포트폴리오 자산 가치 추이'
              }
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-gray-400" />
            <input
              type="date"
              value={customStartDate}
              onChange={(e) => setCustomStartDate(e.target.value)}
              onBlur={handleDateBlur}
              onKeyDown={handleDateKeyDown}
              className="text-sm border border-gray-200 rounded-md px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <span className="text-gray-400">~</span>
            <input
              type="date"
              value={customEndDate}
              onChange={(e) => setCustomEndDate(e.target.value)}
              onBlur={handleDateBlur}
              onKeyDown={handleDateKeyDown}
              className="text-sm border border-gray-200 rounded-md px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
            {(['today', 'week', 'month'] as const).map((preset) => (
              <button
                key={preset}
                onClick={() => handlePresetClick(preset)}
                className={cn(
                  'px-3 py-1.5 text-sm font-medium rounded-md transition-all',
                  datePreset === preset
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                )}
              >
                {preset === 'today' ? '오늘' : preset === 'week' ? '1주일' : '한달'}
              </button>
            ))}
          </div>

          <div className="relative">
            <button
              onClick={() => setShowStockDropdown(!showStockDropdown)}
              className={cn(
                'flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-lg border transition-all',
                selectedStockIds.length > 0
                  ? 'border-blue-500 bg-blue-50 text-blue-600'
                  : 'border-gray-200 text-gray-600 hover:border-gray-300'
              )}
            >
              {selectedStockIds.length > 0 ? `${selectedStockIds.length}개 종목` : '전체 종목'}
              <ChevronDown className="h-4 w-4" />
            </button>
            
            {showStockDropdown && (
              <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-10 max-h-64 overflow-y-auto">
                <div className="p-2 border-b border-gray-100">
                  <button
                    onClick={clearStockFilter}
                    className="w-full text-left px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-md"
                  >
                    전체 (필터 해제)
                  </button>
                </div>
                <div className="p-2">
                  {holdings?.map((holding) => (
                    <label
                      key={holding.stock_id}
                      className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-gray-50 rounded-md cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={selectedStockIds.includes(holding.stock_id)}
                        onChange={() => handleStockToggle(holding.stock_id)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="font-medium">{holding.stock.ticker}</span>
                      <span className="text-gray-500 truncate">{holding.stock.name}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <Settings2 className="h-4 w-4 text-gray-400" />
            <span className="text-gray-600">Y축:</span>
            <button
              onClick={() => setYAxisMode(yAxisMode === 'auto' ? 'manual' : 'auto')}
              className={cn(
                'px-2 py-1 rounded text-xs font-medium',
                yAxisMode === 'auto' ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600'
              )}
            >
              {yAxisMode === 'auto' ? '자동' : '0부터'}
            </button>
          </div>
          {yAxisMode === 'auto' && (
            <div className="flex items-center gap-2">
              <span className="text-gray-500">여백:</span>
              <input
                type="range"
                min="0"
                max="50"
                value={yAxisPadding}
                onChange={(e) => setYAxisPadding(Number(e.target.value))}
                className="w-20 h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <span className="text-gray-500 w-8">{yAxisPadding}%</span>
            </div>
          )}
        </div>

        {chartData.length === 0 ? (
          <div className="h-[300px] flex items-center justify-center text-gray-500">
            선택한 기간에 데이터가 없습니다
          </div>
        ) : (
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                  </linearGradient>
                </defs>
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
                  domain={yAxisDomain}
                  tickFormatter={(value) =>
                    new Intl.NumberFormat('ko-KR', { notation: 'compact', maximumFractionDigits: 1 }).format(value)
                  }
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
                  formatter={(value: number) => [formatCurrency(value, 'KRW'), '총 자산']}
                  labelFormatter={formatShortDate}
                />
                <Area
                  type="monotone"
                  dataKey="total_value_krw"
                  stroke="#3B82F6"
                  strokeWidth={3}
                  fillOpacity={1}
                  fill="url(#colorValue)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {trend?.data && trend.data.length > 0 && (
          <div className="flex items-center gap-6 pt-2 border-t border-gray-100 text-sm">
            <div>
              <span className="text-gray-500">기간 수익률: </span>
              <span className={cn(
                'font-semibold',
                trend.period_return_percent >= 0 ? 'text-green-600' : 'text-red-600'
              )}>
                {trend.period_return_percent >= 0 ? '+' : ''}{trend.period_return_percent.toFixed(2)}%
              </span>
            </div>
            <div>
              <span className="text-gray-500">최대 낙폭: </span>
              <span className="font-semibold text-red-600">
                -{trend.max_drawdown_percent.toFixed(2)}%
              </span>
            </div>
          </div>
        )}
      </div>

      {showStockDropdown && (
        <div 
          className="fixed inset-0 z-0" 
          onClick={() => setShowStockDropdown(false)}
        />
      )}
    </Card>
  )
}

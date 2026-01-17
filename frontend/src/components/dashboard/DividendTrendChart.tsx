import { useState, useMemo } from 'react'
import {
  ComposedChart,
  Bar,
  Line,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { ChevronDown, Maximize2, X } from 'lucide-react'
import { useHoldings } from '../../hooks/useHoldings'
import { useDividends } from '../../hooks/useDividends'
import { Card } from '../ui/Card'
import { formatCurrency, cn } from '../../lib/utils'
import { Loading } from '../ui/Loading'
import { Button } from '../ui/Button'

export function DividendTrendChart() {
  const currentYear = new Date().getFullYear().toString()
  const [selectedYear, setSelectedYear] = useState<string>(currentYear)

  const [selectedStockIds, setSelectedStockIds] = useState<number[]>([])
  const [showStockDropdown, setShowStockDropdown] = useState(false)
  const [isFullScreen, setIsFullScreen] = useState(false)

  const { data: holdings } = useHoldings()
  const { data: dividends, isLoading } = useDividends()

  const availableYears = useMemo(() => {
    const currentYearNum = new Date().getFullYear()
    const years: string[] = []
    for (let year = currentYearNum; year >= 2024; year--) {
      years.push(year.toString())
    }
    return years
  }, [])

  // 필터링된 배당 데이터
  const filteredDividends = useMemo(() => {
    if (!dividends) return []
    return dividends.filter(div => {
      if (selectedYear !== 'all') {
        const divYear = div.dividend_date.substring(0, 4)
        if (divYear !== selectedYear) return false
      }
      if (selectedStockIds.length > 0 && !selectedStockIds.includes(div.stock_id)) {
        return false
      }
      return true
    })
  }, [dividends, selectedYear, selectedStockIds])

  // 종목 목록 (색상 할당용)
  const stockList = useMemo(() => {
    if (!holdings) return []
    return holdings.map(h => ({
      id: h.stock_id,
      ticker: h.stock.ticker,
      name: h.stock.name,
    }))
  }, [holdings])

  const chartData = useMemo(() => {
    if (selectedYear !== 'all') {
      const months = Array.from({ length: 12 }, (_, i) => {
        const month = (i + 1).toString().padStart(2, '0')
        return `${selectedYear}-${month}`
      })
      
      const groupedByMonth = filteredDividends.reduce((acc, div) => {
        const month = div.dividend_date.substring(0, 7)
        if (!acc[month]) {
          acc[month] = []
        }
        acc[month].push(div)
        return acc
      }, {} as Record<string, typeof filteredDividends>)
      
      let cumulative = 0
      return months.map(month => {
        const dividendsInMonth = groupedByMonth[month] || []
        const monthlyTotal = dividendsInMonth.reduce((sum, div) => sum + div.amount, 0)
        cumulative += monthlyTotal
        
        const stockAmounts: Record<string, number> = {}
        dividendsInMonth.forEach(div => {
          const key = `stock_${div.stock_id}`
          stockAmounts[key] = (stockAmounts[key] || 0) + div.amount
        })
        
        return {
          date: month,
          ...stockAmounts,
          cumulative_dividend: cumulative
        }
      })
    }
    
    if (!filteredDividends || filteredDividends.length === 0) return []
    
    const groupedByDate = filteredDividends.reduce((acc, div) => {
      const date = div.dividend_date
      if (!acc[date]) {
        acc[date] = []
      }
      acc[date].push(div)
      return acc
    }, {} as Record<string, typeof filteredDividends>)

    const sortedDates = Object.keys(groupedByDate).sort()
    
    let cumulative = 0
    return sortedDates.map(date => {
      const dividendsOnDate = groupedByDate[date]
      const dailyTotal = dividendsOnDate.reduce((sum, div) => sum + div.amount, 0)
      cumulative += dailyTotal
      
      const stockAmounts: Record<string, number> = {}
      dividendsOnDate.forEach(div => {
        const key = `stock_${div.stock_id}`
        stockAmounts[key] = (stockAmounts[key] || 0) + div.amount
      })
      
      return {
        date,
        ...stockAmounts,
        cumulative_dividend: cumulative
      }
    })
  }, [filteredDividends, selectedYear])

  const handleYearChange = (year: string) => {
    setSelectedYear(year)
  }

  const handleStockToggle = (stockId: number) => {
    setSelectedStockIds(prev => 
      prev.includes(stockId) ? prev.filter(id => id !== stockId) : [...prev, stockId]
    )
  }

  const clearStockFilter = () => setSelectedStockIds([])

  const totalDividend = useMemo(() => {
    return filteredDividends.reduce((sum, div) => sum + div.amount, 0)
  }, [filteredDividends])

  const STOCK_COLORS = [
    '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
    '#EC4899', '#14B8A6', '#F97316', '#6366F1', '#84CC16',
    '#06B6D4', '#F43F5E', '#8B5CF6', '#22D3EE', '#A855F7'
  ]

  const getStockColor = (stockId: number) => {
    const index = stockList.findIndex(s => s.id === stockId)
    return STOCK_COLORS[index % STOCK_COLORS.length]
  }

  const ChartContent = () => (
    <>
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant={selectedYear === 'all' ? 'primary' : 'outline'}
            onClick={() => handleYearChange('all')}
          >
            전체
          </Button>
          {availableYears.map(year => (
            <Button
              key={year}
              size="sm"
              variant={selectedYear === year ? 'primary' : 'outline'}
              onClick={() => handleYearChange(year)}
            >
              {year}년
            </Button>
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

      {chartData.length === 0 ? (
        <div className="h-[300px] flex items-center justify-center text-gray-500">
          선택한 기간에 데이터가 없습니다
        </div>
      ) : (
        <div className={cn("w-full", isFullScreen ? "h-full min-h-[400px]" : "h-[300px]")}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
              <XAxis
                dataKey="date"
                stroke="#9CA3AF"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                dy={10}
                tickFormatter={(value) => {
                  if (selectedYear !== 'all' && value.includes('-')) {
                    const month = value.split('-')[1]
                    return `${parseInt(month)}월`
                  }
                  return value
                }}
              />
              <YAxis
                yAxisId="left"
                tickFormatter={(value) =>
                  new Intl.NumberFormat('ko-KR', { notation: 'compact', maximumFractionDigits: 1 }).format(value)
                }
                stroke="#9CA3AF"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                dx={-10}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                tickFormatter={(value) =>
                  new Intl.NumberFormat('ko-KR', { notation: 'compact', maximumFractionDigits: 1 }).format(value)
                }
                stroke="#9CA3AF"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                dx={10}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #E5E7EB',
                  borderRadius: '0.5rem',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                }}
                formatter={(value: number, name: string) => {
                  if (name === 'cumulative_dividend') {
                    return [formatCurrency(value, 'KRW'), '누적 배당금']
                  }
                  const stockId = parseInt(name.replace('stock_', ''))
                  const stock = stockList.find(s => s.id === stockId)
                  if (!stock) return [formatCurrency(value, 'KRW'), name]
                  return [formatCurrency(value, 'KRW'), stock.name]
                }}
              />
              {stockList.map((stock) => (
                <Bar
                  key={stock.id}
                  yAxisId="left"
                  dataKey={`stock_${stock.id}`}
                  stackId="dividend"
                  fill={getStockColor(stock.id)}
                  opacity={0.8}
                />
              ))}
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="cumulative_dividend"
                stroke="#3B82F6"
                strokeWidth={2}
                dot={{ fill: '#3B82F6', r: 3 }}
                activeDot={{ r: 5 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
    </>
  )

  if (isFullScreen) {
    return (
      <div className="fixed inset-0 z-50 bg-white flex flex-col">
        <div className="flex items-center justify-between p-6 pb-4 border-b">
          <div className="flex items-center gap-6">
            <div>
              <h3 className="text-2xl font-bold text-gray-900">배당 성장 (전체화면)</h3>
              <p className="text-gray-500">누적 배당금 추이</p>
            </div>
            <div className="flex items-center gap-6 text-sm">
              <div>
                <span className="text-gray-500">총 배당금: </span>
                <span className="font-semibold text-green-600">
                  {formatCurrency(totalDividend, 'KRW')}
                </span>
              </div>
              <div>
                <span className="text-gray-500">배당 건수: </span>
                <span className="font-semibold text-gray-900">
                  {filteredDividends.length}건
                </span>
              </div>
            </div>
          </div>
          <button
            onClick={() => setIsFullScreen(false)}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="h-6 w-6 text-gray-500" />
          </button>
        </div>
        <div className="flex-1 overflow-auto p-6">
          <ChartContent />
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <Card className="col-span-4 lg:col-span-3">
        <div className="h-[400px] flex items-center justify-center">
          <Loading />
        </div>
      </Card>
    )
  }

  return (
    <Card className="col-span-4 lg:col-span-3 h-full flex flex-col">
      <div className="space-y-4 flex-1 flex flex-col">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                배당 성장
              </h3>
              <p className="text-sm text-gray-500">
                {selectedStockIds.length > 0 
                  ? `선택된 ${selectedStockIds.length}개 종목의 누적 배당금 추이`
                  : '전체 포트폴리오 누적 배당금 추이'
                }
              </p>
            </div>
            <div className="flex items-center gap-6 text-sm">
              <div>
                <span className="text-gray-500">총 배당금: </span>
                <span className="font-semibold text-green-600">
                  {formatCurrency(totalDividend, 'KRW')}
                </span>
              </div>
              <div>
                <span className="text-gray-500">배당 건수: </span>
                <span className="font-semibold text-gray-900">
                  {filteredDividends.length}건
                </span>
              </div>
            </div>
          </div>
          <button
            onClick={() => setIsFullScreen(true)}
            className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all"
            title="크게 보기"
          >
            <Maximize2 className="h-5 w-5" />
          </button>
        </div>

        <ChartContent />
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

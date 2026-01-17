import { useState, useMemo } from 'react'
import { useDividends, useDeleteDividend } from '../../hooks/useDividends'
import { Card } from '../ui/Card'
import { Loading } from '../ui/Loading'
import { formatCurrency, formatDate, cn } from '../../lib/utils'
import { Trash2, Pencil, ChevronDown, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'
import { Button } from '../ui/Button'
import { Dividend } from '../../types'

interface DividendListProps {
  onEdit?: (dividend: Dividend) => void
}

type SortField = 'dividend_date' | 'stock.name' | 'amount' | 'tax' | 'net_amount'
type SortDirection = 'asc' | 'desc'

interface SortConfig {
  field: SortField
  direction: SortDirection
}

export function DividendList({ onEdit }: DividendListProps) {
  const [selectedYear, setSelectedYear] = useState<string>('all')
  const [selectedStockIds, setSelectedStockIds] = useState<number[]>([])
  const [showStockDropdown, setShowStockDropdown] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [sortConfig, setSortConfig] = useState<SortConfig>({ field: 'dividend_date', direction: 'desc' })
  const itemsPerPage = 20
  
  const { data: dividends, isLoading } = useDividends()
  const deleteDividend = useDeleteDividend()

  const availableYears = useMemo(() => {
    if (!dividends) return []
    const years = new Set<string>()
    dividends.forEach(d => {
      const year = d.dividend_date.substring(0, 4)
      years.add(year)
    })
    return Array.from(years).sort().reverse()
  }, [dividends])

  const availableStocks = useMemo(() => {
    if (!dividends) return []
    const stockMap = new Map()
    dividends.forEach(d => {
      if (!stockMap.has(d.stock_id)) {
        stockMap.set(d.stock_id, d.stock)
      }
    })
    return Array.from(stockMap.values())
  }, [dividends])

  const filteredDividends = useMemo(() => {
    if (!dividends) return []
    
    return dividends.filter(d => {
      if (selectedYear !== 'all') {
        const dYear = d.dividend_date.substring(0, 4)
        if (dYear !== selectedYear) return false
      }
      
      if (selectedStockIds.length > 0 && !selectedStockIds.includes(d.stock_id)) {
        return false
      }
      
      return true
    })
  }, [dividends, selectedYear, selectedStockIds])

  const sortedDividends = useMemo(() => {
    return [...filteredDividends].sort((a, b) => {
      const { field, direction } = sortConfig
      const multiplier = direction === 'asc' ? 1 : -1

      if (field === 'stock.name') {
        return multiplier * a.stock.name.localeCompare(b.stock.name)
      }
      
      if (field === 'dividend_date') {
        if (a[field] < b[field]) return -1 * multiplier
        if (a[field] > b[field]) return 1 * multiplier
        return 0
      }

      // 숫자형 필드 처리
      let valA = 0
      let valB = 0
      
      if (field === 'net_amount') {
        valA = a.amount - a.tax
        valB = b.amount - b.tax
      } else {
        valA = Number(a[field as keyof typeof a])
        valB = Number(b[field as keyof typeof b])
      }
      
      return multiplier * (valA - valB)
    })
  }, [filteredDividends, sortConfig])

  const totalPages = Math.ceil(sortedDividends.length / itemsPerPage)
  
  const paginatedDividends = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage
    const endIndex = startIndex + itemsPerPage
    return sortedDividends.slice(startIndex, endIndex)
  }, [sortedDividends, currentPage, itemsPerPage])

  const summary = useMemo(() => {
    let totalAmount = 0
    let totalTax = 0
    
    filteredDividends.forEach(d => {
      totalAmount += d.amount
      totalTax += d.tax
    })
    
    return { totalAmount, totalTax, netAmount: totalAmount - totalTax }
  }, [filteredDividends])

  const handleYearChange = (year: string) => {
    setSelectedYear(year)
    setCurrentPage(1)
  }

  const handleStockToggle = (stockId: number) => {
    setSelectedStockIds(prev =>
      prev.includes(stockId)
        ? prev.filter(id => id !== stockId)
        : [...prev, stockId]
    )
    setCurrentPage(1)
  }

  const handleSort = (field: SortField) => {
    setSortConfig(prev => ({
      field,
      direction: prev.field === field && prev.direction === 'desc' ? 'asc' : 'desc'
    }))
  }

  const handleDelete = (id: number) => {
    if (confirm('정말 이 배당 내역을 삭제하시겠습니까?')) {
      deleteDividend.mutate(id)
    }
  }

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortConfig.field !== field) return <ArrowUpDown className="ml-2 h-4 w-4 text-gray-400" />
    return sortConfig.direction === 'asc' 
      ? <ArrowUp className="ml-2 h-4 w-4 text-blue-600" />
      : <ArrowDown className="ml-2 h-4 w-4 text-blue-600" />
  }

  const SortHeader = ({ field, label, align = 'left' }: { field: SortField, label: string, align?: 'left' | 'right' }) => (
    <th 
      className={cn(
        "px-6 py-3 font-medium cursor-pointer hover:bg-gray-100 transition-colors group select-none",
        align === 'right' ? "text-right" : "text-left"
      )}
      onClick={() => handleSort(field)}
    >
      <div className={cn("flex items-center", align === 'right' ? "justify-end" : "justify-start")}>
        {label}
        <SortIcon field={field} />
      </div>
    </th>
  )

  if (isLoading) return <Card className="p-12"><Loading /></Card>

  return (
    <Card noPadding className="overflow-hidden">
      <div className="p-4 border-b border-gray-200 bg-gray-50/50 space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex gap-2">
            <Button
              variant={selectedYear === 'all' ? 'primary' : 'outline'}
              size="sm"
              onClick={() => handleYearChange('all')}
            >
              전체
            </Button>
            {availableYears.map(year => (
              <Button
                key={year}
                variant={selectedYear === year ? 'primary' : 'outline'}
                size="sm"
                onClick={() => handleYearChange(year)}
              >
                {year}년
              </Button>
            ))}
          </div>

          <div className="relative">
            <button
              onClick={() => setShowStockDropdown(!showStockDropdown)}
              className="flex items-center gap-2 px-3 py-1.5 text-sm border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
            >
              <span>{selectedStockIds.length > 0 ? `${selectedStockIds.length}개 종목` : '전체 종목'}</span>
              <ChevronDown className="h-4 w-4" />
            </button>
            
            {showStockDropdown && availableStocks.length > 0 && (
              <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-200 rounded-md shadow-lg z-10 max-h-64 overflow-y-auto">
                <div className="p-2">
                  <button
                    onClick={() => setSelectedStockIds([])}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 rounded-md"
                  >
                    전체 선택 해제
                  </button>
                  {availableStocks.map(stock => (
                    <label
                      key={stock.id}
                      className="flex items-center gap-2 px-3 py-2 hover:bg-gray-50 rounded-md cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={selectedStockIds.includes(stock.id)}
                        onChange={() => handleStockToggle(stock.id)}
                        className="rounded border-gray-300"
                      />
                      <span className="text-sm">{stock.name} ({stock.ticker})</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
        
        <div className="flex items-center justify-between text-sm text-gray-500">
          <div>총 {filteredDividends.length}건의 배당</div>
          <div className="flex gap-4">
            <div className="flex items-center gap-1">
              <span className="inline-block w-2 h-2 rounded-full bg-green-500"></span>
              <span>세전: {formatCurrency(summary.totalAmount, 'KRW')}</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="inline-block w-2 h-2 rounded-full bg-blue-500"></span>
              <span>수령액(세후): {formatCurrency(summary.netAmount, 'KRW')}</span>
            </div>
          </div>
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-gray-500 border-b border-gray-200">
            <tr>
              <SortHeader field="dividend_date" label="날짜" />
              <SortHeader field="stock.name" label="종목" />
              <SortHeader field="net_amount" label="배당금" align="right" />
              <th className="px-6 py-3 font-medium text-right">작업</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {paginatedDividends.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                  배당 내역이 없습니다.
                </td>
              </tr>
            ) : (
              paginatedDividends.map((d) => (
                <tr key={d.id} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-6 py-4 text-gray-500 whitespace-nowrap">
                    {formatDate(d.dividend_date)}
                  </td>
                  <td className="px-6 py-4">
                    <div className="font-medium text-gray-900">{d.stock.name}</div>
                    <div className="text-xs text-gray-500">{d.stock.ticker}</div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="font-medium text-blue-600">
                      {formatCurrency(d.amount - d.tax, d.currency)}
                    </div>
                    <div className="text-xs text-gray-400">
                      세전: {formatCurrency(d.amount, d.currency)} (세금: {formatCurrency(d.tax, d.currency)})
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-gray-400 hover:text-blue-600"
                        onClick={() => onEdit?.(d)}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-gray-400 hover:text-red-600"
                        onClick={() => handleDelete(d.id)}
                        isLoading={deleteDividend.isPending && deleteDividend.variables === d.id}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50/50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              {filteredDividends.length}건 중 {((currentPage - 1) * itemsPerPage) + 1}-{Math.min(currentPage * itemsPerPage, filteredDividends.length)}건 표시
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
              >
                이전
              </Button>
              <div className="flex items-center gap-1">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => {
                  if (
                    page === 1 ||
                    page === totalPages ||
                    (page >= currentPage - 1 && page <= currentPage + 1)
                  ) {
                    return (
                      <Button
                        key={page}
                        variant={currentPage === page ? 'primary' : 'outline'}
                        size="sm"
                        onClick={() => setCurrentPage(page)}
                      >
                        {page}
                      </Button>
                    )
                  } else if (page === currentPage - 2 || page === currentPage + 2) {
                    return <span key={page} className="px-2 text-gray-400">...</span>
                  }
                  return null
                })}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
              >
                다음
              </Button>
            </div>
          </div>
        </div>
      )}
    </Card>
  )
}

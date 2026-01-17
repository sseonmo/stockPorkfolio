import { useState, useMemo } from 'react'
import { useTransactions, useDeleteTransaction } from '../../hooks/useTransactions'
import { Card } from '../ui/Card'
import { Loading } from '../ui/Loading'
import { formatCurrency, formatDate, cn } from '../../lib/utils'
import { Trash2, Pencil, ChevronDown, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'
import { Button } from '../ui/Button'
import { Transaction } from '../../types'

interface TransactionListProps {
  onEdit?: (transaction: Transaction) => void
}

type SortField = 'transaction_date' | 'transaction_type' | 'stock.name' | 'quantity' | 'price' | 'total_amount_krw'
type SortDirection = 'asc' | 'desc'

interface SortConfig {
  field: SortField
  direction: SortDirection
}

export function TransactionList({ onEdit }: TransactionListProps) {
  const [selectedYear, setSelectedYear] = useState<string>('all')
  const [selectedStockIds, setSelectedStockIds] = useState<number[]>([])
  const [showStockDropdown, setShowStockDropdown] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [sortConfig, setSortConfig] = useState<SortConfig>({ field: 'transaction_date', direction: 'desc' })
  const itemsPerPage = 20
  
  const { data: transactions, isLoading } = useTransactions()
  const deleteTransaction = useDeleteTransaction()

  const availableYears = useMemo(() => {
    if (!transactions) return []
    const years = new Set<string>()
    transactions.forEach(tx => {
      const year = tx.transaction_date.substring(0, 4)
      years.add(year)
    })
    return Array.from(years).sort().reverse()
  }, [transactions])

  const availableStocks = useMemo(() => {
    if (!transactions) return []
    const stockMap = new Map()
    transactions.forEach(tx => {
      if (!stockMap.has(tx.stock_id)) {
        stockMap.set(tx.stock_id, tx.stock)
      }
    })
    return Array.from(stockMap.values())
  }, [transactions])

  const filteredTransactions = useMemo(() => {
    if (!transactions) return []
    
    return transactions.filter(tx => {
      if (selectedYear !== 'all') {
        const txYear = tx.transaction_date.substring(0, 4)
        if (txYear !== selectedYear) return false
      }
      
      if (selectedStockIds.length > 0 && !selectedStockIds.includes(tx.stock_id)) {
        return false
      }
      
      return true
    })
  }, [transactions, selectedYear, selectedStockIds])

  const handleSort = (field: SortField) => {
    setSortConfig(prev => ({
      field,
      direction: prev.field === field && prev.direction === 'desc' ? 'asc' : 'desc'
    }))
  }

  const sortedTransactions = useMemo(() => {
    return [...filteredTransactions].sort((a, b) => {
      const { field, direction } = sortConfig
      const multiplier = direction === 'asc' ? 1 : -1

      if (field === 'stock.name') {
        return multiplier * a.stock.name.localeCompare(b.stock.name)
      }
      
      if (field === 'transaction_date') {
        if (a[field] < b[field]) return -1 * multiplier
        if (a[field] > b[field]) return 1 * multiplier
        return 0
      }
      
      if (field === 'transaction_type') {
        return multiplier * a.transaction_type.localeCompare(b.transaction_type)
      }

      // 숫자형 필드 처리
      const valA = Number(field === 'total_amount_krw' ? a.total_amount_krw : a[field as keyof typeof a])
      const valB = Number(field === 'total_amount_krw' ? b.total_amount_krw : b[field as keyof typeof b])
      return multiplier * (valA - valB)
    })
  }, [filteredTransactions, sortConfig])

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

  const summary = useMemo(() => {
    let totalBuy = 0
    let totalSell = 0
    
    filteredTransactions.forEach(tx => {
      // total_amount_krw가 있으면 사용, 없으면 quantity * price
      const amount = tx.total_amount_krw || (tx.quantity * tx.price)
      
      if (tx.transaction_type === 'BUY') {
        totalBuy += amount
      } else if (tx.transaction_type === 'SELL') {
        totalSell += amount
      }
    })
    
    return { totalBuy, totalSell }
  }, [filteredTransactions])

  const totalPages = Math.ceil(sortedTransactions.length / itemsPerPage)
  
  const paginatedTransactions = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage
    const endIndex = startIndex + itemsPerPage
    return sortedTransactions.slice(startIndex, endIndex)
  }, [sortedTransactions, currentPage, itemsPerPage])

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

  const handleDelete = (id: number) => {
    if (confirm('정말 이 거래 내역을 삭제하시겠습니까?')) {
      deleteTransaction.mutate(id)
    }
  }

  if (isLoading) return <Card className="p-12"><Loading /></Card>

  if (!transactions || transactions.length === 0) {
    return (
      <Card className="p-8 text-center text-gray-500">
        거래 내역이 없습니다. 거래를 추가해보세요!
      </Card>
    )
  }

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
          <div>총 {filteredTransactions.length}건의 거래</div>
          <div className="flex gap-4">
            <div className="flex items-center gap-1">
              <span className="inline-block w-2 h-2 rounded-full bg-red-500"></span>
              <span>매수: {formatCurrency(summary.totalBuy, 'KRW')}</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="inline-block w-2 h-2 rounded-full bg-blue-500"></span>
              <span>매도: {formatCurrency(summary.totalSell, 'KRW')}</span>
            </div>
          </div>
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-gray-500 border-b border-gray-200">
            <tr>
              <SortHeader field="transaction_date" label="날짜" />
              <SortHeader field="transaction_type" label="유형" />
              <SortHeader field="stock.name" label="종목" />
              <SortHeader field="quantity" label="수량" align="right" />
              <SortHeader field="price" label="가격" align="right" />
              <SortHeader field="total_amount_krw" label="총액" align="right" />
              <th className="px-6 py-3 font-medium text-right">작업</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {paginatedTransactions.map((tx) => (
              <tr key={tx.id} className="hover:bg-gray-50/50 transition-colors">
                <td className="px-6 py-4 text-gray-500 whitespace-nowrap">
                  {formatDate(tx.transaction_date)}
                </td>
                <td className="px-6 py-4">
                  <span className={cn(
                    "inline-flex items-center rounded-full px-2 py-1 text-xs font-medium",
                    tx.transaction_type === 'BUY' ? "bg-blue-50 text-blue-700" :
                      tx.transaction_type === 'SELL' ? "bg-red-50 text-red-700" :
                        "bg-green-50 text-green-700"
                  )}>
                    {tx.transaction_type}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="font-medium text-gray-900">{tx.stock.name}</div>
                  <div className="text-xs text-gray-500">{tx.stock.ticker}</div>
                </td>
                <td className="px-6 py-4 text-right">
                  {tx.quantity}
                </td>
                <td className="px-6 py-4 text-right">
                  {formatCurrency(tx.price, tx.stock.currency)}
                </td>
                <td className="px-6 py-4 text-right font-medium text-gray-900">
                  {formatCurrency(tx.total_amount_krw, 'KRW')}
                </td>
                <td className="px-6 py-4 text-right">
                  <div className="flex justify-end gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-gray-400 hover:text-blue-600"
                      onClick={() => onEdit?.(tx)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-gray-400 hover:text-red-600"
                      onClick={() => handleDelete(tx.id)}
                      isLoading={deleteTransaction.isPending && deleteTransaction.variables === tx.id}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50/50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              {filteredTransactions.length}건 중 {((currentPage - 1) * itemsPerPage) + 1}-{Math.min(currentPage * itemsPerPage, filteredTransactions.length)}건 표시
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

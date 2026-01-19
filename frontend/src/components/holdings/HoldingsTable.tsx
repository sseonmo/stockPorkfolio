import { useState, useMemo } from 'react'
import { useHoldings } from '../../hooks/useHoldings'
import { MarketType, Holding } from '../../types'
import { Card } from '../ui/Card'
import { Button } from '../ui/Button'
import { formatCurrency, formatPercent, cn } from '../../lib/utils'
import { ArrowUpRight, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'
import { TransactionHistoryModal } from './TransactionHistoryModal'

interface HoldingsTableProps {
  market: MarketType | 'ALL'
}

type SortField = 'stock.name' | 'stock.current_price' | 'average_cost' | 'quantity' | 'current_value_krw' | 'unrealized_gain' | 'weight_percent' | 'total_invested'
type SortDirection = 'asc' | 'desc'

interface SortConfig {
  field: SortField
  direction: SortDirection
}

export function HoldingsTable({ market }: HoldingsTableProps) {
  const queryMarket = market === 'ALL' ? undefined : market
  const { data: holdings } = useHoldings(queryMarket)
  const [currentPage, setCurrentPage] = useState(1)
  const [sortConfig, setSortConfig] = useState<SortConfig>({ field: 'current_value_krw', direction: 'desc' })
  const [selectedHolding, setSelectedHolding] = useState<Holding | null>(null)
  const itemsPerPage = 20

  const handleSort = (field: SortField) => {
    setSortConfig(prev => ({
      field,
      direction: prev.field === field && prev.direction === 'desc' ? 'asc' : 'desc'
    }))
  }

  const sortedHoldings = useMemo(() => {
    if (!holdings) return []
    return [...holdings].sort((a, b) => {
      const { field, direction } = sortConfig
      const multiplier = direction === 'asc' ? 1 : -1

      if (field === 'stock.name') {
        return multiplier * a.stock.name.localeCompare(b.stock.name)
      }
      
      if (field === 'stock.current_price') {
        return multiplier * ((a.stock.current_price || 0) - (b.stock.current_price || 0))
      }

      // 숫자형 필드 처리
      const valA = Number(a[field as keyof typeof a])
      const valB = Number(b[field as keyof typeof b])
      return multiplier * (valA - valB)
    })
  }, [holdings, sortConfig])

  const totalPages = Math.ceil((sortedHoldings.length || 0) / itemsPerPage)
  
  const paginatedHoldings = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage
    const endIndex = startIndex + itemsPerPage
    return sortedHoldings.slice(startIndex, endIndex)
  }, [sortedHoldings, currentPage, itemsPerPage])

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortConfig.field !== field) return <ArrowUpDown className="ml-1 h-3 w-3 text-gray-300" />
    return sortConfig.direction === 'asc' 
      ? <ArrowUp className="ml-1 h-3 w-3 text-blue-600" />
      : <ArrowDown className="ml-1 h-3 w-3 text-blue-600" />
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
              <SortHeader field="stock.name" label="종목" />
              <SortHeader field="stock.current_price" label="현재가" align="right" />
              <SortHeader field="average_cost" label="평단가" align="right" />
              <SortHeader field="quantity" label="보유수량" align="right" />
              <SortHeader field="total_invested" label="매수금액" align="right" />
              <SortHeader field="current_value_krw" label="평가금액" align="right" />
              <SortHeader field="unrealized_gain" label="손익" align="right" />
              <SortHeader field="weight_percent" label="비중" align="right" />
            </tr>
          </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
            {paginatedHoldings.map((holding) => {
              const isGain = holding.unrealized_gain >= 0
              return (
                <tr 
                  key={holding.id} 
                  className="hover:bg-gray-50/50 transition-colors cursor-pointer"
                  onClick={() => setSelectedHolding(holding)}
                >
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
                  <td className="px-6 py-4 text-right text-gray-500">
                    {formatCurrency(holding.total_invested, 'KRW')}
                  </td>
                  <td className="px-6 py-4 text-right font-medium text-gray-900">
                    {formatCurrency(holding.current_value_krw, 'KRW')}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className={cn("flex items-center justify-end font-medium", isGain ? "text-red-600" : "text-blue-600")}>
                      {isGain ? <ArrowUp className="w-3 h-3 mr-1" /> : <ArrowDown className="w-3 h-3 mr-1" />}
                      {formatPercent(holding.unrealized_gain_percent)}
                    </div>
                    <div className={cn("text-xs", isGain ? "text-red-600/70" : "text-blue-600/70")}>
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

      {selectedHolding && (
        <TransactionHistoryModal
          isOpen={!!selectedHolding}
          onClose={() => setSelectedHolding(null)}
          holding={selectedHolding}
        />
      )}

      {totalPages > 1 && (
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50/50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              {holdings.length}건 중 {((currentPage - 1) * itemsPerPage) + 1}-{Math.min(currentPage * itemsPerPage, holdings.length)}건 표시
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

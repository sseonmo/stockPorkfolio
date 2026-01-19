import { useState } from 'react'
import { Card } from '../ui/Card'
import { Button } from '../ui/Button'
import { X, Loader2, ArrowUp, ArrowDown } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { getTransactionsByStock } from '../../api/transactions'
import { formatCurrency, formatPercent, cn } from '../../lib/utils'
import { Holding } from '../../types'

interface TransactionHistoryModalProps {
    isOpen: boolean
    onClose: () => void
    holding: Holding
}

export function TransactionHistoryModal({ isOpen, onClose, holding }: TransactionHistoryModalProps) {
    const [selectedYear, setSelectedYear] = useState<number | null>(null)
    const [currentPage, setCurrentPage] = useState(1)
    const itemsPerPage = 10

    const { data, isLoading, isError, error, refetch } = useQuery({
        queryKey: ['transactions-by-stock', holding.stock.id, selectedYear, currentPage],
        queryFn: () => getTransactionsByStock(holding.stock.id, {
            year: selectedYear ?? undefined,
            page: currentPage,
            size: itemsPerPage,
        }),
        enabled: isOpen,
    })

    const handleYearChange = (year: number | null) => {
        setSelectedYear(year)
        setCurrentPage(1)
    }

    const renderPageNumbers = () => {
        if (!data) return null
        const totalPages = data.total_pages
        const current = data.current_page
        
        let start = Math.max(1, current - 2)
        const end = Math.min(totalPages, start + 4)
        
        if (end - start < 4) {
            start = Math.max(1, end - 4)
        }

        const pages = []
        for (let i = start; i <= end; i++) {
            pages.push(
                <Button
                    key={i}
                    variant={i === current ? "primary" : "outline"}
                    size="sm"
                    className="w-8 h-8 p-0"
                    onClick={() => setCurrentPage(i)}
                >
                    {i}
                </Button>
            )
        }
        return pages
    }

    if (!isOpen) return null

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <Card className="w-full max-w-4xl h-[85vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200 shadow-2xl">
                <div className="flex items-center justify-between border-b p-4 bg-white z-10">
                    <div className="flex items-baseline gap-2">
                        <h2 className="text-xl font-bold">{holding.stock.name}</h2>
                        <span className="text-sm text-gray-500 font-mono">{holding.stock.ticker}</span>
                    </div>
                    <button onClick={onClose} className="rounded-full p-1 hover:bg-gray-100 transition-colors">
                        <X className="h-5 w-5" />
                    </button>
                </div>

                <div className="flex-1 overflow-hidden flex flex-col relative">
                    {isError && (
                        <div className="absolute inset-0 z-20 flex items-center justify-center bg-white/80">
                            <div className="text-center p-6">
                                <p className="text-red-600 font-medium mb-2">데이터를 불러오지 못했습니다.</p>
                                <p className="text-sm text-gray-500 mb-4 break-words max-w-sm mx-auto">
                                    {(error as any)?.response?.data?.detail || (error as Error)?.message}
                                </p>
                                <Button size="sm" onClick={() => refetch()}>
                                    다시 시도
                                </Button>
                            </div>
                        </div>
                    )}

                    {(isLoading) && !isError && (
                        <div className="absolute inset-0 z-20 flex items-center justify-center bg-white/50 backdrop-blur-[1px]">
                            <div className="flex flex-col items-center gap-2 bg-white p-4 rounded-lg shadow-lg border">
                                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                                <span className="text-sm font-medium text-gray-600">거래내역 조회 중...</span>
                            </div>
                        </div>
                    )}

                    <div className="flex-1 overflow-auto p-6 space-y-6">
                        <div className="grid grid-cols-3 gap-4 bg-gray-50 p-5 rounded-xl border border-gray-100">
                            <div className="space-y-1">
                                <span className="text-sm font-medium text-gray-500">보유수량</span>
                                <div className="text-lg font-semibold text-gray-900">
                                    {holding.quantity.toLocaleString()}주
                                </div>
                            </div>
                            <div className="space-y-1 text-center">
                                <span className="text-sm font-medium text-gray-500">현재가</span>
                                <div className="text-lg font-semibold font-mono text-gray-900">
                                    {formatCurrency(holding.stock.current_price || 0, holding.stock.currency)}
                                </div>
                            </div>
                            <div className="space-y-1 text-right">
                                <span className="text-sm font-medium text-gray-500">평균단가</span>
                                <div className="text-lg font-semibold font-mono text-gray-900">
                                    {formatCurrency(holding.average_cost, holding.stock.currency)}
                                </div>
                            </div>
                            <div className="space-y-1">
                                <span className="text-sm font-medium text-gray-500">평가금액</span>
                                <div className="text-lg font-bold font-mono text-gray-900">
                                    {formatCurrency(holding.current_value_krw, 'KRW')}
                                </div>
                            </div>
                            <div className="space-y-1 text-center">
                                <span className="text-sm font-medium text-gray-500">평가손익</span>
                                <div className={cn(
                                    "text-lg font-bold font-mono",
                                    holding.unrealized_gain >= 0 ? "text-red-600" : "text-blue-600"
                                )}>
                                    {formatCurrency(holding.unrealized_gain, 'KRW')}
                                </div>
                            </div>
                            <div className="space-y-1 text-right">
                                <span className="text-sm font-medium text-gray-500">수익률</span>
                                <div className={cn(
                                    "text-lg font-bold font-mono flex items-center justify-end gap-1",
                                    holding.unrealized_gain_percent >= 0 ? "text-red-600" : "text-blue-600"
                                )}>
                                    {holding.unrealized_gain_percent >= 0 ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />}
                                    {formatPercent(holding.unrealized_gain_percent)}
                                </div>
                            </div>
                        </div>

                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <h3 className="font-bold text-gray-900">거래내역</h3>
                            </div>

                            {data && (
                                <div className="flex flex-wrap gap-2">
                                    <Button
                                        size="sm"
                                        variant={selectedYear === null ? "primary" : "outline"}
                                        onClick={() => handleYearChange(null)}
                                        className="text-xs h-8"
                                    >
                                        전체
                                    </Button>
                                    {data.available_years.map((year) => (
                                        <Button
                                            key={year}
                                            size="sm"
                                            variant={selectedYear === year ? "primary" : "outline"}
                                            onClick={() => handleYearChange(year)}
                                            className="text-xs h-8"
                                        >
                                            {year}
                                        </Button>
                                    ))}
                                </div>
                            )}

                            <div className="rounded-xl border shadow-sm overflow-hidden bg-white">
                                <table className="w-full text-sm">
                                    <thead className="bg-gray-50/80 border-b">
                                        <tr>
                                            <th className="px-4 py-3 text-left font-medium text-gray-500">거래일자</th>
                                            <th className="px-4 py-3 text-center font-medium text-gray-500">구분</th>
                                            <th className="px-4 py-3 text-right font-medium text-gray-500">수량</th>
                                            <th className="px-4 py-3 text-right font-medium text-gray-500">단가</th>
                                            <th className="px-4 py-3 text-right font-medium text-gray-500">금액</th>
                                            <th className="px-4 py-3 text-right font-medium text-gray-500">실현손익</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-100">
                                        {!data || data.content.length === 0 ? (
                                            <tr>
                                                <td colSpan={6} className="p-12 text-center text-gray-500">
                                                    거래내역이 없습니다.
                                                </td>
                                            </tr>
                                        ) : (
                                            data.content.map((tx) => (
                                                <tr key={tx.id} className="hover:bg-gray-50/50 transition-colors">
                                                    <td className="px-4 py-3 text-gray-900 font-mono">
                                                        {tx.transaction_date}
                                                    </td>
                                                    <td className="px-4 py-3 text-center font-medium">
                                                        <span className={cn(
                                                            tx.transaction_type === 'BUY' ? "text-red-600 bg-red-50" : 
                                                            tx.transaction_type === 'SELL' ? "text-blue-600 bg-blue-50" : "text-gray-600 bg-gray-50",
                                                            "px-2 py-1 rounded text-xs"
                                                        )}>
                                                            {tx.transaction_type === 'BUY' ? '매수' : 
                                                             tx.transaction_type === 'SELL' ? '매도' : tx.transaction_type}
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-3 text-right text-gray-900">
                                                        {tx.quantity}주
                                                    </td>
                                                    <td className="px-4 py-3 text-right font-mono text-gray-600">
                                                        {formatCurrency(tx.price, holding.stock.currency)}
                                                    </td>
                                                    <td className="px-4 py-3 text-right font-mono font-medium text-gray-900">
                                                        {formatCurrency(tx.total_amount, holding.stock.currency)}
                                                    </td>
                                                    {tx.transaction_type === 'SELL' && tx.realized_gain !== undefined && tx.realized_gain_percent !== undefined ? (
                                                        <td className="px-4 py-3 text-right">
                                                            <div className={cn(
                                                                "flex items-center justify-end gap-1 font-medium",
                                                                tx.realized_gain >= 0 ? "text-red-600" : "text-blue-600"
                                                            )}>
                                                                {tx.realized_gain >= 0 ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
                                                                {formatCurrency(tx.realized_gain, 'KRW')}
                                                            </div>
                                                            <div className={cn(
                                                                "text-xs",
                                                                tx.realized_gain_percent >= 0 ? "text-red-600/70" : "text-blue-600/70"
                                                            )}>
                                                                {formatPercent(tx.realized_gain_percent)}
                                                            </div>
                                                        </td>
                                                    ) : (
                                                        <td className="px-4 py-3 text-right text-gray-400">-</td>
                                                    )}
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

                {data && data.total_pages > 0 && (
                    <div className="p-4 border-t bg-gray-50 flex items-center justify-between z-10">
                        <div className="text-sm text-gray-500">
                            총 {data.total_elements}건 ({data.current_page}/{data.total_pages} 페이지)
                        </div>
                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                                disabled={currentPage === 1 || isLoading}
                            >
                                &lt;
                            </Button>
                            {renderPageNumbers()}
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setCurrentPage(prev => Math.min(data.total_pages, prev + 1))}
                                disabled={currentPage === data.total_pages || isLoading}
                            >
                                &gt;
                            </Button>
                        </div>
                    </div>
                )}
            </Card>
        </div>
    )
}

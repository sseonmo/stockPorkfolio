import { useState } from 'react'
import { Card } from '../ui/Card'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { X, Loader2, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import * as dashboardApi from '../../api/dashboard'
import { getHoldings } from '../../api/holdings'
import { formatCurrency, formatPercent, cn } from '../../lib/utils'

interface DailyPnlModalProps {
    isOpen: boolean
    onClose: () => void
}

type SortField = 'date' | 'total_value_krw' | 'daily_pnl' | 'roi'
type SortDirection = 'asc' | 'desc'

export function DailyPnlModal({ isOpen, onClose }: DailyPnlModalProps) {
    const [startDate, setStartDate] = useState(
        new Date(new Date().setDate(new Date().getDate() - 7)).toISOString().split('T')[0]
    )
    const [endDate, setEndDate] = useState(
        new Date().toISOString().split('T')[0]
    )
    const [selectedStockIds, setSelectedStockIds] = useState<number[]>([])
    const [currentPage, setCurrentPage] = useState(1)
    const [sortField, setSortField] = useState<SortField>('date')
    const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
    const [activeDateRange, setActiveDateRange] = useState<number>(7)
    const itemsPerPage = 20
    const queryClient = useQueryClient()

    // Fetch stocks for filter
    const { data: holdings } = useQuery({
        queryKey: ['holdings'],
        queryFn: () => getHoldings()
    })

    const skip = (currentPage - 1) * itemsPerPage

    const { data, isLoading, isFetching, isError, error } = useQuery({
        queryKey: ['daily-pnl-history', startDate, endDate, selectedStockIds, skip, itemsPerPage],
        queryFn: () => dashboardApi.getDailyPnlHistory(
            startDate, 
            endDate, 
            selectedStockIds.length > 0 ? selectedStockIds : undefined,
            skip,
            itemsPerPage
        ),
        enabled: isOpen,
        retry: 1,
    })

    const totalPages = Math.ceil((data?.total_count || 0) / itemsPerPage)
    const paginatedData = data?.data || []

    const toggleStock = (id: number) => {
        if (id === -1) {
            // 전체 선택 (초기화)
            setSelectedStockIds([])
        } else {
            if (selectedStockIds.includes(id)) {
                setSelectedStockIds(selectedStockIds.filter(s => s !== id))
            } else {
                setSelectedStockIds([...selectedStockIds, id])
            }
        }
        setCurrentPage(1)
    }

    const setDateRange = (days: number) => {
        const end = new Date()
        const start = new Date()
        if (days === 0) {
            start.setDate(end.getDate() - 1)
        } else {
            start.setDate(end.getDate() - days)
        }
        setEndDate(end.toISOString().split('T')[0])
        setStartDate(start.toISOString().split('T')[0])
        setActiveDateRange(days)
        setCurrentPage(1)
    }

    const handleSort = (field: SortField) => {
        if (sortField === field) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
        } else {
            setSortField(field)
            setSortDirection(field === 'date' ? 'desc' : 'asc')
        }
    }

    const sortedData = [...(paginatedData || [])].sort((a, b) => {
        let aVal: any = a[sortField]
        let bVal: any = b[sortField]
        
        if (sortField === 'date') {
            aVal = new Date(aVal).getTime()
            bVal = new Date(bVal).getTime()
        }
        
        if (sortDirection === 'asc') {
            return aVal > bVal ? 1 : -1
        } else {
            return aVal < bVal ? 1 : -1
        }
    })

    const SortIcon = ({ field }: { field: SortField }) => {
        if (sortField !== field) return <ArrowUpDown className="h-4 w-4 opacity-30" />
        return sortDirection === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />
    }

    if (!isOpen) return null

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <Card className="w-full max-w-7xl h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200 shadow-2xl">
                <div className="flex items-center justify-between border-b p-4 bg-white z-10">
                    <h2 className="text-xl font-bold">일일 손익 상세</h2>
                    <button onClick={onClose} className="rounded-full p-1 hover:bg-gray-100">
                        <X className="h-5 w-5" />
                    </button>
                </div>

                <div className="flex-1 overflow-hidden flex flex-col relative">
                    {/* Error Overlay */}
                    {isError && (
                        <div className="absolute inset-0 z-20 flex items-center justify-center bg-white/80">
                            <div className="text-center p-6">
                                <p className="text-red-600 font-medium mb-2">데이터를 불러오지 못했습니다.</p>
                                <p className="text-sm text-gray-500 mb-4 break-words max-w-sm mx-auto">{(error as any)?.response?.data?.detail || (error as Error)?.message}</p>
                                <Button size="sm" onClick={() => queryClient.invalidateQueries({ queryKey: ['daily-pnl-history'] })}>
                                    다시 시도
                                </Button>
                            </div>
                        </div>
                    )}

                    {/* Loading Overlay */}
                    {(isLoading || isFetching) && !isError && (
                        <div className="absolute inset-0 z-20 flex items-center justify-center bg-white/50 backdrop-blur-[1px]">
                            <div className="flex flex-col items-center gap-2 bg-white p-4 rounded-lg shadow-lg border">
                                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                                <span className="text-sm font-medium text-gray-600">데이터 조회 중...</span>
                            </div>
                        </div>
                    )}

                    <div className="flex-1 overflow-auto p-6 space-y-6">
                        {/* Filters */}
                        <div className="grid gap-6 md:grid-cols-2">
                            <div className="flex flex-col gap-3">
                                <label className="text-sm font-medium text-gray-700">조회 기간</label>
                                <div className="flex gap-2">
                                    <Button 
                                        size="sm" 
                                        variant={activeDateRange === 0 ? "primary" : "outline"} 
                                        onClick={() => setDateRange(0)}
                                    >
                                        오늘
                                    </Button>
                                    <Button 
                                        size="sm" 
                                        variant={activeDateRange === 7 ? "primary" : "outline"} 
                                        onClick={() => setDateRange(7)}
                                    >
                                        1주일
                                    </Button>
                                    <Button 
                                        size="sm" 
                                        variant={activeDateRange === 30 ? "primary" : "outline"} 
                                        onClick={() => setDateRange(30)}
                                    >
                                        1개월
                                    </Button>
                                    <Button 
                                        size="sm" 
                                        variant={activeDateRange === 365 ? "primary" : "outline"} 
                                        onClick={() => setDateRange(365)}
                                    >
                                        1년
                                    </Button>
                                </div>
                                <div className="flex gap-2 items-center">
                                    <Input
                                        type="date"
                                        value={startDate}
                                        onChange={e => {
                                            setStartDate(e.target.value)
                                            setActiveDateRange(-1)
                                            setCurrentPage(1)
                                        }}
                                        className="w-40"
                                    />
                                    <span className="text-gray-400">~</span>
                                    <Input
                                        type="date"
                                        value={endDate}
                                        onChange={e => {
                                            setEndDate(e.target.value)
                                            setActiveDateRange(-1)
                                            setCurrentPage(1)
                                        }}
                                        className="w-40"
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="text-sm font-medium text-gray-700 block mb-2">종목 필터</label>
                                <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto border p-3 rounded-lg bg-gray-50/50">
                                    <button
                                        onClick={() => toggleStock(-1)}
                                        className={cn(
                                            "text-xs px-3 py-1.5 rounded-full border transition-all font-medium",
                                            selectedStockIds.length === 0
                                                ? "bg-blue-600 border-blue-600 text-white shadow-sm"
                                                : "bg-white border-gray-200 text-gray-600 hover:border-gray-300 hover:bg-gray-50"
                                        )}
                                    >
                                        전체
                                    </button>
                                     {(holdings || []).map(h => (
                                        <button
                                            key={h.stock.id}
                                            onClick={() => toggleStock(h.stock.id)}
                                            className={cn(
                                                "text-xs px-3 py-1.5 rounded-full border transition-all",
                                                selectedStockIds.includes(h.stock.id)
                                                    ? "bg-blue-100 border-blue-500 text-blue-700 font-medium"
                                                    : "bg-white border-gray-200 text-gray-600 hover:border-gray-300 hover:bg-gray-50"
                                            )}
                                        >
                                            {h.stock.name}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Summary */}
                        {data && (
                            <div className="grid grid-cols-2 gap-6 bg-gray-50 p-6 rounded-xl border border-gray-100">
                                <div>
                                    <span className="text-sm font-medium text-gray-500">기간 총 수익금</span>
                                    <div className={cn("text-2xl font-bold mt-1", data.total_pnl >= 0 ? "text-red-600" : "text-blue-600")}>
                                        {formatCurrency(data.total_pnl, "KRW")}
                                    </div>
                                </div>
                                <div>
                                    <span className="text-sm font-medium text-gray-500">기간 수익률 (합산)</span>
                                    <div className={cn("text-2xl font-bold mt-1", data.total_roi_percent >= 0 ? "text-red-600" : "text-blue-600")}>
                                        {formatPercent(data.total_roi_percent)}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Table */}
                        <div className="rounded-xl border shadow-sm overflow-hidden bg-white">
                            <table className="w-full text-sm">
                                <thead className="bg-gray-50/80 border-b">
                                    <tr>
                                        <th 
                                            className="px-6 py-4 text-left font-medium text-gray-500 cursor-pointer hover:bg-gray-100 transition-colors select-none"
                                            onClick={() => handleSort('date')}
                                        >
                                            <div className="flex items-center gap-2">
                                                날짜
                                                <SortIcon field="date" />
                                            </div>
                                        </th>
                                        <th 
                                            className="px-6 py-4 text-right font-medium text-gray-500 cursor-pointer hover:bg-gray-100 transition-colors select-none"
                                            onClick={() => handleSort('total_value_krw')}
                                        >
                                            <div className="flex items-center justify-end gap-2">
                                                총 자산
                                                <SortIcon field="total_value_krw" />
                                            </div>
                                        </th>
                                        <th 
                                            className="px-6 py-4 text-right font-medium text-gray-500 cursor-pointer hover:bg-gray-100 transition-colors select-none"
                                            onClick={() => handleSort('daily_pnl')}
                                        >
                                            <div className="flex items-center justify-end gap-2">
                                                일일 손익
                                                <SortIcon field="daily_pnl" />
                                            </div>
                                        </th>
                                        <th 
                                            className="px-6 py-4 text-right font-medium text-gray-500 cursor-pointer hover:bg-gray-100 transition-colors select-none"
                                            onClick={() => handleSort('roi')}
                                        >
                                            <div className="flex items-center justify-end gap-2">
                                                수익률
                                                <SortIcon field="roi" />
                                            </div>
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                    {!data || data.data.length === 0 ? (
                                        <tr><td colSpan={4} className="p-12 text-center text-gray-500">데이터가 없습니다.</td></tr>
                                    ) : (
                                        sortedData.map((row, i) => (
                                            <tr key={i} className="hover:bg-gray-50/50 transition-colors">
                                                <td className="px-6 py-4 text-gray-900">{row.date}</td>
                                                <td className="px-6 py-4 text-right font-mono text-gray-600">
                                                    {row.total_value_krw ? formatCurrency(row.total_value_krw, "KRW") : '-'}
                                                </td>
                                                <td className={cn("px-6 py-4 text-right font-mono font-medium", row.daily_pnl >= 0 ? "text-red-600" : "text-blue-600")}>
                                                    {formatCurrency(row.daily_pnl, "KRW")}
                                                </td>
                                                <td className={cn("px-6 py-4 text-right font-mono font-medium", row.roi >= 0 ? "text-red-600" : "text-blue-600")}>
                                                    {formatPercent(row.roi)}
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                
                {totalPages > 1 && (
                    <div className="p-4 border-t bg-gray-50 flex items-center justify-between z-10">
                        <div className="text-sm text-gray-500">
                            총 {data?.total_count || 0}건 중 {((currentPage - 1) * itemsPerPage) + 1}-{Math.min(currentPage * itemsPerPage, data?.total_count || 0)}건
                        </div>
                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                                disabled={currentPage === 1 || isLoading}
                            >
                                이전
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                                disabled={currentPage === totalPages || isLoading}
                            >
                                다음
                            </Button>
                        </div>
                    </div>
                )}
            </Card>
        </div>
    )
}

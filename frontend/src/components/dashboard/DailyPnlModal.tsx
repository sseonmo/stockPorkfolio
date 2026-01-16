import { useState } from 'react'
import { Card } from '../ui/Card'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { X } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import * as dashboardApi from '../../api/dashboard'
import { formatCurrency, formatPercent, cn } from '../../lib/utils'

interface DailyPnlModalProps {
    isOpen: boolean
    onClose: () => void
}

export function DailyPnlModal({ isOpen, onClose }: DailyPnlModalProps) {
    const [startDate, setStartDate] = useState(
        new Date().toISOString().split('T')[0]
    )
    const [endDate, setEndDate] = useState(
        new Date().toISOString().split('T')[0]
    )
    const [selectedStockIds, setSelectedStockIds] = useState<number[]>([])

    // Fetch stocks for filter
    const { data: holdings } = useQuery({
        queryKey: ['holdings'],
        queryFn: async () => {
            const mod = await import('../../api/holdings')
            return mod.getHoldings()
        }
    })

    const { data, isLoading } = useQuery({
        queryKey: ['daily-pnl-history', startDate, endDate, selectedStockIds],
        queryFn: () => dashboardApi.getDailyPnlHistory(startDate, endDate, selectedStockIds.length > 0 ? selectedStockIds : undefined),
        enabled: isOpen,
    })

    if (!isOpen) return null

    const toggleStock = (id: number) => {
        if (selectedStockIds.includes(id)) {
            setSelectedStockIds(selectedStockIds.filter(s => s !== id))
        } else {
            setSelectedStockIds([...selectedStockIds, id])
        }
    }

    const setDateRange = (days: number) => {
        const end = new Date()
        const start = new Date()
        if (days > 0) {
            start.setDate(end.getDate() - days)
        }
        setEndDate(end.toISOString().split('T')[0])
        setStartDate(start.toISOString().split('T')[0])
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <Card className="w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                <div className="flex items-center justify-between border-b p-4">
                    <h2 className="text-xl font-bold">일일 손익 상세</h2>
                    <button onClick={onClose} className="rounded-full p-1 hover:bg-gray-100">
                        <X className="h-5 w-5" />
                    </button>
                </div>

                <div className="flex-1 overflow-auto p-4 space-y-4">
                    {/* Filters */}
                    <div className="grid gap-4 md:grid-cols-2">
                        <div className="flex flex-col gap-2">
                            <div className="flex gap-2">
                                <Button size="sm" variant="outline" onClick={() => setDateRange(0)}>오늘</Button>
                                <Button size="sm" variant="outline" onClick={() => setDateRange(7)}>1주일</Button>
                                <Button size="sm" variant="outline" onClick={() => setDateRange(30)}>1개월</Button>
                            </div>
                            <div className="flex gap-2 items-end">
                                <Input
                                    label="From"
                                    type="date"
                                    value={startDate}
                                    onChange={e => setStartDate(e.target.value)}
                                />
                                <Input
                                    label="To"
                                    type="date"
                                    value={endDate}
                                    onChange={e => setEndDate(e.target.value)}
                                />
                            </div>
                        </div>
                        <div>
                            <label className="text-sm font-medium text-gray-700 block mb-1">종목 필터 (선택 시 해당 종목 합산)</label>
                            <div className="flex flex-wrap gap-2 max-h-24 overflow-y-auto border p-2 rounded-md">
                                {holdings?.map(h => (
                                    <button
                                        key={h.stock.id}
                                        onClick={() => toggleStock(h.stock.id)}
                                        className={cn(
                                            "text-xs px-2 py-1 rounded-full border transition-colors",
                                            selectedStockIds.includes(h.stock.id)
                                                ? "bg-blue-100 border-blue-500 text-blue-700"
                                                : "bg-gray-50 border-gray-200 hover:bg-gray-100"
                                        )}
                                    >
                                        {h.stock.name}
                                    </button>
                                ))}
                                {(!holdings || holdings.length === 0) && <span className="text-xs text-gray-400">보유 종목 없음</span>}
                            </div>
                        </div>
                    </div>

                    {/* Summary */}
                    {data && (
                        <div className="grid grid-cols-2 gap-4 bg-gray-50 p-4 rounded-lg">
                            <div>
                                <span className="text-sm text-gray-500">기간 총 수익금</span>
                                <div className={cn("text-xl font-bold", data.total_pnl >= 0 ? "text-green-600" : "text-red-600")}>
                                    {formatCurrency(data.total_pnl, "KRW")}
                                </div>
                            </div>
                            <div>
                                <span className="text-sm text-gray-500">기간 수익률 (합산)</span>
                                <div className={cn("text-xl font-bold", data.total_roi_percent >= 0 ? "text-green-600" : "text-red-600")}>
                                    {formatPercent(data.total_roi_percent)}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Table */}
                    <div className="rounded-lg border">
                        <table className="w-full text-sm">
                            <thead className="bg-gray-50 border-b">
                                <tr>
                                    <th className="px-4 py-3 text-left font-medium text-gray-500">날짜</th>
                                    {selectedStockIds.length === 0 && (
                                        <th className="px-4 py-3 text-right font-medium text-gray-500">총 자산</th>
                                    )}
                                    <th className="px-4 py-3 text-right font-medium text-gray-500">일일 손익</th>
                                    <th className="px-4 py-3 text-right font-medium text-gray-500">수익률</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y">
                                {isLoading ? (
                                    <tr><td colSpan={4} className="p-8 text-center text-gray-500">Loading...</td></tr>
                                ) : !data || data.data.length === 0 ? (
                                    <tr><td colSpan={4} className="p-8 text-center text-gray-500">데이터가 없습니다.</td></tr>
                                ) : (
                                    data.data.map((row, i) => (
                                        <tr key={i} className="hover:bg-gray-50">
                                            <td className="px-4 py-3">{row.date}</td>
                                            {selectedStockIds.length === 0 && (
                                                <td className="px-4 py-3 text-right font-mono">
                                                    {row.total_value_krw ? formatCurrency(row.total_value_krw, "KRW") : '-'}
                                                </td>
                                            )}
                                            <td className={cn("px-4 py-3 text-right font-mono font-medium", row.daily_pnl >= 0 ? "text-green-600" : "text-red-600")}>
                                                {formatCurrency(row.daily_pnl, "KRW")}
                                            </td>
                                            <td className={cn("px-4 py-3 text-right font-mono", row.roi >= 0 ? "text-green-600" : "text-red-600")}>
                                                {formatPercent(row.roi)}
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div className="p-4 border-t bg-gray-50 flex justify-end">
                    <Button onClick={onClose}>닫기</Button>
                </div>
            </Card>
        </div>
    )
}

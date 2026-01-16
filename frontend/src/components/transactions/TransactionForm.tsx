import { useState, useEffect } from 'react'
import { useCreateTransaction, useUpdateTransaction } from '../../hooks/useTransactions'
import { StockSearchResult, TransactionType, Transaction } from '../../types'
import { StockSearch } from './StockSearch'
import { Card } from '../ui/Card'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { cn } from '../../lib/utils'
import { useCreateStock } from '../../hooks/useStocks'

export function TransactionForm({ onClose, initialData }: { onClose?: () => void, initialData?: Transaction | null }) {
  const [selectedStock, setSelectedStock] = useState<StockSearchResult | null>(null)
  const [type, setType] = useState<TransactionType>('BUY')
  const [quantity, setQuantity] = useState('')
  const [price, setPrice] = useState('')
  const [date, setDate] = useState(new Date().toISOString().split('T')[0])
  const [fees, setFees] = useState('0')
  const [notes, setNotes] = useState('')

  const createTransaction = useCreateTransaction()
  const updateTransaction = useUpdateTransaction()
  const createStock = useCreateStock()

  useEffect(() => {
    if (initialData) {
      setSelectedStock({
        ticker: initialData.stock.ticker,
        name: initialData.stock.name,
        market_type: initialData.stock.market_type,
        exchange: initialData.stock.exchange,
        current_price: initialData.stock.current_price,
      })
      setType(initialData.transaction_type)
      setQuantity(initialData.quantity.toString())
      setPrice(initialData.price.toString())
      setDate(initialData.transaction_date.toString())
      setFees(initialData.fees.toString())
      setNotes(initialData.notes || '')
    } else {
      setSelectedStock(null)
      setQuantity('')
      setPrice('')
      setDate(new Date().toISOString().split('T')[0])
      setFees('0')
      setNotes('')
      setType('BUY')
    }
  }, [initialData])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedStock) return

    try {
      if (initialData) {
        // Edit mode
        await updateTransaction.mutateAsync({
          id: initialData.id,
          data: {
            quantity: parseFloat(quantity),
            price: parseFloat(price),
            transaction_date: date,
            fees: parseFloat(fees),
            notes: notes,
          }
        })
      } else {
        // Create mode
        const stockRes = await createStock.mutateAsync({
          ticker: selectedStock.ticker,
          name: selectedStock.name,
          market_type: selectedStock.market_type,
          exchange: selectedStock.exchange,
        })

        const stockId = stockRes.id

        await createTransaction.mutateAsync({
          stock_id: stockId,
          transaction_type: type,
          quantity: parseFloat(quantity),
          price: parseFloat(price),
          transaction_date: date,
          fees: parseFloat(fees),
          notes: notes,
        })
      }

      onClose?.()
      if (!initialData) {
        setSelectedStock(null)
        setQuantity('')
        setPrice('')
        setNotes('')
      }
    } catch (error) {
      console.error("Failed to save transaction", error)
    }
  }

  const isLoading = createTransaction.isPending || updateTransaction.isPending || createStock.isPending

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">{initialData ? '거래 수정' : '새 거래 추가'}</h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700">종목</label>
          {selectedStock ? (
            <div className="flex items-center justify-between p-2 border rounded-lg bg-blue-50 border-blue-100">
              <div>
                <div className="font-bold text-blue-900">{selectedStock.name}</div>
                <div className="text-xs text-blue-700">{selectedStock.ticker} • {selectedStock.market_type}</div>
              </div>
              {!initialData && (
                <Button size="sm" variant="ghost" type="button" onClick={() => setSelectedStock(null)}>변경</Button>
              )}
            </div>
          ) : (
            <StockSearch onSelect={setSelectedStock} />
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700">유형</label>
            <div className="flex rounded-lg bg-gray-100 p-1">
              {([
                { value: 'BUY', label: '매수' },
                { value: 'SELL', label: '매도' },
                { value: 'DIVIDEND', label: '배당' }
              ] as const).map((t) => (
                <button
                  key={t.value}
                  type="button"
                  onClick={() => !initialData && setType(t.value)}
                  disabled={!!initialData}
                  className={cn(
                    "flex-1 text-xs font-medium py-1.5 rounded-md transition-all",
                    type === t.value ? "bg-white shadow-sm text-gray-900" : "text-gray-500 hover:text-gray-900",
                    initialData ? "cursor-not-allowed opacity-70" : ""
                  )}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>
          <Input
            label="날짜"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="수량"
            type="number"
            step="any"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            placeholder="0"
            required
          />
          <Input
            label="가격"
            type="number"
            step="any"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            placeholder="0.00"
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="수수료 (선택)"
            type="number"
            step="any"
            value={fees}
            onChange={(e) => setFees(e.target.value)}
            placeholder="0"
          />
          <Input
            label="총 금액 (예상)"
            type="text" // readOnly, so text is fine to formatting
            value={(() => {
              const q = parseFloat(quantity) || 0
              const p = parseFloat(price) || 0
              const total = q * p
              return total > 0 ? total.toLocaleString() : ''
            })()}
            readOnly
            className="bg-gray-50 text-gray-500 cursor-not-allowed"
          />
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700">메모</label>
          <textarea
            className="w-full rounded-lg border border-gray-200 p-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>

        <div className="flex justify-end gap-2 pt-2">
          {onClose && <Button type="button" variant="ghost" onClick={onClose}>취소</Button>}
          <Button type="submit" isLoading={isLoading}>{initialData ? '수정' : '저장'}</Button>
        </div>
      </form>
    </Card>
  )
}

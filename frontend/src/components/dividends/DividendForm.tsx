import { useState, useEffect } from 'react'
import { useCreateDividend, useUpdateDividend } from '../../hooks/useDividends'
import { StockSearchResult, Dividend } from '../../types'
import { StockSearch } from '../transactions/StockSearch'
import { Card } from '../ui/Card'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { useCreateStock } from '../../hooks/useStocks'

export function DividendForm({ onClose, initialData }: { onClose?: () => void, initialData?: Dividend | null }) {
  const [selectedStock, setSelectedStock] = useState<StockSearchResult | null>(null)
  const [amount, setAmount] = useState('')
  const [tax, setTax] = useState('0')
  const [date, setDate] = useState(new Date().toISOString().split('T')[0])
  const [notes, setNotes] = useState('')

  const createDividend = useCreateDividend()
  const updateDividend = useUpdateDividend()
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
      setAmount(initialData.amount.toString())
      setTax(initialData.tax.toString())
      setDate(initialData.dividend_date.toString())
      setNotes(initialData.notes || '')
    } else {
      setSelectedStock(null)
      setAmount('')
      setTax('0')
      setDate(new Date().toISOString().split('T')[0])
      setNotes('')
    }
  }, [initialData])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedStock) return

    try {
      if (initialData) {
        // Edit mode
        await updateDividend.mutateAsync({
          id: initialData.id,
          data: {
            amount: parseFloat(amount),
            tax: parseFloat(tax),
            dividend_date: date,
            notes: notes,
          }
        })
      } else {
        // Create mode
        let stockId = 0
        
        // Stock이 없을 수도 있으므로(검색 결과에서 바로 선택하면 ID가 없을 수 있음?)
        // StockSearch는 StockSearchResult를 주는데 id는 없음.
        // 하지만 백엔드에서는 ticker로 찾거나 생성해야 함.
        // useCreateStock 훅을 사용하여 stock을 확보해야 함.
        
        const stockRes = await createStock.mutateAsync({
          ticker: selectedStock.ticker,
          name: selectedStock.name,
          market_type: selectedStock.market_type,
          exchange: selectedStock.exchange,
        })
        stockId = stockRes.id

        await createDividend.mutateAsync({
          stock_id: stockId,
          amount: parseFloat(amount),
          tax: parseFloat(tax),
          currency: 'KRW', // 기본값
          dividend_date: date,
          notes: notes,
        })
      }

      onClose?.()
      if (!initialData) {
        setSelectedStock(null)
        setAmount('')
        setTax('0')
        setNotes('')
      }
    } catch (error) {
      console.error("Failed to save dividend", error)
    }
  }

  const isLoading = createDividend.isPending || updateDividend.isPending || createStock.isPending

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">{initialData ? '배당 수정' : '새 배당 추가'}</h3>
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
          <Input
            label="배당 지급일"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            required
          />
          <Input
            label="세전 배당금"
            type="number"
            step="any"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="0"
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="세금 (15.4% 등)"
            type="number"
            step="any"
            value={tax}
            onChange={(e) => setTax(e.target.value)}
            placeholder="0"
          />
          <Input
            label="수령액 (예상)"
            type="text"
            value={(() => {
              const a = parseFloat(amount) || 0
              const t = parseFloat(tax) || 0
              const net = a - t
              return net > 0 ? net.toLocaleString() : ''
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

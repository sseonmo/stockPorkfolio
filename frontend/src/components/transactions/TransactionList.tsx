import { useTransactions, useDeleteTransaction } from '../../hooks/useTransactions'
import { Card } from '../ui/Card'
import { Loading } from '../ui/Loading'
import { formatCurrency, formatDate, cn } from '../../lib/utils'
import { Trash2, Pencil } from 'lucide-react'
import { Button } from '../ui/Button'
import { Transaction } from '../../types'

interface TransactionListProps {
  onEdit?: (transaction: Transaction) => void
}

export function TransactionList({ onEdit }: TransactionListProps) {
  const { data: transactions, isLoading } = useTransactions()
  const deleteTransaction = useDeleteTransaction()

  if (isLoading) return <Card className="p-12"><Loading /></Card>

  if (!transactions || transactions.length === 0) {
    return (
      <Card className="p-8 text-center text-gray-500">
        거래 내역이 없습니다. 거래를 추가해보세요!
      </Card>
    )
  }

  const handleDelete = (id: number) => {
    if (confirm('정말 이 거래 내역을 삭제하시겠습니까?')) {
      deleteTransaction.mutate(id)
    }
  }

  return (
    <Card noPadding className="overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-gray-500 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 font-medium">날짜</th>
              <th className="px-6 py-3 font-medium">유형</th>
              <th className="px-6 py-3 font-medium">종목</th>
              <th className="px-6 py-3 font-medium text-right">수량</th>
              <th className="px-6 py-3 font-medium text-right">가격</th>
              <th className="px-6 py-3 font-medium text-right">총액</th>
              <th className="px-6 py-3 font-medium text-right">작업</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {transactions.map((tx) => (
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
    </Card>
  )
}

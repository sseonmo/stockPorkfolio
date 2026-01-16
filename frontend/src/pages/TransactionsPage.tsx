import { useState } from 'react'
import { Plus, X } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { TransactionList } from '../components/transactions/TransactionList'
import { TransactionForm } from '../components/transactions/TransactionForm'
import { Transaction } from '../types'

export function TransactionsPage() {
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingTransaction, setEditingTransaction] = useState<Transaction | null>(null)

  const handleEdit = (transaction: Transaction) => {
    setEditingTransaction(transaction)
    setIsFormOpen(true)
  }

  const handleCloseForm = () => {
    setIsFormOpen(false)
    setEditingTransaction(null)
  }

  const handleToggleForm = () => {
    if (isFormOpen) {
      handleCloseForm()
    } else {
      setEditingTransaction(null)
      setIsFormOpen(true)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">거래 내역</h1>
          <p className="text-sm text-gray-500">거래 내역 조회 및 관리</p>
        </div>
        <Button onClick={handleToggleForm}>
          {isFormOpen ? (
            <>
              <X className="mr-2 h-4 w-4" /> 닫기
            </>
          ) : (
            <>
              <Plus className="mr-2 h-4 w-4" /> 거래 추가
            </>
          )}
        </Button>
      </div>

      {isFormOpen && (
        <div className="animate-in slide-in-from-top-4 duration-200">
          <TransactionForm
            onClose={handleCloseForm}
            initialData={editingTransaction}
          />
        </div>
      )}

      <TransactionList onEdit={handleEdit} />
    </div>
  )
}

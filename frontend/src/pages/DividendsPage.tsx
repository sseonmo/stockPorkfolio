import { useState } from 'react'
import { Plus, X } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { DividendList } from '../components/dividends/DividendList'
import { DividendForm } from '../components/dividends/DividendForm'
import { Dividend } from '../types'

export function DividendsPage() {
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingDividend, setEditingDividend] = useState<Dividend | null>(null)

  const handleEdit = (dividend: Dividend) => {
    setEditingDividend(dividend)
    setIsFormOpen(true)
  }

  const handleCloseForm = () => {
    setIsFormOpen(false)
    setEditingDividend(null)
  }

  const handleToggleForm = () => {
    if (isFormOpen) {
      handleCloseForm()
    } else {
      setEditingDividend(null)
      setIsFormOpen(true)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">배당 내역</h1>
          <p className="text-sm text-gray-500">배당금 수령 내역 관리</p>
        </div>
        <Button onClick={handleToggleForm}>
          {isFormOpen ? (
            <>
              <X className="mr-2 h-4 w-4" /> 닫기
            </>
          ) : (
            <>
              <Plus className="mr-2 h-4 w-4" /> 배당 추가
            </>
          )}
        </Button>
      </div>

      {isFormOpen && (
        <div className="animate-in slide-in-from-top-4 duration-200">
          <DividendForm
            onClose={handleCloseForm}
            initialData={editingDividend}
          />
        </div>
      )}

      <DividendList onEdit={handleEdit} />
    </div>
  )
}

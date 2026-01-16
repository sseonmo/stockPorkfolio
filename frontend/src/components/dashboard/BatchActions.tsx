import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { RefreshCw, Database, DollarSign, TrendingUp } from 'lucide-react'
import { Card } from '../ui/Card'
import * as batchApi from '../../api/batch'
import { cn } from '../../lib/utils'

interface BatchButtonProps {
  label: string
  icon: React.ElementType
  onClick: () => void
  isLoading: boolean
  color: string
}

function BatchButton({ label, icon: Icon, onClick, isLoading, color }: BatchButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={isLoading}
      className={cn(
        'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all',
        'border border-gray-200 hover:border-gray-300',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        color
      )}
    >
      <Icon className={cn('h-4 w-4', isLoading && 'animate-spin')} />
      {label}
    </button>
  )
}

export function BatchActions() {
  const queryClient = useQueryClient()
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text })
    setTimeout(() => setMessage(null), 3000)
  }

  const invalidateQueries = () => {
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    queryClient.invalidateQueries({ queryKey: ['holdings'] })
  }

  const krPricesMutation = useMutation({
    mutationFn: batchApi.updateKrPrices,
    onSuccess: (data) => {
      showMessage('success', data.message)
      invalidateQueries()
    },
    onError: () => showMessage('error', '한국 주식 가격 업데이트 실패'),
  })

  const usPricesMutation = useMutation({
    mutationFn: batchApi.updateUsPrices,
    onSuccess: (data) => {
      showMessage('success', data.message)
      invalidateQueries()
    },
    onError: () => showMessage('error', '미국 주식 가격 업데이트 실패'),
  })

  const snapshotMutation = useMutation({
    mutationFn: batchApi.createSnapshot,
    onSuccess: (data) => {
      showMessage('success', data.message)
      invalidateQueries()
    },
    onError: () => showMessage('error', '스냅샷 생성 실패'),
  })

  const refreshAllMutation = useMutation({
    mutationFn: batchApi.refreshAll,
    onSuccess: (data) => {
      showMessage('success', data.message)
      invalidateQueries()
    },
    onError: () => showMessage('error', '전체 새로고침 실패'),
  })

  const isAnyLoading =
    krPricesMutation.isPending ||
    usPricesMutation.isPending ||
    snapshotMutation.isPending ||
    refreshAllMutation.isPending

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700">데이터 관리</h3>
        {message && (
          <span
            className={cn(
              'text-xs px-2 py-1 rounded',
              message.type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            )}
          >
            {message.text}
          </span>
        )}
      </div>
      <div className="flex flex-wrap gap-2">
        <BatchButton
          label="KR 가격"
          icon={TrendingUp}
          onClick={() => krPricesMutation.mutate()}
          isLoading={krPricesMutation.isPending}
          color="text-blue-600 bg-blue-50 hover:bg-blue-100"
        />
        <BatchButton
          label="US 가격"
          icon={DollarSign}
          onClick={() => usPricesMutation.mutate()}
          isLoading={usPricesMutation.isPending}
          color="text-green-600 bg-green-50 hover:bg-green-100"
        />
        <BatchButton
          label="스냅샷"
          icon={Database}
          onClick={() => snapshotMutation.mutate()}
          isLoading={snapshotMutation.isPending}
          color="text-violet-600 bg-violet-50 hover:bg-violet-100"
        />
        <BatchButton
          label="전체 새로고침"
          icon={RefreshCw}
          onClick={() => refreshAllMutation.mutate()}
          isLoading={refreshAllMutation.isPending}
          color="text-orange-600 bg-orange-50 hover:bg-orange-100"
        />
      </div>
    </Card>
  )
}

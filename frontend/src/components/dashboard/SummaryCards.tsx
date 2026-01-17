import { useState } from 'react'
import { ArrowUp, ArrowDown, DollarSign, Wallet, TrendingUp, Calendar } from 'lucide-react'
import { Card } from '../ui/Card'
import { usePortfolioSummary } from '../../hooks/useDashboard'
import { formatCurrency, formatPercent, cn } from '../../lib/utils'
import { DailyPnlModal } from './DailyPnlModal'

export function SummaryCards() {
  const { data: summary, isLoading } = usePortfolioSummary()
  const [isModalOpen, setIsModalOpen] = useState(false)

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="h-32 animate-pulse bg-gray-100 border-none shadow-none" />
        ))}
      </div>
    )
  }

  const displaySummary = summary || {
    total_value_krw: 0,
    total_invested_krw: 0,
    total_unrealized_gain: 0,
    total_unrealized_gain_percent: 0,
    daily_pnl: 0,
    daily_pnl_percent: 0,
    total_dividends: 0,
    exchange_rate: 0,
  }

  const cards = [
    {
      label: '총 자산',
      value: formatCurrency(displaySummary.total_value_krw, 'KRW'),
      subValue: '포트폴리오 가치',
      icon: Wallet,
      color: 'text-blue-600',
      bg: 'bg-blue-50',
    },
    {
      label: '총 투자금액',
      value: formatCurrency(displaySummary.total_invested_krw, 'KRW'),
      subValue: '원금',
      icon: DollarSign,
      color: 'text-violet-600',
      bg: 'bg-violet-50',
    },
    {
      label: '평가 손익',
      value: formatCurrency(displaySummary.total_unrealized_gain, 'KRW'),
      subValue: formatPercent(displaySummary.total_unrealized_gain_percent),
      icon: TrendingUp,
      color: displaySummary.total_unrealized_gain >= 0 ? 'text-red-600' : 'text-blue-600',
      bg: displaySummary.total_unrealized_gain >= 0 ? 'bg-red-50' : 'bg-blue-50',
      isGain: true,
    },
    {
      label: '일일 손익',
      value: formatCurrency(displaySummary.daily_pnl, 'KRW'),
      subValue: formatPercent(displaySummary.daily_pnl_percent),
      icon: Calendar,
      color: displaySummary.daily_pnl >= 0 ? 'text-red-600' : 'text-blue-600',
      bg: displaySummary.daily_pnl >= 0 ? 'bg-red-50' : 'bg-blue-50',
      isGain: true,
    },
  ]

  return (
    <>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {cards.map((card, index) => (
          <Card
            key={index}
            className={cn(
              "relative overflow-hidden transition-all hover:shadow-md",
              card.label === '일일 손익' ? "cursor-pointer ring-1 ring-transparent hover:ring-blue-500" : ""
            )}
            onClick={() => {
              if (card.label === '일일 손익') setIsModalOpen(true)
            }}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">{card.label}</p>
                <h3 className="mt-2 text-2xl font-bold tracking-tight text-gray-900">{card.value}</h3>
              </div>
              <div className={cn('rounded-xl p-2.5', card.bg)}>
                <card.icon className={cn('h-6 w-6', card.color)} />
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm">
              {card.isGain ? (
                <span
                  className={cn(
                    'font-medium flex items-center',
                    card.subValue.includes('-') ? 'text-blue-600' : 'text-red-600'
                  )}
                >
                  {card.subValue.includes('-') ? (
                    <ArrowDown className="mr-1 h-4 w-4" />
                  ) : (
                    <ArrowUp className="mr-1 h-4 w-4" />
                  )}
                  {card.subValue}
                </span>
              ) : (
                <span className="text-gray-500">{card.subValue}</span>
              )}
            </div>
          </Card>
        ))}
      </div>
      {isModalOpen && (
        <DailyPnlModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
      )}
    </>
  )
}

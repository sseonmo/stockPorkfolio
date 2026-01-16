import { useState } from 'react'
import { MarketType } from '../types'
import { MarketTabs } from '../components/holdings/MarketTabs'
import { HoldingsTable } from '../components/holdings/HoldingsTable'

export function HoldingsPage() {
  const [market, setMarket] = useState<MarketType | 'ALL'>('ALL')

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">보유 종목</h1>
          <p className="text-sm text-gray-500">보유 주식 관리</p>
        </div>
        <MarketTabs activeTab={market} onTabChange={setMarket} />
      </div>

      <HoldingsTable market={market} />
    </div>
  )
}

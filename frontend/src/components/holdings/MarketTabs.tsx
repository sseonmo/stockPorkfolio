import { MarketType } from '../../types'
import { cn } from '../../lib/utils'

interface MarketTabsProps {
  activeTab: MarketType | 'ALL'
  onTabChange: (tab: MarketType | 'ALL') => void
}

export function MarketTabs({ activeTab, onTabChange }: MarketTabsProps) {
  const tabs = [
    { id: 'ALL', label: '전체' },
    { id: 'KR', label: '국내 (KR)' },
    { id: 'US', label: '해외 (US)' },
  ] as const

  return (
    <div className="flex space-x-1 rounded-xl bg-gray-100 p-1">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={cn(
            'w-full rounded-lg px-3 py-1.5 text-sm font-medium transition-all',
            activeTab === tab.id
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-500 hover:text-gray-900 hover:bg-gray-200/50'
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}

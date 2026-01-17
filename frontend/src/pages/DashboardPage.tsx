import { useState } from 'react'
import { Responsive, WidthProvider } from 'react-grid-layout/legacy'
import { Wallet, DollarSign, TrendingUp, Calendar } from 'lucide-react'
import { AssetTrendChart } from '../components/dashboard/AssetTrendChart'
import { DividendTrendChart } from '../components/dashboard/DividendTrendChart'
import { MarketBreakdownChart } from '../components/dashboard/MarketBreakdownChart'
import { BatchActions } from '../components/dashboard/BatchActions'
import { SummaryCard } from '../components/dashboard/SummaryCard'
import { DailyPnlModal } from '../components/dashboard/DailyPnlModal'
import { usePortfolioSummary } from '../hooks/useDashboard'
import { formatCurrency, formatPercent } from '../lib/utils'

const ResponsiveGridLayout = WidthProvider(Responsive)

const INITIAL_LAYOUTS = {
  lg: [
    { i: 'total_value', x: 0, y: 0, w: 1, h: 1 },
    { i: 'invested', x: 1, y: 0, w: 1, h: 1 },
    { i: 'unrealized', x: 2, y: 0, w: 1, h: 1 },
    { i: 'daily', x: 3, y: 0, w: 1, h: 1 },
    { i: 'asset_trend', x: 0, y: 1, w: 3, h: 5 },
    { i: 'market_breakdown', x: 3, y: 1, w: 1, h: 5 },
    { i: 'dividend_trend', x: 0, y: 6, w: 3, h: 5 },
  ],
  md: [
    { i: 'total_value', x: 0, y: 0, w: 1, h: 1 },
    { i: 'invested', x: 1, y: 0, w: 1, h: 1 },
    { i: 'unrealized', x: 0, y: 1, w: 1, h: 1 },
    { i: 'daily', x: 1, y: 1, w: 1, h: 1 },
    { i: 'asset_trend', x: 0, y: 2, w: 2, h: 4 },
    { i: 'market_breakdown', x: 0, y: 6, w: 2, h: 3 },
    { i: 'dividend_trend', x: 0, y: 9, w: 2, h: 4 },
  ],
  sm: [
    { i: 'total_value', x: 0, y: 0, w: 1, h: 1 },
    { i: 'invested', x: 0, y: 1, w: 1, h: 1 },
    { i: 'unrealized', x: 0, y: 2, w: 1, h: 1 },
    { i: 'daily', x: 0, y: 3, w: 1, h: 1 },
    { i: 'asset_trend', x: 0, y: 4, w: 1, h: 4 },
    { i: 'market_breakdown', x: 0, y: 8, w: 1, h: 3 },
    { i: 'dividend_trend', x: 0, y: 11, w: 1, h: 4 },
  ],
}

export function DashboardPage() {
  const [layouts, setLayouts] = useState(() => {
    const saved = localStorage.getItem('dashboard-layout')
    return saved ? JSON.parse(saved) : INITIAL_LAYOUTS
  })
  const [isModalOpen, setIsModalOpen] = useState(false)
  const { data: summary } = usePortfolioSummary()

  const onLayoutChange = (_layout: any, layouts: any) => {
    setLayouts(layouts)
    localStorage.setItem('dashboard-layout', JSON.stringify(layouts))
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">대시보드</h1>
          <p className="text-sm text-gray-500">포트폴리오에 오신 것을 환영합니다</p>
        </div>
        <BatchActions />
      </div>

      <ResponsiveGridLayout
        className="layout"
        layouts={layouts}
        breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
        cols={{ lg: 4, md: 2, sm: 1, xs: 1, xxs: 1 }}
        rowHeight={120}
        isDraggable={true}
        isResizable={true}
        onLayoutChange={onLayoutChange}
        margin={[16, 16]}
      >
        <div key="total_value">
          <SummaryCard
            label="총 자산"
            value={formatCurrency(displaySummary.total_value_krw, 'KRW')}
            subValue="포트폴리오 가치"
            icon={Wallet}
            color="text-blue-600"
            bg="bg-blue-50"
          />
        </div>
        <div key="invested">
          <SummaryCard
            label="총 투자금액"
            value={formatCurrency(displaySummary.total_invested_krw, 'KRW')}
            subValue="원금"
            icon={DollarSign}
            color="text-violet-600"
            bg="bg-violet-50"
          />
        </div>
        <div key="unrealized">
          <SummaryCard
            label="평가 손익"
            value={formatCurrency(displaySummary.total_unrealized_gain, 'KRW')}
            subValue={formatPercent(displaySummary.total_unrealized_gain_percent)}
            icon={TrendingUp}
            color={displaySummary.total_unrealized_gain >= 0 ? 'text-red-600' : 'text-blue-600'}
            bg={displaySummary.total_unrealized_gain >= 0 ? 'bg-red-50' : 'bg-blue-50'}
            isGain
          />
        </div>
        <div key="daily">
          <SummaryCard
            label="일일 손익"
            value={formatCurrency(displaySummary.daily_pnl, 'KRW')}
            subValue={formatPercent(displaySummary.daily_pnl_percent)}
            icon={Calendar}
            color={displaySummary.daily_pnl >= 0 ? 'text-red-600' : 'text-blue-600'}
            bg={displaySummary.daily_pnl >= 0 ? 'bg-red-50' : 'bg-blue-50'}
            isGain
            onClick={() => setIsModalOpen(true)}
          />
        </div>
        
        <div key="asset_trend">
          <AssetTrendChart />
        </div>
        
        <div key="market_breakdown">
          <MarketBreakdownChart />
        </div>
        
        <div key="dividend_trend">
          <DividendTrendChart />
        </div>
      </ResponsiveGridLayout>

      {isModalOpen && (
        <DailyPnlModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
      )}
    </div>
  )
}

export type MarketType = 'KR' | 'US'
export type TransactionType = 'BUY' | 'SELL' | 'DIVIDEND'
export type BaseCurrency = 'KRW' | 'USD'

export interface User {
  id: number
  email: string
  name: string
  base_currency: BaseCurrency
  is_active: boolean
  created_at: string
}

export interface Stock {
  id: number
  ticker: string
  name: string
  market_type: MarketType
  exchange: string
  sector: string | null
  current_price: number | null
  currency: string
  created_at: string
}

export interface StockSearchResult {
  ticker: string
  name: string
  market_type: MarketType
  exchange: string
  current_price: number | null
}

export interface Transaction {
  id: number
  user_id: number
  stock_id: number
  transaction_type: TransactionType
  quantity: number
  price: number
  exchange_rate: number
  fees: number
  transaction_date: string
  notes: string | null
  created_at: string
  total_amount: number
  total_amount_krw: number
  stock: Stock
}

export interface TransactionCreate {
  stock_id: number
  transaction_type: TransactionType
  quantity: number
  price: number
  exchange_rate?: number
  fees?: number
  transaction_date: string
  notes?: string
}

export interface Holding {
  id: number
  user_id: number
  stock_id: number
  quantity: number
  average_cost: number
  average_exchange_rate: number
  total_invested: number
  total_dividends: number
  realized_gain: number
  created_at: string
  updated_at: string
  stock: Stock
  current_value: number
  current_value_krw: number
  unrealized_gain: number
  unrealized_gain_percent: number
  weight_percent: number
}

export interface PortfolioSummary {
  total_value_krw: number
  total_invested_krw: number
  total_unrealized_gain: number
  total_unrealized_gain_percent: number
  daily_pnl: number
  daily_pnl_percent: number
  total_dividends: number
  exchange_rate: number
}

export interface MarketBreakdown {
  market_type: MarketType
  value_original: number
  value_krw: number
  weight_percent: number
  unrealized_gain: number
  unrealized_gain_percent: number
}

export interface DailyPerformancePoint {
  date: string
  total_value_krw: number
  daily_pnl: number
  daily_pnl_percent: number
  cumulative_return_percent: number
}

export interface AssetTrendResponse {
  data: DailyPerformancePoint[]
  period_return_percent: number
  max_drawdown_percent: number
}

export interface SectorAllocation {
  sector: string
  value_krw: number
  weight_percent: number
  stock_count: number
}

export interface BenchmarkDataPoint {
  date: string
  portfolio_return_percent: number
  benchmark_return_percent: number
}

export interface BenchmarkComparison {
  benchmark_name: string
  benchmark_ticker: string
  data: BenchmarkDataPoint[]
  portfolio_total_return: number
  benchmark_total_return: number
  alpha: number
}

export interface ConcentrationWarning {
  ticker: string
  name: string
  weight_percent: number
  threshold_percent: number
  message: string
}

export interface RiskMetrics {
  max_drawdown_percent: number
  max_drawdown_start: string | null
  max_drawdown_end: string | null
  concentration_warnings: ConcentrationWarning[]
  top_5_weight_percent: number
  diversification_score: number
}

export interface DailyPnlHistoryItem {
  date: string
  daily_pnl: number
  daily_pnl_percent: number
  total_value_krw: number | null
  roi: number
}

export interface DailyPnlHistoryResponse {
  data: DailyPnlHistoryItem[]
  total_pnl: number
  total_roi_percent: number
}

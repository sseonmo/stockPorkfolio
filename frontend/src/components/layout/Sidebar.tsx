import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Wallet,
  ArrowRightLeft,
  PieChart,
  LogOut,
  TrendingUp,
  Banknote,
} from 'lucide-react'
import { cn } from '../../lib/utils'

const NAV_ITEMS = [
  { label: 'Dashboard', path: '/', icon: LayoutDashboard },
  { label: 'Holdings', path: '/holdings', icon: Wallet },
  { label: 'Transactions', path: '/transactions', icon: ArrowRightLeft },
  { label: 'Dividends', path: '/dividends', icon: Banknote },
  { label: 'Analytics', path: '/analytics', icon: PieChart },
]

export function Sidebar() {
  const location = useLocation()
  // Assuming useAuth might exist or I can just mock logout for UI structure if not exported
  // Wait, I saw useUser, useLogin, useRegister. I didn't see useLogout.
  // I will check useAuth again or just put a placeholder button.
  // Re-reading useAuth.ts content provided in context... it has useUser, useLogin, useRegister. NO LOGOUT.
  // I'll assume for now logout is a future feature or just client side token removal.
  // I'll leave the button visually but maybe disabled or simple reload.

  return (
    <div className="flex h-screen w-64 flex-col bg-slate-900 text-white shadow-xl flex-shrink-0">
      <div className="flex h-16 items-center px-6 border-b border-slate-800">
        <TrendingUp className="mr-2 h-6 w-6 text-blue-500" />
        <span className="text-xl font-bold tracking-tight text-white">StockFlow</span>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-6">
        {NAV_ITEMS.map((item) => {
          const isActive = location.pathname === item.path
          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                'group flex items-center rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200',
                isActive
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-900/20'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              )}
            >
              <item.icon
                className={cn(
                  'mr-3 h-5 w-5 flex-shrink-0 transition-colors',
                  isActive ? 'text-white' : 'text-slate-400 group-hover:text-white'
                )}
              />
              {item.label}
            </Link>
          )
        })}
      </nav>

      <div className="border-t border-slate-800 p-4">
        <button
          className="group flex w-full items-center rounded-lg px-3 py-2.5 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-800 hover:text-white"
          onClick={() => {
            // Placeholder logout
            console.log('Logout clicked')
          }}
        >
          <LogOut className="mr-3 h-5 w-5 text-slate-400 transition-colors group-hover:text-red-400" />
          로그아웃
        </button>
      </div>
    </div>
  )
}

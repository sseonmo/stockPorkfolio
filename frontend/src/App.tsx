import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/layout/Layout'
import { DashboardPage } from './pages/DashboardPage'
import { HoldingsPage } from './pages/HoldingsPage'
import { TransactionsPage } from './pages/TransactionsPage'
import { DividendsPage } from './pages/DividendsPage'
import { AnalyticsPage } from './pages/AnalyticsPage'
import { LoginPage } from './pages/LoginPage'
import { useUser } from './hooks/useAuth'
import { Loading } from './components/ui/Loading'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('access_token')
  const { data: user, isLoading, isError } = useUser()

  // If no token exists, immediately redirect to login without waiting for API
  if (!token) {
    return <Navigate to="/login" replace />
  }

  if (isLoading) {
    return <Loading fullScreen />
  }

  if (isError || !user) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route path="holdings" element={<HoldingsPage />} />
          <Route path="transactions" element={<TransactionsPage />} />
          <Route path="dividends" element={<DividendsPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

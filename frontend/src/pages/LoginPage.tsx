import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLogin, useRegister } from '../hooks/useAuth'
import { Card } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { Button } from '../components/ui/Button'
import { TrendingUp, CheckSquare, Square } from 'lucide-react'

export function LoginPage() {
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [rememberEmail, setRememberEmail] = useState(false)

  const navigate = useNavigate()
  const login = useLogin()
  const register = useRegister()

  useEffect(() => {
    const savedEmail = localStorage.getItem('savedEmail')
    if (savedEmail) {
      setEmail(savedEmail)
      setRememberEmail(true)
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (isLogin) {
        if (rememberEmail) {
          localStorage.setItem('savedEmail', email)
        } else {
          localStorage.removeItem('savedEmail')
        }
        await login.mutateAsync({ email, password })
        navigate('/')
      } else {
        await register.mutateAsync({ email, password, name })
        alert('Account created successfully! Please sign in.')
        setIsLogin(true)
      }
    } catch (error) {
      console.error('Auth failed', error)
      alert(isLogin ? 'Login failed. Please check your credentials.' : 'Registration failed. Please try again.')
    }
  }

  const isLoading = login.isPending || register.isPending

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-md">
        <div className="mb-8 flex flex-col items-center">
          <div className="rounded-xl bg-blue-600 p-3 shadow-lg shadow-blue-600/20">
            <TrendingUp className="h-8 w-8 text-white" />
          </div>
          <h1 className="mt-4 text-2xl font-bold tracking-tight text-gray-900">StockFlow</h1>
          <p className="mt-1 text-sm text-gray-500">포트폴리오를 정밀하게 관리하세요</p>
        </div>

        <Card className="p-8">
          <form onSubmit={handleSubmit} className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">
              {isLogin ? '환영합니다' : '계정 생성'}
            </h2>

            {!isLogin && (
              <Input
                label="이름"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="홍길동"
                required
              />
            )}

            <Input
              label="이메일"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
            />

            <Input
              label="비밀번호"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />

            {isLogin && (
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => setRememberEmail(!rememberEmail)}
                  className="flex items-center text-sm text-gray-600 hover:text-gray-900"
                >
                  {rememberEmail ? (
                    <CheckSquare className="mr-2 h-4 w-4 text-blue-600" />
                  ) : (
                    <Square className="mr-2 h-4 w-4 text-gray-400" />
                  )}
                  아이디 저장
                </button>
              </div>
            )}

            <Button className="w-full" type="submit" isLoading={isLoading}>
              {isLogin ? '로그인' : '계정 만들기'}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm">
            <span className="text-gray-500">
              {isLogin ? "계정이 없으신가요? " : "이미 계정이 있으신가요? "}
            </span>
            <button
              onClick={() => setIsLogin(!isLogin)}
              className="font-medium text-blue-600 hover:text-blue-500 hover:underline"
            >
              {isLogin ? '회원가입' : '로그인'}
            </button>
          </div>
        </Card>
      </div>
    </div>
  )
}

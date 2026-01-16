import api from '../lib/api'
import type { User } from '../types'

export async function login(email: string, password: string): Promise<string> {
  const formData = new URLSearchParams()
  formData.append('username', email)
  formData.append('password', password)
  
  const response = await api.post('/auth/token', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  const token = response.data.access_token
  localStorage.setItem('access_token', token)
  return token
}

export async function register(
  email: string,
  password: string,
  name: string
): Promise<User> {
  const response = await api.post('/auth/register', { email, password, name })
  return response.data
}

export async function getMe(): Promise<User> {
  const response = await api.get('/auth/me')
  return response.data
}

export function logout(): void {
  localStorage.removeItem('access_token')
  window.location.href = '/login'
}

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as authApi from '../api/auth'

export function useUser() {
  const token = localStorage.getItem('access_token')
  return useQuery({
    queryKey: ['user'],
    queryFn: authApi.getMe,
    enabled: !!token,
    retry: false,
  })
}

export function useLogin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      authApi.login(email, password),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user'] })
    },
  })
}

export function useRegister() {
  return useMutation({
    mutationFn: ({
      email,
      password,
      name,
    }: {
      email: string
      password: string
      name: string
    }) => authApi.register(email, password, name),
  })
}

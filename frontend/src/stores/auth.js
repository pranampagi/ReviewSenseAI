/**
 * Pinia auth store — JWT token, user profile, login/register/logout.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api/axios'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null)
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const isLoggedIn = computed(() => !!token.value)

  async function login(email, password) {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)
    const { data } = await api.post('/auth/login', formData)
    token.value = data.access_token
    localStorage.setItem('token', data.access_token)
    const me = await api.get('/auth/me')
    user.value = me.data
    localStorage.setItem('user', JSON.stringify(me.data))
  }

  async function register(email, password, full_name) {
    const { data } = await api.post('/auth/register', { email, password, full_name })
    token.value = data.access_token
    localStorage.setItem('token', data.access_token)
    const me = await api.get('/auth/me')
    user.value = me.data
    localStorage.setItem('user', JSON.stringify(me.data))
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return { token, user, isLoggedIn, login, register, logout }
})

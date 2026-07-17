/**
 * Auth store — minimal stub for Commit #17 (axios interceptors).
 * Expanded with login/register in Commit #18.
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null)

  async function logout() {
    token.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return { token, logout }
})

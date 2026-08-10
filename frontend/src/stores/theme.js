import { defineStore } from 'pinia'
import { ref, computed, watchEffect } from 'vue'

const STORAGE_KEY = 'reviewsense-theme-preference'

function getStoredPreference() {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (['system', 'light', 'dark'].includes(stored)) return stored
  
  // Migrate old values if they exist, else default to system
  if (localStorage.getItem('reviewsense-theme') === 'dark') return 'dark'
  if (localStorage.getItem('reviewsense-theme') === 'light') return 'light'
  
  return 'system'
}

export const useThemeStore = defineStore('theme', () => {
  const preference = ref(getStoredPreference())
  
  const systemIsDark = ref(window.matchMedia('(prefers-color-scheme: dark)').matches)
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    systemIsDark.value = e.matches
  })

  const theme = computed(() => {
    if (preference.value === 'system') {
      return systemIsDark.value ? 'dark' : 'light'
    }
    return preference.value
  })

  watchEffect(() => {
    document.documentElement.dataset.theme = theme.value
    document.documentElement.dataset.bsTheme = theme.value
  })

  function cycleTheme() {
    const next = {
      'system': 'light',
      'light': 'dark',
      'dark': 'system'
    }
    setPreference(next[preference.value])
  }

  function setPreference(newPref) {
    preference.value = newPref
    localStorage.setItem(STORAGE_KEY, newPref)
    localStorage.removeItem('reviewsense-theme') // Clean up old key
  }

  return { preference, theme, cycleTheme, setPreference }
})

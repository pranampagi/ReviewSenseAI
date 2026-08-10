<script setup>
import { computed } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'

const auth = useAuthStore()
const themeStore = useThemeStore()
const router = useRouter()

const themeLabel = computed(() => {
  if (themeStore.preference === 'system') return 'System theme'
  return themeStore.preference === 'dark' ? 'Dark mode' : 'Light mode'
})

function onLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="app-shell container-fluid px-3 px-md-4 py-3 py-md-4">
    <nav class="navbar navbar-expand-lg glass-navbar rounded-pill mb-4 px-3 px-lg-4 py-2 sticky-top">
      <RouterLink class="navbar-brand mb-0 h1 text-decoration-none me-auto" to="/dashboard">
        <span class="brand-gradient">ReviewSense AI</span>
      </RouterLink>

      <div class="d-flex align-items-center gap-2 order-lg-last ms-2">
        <button
          type="button"
          class="btn btn-theme-toggle btn-sm rounded-pill px-3"
          :aria-label="themeLabel"
          :title="themeLabel"
          @click="themeStore.cycleTheme()"
        >
          <span v-if="themeStore.preference === 'system'" aria-hidden="true">💻</span>
          <span v-else-if="themeStore.preference === 'dark'" aria-hidden="true">🌙</span>
          <span v-else aria-hidden="true">☀️</span>
          <span class="d-none d-sm-inline ms-1">{{ themeStore.preference === 'system' ? 'System' : (themeStore.preference === 'dark' ? 'Dark' : 'Light') }}</span>
        </button>

        <button
          class="navbar-toggler border-0 shadow-none"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#mainNavbar"
          aria-controls="mainNavbar"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span class="navbar-toggler-icon" />
        </button>
      </div>

      <div id="mainNavbar" class="collapse navbar-collapse">
        <div v-if="auth.isLoggedIn" class="navbar-nav ms-lg-auto align-items-lg-center gap-lg-3 py-3 py-lg-0">
          <RouterLink class="nav-link nav-link-premium" to="/dashboard">Dashboard</RouterLink>
          <RouterLink class="nav-link nav-link-premium" to="/products">Products</RouterLink>
          <RouterLink class="nav-link nav-link-premium" to="/analytics">Analytics</RouterLink>
          <button
            type="button"
            class="btn btn-premium-danger btn-sm rounded-pill px-3 mt-2 mt-lg-0 ms-lg-2"
            @click="onLogout"
          >
            Logout
          </button>
        </div>

        <div v-else class="navbar-nav ms-lg-auto align-items-lg-center gap-lg-3 py-3 py-lg-0">
          <RouterLink class="nav-link nav-link-premium" to="/login">Sign in</RouterLink>
          <RouterLink class="btn btn-premium btn-sm rounded-pill px-3 mt-2 mt-lg-0" to="/register">
            Register
          </RouterLink>
        </div>
      </div>
    </nav>

    <RouterView />
  </div>
</template>

<style scoped>
.brand-gradient {
  background: var(--accent-gradient);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.btn-theme-toggle {
  background: var(--surface-glass);
  border: 1px solid var(--surface-glass-border);
  color: var(--text-main);
  font-weight: 500;
  transition: all 0.2s ease;
}

.btn-theme-toggle:hover {
  background: var(--surface-hover);
  color: var(--text-main);
}
</style>

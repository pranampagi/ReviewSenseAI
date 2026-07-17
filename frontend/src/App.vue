<script setup>
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

function onLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="container py-4">
    <nav class="navbar navbar-expand-lg glass-navbar rounded-pill mb-4 px-4 py-3 sticky-top mt-3 mx-2">
      <RouterLink class="navbar-brand mb-0 h1 text-decoration-none" to="/dashboard">
        <span style="background: var(--accent-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">ReviewSense AI</span>
      </RouterLink>

      <div v-if="auth.isLoggedIn" class="navbar-nav ms-auto flex-row gap-3 align-items-center">
        <RouterLink class="nav-link nav-link-premium" to="/dashboard">Dashboard</RouterLink>
        <RouterLink class="nav-link nav-link-premium" to="/products">Products</RouterLink>
        <RouterLink class="nav-link nav-link-premium" to="/analytics">Analytics</RouterLink>
        <button type="button" class="btn btn-outline-danger btn-sm ms-3 rounded-pill px-3" @click="onLogout">
          Logout
        </button>
      </div>

      <div v-else class="navbar-nav ms-auto flex-row gap-3 align-items-center">
        <RouterLink class="nav-link nav-link-premium" to="/login">Sign in</RouterLink>
        <RouterLink class="btn btn-premium btn-sm rounded-pill px-3" to="/register">Register</RouterLink>
      </div>
    </nav>

    <RouterView />
  </div>
</template>

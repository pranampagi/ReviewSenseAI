<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    router.push('/dashboard')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Login failed. Check your credentials.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="row justify-content-center animate-enter mt-5">
    <div class="col-md-5">
      <div class="glass-panel border-0">
        <div class="card-body p-5">
          <h2 class="card-title mb-4 text-center">Sign in</h2>

          <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

          <form @submit.prevent="onSubmit">
            <div class="mb-3">
              <label class="form-label" for="email">Email</label>
              <input
                id="email"
                v-model="email"
                type="email"
                class="form-control form-control-premium"
                required
                autocomplete="email"
              />
            </div>
            <div class="mb-3">
              <label class="form-label" for="password">Password</label>
              <input
                id="password"
                v-model="password"
                type="password"
                class="form-control form-control-premium"
                required
                autocomplete="current-password"
              />
            </div>
            <button type="submit" class="btn btn-premium w-100 mt-3" :disabled="loading">
              {{ loading ? 'Signing in…' : 'Sign in' }}
            </button>
          </form>

          <p class="text-center text-muted mt-3 mb-0">
            No account?
            <RouterLink to="/register">Register</RouterLink>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

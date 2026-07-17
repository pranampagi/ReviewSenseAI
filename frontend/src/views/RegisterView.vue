<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const fullName = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const loading = ref(false)

async function onSubmit() {
  error.value = ''
  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match.'
    return
  }
  if (password.value.length < 8) {
    error.value = 'Password must be at least 8 characters.'
    return
  }

  loading.value = true
  try {
    await auth.register(email.value, password.value, fullName.value)
    router.push('/dashboard')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Registration failed.'
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
          <h2 class="card-title mb-4 text-center">Create account</h2>

          <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

          <form @submit.prevent="onSubmit">
            <div class="mb-3">
              <label class="form-label" for="fullName">Full name</label>
              <input
                id="fullName"
                v-model="fullName"
                type="text"
                class="form-control form-control-premium"
                autocomplete="name"
              />
            </div>
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
                minlength="8"
                autocomplete="new-password"
              />
            </div>
            <div class="mb-3">
              <label class="form-label" for="confirmPassword">Confirm password</label>
              <input
                id="confirmPassword"
                v-model="confirmPassword"
                type="password"
                class="form-control form-control-premium"
                required
                autocomplete="new-password"
              />
            </div>
            <button type="submit" class="btn btn-premium w-100 mt-3" :disabled="loading">
              {{ loading ? 'Creating account…' : 'Register' }}
            </button>
          </form>

          <p class="text-center text-muted mt-3 mb-0">
            Already have an account?
            <RouterLink to="/login">Sign in</RouterLink>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

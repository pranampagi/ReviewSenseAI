<script setup>
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<template>
  <div class="glass-panel border-0 animate-enter mt-4">
    <div class="card-body p-5">
      <h2 class="card-title">Dashboard</h2>
      <p class="text-muted mb-0">
        Welcome{{ auth.user?.full_name ? `, ${auth.user.full_name}` : '' }}.
        Product and analytics views are wired in upcoming updates.
      </p>
    </div>
  </div>
</template>

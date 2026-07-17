<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <div class="card shadow-sm">
    <div class="card-body p-4">
      <h2 class="card-title">Product detail</h2>
      <p class="text-muted mb-0">Product ID: {{ route.params.id }}.</p>
    </div>
  </div>
</template>

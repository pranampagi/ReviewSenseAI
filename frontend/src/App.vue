<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="container py-4">
    <nav class="navbar navbar-expand-lg navbar-light bg-light rounded mb-4 px-3">
      <span class="navbar-brand mb-0 h1">ReviewSense AI</span>
      <div class="navbar-nav ms-auto">
        <RouterLink class="nav-link" to="/">Home</RouterLink>
        <RouterLink class="nav-link" to="/about">About</RouterLink>
      </div>
    </nav>
    <RouterView />
  </div>
</template>

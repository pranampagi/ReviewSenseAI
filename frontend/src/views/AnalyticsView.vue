<script setup>
import { onMounted, ref, watch } from 'vue'
import api from '@/api/axios'
import SentimentChart from '@/components/SentimentChart.vue'
import { useProductsStore } from '@/stores/products'

const productsStore = useProductsStore()

const productId = ref('')
const startDate = ref('')
const endDate = ref('')
const trendData = ref([])
const loading = ref(false)
const error = ref('')

async function loadProducts() {
  await productsStore.fetchProducts(1, '')
  if (!productId.value && productsStore.products.length) {
    productId.value = productsStore.products[0].id
  }
}

async function loadTrend() {
  if (!productId.value) {
    trendData.value = []
    return
  }
  loading.value = true
  error.value = ''
  try {
    const params = { product_id: productId.value }
    if (startDate.value) params.start = `${startDate.value}T00:00:00Z`
    if (endDate.value) params.end = `${endDate.value}T23:59:59Z`
    const { data } = await api.get('/analyze/sentiment-trend', { params })
    trendData.value = data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Could not load sentiment trend.'
    trendData.value = []
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadProducts()
  await loadTrend()
})

watch([productId, startDate, endDate], () => {
  loadTrend()
})
</script>

<template>
  <div class="animate-enter">
    <h1 class="h3 mb-4">Analytics</h1>

    <div class="card glass-panel border-0 mb-4">
      <div class="card-body">
        <div class="row g-3 align-items-end">
          <div class="col-md-4">
            <label class="form-label" for="analyticsProduct">Product</label>
            <select id="analyticsProduct" v-model="productId" class="form-select form-control-premium">
              <option v-if="!productsStore.products.length" value="">No products</option>
              <option v-for="product in productsStore.products" :key="product.id" :value="product.id">
                {{ product.name }}
              </option>
            </select>
          </div>
          <div class="col-md-3">
            <label class="form-label" for="startDate">Start date</label>
            <input id="startDate" v-model="startDate" type="date" class="form-control form-control-premium" />
          </div>
          <div class="col-md-3">
            <label class="form-label" for="endDate">End date</label>
            <input id="endDate" v-model="endDate" type="date" class="form-control form-control-premium" />
          </div>
          <div class="col-md-2">
            <button type="button" class="btn btn-premium w-100" @click="loadTrend">
              Refresh
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div class="card glass-panel border-0">
      <div class="card-body">
        <h5 class="card-title mb-3">Sentiment trend</h5>
        <div v-if="loading" class="text-muted py-5 text-center">Loading chart…</div>
        <SentimentChart v-else :data="trendData" />
      </div>
    </div>
  </div>
</template>

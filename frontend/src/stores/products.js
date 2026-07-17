/**
 * Pinia store for product catalog — list, detail, create, delete.
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api/axios'

export const useProductsStore = defineStore('products', () => {
  const products = ref([])
  const currentProduct = ref(null)
  const loading = ref(false)
  const pagination = ref({ page: 1, pages: 1, total: 0, limit: 12 })

  async function fetchReviewCount(productId) {
    try {
      const { data } = await api.get('/reviews', {
        params: { product_id: productId, limit: 1 },
      })
      return data.total
    } catch {
      return 0
    }
  }

  async function fetchProducts(page = 1, search = '') {
    loading.value = true
    try {
      const { data } = await api.get('/products', {
        params: { page, limit: pagination.value.limit, search },
      })
      products.value = await Promise.all(
        data.items.map(async (product) => ({
          ...product,
          reviewCount: await fetchReviewCount(product.id),
        })),
      )
      pagination.value = {
        page: data.page,
        pages: data.pages,
        total: data.total,
        limit: pagination.value.limit,
      }
    } finally {
      loading.value = false
    }
  }

  async function fetchProduct(id) {
    loading.value = true
    try {
      const { data } = await api.get(`/products/${id}`)
      currentProduct.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function createProduct(payload) {
    const { data } = await api.post('/products', payload)
    return data
  }

  async function deleteProduct(id) {
    await api.delete(`/products/${id}`)
    products.value = products.value.filter((p) => p.id !== id)
    if (currentProduct.value?.id === id) {
      currentProduct.value = null
    }
  }

  return {
    products,
    currentProduct,
    loading,
    pagination,
    fetchProducts,
    fetchProduct,
    createProduct,
    deleteProduct,
  }
})

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api/axios'
import BulkUpload from '@/components/BulkUpload.vue'
import ReviewForm from '@/components/ReviewForm.vue'
import { useProductsStore } from '@/stores/products'

const route = useRoute()
const router = useRouter()
const store = useProductsStore()

const activeTab = ref('reviews')
const reviews = ref([])
const reviewsLoading = ref(false)
const reviewPagination = ref({ page: 1, pages: 1, total: 0 })
const deleteError = ref('')
const showReviewForm = ref(false)
const successToast = ref('')

const product = computed(() => store.currentProduct)
const productId = computed(() => String(route.params.id))

async function loadProduct() {
  try {
    await store.fetchProduct(route.params.id)
  } catch {
    router.push({ name: 'products' })
  }
}

async function loadReviews(page = 1) {
  reviewsLoading.value = true
  try {
    const { data } = await api.get('/reviews', {
      params: { product_id: route.params.id, page, limit: 10 },
    })
    reviews.value = await Promise.all(
      data.items.map(async (review) => {
        if (review.status !== 'complete') {
          return { ...review, analysis_result: null }
        }
        try {
          const detail = await api.get(`/reviews/${review.id}`)
          return detail.data
        } catch {
          return { ...review, analysis_result: null }
        }
      }),
    )
    reviewPagination.value = {
      page: data.page,
      pages: data.pages,
      total: data.total,
    }
  } finally {
    reviewsLoading.value = false
  }
}

async function deleteProduct() {
  if (!confirm('Delete this product and all its reviews?')) return
  deleteError.value = ''
  try {
    await store.deleteProduct(route.params.id)
    router.push({ name: 'products' })
  } catch (err) {
    deleteError.value = err.response?.data?.detail || 'Could not delete product.'
  }
}

function changeReviewPage(page) {
  if (page < 1 || page > reviewPagination.value.pages) return
  loadReviews(page)
}

function sentimentClass(sentiment) {
  return sentiment === 'POSITIVE' ? 'sentiment-badge-positive' : 'sentiment-badge-negative'
}

function onReviewSubmitted() {
  successToast.value = 'Review submitted. Analysis may take a few seconds.'
  loadReviews(1)
  setTimeout(() => {
    successToast.value = ''
  }, 4000)
}

function onUploadComplete() {
  successToast.value = 'Bulk upload finished. Refreshing reviews…'
  loadReviews(1)
  setTimeout(() => {
    successToast.value = ''
  }, 4000)
}

onMounted(async () => {
  await loadProduct()
  await loadReviews(1)
})

watch(
  () => route.params.id,
  async () => {
    await loadProduct()
    await loadReviews(1)
  },
)
</script>

<template>
  <div v-if="store.loading && !product" class="text-center py-5 text-muted">Loading…</div>

  <div v-else-if="product">
    <div class="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-4">
      <div>
        <h1 class="h3 mb-1">{{ product.name }}</h1>
        <p class="text-muted mb-0">{{ product.category || 'Uncategorized' }}</p>
        <p v-if="product.description" class="mt-2 mb-0">{{ product.description }}</p>
      </div>
      <button type="button" class="btn btn-premium-danger shadow-sm px-3 py-1" style="border-radius: 8px;" @click="deleteProduct">
        Delete product
      </button>
    </div>

    <div v-if="deleteError" class="alert alert-danger">{{ deleteError }}</div>
    <div v-if="successToast" class="alert alert-success">{{ successToast }}</div>

    <ul class="nav nav-pills-premium mb-4">
      <li class="nav-item">
        <button
          type="button"
          class="nav-link"
          :class="{ active: activeTab === 'reviews' }"
          @click="activeTab = 'reviews'"
        >
          Reviews
        </button>
      </li>
      <li class="nav-item">
        <button
          type="button"
          class="nav-link"
          :class="{ active: activeTab === 'analytics' }"
          @click="activeTab = 'analytics'"
        >
          Analytics
        </button>
      </li>
    </ul>

    <div v-show="activeTab === 'reviews'">
      <div class="d-flex flex-wrap gap-2 mb-3">
        <button type="button" class="btn btn-premium px-3 py-1" @click="showReviewForm = true">
          Add review
        </button>
      </div>

      <div class="mb-4">
        <BulkUpload :product-id="productId" @upload-complete="onUploadComplete" />
      </div>

      <div v-if="reviewsLoading" class="text-muted py-3">Loading reviews…</div>
      <div v-else-if="reviews.length === 0" class="alert alert-light border">
        No reviews for this product yet.
      </div>
      <div v-else class="vstack gap-3">
        <div v-for="review in reviews" :key="review.id" class="card glass-panel border-0 review-card mb-3">
          <div class="card-body">
            <div class="d-flex flex-wrap justify-content-between align-items-start gap-2 mb-2">
              <div>
                <span class="badge bg-light text-dark shadow-sm border me-2">{{ review.rating }}★</span>
                <span class="text-muted small">{{ review.author || 'Anonymous' }}</span>
              </div>
              <div class="d-flex gap-2 flex-wrap">
                <span
                  v-if="review.analysis_result?.sentiment"
                  class="badge"
                  :class="sentimentClass(review.analysis_result.sentiment)"
                >
                  {{ review.analysis_result.sentiment }}
                </span>
                <span v-if="review.analysis_result?.is_fake" class="badge fake-alert-badge">
                  Likely fake
                </span>
                <span v-else-if="review.status === 'pending'" class="badge bg-warning text-dark">
                  Analysing…
                </span>
              </div>
            </div>
            <p class="mb-0">{{ review.body }}</p>
          </div>
        </div>
      </div>

      <nav v-if="reviewPagination.pages > 1" class="mt-4" aria-label="Review pagination">
        <ul class="pagination pagination-premium justify-content-center mb-0">
          <li class="page-item" :class="{ disabled: reviewPagination.page <= 1 }">
            <button
              type="button"
              class="page-link"
              @click="changeReviewPage(reviewPagination.page - 1)"
            >
              Previous
            </button>
          </li>
          <li
            v-for="page in reviewPagination.pages"
            :key="page"
            class="page-item"
            :class="{ active: page === reviewPagination.page }"
          >
            <button type="button" class="page-link" @click="changeReviewPage(page)">
              {{ page }}
            </button>
          </li>
          <li
            class="page-item"
            :class="{ disabled: reviewPagination.page >= reviewPagination.pages }"
          >
            <button
              type="button"
              class="page-link"
              @click="changeReviewPage(reviewPagination.page + 1)"
            >
              Next
            </button>
          </li>
        </ul>
      </nav>
    </div>

    <div v-show="activeTab === 'analytics'" class="card glass-panel border-0">
      <div class="card-body p-4 text-muted">
        Aspect radar and sentiment charts.
      </div>
    </div>

    <ReviewForm
      v-model:show="showReviewForm"
      :product-id="productId"
      @review-submitted="onReviewSubmitted"
    />
  </div>
</template>

<style scoped>
.review-card {
  transition: box-shadow 0.2s;
}
.review-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
.sentiment-badge-positive {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}
.sentiment-badge-negative {
  background: linear-gradient(135deg, #f43f5e 0%, #e11d48 100%);
  color: white;
}
.fake-alert-badge {
  background: linear-gradient(135deg, #f97316 0%, #ef4444 100%);
  color: white;
}
</style>

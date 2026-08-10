<script setup>
/**
 * Paginated table of reviews flagged as likely fake (GET /analyze/fake-alerts).
 */
import { onMounted, ref, watch } from 'vue'
import api from '@/api/axios'
import ReviewDetailModal from '@/components/ReviewDetailModal.vue'

const props = defineProps({
  productId: { type: String, default: '' },
})

const items = ref([])
const pagination = ref({ page: 1, pages: 1, total: 0 })
const loading = ref(false)
const error = ref('')
const selectedReviewId = ref('')
const showDetailModal = ref(false)

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString()
}

function fakePercent(value) {
  if (value == null) return 0
  return Math.min(100, Math.round(value * 100))
}

async function loadAlerts(page = 1) {
  loading.value = true
  error.value = ''
  try {
    const params = { page, limit: 10 }
    if (props.productId) params.product_id = props.productId
    const { data } = await api.get('/analyze/fake-alerts', { params })
    items.value = data.items
    pagination.value = {
      page: data.page,
      pages: data.pages,
      total: data.total,
    }
  } catch (err) {
    error.value = err.response?.data?.detail || 'Could not load fake alerts.'
    items.value = []
  } finally {
    loading.value = false
  }
}

function changePage(page) {
  if (page < 1 || page > pagination.value.pages) return
  loadAlerts(page)
}

function openReview(reviewId) {
  selectedReviewId.value = reviewId
  showDetailModal.value = true
}

onMounted(() => {
  loadAlerts(1)
})

watch(
  () => props.productId,
  () => {
    loadAlerts(1)
  },
)
</script>

<template>
  <div>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <div v-if="loading" class="text-muted py-4 text-center">Loading fake alerts…</div>

    <div v-else-if="items.length === 0" class="text-muted py-4 text-center">
      No reviews flagged as likely fake.
    </div>

    <div v-else class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead>
          <tr>
            <th scope="col">Review excerpt</th>
            <th v-if="!productId" scope="col">Product</th>
            <th scope="col" style="min-width: 160px">Fake probability</th>
            <th scope="col">Date</th>
            <th scope="col">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.review_id">
            <td class="text-break">{{ item.body_excerpt }}</td>
            <td v-if="!productId">{{ item.product_name }}</td>
            <td>
              <div class="d-flex align-items-center gap-2">
                <div class="progress flex-grow-1" style="height: 8px">
                  <div
                    class="progress-bar bg-danger"
                    role="progressbar"
                    :style="{ width: `${fakePercent(item.fake_prob)}%` }"
                    :aria-valuenow="fakePercent(item.fake_prob)"
                    aria-valuemin="0"
                    aria-valuemax="100"
                  />
                </div>
                <span class="small text-nowrap">{{ fakePercent(item.fake_prob) }}%</span>
              </div>
            </td>
            <td class="text-nowrap">{{ formatDate(item.created_at) }}</td>
            <td>
              <button
                type="button"
                class="btn btn-sm btn-outline-danger"
                @click="openReview(item.review_id)"
              >
                View full review
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <nav v-if="pagination.pages > 1" class="mt-4" aria-label="Fake alert pagination">
      <ul class="pagination pagination-premium justify-content-center mb-0">
        <li class="page-item" :class="{ disabled: pagination.page <= 1 }">
          <button type="button" class="page-link" @click="changePage(pagination.page - 1)">
            Previous
          </button>
        </li>
        <li
          v-for="page in pagination.pages"
          :key="page"
          class="page-item"
          :class="{ active: page === pagination.page }"
        >
          <button type="button" class="page-link" @click="changePage(page)">
            {{ page }}
          </button>
        </li>
        <li class="page-item" :class="{ disabled: pagination.page >= pagination.pages }">
          <button type="button" class="page-link" @click="changePage(pagination.page + 1)">
            Next
          </button>
        </li>
      </ul>
    </nav>

    <ReviewDetailModal v-model:show="showDetailModal" :review-id="selectedReviewId" />
  </div>
</template>

<script setup>
/**
 * Modal showing a single review and its ML analysis (GET /reviews/{id}).
 * Commit #24 adds polling while analysis is pending.
 */
import { ref, watch } from 'vue'
import api from '@/api/axios'
import { formatDate } from '@/utils/formatters'

const props = defineProps({
  show: { type: Boolean, default: false },
  reviewId: { type: String, default: '' },
})

const emit = defineEmits(['update:show'])

const review = ref(null)
const loading = ref(false)
const error = ref('')

function close() {
  emit('update:show', false)
}

function formatScore(value) {
  if (value == null) return '—'
  return `${Math.round(value * 100)}%`
}

async function loadReview() {
  if (!props.reviewId) return
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get(`/reviews/${props.reviewId}`)
    review.value = data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Could not load review.'
    review.value = null
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.show, props.reviewId],
  ([open, id]) => {
    if (open && id) {
      loadReview()
    } else {
      review.value = null
      error.value = ''
    }
  },
)
</script>

<template>
  <Teleport to="body">
    <div
      v-if="show"
    class="modal fade show d-block"
    tabindex="-1"
    style="background: rgba(0, 0, 0, 0.45)"
    @click.self="close"
  >
    <div class="modal-dialog modal-lg modal-dialog-scrollable modal-dialog-centered">
      <div class="modal-content glass-panel modal-premium-bg border-0 animate-enter">
        <div class="modal-header border-0">
          <h5 class="modal-title">Review details</h5>
          <button type="button" class="btn-close" aria-label="Close" @click="close" />
        </div>
        <div class="modal-body">
          <div v-if="loading" class="text-muted py-4 text-center">Loading review…</div>
          <div v-else-if="error" class="alert alert-danger mb-0">{{ error }}</div>
          <div v-else-if="review">
            <div class="d-flex flex-wrap gap-2 mb-3 align-items-center">
              <span class="badge bg-warning text-dark rounded-pill px-3 py-1 fs-6 shadow-sm border border-warning border-opacity-50">
                {{ review.rating }} ★
              </span>
              <span class="text-muted small fw-medium ms-2">{{ review.author || 'Anonymous' }}</span>
              <span class="text-muted small">&bull; {{ formatDate(review.created_at) }}</span>
              <span v-if="review.status === 'pending'" class="badge bg-info-subtle text-info rounded-pill px-2 border border-info-subtle">
                Analysing…
              </span>
            </div>
            <p class="mb-4">{{ review.body }}</p>

            <div v-if="review.analysis_result" class="border-top pt-4">
              <h6 class="mb-4 fw-bold text-primary">Analysis Metrics</h6>
              <div class="row g-4">
                <div class="col-sm-6">
                  <div class="p-3 rounded-3 border h-100 bg-light">
                    <div class="small text-muted mb-3 text-uppercase fw-semibold" style="letter-spacing: 0.5px">Sentiment</div>
                    <div class="d-flex align-items-center gap-3">
                      <span class="badge rounded-pill px-3 py-2 text-capitalize fs-6" :class="{
                        'bg-success-subtle text-success border border-success-subtle': review.analysis_result.sentiment?.toLowerCase() === 'positive',
                        'bg-danger-subtle text-danger border border-danger-subtle': review.analysis_result.sentiment?.toLowerCase() === 'negative',
                        'bg-secondary-subtle text-secondary border border-secondary-subtle': review.analysis_result.sentiment?.toLowerCase() === 'neutral',
                        'bg-light text-body border': !['positive', 'negative', 'neutral'].includes(review.analysis_result.sentiment?.toLowerCase())
                      }">
                        {{ review.analysis_result.sentiment || 'Unknown' }}
                      </span>
                      <span class="small fw-bold text-muted">{{ formatScore(review.analysis_result.sentiment_score) }}</span>
                    </div>
                  </div>
                </div>

                <div class="col-sm-6">
                  <div class="p-3 rounded-3 border h-100" :class="review.analysis_result.is_fake ? 'border-danger bg-danger-subtle bg-opacity-25' : 'bg-light'">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                      <div class="small text-muted text-uppercase fw-semibold" style="letter-spacing: 0.5px">Fake Probability</div>
                      <span class="badge rounded-pill" :class="review.analysis_result.is_fake ? 'bg-danger' : 'bg-success-subtle text-success border border-success-subtle'">
                        {{ review.analysis_result.is_fake ? 'Flagged' : 'Authentic' }}
                      </span>
                    </div>
                    <div class="d-flex align-items-center gap-3 mt-3">
                      <div class="progress flex-grow-1" style="height: 8px;">
                        <div class="progress-bar" :class="review.analysis_result.is_fake ? 'bg-danger' : 'bg-success'" :style="{ width: formatScore(review.analysis_result.fake_prob) }"></div>
                      </div>
                      <span class="small fw-bold" :class="{'text-danger': review.analysis_result.is_fake}">{{ formatScore(review.analysis_result.fake_prob) }}</span>
                    </div>
                  </div>
                </div>

                <div class="col-12 mt-4">
                  <div class="small text-muted mb-3 text-uppercase fw-semibold" style="letter-spacing: 0.5px">Topic Relevance Scores</div>
                  <div class="row g-4">
                    <div class="col-sm-6">
                      <div class="d-flex justify-content-between small mb-1">
                        <span class="text-secondary fw-medium">Price</span>
                        <span class="fw-bold">{{ formatScore(review.analysis_result.aspect_price) }}</span>
                      </div>
                      <div class="progress" style="height: 6px;">
                        <div class="progress-bar bg-primary opacity-75" :style="{ width: formatScore(review.analysis_result.aspect_price) }"></div>
                      </div>
                    </div>
                    <div class="col-sm-6">
                      <div class="d-flex justify-content-between small mb-1">
                        <span class="text-secondary fw-medium">Quality</span>
                        <span class="fw-bold">{{ formatScore(review.analysis_result.aspect_quality) }}</span>
                      </div>
                      <div class="progress" style="height: 6px;">
                        <div class="progress-bar bg-info opacity-75" :style="{ width: formatScore(review.analysis_result.aspect_quality) }"></div>
                      </div>
                    </div>
                    <div class="col-sm-6">
                      <div class="d-flex justify-content-between small mb-1">
                        <span class="text-secondary fw-medium">Shipping</span>
                        <span class="fw-bold">{{ formatScore(review.analysis_result.aspect_shipping) }}</span>
                      </div>
                      <div class="progress" style="height: 6px;">
                        <div class="progress-bar bg-warning opacity-75" :style="{ width: formatScore(review.analysis_result.aspect_shipping) }"></div>
                      </div>
                    </div>
                    <div class="col-sm-6">
                      <div class="d-flex justify-content-between small mb-1">
                        <span class="text-secondary fw-medium">Service</span>
                        <span class="fw-bold">{{ formatScore(review.analysis_result.aspect_service) }}</span>
                      </div>
                      <div class="progress" style="height: 6px;">
                        <div class="progress-bar bg-success opacity-75" :style="{ width: formatScore(review.analysis_result.aspect_service) }"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="text-muted small">Analysis not available yet.</div>
          </div>
        </div>
        <div class="modal-footer border-0 p-3"></div>
      </div>
    </div>
  </div>
  </Teleport>
</template>

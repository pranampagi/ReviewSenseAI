<script setup>
/**
 * Full ML breakdown for a single review (GET /reviews/{id}).
 * Polls while status is pending; supports POST /analyze/rerun/{id}.
 */
import { computed, onUnmounted, ref, watch } from 'vue'
import api from '@/api/axios'
import { formatDate } from '@/utils/formatters'

const props = defineProps({
  show: { type: Boolean, default: false },
  reviewId: { type: String, default: '' },
})

const emit = defineEmits(['update:show', 'analysis-complete'])

const POLL_MS = 2000
const MAX_POLLS = 45

const review = ref(null)
const loading = ref(false)
const error = ref('')
const rerunning = ref(false)
const pollCount = ref(0)
const polling = ref(false)

let pollTimer = null

const isPending = computed(() => review.value?.status === 'pending')
const isFailed = computed(() => review.value?.status === 'failed')
const analysis = computed(() => review.value?.analysis_result || null)

const sentimentClass = computed(() => {
  const s = analysis.value?.sentiment?.toUpperCase?.() || analysis.value?.sentiment || ''
  if (s === 'POSITIVE') return 'sentiment-badge-positive'
  if (s === 'NEGATIVE') return 'sentiment-badge-negative'
  return 'badge-rating'
})

function formatScore(value) {
  if (value == null) return '—'
  return `${Math.round(value * 100)}%`
}

function scoreWidth(value) {
  if (value == null) return '0%'
  return `${Math.min(100, Math.round(value * 100))}%`
}

function clearPoll() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  polling.value = false
}

function close() {
  clearPoll()
  emit('update:show', false)
}

async function fetchReview({ silent = false } = {}) {
  if (!props.reviewId) return null
  if (!silent) {
    loading.value = true
    error.value = ''
  }
  try {
    const { data } = await api.get(`/reviews/${props.reviewId}`)
    review.value = data
    return data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Could not load review.'
    if (!silent) review.value = null
    return null
  } finally {
    if (!silent) loading.value = false
  }
}

function startPolling() {
  clearPoll()
  pollCount.value = 0
  polling.value = true
  pollTimer = setInterval(async () => {
    pollCount.value += 1
    const data = await fetchReview({ silent: true })
    if (!data) {
      clearPoll()
      return
    }
    if (data.status === 'complete' || data.status === 'failed') {
      clearPoll()
      if (data.status === 'complete') {
        emit('analysis-complete', data)
      }
      return
    }
    if (pollCount.value >= MAX_POLLS) {
      clearPoll()
      error.value = 'Analysis is taking longer than expected. Try re-running or refresh later.'
    }
  }, POLL_MS)
}

async function loadAndMaybePoll() {
  clearPoll()
  const data = await fetchReview()
  if (data?.status === 'pending') {
    startPolling()
  }
}

async function rerunAnalysis() {
  if (!props.reviewId || rerunning.value) return
  rerunning.value = true
  error.value = ''
  try {
    await api.post(`/analyze/rerun/${props.reviewId}`)
    if (review.value) {
      review.value = { ...review.value, status: 'pending', analysis_result: null }
    }
    startPolling()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Could not re-queue analysis.'
  } finally {
    rerunning.value = false
  }
}

watch(
  () => [props.show, props.reviewId],
  ([open, id]) => {
    if (open && id) {
      loadAndMaybePoll()
    } else {
      clearPoll()
      review.value = null
      error.value = ''
      pollCount.value = 0
    }
  },
)

onUnmounted(clearPoll)
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
            <div v-else-if="error && !review" class="alert alert-danger mb-0">{{ error }}</div>

            <div v-else-if="review">
              <div v-if="error" class="alert alert-warning">{{ error }}</div>

              <div class="d-flex flex-wrap gap-2 mb-3 align-items-center">
                <span class="badge badge-rating rounded-pill px-3 py-1">{{ review.rating }} ★</span>
                <span class="text-muted small fw-medium">{{ review.author || 'Anonymous' }}</span>
                <span class="text-muted small">• {{ formatDate(review.created_at) }}</span>
                <span v-if="isPending" class="badge badge-analysis-pending">
                  Analysing{{ polling ? '…' : '' }}
                </span>
                <span v-else-if="isFailed" class="badge badge-flagged">Failed</span>
              </div>

              <p class="mb-4">{{ review.body }}</p>

              <div v-if="isPending" class="border-top pt-4">
                <div class="d-flex align-items-center gap-3 text-muted">
                  <div class="spinner-border spinner-border-sm text-primary" role="status">
                    <span class="visually-hidden">Analysing</span>
                  </div>
                  <div>
                    <div class="fw-medium text-body">Running ML pipeline</div>
                    <div class="small">
                      Sentiment, fake detection, and aspect scores update automatically.
                    </div>
                  </div>
                </div>
              </div>

              <div v-else-if="analysis" class="border-top pt-4">
                <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-4">
                  <h6 class="mb-0 fw-bold text-primary">Analysis metrics</h6>
                  <span v-if="analysis.completed_at" class="small text-muted">
                    Completed {{ formatDate(analysis.completed_at) }}
                  </span>
                </div>

                <div class="row g-4">
                  <div class="col-sm-6">
                    <div class="p-3 rounded-3 border h-100 metric-card">
                      <div class="small text-muted mb-3 text-uppercase fw-semibold metric-label">
                        Sentiment
                      </div>
                      <div class="d-flex align-items-center gap-3">
                        <span class="badge rounded-pill px-3 py-2 text-uppercase" :class="sentimentClass">
                          {{ analysis.sentiment || 'Unknown' }}
                        </span>
                        <span class="small fw-bold text-muted">
                          {{ formatScore(analysis.sentiment_score) }}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div class="col-sm-6">
                    <div
                      class="p-3 rounded-3 border h-100 metric-card"
                      :class="analysis.is_fake ? 'border-danger' : ''"
                    >
                      <div class="d-flex justify-content-between align-items-center mb-2">
                        <div class="small text-muted text-uppercase fw-semibold metric-label">
                          Fake probability
                        </div>
                        <span
                          class="badge rounded-pill"
                          :class="analysis.is_fake ? 'badge-flagged' : 'badge-authentic'"
                        >
                          {{ analysis.is_fake ? 'Flagged' : 'Authentic' }}
                        </span>
                      </div>
                      <div class="d-flex align-items-center gap-3 mt-3">
                        <div class="progress flex-grow-1" style="height: 8px">
                          <div
                            class="progress-bar"
                            :class="analysis.is_fake ? 'bg-danger' : 'bg-success'"
                            :style="{ width: scoreWidth(analysis.fake_prob) }"
                          />
                        </div>
                        <span
                          class="small fw-bold"
                          :class="{ 'text-danger': analysis.is_fake }"
                        >
                          {{ formatScore(analysis.fake_prob) }}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div class="col-12">
                    <div class="small text-muted mb-3 text-uppercase fw-semibold metric-label">
                      Aspect scores
                    </div>
                    <div class="row g-3">
                      <div
                        v-for="aspect in [
                          { key: 'aspect_price', label: 'Price', bar: 'bg-primary' },
                          { key: 'aspect_quality', label: 'Quality', bar: 'bg-info' },
                          { key: 'aspect_shipping', label: 'Shipping', bar: 'bg-warning' },
                          { key: 'aspect_service', label: 'Service', bar: 'bg-success' },
                        ]"
                        :key="aspect.key"
                        class="col-sm-6"
                      >
                        <div class="d-flex justify-content-between small mb-1">
                          <span class="text-secondary fw-medium">{{ aspect.label }}</span>
                          <span class="fw-bold">{{ formatScore(analysis[aspect.key]) }}</span>
                        </div>
                        <div class="progress" style="height: 6px">
                          <div
                            class="progress-bar opacity-75"
                            :class="aspect.bar"
                            :style="{ width: scoreWidth(analysis[aspect.key]) }"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div v-else-if="isFailed" class="border-top pt-4">
                <div class="alert alert-danger mb-0">
                  Analysis failed. Re-run the pipeline to try again.
                </div>
              </div>

              <div v-else class="border-top pt-4 text-muted small">
                Analysis not available yet.
              </div>
            </div>
          </div>

          <div class="modal-footer border-0 gap-2">
            <button
              v-if="review && !isPending"
              type="button"
              class="btn btn-outline-primary btn-sm rounded-pill px-3"
              :disabled="rerunning"
              @click="rerunAnalysis"
            >
              {{ rerunning ? 'Queuing…' : 'Re-run analysis' }}
            </button>
            <button type="button" class="btn btn-outline-secondary btn-sm rounded-pill px-3" @click="close">
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.metric-label {
  letter-spacing: 0.5px;
}

.metric-card {
  background: var(--surface-muted);
  border-color: var(--surface-glass-border) !important;
}
</style>

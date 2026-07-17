<script setup>
/**
 * Modal form to submit a single product review (author, rating, body).
 * Emits ``review-submitted`` after a successful POST /reviews.
 */
import { computed, ref, watch } from 'vue'
import api from '@/api/axios'

const props = defineProps({
  productId: { type: String, required: true },
  show: { type: Boolean, default: false },
})

const emit = defineEmits(['update:show', 'review-submitted'])

const author = ref('')
const rating = ref(0)
const body = ref('')
const error = ref('')
const loading = ref(false)
const toast = ref('')

const bodyValid = computed(() => body.value.trim().length >= 20)
const canSubmit = computed(() => bodyValid.value && rating.value > 0 && !loading.value)

watch(
  () => props.show,
  (open) => {
    if (open) {
      author.value = ''
      rating.value = 0
      body.value = ''
      error.value = ''
      toast.value = ''
    }
  },
)

function close() {
  emit('update:show', false)
}

async function onSubmit() {
  if (rating.value === 0) {
    error.value = 'Please select a star rating.'
    return
  }
  if (!bodyValid.value) {
    error.value = 'Review text must be at least 20 characters.'
    return
  }
  error.value = ''
  loading.value = true
  try {
    await api.post('/reviews', {
      product_id: props.productId,
      author: author.value.trim() || null,
      rating: rating.value,
      body: body.value.trim(),
    })
    emit('review-submitted')
    close()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Could not submit review.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div
    v-if="show"
    class="modal fade show d-block"
    tabindex="-1"
    style="background: rgba(0, 0, 0, 0.45)"
  >
    <div class="modal-dialog">
      <div class="modal-content glass-panel border-0 animate-enter">
        <div class="modal-header border-0">
          <h5 class="modal-title font-weight-bold">Add review</h5>
          <button type="button" class="btn-close" aria-label="Close" @click="close" />
        </div>
        <form @submit.prevent="onSubmit">
          <div class="modal-body">
            <div v-if="toast" class="alert alert-success">{{ toast }}</div>
            <div v-if="error" class="alert alert-danger">{{ error }}</div>

            <div class="mb-3">
              <label class="form-label" for="reviewAuthor">Author (optional)</label>
              <input id="reviewAuthor" v-model="author" type="text" class="form-control form-control-premium" />
            </div>

            <div class="mb-3">
              <label class="form-label">Rating</label>
              <div class="d-flex gap-2">
                <button
                  v-for="star in 5"
                  :key="star"
                  type="button"
                  class="star-btn"
                  :class="{ 'active': star <= rating }"
                  @click="rating = star"
                  :title="`Rate ${star} stars`"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="star-icon">
                    <path fill-rule="evenodd" d="M10.788 3.21c.448-1.077 1.976-1.077 2.424 0l2.082 5.007 5.404.433c1.164.093 1.636 1.545.749 2.305l-4.117 3.527 1.257 5.273c.271 1.136-.964 2.033-1.96 1.425L12 18.354 7.373 21.18c-.996.608-2.231-.29-1.96-1.425l1.257-5.273-4.117-3.527c-.887-.76-.415-2.212.749-2.305l5.404-.433 2.082-5.006z" clip-rule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>

            <div class="mb-3">
              <label class="form-label" for="reviewBody">Review</label>
              <textarea
                id="reviewBody"
                v-model="body"
                class="form-control form-control-premium"
                rows="4"
                minlength="20"
                required
                placeholder="Write at least 20 characters…"
              />
              <div class="form-text">{{ body.trim().length }} / 20 min</div>
            </div>
          </div>
          <div class="modal-footer border-0">
            <button type="button" class="btn btn-secondary" @click="close">Cancel</button>
            <button type="submit" class="btn btn-premium px-4" :disabled="!canSubmit">
              {{ loading ? 'Submitting…' : 'Submit review' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.star-btn {
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  outline: none;
}
.star-btn:hover {
  transform: scale(1.2);
}
.star-icon {
  width: 32px;
  height: 32px;
  color: #cbd5e1;
  transition: all 0.3s ease;
}
.star-btn.active .star-icon {
  color: #f59e0b;
  filter: drop-shadow(0 2px 4px rgba(245, 158, 11, 0.4));
}
</style>

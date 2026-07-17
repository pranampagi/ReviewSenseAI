<script setup>
/**
 * Drag-and-drop CSV bulk upload with job-status polling and progress bar.
 * CSV columns required: author, rating, body. Max file size 10MB.
 */
import { computed, onUnmounted, ref } from 'vue'
import api from '@/api/axios'

const props = defineProps({
  productId: { type: String, required: true },
})

const emit = defineEmits(['upload-complete'])

const MAX_BYTES = 10 * 1024 * 1024
const POLL_MS = 2000

const dragOver = ref(false)
const file = ref(null)
const error = ref('')
const summary = ref('')
const uploading = ref(false)
const polling = ref(false)
const progress = ref({ accepted: 0, total: 0 })

let pollTimer = null

const percent = computed(() => {
  if (!progress.value.total) return 0
  return Math.min(100, Math.round((progress.value.accepted / progress.value.total) * 100))
})

function clearPoll() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  polling.value = false
}

onUnmounted(clearPoll)

function validateFile(selected) {
  if (!selected) return 'No file selected.'
  if (!selected.name.toLowerCase().endsWith('.csv')) return 'Only .csv files are allowed.'
  if (selected.size > MAX_BYTES) return 'File must be 10MB or smaller.'
  return ''
}

function onFilePick(event) {
  const selected = event.target.files?.[0]
  error.value = ''
  summary.value = ''
  const msg = validateFile(selected)
  if (msg) {
    error.value = msg
    file.value = null
    return
  }
  file.value = selected
}

function onDrop(event) {
  dragOver.value = false
  const selected = event.dataTransfer?.files?.[0]
  error.value = ''
  summary.value = ''
  const msg = validateFile(selected)
  if (msg) {
    error.value = msg
    file.value = null
    return
  }
  file.value = selected
}

async function pollJob(jobId) {
  polling.value = true
  const tick = async () => {
    try {
      const { data } = await api.get(`/reviews/bulk-jobs/${jobId}`)
      progress.value = {
        accepted: data.success_count ?? 0,
        total: data.total_rows ?? 0,
      }
      if (data.status === 'completed' || data.completed_at) {
        clearPoll()
        const errors = data.error_count ?? 0
        summary.value = `${data.success_count ?? 0} reviews imported${errors ? `, ${errors} errors` : ''}.`
        emit('upload-complete', data)
      }
    } catch (err) {
      clearPoll()
      error.value = err.response?.data?.detail || 'Could not poll upload job status.'
    }
  }
  await tick()
  if (polling.value) {
    pollTimer = setInterval(tick, POLL_MS)
  }
}

async function startUpload() {
  if (!file.value) {
    error.value = 'Choose a CSV file first.'
    return
  }
  error.value = ''
  summary.value = ''
  uploading.value = true
  progress.value = { accepted: 0, total: 0 }

  const form = new FormData()
  form.append('product_id', props.productId)
  form.append('file', file.value)

  try {
    const { data } = await api.post('/reviews/bulk-upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    progress.value = {
      accepted: data.accepted ?? 0,
      total: (data.accepted ?? 0) + (data.errors?.length ?? 0),
    }
    if (data.job_id) {
      await pollJob(data.job_id)
    } else {
      summary.value = `${data.accepted ?? 0} reviews imported.`
      emit('upload-complete', data)
    }
  } catch (err) {
    error.value = err.response?.data?.detail || 'Upload failed.'
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="card shadow-sm">
    <div class="card-body">
      <h5 class="card-title mb-3">Bulk CSV upload</h5>
      <p class="text-muted small">
        Required columns: <code>author</code>, <code>rating</code>, <code>body</code>. Max 10MB.
      </p>

      <div
        class="border border-2 rounded p-4 text-center mb-3"
        :class="dragOver ? 'border-primary bg-light' : 'border-dashed'"
        @dragover.prevent="dragOver = true"
        @dragleave.prevent="dragOver = false"
        @drop.prevent="onDrop"
      >
        <p class="mb-2">Drag &amp; drop a .csv file here</p>
        <input type="file" accept=".csv,text/csv" class="form-control" @change="onFilePick" />
        <p v-if="file" class="small text-muted mt-2 mb-0">Selected: {{ file.name }}</p>
      </div>

      <div v-if="error" class="alert alert-danger">{{ error }}</div>
      <div v-if="summary" class="alert alert-success">{{ summary }}</div>

      <div v-if="uploading || polling" class="mb-3">
        <div class="d-flex justify-content-between small mb-1">
          <span>Importing…</span>
          <span>{{ progress.accepted }} / {{ progress.total || '…' }}</span>
        </div>
        <div class="progress" role="progressbar" :aria-valuenow="percent">
          <div class="progress-bar progress-bar-striped progress-bar-animated" :style="{ width: `${percent || 10}%` }" />
        </div>
      </div>

      <button
        type="button"
        class="btn btn-primary"
        :disabled="!file || uploading || polling"
        @click="startUpload"
      >
        {{ uploading || polling ? 'Uploading…' : 'Upload CSV' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.border-dashed {
  border-style: dashed !important;
}
</style>

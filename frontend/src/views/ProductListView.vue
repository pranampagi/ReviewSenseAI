<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useProductsStore } from '@/stores/products'

const router = useRouter()
const store = useProductsStore()

const search = ref('')
const showModal = ref(false)
const formError = ref('')
const saving = ref(false)
const newProduct = ref({ name: '', category: '', description: '' })

let searchTimer = null

function loadProducts(page = 1) {
  store.fetchProducts(page, search.value.trim())
}

function onSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => loadProducts(1), 350)
}

function openModal() {
  formError.value = ''
  newProduct.value = { name: '', category: '', description: '' }
  showModal.value = true
}

async function submitProduct() {
  if (!newProduct.value.name.trim()) {
    formError.value = 'Product name is required.'
    return
  }
  saving.value = true
  formError.value = ''
  try {
    await store.createProduct({
      name: newProduct.value.name.trim(),
      category: newProduct.value.category.trim() || null,
      description: newProduct.value.description.trim() || null,
    })
    showModal.value = false
    await loadProducts(store.pagination.page)
  } catch (err) {
    formError.value = err.response?.data?.detail || 'Could not create product.'
  } finally {
    saving.value = false
  }
}

function goToProduct(id) {
  router.push({ name: 'product-detail', params: { id } })
}

function changePage(page) {
  if (page < 1 || page > store.pagination.pages) return
  loadProducts(page)
}

onMounted(() => loadProducts(1))
</script>

<template>
  <div>
    <div class="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
      <h1 class="h3 mb-0">Products</h1>
      <div class="position-relative" style="width: 100%; max-width: 280px">
        <svg
          class="position-absolute"
          style="left: 12px; top: 50%; transform: translateY(-50%); width: 18px; height: 18px; color: #94a3b8; pointer-events: none;"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          v-model="search"
          type="search"
          class="form-control form-control-premium"
          style="padding-left: 38px; width: 100%;"
          placeholder="Search name or category…"
          @input="onSearchInput"
        />
      </div>
    </div>

    <div v-if="store.loading" class="text-center py-5 text-muted">Loading products…</div>

    <div v-else-if="store.products.length === 0" class="alert alert-info">
      No products yet. Click <strong>Add Product</strong> to create your first one.
    </div>

    <div v-else class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
      <div v-for="product in store.products" :key="product.id" class="col">
        <div class="card h-100 glass-panel border-0 review-card">
          <div class="card-body d-flex flex-column">
            <h5 class="card-title">{{ product.name }}</h5>
            <p class="text-muted small mb-1">
              {{ product.category || 'Uncategorized' }}
            </p>
            <p class="small mb-3">{{ product.reviewCount }} {{ product.reviewCount === 1 ? 'review' : 'reviews' }}</p>
            <button
              type="button"
              class="btn btn-premium px-3 py-1 mt-auto align-self-start"
              style="font-size: 0.875rem;"
              @click="goToProduct(product.id)"
            >
              View Details
            </button>
          </div>
        </div>
      </div>
    </div>

    <nav v-if="store.pagination.pages > 1" class="mt-4" aria-label="Product pagination">
      <ul class="pagination pagination-premium justify-content-center mb-0">
        <li class="page-item" :class="{ disabled: store.pagination.page <= 1 }">
          <button
            type="button"
            class="page-link"
            @click="changePage(store.pagination.page - 1)"
          >
            Previous
          </button>
        </li>
        <li
          v-for="page in store.pagination.pages"
          :key="page"
          class="page-item"
          :class="{ active: page === store.pagination.page }"
        >
          <button type="button" class="page-link" @click="changePage(page)">{{ page }}</button>
        </li>
        <li
          class="page-item"
          :class="{ disabled: store.pagination.page >= store.pagination.pages }"
        >
          <button
            type="button"
            class="page-link"
            @click="changePage(store.pagination.page + 1)"
          >
            Next
          </button>
        </li>
      </ul>
    </nav>

    <button
      type="button"
      class="btn btn-premium rounded-circle position-fixed bottom-0 end-0 m-4 d-flex justify-content-center align-items-center p-0"
      style="width: 56px; height: 56px; font-size: 1.5rem; z-index: 1030"
      title="Add product"
      @click="openModal"
    >
      +
    </button>

    <div
      v-if="showModal"
      class="modal fade show d-block"
      tabindex="-1"
      style="background: rgba(0, 0, 0, 0.45)"
    >
      <div class="modal-dialog">
        <div class="modal-content glass-panel border-0 animate-enter">
          <div class="modal-header border-0">
            <h5 class="modal-title font-weight-bold">Add product</h5>
            <button type="button" class="btn-close" @click="showModal = false" />
          </div>
          <form @submit.prevent="submitProduct">
            <div class="modal-body">
              <div v-if="formError" class="alert alert-danger">{{ formError }}</div>
              <div class="mb-3">
                <label class="form-label" for="productName">Name</label>
                <input
                  id="productName"
                  v-model="newProduct.name"
                  type="text"
                  class="form-control form-control-premium"
                  required
                />
              </div>
              <div class="mb-3">
                <label class="form-label" for="productCategory">Category</label>
                <input id="productCategory" v-model="newProduct.category" type="text" class="form-control form-control-premium" />
              </div>
              <div class="mb-3">
                <label class="form-label" for="productDescription">Description</label>
                <textarea
                  id="productDescription"
                  v-model="newProduct.description"
                  class="form-control form-control-premium"
                  rows="3"
                />
              </div>
            </div>
            <div class="modal-footer border-0">
              <button type="button" class="btn btn-secondary" @click="showModal = false">
                Cancel
              </button>
              <button type="submit" class="btn btn-premium px-4" :disabled="saving">
                {{ saving ? 'Saving…' : 'Create' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.review-card {
  transition: box-shadow 0.2s;
}
.review-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
</style>

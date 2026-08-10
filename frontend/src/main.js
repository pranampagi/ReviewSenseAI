import { createApp } from 'vue'
import { createPinia } from 'pinia'
import VueApexCharts from 'vue3-apexcharts'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'

import App from './App.vue'
import router from './router'
import { useThemeStore } from './stores/theme'
import './assets/custom.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
useThemeStore(pinia)
app.use(router)
app.use(VueApexCharts)

app.mount('#app')

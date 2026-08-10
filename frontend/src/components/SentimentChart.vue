<script setup>
/**
 * Area/line chart for daily sentiment trend data from GET /analyze/sentiment-trend.
 * Expects rows: { date, avg_score, positive_count, negative_count }.
 */
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useThemeStore } from '@/stores/theme'

const props = defineProps({
  data: {
    type: Array,
    default: () => [],
  },
})

const { theme } = storeToRefs(useThemeStore())
const isDark = computed(() => theme.value === 'dark')

const chartOptions = computed(() => ({
  chart: { 
    id: 'sentiment-trend', 
    toolbar: { show: false },
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    background: 'transparent',
    foreColor: isDark.value ? '#94a3b8' : '#64748b',
  },
  theme: { mode: isDark.value ? 'dark' : 'light' },
  stroke: { curve: 'smooth', width: 3 },
  fill: {
    type: 'solid',
    opacity: 1,
  },
  plotOptions: {
    bar: { borderRadius: 4, columnWidth: '50%' }
  },
  grid: { 
    borderColor: 'var(--chart-grid)', 
    strokeDashArray: 4, 
    position: 'back' 
  },
  xaxis: {
    type: 'datetime',
    categories: props.data.map((row) => row.date),
    title: { text: 'Date' },
  },
  yaxis: [
    {
      min: 0,
      max: 1,
      title: { text: 'Avg sentiment score' },
    },
    {
      opposite: true,
      title: { text: 'Review count' },
    },
  ],
  colors: ['#4f46e5', '#10b981', '#f43f5e'],
  legend: { position: 'top' },
  dataLabels: { enabled: false },
  tooltip: {
    theme: isDark.value ? 'dark' : 'light',
    style: { fontSize: '13px' },
    fillSeriesColor: false,
    x: {
      format: 'dd MMM yyyy'
    }
  }
}))

const series = computed(() => {
  if (!props.data.length) return []
  return [
    {
      name: 'Avg score',
      type: 'line',
      data: props.data.map((row) => row.avg_score),
    },
    {
      name: 'Positive count',
      type: 'column',
      data: props.data.map((row) => row.positive_count),
    },
    {
      name: 'Negative count',
      type: 'column',
      data: props.data.map((row) => row.negative_count),
    },
  ]
})
</script>

<template>
  <div v-if="!data.length" class="text-muted text-center py-5">
    No sentiment data for the selected product and date range.
  </div>
  <apexchart
    v-else
    type="line"
    height="300"
    :options="chartOptions"
    :series="series"
  />
</template>

<style scoped>
:deep(.apexcharts-tooltip) {
  background: var(--chart-tooltip-bg) !important;
  color: var(--text-main) !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  border: 1px solid var(--surface-glass-border) !important;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
  border-radius: 8px !important;
}
:deep(.apexcharts-tooltip-title) {
  background: transparent !important;
  color: var(--text-main) !important;
  border-bottom: 1px solid var(--surface-glass-border) !important;
  font-family: 'Outfit', sans-serif !important;
  font-weight: 600 !important;
  padding-bottom: 4px !important;
  margin-bottom: 4px !important;
}
</style>

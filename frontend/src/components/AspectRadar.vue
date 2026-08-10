<script setup>
/**
 * Radar chart for average aspect scores (price, quality, shipping, service).
 * Expects data from GET /analyze/aspect-summary/{product_id}.
 */
import { computed } from 'vue'

const props = defineProps({
  data: {
    type: Object,
    default: () => ({
      price: 0,
      quality: 0,
      shipping: 0,
      service: 0,
    }),
  },
})

const hasData = computed(() =>
  ['price', 'quality', 'shipping', 'service'].some((key) => props.data[key] > 0),
)

const chartOptions = computed(() => ({
  chart: {
    id: 'aspect-radar',
    toolbar: { show: false },
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    background: 'transparent',
  },
  xaxis: {
    categories: ['Price', 'Quality', 'Shipping', 'Service'],
  },
  yaxis: {
    show: true,
    min: 0,
    max: 1,
    tickAmount: 5,
  },
  stroke: { width: 2 },
  fill: {
    opacity: 0.25,
  },
  colors: ['#4f46e5'],
  markers: { size: 4 },
  legend: { show: false },
  tooltip: {
    theme: 'light',
    y: {
      formatter: (value) => `${Math.round(value * 100)}% positive`,
    },
  },
}))

const series = computed(() => [
  {
    name: 'Aspect sentiment',
    data: [
      props.data.price ?? 0,
      props.data.quality ?? 0,
      props.data.shipping ?? 0,
      props.data.service ?? 0,
    ],
  },
])
</script>

<template>
  <div v-if="!hasData" class="text-muted text-center py-5">
    No aspect data yet. Complete reviews need to finish analysis first.
  </div>
  <apexchart
    v-else
    type="radar"
    height="320"
    :options="chartOptions"
    :series="series"
  />
</template>

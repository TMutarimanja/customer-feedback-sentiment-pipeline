<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { Chart, BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js'

// Register chart.js components
Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend)

// Props: expects object like { positive: 22, negative: 15, neutral: 5, mixed: 0 }
const props = defineProps({
  data: {
    type: Object,
    required: true,
    default: () => ({ positive: 0, negative: 0, neutral: 0, mixed: 0 })
  }
})

const chartCanvas = ref(null)
let chartInstance = null

// Create Chart
function createChart() {
  if (!chartCanvas.value) {
    console.warn('Canvas not ready, skipping chart creation')
    return
  }

  const ctx = chartCanvas.value.getContext('2d')
  if (!ctx) {
    console.error('Failed to get 2D context from canvas')
    return
  }

  console.log('Creating chart with data:', props.data)

  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Positive', 'Negative', 'Neutral', 'Mixed'],
      datasets: [
        {
          label: 'Sentiment',
          data: [
            props.data.positive,
            props.data.negative,
            props.data.neutral,
            props.data.mixed
          ],
          backgroundColor: ['#4ade80', '#f87171', '#60a5fa', '#facc15']
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 700,
        easing: 'easeOutQuart'
      },
      scales: {
        y: {
          beginAtZero: true
          
        },
        x: {
          grid: { display: false }
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  })
}

// Update Chart
function updateChart() {
  if (!chartInstance) {
    console.warn('Chart not yet created, creating...')
    createChart()
    return
  }

  chartInstance.data.datasets[0].data = [
    props.data.positive,
    props.data.negative,
    props.data.neutral,
    props.data.mixed
  ]
  chartInstance.update('active')
}

// Watch for prop changes
watch(
  () => props.data,
  (newData) => {
    console.log('Updating chart with new data:', newData)
    updateChart()
  },
  { deep: true, immediate: true }
)

onMounted(async () => {
  await nextTick()
  console.log('Chart data on mount:', props.data)
  createChart()
})

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
})
</script>

<template>
  <UCard class="w-full">
    <template #header>
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold">Sentiment Distribution</h3>
      </div>
    </template>
    
    <div class="relative w-full h-[300px]">
      <canvas ref="chartCanvas"></canvas>
    </div>
  </UCard>
</template>

<style scoped>
/* optional: add smooth appearance */
canvas {
  transition: opacity 0.3s ease;
}
</style>

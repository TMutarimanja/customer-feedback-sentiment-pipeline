<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useSentimentStore } from '~/stores/sentiment'
import { debounce } from 'lodash-es'
import SentimentChart from '~/components/SentimentChart.vue'

// Store
const sentimentStore = useSentimentStore()

// Reactive data
const isLoading = ref(false)
const currentPage = ref(1)
const itemsPerPage = 10
const filtersExpanded = ref(false)

// Filters
const filters = ref({
  sentiment: null,
  startDate: '',
  endDate: '',
  searchText: ''
})

const allResults = computed(() => sentimentStore.results)
const summary = computed(() => sentimentStore.summary)
const chartError = ref(null)

// Chart data computed property - now uses filtered results
const chartData = computed(() => {
  console.log("Computing chartData from filtered results:", filteredResults.value.length)
  
  if (!filteredResults.value || filteredResults.value.length === 0) {
    console.log("No filtered results, returning zeros")
    return {
      positive: 0,
      negative: 0,
      neutral: 0,
      mixed: 0
    }
  }
  
  // Count sentiment types from filtered results
  const counts = filteredResults.value.reduce((acc, result) => {
    const sentiment = result.sentiment?.toUpperCase()
    if (sentiment && acc.hasOwnProperty(sentiment.toLowerCase())) {
      acc[sentiment.toLowerCase()]++
    }
    return acc
  }, {
    positive: 0,
    negative: 0,
    neutral: 0,
    mixed: 0
  })
  
  console.log("Chart data computed from filtered results:", counts)
  return counts
})

const filteredResults = computed(() => {
  let results = [...allResults.value]
  
  // Apply sentiment filter
  if (filters.value.sentiment) {
    results = results.filter(r => r.sentiment === filters.value.sentiment)
  }
  
  // Apply date range filter
  if (filters.value.startDate) {
    results = results.filter(r => new Date(r.timestamp) >= new Date(filters.value.startDate))
  }
  
  if (filters.value.endDate) {
    results = results.filter(r => new Date(r.timestamp) <= new Date(filters.value.endDate))
  }
  
  // Apply search filter
  if (filters.value.searchText) {
    const searchLower = filters.value.searchText.toLowerCase()
    results = results.filter(r => 
      r.feedback_text.toLowerCase().includes(searchLower) ||
      r.sentiment.toLowerCase().includes(searchLower)
    )
  }
  
  return results
})

const totalPages = computed(() => Math.ceil(filteredResults.value.length / itemsPerPage))

const paginatedResults = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return filteredResults.value.slice(start, end)
})

// Debounced search
const debouncedSearch = debounce(() => {
  applyFilters()
}, 300)

// Methods
const refreshData = async () => {
  isLoading.value = true
  try {
    await Promise.all([
      sentimentStore.fetchResults(),
      sentimentStore.fetchSummary()
    ])
  } catch (error) {
    console.error('Error refreshing data:', error)
  } finally {
    isLoading.value = false
  }
}

const applyFilters = () => {
  currentPage.value = 1 // Reset to first page when filters change
}

const clearFilters = () => {
  filters.value = {
    sentiment: null,
    startDate: '',
    endDate: '',
    searchText: ''
  }
  currentPage.value = 1
}

const getSentimentCount = (sentiment) => {
  return filteredResults.value.filter(r => r.sentiment === sentiment).length
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  try {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (error) {
    return 'Invalid Date'
  }
}

const getSentimentColor = (sentiment) => {
  const colors = {
    POSITIVE: 'green',
    NEGATIVE: 'red',
    NEUTRAL: 'yellow',
    MIXED: 'purple'
  }
  return colors[sentiment] || 'gray'
}

// Format metadata values (e.g., submitted_at) into readable dates when applicable
const formatMetadataValue = (key, value) => {
  if (!value) return ''
  const lowerKey = String(key).toLowerCase()
  const looksLikeDate =
    lowerKey.includes('date') ||
    lowerKey.includes('time') ||
    lowerKey === 'submitted_at' ||
    lowerKey === 'timestamp' ||
    lowerKey.endsWith('_at')

  if (looksLikeDate) {
    try {
      return new Date(String(value)).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch (e) {
      return String(value)
    }
  }

  return String(value)
}



const exportResults = () => {
  if (filteredResults.value.length === 0) {
    alert('No results to export')
    return
  }
  
  const csvContent = [
    ['ID', 'Sentiment', 'Text', 'Timestamp', 'Confidence'],
    ...filteredResults.value.map(result => [
      result.id || '',
      result.sentiment || '',
      `"${(result.text || result.feedback_text || '').replace(/"/g, '""')}"`,
      result.timestamp || '',
      result.confidence || ''
    ])
  ].map(row => row.join(',')).join('\n')
  
  const blob = new Blob([csvContent], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `sentiment-results-${new Date().toISOString().split('T')[0]}.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}

// Lifecycle
onMounted(async () => {
  await refreshData()
})

// Watch for filter changes
watch(() => filters.value, applyFilters, { deep: true })
</script>

<template>
  <div class="container mx-auto px-4 py-8 space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div class="flex items-center space-x-4">
        <!-- Back Button -->
        <UButton
          to="/"
          variant="outline"
          icon="i-heroicons-arrow-left"
        >
          Back
        </UButton>
      </div>
      
      <div class="flex items-center space-x-4">
        <!-- Refresh Button -->
        <UButton
          @click="refreshData"
          :loading="isLoading"
          variant="outline"
          icon="i-heroicons-arrow-path"
        >
          Refresh
        </UButton>
        
        <!-- Export Button -->
        <UButton
          @click="exportResults"
          variant="solid"
          icon="i-heroicons-arrow-down-tray"
        >
          Export
        </UButton>
      </div>
    </div>

    <!-- Filters -->
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold">Filters</h3>
          <UButton
            @click="filtersExpanded = !filtersExpanded"
            variant="ghost"
            size="sm"
            class="md:hidden"
            :icon="filtersExpanded ? 'i-heroicons-chevron-up' : 'i-heroicons-chevron-down'"
          >
            {{ filtersExpanded ? 'Hide' : 'Show' }} Filters
          </UButton>
        </div>
      </template>
      
      <div 
        class="grid grid-cols-1 md:grid-cols-4 gap-4 transition-all duration-300 ease-in-out"
        :class="{ 'hidden md:grid': !filtersExpanded, 'block': filtersExpanded }"
      >
        <!-- Sentiment Filter -->
        <div>
          <UFormField label="Sentiment">
            <USelect
              v-model="filters.sentiment"
              placeholder="All sentiments"
              clearable
              :items="[
                { label: 'Positive', value: 'POSITIVE' },
                { label: 'Negative', value: 'NEGATIVE' },
                { label: 'Neutral', value: 'NEUTRAL' },
                { label: 'Mixed', value: 'MIXED' }
              ]"
              @change="applyFilters"
            />
          </UFormField>
        </div>
        
        <!-- Date Range Filter -->
        <div>
          <UFormField label="Start Date">
            <UInput
            class="w-full"
              v-model="filters.startDate"
              type="date"
              @change="applyFilters"
            />
          </UFormField>
        </div>
        
        <div>
          <UFormField label="End Date">
            <UInput
              class="w-full"
              v-model="filters.endDate"
              type="date"
              @change="applyFilters"
            />
          </UFormField>
        </div>
        
        <!-- Search Filter -->
        <div>
          <UFormField label="Search Text">
            <UInput
              class="w-full"
              v-model="filters.searchText"
              placeholder="Search feedback..."
              @input="debouncedSearch"
            />
          </UFormField>
        </div>
      </div>
      
      <template #footer>
        <div class="flex justify-end">
          <UButton
            @click="clearFilters"
            variant="ghost"
            size="sm"
          >
            Clear all filters
          </UButton>
        </div>
      </template>
    </UCard>

    <!-- Summary + Chart side-by-side on wide screens -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Chart -->
      <div>
        
        <SentimentChart :data="chartData" />
      </div>
      <!-- Summary Statistics -->
      <UCard>
      <template #header>
        <h3 class="text-lg font-semibold">Summary Statistics</h3>
      </template>
      
      <div class="grid grid-cols-2 gap-4">
        <UCard class="bg-green-50 dark:bg-green-900/20">
          <div class="text-center p-4">
            <div class="text-2xl font-bold text-green-600 dark:text-green-400">
              {{ getSentimentCount('POSITIVE') }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-400">Positive</div>
          </div>
        </UCard>
        
        <UCard class="bg-red-50 dark:bg-red-900/20">
          <div class="text-center p-4">
            <div class="text-2xl font-bold text-red-600 dark:text-red-400">
              {{ getSentimentCount('NEGATIVE') }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-400">Negative</div>
          </div>
        </UCard>
        
        <UCard class="bg-yellow-50 dark:bg-yellow-900/20">
          <div class="text-center p-4">
            <div class="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
              {{ getSentimentCount('NEUTRAL') }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-400">Neutral</div>
          </div>
        </UCard>
        
        <UCard class="bg-purple-50 dark:bg-purple-900/20">
          <div class="text-center p-4">
            <div class="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {{ getSentimentCount('MIXED') }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-400">Mixed</div>
          </div>
        </UCard>
      </div>
      
      <!-- Total Records -->
      <div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div class="text-center">
          <div class="text-xl font-bold text-blue-600 dark:text-blue-400">
            {{ filteredResults.length }}
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400">Total Feedback Items</div>
        </div>
      </div>
      </UCard>

    </div>

    <!-- Results -->
    <UCard>
      <template #header>
        <div class="flex justify-between items-center">
          <h3 class="text-xl font-semibold">Results</h3>
          <div class="text-sm text-gray-600 dark:text-gray-400">
            Showing {{ filteredResults.length }} of {{ allResults.length }} results
          </div>
        </div>
      </template>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-8">
        <UIcon name="i-heroicons-arrow-path" class="w-8 h-8 animate-spin mx-auto mb-4" />
        <p class="text-gray-600 dark:text-gray-400">Loading results...</p>
      </div>
      
      <!-- Empty State -->
      <div v-else-if="filteredResults.length === 0" class="text-center py-8 text-gray-500 dark:text-gray-400">
        <UIcon name="i-heroicons-document-text" class="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>No results found matching your filters.</p>
      </div>
      
      <!-- Results -->
      <div v-else class="space-y-4">
        <UCard
          v-for="result in paginatedResults"
          :key="result.id"
          class="hover:shadow-md transition-shadow duration-200"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <!-- Header -->
              <div class="flex items-center space-x-4 mb-3">
                <UBadge
                  :color="getSentimentColor(result.sentiment)"
                  variant="soft"
                >
                  {{ result.sentiment }}
                </UBadge>
                <span class="text-sm text-gray-600 dark:text-gray-400">
                  {{ formatDate(result.timestamp) }}
                </span>
              </div>
              
              <!-- Feedback Text -->
              <p class="text-gray-900 dark:text-white mb-3">
                {{ result.text || result.feedback_text }}
              </p>
              
              <!-- Metadata -->
              <div v-if="result.metadata && Object.keys(result.metadata).length > 0" class="text-sm text-gray-600 dark:text-gray-400">
                <div class="flex flex-wrap gap-2">
                  <UBadge
                    v-for="(value, key) in result.metadata"
                    :key="key"
                    variant="outline"
                    size="xs"
                  >
                    {{ key }}: {{ formatMetadataValue(key, value) }}
                  </UBadge>
                </div>
              </div>
            </div>
            
            
          </div>
        </UCard>
      </div>

      <!-- Pagination -->
      <template v-if="totalPages > 1" #footer>
        <div class="flex justify-center items-center space-x-4">
          <UButton
            @click="currentPage = Math.max(1, currentPage - 1)"
            :disabled="currentPage === 1"
            variant="outline"
            size="sm"
          >
            Previous
          </UButton>
          
          <span class="px-3 py-2 text-sm text-gray-700 dark:text-gray-300">
            Page {{ currentPage }} of {{ totalPages }}
          </span>
          
          <UButton
            @click="currentPage = Math.min(totalPages, currentPage + 1)"
            :disabled="currentPage === totalPages"
            variant="outline"
            size="sm"
          >
            Next
          </UButton>
        </div>
      </template>
    </UCard>
  </div>
</template>

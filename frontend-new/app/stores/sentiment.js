import { defineStore } from 'pinia'

export const useSentimentStore = defineStore('sentiment', () => {
  // State
  const results = ref([])
  const summary = ref({})
  const recentResults = ref([])
  const isLoading = ref(false)
  const error = ref(null)

  // Getters
  const totalResults = computed(() => results.value.length)
  const positiveCount = computed(() => results.value.filter(r => r.sentiment === 'POSITIVE').length)
  const negativeCount = computed(() => results.value.filter(r => r.sentiment === 'NEGATIVE').length)
  const neutralCount = computed(() => results.value.filter(r => r.sentiment === 'NEUTRAL').length)
  const mixedCount = computed(() => results.value.filter(r => r.sentiment === 'MIXED').length)

  // Actions
  const fetchResults = async (filters = {}) => {
    isLoading.value = true
    error.value = null
    
    try {
      const config = useRuntimeConfig()
      const response = await $fetch(`${config.public.apiBaseUrl}/sentiment`, {
        method: 'GET',
        query: filters
      })
      
      // Handle the response format from our Lambda function
      if (response.results && Array.isArray(response.results)) {
        results.value = response.results
        return { results: response.results }
      } else {
        // No data available
        results.value = []
        return { results: [] }
      }
    } catch (err) {
      console.warn('API unavailable:', err.message)
      // No fallback data - show empty state
      results.value = []
      return { results: [] }
    } finally {
      isLoading.value = false
    }
  }

  const fetchSummary = async () => {
    try {
      const config = useRuntimeConfig()
      const response = await $fetch(`${config.public.apiBaseUrl}/sentiment`, {
        method: 'GET',
        query: { summary: 'true' }
      })
      
      // Handle the response format from our Lambda function
      if (response.total_feedback_items !== undefined) {
        summary.value = {
          total_records: response.total_feedback_items,
          positive_sentiment: response.sentiment_counts?.POSITIVE || 0,
          negative_sentiment: response.sentiment_counts?.NEGATIVE || 0,
          neutral_sentiment: response.sentiment_counts?.NEUTRAL || 0,
          mixed_sentiment: response.sentiment_counts?.MIXED || 0
        }
        return summary.value
      } else {
        // No data available
        summary.value = {
          total_files: 0,
          total_records: 0,
          positive_sentiment: 0,
          negative_sentiment: 0,
          neutral_sentiment: 0,
          mixed_sentiment: 0,
          average_sentiment: 0
        }
        return summary.value
      }
    } catch (err) {
      console.warn('API unavailable:', err.message)
      // No fallback data - show empty state
      summary.value = {
        total_files: 0,
        total_records: 0,
        positive_sentiment: 0,
        negative_sentiment: 0,
        neutral_sentiment: 0,
        mixed_sentiment: 0,
        average_sentiment: 0
      }
      return summary.value
    }
  }

  const fetchRecentResults = async (limit = 10) => {
    try {
      const config = useRuntimeConfig()
      // Fetch full results; we'll sort and slice client-side to ensure true recency
      const response = await $fetch(`${config.public.apiBaseUrl}/sentiment`, {
        method: 'GET'
      })
      
      // Handle the response format from our Lambda function
      if (response.results && Array.isArray(response.results)) {
        // Order by most recent timestamp first using common timestamp fields
        const sorted = response.results
          .slice()
          .sort((a, b) => {
            const tb = Date.parse(b.timestamp || b.created_at || b.date || 0) || 0
            const ta = Date.parse(a.timestamp || a.created_at || a.date || 0) || 0
            return tb - ta
          })
        recentResults.value = sorted.slice(0, limit)
        return { results: recentResults.value }
      } else {
        // No data available
        recentResults.value = []
        return { results: [] }
      }
    } catch (err) {
      console.warn('API unavailable:', err.message)
      // No fallback data - show empty state
      recentResults.value = []
      return { results: [] }
    }
  }

  const fetchResultById = async (id) => {
    try {
      const config = useRuntimeConfig()
      const response = await $fetch(`${config.public.apiBaseUrl}/sentiment/results/${id}`, {
        method: 'GET'
      })
      
      if (response.data) {
        return response.data
      } else {
        throw new Error('Result not found')
      }
    } catch (err) {
      console.error('Error fetching result:', err)
      throw err
    }
  }

  const uploadFile = async (file) => {
    isLoading.value = true
    error.value = null
    
    try {
      const config = useRuntimeConfig()
      
      // Create form data
      const formData = new FormData()
      formData.append('file', file)
      
      // Upload file to Lambda (bulk route)
      const uploadResponse = await $fetch(`${config.public.apiBaseUrl}/sentiment/bulk`, {
        method: 'POST',
        body: formData
      })
      
      console.log('Upload successful:', uploadResponse)
      
      // Refresh data after successful upload
      await Promise.all([
        fetchSummary(),
        fetchRecentResults()
      ])
      
      return uploadResponse
    } catch (err) {
      error.value = err.message || 'Failed to upload file'
      console.error('Error uploading file:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const submitTextFeedback = async (feedbackData) => {
    isLoading.value = true
    error.value = null
    
    try {
      const config = useRuntimeConfig()
      
      // Submit single text feedback to Lambda (single route)
      const response = await $fetch(`${config.public.apiBaseUrl}/sentiment/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: feedbackData
      })
      
      console.log('Text feedback submitted:', response)
      
      // Refresh data after successful submission
      await Promise.all([
        fetchSummary(),
        fetchRecentResults()
      ])
      
      return response
    } catch (err) {
      error.value = err.message || 'Failed to submit feedback'
      console.error('Error submitting text feedback:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const clearError = () => {
    error.value = null
  }

  const reset = () => {
    results.value = []
    summary.value = {}
    recentResults.value = []
    isLoading.value = false
    error.value = null
  }

  return {
    // State
    results,
    summary,
    recentResults,
    isLoading,
    error,
    
    // Getters
    totalResults,
    positiveCount,
    negativeCount,
    neutralCount,
    mixedCount,
    
    // Actions
    fetchResults,
    fetchSummary,
    fetchRecentResults,
    fetchResultById,
    uploadFile,
    submitTextFeedback,
    clearError,
    reset
  }
})

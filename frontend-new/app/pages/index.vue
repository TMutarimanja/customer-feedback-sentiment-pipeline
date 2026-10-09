<script setup>
import { useSentimentStore } from '~/stores/sentiment'

// Store
const sentimentStore = useSentimentStore()

// Reactive data
const isLoading = ref(false)
const fileInput = ref(null)
const feedbackText = ref('')
const rating = ref(5)
// Optional customer info
const customerName = ref('')
const customerEmail = ref('')
const customerId = ref('')

// Methods
const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  try {
    await sentimentStore.uploadFile(file)
    await navigateTo('/results')
  } catch (error) {
    console.error('Upload failed:', error)
  }
}

const submitFeedback = async () => {
  if (!feedbackText.value.trim()) {
    alert('Please enter feedback text')
    return
  }

  try {
    const payload = {
      text: feedbackText.value,
      rating: rating.value,
      timestamp: new Date().toISOString()
    }
    if (customerName.value) payload.customer_name = customerName.value
    if (customerEmail.value) payload.customer_email = customerEmail.value
    if (customerId.value) payload.customer_id = customerId.value

    await sentimentStore.submitTextFeedback(payload)
    
    feedbackText.value = ''
    rating.value = 5
    customerName.value = ''
    customerEmail.value = ''
    customerId.value = ''
    await navigateTo('/results')
  } catch (error) {
    console.error('Submission failed:', error)
  }
}
</script>

<template>
  <div class="container mx-auto px-4 py-8 space-y-8">
    <!-- Hero Section -->
    <div class="text-center">
      <h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-4">
        Customer Feedback Sentiment Analysis
      </h1>
      <p class="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
        Analyze customer feedback using AWS AI services. Upload files or submit individual feedback to get real-time sentiment analysis.
      </p>
    </div>

    <!-- File Upload Section -->
    <UCard>
      <template #header>
        <h2 class="text-2xl font-semibold">Upload Feedback Files</h2>
      </template>
      
      <div class="space-y-4">
        <p class="text-gray-600 dark:text-gray-400">
          Upload CSV, JSON, or TXT files containing customer feedback. The system will automatically process and analyze sentiment.
        </p>
        
        <div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center">
          <UIcon name="i-heroicons-cloud-arrow-up" class="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <p class="text-gray-600 dark:text-gray-400 mb-4">
            Drag and drop files here, or click to select
          </p>
          <UButton
            @click="fileInput?.click()"
            variant="outline"
          >
            Choose Files
          </UButton>
          <input
            ref="fileInput"
            type="file"
            accept=".csv,.json,.txt"
            @change="handleFileUpload"
            class="hidden"
          />
        </div>
        
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Supported formats: CSV, JSON, TXT
        </p>
      </div>
    </UCard>

    <!-- Individual Feedback Section -->
    <UCard>
      <template #header>
        <h2 class="text-2xl font-semibold">Submit Individual Feedback</h2>
      </template>
      
      <div class="space-y-4 max-w-md mx-auto">
        <UFormField label="Feedback Text" required>
          <UTextarea
            class="w-full"
            v-model="feedbackText"
            placeholder="Enter your feedback here..."
            rows="4"
            :disabled="isLoading"
            autoresize
          />
        </UFormField>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <UFormField label="Rating (1-5)">
            <USelect
              class="w-full"
              v-model="rating"
              :items="[1,2,3,4,5]"
              :disabled="isLoading"
            />
          </UFormField>

          <UFormField label="Customer Name (optional)">
            <UInput v-model="customerName" class="w-full" :disabled="isLoading" placeholder="e.g., Jane Doe" />
          </UFormField>

          <UFormField label="Customer Email (optional)">
            <UInput v-model="customerEmail" class="w-full" :disabled="isLoading" type="email" placeholder="e.g., jane@example.com" />
          </UFormField>

         
        </div>
        
        <UButton
          @click="submitFeedback"
          :loading="isLoading"
          size="lg"
          class="w-full"
        >
          Submit Feedback
        </UButton>
      </div>
    </UCard>

    <!-- Quick Actions -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">View Results</h3>
        </template>
        
        <p class="text-gray-600 dark:text-gray-400 mb-4">
          View all analyzed feedback with interactive charts and filtering options.
        </p>
        
        <UButton
          to="/results"
          variant="outline"
          block
        >
          Go to Results
        </UButton>
      </UCard>
      
      <UCard>
        <template #header>
          <h3 class="text-lg font-semibold">System Status</h3>
        </template>
        
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600 dark:text-gray-400">API Status</span>
            <UBadge color="green" variant="soft">Online</UBadge>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600 dark:text-gray-400">Processing</span>
            <UBadge color="blue" variant="soft">Ready</UBadge>
          </div>
        </div>
      </UCard>
    </div>
  </div>
</template>

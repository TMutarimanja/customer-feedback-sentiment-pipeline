<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Header -->
    <header class="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-4">
          <div class="flex items-center">
            <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
              Customer Feedback Sentiment Analysis
            </h1>
          </div>
          <div class="flex items-center space-x-4">
            <!-- Theme Toggle -->
            <UColorModeButton />
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <NuxtPage />
    </main>

    <!-- Footer -->
    <footer class="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 mt-16">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div class="text-center text-gray-600 dark:text-gray-400">
          <p>&copy; 2025 Customer Feedback Sentiment Analysis System. Built with AWS and Nuxt.js.</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
// Meta tags
useHead({
  title: 'Customer Feedback Sentiment Analysis',
  meta: [
    { name: 'description', content: 'Analyze customer feedback sentiment with AWS AI services' }
  ]
})
</script>

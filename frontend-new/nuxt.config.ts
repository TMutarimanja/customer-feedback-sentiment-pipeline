// https://nuxt.com/docs/api/configuration/nuxt-config
import tailwindcss from "@tailwindcss/vite";
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  modules: [
    '@nuxt/content',
    '@nuxt/eslint',
    '@nuxt/image',
    '@nuxt/scripts',
    '@nuxt/test-utils',
    '@nuxt/ui',
    '@pinia/nuxt',
    '@vueuse/nuxt'
  ],

  runtimeConfig: {
    public: {
      apiBaseUrl: process.env.API_BASE_URL || 'https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev',
      s3BucketName: process.env.S3_BUCKET_NAME || 'customer-feedback-sentiment-analysis-clean-dev-123456789012'
    }
  },

  vite: {
    plugins: [tailwindcss()]
  },
  css: ['~/assets/css/main.css'],

  ssr: false,
  nitro: {
    preset: 'static'
  }
})
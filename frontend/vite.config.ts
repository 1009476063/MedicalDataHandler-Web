import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia', 'vue-i18n', 'axios'],
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'cornerstone-core': ['@cornerstonejs/core'],
          'cornerstone-tools': ['@cornerstonejs/tools'],
          'cornerstone-streaming': ['@cornerstonejs/streaming-image-volume-loader'],
          'vue-vendor': ['vue', 'vue-router', 'pinia', 'vue-i18n'],
          'dicom-parser': ['dicom-parser'],
        },
      },
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})

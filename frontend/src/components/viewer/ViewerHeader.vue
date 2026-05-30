<template>
  <div class="flex items-center justify-between px-4 py-2 border-b border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900">
    <h1 class="text-lg font-semibold text-accent-900 dark:text-white">{{ $t('viewer.title') }}</h1>
    <div class="flex items-center gap-1.5">
      <span
        v-if="gpuInfo?.gpu_available"
        class="text-[10px] font-medium px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300"
      >
        GPU: {{ gpuInfo.gpu_name }}
      </span>
      <span
        v-if="canvasMode"
        class="text-[10px] font-medium px-2 py-0.5 rounded-full bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300"
      >
        Canvas2D
      </span>
      <span
        v-if="clientMode"
        class="text-[10px] font-medium px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300"
      >
        Client Mode
      </span>
      <!-- GPU tips tooltip -->
      <div v-if="canvasMode && recommendations.length > 0" class="relative group">
        <button class="p-1 rounded hover:bg-accent-100 dark:hover:bg-accent-800 text-accent-500 dark:text-accent-400 transition-colors">
          <InformationCircleIcon class="w-4 h-4" />
        </button>
        <div class="absolute right-0 top-full mt-1 z-50 w-72 p-3 rounded-lg bg-white dark:bg-accent-800 border border-accent-200 dark:border-accent-600 shadow-lg opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto transition-opacity">
          <p class="text-xs font-medium text-accent-800 dark:text-accent-200 mb-2">推荐使用以下浏览器以获得最佳 3D 渲染体验：</p>
          <ul class="space-y-1.5">
            <li v-for="rec in recommendations" :key="rec.browser" class="text-xs text-accent-600 dark:text-accent-300">
              <a :href="rec.url" target="_blank" rel="noopener" class="font-medium hover:underline">{{ rec.browser }}</a>
              <span class="block text-[10px] text-accent-500 dark:text-accent-400">{{ rec.reason }}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
    <div class="flex items-center gap-2">
      <button
        class="p-1.5 rounded-lg hover:bg-accent-100 dark:hover:bg-accent-800 text-accent-600 dark:text-accent-400 transition-colors"
        :title="$t('viewer.screenshot')"
        @click="$emit('screenshot')"
      >
        <CameraIcon class="w-4 h-4" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { CameraIcon, InformationCircleIcon } from '@heroicons/vue/24/outline'
import { getBrowserRecommendations, type BrowserRecommendation } from '@/utils/webglDetector'

defineProps<{
  gpuInfo: { gpu_available: boolean; gpu_name?: string } | null
  canvasMode: boolean
  clientMode: boolean
}>()

defineEmits<{
  screenshot: []
}>()

const recommendations: BrowserRecommendation[] = getBrowserRecommendations()
</script>

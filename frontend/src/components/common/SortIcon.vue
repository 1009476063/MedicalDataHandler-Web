<template>
  <svg v-if="field === current" class="w-3 h-3" :class="dir === 'desc' ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"/>
  </svg>
  <svg v-else class="w-3 h-3 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"/>
  </svg>
</template>

<script setup lang="ts">
defineProps<{
  field: string
  current: string
  dir: 'asc' | 'desc'
}>()
</script>

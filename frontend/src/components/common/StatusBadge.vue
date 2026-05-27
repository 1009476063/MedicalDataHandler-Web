<template>
  <span :class="[
    'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium',
    colors.bg, colors.text
  ]">
    <span :class="['w-1.5 h-1.5 rounded-full', colors.dot]" />
    {{ label || status }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { MODALITY_COLORS } from '@/types'

const props = defineProps<{
  status: string
  label?: string
}>()

const colors = computed(() => MODALITY_COLORS[props.status] || {
  bg: 'bg-gray-100 dark:bg-gray-800/30',
  text: 'text-gray-700 dark:text-gray-300',
  dot: 'bg-gray-500',
})
</script>

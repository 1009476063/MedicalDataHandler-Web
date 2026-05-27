<template>
  <div class="flex items-center justify-center" :class="wrapperClass">
    <svg :class="['animate-spin', sizeClass]" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
    <span v-if="text" class="ml-2 text-accent-600 dark:text-accent-400">{{ text }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  size?: 'sm' | 'md' | 'lg'
  text?: string
  wrapperClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  wrapperClass: '',
})

const sizeClasses: Record<string, string> = { sm: 'h-4 w-4', md: 'h-6 w-6', lg: 'h-8 w-8' }
const sizeClass = computed(() => sizeClasses[props.size] || sizeClasses.md)
</script>

<template>
  <div class="p-6 bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-card hover:shadow-card-hover transition-shadow">
    <div class="flex items-start justify-between">
      <div>
        <p class="text-sm font-medium text-accent-500 dark:text-accent-400">{{ title }}</p>
        <p class="mt-2 text-3xl font-bold text-accent-900 dark:text-white">{{ formattedValue }}</p>
      </div>
      <div :class="['p-3 rounded-xl', colorClasses[color].bg]">
        <component :is="icon" :class="['w-6 h-6', colorClasses[color].text]" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  title: string
  value: number | string
  icon: any
  color?: 'primary' | 'green' | 'blue' | 'purple' | 'orange'
}>(), {
  color: 'primary',
})

const formattedValue = computed(() => {
  if (typeof props.value === 'number') return props.value.toLocaleString()
  return props.value
})

const colorClasses = {
  primary: { bg: 'bg-primary-100 dark:bg-primary-900/30', text: 'text-primary-600 dark:text-primary-400' },
  green: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-600 dark:text-green-400' },
  blue: { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-600 dark:text-blue-400' },
  purple: { bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-600 dark:text-purple-400' },
  orange: { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-600 dark:text-orange-400' },
}
</script>

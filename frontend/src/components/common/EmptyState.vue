<template>
  <div class="flex flex-col items-center justify-center py-12 px-4 text-center">
    <div class="p-4 rounded-full bg-accent-100 dark:bg-accent-800 mb-4">
      <component :is="icon" class="w-8 h-8 text-accent-400" />
    </div>
    <h3 class="text-lg font-medium text-accent-900 dark:text-white">{{ title || t('common.noData') }}</h3>
    <p class="mt-1 text-sm text-accent-500 dark:text-accent-400 max-w-sm">{{ description || t('common.noRecords') }}</p>
    <slot name="action" />
  </div>
</template>

<script setup lang="ts">
import { InboxIcon } from '@heroicons/vue/24/outline'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

withDefaults(defineProps<{
  title?: string
  description?: string
  icon?: any
}>(), {
  title: '',
  description: '',
  icon: InboxIcon,
})
</script>

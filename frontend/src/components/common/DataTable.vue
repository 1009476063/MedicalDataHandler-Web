<template>
  <div class="space-y-4">
    <div class="hidden lg:block overflow-hidden rounded-xl border border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900 relative">
      <table class="w-full">
        <thead>
          <tr class="border-b border-accent-200 dark:border-accent-700 bg-accent-50 dark:bg-accent-800/50">
            <th
              v-for="column in columns"
              :key="column.key"
              class="px-4 py-3 text-left text-sm font-medium text-accent-600 dark:text-accent-400"
            >
              {{ column.label }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-accent-200 dark:divide-accent-700">
          <tr
            v-for="(row, index) in data"
            :key="index"
            class="hover:bg-accent-50 dark:hover:bg-accent-800/50 transition-colors cursor-pointer"
            @click="$emit('row-click', row)"
          >
            <td
              v-for="column in columns"
              :key="column.key"
              class="px-4 py-3 text-sm text-accent-900 dark:text-white"
            >
              <slot :name="`cell-${column.key}`" :row="row" :value="row[column.key]">
                {{ row[column.key] }}
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="lg:hidden space-y-3">
      <div
        v-for="(row, index) in data"
        :key="index"
        class="p-4 bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-card cursor-pointer"
        @click="$emit('row-click', row)"
      >
        <div
          v-for="column in columns"
          :key="column.key"
          class="flex justify-between py-2 border-b border-accent-100 dark:border-accent-800 last:border-0"
        >
          <span class="text-sm text-accent-500 dark:text-accent-400">{{ column.label }}</span>
          <span class="text-sm font-medium text-accent-900 dark:text-white">
            <slot :name="`cell-${column.key}`" :row="row" :value="row[column.key]">
              {{ row[column.key] }}
            </slot>
          </span>
        </div>
      </div>
    </div>

    <EmptyState v-if="!loading && data.length === 0" :title="emptyTitle || t('common.noData')" :description="emptyDescription || t('common.noRecords')" />

    <div v-if="loading" class="flex justify-center py-8">
      <LoadingSpinner :text="$t('common.loading')" />
    </div>
  </div>
</template>

<script setup lang="ts">
import EmptyState from './EmptyState.vue'
import LoadingSpinner from './LoadingSpinner.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface Column {
  key: string
  label: string
}

withDefaults(defineProps<{
  columns: Column[]
  data: Record<string, any>[]
  loading?: boolean
  emptyTitle?: string
  emptyDescription?: string
}>(), {
  loading: false,
  emptyTitle: '',
  emptyDescription: '',
})

defineEmits<{
  'row-click': [row: Record<string, any>]
}>()
</script>

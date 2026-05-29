<template>
  <header class="sticky top-0 z-40 glass border-b border-accent-200/50 dark:border-accent-700/50">
    <div class="flex items-center justify-between h-16 px-4 lg:px-6">
      <div class="flex items-center gap-3">
        <button
          @click="$emit('toggle-mobile')"
          class="p-2 rounded-xl text-accent-600 dark:text-accent-400 hover:bg-accent-100 dark:hover:bg-accent-800 lg:hidden"
        >
          <Bars3Icon class="w-5 h-5" />
        </button>
        <div>
          <h2 class="text-lg font-semibold text-accent-900 dark:text-white">{{ pageTitle }}</h2>
          <p v-if="pageDescription" class="text-sm text-accent-500 hidden sm:block">{{ pageDescription }}</p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <div v-if="store.sessionId" class="hidden md:flex items-center gap-2 px-3 py-1.5 bg-primary-50 dark:bg-primary-900/30 rounded-xl">
          <span class="w-2 h-2 rounded-full bg-primary-500 animate-pulse" />
          <span class="text-sm font-medium text-primary-700 dark:text-primary-300">
            {{ $t('header.patients', { count: store.patients.length }) }}
          </span>
        </div>

        <a
          href="https://github.com/1009476063/MedVista"
          target="_blank"
          class="hidden sm:flex p-2 rounded-xl text-accent-600 dark:text-accent-400 hover:bg-accent-100 dark:hover:bg-accent-800"
        >
          <BookOpenIcon class="w-5 h-5" />
        </a>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import { Bars3Icon, BookOpenIcon } from '@heroicons/vue/24/outline'

defineProps<{ sidebarCollapsed: boolean }>()
defineEmits<{
  'toggle-sidebar': []
  'toggle-mobile': []
}>()

const route = useRoute()
const store = useAppStore()
const { t } = useI18n()
const pageTitle = computed(() => {
  const titleKey = route.meta?.titleKey as string
  return titleKey ? t(titleKey) : t('sidebar.nav.dashboard')
})
const pageDescription = computed(() => route.meta?.description as string)
</script>

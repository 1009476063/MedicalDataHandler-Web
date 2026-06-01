<template>
  <div class="h-full flex flex-col animate-fade-in">
    <div class="px-4 py-2 border-b border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900">
      <h1 class="text-lg font-semibold text-accent-900 dark:text-white">{{ $t('sr.title') }}</h1>
    </div>

    <div class="flex-1 overflow-y-auto p-4">
      <div v-if="!appStore.sessionId" class="flex items-center justify-center h-full">
        <div class="text-center">
          <DocumentTextIcon class="w-12 h-12 text-accent-300 dark:text-accent-600 mx-auto mb-3" />
          <h3 class="text-lg font-medium text-accent-900 dark:text-white">{{ $t('sr.noDataTitle') }}</h3>
          <p class="text-sm text-accent-500 dark:text-accent-400 mt-1">{{ $t('sr.noDataDesc') }}</p>
        </div>
      </div>

      <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <!-- Left: Document list -->
        <div class="lg:col-span-1 space-y-4">
          <div class="bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700 p-4">
            <div class="flex items-center justify-between mb-3">
              <label class="text-xs font-medium text-accent-600 dark:text-accent-400">{{ $t('sr.documents') }}</label>
              <button
                class="text-xs text-primary-500 hover:text-primary-600"
                @click="handleRefresh"
                :disabled="sr.loading.value"
              >
                {{ $t('sr.refresh') }}
              </button>
            </div>
            <div v-if="sr.loading.value && sr.documents.value.length === 0" class="text-center py-8 text-accent-400 text-sm">
              {{ $t('sr.loading') }}
            </div>
            <div v-else-if="sr.documents.value.length === 0" class="text-center py-8 text-accent-400 text-sm">
              {{ $t('sr.empty') }}
            </div>
            <div v-else class="space-y-2 max-h-[500px] overflow-y-auto">
              <button
                v-for="doc in sr.documents.value"
                :key="doc.id"
                class="w-full text-left px-3 py-2 rounded-lg border transition-colors"
                :class="sr.selectedDoc.value?.id === doc.id
                  ? 'border-primary-300 dark:border-primary-700 bg-primary-50 dark:bg-primary-900/20'
                  : 'border-accent-200 dark:border-accent-700 hover:bg-accent-50 dark:hover:bg-accent-700/50'"
                @click="sr.loadDocument(doc.id)"
              >
                <div class="text-sm font-medium text-accent-900 dark:text-white truncate">{{ doc.title }}</div>
                <div class="text-xs text-accent-500 dark:text-accent-400 mt-0.5">
                  {{ doc.patient_name }} · {{ doc.study_date }}
                </div>
              </button>
            </div>
          </div>

          <div v-if="sr.error.value" class="text-sm text-red-500 bg-red-50 dark:bg-red-900/20 rounded-lg p-3">
            {{ sr.error.value }}
          </div>
        </div>

        <!-- Right: Content tree -->
        <div class="lg:col-span-2">
          <div class="bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700">
            <div class="px-4 py-3 border-b border-accent-200 dark:border-accent-700 flex items-center justify-between">
              <div>
                <h3 class="text-sm font-medium text-accent-900 dark:text-white">
                  {{ sr.selectedDoc.value?.title || $t('sr.selectDocument') }}
                </h3>
                <p v-if="sr.selectedDoc.value" class="text-xs text-accent-500 dark:text-accent-400 mt-0.5">
                  {{ sr.selectedDoc.value.sr_type }} · {{ sr.selectedDoc.value.institution_name }}
                </p>
              </div>
              <button
                v-if="sr.selectedDoc.value"
                class="text-xs text-red-500 hover:text-red-700"
                @click="handleDelete"
              >
                {{ $t('sr.delete') }}
              </button>
            </div>
            <div class="p-4 max-h-[600px] overflow-y-auto">
              <div v-if="sr.contentTree.value.length === 0" class="text-center py-12 text-accent-400 text-sm">
                {{ $t('sr.noContent') }}
              </div>
              <SRContentTree v-else :nodes="sr.contentTree.value" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { useSR } from '@/composables/useSR'
import SRContentTree from '@/components/viewer/SRContentTree.vue'
import { DocumentTextIcon } from '@heroicons/vue/24/outline'

const appStore = useAppStore()
const sr = useSR()

onMounted(() => {
  if (appStore.sessionId) {
    sr.fetchDocuments(appStore.sessionId)
  }
})

function handleRefresh() {
  if (appStore.sessionId) {
    sr.fetchDocuments(appStore.sessionId)
  }
}

async function handleDelete() {
  if (!sr.selectedDoc.value) return
  await sr.deleteDocument(sr.selectedDoc.value.id)
}
</script>

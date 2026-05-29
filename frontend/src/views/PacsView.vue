<template>
  <div class="h-full flex flex-col animate-fade-in">
    <div class="flex items-center justify-between px-4 py-2 border-b border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900">
      <h1 class="text-lg font-semibold text-accent-900 dark:text-white">{{ $t('pacs.title') }}</h1>
      <button
        class="px-3 py-1.5 text-xs bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors"
        @click="showConnectDialog = true"
      >
        {{ $t('pacs.connect') }}
      </button>
    </div>

    <div class="flex-1 p-4 overflow-y-auto">
      <PacsBrowser
        :connections="dicomweb.connections.value"
        :studies="dicomweb.studies.value"
        :series-list="dicomweb.series.value"
        @connect="showConnectDialog = true"
        @disconnect="dicomweb.disconnect"
        @search="handleSearch"
        @select-study="handleSelectStudy"
      />
    </div>

    <PacsConnectionDialog
      :show="showConnectDialog"
      :loading="dicomweb.loading.value"
      :error="dicomweb.error.value"
      @close="showConnectDialog = false"
      @connect="dicomweb.connect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useDicomweb } from '@/composables/useDicomweb'
import PacsBrowser from '@/components/pacs/PacsBrowser.vue'
import PacsConnectionDialog from '@/components/pacs/PacsConnectionDialog.vue'

const dicomweb = useDicomweb()
const showConnectDialog = ref(false)
const activeConnection = ref('')

onMounted(() => {
  dicomweb.fetchConnections()
})

function handleSearch(connection: string) {
  activeConnection.value = connection
  dicomweb.searchStudies(connection)
}

function handleSelectStudy(studyUid: string) {
  if (activeConnection.value) {
    dicomweb.searchSeries(activeConnection.value, studyUid)
  }
}
</script>

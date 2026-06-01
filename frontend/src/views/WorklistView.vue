<template>
  <div class="h-full flex flex-col animate-fade-in">
    <div class="px-4 py-2 border-b border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900">
      <h1 class="text-lg font-semibold text-accent-900 dark:text-white">{{ $t('worklist.title') }}</h1>
    </div>

    <div class="flex-1 overflow-y-auto p-4">
      <div v-if="!appStore.sessionId" class="flex items-center justify-center h-full">
        <div class="text-center">
          <ClipboardDocumentListIcon class="w-12 h-12 text-accent-300 dark:text-accent-600 mx-auto mb-3" />
          <h3 class="text-lg font-medium text-accent-900 dark:text-white">{{ $t('worklist.noDataTitle') }}</h3>
          <p class="text-sm text-accent-500 dark:text-accent-400 mt-1">{{ $t('worklist.noDataDesc') }}</p>
        </div>
      </div>

      <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <!-- Left: Controls -->
        <div class="lg:col-span-1 space-y-4">
          <!-- Search -->
          <div class="bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700 p-4">
            <label class="block text-xs font-medium text-accent-600 dark:text-accent-400 mb-2">{{ $t('worklist.search') }}</label>
            <div class="flex gap-2">
              <input
                v-model="wl.searchQuery.value"
                type="text"
                :placeholder="$t('worklist.searchPlaceholder')"
                class="flex-1 px-3 py-2 text-sm rounded-lg border border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900 text-accent-900 dark:text-white"
                @keyup.enter="handleSearch"
              />
              <button
                class="px-3 py-2 text-sm bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
                :disabled="wl.loading.value"
                @click="handleSearch"
              >
                {{ $t('worklist.searchBtn') }}
              </button>
            </div>
          </div>

          <!-- Import/Export -->
          <div class="bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700 p-4">
            <label class="block text-xs font-medium text-accent-600 dark:text-accent-400 mb-2">{{ $t('worklist.actions') }}</label>
            <div class="flex gap-2">
              <label class="flex-1 px-3 py-2 text-sm bg-accent-100 dark:bg-accent-700 text-accent-700 dark:text-accent-300 rounded-lg hover:bg-accent-200 dark:hover:bg-accent-600 transition-colors text-center cursor-pointer">
                {{ $t('worklist.import') }}
                <input type="file" accept=".csv" class="hidden" @change="handleImport" />
              </label>
              <button
                class="flex-1 px-3 py-2 text-sm bg-accent-100 dark:bg-accent-700 text-accent-700 dark:text-accent-300 rounded-lg hover:bg-accent-200 dark:hover:bg-accent-600 transition-colors"
                @click="handleExport"
              >
                {{ $t('worklist.export') }}
              </button>
            </div>
          </div>

          <!-- Add item -->
          <div class="bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700 p-4">
            <label class="block text-xs font-medium text-accent-600 dark:text-accent-400 mb-2">{{ $t('worklist.addItem') }}</label>
            <div class="space-y-2">
              <input v-model="newItem.patient_name" :placeholder="$t('worklist.patientName')" class="w-full px-3 py-1.5 text-sm rounded-lg border border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900 text-accent-900 dark:text-white" />
              <input v-model="newItem.patient_id" :placeholder="$t('worklist.patientId')" class="w-full px-3 py-1.5 text-sm rounded-lg border border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900 text-accent-900 dark:text-white" />
              <input v-model="newItem.accession_number" :placeholder="$t('worklist.accessionNumber')" class="w-full px-3 py-1.5 text-sm rounded-lg border border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900 text-accent-900 dark:text-white" />
              <input v-model="newItem.study_date" :placeholder="$t('worklist.studyDate')" class="w-full px-3 py-1.5 text-sm rounded-lg border border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900 text-accent-900 dark:text-white" />
              <button
                class="w-full px-3 py-2 text-sm bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
                :disabled="!newItem.patient_name || wl.loading.value"
                @click="handleAdd"
              >
                {{ $t('worklist.add') }}
              </button>
            </div>
          </div>

          <!-- Remote query -->
          <div class="bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700 p-4">
            <label class="block text-xs font-medium text-accent-600 dark:text-accent-400 mb-2">{{ $t('worklist.remoteQuery') }}</label>
            <div class="space-y-2">
              <input v-model="remoteUrl" :placeholder="$t('worklist.remoteUrl')" class="w-full px-3 py-1.5 text-sm rounded-lg border border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900 text-accent-900 dark:text-white" />
              <input v-model="remoteToken" type="password" :placeholder="$t('worklist.remoteToken')" class="w-full px-3 py-1.5 text-sm rounded-lg border border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900 text-accent-900 dark:text-white" />
              <button
                class="w-full px-3 py-2 text-sm bg-accent-100 dark:bg-accent-700 text-accent-700 dark:text-accent-300 rounded-lg hover:bg-accent-200 dark:hover:bg-accent-600 transition-colors"
                :disabled="!remoteUrl || wl.loading.value"
                @click="handleRemoteQuery"
              >
                {{ $t('worklist.queryRemote') }}
              </button>
            </div>
          </div>

          <div v-if="wl.error.value" class="text-sm text-red-500 bg-red-50 dark:bg-red-900/20 rounded-lg p-3">
            {{ wl.error.value }}
          </div>
        </div>

        <!-- Right: Table -->
        <div class="lg:col-span-2 space-y-4">
          <div class="bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700">
            <div class="px-4 py-3 border-b border-accent-200 dark:border-accent-700 flex items-center justify-between">
              <h3 class="text-sm font-medium text-accent-900 dark:text-white">
                {{ $t('worklist.items') }} ({{ wl.items.value.length }})
              </h3>
            </div>
            <div class="max-h-[600px] overflow-y-auto">
              <table class="w-full text-xs">
                <thead class="sticky top-0 bg-accent-50 dark:bg-accent-800">
                  <tr>
                    <th class="px-3 py-2 text-left font-medium text-accent-600 dark:text-accent-400">{{ $t('worklist.patientName') }}</th>
                    <th class="px-3 py-2 text-left font-medium text-accent-600 dark:text-accent-400">{{ $t('worklist.patientId') }}</th>
                    <th class="px-3 py-2 text-left font-medium text-accent-600 dark:text-accent-400">{{ $t('worklist.accessionNumber') }}</th>
                    <th class="px-3 py-2 text-left font-medium text-accent-600 dark:text-accent-400">{{ $t('worklist.studyDate') }}</th>
                    <th class="px-3 py-2 text-left font-medium text-accent-600 dark:text-accent-400">{{ $t('worklist.modality') }}</th>
                    <th class="px-3 py-2 text-left font-medium text-accent-600 dark:text-accent-400">{{ $t('worklist.status') }}</th>
                    <th class="px-3 py-2 text-right font-medium text-accent-600 dark:text-accent-400"></th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-accent-100 dark:divide-accent-700">
                  <tr
                    v-for="item in wl.items.value"
                    :key="item.id"
                    class="hover:bg-accent-50 dark:hover:bg-accent-700/50 cursor-pointer"
                    :class="selectedId === item.id ? 'bg-primary-50 dark:bg-primary-900/20' : ''"
                    @click="selectedId = item.id"
                  >
                    <td class="px-3 py-2 text-accent-900 dark:text-white">{{ item.patient_name }}</td>
                    <td class="px-3 py-2 font-mono text-accent-600 dark:text-accent-400">{{ item.patient_id }}</td>
                    <td class="px-3 py-2 font-mono text-accent-600 dark:text-accent-400">{{ item.accession_number }}</td>
                    <td class="px-3 py-2 text-accent-600 dark:text-accent-400">{{ item.study_date }}</td>
                    <td class="px-3 py-2">
                      <span class="px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
                        {{ item.modality }}
                      </span>
                    </td>
                    <td class="px-3 py-2 text-accent-600 dark:text-accent-400">{{ item.scheduled_step_status }}</td>
                    <td class="px-3 py-2 text-right">
                      <button
                        class="text-red-500 hover:text-red-700 text-xs"
                        @click.stop="handleDelete(item.id)"
                      >{{ $t('worklist.deleteBtn') }}</button>
                    </td>
                  </tr>
                </tbody>
              </table>
              <div v-if="wl.items.value.length === 0" class="flex items-center justify-center h-32 text-accent-400 text-sm">
                {{ $t('worklist.empty') }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { useWorklist } from '@/composables/useWorklist'
import { ClipboardDocumentListIcon } from '@heroicons/vue/24/outline'

const appStore = useAppStore()
const wl = useWorklist()

const selectedId = ref('')
const remoteUrl = ref('')
const remoteToken = ref('')
const newItem = ref({
  patient_name: '',
  patient_id: '',
  accession_number: '',
  study_date: '',
  modality: '',
})

onMounted(() => {
  if (appStore.sessionId) {
    wl.search(appStore.sessionId)
  }
})

function handleSearch() {
  if (appStore.sessionId) {
    wl.search(appStore.sessionId, wl.searchQuery.value)
  }
}

async function handleImport(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file || !appStore.sessionId) return
  await wl.importCsv(appStore.sessionId, file)
  input.value = ''
}

async function handleExport() {
  if (!appStore.sessionId) return
  const csv = await wl.exportCsv(appStore.sessionId)
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'worklist.csv'
  a.click()
  URL.revokeObjectURL(url)
}

async function handleAdd() {
  if (!appStore.sessionId) return
  await wl.addItem(appStore.sessionId, newItem.value)
  newItem.value = { patient_name: '', patient_id: '', accession_number: '', study_date: '', modality: '' }
}

async function handleDelete(id: string) {
  if (!appStore.sessionId) return
  await wl.deleteItem(appStore.sessionId, id)
  if (selectedId.value === id) selectedId.value = ''
}

async function handleRemoteQuery() {
  const results = await wl.remoteQuery({
    base_url: remoteUrl.value,
    auth_token: remoteToken.value || undefined,
  })
  if (appStore.sessionId) {
    for (const item of results) {
      await wl.addItem(appStore.sessionId, item)
    }
  }
}
</script>

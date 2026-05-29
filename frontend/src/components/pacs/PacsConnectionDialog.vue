<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="show"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
        @click.self="$emit('close')"
      >
        <div class="bg-white dark:bg-accent-900 rounded-xl border border-accent-200 dark:border-accent-700 shadow-xl max-w-sm w-full mx-4 p-6 animate-scale-in">
          <h3 class="text-lg font-semibold text-accent-900 dark:text-white mb-4">Connect to PACS</h3>
          <div class="space-y-3">
            <div>
              <label class="block text-xs text-accent-500 mb-1">Connection Name</label>
              <input
                v-model="form.name"
                type="text"
                placeholder="e.g. Local Orthanc"
                class="w-full px-3 py-2 bg-accent-50 dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white placeholder-accent-400 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              />
            </div>
            <div>
              <label class="block text-xs text-accent-500 mb-1">DICOMweb Base URL</label>
              <input
                v-model="form.baseUrl"
                type="url"
                placeholder="http://localhost:8042/dicom-web"
                class="w-full px-3 py-2 bg-accent-50 dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white placeholder-accent-400 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              />
            </div>
            <div>
              <label class="block text-xs text-accent-500 mb-1">Auth Token (optional)</label>
              <input
                v-model="form.token"
                type="password"
                placeholder="Bearer token"
                class="w-full px-3 py-2 bg-accent-50 dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded-lg text-sm text-accent-900 dark:text-white placeholder-accent-400 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              />
            </div>
            <p v-if="error" class="text-xs text-red-500">{{ error }}</p>
          </div>
          <div class="flex justify-end gap-3 mt-6">
            <button
              class="px-4 py-2 text-sm text-accent-700 dark:text-accent-300 hover:bg-accent-100 dark:hover:bg-accent-800 rounded-lg transition-colors"
              @click="$emit('close')"
            >
              Cancel
            </button>
            <button
              :disabled="!form.name || !form.baseUrl || loading"
              class="px-4 py-2 text-sm bg-primary-500 hover:bg-primary-600 disabled:opacity-50 text-white rounded-lg transition-colors"
              @click="handleConnect"
            >
              {{ loading ? 'Connecting...' : 'Connect' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { reactive } from 'vue'

defineProps<{
  show: boolean
  loading: boolean
  error: string
}>()

const emit = defineEmits<{
  close: []
  connect: [name: string, baseUrl: string, token?: string]
}>()

const form = reactive({
  name: '',
  baseUrl: '',
  token: '',
})

function handleConnect() {
  emit('connect', form.name, form.baseUrl, form.token || undefined)
}
</script>

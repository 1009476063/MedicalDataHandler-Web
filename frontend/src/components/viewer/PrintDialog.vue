<template>
  <Transition name="fade">
    <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="$emit('close')">
      <div class="bg-white dark:bg-accent-800 rounded-2xl border border-accent-200 dark:border-accent-700 shadow-xl w-full max-w-md mx-4 overflow-hidden">
        <div class="px-5 py-4 border-b border-accent-200 dark:border-accent-700 flex items-center justify-between">
          <h3 class="text-base font-semibold text-accent-900 dark:text-white">{{ $t('print.title') }}</h3>
          <button class="text-accent-400 hover:text-accent-600" @click="$emit('close')">
            <XMarkIcon class="w-5 h-5" />
          </button>
        </div>

        <div class="p-5 space-y-4">
          <!-- Printer selection -->
          <div>
            <label class="block text-xs font-medium text-accent-600 dark:text-accent-400 mb-1">{{ $t('print.printer') }}</label>
            <select
              v-model="selectedPrinterId"
              class="w-full px-3 py-2 text-sm rounded-lg border border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900 text-accent-900 dark:text-white"
            >
              <option value="">{{ $t('print.selectPrinter') }}</option>
              <option v-for="p in print.printers.value" :key="p.id" :value="p.id">
                {{ p.name }} ({{ p.ae_title }}@{{ p.host }}:{{ p.port }})
              </option>
            </select>
          </div>

          <!-- Film size -->
          <div>
            <label class="block text-xs font-medium text-accent-600 dark:text-accent-400 mb-1">{{ $t('print.filmSize') }}</label>
            <select
              v-model="filmSize"
              class="w-full px-3 py-2 text-sm rounded-lg border border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900 text-accent-900 dark:text-white"
            >
              <option v-for="size in filmSizes" :key="size" :value="size">{{ size }}</option>
            </select>
          </div>

          <!-- Orientation -->
          <div>
            <label class="block text-xs font-medium text-accent-600 dark:text-accent-400 mb-1">{{ $t('print.orientation') }}</label>
            <div class="flex gap-2">
              <button
                v-for="opt in orientationOptions"
                :key="opt.value"
                class="flex-1 px-3 py-2 text-sm rounded-lg border transition-colors"
                :class="orientation === opt.value
                  ? 'border-primary-300 dark:border-primary-700 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300'
                  : 'border-accent-200 dark:border-accent-700 text-accent-600 dark:text-accent-400 hover:bg-accent-50 dark:hover:bg-accent-700/50'"
                @click="orientation = opt.value"
              >
                {{ opt.label }}
              </button>
            </div>
          </div>

          <!-- Status -->
          <div v-if="print.currentJob.value" class="flex items-center gap-2 text-sm">
            <span
              class="inline-block w-2 h-2 rounded-full"
              :class="print.currentJob.value.status === 'completed' ? 'bg-green-500' : 'bg-yellow-500'"
            />
            <span class="text-accent-600 dark:text-accent-400">
              {{ $t('print.status') }}: {{ print.currentJob.value.status }}
            </span>
          </div>

          <div v-if="print.error.value" class="text-sm text-red-500 bg-red-50 dark:bg-red-900/20 rounded-lg p-3">
            {{ print.error.value }}
          </div>
        </div>

        <div class="px-5 py-4 border-t border-accent-200 dark:border-accent-700 flex justify-end gap-2">
          <button
            class="px-4 py-2 text-sm rounded-lg border border-accent-200 dark:border-accent-700 text-accent-600 dark:text-accent-400 hover:bg-accent-50 dark:hover:bg-accent-700/50"
            @click="$emit('close')"
          >
            {{ $t('print.cancel') }}
          </button>
          <button
            class="px-4 py-2 text-sm rounded-lg bg-primary-500 text-white hover:bg-primary-600 transition-colors disabled:opacity-50"
            :disabled="!selectedPrinterId || print.loading.value"
            @click="handlePrint"
          >
            {{ print.loading.value ? $t('print.sending') : $t('print.send') }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usePrint } from '@/composables/usePrint'
import { XMarkIcon } from '@heroicons/vue/24/outline'

const props = defineProps<{ visible: boolean; imageDataUrl?: string }>()
defineEmits<{ close: [] }>()

const print = usePrint()

const selectedPrinterId = ref('')
const filmSize = ref('8X10')
const orientation = ref('PORTRAIT')

const filmSizes = ['8X10', '10X12', '11X14', '14X17']
const orientationOptions = [
  { value: 'PORTRAIT', label: 'Portrait' },
  { value: 'LANDSCAPE', label: 'Landscape' },
]

onMounted(() => {
  print.fetchPrinters()
})

function handlePrint() {
  print.sendPrint(selectedPrinterId.value, props.imageDataUrl || '', {
    film_size: filmSize.value,
    orientation: orientation.value,
  })
}
</script>

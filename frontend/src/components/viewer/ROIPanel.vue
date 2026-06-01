<template>
  <div class="space-y-4">
    <!-- Labels -->
    <div>
      <div class="flex items-center justify-between mb-2">
        <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300">{{ $t('roi.labels') }}</h3>
        <button
          class="px-1.5 py-0.5 text-[10px] rounded bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 hover:bg-primary-200 dark:hover:bg-primary-900/50 transition-colors"
          @click="addNewLabel"
        >
          + {{ $t('roi.addLabel') }}
        </button>
      </div>
      <div class="space-y-1">
        <div
          v-for="label in labels"
          :key="label.id"
          :class="[
            'flex items-center gap-2 px-2 py-1.5 rounded text-xs cursor-pointer transition-colors',
            activeLabel === label.id
              ? 'bg-primary-100 dark:bg-primary-900/30 ring-1 ring-primary-500/50'
              : 'hover:bg-accent-50 dark:hover:bg-accent-800/50',
          ]"
          @click="$emit('select-label', label.id)"
        >
          <input
            type="color"
            :value="label.color"
            class="w-5 h-5 rounded border-0 cursor-pointer flex-shrink-0"
            @input="$emit('update-label-color', label.id, ($event.target as HTMLInputElement).value)"
          />
          <span class="flex-1 truncate text-accent-700 dark:text-accent-300">{{ label.name }}</span>
          <button
            class="p-0.5 rounded hover:bg-accent-200 dark:hover:bg-accent-700 text-accent-400 transition-colors"
            :title="$t('roi.rename')"
            @click.stop="renameLabel(label)"
          >
            ✎
          </button>
          <button
            class="p-0.5 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-accent-400 hover:text-red-500 transition-colors"
            :title="$t('roi.remove')"
            @click.stop="$emit('remove-label', label.id)"
          >
            ✕
          </button>
        </div>
      </div>
    </div>

    <!-- Morphology -->
    <div>
      <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">{{ $t('roi.postProcessing') }}</h3>
      <div class="flex flex-wrap gap-1">
        <button
          class="px-2 py-1 text-xs rounded bg-accent-100 dark:bg-accent-800 text-accent-700 dark:text-accent-300 hover:bg-accent-200 dark:hover:bg-accent-700 transition-colors"
          @click="$emit('erode')"
        >
          {{ $t('roi.erode') }}
        </button>
        <button
          class="px-2 py-1 text-xs rounded bg-accent-100 dark:bg-accent-800 text-accent-700 dark:text-accent-300 hover:bg-accent-200 dark:hover:bg-accent-700 transition-colors"
          @click="$emit('dilate')"
        >
          {{ $t('roi.dilate') }}
        </button>
        <button
          class="px-2 py-1 text-xs rounded bg-accent-100 dark:bg-accent-800 text-accent-700 dark:text-accent-300 hover:bg-accent-200 dark:hover:bg-accent-700 transition-colors"
          @click="$emit('smooth')"
        >
          {{ $t('roi.smooth') }}
        </button>
        <button
          class="px-2 py-1 text-xs rounded bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors"
          @click="$emit('clear-label')"
        >
          {{ $t('roi.clear') }}
        </button>
      </div>
    </div>

    <!-- AI Segmentation -->
    <div>
      <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">{{ $t('roi.aiSegmentation') }}</h3>
      <div class="space-y-2">
        <button
          :disabled="aiLoading"
          class="w-full px-3 py-1.5 text-xs rounded bg-primary-500 text-white hover:bg-primary-600 disabled:opacity-50 transition-colors"
          @click="$emit('run-auto-segment')"
        >
          {{ aiLoading ? $t('roi.running') : $t('roi.autoSegment') }}
        </button>
        <div class="flex gap-1">
          <input
            v-model="textPrompt"
            type="text"
            :placeholder="$t('roi.textPromptPlaceholder')"
            class="flex-1 px-2 py-1 text-xs bg-accent-50 dark:bg-accent-800 border border-accent-200 dark:border-accent-700 rounded text-accent-900 dark:text-white placeholder-accent-400 focus:outline-none focus:ring-1 focus:ring-primary-500/50"
            @keyup.enter="onTextSegment"
          />
          <button
            :disabled="aiLoading || !textPrompt"
            class="px-2 py-1 text-xs rounded bg-accent-100 dark:bg-accent-800 text-accent-700 dark:text-accent-300 hover:bg-accent-200 dark:hover:bg-accent-700 disabled:opacity-50 transition-colors"
            @click="onTextSegment"
          >
            {{ $t('roi.go') }}
          </button>
        </div>
        <button
          :disabled="aiLoading"
          class="w-full px-3 py-1.5 text-xs rounded bg-accent-100 dark:bg-accent-800 text-accent-700 dark:text-accent-300 hover:bg-accent-200 dark:hover:bg-accent-700 disabled:opacity-50 transition-colors"
          @click="$emit('run-reference-segment')"
        >
          {{ $t('roi.refSegment') }}
        </button>
        <div v-if="aiLoading" class="space-y-1">
          <div class="w-full bg-accent-200 dark:bg-accent-700 rounded-full h-1.5">
            <div
              class="bg-primary-500 h-1.5 rounded-full transition-all"
              :style="{ width: `${aiProgress}%` }"
            />
          </div>
          <p class="text-[10px] text-accent-500 text-center">{{ aiMessage }}</p>
        </div>
      </div>
    </div>

    <!-- Export -->
    <div>
      <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">{{ $t('roi.export') }}</h3>
      <div class="flex flex-wrap gap-1">
        <button
          class="px-2 py-1 text-xs rounded bg-accent-100 dark:bg-accent-800 text-accent-700 dark:text-accent-300 hover:bg-accent-200 dark:hover:bg-accent-700 transition-colors"
          @click="$emit('export-nifti')"
        >
          NIfTI
        </button>
        <button
          class="px-2 py-1 text-xs rounded bg-accent-100 dark:bg-accent-800 text-accent-700 dark:text-accent-300 hover:bg-accent-200 dark:hover:bg-accent-700 transition-colors"
          @click="$emit('export-dicom-seg')"
        >
          DICOM SEG
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { ROILabel } from '@/types'

const { t } = useI18n()

defineProps<{
  labels: ROILabel[]
  activeLabel: number
  aiLoading: boolean
  aiProgress: number
  aiMessage: string
}>()

const emit = defineEmits<{
  'select-label': [id: number]
  'add-label': []
  'update-label-color': [id: number, color: string]
  'rename-label': [id: number, name: string]
  'remove-label': [id: number]
  erode: []
  dilate: []
  smooth: []
  'clear-label': []
  'run-auto-segment': []
  'run-text-segment': [prompt: string]
  'run-reference-segment': []
  'export-nifti': []
  'export-dicom-seg': []
}>()

const textPrompt = ref('')

function addNewLabel() {
  emit('add-label')
}

function renameLabel(label: ROILabel) {
  const newName = prompt(t('roi.renamePrompt'), label.name)
  if (newName && newName !== label.name) {
    emit('rename-label', label.id, newName)
  }
}

function onTextSegment() {
  if (textPrompt.value) {
    emit('run-text-segment', textPrompt.value)
    textPrompt.value = ''
  }
}
</script>

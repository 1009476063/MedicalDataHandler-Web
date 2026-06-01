<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import type { AIModel } from '@/types'

const { t } = useI18n()

const props = defineProps<{
  models: AIModel[]
  loading: boolean
  progress: number
  progressMessage: string
  analysisResult: Record<string, unknown> | null
  confidenceThreshold: number
  studySummary: { summary: string; key_findings: string[]; recommendations: string[] } | null
  summaryLoading: boolean
}>()

const emit = defineEmits<{
  (e: 'fetch-models'): void
  (e: 'run-analysis', modelId: string, prompt: string, sliceStrategy: string): void
  (e: 'reset'): void
  (e: 'create-sr'): void
  (e: 'generate-summary'): void
}>()

const selectedModel = defineModel<string>('selectedModel', { default: 'gpt-4o' })
const prompt = defineModel<string>('prompt', { default: '' })
const sliceStrategy = defineModel<string>('sliceStrategy', { default: 'middle' })

const findings = computed(() => {
  if (!props.analysisResult) return []
  return (props.analysisResult.findings as Array<{
    region: string
    description: string
    confidence: number
    severity: string
  }>) || []
})

const highConfidenceFindings = computed(() =>
  findings.value.filter(f => f.confidence >= props.confidenceThreshold),
)

const lowConfidenceFindings = computed(() =>
  findings.value.filter(f => f.confidence < props.confidenceThreshold),
)

const showLowConfidence = ref(false)

watch(() => props.analysisResult, () => {
  showLowConfidence.value = false
})

const summary = computed(() => {
  return (props.analysisResult?.summary as string) || ''
})

const progressPercent = computed(() => Math.round(props.progress * 100))

const severityColor = (severity: string) => {
  switch (severity) {
    case 'severe': return 'text-red-400'
    case 'moderate': return 'text-yellow-400'
    case 'mild': return 'text-blue-400'
    default: return 'text-green-400'
  }
}

onMounted(() => {
  if (props.models.length === 0) {
    emit('fetch-models')
  }
})
</script>

<template>
  <div class="space-y-3">
    <!-- Model Selection -->
    <div>
      <label class="block text-xs text-slate-400 mb-1">{{ t('viewer.ai.model') }}</label>
      <select
        v-model="selectedModel"
        class="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1.5 text-sm text-white focus:border-teal-500 focus:outline-none"
        :disabled="loading"
      >
        <option v-for="m in models" :key="m.id" :value="m.id">{{ m.name }}</option>
      </select>
    </div>

    <!-- Custom Prompt -->
    <div>
      <label class="block text-xs text-slate-400 mb-1">{{ t('viewer.ai.prompt') }}</label>
      <textarea
        v-model="prompt"
        :placeholder="t('viewer.ai.promptPlaceholder')"
        class="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1.5 text-sm text-white resize-none focus:border-teal-500 focus:outline-none"
        rows="2"
        :disabled="loading"
      />
    </div>

    <!-- Slice Strategy -->
    <div>
      <label class="block text-xs text-slate-400 mb-1">{{ t('viewer.ai.sliceStrategy') }}</label>
      <select
        v-model="sliceStrategy"
        class="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1.5 text-sm text-white focus:border-teal-500 focus:outline-none"
        :disabled="loading"
      >
        <option value="middle">{{ t('viewer.ai.sliceMiddle') }}</option>
        <option value="multi">{{ t('viewer.ai.sliceMulti') }}</option>
        <option value="mip">{{ t('viewer.ai.sliceMip') }}</option>
      </select>
    </div>

    <!-- Run / Reset -->
    <div class="flex gap-2">
      <button
        class="flex-1 px-3 py-1.5 rounded text-sm font-medium transition-colors"
        :class="loading
          ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
          : 'bg-teal-600 hover:bg-teal-500 text-white'"
        :disabled="loading"
        @click="emit('run-analysis', selectedModel, prompt, sliceStrategy)"
      >
        {{ loading ? t('viewer.ai.analyzing') : t('viewer.ai.run') }}
      </button>
      <button
        v-if="analysisResult || loading"
        class="px-3 py-1.5 rounded text-sm bg-slate-700 hover:bg-slate-600 text-slate-300 transition-colors"
        @click="emit('reset')"
      >
        {{ t('viewer.ai.reset') }}
      </button>
    </div>

    <!-- Progress -->
    <div v-if="loading" class="space-y-1">
      <div class="flex justify-between text-xs text-slate-400">
        <span>{{ progressMessage }}</span>
        <span>{{ progressPercent }}%</span>
      </div>
      <div class="w-full bg-slate-700 rounded-full h-1.5">
        <div
          class="bg-teal-500 h-1.5 rounded-full transition-all duration-300"
          :style="{ width: progressPercent + '%' }"
        />
      </div>
    </div>

    <!-- Error -->
    <div v-if="!loading && !analysisResult && progressMessage" class="bg-red-900/30 border border-red-500/30 rounded p-2">
      <p class="text-xs text-red-400">{{ progressMessage }}</p>
    </div>

    <!-- Results -->
    <div v-if="analysisResult && !loading" class="space-y-2">
      <h4 class="text-xs font-semibold text-slate-300 uppercase tracking-wide">
        {{ t('viewer.ai.findings') }}
      </h4>

      <!-- Summary -->
      <p v-if="summary" class="text-xs text-slate-400 bg-slate-800/50 rounded p-2">
        {{ summary }}
      </p>

      <!-- Findings list (high confidence) -->
      <div v-for="(f, i) in highConfidenceFindings" :key="'h-' + i" class="bg-slate-800/50 rounded p-2 space-y-1">
        <div class="flex items-center justify-between">
          <span class="text-xs font-medium text-white">{{ f.region }}</span>
          <span class="text-xs" :class="severityColor(f.severity)">{{ f.severity }}</span>
        </div>
        <p class="text-xs text-slate-400">{{ f.description }}</p>
        <div class="flex items-center gap-2">
          <div class="flex-1 bg-slate-700 rounded-full h-1">
            <div
              class="bg-teal-500 h-1 rounded-full"
              :style="{ width: (f.confidence * 100) + '%' }"
            />
          </div>
          <span class="text-xs text-slate-500">{{ Math.round(f.confidence * 100) }}%</span>
        </div>
      </div>

      <!-- Low Confidence (collapsible) -->
      <div v-if="lowConfidenceFindings.length > 0">
        <button
          class="w-full flex items-center justify-between text-xs text-slate-500 hover:text-slate-300 py-1 transition-colors"
          @click="showLowConfidence = !showLowConfidence"
        >
          <span>{{ t('viewer.ai.lowConfidence') }} ({{ lowConfidenceFindings.length }})</span>
          <svg :class="['w-3 h-3 transition-transform', showLowConfidence ? 'rotate-180' : '']" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        <div v-if="showLowConfidence" class="space-y-2 mt-1">
          <div v-for="(f, i) in lowConfidenceFindings" :key="'l-' + i" class="bg-slate-800/30 rounded p-2 space-y-1 opacity-60">
            <div class="flex items-center justify-between">
              <span class="text-xs font-medium text-white">{{ f.region }}</span>
              <span class="text-xs" :class="severityColor(f.severity)">{{ f.severity }}</span>
            </div>
            <p class="text-xs text-slate-400">{{ f.description }}</p>
            <div class="flex items-center gap-2">
              <div class="flex-1 bg-slate-700 rounded-full h-1">
                <div
                  class="bg-yellow-500 h-1 rounded-full"
                  :style="{ width: (f.confidence * 100) + '%' }"
                />
              </div>
              <span class="text-xs text-slate-500">{{ Math.round(f.confidence * 100) }}%</span>
            </div>
          </div>
        </div>
      </div>

      <p v-if="findings.length === 0" class="text-xs text-slate-500 italic">
        {{ t('viewer.ai.noFindings') }}
      </p>

      <!-- Create SR Report button -->
      <button
        v-if="findings.length > 0"
        class="w-full px-3 py-1.5 rounded text-sm font-medium bg-blue-600 hover:bg-blue-500 text-white transition-colors"
        @click="emit('create-sr')"
      >
        {{ t('viewer.ai.createSr') }}
      </button>

      <!-- Generate Summary button -->
      <button
        v-if="findings.length > 0 && !studySummary"
        class="w-full px-3 py-1.5 rounded text-sm font-medium bg-purple-600 hover:bg-purple-500 text-white transition-colors"
        :disabled="summaryLoading"
        @click="emit('generate-summary')"
      >
        {{ summaryLoading ? t('viewer.ai.analyzing') : t('viewer.ai.generateSummary') }}
      </button>

      <!-- Study Summary Display -->
      <div v-if="studySummary" class="bg-slate-800/50 rounded p-3 space-y-2 border border-purple-500/30">
        <h4 class="text-xs font-semibold text-purple-300 uppercase tracking-wide">
          {{ t('viewer.ai.summaryTitle') }}
        </h4>
        <p class="text-xs text-slate-300">{{ studySummary.summary }}</p>
        <div v-if="studySummary.key_findings.length > 0">
          <h5 class="text-xs font-medium text-slate-400 mb-1">{{ t('viewer.ai.keyFindings') }}</h5>
          <ul class="space-y-0.5">
            <li v-for="(kf, i) in studySummary.key_findings" :key="i" class="text-xs text-slate-400 flex items-start gap-1">
              <span class="text-purple-400 mt-0.5">•</span>
              <span>{{ kf }}</span>
            </li>
          </ul>
        </div>
        <div v-if="studySummary.recommendations.length > 0">
          <h5 class="text-xs font-medium text-slate-400 mb-1">{{ t('viewer.ai.recommendations') }}</h5>
          <ul class="space-y-0.5">
            <li v-for="(rec, i) in studySummary.recommendations" :key="i" class="text-xs text-slate-400 flex items-start gap-1">
              <span class="text-teal-400 mt-0.5">→</span>
              <span>{{ rec }}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

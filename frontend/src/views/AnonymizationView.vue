<template>
  <div class="h-full flex flex-col animate-fade-in">
    <div class="px-4 py-2 border-b border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900">
      <h1 class="text-lg font-semibold text-accent-900 dark:text-white">{{ $t('anonymize.title') }}</h1>
    </div>

    <div class="flex-1 overflow-y-auto p-4">
      <div v-if="!appStore.sessionId" class="flex items-center justify-center h-full">
        <div class="text-center">
          <ShieldCheckIcon class="w-12 h-12 text-accent-300 dark:text-accent-600 mx-auto mb-3" />
          <h3 class="text-lg font-medium text-accent-900 dark:text-white">{{ $t('anonymize.noDataTitle') }}</h3>
          <p class="text-sm text-accent-500 dark:text-accent-400 mt-1">{{ $t('anonymize.noDataDesc') }}</p>
        </div>
      </div>

      <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <!-- Left: Controls -->
        <div class="lg:col-span-1 space-y-4">
          <!-- Patient selector -->
          <div class="bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700 p-4">
            <label class="block text-xs font-medium text-accent-600 dark:text-accent-400 mb-2">{{ $t('anonymize.patient') }}</label>
            <select
              v-model="selectedPatient"
              class="w-full px-3 py-2 text-sm rounded-lg border border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900 text-accent-900 dark:text-white"
            >
              <option value="">{{ $t('anonymize.selectPatient') }}</option>
              <option v-for="p in appStore.patients" :key="p.patient_id" :value="p.patient_id">{{ p.name || p.patient_id }}</option>
            </select>
          </div>

          <!-- Profile selector -->
          <div class="bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700 p-4">
            <label class="block text-xs font-medium text-accent-600 dark:text-accent-400 mb-2">{{ $t('anonymize.profile') }}</label>
            <div class="space-y-2">
              <label
                v-for="p in anon.profiles.value"
                :key="p.key"
                class="flex items-start gap-2 p-2 rounded-lg cursor-pointer transition-colors"
                :class="selectedProfile === p.key ? 'bg-primary-50 dark:bg-primary-900/20 ring-1 ring-primary-300 dark:ring-primary-700' : 'hover:bg-accent-50 dark:hover:bg-accent-700'"
              >
                <input type="radio" :value="p.key" v-model="selectedProfile" class="mt-0.5" />
                <div>
                  <div class="text-sm font-medium text-accent-900 dark:text-white">{{ p.name }}</div>
                  <div class="text-xs text-accent-500 dark:text-accent-400">{{ p.description }}</div>
                </div>
              </label>
            </div>
          </div>

          <!-- Options -->
          <div class="bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700 p-4">
            <label class="block text-xs font-medium text-accent-600 dark:text-accent-400 mb-2">{{ $t('anonymize.options') }}</label>
            <div class="space-y-3">
              <div>
                <label class="text-xs text-accent-600 dark:text-accent-400">{{ $t('anonymize.dateOffset') }}</label>
                <input
                  v-model.number="dateOffsetDays"
                  type="number"
                  :placeholder="$t('anonymize.dateOffsetPlaceholder')"
                  class="w-full mt-1 px-3 py-1.5 text-sm rounded-lg border border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900 text-accent-900 dark:text-white"
                />
              </div>
              <div>
                <label class="text-xs text-accent-600 dark:text-accent-400">{{ $t('anonymize.seed') }}</label>
                <input
                  v-model="seed"
                  type="text"
                  :placeholder="$t('anonymize.seedPlaceholder')"
                  class="w-full mt-1 px-3 py-1.5 text-sm rounded-lg border border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900 text-accent-900 dark:text-white"
                />
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex gap-2">
            <button
              class="flex-1 px-3 py-2 text-sm bg-accent-100 dark:bg-accent-700 text-accent-700 dark:text-accent-300 rounded-lg hover:bg-accent-200 dark:hover:bg-accent-600 transition-colors"
              :disabled="!selectedPatient || anon.loading.value"
              @click="handlePreview"
            >
              {{ $t('anonymize.preview') }}
            </button>
            <button
              class="flex-1 px-3 py-2 text-sm bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
              :disabled="!selectedPatient || anon.loading.value"
              @click="handleApply"
            >
              {{ anon.loading.value ? $t('anonymize.applying') : $t('anonymize.apply') }}
            </button>
          </div>

          <!-- Validate + Burned-in -->
          <div class="flex gap-2">
            <button
              class="flex-1 px-3 py-2 text-sm bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
              :disabled="!selectedPatient || anon.loading.value"
              @click="handleValidate"
            >
              {{ $t('anonymize.validate') }}
            </button>
            <button
              class="flex-1 px-3 py-2 text-sm bg-accent-100 dark:bg-accent-700 text-accent-700 dark:text-accent-300 rounded-lg hover:bg-accent-200 dark:hover:bg-accent-600 transition-colors"
              :disabled="!selectedPatient || anon.loading.value"
              @click="handleDetectBurnedIn"
            >
              {{ $t('anonymize.detectBurnedIn') }}
            </button>
          </div>

          <!-- AI Actions -->
          <div class="border-t border-accent-200 dark:border-accent-700 pt-3 space-y-2">
            <label class="block text-xs font-medium text-accent-600 dark:text-accent-400">AI {{ $t('anonymize.options') }}</label>
            <button
              class="w-full px-3 py-2 text-sm bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors flex items-center justify-center gap-2"
              :disabled="!selectedPatient || anon.loading.value || aiLoading"
              @click="handleAiBurnedIn"
            >
              <SparklesIcon class="w-4 h-4" />
              {{ aiLoading ? $t('anonymize.analyzing') : $t('anonymize.detectBurnedInAi') }}
            </button>
            <button
              class="w-full px-3 py-2 text-sm bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors flex items-center justify-center gap-2"
              :disabled="!selectedPatient || anon.loading.value || aiLoading"
              @click="handleAiCompliance"
            >
              <SparklesIcon class="w-4 h-4" />
              {{ aiLoading ? $t('anonymize.analyzing') : $t('anonymize.validateAi') }}
            </button>
          </div>

          <!-- Error -->
          <div v-if="anon.error.value" class="text-sm text-red-500 bg-red-50 dark:bg-red-900/20 rounded-lg p-3">
            {{ anon.error.value }}
          </div>
        </div>

        <!-- Right: Results -->
        <div class="lg:col-span-2 space-y-4">
          <!-- Preview diff -->
          <div v-if="anon.preview.value" class="bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700">
            <div class="px-4 py-3 border-b border-accent-200 dark:border-accent-700">
              <h3 class="text-sm font-medium text-accent-900 dark:text-white">
                {{ $t('anonymize.previewTitle') }} ({{ anon.preview.value.total }} {{ $t('anonymize.changes') }})
              </h3>
            </div>
            <div class="max-h-[500px] overflow-y-auto">
              <table class="w-full text-xs">
                <thead class="sticky top-0 bg-accent-50 dark:bg-accent-800">
                  <tr>
                    <th class="px-3 py-2 text-left font-medium text-accent-600 dark:text-accent-400">{{ $t('anonymize.colTag') }}</th>
                    <th class="px-3 py-2 text-left font-medium text-accent-600 dark:text-accent-400">{{ $t('anonymize.colOriginal') }}</th>
                    <th class="px-3 py-2 text-left font-medium text-accent-600 dark:text-accent-400">{{ $t('anonymize.colAction') }}</th>
                    <th class="px-3 py-2 text-left font-medium text-accent-600 dark:text-accent-400">{{ $t('anonymize.colNew') }}</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-accent-100 dark:divide-accent-700">
                  <tr v-for="(change, i) in anon.preview.value.changes" :key="i" class="hover:bg-accent-50 dark:hover:bg-accent-700/50">
                    <td class="px-3 py-1.5 font-mono text-accent-700 dark:text-accent-300">{{ change.tag }}</td>
                    <td class="px-3 py-1.5 text-accent-500 dark:text-accent-400 max-w-[200px] truncate">{{ change.original }}</td>
                    <td class="px-3 py-1.5">
                      <span class="px-1.5 py-0.5 rounded text-[10px] font-medium" :class="actionClass(change.action)">
                        {{ change.action }}
                      </span>
                    </td>
                    <td class="px-3 py-1.5 text-accent-500 dark:text-accent-400">{{ change.new_value || '—' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Apply result -->
          <div v-if="anon.result.value" class="bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700 p-4">
            <div class="flex items-center gap-2 mb-3">
              <CheckCircleIcon class="w-5 h-5 text-green-500" />
              <h3 class="text-sm font-medium text-accent-900 dark:text-white">{{ $t('anonymize.complete') }}</h3>
            </div>
            <div class="grid grid-cols-3 gap-4 text-center">
              <div>
                <div class="text-2xl font-bold text-accent-900 dark:text-white">{{ anon.result.value.files.length }}</div>
                <div class="text-xs text-accent-500">{{ $t('anonymize.filesAnonymized') }}</div>
              </div>
              <div>
                <div class="text-2xl font-bold text-accent-900 dark:text-white">{{ anon.result.value.total_changes }}</div>
                <div class="text-xs text-accent-500">{{ $t('anonymize.totalChanges') }}</div>
              </div>
              <div>
                <div class="text-2xl font-bold text-red-500">{{ anon.result.value.errors.length }}</div>
                <div class="text-xs text-accent-500">{{ $t('anonymize.errors') }}</div>
              </div>
            </div>
            <div v-if="anon.result.value.files.length > 0" class="mt-3 space-y-1">
              <div v-for="f in anon.result.value.files" :key="f.original_uid" class="flex items-center justify-between text-xs text-accent-600 dark:text-accent-400">
                <span class="font-mono">{{ f.original_uid }}</span>
                <span>{{ f.changes }} {{ $t('anonymize.changes') }}</span>
              </div>
            </div>
            <div v-if="anon.result.value.errors.length > 0" class="mt-3">
              <div v-for="(err, i) in anon.result.value.errors" :key="i" class="text-xs text-red-500">{{ err }}</div>
            </div>
          </div>

          <!-- Compliance validation result -->
          <div v-if="complianceResult" class="bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700 p-4">
            <div class="flex items-center gap-2 mb-3">
              <component
                :is="complianceResult.compliant ? CheckCircleIcon : ExclamationTriangleIcon"
                class="w-5 h-5"
                :class="complianceResult.compliant ? 'text-green-500' : 'text-red-500'"
              />
              <h3 class="text-sm font-medium text-accent-900 dark:text-white">
                {{ complianceResult.compliant ? $t('anonymize.compliancePassed') : $t('anonymize.complianceFailed') }}
              </h3>
              <span class="text-xs text-accent-500 dark:text-accent-400 ml-auto">
                {{ complianceResult.profile }} · {{ complianceResult.standard }}
              </span>
            </div>
            <div class="grid grid-cols-3 gap-4 text-center mb-3">
              <div>
                <div class="text-xl font-bold text-accent-900 dark:text-white">{{ complianceResult.checked_tags }}</div>
                <div class="text-xs text-accent-500">{{ $t('anonymize.checkedTags') }}</div>
              </div>
              <div>
                <div class="text-xl font-bold text-green-500">{{ complianceResult.passed }}</div>
                <div class="text-xs text-accent-500">{{ $t('anonymize.passed') }}</div>
              </div>
              <div>
                <div class="text-xl font-bold text-red-500">{{ complianceResult.failed }}</div>
                <div class="text-xs text-accent-500">{{ $t('anonymize.failed') }}</div>
              </div>
            </div>
            <!-- HIPAA 18 identifier coverage -->
            <div class="mb-3">
              <div class="flex justify-between text-xs text-accent-600 dark:text-accent-400 mb-1">
                <span>{{ $t('anonymize.hipaaCoverage') }}</span>
                <span>{{ Math.round((complianceResult.passed / Math.max(complianceResult.checked_tags, 1)) * 100) }}%</span>
              </div>
              <div class="w-full bg-accent-100 dark:bg-accent-700 rounded-full h-2">
                <div
                  class="h-2 rounded-full transition-all"
                  :class="complianceResult.compliant ? 'bg-green-500' : 'bg-red-500'"
                  :style="{ width: `${Math.round((complianceResult.passed / Math.max(complianceResult.checked_tags, 1)) * 100)}%` }"
                />
              </div>
            </div>
            <!-- Violations list -->
            <div v-if="complianceResult.violations.length > 0" class="space-y-1 max-h-[200px] overflow-y-auto">
              <div
                v-for="(v, i) in complianceResult.violations"
                :key="i"
                class="flex items-start gap-2 text-xs p-2 rounded bg-red-50 dark:bg-red-900/20"
              >
                <ExclamationTriangleIcon class="w-3.5 h-3.5 text-red-500 mt-0.5 shrink-0" />
                <div>
                  <span class="font-mono text-red-700 dark:text-red-300">{{ v.tag }}</span>
                  <span class="text-red-600 dark:text-red-400 ml-1">{{ v.message }}</span>
                  <span v-if="v.value" class="text-accent-400 ml-1">({{ v.value }})</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Burned-in annotation result -->
          <div v-if="burnedInResult" class="bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700 p-4">
            <div class="flex items-center gap-2">
              <component
                :is="burnedInResult.has_burned_in ? ExclamationTriangleIcon : CheckCircleIcon"
                class="w-5 h-5"
                :class="burnedInResult.has_burned_in ? 'text-yellow-500' : 'text-green-500'"
              />
              <h3 class="text-sm font-medium text-accent-900 dark:text-white">
                {{ burnedInResult.has_burned_in ? $t('anonymize.burnedInDetected') : $t('anonymize.burnedInClean') }}
              </h3>
            </div>
            <p class="text-xs text-accent-500 dark:text-accent-400 mt-1">
              {{ $t('anonymize.method') }}: {{ burnedInResult.method }} — {{ burnedInResult.details }}
            </p>
          </div>

          <!-- AI Burned-in detection result -->
          <div v-if="aiBurnedInResult" class="bg-white dark:bg-accent-800 rounded-xl border border-purple-200 dark:border-purple-700 p-4">
            <div class="flex items-center gap-2 mb-2">
              <SparklesIcon class="w-5 h-5 text-purple-500" />
              <h3 class="text-sm font-medium text-accent-900 dark:text-white">
                {{ $t('anonymize.aiBurnedInTitle') }}
              </h3>
            </div>
            <div class="flex items-center gap-2 mb-2">
              <component
                :is="aiBurnedInResult.detected ? ExclamationTriangleIcon : CheckCircleIcon"
                class="w-5 h-5"
                :class="aiBurnedInResult.detected ? 'text-yellow-500' : 'text-green-500'"
              />
              <span class="text-sm text-accent-700 dark:text-accent-300">
                {{ aiBurnedInResult.detected ? $t('anonymize.burnedInDetected') : $t('anonymize.burnedInClean') }}
              </span>
              <span class="text-xs text-accent-500 ml-auto">
                {{ $t('anonymize.confidence') }}: {{ Math.round(aiBurnedInResult.confidence * 100) }}%
              </span>
            </div>
            <div v-if="aiBurnedInResult.regions.length > 0" class="space-y-1 mt-2">
              <div
                v-for="(region, i) in aiBurnedInResult.regions"
                :key="i"
                class="flex items-start gap-2 text-xs p-2 rounded bg-yellow-50 dark:bg-yellow-900/20"
              >
                <ExclamationTriangleIcon class="w-3.5 h-3.5 text-yellow-500 mt-0.5 shrink-0" />
                <div>
                  <span class="font-medium text-yellow-700 dark:text-yellow-300">{{ region.type }}</span>
                  <span class="text-yellow-600 dark:text-yellow-400 ml-1">{{ region.description }}</span>
                  <span class="text-accent-400 ml-1">({{ Math.round(region.confidence * 100) }}%)</span>
                </div>
              </div>
            </div>
            <p v-if="aiBurnedInResult.raw_response" class="text-xs text-accent-400 mt-2 italic">{{ aiBurnedInResult.raw_response }}</p>
          </div>

          <!-- AI Compliance result -->
          <div v-if="aiComplianceResult" class="bg-white dark:bg-accent-800 rounded-xl border border-purple-200 dark:border-purple-700 p-4">
            <div class="flex items-center gap-2 mb-2">
              <SparklesIcon class="w-5 h-5 text-purple-500" />
              <h3 class="text-sm font-medium text-accent-900 dark:text-white">
                {{ $t('anonymize.aiComplianceTitle') }}
              </h3>
            </div>
            <div class="flex items-center gap-2 mb-2">
              <component
                :is="aiComplianceResult.compliant ? CheckCircleIcon : ExclamationTriangleIcon"
                class="w-5 h-5"
                :class="aiComplianceResult.compliant ? 'text-green-500' : 'text-red-500'"
              />
              <span class="text-sm text-accent-700 dark:text-accent-300">
                {{ aiComplianceResult.compliant ? $t('anonymize.compliancePassed') : $t('anonymize.complianceFailed') }}
              </span>
            </div>
            <p class="text-xs text-accent-600 dark:text-accent-400 mb-2">{{ aiComplianceResult.summary }}</p>
            <div v-if="aiComplianceResult.risks.length > 0" class="space-y-1">
              <div
                v-for="(risk, i) in aiComplianceResult.risks"
                :key="i"
                class="flex items-start gap-2 text-xs p-2 rounded bg-red-50 dark:bg-red-900/20"
              >
                <ExclamationTriangleIcon class="w-3.5 h-3.5 text-red-500 mt-0.5 shrink-0" />
                <div>
                  <span class="font-mono text-red-700 dark:text-red-300">{{ risk.tag }}</span>
                  <span class="text-red-600 dark:text-red-400 ml-1">{{ risk.risk }}</span>
                  <span class="text-accent-400 ml-1">({{ risk.severity }})</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Empty state -->
          <div v-if="!anon.preview.value && !anon.result.value && !complianceResult && !burnedInResult && !aiBurnedInResult && !aiComplianceResult" class="flex items-center justify-center h-64">
            <div class="text-center text-accent-400">
              <ShieldCheckIcon class="w-10 h-10 mx-auto mb-2 opacity-50" />
              <p class="text-sm">{{ $t('anonymize.selectHint') }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { useAnonymization, type ComplianceResult, type BurnedInResult, type AIBurnedInResult, type AIComplianceResult } from '@/composables/useAnonymization'
import { useSettings } from '@/composables/useSettings'
import { ShieldCheckIcon, CheckCircleIcon, ExclamationTriangleIcon, SparklesIcon } from '@heroicons/vue/24/outline'

const appStore = useAppStore()
const anon = useAnonymization()
const { defaultAnonProfile } = useSettings()
const selectedProfile = ref(defaultAnonProfile.value)

const selectedPatient = ref('')
const dateOffsetDays = ref<number | null>(null)
const seed = ref('')
const complianceResult = ref<ComplianceResult | null>(null)
const burnedInResult = ref<BurnedInResult | null>(null)
const aiBurnedInResult = ref<AIBurnedInResult | null>(null)
const aiComplianceResult = ref<AIComplianceResult | null>(null)
const aiLoading = ref(false)

onMounted(() => {
  anon.fetchProfiles()
})

watch(() => anon.profiles.value, (profiles) => {
  if (profiles.length > 0 && !profiles.some(p => p.key === selectedProfile.value)) {
    selectedProfile.value = profiles[0].key
  }
})

watch([selectedPatient, selectedProfile], () => {
  complianceResult.value = null
  burnedInResult.value = null
  aiBurnedInResult.value = null
  aiComplianceResult.value = null
})

function actionClass(action: string): string {
  switch (action) {
    case 'clear': return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
    case 'replace_uid': return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
    case 'offset_date': case 'offset_time': return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300'
    case 'remove_private': return 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300'
    default: return 'bg-accent-100 dark:bg-accent-700 text-accent-600 dark:text-accent-400'
  }
}

async function handlePreview() {
  if (!selectedPatient.value || !appStore.sessionId) return
  await anon.previewAnonymization(
    appStore.sessionId, selectedPatient.value,
    selectedProfile.value, undefined, dateOffsetDays.value ?? undefined, seed.value,
  )
}

async function handleApply() {
  if (!selectedPatient.value || !appStore.sessionId) return
  await anon.applyAnonymization(
    appStore.sessionId, selectedPatient.value,
    selectedProfile.value, undefined, dateOffsetDays.value ?? undefined, seed.value,
  )
}

async function handleValidate() {
  if (!selectedPatient.value || !appStore.sessionId) return
  complianceResult.value = await anon.validateCompliance(
    appStore.sessionId, selectedPatient.value, selectedProfile.value,
  )
}

async function handleDetectBurnedIn() {
  if (!selectedPatient.value || !appStore.sessionId) return
  burnedInResult.value = await anon.detectBurnedIn(
    appStore.sessionId, selectedPatient.value,
  )
}

async function handleAiBurnedIn() {
  if (!selectedPatient.value || !appStore.sessionId) return
  aiLoading.value = true
  try {
    aiBurnedInResult.value = await anon.detectBurnedInAi(
      appStore.sessionId, selectedPatient.value,
    )
  } finally {
    aiLoading.value = false
  }
}

async function handleAiCompliance() {
  if (!selectedPatient.value || !appStore.sessionId) return
  aiLoading.value = true
  try {
    aiComplianceResult.value = await anon.validateComplianceAi(
      appStore.sessionId, selectedPatient.value, selectedProfile.value,
    )
  } finally {
    aiLoading.value = false
  }
}
</script>

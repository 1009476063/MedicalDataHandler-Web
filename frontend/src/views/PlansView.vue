<template>
  <div class="h-full flex flex-col animate-fade-in">
    <div class="px-4 py-2 border-b border-accent-200 dark:border-accent-700 bg-white dark:bg-accent-900">
      <h1 class="text-lg font-semibold text-accent-900 dark:text-white">{{ $t('plans.title') }}</h1>
    </div>

    <div class="flex-1 overflow-y-auto p-4">
      <div v-if="!appStore.sessionId" class="flex items-center justify-center h-full">
        <div class="text-center">
          <svg class="w-12 h-12 text-accent-300 dark:text-accent-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
          </svg>
          <h3 class="text-lg font-medium text-accent-900 dark:text-white">{{ $t('plans.noDataTitle') }}</h3>
          <p class="text-sm text-accent-500 dark:text-accent-400 mt-1">{{ $t('plans.noDataDesc') }}</p>
        </div>
      </div>

      <div v-else-if="loading" class="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" :text="$t('plans.loadingPlans')" />
      </div>

      <div v-else-if="plans.length === 0" class="flex items-center justify-center h-64">
        <div class="text-center">
          <svg class="w-12 h-12 text-accent-300 dark:text-accent-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
          </svg>
          <h3 class="text-lg font-medium text-accent-900 dark:text-white">{{ $t('plans.noPlansTitle') }}</h3>
          <p class="text-sm text-accent-500 dark:text-accent-400 mt-1">{{ $t('plans.noPlansDesc') }}</p>
        </div>
      </div>

      <div v-else class="space-y-4">
        <div
          v-for="(plan, idx) in plans"
          :key="idx"
          class="bg-white dark:bg-accent-800 rounded-xl border border-accent-200 dark:border-accent-700 overflow-hidden"
        >
          <div
            class="px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-accent-50 dark:hover:bg-accent-700/50 transition-colors"
            @click="togglePlanExpand(idx)"
          >
            <div class="flex items-center gap-3">
              <StatusBadge status="RTPLAN" />
              <div>
                <p class="text-sm font-medium text-accent-900 dark:text-white">
                  {{ plan.plan_label || `Plan ${idx + 1}` }}
                </p>
                <p class="text-xs text-accent-500 dark:text-accent-400">
                  {{ plan.file_count > 1 ? $t('plans.planInfo', { patient: plan.patient_id, count: plan.file_count || 1 }) : $t('plans.planInfoSingle', { patient: plan.patient_id }) }}
                </p>
              </div>
            </div>
            <svg
              :class="['w-5 h-5 text-accent-400 transition-transform', expandedPlans.has(idx) ? 'rotate-180' : '']"
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
            </svg>
          </div>

          <div v-if="expandedPlans.has(idx)" class="border-t border-accent-200 dark:border-accent-700">
            <!-- Plan info -->
            <div class="p-4 grid grid-cols-2 md:grid-cols-4 gap-4">
              <div v-for="(info, key) in plan.info" :key="key">
                <p class="text-xs text-accent-500 dark:text-accent-400">{{ formatKey(String(key)) }}</p>
                <p class="text-sm font-medium text-accent-900 dark:text-white">{{ info }}</p>
              </div>
            </div>

            <!-- Beam list -->
            <div v-if="plan.beams && plan.beams.length > 0" class="border-t border-accent-200 dark:border-accent-700">
              <div class="px-4 py-2 bg-accent-50 dark:bg-accent-700/50">
                <h4 class="text-sm font-medium text-accent-700 dark:text-accent-300">
                  {{ $t('plans.beams', { count: plan.beams.length }) }}
                </h4>
              </div>
              <div class="divide-y divide-accent-100 dark:divide-accent-700">
                <div
                  v-for="(beam, bIdx) in plan.beams"
                  :key="bIdx"
                  class="px-4 py-3 grid grid-cols-4 gap-4 text-xs"
                >
                  <div>
                    <p class="text-accent-500 dark:text-accent-400">{{ $t('plans.beamName') }}</p>
                    <p class="font-medium text-accent-900 dark:text-white">{{ beam.name || `Beam ${bIdx + 1}` }}</p>
                  </div>
                  <div>
                    <p class="text-accent-500 dark:text-accent-400">{{ $t('plans.energy') }}</p>
                    <p class="font-medium text-accent-900 dark:text-white">{{ beam.energy || $t('viewer.na') }}</p>
                  </div>
                  <div>
                    <p class="text-accent-500 dark:text-accent-400">{{ $t('plans.gantryAngle') }}</p>
                    <p class="font-medium text-accent-900 dark:text-white">{{ beam.gantry_angle || $t('viewer.na') }}°</p>
                  </div>
                  <div>
                    <p class="text-accent-500 dark:text-accent-400">{{ $t('plans.weight') }}</p>
                    <p class="font-medium text-accent-900 dark:text-white">{{ beam.weight || $t('viewer.na') }}</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Fractions -->
            <div v-if="plan.fractions" class="border-t border-accent-200 dark:border-accent-700 p-4">
              <h4 class="text-sm font-medium text-accent-700 dark:text-accent-300 mb-2">{{ $t('plans.fractionation') }}</h4>
              <div class="grid grid-cols-3 gap-4 text-xs">
                <div>
                  <p class="text-accent-500 dark:text-accent-400">{{ $t('plans.numFractions') }}</p>
                  <p class="font-medium text-accent-900 dark:text-white">{{ plan.fractions.number || $t('viewer.na') }}</p>
                </div>
                <div>
                  <p class="text-accent-500 dark:text-accent-400">{{ $t('plans.dosePerFraction') }}</p>
                  <p class="font-medium text-accent-900 dark:text-white">{{ plan.fractions.dose_per_fraction || $t('viewer.na') }} {{ $t('plans.gy') }}</p>
                </div>
                <div>
                  <p class="text-accent-500 dark:text-accent-400">{{ $t('plans.totalDose') }}</p>
                  <p class="font-medium text-accent-900 dark:text-white">{{ plan.fractions.total_dose || $t('viewer.na') }} {{ $t('plans.gy') }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useAppStore } from '@/stores/app'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'

const appStore = useAppStore()
const plans = ref<any[]>([])
const loading = ref(false)
const expandedPlans = ref<Set<number>>(new Set())

watch(
  () => appStore.selectedPatientId,
  () => loadPlans()
)

async function loadPlans() {
  if (!appStore.sessionId || !appStore.selectedPatientId) {
    plans.value = []
    return
  }
  loading.value = true
  try {
    const res = await fetch(`/api/dicom/plans/${appStore.sessionId}/${appStore.selectedPatientId}`)
    if (res.ok) {
      const data = await res.json()
      plans.value = data.plans || []
    } else {
      plans.value = []
    }
  } catch {
    plans.value = []
  } finally {
    loading.value = false
  }
}

function togglePlanExpand(idx: number) {
  const newSet = new Set(expandedPlans.value)
  if (newSet.has(idx)) {
    newSet.delete(idx)
  } else {
    newSet.add(idx)
  }
  expandedPlans.value = newSet
}

function formatKey(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}
</script>

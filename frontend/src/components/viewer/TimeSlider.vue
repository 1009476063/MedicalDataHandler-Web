<template>
  <div class="space-y-2">
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-medium text-accent-700 dark:text-accent-300">
        {{ $t('viewer.timeSlider') }}
      </h3>
      <span class="text-[10px] text-accent-400">
        {{ currentTimePoint + 1 }} / {{ timePointCount }}
      </span>
    </div>

    <!-- Slider -->
    <input
      type="range"
      :min="0"
      :max="timePointCount - 1"
      :value="sliderIndex"
      class="w-full h-1.5 accent-primary-500 cursor-pointer"
      @input="onSliderChange"
    />

    <!-- Controls -->
    <div class="flex items-center gap-1">
      <button
        class="p-1 rounded hover:bg-accent-100 dark:hover:bg-accent-800 text-accent-600 dark:text-accent-400 transition-colors"
        :title="$t('viewer.stepBackward')"
        @click="$emit('stepBackward')"
      >
        <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
          <path d="M15.707 15.707a1 1 0 01-1.414 0l-5-5a1 1 0 010-1.414l5-5a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 010 1.414zm-6 0a1 1 0 01-1.414 0l-5-5a1 1 0 010-1.414l5-5a1 1 0 011.414 1.414L5.414 10l4.293 4.293a1 1 0 010 1.414z"/>
        </svg>
      </button>

      <button
        class="p-1 rounded hover:bg-accent-100 dark:hover:bg-accent-800 text-accent-600 dark:text-accent-400 transition-colors"
        :title="playing ? $t('viewer.pause') : $t('viewer.play')"
        @click="onPlayToggle"
      >
        <svg v-if="!playing" class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
          <path d="M6.3 2.841A1.5 1.5 0 004 4.11v11.78a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z"/>
        </svg>
        <svg v-else class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
          <path d="M5.75 3a.75.75 0 00-.75.75v12.5c0 .414.336.75.75.75h1.5a.75.75 0 00.75-.75V3.75A.75.75 0 007.25 3h-1.5zM12.75 3a.75.75 0 00-.75.75v12.5c0 .414.336.75.75.75h1.5a.75.75 0 00.75-.75V3.75a.75.75 0 00-.75-.75h-1.5z"/>
        </svg>
      </button>

      <button
        class="p-1 rounded hover:bg-accent-100 dark:hover:bg-accent-800 text-accent-600 dark:text-accent-400 transition-colors"
        :title="$t('viewer.stepForward')"
        @click="$emit('stepForward')"
      >
        <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
          <path d="M4.293 15.707a1 1 0 010-1.414L8.586 10 4.293 5.707a1 1 0 011.414-1.414l5 5a1 1 0 010 1.414l-5 5a1 1 0 01-1.414 0zm6 0a1 1 0 010-1.414L14.586 10l-4.293-4.293a1 1 0 011.414-1.414l5 5a1 1 0 010 1.414l-5 5a1 1 0 01-1.414 0z"/>
        </svg>
      </button>

      <!-- FPS control -->
      <div class="ml-auto flex items-center gap-1">
        <label class="text-[10px] text-accent-400">{{ $t('viewer.fps') }}</label>
        <select
          :value="fps"
          class="text-[10px] bg-transparent text-accent-600 dark:text-accent-400 border border-accent-200 dark:border-accent-700 rounded px-1 py-0.5"
          @change="$emit('updateFps', Number(($event.target as HTMLSelectElement).value))"
        >
          <option :value="1">1</option>
          <option :value="2">2</option>
          <option :value="4">4</option>
          <option :value="8">8</option>
          <option :value="16">16</option>
        </select>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { FourDTimePoint } from '@/composables/useFourD'

const props = defineProps<{
  timePoints: FourDTimePoint[]
  currentTimePoint: number
  playing: boolean
  fps: number
}>()

const emit = defineEmits<{
  stepForward: []
  stepBackward: []
  play: []
  pause: []
  updateFps: [fps: number]
  changeTimePoint: [position: number]
}>()

const timePointCount = computed(() => props.timePoints.length)

const sliderIndex = computed(() => {
  const idx = props.timePoints.findIndex(tp => tp.position === props.currentTimePoint)
  return idx >= 0 ? idx : 0
})

function onSliderChange(event: Event) {
  const idx = Number((event.target as HTMLInputElement).value)
  if (idx >= 0 && idx < props.timePoints.length) {
    emit('changeTimePoint', props.timePoints[idx].position)
  }
}

function onPlayToggle() {
  if (props.playing) {
    emit('pause')
  } else {
    emit('play')
  }
}
</script>

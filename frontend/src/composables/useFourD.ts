import { ref, computed, onUnmounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { useSettings } from './useSettings'

export interface FourDTimePoint {
  position: number
  fileCount: number
  shape: number[]
}

export function useFourD() {
  const appStore = useAppStore()
  const { playbackFps, fourDPlaybackMode } = useSettings()
  const is4D = ref(false)
  const timePoints = ref<FourDTimePoint[]>([])
  const currentTimePoint = ref(0)
  const loading = ref(false)
  const error = ref('')
  const playing = ref(false)
  const fps = computed(() => playbackFps.value)
  const volumeData = ref<Record<string, { data: number[][][]; shape: number[]; spacing: number[]; origin: number[]; dtype: string; min: number; max: number; mean: number }>>({})

  let playTimer: ReturnType<typeof setInterval> | null = null
  let isFetching = false
  const MAX_VOLUME_CACHE = 10
  const volumeCacheOrder: string[] = []

  onUnmounted(() => pause())

  const timePointCount = computed(() => timePoints.value.length)

  async function detect4D(patientId: string, seriesUid: string) {
    loading.value = true
    error.value = ''
    try {
      const info = await appStore.get4DInfo(patientId, seriesUid)
      is4D.value = info.is_4d
      timePoints.value = info.time_points.map((tp: { position: number; file_count: number; shape: number[] }) => ({
        position: tp.position,
        fileCount: tp.file_count,
        shape: tp.shape,
      }))
      if (timePoints.value.length > 0) {
        currentTimePoint.value = timePoints.value[0].position
      }
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to detect 4D data'
      is4D.value = false
      timePoints.value = []
    } finally {
      loading.value = false
    }
  }

  async function loadTimePoint(patientId: string, seriesUid: string, timePoint: number) {
    try {
      const result = await appStore.get4DVolume(patientId, seriesUid, timePoint)
      // Merge into volumeData, evicting oldest when exceeding cache limit
      for (const [key, vol] of Object.entries(result.volumes)) {
        if (!(key in volumeData.value)) {
          volumeCacheOrder.push(key)
        }
        volumeData.value[key] = vol
      }
      while (volumeCacheOrder.length > MAX_VOLUME_CACHE) {
        const evictKey = volumeCacheOrder.shift()!
        delete volumeData.value[evictKey]
      }
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load time point'
    }
  }

  function setTimePoint(pos: number) {
    currentTimePoint.value = pos
  }

  function setFps(value: number) {
    playbackFps.value = value
  }

  function play(patientId: string, seriesUid: string) {
    if (playing.value || timePoints.value.length <= 1) return
    playing.value = true
    const positions = timePoints.value.map(tp => tp.position)
    let idx = positions.indexOf(currentTimePoint.value)
    if (idx < 0) idx = 0
    let direction = 1

    playTimer = setInterval(() => {
      const mode = fourDPlaybackMode.value
      if (mode === 'once' && idx === positions.length - 1 && direction === 1) {
        pause()
        return
      }
      if (mode === 'pingPong') {
        if (idx >= positions.length - 1) direction = -1
        else if (idx <= 0) direction = 1
      }
      idx += direction
      idx = Math.max(0, Math.min(idx, positions.length - 1))
      currentTimePoint.value = positions[idx]
      if (!isFetching) {
        isFetching = true
        loadTimePoint(patientId, seriesUid, positions[idx]).finally(() => { isFetching = false })
      }
    }, 1000 / fps.value)
  }

  function pause() {
    playing.value = false
    if (playTimer) {
      clearInterval(playTimer)
      playTimer = null
    }
  }

  function stepForward(patientId: string, seriesUid: string) {
    const positions = timePoints.value.map(tp => tp.position)
    const idx = positions.indexOf(currentTimePoint.value)
    const nextIdx = Math.min(idx + 1, positions.length - 1)
    currentTimePoint.value = positions[nextIdx]
    loadTimePoint(patientId, seriesUid, positions[nextIdx])
  }

  function stepBackward(patientId: string, seriesUid: string) {
    const positions = timePoints.value.map(tp => tp.position)
    const idx = positions.indexOf(currentTimePoint.value)
    const prevIdx = Math.max(idx - 1, 0)
    currentTimePoint.value = positions[prevIdx]
    loadTimePoint(patientId, seriesUid, positions[prevIdx])
  }

  function reset() {
    pause()
    is4D.value = false
    timePoints.value = []
    currentTimePoint.value = 0
    volumeData.value = {}
    volumeCacheOrder.length = 0
    error.value = ''
  }

  return {
    is4D,
    timePoints,
    currentTimePoint,
    loading,
    error,
    playing,
    fps,
    timePointCount,
    volumeData,
    detect4D,
    loadTimePoint,
    setTimePoint,
    setFps,
    play,
    pause,
    stepForward,
    stepBackward,
    reset,
  }
}

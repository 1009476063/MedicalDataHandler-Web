import { ref, onBeforeUnmount } from 'vue'
import axios from 'axios'
import type { AIModel, AIJob } from '@/types'

export interface StudySummary {
  summary: string
  key_findings: string[]
  recommendations: string[]
}

export function useAI() {
  const models = ref<AIModel[]>([])
  const currentJob = ref<AIJob | null>(null)
  const progress = ref(0)
  const progressMessage = ref('')
  const analysisResult = ref<Record<string, unknown> | null>(null)
  const studySummary = ref<StudySummary | null>(null)
  const summaryLoading = ref(false)
  const loading = ref(false)

  let activeEventSource: EventSource | null = null
  let pollAbortController: AbortController | null = null

  async function fetchModels(): Promise<AIModel[]> {
    try {
      const res = await axios.get('/api/ai/models')
      models.value = res.data?.data || []
      return models.value
    } catch {
      models.value = []
      return []
    }
  }

  async function runAnalysis(
    sessionId: string,
    patientId: string,
    seriesUid: string,
    modelId: string = 'gpt-4o',
    prompt: string = '',
    sliceStrategy: string = 'middle',
  ): Promise<void> {
    loading.value = true
    progress.value = 0
    progressMessage.value = 'Starting analysis...'
    analysisResult.value = null

    try {
      // Start job
      const res = await axios.post('/api/ai/analyze', {
        session_id: sessionId,
        patient_id: patientId,
        series_uid: seriesUid,
        model_id: modelId,
        prompt,
        slice_strategy: sliceStrategy,
      })

      const jobId = res.data?.data?.job_id
      if (!jobId) throw new Error('No job ID returned')

      currentJob.value = {
        job_id: jobId,
        status: 'pending',
        progress: 0,
        model_id: modelId,
        created_at: new Date().toISOString(),
      }

      // Stream progress via SSE
      await streamProgress(jobId)
    } catch (err) {
      progressMessage.value = err instanceof Error ? err.message : 'Analysis failed'
      currentJob.value = currentJob.value
        ? { ...currentJob.value, status: 'failed', error: progressMessage.value }
        : null
    } finally {
      loading.value = false
    }
  }

  function streamProgress(jobId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const eventSource = new EventSource(`/api/ai/jobs/${jobId}/stream`)
      activeEventSource = eventSource

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          progress.value = data.progress || 0
          progressMessage.value = data.message || ''

          if (data.done) {
            eventSource.close()
            activeEventSource = null
            if (data.error) {
              reject(new Error(data.message))
            } else {
              fetchResults(jobId).then(() => resolve())
            }
          }
        } catch {
          // Ignore parse errors (keepalive lines)
        }
      }

      eventSource.onerror = () => {
        eventSource.close()
        activeEventSource = null
        // Fallback: poll for results
        pollForResults(jobId).then(resolve).catch(reject)
      }
    })
  }

  async function pollForResults(jobId: string): Promise<void> {
    const controller = new AbortController()
    pollAbortController = controller
    const maxAttempts = 60
    try {
      for (let i = 0; i < maxAttempts; i++) {
        if (controller.signal.aborted) return
        try {
          const res = await axios.get(`/api/ai/jobs/${jobId}`, { signal: controller.signal })
          const job = res.data?.data
          if (!job) break

          progress.value = job.progress || 0
          progressMessage.value = job.status === 'completed' ? 'Done' : `Status: ${job.status}`

          if (job.status === 'completed') {
            await fetchResults(jobId)
            return
          }
          if (job.status === 'failed') {
            throw new Error(job.error || 'Analysis failed')
          }
        } catch (err) {
          if (controller.signal.aborted) return
          if (err instanceof Error && err.message !== 'Analysis failed') {
            // Network error, retry
          } else {
            throw err
          }
        }
        await new Promise((r) => setTimeout(r, 1000))
      }
    } finally {
      pollAbortController = null
    }
  }

  async function fetchResults(jobId: string): Promise<void> {
    try {
      const res = await axios.get(`/api/ai/results/${jobId}`)
      analysisResult.value = res.data?.data?.result || null
      currentJob.value = currentJob.value
        ? { ...currentJob.value, status: 'completed', progress: 1 }
        : null
    } catch {
      analysisResult.value = null
    }
  }

  function reset() {
    currentJob.value = null
    progress.value = 0
    progressMessage.value = ''
    analysisResult.value = null
    studySummary.value = null
    summaryLoading.value = false
    loading.value = false
  }

  async function generateSummary(
    findings: Array<{ region: string; description: string; confidence: number; severity: string }>,
    modelId: string = 'gpt-4o-mini',
    patientContext: string = '',
  ): Promise<void> {
    summaryLoading.value = true
    try {
      const res = await axios.post('/api/ai/summary', {
        findings,
        model_id: modelId,
        patient_context: patientContext,
      })
      studySummary.value = res.data?.data || null
    } catch {
      studySummary.value = null
    } finally {
      summaryLoading.value = false
    }
  }

  function cleanup() {
    activeEventSource?.close()
    activeEventSource = null
    pollAbortController?.abort()
    pollAbortController = null
  }

  onBeforeUnmount(() => {
    cleanup()
  })

  return {
    models,
    currentJob,
    progress,
    progressMessage,
    analysisResult,
    studySummary,
    summaryLoading,
    loading,
    fetchModels,
    runAnalysis,
    generateSummary,
    reset,
    cleanup,
  }
}

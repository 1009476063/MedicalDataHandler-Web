import { ref } from 'vue'
import axios from 'axios'

export interface PrinterConfig {
  id: string
  name: string
  ae_title: string
  host: string
  port: number
  film_size: string
  orientation: string
  density: number
}

export interface PrintJob {
  id: string
  printer_id: string
  status: string
  film_size: string
  orientation: string
  created_at: string
}

export function usePrint() {
  const printers = ref<PrinterConfig[]>([])
  const currentJob = ref<PrintJob | null>(null)
  const loading = ref(false)
  const error = ref('')

  async function fetchPrinters() {
    loading.value = true
    error.value = ''
    try {
      const resp = await axios.get('/api/print/printers')
      printers.value = resp.data.data
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch printers'
    } finally {
      loading.value = false
    }
  }

  async function addPrinter(config: Partial<PrinterConfig>) {
    loading.value = true
    error.value = ''
    try {
      const resp = await axios.post('/api/print/printers', config)
      printers.value.push(resp.data.data)
      return resp.data.data as PrinterConfig
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to add printer'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updatePrinter(id: string, updates: Partial<PrinterConfig>) {
    loading.value = true
    error.value = ''
    try {
      const resp = await axios.put(`/api/print/printers/${id}`, updates)
      const idx = printers.value.findIndex(p => p.id === id)
      if (idx >= 0) printers.value[idx] = resp.data.data
      return resp.data.data as PrinterConfig
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to update printer'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function removePrinter(id: string) {
    loading.value = true
    error.value = ''
    try {
      await axios.delete(`/api/print/printers/${id}`)
      printers.value = printers.value.filter(p => p.id !== id)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to remove printer'
    } finally {
      loading.value = false
    }
  }

  async function sendPrint(printerId: string, imageData: string, options?: { film_size?: string; orientation?: string }) {
    loading.value = true
    error.value = ''
    try {
      const resp = await axios.post('/api/print/send', {
        printer_id: printerId,
        image_data: imageData,
        ...options,
      })
      currentJob.value = resp.data.data
      return resp.data.data as PrintJob
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to send print job'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function getJobStatus(jobId: string) {
    try {
      const resp = await axios.get(`/api/print/jobs/${jobId}`)
      currentJob.value = resp.data.data
      return resp.data.data as PrintJob
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to get job status'
    }
  }

  return {
    printers,
    currentJob,
    loading,
    error,
    fetchPrinters,
    addPrinter,
    updatePrinter,
    removePrinter,
    sendPrint,
    getJobStatus,
  }
}

import { ref } from 'vue'
import axios from 'axios'
import type { SrDocument, ContentTreeNode, AiFinding } from '@/types'

export function useSR() {
  const documents = ref<SrDocument[]>([])
  const selectedDoc = ref<SrDocument | null>(null)
  const contentTree = ref<ContentTreeNode[]>([])
  const loading = ref(false)
  const error = ref('')

  async function fetchDocuments(sessionId: string, patientId: string = '') {
    loading.value = true
    error.value = ''
    try {
      const resp = await axios.get('/api/sr/documents', {
        params: { session_id: sessionId, patient_id: patientId },
      })
      documents.value = resp.data.data
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch SR documents'
    } finally {
      loading.value = false
    }
  }

  async function loadDocument(docId: string) {
    loading.value = true
    error.value = ''
    try {
      const resp = await axios.get(`/api/sr/documents/${docId}`)
      selectedDoc.value = resp.data.data
      contentTree.value = resp.data.data.content_tree || []
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load SR document'
    } finally {
      loading.value = false
    }
  }

  async function createFromAi(
    sessionId: string,
    patientId: string,
    patientName: string,
    studyDate: string,
    findings: AiFinding[],
    institution: string = '',
  ) {
    loading.value = true
    error.value = ''
    try {
      const resp = await axios.post('/api/sr/create', {
        session_id: sessionId,
        patient_id: patientId,
        patient_name: patientName,
        study_date: studyDate,
        findings,
        institution,
      })
      const doc = resp.data.data as SrDocument
      documents.value.unshift(doc)
      return doc
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to create SR document'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteDocument(docId: string) {
    loading.value = true
    error.value = ''
    try {
      await axios.delete(`/api/sr/documents/${docId}`)
      documents.value = documents.value.filter(d => d.id !== docId)
      if (selectedDoc.value?.id === docId) {
        selectedDoc.value = null
        contentTree.value = []
      }
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to delete SR document'
    } finally {
      loading.value = false
    }
  }

  return {
    documents,
    selectedDoc,
    contentTree,
    loading,
    error,
    fetchDocuments,
    loadDocument,
    createFromAi,
    deleteDocument,
  }
}

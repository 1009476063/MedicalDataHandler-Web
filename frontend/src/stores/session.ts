import { deleteSession } from '@/api/dicom'

export async function cleanupSessionAction(sessionId: string): Promise<boolean> {
  try {
    await deleteSession(sessionId)
    return true
  } catch {
    return false
  }
}

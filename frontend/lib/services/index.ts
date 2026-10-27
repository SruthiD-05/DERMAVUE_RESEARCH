import { isBackendConfigured, isRemoteData } from '../config'
import { localStore } from '../data/local-store'
import { newCaseId, newImageId, newNoteId, newPatientId } from '../ids'
import type {
  AnalysisResult,
  Case,
  CaseImage,
  CaseWithPatient,
  ClinicalHistory,
  LesionDetails,
  ModelInfo,
  ModelStatus,
  Patient,
  ReviewStatus,
  WorkspaceSettings,
} from '../types'
import { ApiError, apiFetch } from './api-client'

/* ------------------------------------------------------------------ */
/* patientService — GET/POST /api/patients, GET /api/patients/{id}     */
/* ------------------------------------------------------------------ */
export const patientService = {
  list: (): Promise<Patient[]> => (isRemoteData ? apiFetch('/api/patients') : localStore.patients.list()),
  get: async (id: string): Promise<Patient | undefined> => {
    if (isRemoteData) return apiFetch(`/api/patients/${encodeURIComponent(id)}`)
    return (await localStore.patients.list()).find((p) => p.id === id)
  },
  create: (input: Omit<Patient, 'id' | 'createdAt' | 'origin'> & { id?: string }): Promise<Patient> => {
    const patient: Patient = {
      ...input,
      id: input.id || newPatientId(),
      origin: isRemoteData ? 'remote' : 'local',
      createdAt: new Date().toISOString(),
    }
    if (isRemoteData) return apiFetch('/api/patients', { method: 'POST', body: JSON.stringify(patient) })
    return localStore.patients.save(patient)
  },
  update: async (id: string, patch: Partial<Patient>): Promise<Patient> => {
    const existing = await patientService.get(id)
    if (!existing) throw new ApiError('Patient not found', 404)
    const updated = { ...existing, ...patch, id: existing.id, createdAt: existing.createdAt, origin: existing.origin }
    if (isRemoteData) return apiFetch(`/api/patients/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify(updated) })
    return localStore.patients.save(updated)
  },
  remove: async (id: string) => {
    const cases = (await caseService.list()).filter((c) => c.patientId === id)
    await Promise.all(cases.map((c) => caseService.remove(c.id)))
    if (isRemoteData) await apiFetch<void>(`/api/patients/${encodeURIComponent(id)}`, { method: 'DELETE' })
    else await localStore.patients.remove(id)
  },
}

/* ------------------------------------------------------------------ */
/* imageService — POST/GET /api/cases/{id}/images                      */
/* ------------------------------------------------------------------ */
export type PendingImage = Omit<CaseImage, 'id' | 'caseId' | 'uploadedAt'>

export const imageService = {
  list: (): Promise<CaseImage[]> => localStore.images.list(),
  forCase: async (caseId: string): Promise<CaseImage[]> => {
    if (isRemoteData) return apiFetch(`/api/cases/${encodeURIComponent(caseId)}/images`)
    return (await localStore.images.list()).filter((i) => i.caseId === caseId)
  },
  attach: async (caseId: string, pending: PendingImage[]): Promise<CaseImage[]> => {
    const uploadedAt = new Date().toISOString()
    const images = pending.map((p) => ({ ...p, id: newImageId(), caseId, uploadedAt }))
    if (isRemoteData) {
      return apiFetch(`/api/cases/${encodeURIComponent(caseId)}/images`, {
        method: 'POST',
        body: JSON.stringify(images),
      })
    }
    return localStore.images.saveMany(images)
  },
}

/* ------------------------------------------------------------------ */
/* caseService — /api/cases CRUD                                       */
/* ------------------------------------------------------------------ */
export interface CreateCaseInput {
  patientId: string
  caseReference?: string
  caseName?: string
  history: ClinicalHistory
  lesion: LesionDetails
  images: PendingImage[]
  asDraft?: boolean
}

async function hydrate(cases: Case[]): Promise<CaseWithPatient[]> {
  const patients = await patientService.list()
  const byPatient = new Map(patients.map((p) => [p.id, p]))
  const hydrated = await Promise.all(cases.map(async (c) => ({
      ...c,
      patient: byPatient.get(c.patientId),
      images: await imageService.forCase(c.id),
    })))
  return hydrated
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
}

export const caseService = {
  list: (): Promise<Case[]> => (isRemoteData ? apiFetch('/api/cases') : localStore.cases.list()),
  listDetailed: async () => hydrate(await caseService.list()),
  get: async (id: string): Promise<CaseWithPatient | undefined> => {
    const record = isRemoteData
      ? await apiFetch<Case>(`/api/cases/${encodeURIComponent(id)}`)
      : (await localStore.cases.list()).find((c) => c.id === id)
    if (!record) return undefined
    const [patient, images] = await Promise.all([patientService.get(record.patientId), imageService.forCase(id)])
    return { ...record, patient, images }
  },
  create: async (input: CreateCaseInput): Promise<Case> => {
    const now = new Date().toISOString()
    const requestedReference = input.caseReference?.trim()
    if (!isRemoteData && requestedReference) {
      const duplicate = (await localStore.cases.list()).some((item) => item.caseReference?.trim().toLowerCase() === requestedReference.toLowerCase())
      if (duplicate) throw new ApiError(`Case ID '${input.caseReference}' is already in use.`, 409)
    }
    const id = newCaseId()
    const images = await imageService.attach(id, input.images)
    const hasDermoscopy = images.some((i) => i.kind === 'dermoscopic')
    const record: Case = {
      id,
      caseReference: input.caseReference || undefined,
      caseName: input.caseName || undefined,
      patientId: input.patientId,
      status: input.asDraft || !hasDermoscopy ? 'draft' : 'ready',
      reviewStatus: 'unreviewed',
      history: input.history,
      lesion: input.lesion,
      imageIds: images.map((i) => i.id),
      notes: [],
      origin: isRemoteData ? 'remote' : 'local',
      createdAt: now,
      updatedAt: now,
    }
    if (isRemoteData) return apiFetch('/api/cases', { method: 'POST', body: JSON.stringify(record) })
    return localStore.cases.save(record)
  },
  update: async (id: string, patch: Partial<Case>): Promise<Case> => {
    if (isRemoteData) return apiFetch(`/api/cases/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify(patch) })
    const existing = (await localStore.cases.list()).find((c) => c.id === id)
    if (!existing) throw new Error('Case not found')
    return localStore.cases.save({ ...existing, ...patch, updatedAt: new Date().toISOString() })
  },
  setReview: (id: string, reviewStatus: ReviewStatus) => caseService.update(id, { reviewStatus }),
  addNote: async (id: string, body: string) => {
    const existing = await caseService.get(id)
    if (!existing) throw new Error('Case not found')
    const note = { id: newNoteId(), body, createdAt: new Date().toISOString() }
    return caseService.update(id, { notes: [note, ...existing.notes] })
  },
  remove: async (id: string) => {
    if (isRemoteData) return apiFetch<void>(`/api/cases/${encodeURIComponent(id)}`, { method: 'DELETE' })
    return localStore.cases.remove(id)
  },
}

/* ------------------------------------------------------------------ */
/* modelService — GET /api/health, /api/model/status, /api/model/info */
/* ------------------------------------------------------------------ */
export const modelService = {
  status: async (): Promise<ModelStatus> => {
    if (!isBackendConfigured) {
      return {
        state: 'configuration-required',
        backendConfigured: false,
        inferenceAvailable: false,
        message: 'No inference backend is configured. Set NEXT_PUBLIC_DERMAVUE_API_URL to connect the research model.',
      }
    }
    try {
      const remote = await apiFetch<Partial<ModelStatus>>('/api/model/status', { timeoutMs: 6000 })
      const checkpointLoaded = remote.checkpointLoaded ?? false
      const inferenceAvailable = Boolean(remote.inferenceAvailable) && checkpointLoaded
      const state = remote.state as ModelStatus['state'] | undefined
      return {
        backendConfigured: true,
        modelName: remote.modelName,
        modelVersion: remote.modelVersion,
        checkpointLoaded,
        inferenceAvailable,
        architecture: remote.architecture,
        artifactState: remote.artifactState,
        loadState: remote.loadState,
        releaseState: remote.releaseState,
        metadataSource: remote.metadataSource,
        reportedMetrics: remote.reportedMetrics,
        researchMode: remote.researchMode,
        lastCheckedAt: new Date().toISOString(),
        state: state ?? (!checkpointLoaded ? 'checkpoint-missing' : inferenceAvailable ? 'connected' : 'inference-unavailable'),
        message:
          remote.message ??
          (!checkpointLoaded
            ? 'The backend is reachable but no model checkpoint is loaded.'
            : inferenceAvailable
              ? 'Backend reachable and reporting inference availability.'
              : 'The backend reports that inference is currently unavailable.'),
      }
    } catch (error) {
      return {
        state: 'disconnected',
        backendConfigured: true,
        inferenceAvailable: false,
        lastCheckedAt: new Date().toISOString(),
        message: error instanceof ApiError ? error.message : 'Unable to reach the backend.',
      }
    }
  },
  info: async (): Promise<ModelInfo | null> => {
    if (!isBackendConfigured) return null
    try {
      return await apiFetch<ModelInfo>('/api/model/info', { timeoutMs: 6000 })
    } catch {
      return null
    }
  },
}

/* ------------------------------------------------------------------ */
/* analysisService — POST /api/cases/{id}/analyze                      */
/* ------------------------------------------------------------------ */
async function dataUrlToBlob(src: string) {
  const res = await fetch(src)
  return res.blob()
}

export const analysisService = {
  /**
   * Sends only the dermoscopic image(s) to the backend. The backend is expected to return
   * { predictedLabel, scores?, scoresAreCalibrated?, modelName, modelVersion, inputImageId, explanationAvailable }.
   * Nothing is ever generated client-side.
   */
  run: async (caseId: string): Promise<AnalysisResult> => {
    const status = await modelService.status()
    const record = await caseService.get(caseId)
    if (!record) throw new ApiError('Case not found')
    const dermoscopic = record.images.filter((i) => i.kind === 'dermoscopic')
    if (dermoscopic.length === 0) throw new ApiError('A dermoscopic image is required for analysis')
    if (!status.inferenceAvailable) {
      await caseService.update(caseId, { status: 'unavailable', result: undefined })
      throw new ApiError(`Analysis is disabled pending genuine-data release approval. The backend is reachable and your uploaded images and metadata were not rejected. ${status.message}`, 503)
    }

      await caseService.update(caseId, { status: 'pending', result: undefined })
    try {
      const form = new FormData()
      for (const image of dermoscopic) {
        form.append('images', await dataUrlToBlob(image.src), image.filename)
        form.append('image_ids', image.id)
      }
      if (record.patient?.age !== undefined) form.append('age', String(record.patient.age))
      const partnerSex = record.patient?.sex === 'male' || record.patient?.sex === 'female' ? record.patient.sex : 'unknown'
      form.append('sex', partnerSex)
      form.append('localization', (record.lesion.bodyRegion || 'unknown').trim().toLowerCase())
      const remote = await apiFetch<Omit<AnalysisResult, 'id' | 'caseId' | 'source' | 'inferredAt'> & { inferredAt?: string }>(
        `/api/cases/${encodeURIComponent(caseId)}/analyze`,
        { method: 'POST', body: form, timeoutMs: 120000 },
      )
      if (!['BENIGN', 'MALIGNANT'].includes(remote.predictedLabel) || !['LOW', 'MODERATE', 'HIGH'].includes(remote.riskLevel || '')) {
        throw new ApiError('The backend returned an invalid analysis category.')
      }
      if (typeof remote.malignancyScore !== 'number' || !Number.isFinite(remote.malignancyScore) || remote.malignancyScore < 0 || remote.malignancyScore > 1) {
        throw new ApiError('The backend returned an invalid malignancy score.')
      }
      if (remote.scores !== undefined && (!Array.isArray(remote.scores) || remote.scores.some((item) => !item || typeof item.label !== 'string' || typeof item.score !== 'number' || !Number.isFinite(item.score) || item.score < 0 || item.score > 1))) {
        throw new ApiError('The backend returned invalid class scores.')
      }
      if (!remote.disclaimer?.trim()) throw new ApiError('The backend returned no research disclaimer.')
      const result: AnalysisResult = {
        ...remote,
        id: `RS-${Date.now()}`,
        caseId,
        source: 'model',
        inferredAt: remote.inferredAt ?? new Date().toISOString(),
        explanationAvailable: Boolean(remote.explanationAvailable),
      }
      await caseService.update(caseId, { status: 'complete', result })
      return result
    } catch (error) {
      await caseService.update(caseId, { status: 'unavailable', result: undefined })
      throw error
    }
  },
}

/* ------------------------------------------------------------------ */
/* reportService — POST /api/reports/{id}/export                       */
/* ------------------------------------------------------------------ */
export const reportService = {
  canExportRemotely: isBackendConfigured,
  exportPdf: async (caseId: string) => {
    if (!isBackendConfigured) {
      window.print()
      return
    }
    await apiFetch(`/api/reports/${encodeURIComponent(caseId)}/export`, { method: 'POST' })
  },
}

/* ------------------------------------------------------------------ */
/* settingsService — local only                                        */
/* ------------------------------------------------------------------ */
export const settingsService = {
  get: () => localStore.settings.get(),
  save: (s: WorkspaceSettings) => localStore.settings.save(s),
  removeDemo: () => localStore.removeDemo(),
  restoreDemo: () => localStore.restoreDemo(),
  clearAll: () => localStore.clearAll(),
}

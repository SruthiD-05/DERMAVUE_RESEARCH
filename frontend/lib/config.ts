export const APP_VERSION = '0.9.0-research'

/** Base URL of the FastAPI inference/data backend, e.g. http://localhost:8000 */
export const API_BASE_URL = process.env.NEXT_PUBLIC_DERMAVUE_API_URL?.replace(/\/$/, '') ?? ''

export const isBackendConfigured = API_BASE_URL.length > 0

/** Records stay in this browser's IndexedDB unless the backend is also set to own data. */
export const isRemoteData = isBackendConfigured && process.env.NEXT_PUBLIC_DERMAVUE_DATA_MODE === 'remote'

export const ACCEPTED_IMAGE_TYPES = {
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/png': ['.png'],
} as const

export const DEFAULT_MAX_UPLOAD_MB = 15

export const RESEARCH_DISCLAIMER =
  'This research tool provides model-generated outputs for research and educational purposes. It is not a medical diagnosis and must not replace assessment by a qualified healthcare professional.'

export const DEVELOPER_REPORTED_ACCURACY = '94.9–95%'

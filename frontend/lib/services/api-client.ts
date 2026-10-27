import { API_BASE_URL, isBackendConfigured } from '../config'

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function apiFetch<T>(path: string, init: RequestInit & { timeoutMs?: number } = {}): Promise<T> {
  if (!isBackendConfigured) throw new ApiError('No backend configured')
  const { timeoutMs = 15000, headers, ...rest } = init
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const isForm = rest.body instanceof FormData
    const res = await fetch(`${API_BASE_URL}${path}`, {
      ...rest,
      signal: controller.signal,
      headers: isForm ? headers : { 'Content-Type': 'application/json', ...headers },
    })
    if (!res.ok) {
      const body = await res.text().catch(() => '')
      let message = body
      try {
        const parsed = JSON.parse(body) as { message?: string; detail?: string; error?: string }
        message = parsed.message || parsed.detail || parsed.error || body
      } catch {
        // Preserve plain-text upstream errors.
      }
      throw new ApiError(message || `Request failed with status ${res.status}`, res.status)
    }
    if (res.status === 204) return undefined as T
    return (await res.json()) as T
  } catch (error) {
    if (error instanceof ApiError) throw error
    if ((error as Error).name === 'AbortError') throw new ApiError('The backend did not respond in time')
    throw new ApiError('Unable to reach the backend')
  } finally {
    clearTimeout(timer)
  }
}

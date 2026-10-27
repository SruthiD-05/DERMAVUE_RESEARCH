'use client'

import useSWR, { useSWRConfig } from 'swr'
import { useCallback, useMemo } from 'react'
import { caseService, modelService, patientService, settingsService } from '@/lib/services'
import { DEFAULT_SETTINGS } from '@/lib/data/local-store'

export function useSettings() {
  const { data, isLoading, mutate } = useSWR('settings', settingsService.get)
  return { settings: data ?? DEFAULT_SETTINGS, isLoading, mutate }
}

export function useCases() {
  const { settings } = useSettings()
  const { data, isLoading, error, mutate } = useSWR('cases', caseService.listDetailed)
  const cases = useMemo(
    () => (data ?? []).filter((c) => settings.showDemoData || c.origin !== 'demo'),
    [data, settings.showDemoData],
  )
  return { cases, isLoading, error, mutate }
}

export function useCase(id: string | undefined) {
  const { data, isLoading, error, mutate } = useSWR(id ? ['case', id] : null, ([, caseId]) => caseService.get(caseId))
  return { record: data, isLoading, error, mutate }
}

export function usePatients() {
  const { settings } = useSettings()
  const { data, isLoading, error, mutate } = useSWR('patients', patientService.list)
  const patients = useMemo(
    () => (data ?? []).filter((p) => settings.showDemoData || p.origin !== 'demo'),
    [data, settings.showDemoData],
  )
  return { patients, isLoading, error, mutate }
}

export function useModelStatus() {
  const { data, isLoading, isValidating, mutate } = useSWR('model-status', modelService.status, {
    refreshInterval: 60000,
    revalidateOnFocus: true,
  })
  return { status: data, isLoading, isValidating, refresh: mutate }
}

export function useModelInfo() {
  const { data, isLoading } = useSWR('model-info', modelService.info)
  return { info: data, isLoading }
}

/** Revalidates every cached record after a write. */
export function useRevalidateAll() {
  const { mutate } = useSWRConfig()
  return useCallback(() => mutate(() => true), [mutate])
}

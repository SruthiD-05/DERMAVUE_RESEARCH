import type {
  CaseStatus,
  ConsentStatus,
  LesionChange,
  LesionSide,
  ReviewStatus,
  Sex,
  Symptom,
  YesNoUnknown,
} from './types'

export function formatDate(iso?: string, opts: Intl.DateTimeFormatOptions = {}) {
  if (!iso) return '—'
  return new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short', year: 'numeric', ...opts }).format(
    new Date(iso),
  )
}

export function formatDateTime(iso?: string) {
  if (!iso) return '—'
  return new Intl.DateTimeFormat('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso))
}

export function formatRelative(iso?: string) {
  if (!iso) return '—'
  const diff = Date.now() - new Date(iso).getTime()
  const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })
  const mins = Math.round(diff / 60000)
  if (Math.abs(mins) < 60) return rtf.format(-mins, 'minute')
  const hours = Math.round(mins / 60)
  if (Math.abs(hours) < 24) return rtf.format(-hours, 'hour')
  const days = Math.round(hours / 24)
  if (Math.abs(days) < 30) return rtf.format(-days, 'day')
  return formatDate(iso)
}

export function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

export const SEX_LABELS: Record<Sex, string> = {
  female: 'Female',
  male: 'Male',
  intersex: 'Intersex',
  'prefer-not-to-say': 'Prefer not to say',
  'not-recorded': 'Not recorded',
}

export const CONSENT_LABELS: Record<ConsentStatus, string> = {
  obtained: 'Consent obtained',
  pending: 'Consent pending',
  declined: 'Consent declined',
  'not-required': 'Not required (anonymised)',
}

export const YNU_LABELS: Record<YesNoUnknown | 'not-recorded', string> = {
  yes: 'Yes',
  no: 'No',
  unknown: 'Unknown',
  'not-recorded': 'Not recorded',
}

export const SIDE_LABELS: Record<LesionSide, string> = {
  left: 'Left',
  right: 'Right',
  midline: 'Midline',
  'not-applicable': 'Not applicable',
}

export const CHANGE_LABELS: Record<LesionChange, string> = {
  'no-change': 'No change reported',
  size: 'Change in size',
  color: 'Change in colour',
  shape: 'Change in shape',
  multiple: 'Multiple changes',
  unknown: 'Unknown',
}

export function caseDisplayLabel(item: { caseName?: string; caseReference?: string; lesion?: { lesionId?: string }; id: string }): string {
  return item.caseName || item.caseReference || item.lesion?.lesionId || item.id
}

export const SYMPTOM_LABELS: Record<Symptom, string> = {
  itching: 'Itching',
  bleeding: 'Bleeding',
  pain: 'Pain',
  none: 'None',
  unknown: 'Unknown',
}

export const CASE_STATUS_LABELS: Record<CaseStatus, string> = {
  draft: 'Draft',
  ready: 'Ready for analysis',
  pending: 'Analysis pending',
  complete: 'Analysis complete',
  unavailable: 'Inference unavailable',
}

export const REVIEW_STATUS_LABELS: Record<ReviewStatus, string> = {
  unreviewed: 'Not reviewed',
  'in-review': 'In review',
  reviewed: 'Reviewed',
}

export const BODY_REGIONS = [
  'Head & scalp',
  'Face',
  'Neck',
  'Chest',
  'Abdomen',
  'Upper back',
  'Lower back',
  'Upper arm',
  'Forearm',
  'Hand',
  'Thigh',
  'Lower leg',
  'Foot',
  'Genital / perineal',
] as const

export function toItems<T extends string>(labels: Record<T, string>) {
  return (Object.keys(labels) as T[]).map((value) => ({ value, label: labels[value] }))
}

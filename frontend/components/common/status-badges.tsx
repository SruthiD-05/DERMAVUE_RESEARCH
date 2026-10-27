import { Badge } from '@/components/ui/badge'
import { CASE_STATUS_LABELS, REVIEW_STATUS_LABELS } from '@/lib/format'
import type { CaseStatus, DataOrigin, ModelConnectionState, ReviewStatus } from '@/lib/types'
import { cn } from '@/lib/utils'

type Tone = 'neutral' | 'teal' | 'success' | 'warning' | 'danger' | 'info'

const TONE: Record<Tone, string> = {
  neutral: 'border-border bg-muted text-muted-foreground',
  teal: 'border-primary/20 bg-secondary text-secondary-foreground',
  success: 'border-success/20 bg-success-soft text-success',
  warning: 'border-warning/25 bg-warning-soft text-warning',
  danger: 'border-destructive/25 bg-destructive/10 text-destructive',
  info: 'border-chart-2/25 bg-chart-2/10 text-foreground/80',
}

export function ToneBadge({
  tone,
  dot = true,
  children,
  className,
}: {
  tone: Tone
  dot?: boolean
  children: React.ReactNode
  className?: string
}) {
  return (
    <Badge variant="outline" className={cn('gap-1.5 font-medium', TONE[tone], className)}>
      {dot && <span aria-hidden="true" className="size-1.5 rounded-full bg-current opacity-80" />}
      {children}
    </Badge>
  )
}

const CASE_TONE: Record<CaseStatus, Tone> = {
  draft: 'neutral',
  ready: 'teal',
  pending: 'info',
  complete: 'success',
  unavailable: 'warning',
}

export function CaseStatusBadge({ status }: { status: CaseStatus }) {
  return <ToneBadge tone={CASE_TONE[status]}>{CASE_STATUS_LABELS[status]}</ToneBadge>
}

const REVIEW_TONE: Record<ReviewStatus, Tone> = {
  unreviewed: 'neutral',
  'in-review': 'info',
  reviewed: 'success',
}

export function ReviewStatusBadge({ status }: { status: ReviewStatus }) {
  return <ToneBadge tone={REVIEW_TONE[status]}>{REVIEW_STATUS_LABELS[status]}</ToneBadge>
}

export const MODEL_STATE_LABELS: Record<ModelConnectionState, string> = {
  connected: 'Connected',
  disconnected: 'Disconnected',
  'checkpoint-missing': 'Checkpoint missing',
  'artifacts-invalid': 'Model artifacts invalid',
  'artifacts-present': 'Model installed — not loaded',
  'release-disabled': 'Model installed — serving disabled',
  'release-approved': 'Release approved — not loaded',
  'research-enabled-not-loaded': 'Local research mode — loading',
  'research-available': 'Local research inference available',
  'inference-unavailable': 'Inference unavailable',
  'configuration-required': 'Configuration required',
  loading: 'Checking…',
}

const MODEL_TONE: Record<ModelConnectionState, Tone> = {
  connected: 'success',
  disconnected: 'danger',
  'checkpoint-missing': 'warning',
  'artifacts-invalid': 'danger',
  'artifacts-present': 'info',
  'release-disabled': 'warning',
  'release-approved': 'info',
  'research-enabled-not-loaded': 'info',
  'research-available': 'success',
  'inference-unavailable': 'warning',
  'configuration-required': 'warning',
  loading: 'neutral',
}

export function ModelStateBadge({ state, className }: { state: ModelConnectionState; className?: string }) {
  return (
    <ToneBadge tone={MODEL_TONE[state]} className={className}>
      {MODEL_STATE_LABELS[state]}
    </ToneBadge>
  )
}

export function DemoBadge({ origin, className }: { origin: DataOrigin; className?: string }) {
  if (origin !== 'demo') return null
  return (
    <Badge
      variant="outline"
      className={cn(
        'border-dashed border-warning/40 bg-warning-soft font-mono text-[10px] tracking-[0.12em] text-warning',
        className,
      )}
    >
      DEMO
    </Badge>
  )
}

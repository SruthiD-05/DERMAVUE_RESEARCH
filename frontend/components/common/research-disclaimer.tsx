import { ShieldAlert } from 'lucide-react'
import { RESEARCH_DISCLAIMER } from '@/lib/config'
import { cn } from '@/lib/utils'

export function ResearchDisclaimer({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <aside
      role="note"
      aria-label="Research use disclaimer"
      className={cn(
        'flex items-start gap-3 rounded-xl border border-warning/25 bg-warning-soft/70 text-foreground/85',
        compact ? 'px-3 py-2.5 text-xs' : 'px-4 py-3.5 text-sm',
        className,
      )}
    >
      <ShieldAlert aria-hidden="true" className={cn('mt-0.5 shrink-0 text-warning', compact ? 'size-3.5' : 'size-4')} />
      <p className="leading-relaxed text-pretty">
        <span className="font-semibold text-foreground">RESEARCH USE ONLY — NOT CLINICALLY VALIDATED. </span>
        {RESEARCH_DISCLAIMER}
      </p>
    </aside>
  )
}

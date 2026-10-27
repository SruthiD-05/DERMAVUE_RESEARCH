import { cn } from '@/lib/utils'

export function LogoMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" aria-hidden="true" className={cn('size-7', className)}>
      <rect width="32" height="32" rx="9" className="fill-primary" />
      <circle cx="16" cy="16" r="9" fill="none" stroke="white" strokeOpacity="0.35" strokeWidth="1.25" />
      <circle cx="16" cy="16" r="5.25" fill="none" stroke="white" strokeWidth="1.75" />
      <circle cx="16" cy="16" r="1.6" fill="white" />
    </svg>
  )
}

export function Logo({ className, tone = 'default' }: { className?: string; tone?: 'default' | 'inverse' }) {
  return (
    <span className={cn('inline-flex items-center gap-2.5', className)}>
      <LogoMark />
      <span
        className={cn(
          'font-display text-[15px] font-extrabold tracking-[0.14em]',
          tone === 'inverse' ? 'text-white' : 'text-foreground',
        )}
      >
        DERMAVUE
      </span>
    </span>
  )
}

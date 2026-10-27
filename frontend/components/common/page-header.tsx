import Link from 'next/link'
import { ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  breadcrumbs,
  className,
}: {
  eyebrow?: string
  title: React.ReactNode
  description?: React.ReactNode
  actions?: React.ReactNode
  breadcrumbs?: { href?: string; label: string }[]
  className?: string
}) {
  return (
    <header className={cn('flex flex-col gap-4 md:flex-row md:items-end md:justify-between', className)}>
      <div className="flex min-w-0 flex-col gap-2">
        {breadcrumbs && (
          <nav aria-label="Breadcrumb">
            <ol className="flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
              {breadcrumbs.map((b, i) => (
                <li key={b.label} className="flex items-center gap-1">
                  {i > 0 && <ChevronRight aria-hidden="true" className="size-3 opacity-60" />}
                  {b.href ? (
                    <Link href={b.href} className="transition-colors hover:text-foreground">
                      {b.label}
                    </Link>
                  ) : (
                    <span aria-current="page" className="text-foreground/80">
                      {b.label}
                    </span>
                  )}
                </li>
              ))}
            </ol>
          </nav>
        )}
        {eyebrow && (
          <p className="font-mono text-[11px] font-medium uppercase tracking-[0.18em] text-primary">{eyebrow}</p>
        )}
        <h1 className="font-display text-2xl font-bold text-foreground md:text-[28px]">{title}</h1>
        {description && <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
    </header>
  )
}

'use client'

import { ClipboardCheck, FolderOpen, Hourglass, Users, type LucideIcon } from 'lucide-react'
import { motion } from 'motion/react'
import { Skeleton } from '@/components/ui/skeleton'
import type { CaseWithPatient, Patient } from '@/lib/types'

interface Stat {
  label: string
  value: number
  hint: string
  icon: LucideIcon
}

export function StatCards({
  cases,
  patients,
  isLoading,
}: {
  cases: CaseWithPatient[]
  patients: Patient[]
  isLoading: boolean
}) {
  const awaiting = cases.filter((c) => c.status === 'ready' || c.status === 'unavailable').length
  const reviewed = cases.filter((c) => c.reviewStatus === 'reviewed').length
  const drafts = cases.filter((c) => c.status === 'draft').length

  const stats: Stat[] = [
    { label: 'Total cases', value: cases.length, hint: `${drafts} draft${drafts === 1 ? '' : 's'}`, icon: FolderOpen },
    { label: 'Patients', value: patients.length, hint: 'De-identified references', icon: Users },
    { label: 'Awaiting analysis', value: awaiting, hint: 'Ready for a connected model', icon: Hourglass },
    {
      label: 'Reviewed',
      value: reviewed,
      hint: cases.length ? `${Math.round((reviewed / cases.length) * 100)}% of cases` : 'No cases yet',
      icon: ClipboardCheck,
    },
  ]

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {stats.map((s, i) => (
        <motion.div
          key={s.label}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: i * 0.05 }}
          className="flex flex-col gap-4 rounded-xl border bg-card p-5 shadow-soft"
        >
          <div className="flex items-center justify-between">
            <p className="text-[13px] font-medium text-muted-foreground">{s.label}</p>
            <s.icon aria-hidden="true" className="size-4 text-primary" />
          </div>
          {isLoading ? (
            <Skeleton className="h-9 w-16" />
          ) : (
            <p className="font-display text-[34px] font-bold leading-none tabular-nums">{s.value}</p>
          )}
          <p className="text-xs text-muted-foreground">{s.hint}</p>
        </motion.div>
      ))}
    </div>
  )
}

'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { ChevronRight } from 'lucide-react'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { CaseStatusBadge, DemoBadge, ReviewStatusBadge } from '@/components/common/status-badges'
import { CaseThumb } from './case-thumb'
import { caseDisplayLabel, formatDate } from '@/lib/format'
import type { CaseWithPatient } from '@/lib/types'

export function CasesTable({ cases, compact = false }: { cases: CaseWithPatient[]; compact?: boolean }) {
  const router = useRouter()
  return (
    <Table>
      <TableHeader>
        <TableRow className="hover:bg-transparent">
          <TableHead className="pl-5">Case</TableHead>
          <TableHead>Patient</TableHead>
          {!compact && <TableHead className="hidden md:table-cell">Lesion</TableHead>}
          <TableHead className="hidden sm:table-cell">Status</TableHead>
          {!compact && <TableHead className="hidden lg:table-cell">Review</TableHead>}
          <TableHead className="hidden md:table-cell">Created</TableHead>
          <TableHead className="w-10 pr-5">
            <span className="sr-only">Open</span>
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {cases.map((c) => (
          <TableRow
            key={c.id}
            className="cursor-pointer"
            onClick={() => router.push(`/cases/${c.id}`)}
          >
            <TableCell className="pl-5">
              <div className="flex items-center gap-3">
                <CaseThumb images={c.images} />
                <div className="flex min-w-0 flex-col gap-0.5">
                  <Link
                    href={`/cases/${c.id}`}
                    onClick={(e) => e.stopPropagation()}
                    className="font-mono text-[13px] font-medium text-foreground outline-none hover:text-primary focus-visible:underline"
                  >
                    {caseDisplayLabel(c)}
                  </Link>
                  {(c.caseReference || c.caseName) && <span className="font-mono text-[10px] text-muted-foreground">Internal ID: {c.id}</span>}
                  <DemoBadge origin={c.origin} className="h-4 w-fit px-1.5 text-[9px]" />
                </div>
              </div>
            </TableCell>
            <TableCell>
              <div className="flex flex-col">
                <span className="text-sm">{c.patient?.reference ?? 'Unknown'}</span>
                <span className="font-mono text-[11px] text-muted-foreground">{c.patientId}</span>
              </div>
            </TableCell>
            {!compact && (
              <TableCell className="hidden md:table-cell">
                <div className="flex flex-col">
                  <span className="text-sm">{c.lesion.bodyRegion}</span>
                  <span className="text-xs text-muted-foreground">{c.lesion.anatomicalSite || '—'}</span>
                </div>
              </TableCell>
            )}
            <TableCell className="hidden sm:table-cell">
              <CaseStatusBadge status={c.status} />
            </TableCell>
            {!compact && (
              <TableCell className="hidden lg:table-cell">
                <ReviewStatusBadge status={c.reviewStatus} />
              </TableCell>
            )}
            <TableCell className="hidden text-sm text-muted-foreground md:table-cell">{formatDate(c.createdAt)}</TableCell>
            <TableCell className="pr-5">
              <ChevronRight aria-hidden="true" className="size-4 text-muted-foreground" />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

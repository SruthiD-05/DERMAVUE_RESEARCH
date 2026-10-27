'use client'

import Link from 'next/link'
import { useMemo, useState } from 'react'
import { Plus, Search, Users } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from '@/components/ui/empty'
import { PageHeader } from '@/components/common/page-header'
import { DemoBadge, ToneBadge } from '@/components/common/status-badges'
import { useCases, usePatients } from '@/hooks/use-data'
import { CONSENT_LABELS, SEX_LABELS, formatDate } from '@/lib/format'

export function PatientsView() {
  const { patients, isLoading } = usePatients()
  const { cases } = useCases()
  const [query, setQuery] = useState('')

  const caseCounts = useMemo(() => {
    const m = new Map<string, number>()
    for (const c of cases) m.set(c.patientId, (m.get(c.patientId) ?? 0) + 1)
    return m
  }, [cases])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    const sorted = [...patients].sort((a, b) => b.createdAt.localeCompare(a.createdAt))
    return q ? sorted.filter((p) => p.id.toLowerCase().includes(q) || p.reference.toLowerCase().includes(q)) : sorted
  }, [patients, query])

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        eyebrow="Records"
        title="Patients"
        description="De-identified patient references. Names and direct identifiers are never stored."
        actions={
          <Button render={<Link href="/cases/new" />} nativeButton={false}>
            <Plus data-icon="inline-start" />
            Register via new case
          </Button>
        }
      />
      <div className="relative max-w-md">
        <Search aria-hidden="true" className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          aria-label="Search patients"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Patient ID or reference"
          className="bg-card pl-8"
        />
      </div>
      <div className="overflow-hidden rounded-xl border bg-card shadow-soft">
        {isLoading ? (
          <div className="flex flex-col gap-3 p-5">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <Empty className="py-16">
            <EmptyHeader>
              <EmptyMedia variant="icon">
                <Users />
              </EmptyMedia>
              <EmptyTitle>{query ? 'No matching patients' : 'No patients yet'}</EmptyTitle>
              <EmptyDescription>Patients are registered as the first step of a new case.</EmptyDescription>
            </EmptyHeader>
            {!query && (
              <EmptyContent>
                <Button render={<Link href="/cases/new" />} nativeButton={false}>
                  New case
                </Button>
              </EmptyContent>
            )}
          </Empty>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="pl-5">Reference</TableHead>
                <TableHead>Age</TableHead>
                <TableHead className="hidden sm:table-cell">Sex</TableHead>
                <TableHead className="hidden md:table-cell">Consent</TableHead>
                <TableHead>Cases</TableHead>
                <TableHead className="hidden pr-5 md:table-cell">Registered</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((p) => (
                <TableRow key={p.id}>
                  <TableCell className="pl-5">
                    <div className="flex flex-col gap-0.5">
                      <span className="flex items-center gap-2 font-medium">
                        <Link href={`/patients/${p.id}`} className="hover:underline">{p.reference}</Link>
                        <DemoBadge origin={p.origin} className="h-4 px-1.5 text-[9px]" />
                      </span>
                      <span className="font-mono text-[11px] text-muted-foreground">{p.id}</span>
                    </div>
                  </TableCell>
                  <TableCell className="tabular-nums">{p.age}</TableCell>
                  <TableCell className="hidden sm:table-cell">{SEX_LABELS[p.sex]}</TableCell>
                  <TableCell className="hidden md:table-cell">
                    <ToneBadge tone={p.consent === 'obtained' ? 'success' : p.consent === 'declined' ? 'danger' : 'neutral'}>
                      {CONSENT_LABELS[p.consent]}
                    </ToneBadge>
                  </TableCell>
                  <TableCell>
                    <Link
                      href={`/cases?q=${encodeURIComponent(p.id)}`}
                      className="font-mono text-sm tabular-nums text-primary hover:underline"
                    >
                      {caseCounts.get(p.id) ?? 0}
                    </Link>
                  </TableCell>
                  <TableCell className="hidden pr-5 text-sm text-muted-foreground md:table-cell">{formatDate(p.createdAt)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  )
}

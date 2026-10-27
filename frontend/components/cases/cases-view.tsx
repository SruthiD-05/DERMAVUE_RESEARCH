'use client'

import Link from 'next/link'
import { useMemo, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { ChevronLeft, ChevronRight, FolderOpen, Plus, Search, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from '@/components/ui/empty'
import { PageHeader } from '@/components/common/page-header'
import { CasesTable } from './cases-table'
import { useCases } from '@/hooks/use-data'
import { CASE_STATUS_LABELS, REVIEW_STATUS_LABELS, toItems } from '@/lib/format'

const PAGE_SIZE = 10
const statusItems = [{ value: 'all', label: 'All statuses' }, ...toItems(CASE_STATUS_LABELS)]
const reviewItems = [{ value: 'all', label: 'All review states' }, ...toItems(REVIEW_STATUS_LABELS)]

export function CasesView() {
  const params = useSearchParams()
  const { cases, isLoading } = useCases()
  const [query, setQuery] = useState(params.get('q') ?? '')
  const [status, setStatus] = useState<string>('all')
  const [review, setReview] = useState<string>('all')
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [page, setPage] = useState(0)

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return cases.filter((c) => {
      if (status !== 'all' && c.status !== status) return false
      if (review !== 'all' && c.reviewStatus !== review) return false
      const day = c.createdAt.slice(0, 10)
      if (from && day < from) return false
      if (to && day > to) return false
      if (!q) return true
      return [c.id, c.caseReference, c.caseName, c.patientId, c.patient?.reference, c.lesion.lesionId, c.lesion.bodyRegion, c.lesion.anatomicalSite]
        .filter(Boolean)
        .some((v) => v!.toLowerCase().includes(q))
    })
  }, [cases, query, status, review, from, to])

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const current = Math.min(page, pageCount - 1)
  const visible = filtered.slice(current * PAGE_SIZE, current * PAGE_SIZE + PAGE_SIZE)
  const hasFilters = query || status !== 'all' || review !== 'all' || from || to

  function resetFilters() {
    setQuery('')
    setStatus('all')
    setReview('all')
    setFrom('')
    setTo('')
    setPage(0)
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        eyebrow="Records"
        title="Cases"
        description="Search and filter every lesion case in this workspace."
        actions={
          <Button render={<Link href="/cases/new" />} nativeButton={false}>
            <Plus data-icon="inline-start" />
            New case
          </Button>
        }
      />

      <div className="flex flex-col gap-3 rounded-xl border bg-card p-4 shadow-soft lg:flex-row lg:items-end">
        <div className="flex flex-1 flex-col gap-1.5">
          <Label htmlFor="case-search">Search</Label>
          <div className="relative">
            <Search aria-hidden="true" className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="case-search"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value)
                setPage(0)
              }}
              placeholder="Case ID, patient ID, reference or body region"
              className="pl-8"
            />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:flex">
          <div className="flex flex-col gap-1.5">
            <Label>Status</Label>
            <Select items={statusItems} value={status} onValueChange={(v) => { setStatus(v as string); setPage(0) }}>
              <SelectTrigger className="w-full lg:w-40" aria-label="Filter by status">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {statusItems.map((i) => (
                    <SelectItem key={i.value} value={i.value}>
                      {i.label}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Review</Label>
            <Select items={reviewItems} value={review} onValueChange={(v) => { setReview(v as string); setPage(0) }}>
              <SelectTrigger className="w-full lg:w-40" aria-label="Filter by review status">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {reviewItems.map((i) => (
                    <SelectItem key={i.value} value={i.value}>
                      {i.label}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="from">From</Label>
            <Input id="from" type="date" value={from} max={to || undefined} onChange={(e) => { setFrom(e.target.value); setPage(0) }} className="lg:w-38" />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="to">To</Label>
            <Input id="to" type="date" value={to} min={from || undefined} onChange={(e) => { setTo(e.target.value); setPage(0) }} className="lg:w-38" />
          </div>
        </div>
        {hasFilters && (
          <Button variant="ghost" onClick={resetFilters} className="self-start lg:self-end">
            <X data-icon="inline-start" />
            Clear
          </Button>
        )}
      </div>

      <div className="overflow-hidden rounded-xl border bg-card shadow-soft">
        {isLoading ? (
          <div className="flex flex-col gap-3 p-5">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : visible.length === 0 ? (
          <Empty className="py-16">
            <EmptyHeader>
              <EmptyMedia variant="icon">
                <FolderOpen />
              </EmptyMedia>
              <EmptyTitle>{hasFilters ? 'No matching cases' : 'No cases yet'}</EmptyTitle>
              <EmptyDescription>
                {hasFilters ? 'Try adjusting the search or filters.' : 'Create a case to begin documenting a lesion.'}
              </EmptyDescription>
            </EmptyHeader>
            <EmptyContent>
              {hasFilters ? (
                <Button variant="outline" onClick={resetFilters}>
                  Clear filters
                </Button>
              ) : (
                <Button render={<Link href="/cases/new" />} nativeButton={false}>
                  <Plus data-icon="inline-start" />
                  New case
                </Button>
              )}
            </EmptyContent>
          </Empty>
        ) : (
          <CasesTable cases={visible} />
        )}
        {filtered.length > 0 && (
          <div className="flex items-center justify-between border-t px-5 py-3 text-sm text-muted-foreground">
            <span>
              Showing {current * PAGE_SIZE + 1}–{Math.min(filtered.length, (current + 1) * PAGE_SIZE)} of {filtered.length}
            </span>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="icon-sm" disabled={current === 0} onClick={() => setPage(current - 1)} aria-label="Previous page">
                <ChevronLeft />
              </Button>
              <span className="font-mono text-xs tabular-nums">
                {current + 1} / {pageCount}
              </span>
              <Button variant="outline" size="icon-sm" disabled={current >= pageCount - 1} onClick={() => setPage(current + 1)} aria-label="Next page">
                <ChevronRight />
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

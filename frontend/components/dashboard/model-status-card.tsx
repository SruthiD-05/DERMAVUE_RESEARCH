'use client'

import Link from 'next/link'
import { Activity, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { ModelStateBadge } from '@/components/common/status-badges'
import { useModelStatus } from '@/hooks/use-data'
import { formatRelative } from '@/lib/format'

export function ModelStatusCard() {
  const { status, isLoading } = useModelStatus()
  return (
    <Card className="relative overflow-hidden shadow-soft">
      <div aria-hidden="true" className="absolute -right-10 -top-10 size-36 rounded-full bg-primary/8 blur-2xl" />
      <CardHeader className="relative">
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="flex items-center gap-2 font-display">
            <Activity aria-hidden="true" className="size-4 text-primary" />
            Inference
          </CardTitle>
          {status ? <ModelStateBadge state={status.state} /> : <Skeleton className="h-5 w-24" />}
        </div>
      </CardHeader>
      <CardContent className="relative flex flex-col gap-3">
        {isLoading || !status ? (
          <Skeleton className="h-10 w-full" />
        ) : (
          <>
            <p className="text-sm leading-relaxed text-muted-foreground">{status.message}</p>
            <dl className="grid grid-cols-2 gap-3 rounded-lg bg-muted/60 p-3 text-xs">
              <div className="flex flex-col gap-0.5">
                <dt className="text-muted-foreground">Model</dt>
                <dd className="font-medium">{status.modelName ?? 'Not reported'}</dd>
              </div>
              <div className="flex flex-col gap-0.5">
                <dt className="text-muted-foreground">Last checked</dt>
                <dd className="font-medium">{status.lastCheckedAt ? formatRelative(status.lastCheckedAt) : 'Never'}</dd>
              </div>
            </dl>
          </>
        )}
      </CardContent>
      <CardFooter className="relative">
        <Button variant="outline" size="sm" className="w-full" render={<Link href="/model" />} nativeButton={false}>
          Model details
          <ArrowRight data-icon="inline-end" />
        </Button>
      </CardFooter>
    </Card>
  )
}

'use client'

import Link from 'next/link'
import { useMemo } from 'react'
import { ArrowRight, FolderOpen, Plus } from 'lucide-react'
import { motion } from 'motion/react'
import { Button } from '@/components/ui/button'
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from '@/components/ui/empty'
import { PageHeader } from '@/components/common/page-header'
import { ResearchDisclaimer } from '@/components/common/research-disclaimer'
import { CasesTable } from '@/components/cases/cases-table'
import { StatCards } from './stat-cards'
import { ActivityChart } from './activity-chart'
import { ModelStatusCard } from './model-status-card'
import { useCases, usePatients, useSettings } from '@/hooks/use-data'

function greeting() {
  const h = new Date().getHours()
  return h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening'
}

export function DashboardView() {
  const { cases, isLoading } = useCases()
  const { patients } = usePatients()
  const { settings } = useSettings()
  const recent = useMemo(() => cases.slice(0, 6), [cases])

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        eyebrow="Overview"
        title={`${greeting()}, ${settings.displayName.split(' ')[0]}`}
        description="A summary of this workspace's cases, review progress and inference availability."
        actions={
          <>
            <Button variant="outline" render={<Link href="/cases" />} nativeButton={false}>
              <FolderOpen data-icon="inline-start" />
              All cases
            </Button>
            <Button render={<Link href="/cases/new" />} nativeButton={false}>
              <Plus data-icon="inline-start" />
              New case
            </Button>
          </>
        }
      />

      <StatCards cases={cases} patients={patients} isLoading={isLoading} />

      <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}>
          <Card className="gap-0 py-0 shadow-soft">
            <CardHeader className="border-b py-5">
              <CardTitle className="font-display">Recent cases</CardTitle>
              <CardDescription>Latest records in this workspace</CardDescription>
              <CardAction>
                <Button variant="ghost" size="sm" render={<Link href="/cases" />} nativeButton={false}>
                  View all
                  <ArrowRight data-icon="inline-end" />
                </Button>
              </CardAction>
            </CardHeader>
            <CardContent className="px-0">
              {isLoading ? (
                <div className="flex flex-col gap-3 p-5">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <Skeleton key={i} className="h-12 w-full" />
                  ))}
                </div>
              ) : recent.length === 0 ? (
                <Empty className="py-14">
                  <EmptyHeader>
                    <EmptyMedia variant="icon">
                      <FolderOpen />
                    </EmptyMedia>
                    <EmptyTitle>No cases yet</EmptyTitle>
                    <EmptyDescription>Register a patient and lesion to create the first case record.</EmptyDescription>
                  </EmptyHeader>
                  <EmptyContent>
                    <Button render={<Link href="/cases/new" />} nativeButton={false}>
                      <Plus data-icon="inline-start" />
                      New case
                    </Button>
                  </EmptyContent>
                </Empty>
              ) : (
                <CasesTable cases={recent} compact />
              )}
            </CardContent>
          </Card>
        </motion.div>

        <div className="flex flex-col gap-6">
          <ModelStatusCard />
          <ActivityChart cases={cases} />
        </div>
      </div>

      <ResearchDisclaimer />
    </div>
  )
}

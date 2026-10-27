import type { Metadata } from 'next'
import { Suspense } from 'react'
import { CasesView } from '@/components/cases/cases-view'

export const metadata: Metadata = { title: 'Cases' }

export default function CasesPage() {
  return (
    <Suspense>
      <CasesView />
    </Suspense>
  )
}

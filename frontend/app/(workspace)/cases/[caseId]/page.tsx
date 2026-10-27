import type { Metadata } from 'next'
import { CaseDetailView } from '@/components/cases/case-detail-view'

export const metadata: Metadata = { title: 'Case detail' }

export default async function CaseDetailPage({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = await params
  return <CaseDetailView caseId={caseId} />
}

import type { Metadata } from 'next'
import { ResultsView } from '@/components/results/results-view'

export const metadata: Metadata = { title: 'Analysis results' }

export default async function ResultsPage({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = await params
  return <ResultsView caseId={caseId} />
}

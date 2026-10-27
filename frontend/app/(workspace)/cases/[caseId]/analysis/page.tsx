import type { Metadata } from 'next'
import { AnalysisWorkspace } from '@/components/analysis/analysis-workspace'

export const metadata: Metadata = { title: 'Analysis workspace' }

export default async function AnalysisPage({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = await params
  return <AnalysisWorkspace caseId={caseId} />
}

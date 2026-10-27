'use client'

import Link from 'next/link'
import { useState } from 'react'
import { ArrowLeft, CheckCircle2, Loader2, Play, TriangleAlert } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useCase, useModelStatus } from '@/hooks/use-data'
import { analysisService } from '@/lib/services'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { PageHeader } from '@/components/common/page-header'
import { ResearchDisclaimer } from '@/components/common/research-disclaimer'
import { ImageViewer } from '@/components/images/image-viewer'

export function AnalysisWorkspace({ caseId }: { caseId: string }) {
  const { record, isLoading } = useCase(caseId); const { status } = useModelStatus(); const router = useRouter(); const [running, setRunning] = useState(false); const [error, setError] = useState('')
  if (isLoading) return <div className="p-8 text-sm text-muted-foreground">Loading analysis workspace…</div>
  if (!record) return <PageHeader title="Case not found" />
  const dermoscopy = record.images.filter((i) => i.kind === 'dermoscopic')
  const run = async () => { setRunning(true); setError(''); try { await analysisService.run(caseId); router.push(`/cases/${caseId}/results`) } catch (e) { setError(e instanceof Error ? e.message : 'Analysis could not be started.') } finally { setRunning(false) } }
  const unavailable = Boolean(status && !status.inferenceAvailable)
  return <div className="space-y-6"><PageHeader eyebrow="Analysis workspace" title="Review inputs before inference" description="Only a configured backend may produce predictions. This workspace never invents a result." actions={<Button variant="outline" render={<Link href={`/cases/${caseId}`} />} nativeButton={false}><ArrowLeft />Case detail</Button>} /><ResearchDisclaimer /><div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]"><ImageViewer images={record.images} /><Card><CardHeader><CardTitle>Inference readiness</CardTitle></CardHeader><CardContent className="space-y-4 text-sm"><div className="flex items-center gap-2">{status?.inferenceAvailable ? <CheckCircle2 className="text-emerald-600" /> : <TriangleAlert className="text-amber-600" />}<span>{status?.message || 'Checking model connection…'}</span></div><div className="rounded-lg bg-muted/50 p-3"><p className="font-medium">Inputs</p><p className="mt-1 text-muted-foreground">Clinical image: {record.images.some((i) => i.kind === 'clinical') ? 'available' : 'not provided'}</p><p className="text-muted-foreground">Dermoscopic image: {dermoscopy.length} available</p><p className="text-muted-foreground">Metadata: {record.patient ? 'available' : 'not available'}</p></div>{error && <p role="alert" className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-destructive">{error}</p>}{unavailable && <p role="status" className="rounded-md border border-amber-300 bg-amber-50 p-3 text-amber-900">Analysis is disabled pending release approval. Your uploaded images are valid inputs for review; they were not rejected.</p>}<Button className="w-full" disabled={running || !status?.inferenceAvailable || dermoscopy.length === 0} onClick={() => void run()}>{running ? <><Loader2 className="animate-spin" />Running analysis…</> : unavailable ? <><TriangleAlert />Analysis unavailable — release pending</> : <><Play />Run model analysis</>}</Button><p className="text-xs text-muted-foreground">Partner checkpoints are installed for compatibility testing, but genuine-data release approval is still pending. Analysis remains unavailable until that gate is explicitly approved.</p></CardContent></Card></div></div>
}

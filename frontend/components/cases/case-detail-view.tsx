'use client'

import Link from 'next/link'
import { useState } from 'react'
import { ArrowLeft, FileText, Play, Trash2 } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useCase, useRevalidateAll } from '@/hooks/use-data'
import { caseService } from '@/lib/services'
import { caseDisplayLabel } from '@/lib/format'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { PageHeader } from '@/components/common/page-header'
import { ImageViewer } from '@/components/images/image-viewer'
import { ResearchDisclaimer } from '@/components/common/research-disclaimer'

export function CaseDetailView({ caseId }: { caseId: string }) {
  const { record, isLoading, mutate } = useCase(caseId); const router = useRouter(); const refresh = useRevalidateAll(); const [note, setNote] = useState('')
  if (isLoading) return <div className="p-8 text-sm text-muted-foreground">Loading case…</div>
  if (!record) return <div className="space-y-4"><PageHeader title="Case not found" /><Button render={<Link href="/cases" />} nativeButton={false}><ArrowLeft />Back to cases</Button></div>
  const saveNote = async () => { if (!note.trim()) return; await caseService.addNote(caseId, note.trim()); setNote(''); await mutate(); await refresh() }
  return <div className="space-y-6"><PageHeader eyebrow="Case record" title={caseDisplayLabel(record)} description={`${record.patient?.reference || 'Patient record'} · ${record.lesion.bodyRegion || 'Site not recorded'} · Internal ID ${record.id}`} actions={<div className="flex gap-2"><Button variant="outline" render={<Link href="/cases" />} nativeButton={false}><ArrowLeft />Cases</Button><Button render={<Link href={`/cases/${caseId}/analysis`} />} nativeButton={false}><Play />Open analysis</Button></div>} />
    <ResearchDisclaimer />
    <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]"><ImageViewer images={record.images} /><div className="space-y-4"><Card><CardHeader><CardTitle>Case status</CardTitle></CardHeader><CardContent className="space-y-3 text-sm"><div className="flex justify-between"><span className="text-muted-foreground">Analysis</span><Badge variant="secondary">{record.status}</Badge></div><div className="flex justify-between"><span className="text-muted-foreground">Review</span><Badge variant="outline">{record.reviewStatus}</Badge></div><div className="flex gap-2"><Button size="sm" variant="outline" onClick={async () => { await caseService.setReview(caseId, 'in-review'); await mutate(); await refresh() }}>Mark in review</Button><Button size="sm" variant="outline" onClick={async () => { await caseService.setReview(caseId, 'reviewed'); await mutate(); await refresh() }}>Mark reviewed</Button></div></CardContent></Card>
      <Card><CardHeader><CardTitle>Patient & lesion</CardTitle></CardHeader><CardContent className="space-y-2 text-sm"><p><span className="text-muted-foreground">Age / sex:</span> {record.patient?.age ?? '—'} / {record.patient?.sex ?? '—'}</p><p><span className="text-muted-foreground">History:</span> personal {record.history.personalSkinCancerHistory}, family {record.history.familySkinCancerHistory}</p><p><span className="text-muted-foreground">Change:</span> {record.lesion.change}; symptoms {record.lesion.symptoms.join(', ') || 'none recorded'}</p><p><span className="text-muted-foreground">Observations:</span> {record.lesion.observations || 'Not recorded'}</p></CardContent></Card>
      <Card><CardHeader><CardTitle>Notes</CardTitle></CardHeader><CardContent className="space-y-3"><div className="flex gap-2"><Input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Add a case note" onKeyDown={(e) => { if (e.key === 'Enter') void saveNote() }} /><Button onClick={() => void saveNote()}>Add</Button></div>{record.notes.length ? record.notes.map((item) => <div key={item.id} className="rounded-md bg-muted/50 p-3 text-sm">{item.body}<p className="mt-1 text-xs text-muted-foreground">{new Date(item.createdAt).toLocaleString()}</p></div>) : <p className="text-sm text-muted-foreground">No notes yet.</p>}</CardContent></Card>
      <div className="flex justify-between"><Button variant="outline" render={<Link href={`/cases/${caseId}/results`} />} nativeButton={false}><FileText />View results</Button><Button variant="ghost" className="text-destructive" onClick={async () => { if (!window.confirm('Delete this local case?')) return; await caseService.remove(caseId); await refresh(); router.push('/cases') }}><Trash2 />Delete case</Button></div></div></div>
  </div>
}

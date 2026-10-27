'use client'

import Link from 'next/link'
import { Download, FileText } from 'lucide-react'
import { useCases } from '@/hooks/use-data'
import { reportService } from '@/lib/services'
import { caseDisplayLabel } from '@/lib/format'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { PageHeader } from '@/components/common/page-header'
import { ResearchDisclaimer } from '@/components/common/research-disclaimer'

export function ReportsView() { const { cases, isLoading } = useCases(); const reportable = cases.filter((c) => c.result); return <div className="space-y-6"><PageHeader eyebrow="Reports" title="Case reports" description="Print or export stored results when a connected model has produced them." /><ResearchDisclaimer /><Card><CardHeader><CardTitle>Available reports</CardTitle></CardHeader><CardContent>{isLoading ? <p className="text-sm text-muted-foreground">Loading…</p> : reportable.length === 0 ? <div className="py-8 text-center"><FileText className="mx-auto size-8 text-muted-foreground" /><p className="mt-3 text-sm text-muted-foreground">No case reports are available yet.</p></div> : <div className="divide-y">{reportable.map((item) => <div key={item.id} className="flex flex-wrap items-center justify-between gap-3 py-4"><div><Link className="font-medium hover:underline" href={`/cases/${item.id}/results`}>{caseDisplayLabel(item)}</Link><p className="text-sm text-muted-foreground">{item.result?.predictedLabel} <Badge variant="outline" className="ml-2">{item.result?.source}</Badge></p></div><Button variant="outline" size="sm" onClick={() => void reportService.exportPdf(item.id)}><Download />Print / export</Button></div>)}</div>}</CardContent></Card></div> }

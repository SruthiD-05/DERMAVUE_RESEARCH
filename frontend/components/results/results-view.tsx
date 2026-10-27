'use client'

import Link from 'next/link'
import { AlertTriangle, ArrowLeft, Download, Info } from 'lucide-react'
import { useCase } from '@/hooks/use-data'
import { reportService } from '@/lib/services'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { PageHeader } from '@/components/common/page-header'
import { ResearchDisclaimer } from '@/components/common/research-disclaimer'
import { caseDisplayLabel } from '@/lib/format'

const classLabels: Record<string, string> = {
  akiec: 'Actinic keratosis / intraepidermal carcinoma',
  bcc: 'Basal cell carcinoma',
  bkl: 'Benign keratosis-like lesion',
  df: 'Dermatofibroma',
  mel: 'Melanoma',
  nv: 'Melanocytic nevus',
  vasc: 'Vascular lesion',
}

function validScore(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1
}

export function ResultsView({ caseId }: { caseId: string }) {
  const { record, isLoading } = useCase(caseId)
  if (isLoading) return <div className="p-8 text-sm text-muted-foreground">Loading results…</div>
  if (!record) return <PageHeader title="Case not found" />
  const result = record.result
  const hasValidScore = validScore(result?.malignancyScore)
  const score = hasValidScore ? (result?.malignancyScore ?? 0) : 0
  const validClassScores = result?.scores?.filter((item) => item && typeof item.label === 'string' && validScore(item.score)) ?? []
  const invalidClassScoreCount = (result?.scores?.length ?? 0) - validClassScores.length
  const maxAuxiliaryScore = validClassScores.length ? Math.max(...validClassScores.map((item) => item.score)) : undefined
  const topAuxiliaryScores = maxAuxiliaryScore === undefined ? [] : validClassScores.filter((item) => item.score === maxAuxiliaryScore)
  const topAuxiliary = topAuxiliaryScores.length === 1 ? topAuxiliaryScores[0] : undefined

  return <div className="space-y-6">
    <PageHeader eyebrow="Analysis result" title={caseDisplayLabel(record)} description="A transparent view of the stored model output for this case." actions={<div className="flex gap-2"><Button variant="outline" render={<Link href={`/cases/${caseId}`} />} nativeButton={false}><ArrowLeft />Case detail</Button><Button variant="outline" onClick={() => void reportService.exportPdf(caseId)}><Download />Print / export</Button></div>} />
    <ResearchDisclaimer />
    {!result ? <Card><CardContent className="flex flex-col items-center gap-3 p-10 text-center"><Info className="size-8 text-muted-foreground" /><h2 className="font-medium">No model result is stored</h2><p className="max-w-md text-sm text-muted-foreground">This case has not been analyzed, or the inference backend was unavailable. No diagnosis is inferred by the interface.</p><Button render={<Link href={`/cases/${caseId}/analysis`} />} nativeButton={false}>Open analysis workspace</Button></CardContent></Card> : <div className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
      <div className="space-y-6">
        <Card><CardHeader><CardTitle>Primary result</CardTitle></CardHeader><CardContent className="space-y-4"><div className="text-3xl font-semibold">{result.predictedLabel}</div><div className="flex flex-wrap gap-2"><Badge variant="secondary">{result.source === 'demo' ? 'Demo result' : 'Model result'}</Badge>{result.riskLevel && <Badge className={result.riskLevel === 'HIGH' ? 'bg-red-600 text-white' : result.riskLevel === 'MODERATE' ? 'bg-amber-500 text-white' : 'bg-emerald-600 text-white'}>{result.riskLevel} risk</Badge>}{result.modelName && <Badge variant="outline">{result.modelName} {result.modelVersion || ''}</Badge>}</div>{result.riskLevel === 'MODERATE' && <p className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">Recommend dermatologist review.</p>}{hasValidScore && <div><div className="mb-1 flex justify-between text-sm"><span>Fused malignancy score</span><span className="tabular-nums">{(score * 100).toFixed(1)}%</span></div><div className="h-3 rounded-full bg-muted"><div className="h-3 rounded-full bg-primary" style={{ width: `${score * 100}%` }} /></div><p className="mt-2 text-xs text-muted-foreground">Lesion-level fused model score used for the binary BENIGN/MALIGNANT decision. It is not a calibrated probability of cancer.</p></div>}{!hasValidScore && <p role="alert" className="text-sm text-amber-700">A valid fused malignancy score was not returned.</p>}<p className="text-sm text-muted-foreground">Generated {new Date(result.inferredAt).toLocaleString()}</p>{result.disclaimer && <p className="border-t pt-3 text-xs text-muted-foreground">{result.disclaimer}</p>}</CardContent></Card>
        <Card><CardHeader><CardTitle>Diagnosis information</CardTitle></CardHeader><CardContent className="space-y-2 text-sm text-muted-foreground"><p>The final fusion model supports broad binary classification only: <span className="font-medium text-foreground">{result.predictedLabel}</span>.</p><p>Specific cancer subtype identification is not available from the final fused model. The auxiliary CNN scores below must not be interpreted as a validated BCC, melanoma, SCC, or other subtype diagnosis.</p>{result.subtypeUnavailableReason && <p className="rounded-md border border-amber-300 bg-amber-50 p-3 text-amber-900">{result.subtypeUnavailableReason}</p>}</CardContent></Card>
        <Card className="border-primary/30"><CardHeader><CardTitle>Top-scoring subtype</CardTitle></CardHeader><CardContent className="space-y-2">{topAuxiliary ? <><p className="text-xl font-semibold">{classLabels[topAuxiliary.label] || topAuxiliary.label}</p><p className="text-sm tabular-nums text-muted-foreground">Auxiliary CNN score: {(topAuxiliary.score * 100).toFixed(1)}%</p><p className="text-xs text-muted-foreground">This is the highest valid auxiliary class score, not a confirmed diagnosis or validated cancer subtype. It does not override the final fused {result.predictedLabel} prediction.</p></> : topAuxiliaryScores.length > 1 ? <><p className="font-medium">No unique top-scoring subtype</p><p className="text-sm text-muted-foreground">Tied auxiliary scores: {topAuxiliaryScores.map((item) => classLabels[item.label] || item.label).join(', ')}.</p></> : <p className="text-sm text-muted-foreground">A top-scoring subtype is unavailable because comparable valid auxiliary scores were not returned.</p>}</CardContent></Card>
      </div>
      <div className="space-y-6">
        <Card><CardHeader><CardTitle>Auxiliary CNN class scores</CardTitle></CardHeader><CardContent>{validClassScores.length ? <><p className="mb-4 text-sm text-muted-foreground">These are the mean seven-class softmax scores from the three CNN streams. They are not the final fused output and are not calibrated probabilities.</p><div className="space-y-3">{validClassScores.slice().sort((a, b) => b.score - a.score).map((item) => <div key={item.label}><div className="mb-1 flex justify-between gap-3 text-sm"><span>{classLabels[item.label] || item.label}</span><span className="tabular-nums">{(item.score * 100).toFixed(1)}%</span></div><div className="h-2 rounded-full bg-muted"><div className="h-2 rounded-full bg-primary" style={{ width: `${item.score * 100}%` }} /></div></div>)}</div>{invalidClassScoreCount > 0 && <p role="alert" className="mt-4 text-xs text-amber-700">{invalidClassScoreCount} returned class score(s) were omitted because they were outside the valid 0–1 range.</p>}</> : <p className="text-sm text-muted-foreground">The backend did not return auxiliary class scores for this result. No class distribution is inferred.</p>}</CardContent></Card>
        <Card><CardHeader><CardTitle>Model and input details</CardTitle></CardHeader><CardContent className="space-y-2 text-sm text-muted-foreground"><p>Model: <span className="text-foreground">{result.modelName || 'Not reported'} {result.modelVersion || ''}</span></p><p>Images analyzed: <span className="text-foreground">{result.numImages ?? 'Not reported'}</span>{result.numImages && result.numImages > 1 ? ' (scores averaged at lesion level)' : ''}</p>{result.inputMetadata && <p>Metadata supplied: <span className="text-foreground">age {result.inputMetadata.ageProvided ? 'yes' : 'no'}, sex {result.inputMetadata.sexProvided ? 'yes' : 'unknown'}, localization {result.inputMetadata.localizationProvided ? 'yes' : 'no'}</span></p>}<p>Score calibration: <span className="text-foreground">{result.scoresAreCalibrated ? 'reported as calibrated' : 'not demonstrated'}</span></p>{result.scoreSemantics && <p>Score semantics: <span className="text-foreground">{result.scoreSemantics}</span></p>}{result.streamScores && <p>Inference streams: <span className="text-foreground">{Object.keys(result.streamScores).join(', ')}</span></p>}</CardContent></Card>
        <Card><CardContent className="flex gap-3 p-4 text-sm text-muted-foreground"><AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-600" /><p>This research output does not confirm or exclude cancer and has not been clinically validated.</p></CardContent></Card>
      </div>
    </div>}
  </div>
}

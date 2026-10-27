'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useMemo, useState } from 'react'
import { ArrowLeft, ArrowRight, Check, ImagePlus, Save, ShieldCheck, Trash2 } from 'lucide-react'
import { motion, AnimatePresence } from 'motion/react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { ResearchDisclaimer } from '@/components/common/research-disclaimer'
import { PageHeader } from '@/components/common/page-header'
import { ACCEPTED_IMAGE_TYPES, DEFAULT_MAX_UPLOAD_MB } from '@/lib/config'
import { caseService, patientService, type PendingImage } from '@/lib/services'
import { useModelInfo } from '@/hooks/use-data'

const steps = ['Patient details', 'Clinical history', 'Lesion details', 'Images', 'Review']
type Upload = PendingImage & { localId: string; fingerprint: string; kind: 'clinical' | 'dermoscopic' }
const MAX_IMAGES_PER_MODALITY = 4

const blankHistory = { personalSkinCancerHistory: 'unknown' as const, familySkinCancerHistory: 'unknown' as const, previousLesionEvaluation: 'unknown' as const, immunosuppression: 'not-recorded' as const, medicalHistory: '', medications: '', allergies: '', notes: '' }

export function NewCaseForm() {
  const router = useRouter()
  const { info: modelInfo } = useModelInfo()
  const [step, setStep] = useState(0)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [caseReference, setCaseReference] = useState('')
  const [caseName, setCaseName] = useState('')
  const [patient, setPatient] = useState({ reference: '', age: '', sex: 'not-recorded' as const, consent: 'pending' as const, notes: '' })
  const [history, setHistory] = useState(blankHistory)
  const [lesion, setLesion] = useState({ lesionId: '', bodyRegion: '', anatomicalSite: '', side: 'not-applicable' as const, duration: '', change: 'unknown' as const, symptoms: [] as string[], previousTreatment: '', observations: '', notes: '' })
  const [uploads, setUploads] = useState<Upload[]>([])
  const [draftSaved, setDraftSaved] = useState(false)

  const accept = Object.keys(ACCEPTED_IMAGE_TYPES).join(',')
  const clinical = uploads.filter((x) => x.kind === 'clinical')
  const dermoscopic = uploads.filter((x) => x.kind === 'dermoscopic')
  const localizationOptions = modelInfo?.allowedLocalizations?.length ? modelInfo.allowedLocalizations : ['unknown']
  const canContinue = useMemo(() => {
    if (step === 0) return Boolean(patient.reference.trim() && patient.age && Number(patient.age) >= 0 && patient.consent !== 'pending')
    if (step === 2) return Boolean(lesion.lesionId.trim() && lesion.bodyRegion.trim())
    if (step === 3) return Boolean(dermoscopic.length)
    return true
  }, [step, patient, lesion, dermoscopic.length])

  function updateHistory(key: keyof typeof history, value: string) { setHistory((x) => ({ ...x, [key]: value })) }
  function updateLesion(key: string, value: string) { setLesion((x) => ({ ...x, [key]: value })) }
  async function readFile(file: File, kind: Upload['kind']) {
    if (!Object.keys(ACCEPTED_IMAGE_TYPES).includes(file.type)) throw new Error('Use JPG, JPEG, or PNG images.')
    if (file.size > DEFAULT_MAX_UPLOAD_MB * 1024 * 1024) throw new Error(`Images must be smaller than ${DEFAULT_MAX_UPLOAD_MB} MB.`)
    const src = await new Promise<string>((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(String(reader.result)); reader.onerror = () => reject(new Error('Unable to read this image.')); reader.readAsDataURL(file) })
    const dimensions = await new Promise<{ width: number; height: number }>((resolve, reject) => { const img = new Image(); img.onload = () => resolve({ width: img.width, height: img.height }); img.onerror = () => reject(new Error(`${file.name} is not a readable image.`)); img.src = src })
    const digest = await crypto.subtle.digest('SHA-256', await file.arrayBuffer())
    const fingerprint = Array.from(new Uint8Array(digest)).map((value) => value.toString(16).padStart(2, '0')).join('')
    return { localId: `${Date.now()}-${Math.random()}`, kind, filename: file.name, mimeType: file.type, sizeBytes: file.size, src, ...dimensions, label: kind === 'clinical' ? 'Clinical photograph' : 'Dermoscopic photograph', fingerprint }
  }
  async function onFiles(files: FileList | null, kind: Upload['kind'], input?: HTMLInputElement) {
    if (!files?.length) return
    setError('')
    const selected = Array.from(files)
    const settled = await Promise.allSettled(selected.map((file) => readFile(file, kind)))
    const items = settled.flatMap((entry) => entry.status === 'fulfilled' ? [entry.value] : [])
    const errors = settled.flatMap((entry) => entry.status === 'rejected' ? [entry.reason instanceof Error ? entry.reason.message : 'An image could not be added.'] : [])
    setUploads((existing) => {
      const fingerprints = new Set(existing.map((item) => item.fingerprint))
      const unique = items.filter((item) => { if (fingerprints.has(item.fingerprint)) return false; fingerprints.add(item.fingerprint); return true })
      const sameKindCount = existing.filter((item) => item.kind === kind).length
      const available = Math.max(0, MAX_IMAGES_PER_MODALITY - sameKindCount)
      if (unique.length > available) errors.push(`A maximum of ${MAX_IMAGES_PER_MODALITY} ${kind} images is supported.`)
      return [...existing, ...unique.slice(0, available)]
    })
    if (errors.length) setError(errors.join(' '))
    if (input) input.value = ''
  }
  function removeUpload(localId: string) { setUploads((x) => x.filter((i) => i.localId !== localId)) }
  function saveDraft() { setDraftSaved(true); setTimeout(() => setDraftSaved(false), 2200) }
  async function submit() {
    setSaving(true); setError('')
    try {
      const p = await patientService.create({ ...patient, age: Number(patient.age) })
      const record = await caseService.create({ patientId: p.id, caseReference: caseReference || undefined, caseName: caseName || undefined, history, lesion: { ...lesion, symptoms: lesion.symptoms as any }, images: uploads.map(({ localId, fingerprint, ...image }) => image), asDraft: !dermoscopic.length })
      router.push(`/cases/${record.id}`)
    } catch (e) { setError((e as Error).message || 'Unable to create the case.') } finally { setSaving(false) }
  }
  return <div className="flex flex-col gap-6">
    <PageHeader eyebrow="Workspace" title="New case" description="Create a de-identified research record. You can save a draft at any point." actions={<Button variant="ghost" render={<Link href="/cases" />} nativeButton={false}><ArrowLeft data-icon="inline-start" />Back to cases</Button>} />
    <ResearchDisclaimer compact />
    <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
      <Card className="h-fit"><CardHeader><CardTitle className="font-display text-base">Case setup</CardTitle><CardDescription>{step + 1} of {steps.length}</CardDescription></CardHeader><CardContent><ol className="flex flex-col gap-2">{steps.map((name, i) => <li key={name} className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm ${i === step ? 'bg-accent font-medium text-accent-foreground' : i < step ? 'text-primary' : 'text-muted-foreground'}`}><span className="flex size-6 items-center justify-center rounded-full border text-xs">{i < step ? <Check className="size-3" /> : i + 1}</span>{name}</li>)}</ol></CardContent></Card>
      <Card><CardHeader><CardTitle className="font-display">{steps[step]}</CardTitle><CardDescription>{step === 0 ? 'Use a pseudonymous reference; do not enter direct identifiers.' : step === 3 ? 'Images are stored locally in this browser unless a backend is configured.' : 'Optional research context can be left unrecorded.'}</CardDescription></CardHeader><CardContent>
        {error && <div role="alert" className="mb-5 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}
        <AnimatePresence mode="wait"><motion.div key={step} initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -12 }} transition={{ duration: 0.2 }} className="min-h-[300px]">
          {step === 0 && <div className="grid gap-5 sm:grid-cols-2"><Field label="Case ID"><Input value={caseReference} onChange={(e) => setCaseReference(e.target.value)} placeholder="Optional user-facing case ID" /></Field><Field label="Case name"><Input value={caseName} onChange={(e) => setCaseName(e.target.value)} placeholder="Optional user-facing case name" /></Field><p className="text-xs text-muted-foreground sm:col-span-2">These values are preserved separately from the internal database ID. If both are blank, the lesion ID or generated internal ID is used as the display fallback.</p><Field label="Patient reference" required><Input value={patient.reference} onChange={(e) => setPatient({ ...patient, reference: e.target.value })} placeholder="e.g. Research subject A" /></Field><Field label="Age" required><Input type="number" min="0" max="120" value={patient.age} onChange={(e) => setPatient({ ...patient, age: e.target.value })} /></Field><Field label="Sex"><Select value={patient.sex} onChange={(e) => setPatient({ ...patient, sex: e.target.value as any })} options={['not-recorded','female','male','intersex','prefer-not-to-say']} /></Field><Field label="Consent status" required><Select value={patient.consent} onChange={(e) => setPatient({ ...patient, consent: e.target.value as any })} options={['pending','obtained','declined','not-required']} /></Field><div className="sm:col-span-2"><Field label="Patient notes"><Textarea value={patient.notes} onChange={(e) => setPatient({ ...patient, notes: e.target.value })} placeholder="Optional de-identified notes" /></Field></div></div>}
          {step === 1 && <div className="grid gap-5 sm:grid-cols-2">{(['personalSkinCancerHistory','familySkinCancerHistory','previousLesionEvaluation','immunosuppression'] as const).map((key) => <Field key={key} label={key.replaceAll(/([A-Z])/g, ' $1')}><Select value={history[key]} onChange={(e) => updateHistory(key, e.target.value)} options={['unknown','yes','no','not-recorded']} /></Field>)}<div className="sm:col-span-2 grid gap-5 sm:grid-cols-2"><Field label="Medical history"><Textarea value={history.medicalHistory} onChange={(e) => updateHistory('medicalHistory', e.target.value)} /></Field><Field label="Additional clinical notes"><Textarea value={history.notes} onChange={(e) => updateHistory('notes', e.target.value)} /></Field></div></div>}
          {step === 2 && <div className="grid gap-5 sm:grid-cols-2"><Field label="Lesion ID" required><Input value={lesion.lesionId} onChange={(e) => updateLesion('lesionId', e.target.value)} placeholder="e.g. LS-0001" /></Field><Field label="Localization" required><Select value={lesion.bodyRegion} onChange={(e) => updateLesion('bodyRegion', e.target.value)} options={['', ...localizationOptions]} /></Field><Field label="Anatomical site"><Input value={lesion.anatomicalSite} onChange={(e) => updateLesion('anatomicalSite', e.target.value)} /></Field><Field label="Side"><Select value={lesion.side} onChange={(e) => updateLesion('side', e.target.value)} options={['not-applicable','left','right','midline']} /></Field><Field label="Change over time"><Select value={lesion.change} onChange={(e) => updateLesion('change', e.target.value)} options={['unknown','no-change','size','color','shape','multiple']} /></Field><Field label="Duration"><Input value={lesion.duration} onChange={(e) => updateLesion('duration', e.target.value)} placeholder="If known" /></Field><div className="sm:col-span-2"><Field label="Researcher observations"><Textarea value={lesion.observations} onChange={(e) => updateLesion('observations', e.target.value)} /></Field></div></div>}
          {step === 3 && <div className="grid gap-5 md:grid-cols-2"><UploadBox kind="clinical" items={clinical} accept={accept} onFiles={onFiles} onRemove={removeUpload} onClear={() => setUploads((x) => x.filter((item) => item.kind !== 'clinical'))} /><UploadBox kind="dermoscopic" items={dermoscopic} accept={accept} onFiles={onFiles} onRemove={removeUpload} onClear={() => setUploads((x) => x.filter((item) => item.kind !== 'dermoscopic'))} /><p className="text-xs text-muted-foreground md:col-span-2">Up to four JPG, JPEG, or PNG files per modality. Dermoscopic files are sent together for lesion-level aggregation; clinical files remain separate context images. Duplicate file bytes are ignored.</p></div>}
          {step === 4 && <div className="grid gap-4"><Summary title="Case identity" values={[caseReference || 'No custom case ID', caseName || 'No custom case name']} /><Summary title="Patient" values={[patient.reference, `${patient.age} years`, patient.sex, `Consent: ${patient.consent}`]} /><Summary title="Clinical history" values={[`Personal history: ${history.personalSkinCancerHistory}`, `Family history: ${history.familySkinCancerHistory}`, history.medicalHistory || 'No additional history recorded']} /><Summary title="Lesion" values={[lesion.lesionId, lesion.bodyRegion, lesion.anatomicalSite || 'No anatomical site recorded', `Change: ${lesion.change}`]} /><Summary title="Images" values={[`${uploads.length} image${uploads.length === 1 ? '' : 's'} attached`, `${clinical.length} clinical image${clinical.length === 1 ? '' : 's'}`, `${dermoscopic.length} dermoscopic image${dermoscopic.length === 1 ? '' : 's'}`]} /></div>}
        </motion.div></AnimatePresence>
        <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t pt-5"><Button variant="ghost" onClick={saveDraft}><Save data-icon="inline-start" />{draftSaved ? 'Draft saved' : 'Save draft'}</Button><div className="flex gap-2">{step > 0 && <Button variant="outline" onClick={() => setStep(step - 1)}><ArrowLeft data-icon="inline-start" />Back</Button>}{step < steps.length - 1 ? <Button onClick={() => canContinue ? setStep(step + 1) : setError('Complete the required fields before continuing.')}>Continue<ArrowRight data-icon="inline-end" /></Button> : <Button disabled={saving} onClick={submit}>{saving ? 'Creating…' : 'Create case'}<Check data-icon="inline-end" /></Button>}</div></div>
      </CardContent></Card>
    </div>
  </div>
}

function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) { return <div className="flex flex-col gap-1.5"><Label>{label}{required && <span className="ml-1 text-destructive">*</span>}</Label>{children}</div> }
function Select({ value, onChange, options }: { value: string; onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void; options: string[] }) { return <select value={value} onChange={onChange} className="h-9 rounded-lg border border-input bg-background px-2.5 text-sm outline-none focus-visible:ring-3 focus-visible:ring-ring/25">{options.map((x) => <option key={x} value={x}>{x ? x.replaceAll('-', ' ') : 'Select an option'}</option>)}</select> }
function Summary({ title, values }: { title: string; values: string[] }) { return <div className="rounded-xl border bg-muted/30 p-4"><h3 className="font-display font-semibold">{title}</h3><ul className="mt-2 flex flex-col gap-1 text-sm text-muted-foreground">{values.map((x) => <li key={x}>{x}</li>)}</ul></div> }
function UploadBox({ kind, items, accept, onFiles, onRemove, onClear }: { kind: Upload['kind']; items: Upload[]; accept: string; onFiles: (files: FileList | null, kind: Upload['kind'], input?: HTMLInputElement) => void; onRemove: (id: string) => void; onClear: () => void }) { return <div className="flex flex-col gap-3 rounded-xl border border-dashed bg-muted/20 p-5"><div className="flex items-center justify-between"><div><p className="font-medium capitalize">{kind} photographs</p><p className="text-xs text-muted-foreground">JPG, JPEG or PNG · max 15 MB · up to 4 files</p></div><ImagePlus className="size-5 text-primary" /></div>{items.length ? <div className="grid gap-2">{items.map((item) => <div key={item.localId} className="relative overflow-hidden rounded-lg border bg-black/5"><img src={item.src} alt={`${item.label}: ${item.filename}`} className="h-40 w-full object-contain" /><div className="flex items-center justify-between gap-2 p-2 text-xs"><span className="truncate"><span className="mr-1 rounded bg-muted px-1">{kind}</span>{item.filename}</span><Button variant="ghost" size="icon-sm" aria-label={`Remove ${kind} image ${item.filename}`} onClick={() => onRemove(item.localId)}><Trash2 /></Button></div></div>)}</div> : <p className="text-xs text-muted-foreground">No {kind} images selected.</p>}<div className="flex gap-2"><label className="flex flex-1 cursor-pointer items-center justify-center rounded-lg border bg-card px-4 py-4 text-sm text-muted-foreground transition-colors hover:border-primary hover:text-primary"><span>{items.length ? 'Add more images' : 'Choose images'}</span><input className="sr-only" type="file" multiple accept={accept} onChange={(e) => void onFiles(e.target.files, kind, e.currentTarget)} /></label>{items.length > 0 && <Button type="button" variant="outline" onClick={onClear}>Clear all</Button>}</div></div> }

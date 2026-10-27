'use client'

import Link from 'next/link'
import { useState } from 'react'
import { ArrowLeft, Save, Trash2 } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useCases, usePatients, useRevalidateAll } from '@/hooks/use-data'
import { patientService } from '@/lib/services'
import { caseDisplayLabel } from '@/lib/format'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { PageHeader } from '@/components/common/page-header'
import { ResearchDisclaimer } from '@/components/common/research-disclaimer'
import { formatDate, SEX_LABELS, CONSENT_LABELS } from '@/lib/format'

export function PatientDetailView({ patientId }: { patientId: string }) {
  const { patients, isLoading } = usePatients()
  const { cases: allCases } = useCases()
  const cases = allCases.filter((item) => item.patientId === patientId)
  const router = useRouter()
  const refresh = useRevalidateAll()
  const patient = patients.find((item) => item.id === patientId)
  const [reference, setReference] = useState('')
  const [age, setAge] = useState('')
  const [notes, setNotes] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  if (isLoading) return <div className="p-8 text-sm text-muted-foreground">Loading patient…</div>
  if (!patient) return <div className="space-y-4"><PageHeader title="Patient not found" /><Button render={<Link href="/patients" />} nativeButton={false}><ArrowLeft />Back to patients</Button></div>

  const currentReference = reference || patient.reference
  const currentAge = age || String(patient.age)
  const currentNotes = notes || patient.notes || ''
  const save = async () => {
    const parsedAge = Number(currentAge)
    if (!currentReference.trim() || !Number.isInteger(parsedAge) || parsedAge < 0 || parsedAge > 120) { setError('Enter a patient reference and an age from 0 to 120.'); return }
    setSaving(true); setError('')
    try { await patientService.update(patient.id, { reference: currentReference.trim(), age: parsedAge, notes: currentNotes.trim() }); await refresh(); router.refresh() }
    catch (e) { setError(e instanceof Error ? e.message : 'Unable to save patient.') }
    finally { setSaving(false) }
  }
  const remove = async () => {
    if (!window.confirm('Delete this patient and all associated cases?')) return
    await patientService.remove(patient.id); await refresh(); router.push('/patients')
  }
  return <div className="space-y-6">
    <PageHeader eyebrow="Patient record" title={patient.reference} description={`${patient.id} · Registered ${formatDate(patient.createdAt)}`} actions={<Button variant="outline" render={<Link href="/patients" />} nativeButton={false}><ArrowLeft />Patients</Button>} />
    <ResearchDisclaimer compact />
    {error && <div role="alert" className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{error}</div>}
    <div className="grid gap-6 lg:grid-cols-[1fr_0.9fr]">
      <Card><CardHeader><CardTitle>Edit patient record</CardTitle></CardHeader><CardContent className="space-y-4"><div className="grid gap-4 sm:grid-cols-2"><div className="space-y-1.5"><Label htmlFor="reference">Reference</Label><Input id="reference" value={currentReference} onChange={(e) => setReference(e.target.value)} /></div><div className="space-y-1.5"><Label htmlFor="age">Age</Label><Input id="age" type="number" min="0" max="120" value={currentAge} onChange={(e) => setAge(e.target.value)} /></div></div><div className="grid gap-4 sm:grid-cols-2 text-sm"><p><span className="text-muted-foreground">Sex:</span> {SEX_LABELS[patient.sex]}</p><p><span className="text-muted-foreground">Consent:</span> {CONSENT_LABELS[patient.consent]}</p></div><div className="space-y-1.5"><Label htmlFor="notes">Notes</Label><Textarea id="notes" value={currentNotes} onChange={(e) => setNotes(e.target.value)} /></div><div className="flex justify-between gap-2"><Button variant="destructive" onClick={() => void remove}><Trash2 />Delete</Button><Button disabled={saving} onClick={() => void save}><Save />{saving ? 'Saving…' : 'Save changes'}</Button></div></CardContent></Card>
      <Card><CardHeader><CardTitle>Cases</CardTitle></CardHeader><CardContent>{cases.length ? <div className="space-y-2">{cases.map((item) => <Link key={item.id} href={`/cases/${item.id}`} className="block rounded-lg border p-3 text-sm hover:border-primary"><span className="font-medium">{caseDisplayLabel(item)}</span><span className="ml-2 text-muted-foreground">{item.status}</span></Link>)}</div> : <p className="text-sm text-muted-foreground">No cases recorded for this patient.</p>}</CardContent></Card>
    </div>
  </div>
}

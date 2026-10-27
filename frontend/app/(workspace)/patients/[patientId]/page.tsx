import { PatientDetailView } from '@/components/patients/patient-detail-view'

export default async function PatientPage({ params }: { params: Promise<{ patientId: string }> }) {
  const { patientId } = await params
  return <PatientDetailView patientId={patientId} />
}

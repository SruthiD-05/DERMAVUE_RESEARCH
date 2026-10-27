import type { Metadata } from 'next'
import { PatientsView } from '@/components/patients/patients-view'

export const metadata: Metadata = { title: 'Patients' }

export default function PatientsPage() {
  return <PatientsView />
}

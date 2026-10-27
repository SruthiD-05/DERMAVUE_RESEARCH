import type { Metadata } from 'next'
import { NewCaseForm } from '@/components/patients/new-case-form'

export const metadata: Metadata = { title: 'New case' }

export default function NewCasePage() {
  return <NewCaseForm />
}

import { redirect } from 'next/navigation'

export default function NewCaseRedirect() {
  redirect('/patients/new')
}

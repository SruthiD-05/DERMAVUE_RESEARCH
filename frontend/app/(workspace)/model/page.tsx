import type { Metadata } from 'next'
import { ModelInfoView } from '@/components/model/model-info-view'

export const metadata: Metadata = { title: 'Model status' }
export default function ModelPage() { return <ModelInfoView /> }

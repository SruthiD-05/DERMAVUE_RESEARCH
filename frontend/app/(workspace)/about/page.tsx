import type { Metadata } from 'next'
import { AboutView } from '@/components/about/about-view'

export const metadata: Metadata = { title: 'About and safety' }
export default function AboutPage() { return <AboutView /> }

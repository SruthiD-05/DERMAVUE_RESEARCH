import { Analytics } from '@vercel/analytics/next'
import type { Metadata, Viewport } from 'next'
import { Geist, Geist_Mono, Manrope } from 'next/font/google'
import { Providers } from '@/components/providers'
import './globals.css'

const geist = Geist({ subsets: ['latin'], variable: '--font-geist' })
const geistMono = Geist_Mono({ subsets: ['latin'], variable: '--font-geist-mono' })
const manrope = Manrope({ subsets: ['latin'], variable: '--font-manrope', weight: ['500', '600', '700', '800'] })

export const metadata: Metadata = {
  title: {
    default: 'DERMAVUE — Dermatology Research Workspace',
    template: '%s · DERMAVUE',
  },
  description:
    'A research-grade workspace for organising dermoscopic cases, clinical context, image review and AI-assisted analysis. For research and educational use only.',
  generator: 'v0.app',
  robots: { index: false, follow: false },
  icons: {
    icon: [
      { url: '/icon-light-32x32.png', media: '(prefers-color-scheme: light)' },
      { url: '/icon-dark-32x32.png', media: '(prefers-color-scheme: dark)' },
      { url: '/icon.svg', type: 'image/svg+xml' },
    ],
    apple: '/apple-icon.png',
  },
}

export const viewport: Viewport = {
  colorScheme: 'light dark',
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#f7f8f6' },
    { media: '(prefers-color-scheme: dark)', color: '#0d1622' },
  ],
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning className={`${geist.variable} ${geistMono.variable} ${manrope.variable}`}>
      <body className="antialiased">
        <Providers>{children}</Providers>
        {process.env.NODE_ENV === 'production' && <Analytics />}
      </body>
    </html>
  )
}

import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import { Logo } from '@/components/brand/logo'
import { Button } from '@/components/ui/button'
import { LandingHero } from '@/components/landing/hero'
import { LandingWorkflow } from '@/components/landing/workflow'
import { LandingFeatures } from '@/components/landing/features'
import { LandingTransparency } from '@/components/landing/transparency'
import { RESEARCH_DISCLAIMER } from '@/lib/config'

export default function LandingPage() {
  return (
    <div className="min-h-svh bg-background">
      <header className="sticky top-0 z-30 border-b border-border/60 bg-background/75 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-[1240px] items-center justify-between px-5 md:px-8">
          <Link href="/" className="rounded-md outline-none focus-visible:ring-2 focus-visible:ring-ring">
            <Logo />
          </Link>
          <nav aria-label="Main" className="hidden items-center gap-7 text-sm text-muted-foreground md:flex">
            <a href="#workflow" className="transition-colors hover:text-foreground">
              Workflow
            </a>
            <a href="#features" className="transition-colors hover:text-foreground">
              Capabilities
            </a>
            <a href="#transparency" className="transition-colors hover:text-foreground">
              Model transparency
            </a>
            <Link href="/about" className="transition-colors hover:text-foreground">
              Safety
            </Link>
          </nav>
          <Button render={<Link href="/dashboard" />} nativeButton={false}>
            Open workspace
            <ArrowRight data-icon="inline-end" />
          </Button>
        </div>
      </header>

      <main>
        <LandingHero />
        <LandingWorkflow />
        <LandingFeatures />
        <LandingTransparency />
      </main>

      <footer className="border-t bg-sidebar text-sidebar-foreground">
        <div className="mx-auto flex max-w-[1240px] flex-col gap-8 px-5 py-12 md:flex-row md:items-start md:justify-between md:px-8">
          <div className="flex max-w-md flex-col gap-4">
            <Logo tone="inverse" />
            <p className="text-sm leading-relaxed text-sidebar-muted">{RESEARCH_DISCLAIMER}</p>
          </div>
          <nav aria-label="Footer" className="grid grid-cols-2 gap-x-12 gap-y-3 text-sm">
            <Link href="/dashboard" className="text-sidebar-foreground/80 hover:text-white">
              Dashboard
            </Link>
            <Link href="/model" className="text-sidebar-foreground/80 hover:text-white">
              Model status
            </Link>
            <Link href="/cases/new" className="text-sidebar-foreground/80 hover:text-white">
              New case
            </Link>
            <Link href="/about" className="text-sidebar-foreground/80 hover:text-white">
              About & safety
            </Link>
          </nav>
        </div>
        <div className="border-t border-sidebar-border">
          <p className="mx-auto max-w-[1240px] px-5 py-5 font-mono text-[11px] tracking-wide text-sidebar-muted md:px-8">
            DERMAVUE research prototype · Not a medical device · Not for clinical diagnosis
          </p>
        </div>
      </footer>
    </div>
  )
}

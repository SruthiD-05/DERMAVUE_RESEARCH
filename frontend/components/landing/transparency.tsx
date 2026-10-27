import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { DEVELOPER_REPORTED_ACCURACY } from '@/lib/config'
import { Reveal } from './reveal'

const PRINCIPLES = [
  'Predictions appear only when a connected model returns them.',
  'Scores are shown as the model reports them, and never as certainty.',
  'Demo records and demonstration outputs are always labelled.',
  'Performance figures are shown with their evaluation context, or not at all.',
]

export function LandingTransparency() {
  return (
    <section id="transparency" className="scroll-mt-20 border-t bg-sidebar text-sidebar-foreground">
      <div className="mx-auto grid max-w-[1240px] gap-12 px-5 py-20 md:px-8 lg:grid-cols-2 lg:py-24">
        <Reveal className="flex flex-col gap-6">
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-sidebar-primary">Model transparency</p>
          <h2 className="font-display text-3xl font-bold text-white md:text-4xl">
            We show you what the model is — and what it isn&apos;t.
          </h2>
          <ul className="flex flex-col gap-3">
            {PRINCIPLES.map((p) => (
              <li key={p} className="flex items-start gap-3 text-sm leading-relaxed text-sidebar-foreground/85">
                <span aria-hidden="true" className="mt-2 size-1.5 shrink-0 rounded-full bg-sidebar-primary" />
                {p}
              </li>
            ))}
          </ul>
          <Button
            variant="outline"
            className="w-fit border-white/15 bg-transparent text-white hover:bg-white/10 hover:text-white"
            render={<Link href="/model" />}
            nativeButton={false}
          >
            View model status
            <ArrowRight data-icon="inline-end" />
          </Button>
        </Reveal>
        <Reveal delay={0.1} className="flex flex-col justify-center gap-6 rounded-2xl border border-sidebar-border bg-sidebar-accent/50 p-8">
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-sidebar-muted">Developer-reported accuracy</p>
          <p className="font-display text-6xl font-extrabold tracking-tight text-white">{DEVELOPER_REPORTED_ACCURACY}</p>
          <p className="text-sm leading-relaxed text-sidebar-foreground/75">
            This figure was reported by the model&apos;s developer. It has not been independently verified, and its
            dataset, sample size and split methodology are required before it can be interpreted. It says nothing
            about performance on any individual case.
          </p>
        </Reveal>
      </div>
    </section>
  )
}

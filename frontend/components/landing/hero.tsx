'use client'

import Image from 'next/image'
import Link from 'next/link'
import { motion } from 'motion/react'
import { ArrowRight, Crosshair, FileImage, ShieldAlert } from 'lucide-react'
import { Button } from '@/components/ui/button'

const ease = [0.22, 1, 0.36, 1] as const

export function LandingHero() {
  return (
    <section className="relative overflow-hidden">
      <div aria-hidden="true" className="hairline-grid pointer-events-none absolute inset-0 opacity-60" />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-40 -top-40 size-[640px] rounded-full bg-primary/10 blur-3xl"
      />
      <div className="relative mx-auto grid max-w-[1240px] items-center gap-14 px-5 pb-20 pt-16 md:px-8 lg:grid-cols-[1.05fr_1fr] lg:pb-28 lg:pt-24">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease }}
          className="flex flex-col gap-7"
        >
          <p className="inline-flex w-fit items-center gap-2 rounded-full border bg-card px-3 py-1 font-mono text-[11px] uppercase tracking-[0.16em] text-muted-foreground shadow-soft">
            <span className="size-1.5 rounded-full bg-primary" aria-hidden="true" />
            Dermatology research workspace
          </p>
          <h1 className="font-display text-[40px] font-extrabold leading-[1.04] text-foreground md:text-[56px]">
            Dermoscopic cases, <span className="text-primary">organised</span> for careful review.
          </h1>
          <p className="max-w-xl text-lg leading-relaxed text-muted-foreground text-pretty">
            DERMAVUE brings patient context, lesion documentation, image review and model-assisted analysis into
            one calm, auditable workspace — built for researchers, not for diagnosis.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <Button size="lg" className="h-11 px-5" render={<Link href="/dashboard" />} nativeButton={false}>
              Open workspace
              <ArrowRight data-icon="inline-end" />
            </Button>
            <Button size="lg" variant="outline" className="h-11 px-5" render={<Link href="/cases/new" />} nativeButton={false}>
              Register a case
            </Button>
          </div>
          <p className="flex max-w-lg items-start gap-2 text-xs leading-relaxed text-muted-foreground">
            <ShieldAlert aria-hidden="true" className="mt-0.5 size-3.5 shrink-0 text-warning" />
            Outputs are model-generated for research and educational purposes and are not a medical diagnosis.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 24, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.9, ease, delay: 0.1 }}
          className="relative"
        >
          <div className="relative overflow-hidden rounded-[22px] border bg-sidebar p-2.5 shadow-lift">
            <div className="flex items-center justify-between px-3 pb-2.5 pt-1.5">
              <div className="flex items-center gap-2">
                <span className="size-2 rounded-full bg-white/15" />
                <span className="size-2 rounded-full bg-white/15" />
                <span className="size-2 rounded-full bg-white/15" />
              </div>
              <span className="font-mono text-[10px] tracking-[0.16em] text-sidebar-muted">DV-DEMO-0142 · DERMOSCOPIC</span>
            </div>
            <div className="relative aspect-[4/3] overflow-hidden rounded-2xl bg-black">
              <Image
                src="/demo/dermoscopy-01.png"
                alt="Illustrative dermoscopic image of a pigmented skin lesion under polarised magnification"
                fill
                priority
                sizes="(min-width: 1024px) 560px, 100vw"
                className="object-cover"
              />
              <div aria-hidden="true" className="absolute inset-0 flex items-center justify-center">
                <motion.div
                  initial={{ opacity: 0, scale: 1.2 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 1, ease, delay: 0.6 }}
                  className="size-[46%] rounded-full border border-dashed border-white/50"
                />
              </div>
              <div className="absolute left-3 top-3 flex items-center gap-1.5 rounded-md bg-black/55 px-2 py-1 font-mono text-[10px] text-white/85 backdrop-blur">
                <Crosshair aria-hidden="true" className="size-3" />
                ROI · 10× polarised
              </div>
              <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between rounded-lg bg-black/55 px-3 py-2 text-white backdrop-blur">
                <span className="flex items-center gap-2 text-xs">
                  <FileImage aria-hidden="true" className="size-3.5 opacity-80" />
                  Illustrative image · demo asset
                </span>
                <span className="font-mono text-[10px] text-white/70">2048 × 1536</span>
              </div>
            </div>
          </div>

          <motion.div
            initial={{ opacity: 0, x: 16 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7, ease, delay: 0.5 }}
            className="absolute -bottom-8 -left-4 hidden w-[260px] rounded-2xl border bg-card p-4 shadow-lift md:block"
          >
            <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">Inference</p>
            <p className="mt-1.5 font-display text-sm font-bold">Awaiting model connection</p>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
              Analysis runs only against a connected research model. Nothing is simulated.
            </p>
          </motion.div>
        </motion.div>
      </div>
    </section>
  )
}

import Image from 'next/image'
import { Database, Eye, History, Lock, NotebookPen, PlugZap } from 'lucide-react'
import { Reveal } from './reveal'

const FEATURES = [
  { icon: Eye, title: 'Careful image review', body: 'Zoom, compare clinical and dermoscopic views, and keep metadata beside the pixels.' },
  { icon: History, title: 'Longitudinal case history', body: 'Every case keeps its images, notes, review status and follow-up in one timeline.' },
  { icon: PlugZap, title: 'Honest model integration', body: 'Connects to your FastAPI backend. When no model is available, analysis is simply disabled.' },
  { icon: NotebookPen, title: 'Structured annotation', body: 'Researcher notes and review states stay attached to the case and export with the report.' },
  { icon: Database, title: 'Local-first storage', body: 'Records live in this browser until a backend is configured. Nothing is sent without it.' },
  { icon: Lock, title: 'De-identified by design', body: 'Patient references replace names, and demo records are always visibly labelled.' },
]

export function LandingFeatures() {
  return (
    <section id="features" className="scroll-mt-20 border-t">
      <div className="mx-auto grid max-w-[1240px] gap-14 px-5 py-20 md:px-8 lg:grid-cols-[0.9fr_1.1fr] lg:py-24">
        <Reveal className="flex flex-col gap-6">
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-primary">Capabilities</p>
          <h2 className="font-display text-3xl font-bold md:text-4xl">A quiet interface for precise work.</h2>
          <p className="max-w-md leading-relaxed text-muted-foreground">
            Designed like a research instrument: dense where it needs to be, calm everywhere else, and explicit about
            what the software does and does not know.
          </p>
          <div className="relative mt-2 aspect-[5/4] overflow-hidden rounded-2xl border bg-muted shadow-soft">
            <Image
              src="/demo/clinical-01.png"
              alt="Illustrative clinical photograph of skin on a forearm with a small pigmented lesion"
              fill
              sizes="(min-width: 1024px) 480px, 100vw"
              className="object-cover"
            />
            <span className="absolute bottom-3 left-3 rounded-md bg-black/55 px-2 py-1 font-mono text-[10px] text-white/85 backdrop-blur">
              Clinical view · demo asset
            </span>
          </div>
        </Reveal>
        <div className="grid gap-x-8 gap-y-10 self-center sm:grid-cols-2">
          {FEATURES.map((f, i) => (
            <Reveal key={f.title} delay={(i % 2) * 0.06} className="flex flex-col gap-3">
              <f.icon aria-hidden="true" className="size-5 text-primary" />
              <h3 className="font-display text-base font-bold">{f.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{f.body}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}

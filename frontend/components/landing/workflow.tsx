import { ClipboardList, FileText, ScanSearch, UserPlus } from 'lucide-react'
import { Reveal } from './reveal'

const STEPS = [
  {
    icon: UserPlus,
    title: 'Register',
    body: 'Record a de-identified patient reference, consent status and relevant clinical history.',
  },
  {
    icon: ClipboardList,
    title: 'Document',
    body: 'Describe the lesion — region, laterality, evolution and symptoms — then attach clinical and dermoscopic images.',
  },
  {
    icon: ScanSearch,
    title: 'Analyse',
    body: 'Submit the dermoscopic image to a connected research model and review exactly what it returns.',
  },
  {
    icon: FileText,
    title: 'Report',
    body: 'Annotate, mark review status and export a clearly labelled research report for your records.',
  },
]

export function LandingWorkflow() {
  return (
    <section id="workflow" className="scroll-mt-20 border-t bg-card/50">
      <div className="mx-auto max-w-[1240px] px-5 py-20 md:px-8 lg:py-24">
        <Reveal className="flex max-w-2xl flex-col gap-3">
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-primary">Workflow</p>
          <h2 className="font-display text-3xl font-bold md:text-4xl">Four deliberate steps, one continuous record.</h2>
        </Reveal>
        <ol className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((step, i) => (
            <Reveal as="li" key={step.title} delay={i * 0.08} className="group relative flex flex-col gap-5 rounded-2xl border bg-card p-6 shadow-soft">
              <div className="flex items-center justify-between">
                <span className="flex size-10 items-center justify-center rounded-xl bg-secondary text-primary">
                  <step.icon aria-hidden="true" className="size-5" />
                </span>
                <span className="font-mono text-xs text-muted-foreground">0{i + 1}</span>
              </div>
              <div className="flex flex-col gap-2">
                <h3 className="font-display text-lg font-bold">{step.title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">{step.body}</p>
              </div>
            </Reveal>
          ))}
        </ol>
      </div>
    </section>
  )
}

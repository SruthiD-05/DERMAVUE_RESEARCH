/* eslint-disable @next/next/no-img-element -- local data URLs from IndexedDB can't go through next/image */
import { ImageOff } from 'lucide-react'
import type { CaseImage } from '@/lib/types'
import { cn } from '@/lib/utils'

export function CaseThumb({ images, className }: { images: CaseImage[]; className?: string }) {
  const image = images.find((i) => i.kind === 'dermoscopic') ?? images[0]
  return (
    <span className={cn('relative flex size-10 shrink-0 items-center justify-center overflow-hidden rounded-lg border bg-muted', className)}>
      {image ? (
        <img src={image.src} alt="" className="size-full object-cover" loading="lazy" />
      ) : (
        <ImageOff aria-hidden="true" className="size-4 text-muted-foreground" />
      )}
    </span>
  )
}

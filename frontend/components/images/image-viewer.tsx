'use client'

import { useMemo, useState } from 'react'
import { Maximize2, Minus, Plus, RotateCcw } from 'lucide-react'
import type { CaseImage } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

export function ImageViewer({ images }: { images: CaseImage[] }) {
  const [index, setIndex] = useState(0)
  const [zoom, setZoom] = useState(100)
  const image = images[index]
  const label = useMemo(() => image?.kind === 'dermoscopic' ? 'Dermoscopy' : image?.kind === 'clinical' ? 'Clinical photograph' : 'Additional image', [image])
  if (!image) return <Card><CardContent className="p-8 text-center text-sm text-muted-foreground">No images have been uploaded for this case.</CardContent></Card>
  return <Card>
    <CardContent className="space-y-4 p-4">
      <div className="flex items-center justify-between gap-3"><div><p className="text-sm font-medium">{label}</p><p className="text-xs text-muted-foreground">{image.filename}</p></div><div className="flex items-center gap-1"><Button variant="ghost" size="icon-sm" onClick={() => setZoom(Math.max(50, zoom - 10))} aria-label="Zoom out"><Minus /></Button><span className="w-12 text-center text-xs tabular-nums">{zoom}%</span><Button variant="ghost" size="icon-sm" onClick={() => setZoom(Math.min(200, zoom + 10))} aria-label="Zoom in"><Plus /></Button><Button variant="ghost" size="icon-sm" onClick={() => setZoom(100)} aria-label="Reset zoom"><RotateCcw /></Button><Button variant="ghost" size="icon-sm" onClick={(e) => { const el = e.currentTarget.closest('[data-viewer]'); if (el instanceof HTMLElement && el.requestFullscreen) void el.requestFullscreen() }} aria-label="Fullscreen"><Maximize2 /></Button></div></div>
      <div data-viewer className="flex min-h-[320px] items-center justify-center overflow-auto rounded-lg bg-slate-950/95 p-4"><img src={image.src} alt={image.label || image.filename} style={{ width: `${zoom}%` }} className="max-h-[620px] max-w-none object-contain transition-[width] duration-200" /></div>
      {images.length > 1 && <div className="flex gap-2 overflow-x-auto">{images.map((item, i) => <button key={item.id} onClick={() => setIndex(i)} className={`h-16 w-20 shrink-0 overflow-hidden rounded-md ring-1 ${i === index ? 'ring-primary' : 'ring-border'}`}><img src={item.src} alt={item.filename} className="h-full w-full object-cover" /></button>)}</div>}
    </CardContent>
  </Card>
}

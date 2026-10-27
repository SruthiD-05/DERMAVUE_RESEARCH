'use client'

import { ThemeProvider } from 'next-themes'
import { SWRConfig } from 'swr'
import { MotionConfig } from 'motion/react'
import { TooltipProvider } from '@/components/ui/tooltip'
import { Toaster } from '@/components/ui/sonner'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem disableTransitionOnChange>
      <SWRConfig value={{ revalidateOnFocus: false, dedupingInterval: 1500 }}>
        <MotionConfig reducedMotion="user">
          <TooltipProvider delay={200}>
            {children}
            <Toaster position="bottom-right" />
          </TooltipProvider>
        </MotionConfig>
      </SWRConfig>
    </ThemeProvider>
  )
}

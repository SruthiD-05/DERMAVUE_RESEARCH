'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useTheme } from 'next-themes'
import { Menu, Moon, Plus, Search, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetTitle } from '@/components/ui/sheet'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { ModelStateBadge } from '@/components/common/status-badges'
import { SidebarContent } from './app-sidebar'
import { useModelStatus, useSettings } from '@/hooks/use-data'

export function TopBar() {
  const router = useRouter()
  const [query, setQuery] = useState('')
  const [menuOpen, setMenuOpen] = useState(false)
  const { resolvedTheme, setTheme } = useTheme()
  const { status } = useModelStatus()
  const { settings } = useSettings()

  function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    const q = query.trim()
    router.push(q ? `/cases?q=${encodeURIComponent(q)}` : '/cases')
  }

  const initials = settings.displayName
    .split(' ')
    .map((p) => p[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

  return (
    <header className="no-print sticky top-0 z-20 flex h-16 items-center gap-3 border-b bg-background/80 px-4 backdrop-blur-xl md:px-8">
      <Button variant="ghost" size="icon" className="lg:hidden" aria-label="Open navigation" onClick={() => setMenuOpen(true)}>
        <Menu />
      </Button>
      <Sheet open={menuOpen} onOpenChange={setMenuOpen}>
        <SheetContent side="left" className="w-[272px] border-none p-0" showCloseButton={false}>
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          <SidebarContent onNavigate={() => setMenuOpen(false)} />
        </SheetContent>
      </Sheet>

      <form role="search" onSubmit={onSubmit} className="relative flex max-w-md flex-1 items-center">
        <label htmlFor="global-search" className="sr-only">
          Search cases and patients
        </label>
        <Search aria-hidden="true" className="pointer-events-none absolute left-3 size-4 text-muted-foreground" />
        <input
          id="global-search"
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search case ID, patient reference, lesion…"
          className="h-9 w-full rounded-lg border border-input bg-card pl-9 pr-3 text-sm outline-none transition-shadow placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/25"
        />
      </form>

      <div className="ml-auto flex items-center gap-2">
        <Link href="/model" className="hidden rounded-full outline-none focus-visible:ring-2 focus-visible:ring-ring md:block">
          <ModelStateBadge state={status?.state ?? 'loading'} className="h-7 px-2.5" />
        </Link>
        <Tooltip>
          <TooltipTrigger
            render={
              <Button
                variant="ghost"
                size="icon"
                aria-label="Toggle colour theme"
                onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
              />
            }
          >
            <Sun className="dark:hidden" />
            <Moon className="hidden dark:block" />
          </TooltipTrigger>
          <TooltipContent>Toggle theme</TooltipContent>
        </Tooltip>
        <Button render={<Link href="/cases/new" />} nativeButton={false} className="hidden sm:inline-flex">
          <Plus data-icon="inline-start" />
          New case
        </Button>
        <span
          aria-label={`Signed in locally as ${settings.displayName}`}
          className="flex size-8 items-center justify-center rounded-full bg-ink font-display text-[11px] font-bold text-background"
        >
          {initials || 'R'}
        </span>
      </div>
    </header>
  )
}

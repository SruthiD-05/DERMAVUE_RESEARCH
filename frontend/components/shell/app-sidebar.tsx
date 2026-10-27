'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Activity,
  FolderOpen,
  BarChart3,
  FileText,
  LayoutDashboard,
  PlusCircle,
  Settings,
  ShieldCheck,
  Users,
  type LucideIcon,
} from 'lucide-react'
import { motion } from 'motion/react'
import { Logo } from '@/components/brand/logo'
import { MODEL_STATE_LABELS } from '@/components/common/status-badges'
import { useModelStatus, useSettings } from '@/hooks/use-data'
import { cn } from '@/lib/utils'

interface NavItem {
  href: string
  label: string
  icon: LucideIcon
  match?: (path: string) => boolean
}

const PRIMARY: NavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  {
    href: '/cases',
    label: 'Cases',
    icon: FolderOpen,
    match: (p) => p.startsWith('/cases') && !p.startsWith('/cases/new'),
  },
  { href: '/cases/new', label: 'New case', icon: PlusCircle },
  { href: '/patients', label: 'Patients', icon: Users },
]

const SECONDARY: NavItem[] = [
  { href: '/insights', label: 'Insights', icon: BarChart3 },
  { href: '/reports', label: 'Reports', icon: FileText },
  { href: '/model', label: 'Model status', icon: Activity },
  { href: '/about', label: 'About & safety', icon: ShieldCheck },
  { href: '/settings', label: 'Settings', icon: Settings },
]

function NavLink({ item, onNavigate }: { item: NavItem; onNavigate?: () => void }) {
  const pathname = usePathname()
  const active = item.match ? item.match(pathname) : pathname === item.href || pathname.startsWith(`${item.href}/`)
  const Icon = item.icon
  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      aria-current={active ? 'page' : undefined}
      className={cn(
        'group relative flex h-9 items-center gap-3 rounded-lg px-3 text-[13.5px] font-medium outline-none transition-colors',
        'text-sidebar-foreground/75 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:ring-2 focus-visible:ring-sidebar-ring',
        active && 'text-sidebar-accent-foreground',
      )}
    >
      {active && (
        <motion.span
          layoutId="sidebar-active"
          className="absolute inset-0 rounded-lg bg-sidebar-accent ring-1 ring-white/5"
          transition={{ type: 'spring', stiffness: 500, damping: 40 }}
        />
      )}
      <Icon
        aria-hidden="true"
        className={cn('relative size-4 shrink-0', active ? 'text-sidebar-primary' : 'text-sidebar-muted')}
      />
      <span className="relative">{item.label}</span>
    </Link>
  )
}

export function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const { status } = useModelStatus()
  const { settings } = useSettings()
  const state = status?.state ?? 'loading'
  const ok = state === 'connected'

  return (
    <div className="flex h-full flex-col bg-sidebar text-sidebar-foreground">
      <div className="flex h-16 items-center px-5">
        <Link href="/" onClick={onNavigate} className="rounded-md outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring">
          <Logo tone="inverse" />
        </Link>
      </div>

      <div className="px-5 pb-4">
        <p className="truncate text-[11px] text-sidebar-muted">{settings.workspaceName}</p>
      </div>

      <nav aria-label="Primary" className="flex flex-1 flex-col gap-6 overflow-y-auto px-3">
        <div className="flex flex-col gap-0.5">
          <p className="px-3 pb-2 font-mono text-[10px] uppercase tracking-[0.18em] text-sidebar-muted/80">Workspace</p>
          {PRIMARY.map((item) => (
            <NavLink key={item.href} item={item} onNavigate={onNavigate} />
          ))}
        </div>
        <div className="flex flex-col gap-0.5">
          <p className="px-3 pb-2 font-mono text-[10px] uppercase tracking-[0.18em] text-sidebar-muted/80">System</p>
          {SECONDARY.map((item) => (
            <NavLink key={item.href} item={item} onNavigate={onNavigate} />
          ))}
        </div>
      </nav>

      <div className="p-3">
        <Link
          href="/model"
          onClick={onNavigate}
          className="flex flex-col gap-2 rounded-xl border border-sidebar-border bg-sidebar-accent/60 p-3.5 outline-none transition-colors hover:bg-sidebar-accent focus-visible:ring-2 focus-visible:ring-sidebar-ring"
        >
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-sidebar-muted">Inference</span>
            <span className="relative flex size-2">
              {ok && <span className="absolute inline-flex size-full animate-ping rounded-full bg-sidebar-primary opacity-60" />}
              <span className={cn('relative inline-flex size-2 rounded-full', ok ? 'bg-sidebar-primary' : 'bg-[#D59B42]')} />
            </span>
          </div>
          <p className="text-[13px] font-medium text-white">{MODEL_STATE_LABELS[state]}</p>
          <p className="line-clamp-2 text-[11px] leading-relaxed text-sidebar-muted">
            {ok ? `${status?.modelName ?? 'Model'} ${status?.modelVersion ?? ''}` : 'Analysis disabled until a model backend is connected.'}
          </p>
        </Link>
      </div>
    </div>
  )
}

export function AppSidebar() {
  return (
    <aside className="no-print fixed inset-y-0 left-0 z-30 hidden w-[248px] border-r border-sidebar-border lg:block">
      <SidebarContent />
    </aside>
  )
}

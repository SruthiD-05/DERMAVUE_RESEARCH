'use client'

import { useState } from 'react'
import { useTheme } from 'next-themes'
import { useRevalidateAll, useSettings } from '@/hooks/use-data'
import { settingsService } from '@/lib/services'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { PageHeader } from '@/components/common/page-header'

export function SettingsView() {
  const { settings } = useSettings(); const { setTheme, theme } = useTheme(); const refresh = useRevalidateAll(); const [saved, setSaved] = useState(false)
  const [workspaceName, setWorkspaceName] = useState(settings.workspaceName); const [displayName, setDisplayName] = useState(settings.displayName); const [maxUploadMb, setMaxUploadMb] = useState(String(settings.maxUploadMb))
  const save = async () => { await settingsService.save({ ...settings, workspaceName: workspaceName.trim() || settings.workspaceName, displayName: displayName.trim() || settings.displayName, maxUploadMb: Math.max(1, Number(maxUploadMb) || settings.maxUploadMb) }); await refresh(); setSaved(true); window.setTimeout(() => setSaved(false), 1800) }
  return <div className="space-y-6"><PageHeader eyebrow="Workspace settings" title="Configure your local workspace" description="These settings affect this browser workspace and do not change the research model." /><Card><CardHeader><CardTitle>Workspace</CardTitle></CardHeader><CardContent className="grid gap-4 sm:grid-cols-2"><div className="space-y-2"><Label htmlFor="workspace">Workspace name</Label><Input id="workspace" value={workspaceName} onChange={(e) => setWorkspaceName(e.target.value)} /></div><div className="space-y-2"><Label htmlFor="display">Display name</Label><Input id="display" value={displayName} onChange={(e) => setDisplayName(e.target.value)} /></div><div className="space-y-2"><Label htmlFor="upload">Maximum upload size (MB)</Label><Input id="upload" type="number" min="1" value={maxUploadMb} onChange={(e) => setMaxUploadMb(e.target.value)} /></div><div className="space-y-2"><Label htmlFor="theme">Theme</Label><select id="theme" value={theme || 'system'} onChange={(e) => setTheme(e.target.value)} className="h-9 w-full rounded-md border bg-background px-3 text-sm"><option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option></select></div></CardContent></Card><Card><CardHeader><CardTitle>Demo data</CardTitle></CardHeader><CardContent className="flex flex-wrap items-center justify-between gap-3"><p className="max-w-xl text-sm text-muted-foreground">Demo records are clearly labeled. Keeping them visible is useful for exploring the UI, but they are not real patient data.</p><div className="flex gap-2"><Button variant="outline" onClick={async () => { await settingsService.restoreDemo(); await refresh() }}>Restore demo</Button><Button variant="outline" onClick={async () => { await settingsService.removeDemo(); await refresh() }}>Hide demo</Button><Button variant="destructive" onClick={async () => { if (window.confirm('Clear all local records and images?')) { await settingsService.clearAll(); await refresh() } }}>Clear local data</Button></div></CardContent></Card><div className="flex justify-end"><Button onClick={() => void save()}>{saved ? 'Saved' : 'Save settings'}</Button></div></div>
}

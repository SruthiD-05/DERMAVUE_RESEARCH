'use client'

import { useMemo } from 'react'
import { Bar, BarChart, CartesianGrid, XAxis } from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from '@/components/ui/chart'
import type { CaseWithPatient } from '@/lib/types'

const config = {
  cases: { label: 'Cases', color: 'var(--chart-1)' },
} satisfies ChartConfig

const WEEKS = 8

export function ActivityChart({ cases }: { cases: CaseWithPatient[] }) {
  const data = useMemo(() => {
    const now = new Date()
    const startOfWeek = new Date(now)
    startOfWeek.setHours(0, 0, 0, 0)
    startOfWeek.setDate(startOfWeek.getDate() - ((startOfWeek.getDay() + 6) % 7))
    return Array.from({ length: WEEKS }, (_, i) => {
      const start = new Date(startOfWeek)
      start.setDate(start.getDate() - (WEEKS - 1 - i) * 7)
      const end = new Date(start)
      end.setDate(end.getDate() + 7)
      const count = cases.filter((c) => {
        const t = new Date(c.createdAt)
        return t >= start && t < end
      }).length
      return {
        week: start.toLocaleDateString(undefined, { day: 'numeric', month: 'short' }),
        cases: count,
      }
    })
  }, [cases])

  return (
    <Card className="shadow-soft">
      <CardHeader>
        <CardTitle className="font-display">Case intake</CardTitle>
        <CardDescription>Cases created per week, last {WEEKS} weeks</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={config} className="aspect-[16/9] w-full">
          <BarChart data={data} margin={{ left: 0, right: 0, top: 4 }}>
            <CartesianGrid vertical={false} strokeDasharray="3 3" />
            <XAxis dataKey="week" tickLine={false} axisLine={false} tickMargin={8} fontSize={11} interval="preserveStartEnd" />
            <ChartTooltip cursor={false} content={<ChartTooltipContent hideLabel={false} />} />
            <Bar dataKey="cases" fill="var(--color-cases)" radius={[5, 5, 2, 2]} maxBarSize={22} />
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}

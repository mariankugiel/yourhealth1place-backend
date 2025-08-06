"use client"

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, XAxis, YAxis } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

const data = [
  { month: "Jan", metrics: 65 },
  { month: "Feb", metrics: 59 },
  { month: "Mar", metrics: 80 },
  { month: "Apr", metrics: 81 },
  { month: "May", metrics: 56 },
  { month: "Jun", metrics: 55 },
]

export function PatientMetricsChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Patient Metrics</CardTitle>
        <CardDescription>Monthly patient health metrics overview</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer
          config={{
            metrics: {
              label: "Health Metrics",
              color: "hsl(var(--chart-1))",
            },
          }}
          className="h-[300px]"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <ChartTooltip content={<ChartTooltipContent />} />
              <Bar dataKey="metrics" fill="var(--color-metrics)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}

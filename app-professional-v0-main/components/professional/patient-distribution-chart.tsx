"use client"

import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartLegend } from "@/components/ui/chart"

const data = [
  { name: "18-24", value: 15 },
  { name: "25-34", value: 25 },
  { name: "35-44", value: 30 },
  { name: "45-54", value: 20 },
  { name: "55+", value: 10 },
]

export function PatientDistributionChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Patient Age Distribution</CardTitle>
        <CardDescription>Breakdown of patient demographics by age group</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer
          config={{
            "18-24": {
              label: "18-24",
              color: "hsl(var(--chart-1))",
            },
            "25-34": {
              label: "25-34",
              color: "hsl(var(--chart-2))",
            },
            "35-44": {
              label: "35-44",
              color: "hsl(var(--chart-3))",
            },
            "45-54": {
              label: "45-54",
              color: "hsl(var(--chart-4))",
            },
            "55+": {
              label: "55+",
              color: "hsl(var(--chart-5))",
            },
          }}
          className="h-[300px]"
        >
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={data} cx="50%" cy="50%" labelLine={false} outerRadius={80} fill="#8884d8" dataKey="value">
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={`var(--color-${entry.name})`} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <ChartLegend />
        </ChartContainer>
      </CardContent>
    </Card>
  )
}

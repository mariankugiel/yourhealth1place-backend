"use client"

import type React from "react"
import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"

// Sample data - this would be replaced with real patient data
const sampleData = [
  { date: "Jan", weight: 70, bloodPressure: 120, glucose: 95 },
  { date: "Feb", weight: 69, bloodPressure: 118, glucose: 92 },
  { date: "Mar", weight: 68, bloodPressure: 115, glucose: 90 },
  { date: "Apr", weight: 67.5, bloodPressure: 117, glucose: 88 },
  { date: "May", weight: 67, bloodPressure: 116, glucose: 89 },
  { date: "Jun", weight: 66.5, bloodPressure: 115, glucose: 87 },
]

interface HealthMetricsChartProps {
  data?: Array<{ date: Date; value: number }>
  metricName?: string
  patientId?: string
  className?: string
}

export const HealthMetricsChart: React.FC<HealthMetricsChartProps> = ({ data, metricName, patientId, className }) => {
  const [metricType, setMetricType] = useState<string>("weight")

  const getMetricColor = (metric: string) => {
    switch (metric?.toLowerCase()) {
      case "weight":
        return "#4f46e5"
      case "bloodpressure":
      case "blood pressure":
        return "#ef4444"
      case "glucose":
        return "#10b981"
      case "heart rate":
      case "heartrate":
        return "#f59e0b"
      case "cholesterol":
        return "#8b5cf6"
      default:
        return "#4f46e5"
    }
  }

  const getMetricUnit = (metric: string) => {
    switch (metric?.toLowerCase()) {
      case "weight":
        return "kg"
      case "bloodpressure":
      case "blood pressure":
        return "mmHg"
      case "glucose":
        return "mg/dL"
      case "heart rate":
      case "heartrate":
        return "bpm"
      case "cholesterol":
        return "mg/dL"
      default:
        return ""
    }
  }

  // If we're using the component directly with data, render a simplified chart
  if (data && metricName) {
    // Format the data for the chart
    const chartData = data.map((item) => ({
      date: item.date,
      value: item.value,
    }))

    return (
      <div className={`w-full ${className}`}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{
              top: 5,
              right: 10,
              left: 10,
              bottom: 5,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis
              dataKey="date"
              tickFormatter={(date) => {
                if (!(date instanceof Date)) return ""
                return new Date(date).toLocaleDateString(undefined, { month: "short", day: "numeric" })
              }}
              tick={{ fontSize: 12 }}
            />
            <YAxis tick={{ fontSize: 12 }} width={30} />
            <Tooltip
              formatter={(value) => [`${value} ${getMetricUnit(metricName)}`, metricName]}
              labelFormatter={(label) => {
                if (!(label instanceof Date)) return ""
                return new Date(label).toLocaleDateString()
              }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={getMetricColor(metricName)}
              activeDot={{ r: 6 }}
              strokeWidth={2}
              dot={{ r: 3 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    )
  }

  // Original implementation for the standalone component
  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle>Health Metrics</CardTitle>
          <Select value={metricType} onValueChange={(value) => setMetricType(value)}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select metric" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="weight">Weight</SelectItem>
              <SelectItem value="bloodPressure">Blood Pressure</SelectItem>
              <SelectItem value="glucose">Glucose</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <CardDescription>Patient health metrics over time</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={sampleData}
              margin={{
                top: 5,
                right: 30,
                left: 20,
                bottom: 5,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis unit={getMetricUnit(metricType)} />
              <Tooltip formatter={(value) => [`${value} ${getMetricUnit(metricType)}`, metricType]} />
              <Legend />
              <Line
                type="monotone"
                dataKey={metricType}
                stroke={getMetricColor(metricType)}
                activeDot={{ r: 8 }}
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}

// Export as default as well to satisfy both import styles
export default HealthMetricsChart

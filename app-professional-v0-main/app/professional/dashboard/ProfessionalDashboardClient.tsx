"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { MessageSquare, AlertTriangle, Phone, MapPin, Video } from "lucide-react"
import { Input } from "@/components/ui/input"
import Link from "next/link"
import { useState } from "react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"

const patientInsights = [
  {
    id: 1,
    name: "Sarah Johnson",
    status: "alert",
    message: "Blood pressure readings trending upward over last 3 measurements.",
    action: "View Health Plan",
    patientId: "sarah-johnson",
  },
  {
    id: 2,
    name: "Emily Rodriguez",
    status: "urgent",
    message: "Missed medication for 3 consecutive days. Blood glucose levels rising.",
    action: "Contact Patient",
    patientId: "emily-rodriguez",
  },
  {
    id: 3,
    name: "Lisa Thompson",
    status: "progress",
    message: "Reported increased pain levels in daily logs.",
    action: "Review Progress",
    patientId: "lisa-thompson",
  },
]

const recentPatients = [
  {
    id: 1,
    name: "Sarah Johnson",
    lastVisit: "Apr 15, 2025",
    condition: "Hypertension",
    nextVisit: { date: "Today", time: "10:00 AM" },
  },
  {
    id: 2,
    name: "Michael Chen",
    lastVisit: "Apr 10, 2025",
    condition: "Annual Check-up",
    nextVisit: { date: "Today", time: "11:30 AM" },
  },
]

const getInsightBackground = (status: string) => {
  switch (status) {
    case "alert":
      return "bg-yellow-50 dark:bg-yellow-900/20"
    case "urgent":
      return "bg-red-50 dark:bg-red-900/20"
    case "progress":
      return "bg-green-50 dark:bg-green-900/20"
    default:
      return ""
  }
}

const getStatusBadge = (status: string) => {
  switch (status) {
    case "alert":
      return <span className="text-yellow-600 font-medium">Alert</span>
    case "urgent":
      return <span className="text-red-600 font-medium">Urgent</span>
    case "progress":
      return <span className="text-green-600 font-medium">Progress</span>
    default:
      return null
  }
}

// Data for different time periods
const performanceData = {
  week: [
    { day: "Mon", appointments: 5, income: 850 },
    { day: "Tue", appointments: 4, income: 700 },
    { day: "Wed", appointments: 6, income: 1050 },
    { day: "Thu", appointments: 3, income: 550 },
    { day: "Fri", appointments: 7, income: 1200 },
    { day: "Sat", appointments: 2, income: 500 },
    { day: "Sun", appointments: 1, income: 390 },
  ],
  month: [
    { day: "Week 1", appointments: 18, income: 3240 },
    { day: "Week 2", appointments: 22, income: 3950 },
    { day: "Week 3", appointments: 16, income: 2780 },
    { day: "Week 4", appointments: 25, income: 4500 },
  ],
  year: [
    { day: "Jan", appointments: 65, income: 11500 },
    { day: "Feb", appointments: 68, income: 12100 },
    { day: "Mar", appointments: 72, income: 13400 },
    { day: "Apr", appointments: 78, income: 14200 },
    { day: "May", appointments: 82, income: 15600 },
    { day: "Jun", appointments: 86, income: 17000 },
    { day: "Jul", appointments: 90, income: 18500 },
    { day: "Aug", appointments: 85, income: 17300 },
    { day: "Sep", appointments: 79, income: 16100 },
    { day: "Oct", appointments: 83, income: 16800 },
    { day: "Nov", appointments: 88, income: 17800 },
    { day: "Dec", appointments: 92, income: 19200 },
  ],
}

function ProfessionalDashboardClient() {
  const [selectedPeriod, setSelectedPeriod] = useState<"week" | "month" | "year">("week")

  // Calculate period totals
  const periodTotals = {
    week: {
      appointments: performanceData.week.reduce((sum, item) => sum + item.appointments, 0),
      income: performanceData.week.reduce((sum, item) => sum + item.income, 0),
    },
    month: {
      appointments: performanceData.month.reduce((sum, item) => sum + item.appointments, 0),
      income: performanceData.month.reduce((sum, item) => sum + item.income, 0),
    },
    year: {
      appointments: performanceData.year.reduce((sum, item) => sum + item.appointments, 0),
      income: performanceData.year.reduce((sum, item) => sum + item.income, 0),
    },
  }

  // Calculate percentage increases
  const percentageIncreases = {
    week: { appointments: "+12%", income: "+8%" },
    month: { appointments: "+15%", income: "+10%" },
    year: { appointments: "+7%", income: "+12%" },
  }

  return (
    <div className="container py-6">
      <header className="mb-6 flex flex-col space-y-3 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-teal-700 dark:text-teal-300">Welcome, Dr. Johnson</h1>
          <p className="text-muted-foreground">Your patient dashboard</p>
        </div>
        <div className="flex flex-wrap items-center gap-4">
          <div className="relative flex-1 sm:flex-none">
            <Input type="search" placeholder="Search patients..." className="w-full sm:w-[300px]" />
          </div>
          <div className="flex gap-2">
            <Button variant="ghost" size="icon">
              <AlertTriangle className="h-5 w-5" />
            </Button>
            <Button variant="ghost" size="icon">
              <MessageSquare className="h-5 w-5" />
            </Button>
            <Button className="bg-teal-600 hover:bg-teal-700">Schedule</Button>
          </div>
        </div>
      </header>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Today's Appointments */}
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle className="text-teal-700 dark:text-teal-300">Today's Appointments</CardTitle>
            <CardDescription>April 22, 2025</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Link key="1" href={`/professional/appointments/1`} className="block">
                <div className="rounded-lg border p-3 transition-colors hover:bg-gray-50 dark:hover:bg-gray-800">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                    <p className="font-medium text-base">Sarah Johnson</p>
                    <p className="text-gray-500">10:00 AM</p>
                  </div>
                  <p className="text-sm text-gray-500">Blood Pressure Follow-up</p>
                  <div className="mt-2 flex items-center">
                    <MapPin className="h-4 w-4 mr-1 text-teal-600" />
                    <span className="text-sm text-teal-600">In-person Consultation</span>
                  </div>
                </div>
              </Link>

              <Link key="2" href={`/professional/appointments/2`} className="block">
                <div className="rounded-lg border p-3 transition-colors hover:bg-gray-50 dark:hover:bg-gray-800">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                    <p className="font-medium text-base">Michael Chen</p>
                    <p className="text-gray-500">11:30 AM</p>
                  </div>
                  <p className="text-sm text-gray-500">Annual Physical</p>
                  <div className="mt-2 flex items-center">
                    <Video className="h-4 w-4 mr-1 text-teal-600" />
                    <span className="text-sm text-teal-600">Video Consultation</span>
                  </div>
                </div>
              </Link>

              <Link key="3" href={`/professional/appointments/3`} className="block">
                <div className="rounded-lg border p-3 transition-colors hover:bg-gray-50 dark:hover:bg-gray-800">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                    <p className="font-medium text-base">Emily Rodriguez</p>
                    <p className="text-gray-500">2:15 PM</p>
                  </div>
                  <p className="text-sm text-gray-500">Diabetes Management</p>
                  <div className="mt-2 flex items-center">
                    <Phone className="h-4 w-4 mr-1 text-teal-600" />
                    <span className="text-sm text-teal-600">Phone Consultation</span>
                  </div>
                </div>
              </Link>

              <Link key="4" href={`/professional/appointments/4`} className="block">
                <div className="rounded-lg border p-3 transition-colors hover:bg-gray-50 dark:hover:bg-gray-800">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                    <p className="font-medium text-base">David Garcia</p>
                    <p className="text-gray-500">4:00 PM</p>
                  </div>
                  <p className="text-sm text-gray-500">Cholesterol Check</p>
                  <div className="mt-2 flex items-center">
                    <MapPin className="h-4 w-4 mr-1 text-teal-600" />
                    <span className="text-sm text-teal-600">In-person Consultation</span>
                  </div>
                </div>
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Patient Insights */}
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle className="text-teal-700 dark:text-teal-300">Patient Insights</CardTitle>
            <CardDescription>AI-generated health alerts</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {patientInsights.map((patient) => (
                <div key={patient.id} className={`rounded-lg p-4 ${getInsightBackground(patient.status)}`}>
                  <div className="flex items-center justify-between mb-2">
                    <p className="font-medium">{patient.name}</p>
                    {getStatusBadge(patient.status)}
                  </div>
                  <p className="text-sm mb-2">{patient.message}</p>
                  <Link
                    href={`/professional/patients/${patient.patientId}`}
                    className="text-sm text-teal-600 hover:underline"
                  >
                    {patient.action}
                  </Link>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Patients */}
        <Card className="md:col-span-2 lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-teal-700 dark:text-teal-300">Recent Patients</CardTitle>
            <CardDescription>Patients you've seen recently</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {recentPatients.map((patient) => (
                <div key={patient.id} className="border-b pb-4 last:border-0 last:pb-0">
                  <p className="font-medium">{patient.name}</p>
                  <p className="text-sm text-muted-foreground">Last visit: {patient.lastVisit}</p>

                  <div className="grid grid-cols-2 gap-2 mt-2">
                    <div>
                      <p className="text-xs text-muted-foreground">Condition</p>
                      <p className="text-sm">{patient.condition}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Next Visit</p>
                      <p className="text-sm">
                        {patient.nextVisit.date}, {patient.nextVisit.time}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
              <Button variant="outline" className="w-full" asChild>
                <Link href="/professional/patients">View All Patients</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 mt-6 md:grid-cols-2">
        {/* Unread Messages Box */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle className="text-teal-700 dark:text-teal-300">Unread Messages</CardTitle>
              <CardDescription>Recent messages from patients</CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/professional/messages">View all</Link>
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Message 1 */}
              <div className="flex items-start gap-4 rounded-lg border p-3 hover:bg-gray-50 dark:hover:bg-gray-800">
                <div className="relative h-8 w-8 rounded-full bg-teal-100 flex items-center justify-center">
                  <span className="text-teal-700 font-medium text-sm">SJ</span>
                  <span className="absolute top-0 right-0 h-2.5 w-2.5 rounded-full bg-red-500 ring-2 ring-white" />
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between">
                    <p className="font-medium">Sarah Johnson</p>
                    <p className="text-xs text-muted-foreground">Today, 2:34 PM</p>
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-1">
                    I've been monitoring my blood pressure as instructed, but I'm still experiencing headaches...
                  </p>
                </div>
              </div>

              {/* Message 2 */}
              <div className="flex items-start gap-4 rounded-lg border p-3 hover:bg-gray-50 dark:hover:bg-gray-800">
                <div className="relative h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                  <span className="text-blue-700 font-medium text-sm">MC</span>
                  <span className="absolute top-0 right-0 h-2.5 w-2.5 rounded-full bg-red-500 ring-2 ring-white" />
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between">
                    <p className="font-medium">Michael Chen</p>
                    <p className="text-xs text-muted-foreground">Today, 11:05 AM</p>
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-1">
                    Just wanted to confirm our video appointment for tomorrow. Do I need to prepare anything?
                  </p>
                </div>
              </div>

              {/* Message 3 */}
              <div className="flex items-start gap-4 rounded-lg border p-3 hover:bg-gray-50 dark:hover:bg-gray-800">
                <div className="relative h-8 w-8 rounded-full bg-purple-100 flex items-center justify-center">
                  <span className="text-purple-700 font-medium text-sm">ER</span>
                  <span className="absolute top-0 right-0 h-2.5 w-2.5 rounded-full bg-red-500 ring-2 ring-white" />
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between">
                    <p className="font-medium">Emily Rodriguez</p>
                    <p className="text-xs text-muted-foreground">Yesterday, 4:17 PM</p>
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-1">
                    I forgot to take my medication yesterday. Should I double the dose today or just continue as normal?
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Statistics Box */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle className="text-teal-700 dark:text-teal-300">Performance Overview</CardTitle>
              <CardDescription>Appointments and revenue statistics</CardDescription>
            </div>
            <Select
              defaultValue="week"
              onValueChange={(value) => setSelectedPeriod(value as "week" | "month" | "year")}
            >
              <SelectTrigger className="w-[120px] h-8">
                <SelectValue placeholder="Period" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="week">This Week</SelectItem>
                <SelectItem value="month">This Month</SelectItem>
                <SelectItem value="year">This Year</SelectItem>
              </SelectContent>
            </Select>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Appointments</p>
                <div className="flex items-baseline gap-2">
                  <p className="text-2xl font-bold">{periodTotals[selectedPeriod].appointments}</p>
                  <p className="text-xs text-green-600">{percentageIncreases[selectedPeriod].appointments}</p>
                </div>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Gross Income</p>
                <div className="flex items-baseline gap-2">
                  <p className="text-2xl font-bold">${periodTotals[selectedPeriod].income.toLocaleString()}</p>
                  <p className="text-xs text-green-600">{percentageIncreases[selectedPeriod].income}</p>
                </div>
              </div>
            </div>

            <div className="h-[180px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={performanceData[selectedPeriod]} margin={{ top: 5, right: 5, left: 5, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="day" tick={{ fontSize: 12 }} />
                  <YAxis
                    yAxisId="left"
                    orientation="left"
                    tick={{ fontSize: 12 }}
                    label={{
                      value: "# Appointments",
                      angle: -90,
                      position: "insideLeft",
                      style: { textAnchor: "middle", fontSize: "10px" },
                    }}
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    tick={{ fontSize: 12 }}
                    label={{
                      value: "Gross Income ($)",
                      angle: 90,
                      position: "insideRight",
                      style: { textAnchor: "middle", fontSize: "10px" },
                    }}
                  />
                  <Tooltip
                    formatter={(value, name) => [
                      name === "appointments" ? value : `$${value}`,
                      name === "appointments" ? "Appointments" : "Revenue",
                    ]}
                  />
                  <Legend />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="appointments"
                    name="Appointments"
                    stroke="#14b8a6"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="income"
                    name="Revenue"
                    stroke="#60a5fa"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default ProfessionalDashboardClient

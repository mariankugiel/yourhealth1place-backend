"use client"

import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { AlertTriangle, User, Video, Phone, MapPin, MessageSquare, Bell, BarChart2 } from "lucide-react"
import { Input } from "@/components/ui/input"
import { useLanguage } from "@/lib/language-context"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useState } from "react"

export default function ProfessionalDashboardClient() {
  const { t } = useLanguage()
  // Sample data for today's appointments with consultation type added
  const todaysAppointments = [
    {
      id: "1",
      patientId: "sarah-johnson",
      patientName: "Sarah Johnson",
      time: "10:00 AM",
      type: "Blood Pressure Follow-up",
      status: "Confirmed",
      consultationType: "physical",
      duration: "30 minutes",
    },
    {
      id: "2",
      patientId: "michael-chen",
      patientName: "Michael Chen",
      time: "11:30 AM",
      type: "Annual Physical",
      status: "Confirmed",
      consultationType: "video",
      duration: "45 minutes",
    },
    {
      id: "3",
      patientId: "emily-rodriguez",
      patientName: "Emily Rodriguez",
      time: "2:15 PM",
      type: "Diabetes Management",
      status: "Confirmed",
      consultationType: "phone",
      duration: "30 minutes",
    },
    // Add a new appointment for today
    {
      id: "4",
      patientId: "david-garcia",
      patientName: "David Garcia",
      time: "4:00 PM",
      type: "Cholesterol Check",
      status: "Confirmed",
      consultationType: "physical",
      duration: "30 minutes",
    },
  ]

  // Sample data for patient insights - updated as requested
  const patientInsights = [
    {
      id: "1",
      patientId: "sarah-johnson",
      name: "Sarah Johnson",
      status: "alert",
      message:
        t("dashboard.bloodPressureAlert") || "Blood pressure readings consistently above target for the past week.",
      action: t("dashboard.viewHealthPlan") || "View Health Plan",
    },
    {
      id: "2",
      patientId: "emily-rodriguez",
      name: "Emily Rodriguez",
      status: "urgent", // Changed to urgent as requested
      message:
        t("dashboard.missedMedicationAlert") ||
        "Missed medication for 3 consecutive days. Blood glucose levels rising.",
      action: t("dashboard.contactPatient") || "Contact Patient",
    },
    {
      id: "3",
      patientId: "lisa-thompson",
      name: "Lisa Thompson",
      status: "alert",
      message: t("dashboard.painLevelsAlert") || "Reported increased pain levels in daily logs.",
      action: t("dashboard.reviewProgress") || "Review Progress",
    },
  ]

  // Recent patients data
  const recentPatients = [
    {
      id: "sarah-johnson",
      name: "Sarah Johnson",
      lastVisit: "Apr 15, 2023",
      condition: t("conditions.hypertension") || "Hypertension",
      nextVisit: {
        date: t("dashboard.today") || "Today",
        time: "10:00 AM",
      },
    },
    {
      id: "michael-chen",
      name: "Michael Chen",
      lastVisit: "Apr 10, 2023",
      condition: t("conditions.annualCheckup") || "Annual Check-up",
      nextVisit: {
        date: t("dashboard.today") || "Today",
        time: "11:30 AM",
      },
    },
    {
      id: "emily-rodriguez",
      name: "Emily Rodriguez",
      lastVisit: "Apr 5, 2023",
      condition: t("conditions.diabetes") || "Diabetes",
      nextVisit: {
        date: "May 17, 2025",
        time: "2:00 PM",
      },
    },
    {
      id: "david-garcia",
      name: "David Garcia",
      lastVisit: "Mar 20, 2023",
      condition: t("conditions.highCholesterol") || "High Cholesterol",
      nextVisit: {
        date: "June 25, 2025",
        time: "2:30 PM",
      },
    },
  ]

  // Sample data for patient statistics chart
  const patientStatisticsData = {
    weekly: [
      { day: "Mon", patients: 5, amount: 750 },
      { day: "Tue", patients: 8, amount: 1200 },
      { day: "Wed", patients: 6, amount: 900 },
      { day: "Thu", patients: 9, amount: 1350 },
      { day: "Fri", patients: 12, amount: 1800 },
      { day: "Sat", patients: 4, amount: 600 },
      { day: "Sun", patients: 2, amount: 300 },
    ],
    monthly: [
      { month: "Jan", patients: 45, amount: 6750 },
      { month: "Feb", patients: 52, amount: 7800 },
      { month: "Mar", patients: 48, amount: 7200 },
      { month: "Apr", patients: 60, amount: 9000 },
      { month: "May", patients: 55, amount: 8250 },
      { month: "Jun", patients: 70, amount: 10500 },
    ],
    yearly: [
      { year: "2020", patients: 420, amount: 63000 },
      { year: "2021", patients: 480, amount: 72000 },
      { year: "2022", patients: 520, amount: 78000 },
      { year: "2023", patients: 580, amount: 87000 },
      { year: "2024", patients: 650, amount: 97500 },
      { year: "2025", patients: 330, amount: 49500 }, // Year to date
    ],
  }

  const [patientStatsPeriod, setPatientStatsPeriod] = useState("weekly")

  // Helper function to get consultation type icon
  const getConsultationTypeIcon = (type: string) => {
    switch (type) {
      case "video":
        return <Video className="h-5 w-5 text-blue-600" />
      case "phone":
        return <Phone className="h-5 w-5 text-purple-600" />
      case "physical":
        return <MapPin className="h-5 w-5 text-green-600" />
      default:
        return <User className="h-5 w-5" />
    }
  }

  // Helper function to get status badge for patient insights
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "alert":
        return <span className="text-yellow-600 font-medium">{t("status.alert") || "Alert"}</span>
      case "urgent":
        return <span className="text-red-600 font-medium">{t("status.urgent") || "Urgent"}</span>
      case "progress":
        return <span className="text-green-600 font-medium">{t("status.progress") || "Progress"}</span>
      default:
        return <span className="text-gray-600 font-medium">{t("status.normal") || "Normal"}</span>
    }
  }

  // Helper function to get background color for patient insights
  const getInsightBackground = (status: string) => {
    switch (status) {
      case "alert":
        return "bg-yellow-50"
      case "urgent":
        return "bg-red-50"
      case "progress":
        return "bg-green-50"
      default:
        return "bg-gray-50"
    }
  }

  // Helper function to translate consultation types
  const getConsultationType = (type: string) => {
    switch (type) {
      case "video":
        return t("consultationTypes.video") || "Video Consultation"
      case "phone":
        return t("consultationTypes.phone") || "Phone Consultation"
      case "physical":
        return t("consultationTypes.physical") || "In-person Consultation"
      default:
        return t("consultationTypes.other") || "Consultation"
    }
  }

  return (
    <div className="container py-6">
      <header className="mb-6 flex flex-col space-y-4 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-teal-700 dark:text-teal-300">
            {t("dashboard.welcome")} {t("dashboard.doctorTitle", "Dr.")} Johnson
          </h1>
          <p className="text-muted-foreground">{t("dashboard.subtitle")}</p>
        </div>
        <div className="flex flex-wrap items-center gap-4">
          <div className="relative flex-1 sm:flex-none">
            <Input type="search" placeholder={t("dashboard.searchPatients")} className="w-full sm:w-[300px]" />
          </div>
          <div className="flex gap-2">
            <Button variant="ghost" size="icon">
              <AlertTriangle className="h-5 w-5" />
            </Button>
            <Button variant="ghost" size="icon">
              <MessageSquare className="h-5 w-5" />
            </Button>
            <Button className="bg-teal-600 hover:bg-teal-700">{t("dashboard.schedule")}</Button>
          </div>
        </div>
      </header>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Today's Appointments */}
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle className="text-teal-700 dark:text-teal-300">{t("dashboard.todaysAppointments")}</CardTitle>
            <CardDescription>April 22, 2025</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {todaysAppointments.map((appointment) => (
                <Link key={appointment.id} href={`/professional/appointments/${appointment.id}`} className="block">
                  <div className="rounded-lg border p-3 transition-colors hover:bg-gray-50 dark:hover:bg-gray-800">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                      <p className="font-medium text-base">{appointment.patientName}</p>
                      <p className="text-gray-500">{appointment.time}</p>
                    </div>
                    <p className="text-sm text-gray-500">{appointment.type}</p>
                    <div className="mt-2 flex items-center">
                      {appointment.consultationType === "video" ? (
                        <Video className="h-4 w-4 mr-1 text-teal-600" />
                      ) : appointment.consultationType === "phone" ? (
                        <Phone className="h-4 w-4 mr-1 text-teal-600" />
                      ) : (
                        <MapPin className="h-4 w-4 mr-1 text-teal-600" />
                      )}
                      <span className="text-sm text-teal-600">{getConsultationType(appointment.consultationType)}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Patient Insights */}
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle className="text-teal-700 dark:text-teal-300">{t("dashboard.patientInsights")}</CardTitle>
            <CardDescription>{t("dashboard.aiGeneratedAlerts")}</CardDescription>
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
            <CardTitle className="text-teal-700 dark:text-teal-300">{t("dashboard.recentPatients")}</CardTitle>
            <CardDescription>{t("dashboard.patientsSeenRecently")}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {recentPatients.map((patient) => (
                <div key={patient.id} className="border-b pb-4 last:border-0 last:pb-0">
                  <p className="font-medium">{patient.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {t("dashboard.lastVisit") || "Last visit"}: {patient.lastVisit}
                  </p>

                  <div className="grid grid-cols-2 gap-2 mt-2">
                    <div>
                      <p className="text-xs text-muted-foreground">{t("dashboard.condition") || "Condition"}</p>
                      <p className="text-sm">{patient.condition}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">{t("dashboard.nextVisit") || "Next Visit"}</p>
                      <p className="text-sm">
                        {patient.nextVisit.date}, {patient.nextVisit.time}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
              <Button variant="outline" className="w-full" asChild>
                <Link href="/professional/patients">{t("dashboard.viewAllPatients")}</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Add the new row of boxes */}
      <div className="grid gap-6 md:grid-cols-3 mt-6">
        {/* Notifications Box */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-teal-700 dark:text-teal-300">
              {t("dashboard.notifications") || "Notifications"}
            </CardTitle>
            <Bell className="h-5 w-5 text-teal-600" />
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {patientInsights.slice(0, 2).map((insight) => (
                <div key={insight.id} className={`rounded-lg p-3 ${getInsightBackground(insight.status)}`}>
                  <div className="flex items-center justify-between mb-1">
                    <p className="font-medium text-sm">{insight.name}</p>
                    {getStatusBadge(insight.status)}
                  </div>
                  <p className="text-xs mb-1">{insight.message}</p>
                </div>
              ))}
              <Button variant="ghost" size="sm" className="w-full text-teal-600">
                {t("dashboard.viewAll") || "View all"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Messages Box */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-teal-700 dark:text-teal-300">
              {t("dashboard.recentMessages") || "Recent Messages"}
            </CardTitle>
            <MessageSquare className="h-5 w-5 text-teal-600" />
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="rounded-lg border p-3">
                <div className="flex items-center justify-between mb-1">
                  <p className="font-medium text-sm">Sarah Johnson</p>
                  <p className="text-xs text-gray-500">10:30 AM</p>
                </div>
                <p className="text-xs text-gray-600">
                  {t("dashboard.messagePreview1") || "Thank you for the prescription. When should I..."}
                </p>
              </div>
              <div className="rounded-lg border p-3">
                <div className="flex items-center justify-between mb-1">
                  <p className="font-medium text-sm">Michael Chen</p>
                  <p className="text-xs text-gray-500">Yesterday</p>
                </div>
                <p className="text-xs text-gray-600">
                  {t("dashboard.messagePreview2") || "My blood pressure readings have been stable..."}
                </p>
              </div>
              <Button variant="ghost" size="sm" className="w-full text-teal-600" asChild>
                <Link href="/professional/messages">{t("dashboard.viewAllMessages") || "View all messages"}</Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Patient Statistics Chart */}
        <Card className="md:col-span-1">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-teal-700 dark:text-teal-300">
              {t("dashboard.patientStatistics") || "Patient Statistics"}
            </CardTitle>
            <div className="flex items-center">
              <BarChart2 className="h-5 w-5 text-teal-600 mr-2" />
              <Select value={patientStatsPeriod} onValueChange={setPatientStatsPeriod}>
                <SelectTrigger className="h-8 w-[100px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="weekly">{t("statistics.timePeriods.weekly") || "Weekly"}</SelectItem>
                  <SelectItem value="monthly">{t("statistics.timePeriods.monthly") || "Monthly"}</SelectItem>
                  <SelectItem value="yearly">{t("statistics.timePeriods.yearly") || "Yearly"}</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={patientStatisticsData[patientStatsPeriod as keyof typeof patientStatisticsData]}
                  margin={{ top: 10, right: 10, left: 0, bottom: 20 }}
                >
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey={
                      patientStatsPeriod === "weekly" ? "day" : patientStatsPeriod === "monthly" ? "month" : "year"
                    }
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis yAxisId="left" orientation="left" tick={{ fontSize: 12 }} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar
                    yAxisId="left"
                    dataKey="patients"
                    name={t("dashboard.patients") || "Patients"}
                    fill="#14b8a6"
                    radius={[4, 4, 0, 0]}
                  />
                  <Bar
                    yAxisId="right"
                    dataKey="amount"
                    name={t("dashboard.revenue") || "Revenue ($)"}
                    fill="#60a5fa"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import {
  AlertCircle,
  Calendar,
  Clock,
  FileText,
  Heart,
  MessageSquare,
  Plus,
  Search,
  AlertTriangle,
  TrendingUp,
  Activity,
  CheckCircle,
} from "lucide-react"
import Link from "next/link"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useLanguage } from "@/lib/language-context"

// Sample patient data
const patients = [
  {
    id: "sarah-johnson",
    name: "Sarah Johnson",
    age: 42,
    gender: "Female",
    condition: "Hypertension",
    lastVisit: "Apr 15, 2025",
    nextVisit: "Apr 22, 2025",
    status: "Active",
    contactInfo: {
      email: "sarah.johnson@example.com",
      phone: "(555) 123-4567",
    },
    patientStatus: "alert",
    insights: [
      {
        type: "alert",
        message: "Blood pressure readings trending upward over last 3 measurements",
      },
    ],
  },
  {
    id: "michael-chen",
    name: "Michael Chen",
    age: 35,
    gender: "Male",
    condition: "Annual Check-up",
    lastVisit: "Apr 10, 2025",
    nextVisit: "Apr 22, 2025",
    status: "Active",
    contactInfo: {
      email: "michael.chen@example.com",
      phone: "(555) 234-5678",
    },
    patientStatus: "normal",
    insights: [
      {
        type: "normal",
        message: "All health metrics within normal ranges",
      },
    ],
  },
  {
    id: "emily-rodriguez",
    name: "Emily Rodriguez",
    age: 58,
    gender: "Female",
    condition: "Diabetes Type 2",
    lastVisit: "Apr 5, 2025",
    nextVisit: "Apr 22, 2025",
    status: "Active",
    contactInfo: {
      email: "emily.rodriguez@example.com",
      phone: "(555) 345-6789",
    },
    patientStatus: "urgent",
    insights: [
      {
        type: "urgent",
        message: "Missed last two medication refills",
      },
      {
        type: "alert",
        message: "HbA1c levels increased by 0.8% since last visit",
      },
    ],
  },
  {
    id: "robert-williams",
    name: "Robert Williams",
    age: 62,
    gender: "Male",
    condition: "Arthritis",
    lastVisit: "Apr 3, 2025",
    nextVisit: "Apr 23, 2025",
    status: "Active",
    contactInfo: {
      email: "robert.williams@example.com",
      phone: "(555) 456-7890",
    },
    patientStatus: "progress",
    insights: [
      {
        type: "progress",
        message: "Pain scores improving with new treatment regimen",
      },
    ],
  },
  {
    id: "lisa-thompson",
    name: "Lisa Thompson",
    age: 45,
    gender: "Female",
    condition: "Chronic Pain",
    lastVisit: "Mar 28, 2025",
    nextVisit: "Apr 23, 2025",
    status: "Active",
    contactInfo: {
      email: "lisa.thompson@example.com",
      phone: "(555) 567-8901",
    },
    patientStatus: "alert",
    insights: [
      {
        type: "alert",
        message: "Reported increased pain levels in daily logs",
      },
    ],
  },
  {
    id: "david-garcia",
    name: "David Garcia",
    age: 50,
    gender: "Male",
    condition: "High Cholesterol",
    lastVisit: "Mar 20, 2025",
    nextVisit: "May 5, 2025",
    status: "Active",
    contactInfo: {
      email: "david.garcia@example.com",
      phone: "(555) 678-9012",
    },
    patientStatus: "progress",
    insights: [
      {
        type: "progress",
        message: "Cholesterol levels trending downward with current treatment",
      },
    ],
  },
]

// Helper function to get the appropriate icon for patient insights
const getInsightIcon = (type: string) => {
  switch (type) {
    case "alert":
      return <AlertTriangle className="h-4 w-4" />
    case "urgent":
      return <AlertCircle className="h-4 w-4" />
    case "progress":
      return <TrendingUp className="h-4 w-4" />
    case "normal":
      return <CheckCircle className="h-4 w-4" />
    default:
      return <Activity className="h-4 w-4" />
  }
}

// Helper function to get the appropriate background color based on patient status
const getCardBackgroundClass = (status: string) => {
  switch (status) {
    case "alert":
      return "bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800"
    case "urgent":
      return "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800"
    case "progress":
      return "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800"
    default:
      return ""
  }
}

export default function PatientsPage() {
  const { t } = useLanguage()
  const [searchTerm, setSearchTerm] = useState("")
  const [activeTab, setActiveTab] = useState("all")
  const [patientStatuses, setPatientStatuses] = useState<{ [key: string]: string }>(
    patients.reduce((acc, patient) => ({ ...acc, [patient.id]: patient.patientStatus }), {}),
  )

  const handleStatusChange = (patientId: string, newStatus: string) => {
    setPatientStatuses((prev) => ({
      ...prev,
      [patientId]: newStatus,
    }))
  }

  const filteredPatients = patients.filter((patient) => {
    const matchesSearch = patient.name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesTab = activeTab === "all" || patient.status.toLowerCase() === activeTab.toLowerCase()
    return matchesSearch && matchesTab
  })

  // Helper function to get status badge for patient insights
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "alert":
        return (
          <Badge className="bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800 text-yellow-600 dark:text-yellow-400">
            {t("status.alert") || "Alert"}
          </Badge>
        )
      case "urgent":
        return (
          <Badge className="bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-600 dark:text-red-400">
            {t("status.urgent") || "Urgent"}
          </Badge>
        )
      case "progress":
        return (
          <Badge className="bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-600 dark:text-green-400">
            {t("status.progress") || "Progress"}
          </Badge>
        )
      case "normal":
        return <Badge variant="outline">{t("status.normal") || "Normal"}</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  return (
    <div className="container py-6">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-teal-700 dark:text-teal-300">{t("patients.title")}</h1>
          <p className="text-muted-foreground">{t("patients.subtitle")}</p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          {t("patients.addNewPatient")}
        </Button>
      </div>

      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder={t("patients.searchPatients")}
            className="pl-8"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <Tabs defaultValue="all" className="w-full sm:w-auto" value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="all">{t("patients.tabs.all") || "All"}</TabsTrigger>
            <TabsTrigger value="active">{t("patients.tabs.active") || "Active"}</TabsTrigger>
            <TabsTrigger value="inactive">{t("patients.tabs.inactive") || "Inactive"}</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredPatients.map((patient) => {
          const currentStatus = patientStatuses[patient.id]
          const cardBackgroundClass = getCardBackgroundClass(currentStatus)

          return (
            <Card key={patient.id} className={`h-full transition-all hover:shadow-md ${cardBackgroundClass}`}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle>{patient.name}</CardTitle>
                    <CardDescription>
                      {patient.age} {t("patients.years") || "years"} • {patient.gender}
                    </CardDescription>
                  </div>
                  <Badge className="bg-teal-600 dark:bg-teal-600">{patient.status}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid gap-2">
                  <div className="flex items-center gap-2">
                    <Heart className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{patient.condition}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">
                      {t("patients.lastVisit") || "Last visit"}: {patient.lastVisit}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">
                      {t("patients.nextVisit") || "Next visit"}: {patient.nextVisit}
                    </span>
                  </div>

                  {/* Patient Status */}
                  <div className="mt-2 flex items-center justify-between">
                    <span className="text-sm font-medium">{t("patients.patientStatus") || "Patient Status"}:</span>
                    <Select value={currentStatus} onValueChange={(value) => handleStatusChange(patient.id, value)}>
                      <SelectTrigger className="w-[130px] h-8">
                        <SelectValue placeholder={t("patients.selectStatus") || "Select status"} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="normal">{t("status.normal") || "Normal"}</SelectItem>
                        <SelectItem value="progress">{t("status.progress") || "Progress"}</SelectItem>
                        <SelectItem value="alert">{t("status.alert") || "Alert"}</SelectItem>
                        <SelectItem value="urgent">{t("status.urgent") || "Urgent"}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Patient Insights */}
                  {patient.insights && patient.insights.length > 0 && (
                    <div className="mt-2 space-y-2">
                      {patient.insights.map((insight, index) => (
                        <div key={index} className="flex items-start gap-2 rounded-md p-2 text-sm border">
                          {getInsightIcon(insight.type)}
                          <span>{insight.message}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
              <CardFooter className="flex justify-between">
                <Button variant="outline" size="sm" className="w-full" asChild>
                  <Link href={`/professional/patients/${patient.id}`}>
                    <FileText className="mr-2 h-4 w-4" />
                    {t("patients.viewRecords") || "View Records"}
                  </Link>
                </Button>
                <Button variant="outline" size="sm" className="w-full ml-2" asChild>
                  <Link href={`/professional/messages?patient=${patient.id}`}>
                    <MessageSquare className="mr-2 h-4 w-4" />
                    {t("patients.message") || "Message"}
                  </Link>
                </Button>
              </CardFooter>
            </Card>
          )
        })}
      </div>
    </div>
  )
}

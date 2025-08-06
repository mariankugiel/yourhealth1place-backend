"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Calendar, Check, FileText, Lightbulb, LineChart, ListTodo, Pill, Plus, Video, X } from "lucide-react"
import { useLanguage } from "@/lib/language-context"
import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"

// Sample appointment data
const appointments = [
  {
    id: "1",
    title: "Blood Pressure Follow-up",
    patient: {
      id: "sarah-johnson",
      name: "Sarah Johnson",
      age: 42,
      gender: "Female",
      avatar: "/stylized-initials.png",
      contact: {
        email: "sarah.johnson@example.com",
        phone: "(555) 123-4567",
        address: "123 Main St, Anytown, CA 94321",
      },
      insurance: {
        provider: "Blue Cross Blue Shield",
        policyNumber: "BCBS-12345678",
        group: "GRP-987654",
      },
      permissions: {
        medicalHistory: "full",
        medications: "full",
        labResults: "limited",
        billingInfo: "full",
        contactInfo: "full",
        appointmentNotes: "denied",
      },
      healthMetrics: [
        {
          id: "blood-pressure",
          name: "Blood Pressure",
          current: "138/88",
          target: "120/80",
          unit: "mmHg",
          history: [
            { date: "2025-04-15", value: 138 },
            { date: "2025-04-08", value: 142 },
            { date: "2025-04-01", value: 145 },
            { date: "2025-03-25", value: 148 },
            { date: "2025-03-18", value: 150 },
            { date: "2025-03-11", value: 152 },
          ],
        },
        {
          id: "weight",
          name: "Weight",
          current: "165",
          target: "150",
          unit: "lbs",
          history: [
            { date: "2025-04-15", value: 165 },
            { date: "2025-04-01", value: 167 },
            { date: "2025-03-15", value: 169 },
            { date: "2025-03-01", value: 172 },
            { date: "2025-02-15", value: 174 },
            { date: "2025-02-01", value: 175 },
          ],
        },
        {
          id: "heart-rate",
          name: "Heart Rate",
          current: "72",
          target: "60-80",
          unit: "bpm",
          history: [
            { date: "2025-04-15", value: 72 },
            { date: "2025-04-08", value: 75 },
            { date: "2025-04-01", value: 78 },
            { date: "2025-03-25", value: 74 },
            { date: "2025-03-18", value: 76 },
            { date: "2025-03-11", value: 73 },
          ],
        },
      ],
      clinicalNotes: [
        {
          id: "note1",
          date: "2025-03-15",
          provider: "Dr. Johnson",
          title: "Hypertension Follow-up",
          content:
            "Patient reports compliance with medication. Blood pressure still elevated but showing improvement. Discussed dietary changes and increased physical activity.",
        },
        {
          id: "note2",
          date: "2025-01-10",
          provider: "Dr. Johnson",
          title: "Annual Physical",
          content:
            "Patient in good health overall. Blood pressure elevated at 145/95. Recommended lifestyle changes and monitoring. Will follow up in 2 months.",
        },
      ],
      conditions: ["Hypertension", "Hyperlipidemia"],
      allergies: ["Penicillin"],
      summary: {
        preConditions:
          "Patient has Stage 1 hypertension diagnosed in January 2025 and hyperlipidemia. Currently on medication management with lifestyle modifications.",
        recentProgress:
          "Blood pressure has shown gradual improvement over the past 3 months, decreasing from 152/95 to 138/88. Weight has decreased by 10 pounds since starting treatment.",
        treatmentPlan:
          "Continue current medication regimen with focus on dietary sodium restriction and regular exercise. Monitor blood pressure daily and track in app.",
        nextSteps:
          "If blood pressure continues to improve, consider maintaining current medication dosage. If target not reached within 1 month, may need to adjust medication or add second agent.",
      },
    },
    date: "April 22, 2025",
    time: "10:00 AM",
    duration: "30 minutes",
    type: "Follow-up",
    status: "Scheduled",
    videoLink: "https://meet.example.com/dr-johnson-123",
    medicalHistory: [
      {
        date: "Mar 15, 2025",
        condition: "Hypertension",
        notes: "Patient diagnosed with Stage 1 hypertension. Started on lisinopril 10mg daily.",
      },
      {
        date: "Jan 10, 2025",
        condition: "Annual Physical",
        notes: "Blood pressure elevated at 145/95. Recommended lifestyle changes and monitoring.",
      },
    ],
    medications: [
      {
        name: "Lisinopril",
        dosage: "10mg",
        frequency: "Once daily",
        startDate: "Mar 15, 2025",
      },
      {
        name: "Hydrochlorothiazide",
        dosage: "12.5mg",
        frequency: "Once daily",
        startDate: "Mar 15, 2025",
      },
    ],
    healthRecords: [
      {
        date: "Apr 15, 2025",
        type: "Blood Pressure",
        value: "138/88",
      },
      {
        date: "Apr 8, 2025",
        type: "Blood Pressure",
        value: "142/90",
      },
      {
        date: "Apr 1, 2025",
        type: "Blood Pressure",
        value: "145/92",
      },
    ],
    healthPlans: [
      {
        title: "Blood Pressure Management",
        target: "Reduce to below 130/80",
        progress: "Moderate",
        recommendations: [
          "Continue medication as prescribed",
          "Reduce sodium intake",
          "30 minutes of exercise 5 days per week",
          "Monitor blood pressure daily",
        ],
      },
    ],
    aiSuggestions: [
      "Blood pressure readings show slight improvement but still above target",
      "Consider discussing sodium intake and dietary habits",
      "Patient may benefit from home blood pressure monitoring education",
      "Review medication adherence and possible side effects",
    ],
    documents: [
      {
        id: "doc1",
        type: "Prescription",
        title: "Lisinopril Renewal",
        date: "Apr 22, 2025",
        status: "Draft",
      },
      {
        id: "doc2",
        type: "Lab Order",
        title: "Comprehensive Metabolic Panel",
        date: "Apr 22, 2025",
        status: "Draft",
      },
    ],
  },
  {
    id: "2",
    title: "Annual Physical",
    patient: {
      id: "michael-chen",
      name: "Michael Chen",
      age: 35,
      gender: "Male",
      avatar: "/microphone-crowd.png",
      contact: {
        email: "michael.chen@example.com",
        phone: "(555) 987-6543",
        address: "456 Oak Ave, Somewhere, NY 10001",
      },
      insurance: {
        provider: "Aetna",
        policyNumber: "AET-87654321",
        group: "GRP-123456",
      },
      permissions: {
        medicalHistory: "full",
        medications: "full",
        labResults: "full",
        billingInfo: "limited",
        contactInfo: "full",
        appointmentNotes: "full",
      },
      healthMetrics: [
        {
          id: "blood-pressure",
          name: "Blood Pressure",
          current: "120/80",
          target: "120/80",
          unit: "mmHg",
          history: [
            { date: "2025-04-10", value: 120 },
            { date: "2024-04-10", value: 122 },
            { date: "2023-04-10", value: 124 },
            { date: "2022-04-10", value: 126 },
            { date: "2021-04-10", value: 128 },
          ],
        },
        {
          id: "cholesterol",
          name: "Total Cholesterol",
          current: "180",
          target: "<200",
          unit: "mg/dL",
          history: [
            { date: "2025-04-10", value: 180 },
            { date: "2024-04-10", value: 185 },
            { date: "2023-04-10", value: 190 },
            { date: "2022-04-10", value: 195 },
            { date: "2021-04-10", value: 200 },
          ],
        },
      ],
      clinicalNotes: [
        {
          id: "note1",
          date: "2024-04-10",
          provider: "Dr. Johnson",
          title: "Annual Physical",
          content:
            "Patient in excellent health. All vitals normal. Recommended continued regular exercise and healthy diet.",
        },
      ],
      conditions: ["None"],
      allergies: ["None"],
      summary: {
        preConditions:
          "Patient has no significant medical conditions. Annual physicals have consistently shown excellent health.",
        recentProgress:
          "Patient maintains a healthy lifestyle with regular exercise and balanced diet. All health metrics are within normal ranges.",
        treatmentPlan: "Continue preventive care with annual check-ups. Maintain current lifestyle habits.",
        nextSteps:
          "Schedule next annual physical in one year. Consider adding cardiovascular fitness assessment at next visit.",
      },
    },
    date: "April 22, 2025",
    time: "11:30 AM",
    duration: "45 minutes",
    type: "Annual Physical",
    status: "Scheduled",
    videoLink: "https://meet.example.com/dr-johnson-456",
    medicalHistory: [
      {
        date: "Apr 10, 2024",
        condition: "Annual Physical",
        notes: "All vitals normal. Recommended regular exercise and healthy diet.",
      },
    ],
    medications: [],
    healthRecords: [
      {
        date: "Apr 10, 2024",
        type: "Blood Pressure",
        value: "120/80",
      },
      {
        date: "Apr 10, 2024",
        type: "Cholesterol",
        value: "Total: 180, LDL: 100, HDL: 60",
      },
    ],
    healthPlans: [
      {
        title: "Preventive Health",
        target: "Maintain healthy lifestyle",
        progress: "Good",
        recommendations: [
          "Regular exercise 3-5 times per week",
          "Balanced diet with plenty of fruits and vegetables",
          "Annual check-ups",
        ],
      },
    ],
    aiSuggestions: [
      "Consider discussing stress management techniques",
      "Review family history for potential screening recommendations",
      "Discuss recommended vaccinations based on age and risk factors",
    ],
    documents: [],
  },
]

export function AppointmentDetailsPage({ appointmentId }: { appointmentId: string }) {
  const appointment = appointments.find((apt) => apt.id === appointmentId) || appointments[0]
  const [notes, setNotes] = useState("")
  const [activeDocumentType, setActiveDocumentType] = useState("Prescription")
  const [documentTitle, setDocumentTitle] = useState("")
  const [documentContent, setDocumentContent] = useState("")
  const [activeTab, setActiveTab] = useState("notes")
  const [activeSuggestions, setActiveSuggestions] = useState<string[]>(appointment.aiSuggestions)
  const { t } = useLanguage()

  const renderPermissionIcon = (status: string) => {
    switch (status) {
      case "full":
        return <Check className="h-4 w-4 text-green-600" title="Full Access" />
      case "limited":
        return <Check className="h-4 w-4 text-yellow-600" title="Limited Access" />
      case "denied":
        return <X className="h-4 w-4 text-red-600" title="No Access" />
      default:
        return (
          <span className="h-4 w-4 text-gray-400" title="Unknown">
            -
          </span>
        )
    }
  }

  const addSuggestionToNotes = (suggestion: string) => {
    setNotes((prevNotes) => {
      const prefix = prevNotes.length > 0 ? prevNotes + "\n\n" : ""
      return prefix + suggestion
    })
  }

  const removeSuggestion = (suggestionToRemove: string) => {
    setActiveSuggestions((prevSuggestions) => prevSuggestions.filter((suggestion) => suggestion !== suggestionToRemove))
  }

  const renderMetricChart = (metric: any) => {
    const data = metric.history.map((item: any) => {
      const date = new Date(item.date)
      return {
        name: `${date.getMonth() + 1}/${date.getDate()}`,
        value: item.value,
      }
    })

    const getColor = () => {
      switch (metric.id) {
        case "blood-pressure":
          return "#ef4444"
        case "weight":
          return "#4f46e5"
        case "heart-rate":
          return "#f59e0b"
        default:
          return "#10b981"
      }
    }

    return (
      <div className="h-[150px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <RechartsLineChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} width={30} />
            <Tooltip
              formatter={(value) => [`${value} ${metric.unit}`, metric.name]}
              labelFormatter={(label) => `Date: ${label}`}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={getColor()}
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 6 }}
            />
          </RechartsLineChart>
        </ResponsiveContainer>
      </div>
    )
  }

  return (
    <div className="container py-6 space-y-6">
      <div className="mb-6 flex flex-col space-y-3 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-teal-700 dark:text-teal-300">
            {t("appointments.details")}
          </h1>
          <p className="text-muted-foreground">
            {appointment.title} {t("appointments.with")} {appointment.patient.name} • {appointment.date}{" "}
            {t("appointments.at")} {appointment.time}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="sm:size-md">
            <Calendar className="mr-2 h-4 w-4" />
            <span className="hidden sm:inline">{t("appointments.reschedule")}</span>
            <span className="sm:hidden">{t("appointments.rescheduleShort")}</span>
          </Button>
          <Button variant="destructive" size="sm" className="sm:size-md">
            <span className="hidden sm:inline">{t("appointments.cancelAppointment")}</span>
            <span className="sm:hidden">{t("appointments.cancel")}</span>
          </Button>
        </div>
      </div>

      {/* Patient Information Card - Expanded and at the top */}
      <Card className="w-full">
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <Avatar className="h-16 w-16">
                <AvatarImage src={appointment.patient.avatar || "/placeholder.svg"} alt={appointment.patient.name} />
                <AvatarFallback>
                  {appointment.patient.name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")}
                </AvatarFallback>
              </Avatar>
              <div>
                <CardTitle className="text-2xl">{appointment.patient.name}</CardTitle>
                <CardDescription className="text-base">
                  {appointment.patient.age} years • {appointment.patient.gender} • Patient ID: {appointment.patient.id}
                </CardDescription>
              </div>
            </div>
            <Badge className={appointment.status === "Scheduled" ? "bg-green-600" : "bg-yellow-600"}>
              {appointment.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <h3 className="font-medium text-lg mb-2">{t("appointments.contactInformation")}</h3>
              <div className="space-y-1 text-sm">
                <p>
                  <span className="font-medium">{t("appointments.email")}:</span> {appointment.patient.contact.email}
                </p>
                <p>
                  <span className="font-medium">{t("appointments.phone")}:</span> {appointment.patient.contact.phone}
                </p>
                <p>
                  <span className="font-medium">{t("appointments.address")}:</span>{" "}
                  {appointment.patient.contact.address}
                </p>
              </div>
            </div>
            <div>
              <h3 className="font-medium text-lg mb-2">{t("appointments.insuranceDetails")}</h3>
              <div className="space-y-1 text-sm">
                <p>
                  <span className="font-medium">{t("appointments.provider")}:</span>{" "}
                  {appointment.patient.insurance.provider}
                </p>
                <p>
                  <span className="font-medium">{t("appointments.policyNumber")}:</span>{" "}
                  {appointment.patient.insurance.policyNumber}
                </p>
                <p>
                  <span className="font-medium">{t("appointments.group")}:</span> {appointment.patient.insurance.group}
                </p>
              </div>
            </div>
            <div className="sm:col-span-2 lg:col-span-1">
              <h3 className="font-medium text-lg mb-2">{t("appointments.patientPermissions")}</h3>
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                <div className="flex items-center justify-between">
                  <span>{t("appointments.medicalHistory")}:</span>
                  {renderPermissionIcon(appointment.patient.permissions.medicalHistory)}
                </div>
                <div className="flex items-center justify-between">
                  <span>{t("appointments.medications")}:</span>
                  {renderPermissionIcon(appointment.patient.permissions.medications)}
                </div>
                <div className="flex items-center justify-between">
                  <span>{t("appointments.labResults")}:</span>
                  {renderPermissionIcon(appointment.patient.permissions.labResults)}
                </div>
                <div className="flex items-center justify-between">
                  <span>{t("appointments.billingInfo")}:</span>
                  {renderPermissionIcon(appointment.patient.permissions.billingInfo)}
                </div>
                <div className="flex items-center justify-between">
                  <span>{t("appointments.contactInfo")}:</span>
                  {renderPermissionIcon(appointment.patient.permissions.contactInfo)}
                </div>
                <div className="flex items-center justify-between">
                  <span>{t("appointments.appointmentNotes")}:</span>
                  {renderPermissionIcon(appointment.patient.permissions.appointmentNotes)}
                </div>
              </div>
              <div className="mt-2 text-xs flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-1">
                  <Check className="h-3 w-3 text-green-600" />
                  <span>{t("appointments.full")}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Check className="h-3 w-3 text-yellow-600" />
                  <span>{t("appointments.limited")}</span>
                </div>
                <div className="flex items-center gap-1">
                  <X className="h-3 w-3 text-red-600" />
                  <span>{t("appointments.none")}</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Middle Section - Video and Medical Info */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Video Conference Panel */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>{t("appointments.videoConference")}</CardTitle>
            <CardDescription>{t("appointments.connectWithPatient")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="aspect-video bg-gray-200 dark:bg-gray-800 rounded-lg flex items-center justify-center">
              <Video className="h-12 w-12 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">{t("appointments.status")}</p>
                <Badge className="bg-yellow-500 dark:bg-yellow-600">{t("appointments.waitingToStart")}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">{t("appointments.scheduledTime")}</p>
                <p className="text-sm">{appointment.time}</p>
              </div>
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">{t("appointments.duration")}</p>
                <p className="text-sm">{appointment.duration}</p>
              </div>
            </div>
            <Button className="w-full">
              <Video className="mr-2 h-4 w-4" />
              {t("appointments.joinVideoCall")}
            </Button>
            <div className="text-center text-xs text-muted-foreground">
              <p>
                {t("appointments.meetingLink")}:{" "}
                <a href={appointment.videoLink} className="text-teal-600 dark:text-teal-400 hover:underline">
                  {appointment.videoLink}
                </a>
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Patient Medical Information Panel */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>{t("appointments.medicalInformation")}</CardTitle>
            <CardDescription>{t("appointments.patientHealthRecords")}</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <Tabs defaultValue="summary">
              <TabsList className="w-full rounded-none border-b bg-transparent p-0 overflow-x-auto flex-nowrap">
                <TabsTrigger
                  value="summary"
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-teal-600 data-[state=active]:bg-transparent data-[state=active]:shadow-none flex-shrink-0"
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Summary
                </TabsTrigger>
                <TabsTrigger
                  value="history"
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-teal-600 data-[state=active]:bg-transparent data-[state=active]:shadow-none flex-shrink-0"
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Medical History
                </TabsTrigger>
                <TabsTrigger
                  value="medications"
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-teal-600 data-[state=active]:bg-transparent data-[state=active]:shadow-none flex-shrink-0"
                >
                  <Pill className="h-4 w-4 mr-2" />
                  Medications
                </TabsTrigger>
                <TabsTrigger
                  value="metrics"
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-teal-600 data-[state=active]:bg-transparent data-[state=active]:shadow-none flex-shrink-0"
                >
                  <LineChart className="h-4 w-4 mr-2" />
                  Health Metrics
                </TabsTrigger>
                <TabsTrigger
                  value="plans"
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-teal-600 data-[state=active]:bg-transparent data-[state=active]:shadow-none flex-shrink-0"
                >
                  <ListTodo className="h-4 w-4 mr-2" />
                  Health Plans
                </TabsTrigger>
                <TabsTrigger
                  value="notes"
                  className="rounded-none border-b-2 border-transparent data-[state=active]:border-teal-600 data-[state=active]:bg-transparent data-[state=active]:shadow-none flex-shrink-0"
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Clinical Notes
                </TabsTrigger>
              </TabsList>
              <TabsContent value="summary" className="p-4 space-y-4">
                <div className="space-y-4">
                  <div>
                    <h3 className="font-medium">{t("appointments.preExistingConditions")}</h3>
                    {appointment.patient.conditions.length > 0 ? (
                      <ul className="mt-1 list-disc pl-5">
                        {appointment.patient.conditions.map((condition, index) => (
                          <li key={index} className="text-sm">
                            {condition}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm mt-1">{t("appointments.noPreExistingConditions")}</p>
                    )}
                  </div>

                  <div>
                    <h3 className="font-medium">{t("appointments.patientSummary")}</h3>
                    <p className="text-sm mt-1">{appointment.patient.summary.preConditions}</p>
                  </div>

                  <div>
                    <h3 className="font-medium">{t("appointments.recentProgress")}</h3>
                    <p className="text-sm mt-1">{appointment.patient.summary.recentProgress}</p>
                  </div>

                  <div>
                    <h3 className="font-medium">{t("appointments.treatmentPlan")}</h3>
                    <p className="text-sm mt-1">{appointment.patient.summary.treatmentPlan}</p>
                  </div>

                  <div>
                    <h3 className="font-medium">{t("appointments.nextSteps")}</h3>
                    <p className="text-sm mt-1">{appointment.patient.summary.nextSteps}</p>
                  </div>

                  <div>
                    <h3 className="font-medium">{t("appointments.lastClinicalNote")}</h3>
                    {appointment.patient.clinicalNotes.length > 0 ? (
                      <div className="mt-1">
                        <p className="text-sm font-medium">
                          {appointment.patient.clinicalNotes[0].title} - {appointment.patient.clinicalNotes[0].date}
                        </p>
                        <p className="text-sm">{appointment.patient.clinicalNotes[0].content}</p>
                      </div>
                    ) : (
                      <p className="text-sm mt-1">{t("appointments.noClinicalNotesAvailable")}</p>
                    )}
                  </div>
                </div>
              </TabsContent>
              <TabsContent value="history" className="p-4 space-y-4">
                {appointment.medicalHistory.map((item, index) => (
                  <div key={index} className="border-b pb-3 last:border-0 last:pb-0">
                    <div className="flex items-center justify-between">
                      <p className="font-medium">{item.condition}</p>
                      <p className="text-sm text-muted-foreground">{item.date}</p>
                    </div>
                    <p className="text-sm mt-1">{item.notes}</p>
                  </div>
                ))}
                <Button variant="outline" className="w-full">
                  <Plus className="mr-2 h-4 w-4" />
                  {t("appointments.addMedicalHistory")}
                </Button>
              </TabsContent>
              <TabsContent value="medications" className="p-4 space-y-4">
                {appointment.medications.length > 0 ? (
                  appointment.medications.map((med, index) => (
                    <div key={index} className="border-b pb-3 last:border-0 last:pb-0">
                      <div className="flex items-center gap-2">
                        <Pill className="h-4 w-4 text-teal-600" />
                        <p className="font-medium">{med.name}</p>
                      </div>
                      <div className="ml-6 text-sm">
                        <p>
                          {t("appointments.dosage")}: {med.dosage}
                        </p>
                        <p>
                          {t("appointments.frequency")}: {med.frequency}
                        </p>
                        <p>
                          {t("appointments.started")}: {med.startDate}
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-center text-muted-foreground">{t("appointments.noMedicationsPrescribed")}</p>
                )}
                <Button variant="outline" className="w-full">
                  <Plus className="mr-2 h-4 w-4" />
                  {t("appointments.addMedication")}
                </Button>
              </TabsContent>
              <TabsContent value="metrics" className="p-4 space-y-6">
                {appointment.patient.healthMetrics.map((metric) => (
                  <div key={metric.id} className="space-y-2 border-b pb-6 last:border-0">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                      <h3 className="font-medium">{metric.name}</h3>
                      <div className="flex items-center gap-2 text-sm">
                        <span>
                          {t("appointments.current")}: <span className="font-medium">{metric.current}</span>{" "}
                          {metric.unit}
                        </span>
                        <span className="text-muted-foreground">|</span>
                        <span>
                          {t("appointments.target")}: <span className="font-medium">{metric.target}</span> {metric.unit}
                        </span>
                      </div>
                    </div>
                    {renderMetricChart(metric)}
                  </div>
                ))}
                <Button variant="outline" className="w-full mt-4">
                  <Plus className="mr-2 h-4 w-4" />
                  {t("appointments.addHealthMetric")}
                </Button>
              </TabsContent>
              <TabsContent value="plans" className="p-4 space-y-4">
                {appointment.healthPlans.map((plan, index) => (
                  <div key={index} className="border-b pb-3 last:border-0 last:pb-0">
                    <div className="flex items-center justify-between">
                      <p className="font-medium">{plan.title}</p>
                      <Badge
                        className={
                          plan.progress === "Good"
                            ? "bg-green-600"
                            : plan.progress === "Moderate"
                              ? "bg-yellow-600"
                              : "bg-red-600"
                        }
                      >
                        {plan.progress}
                      </Badge>
                    </div>
                    <p className="text-sm mt-1">
                      {t("appointments.target")}: {plan.target}
                    </p>
                    <div className="mt-2">
                      <p className="text-sm font-medium">{t("appointments.recommendations")}:</p>
                      <ul className="text-sm list-disc pl-5 mt-1">
                        {plan.recommendations.map((rec, i) => (
                          <li key={i}>{rec}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ))}
                <Button variant="outline" className="w-full">
                  <Plus className="mr-2 h-4 w-4" />
                  {t("appointments.addHealthPlan")}
                </Button>
              </TabsContent>
              <TabsContent value="notes" className="p-4 space-y-4">
                {appointment.patient.clinicalNotes.map((note) => (
                  <div key={note.id} className="border-b pb-3 last:border-0 last:pb-0">
                    <div className="flex items-center justify-between">
                      <p className="font-medium">{note.title}</p>
                      <p className="text-sm text-muted-foreground">
                        {note.date} • {note.provider}
                      </p>
                    </div>
                    <p className="text-sm mt-1">{note.content}</p>
                  </div>
                ))}
                <Button variant="outline" className="w-full">
                  <Plus className="mr-2 h-4 w-4" />
                  {t("appointments.addClinicalNote")}
                </Button>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>

      {/* Notes and Documents Section - Combined */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Notes & Documents</CardTitle>
              <CardDescription>Record observations and manage patient documents</CardDescription>
            </div>
            <Dialog>
              <DialogTrigger asChild>
                <Button>
                  <FileText className="mr-2 h-4 w-4" />
                  {t("appointments.createDocument")}
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[600px]">
                <DialogHeader>
                  <DialogTitle>Create New Document</DialogTitle>
                  <DialogDescription>Create a new document to share with the patient</DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid grid-cols-4 items-center gap-4">
                    <label htmlFor="documentType" className="text-right">
                      {t("appointments.type")}
                    </label>
                    <Select value={activeDocumentType} onValueChange={setActiveDocumentType}>
                      <SelectTrigger className="col-span-3">
                        <SelectValue placeholder="Select document type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Prescription">Prescription</SelectItem>
                        <SelectItem value="Lab Order">Lab Order</SelectItem>
                        <SelectItem value="Referral">Referral</SelectItem>
                        <SelectItem value="Medical Certificate">Medical Certificate</SelectItem>
                        <SelectItem value="Clinical Note">Clinical Note</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid grid-cols-4 items-center gap-4">
                    <label htmlFor="title" className="text-right">
                      {t("appointments.title")}
                    </label>
                    <input
                      id="title"
                      value={documentTitle}
                      onChange={(e) => setDocumentTitle(e.target.value)}
                      className="col-span-3 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    />
                  </div>
                  <div className="grid grid-cols-4 items-start gap-4">
                    <label htmlFor="content" className="text-right pt-2">
                      {t("appointments.content")}
                    </label>
                    <Textarea
                      id="content"
                      value={documentContent}
                      onChange={(e) => setDocumentContent(e.target.value)}
                      className="col-span-3 min-h-[150px]"
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline">{t("appointments.saveAsDraft")}</Button>
                  <Button>{t("appointments.createDocument")}</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <Tabs defaultValue="notes" onValueChange={setActiveTab}>
            <TabsList className="w-full rounded-none border-b bg-transparent p-0">
              <TabsTrigger
                value="notes"
                className="rounded-none border-b-2 border-transparent data-[state=active]:border-teal-600 data-[state=active]:bg-transparent data-[state=active]:shadow-none"
              >
                Notes
              </TabsTrigger>
              <TabsTrigger
                value="documents"
                className="rounded-none border-b-2 border-transparent data-[state=active]:border-teal-600 data-[state=active]:bg-transparent data-[state=active]:shadow-none"
              >
                Documents
              </TabsTrigger>
            </TabsList>
            <TabsContent value="notes" className="p-4">
              <div className="space-y-4">
                <Textarea
                  placeholder="Enter your notes for this appointment..."
                  className="min-h-[150px]"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />

                {/* AI Suggestions Section */}
                <div className="mt-6">
                  <h3 className="font-medium mb-2 flex items-center">
                    <Lightbulb className="h-4 w-4 mr-2 text-teal-600" />
                    AI Suggestions
                  </h3>
                  <div className="space-y-2">
                    {activeSuggestions.length > 0 ? (
                      activeSuggestions.map((suggestion, index) => (
                        <div
                          key={index}
                          className="flex items-start justify-between gap-2 p-2 border rounded-md hover:bg-gray-50 dark:hover:bg-gray-800 group"
                        >
                          <button
                            className="text-sm text-left flex-1 cursor-pointer"
                            onClick={() => addSuggestionToNotes(suggestion)}
                          >
                            {suggestion}
                          </button>
                          <button
                            className="opacity-0 group-hover:opacity-100 transition-opacity"
                            onClick={() => removeSuggestion(suggestion)}
                            aria-label="Remove suggestion"
                          >
                            <X className="h-4 w-4 text-gray-400 hover:text-red-500" />
                          </button>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-muted-foreground text-center py-2">No AI suggestions available</p>
                    )}
                  </div>
                </div>
              </div>
            </TabsContent>
            <TabsContent value="documents" className="p-4">
              {appointment.documents && appointment.documents.length > 0 ? (
                <div className="space-y-4">
                  {appointment.documents.map((doc) => (
                    <div key={doc.id} className="flex items-center justify-between p-3 border rounded-md">
                      <div className="flex items-center gap-3">
                        <FileText className="h-5 w-5 text-teal-600" />
                        <div>
                          <p className="font-medium">{doc.title}</p>
                          <p className="text-sm text-muted-foreground">
                            {doc.type} • {doc.date}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{doc.status}</Badge>
                        <Button variant="ghost" size="sm">
                          {t("appointments.edit")}
                        </Button>
                        <Button variant="ghost" size="sm">
                          {t("appointments.preview")}
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6">
                  <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-2" />
                  <p className="text-muted-foreground">No documents created yet</p>
                  <p className="text-sm text-muted-foreground mb-4">Create a document to share with the patient</p>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
        <CardFooter className="flex flex-col sm:flex-row justify-between gap-3 mt-4">
          <Button variant="outline" className="w-full sm:w-auto">
            Save Draft
          </Button>
          <Button className="w-full sm:w-auto">
            {activeTab === "documents" ? "Send Documents" : "Complete & Send Summary"}
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}

export default AppointmentDetailsPage

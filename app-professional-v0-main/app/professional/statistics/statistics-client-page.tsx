"use client"

import { Label } from "@/components/ui/label"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { cn } from "@/lib/utils"
import { format } from "date-fns"
import { CalendarIcon, Download, FileText, Filter, Search } from "lucide-react"
import { useMediaQuery } from "@/hooks/use-media-query"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { useLanguage } from "@/lib/language-context"

// Import chart components
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"

// Sample data for charts
const consultationData = [
  { month: "Jan", completed: 45, cancelled: 5, rescheduled: 8 },
  { month: "Feb", completed: 52, cancelled: 7, rescheduled: 10 },
  { month: "Mar", completed: 48, cancelled: 4, rescheduled: 6 },
  { month: "Apr", completed: 60, cancelled: 8, rescheduled: 12 },
  { month: "May", completed: 55, cancelled: 6, rescheduled: 9 },
  { month: "Jun", completed: 70, cancelled: 10, rescheduled: 15 },
]

const weeklyConsultationData = [
  { day: "Mon", completed: 12, cancelled: 1, rescheduled: 2 },
  { day: "Tue", completed: 15, cancelled: 2, rescheduled: 3 },
  { day: "Wed", completed: 10, cancelled: 1, rescheduled: 1 },
  { day: "Thu", completed: 14, cancelled: 2, rescheduled: 2 },
  { day: "Fri", completed: 18, cancelled: 3, rescheduled: 4 },
  { day: "Sat", completed: 8, cancelled: 1, rescheduled: 1 },
  { day: "Sun", completed: 3, cancelled: 0, rescheduled: 0 },
]

const patientAgeData = [
  { name: "0-18", value: 15 },
  { name: "19-35", value: 30 },
  { name: "36-50", value: 25 },
  { name: "51-65", value: 20 },
  { name: "65+", value: 10 },
]

const patientGenderData = [
  { name: "Female", value: 55 },
  { name: "Male", value: 43 },
  { name: "Other", value: 2 },
]

const newPatientsData = [
  { month: "Jan", count: 12 },
  { month: "Feb", count: 15 },
  { month: "Mar", count: 10 },
  { month: "Apr", count: 18 },
  { month: "May", count: 14 },
  { month: "Jun", count: 20 },
]

const weeklyNewPatientsData = [
  { day: "Mon", count: 3 },
  { day: "Tue", count: 4 },
  { day: "Wed", count: 2 },
  { day: "Thu", count: 5 },
  { day: "Fri", count: 3 },
  { day: "Sat", count: 2 },
  { day: "Sun", count: 1 },
]

const incomeData = [
  { month: "Jan", consultations: 4500, plans: 2500, total: 7000 },
  { month: "Feb", consultations: 5200, plans: 3000, total: 8200 },
  { month: "Mar", consultations: 4800, plans: 2800, total: 7600 },
  { month: "Apr", consultations: 6000, plans: 3500, total: 9500 },
  { month: "May", consultations: 5500, plans: 3200, total: 8700 },
  { month: "Jun", consultations: 7000, plans: 4000, total: 11000 },
]

const weeklyIncomeData = [
  { day: "Mon", consultations: 1200, plans: 600, total: 1800 },
  { day: "Tue", consultations: 1500, plans: 800, total: 2300 },
  { day: "Wed", consultations: 1000, plans: 500, total: 1500 },
  { day: "Thu", consultations: 1400, plans: 700, total: 2100 },
  { day: "Fri", consultations: 1800, plans: 900, total: 2700 },
  { day: "Sat", consultations: 800, plans: 400, total: 1200 },
  { day: "Sun", consultations: 300, plans: 100, total: 400 },
]

// Add this after the existing data declarations
const monthlyWeeklyData = {
  "1": [
    // January
    { week: "Week 1", completed: 10, cancelled: 1, rescheduled: 2 },
    { week: "Week 2", completed: 12, cancelled: 2, rescheduled: 1 },
    { week: "Week 3", completed: 11, cancelled: 1, rescheduled: 3 },
    { week: "Week 4", completed: 12, cancelled: 1, rescheduled: 2 },
  ],
  "2": [
    // February
    { week: "Week 1", completed: 13, cancelled: 2, rescheduled: 3 },
    { week: "Week 2", completed: 14, cancelled: 1, rescheduled: 2 },
    { week: "Week 3", completed: 12, cancelled: 2, rescheduled: 2 },
    { week: "Week 4", completed: 13, cancelled: 2, rescheduled: 3 },
  ],
  "3": [
    // March
    { week: "Week 1", completed: 11, cancelled: 1, rescheduled: 1 },
    { week: "Week 2", completed: 12, cancelled: 1, rescheduled: 2 },
    { week: "Week 3", completed: 13, cancelled: 1, rescheduled: 1 },
    { week: "Week 4", completed: 12, cancelled: 1, rescheduled: 2 },
  ],
  "4": [
    // April
    { week: "Week 1", completed: 14, cancelled: 2, rescheduled: 3 },
    { week: "Week 2", completed: 15, cancelled: 2, rescheduled: 3 },
    { week: "Week 3", completed: 16, cancelled: 2, rescheduled: 3 },
    { week: "Week 4", completed: 15, cancelled: 2, rescheduled: 3 },
  ],
  "5": [
    // May
    { week: "Week 1", completed: 13, cancelled: 1, rescheduled: 2 },
    { week: "Week 2", completed: 14, cancelled: 2, rescheduled: 2 },
    { week: "Week 3", completed: 13, cancelled: 1, rescheduled: 3 },
    { week: "Week 4", completed: 15, cancelled: 2, rescheduled: 2 },
  ],
  "6": [
    // June
    { week: "Week 1", completed: 17, cancelled: 2, rescheduled: 4 },
    { week: "Week 2", completed: 18, cancelled: 3, rescheduled: 4 },
    { week: "Week 3", completed: 17, cancelled: 2, rescheduled: 3 },
    { week: "Week 4", completed: 18, cancelled: 3, rescheduled: 4 },
  ],
  "7": [
    // July
    { week: "Week 1", completed: 16, cancelled: 2, rescheduled: 3 },
    { week: "Week 2", completed: 15, cancelled: 2, rescheduled: 3 },
    { week: "Week 3", completed: 16, cancelled: 2, rescheduled: 3 },
    { week: "Week 4", completed: 15, cancelled: 2, rescheduled: 3 },
  ],
  "8": [
    // August
    { week: "Week 1", completed: 14, cancelled: 2, rescheduled: 3 },
    { week: "Week 2", completed: 13, cancelled: 1, rescheduled: 2 },
    { week: "Week 3", completed: 14, cancelled: 2, rescheduled: 3 },
    { week: "Week 4", completed: 13, cancelled: 1, rescheduled: 2 },
  ],
  "9": [
    // September
    { week: "Week 1", completed: 15, cancelled: 2, rescheduled: 3 },
    { week: "Week 2", completed: 16, cancelled: 2, rescheduled: 3 },
    { week: "Week 3", completed: 15, cancelled: 2, rescheduled: 3 },
    { week: "Week 4", completed: 16, cancelled: 2, rescheduled: 3 },
  ],
  "10": [
    // October
    { week: "Week 1", completed: 17, cancelled: 2, rescheduled: 4 },
    { week: "Week 2", completed: 18, cancelled: 3, rescheduled: 4 },
    { week: "Week 3", completed: 17, cancelled: 2, rescheduled: 4 },
    { week: "Week 4", completed: 18, cancelled: 3, rescheduled: 4 },
  ],
  "11": [
    // November
    { week: "Week 1", completed: 16, cancelled: 2, rescheduled: 3 },
    { week: "Week 2", completed: 15, cancelled: 2, rescheduled: 3 },
    { week: "Week 3", completed: 16, cancelled: 2, rescheduled: 3 },
    { week: "Week 4", completed: 15, cancelled: 2, rescheduled: 3 },
  ],
  "12": [
    // December
    { week: "Week 1", completed: 14, cancelled: 2, rescheduled: 3 },
    { week: "Week 2", completed: 13, cancelled: 1, rescheduled: 2 },
    { week: "Week 3", completed: 14, cancelled: 2, rescheduled: 3 },
    { week: "Week 4", completed: 13, cancelled: 1, rescheduled: 2 },
  ],
}

// Similar data for patients and income
const monthlyWeeklyPatientsData = {
  "1": [
    // January
    { week: "Week 1", count: 3 },
    { week: "Week 2", count: 4 },
    { week: "Week 3", count: 2 },
    { week: "Week 4", count: 3 },
  ],
  "2": [
    { week: "Week 1", count: 3 },
    { week: "Week 2", count: 4 },
    { week: "Week 3", count: 2 },
    { week: "Week 4", count: 3 },
  ],
  "3": [
    { week: "Week 1", count: 3 },
    { week: "Week 2", count: 4 },
    { week: "Week 3", count: 2 },
    { week: "Week 4", count: 3 },
  ],
  "4": [
    { week: "Week 1", count: 3 },
    { week: "Week 2", count: 4 },
    { week: "Week 3", count: 2 },
    { week: "Week 4", count: 3 },
  ],
  "5": [
    { week: "Week 1", count: 3 },
    { week: "Week 2", count: 4 },
    { week: "Week 3", count: 2 },
    { week: "Week 4", count: 3 },
  ],
  "6": [
    { week: "Week 1", count: 3 },
    { week: "Week 2", count: 4 },
    { week: "Week 3", count: 2 },
    { week: "Week 4", count: 3 },
  ],
  "7": [
    { week: "Week 1", count: 3 },
    { week: "Week 2", count: 4 },
    { week: "Week 3", count: 2 },
    { week: "Week 4", count: 3 },
  ],
  "8": [
    { week: "Week 1", count: 3 },
    { week: "Week 2", count: 4 },
    { week: "Week 3", count: 2 },
    { week: "Week 4", count: 3 },
  ],
  "9": [
    { week: "Week 1", count: 3 },
    { week: "Week 2", count: 4 },
    { week: "Week 3", count: 2 },
    { week: "Week 4", count: 3 },
  ],
  "10": [
    { week: "Week 1", count: 3 },
    { week: "Week 2", count: 4 },
    { week: "Week 3", count: 2 },
    { week: "Week 4", count: 3 },
  ],
  "11": [
    { week: "Week 1", count: 3 },
    { week: "Week 2", count: 4 },
    { week: "Week 3", count: 2 },
    { week: "Week 4", count: 3 },
  ],
  "12": [
    { week: "Week 1", count: 3 },
    { week: "Week 2", count: 4 },
    { week: "Week 3", count: 2 },
    { week: "Week 4", count: 3 },
  ],
}

const monthlyWeeklyIncomeData = {
  "1": [
    // January
    { week: "Week 1", consultations: 1100, plans: 600, total: 1700 },
    { week: "Week 2", consultations: 1200, plans: 650, total: 1850 },
    { week: "Week 3", consultations: 1050, plans: 550, total: 1600 },
    { week: "Week 4", consultations: 1150, plans: 700, total: 1850 },
  ],
  "2": [
    { week: "Week 1", consultations: 1100, plans: 600, total: 1700 },
    { week: "Week 2", consultations: 1200, plans: 650, total: 1850 },
    { week: "Week 3", consultations: 1050, plans: 550, total: 1600 },
    { week: "Week 4", consultations: 1150, plans: 700, total: 1850 },
  ],
  "3": [
    { week: "Week 1", consultations: 1100, plans: 600, total: 1700 },
    { week: "Week 2", consultations: 1200, plans: 650, total: 1850 },
    { week: "Week 3", consultations: 1050, plans: 550, total: 1600 },
    { week: "Week 4", consultations: 1150, plans: 700, total: 1850 },
  ],
  "4": [
    { week: "Week 1", consultations: 1100, plans: 600, total: 1700 },
    { week: "Week 2", consultations: 1200, plans: 650, total: 1850 },
    { week: "Week 3", consultations: 1050, plans: 550, total: 1600 },
    { week: "Week 4", consultations: 1150, plans: 700, total: 1850 },
  ],
  "5": [
    { week: "Week 1", consultations: 1100, plans: 600, total: 1700 },
    { week: "Week 2", consultations: 1200, plans: 650, total: 1850 },
    { week: "Week 3", consultations: 1050, plans: 550, total: 1600 },
    { week: "Week 4", consultations: 1150, plans: 700, total: 1850 },
  ],
  "6": [
    { week: "Week 1", consultations: 1100, plans: 600, total: 1700 },
    { week: "Week 2", consultations: 1200, plans: 650, total: 1850 },
    { week: "Week 3", consultations: 1050, plans: 550, total: 1600 },
    { week: "Week 4", consultations: 1150, plans: 700, total: 1850 },
  ],
  "7": [
    { week: "Week 1", consultations: 1100, plans: 600, total: 1700 },
    { week: "Week 2", consultations: 1200, plans: 650, total: 1850 },
    { week: "Week 3", consultations: 1050, plans: 550, total: 1600 },
    { week: "Week 4", consultations: 1150, plans: 700, total: 1850 },
  ],
  "8": [
    { week: "Week 1", consultations: 1100, plans: 600, total: 1700 },
    { week: "Week 2", consultations: 1200, plans: 650, total: 1850 },
    { week: "Week 3", consultations: 1050, plans: 550, total: 1600 },
    { week: "Week 4", consultations: 1150, plans: 700, total: 1850 },
  ],
  "9": [
    { week: "Week 1", consultations: 1100, plans: 600, total: 1700 },
    { week: "Week 2", consultations: 1200, plans: 650, total: 1850 },
    { week: "Week 3", consultations: 1050, plans: 550, total: 1600 },
    { week: "Week 4", consultations: 1150, plans: 700, total: 1850 },
  ],
  "10": [
    { week: "Week 1", consultations: 1100, plans: 600, total: 1700 },
    { week: "Week 2", consultations: 1200, plans: 650, total: 1850 },
    { week: "Week 3", consultations: 1050, plans: 550, total: 1600 },
    { week: "Week 4", consultations: 1150, plans: 700, total: 1850 },
  ],
  "11": [
    { week: "Week 1", consultations: 1100, plans: 600, total: 1700 },
    { week: "Week 2", consultations: 1200, plans: 650, total: 1850 },
    { week: "Week 3", consultations: 1050, plans: 550, total: 1600 },
    { week: "Week 4", consultations: 1150, plans: 700, total: 1850 },
  ],
  "12": [
    { week: "Week 1", consultations: 1100, plans: 600, total: 1700 },
    { week: "Week 2", consultations: 1200, plans: 650, total: 1850 },
    { week: "Week 3", consultations: 1050, plans: 550, total: 1600 },
    { week: "Week 4", consultations: 1150, plans: 700, total: 1850 },
  ],
}

// Sample invoice data
const invoiceData = [
  {
    id: "INV-2025-001",
    date: "2025-06-01",
    amount: 4250.0,
    items: 15,
    period: "May 2025",
    status: "Paid",
    platform_fee: 1062.5, // 25% of 4250
    net_amount: 3187.5, // 75% of 4250
  },
  {
    id: "INV-2025-002",
    date: "2025-05-01",
    amount: 3850.0,
    items: 12,
    period: "April 2025",
    status: "Paid",
    platform_fee: 962.5, // 25% of 3850
    net_amount: 2887.5, // 75% of 3850
  },
  {
    id: "INV-2025-003",
    date: "2025-04-01",
    amount: 4100.0,
    items: 14,
    period: "March 2025",
    status: "Paid",
    platform_fee: 1025.0, // 25% of 4100
    net_amount: 3075.0, // 75% of 4100
  },
  {
    id: "INV-2025-004",
    date: "2025-03-01",
    amount: 3600.0,
    items: 11,
    period: "February 2025",
    status: "Paid",
    platform_fee: 900.0, // 25% of 3600
    net_amount: 2700.0, // 75% of 3600
  },
  {
    id: "INV-2025-005",
    date: "2025-02-01",
    amount: 3300.0,
    items: 10,
    period: "January 2025",
    status: "Paid",
    platform_fee: 825.0, // 25% of 3300
    net_amount: 2475.0, // 75% of 3300
  },
]

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884D8"]

export default function StatisticsClientPage() {
  const { t } = useLanguage()
  const [timeFilter, setTimeFilter] = useState("month")
  const [yearFilter, setYearFilter] = useState("2025")
  const [monthFilter, setMonthFilter] = useState("all")
  const [consultationsTimeFilter, setConsultationsTimeFilter] = useState("month")
  const [consultationsYearFilter, setConsultationsYearFilter] = useState("2025")
  const [consultationsMonthFilter, setConsultationsMonthFilter] = useState("all")
  const [patientsTimeFilter, setPatientsTimeFilter] = useState("month")
  const [patientsYearFilter, setPatientsYearFilter] = useState("2025")
  const [patientsMonthFilter, setPatientsMonthFilter] = useState("all")
  const [incomeTimeFilter, setIncomeTimeFilter] = useState("month")
  const [incomeYearFilter, setIncomeYearFilter] = useState("2025")
  const [incomeMonthFilter, setIncomeMonthFilter] = useState("all")
  const [startDate, setStartDate] = useState<Date | undefined>(new Date(2025, 0, 1))
  const [endDate, setEndDate] = useState<Date | undefined>(new Date(2025, 5, 30))
  const [invoiceSearch, setInvoiceSearch] = useState("")
  const [invoiceStatusFilter, setInvoiceStatusFilter] = useState("all")

  // Check if the screen is mobile
  const isMobile = useMediaQuery("(max-width: 768px)")

  // Get the appropriate data based on the time filter
  const getConsultationData = () => {
    if (consultationsTimeFilter === "week") {
      return weeklyConsultationData
    } else if (consultationsTimeFilter === "month" && consultationsMonthFilter !== "all") {
      // Return weekly data for the selected month
      return monthlyWeeklyData[consultationsMonthFilter] || consultationData
    } else {
      return consultationData
    }
  }

  const getNewPatientsData = () => {
    if (patientsTimeFilter === "week") {
      return weeklyNewPatientsData
    } else if (patientsTimeFilter === "month" && patientsMonthFilter !== "all") {
      // Return weekly data for the selected month
      return monthlyWeeklyPatientsData[patientsMonthFilter] || newPatientsData
    } else {
      return newPatientsData
    }
  }

  const getIncomeData = () => {
    if (incomeTimeFilter === "week") {
      return weeklyIncomeData
    } else if (incomeTimeFilter === "month" && incomeMonthFilter !== "all") {
      // Return weekly data for the selected month
      return monthlyWeeklyIncomeData[incomeMonthFilter] || incomeData
    } else {
      return incomeData
    }
  }

  // Get the appropriate x-axis key based on the time filter
  const getXAxisKey = (timeFilter: string, monthFilter?: string) => {
    if (timeFilter === "week") {
      return "day"
    } else if (timeFilter === "month" && monthFilter && monthFilter !== "all") {
      return "week"
    } else {
      return "month"
    }
  }

  // Filter invoices based on search and status
  const filteredInvoices = invoiceData.filter((invoice) => {
    const matchesSearch =
      invoice.id.toLowerCase().includes(invoiceSearch.toLowerCase()) ||
      invoice.period.toLowerCase().includes(invoiceSearch.toLowerCase())
    const matchesStatus =
      invoiceStatusFilter === "all" || invoice.status.toLowerCase() === invoiceStatusFilter.toLowerCase()
    return matchesSearch && matchesStatus
  })

  return (
    <div className="container py-6 px-4 md:px-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-teal-700 dark:text-teal-300">{t("statistics.title", "Statistics")}</h1>
        <p className="text-muted-foreground">
          {t("statistics.subtitle", "View and analyze your practice performance")}
        </p>
      </div>

      <Tabs defaultValue="summary" className="space-y-4">
        <TabsList className="grid w-full grid-cols-2 md:grid-cols-5">
          <TabsTrigger value="summary">{t("statistics.tabs.summary", "Summary")}</TabsTrigger>
          <TabsTrigger value="consultations">{t("statistics.tabs.consultations", "Consultations")}</TabsTrigger>
          <TabsTrigger value="patients">{t("statistics.tabs.patients", "Patients")}</TabsTrigger>
          <TabsTrigger value="income">{t("statistics.tabs.income", "Income")}</TabsTrigger>
          <TabsTrigger value="invoices">{t("statistics.tabs.invoices", "Invoices")}</TabsTrigger>
        </TabsList>

        {/* Summary Tab */}
        <TabsContent value="summary" className="space-y-4">
          <div className="flex flex-col md:flex-row justify-between gap-4 mb-4">
            <div className="flex flex-col md:flex-row gap-2">
              <Select value={timeFilter} onValueChange={setTimeFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder={t("statistics.selectTimePeriod", "Select time period")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="week">{t("statistics.timePeriods.weekly", "Weekly")}</SelectItem>
                  <SelectItem value="month">{t("statistics.timePeriods.monthly", "Monthly")}</SelectItem>
                  <SelectItem value="year">{t("statistics.timePeriods.yearly", "Yearly")}</SelectItem>
                </SelectContent>
              </Select>

              <Select value={yearFilter} onValueChange={setYearFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder={t("statistics.selectYear", "Select year")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="2024">2024</SelectItem>
                  <SelectItem value="2025">2025</SelectItem>
                </SelectContent>
              </Select>

              {timeFilter !== "year" && (
                <Select value={monthFilter} onValueChange={setMonthFilter}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder={t("statistics.selectMonth", "Select month")} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">{t("statistics.months.all", "All Months")}</SelectItem>
                    <SelectItem value="1">{t("statistics.months.january", "January")}</SelectItem>
                    <SelectItem value="2">{t("statistics.months.february", "February")}</SelectItem>
                    <SelectItem value="3">{t("statistics.months.march", "March")}</SelectItem>
                    <SelectItem value="4">{t("statistics.months.april", "April")}</SelectItem>
                    <SelectItem value="5">{t("statistics.months.may", "May")}</SelectItem>
                    <SelectItem value="6">{t("statistics.months.june", "June")}</SelectItem>
                    <SelectItem value="7">{t("statistics.months.july", "July")}</SelectItem>
                    <SelectItem value="8">{t("statistics.months.august", "August")}</SelectItem>
                    <SelectItem value="9">{t("statistics.months.september", "September")}</SelectItem>
                    <SelectItem value="10">{t("statistics.months.october", "October")}</SelectItem>
                    <SelectItem value="11">{t("statistics.months.november", "November")}</SelectItem>
                    <SelectItem value="12">{t("statistics.months.december", "December")}</SelectItem>
                  </SelectContent>
                </Select>
              )}
            </div>

            <div className="flex items-center gap-2">
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant={"outline"}
                    className={cn("justify-start text-left font-normal", !startDate && "text-muted-foreground")}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {startDate ? format(startDate, "PPP") : <span>{t("calendar.pickDate", "Pick a date")}</span>}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar mode="single" selected={startDate} onSelect={setStartDate} initialFocus />
                </PopoverContent>
              </Popover>
              <span>{t("statistics.to", "to")}</span>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant={"outline"}
                    className={cn("justify-start text-left font-normal", !endDate && "text-muted-foreground")}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {endDate ? format(endDate, "PPP") : <span>{t("calendar.pickDate", "Pick a date")}</span>}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar mode="single" selected={endDate} onSelect={setEndDate} initialFocus />
                </PopoverContent>
              </Popover>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("statistics.totalConsultations", "Total Consultations")}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">280</div>
                <p className="text-xs text-muted-foreground">
                  {t("statistics.percentIncrease", "+12% from last period")}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{t("statistics.newPatients", "New Patients")}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">89</div>
                <p className="text-xs text-muted-foreground">
                  {t("statistics.percentIncrease", "+5% from last period")}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{t("statistics.totalRevenue", "Total Revenue")}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">$52,000</div>
                <p className="text-xs text-muted-foreground">
                  {t("statistics.percentIncrease", "+18% from last period")}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("statistics.avgConsultationValue", "Avg. Consultation Value")}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">$185</div>
                <p className="text-xs text-muted-foreground">
                  {t("statistics.percentIncrease", "+2% from last period")}
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>{t("statistics.consultationsOverview", "Consultations Overview")}</CardTitle>
                <CardDescription>
                  {t("statistics.consultationsOverviewDesc", "Completed, cancelled, and rescheduled consultations")}
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={getConsultationData()}
                    margin={{
                      top: 20,
                      right: 30,
                      left: 0,
                      bottom: 0,
                    }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey={getXAxisKey(timeFilter, monthFilter)} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="completed" name={t("statistics.completed", "Completed")} fill="#14b8a6" />
                    <Bar dataKey="cancelled" name={t("statistics.cancelled", "Cancelled")} fill="#f87171" />
                    <Bar dataKey="rescheduled" name={t("statistics.rescheduled", "Rescheduled")} fill="#60a5fa" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t("statistics.patientDemographics", "Patient Demographics")}</CardTitle>
                <CardDescription>
                  {t("statistics.patientDemographicsDesc", "Distribution by age and gender")}
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[300px]">
                <div className="grid grid-cols-2 gap-4 h-full">
                  <div>
                    <h4 className="text-sm font-medium mb-2 text-center">
                      {t("statistics.ageDistribution", "Age Distribution")}
                    </h4>
                    <ResponsiveContainer width="100%" height="90%">
                      <PieChart>
                        <Pie
                          data={patientAgeData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) =>
                            isMobile ? `${(percent * 100).toFixed(0)}%` : `${name}: ${(percent * 100).toFixed(0)}%`
                          }
                          outerRadius={isMobile ? 60 : 80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {patientAgeData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium mb-2 text-center">
                      {t("statistics.genderDistribution", "Gender Distribution")}
                    </h4>
                    <ResponsiveContainer width="100%" height="90%">
                      <PieChart>
                        <Pie
                          data={patientGenderData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) =>
                            isMobile ? `${(percent * 100).toFixed(0)}%` : `${name}: ${(percent * 100).toFixed(0)}%`
                          }
                          outerRadius={isMobile ? 60 : 80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {patientGenderData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>{t("statistics.newPatientsTrend", "New Patients")}</CardTitle>
                <CardDescription>
                  {t("statistics.newPatientsTrendDesc", "Number of new patients over time")}
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={getNewPatientsData()}
                    margin={{
                      top: 20,
                      right: 30,
                      left: 0,
                      bottom: 0,
                    }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey={getXAxisKey(timeFilter, monthFilter)} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="count"
                      name={t("statistics.count", "Count")}
                      stroke="#14b8a6"
                      activeDot={{ r: 8 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t("statistics.revenueBreakdown", "Revenue Breakdown")}</CardTitle>
                <CardDescription>
                  {t("statistics.revenueBreakdownDesc", "Income from consultations and health plans")}
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={getIncomeData()}
                    margin={{
                      top: 20,
                      right: 30,
                      left: 0,
                      bottom: 0,
                    }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey={getXAxisKey(timeFilter, monthFilter)} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar
                      dataKey="consultations"
                      name={t("statistics.consultationsRevenue", "Consultations")}
                      fill="#14b8a6"
                    />
                    <Bar dataKey="plans" name={t("statistics.plansRevenue", "Plans")} fill="#60a5fa" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Consultations Tab */}
        <TabsContent value="consultations" className="space-y-4">
          <div className="flex flex-col md:flex-row justify-between gap-4 mb-4">
            <div className="flex flex-col md:flex-row gap-2">
              <Select value={consultationsTimeFilter} onValueChange={setConsultationsTimeFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder={t("statistics.selectTimePeriod", "Select time period")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="week">{t("statistics.timePeriods.weekly", "Weekly")}</SelectItem>
                  <SelectItem value="month">{t("statistics.timePeriods.monthly", "Monthly")}</SelectItem>
                  <SelectItem value="year">{t("statistics.timePeriods.yearly", "Yearly")}</SelectItem>
                </SelectContent>
              </Select>

              <Select value={consultationsYearFilter} onValueChange={setConsultationsYearFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder={t("statistics.selectYear", "Select year")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="2024">2024</SelectItem>
                  <SelectItem value="2025">2025</SelectItem>
                </SelectContent>
              </Select>

              {consultationsTimeFilter !== "year" && (
                <Select value={consultationsMonthFilter} onValueChange={setConsultationsMonthFilter}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder={t("statistics.selectMonth", "Select month")} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">{t("statistics.months.all", "All Months")}</SelectItem>
                    <SelectItem value="1">{t("statistics.months.january", "January")}</SelectItem>
                    <SelectItem value="2">{t("statistics.months.february", "February")}</SelectItem>
                    <SelectItem value="3">{t("statistics.months.march", "March")}</SelectItem>
                    <SelectItem value="4">{t("statistics.months.april", "April")}</SelectItem>
                    <SelectItem value="5">{t("statistics.months.may", "May")}</SelectItem>
                    <SelectItem value="6">{t("statistics.months.june", "June")}</SelectItem>
                    <SelectItem value="7">{t("statistics.months.july", "July")}</SelectItem>
                    <SelectItem value="8">{t("statistics.months.august", "August")}</SelectItem>
                    <SelectItem value="9">{t("statistics.months.september", "September")}</SelectItem>
                    <SelectItem value="10">{t("statistics.months.october", "October")}</SelectItem>
                    <SelectItem value="11">{t("statistics.months.november", "November")}</SelectItem>
                    <SelectItem value="12">{t("statistics.months.december", "December")}</SelectItem>
                  </SelectContent>
                </Select>
              )}
            </div>

            <div className="flex items-center gap-2">
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant={"outline"}
                    className={cn("justify-start text-left font-normal", !startDate && "text-muted-foreground")}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {startDate ? format(startDate, "PPP") : <span>{t("calendar.pickDate", "Pick a date")}</span>}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar mode="single" selected={startDate} onSelect={setStartDate} initialFocus />
                </PopoverContent>
              </Popover>
              <span>{t("statistics.to", "to")}</span>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant={"outline"}
                    className={cn("justify-start text-left font-normal", !endDate && "text-muted-foreground")}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {endDate ? format(endDate, "PPP") : <span>{t("calendar.pickDate", "Pick a date")}</span>}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar mode="single" selected={endDate} onSelect={setEndDate} initialFocus />
                </PopoverContent>
              </Popover>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("statistics.totalConsultations", "Total Consultations")}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">280</div>
                <p className="text-xs text-muted-foreground">
                  {t("statistics.percentIncrease", "+12% from last period")}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{t("statistics.completed", "Completed")}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">245</div>
                <p className="text-xs text-muted-foreground">
                  {t("statistics.completionRate", "87.5% completion rate")}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{t("statistics.cancelled", "Cancelled")}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">20</div>
                <p className="text-xs text-muted-foreground">
                  {t("statistics.cancellationRate", "7.1% cancellation rate")}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{t("statistics.rescheduled", "Rescheduled")}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">15</div>
                <p className="text-xs text-muted-foreground">
                  {t("statistics.rescheduleRate", "5.4% reschedule rate")}
                </p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>{t("statistics.consultationsTrend", "Consultations Trend")}</CardTitle>
              <CardDescription>
                {t(
                  "statistics.consultationsTrendDesc",
                  "Completed, cancelled, and rescheduled consultations over time",
                )}
              </CardDescription>
            </CardHeader>
            <CardContent className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={getConsultationData()}
                  margin={{
                    top: 20,
                    right: 30,
                    left: 20,
                    bottom: 20,
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey={getXAxisKey(consultationsTimeFilter, consultationsMonthFilter)} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="completed" name={t("statistics.completed", "Completed")} fill="#14b8a6" />
                  <Bar dataKey="cancelled" name={t("statistics.cancelled", "Cancelled")} fill="#f87171" />
                  <Bar dataKey="rescheduled" name={t("statistics.rescheduled", "Rescheduled")} fill="#60a5fa" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>{t("statistics.consultationTypes", "Consultation Types")}</CardTitle>
                <CardDescription>
                  {t("statistics.consultationTypesDesc", "Distribution by consultation type")}
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={[
                        { name: t("statistics.consultationTypeInitial", "Initial Consultation"), value: 65 },
                        { name: t("statistics.consultationTypeFollowUp", "Follow-up"), value: 120 },
                        { name: t("statistics.consultationTypeAnnual", "Annual Physical"), value: 45 },
                        { name: t("statistics.consultationTypeUrgent", "Urgent Care"), value: 50 },
                      ]}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) =>
                        isMobile ? `${(percent * 100).toFixed(0)}%` : `${name}: ${(percent * 100).toFixed(0)}%`
                      }
                      outerRadius={isMobile ? 80 : 100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {patientAgeData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t("statistics.consultationDuration", "Consultation Duration")}</CardTitle>
                <CardDescription>
                  {t("statistics.consultationDurationDesc", "Average duration by consultation type")}
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={[
                      { type: t("statistics.consultationTypeInitialShort", "Initial"), duration: 45 },
                      { type: t("statistics.consultationTypeFollowUpShort", "Follow-up"), duration: 30 },
                      { type: t("statistics.consultationTypeAnnualShort", "Annual"), duration: 60 },
                      { type: t("statistics.consultationTypeUrgentShort", "Urgent"), duration: 25 },
                    ]}
                    margin={{
                      top: 20,
                      right: 30,
                      left: 20,
                      bottom: 20,
                    }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="type" />
                    <YAxis label={{ value: t("statistics.minutes", "Minutes"), angle: -90, position: "insideLeft" }} />
                    <Tooltip />
                    <Bar dataKey="duration" name={t("statistics.duration", "Duration")} fill="#14b8a6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Patients Tab */}
        <TabsContent value="patients" className="space-y-4">
          <div className="flex flex-col md:flex-row justify-between gap-4 mb-4">
            <div className="flex flex-col md:flex-row gap-2">
              <Select value={patientsTimeFilter} onValueChange={setPatientsTimeFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder={t("statistics.selectTimePeriod", "Select time period")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="week">{t("statistics.timePeriods.weekly", "Weekly")}</SelectItem>
                  <SelectItem value="month">{t("statistics.timePeriods.monthly", "Monthly")}</SelectItem>
                  <SelectItem value="year">{t("statistics.timePeriods.yearly", "Yearly")}</SelectItem>
                </SelectContent>
              </Select>

              <Select value={patientsYearFilter} onValueChange={setPatientsYearFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder={t("statistics.selectYear", "Select year")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="2024">2024</SelectItem>
                  <SelectItem value="2025">2025</SelectItem>
                </SelectContent>
              </Select>

              {patientsTimeFilter !== "year" && (
                <Select value={patientsMonthFilter} onValueChange={setPatientsMonthFilter}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder={t("statistics.selectMonth", "Select month")} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">{t("statistics.months.all", "All Months")}</SelectItem>
                    <SelectItem value="1">{t("statistics.months.january", "January")}</SelectItem>
                    <SelectItem value="2">{t("statistics.months.february", "February")}</SelectItem>
                    <SelectItem value="3">{t("statistics.months.march", "March")}</SelectItem>
                    <SelectItem value="4">{t("statistics.months.april", "April")}</SelectItem>
                    <SelectItem value="5">{t("statistics.months.may", "May")}</SelectItem>
                    <SelectItem value="6">{t("statistics.months.june", "June")}</SelectItem>
                    <SelectItem value="7">{t("statistics.months.july", "July")}</SelectItem>
                    <SelectItem value="8">{t("statistics.months.august", "August")}</SelectItem>
                    <SelectItem value="9">{t("statistics.months.september", "September")}</SelectItem>
                    <SelectItem value="10">{t("statistics.months.october", "October")}</SelectItem>
                    <SelectItem value="11">{t("statistics.months.november", "November")}</SelectItem>
                    <SelectItem value="12">{t("statistics.months.december", "December")}</SelectItem>
                  </SelectContent>
                </Select>
              )}
            </div>

            <div className="flex items-center gap-2">
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant={"outline"}
                    className={cn("justify-start text-left font-normal", !startDate && "text-muted-foreground")}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {startDate ? format(startDate, "PPP") : <span>{t("calendar.pickDate", "Pick a date")}</span>}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar mode="single" selected={startDate} onSelect={setStartDate} initialFocus />
                </PopoverContent>
              </Popover>
              <span>{t("statistics.to", "to")}</span>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant={"outline"}
                    className={cn("justify-start text-left font-normal", !endDate && "text-muted-foreground")}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {endDate ? format(endDate, "PPP") : <span>{t("calendar.pickDate", "Pick a date")}</span>}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar mode="single" selected={endDate} onSelect={setEndDate} initialFocus />
                </PopoverContent>
              </Popover>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{t("statistics.totalPatients", "Total Patients")}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">450</div>
                <p className="text-xs text-muted-foreground">
                  {t("statistics.percentIncrease", "+8% from last period")}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{t("statistics.newPatients", "New Patients")}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">89</div>
                <p className="text-xs text-muted-foreground">
                  {t("statistics.percentIncrease", "+5% from last period")}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("statistics.activePatients", "Active Patients")}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">320</div>
                <p className="text-xs text-muted-foreground">
                  {t("statistics.percentOfTotal", "71% of total patients")}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("statistics.avgVisitsPerPatient", "Avg. Visits per Patient")}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">3.2</div>
                <p className="text-xs text-muted-foreground">
                  {t("statistics.increaseFromLastPeriod", "+0.3 from last period")}
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>{t("statistics.newPatientsTrend", "New Patients Trend")}</CardTitle>
                <CardDescription>
                  {t("statistics.newPatientsTrendDesc", "Number of new patients over time")}
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={getNewPatientsData()}
                    margin={{
                      top: 20,
                      right: 30,
                      left: 20,
                      bottom: 20,
                    }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey={getXAxisKey(patientsTimeFilter, patientsMonthFilter)} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="count"
                      name={t("statistics.count", "Count")}
                      stroke="#14b8a6"
                      activeDot={{ r: 8 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t("statistics.patientDemographics", "Patient Demographics")}</CardTitle>
                <CardDescription>
                  {t("statistics.patientDemographicsDesc", "Distribution by age and gender")}
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[300px]">
                <div className="grid grid-cols-2 gap-4 h-full">
                  <div>
                    <h4 className="text-sm font-medium mb-2 text-center">
                      {t("statistics.ageDistribution", "Age Distribution")}
                    </h4>
                    <ResponsiveContainer width="100%" height="90%">
                      <PieChart>
                        <Pie
                          data={patientAgeData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) =>
                            isMobile ? `${(percent * 100).toFixed(0)}%` : `${name}: ${(percent * 100).toFixed(0)}%`
                          }
                          outerRadius={isMobile ? 60 : 80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {patientAgeData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium mb-2 text-center">
                      {t("statistics.genderDistribution", "Gender Distribution")}
                    </h4>
                    <ResponsiveContainer width="100%" height="90%">
                      <PieChart>
                        <Pie
                          data={patientGenderData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) =>
                            isMobile ? `${(percent * 100).toFixed(0)}%` : `${name}: ${(percent * 100).toFixed(0)}%`
                          }
                          outerRadius={isMobile ? 60 : 80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {patientGenderData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>{t("statistics.patientRetention", "Patient Retention")}</CardTitle>
              <CardDescription>
                {t("statistics.patientRetentionDesc", "Percentage of returning patients over time")}
              </CardDescription>
            </CardHeader>
            <CardContent className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={[
                    { month: "Jan", retention: 75 },
                    { month: "Feb", retention: 78 },
                    { month: "Mar", retention: 76 },
                    { month: "Apr", retention: 80 },
                    { month: "May", retention: 82 },
                    { month: "Jun", retention: 85 },
                  ]}
                  margin={{
                    top: 20,
                    right: 30,
                    left: 20,
                    bottom: 20,
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="retention"
                    name={t("statistics.retention", "Retention")}
                    stroke="#14b8a6"
                    activeDot={{ r: 8 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Income Tab */}
        <TabsContent value="income" className="space-y-4">
          <div className="flex flex-col md:flex-row justify-between gap-4 mb-4">
            <div className="flex flex-col md:flex-row gap-2">
              <Select value={incomeTimeFilter} onValueChange={setIncomeTimeFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder={t("statistics.selectTimePeriod", "Select time period")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="week">{t("statistics.timePeriods.weekly", "Weekly")}</SelectItem>
                  <SelectItem value="month">{t("statistics.timePeriods.monthly", "Monthly")}</SelectItem>
                  <SelectItem value="year">{t("statistics.timePeriods.yearly", "Yearly")}</SelectItem>
                </SelectContent>
              </Select>

              <Select value={incomeYearFilter} onValueChange={setIncomeYearFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder={t("statistics.selectYear", "Select year")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="2024">2024</SelectItem>
                  <SelectItem value="2025">2025</SelectItem>
                </SelectContent>
              </Select>

              {incomeTimeFilter !== "year" && (
                <Select value={incomeMonthFilter} onValueChange={setIncomeMonthFilter}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder={t("statistics.selectMonth", "Select month")} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">{t("statistics.months.all", "All Months")}</SelectItem>
                    <SelectItem value="1">{t("statistics.months.january", "January")}</SelectItem>
                    <SelectItem value="2">{t("statistics.months.february", "February")}</SelectItem>
                    <SelectItem value="3">{t("statistics.months.march", "March")}</SelectItem>
                    <SelectItem value="4">{t("statistics.months.april", "April")}</SelectItem>
                    <SelectItem value="5">{t("statistics.months.may", "May")}</SelectItem>
                    <SelectItem value="6">{t("statistics.months.june", "June")}</SelectItem>
                    <SelectItem value="7">{t("statistics.months.july", "July")}</SelectItem>
                    <SelectItem value="8">{t("statistics.months.august", "August")}</SelectItem>
                    <SelectItem value="9">{t("statistics.months.september", "September")}</SelectItem>
                    <SelectItem value="10">{t("statistics.months.october", "October")}</SelectItem>
                    <SelectItem value="11">{t("statistics.months.november", "November")}</SelectItem>
                    <SelectItem value="12">{t("statistics.months.december", "December")}</SelectItem>
                  </SelectContent>
                </Select>
              )}
            </div>

            <div className="flex items-center gap-2">
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant={"outline"}
                    className={cn("justify-start text-left font-normal", !startDate && "text-muted-foreground")}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {startDate ? format(startDate, "PPP") : <span>{t("calendar.pickDate", "Pick a date")}</span>}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar mode="single" selected={startDate} onSelect={setStartDate} initialFocus />
                </PopoverContent>
              </Popover>
              <span>{t("statistics.to", "to")}</span>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant={"outline"}
                    className={cn("justify-start text-left font-normal", !endDate && "text-muted-foreground")}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {endDate ? format(endDate, "PPP") : <span>{t("calendar.pickDate", "Pick a date")}</span>}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar mode="single" selected={endDate} onSelect={setEndDate} initialFocus />
                </PopoverContent>
              </Popover>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{t("statistics.totalRevenue", "Total Revenue")}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">$52,000</div>
                <p className="text-xs text-muted-foreground">
                  {t("statistics.percentIncrease", "+18% from last period")}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("statistics.consultationsRevenue", "Consultation Revenue")}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">$33,000</div>
                <p className="text-xs text-muted-foreground">
                  {t("statistics.percentOfTotal", "63.5% of total revenue")}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("statistics.healthPlanRevenue", "Health Plan Revenue")}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">$19,000</div>
                <p className="text-xs text-muted-foreground">
                  {t("statistics.percentOfTotal", "36.5% of total revenue")}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {t("statistics.avgRevenuePerPatient", "Avg. Revenue per Patient")}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">$115</div>
                <p className="text-xs text-muted-foreground">
                  {t("statistics.percentIncrease", "+5% from last period")}
                </p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>{t("statistics.revenueBreakdown", "Revenue Breakdown")}</CardTitle>
              <CardDescription>
                {t("statistics.revenueBreakdownDesc", "Income from consultations and health plans")}
              </CardDescription>
            </CardHeader>
            <CardContent className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={getIncomeData()}
                  margin={{
                    top: 20,
                    right: 30,
                    left: 20,
                    bottom: 20,
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey={getXAxisKey(incomeTimeFilter, incomeMonthFilter)} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar
                    dataKey="consultations"
                    name={t("statistics.consultationsRevenue", "Consultations")}
                    fill="#14b8a6"
                  />
                  <Bar dataKey="plans" name={t("statistics.plansRevenue", "Plans")} fill="#60a5fa" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>{t("statistics.netIncomeTrend", "Net Income Trend")}</CardTitle>
                <CardDescription>{t("statistics.netIncomeTrendDesc", "Total revenue over time")}</CardDescription>
              </CardHeader>
              <CardContent className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={getIncomeData()}
                    margin={{
                      top: 20,
                      right: 30,
                      left: 20,
                      bottom: 20,
                    }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey={getXAxisKey(incomeTimeFilter, incomeMonthFilter)} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="total"
                      name={t("statistics.total", "Total")}
                      stroke="#14b8a6"
                      activeDot={{ r: 8 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t("statistics.revenueByServiceType", "Revenue by Service Type")}</CardTitle>
                <CardDescription>
                  {t("statistics.revenueByServiceTypeDesc", "Distribution of income by service")}
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={[
                        { name: t("statistics.initialConsultations", "Initial Consultations"), value: 13000 },
                        { name: t("statistics.followUps", "Follow-ups"), value: 12000 },
                        { name: t("statistics.annualPhysicals", "Annual Physicals"), value: 8000 },
                        { name: t("statistics.healthPlans", "Health Plans"), value: 19000 },
                      ]}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) =>
                        isMobile ? `${(percent * 100).toFixed(0)}%` : `${name}: ${(percent * 100).toFixed(0)}%`
                      }
                      outerRadius={isMobile ? 80 : 100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {patientAgeData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => `$${value}`} />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Invoices Tab */}
        <TabsContent value="invoices" className="space-y-4">
          <div className="flex flex-col md:flex-row justify-between gap-4 mb-4">
            <div className="flex flex-col md:flex-row gap-2">
              <div className="relative w-full md:w-[300px]">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder={t("statistics.searchInvoices", "Search invoices...")}
                  className="pl-8"
                  value={invoiceSearch}
                  onChange={(e) => setInvoiceSearch(e.target.value)}
                />
              </div>

              <Select value={invoiceStatusFilter} onValueChange={setInvoiceStatusFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder={t("statistics.filterByStatus", "Filter by status")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t("statistics.allStatuses", "All Statuses")}</SelectItem>
                  <SelectItem value="paid">{t("statistics.paid", "Paid")}</SelectItem>
                  <SelectItem value="pending">{t("statistics.pending", "Pending")}</SelectItem>
                  <SelectItem value="overdue">{t("statistics.overdue", "Overdue")}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex flex-col md:flex-row gap-2">
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" size="sm" className="h-10">
                    <Filter className="mr-2 h-4 w-4" />
                    {t("statistics.filter", "Filter")}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-80 p-4" align="end">
                  <div className="space-y-4">
                    <h4 className="font-medium">{t("statistics.dateRange", "Date Range")}</h4>
                    <div className="flex flex-col gap-2">
                      <div className="space-y-2">
                        <Label htmlFor="from-date">{t("statistics.from", "From")}</Label>
                        <Input id="from-date" type="date" />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="to-date">{t("statistics.to", "To")}</Label>
                        <Input id="to-date" type="date" />
                      </div>
                    </div>
                    <div className="flex justify-end">
                      <Button size="sm">{t("statistics.applyFilters", "Apply Filters")}</Button>
                    </div>
                  </div>
                </PopoverContent>
              </Popover>

              <Button variant="outline" size="sm" className="h-10">
                <Download className="mr-2 h-4 w-4" />
                {t("statistics.export", "Export")}
              </Button>
            </div>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>{t("statistics.platformInvoices", "Platform Invoices")}</CardTitle>
              <CardDescription>
                {t("statistics.platformInvoicesDesc", "All invoices submitted by the platform for your services")}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="border rounded-md">
                <table className="w-full">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-3 font-medium">{t("statistics.invoiceNumber", "Invoice #")}</th>
                      <th className="text-left p-3 font-medium">{t("statistics.date", "Date")}</th>
                      <th className="text-left p-3 font-medium">{t("statistics.period", "Period")}</th>
                      <th className="text-left p-3 font-medium">{t("statistics.amount", "Amount")}</th>
                      <th className="text-left p-3 font-medium">{t("statistics.platformFee", "Platform Fee")}</th>
                      <th className="text-left p-3 font-medium">{t("statistics.netAmount", "Net Amount")}</th>
                      <th className="text-left p-3 font-medium">{t("statistics.status", "Status")}</th>
                      <th className="text-center p-3 font-medium">{t("statistics.actions", "Actions")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredInvoices.length > 0 ? (
                      filteredInvoices.map((invoice) => (
                        <tr key={invoice.id} className="border-b hover:bg-muted/30">
                          <td className="p-3">{invoice.id}</td>
                          <td className="p-3">{invoice.date}</td>
                          <td className="p-3">{invoice.period}</td>
                          <td className="p-3">${invoice.amount.toFixed(2)}</td>
                          <td className="p-3">${invoice.platform_fee.toFixed(2)}</td>
                          <td className="p-3">${invoice.net_amount.toFixed(2)}</td>
                          <td className="p-3">
                            <Badge
                              variant={
                                invoice.status === "Paid"
                                  ? "default"
                                  : invoice.status === "Pending"
                                    ? "outline"
                                    : "destructive"
                              }
                            >
                              {t(`statistics.${invoice.status.toLowerCase()}`, invoice.status)}
                            </Badge>
                          </td>
                          <td className="p-3 text-center">
                            <Button variant="ghost" size="sm" className="h-8 px-2">
                              <FileText className="h-4 w-4 mr-1" />
                              {t("statistics.view", "View")}
                            </Button>
                            <Button variant="ghost" size="sm" className="h-8 px-2">
                              <Download className="h-4 w-4 mr-1" />
                              {t("statistics.pdf", "PDF")}
                            </Button>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={8} className="p-4 text-center text-muted-foreground">
                          {t("statistics.noInvoicesFound", "No invoices found matching your search criteria.")}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              <div className="mt-4 flex justify-between items-center">
                <p className="text-sm text-muted-foreground">
                  {t("statistics.showingInvoices", "Showing {0} of {1} invoices", {
                    0: filteredInvoices.length,
                    1: invoiceData.length,
                  })}
                </p>
                <div className="flex gap-1">
                  <Button variant="outline" size="sm" disabled>
                    {t("statistics.previous", "Previous")}
                  </Button>
                  <Button variant="outline" size="sm" disabled>
                    {t("statistics.next", "Next")}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>{t("statistics.invoiceSummary", "Invoice Summary")}</CardTitle>
                <CardDescription>
                  {t("statistics.invoiceSummaryDesc", "Financial overview of your platform invoices")}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-muted-foreground">
                      {t("statistics.totalInvoiced", "Total Invoiced (2025)")}
                    </p>
                    <p className="text-2xl font-bold">$19,100.00</p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-muted-foreground">
                      {t("statistics.platformFees", "Platform Fees")}
                    </p>
                    <p className="text-2xl font-bold">$4,775.00</p> {/* 25% of $19,100 */}
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-muted-foreground">
                      {t("statistics.netEarnings", "Net Earnings")}
                    </p>
                    <p className="text-2xl font-bold">$14,325.00</p> {/* 75% of $19,100 */}
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-muted-foreground">
                      {t("statistics.averageMonthly", "Average Monthly")}
                    </p>
                    <p className="text-2xl font-bold">$3,820.00</p>
                  </div>
                </div>

                <div className="mt-6 h-[200px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={[
                        { month: "Jan", amount: 3300 },
                        { month: "Feb", amount: 3600 },
                        { month: "Mar", amount: 4100 },
                        { month: "Apr", amount: 3850 },
                        { month: "May", amount: 4250 },
                      ]}
                      margin={{
                        top: 5,
                        right: 30,
                        left: 20,
                        bottom: 5,
                      }}
                    >
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="month" />
                      <YAxis />
                      <Tooltip formatter={(value) => [`$${value}`, t("statistics.amount", "Amount")]} />
                      <Line
                        type="monotone"
                        dataKey="amount"
                        name={t("statistics.amount", "Amount")}
                        stroke="#14b8a6"
                        activeDot={{ r: 8 }}
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t("statistics.platformFeeAnalysis", "Platform Fee Analysis")}</CardTitle>
                <CardDescription>
                  {t("statistics.platformFeeAnalysisDesc", "Breakdown of platform fees over time")}
                </CardDescription>
              </CardHeader>
              <CardContent className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={[
                      { month: "Jan", fees: 825, revenue: 2475 }, // 25% and 75% of 3300
                      { month: "Feb", fees: 900, revenue: 2700 }, // 25% and 75% of 3600
                      { month: "Mar", fees: 1025, revenue: 3075 }, // 25% and 75% of 4100
                      { month: "Apr", fees: 962.5, revenue: 2887.5 }, // 25% and 75% of 3850
                      { month: "May", fees: 1062.5, revenue: 3187.5 }, // 25% and 75% of 4250
                    ]}
                    margin={{
                      top: 20,
                      right: 30,
                      left: 0,
                      bottom: 20,
                    }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip formatter={(value) => [`$${value}`, ""]} />
                    <Legend />
                    <Bar dataKey="fees" name={t("statistics.platformFees", "Platform Fees")} fill="#f87171" />
                    <Bar dataKey="revenue" name={t("statistics.netRevenue", "Net Revenue")} fill="#14b8a6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

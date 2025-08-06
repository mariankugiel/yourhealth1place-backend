"use client"

import { useState } from "react"
import { Calendar, momentLocalizer } from "react-big-calendar"
import moment from "moment"
import "react-big-calendar/lib/css/react-big-calendar.css"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
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
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import {
  Clock,
  Plus,
  RefreshCw,
  Video,
  ChevronLeft,
  ChevronRight,
  CalendarIcon,
  Check,
  AlertCircle,
  Ban,
  X,
  Menu,
  CalendarPlus2Icon as CalendarIcon2,
  Clock3,
  User,
  Search,
  Filter,
  ArrowUpDown,
} from "lucide-react"
import Link from "next/link"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { cn } from "@/lib/utils"
import {
  format,
  addDays,
  startOfWeek,
  endOfWeek,
  addWeeks,
  subWeeks,
  isToday,
  isSameDay,
  subMonths,
  isAfter,
  isBefore,
} from "date-fns"
import { Calendar as CalendarComponent } from "@/components/ui/calendar"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { useMediaQuery } from "@/hooks/use-media-query"
import { useLanguage } from "@/lib/language-context"

// Set up the localizer for the calendar
const localizer = momentLocalizer(moment)

// Sample appointment data
const appointments = [
  {
    id: 1,
    title: "Sarah Johnson - Blood Pressure Follow-up",
    start: new Date(2025, 3, 22, 10, 0),
    end: new Date(2025, 3, 22, 10, 30),
    patientId: "sarah-johnson",
  },
  {
    id: 2,
    title: "Michael Chen - Annual Physical",
    start: new Date(2025, 3, 22, 11, 30),
    end: new Date(2025, 3, 22, 12, 15),
    patientId: "michael-chen",
  },
  {
    id: 3,
    title: "Emily Rodriguez - Diabetes Management",
    start: new Date(2025, 3, 22, 14, 15),
    end: new Date(2025, 3, 22, 14, 45),
    patientId: "emily-rodriguez",
  },
  {
    id: 4,
    title: "Robert Williams - Medication Review",
    start: new Date(2025, 3, 23, 9, 0),
    end: new Date(2025, 3, 23, 9, 30),
    patientId: "robert-williams",
  },
  {
    id: 5,
    title: "Lisa Thompson - Chronic Pain Management",
    start: new Date(2025, 3, 23, 13, 0),
    end: new Date(2025, 3, 23, 13, 45),
    patientId: "lisa-thompson",
  },
  // May appointments
  {
    id: 6,
    title: "Sarah Johnson - Hypertension Follow-up",
    start: new Date(2025, 4, 15, 10, 0),
    end: new Date(2025, 4, 15, 10, 30),
    patientId: "sarah-johnson",
  },
  {
    id: 7,
    title: "David Garcia - Cholesterol Check",
    start: new Date(2025, 4, 15, 11, 30),
    end: new Date(2025, 4, 15, 12, 0),
    patientId: "david-garcia",
  },
  {
    id: 8,
    title: "Emily Rodriguez - Diabetes Review",
    start: new Date(2025, 4, 17, 14, 0),
    end: new Date(2025, 4, 17, 14, 30),
    patientId: "emily-rodriguez",
  },
  {
    id: 9,
    title: "Michael Chen - Blood Test Results",
    start: new Date(2025, 4, 20, 9, 30),
    end: new Date(2025, 4, 20, 10, 0),
    patientId: "michael-chen",
  },
  {
    id: 10,
    title: "Lisa Thompson - Pain Management",
    start: new Date(2025, 4, 22, 15, 0),
    end: new Date(2025, 4, 22, 15, 45),
    patientId: "lisa-thompson",
  },
  // June appointments
  {
    id: 11,
    title: "Robert Williams - Arthritis Check",
    start: new Date(2025, 5, 5, 10, 30),
    end: new Date(2025, 5, 5, 11, 0),
    patientId: "robert-williams",
  },
  {
    id: 12,
    title: "Sarah Johnson - Blood Pressure Review",
    start: new Date(2025, 5, 10, 9, 0),
    end: new Date(2025, 5, 10, 9, 30),
    patientId: "sarah-johnson",
  },
  {
    id: 13,
    title: "Emily Rodriguez - Quarterly Check-up",
    start: new Date(2025, 5, 12, 13, 30),
    end: new Date(2025, 5, 12, 14, 15),
    patientId: "emily-rodriguez",
  },
  {
    id: 14,
    title: "Michael Chen - Vaccination",
    start: new Date(2025, 5, 18, 11, 0),
    end: new Date(2025, 5, 18, 11, 30),
    patientId: "michael-chen",
  },
  {
    id: 15,
    title: "David Garcia - Medication Adjustment",
    start: new Date(2025, 5, 25, 14, 30),
    end: new Date(2025, 5, 25, 15, 0),
    patientId: "david-garcia",
  },
  // Past appointments (for the previous appointments section)
  {
    id: 16,
    title: "Sarah Johnson - Initial Consultation",
    start: new Date(2025, 2, 10, 9, 0),
    end: new Date(2025, 2, 10, 10, 0),
    patientId: "sarah-johnson",
    status: "completed",
    notes: "Patient presented with high blood pressure. Prescribed medication and lifestyle changes.",
  },
  {
    id: 17,
    title: "Michael Chen - Flu Symptoms",
    start: new Date(2025, 2, 12, 14, 0),
    end: new Date(2025, 2, 12, 14, 30),
    patientId: "michael-chen",
    status: "completed",
    notes: "Diagnosed with seasonal flu. Recommended rest and fluids.",
  },
  {
    id: 18,
    title: "Emily Rodriguez - Diabetes Initial Assessment",
    start: new Date(2025, 2, 15, 11, 0),
    end: new Date(2025, 2, 15, 12, 0),
    patientId: "emily-rodriguez",
    status: "completed",
    notes: "Diagnosed with Type 2 Diabetes. Started on medication and dietary plan.",
  },
  {
    id: 19,
    title: "Robert Williams - Back Pain",
    start: new Date(2025, 2, 18, 10, 30),
    end: new Date(2025, 2, 18, 11, 0),
    patientId: "robert-williams",
    status: "completed",
    notes: "Chronic lower back pain. Referred to physical therapy.",
  },
  {
    id: 20,
    title: "Lisa Thompson - Migraine Follow-up",
    start: new Date(2025, 2, 20, 15, 30),
    end: new Date(2025, 2, 20, 16, 0),
    patientId: "lisa-thompson",
    status: "completed",
    notes: "Migraines have reduced in frequency. Continuing current medication.",
  },
  {
    id: 21,
    title: "David Garcia - Annual Check-up",
    start: new Date(2025, 2, 22, 9, 30),
    end: new Date(2025, 2, 22, 10, 30),
    patientId: "david-garcia",
    status: "completed",
    notes: "All vitals normal. Recommended standard screenings for age.",
  },
  {
    id: 22,
    title: "Sarah Johnson - Blood Pressure Check",
    start: new Date(2025, 2, 25, 14, 0),
    end: new Date(2025, 2, 25, 14, 30),
    patientId: "sarah-johnson",
    status: "completed",
    notes: "Blood pressure improved. Continuing current treatment plan.",
  },
  {
    id: 23,
    title: "Michael Chen - Follow-up",
    start: new Date(2025, 2, 28, 11, 30),
    end: new Date(2025, 2, 28, 12, 0),
    patientId: "michael-chen",
    status: "completed",
    notes: "Fully recovered from flu. No further treatment needed.",
  },
  {
    id: 24,
    title: "Emily Rodriguez - Diabetes Education",
    start: new Date(2025, 3, 2, 10, 0),
    end: new Date(2025, 3, 2, 11, 0),
    patientId: "emily-rodriguez",
    status: "completed",
    notes: "Provided education on glucose monitoring and insulin administration.",
  },
  {
    id: 25,
    title: "Robert Williams - Physical Therapy Follow-up",
    start: new Date(2025, 3, 5, 9, 0),
    end: new Date(2025, 3, 5, 9, 30),
    patientId: "robert-williams",
    status: "completed",
    notes: "Reporting improvement with physical therapy. Continuing exercises.",
  },
]

// Sample availability data
const availabilityHours = [
  { day: "Monday", start: "09:00", end: "17:00", active: true },
  { day: "Tuesday", start: "09:00", end: "17:00", active: true },
  { day: "Wednesday", start: "09:00", end: "17:00", active: true },
  { day: "Thursday", start: "09:00", end: "17:00", active: true },
  { day: "Friday", start: "09:00", end: "15:00", active: true },
  { day: "Saturday", start: "10:00", end: "14:00", active: false },
  { day: "Sunday", start: "00:00", end: "00:00", active: false },
]

// Sample blocked periods
const blockedPeriods = [
  {
    id: 1,
    title: "Summer Vacation",
    start: new Date(2025, 6, 15),
    end: new Date(2025, 6, 30),
    allDay: true,
    type: "vacation",
  },
  {
    id: 2,
    title: "Conference",
    start: new Date(2025, 4, 5),
    end: new Date(2025, 4, 7),
    allDay: true,
    type: "conference",
  },
  {
    id: 3,
    title: "Personal Day",
    start: new Date(2025, 3, 25),
    end: new Date(2025, 3, 25),
    allDay: true,
    type: "personal",
  },
]

// Sample specific date availability changes
const specificDateAvailability = [
  {
    id: 1,
    date: new Date(2025, 4, 2), // May 2, 2025
    slots: [{ start: "15:00", end: "16:30", available: true }],
    note: "Only available in the afternoon due to morning meeting",
  },
  {
    id: 2,
    date: new Date(2025, 3, 30), // April 30, 2025
    slots: [
      { start: "09:00", end: "12:00", available: true },
      { start: "14:00", end: "17:00", available: true },
    ],
    note: "Lunch meeting from 12-2pm",
  },
]

// Helper function to get appointments for a specific date
const getAppointmentsForDate = (date: Date) => {
  return appointments
    .filter(
      (apt) =>
        apt.start.getFullYear() === date.getFullYear() &&
        apt.start.getMonth() === date.getMonth() &&
        apt.start.getDate() === date.getDate(),
    )
    .sort((a, b) => a.start.getTime() - b.start.getTime())
}

// Helper function to get blocked periods for a specific date
const getBlockedPeriodsForDate = (date: Date) => {
  return blockedPeriods.filter((period) => date >= period.start && date <= period.end)
}

// Mobile Calendar Day Component
const MobileCalendarDay = ({ date, isSelected, onClick }: { date: Date; isSelected: boolean; onClick: () => void }) => {
  const dayNumber = date.getDate()
  const isCurrentDay = isToday(date)
  const hasAppointments = getAppointmentsForDate(date).length > 0
  const isBlocked = getBlockedPeriodsForDate(date).length > 0

  return (
    <div
      onClick={onClick}
      className={cn(
        "flex flex-col items-center justify-center w-10 h-10 rounded-full cursor-pointer",
        isSelected ? "bg-teal-600 text-white" : "",
        isCurrentDay && !isSelected ? "border border-teal-600" : "",
        isBlocked && !isSelected ? "bg-red-100 dark:bg-red-900/20" : "",
      )}
    >
      <span className={cn("text-sm font-medium", isCurrentDay && !isSelected ? "text-teal-600" : "")}>{dayNumber}</span>
      {hasAppointments && !isSelected && <div className="w-1 h-1 bg-teal-600 rounded-full mt-0.5"></div>}
    </div>
  )
}

// Mobile Calendar Week Component
const MobileCalendarWeek = ({
  startDate,
  selectedDate,
  onSelectDate,
}: {
  startDate: Date
  selectedDate: Date
  onSelectDate: (date: Date) => void
}) => {
  const days = []
  const weekStart = startOfWeek(startDate, { weekStartsOn: 1 }) // Start on Monday

  for (let i = 0; i < 7; i++) {
    const day = addDays(weekStart, i)
    days.push(day)
  }

  return (
    <div className="flex justify-between items-center py-2">
      {days.map((day, index) => (
        <MobileCalendarDay
          key={index}
          date={day}
          isSelected={isSameDay(day, selectedDate)}
          onClick={() => onSelectDate(day)}
        />
      ))}
    </div>
  )
}

// Mobile Calendar View Component
const MobileCalendarView = ({
  selectedDate,
  onSelectDate,
}: {
  selectedDate: Date
  onSelectDate: (date: Date) => void
}) => {
  const { t } = useLanguage()
  const [currentWeekStart, setCurrentWeekStart] = useState(startOfWeek(selectedDate, { weekStartsOn: 1 }))

  const goToPreviousWeek = () => {
    setCurrentWeekStart(subWeeks(currentWeekStart, 1))
  }

  const goToNextWeek = () => {
    setCurrentWeekStart(addWeeks(currentWeekStart, 1))
  }

  const goToToday = () => {
    const today = new Date()
    setCurrentWeekStart(startOfWeek(today, { weekStartsOn: 1 }))
    onSelectDate(today)
  }

  const weekEnd = endOfWeek(currentWeekStart, { weekStartsOn: 1 })
  const monthYear =
    currentWeekStart.getMonth() === weekEnd.getMonth()
      ? format(currentWeekStart, "MMMM yyyy")
      : `${format(currentWeekStart, "MMM")} - ${format(weekEnd, "MMM")} ${format(currentWeekStart, "yyyy")}`

  const dayNames = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

  const appointmentsForSelectedDate = getAppointmentsForDate(selectedDate)
  const blockedPeriodsForSelectedDate = getBlockedPeriodsForDate(selectedDate)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={goToPreviousWeek}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <div className="text-sm font-medium">{monthYear}</div>
          <Button variant="ghost" size="icon" onClick={goToNextWeek}>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
        <Button variant="outline" size="sm" onClick={goToToday}>
          {t("calendar.today", "Today")}
        </Button>
      </div>

      <div className="flex justify-between items-center text-xs text-muted-foreground">
        {dayNames.map((day, index) => (
          <div key={index} className="w-10 text-center">
            {day}
          </div>
        ))}
      </div>

      <MobileCalendarWeek startDate={currentWeekStart} selectedDate={selectedDate} onSelectDate={onSelectDate} />

      <div className="pt-2 border-t">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">{format(selectedDate, "EEEE, MMMM d, yyyy")}</h3>
          {isToday(selectedDate) && <Badge>{t("calendar.today", "Today")}</Badge>}
        </div>

        {blockedPeriodsForSelectedDate.length > 0 && (
          <div className="mt-2">
            {blockedPeriodsForSelectedDate.map((period) => (
              <div key={period.id} className="flex items-center gap-2 text-red-600 dark:text-red-400 mb-1">
                <Ban className="h-4 w-4" />
                <span className="text-sm">{period.title}</span>
              </div>
            ))}
          </div>
        )}

        <div className="mt-4 space-y-3">
          {appointmentsForSelectedDate.length > 0 ? (
            appointmentsForSelectedDate.map((apt) => (
              <Link href={`/professional/appointments/${apt.id}`} key={apt.id}>
                <div className="rounded-lg border p-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Clock3 className="h-4 w-4 text-muted-foreground" />
                      <p className="text-sm text-muted-foreground">
                        {format(apt.start, "h:mm a")} - {format(apt.end, "h:mm a")}
                      </p>
                    </div>
                  </div>
                  <div className="mt-1">
                    <div className="flex items-center gap-2">
                      <User className="h-4 w-4 text-teal-600" />
                      <p className="font-medium">{apt.title.split(" - ")[0]}</p>
                    </div>
                    <p className="text-sm text-muted-foreground ml-6">{apt.title.split(" - ")[1]}</p>
                  </div>
                  <div className="mt-2 flex items-center">
                    <Video className="h-4 w-4 mr-1 text-teal-600" />
                    <span className="text-xs text-teal-600">{t("consultationTypes.video", "Video Consultation")}</span>
                  </div>
                </div>
              </Link>
            ))
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <CalendarIcon2 className="h-12 w-12 mx-auto mb-2 opacity-20" />
              <p>{t("calendar.noAppointments", "No appointments scheduled for this day")}</p>
              <Button variant="outline" size="sm" className="mt-4" onClick={() => {}}>
                <Plus className="h-4 w-4 mr-2" />
                {t("calendar.addAppointment", "Add Appointment")}
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function CalendarClientPage() {
  const { t } = useLanguage()
  const [view, setView] = useState("month")
  const [date, setDate] = useState(new Date())
  const [syncStatus, setSyncStatus] = useState(t("calendar.connectedToGoogle", "Connected to Google Calendar"))
  const [showAvailabilityDialog, setShowAvailabilityDialog] = useState(false)
  const [showNewAppointmentDialog, setShowNewAppointmentDialog] = useState(false)
  const [showBlockTimeDialog, setShowBlockTimeDialog] = useState(false)
  const [showSpecificDateDialog, setShowSpecificDateDialog] = useState(false)
  const [availabilityTab, setAvailabilityTab] = useState("regular")
  const [showCalendarControls, setShowCalendarControls] = useState(false)
  const [showPreviousAppointmentsDialog, setShowPreviousAppointmentsDialog] = useState(false)

  // State for block time dialog
  const [blockTitle, setBlockTitle] = useState("")
  const [blockStartDate, setBlockStartDate] = useState<Date | undefined>(new Date())
  const [blockEndDate, setBlockEndDate] = useState<Date | undefined>(new Date())
  const [blockType, setBlockType] = useState("vacation")
  const [blockNote, setBlockNote] = useState("")

  // State for specific date availability
  const [specificDate, setSpecificDate] = useState<Date | undefined>(new Date())
  const [specificDateSlots, setSpecificDateSlots] = useState([{ id: 1, start: "09:00", end: "12:00" }])
  const [specificDateNote, setSpecificDateNote] = useState("")

  // State for previous appointments filtering
  const [searchQuery, setSearchQuery] = useState("")
  const [dateRangeStart, setDateRangeStart] = useState<Date | undefined>(subMonths(new Date(), 3))
  const [dateRangeEnd, setDateRangeEnd] = useState<Date | undefined>(new Date())
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc")
  const [currentPage, setCurrentPage] = useState(1)
  const appointmentsPerPage = 10

  // Check if the screen is mobile
  const isMobile = useMediaQuery("(max-width: 768px)")

  const handleSelectEvent = (event: any) => {
    window.location.href = `/professional/appointments/${event.id}`
  }

  const handleSyncCalendar = () => {
    setSyncStatus(t("calendar.syncing", "Syncing..."))
    setTimeout(() => {
      setSyncStatus(t("calendar.connectedToGoogle", "Connected to Google Calendar"))
    }, 1500)
  }

  const addSpecificDateSlot = () => {
    setSpecificDateSlots([...specificDateSlots, { id: specificDateSlots.length + 1, start: "09:00", end: "10:00" }])
  }

  const removeSpecificDateSlot = (id: number) => {
    setSpecificDateSlots(specificDateSlots.filter((slot) => slot.id !== id))
  }

  const updateSpecificDateSlot = (id: number, field: string, value: string) => {
    setSpecificDateSlots(specificDateSlots.map((slot) => (slot.id === id ? { ...slot, [field]: value } : slot)))
  }

  // Custom event component to avoid external resource loading
  const customEventComponent = ({ event }: { event: any }) => (
    <div className="p-1">
      <div className="text-xs font-medium truncate">{event.title}</div>
    </div>
  )

  // Filter previous appointments based on search and date range
  const filteredPreviousAppointments = appointments
    .filter((apt) => {
      const isPastAppointment = apt.start < new Date()
      const matchesSearch = searchQuery ? apt.title.toLowerCase().includes(searchQuery.toLowerCase()) : true
      const isInDateRange =
        (!dateRangeStart || isAfter(apt.start, dateRangeStart)) && (!dateRangeEnd || isBefore(apt.start, dateRangeEnd))

      return isPastAppointment && matchesSearch && isInDateRange
    })
    .sort((a, b) => {
      const comparison =
        sortDirection === "asc" ? a.start.getTime() - b.start.getTime() : b.start.getTime() - a.start.getTime()
      return comparison
    })

  // Pagination for previous appointments
  const totalPages = Math.ceil(filteredPreviousAppointments.length / appointmentsPerPage)
  const paginatedAppointments = filteredPreviousAppointments.slice(
    (currentPage - 1) * appointmentsPerPage,
    currentPage * appointmentsPerPage,
  )

  const toggleSortDirection = () => {
    setSortDirection(sortDirection === "asc" ? "desc" : "asc")
  }

  return (
    <div className="container py-4 md:py-6 px-2 md:px-6">
      <div className="mb-4 md:mb-6 flex flex-col gap-2 md:gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-teal-700 dark:text-teal-300">
            {t("calendar.title", "Calendar")}
          </h1>
          <p className="text-sm md:text-base text-muted-foreground">
            {t("calendar.subtitle", "Manage your appointments and availability")}
          </p>
        </div>

        {/* Mobile action buttons */}
        <div className="flex gap-2 md:hidden">
          <Button variant="outline" size="sm" onClick={() => setShowCalendarControls(!showCalendarControls)}>
            <Menu className="h-4 w-4 mr-2" />
            {t("calendar.controls", "Controls")}
          </Button>
          <Button size="sm" onClick={() => setShowNewAppointmentDialog(true)}>
            <Plus className="h-4 w-4 mr-1" />
            {t("calendar.new", "New")}
          </Button>
        </div>

        {/* Desktop action buttons */}
        <div className="hidden md:flex gap-2">
          <Dialog open={showAvailabilityDialog} onOpenChange={setShowAvailabilityDialog}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Clock className="mr-2 h-4 w-4" />
                {t("calendar.setAvailability", "Set Availability")}
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>{t("calendar.setYourAvailability", "Set Your Availability")}</DialogTitle>
                <DialogDescription>
                  {t("calendar.configureAvailability", "Configure your available hours for appointments.")}
                </DialogDescription>
              </DialogHeader>

              <Tabs defaultValue="regular" value={availabilityTab} onValueChange={setAvailabilityTab}>
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="regular">{t("calendar.regularHours", "Regular Hours")}</TabsTrigger>
                  <TabsTrigger value="blocked">{t("calendar.blockedPeriods", "Blocked Periods")}</TabsTrigger>
                  <TabsTrigger value="specific">{t("calendar.specificDates", "Specific Dates")}</TabsTrigger>
                </TabsList>

                <TabsContent value="regular" className="space-y-4 py-4">
                  {availabilityHours.map((item, index) => (
                    <div key={index} className="grid grid-cols-5 items-center gap-4">
                      <Label className="text-right">{t(`calendar.days.${item.day.toLowerCase()}`, item.day)}</Label>
                      <Input id={`start-${item.day}`} defaultValue={item.start} className="col-span-1" type="time" />
                      <Input id={`end-${item.day}`} defaultValue={item.end} className="col-span-1" type="time" />
                      <Switch defaultChecked={item.active} id={`active-${item.day}`} />
                      <span className="text-sm text-muted-foreground">
                        {item.active ? t("calendar.available", "Available") : t("calendar.unavailable", "Unavailable")}
                      </span>
                    </div>
                  ))}
                </TabsContent>

                <TabsContent value="blocked" className="py-4">
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <h3 className="text-lg font-medium">{t("calendar.blockedPeriods", "Blocked Periods")}</h3>
                      <Button size="sm" onClick={() => setShowBlockTimeDialog(true)}>
                        <Ban className="mr-2 h-4 w-4" />
                        {t("calendar.blockTime", "Block Time")}
                      </Button>
                    </div>

                    {blockedPeriods.length > 0 ? (
                      <div className="space-y-2">
                        {blockedPeriods.map((period) => (
                          <div key={period.id} className="flex items-center justify-between border p-3 rounded-md">
                            <div>
                              <p className="font-medium">{period.title}</p>
                              <p className="text-sm text-muted-foreground">
                                {format(period.start, "MMM d, yyyy")} - {format(period.end, "MMM d, yyyy")}
                              </p>
                            </div>
                            <Badge
                              variant={
                                period.type === "vacation"
                                  ? "default"
                                  : period.type === "conference"
                                    ? "secondary"
                                    : "outline"
                              }
                            >
                              {t(
                                `calendar.blockTypes.${period.type}`,
                                period.type.charAt(0).toUpperCase() + period.type.slice(1),
                              )}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-center text-muted-foreground py-4">
                        {t("calendar.noBlockedPeriods", "No blocked periods set")}
                      </p>
                    )}
                  </div>
                </TabsContent>

                <TabsContent value="specific" className="py-4">
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <h3 className="text-lg font-medium">
                        {t("calendar.specificDateAvailability", "Specific Date Availability")}
                      </h3>
                      <Button size="sm" onClick={() => setShowSpecificDateDialog(true)}>
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {t("calendar.addDate", "Add Date")}
                      </Button>
                    </div>

                    {specificDateAvailability.length > 0 ? (
                      <div className="space-y-2">
                        {specificDateAvailability.map((item) => (
                          <div key={item.id} className="border p-3 rounded-md">
                            <div className="flex items-center justify-between">
                              <p className="font-medium">{format(item.date, "MMMM d, yyyy")}</p>
                              <Button variant="ghost" size="sm">
                                {t("calendar.edit", "Edit")}
                              </Button>
                            </div>
                            <div className="mt-2 space-y-1">
                              {item.slots.map((slot, idx) => (
                                <div key={idx} className="flex items-center text-sm">
                                  <Check className="h-4 w-4 mr-2 text-green-600" />
                                  <span>
                                    {t("calendar.availableTime", "Available")} {slot.start} - {slot.end}
                                  </span>
                                </div>
                              ))}
                            </div>
                            {item.note && <p className="text-sm text-muted-foreground mt-2">{item.note}</p>}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-center text-muted-foreground py-4">
                        {t("calendar.noSpecificDateAvailability", "No specific date availability set")}
                      </p>
                    )}
                  </div>
                </TabsContent>
              </Tabs>

              <DialogFooter>
                <Button type="submit" onClick={() => setShowAvailabilityDialog(false)}>
                  {t("calendar.saveChanges", "Save changes")}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Dialog open={showNewAppointmentDialog} onOpenChange={setShowNewAppointmentDialog}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                {t("calendar.newAppointment", "New Appointment")}
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px] max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>{t("calendar.scheduleNewAppointment", "Schedule New Appointment")}</DialogTitle>
                <DialogDescription>
                  {t("calendar.createNewAppointment", "Create a new appointment with a patient.")}
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="patient" className="text-right">
                    {t("calendar.patient", "Patient")}
                  </Label>
                  <Select>
                    <SelectTrigger className="col-span-3">
                      <SelectValue placeholder={t("calendar.selectPatient", "Select patient")} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="sarah-johnson">Sarah Johnson</SelectItem>
                      <SelectItem value="michael-chen">Michael Chen</SelectItem>
                      <SelectItem value="emily-rodriguez">Emily Rodriguez</SelectItem>
                      <SelectItem value="robert-williams">Robert Williams</SelectItem>
                      <SelectItem value="lisa-thompson">Lisa Thompson</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="date" className="text-right">
                    {t("calendar.date", "Date")}
                  </Label>
                  <Input id="date" type="date" className="col-span-3" />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="time" className="text-right">
                    {t("calendar.time", "Time")}
                  </Label>
                  <Input id="time" type="time" className="col-span-3" />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="duration" className="text-right">
                    {t("calendar.duration", "Duration")}
                  </Label>
                  <Select defaultValue="30">
                    <SelectTrigger className="col-span-3">
                      <SelectValue placeholder={t("calendar.selectDuration", "Select duration")} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="15">{t("calendar.minutes", "15 minutes")}</SelectItem>
                      <SelectItem value="30">{t("calendar.minutes", "30 minutes")}</SelectItem>
                      <SelectItem value="45">{t("calendar.minutes", "45 minutes")}</SelectItem>
                      <SelectItem value="60">{t("calendar.minutes", "60 minutes")}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="type" className="text-right">
                    {t("calendar.type", "Type")}
                  </Label>
                  <Select defaultValue="follow-up">
                    <SelectTrigger className="col-span-3">
                      <SelectValue placeholder={t("calendar.selectType", "Select type")} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="initial">
                        {t("calendar.appointmentTypes.initial", "Initial Consultation")}
                      </SelectItem>
                      <SelectItem value="follow-up">{t("calendar.appointmentTypes.followUp", "Follow-up")}</SelectItem>
                      <SelectItem value="annual">{t("calendar.appointmentTypes.annual", "Annual Physical")}</SelectItem>
                      <SelectItem value="urgent">{t("calendar.appointmentTypes.urgent", "Urgent Care")}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button type="submit" onClick={() => setShowNewAppointmentDialog(false)}>
                  {t("calendar.schedule", "Schedule")}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Mobile calendar controls */}
      {showCalendarControls && (
        <div className="mb-4 p-3 border rounded-lg bg-background md:hidden">
          <div className="flex flex-col gap-3">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-medium">{t("calendar.calendarControls", "Calendar Controls")}</h3>
              <Button variant="ghost" size="sm" onClick={() => setShowCalendarControls(false)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Button variant="outline" size="sm" onClick={() => setShowAvailabilityDialog(true)}>
                <Clock className="mr-2 h-4 w-4" />
                {t("calendar.setAvailability", "Set Availability")}
              </Button>
              <Button variant="outline" size="sm" onClick={handleSyncCalendar}>
                <RefreshCw className="mr-2 h-4 w-4" />
                {t("calendar.syncCalendar", "Sync Calendar")}
              </Button>
            </div>
            <div className="flex items-center justify-between">
              <Badge
                variant={syncStatus.includes("Connected") ? "outline" : "secondary"}
                className="flex items-center gap-1"
              >
                {syncStatus.includes("Connected") ? <Check className="h-3 w-3" /> : <AlertCircle className="h-3 w-3" />}
                <span className="text-xs">{syncStatus}</span>
              </Badge>
            </div>
          </div>
        </div>
      )}

      <div className="grid gap-4 md:gap-6 md:grid-cols-4">
        <div className="md:col-span-3">
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>{t("calendar.appointments", "Appointments")}</CardTitle>
                  <CardDescription>{t("calendar.viewAndManage", "View and manage your schedule")}</CardDescription>
                </div>
                <div className="hidden md:flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => setDate(new Date(date.getFullYear(), date.getMonth() - 1, date.getDate()))}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <div className="text-sm font-medium">
                      {date.toLocaleDateString("en-US", { month: "long", year: "numeric" })}
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => setDate(new Date(date.getFullYear(), date.getMonth() + 1, date.getDate()))}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                  <Select
                    value={view}
                    onValueChange={(value) => {
                      setView(value)
                    }}
                  >
                    <SelectTrigger className="w-[120px]">
                      <SelectValue placeholder={t("calendar.view", "View")} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="month">{t("calendar.views.month", "Month")}</SelectItem>
                      <SelectItem value="week">{t("calendar.views.week", "Week")}</SelectItem>
                      <SelectItem value="day">{t("calendar.views.day", "Day")}</SelectItem>
                      <SelectItem value="agenda">{t("calendar.views.agenda", "Agenda")}</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button variant="outline" size="icon" onClick={handleSyncCalendar}>
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {isMobile ? (
                <MobileCalendarView selectedDate={date} onSelectDate={setDate} />
              ) : (
                <div className="h-[500px] md:h-[600px] overflow-x-auto">
                  <Calendar
                    localizer={localizer}
                    events={[...appointments, ...blockedPeriods]}
                    startAccessor="start"
                    endAccessor="end"
                    style={{ height: "100%" }}
                    view={view as any}
                    onView={(view) => setView(view)}
                    date={date}
                    onNavigate={(date) => setDate(date)}
                    onSelectEvent={handleSelectEvent}
                    components={{
                      event: customEventComponent,
                    }}
                    eventPropGetter={(event) => {
                      if (!event) return {}

                      if (event.type === "vacation") {
                        return {
                          style: {
                            backgroundColor: "#f87171",
                            borderColor: "#ef4444",
                          },
                        }
                      } else if (event.type === "conference") {
                        return {
                          style: {
                            backgroundColor: "#60a5fa",
                            borderColor: "#3b82f6",
                          },
                        }
                      } else if (event.type === "personal") {
                        return {
                          style: {
                            backgroundColor: "#d1d5db",
                            borderColor: "#9ca3af",
                          },
                        }
                      }
                      return {}
                    }}
                  />
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="order-first md:order-none mb-4 md:mb-0">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>{t("calendar.todaysAppointments", "Today's Appointments")}</CardTitle>
                  <CardDescription>April 22, 2025</CardDescription>
                </div>
                <Badge
                  variant={syncStatus.includes("Connected") ? "outline" : "secondary"}
                  className="flex items-center gap-1"
                >
                  {syncStatus.includes("Connected") ? (
                    <Check className="h-3 w-3" />
                  ) : (
                    <AlertCircle className="h-3 w-3" />
                  )}
                  <span className="text-xs">{syncStatus}</span>
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {appointments
                  .filter((apt) => apt.start.toDateString() === new Date(2025, 3, 22).toDateString())
                  .map((apt) => (
                    <Link href={`/professional/appointments/${apt.id}`} key={apt.id}>
                      <div className="rounded-lg border p-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                        <div className="flex items-center justify-between">
                          <p className="font-medium">{apt.title.split(" - ")[0]}</p>
                          <p className="text-sm text-muted-foreground">
                            {apt.start.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          </p>
                        </div>
                        <p className="text-sm text-muted-foreground">{apt.title.split(" - ")[1]}</p>
                        <div className="mt-2 flex items-center">
                          <Video className="h-4 w-4 mr-1 text-teal-600" />
                          <span className="text-xs text-teal-600">
                            {t("consultationTypes.video", "Video Consultation")}
                          </span>
                        </div>
                      </div>
                    </Link>
                  ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="mt-6">
        <Card>
          <CardHeader>
            <CardTitle>{t("calendar.previousAppointments", "Previous Appointments")}</CardTitle>
            <CardDescription>{t("calendar.recentHistory", "Recent appointment history")}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {appointments
                .filter((apt) => new Date(apt.start) < new Date())
                .sort((a, b) => new Date(b.start).getTime() - new Date(a.start).getTime())
                .slice(0, 5)
                .map((apt) => (
                  <Link href={`/professional/appointments/${apt.id}`} key={apt.id}>
                    <div className="rounded-lg border p-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-teal-600" />
                          <p className="font-medium">{apt.title.split(" - ")[0]}</p>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {format(apt.start, "MMM d, yyyy")} • {format(apt.start, "h:mm a")}
                        </p>
                      </div>
                      <p className="text-sm text-muted-foreground ml-6">{apt.title.split(" - ")[1]}</p>
                    </div>
                  </Link>
                ))}

              <div className="flex justify-center">
                <Dialog open={showPreviousAppointmentsDialog} onOpenChange={setShowPreviousAppointmentsDialog}>
                  <DialogTrigger asChild>
                    <Button variant="outline" size="sm">
                      {t("calendar.viewAllAppointments", "View All Appointments")}
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-[800px] max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                      <DialogTitle>{t("calendar.previousAppointments", "Previous Appointments")}</DialogTitle>
                      <DialogDescription>
                        {t("calendar.viewPastAppointments", "View and search your past appointments")}
                      </DialogDescription>
                    </DialogHeader>

                    <div className="py-4 space-y-4">
                      {/* Search and filter controls */}
                      <div className="flex flex-col md:flex-row gap-4">
                        <div className="relative flex-1">
                          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                          <Input
                            placeholder={t("calendar.searchAppointments", "Search appointments...")}
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-8"
                          />
                        </div>

                        <div className="flex gap-2">
                          <Popover>
                            <PopoverTrigger asChild>
                              <Button variant="outline" size="sm" className="flex gap-2 items-center">
                                <Filter className="h-4 w-4" />
                                <span>{t("calendar.dateRange", "Date Range")}</span>
                              </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-auto p-4" align="end">
                              <div className="space-y-2">
                                <h4 className="font-medium">{t("calendar.selectDateRange", "Select Date Range")}</h4>
                                <div className="grid gap-2">
                                  <div className="grid gap-1">
                                    <Label htmlFor="from-date">{t("calendar.from", "From")}</Label>
                                    <Popover>
                                      <PopoverTrigger asChild>
                                        <Button
                                          id="from-date"
                                          variant={"outline"}
                                          className={cn(
                                            "w-full justify-start text-left font-normal",
                                            !dateRangeStart && "text-muted-foreground",
                                          )}
                                        >
                                          <CalendarIcon className="mr-2 h-4 w-4" />
                                          {dateRangeStart ? (
                                            format(dateRangeStart, "PPP")
                                          ) : (
                                            <span>{t("calendar.pickDate", "Pick a date")}</span>
                                          )}
                                        </Button>
                                      </PopoverTrigger>
                                      <PopoverContent className="w-auto p-0" align="start">
                                        <CalendarComponent
                                          mode="single"
                                          selected={dateRangeStart}
                                          onSelect={setDateRangeStart}
                                          initialFocus
                                        />
                                      </PopoverContent>
                                    </Popover>
                                  </div>
                                  <div className="grid gap-1">
                                    <Label htmlFor="to-date">{t("calendar.to", "To")}</Label>
                                    <Popover>
                                      <PopoverTrigger asChild>
                                        <Button
                                          id="to-date"
                                          variant={"outline"}
                                          className={cn(
                                            "w-full justify-start text-left font-normal",
                                            !dateRangeEnd && "text-muted-foreground",
                                          )}
                                        >
                                          <CalendarIcon className="mr-2 h-4 w-4" />
                                          {dateRangeEnd ? (
                                            format(dateRangeEnd, "PPP")
                                          ) : (
                                            <span>{t("calendar.pickDate", "Pick a date")}</span>
                                          )}
                                        </Button>
                                      </PopoverTrigger>
                                      <PopoverContent className="w-auto p-0" align="start">
                                        <CalendarComponent
                                          mode="single"
                                          selected={dateRangeEnd}
                                          onSelect={setDateRangeEnd}
                                          initialFocus
                                        />
                                      </PopoverContent>
                                    </Popover>
                                  </div>
                                </div>
                                <div className="flex justify-end pt-2">
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => {
                                      setDateRangeStart(subMonths(new Date(), 3))
                                      setDateRangeEnd(new Date())
                                    }}
                                  >
                                    {t("calendar.reset", "Reset")}
                                  </Button>
                                </div>
                              </div>
                            </PopoverContent>
                          </Popover>

                          <Button
                            variant="outline"
                            size="sm"
                            onClick={toggleSortDirection}
                            className="flex gap-2 items-center"
                          >
                            <ArrowUpDown className="h-4 w-4" />
                            <span>
                              {sortDirection === "desc"
                                ? t("calendar.sortNewestFirst", "Newest First")
                                : t("calendar.sortOldestFirst", "Oldest First")}
                            </span>
                          </Button>
                        </div>
                      </div>

                      {/* Appointments list */}
                      <div className="space-y-4 mt-4">
                        {paginatedAppointments.length > 0 ? (
                          paginatedAppointments.map((apt) => (
                            <Link href={`/professional/appointments/${apt.id}`} key={apt.id}>
                              <div className="rounded-lg border p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                                  <div>
                                    <div className="flex items-center gap-2">
                                      <User className="h-4 w-4 text-teal-600" />
                                      <p className="font-medium">{apt.title.split(" - ")[0]}</p>
                                    </div>
                                    <p className="text-sm text-muted-foreground ml-6">{apt.title.split(" - ")[1]}</p>
                                  </div>
                                  <div className="flex flex-col items-end">
                                    <p className="text-sm font-medium">{format(apt.start, "EEEE, MMMM d, yyyy")}</p>
                                    <p className="text-sm text-muted-foreground">
                                      {format(apt.start, "h:mm a")} - {format(apt.end, "h:mm a")}
                                    </p>
                                  </div>
                                </div>
                                {apt.notes && (
                                  <div className="mt-2 text-sm text-muted-foreground border-t pt-2">
                                    <p className="line-clamp-1">{apt.notes}</p>
                                  </div>
                                )}
                              </div>
                            </Link>
                          ))
                        ) : (
                          <div className="text-center py-8 text-muted-foreground">
                            <p>{t("calendar.noAppointmentsFound", "No appointments found")}</p>
                          </div>
                        )}
                      </div>

                      {/* Pagination */}
                      {totalPages > 1 && (
                        <div className="flex justify-center items-center gap-2 mt-4">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                            disabled={currentPage === 1}
                          >
                            <ChevronLeft className="h-4 w-4 mr-1" />
                            {t("calendar.previous", "Previous")}
                          </Button>
                          <span className="text-sm text-muted-foreground">
                            {t("calendar.pageOf", "Page {{current}} of {{total}}", {
                              current: currentPage,
                              total: totalPages,
                            })}
                          </span>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                            disabled={currentPage === totalPages}
                          >
                            {t("calendar.next", "Next")}
                            <ChevronRight className="h-4 w-4 ml-1" />
                          </Button>
                        </div>
                      )}
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Block Time Dialog */}
      <Dialog open={showBlockTimeDialog} onOpenChange={setShowBlockTimeDialog}>
        <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{t("calendar.blockTimePeriod", "Block Time Period")}</DialogTitle>
            <DialogDescription>
              {t("calendar.blockTimeDesc", "Block a period of time on your calendar")}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="block-title">{t("calendar.title", "Title")}</Label>
              <Input
                id="block-title"
                placeholder={t("calendar.blockTitlePlaceholder", "e.g., Vacation, Conference, Personal Day")}
                value={blockTitle}
                onChange={(e) => setBlockTitle(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="start-date">{t("calendar.startDate", "Start Date")}</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      id="start-date"
                      variant={"outline"}
                      className={cn(
                        "w-full justify-start text-left font-normal",
                        !blockStartDate && "text-muted-foreground",
                      )}
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {blockStartDate ? (
                        format(blockStartDate, "PPP")
                      ) : (
                        <span>{t("calendar.pickDate", "Pick a date")}</span>
                      )}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <CalendarComponent
                      mode="single"
                      selected={blockStartDate}
                      onSelect={setBlockStartDate}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="end-date">{t("calendar.endDate", "End Date")}</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      id="end-date"
                      variant={"outline"}
                      className={cn(
                        "w-full justify-start text-left font-normal",
                        !blockEndDate && "text-muted-foreground",
                      )}
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {blockEndDate ? (
                        format(blockEndDate, "PPP")
                      ) : (
                        <span>{t("calendar.pickDate", "Pick a date")}</span>
                      )}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <CalendarComponent mode="single" selected={blockEndDate} onSelect={setBlockEndDate} initialFocus />
                  </PopoverContent>
                </Popover>
              </div>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="block-type">{t("calendar.type", "Type")}</Label>
              <Select value={blockType} onValueChange={setBlockType}>
                <SelectTrigger id="block-type">
                  <SelectValue placeholder={t("calendar.selectType", "Select type")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="vacation">{t("calendar.blockTypes.vacation", "Vacation")}</SelectItem>
                  <SelectItem value="conference">{t("calendar.blockTypes.conference", "Conference")}</SelectItem>
                  <SelectItem value="personal">{t("calendar.blockTypes.personal", "Personal")}</SelectItem>
                  <SelectItem value="other">{t("calendar.blockTypes.other", "Other")}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="block-note">{t("calendar.noteOptional", "Note (Optional)")}</Label>
              <Textarea
                id="block-note"
                placeholder={t("calendar.additionalDetails", "Add any additional details")}
                value={blockNote}
                onChange={(e) => setBlockNote(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowBlockTimeDialog(false)}>
              {t("calendar.cancel", "Cancel")}
            </Button>
            <Button
              onClick={() => {
                // In a real app, this would save the blocked period
                setShowBlockTimeDialog(false)
              }}
            >
              {t("calendar.blockTime", "Block Time")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Specific Date Availability Dialog */}
      <Dialog open={showSpecificDateDialog} onOpenChange={setShowSpecificDateDialog}>
        <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{t("calendar.setSpecificDateAvailability", "Set Specific Date Availability")}</DialogTitle>
            <DialogDescription>
              {t("calendar.configureSpecificDate", "Configure your availability for a specific date")}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="specific-date">{t("calendar.date", "Date")}</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    id="specific-date"
                    variant={"outline"}
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !specificDate && "text-muted-foreground",
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {specificDate ? format(specificDate, "PPP") : <span>{t("calendar.pickDate", "Pick a date")}</span>}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <CalendarComponent mode="single" selected={specificDate} onSelect={setSpecificDate} initialFocus />
                </PopoverContent>
              </Popover>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium">{t("calendar.availableTimeSlots", "Available Time Slots")}</h3>
                <Button size="sm" variant="outline" onClick={addSpecificDateSlot}>
                  <Plus className="h-4 w-4 mr-1" /> {t("calendar.addSlot", "Add Slot")}
                </Button>
              </div>

              {specificDateSlots.map((slot) => (
                <div key={slot.id} className="flex items-center gap-2">
                  <Input
                    type="time"
                    value={slot.start}
                    onChange={(e) => updateSpecificDateSlot(slot.id, "start", e.target.value)}
                    className="w-[120px]"
                  />
                  <span>{t("calendar.to", "to")}</span>
                  <Input
                    type="time"
                    value={slot.end}
                    onChange={(e) => updateSpecificDateSlot(slot.id, "end", e.target.value)}
                    className="w-[120px]"
                  />
                  <Button variant="ghost" size="icon" onClick={() => removeSpecificDateSlot(slot.id)}>
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>

            <div className="grid gap-2">
              <Label htmlFor="specific-date-note">{t("calendar.noteOptional", "Note (Optional)")}</Label>
              <Textarea
                id="specific-date-note"
                placeholder={t("calendar.additionalDetails", "Add any additional details")}
                value={specificDateNote}
                onChange={(e) => setSpecificDateNote(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSpecificDateDialog(false)}>
              {t("calendar.cancel", "Cancel")}
            </Button>
            <Button
              onClick={() => {
                // In a real app, this would save the specific date availability
                setShowSpecificDateDialog(false)
              }}
            >
              {t("calendar.saveAvailability", "Save Availability")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

"use client"

import { useState, useEffect } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Check, Calendar, CalendarClock, Sun, Moon, Laptop, CreditCard, File, DollarSign, Globe } from "lucide-react"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Slider } from "@/components/ui/slider"
import { Checkbox } from "@/components/ui/checkbox"
import { useLanguage } from "@/lib/language-context"
import type { Language } from "@/lib/translations"
import { toast } from "@/components/ui/use-toast"

export default function SettingsClientPage() {
  // Language context
  const { language, setLanguage, t } = useLanguage()
  const [selectedLanguage, setSelectedLanguage] = useState<Language>(language)

  // Profile states
  const [emailNotifications, setEmailNotifications] = useState(true)
  const [smsNotifications, setSmsNotifications] = useState(true)
  const [appointmentReminders, setAppointmentReminders] = useState(true)
  const [marketingEmails, setMarketingEmails] = useState(false)
  const [googleCalendarSync, setGoogleCalendarSync] = useState(true)
  const [outlookCalendarSync, setOutlookCalendarSync] = useState(false)

  // Insurance selection states
  const [selectedInsuranceProvider, setSelectedInsuranceProvider] = useState("provider-1")
  const [selectedInsurancePlan, setSelectedInsurancePlan] = useState("default-plan")
  const [currentInsuranceDetails, setCurrentInsuranceDetails] = useState({
    provider: "BlueCross BlueShield",
    plan: "PPO Plus",
    status: "Active",
    contractRef: "BC-12345-2025",
  })

  // Preferences states
  const [theme, setTheme] = useState("system")
  const [textSize, setTextSize] = useState(100)
  const [reducedMotion, setReducedMotion] = useState(false)
  const [highContrast, setHighContrast] = useState(false)
  const [timeFormat, setTimeFormat] = useState("12h")
  const [currency, setCurrency] = useState("usd")
  const [measurementSystem, setMeasurementSystem] = useState("metric")

  // Notification preferences states
  const [notificationChannels, setNotificationChannels] = useState({
    appointmentRemindersEmail: true,
    appointmentRemindersSMS: true,
    appointmentRemindersPush: false,
    messagesEmail: true,
    messagesSMS: true,
    messagesPush: false,
    urgentPatientEmail: true,
    urgentPatientSMS: true,
    urgentPatientPush: true,
    alertPatientEmail: true,
    alertPatientSMS: false,
    alertPatientPush: false,
    medicalRecordsEmail: true,
    medicalRecordsSMS: false,
    medicalRecordsPush: false,
  })

  // Update selectedLanguage when language context changes
  useEffect(() => {
    setSelectedLanguage(language)
  }, [language])

  // Function to update notification channels
  const updateNotificationChannel = (key: string, value: boolean) => {
    setNotificationChannels({
      ...notificationChannels,
      [key]: value,
    })
  }

  // Sample pricing data
  const pricingData = [
    { id: 1, type: "Initial Consultation", duration: 60, price: 150 },
    { id: 2, type: "Follow-up Consultation", duration: 30, price: 100 },
    { id: 3, type: "Annual Physical", duration: 90, price: 200 },
    { id: 4, type: "Emergency Consultation", duration: 45, price: 180 },
    { id: 5, type: "Video Consultation", duration: 20, price: 80 },
  ]

  // Sample insurance agreements
  const insuranceData = [
    { id: 1, provider: "BlueCross BlueShield", plan: "PPO Plus", status: "Active", contractRef: "BC-12345-2025" },
    { id: 2, provider: "Aetna", plan: "Select Network", status: "Active", contractRef: "AET-67890-2025" },
    { id: 3, provider: "UnitedHealthcare", plan: "Choice Plus", status: "Active", contractRef: "UHC-24680-2025" },
    { id: 4, provider: "Cigna", plan: "Open Access", status: "Pending", contractRef: "CIG-13579-2025" },
    { id: 5, provider: "Humana", plan: "Gold Plus", status: "Expired", contractRef: "HUM-97531-2024" },
  ]

  // Function to handle insurance provider selection
  const handleInsuranceProviderChange = (providerId: string) => {
    setSelectedInsuranceProvider(providerId)

    // Find the selected insurance provider
    const selectedId = Number.parseInt(providerId.split("-")[1])
    const selectedInsurance = insuranceData.find((insurance) => insurance.id === selectedId)

    if (selectedInsurance) {
      const planValue = selectedInsurance.plan.toLowerCase().replace(/\s+/g, "-")
      setSelectedInsurancePlan(planValue || "default-plan")
      setCurrentInsuranceDetails({
        provider: selectedInsurance.provider,
        plan: selectedInsurance.plan,
        status: selectedInsurance.status,
        contractRef: selectedInsurance.contractRef,
      })
    } else {
      setSelectedInsurancePlan("default-plan")
      setCurrentInsuranceDetails({
        provider: "Select Provider",
        plan: "Select Plan",
        status: "Inactive",
        contractRef: "N/A",
      })
    }
  }

  // Function to handle profile save
  const handleProfileSave = () => {
    // Apply language change if it's different from current
    if (selectedLanguage !== language) {
      setLanguage(selectedLanguage)
      toast({
        title: "Language Updated",
        description: "Your language preference has been saved.",
        duration: 3000,
      })
    } else {
      toast({
        title: "Profile Updated",
        description: "Your profile information has been saved.",
        duration: 3000,
      })
    }
  }

  // Language display names
  const languageNames = {
    en: "English",
    es: "Español",
    pt: "Português",
  }

  return (
    <div className="container py-6 px-4 md:px-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-teal-700 dark:text-teal-300">{t("settings.title") || "Settings"}</h1>
        <p className="text-muted-foreground">
          {t("settings.subtitle") || "Manage your account settings and preferences"}
        </p>
      </div>

      <Tabs defaultValue="profile" className="space-y-4">
        <div className="overflow-x-auto pb-2">
          <TabsList className="inline-flex w-full md:w-auto">
            <TabsTrigger value="profile">{t("settings.tabs.profile") || "Profile"}</TabsTrigger>
            <TabsTrigger value="preferences">{t("settings.tabs.preferences") || "Preferences"}</TabsTrigger>
            <TabsTrigger value="notifications">{t("settings.tabs.notifications") || "Notifications"}</TabsTrigger>
            <TabsTrigger value="calendar">{t("settings.tabs.calendar") || "Calendar"}</TabsTrigger>
            <TabsTrigger value="pricing">{t("settings.tabs.pricing") || "Pricing"}</TabsTrigger>
            <TabsTrigger value="billing">{t("settings.tabs.billing") || "Billing"}</TabsTrigger>
            <TabsTrigger value="insurance">{t("settings.tabs.insurance") || "Insurance"}</TabsTrigger>
            <TabsTrigger value="security">{t("settings.tabs.security") || "Security"}</TabsTrigger>
          </TabsList>
        </div>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t("settings.profile.title") || "Profile Information"}</CardTitle>
              <CardDescription>
                {t("settings.profile.description") || "Update your personal information and professional details"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex flex-col md:flex-row gap-6">
                <div className="flex flex-col items-center gap-4">
                  <Avatar className="h-24 w-24">
                    <AvatarImage
                      src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/DJ-av1INrSBf4G56sN1Hm2ACUUzj7ZsGa.png"
                      alt="Profile"
                    />
                    <AvatarFallback>DR</AvatarFallback>
                  </Avatar>
                  <Button variant="outline" size="sm">
                    {t("settings.profile.changePhoto") || "Change Photo"}
                  </Button>
                </div>
                <div className="flex-1 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="first-name">{t("settings.profile.firstName") || "First Name"}</Label>
                      <Input id="first-name" defaultValue="Dr. Daniel" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="last-name">{t("settings.profile.lastName") || "Last Name"}</Label>
                      <Input id="last-name" defaultValue="Johnson" />
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="email">{t("settings.profile.email") || "Email"}</Label>
                      <Input id="email" type="email" defaultValue="dr.daniel@saluso.com" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="phone">{t("settings.profile.phone") || "Phone Number"}</Label>
                      <Input id="phone" type="tel" defaultValue="+1 (555) 123-4567" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="mobile">{t("settings.profile.mobile") || "Mobile Number"}</Label>
                      <Input id="mobile" type="tel" defaultValue="+1 (555) 987-6543" />
                    </div>
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h3 className="text-lg font-medium flex items-center gap-2">
                  <Globe className="h-5 w-5 text-teal-600" />
                  {t("settings.profile.language") || "Language Preference"}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="language-preference">
                      {t("settings.profile.selectLanguage") || "Select Language"}
                    </Label>
                    <Select value={selectedLanguage} onValueChange={(value) => setSelectedLanguage(value as Language)}>
                      <SelectTrigger id="language-preference" className="w-full">
                        <SelectValue placeholder="Select language" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="en">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">English</span>
                            {language === "en" && <Check className="h-4 w-4 text-green-500" />}
                          </div>
                        </SelectItem>
                        <SelectItem value="es">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">Español</span>
                            {language === "es" && <Check className="h-4 w-4 text-green-500" />}
                          </div>
                        </SelectItem>
                        <SelectItem value="pt">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">Português</span>
                            {language === "pt" && <Check className="h-4 w-4 text-green-500" />}
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-sm text-muted-foreground">
                      {t("settings.profile.languageNote") ||
                        "Changing the language will translate the entire application."}
                    </p>
                  </div>
                  <div className="flex items-center justify-start md:justify-end h-full">
                    <div className="flex items-center gap-2 mt-6">
                      <Badge variant="outline" className="text-sm font-normal">
                        {t("settings.profile.currentLanguage") || "Current"}: {languageNames[language]}
                      </Badge>
                      {selectedLanguage !== language && (
                        <Badge variant="secondary" className="text-sm font-normal">
                          {t("settings.profile.pendingChange") || "Pending"}: {languageNames[selectedLanguage]}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h3 className="text-lg font-medium">
                  {t("settings.profile.professionalInfo") || "Professional Information"}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="specialty">{t("settings.profile.specialty") || "Specialty"}</Label>
                    <Select defaultValue="family-medicine">
                      <SelectTrigger id="specialty">
                        <SelectValue placeholder={t("settings.profile.selectSpecialty") || "Select specialization"} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="family-medicine">
                          {t("settings.profile.specialties.familyMedicine") || "Family Medicine"}
                        </SelectItem>
                        <SelectItem value="internal-medicine">
                          {t("settings.profile.specialties.internalMedicine") || "Internal Medicine"}
                        </SelectItem>
                        <SelectItem value="cardiology">
                          {t("settings.profile.specialties.cardiology") || "Cardiology"}
                        </SelectItem>
                        <SelectItem value="pediatrics">
                          {t("settings.profile.specialties.pediatrics") || "Pediatrics"}
                        </SelectItem>
                        <SelectItem value="psychiatry">
                          {t("settings.profile.specialties.psychiatry") || "Psychiatry"}
                        </SelectItem>
                        <SelectItem value="dermatology">
                          {t("settings.profile.specialties.dermatology") || "Dermatology"}
                        </SelectItem>
                        <SelectItem value="neurology">
                          {t("settings.profile.specialties.neurology") || "Neurology"}
                        </SelectItem>
                        <SelectItem value="orthopedics">
                          {t("settings.profile.specialties.orthopedics") || "Orthopedics"}
                        </SelectItem>
                        <SelectItem value="other">{t("settings.profile.specialties.other") || "Other"}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="years-practice">{t("settings.profile.yearsPractice") || "Years in Practice"}</Label>
                    <Input id="years-practice" type="number" defaultValue="10" min="0" />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="license">{t("settings.profile.licenseNumber") || "License Number"}</Label>
                    <Input id="license" defaultValue="MD12345678" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="license-state">
                      {t("settings.profile.licenseState") || "License State/Region"}
                    </Label>
                    <Input id="license-state" defaultValue="New York" />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="practice-name">
                    {t("settings.profile.practiceName") || "Practice/Hospital Name"}
                  </Label>
                  <Input id="practice-name" defaultValue="City Medical Center" />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="bio">{t("settings.profile.bio") || "Professional Bio"}</Label>
                  <Textarea
                    id="bio"
                    defaultValue="Board-certified family physician with over 10 years of experience in preventive care, chronic disease management, and holistic health approaches."
                    rows={4}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="license-upload">
                    {t("settings.profile.uploadLicense") || "Update Medical License (PDF)"}
                  </Label>
                  <Input id="license-upload" type="file" accept=".pdf" />
                  <p className="text-xs text-muted-foreground mt-1">
                    {t("settings.profile.uploadNote") ||
                      "Please upload a clear copy of your current medical license (Max size: 5MB)"}
                  </p>
                </div>

                <div className="flex items-center space-x-2 mt-4">
                  <Checkbox id="terms" defaultChecked />
                  <Label htmlFor="terms" className="text-sm">
                    {t("settings.profile.confirmAccuracy") ||
                      "I confirm that all the provided information is accurate and up to date"}
                  </Label>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-end">
              <Button onClick={handleProfileSave}>{t("settings.profile.saveChanges") || "Save Changes"}</Button>
            </CardFooter>
          </Card>
        </TabsContent>

        {/* Preferences Tab */}
        <TabsContent value="preferences" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t("settings.preferences.title") || "Theme Preferences"}</CardTitle>
              <CardDescription>
                {t("settings.preferences.description") || "Customize the appearance of the application"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-lg font-medium">{t("settings.preferences.theme") || "Theme"}</h3>
                <RadioGroup defaultValue={theme} onValueChange={setTheme} className="flex flex-wrap gap-4">
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="light" id="theme-light" />
                    <Label htmlFor="theme-light" className="flex items-center space-x-2 cursor-pointer">
                      <Sun className="h-5 w-5" />
                      <span>{t("settings.preferences.light") || "Light"}</span>
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="dark" id="theme-dark" />
                    <Label htmlFor="theme-dark" className="flex items-center space-x-2 cursor-pointer">
                      <Moon className="h-5 w-5" />
                      <span>{t("settings.preferences.dark") || "Dark"}</span>
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="system" id="theme-system" />
                    <Label htmlFor="theme-system" className="flex items-center space-x-2 cursor-pointer">
                      <Laptop className="h-5 w-5" />
                      <span>{t("settings.preferences.system") || "System"}</span>
                    </Label>
                  </div>
                </RadioGroup>
              </div>

              <Separator />

              <div className="space-y-6">
                <h3 className="text-lg font-medium">{t("settings.preferences.accessibility") || "Accessibility"}</h3>
                <div className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <Label htmlFor="text-size">
                        {t("settings.preferences.textSize", { size: textSize }) || `Text Size (${textSize}%)`}
                      </Label>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setTextSize(100)}
                        className="h-7 rounded-sm px-2"
                      >
                        {t("settings.preferences.reset") || "Reset"}
                      </Button>
                    </div>
                    <Slider
                      id="text-size"
                      defaultValue={[textSize]}
                      max={150}
                      min={50}
                      step={10}
                      onValueChange={(value) => setTextSize(value[0])}
                      className="w-full"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label htmlFor="reduced-motion">
                        {t("settings.preferences.reducedMotion") || "Reduced Motion"}
                      </Label>
                      <p className="text-sm text-muted-foreground">
                        {t("settings.preferences.reducedMotionDescription") ||
                          "Minimize animations throughout the application"}
                      </p>
                    </div>
                    <Switch id="reduced-motion" checked={reducedMotion} onCheckedChange={setReducedMotion} />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label htmlFor="high-contrast">{t("settings.preferences.highContrast") || "High Contrast"}</Label>
                      <p className="text-sm text-muted-foreground">
                        {t("settings.preferences.highContrastDescription") || "Increase contrast for better visibility"}
                      </p>
                    </div>
                    <Switch id="high-contrast" checked={highContrast} onCheckedChange={setHighContrast} />
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-6">
                <h3 className="text-lg font-medium">{t("settings.preferences.regionFormat") || "Region & Format"}</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="time-format">{t("settings.preferences.timeFormat") || "Time Format"}</Label>
                    <Select defaultValue={timeFormat} onValueChange={setTimeFormat}>
                      <SelectTrigger id="time-format" className="w-full">
                        <SelectValue placeholder={t("settings.preferences.selectTimeFormat") || "Select time format"} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="12h">
                          {t("settings.preferences.timeFormat12h") || "12-hour (1:30 PM)"}
                        </SelectItem>
                        <SelectItem value="24h">
                          {t("settings.preferences.timeFormat24h") || "24-hour (13:30)"}
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="currency">{t("settings.preferences.currency") || "Currency"}</Label>
                    <Select defaultValue={currency} onValueChange={setCurrency}>
                      <SelectTrigger id="currency" className="w-full">
                        <SelectValue placeholder={t("settings.preferences.selectCurrency") || "Select currency"} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="usd">USD ($)</SelectItem>
                        <SelectItem value="eur">EUR (€)</SelectItem>
                        <SelectItem value="gbp">GBP (£)</SelectItem>
                        <SelectItem value="jpy">JPY (¥)</SelectItem>
                        <SelectItem value="cad">CAD (C$)</SelectItem>
                        <SelectItem value="aud">AUD (A$)</SelectItem>
                        <SelectItem value="brl">BRL (R$)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="measurement-system">
                      {t("settings.preferences.measurementSystem") || "Measurement System"}
                    </Label>
                    <RadioGroup
                      defaultValue={measurementSystem}
                      onValueChange={setMeasurementSystem}
                      className="flex gap-6"
                    >
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="metric" id="metric" />
                        <Label htmlFor="metric" className="cursor-pointer">
                          {t("settings.preferences.metric") || "Metric (kg, cm)"}
                        </Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="imperial" id="imperial" />
                        <Label htmlFor="imperial" className="cursor-pointer">
                          {t("settings.preferences.imperial") || "Imperial (lb, in)"}
                        </Label>
                      </div>
                    </RadioGroup>
                  </div>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-end">
              <Button>{t("settings.preferences.savePreferences") || "Save Preferences"}</Button>
            </CardFooter>
          </Card>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t("settings.notifications.title") || "Notification Preferences"}</CardTitle>
              <CardDescription>
                {t("settings.notifications.description") || "Manage how you receive notifications and alerts"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-lg font-medium">
                  {t("settings.notifications.communicationChannels") || "Communication Channels"}
                </h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label htmlFor="email-notifications">
                        {t("settings.notifications.emailNotifications") || "Email Notifications"}
                      </Label>
                      <p className="text-sm text-muted-foreground">
                        {t("settings.notifications.emailNotificationsDescription") || "Receive notifications via email"}
                      </p>
                    </div>
                    <Switch
                      id="email-notifications"
                      checked={emailNotifications}
                      onCheckedChange={setEmailNotifications}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label htmlFor="sms-notifications">
                        {t("settings.notifications.smsNotifications") || "SMS Notifications"}
                      </Label>
                      <p className="text-sm text-muted-foreground">
                        {t("settings.notifications.smsNotificationsDescription") ||
                          "Receive notifications via text message"}
                      </p>
                    </div>
                    <Switch id="sms-notifications" checked={smsNotifications} onCheckedChange={setSmsNotifications} />
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h3 className="text-lg font-medium">
                  {t("settings.notifications.notificationTypes") || "Notification Types"}
                </h3>

                {/* Appointment Reminders */}
                <div className="rounded-lg border p-4">
                  <h4 className="text-base font-medium mb-2">
                    {t("settings.notifications.appointmentReminders") || "Appointment Reminders"}
                  </h4>
                  <p className="text-sm text-muted-foreground mb-4">
                    {t("settings.notifications.appointmentRemindersDescription") ||
                      "Receive reminders about upcoming appointments"}
                  </p>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="flex items-center justify-between sm:flex-col sm:items-start sm:space-y-2">
                      <Label htmlFor="appointment-email" className="text-sm">
                        {t("settings.notifications.email") || "Email"}
                      </Label>
                      <Switch
                        id="appointment-email"
                        checked={notificationChannels.appointmentRemindersEmail}
                        onCheckedChange={(checked) => updateNotificationChannel("appointmentRemindersEmail", checked)}
                      />
                    </div>
                    <div className="flex items-center justify-between sm:flex-col sm:items-start sm:space-y-2">
                      <Label htmlFor="appointment-sms" className="text-sm">
                        {t("settings.notifications.sms") || "SMS"}
                      </Label>
                      <Switch
                        id="appointment-sms"
                        checked={notificationChannels.appointmentRemindersSMS}
                        onCheckedChange={(checked) => updateNotificationChannel("appointmentRemindersSMS", checked)}
                      />
                    </div>
                    <div className="flex items-center justify-between sm:flex-col sm:items-start sm:space-y-2">
                      <Label htmlFor="appointment-push" className="text-sm">
                        {t("settings.notifications.push") || "Push"}
                      </Label>
                      <Switch
                        id="appointment-push"
                        checked={notificationChannels.appointmentRemindersPush}
                        onCheckedChange={(checked) => updateNotificationChannel("appointmentRemindersPush", checked)}
                      />
                    </div>
                  </div>
                </div>

                {/* Messages */}
                <div className="rounded-lg border p-4">
                  <h4 className="text-base font-medium mb-2">{t("settings.notifications.messages") || "Messages"}</h4>
                  <p className="text-sm text-muted-foreground mb-4">
                    {t("settings.notifications.messagesDescription") ||
                      "Receive notifications about new messages from patients"}
                  </p>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="flex items-center justify-between sm:flex-col sm:items-start sm:space-y-2">
                      <Label htmlFor="messages-email" className="text-sm">
                        {t("settings.notifications.email") || "Email"}
                      </Label>
                      <Switch
                        id="messages-email"
                        checked={notificationChannels.messagesEmail}
                        onCheckedChange={(checked) => updateNotificationChannel("messagesEmail", checked)}
                      />
                    </div>
                    <div className="flex items-center justify-between sm:flex-col sm:items-start sm:space-y-2">
                      <Label htmlFor="messages-sms" className="text-sm">
                        {t("settings.notifications.sms") || "SMS"}
                      </Label>
                      <Switch
                        id="messages-sms"
                        checked={notificationChannels.messagesSMS}
                        onCheckedChange={(checked) => updateNotificationChannel("messagesSMS", checked)}
                      />
                    </div>
                    <div className="flex items-center justify-between sm:flex-col sm:items-start sm:space-y-2">
                      <Label htmlFor="messages-push" className="text-sm">
                        {t("settings.notifications.push") || "Push"}
                      </Label>
                      <Switch
                        id="messages-push"
                        checked={notificationChannels.messagesPush}
                        onCheckedChange={(checked) => updateNotificationChannel("messagesPush", checked)}
                      />
                    </div>
                  </div>
                </div>

                {/* Patient Status - Urgent */}
                <div className="rounded-lg border p-4 bg-red-50 dark:bg-red-900/10">
                  <h4 className="text-base font-medium mb-2 text-red-700 dark:text-red-400">
                    {t("settings.notifications.patientStatusUrgent") || "Patient Status: Urgent"}
                  </h4>
                  <p className="text-sm text-muted-foreground mb-4">
                    {t("settings.notifications.patientStatusUrgentDescription") ||
                      "Notifications for patients requiring immediate attention"}
                  </p>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="flex items-center justify-between sm:flex-col sm:items-start sm:space-y-2">
                      <Label htmlFor="urgent-email" className="text-sm">
                        {t("settings.notifications.email") || "Email"}
                      </Label>
                      <Switch
                        id="urgent-email"
                        checked={notificationChannels.urgentPatientEmail}
                        onCheckedChange={(checked) => updateNotificationChannel("urgentPatientEmail", checked)}
                      />
                    </div>
                    <div className="flex items-center justify-between sm:flex-col sm:items-start sm:space-y-2">
                      <Label htmlFor="urgent-sms" className="text-sm">
                        {t("settings.notifications.sms") || "SMS"}
                      </Label>
                      <Switch
                        id="urgent-sms"
                        checked={notificationChannels.urgentPatientSMS}
                        onCheckedChange={(checked) => updateNotificationChannel("urgentPatientSMS", checked)}
                      />
                    </div>
                    <div className="flex items-center justify-between sm:flex-col sm:items-start sm:space-y-2">
                      <Label htmlFor="urgent-push" className="text-sm">
                        {t("settings.notifications.push") || "Push"}
                      </Label>
                      <Switch
                        id="urgent-push"
                        checked={notificationChannels.urgentPatientPush}
                        onCheckedChange={(checked) => updateNotificationChannel("urgentPatientPush", checked)}
                      />
                    </div>
                  </div>
                </div>

                {/* Patient Status - Alert */}
                <div className="rounded-lg border p-4 bg-yellow-50 dark:bg-yellow-900/10">
                  <h4 className="text-base font-medium mb-2 text-yellow-700 dark:text-yellow-400">
                    {t("settings.notifications.patientStatusAlert") || "Patient Status: Alert"}
                  </h4>
                  <p className="text-sm text-muted-foreground mb-4">
                    {t("settings.notifications.patientStatusAlertDescription") ||
                      "Notifications for patients requiring attention soon"}
                  </p>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="flex items-center justify-between sm:flex-col sm:items-start sm:space-y-2">
                      <Label htmlFor="alert-email" className="text-sm">
                        {t("settings.notifications.email") || "Email"}
                      </Label>
                      <Switch
                        id="alert-email"
                        checked={notificationChannels.alertPatientEmail}
                        onCheckedChange={(checked) => updateNotificationChannel("alertPatientEmail", checked)}
                      />
                    </div>
                    <div className="flex items-center justify-between sm:flex-col sm:items-start sm:space-y-2">
                      <Label htmlFor="alert-sms" className="text-sm">
                        {t("settings.notifications.sms") || "SMS"}
                      </Label>
                      <Switch
                        id="alert-sms"
                        checked={notificationChannels.alertPatientSMS}
                        onCheckedChange={(checked) => updateNotificationChannel("alertPatientSMS", checked)}
                      />
                    </div>
                    <div className="flex items-center justify-between sm:flex-col sm:items-start sm:space-y-2">
                      <Label htmlFor="alert-push" className="text-sm">
                        {t("settings.notifications.push") || "Push"}
                      </Label>
                      <Switch
                        id="alert-push"
                        checked={notificationChannels.alertPatientPush}
                        onCheckedChange={(checked) => updateNotificationChannel("alertPatientPush", checked)}
                      />
                    </div>
                  </div>
                </div>

                {/* New Medical Record */}
                <div className="rounded-lg border p-4">
                  <h4 className="text-base font-medium mb-2">
                    {t("settings.notifications.newMedicalRecord") || "New Medical Record"}
                  </h4>
                  <p className="text-sm text-muted-foreground mb-4">
                    {t("settings.notifications.newMedicalRecordDescription") ||
                      "Notifications when new medical records are added"}
                  </p>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="flex items-center justify-between sm:flex-col sm:items-start sm:space-y-2">
                      <Label htmlFor="records-email" className="text-sm">
                        {t("settings.notifications.email") || "Email"}
                      </Label>
                      <Switch
                        id="records-email"
                        checked={notificationChannels.medicalRecordsEmail}
                        onCheckedChange={(checked) => updateNotificationChannel("medicalRecordsEmail", checked)}
                      />
                    </div>
                    <div className="flex items-center justify-between sm:flex-col sm:items-start sm:space-y-2">
                      <Label htmlFor="records-sms" className="text-sm">
                        {t("settings.notifications.sms") || "SMS"}
                      </Label>
                      <Switch
                        id="records-sms"
                        checked={notificationChannels.medicalRecordsSMS}
                        onCheckedChange={(checked) => updateNotificationChannel("medicalRecordsSMS", checked)}
                      />
                    </div>
                    <div className="flex items-center justify-between sm:flex-col sm:items-start sm:space-y-2">
                      <Label htmlFor="records-push" className="text-sm">
                        {t("settings.notifications.push") || "Push"}
                      </Label>
                      <Switch
                        id="records-push"
                        checked={notificationChannels.medicalRecordsPush}
                        onCheckedChange={(checked) => updateNotificationChannel("medicalRecordsPush", checked)}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-end">
              <Button>{t("settings.notifications.savePreferences") || "Save Preferences"}</Button>
            </CardFooter>
          </Card>
        </TabsContent>

        {/* Calendar Tab */}
        <TabsContent value="calendar" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t("settings.calendar.title") || "Calendar Settings"}</CardTitle>
              <CardDescription>
                {t("settings.calendar.description") || "Manage your calendar preferences and integrations"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-lg font-medium">
                  {t("settings.calendar.calendarIntegrations") || "Calendar Integrations"}
                </h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Calendar className="h-6 w-6 text-blue-500" />
                      <div className="space-y-0.5">
                        <Label htmlFor="google-calendar">
                          {t("settings.calendar.googleCalendar") || "Google Calendar"}
                        </Label>
                        <p className="text-sm text-muted-foreground">
                          {t("settings.calendar.googleCalendarDescription") ||
                            "Sync your appointments with Google Calendar"}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {googleCalendarSync && (
                        <Badge variant="outline" className="flex items-center gap-1">
                          <Check className="h-3 w-3" />
                          <span className="text-xs">{t("settings.calendar.connected") || "Connected"}</span>
                        </Badge>
                      )}
                      <Switch
                        id="google-calendar"
                        checked={googleCalendarSync}
                        onCheckedChange={setGoogleCalendarSync}
                      />
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <CalendarClock className="h-6 w-6 text-blue-700" />
                      <div className="space-y-0.5">
                        <Label htmlFor="outlook-calendar">
                          {t("settings.calendar.outlookCalendar") || "Outlook Calendar"}
                        </Label>
                        <p className="text-sm text-muted-foreground">
                          {t("settings.calendar.outlookCalendarDescription") ||
                            "Sync your appointments with Outlook Calendar"}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {outlookCalendarSync && (
                        <Badge variant="outline" className="flex items-center gap-1">
                          <Check className="h-3 w-3" />
                          <span className="text-xs">{t("settings.calendar.connected") || "Connected"}</span>
                        </Badge>
                      )}
                      <Switch
                        id="outlook-calendar"
                        checked={outlookCalendarSync}
                        onCheckedChange={setOutlookCalendarSync}
                      />
                    </div>
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h3 className="text-lg font-medium">{t("settings.calendar.calendarDisplay") || "Calendar Display"}</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="default-view">
                      {t("settings.calendar.defaultView") || "Default Calendar View"}
                    </Label>
                    <Select defaultValue="week">
                      <SelectTrigger id="default-view">
                        <SelectValue placeholder={t("settings.calendar.selectDefaultView") || "Select default view"} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="day">{t("settings.calendar.day") || "Day"}</SelectItem>
                        <SelectItem value="week">{t("settings.calendar.week") || "Week"}</SelectItem>
                        <SelectItem value="month">{t("settings.calendar.month") || "Month"}</SelectItem>
                        <SelectItem value="agenda">{t("settings.calendar.agenda") || "Agenda"}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="time-zone">{t("settings.calendar.timeZone") || "Time Zone"}</Label>
                    <Select defaultValue="america-new_york">
                      <SelectTrigger id="time-zone">
                        <SelectValue placeholder={t("settings.calendar.selectTimeZone") || "Select time zone"} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="america-new_york">
                          {t("settings.calendar.easternTime") || "Eastern Time (ET)"}
                        </SelectItem>
                        <SelectItem value="america-chicago">
                          {t("settings.calendar.centralTime") || "Central Time (CT)"}
                        </SelectItem>
                        <SelectItem value="america-denver">
                          {t("settings.calendar.mountainTime") || "Mountain Time (MT)"}
                        </SelectItem>
                        <SelectItem value="america-los_angeles">
                          {t("settings.calendar.pacificTime") || "Pacific Time (PT)"}
                        </SelectItem>
                        <SelectItem value="europe-london">
                          {t("settings.calendar.greenwichMeanTime") || "Greenwich Mean Time (GMT)"}
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-end">
              <Button>{t("settings.calendar.saveSettings") || "Save Settings"}</Button>
            </CardFooter>
          </Card>
        </TabsContent>

        {/* Pricing Tab */}
        <TabsContent value="pricing" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t("settings.pricing.title") || "Appointment Pricing"}</CardTitle>
              <CardDescription>
                {t("settings.pricing.description") || "Set and manage your consultation fees"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-medium">
                    {t("settings.pricing.standardPricing") || "Standard Pricing (Non-Insured Patients)"}
                  </h3>
                  <Button size="sm" variant="outline" className="flex items-center gap-1">
                    <DollarSign className="h-4 w-4" />
                    {t("settings.pricing.addNewService") || "Add New Service"}
                  </Button>
                </div>

                <div className="border rounded-md">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-3">{t("settings.pricing.serviceType") || "Service Type"}</th>
                        <th className="text-left p-3">{t("settings.pricing.duration") || "Duration (min)"}</th>
                        <th className="text-left p-3">{t("settings.pricing.price") || "Price"}</th>
                        <th className="text-center p-3">{t("settings.pricing.actions") || "Actions"}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pricingData.map((service) => (
                        <tr key={service.id} className="border-b hover:bg-muted/50">
                          <td className="p-3">{service.type}</td>
                          <td className="p-3">{service.duration}</td>
                          <td className="p-3">${service.price.toFixed(2)}</td>
                          <td className="p-3 text-center">
                            <Button variant="ghost" size="sm">
                              {t("settings.pricing.edit") || "Edit"}
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-medium">
                    {t("settings.pricing.insuredPatientPricing") || "Insured Patient Pricing"}
                  </h3>
                  <Button size="sm" variant="outline" className="flex items-center gap-1">
                    <DollarSign className="h-4 w-4" />
                    {t("settings.pricing.addNewService") || "Add New Service"}
                  </Button>
                </div>

                <p className="text-sm text-muted-foreground">
                  {t("settings.pricing.insuredPatientPricingDescription") ||
                    "Set pricing for insured patients by insurance provider and plan"}
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div className="space-y-2">
                    <Label htmlFor="insurance-provider">
                      {t("settings.pricing.insuranceProvider") || "Insurance Provider"}
                    </Label>
                    <Select defaultValue={selectedInsuranceProvider} onValueChange={handleInsuranceProviderChange}>
                      <SelectTrigger id="insurance-provider">
                        <SelectValue placeholder={t("settings.pricing.selectProvider") || "Select provider"} />
                      </SelectTrigger>
                      <SelectContent>
                        {insuranceData.map((insurance) => (
                          <SelectItem key={insurance.id} value={`provider-${insurance.id}`}>
                            {insurance.provider}
                            {insurance.status !== "Active" && ` (${insurance.status})`}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="insurance-plan">{t("settings.pricing.plan") || "Plan"}</Label>
                    <Select
                      defaultValue={selectedInsurancePlan || "default-plan"}
                      value={selectedInsurancePlan || "default-plan"}
                    >
                      <SelectTrigger id="insurance-plan">
                        <SelectValue placeholder={t("settings.pricing.selectPlan") || "Select plan"} />
                      </SelectTrigger>
                      <SelectContent>
                        {selectedInsurancePlan ? (
                          <SelectItem value={selectedInsurancePlan}>{currentInsuranceDetails.plan}</SelectItem>
                        ) : (
                          <SelectItem value="default-plan">
                            {t("settings.pricing.selectProviderFirst") || "Select a provider first"}
                          </SelectItem>
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="flex items-center space-x-2 mb-4">
                  <Badge variant="outline" className="text-blue-600 border-blue-600">
                    {t("settings.pricing.contract") || "Contract"}: {currentInsuranceDetails.contractRef}
                  </Badge>
                  <Badge
                    variant={
                      currentInsuranceDetails.status === "Active"
                        ? "default"
                        : currentInsuranceDetails.status === "Pending"
                          ? "outline"
                          : "destructive"
                    }
                  >
                    {currentInsuranceDetails.status}
                  </Badge>
                </div>

                <div className="border rounded-md">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-3">{t("settings.pricing.serviceType") || "Service Type"}</th>
                        <th className="text-left p-3">{t("settings.pricing.duration") || "Duration (min)"}</th>
                        <th className="text-left p-3">{t("settings.pricing.totalPrice") || "Total Price ($)"}</th>
                        <th className="text-left p-3">{t("settings.pricing.insurancePays") || "Insurance Pays ($)"}</th>
                        <th className="text-left p-3">{t("settings.pricing.patientCoPay") || "Patient Co-pay ($)"}</th>
                        <th className="text-center p-3">{t("settings.pricing.actions") || "Actions"}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b hover:bg-muted/50">
                        <td className="p-3">{t("settings.pricing.initialConsultation") || "Initial Consultation"}</td>
                        <td className="p-3">60</td>
                        <td className="p-3">
                          <Input type="number" defaultValue="180" className="h-8 w-24" />
                        </td>
                        <td className="p-3">
                          <Input type="number" defaultValue="150" className="h-8 w-24" />
                        </td>
                        <td className="p-3">
                          <Input type="number" defaultValue="30" className="h-8 w-24" />
                        </td>
                        <td className="p-3 text-center">
                          <Button variant="ghost" size="sm">
                            {t("settings.pricing.save") || "Save"}
                          </Button>
                        </td>
                      </tr>
                      <tr className="border-b hover:bg-muted/50">
                        <td className="p-3">
                          {t("settings.pricing.followUpConsultation") || "Follow-up Consultation"}
                        </td>
                        <td className="p-3">30</td>
                        <td className="p-3">
                          <Input type="number" defaultValue="120" className="h-8 w-24" />
                        </td>
                        <td className="p-3">
                          <Input type="number" defaultValue="100" className="h-8 w-24" />
                        </td>
                        <td className="p-3">
                          <Input type="number" defaultValue="20" className="h-8 w-24" />
                        </td>
                        <td className="p-3 text-center">
                          <Button variant="ghost" size="sm">
                            {t("settings.pricing.save") || "Save"}
                          </Button>
                        </td>
                      </tr>
                      <tr className="border-b hover:bg-muted/50">
                        <td className="p-3">{t("settings.pricing.annualPhysical") || "Annual Physical"}</td>
                        <td className="p-3">90</td>
                        <td className="p-3">
                          <Input type="number" defaultValue="250" className="h-8 w-24" />
                        </td>
                        <td className="p-3">
                          <Input type="number" defaultValue="210" className="h-8 w-24" />
                        </td>
                        <td className="p-3">
                          <Input type="number" defaultValue="40" className="h-8 w-24" />
                        </td>
                        <td className="p-3 text-center">
                          <Button variant="ghost" size="sm">
                            {t("settings.pricing.save") || "Save"}
                          </Button>
                        </td>
                      </tr>
                      <tr className="border-b hover:bg-muted/50">
                        <td className="p-3">
                          {t("settings.pricing.emergencyConsultation") || "Emergency Consultation"}
                        </td>
                        <td className="p-3">45</td>
                        <td className="p-3">
                          <Input type="number" defaultValue="200" className="h-8 w-24" />
                        </td>
                        <td className="p-3">
                          <Input type="number" defaultValue="150" className="h-8 w-24" />
                        </td>
                        <td className="p-3">
                          <Input type="number" defaultValue="50" className="h-8 w-24" />
                        </td>
                        <td className="p-3 text-center">
                          <Button variant="ghost" size="sm">
                            {t("settings.pricing.save") || "Save"}
                          </Button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h3 className="text-lg font-medium">
                  {t("settings.pricing.discountCampaigns") || "Discount Campaigns"}
                </h3>
                <p className="text-sm text-muted-foreground">
                  {t("settings.pricing.discountCampaignsDescription") ||
                    "Create time-limited discount campaigns for specific patient groups and services"}
                </p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="campaign-name">{t("settings.pricing.campaignName") || "Campaign Name"}</Label>
                    <Input
                      id="campaign-name"
                      placeholder={t("settings.pricing.enterCampaignName") || "Enter campaign name"}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="discount-code">{t("settings.pricing.discountCode") || "Discount Code"}</Label>
                    <Input
                      id="discount-code"
                      placeholder={t("settings.pricing.enterDiscountCode") || "Enter discount code"}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="discount-type">{t("settings.pricing.discountType") || "Discount Type"}</Label>
                    <Select defaultValue="percentage">
                      <SelectTrigger id="discount-type">
                        <SelectValue placeholder={t("settings.pricing.selectDiscountType") || "Select discount type"} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="percentage">
                          {t("settings.pricing.percentage") || "Percentage (%)"}
                        </SelectItem>
                        <SelectItem value="fixed">{t("settings.pricing.fixedAmount") || "Fixed Amount ($)"}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="discount-value">{t("settings.pricing.discountValue") || "Discount Value"}</Label>
                    <Input
                      id="discount-value"
                      type="number"
                      placeholder={t("settings.pricing.enterDiscountValue") || "Enter discount value"}
                      min="0"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="patient-group">{t("settings.pricing.patientType") || "Patient Type"}</Label>
                    <Select defaultValue="all">
                      <SelectTrigger id="patient-group">
                        <SelectValue placeholder={t("settings.pricing.selectPatientGroup") || "Select patient group"} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">{t("settings.pricing.allPatients") || "All Patients"}</SelectItem>
                        <SelectItem value="new">{t("settings.pricing.newPatients") || "New Patients"}</SelectItem>
                        <SelectItem value="recurring">
                          {t("settings.pricing.recurringPatients") || "Recurring Patients"}
                        </SelectItem>
                        <SelectItem value="insured">
                          {t("settings.pricing.insuredPatients") || "Insured Patients"}
                        </SelectItem>
                        <SelectItem value="non-insured">
                          {t("settings.pricing.nonInsuredPatients") || "Non-Insured Patients"}
                        </SelectItem>
                        <SelectItem value="elderly">
                          {t("settings.pricing.seniorCitizens") || "Senior Citizens"}
                        </SelectItem>
                        <SelectItem value="children">{t("settings.pricing.children") || "Children"}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="discount-services">{t("settings.pricing.services") || "Services"}</Label>
                    <Select defaultValue="all">
                      <SelectTrigger id="discount-services">
                        <SelectValue placeholder={t("settings.pricing.selectServices") || "Select services"} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">{t("settings.pricing.allServices") || "All Services"}</SelectItem>
                        <SelectItem value="initial">
                          {t("settings.pricing.initialConsultations") || "Initial Consultations"}
                        </SelectItem>
                        <SelectItem value="follow-up">
                          {t("settings.pricing.followUpConsultations") || "Follow-up Consultations"}
                        </SelectItem>
                        <SelectItem value="annual">
                          {t("settings.pricing.annualPhysicals") || "Annual Physicals"}
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="start-date">{t("settings.pricing.startDate") || "Start Date"}</Label>
                    <Input id="start-date" type="date" />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="end-date">{t("settings.pricing.endDate") || "End Date"}</Label>
                    <Input id="end-date" type="date" />
                  </div>
                </div>

                <Button className="mt-2">{t("settings.pricing.addDiscountCampaign") || "Add Discount Campaign"}</Button>

                <div className="mt-4 border rounded-md">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-3">{t("settings.pricing.campaign") || "Campaign"}</th>
                        <th className="text-left p-3">{t("settings.pricing.code") || "Code"}</th>
                        <th className="text-left p-3">{t("settings.pricing.discount") || "Discount"}</th>
                        <th className="text-left p-3">{t("settings.pricing.patientType") || "Patient Type"}</th>
                        <th className="text-left p-3">{t("settings.pricing.services") || "Services"}</th>
                        <th className="text-left p-3">{t("settings.pricing.period") || "Period"}</th>
                        <th className="text-left p-3">{t("settings.pricing.status") || "Status"}</th>
                        <th className="text-center p-3">{t("settings.pricing.actions") || "Actions"}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b hover:bg-muted/50">
                        <td className="p-3">{t("settings.pricing.summerSpecial") || "Summer Special"}</td>
                        <td className="p-3">SUMMER25</td>
                        <td className="p-3">15%</td>
                        <td className="p-3">{t("settings.pricing.newPatients") || "New Patients"}</td>
                        <td className="p-3">{t("settings.pricing.allServices") || "All Services"}</td>
                        <td className="p-3">Jun 1 - Aug 31, 2025</td>
                        <td className="p-3">
                          <Badge>{t("settings.pricing.active") || "Active"}</Badge>
                        </td>
                        <td className="p-3 text-center">
                          <Button variant="ghost" size="sm">
                            {t("settings.pricing.edit") || "Edit"}
                          </Button>
                        </td>
                      </tr>
                      <tr className="border-b hover:bg-muted/50">
                        <td className="p-3">{t("settings.pricing.seniorDiscount") || "Senior Discount"}</td>
                        <td className="p-3">SENIOR20</td>
                        <td className="p-3">$20.00</td>
                        <td className="p-3">{t("settings.pricing.seniorCitizens") || "Senior Citizens"}</td>
                        <td className="p-3">{t("settings.pricing.annualPhysicals") || "Annual Physicals"}</td>
                        <td className="p-3">Jan 1 - Dec 31, 2025</td>
                        <td className="p-3">
                          <Badge>{t("settings.pricing.active") || "Active"}</Badge>
                        </td>
                        <td className="p-3 text-center">
                          <Button variant="ghost" size="sm">
                            {t("settings.pricing.edit") || "Edit"}
                          </Button>
                        </td>
                      </tr>
                      <tr className="border-b hover:bg-muted/50">
                        <td className="p-3">{t("settings.pricing.springPromotion") || "Spring Promotion"}</td>
                        <td className="p-3">SPRING10</td>
                        <td className="p-3">10%</td>
                        <td className="p-3">{t("settings.pricing.allPatients") || "All Patients"}</td>
                        <td className="p-3">{t("settings.pricing.initialConsultations") || "Initial Consultations"}</td>
                        <td className="p-3">Mar 1 - May 31, 2025</td>
                        <td className="p-3">
                          <Badge variant="outline">{t("settings.pricing.upcoming") || "Upcoming"}</Badge>
                        </td>
                        <td className="p-3 text-center">
                          <Button variant="ghost" size="sm">
                            {t("settings.pricing.edit") || "Edit"}
                          </Button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-end">
              <Button>{t("settings.pricing.savePricing") || "Save Pricing"}</Button>
            </CardFooter>
          </Card>
        </TabsContent>

        {/* Billing Tab */}
        <TabsContent value="billing" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t("settings.billing.title") || "Billing Information"}</CardTitle>
              <CardDescription>
                {t("settings.billing.description") || "Manage your payment methods and billing details"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-lg font-medium">{t("settings.billing.invoiceDetails") || "Invoice Details"}</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="business-name">
                      {t("settings.billing.businessName") || "Business/Practice Name"}
                    </Label>
                    <Input id="business-name" defaultValue="Dr. Daniel Johnson, MD" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="tax-id">{t("settings.billing.taxId") || "Tax ID / EIN"}</Label>
                    <Input id="tax-id" defaultValue="12-3456789" />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="billing-address">{t("settings.billing.billingAddress") || "Billing Address"}</Label>
                  <Textarea
                    id="billing-address"
                    defaultValue="123 Medical Center Dr.
Suite 456
New York, NY 10001
United States"
                    rows={4}
                  />
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h3 className="text-lg font-medium">{t("settings.billing.paymentMethods") || "Payment Methods"}</h3>
                <p className="text-sm text-muted-foreground">
                  {t("settings.billing.paymentMethodsDescription") || "Add or update your payment information"}
                </p>

                <div className="rounded-md border p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <CreditCard className="h-6 w-6 text-blue-500" />
                      <div>
                        <p className="font-medium">{t("settings.billing.visaEnding") || "Visa ending in 4242"}</p>
                        <p className="text-sm text-muted-foreground">
                          {t("settings.billing.expires") || "Expires 05/2025"}
                        </p>
                      </div>
                    </div>
                    <Badge>{t("settings.billing.default") || "Default"}</Badge>
                  </div>
                </div>

                <div className="rounded-md border p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <CreditCard className="h-6 w-6 text-purple-500" />
                      <div>
                        <p className="font-medium">
                          {t("settings.billing.mastercardEnding") || "Mastercard ending in 8888"}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {t("settings.billing.expires") || "Expires 09/2024"}
                        </p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm">
                      {t("settings.billing.setDefault") || "Set Default"}
                    </Button>
                  </div>
                </div>

                <Button variant="outline" className="mt-2">
                  {t("settings.billing.addPaymentMethod") || "Add Payment Method"}
                </Button>
              </div>

              <Separator />

              <div className="space-y-4">
                <h3 className="text-lg font-medium">
                  {t("settings.billing.bankAccountInformation") || "Bank Account Information"}
                </h3>
                <p className="text-sm text-muted-foreground">
                  {t("settings.billing.bankAccountInformationDescription") ||
                    "For receiving payments from the platform"}
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="account-name">
                      {t("settings.billing.accountHolderName") || "Account Holder Name"}
                    </Label>
                    <Input id="account-name" defaultValue="Daniel Johnson" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bank-name">{t("settings.billing.bankName") || "Bank Name"}</Label>
                    <Input id="bank-name" defaultValue="First National Bank" />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="account-number">{t("settings.billing.accountNumber") || "Account Number"}</Label>
                    <Input id="account-number" defaultValue="XXXX-XXXX-7890" type="password" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="routing-number">{t("settings.billing.routingNumber") || "Routing Number"}</Label>
                    <Input id="routing-number" defaultValue="XXX-XXX-456" type="password" />
                  </div>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-end">
              <Button>{t("settings.billing.saveBillingInformation") || "Save Billing Information"}</Button>
            </CardFooter>
          </Card>
        </TabsContent>

        {/* Insurance Tab */}
        <TabsContent value="insurance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t("settings.insurance.title") || "Insurance Agreements"}</CardTitle>
              <CardDescription>
                {t("settings.insurance.description") || "Manage your insurance provider agreements"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-medium">
                    {t("settings.insurance.activeInsuranceProviders") || "Active Insurance Providers"}
                  </h3>
                  <Button size="sm" variant="outline" className="flex items-center gap-1">
                    <File className="h-4 w-4" />
                    {t("settings.insurance.addNewProvider") || "Add New Provider"}
                  </Button>
                </div>

                <div className="border rounded-md">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-3">{t("settings.insurance.provider") || "Provider"}</th>
                        <th className="text-left p-3">{t("settings.insurance.plan") || "Plan"}</th>
                        <th className="text-left p-3">{t("settings.insurance.contractRef") || "Contract Ref #"}</th>
                        <th className="text-left p-3">{t("settings.insurance.status") || "Status"}</th>
                        <th className="text-center p-3">{t("settings.insurance.actions") || "Actions"}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {insuranceData.map((insurance) => (
                        <tr key={insurance.id} className="border-b hover:bg-muted/50">
                          <td className="p-3">{insurance.provider}</td>
                          <td className="p-3">{insurance.plan}</td>
                          <td className="p-3">{insurance.contractRef}</td>
                          <td className="p-3">
                            <Badge
                              variant={
                                insurance.status === "Active"
                                  ? "default"
                                  : insurance.status === "Pending"
                                    ? "outline"
                                    : "destructive"
                              }
                            >
                              {insurance.status}
                            </Badge>
                          </td>
                          <td className="p-3 text-center">
                            <Button variant="ghost" size="sm">
                              {t("settings.insurance.view") || "View"}
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h3 className="text-lg font-medium">
                  {t("settings.insurance.addInsuranceProvider") || "Add Insurance Provider"}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="provider-name">{t("settings.insurance.providerName") || "Provider Name"}</Label>
                    <Input
                      id="provider-name"
                      placeholder={t("settings.insurance.insuranceProviderName") || "Insurance provider name"}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="plan-name">{t("settings.insurance.planName") || "Plan Name"}</Label>
                    <Input
                      id="plan-name"
                      placeholder={t("settings.insurance.insurancePlanName") || "Insurance plan name"}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="provider-id">{t("settings.insurance.providerId") || "Provider ID"}</Label>
                    <Input
                      id="provider-id"
                      placeholder={t("settings.insurance.yourProviderId") || "Your provider ID"}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="contract-ref">
                      {t("settings.insurance.contractRefNumber") || "Contract Reference Number"}
                    </Label>
                    <Input
                      id="contract-ref"
                      placeholder={t("settings.insurance.contractReferenceNumber") || "Contract reference number"}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="agreement-date">{t("settings.insurance.agreementDate") || "Agreement Date"}</Label>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Input id="agreement-date" type="date" />
                    <Select defaultValue="active">
                      <SelectTrigger id="agreement-status">
                        <SelectValue placeholder={t("settings.insurance.agreementStatus") || "Agreement status"} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="active">{t("settings.insurance.active") || "Active"}</SelectItem>
                        <SelectItem value="pending">{t("settings.insurance.pending") || "Pending"}</SelectItem>
                        <SelectItem value="expired">{t("settings.insurance.expired") || "Expired"}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="agreement-notes">{t("settings.insurance.notes") || "Notes"}</Label>
                  <Textarea
                    id="agreement-notes"
                    placeholder={t("settings.insurance.additionalDetails") || "Additional details about this agreement"}
                    rows={3}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="agreement-upload">
                    {t("settings.insurance.uploadAgreementDocument") || "Upload Agreement Document"}
                  </Label>
                  <Input id="agreement-upload" type="file" accept=".pdf,.doc,.docx" />
                  <p className="text-xs text-muted-foreground mt-1">
                    {t("settings.insurance.uploadCopySignedAgreement") ||
                      "Upload a copy of your signed agreement (PDF, DOC, or DOCX format)"}
                  </p>
                </div>

                <Button className="mt-2">
                  {t("settings.insurance.addInsuranceProvider") || "Add Insurance Provider"}
                </Button>
              </div>
            </CardContent>
            <CardFooter className="flex justify-end">
              <Button>{t("settings.insurance.saveInsuranceSettings") || "Save Insurance Settings"}</Button>
            </CardFooter>
          </Card>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t("settings.security.title") || "Security Settings"}</CardTitle>
              <CardDescription>
                {t("settings.security.description") || "Manage your account security and authentication"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-lg font-medium">{t("settings.security.password") || "Password"}</h3>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="current-password">
                      {t("settings.security.currentPassword") || "Current Password"}
                    </Label>
                    <Input id="current-password" type="password" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="new-password">{t("settings.security.newPassword") || "New Password"}</Label>
                    <Input id="new-password" type="password" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="confirm-password">
                      {t("settings.security.confirmNewPassword") || "Confirm New Password"}
                    </Label>
                    <Input id="confirm-password" type="password" />
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h3 className="text-lg font-medium">
                  {t("settings.security.twoFactorAuthentication") || "Two-Factor Authentication"}
                </h3>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="two-factor">
                      {t("settings.security.enableTwoFactorAuthentication") || "Enable Two-Factor Authentication"}
                    </Label>
                    <p className="text-sm text-muted-foreground">
                      {t("settings.security.twoFactorAuthenticationDescription") ||
                        "Add an extra layer of security to your account"}
                    </p>
                  </div>
                  <Switch id="two-factor" />
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h3 className="text-lg font-medium">
                  {t("settings.security.sessionManagement") || "Session Management"}
                </h3>
                <div className="space-y-2">
                  <div className="rounded-md border p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{t("settings.security.currentSession") || "Current Session"}</p>
                        <p className="text-sm text-muted-foreground">
                          {t("settings.security.currentSessionDetails") ||
                            "Chrome on Windows • New York, USA • Started 2 hours ago"}
                        </p>
                      </div>
                      <Badge>{t("settings.security.active") || "Active"}</Badge>
                    </div>
                  </div>
                  <Button variant="outline" className="w-full">
                    {t("settings.security.signOutAllOtherSessions") || "Sign Out of All Other Sessions"}
                  </Button>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-end">
              <Button>{t("settings.security.saveSecuritySettings") || "Save Security Settings"}</Button>
            </CardFooter>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

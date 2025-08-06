"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Calendar, Clock, Heart, Plus, Search, Users, CheckCircle, Edit, Copy } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useLanguage } from "@/lib/language-context"

// Sample health plans data
const healthPlans = [
  {
    id: "hypertension-management",
    title: "Hypertension Management Plan",
    description: "A comprehensive plan for managing high blood pressure",
    targetCondition: "Hypertension",
    duration: "3 months",
    assignedCount: 12,
    lastUpdated: "Apr 10, 2025",
    status: "Active",
  },
  {
    id: "diabetes-care",
    title: "Diabetes Care Plan",
    description: "Monitoring and management plan for Type 2 Diabetes",
    targetCondition: "Diabetes Type 2",
    duration: "6 months",
    assignedCount: 8,
    lastUpdated: "Apr 5, 2025",
    status: "Active",
  },
  {
    id: "weight-management",
    title: "Weight Management Program",
    description: "Structured plan for healthy weight loss and maintenance",
    targetCondition: "Obesity",
    duration: "6 months",
    assignedCount: 15,
    lastUpdated: "Mar 28, 2025",
    status: "Active",
  },
  {
    id: "cardiac-rehab",
    title: "Cardiac Rehabilitation Program",
    description: "Recovery and prevention plan for heart disease patients",
    targetCondition: "Heart Disease",
    duration: "12 months",
    assignedCount: 6,
    lastUpdated: "Mar 20, 2025",
    status: "Active",
  },
  {
    id: "pain-management",
    title: "Chronic Pain Management",
    description: "Multimodal approach to managing chronic pain conditions",
    targetCondition: "Chronic Pain",
    duration: "Ongoing",
    assignedCount: 10,
    lastUpdated: "Mar 15, 2025",
    status: "Active",
  },
  {
    id: "smoking-cessation",
    title: "Smoking Cessation Program",
    description: "Step-by-step plan to quit smoking",
    targetCondition: "Tobacco Use",
    duration: "3 months",
    assignedCount: 7,
    lastUpdated: "Mar 10, 2025",
    status: "Active",
  },
]

export default function HealthPlansClientPage() {
  const { t } = useLanguage()
  const [searchTerm, setSearchTerm] = useState("")
  const [activeTab, setActiveTab] = useState("all")
  const [isCreatingPlan, setIsCreatingPlan] = useState(false)

  const filteredPlans = healthPlans.filter((plan) => {
    const matchesSearch =
      plan.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      plan.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      plan.targetCondition.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesTab = activeTab === "all" || plan.status.toLowerCase() === activeTab.toLowerCase()
    return matchesSearch && matchesTab
  })

  const handleCreatePlan = () => {
    setIsCreatingPlan(true)
    // Simulate API call
    setTimeout(() => {
      setIsCreatingPlan(false)
    }, 2000)
  }

  return (
    <div className="container py-6">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-teal-700 dark:text-teal-300">
            {t("healthPlans.title", "Health Plans")}
          </h1>
          <p className="text-muted-foreground">{t("healthPlans.subtitle", "Create and manage treatment plans")}</p>
        </div>
        <Dialog>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              {t("healthPlans.createNewPlan", "Create New Plan")}
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[600px]">
            <DialogHeader>
              <DialogTitle>{t("healthPlans.createNewHealthPlan", "Create New Health Plan")}</DialogTitle>
              <DialogDescription>
                {t("healthPlans.designTemplate", "Design a standardized health plan template for patients.")}
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="plan-title">{t("healthPlans.planTitle", "Plan Title")}</Label>
                <Input
                  id="plan-title"
                  placeholder={t("healthPlans.planTitlePlaceholder", "e.g., Blood Pressure Management Plan")}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="plan-condition">{t("healthPlans.targetCondition", "Target Condition")}</Label>
                <Input id="plan-condition" placeholder={t("healthPlans.conditionPlaceholder", "e.g., Hypertension")} />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="plan-duration">{t("healthPlans.duration", "Duration")}</Label>
                <Select defaultValue="3-months">
                  <SelectTrigger>
                    <SelectValue placeholder={t("healthPlans.selectDuration", "Select duration")} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1-month">{t("healthPlans.durations.oneMonth", "1 Month")}</SelectItem>
                    <SelectItem value="3-months">{t("healthPlans.durations.threeMonths", "3 Months")}</SelectItem>
                    <SelectItem value="6-months">{t("healthPlans.durations.sixMonths", "6 Months")}</SelectItem>
                    <SelectItem value="1-year">{t("healthPlans.durations.oneYear", "1 Year")}</SelectItem>
                    <SelectItem value="ongoing">{t("healthPlans.durations.ongoing", "Ongoing")}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="plan-description">{t("healthPlans.description", "Description")}</Label>
                <Textarea
                  id="plan-description"
                  placeholder={t("healthPlans.descriptionPlaceholder", "Brief description of the health plan")}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="plan-goals">{t("healthPlans.goals", "Goals")}</Label>
                <Textarea
                  id="plan-goals"
                  placeholder={t("healthPlans.goalsPlaceholder", "List the primary goals of this plan")}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="plan-interventions">{t("healthPlans.interventions", "Interventions")}</Label>
                <Textarea
                  id="plan-interventions"
                  placeholder={t(
                    "healthPlans.interventionsPlaceholder",
                    "List recommended interventions, medications, etc.",
                  )}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="plan-monitoring">{t("healthPlans.monitoring", "Monitoring Requirements")}</Label>
                <Textarea
                  id="plan-monitoring"
                  placeholder={t(
                    "healthPlans.monitoringPlaceholder",
                    "e.g., Daily blood pressure readings, weekly weight check",
                  )}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="submit" onClick={handleCreatePlan} disabled={isCreatingPlan}>
                {isCreatingPlan ? t("healthPlans.creating", "Creating...") : t("healthPlans.createPlan", "Create Plan")}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder={t("healthPlans.searchPlans", "Search health plans...")}
            className="pl-8"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <Tabs defaultValue="all" className="w-full sm:w-auto" value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="all">{t("healthPlans.tabs.all", "All")}</TabsTrigger>
            <TabsTrigger value="active">{t("healthPlans.tabs.active", "Active")}</TabsTrigger>
            <TabsTrigger value="draft">{t("healthPlans.tabs.drafts", "Drafts")}</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredPlans.map((plan) => (
          <Card key={plan.id} className="h-full transition-all hover:shadow-md">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle>{plan.title}</CardTitle>
                  <CardDescription>{plan.description}</CardDescription>
                </div>
                <Badge className="bg-teal-600 dark:bg-teal-600">{plan.status}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2">
                <div className="flex items-center gap-2">
                  <Heart className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">
                    {t("healthPlans.condition", "Condition")}: {plan.targetCondition}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">
                    {t("healthPlans.duration", "Duration")}: {plan.duration}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">
                    {t("healthPlans.assignedTo", "Assigned to")} {plan.assignedCount}{" "}
                    {t("healthPlans.patients", "patients")}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">
                    {t("healthPlans.lastUpdated", "Last updated")}: {plan.lastUpdated}
                  </span>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-between">
              <Button variant="outline" size="sm">
                <Edit className="mr-2 h-4 w-4" />
                {t("healthPlans.edit", "Edit")}
              </Button>
              <Button variant="outline" size="sm">
                <Copy className="mr-2 h-4 w-4" />
                {t("healthPlans.duplicate", "Duplicate")}
              </Button>
              <Button variant="outline" size="sm">
                <CheckCircle className="mr-2 h-4 w-4" />
                {t("healthPlans.assign", "Assign")}
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  )
}

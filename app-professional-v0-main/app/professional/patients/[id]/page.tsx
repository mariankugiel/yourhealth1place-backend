"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
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
import { Calendar, MessageSquare, FileText, Plus, Clock, Send } from "lucide-react"
import HealthMetricsChart from "@/components/patient/health-metrics-chart"

export default function PatientDetail({ params }: { params: { id: string } }) {
  const [isCreatingPlan, setIsCreatingPlan] = useState(false)

  // This would normally come from an API call using the ID
  const patient = {
    id: params.id,
    name: "Sarah Johnson",
    age: 42,
    gender: "Female",
    conditions: ["Hypertension", "High Cholesterol"],
    allergies: ["Penicillin"],
    bloodType: "A+",
    lastVisit: "April 15, 2023",
    summary: {
      preConditions:
        "Patient has Stage 1 hypertension diagnosed in January 2023 and hyperlipidemia. Currently on medication management with lifestyle modifications.",
      recentProgress:
        "Blood pressure has shown gradual improvement over the past 3 months, decreasing from 152/95 to 138/88. Weight has decreased by 10 pounds since starting treatment.",
      treatmentPlan:
        "Continue current medication regimen with focus on dietary sodium restriction and regular exercise. Monitor blood pressure daily and track in app.",
      nextSteps:
        "If blood pressure continues to improve, consider maintaining current medication dosage. If target not reached within 1 month, may need to adjust medication or add second agent.",
    },
    clinicalNotes: [
      {
        id: "note1",
        date: "2023-03-15",
        provider: "Dr. Johnson",
        title: "Hypertension Follow-up",
        content:
          "Patient reports compliance with medication. Blood pressure still elevated but showing improvement. Discussed dietary changes and increased physical activity.",
      },
      {
        id: "note2",
        date: "2023-01-10",
        provider: "Dr. Johnson",
        title: "Annual Physical",
        content:
          "Patient in good health overall. Blood pressure elevated at 145/95. Recommended lifestyle changes and monitoring. Will follow up in 2 months.",
      },
    ],
  }

  const handleCreatePlan = () => {
    setIsCreatingPlan(true)
    // Simulate API call
    setTimeout(() => {
      setIsCreatingPlan(false)
    }, 2000)
  }

  return (
    <div className="container py-6">
      <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <Avatar className="h-16 w-16">
            <AvatarImage src="/placeholder-user.jpg" alt={patient.name} />
            <AvatarFallback>SJ</AvatarFallback>
          </Avatar>
          <div>
            <h1 className="text-3xl font-bold">{patient.name}</h1>
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline">{patient.age} years</Badge>
              <Badge variant="outline">{patient.gender}</Badge>
              <Badge variant="outline">{patient.bloodType}</Badge>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="gap-1">
            <MessageSquare className="h-4 w-4" />
            Message
          </Button>
          <Button className="gap-1">
            <Calendar className="h-4 w-4" />
            Schedule
          </Button>
        </div>
      </header>

      <div className="grid gap-6 md:grid-cols-3">
        <div className="md:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Patient Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="font-medium">Medical Conditions</h3>
                <ul className="mt-1 space-y-1">
                  {patient.conditions.map((condition, index) => (
                    <li key={index} className="flex items-center text-sm">
                      <span className="mr-2 h-2 w-2 rounded-full bg-red-500" />
                      {condition}
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <h3 className="font-medium">Allergies</h3>
                <ul className="mt-1 space-y-1">
                  {patient.allergies.map((allergy, index) => (
                    <li key={index} className="flex items-center text-sm">
                      <span className="mr-2 h-2 w-2 rounded-full bg-yellow-500" />
                      {allergy}
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <h3 className="font-medium">Current Medications</h3>
                <ul className="mt-1 space-y-1">
                  <li className="flex items-center text-sm">
                    <span className="mr-2 h-2 w-2 rounded-full bg-blue-500" />
                    Lisinopril 10mg (1x daily)
                  </li>
                  <li className="flex items-center text-sm">
                    <span className="mr-2 h-2 w-2 rounded-full bg-blue-500" />
                    Atorvastatin 20mg (1x daily)
                  </li>
                </ul>
              </div>

              <div>
                <h3 className="font-medium">Last Visit</h3>
                <p className="text-sm">{patient.lastVisit}</p>
                <p className="text-sm text-muted-foreground">Blood pressure follow-up</p>
              </div>

              <Dialog>
                <DialogTrigger asChild>
                  <Button variant="outline" className="w-full">
                    Update Information
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Update Patient Information</DialogTitle>
                    <DialogDescription>Make changes to the patient's medical information.</DialogDescription>
                  </DialogHeader>
                  <div className="grid gap-4 py-4">
                    <div className="grid gap-2">
                      <Label htmlFor="conditions">Medical Conditions</Label>
                      <Input id="conditions" defaultValue={patient.conditions.join(", ")} />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="allergies">Allergies</Label>
                      <Input id="allergies" defaultValue={patient.allergies.join(", ")} />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="medications">Current Medications</Label>
                      <Textarea
                        id="medications"
                        defaultValue="Lisinopril 10mg (1x daily)
Atorvastatin 20mg (1x daily)"
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button type="submit">Save Changes</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </CardContent>
          </Card>
        </div>

        <div className="md:col-span-2">
          <Tabs defaultValue="summary">
            <TabsList className="mb-4">
              <TabsTrigger value="summary">Summary</TabsTrigger>
              <TabsTrigger value="health-plan">Health Plan</TabsTrigger>
              <TabsTrigger value="records">Medical Records</TabsTrigger>
              <TabsTrigger value="metrics">Health Metrics</TabsTrigger>
              <TabsTrigger value="notes">Clinical Notes</TabsTrigger>
            </TabsList>

            <TabsContent value="summary" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Patient Summary</CardTitle>
                  <CardDescription>Overview of patient's health status and treatment</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <h3 className="font-medium">Pre-existing Conditions</h3>
                      <p className="text-sm mt-1">{patient.summary.preConditions}</p>
                    </div>

                    <div>
                      <h3 className="font-medium">Recent Progress</h3>
                      <p className="text-sm mt-1">{patient.summary.recentProgress}</p>
                    </div>

                    <div>
                      <h3 className="font-medium">Treatment Plan</h3>
                      <p className="text-sm mt-1">{patient.summary.treatmentPlan}</p>
                    </div>

                    <div>
                      <h3 className="font-medium">Next Steps</h3>
                      <p className="text-sm mt-1">{patient.summary.nextSteps}</p>
                    </div>

                    <div>
                      <h3 className="font-medium">Last Clinical Note</h3>
                      {patient.clinicalNotes.length > 0 ? (
                        <div className="mt-1">
                          <p className="text-sm font-medium">
                            {patient.clinicalNotes[0].title} - {patient.clinicalNotes[0].date}
                          </p>
                          <p className="text-sm">{patient.clinicalNotes[0].content}</p>
                        </div>
                      ) : (
                        <p className="text-sm mt-1">No clinical notes available</p>
                      )}
                    </div>

                    <div className="flex justify-end gap-2">
                      <Button variant="outline" size="sm">
                        Print Summary
                      </Button>
                      <Button size="sm">Update Summary</Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="health-plan" className="space-y-4">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Current Health Plan</CardTitle>
                      <CardDescription>Created on April 15, 2023</CardDescription>
                    </div>
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button size="sm">
                          <Plus className="mr-2 h-4 w-4" />
                          New Plan
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="sm:max-w-[600px]">
                        <DialogHeader>
                          <DialogTitle>Create New Health Plan</DialogTitle>
                          <DialogDescription>Design a personalized health plan for the patient.</DialogDescription>
                        </DialogHeader>
                        <div className="grid gap-4 py-4">
                          <div className="grid gap-2">
                            <Label htmlFor="plan-title">Plan Title</Label>
                            <Input id="plan-title" placeholder="e.g., Blood Pressure Management Plan" />
                          </div>
                          <div className="grid gap-2">
                            <Label htmlFor="plan-goal">Primary Goal</Label>
                            <Input id="plan-goal" placeholder="e.g., Reduce blood pressure to 120/80" />
                          </div>
                          <div className="grid gap-2">
                            <Label htmlFor="plan-duration">Duration</Label>
                            <Select defaultValue="3-months">
                              <SelectTrigger>
                                <SelectValue placeholder="Select duration" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="1-month">1 Month</SelectItem>
                                <SelectItem value="3-months">3 Months</SelectItem>
                                <SelectItem value="6-months">6 Months</SelectItem>
                                <SelectItem value="1-year">1 Year</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="grid gap-2">
                            <Label htmlFor="plan-medications">Medications</Label>
                            <Textarea id="plan-medications" placeholder="List medications with dosage and frequency" />
                          </div>
                          <div className="grid gap-2">
                            <Label htmlFor="plan-lifestyle">Lifestyle Recommendations</Label>
                            <Textarea id="plan-lifestyle" placeholder="Diet, exercise, and other lifestyle changes" />
                          </div>
                          <div className="grid gap-2">
                            <Label htmlFor="plan-monitoring">Monitoring Requirements</Label>
                            <Textarea
                              id="plan-monitoring"
                              placeholder="e.g., Daily blood pressure readings, weekly weight check"
                            />
                          </div>
                        </div>
                        <DialogFooter>
                          <Button type="submit" onClick={handleCreatePlan} disabled={isCreatingPlan}>
                            {isCreatingPlan ? "Creating..." : "Create Plan"}
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <h3 className="font-medium">Blood Pressure Management Plan</h3>
                      <p className="text-sm text-muted-foreground">
                        3-month plan to reduce and stabilize blood pressure
                      </p>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium">Goals</h4>
                      <ul className="mt-1 space-y-1 text-sm">
                        <li className="flex items-center">
                          <span className="mr-2 h-2 w-2 rounded-full bg-blue-500" />
                          Reduce blood pressure to 120/80 mmHg
                        </li>
                        <li className="flex items-center">
                          <span className="mr-2 h-2 w-2 rounded-full bg-blue-500" />
                          Maintain consistent daily medication schedule
                        </li>
                        <li className="flex items-center">
                          <span className="mr-2 h-2 w-2 rounded-full bg-blue-500" />
                          Reduce sodium intake to less than 2,300mg per day
                        </li>
                      </ul>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium">Medications</h4>
                      <ul className="mt-1 space-y-1 text-sm">
                        <li className="flex items-center">
                          <span className="mr-2 h-2 w-2 rounded-full bg-green-500" />
                          Lisinopril 10mg - 1 tablet daily in the morning
                        </li>
                        <li className="flex items-center">
                          <span className="mr-2 h-2 w-2 rounded-full bg-green-500" />
                          Atorvastatin 20mg - 1 tablet daily in the evening
                        </li>
                      </ul>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium">Lifestyle Recommendations</h4>
                      <ul className="mt-1 space-y-1 text-sm">
                        <li className="flex items-center">
                          <span className="mr-2 h-2 w-2 rounded-full bg-purple-500" />
                          DASH diet (Dietary Approaches to Stop Hypertension)
                        </li>
                        <li className="flex items-center">
                          <span className="mr-2 h-2 w-2 rounded-full bg-purple-500" />
                          30 minutes of moderate exercise 5 days per week
                        </li>
                        <li className="flex items-center">
                          <span className="mr-2 h-2 w-2 rounded-full bg-purple-500" />
                          Stress reduction techniques (meditation, deep breathing)
                        </li>
                        <li className="flex items-center">
                          <span className="mr-2 h-2 w-2 rounded-full bg-purple-500" />
                          Limit alcohol consumption to 1 drink per day
                        </li>
                      </ul>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium">Monitoring</h4>
                      <ul className="mt-1 space-y-1 text-sm">
                        <li className="flex items-center">
                          <span className="mr-2 h-2 w-2 rounded-full bg-orange-500" />
                          Measure blood pressure twice daily (morning and evening)
                        </li>
                        <li className="flex items-center">
                          <span className="mr-2 h-2 w-2 rounded-full bg-orange-500" />
                          Log readings in the HealthConnect app
                        </li>
                        <li className="flex items-center">
                          <span className="mr-2 h-2 w-2 rounded-full bg-orange-500" />
                          Weekly weight check
                        </li>
                      </ul>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium">Follow-up</h4>
                      <ul className="mt-1 space-y-1 text-sm">
                        <li className="flex items-center">
                          <span className="mr-2 h-2 w-2 rounded-full bg-red-500" />
                          Virtual check-in: May 15, 2023
                        </li>
                        <li className="flex items-center">
                          <span className="mr-2 h-2 w-2 rounded-full bg-red-500" />
                          In-person follow-up: July 15, 2023
                        </li>
                      </ul>
                    </div>

                    <div className="flex justify-end gap-2">
                      <Button variant="outline" size="sm">
                        Edit Plan
                      </Button>
                      <Button size="sm">Share with Patient</Button>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Patient Communication</CardTitle>
                  <CardDescription>Send messages regarding the health plan</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="rounded-lg border p-3">
                      <div className="flex items-center gap-2">
                        <Avatar className="h-8 w-8">
                          <AvatarImage src="/placeholder-user.jpg" alt="Sarah Johnson" />
                          <AvatarFallback>SJ</AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="text-sm font-medium">Sarah Johnson</p>
                          <p className="text-xs text-muted-foreground">April 16, 2023 • 10:23 AM</p>
                        </div>
                      </div>
                      <p className="mt-2 text-sm">
                        I've been following the plan, but I'm having trouble keeping my sodium intake low. Do you have
                        any specific recommendations for low-sodium meals?
                      </p>
                    </div>

                    <div className="rounded-lg border bg-muted p-3">
                      <div className="flex items-center gap-2">
                        <Avatar className="h-8 w-8">
                          <AvatarImage src="/placeholder-user.jpg" alt="Dr. Johnson" />
                          <AvatarFallback>DJ</AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="text-sm font-medium">Dr. Johnson</p>
                          <p className="text-xs text-muted-foreground">April 16, 2023 • 2:45 PM</p>
                        </div>
                      </div>
                      <p className="mt-2 text-sm">
                        Great question, Sarah. I'll send you a list of low-sodium recipes and meal ideas. In the
                        meantime, try to focus on fresh fruits and vegetables, and avoid processed foods as much as
                        possible. Also, herbs and spices are great for adding flavor without salt.
                      </p>
                    </div>

                    <div className="flex gap-2">
                      <Textarea placeholder="Type your message..." className="min-h-[80px]" />
                      <Button size="icon" className="self-end">
                        <Send className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="records" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Medical Records</CardTitle>
                  <CardDescription>Patient's uploaded medical documents</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="rounded-lg border p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <FileText className="h-8 w-8 text-blue-500" />
                          <div>
                            <p className="font-medium">Complete Blood Count (CBC)</p>
                            <p className="text-sm text-muted-foreground">Uploaded Apr 15, 2023</p>
                          </div>
                        </div>
                        <Badge>Abnormal</Badge>
                      </div>
                      <div className="mt-3 flex gap-2">
                        <Button variant="outline" size="sm">
                          View
                        </Button>
                        <Button variant="outline" size="sm">
                          Download
                        </Button>
                      </div>
                    </div>

                    <div className="rounded-lg border p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <FileText className="h-8 w-8 text-blue-500" />
                          <div>
                            <p className="font-medium">Chest X-Ray</p>
                            <p className="text-sm text-muted-foreground">Uploaded Mar 22, 2023</p>
                          </div>
                        </div>
                        <Badge variant="outline">Normal</Badge>
                      </div>
                      <div className="mt-3 flex gap-2">
                        <Button variant="outline" size="sm">
                          View
                        </Button>
                        <Button variant="outline" size="sm">
                          Download
                        </Button>
                      </div>
                    </div>

                    <div className="rounded-lg border p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <FileText className="h-8 w-8 text-blue-500" />
                          <div>
                            <p className="font-medium">Lipid Panel</p>
                            <p className="text-sm text-muted-foreground">Uploaded Feb 10, 2023</p>
                          </div>
                        </div>
                        <Badge>Abnormal</Badge>
                      </div>
                      <div className="mt-3 flex gap-2">
                        <Button variant="outline" size="sm">
                          View
                        </Button>
                        <Button variant="outline" size="sm">
                          Download
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="metrics" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Health Metrics</CardTitle>
                  <CardDescription>Patient's health data over time</CardDescription>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="blood-pressure">
                    <TabsList>
                      <TabsTrigger value="blood-pressure">Blood Pressure</TabsTrigger>
                      <TabsTrigger value="glucose">Blood Glucose</TabsTrigger>
                      <TabsTrigger value="weight">Weight</TabsTrigger>
                      <TabsTrigger value="activity">Activity</TabsTrigger>
                    </TabsList>
                    <TabsContent value="blood-pressure" className="pt-4">
                      <HealthMetricsChart
                        data={[
                          { date: new Date("2023-04-01"), value: 135 },
                          { date: new Date("2023-04-05"), value: 132 },
                          { date: new Date("2023-04-10"), value: 145 },
                          { date: new Date("2023-04-15"), value: 138 },
                          { date: new Date("2023-04-18"), value: 128 },
                        ]}
                        metricName="Systolic BP"
                      />
                      <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
                        <div className="rounded-lg border p-3 text-center">
                          <p className="text-sm text-muted-foreground">Average Systolic</p>
                          <p className="text-2xl font-bold">132</p>
                          <p className="text-xs text-muted-foreground">mmHg</p>
                        </div>
                        <div className="rounded-lg border p-3 text-center">
                          <p className="text-sm text-muted-foreground">Average Diastolic</p>
                          <p className="text-2xl font-bold">85</p>
                          <p className="text-xs text-muted-foreground">mmHg</p>
                        </div>
                        <div className="rounded-lg border p-3 text-center">
                          <p className="text-sm text-muted-foreground">Highest Reading</p>
                          <p className="text-2xl font-bold">145/92</p>
                          <p className="text-xs text-muted-foreground">Apr 10, 2023</p>
                        </div>
                        <div className="rounded-lg border p-3 text-center">
                          <p className="text-sm text-muted-foreground">Lowest Reading</p>
                          <p className="text-2xl font-bold">128/82</p>
                          <p className="text-xs text-muted-foreground">Apr 18, 2023</p>
                        </div>
                      </div>
                    </TabsContent>
                    <TabsContent value="glucose" className="pt-4">
                      <HealthMetricsChart
                        data={[
                          { date: new Date("2023-04-01"), value: 110 },
                          { date: new Date("2023-04-05"), value: 115 },
                          { date: new Date("2023-04-10"), value: 108 },
                          { date: new Date("2023-04-15"), value: 112 },
                          { date: new Date("2023-04-18"), value: 105 },
                        ]}
                        metricName="Blood Glucose"
                      />
                    </TabsContent>
                    <TabsContent value="weight" className="pt-4">
                      <HealthMetricsChart
                        data={[
                          { date: new Date("2023-04-01"), value: 168 },
                          { date: new Date("2023-04-05"), value: 167 },
                          { date: new Date("2023-04-10"), value: 166 },
                          { date: new Date("2023-04-15"), value: 165 },
                          { date: new Date("2023-04-18"), value: 165 },
                        ]}
                        metricName="Weight"
                      />
                    </TabsContent>
                    <TabsContent value="activity" className="pt-4">
                      <HealthMetricsChart
                        data={[
                          { date: new Date("2023-04-01"), value: 5000 },
                          { date: new Date("2023-04-05"), value: 7500 },
                          { date: new Date("2023-04-10"), value: 6200 },
                          { date: new Date("2023-04-15"), value: 8000 },
                          { date: new Date("2023-04-18"), value: 7200 },
                        ]}
                        metricName="Steps"
                      />
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="notes" className="space-y-4">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Clinical Notes</CardTitle>
                      <CardDescription>Medical observations and notes</CardDescription>
                    </div>
                    <Button size="sm">
                      <Plus className="mr-2 h-4 w-4" />
                      Add Note
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {patient.clinicalNotes.map((note) => (
                      <div key={note.id} className="rounded-lg border p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">{note.title}</p>
                            <p className="text-sm text-muted-foreground">{note.date}</p>
                          </div>
                          <Badge variant="outline">
                            <Clock className="mr-1 h-3 w-3" />
                            30 min
                          </Badge>
                        </div>
                        <div className="mt-3 space-y-2">
                          <p className="text-sm">{note.content}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  )
}

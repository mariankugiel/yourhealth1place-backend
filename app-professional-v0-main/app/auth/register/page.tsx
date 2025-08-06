"use client"

import type React from "react"

import { useState } from "react"
import Link from "next/link"
import Image from "next/image"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { useLanguage } from "@/lib/language-context"

export default function RegisterPage() {
  const router = useRouter()
  const { t } = useLanguage()
  const [isLoading, setIsLoading] = useState(false)

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    // In a real app, this would register with a backend
    // Simulating API call with timeout
    setTimeout(() => {
      setIsLoading(false)
      router.push("/auth/registration-success")
    }, 1500)
  }

  return (
    <div className="container py-8">
      <div className="flex justify-center mb-8">
        <Link href="/">
          <Image src="/images/saluso_logo.png" alt="Saluso" width={120} height={40} className="h-12 w-auto" />
        </Link>
      </div>

      <Card className="mx-auto max-w-2xl">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl text-teal-700 dark:text-teal-300">
            {t("register.title", "Healthcare Professional Registration")}
          </CardTitle>
          <CardDescription>
            {t("register.description", "Create your account to access the Saluso platform")}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleRegister} className="space-y-6">
            <div className="space-y-4">
              <h3 className="text-lg font-medium">{t("register.personalInfo", "Personal Information")}</h3>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="first-name">{t("register.firstName", "First Name")}</Label>
                  <Input id="first-name" required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="last-name">{t("register.lastName", "Last Name")}</Label>
                  <Input id="last-name" required />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="email">{t("register.email", "Email")}</Label>
                  <Input id="email" type="email" required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">{t("register.phone", "Phone Number")}</Label>
                  <Input id="phone" type="tel" required />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="password">{t("register.password", "Password")}</Label>
                  <Input id="password" type="password" required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirm-password">{t("register.confirmPassword", "Confirm Password")}</Label>
                  <Input id="confirm-password" type="password" required />
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="text-lg font-medium">{t("register.professionalInfo", "Professional Information")}</h3>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="license-number">{t("register.licenseNumber", "Medical License Number")}</Label>
                  <Input id="license-number" required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="license-state">{t("register.licenseState", "License State/Region")}</Label>
                  <Input id="license-state" required />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="specialization">{t("register.specialization", "Specialization")}</Label>
                  <Select>
                    <SelectTrigger id="specialization">
                      <SelectValue placeholder={t("register.selectSpecialization", "Select specialization")} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="family-medicine">
                        {t("register.specializations.familyMedicine", "Family Medicine")}
                      </SelectItem>
                      <SelectItem value="internal-medicine">
                        {t("register.specializations.internalMedicine", "Internal Medicine")}
                      </SelectItem>
                      <SelectItem value="cardiology">
                        {t("register.specializations.cardiology", "Cardiology")}
                      </SelectItem>
                      <SelectItem value="pediatrics">
                        {t("register.specializations.pediatrics", "Pediatrics")}
                      </SelectItem>
                      <SelectItem value="psychiatry">
                        {t("register.specializations.psychiatry", "Psychiatry")}
                      </SelectItem>
                      <SelectItem value="dermatology">
                        {t("register.specializations.dermatology", "Dermatology")}
                      </SelectItem>
                      <SelectItem value="neurology">{t("register.specializations.neurology", "Neurology")}</SelectItem>
                      <SelectItem value="orthopedics">
                        {t("register.specializations.orthopedics", "Orthopedics")}
                      </SelectItem>
                      <SelectItem value="other">{t("register.specializations.other", "Other")}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="years-practice">{t("register.yearsPractice", "Years in Practice")}</Label>
                  <Input id="years-practice" type="number" min="0" required />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="practice-name">{t("register.practiceName", "Practice/Hospital Name")}</Label>
                <Input id="practice-name" required />
              </div>

              <div className="space-y-2">
                <Label htmlFor="bio">{t("register.professionalBio", "Professional Bio")}</Label>
                <Textarea
                  id="bio"
                  placeholder={t(
                    "register.bioPlaceholder",
                    "Brief description of your professional background and expertise",
                  )}
                  className="min-h-[100px]"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="license-upload">{t("register.uploadLicense", "Upload Medical License (PDF)")}</Label>
                <Input id="license-upload" type="file" accept=".pdf" required />
                <p className="text-xs text-muted-foreground mt-1">
                  {t(
                    "register.uploadInstructions",
                    "Please upload a clear copy of your current medical license (Max size: 5MB)",
                  )}
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <input type="checkbox" id="terms" className="h-4 w-4 rounded border-gray-300" required />
                <Label htmlFor="terms" className="text-sm">
                  {t("register.agreeTermsPrefix", "I agree to the")}{" "}
                  <Link href="/terms" className="text-teal-600 hover:underline">
                    {t("register.termsOfService", "Terms of Service")}
                  </Link>{" "}
                  {t("register.agreeTermsConnector", "and")}{" "}
                  <Link href="/privacy" className="text-teal-600 hover:underline">
                    {t("register.privacyPolicy", "Privacy Policy")}
                  </Link>
                </Label>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full bg-teal-600 hover:bg-teal-700 dark:bg-teal-600 dark:hover:bg-teal-700"
              disabled={isLoading}
            >
              {isLoading ? t("register.processing", "Processing...") : t("register.registerButton", "Register")}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex justify-center">
          <p className="text-sm text-muted-foreground">
            {t("register.alreadyHaveAccount", "Already have an account?")}{" "}
            <Link href="/" className="text-teal-600 hover:underline">
              {t("register.loginLink", "Login")}
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  )
}

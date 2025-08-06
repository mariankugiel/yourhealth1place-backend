"use client"

import Link from "next/link"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { CheckCircle } from "lucide-react"
import { useLanguage } from "@/lib/language-context"

export default function RegistrationSuccessPage() {
  const { t } = useLanguage()

  return (
    <div className="container flex h-screen items-center justify-center">
      <Card className="mx-auto w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Image src="/images/saluso_logo.png" alt="Saluso" width={120} height={40} className="h-12 w-auto" />
          </div>
          <div className="flex justify-center mb-4">
            <CheckCircle className="h-16 w-16 text-green-500" />
          </div>
          <CardTitle className="text-2xl text-teal-700 dark:text-teal-300">
            {t("registrationSuccess.title", "Registration Successful!")}
          </CardTitle>
          <CardDescription>
            {t("registrationSuccess.description", "Your account has been created and is pending verification.")}
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center">
          <p className="mb-4">
            {t(
              "registrationSuccess.verificationMessage",
              "We need to verify your medical credentials before you can access the platform. This process typically takes 1-2 business days.",
            )}
          </p>
          <p>
            {t(
              "registrationSuccess.emailNotification",
              "You will receive an email notification once your account has been verified.",
            )}
          </p>
        </CardContent>
        <CardFooter className="flex justify-center">
          <Button asChild className="bg-teal-600 hover:bg-teal-700 dark:bg-teal-600 dark:hover:bg-teal-700">
            <Link href="/">{t("registrationSuccess.returnToHome", "Return to Home")}</Link>
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}

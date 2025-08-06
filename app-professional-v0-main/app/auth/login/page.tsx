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
import { useLanguage } from "@/lib/language-context"

export default function LoginPage() {
  const router = useRouter()
  const { t } = useLanguage()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    // In a real app, this would authenticate with a backend
    router.push("/professional/dashboard")
  }

  return (
    <div className="container flex h-screen items-center justify-center">
      <Card className="mx-auto w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <div className="flex items-center justify-center gap-2 mb-8">
            <Image src="/images/saluso_logo.png" alt="Saluso" width={180} height={60} className="h-16 w-auto" />
          </div>
          <CardTitle className="text-2xl text-teal-700 dark:text-teal-300">
            {t("login.title", "Healthcare Professional Login")}
          </CardTitle>
          <CardDescription>
            {t("login.description", "Enter your email and password to access your account")}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4 pt-4">
            <div className="space-y-2">
              <Label htmlFor="pro-email">{t("login.email", "Email")}</Label>
              <Input
                id="pro-email"
                type="email"
                placeholder={t("login.emailPlaceholder", "doctor@example.com")}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="pro-password">{t("login.password", "Password")}</Label>
              <Input
                id="pro-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <Button
              type="submit"
              className="w-full bg-teal-600 hover:bg-teal-700 dark:bg-teal-600 dark:hover:bg-teal-700"
            >
              {t("login.loginButton", "Login")}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col space-y-4">
          <div className="text-center text-sm">
            {t("login.noAccount", "Don't have an account?")}{" "}
            <Link href="/auth/register" className="text-teal-600 hover:underline dark:text-teal-400">
              {t("login.signUp", "Sign up")}
            </Link>
          </div>
        </CardFooter>
      </Card>
    </div>
  )
}

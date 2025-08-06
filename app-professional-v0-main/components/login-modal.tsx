"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { useLanguage } from "@/lib/language-context"

export default function LoginModal({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const { t } = useLanguage()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [open, setOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    // In a real app, this would authenticate with a backend
    // Simulating API call with timeout
    setTimeout(() => {
      setIsLoading(false)
      setOpen(false)
      // Use window.location.href for a full page navigation to ensure proper loading
      window.location.href = "/professional/dashboard"
    }, 1000)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader className="text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Image src="/images/saluso_logo.png" alt="Saluso" width={120} height={40} className="h-12 w-auto" />
          </div>
          <DialogTitle className="text-xl text-teal-700 dark:text-teal-300">
            {t("login.title", "Healthcare Professional Login")}
          </DialogTitle>
          <DialogDescription>
            {t("login.description", "Enter your credentials to access your account")}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleLogin} className="space-y-4 pt-2">
          <div className="space-y-2">
            <Label htmlFor="email">{t("login.email", "Email")}</Label>
            <Input
              id="email"
              type="email"
              placeholder={t("login.emailPlaceholder", "doctor@example.com")}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="password">{t("login.password", "Password")}</Label>
              <Button variant="link" className="h-auto p-0 text-xs" type="button">
                {t("login.forgotPassword", "Forgot password?")}
              </Button>
            </div>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <Button
            type="submit"
            className="w-full bg-teal-600 hover:bg-teal-700 dark:bg-teal-600 dark:hover:bg-teal-700"
            disabled={isLoading}
          >
            {isLoading ? t("login.loggingIn", "Logging in...") : t("login.loginButton", "Login")}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}

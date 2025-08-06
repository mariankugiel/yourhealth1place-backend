"use client"

import type React from "react"
import { useState } from "react"
import Link from "next/link"
import Image from "next/image"
import { usePathname } from "next/navigation"
import {
  Calendar,
  LayoutDashboard,
  MessageSquare,
  Settings,
  Users,
  BarChart,
  FileBox,
  HeartPulse,
  Menu,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { useLanguage } from "@/lib/language-context"
// Import the NotificationBell component
import { NotificationBell } from "@/components/professional/notifications"

interface SidebarProps extends React.HTMLAttributes<HTMLDivElement> {}

export default function Sidebar({ className, ...props }: SidebarProps) {
  const pathname = usePathname()
  const [open, setOpen] = useState(false)
  const { t } = useLanguage()

  const isActive = (path: string) => {
    return pathname?.startsWith(path)
  }

  const NavItems = () => (
    <nav className="grid items-start px-2 text-sm">
      <Link
        href="/professional/dashboard"
        className={`flex items-center gap-3 rounded-lg px-3 py-2 transition-all ${
          isActive("/professional/dashboard")
            ? "bg-teal-100 text-teal-900 dark:bg-teal-900/50 dark:text-teal-50"
            : "text-muted-foreground hover:bg-muted hover:text-foreground"
        }`}
        onClick={() => setOpen(false)}
      >
        <LayoutDashboard className="h-4 w-4" />
        {t("sidebar.dashboard") || "Dashboard"}
      </Link>
      <Link
        href="/professional/calendar"
        className={`flex items-center gap-3 rounded-lg px-3 py-2 transition-all ${
          isActive("/professional/calendar")
            ? "bg-teal-100 text-teal-900 dark:bg-teal-900/50 dark:text-teal-50"
            : "text-muted-foreground hover:bg-muted hover:text-foreground"
        }`}
        onClick={() => setOpen(false)}
      >
        <Calendar className="h-4 w-4" />
        {t("sidebar.calendar") || "Calendar"}
      </Link>
      <Link
        href="/professional/patients"
        className={`flex items-center gap-3 rounded-lg px-3 py-2 transition-all ${
          isActive("/professional/patients")
            ? "bg-teal-100 text-teal-900 dark:bg-teal-900/50 dark:text-teal-50"
            : "text-muted-foreground hover:bg-muted hover:text-foreground"
        }`}
        onClick={() => setOpen(false)}
      >
        <Users className="h-4 w-4" />
        {t("sidebar.patients") || "Patients"}
      </Link>
      <Link
        href="/professional/messages"
        className={`flex items-center gap-3 rounded-lg px-3 py-2 transition-all ${
          isActive("/professional/messages")
            ? "bg-teal-100 text-teal-900 dark:bg-teal-900/50 dark:text-teal-50"
            : "text-muted-foreground hover:bg-muted hover:text-foreground"
        }`}
        onClick={() => setOpen(false)}
      >
        <MessageSquare className="h-4 w-4" />
        {t("sidebar.messages") || "Messages"}
      </Link>
      <Link
        href="/professional/health-plans"
        className={`flex items-center gap-3 rounded-lg px-3 py-2 transition-all ${
          isActive("/professional/health-plans")
            ? "bg-teal-100 text-teal-900 dark:bg-teal-900/50 dark:text-teal-50"
            : "text-muted-foreground hover:bg-muted hover:text-foreground"
        }`}
        onClick={() => setOpen(false)}
      >
        <HeartPulse className="h-4 w-4" />
        {t("sidebar.healthPlans") || "Health Plans"}
      </Link>
      <Link
        href="/professional/documents"
        className={`flex items-center gap-3 rounded-lg px-3 py-2 transition-all ${
          isActive("/professional/documents")
            ? "bg-teal-100 text-teal-900 dark:bg-teal-900/50 dark:text-teal-50"
            : "text-muted-foreground hover:bg-muted hover:text-foreground"
        }`}
        onClick={() => setOpen(false)}
      >
        <FileBox className="h-4 w-4" />
        {t("sidebar.documents") || "Documents"}
      </Link>
      <Link
        href="/professional/statistics"
        className={`flex items-center gap-3 rounded-lg px-3 py-2 transition-all ${
          isActive("/professional/statistics")
            ? "bg-teal-100 text-teal-900 dark:bg-teal-900/50 dark:text-teal-50"
            : "text-muted-foreground hover:bg-muted hover:text-foreground"
        }`}
        onClick={() => setOpen(false)}
      >
        <BarChart className="h-4 w-4" />
        {t("sidebar.statistics") || "Statistics"}
      </Link>
      <Link
        href="/professional/settings"
        className={`flex items-center gap-3 rounded-lg px-3 py-2 transition-all ${
          isActive("/professional/settings")
            ? "bg-teal-100 text-teal-900 dark:bg-teal-900/50 dark:text-teal-50"
            : "text-muted-foreground hover:bg-muted hover:text-foreground"
        }`}
        onClick={() => setOpen(false)}
      >
        <Settings className="h-4 w-4" />
        {t("sidebar.settings") || "Settings"}
      </Link>
    </nav>
  )

  return (
    <>
      {/* Mobile Menu Button */}
      <div className="flex h-14 items-center border-b px-4 lg:hidden">
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" className="lg:hidden">
              <Menu className="h-6 w-6" />
              <span className="sr-only">{t("sidebar.toggleMenu") || "Toggle Menu"}</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-[250px] p-0">
            <div className="flex h-14 items-center border-b px-4">
              <Link
                href="/professional/dashboard"
                className="flex items-center gap-2 font-semibold"
                onClick={() => setOpen(false)}
              >
                <div className="flex items-center gap-2">
                  <Image
                    src="/images/saluso_logo.png"
                    alt="Saluso Logo"
                    width={140}
                    height={45}
                    className="h-10 w-auto"
                  />
                </div>
              </Link>
            </div>
            <div className="flex-1 overflow-auto py-2">
              <div className="px-2 mb-2">
                <NotificationBell />
              </div>
              <NavItems />
            </div>
          </SheetContent>
        </Sheet>
        <Link href="/professional/dashboard" className="flex items-center gap-2 font-semibold ml-2">
          <div className="flex items-center gap-2 px-2">
            <Image src="/images/saluso_logo.png" alt="Saluso Logo" width={140} height={45} className="h-12 w-auto" />
          </div>
        </Link>
        <div className="ml-auto flex items-center gap-2">
          <NotificationBell />
        </div>
      </div>

      {/* Desktop Sidebar */}
      <div className="hidden lg:flex h-full w-[250px] flex-col border-r bg-background">
        <div className="flex h-16 items-center border-b px-4">
          <Link href="/professional/dashboard" className="flex items-center gap-2 font-semibold">
            <div className="flex items-center gap-2 px-2">
              <Image src="/images/saluso_logo.png" alt="Saluso Logo" width={140} height={45} className="h-14 w-auto" />
            </div>
          </Link>
        </div>
        <div className="flex-1 overflow-auto py-2">
          <div className="px-4 mb-4 text-left">
            <NotificationBell />
          </div>
          <NavItems />
        </div>
      </div>
    </>
  )
}

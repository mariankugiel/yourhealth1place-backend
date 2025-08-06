"use client"

import { useState } from "react"
import { Bell } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { useLanguage } from "@/lib/language-context"
import { cn } from "@/lib/utils"

type NotificationType = "appointment" | "message" | "alert" | "system" | "document"

interface Notification {
  id: string
  type: NotificationType
  message: string
  time: string // This will be translated (e.g., "5 minutes ago")
  read: boolean
}

export function NotificationBell() {
  const { t } = useLanguage()
  const [notifications, setNotifications] = useState<Notification[]>([
    {
      id: "1",
      type: "appointment",
      message: t("notifications.appointmentMessage"),
      time: t("notifications.minutesAgo", { 0: "5" }),
      read: false,
    },
    {
      id: "2",
      type: "message",
      message: t("notifications.messageNotification"),
      time: t("notifications.hoursAgo", { 0: "2" }),
      read: false,
    },
    {
      id: "3",
      type: "alert",
      message: t("notifications.alertMessage"),
      time: t("notifications.hoursAgo", { 0: "3" }),
      read: false,
    },
    {
      id: "4",
      type: "system",
      message: t("notifications.systemMessage"),
      time: t("notifications.daysAgo", { 0: "1" }),
      read: true,
    },
    {
      id: "5",
      type: "document",
      message: t("notifications.reminderMessage"),
      time: t("notifications.daysAgo", { 0: "2" }),
      read: true,
    },
  ])

  const unreadCount = notifications.filter((n) => !n.read).length

  const markAsRead = (id: string) => {
    setNotifications(
      notifications.map((notification) => (notification.id === id ? { ...notification, read: true } : notification)),
    )
  }

  const markAllAsRead = () => {
    setNotifications(notifications.map((notification) => ({ ...notification, read: true })))
  }

  const dismissNotification = (id: string) => {
    setNotifications(notifications.filter((notification) => notification.id !== id))
  }

  const getNotificationTitle = (type: NotificationType) => {
    switch (type) {
      case "appointment":
        return t("notifications.newAppointment")
      case "message":
        return t("notifications.newMessage")
      case "alert":
        return t("notifications.patientAlert")
      case "system":
        return t("notifications.systemUpdate")
      case "document":
        return t("notifications.documentReminder")
      default:
        return ""
    }
  }

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative text-muted-foreground hover:text-foreground rounded-full border-2 border-teal-500"
          aria-label={t("sidebar.notifications")}
        >
          <Bell className="h-5 w-5 text-teal-600" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs text-white">
              {unreadCount}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80 p-0" align="end">
        <div className="flex items-center justify-between border-b p-3">
          <h3 className="font-medium">{t("notifications.title")}</h3>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-muted-foreground hover:text-foreground"
              onClick={markAllAsRead}
            >
              {t("notifications.markAllRead")}
            </Button>
          )}
        </div>
        <div className="max-h-[300px] overflow-y-auto">
          {notifications.length > 0 ? (
            <div className="divide-y">
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={cn("p-3 transition-colors hover:bg-muted/50", !notification.read && "bg-muted/30")}
                >
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <p className="text-sm font-medium">{getNotificationTitle(notification.type)}</p>
                      <p className="text-sm text-muted-foreground">{notification.message}</p>
                      <p className="text-xs text-muted-foreground">{notification.time}</p>
                    </div>
                    <div className="flex space-x-1">
                      {!notification.read && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0 text-muted-foreground"
                          onClick={() => markAsRead(notification.id)}
                        >
                          <span className="sr-only">{t("notifications.markRead")}</span>
                          <span className="h-1.5 w-1.5 rounded-full bg-teal-500" />
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 text-muted-foreground"
                        onClick={() => dismissNotification(notification.id)}
                      >
                        <span className="sr-only">{t("notifications.dismiss")}</span>
                        <span className="text-xs">×</span>
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-muted-foreground">
              <p>{t("notifications.noNotifications")}</p>
            </div>
          )}
        </div>
        <div className="border-t p-3">
          <Button variant="ghost" size="sm" className="w-full justify-center text-xs">
            {t("notifications.viewAll")}
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  )
}

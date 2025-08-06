"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { ExternalLink, FileText, Search, Send } from "lucide-react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import Link from "next/link"
import { useLanguage } from "@/lib/language-context"

// Sample messages data
const conversations = [
  {
    id: 1,
    patient: {
      id: "sarah-johnson",
      name: "Sarah Johnson",
      avatar: "/stylized-initials.png",
    },
    lastMessage: "I've been monitoring my blood pressure as you suggested.",
    timestamp: "10:30 AM",
    unread: true,
    messages: [
      {
        id: 1,
        sender: "patient",
        content: "Hello Dr. Johnson, I've been monitoring my blood pressure as you suggested.",
        timestamp: "10:30 AM",
      },
      {
        id: 2,
        sender: "doctor",
        content: "That's great to hear, Sarah. Have you noticed any patterns or concerning readings?",
        timestamp: "10:35 AM",
      },
      {
        id: 3,
        sender: "patient",
        content:
          "Yes, I've noticed it tends to be higher in the mornings. I've been taking it around 7 AM and it's usually around 140/90, but by evening it's closer to 130/85.",
        timestamp: "10:40 AM",
      },
    ],
  },
  {
    id: 2,
    patient: {
      id: "michael-chen",
      name: "Michael Chen",
      avatar: "/microphone-crowd.png",
    },
    lastMessage: "I have a question about the new medication you prescribed.",
    timestamp: "Yesterday",
    unread: false,
    messages: [
      {
        id: 1,
        sender: "patient",
        content: "I have a question about the new medication you prescribed.",
        timestamp: "Yesterday, 3:45 PM",
      },
      {
        id: 2,
        sender: "doctor",
        content: "Of course, Michael. What would you like to know?",
        timestamp: "Yesterday, 4:00 PM",
      },
      {
        id: 3,
        sender: "patient",
        content:
          "I've been experiencing some dizziness after taking it. Is this a normal side effect or should I be concerned?",
        timestamp: "Yesterday, 4:15 PM",
      },
      {
        id: 4,
        sender: "doctor",
        content:
          "Dizziness can be a side effect, but I'd like to know more about when it occurs and how severe it is. Can you provide more details?",
        timestamp: "Yesterday, 4:30 PM",
      },
    ],
  },
  {
    id: 3,
    patient: {
      id: "emily-rodriguez",
      name: "Emily Rodriguez",
      avatar: "/emergency-room-scene.png",
    },
    lastMessage: "My blood sugar readings for the past week are attached.",
    timestamp: "Apr 20",
    unread: false,
    messages: [
      {
        id: 1,
        sender: "patient",
        content: "My blood sugar readings for the past week are attached.",
        timestamp: "Apr 20, 2:15 PM",
      },
      {
        id: 2,
        sender: "doctor",
        content:
          "Thank you for sharing these, Emily. I can see your readings have been more stable. The dietary changes seem to be working well.",
        timestamp: "Apr 20, 2:30 PM",
      },
      {
        id: 3,
        sender: "patient",
        content:
          "Yes, I've been following the meal plan you suggested. I feel much better overall too. Less fatigue during the day.",
        timestamp: "Apr 20, 2:45 PM",
      },
    ],
  },
]

export function MessagesPage() {
  const { t } = useLanguage()
  const [activeConversation, setActiveConversation] = useState(conversations[0])
  const [searchTerm, setSearchTerm] = useState("")
  const [newMessage, setNewMessage] = useState("")

  const filteredConversations = conversations.filter((conversation) =>
    conversation.patient.name.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  const handleSendMessage = () => {
    if (newMessage.trim() === "") return

    // In a real app, you would send this to an API
    console.log("Sending message:", newMessage)

    // For demo purposes, we'll just update the local state
    const updatedConversations = conversations.map((conv) => {
      if (conv.id === activeConversation.id) {
        return {
          ...conv,
          messages: [
            ...conv.messages,
            {
              id: conv.messages.length + 1,
              sender: "doctor",
              content: newMessage,
              timestamp: t("messages.justNow", "Just now"),
            },
          ],
          lastMessage: newMessage,
          timestamp: t("messages.justNow", "Just now"),
        }
      }
      return conv
    })

    // Update the active conversation
    const updatedActiveConversation = updatedConversations.find((conv) => conv.id === activeConversation.id)
    if (updatedActiveConversation) {
      setActiveConversation(updatedActiveConversation)
    }

    setNewMessage("")
  }

  return (
    <div className="container py-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-teal-700 dark:text-teal-300">{t("messages.title", "Messages")}</h1>
        <p className="text-muted-foreground">{t("messages.subtitle", "Communicate with your patients")}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1">
          <Card className="h-[600px] flex flex-col">
            <CardHeader className="pb-2">
              <CardTitle>{t("messages.conversations", "Conversations")}</CardTitle>
              <CardDescription>{t("messages.manageMessages", "Manage patient messages")}</CardDescription>
              <div className="relative mt-2">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="search"
                  placeholder={t("messages.searchConversations", "Search conversations...")}
                  className="pl-8"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </CardHeader>
            <CardContent className="flex-1 overflow-hidden p-0">
              <Tabs defaultValue="all" className="w-full px-6">
                <TabsList className="w-full">
                  <TabsTrigger value="all" className="flex-1">
                    {t("messages.tabs.all", "All")}
                  </TabsTrigger>
                  <TabsTrigger value="unread" className="flex-1">
                    {t("messages.tabs.unread", "Unread")}
                  </TabsTrigger>
                  <TabsTrigger value="flagged" className="flex-1">
                    {t("messages.tabs.flagged", "Flagged")}
                  </TabsTrigger>
                </TabsList>
              </Tabs>
              <ScrollArea className="h-[calc(600px-10rem)]">
                <div className="px-6 py-2">
                  {filteredConversations.map((conversation) => (
                    <div
                      key={conversation.id}
                      className={`flex items-center gap-3 rounded-lg p-3 cursor-pointer transition-colors ${
                        activeConversation.id === conversation.id
                          ? "bg-teal-50 dark:bg-teal-950"
                          : "hover:bg-gray-50 dark:hover:bg-gray-800"
                      }`}
                      onClick={() => setActiveConversation(conversation)}
                    >
                      <Avatar>
                        <AvatarImage
                          src={conversation.patient.avatar || "/placeholder.svg"}
                          alt={conversation.patient.name}
                        />
                        <AvatarFallback>
                          {conversation.patient.name
                            .split(" ")
                            .map((n) => n[0])
                            .join("")}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <p className="font-medium truncate">{conversation.patient.name}</p>
                          <p className="text-xs text-muted-foreground">{conversation.timestamp}</p>
                        </div>
                        <p className="text-sm text-muted-foreground truncate">{conversation.lastMessage}</p>
                      </div>
                      {conversation.unread && (
                        <Badge className="bg-teal-600 dark:bg-teal-600 h-2 w-2 rounded-full p-0" />
                      )}
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        <div className="md:col-span-2">
          <Card className="h-[600px] flex flex-col">
            <CardHeader className="pb-2 flex-shrink-0">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <Avatar>
                    <AvatarImage
                      src={activeConversation?.patient.avatar || "/placeholder.svg"}
                      alt={activeConversation?.patient.name}
                    />
                    <AvatarFallback>
                      {activeConversation?.patient.name
                        .split(" ")
                        .map((n) => n[0])
                        .join("")}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <CardTitle>{activeConversation?.patient.name}</CardTitle>
                    <CardDescription>{t("messages.patientLabel", "Patient")}</CardDescription>
                  </div>
                </div>
                <Button variant="outline" size="sm" asChild>
                  <Link
                    href={`/professional/patients/${activeConversation?.patient.id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <FileText className="mr-2 h-4 w-4" />
                    {t("messages.viewPatientData", "View Patient Data")}
                    <ExternalLink className="ml-1 h-3 w-3" />
                  </Link>
                </Button>
              </div>
            </CardHeader>
            <CardContent className="flex-1 overflow-hidden p-0">
              <ScrollArea className="h-[calc(600px-10rem)]">
                <div className="flex flex-col gap-4 p-6">
                  {activeConversation?.messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.sender === "doctor" ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`max-w-[80%] rounded-lg p-3 ${
                          message.sender === "doctor"
                            ? "bg-teal-600 text-white dark:bg-teal-700"
                            : "bg-gray-100 dark:bg-gray-800"
                        }`}
                      >
                        <p className="text-sm">{message.content}</p>
                        <p className="text-xs text-right mt-1 opacity-70">{message.timestamp}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
            <CardFooter className="flex-shrink-0">
              <div className="flex w-full items-center gap-2">
                <Input
                  placeholder={t("messages.typeMessage", "Type your message...")}
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      handleSendMessage()
                    }
                  }}
                />
                <Button size="icon" onClick={handleSendMessage}>
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </CardFooter>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default MessagesPage

"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import {
  Calendar,
  Download,
  Search,
  Upload,
  Eye,
  Share2,
  File,
  FileIcon as FilePdf,
  FileImage,
  FileTextIcon as FileText2,
} from "lucide-react"
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useLanguage } from "@/lib/language-context"

// Sample documents data
const documents = [
  {
    id: "consent-form",
    title: "Patient Consent Form",
    type: "PDF",
    category: "Forms",
    lastUpdated: "Apr 15, 2025",
    size: "245 KB",
    status: "Active",
    icon: <FilePdf className="h-10 w-10 text-red-500" />,
  },
  {
    id: "medical-history",
    title: "Medical History Questionnaire",
    type: "PDF",
    category: "Forms",
    lastUpdated: "Apr 10, 2025",
    size: "320 KB",
    status: "Active",
    icon: <FilePdf className="h-10 w-10 text-red-500" />,
  },
  {
    id: "privacy-policy",
    title: "Privacy Policy",
    type: "PDF",
    category: "Legal",
    lastUpdated: "Apr 5, 2025",
    size: "180 KB",
    status: "Active",
    icon: <FilePdf className="h-10 w-10 text-red-500" />,
  },
  {
    id: "prescription-template",
    title: "Prescription Template",
    type: "DOCX",
    category: "Templates",
    lastUpdated: "Mar 28, 2025",
    size: "125 KB",
    status: "Active",
    icon: <FileText2 className="h-10 w-10 text-blue-500" />,
  },
  {
    id: "clinic-brochure",
    title: "Clinic Services Brochure",
    type: "PDF",
    category: "Marketing",
    lastUpdated: "Mar 20, 2025",
    size: "4.2 MB",
    status: "Active",
    icon: <FilePdf className="h-10 w-10 text-red-500" />,
  },
  {
    id: "patient-education",
    title: "Hypertension Education Materials",
    type: "PDF",
    category: "Education",
    lastUpdated: "Mar 15, 2025",
    size: "1.8 MB",
    status: "Active",
    icon: <FilePdf className="h-10 w-10 text-red-500" />,
  },
  {
    id: "clinic-logo",
    title: "Clinic Logo",
    type: "PNG",
    category: "Media",
    lastUpdated: "Mar 10, 2025",
    size: "350 KB",
    status: "Active",
    icon: <FileImage className="h-10 w-10 text-green-500" />,
  },
  {
    id: "referral-form",
    title: "Specialist Referral Form",
    type: "PDF",
    category: "Forms",
    lastUpdated: "Mar 5, 2025",
    size: "210 KB",
    status: "Active",
    icon: <FilePdf className="h-10 w-10 text-red-500" />,
  },
  {
    id: "lab-requisition",
    title: "Laboratory Requisition Form",
    type: "PDF",
    category: "Forms",
    lastUpdated: "Mar 1, 2025",
    size: "195 KB",
    status: "Active",
    icon: <FilePdf className="h-10 w-10 text-red-500" />,
  },
]

export default function DocumentsClientPage() {
  const { t } = useLanguage()
  const [searchTerm, setSearchTerm] = useState("")
  const [activeTab, setActiveTab] = useState("all")
  const [isUploading, setIsUploading] = useState(false)

  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch =
      doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.type.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesTab = activeTab === "all" || doc.category.toLowerCase() === activeTab.toLowerCase()
    return matchesSearch && matchesTab
  })

  const handleUpload = () => {
    setIsUploading(true)
    // Simulate API call
    setTimeout(() => {
      setIsUploading(false)
    }, 2000)
  }

  return (
    <div className="container py-6">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-teal-700 dark:text-teal-300">{t("documents.title", "Documents")}</h1>
          <p className="text-muted-foreground">{t("documents.subtitle", "Manage your clinical documents and forms")}</p>
        </div>
        <Dialog>
          <DialogTrigger asChild>
            <Button>
              <Upload className="mr-2 h-4 w-4" />
              {t("documents.uploadDocument", "Upload Document")}
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>{t("documents.uploadDocument", "Upload Document")}</DialogTitle>
              <DialogDescription>
                {t("documents.uploadDescription", "Upload a new document to your practice library.")}
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="doc-title">{t("documents.documentTitle", "Document Title")}</Label>
                <Input id="doc-title" placeholder={t("documents.titlePlaceholder", "e.g., Patient Consent Form")} />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="doc-category">{t("documents.category", "Category")}</Label>
                <Select defaultValue="forms">
                  <SelectTrigger>
                    <SelectValue placeholder={t("documents.selectCategory", "Select category")} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="forms">{t("documents.categories.forms", "Forms")}</SelectItem>
                    <SelectItem value="templates">{t("documents.categories.templates", "Templates")}</SelectItem>
                    <SelectItem value="education">{t("documents.categories.education", "Education")}</SelectItem>
                    <SelectItem value="legal">{t("documents.categories.legal", "Legal")}</SelectItem>
                    <SelectItem value="marketing">{t("documents.categories.marketing", "Marketing")}</SelectItem>
                    <SelectItem value="media">{t("documents.categories.media", "Media")}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="doc-file">{t("documents.file", "File")}</Label>
                <div className="border-2 border-dashed rounded-md p-6 text-center cursor-pointer hover:bg-muted/50">
                  <File className="mx-auto h-8 w-8 text-muted-foreground" />
                  <p className="mt-2 text-sm font-medium">
                    {t("documents.dragAndDrop", "Drag and drop your file here, or click to browse")}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {t("documents.supportedFormats", "Supports PDF, DOCX, XLSX, JPG, PNG (Max 10MB)")}
                  </p>
                  <Input id="doc-file" type="file" className="hidden" />
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button type="submit" onClick={handleUpload} disabled={isUploading}>
                {isUploading
                  ? t("documents.uploading", "Uploading...")
                  : t("documents.uploadDocument", "Upload Document")}
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
            placeholder={t("documents.searchDocuments", "Search documents...")}
            className="pl-8"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <Tabs defaultValue="all" className="w-full sm:w-auto" value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="all">{t("documents.tabs.all", "All")}</TabsTrigger>
            <TabsTrigger value="forms">{t("documents.tabs.forms", "Forms")}</TabsTrigger>
            <TabsTrigger value="templates">{t("documents.tabs.templates", "Templates")}</TabsTrigger>
            <TabsTrigger value="education">{t("documents.tabs.education", "Education")}</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredDocuments.map((doc) => (
          <Card key={doc.id} className="h-full transition-all hover:shadow-md">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  {doc.icon}
                  <div>
                    <CardTitle className="text-base">{doc.title}</CardTitle>
                    <CardDescription>
                      {doc.type} • {doc.size}
                    </CardDescription>
                  </div>
                </div>
                <Badge>{doc.category}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">
                  {t("documents.lastUpdated", "Last updated")}: {doc.lastUpdated}
                </span>
              </div>
            </CardContent>
            <CardFooter className="flex justify-between">
              <Button variant="outline" size="sm">
                <Eye className="mr-2 h-4 w-4" />
                {t("documents.view", "View")}
              </Button>
              <Button variant="outline" size="sm">
                <Download className="mr-2 h-4 w-4" />
                {t("documents.download", "Download")}
              </Button>
              <Button variant="outline" size="sm">
                <Share2 className="mr-2 h-4 w-4" />
                {t("documents.share", "Share")}
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  )
}

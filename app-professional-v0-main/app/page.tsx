"use client"

import Image from "next/image"
import Link from "next/link"
import {
  Shield,
  Database,
  Brain,
  MessageSquare,
  Users,
  Activity,
  ClipboardList,
  Lock,
  FileCheck,
  Mail,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import LoginModal from "@/components/login-modal"
import LanguageSelector from "@/components/language-selector"
import { useLanguage } from "@/lib/language-context"

export default function Home() {
  const { t } = useLanguage()

  return (
    <div className="min-h-screen bg-gradient-to-b from-teal-50 to-white dark:from-gray-900 dark:to-gray-950">
      {/* Navigation */}
      <header className="border-b border-teal-100 dark:border-teal-900">
        <div className="container mx-auto flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center">
            {/* Using direct img tag for maximum compatibility */}
            <img src="/images/logo_initial_page_professionals.png" alt="Saluso" className="h-[50px] w-auto" />
          </div>
          <nav className="hidden space-x-8 md:flex">
            <Link
              href="#features"
              className="text-sm font-medium text-teal-700 hover:text-teal-500 dark:text-teal-300 dark:hover:text-teal-400"
            >
              {t("features")}
            </Link>
            <Link
              href="#approach"
              className="text-sm font-medium text-teal-700 hover:text-teal-500 dark:text-teal-300 dark:hover:text-teal-400"
            >
              {t("approach")}
            </Link>
            <Link
              href="#security"
              className="text-sm font-medium text-teal-700 hover:text-teal-500 dark:text-teal-300 dark:hover:text-teal-400"
            >
              {t("security")}
            </Link>
          </nav>
          <div className="flex items-center space-x-4">
            <LanguageSelector />
            <LoginModal>
              <Button
                variant="ghost"
                size="sm"
                className="text-teal-700 hover:bg-teal-100 hover:text-teal-800 dark:text-teal-300 dark:hover:bg-teal-900 dark:hover:text-teal-200"
              >
                {t("Login")}
              </Button>
            </LoginModal>
            <Link href="/auth/register">
              <Button size="sm" className="bg-teal-600 hover:bg-teal-700 dark:bg-teal-600 dark:hover:bg-teal-700">
                {t("signup")}
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 sm:px-6 lg:px-8 lg:py-24">
        <div className="grid items-center gap-12 lg:grid-cols-2">
          <div>
            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
              <span className="block text-teal-600 dark:text-teal-400">{t("heroTitle1")}</span>
              <span className="block">{t("heroTitle2")}</span>
            </h1>
            <p className="mt-6 max-w-2xl text-lg text-gray-600 dark:text-gray-300">{t("heroDescription")}</p>
            <div className="mt-8 flex flex-wrap gap-4">
              <LoginModal>
                <Button
                  size="lg"
                  variant="ghost"
                  className="text-teal-700 hover:bg-teal-100 hover:text-teal-800 dark:text-teal-300 dark:hover:bg-teal-900 dark:hover:text-teal-200"
                >
                  {t("Login")}
                </Button>
              </LoginModal>
              <Link href="/auth/register">
                <Button size="lg" className="bg-teal-600 hover:bg-teal-700 dark:bg-teal-600 dark:hover:bg-teal-700">
                  {t("signup")}
                </Button>
              </Link>
            </div>
          </div>
          <div className="relative hidden lg:block">
            <Image
              src="/images/doctor-hero.png"
              alt="Healthcare Professional"
              width={500}
              height={600}
              className="mx-auto"
            />
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="bg-white py-16 dark:bg-gray-900 sm:py-24">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white sm:text-4xl">
              {t("featuresTitle")}
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-300">{t("featuresSubtitle")}</p>
          </div>
          <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {/* Feature 1 */}
            <div className="rounded-lg border border-teal-100 bg-white p-6 shadow-sm dark:border-teal-900 dark:bg-gray-800">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-md bg-teal-100 text-teal-600 dark:bg-teal-900 dark:text-teal-300">
                <Database className="h-6 w-6" />
              </div>
              <h3 className="mb-2 text-lg font-medium text-gray-900 dark:text-white">{t("centralizedRecords")}</h3>
              <p className="text-gray-600 dark:text-gray-300">{t("centralizedRecordsDesc")}</p>
            </div>

            {/* Feature 2 */}
            <div className="rounded-lg border border-teal-100 bg-white p-6 shadow-sm dark:border-teal-900 dark:bg-gray-800">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-md bg-teal-100 text-teal-600 dark:bg-teal-900 dark:text-teal-300">
                <Brain className="h-6 w-6" />
              </div>
              <h3 className="mb-2 text-lg font-medium text-gray-900 dark:text-white">{t("improvedProductivity")}</h3>
              <p className="text-gray-600 dark:text-gray-300">{t("improvedProductivityDesc")}</p>
            </div>

            {/* Feature 3 */}
            <div className="rounded-lg border border-teal-100 bg-white p-6 shadow-sm dark:border-teal-900 dark:bg-gray-800">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-md bg-teal-100 text-teal-600 dark:bg-teal-900 dark:text-teal-300">
                <MessageSquare className="h-6 w-6" />
              </div>
              <h3 className="mb-2 text-lg font-medium text-gray-900 dark:text-white">{t("seamlessCommunication")}</h3>
              <p className="text-gray-600 dark:text-gray-300">{t("seamlessCommunicationDesc")}</p>
            </div>

            {/* Feature 4 */}
            <div className="rounded-lg border border-teal-100 bg-white p-6 shadow-sm dark:border-teal-900 dark:bg-gray-800">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-md bg-teal-100 text-teal-600 dark:bg-teal-900 dark:text-teal-300">
                <Users className="h-6 w-6" />
              </div>
              <h3 className="mb-2 text-lg font-medium text-gray-900 dark:text-white">{t("moreIndependence")}</h3>
              <p className="text-gray-600 dark:text-gray-300">{t("moreIndependenceDesc")}</p>
            </div>
          </div>
        </div>
      </section>

      {/* New Approach Section */}
      <section id="approach" className="bg-teal-50 py-16 dark:bg-gray-800 sm:py-24">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white sm:text-4xl">
              {t("approachTitle")}
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-300">{t("approachSubtitle")}</p>
          </div>
          <div className="mt-12 grid gap-8 md:grid-cols-2">
            <div className="rounded-lg bg-white p-6 shadow-md dark:bg-gray-700">
              <div className="mb-4 flex items-center">
                <div className="mr-4 inline-flex h-12 w-12 items-center justify-center rounded-md bg-teal-100 text-teal-600 dark:bg-teal-900 dark:text-teal-300">
                  <Activity className="h-6 w-6" />
                </div>
                <h3 className="text-xl font-medium text-teal-700 dark:text-teal-300">{t("remoteMonitoring")}</h3>
              </div>
              <p className="text-gray-600 dark:text-gray-300">{t("remoteMonitoringDesc")}</p>
            </div>
            <div className="rounded-lg bg-white p-6 shadow-md dark:bg-gray-700">
              <div className="mb-4 flex items-center">
                <div className="mr-4 inline-flex h-12 w-12 items-center justify-center rounded-md bg-teal-100 text-teal-600 dark:bg-teal-900 dark:text-teal-300">
                  <ClipboardList className="h-6 w-6" />
                </div>
                <h3 className="text-xl font-medium text-teal-700 dark:text-teal-300">{t("personalizedCare")}</h3>
              </div>
              <p className="text-gray-600 dark:text-gray-300">{t("personalizedCareDesc")}</p>
            </div>
          </div>
          <div className="mt-8 text-center">
            <p className="mx-auto max-w-2xl text-lg text-gray-600 dark:text-gray-300">{t("approachFooter")}</p>
          </div>
        </div>
      </section>

      {/* Security Section */}
      <section id="security" className="bg-white py-16 dark:bg-gray-900 sm:py-24">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-6 flex justify-center">
              <Shield className="h-16 w-16 text-teal-600 dark:text-teal-400" />
            </div>
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white sm:text-4xl">
              {t("securityTitle")}
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-300">{t("securitySubtitle")}</p>
          </div>
          <div className="mt-12 grid gap-6 md:grid-cols-3">
            <div className="rounded-lg border border-teal-100 bg-white p-6 text-center dark:border-teal-900 dark:bg-gray-800">
              <div className="mb-4 flex justify-center">
                <Shield className="h-10 w-10 text-teal-600 dark:text-teal-400" />
              </div>
              <h3 className="mb-2 text-lg font-medium text-gray-900 dark:text-white">{t("hipaa")}</h3>
              <p className="text-gray-600 dark:text-gray-300">{t("hipaaDesc")}</p>
            </div>
            <div className="rounded-lg border border-teal-100 bg-white p-6 text-center dark:border-teal-900 dark:bg-gray-800">
              <div className="mb-4 flex justify-center">
                <Lock className="h-10 w-10 text-teal-600 dark:text-teal-400" />
              </div>
              <h3 className="mb-2 text-lg font-medium text-gray-900 dark:text-white">{t("encryption")}</h3>
              <p className="text-gray-600 dark:text-gray-300">{t("encryptionDesc")}</p>
            </div>
            <div className="rounded-lg border border-teal-100 bg-white p-6 text-center dark:border-teal-900 dark:bg-gray-800">
              <div className="mb-4 flex justify-center">
                <FileCheck className="h-10 w-10 text-teal-600 dark:text-teal-400" />
              </div>
              <h3 className="mb-2 text-lg font-medium text-gray-900 dark:text-white">{t("audits")}</h3>
              <p className="text-gray-600 dark:text-gray-300">{t("auditsDesc")}</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-teal-800 py-12 text-white dark:bg-gray-900">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center justify-between md:flex-row">
            <div className="mb-6 md:mb-0">
              <img src="/images/logo_initial_page_professionals_footnote.png" alt="Saluso" className="h-auto w-48" />
              <p className="mt-2 text-sm text-teal-100 dark:text-gray-400">{t("transforming")}</p>
            </div>
            <div className="flex items-center space-x-4">
              <a href="mailto:info@saluso.com" className="flex items-center text-teal-100 hover:text-white">
                <Mail className="mr-2 h-4 w-4" />
                info@saluso.com
              </a>
            </div>
          </div>

          <div className="mt-8 border-t border-teal-700 pt-8 dark:border-gray-700">
            <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
              <div className="flex flex-wrap gap-4">
                <Link
                  href="/privacy-policy"
                  className="text-sm text-teal-100 hover:text-white dark:text-gray-400 dark:hover:text-teal-400"
                >
                  {t("privacyPolicy")}
                </Link>
                <Link
                  href="/terms"
                  className="text-sm text-teal-100 hover:text-white dark:text-gray-400 dark:hover:text-teal-400"
                >
                  {t("terms")}
                </Link>
                <LanguageSelector />
              </div>
              <p className="text-sm text-teal-100 dark:text-gray-400">{t("copyright")}</p>
            </div>

            <div className="mt-8 rounded-lg bg-teal-700 p-4 text-center text-sm text-teal-100 dark:bg-gray-800 dark:text-gray-400">
              {t("footerNote")}
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"

export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      <div className="container mx-auto px-4 py-12 sm:px-6 lg:px-8">
        <div className="mb-8">
          <Link href="/">
            <Button variant="ghost" className="flex items-center gap-2">
              <ArrowLeft className="h-4 w-4" />
              Back to Home
            </Button>
          </Link>
        </div>

        <div className="prose prose-teal mx-auto dark:prose-invert lg:prose-lg">
          <h1>Privacy Policy</h1>

          <p>Last updated: May 2, 2025</p>

          <h2>1. Introduction</h2>
          <p>
            At Saluso, we take your privacy seriously. This Privacy Policy explains how we collect, use, disclose, and
            safeguard your information when you use our platform. Please read this privacy policy carefully. If you do
            not agree with the terms of this privacy policy, please do not access the platform.
          </p>

          <h2>2. Information We Collect</h2>
          <p>
            We collect information that you provide directly to us when you register on our platform, create or modify
            your profile, set preferences, sign-up for or make purchases through the platform.
          </p>

          <h3>Personal Information:</h3>
          <ul>
            <li>Name, email address, phone number</li>
            <li>Professional credentials and specialties</li>
            <li>Practice information</li>
          </ul>

          <h3>Health Information:</h3>
          <p>
            As a healthcare platform, we may collect and process protected health information (PHI) in accordance with
            HIPAA regulations and with appropriate consent.
          </p>

          <h2>3. How We Use Your Information</h2>
          <p>We use the information we collect to:</p>
          <ul>
            <li>Provide, maintain, and improve our services</li>
            <li>Process transactions and send related information</li>
            <li>Send administrative messages, updates, and security alerts</li>
            <li>Respond to your comments, questions, and requests</li>
            <li>Provide customer service</li>
            <li>Monitor and analyze trends, usage, and activities</li>
          </ul>

          <h2>4. Data Security</h2>
          <p>
            We implement appropriate technical and organizational measures to protect the security of your personal
            information. However, please be aware that no method of transmission over the internet or electronic storage
            is 100% secure.
          </p>

          <h2>5. HIPAA Compliance</h2>
          <p>
            As a platform that serves healthcare professionals, we are committed to maintaining HIPAA compliance. We
            implement all required safeguards for protected health information.
          </p>

          <h2>6. Changes to This Privacy Policy</h2>
          <p>
            We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new
            Privacy Policy on this page and updating the "Last Updated" date.
          </p>

          <h2>7. Contact Us</h2>
          <p>If you have any questions about this Privacy Policy, please contact us at privacy@saluso.com.</p>
        </div>
      </div>
    </div>
  )
}

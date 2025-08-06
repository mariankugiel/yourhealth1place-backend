import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"

export default function Terms() {
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
          <h1>Terms and Conditions</h1>

          <p>Last updated: May 2, 2025</p>

          <h2>1. Agreement to Terms</h2>
          <p>
            By accessing or using the Saluso platform, you agree to be bound by these Terms and Conditions and our
            Privacy Policy. If you disagree with any part of the terms, you do not have permission to access the
            platform.
          </p>

          <h2>2. Description of Service</h2>
          <p>
            Saluso provides a healthcare platform designed to connect patients with healthcare professionals and
            facilitate the management of healthcare services. Our platform includes features for appointment scheduling,
            secure messaging, health record management, and other healthcare-related services.
          </p>

          <h2>3. User Accounts</h2>
          <p>
            When you create an account with us, you must provide accurate and complete information. You are responsible
            for safeguarding the password and for all activities that occur under your account. You agree to notify us
            immediately of any unauthorized use of your account.
          </p>

          <h2>4. Healthcare Professional Responsibilities</h2>
          <p>
            If you are a healthcare professional using our platform, you represent and warrant that you hold all
            necessary licenses, certifications, and credentials required to provide healthcare services in your
            jurisdiction. You are solely responsible for the professional advice, treatment, and services that you
            provide to patients.
          </p>

          <h2>5. Intellectual Property</h2>
          <p>
            The Saluso platform and its original content, features, and functionality are owned by Saluso and are
            protected by international copyright, trademark, patent, trade secret, and other intellectual property laws.
          </p>

          <h2>6. Limitation of Liability</h2>
          <p>
            To the maximum extent permitted by law, Saluso shall not be liable for any indirect, incidental, special,
            consequential, or punitive damages, or any loss of profits or revenues, whether incurred directly or
            indirectly, or any loss of data, use, goodwill, or other intangible losses resulting from your access to or
            use of or inability to access or use the platform.
          </p>

          <h2>7. Governing Law</h2>
          <p>
            These Terms shall be governed by the laws of the jurisdiction in which Saluso is established, without regard
            to its conflict of law provisions.
          </p>

          <h2>8. Changes to Terms</h2>
          <p>
            We reserve the right to modify these terms at any time. We will provide notice of any material changes by
            posting the new Terms on the platform and updating the "Last Updated" date.
          </p>

          <h2>9. Contact Us</h2>
          <p>If you have any questions about these Terms, please contact us at legal@saluso.com.</p>
        </div>
      </div>
    </div>
  )
}

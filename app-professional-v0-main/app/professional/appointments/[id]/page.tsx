import { AppointmentDetailsPage } from "./appointment-details-client-page"

export default function AppointmentDetails({ params }: { params: { id: string } }) {
  return <AppointmentDetailsPage appointmentId={params.id} />
}

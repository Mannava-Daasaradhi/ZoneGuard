import { Routes, Route, Navigate } from 'react-router-dom'
import { NotificationProvider } from './components/Notifications'
import LandingPage from './pages/Landing'
import RiderDashboard from './pages/RiderDashboard'
import AdminDashboard from './pages/AdminDashboard'
import OnboardingPage from './pages/Onboarding'
import PolicyPage from './pages/PolicyPage'
import { ChatWidget } from './components/Chatbot'
import PulseDashboard from './features/Feature14/PulseDashboard'
import { Routes, Route, Navigate, useParams } from 'react-router-dom'

function PulseDashboardRoute() {
  const { zoneId } = useParams<{ zoneId: string }>()
  return <PulseDashboard zoneId={zoneId ?? 'hsr'} />
}

export default function App() {
  return (
    <NotificationProvider>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/rider" element={<RiderDashboard />} />
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/onboarding" element={<OnboardingPage />} />
        <Route path="/policy" element={<PolicyPage />} />
        <Route path="/pulse/:zoneId" element={<PulseDashboardRoute />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <ChatWidget />
    </NotificationProvider>
  )
}

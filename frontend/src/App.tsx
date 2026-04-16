import { Routes, Route } from 'react-router-dom'
import { NotificationProvider } from './components/Notifications'
import ErrorBoundary from './components/shared/ErrorBoundary'
import LandingPage from './pages/Landing'
import RiderDashboard from './pages/RiderDashboard'
import AdminDashboard from './pages/AdminDashboard'
import OnboardingPage from './pages/Onboarding'
import PolicyPage from './pages/PolicyPage'
import NotFound from './pages/NotFound'
import { ChatWidget } from './components/Chatbot'

export default function App() {
  return (
    <ErrorBoundary>
      <NotificationProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/rider" element={<RiderDashboard />} />
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/onboarding" element={<OnboardingPage />} />
          <Route path="/policy" element={<PolicyPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
        <ChatWidget />
      </NotificationProvider>
    </ErrorBoundary>
  )
}

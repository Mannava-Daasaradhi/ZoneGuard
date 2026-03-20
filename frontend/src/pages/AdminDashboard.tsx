import { useNavigate } from 'react-router-dom'
import { ZONES, KPIS, CLAIMS_QUEUE } from '../data/mock'
import KPIStrip from '../components/Admin/KPIStrip'
import ZoneHeatmap from '../components/Admin/ZoneHeatmap'
import QuadSignalPanel from '../components/Admin/QuadSignalPanel'
import ClaimsQueue from '../components/Admin/ClaimsQueue'

export default function AdminDashboard() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-950 border-b border-slate-800 px-4 lg:px-6 py-3 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <button
            aria-label="Go back"
            onClick={() => navigate('/')}
            className="w-8 h-8 rounded-lg flex items-center justify-center hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 bg-blue-500 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/20">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <p className="text-white font-bold text-sm leading-tight">ZoneGuard Admin</p>
              <p className="text-slate-500 text-xs">Insurer Operations Dashboard</p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2.5">
          <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
          <span className="text-slate-400 text-xs hidden sm:block">
            Live · Bengaluru · 10 zones · {new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })} IST
          </span>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 lg:px-6 py-5 space-y-5">
        <KPIStrip kpis={KPIS} />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <ZoneHeatmap zones={ZONES} />
          <QuadSignalPanel />
        </div>

        <ClaimsQueue claims={CLAIMS_QUEUE} />

        <div className="text-center pb-4">
          <p className="text-slate-600 text-xs">
            ZoneGuard v1.0 · Guidewire DEVTrails 2026 · Bengaluru pilot · 10 zones · IRDAI parametric sandbox
          </p>
        </div>
      </main>
    </div>
  )
}

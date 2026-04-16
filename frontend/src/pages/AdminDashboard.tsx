import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { ZONES, KPIS, CLAIMS_QUEUE } from '../data/mock'
import { getZones, getKPIs, getClaims, reviewClaim, getZoneSignals } from '../services/api'
import KPIStrip from '../components/Admin/KPIStrip'
import QuadSignalPanel from '../components/Admin/QuadSignalPanel'
import BengaluruZoneMap from '../components/Map/BengaluruZoneMap'
import DisruptionSimulator from '../components/Simulator/DisruptionSimulator'
import ClaimsChart from '../components/Admin/ClaimsChart'
import PayoutChart from '../components/Admin/PayoutChart'
import LossRatioWidget from '../components/Admin/LossRatioWidget'
import type { KPI, ZoneSignalData, SimulationResult, RawApiZone, RawApiClaim } from '../types'

export default function AdminDashboard() {
  const navigate = useNavigate()
  const [zones, setZones] = useState<RawApiZone[]>([])
  const [kpis, setKPIs] = useState<KPI[]>(KPIS)
  const [claims, setClaims] = useState<RawApiClaim[]>(CLAIMS_QUEUE as RawApiClaim[])
  const [selectedZoneId, setSelectedZoneId] = useState<string | null>(null)
  const [signalData, setSignalData] = useState<Record<string, ZoneSignalData>>({})
  const [apiAvailable, setApiAvailable] = useState(false)
  const [expandedClaim, setExpandedClaim] = useState<string | null>(null)
  const [claimStatuses, setClaimStatuses] = useState<Record<string, string>>({})

  useEffect(() => {
    const init = async () => {
      try {
        const z = await getZones()
        setZones(z)
        setApiAvailable(true)

        const kpiData = await getKPIs()
        if (kpiData.kpis) setKPIs(kpiData.kpis)

        const c = await getClaims({})
        if (c.length > 0) {
          setClaims(c.map((claim) => ({
            id: claim.id, zone: claim.zone_id, zone_id: claim.zone_id, rider_id: claim.rider_id,
            date: claim.created_at?.split('T')[0] || '', confidence: claim.confidence,
            signals: 3, recommendedPayout: claim.recommended_payout, recommended_payout: claim.recommended_payout,
            auditSummary: '', status: claim.status,
            exclusion_check: claim.exclusion_check, fraud_score: claim.fraud_score,
          })))
        }
      } catch {
        setApiAvailable(false)
        setZones(ZONES as RawApiZone[])
      }
    }
    init()
  }, [])

  const normalizedZones = zones.map((z) => ({
    id: z.id, name: z.name, lat: z.lat || 12.9716, lng: z.lng || 77.5946,
    riskScore: z.risk_score ?? z.riskScore ?? 50, riskTier: z.risk_tier || z.riskTier || 'medium',
    activeRiders: z.active_riders ?? z.activeRiders ?? 0, weeklyPremium: z.weekly_premium ?? z.weeklyPremium ?? 49,
  }))

  const selectedZone = normalizedZones.find(z => z.id === selectedZoneId)

  const handleZoneClick = async (zoneId: string) => {
    setSelectedZoneId(zoneId === selectedZoneId ? null : zoneId)
    if (apiAvailable && !signalData[zoneId]) {
      try {
        const signals = await getZoneSignals(zoneId)
        setSignalData(prev => ({ ...prev, [zoneId]: signals }))
      } catch { /* ignore */ }
    }
  }

  const handleSimulation = useCallback(async (result: SimulationResult) => {
    // Refresh signals for the affected zone
    if (result.signals) {
      setSignalData(prev => ({ ...prev, [result.zone.id]: result.signals }))
    }

    // Refresh claims
    if (result.claims?.length > 0) {
      setClaims(prev => [
        ...result.claims.map((c) => ({
          id: c.id, zone: result.zone.name, zone_id: result.zone.id, rider_id: c.rider_id,
          date: new Date().toISOString().split('T')[0], confidence: result.fusion.confidence,
          signals: result.fusion.signals_fired, recommendedPayout: c.recommended_payout,
          auditSummary: `Simulated ${result.scenario} — ${result.fusion.signals_fired}/4 signals fired.`,
          status: c.status, exclusion_check: c.exclusion_check, fraud_score: c.fraud_score,
        })),
        ...prev,
      ])
    }

    // Refresh KPIs
    if (apiAvailable) {
      try {
        const kpiData = await getKPIs()
        if (kpiData.kpis) setKPIs(kpiData.kpis)
      } catch { /* ignore */ }
    }
  }, [apiAvailable])

  const handleReviewClaim = async (claimId: string, action: 'approve' | 'reject') => {
    if (apiAvailable) {
      try { await reviewClaim(claimId, action) } catch { /* fallback */ }
    }
    setClaimStatuses(prev => ({ ...prev, [claimId]: action === 'approve' ? 'approved' : 'rejected' }))
  }

  const pendingClaims = claims.filter(c => {
    const status = claimStatuses[c.id] || c.status
    return status === 'pending' || status === 'pending_review'
  })

  return (
    <div className="min-h-screen bg-slate-900">
      <header className="bg-slate-950 border-b border-slate-800 px-3 sm:px-4 lg:px-6 py-3 flex items-center justify-between sticky top-0 z-[1000]">
        <div className="flex items-center gap-2 sm:gap-3">
          <button aria-label="Go back" onClick={() => navigate('/')} className="w-8 h-8 rounded-lg flex items-center justify-center hover:bg-slate-800 text-slate-400 hover:text-white transition-colors">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
          </button>
          <div className="flex items-center gap-2 sm:gap-2.5">
            <div className="w-6 h-6 sm:w-7 sm:h-7 bg-blue-500 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/20">
              <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <p className="text-white font-bold text-xs sm:text-sm leading-tight">ZoneGuard Admin</p>
              <p className="text-slate-500 text-xs hidden sm:block">Insurer Operations Dashboard</p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 sm:gap-2.5">
          <div className={`w-2 h-2 rounded-full ${apiAvailable ? 'bg-emerald-400' : 'bg-amber-400'} animate-pulse`} />
          <span className="text-slate-400 text-xs hidden sm:block">
            {apiAvailable ? 'Live' : 'Demo'} · Bengaluru · {normalizedZones.length} zones · {new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })} IST
          </span>
          <span className="text-slate-400 text-xs sm:hidden">
            {apiAvailable ? 'Live' : 'Demo'}
          </span>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-3 sm:px-4 lg:px-6 py-4 sm:py-5 space-y-4 sm:space-y-5">
        <KPIStrip kpis={kpis} />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Leaflet Choropleth Map */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-3 sm:p-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 sm:gap-0 mb-3 sm:mb-4">
              <div>
                <h2 className="text-white font-bold text-base sm:text-lg">Bengaluru Zone Risk Map</h2>
                <p className="text-slate-400 text-xs">Interactive Leaflet choropleth · Click zone for details</p>
              </div>
              <div className="flex items-center gap-2 sm:gap-3 text-xs overflow-x-auto pb-1 sm:pb-0">
                {[['#10b981', 'Low'], ['#f59e0b', 'Med'], ['#f97316', 'High'], ['#ef4444', 'Flood']].map(([color, label]) => (
                  <div key={label} className="flex items-center gap-1 flex-shrink-0">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
                    <span className="text-slate-400">{label}</span>
                  </div>
                ))}
              </div>
            </div>

            <BengaluruZoneMap
              zones={normalizedZones}
              selectedZoneId={selectedZoneId || undefined}
              onZoneClick={handleZoneClick}
              height="320px"
              mobileHeight="240px"
              signalData={signalData}
            />

            {/* Selected zone details */}
            {selectedZone && (
              <div className="mt-3 sm:mt-4 bg-slate-900 border border-slate-700 rounded-xl p-3 sm:p-4">
                <h3 className="text-white font-bold text-sm sm:text-base mb-2">{selectedZone.name}</h3>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div><span className="text-slate-400">Risk Score</span><p className="text-white font-bold">{selectedZone.riskScore}/100</p></div>
                  <div><span className="text-slate-400">Premium</span><p className="text-white font-bold">₹{selectedZone.weeklyPremium}/wk</p></div>
                  <div><span className="text-slate-400">Riders</span><p className="text-white font-bold">{selectedZone.activeRiders}</p></div>
                </div>
                {signalData[selectedZone.id] && (
                  <div className="mt-3 pt-3 border-t border-slate-700">
                    <p className={`text-xs font-bold ${signalData[selectedZone.id].is_disrupted ? 'text-red-400' : 'text-emerald-400'}`}>
                      {signalData[selectedZone.id].is_disrupted ? `⚠ DISRUPTION — ${signalData[selectedZone.id].confidence}` : '✓ All signals normal'}
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* QuadSignal Panel */}
          <QuadSignalPanel />
        </div>

        {/* Disruption Simulator */}
        <DisruptionSimulator
          zones={normalizedZones.map(z => ({ id: z.id, name: z.name }))}
          onSimulationTriggered={handleSimulation}
        />

        {/* Analytics Charts Section */}
        <div className="space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-white font-bold text-lg">Analytics</h2>
              <p className="text-slate-400 text-xs">Weekly performance metrics and trends</p>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <span>Last 7 days</span>
            </div>
          </div>

          {/* Two-column grid for charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <ClaimsChart />
            <PayoutChart />
          </div>

          {/* Loss Ratio Widget - Full width on mobile, centered on desktop */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            <div className="lg:col-start-2">
              <LossRatioWidget />
            </div>
          </div>
        </div>

        {/* Claims Queue */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-3 sm:p-5">
          <div className="flex items-center justify-between mb-3 sm:mb-4">
            <div>
              <h2 className="text-white font-bold text-base sm:text-lg">Claims Queue</h2>
              <p className="text-slate-400 text-xs">Review claims · Gemini AI audit reports included</p>
            </div>
            {pendingClaims.length > 0 && (
              <span className="bg-amber-500/20 text-amber-400 border border-amber-500/30 text-xs font-bold px-2.5 py-1 rounded-full">
                {pendingClaims.length} pending
              </span>
            )}
          </div>

          <div className="space-y-2.5">
            {claims.map((claim) => {
              const status = claimStatuses[claim.id] || claim.status
              const isPending = status === 'pending' || status === 'pending_review'
              return (
                <div key={claim.id} className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden">
                  <button
                    className="w-full p-3 sm:p-4 flex items-center justify-between text-left hover:bg-slate-800/50 transition-colors"
                    onClick={() => setExpandedClaim(expandedClaim === claim.id ? null : claim.id)}
                  >
                    <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
                      <div className={`w-2 h-2 rounded-full flex-shrink-0 ${isPending ? 'bg-amber-400 animate-pulse' : status === 'approved' ? 'bg-emerald-400' : 'bg-red-400'}`} />
                      <div className="min-w-0">
                        <p className="text-white font-semibold text-sm truncate">{claim.zone || claim.zone_id}</p>
                        <p className="text-slate-400 text-xs truncate">{claim.date} · {claim.confidence} · ₹{(claim.recommendedPayout || claim.recommended_payout || 0).toLocaleString()}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0 ml-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full border capitalize ${
                        isPending ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' :
                        status === 'approved' ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' :
                        'bg-red-500/20 text-red-400 border-red-500/30'
                      }`}>{status}</span>
                      <svg className={`w-4 h-4 text-slate-500 transition-transform ${expandedClaim === claim.id ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </button>

                  {expandedClaim === claim.id && (
                    <div className="px-3 sm:px-4 pb-3 sm:pb-4 border-t border-slate-800">
                      {/* Exclusion check results */}
                      {claim.exclusion_check && (
                        <div className="mt-3 bg-slate-800 rounded-xl p-3">
                          <p className={`text-xs font-bold mb-1 ${claim.exclusion_check.passed ? 'text-emerald-400' : 'text-red-400'}`}>
                            Exclusion Check: {claim.exclusion_check.passed ? 'PASSED' : 'TRIGGERED'}
                          </p>
                          <p className="text-slate-400 text-xs">
                            {claim.exclusion_check.exclusions_evaluated?.length || 10} exclusions evaluated
                            {claim.exclusion_check.exclusions_triggered?.length > 0 && (
                              <span className="text-red-400"> · {claim.exclusion_check.exclusions_triggered.map((e) => e.name).join(', ')}</span>
                            )}
                          </p>
                        </div>
                      )}

                      {/* Fraud score */}
                      {claim.fraud_score !== undefined && (
                        <div className="mt-2 flex items-center gap-2 text-xs">
                          <span className="text-slate-400">FraudShield:</span>
                          <span className={`font-bold ${claim.fraud_score > 0.65 ? 'text-red-400' : 'text-emerald-400'}`}>
                            {(claim.fraud_score * 100).toFixed(0)}% risk
                          </span>
                        </div>
                      )}

                      {/* Audit summary */}
                      {claim.auditSummary && (
                        <div className="mt-2 bg-slate-800 rounded-xl p-3">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs">🤖</span>
                            <p className="text-slate-300 text-xs font-semibold">AI Audit Report</p>
                          </div>
                          <p className="text-slate-300 text-xs leading-relaxed">{claim.auditSummary}</p>
                        </div>
                      )}

                      {isPending && (
                        <div className="flex flex-col sm:flex-row gap-2 mt-3">
                          <button onClick={() => handleReviewClaim(claim.id, 'approve')}
                            className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold py-2.5 rounded-lg transition-colors">
                            ✓ Approve Payout
                          </button>
                          <button onClick={() => handleReviewClaim(claim.id, 'reject')}
                            className="flex-1 bg-slate-700 hover:bg-slate-600 text-slate-300 text-xs font-bold py-2.5 rounded-lg transition-colors">
                            ✗ Reject
                          </button>
                        </div>
                      )}
                      {!isPending && (
                        <p className={`mt-3 text-xs text-center ${status === 'approved' ? 'text-emerald-400' : 'text-red-400'}`}>
                          {status === 'approved' ? '✓ Payout approved and disbursed' : '✗ Claim rejected'}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        <div className="text-center pb-4">
          <p className="text-slate-600 text-xs">
            ZoneGuard v2.0 · Guidewire DEVTrails 2026 · Bengaluru pilot · {normalizedZones.length} zones · IRDAI parametric sandbox
          </p>
        </div>
      </main>
    </div>
  )
}

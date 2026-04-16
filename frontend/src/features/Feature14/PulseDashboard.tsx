/**
 * ZoneGuard Pulse — Feature 14
 * PulseDashboard.tsx
 *
 * Real-time rider risk intelligence feed.
 *
 * Displays:
 *   1. QuadSignal meter (S1–S4 vs trigger threshold)
 *   2. 72-hour disruption probability bar chart
 *   3. Coverage status panel
 *   4. Zone activity signal (anonymised rider count)
 *   5. WhatsApp brief generator button
 *
 * Usage:
 *   import PulseDashboard from './features/Feature14/PulseDashboard'
 *   <PulseDashboard zoneId="hsr" />
 *
 * Route integration — see CHANGES.md for App.tsx import instructions.
 */

import { useEffect, useState, useCallback } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface SignalMeter {
  signal: string
  label: string
  value: number
  threshold_display: string
  pct_of_threshold: number
  is_breached: boolean
  alert_triggered: boolean
  recorded_at: string | null
}

interface ChartBucket {
  bucket: number
  label: string
  disruption_probability: number
  inactivity_p50: number
  rainfall_forecast_mm: number
  severity_band: 'low' | 'medium' | 'high'
}

interface CoverageStatus {
  zone_id: string
  total_riders: number
  active_policies: number
  coverage_pct: number
  expiring_within_7_days: number
  coverage_band: 'good' | 'moderate' | 'low'
}

interface ZoneActivity {
  zone_id: string
  approximate_count: number
  active_rider_band: string
  note: string
}

interface PulseSnapshot {
  zone_id: string
  zone_name: string
  generated_at: string
  quad_signal_meter: SignalMeter[]
  disruption_72h_chart: ChartBucket[]
  coverage_status: CoverageStatus
  zone_activity: ZoneActivity
}

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const FEATURE14_POLL_INTERVAL_MS = Number(
  import.meta.env.VITE_FEATURE14_POLL_INTERVAL_MS ?? 30_000
)
const ALERT_PCT = 75

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function signalColour(pct: number, breached: boolean): string {
  if (breached) return '#ef4444'   // red-500
  if (pct >= ALERT_PCT) return '#f97316'   // orange-500
  if (pct >= 50) return '#eab308'   // yellow-500
  return '#22c55e'   // green-500
}

function coverageBandColour(band: string): string {
  if (band === 'good') return 'text-green-400'
  if (band === 'moderate') return 'text-yellow-400'
  return 'text-red-400'
}

function activityBandColour(band: string): string {
  if (band === 'high') return 'text-blue-400'
  if (band === 'moderate') return 'text-cyan-400'
  if (band === 'low') return 'text-slate-400'
  return 'text-slate-500'
}

function bucketColour(severity: string): string {
  if (severity === 'high') return '#ef4444'
  if (severity === 'medium') return '#f97316'
  return '#22c55e'
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center h-40">
      <div className="animate-spin rounded-full h-10 w-10 border-4 border-blue-500 border-t-transparent" />
    </div>
  )
}

function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="rounded-lg bg-red-900/40 border border-red-700 p-4 text-red-300 text-sm">
      ⚠️ {message}
    </div>
  )
}

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl bg-slate-800 border border-slate-700 p-4 shadow-lg">
      <h3 className="text-xs font-semibold uppercase tracking-widest text-slate-400 mb-3">{title}</h3>
      {children}
    </div>
  )
}

// QuadSignal Meter
function QuadSignalMeter({ signals }: { signals: SignalMeter[] }) {
  return (
    <div className="space-y-3">
      {signals.map((s) => {
        const colour = signalColour(s.pct_of_threshold, s.is_breached)
        return (
          <div key={s.signal}>
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm font-medium text-slate-200">
                {s.signal} — {s.label}
              </span>
              <div className="flex items-center gap-2">
                {s.alert_triggered && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-orange-500/20 text-orange-300 border border-orange-500/40">
                    {s.is_breached ? 'BREACHED' : '⚡ ALERT'}
                  </span>
                )}
                <span className="text-xs text-slate-400">{s.pct_of_threshold}%</span>
              </div>
            </div>
            {/* Progress bar */}
            <div className="h-2.5 w-full bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{
                  width: `${Math.min(100, s.pct_of_threshold)}%`,
                  backgroundColor: colour,
                }}
              />
            </div>
            {/* 75% alert marker */}
            <div className="relative h-0">
              <div
                className="absolute top-0 w-px h-3 bg-orange-400/70 -mt-3"
                style={{ left: `${ALERT_PCT}%` }}
                title={`${ALERT_PCT}% alert threshold`}
              />
            </div>
            <div className="text-xs text-slate-500 mt-1">
              Threshold: {s.threshold_display}
              {s.recorded_at && (
                <span className="ml-2">
                  · {new Date(s.recorded_at).toLocaleTimeString()}
                </span>
              )}
            </div>
          </div>
        )
      })}
      <p className="text-xs text-slate-500 pt-1">
        Orange marker at {ALERT_PCT}% = push notification threshold
      </p>
    </div>
  )
}

// 72-hour chart
function DisruptionChart({ buckets }: { buckets: ChartBucket[] }) {
  const thinned = buckets.filter((_, i) => i % 2 === 0) // show every other label to avoid crowding
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={thinned} margin={{ top: 4, right: 8, left: -20, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 10, fill: '#94a3b8' }}
          interval={1}
          angle={-30}
          textAnchor="end"
          height={42}
        />
        <YAxis
          domain={[0, 100]}
          tick={{ fontSize: 10, fill: '#94a3b8' }}
          unit="%"
        />
        <Tooltip
          contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
          labelStyle={{ color: '#e2e8f0', fontSize: 12 }}
          formatter={(value: number) => [`${value}%`, 'Disruption prob.']}
        />
        <Bar dataKey="disruption_probability" radius={[3, 3, 0, 0]}>
          {thinned.map((b) => (
            <Cell key={b.bucket} fill={bucketColour(b.severity_band)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// Coverage status
function CoveragePanel({ coverage }: { coverage: CoverageStatus }) {
  const bandColour = coverageBandColour(coverage.coverage_band)
  return (
    <div className="grid grid-cols-2 gap-3">
      <div className="rounded-lg bg-slate-700/50 p-3">
        <p className="text-xs text-slate-400">Active policies</p>
        <p className="text-2xl font-bold text-white mt-1">{coverage.active_policies}</p>
        <p className="text-xs text-slate-500">of {coverage.total_riders} riders</p>
      </div>
      <div className="rounded-lg bg-slate-700/50 p-3">
        <p className="text-xs text-slate-400">Coverage</p>
        <p className={`text-2xl font-bold mt-1 ${bandColour}`}>{coverage.coverage_pct}%</p>
        <p className="text-xs text-slate-500 capitalize">{coverage.coverage_band}</p>
      </div>
      {coverage.expiring_within_7_days > 0 && (
        <div className="col-span-2 rounded-lg bg-yellow-900/30 border border-yellow-700/40 p-3">
          <p className="text-xs text-yellow-300">
            ⚠️ {coverage.expiring_within_7_days} policy/policies expire within 7 days
          </p>
        </div>
      )}
    </div>
  )
}

// Zone activity
function ActivityPanel({ activity }: { activity: ZoneActivity }) {
  const colour = activityBandColour(activity.active_rider_band)
  return (
    <div className="flex items-center gap-4">
      <div className="rounded-full bg-slate-700 p-4">
        <svg className="w-6 h-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      </div>
      <div>
        <p className="text-xs text-slate-400">Riders online (approx.)</p>
        <p className={`text-3xl font-bold ${colour}`}>~{activity.approximate_count}</p>
        <p className="text-xs text-slate-500 capitalize">{activity.active_rider_band} activity · {activity.note}</p>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

interface PulseDashboardProps {
  zoneId: string
  autoRefresh?: boolean
}

export default function PulseDashboard({
  zoneId,
  autoRefresh = true,
}: PulseDashboardProps) {
  const [snapshot, setSnapshot] = useState<PulseSnapshot | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  // WhatsApp brief state
  const [brief, setBrief] = useState<string | null>(null)
  const [briefLoading, setBriefLoading] = useState(false)
  const [briefError, setBriefError] = useState<string | null>(null)
  const [briefCopied, setBriefCopied] = useState(false)

  const fetchSnapshot = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/pulse/${zoneId}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data: PulseSnapshot = await res.json()
      setSnapshot(data)
      setError(null)
      setLastUpdated(new Date())
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch pulse data')
    } finally {
      setLoading(false)
    }
  }, [zoneId])

  useEffect(() => {
    setLoading(true)
    fetchSnapshot()
  }, [fetchSnapshot])

  useEffect(() => {
    if (!autoRefresh) return
    const id = setInterval(fetchSnapshot, FEATURE14_POLL_INTERVAL_MS)
    return () => clearInterval(id)
  }, [fetchSnapshot, autoRefresh])

  const handleGenerateBrief = async () => {
    setBriefLoading(true)
    setBriefError(null)
    setBrief(null)
    try {
      const res = await fetch(`${API_URL}/api/v1/pulse/whatsapp-brief`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ zone_id: zoneId }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setBrief(data.brief)
    } catch (err: unknown) {
      setBriefError(err instanceof Error ? err.message : 'Failed to generate brief')
    } finally {
      setBriefLoading(false)
    }
  }

  const handleCopyBrief = () => {
    if (!brief) return
    navigator.clipboard.writeText(brief).then(() => {
      setBriefCopied(true)
      setTimeout(() => setBriefCopied(false), 2000)
    })
  }

  if (loading) return <LoadingSpinner />

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-4 md:p-6">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-block w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            <span className="text-xs uppercase tracking-widest text-slate-400">Live</span>
          </div>
          <h1 className="text-2xl font-bold text-white">
            ZoneGuard Pulse
          </h1>
          <p className="text-sm text-slate-400 mt-0.5">
            {snapshot?.zone_name ?? zoneId} · Risk Intelligence Feed
          </p>
        </div>
        <div className="text-right">
          <button
            onClick={fetchSnapshot}
            className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
            title="Refresh now"
          >
            ↻ Refresh
          </button>
          {lastUpdated && (
            <p className="text-xs text-slate-500 mt-1">
              {lastUpdated.toLocaleTimeString()}
            </p>
          )}
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      {snapshot && (
        <div className="space-y-4">
          {/* QuadSignal Meter */}
          <SectionCard title="QuadSignal Meter — Signal vs Trigger Threshold">
            <QuadSignalMeter signals={snapshot.quad_signal_meter} />
          </SectionCard>

          {/* 72-hour chart */}
          <SectionCard title="72-Hour Disruption Probability (ZoneTwin v1)">
            <DisruptionChart buckets={snapshot.disruption_72h_chart} />
            <p className="text-xs text-slate-500 mt-2">
              Based on historical ZoneTwin counterfactual simulation for zone{' '}
              <span className="font-mono">{zoneId}</span>. 6-hour buckets.
            </p>
          </SectionCard>

          {/* Coverage + Activity side by side on wider screens */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <SectionCard title="Policy Coverage Status">
              <CoveragePanel coverage={snapshot.coverage_status} />
            </SectionCard>
            <SectionCard title="Zone Activity Signal">
              <ActivityPanel activity={snapshot.zone_activity} />
            </SectionCard>
          </div>

          {/* WhatsApp brief generator */}
          <SectionCard title="WhatsApp Brief Generator">
            <p className="text-xs text-slate-400 mb-3">
              Generate a plain-text brief summarising current Pulse data, ready to
              send via WhatsApp.
            </p>
            <button
              onClick={handleGenerateBrief}
              disabled={briefLoading}
              className="px-4 py-2 rounded-lg bg-green-600 hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-semibold text-white transition-colors"
            >
              {briefLoading ? 'Generating…' : '📲 Generate WhatsApp Brief'}
            </button>

            {briefError && (
              <p className="text-xs text-red-400 mt-2">⚠️ {briefError}</p>
            )}

            {brief && (
              <div className="mt-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-slate-400">{brief.length} chars</span>
                  <button
                    onClick={handleCopyBrief}
                    className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                  >
                    {briefCopied ? '✓ Copied!' : 'Copy'}
                  </button>
                </div>
                <pre className="text-xs text-slate-300 bg-slate-900 border border-slate-600 rounded-lg p-3 whitespace-pre-wrap font-mono leading-relaxed overflow-y-auto max-h-64">
                  {brief}
                </pre>
              </div>
            )}
          </SectionCard>
        </div>
      )}
    </div>
  )
}

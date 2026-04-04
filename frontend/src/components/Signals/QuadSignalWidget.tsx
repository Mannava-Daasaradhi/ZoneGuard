import { useState, useEffect, useCallback } from 'react'
import SignalIndicator from './SignalIndicator'
import type { ZoneSignalData } from '../../types'
import { getZoneSignals } from '../../services/api'

interface Props {
  zoneId: string
  initialData?: ZoneSignalData | null
  refreshInterval?: number // in milliseconds, default 30000 (30 seconds)
}

type OverallStatus = 'normal' | 'warning' | 'disruption'

function getOverallStatus(signalsFired: number): OverallStatus {
  if (signalsFired >= 3) return 'disruption'
  if (signalsFired >= 2) return 'warning'
  return 'normal'
}

function formatTimeAgo(seconds: number): string {
  if (seconds < 60) return `${seconds} second${seconds !== 1 ? 's' : ''} ago`
  const minutes = Math.floor(seconds / 60)
  return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`
}

export default function QuadSignalWidget({ 
  zoneId, 
  initialData = null, 
  refreshInterval = 30000 
}: Props) {
  const [signalData, setSignalData] = useState<ZoneSignalData | null>(initialData)
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date())
  const [secondsAgo, setSecondsAgo] = useState(0)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch signal data
  const fetchSignals = useCallback(async () => {
    if (!zoneId) return
    
    setIsRefreshing(true)
    setError(null)
    
    try {
      const data = await getZoneSignals(zoneId)
      setSignalData(data)
      setLastUpdated(new Date())
      setSecondsAgo(0)
    } catch (err) {
      setError('Failed to fetch signal data')
      console.error('Error fetching zone signals:', err)
    } finally {
      setIsRefreshing(false)
    }
  }, [zoneId])

  // Initial fetch if no initialData
  useEffect(() => {
    if (!initialData && zoneId) {
      fetchSignals()
    }
  }, [initialData, zoneId, fetchSignals])

  // Sync initialData when it changes
  useEffect(() => {
    if (initialData) {
      setSignalData(initialData)
      setLastUpdated(new Date())
      setSecondsAgo(0)
    }
  }, [initialData])

  // Auto-refresh polling
  useEffect(() => {
    if (!zoneId || refreshInterval <= 0) return
    
    const interval = setInterval(fetchSignals, refreshInterval)
    return () => clearInterval(interval)
  }, [zoneId, refreshInterval, fetchSignals])

  // Update "seconds ago" counter
  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date()
      const diff = Math.floor((now.getTime() - lastUpdated.getTime()) / 1000)
      setSecondsAgo(diff)
    }, 1000)
    
    return () => clearInterval(interval)
  }, [lastUpdated])

  // Loading state
  if (!signalData && !error) {
    return (
      <div className="bg-white rounded-2xl border border-amber-100 shadow-sm p-6">
        <div className="flex items-center justify-center gap-3 py-8">
          <div className="w-5 h-5 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-stone-500 text-sm">Loading signal data...</span>
        </div>
      </div>
    )
  }

  // Error state with fallback
  if (error && !signalData) {
    return (
      <div className="bg-white rounded-2xl border border-red-200 shadow-sm p-6">
        <div className="flex items-center gap-3 text-red-600">
          <span className="text-xl">⚠️</span>
          <div>
            <p className="font-semibold text-sm">{error}</p>
            <button 
              onClick={fetchSignals}
              className="text-xs text-red-500 hover:text-red-700 underline mt-1"
            >
              Try again
            </button>
          </div>
        </div>
      </div>
    )
  }

  const signalsFired = signalData?.signals_fired ?? 0
  const overallStatus = getOverallStatus(signalsFired)

  return (
    <div className="bg-white rounded-2xl border border-amber-100 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-4 pt-4 pb-3 border-b border-stone-100">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-xl">📡</span>
            <h2 className="text-stone-800 font-bold text-base">QuadSignal™ Status</h2>
          </div>
          <div className="flex items-center gap-2">
            {isRefreshing && (
              <div className="w-4 h-4 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
            )}
            <button
              onClick={fetchSignals}
              disabled={isRefreshing}
              className="text-stone-400 hover:text-amber-600 transition-colors disabled:opacity-50"
              aria-label="Refresh signals"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
        </div>
        <p className="text-stone-500 text-xs">
          {signalData?.zone_name || 'Zone'} · Last updated: {formatTimeAgo(secondsAgo)}
        </p>
      </div>

      {/* Overall Status Banner */}
      <div
        className={`
          px-4 py-3 flex items-center justify-between
          ${overallStatus === 'disruption' 
            ? 'bg-red-50 border-b border-red-200' 
            : overallStatus === 'warning'
              ? 'bg-amber-50 border-b border-amber-200'
              : 'bg-emerald-50 border-b border-emerald-200'
          }
        `}
      >
        <div className="flex items-center gap-3">
          <div
            className={`
              w-3 h-3 rounded-full
              ${overallStatus === 'disruption'
                ? 'bg-red-500 animate-pulse shadow-lg shadow-red-300'
                : overallStatus === 'warning'
                  ? 'bg-amber-500 animate-pulse'
                  : 'bg-emerald-500'
              }
            `}
          />
          <span
            className={`
              font-semibold text-sm
              ${overallStatus === 'disruption'
                ? 'text-red-700'
                : overallStatus === 'warning'
                  ? 'text-amber-700'
                  : 'text-emerald-700'
              }
            `}
          >
            {overallStatus === 'disruption'
              ? 'DISRUPTION DETECTED'
              : overallStatus === 'warning'
                ? `${signalsFired}/4 signals active`
                : 'All signals normal'
            }
          </span>
        </div>
        {signalData?.confidence && (
          <span
            className={`
              text-xs font-bold px-2 py-0.5 rounded-full
              ${overallStatus === 'disruption'
                ? 'bg-red-100 text-red-700'
                : overallStatus === 'warning'
                  ? 'bg-amber-100 text-amber-700'
                  : 'bg-emerald-100 text-emerald-700'
              }
            `}
          >
            {signalData.confidence}
          </span>
        )}
      </div>

      {/* 2x2 Signal Grid */}
      <div className="p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {signalData && (
            <>
              <SignalIndicator type="S1" signal={signalData.s1_environmental} />
              <SignalIndicator type="S2" signal={signalData.s2_mobility} />
              <SignalIndicator type="S3" signal={signalData.s3_economic} />
              <SignalIndicator type="S4" signal={signalData.s4_crowd} />
            </>
          )}
        </div>
      </div>

      {/* Footer with auto-refresh indicator */}
      <div className="px-4 py-3 bg-stone-50 border-t border-stone-100 flex items-center justify-between">
        <div className="flex items-center gap-2 text-stone-400 text-xs">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>Auto-refresh: {refreshInterval / 1000}s</span>
        </div>
        {signalData?.is_disrupted && (
          <span className="text-xs font-medium text-red-600">
            ⚡ Payout may be triggered
          </span>
        )}
      </div>
    </div>
  )
}

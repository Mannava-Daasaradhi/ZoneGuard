import { useState } from 'react'
import { submitEShramKYC } from '../../services/api'
import type { EShramVerificationResponse } from '../../types'

interface Props {
  riderId: string
  weeklyEarnings?: number
  onVerified?: (result: EShramVerificationResponse) => void
}

export default function EShramKYCCard({ riderId, weeklyEarnings, onVerified }: Props) {
  const [eshramId, setEshramId] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<EShramVerificationResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState(false)

  const isValidFormat = /^(UW-\d{10}-\d|\d{12})$/.test(eshramId.trim().toUpperCase())

  const handleSubmit = async () => {
    if (!isValidFormat) return
    setLoading(true)
    setError(null)
    try {
      const res = await submitEShramKYC(riderId, eshramId.trim().toUpperCase(), weeklyEarnings)
      setResult(res)
      onVerified?.(res)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Verification failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // Already verified — show compact badge
  if (result?.eshram_verified) {
    return (
      <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-emerald-100 rounded-full flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-emerald-800 font-bold text-sm">e-Shram Verified</p>
            <p className="text-emerald-600 text-xs truncate">{result.eshram_id}</p>
          </div>
          {result.eshram_income_verified && (
            <span className="text-[10px] bg-emerald-600 text-white font-bold px-2 py-0.5 rounded-full flex-shrink-0">
              Income ✓
            </span>
          )}
        </div>
        {result.income_match === 'deviation_minor' && (
          <p className="text-emerald-700 text-xs mt-2 pl-12">
            Minor earnings deviation ({result.income_deviation_pct}%) — flagged for review, coverage proceeds.
          </p>
        )}
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl border border-blue-100 shadow-sm overflow-hidden">
      {/* Header — always visible */}
      {/*
        FIX: type="button" added to prevent accidental form submission if this
        component is ever wrapped in a <form>.  Without it the browser defaults
        to type="submit" which triggers the nearest form's submit handler.
      */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 p-4 hover:bg-blue-50/50 transition-colors"
      >
        <div className="w-9 h-9 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0">
          <span className="text-lg">🏛️</span>
        </div>
        <div className="flex-1 text-left min-w-0">
          <p className="text-stone-800 font-bold text-sm">Link e-Shram ID</p>
          <p className="text-stone-500 text-xs">Optional · Faster KYC · Earnings verified</p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="text-[10px] bg-blue-100 text-blue-700 font-bold px-2 py-0.5 rounded-full">
            Phase 3
          </span>
          <svg
            className={`w-4 h-4 text-stone-400 transition-transform ${expanded ? 'rotate-180' : ''}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {/* Expanded form */}
      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-blue-50">
          <div className="pt-3">
            <p className="text-stone-500 text-xs leading-relaxed">
              Your e-Shram UAN links your identity and work history to ZoneGuard —
              enabling instant KYC, deduplication, and optional earnings verification
              against government records.
            </p>
          </div>

          {/* Benefits */}
          <div className="grid grid-cols-3 gap-2">
            {[
              { icon: '⚡', label: 'Instant KYC' },
              { icon: '🔐', label: 'Fraud-proof' },
              { icon: '✅', label: 'Income verified' },
            ].map(({ icon, label }) => (
              <div key={label} className="bg-blue-50 rounded-xl p-2 text-center">
                <p className="text-base mb-0.5">{icon}</p>
                <p className="text-blue-700 text-[10px] font-semibold">{label}</p>
              </div>
            ))}
          </div>

          {/* Input */}
          <div>
            <label className="text-xs text-stone-500 font-medium block mb-1.5">
              e-Shram UAN
            </label>
            <input
              type="text"
              value={eshramId}
              onChange={e => setEshramId(e.target.value)}
              placeholder="UW-1234567890-1"
              maxLength={16}
              className={`w-full border rounded-xl px-4 py-2.5 text-stone-800 placeholder-stone-300 focus:outline-none focus:ring-2 font-mono text-sm transition-colors ${
                eshramId && !isValidFormat
                  ? 'border-red-200 focus:ring-red-300'
                  : 'border-blue-200 focus:ring-blue-300'
              }`}
            />
            {eshramId && !isValidFormat && (
              <p className="text-red-500 text-xs mt-1">
                Format: UW-XXXXXXXXXX-X or 12-digit UAN
              </p>
            )}
            <p className="text-stone-400 text-xs mt-1">
              Find this in your e-Shram portal profile or registration certificate
            </p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-xs text-red-700">
              {error}
            </div>
          )}

          {/*
            FIX: type="button" here too — same reason as the toggle above.
            Without this, pressing Enter in the input above could trigger this
            button as a form submit in some browser/framework combinations.
          */}
          <button
            type="button"
            onClick={handleSubmit}
            disabled={loading || !isValidFormat}
            className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-blue-200 disabled:cursor-not-allowed text-white font-bold py-2.5 rounded-xl transition-colors text-sm flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                Verifying with e-Shram portal…
              </>
            ) : (
              'Verify e-Shram ID'
            )}
          </button>

          <p className="text-stone-300 text-[10px] text-center">
            Optional · Skip if you don't have an e-Shram registration
          </p>
        </div>
      )}
    </div>
  )
}

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ZONES } from '../data/mock'
import type { Zone } from '../types'

type Step = 1 | 2 | 3 | 4

const tierBadge: Record<Zone['riskTier'], string> = {
  'low':        'bg-emerald-100 text-emerald-700',
  'medium':     'bg-amber-100 text-amber-700',
  'high':       'bg-orange-100 text-orange-700',
  'flood-prone':'bg-red-100 text-red-700',
}

const tierLabel: Record<Zone['riskTier'], string> = {
  'low':        'Low Risk',
  'medium':     'Medium Risk',
  'high':       'High Risk',
  'flood-prone':'Flood-Prone',
}

export default function OnboardingPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState<Step>(1)
  const [riderId, setRiderId] = useState('')
  const [selectedZoneId, setSelectedZoneId] = useState('')
  const [earnings, setEarnings] = useState('')

  const selectedZone = ZONES.find(z => z.id === selectedZoneId)
  const dailyAvg = earnings ? Math.round(parseInt(earnings) / 7) : 0
  const perDayPayout = Math.round(dailyAvg * 0.75)

  const goBack = () => {
    if (step === 1) navigate('/')
    else setStep((step - 1) as Step)
  }

  return (
    <div className="min-h-screen bg-[#FFFBF3] flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-amber-100 px-4 py-3 flex items-center gap-3 sticky top-0 z-10">
        <button
          onClick={goBack}
          className="w-8 h-8 rounded-lg flex items-center justify-center hover:bg-amber-50 text-amber-600 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <div>
          <h1 className="text-stone-800 font-bold text-base">Get Covered in 90 Seconds</h1>
          {step <= 3 && (
            <p className="text-stone-500 text-xs">Step {step} of 3</p>
          )}
        </div>
      </header>

      {/* Progress bar */}
      {step <= 3 && (
        <div className="h-1 bg-amber-100">
          <div
            className="h-1 bg-amber-500 transition-all duration-500 ease-out"
            style={{ width: `${(step / 3) * 100}%` }}
          />
        </div>
      )}

      <main className="flex-1 flex flex-col items-center justify-center px-4 py-8">
        <div className="w-full max-w-md">

          {/* Step 1: Rider ID */}
          {step === 1 && (
            <div className="bg-white rounded-2xl border border-amber-100 shadow-sm p-6">
              <div className="text-4xl mb-4">🪪</div>
              <h2 className="text-stone-800 font-bold text-xl mb-1">What's your Rider ID?</h2>
              <p className="text-stone-500 text-sm mb-6 leading-relaxed">
                Find it in your Amazon Flex app under{' '}
                <span className="font-medium text-stone-700">Account → Partner ID</span>
              </p>
              <input
                type="text"
                value={riderId}
                onChange={e => setRiderId(e.target.value.toUpperCase())}
                placeholder="AMZFLEX-BLR-XXXXX"
                className="w-full border border-amber-200 rounded-xl px-4 py-3 text-stone-800 placeholder-stone-300 focus:outline-none focus:ring-2 focus:ring-amber-400 focus:border-transparent font-mono text-sm transition-shadow"
              />
              <p className="text-stone-400 text-xs mt-2">
                Example: AMZFLEX-BLR-04821
              </p>
              <button
                onClick={() => riderId.trim().length >= 5 && setStep(2)}
                disabled={riderId.trim().length < 5}
                className="w-full mt-5 bg-amber-500 hover:bg-amber-400 disabled:bg-amber-200 disabled:cursor-not-allowed text-white font-bold py-3 rounded-xl transition-colors"
              >
                Continue
              </button>
            </div>
          )}

          {/* Step 2: Zone selector */}
          {step === 2 && (
            <div className="bg-white rounded-2xl border border-amber-100 shadow-sm p-6">
              <div className="text-4xl mb-4">📍</div>
              <h2 className="text-stone-800 font-bold text-xl mb-1">Which zone do you primarily work in?</h2>
              <p className="text-stone-500 text-sm mb-5">Select your main delivery zone in Bengaluru</p>

              <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                {ZONES.map(zone => (
                  <button
                    key={zone.id}
                    onClick={() => setSelectedZoneId(zone.id)}
                    className={`w-full text-left px-4 py-3 rounded-xl border transition-all ${
                      selectedZoneId === zone.id
                        ? 'border-amber-400 bg-amber-50 shadow-sm shadow-amber-100'
                        : 'border-stone-100 hover:border-amber-200 hover:bg-amber-50/50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {selectedZoneId === zone.id && (
                          <div className="w-2 h-2 rounded-full bg-amber-500 flex-shrink-0" />
                        )}
                        <span className="text-stone-800 font-medium text-sm">{zone.name}</span>
                      </div>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${tierBadge[zone.riskTier]}`}>
                        ₹{zone.weeklyPremium}/wk
                      </span>
                    </div>
                    <p className="text-stone-400 text-xs mt-1 pl-4">
                      {zone.pinCode} · {tierLabel[zone.riskTier]} · ~{zone.disruptions} disruption days/yr
                    </p>
                  </button>
                ))}
              </div>

              <button
                onClick={() => selectedZoneId && setStep(3)}
                disabled={!selectedZoneId}
                className="w-full mt-5 bg-amber-500 hover:bg-amber-400 disabled:bg-amber-200 disabled:cursor-not-allowed text-white font-bold py-3 rounded-xl transition-colors"
              >
                Continue
              </button>
            </div>
          )}

          {/* Step 3: Earnings + quote */}
          {step === 3 && selectedZone && (
            <div className="bg-white rounded-2xl border border-amber-100 shadow-sm p-6">
              <div className="text-4xl mb-4">💰</div>
              <h2 className="text-stone-800 font-bold text-xl mb-1">What's your typical weekly earning?</h2>
              <p className="text-stone-500 text-sm mb-5 leading-relaxed">
                We'll use this to calculate your payout if a disruption qualifies
              </p>

              {/* Earnings input */}
              <div className="relative mb-5">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-stone-500 font-medium text-sm">₹</span>
                <input
                  type="number"
                  value={earnings}
                  onChange={e => setEarnings(e.target.value)}
                  placeholder="15000"
                  min="0"
                  className="w-full border border-amber-200 rounded-xl pl-8 pr-4 py-3 text-stone-800 placeholder-stone-300 focus:outline-none focus:ring-2 focus:ring-amber-400 focus:border-transparent transition-shadow"
                />
              </div>

              {/* Quote card */}
              <div className="bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 rounded-xl p-4">
                <p className="text-stone-500 text-xs font-semibold uppercase tracking-wide mb-3">Your Coverage Quote</p>
                {([
                  ['Zone', selectedZone.name],
                  ['Risk tier', tierLabel[selectedZone.riskTier]],
                  ['Weekly premium', `₹${selectedZone.weeklyPremium}`],
                  ['Max payout/week', `₹${selectedZone.maxWeeklyPayout.toLocaleString()}`],
                  ['Per-day payout', earnings && parseInt(earnings) > 0
                    ? `₹${perDayPayout.toLocaleString()} (75% of ₹${dailyAvg.toLocaleString()} daily avg)`
                    : '—  Enter earnings above'],
                ] as [string, string][]).map(([k, v]) => (
                  <div key={k} className="flex justify-between py-1.5 border-b border-amber-100 last:border-0">
                    <span className="text-stone-500 text-sm">{k}</span>
                    <span className="text-stone-800 font-semibold text-sm">{v}</span>
                  </div>
                ))}
              </div>

              <p className="text-stone-400 text-xs mt-3 text-center leading-relaxed">
                Premium deducted from your next Amazon Flex payout · No app download needed
              </p>

              <button
                onClick={() => setStep(4)}
                className="w-full mt-4 bg-amber-500 hover:bg-amber-400 text-white font-bold py-3 rounded-xl transition-colors"
              >
                Confirm & Activate Coverage →
              </button>
            </div>
          )}

          {/* Step 4: Success */}
          {step === 4 && selectedZone && (
            <div className="bg-white rounded-2xl border border-emerald-200 shadow-sm p-8 text-center">
              {/* Success icon */}
              <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-5">
                <svg className="w-8 h-8 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
              </div>

              <h2 className="text-stone-800 font-bold text-2xl mb-1">You're covered!</h2>
              <p className="text-stone-500 text-sm mb-1">{selectedZone.name} · ₹{selectedZone.weeklyPremium}/week</p>
              <div className="inline-flex items-center gap-1.5 bg-emerald-50 border border-emerald-200 rounded-full px-3 py-1 mb-6">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-emerald-700 text-xs font-semibold">Active now</span>
              </div>

              <p className="text-stone-500 text-sm leading-relaxed mb-2">
                If all 4 signals converge in your zone,
              </p>
              <p className="text-stone-800 font-bold text-lg mb-1">
                ₹{selectedZone.maxWeeklyPayout.toLocaleString()} lands in your UPI
              </p>
              <p className="text-stone-400 text-sm mb-8">
                automatically — within 2 hours. No claim needed.
              </p>

              {/* What's covered summary */}
              <div className="bg-stone-50 border border-stone-100 rounded-xl p-4 text-left mb-6">
                <p className="text-stone-600 text-xs font-semibold mb-2">What you're protected against</p>
                {['Flash floods & heavy rainfall (>65mm/hr)', 'Severe air pollution (AQI >300)', 'Zone curfews & transport strikes', 'NDMA-declared flood alerts'].map(item => (
                  <div key={item} className="flex items-start gap-2 py-1">
                    <span className="text-emerald-500 text-xs mt-0.5">✓</span>
                    <span className="text-stone-600 text-xs">{item}</span>
                  </div>
                ))}
              </div>

              <button
                onClick={() => navigate('/rider')}
                className="w-full bg-amber-500 hover:bg-amber-400 text-white font-bold py-3 rounded-xl transition-colors"
              >
                View My Dashboard
              </button>
              <button
                onClick={() => navigate('/')}
                className="w-full mt-2 text-stone-400 hover:text-stone-600 text-sm transition-colors py-2"
              >
                Back to home
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

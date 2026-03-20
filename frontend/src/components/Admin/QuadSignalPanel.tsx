import { useState, useEffect, useRef } from 'react'
import type { Signal, ConfidenceLevel } from '../../types'
import { QUAD_SIGNALS } from '../../data/mock'

const DEMO_STEPS = [
  { idx: 0, value: 'Rainfall: 71mm/hr ⚡', delay: 0 },
  { idx: 1, value: 'Mobility: 18% of baseline ⚡', delay: 1800 },
  { idx: 2, value: 'Orders: 22% of baseline ⚡', delay: 3400 },
  { idx: 3, value: '47/103 riders inactive (46%) ⚡', delay: 5000 },
]

const getConfidence = (fired: number): ConfidenceLevel =>
  fired === 4 ? 'HIGH' : fired === 3 ? 'MEDIUM' : fired === 2 ? 'LOW' : 'NOISE'

const confidenceConfig: Record<ConfidenceLevel, { bg: string; border: string; text: string; label: string }> = {
  HIGH:   { bg: 'bg-emerald-500/10', border: 'border-emerald-500/50', text: 'text-emerald-400', label: 'Automatic payout initiating within 2 hours' },
  MEDIUM: { bg: 'bg-amber-500/10',   border: 'border-amber-500/50',   text: 'text-amber-400',   label: '1-hour recheck scheduled' },
  LOW:    { bg: 'bg-orange-500/10',  border: 'border-orange-500/50',  text: 'text-orange-400',  label: 'Flagged for human review' },
  NOISE:  { bg: 'bg-slate-700/50',   border: 'border-slate-600',      text: 'text-slate-400',   label: 'Monitoring — no action' },
}

export default function QuadSignalPanel() {
  const [signals, setSignals] = useState<Signal[]>(QUAD_SIGNALS)
  const [isDemoRunning, setIsDemoRunning] = useState(false)
  const [payoutFired, setPayoutFired] = useState(false)
  const timers = useRef<ReturnType<typeof setTimeout>[]>([])

  const firedCount = signals.filter(s => s.status === 'firing').length
  const confidence = getConfidence(firedCount)
  const cfg = confidenceConfig[confidence]

  const runDemo = () => {
    if (isDemoRunning) return
    timers.current.forEach(clearTimeout)
    timers.current = []
    setSignals(QUAD_SIGNALS.map(s => ({ ...s, status: 'inactive' as const })))
    setPayoutFired(false)
    setIsDemoRunning(true)

    DEMO_STEPS.forEach(({ idx, value, delay }) => {
      const t = setTimeout(() => {
        setSignals(prev => prev.map((s, i) =>
          i === idx ? { ...s, status: 'firing' as const, value } : s
        ))
      }, delay)
      timers.current.push(t)
    })

    const payoutTimer = setTimeout(() => {
      setPayoutFired(true)
      setIsDemoRunning(false)
    }, 7000)
    timers.current.push(payoutTimer)
  }

  const reset = () => {
    timers.current.forEach(clearTimeout)
    setSignals(QUAD_SIGNALS)
    setPayoutFired(false)
    setIsDemoRunning(false)
  }

  useEffect(() => () => { timers.current.forEach(clearTimeout) }, [])

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <h2 className="text-white font-bold text-lg">QuadSignal Fusion Engine</h2>
          <p className="text-slate-400 text-xs">HSR Layout · 2-hour rolling window · 15-min refresh</p>
        </div>
        <div className="flex gap-2">
          {!isDemoRunning && !payoutFired && (
            <button
              onClick={runDemo}
              className="bg-amber-500 hover:bg-amber-400 text-white font-bold text-xs px-4 py-2 rounded-lg transition-colors shadow-lg shadow-amber-500/20"
            >
              ▶ TRIGGER DEMO
            </button>
          )}
          {(isDemoRunning || payoutFired) && (
            <button
              onClick={reset}
              className="bg-slate-700 hover:bg-slate-600 text-slate-300 text-xs px-4 py-2 rounded-lg transition-colors"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Signal cards */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {signals.map((sig) => (
          <div
            key={sig.id}
            className={`rounded-xl border p-3 transition-all duration-700 ${
              sig.status === 'firing'
                ? 'bg-amber-500/10 border-amber-500/60 shadow-lg shadow-amber-500/10'
                : 'bg-slate-900 border-slate-700'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-400 text-xs font-bold tracking-wide">{sig.id}</span>
              <div className={`w-2.5 h-2.5 rounded-full transition-colors duration-500 ${
                sig.status === 'firing' ? 'bg-amber-400 animate-pulse' : 'bg-slate-600'
              }`} />
            </div>
            <p className={`font-semibold text-sm mb-0.5 transition-colors duration-500 ${
              sig.status === 'firing' ? 'text-amber-300' : 'text-white'
            }`}>
              {sig.name}
            </p>
            <p className="text-slate-500 text-xs mb-2">{sig.description}</p>
            <div className="border-t border-slate-700/50 pt-2">
              <p className={`text-xs transition-colors duration-500 ${
                sig.status === 'firing' ? 'text-amber-400 font-medium' : 'text-slate-400'
              }`}>
                {sig.value}
              </p>
              <p className="text-slate-600 text-xs">Threshold: {sig.threshold}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Confidence indicator */}
      <div className={`border rounded-xl px-4 py-3 flex items-center justify-between transition-all duration-700 ${cfg.bg} ${cfg.border}`}>
        <div>
          <p className={`font-bold text-sm ${cfg.text}`}>
            {firedCount}/4 signals · Confidence: {confidence}
          </p>
          <p className={`text-xs mt-0.5 opacity-70 ${cfg.text}`}>{cfg.label}</p>
        </div>
        <span className="text-2xl">
          {firedCount === 4 ? '⚡' : firedCount >= 3 ? '⚠️' : firedCount >= 2 ? '🔍' : '📡'}
        </span>
      </div>

      {/* AUTO-PAYOUT banner */}
      {payoutFired && (
        <div className="mt-4 bg-emerald-500/15 border border-emerald-400/60 rounded-xl p-4 flex items-center justify-between">
          <div>
            <p className="text-emerald-400 font-bold text-sm">⚡ AUTO-PAYOUT TRIGGERED</p>
            <p className="text-emerald-300 text-xs mt-1">
              142 riders · HSR Layout · ₹1,950 each · Total: ₹2,76,900 · Disbursing via UPI...
            </p>
          </div>
          <div className="text-right">
            <p className="text-emerald-400 font-bold text-lg">₹2.77L</p>
            <p className="text-emerald-500 text-xs">processing</p>
          </div>
        </div>
      )}

      {/* Demo running indicator */}
      {isDemoRunning && (
        <div className="mt-3 flex items-center gap-2 text-amber-400 text-xs">
          <div className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
          Demo in progress — signals firing...
        </div>
      )}
    </div>
  )
}

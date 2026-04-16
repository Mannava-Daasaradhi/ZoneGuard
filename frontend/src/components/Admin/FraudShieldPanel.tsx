import { useState } from 'react'
import { triggerFederatedRound, ringDetectionDemo } from '../../services/api'
import type { FederatedRoundResult, RingDetectionDemoResult } from '../../types'

type Tab = 'federated' | 'ring'

export default function FraudShieldPanel() {
  const [activeTab, setActiveTab] = useState<Tab>('federated')

  // Federated Learning state
  const [flLoading, setFlLoading] = useState(false)
  const [flResult, setFlResult] = useState<FederatedRoundResult | null>(null)
  const [flError, setFlError] = useState<string | null>(null)
  const [nRounds, setNRounds] = useState(3)

  // Ring Detection state
  const [ringLoading, setRingLoading] = useState(false)
  const [ringResult, setRingResult] = useState<RingDetectionDemoResult | null>(null)
  const [ringError, setRingError] = useState<string | null>(null)

  const runFederatedRound = async () => {
    setFlLoading(true)
    setFlError(null)
    setFlResult(null)
    try {
      const result = await triggerFederatedRound(nRounds)
      setFlResult(result)
    } catch (e) {
      setFlError(e instanceof Error ? e.message : 'Federated round failed')
    } finally {
      setFlLoading(false)
    }
  }

  const runRingDemo = async () => {
    setRingLoading(true)
    setRingError(null)
    setRingResult(null)
    try {
      const result = await ringDetectionDemo()
      setRingResult(result)
    } catch (e) {
      setRingError(e instanceof Error ? e.message : 'Ring detection demo failed')
    } finally {
      setRingLoading(false)
    }
  }

  const verdictColor = (verdict: string) => {
    if (verdict === 'genuine') return 'text-emerald-600 bg-emerald-50 border-emerald-200'
    if (verdict === 'suspicious') return 'text-amber-600 bg-amber-50 border-amber-200'
    if (verdict === 'ring_detected') return 'text-red-600 bg-red-50 border-red-200'
    return 'text-stone-500 bg-stone-50 border-stone-200'
  }

  const verdictIcon = (verdict: string) => {
    if (verdict === 'genuine') return '✓'
    if (verdict === 'suspicious') return '⚠'
    if (verdict === 'ring_detected') return '🚨'
    return '—'
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-800 to-slate-700 px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-white/10 rounded-lg flex items-center justify-center">
            <span className="text-base">🛡️</span>
          </div>
          <div>
            <h3 className="text-white font-bold text-sm">FraudShield v2</h3>
            <p className="text-slate-400 text-xs">Federated Learning · Temporal Ring Detection</p>
          </div>
          <div className="ml-auto flex items-center gap-1.5 bg-purple-500/20 border border-purple-400/30 rounded-full px-2.5 py-1">
            <div className="w-1.5 h-1.5 rounded-full bg-purple-400" />
            <span className="text-purple-300 text-xs font-medium">Phase 3</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-100">
        <button
          onClick={() => setActiveTab('federated')}
          className={`flex-1 py-2.5 text-xs font-semibold transition-colors ${
            activeTab === 'federated'
              ? 'text-slate-800 border-b-2 border-slate-700 bg-slate-50'
              : 'text-slate-500 hover:text-slate-700'
          }`}
        >
          Federated Learning
        </button>
        <button
          onClick={() => setActiveTab('ring')}
          className={`flex-1 py-2.5 text-xs font-semibold transition-colors ${
            activeTab === 'ring'
              ? 'text-slate-800 border-b-2 border-slate-700 bg-slate-50'
              : 'text-slate-500 hover:text-slate-700'
          }`}
        >
          Ring Detection Demo
        </button>
      </div>

      <div className="p-4 sm:p-5">

        {/* ── FEDERATED LEARNING TAB ── */}
        {activeTab === 'federated' && (
          <div className="space-y-4">
            <div className="bg-slate-50 rounded-xl p-3 text-xs text-slate-600 leading-relaxed border border-slate-100">
              Runs FedAvg across <strong>5 city clients</strong> (Bengaluru, Mumbai, Hyderabad, Pune, Chennai).
              Each client trains a local IsolationForest — only weight vectors are shared.
              <span className="text-purple-600 font-medium"> Raw GPS data never leaves the city. DPDP Act 2023 compliant.</span>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex-1">
                <label className="text-xs text-slate-500 font-medium block mb-1">Training rounds</label>
                <div className="flex gap-1">
                  {[1, 2, 3].map(n => (
                    <button
                      key={n}
                      onClick={() => setNRounds(n)}
                      className={`flex-1 py-1.5 rounded-lg text-xs font-bold border transition-colors ${
                        nRounds === n
                          ? 'bg-slate-700 text-white border-slate-700'
                          : 'bg-white text-slate-600 border-slate-200 hover:border-slate-400'
                      }`}
                    >
                      {n} round{n > 1 ? 's' : ''}
                    </button>
                  ))}
                </div>
              </div>
              <button
                onClick={runFederatedRound}
                disabled={flLoading}
                className="mt-5 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-300 text-white font-bold text-xs py-2 px-5 rounded-xl transition-colors flex items-center gap-2"
              >
                {flLoading ? (
                  <>
                    <div className="w-3 h-3 border border-white/40 border-t-white rounded-full animate-spin" />
                    Training…
                  </>
                ) : (
                  <>▶ Run FedAvg</>
                )}
              </button>
            </div>

            {flError && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-xs text-red-700">
                {flError}
              </div>
            )}

            {flResult && (
              <div className="space-y-3 animate-[fadeIn_0.3s_ease]">
                {/* Summary row */}
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { label: 'Rounds', value: flResult.federated_training.rounds_completed },
                    { label: 'Total samples', value: flResult.federated_training.total_samples_across_clients.toLocaleString() },
                    { label: 'Weight norm', value: flResult.federated_training.final_weight_norm.toFixed(3) },
                  ].map(({ label, value }) => (
                    <div key={label} className="bg-slate-50 rounded-xl p-2.5 text-center border border-slate-100">
                      <p className="text-slate-800 font-bold text-base">{value}</p>
                      <p className="text-slate-500 text-xs">{label}</p>
                    </div>
                  ))}
                </div>

                {/* City participants */}
                <div className="bg-slate-50 rounded-xl p-3 border border-slate-100">
                  <p className="text-slate-500 text-xs font-semibold uppercase tracking-wide mb-2">Participating Cities</p>
                  <div className="flex flex-wrap gap-1.5">
                    {flResult.federated_training.cities.map(city => (
                      <span key={city} className="bg-white border border-slate-200 text-slate-700 text-xs px-2 py-0.5 rounded-full capitalize font-medium">
                        {city}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Round-by-round */}
                <div>
                  <p className="text-slate-500 text-xs font-semibold uppercase tracking-wide mb-2">Round Progress</p>
                  {flResult.federated_training.round_summaries.map(r => (
                    <div key={r.round} className="flex items-center gap-3 py-1.5 border-b border-slate-50 last:border-0">
                      <span className="w-12 text-slate-400 text-xs">Rnd {r.round}</span>
                      <div className="flex-1 h-1.5 bg-slate-100 rounded-full">
                        <div
                          className="h-1.5 bg-slate-600 rounded-full transition-all"
                          style={{ width: `${Math.min(100, (r.global_weight_norm / 10) * 100)}%` }}
                        />
                      </div>
                      <span className="text-slate-600 text-xs font-mono w-16 text-right">
                        norm={r.global_weight_norm.toFixed(3)}
                      </span>
                      <span className="text-slate-400 text-xs">{r.elapsed_seconds}s</span>
                    </div>
                  ))}
                </div>

                {/* Privacy guarantee */}
                <div className="bg-purple-50 border border-purple-100 rounded-xl p-3">
                  <p className="text-purple-700 text-xs leading-relaxed">
                    <strong>Privacy:</strong> {flResult.federated_training.architecture.privacy_guarantee}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── RING DETECTION TAB ── */}
        {activeTab === 'ring' && (
          <div className="space-y-4">
            <div className="bg-slate-50 rounded-xl p-3 text-xs text-slate-600 leading-relaxed border border-slate-100">
              Compares a <strong>genuine disruption</strong> (Poisson-distributed claim arrivals) against
              a <strong>Telegram-coordinated fraud ring</strong> (tight temporal spike).
              Detection uses CV, clustering coefficient, and ZoneTwin z-score — no GPS data required.
            </div>

            <button
              onClick={runRingDemo}
              disabled={ringLoading}
              className="w-full bg-red-600 hover:bg-red-500 disabled:bg-red-300 text-white font-bold text-xs py-2.5 rounded-xl transition-colors flex items-center justify-center gap-2"
            >
              {ringLoading ? (
                <>
                  <div className="w-3 h-3 border border-white/40 border-t-white rounded-full animate-spin" />
                  Analysing…
                </>
              ) : (
                <>🔍 Run Ring Detection Demo</>
              )}
            </button>

            {ringError && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-xs text-red-700">
                {ringError}
              </div>
            )}

            {ringResult && (
              <div className="space-y-3 animate-[fadeIn_0.3s_ease]">
                {[
                  { label: 'Genuine Disruption', data: ringResult.genuine_disruption },
                  { label: 'Coordinated Ring', data: ringResult.coordinated_ring },
                ].map(({ label, data }) => (
                  <div key={label} className={`rounded-xl border p-3 ${verdictColor(data.analysis.verdict)}`}>
                    <div className="flex items-center justify-between mb-2">
                      <p className="font-bold text-xs">{label}</p>
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${verdictColor(data.analysis.verdict)}`}>
                        {verdictIcon(data.analysis.verdict)} {data.analysis.verdict.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>
                    <p className="text-xs opacity-70 mb-2">{data.description}</p>
                    <div className="grid grid-cols-2 gap-1.5 text-xs">
                      <div className="bg-white/60 rounded-lg p-2">
                        <p className="opacity-60 text-[10px] uppercase font-semibold">Claims</p>
                        <p className="font-bold">{data.analysis.claim_count}</p>
                      </div>
                      <div className="bg-white/60 rounded-lg p-2">
                        <p className="opacity-60 text-[10px] uppercase font-semibold">Confidence</p>
                        <p className="font-bold">{(data.analysis.confidence * 100).toFixed(0)}%</p>
                      </div>
                      <div className="bg-white/60 rounded-lg p-2">
                        <p className="opacity-60 text-[10px] uppercase font-semibold">Inter-arrival CV</p>
                        <p className="font-bold">{data.analysis.inter_arrival.cv?.toFixed(2) ?? '—'}</p>
                      </div>
                      <div className="bg-white/60 rounded-lg p-2">
                        <p className="opacity-60 text-[10px] uppercase font-semibold">Cluster Coeff</p>
                        <p className="font-bold">{data.analysis.clustering_coefficient.toFixed(2)}</p>
                      </div>
                    </div>
                    {data.analysis.ring_signals.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {data.analysis.ring_signals.map((sig, i) => (
                          <p key={i} className="text-[10px] opacity-80 flex gap-1">
                            <span className="opacity-40">→</span> {sig}
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                ))}

                <div className="bg-amber-50 border border-amber-200 rounded-xl p-3">
                  <p className="text-amber-800 text-xs leading-relaxed">{ringResult.takeaway}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

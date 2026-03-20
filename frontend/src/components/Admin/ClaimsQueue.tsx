import { useState } from 'react'
import type { ClaimEvent } from '../../types'

interface Props { claims: ClaimEvent[] }

const statusStyle = {
  pending:  'bg-amber-500/20 text-amber-400 border-amber-500/30',
  approved: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  rejected: 'bg-red-500/20 text-red-400 border-red-500/30',
}

export default function ClaimsQueue({ claims }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null)
  const [statuses, setStatuses] = useState<Record<string, ClaimEvent['status']>>(
    Object.fromEntries(claims.map(c => [c.id, c.status]))
  )

  const pending = Object.values(statuses).filter(s => s === 'pending').length

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-white font-bold text-lg">MEDIUM-Confidence Claims Queue</h2>
          <p className="text-slate-400 text-xs">Requires human review · Claude AI audit reports included</p>
        </div>
        {pending > 0 && (
          <span className="bg-amber-500/20 text-amber-400 border border-amber-500/30 text-xs font-bold px-2.5 py-1 rounded-full">
            {pending} pending
          </span>
        )}
      </div>

      <div className="space-y-2.5">
        {claims.map((claim) => {
          const status = statuses[claim.id] ?? claim.status
          return (
            <div key={claim.id} className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden">
              <button
                className="w-full p-4 flex items-center justify-between text-left hover:bg-slate-800/50 transition-colors"
                onClick={() => setExpanded(expanded === claim.id ? null : claim.id)}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                    status === 'pending' ? 'bg-amber-400 animate-pulse' :
                    status === 'approved' ? 'bg-emerald-400' : 'bg-red-400'
                  }`} />
                  <div className="text-left">
                    <p className="text-white font-semibold text-sm">{claim.zone}</p>
                    <p className="text-slate-400 text-xs">
                      {claim.date} · {claim.signals}/4 signals · ₹{claim.recommendedPayout.toLocaleString()} recommended
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full border capitalize ${statusStyle[status]}`}>
                    {status}
                  </span>
                  <svg
                    className={`w-4 h-4 text-slate-500 transition-transform duration-200 ${expanded === claim.id ? 'rotate-180' : ''}`}
                    fill="none" viewBox="0 0 24 24" stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </button>

              {expanded === claim.id && (
                <div className="px-4 pb-4 border-t border-slate-800">
                  <div className="mt-3 bg-slate-800 rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs">🤖</span>
                      <p className="text-slate-300 text-xs font-semibold">Claude AI Audit Report</p>
                      <span className="text-xs text-slate-500">(claude-sonnet · generated in 1.2s)</span>
                    </div>
                    <p className="text-slate-300 text-xs leading-relaxed">{claim.auditSummary}</p>
                  </div>

                  {status === 'pending' && (
                    <div className="flex gap-2 mt-3">
                      <button
                        onClick={() => setStatuses(prev => ({ ...prev, [claim.id]: 'approved' }))}
                        className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold py-2.5 rounded-lg transition-colors"
                      >
                        ✓ Approve Payout
                      </button>
                      <button
                        onClick={() => setStatuses(prev => ({ ...prev, [claim.id]: 'rejected' }))}
                        className="flex-1 bg-slate-700 hover:bg-slate-600 text-slate-300 text-xs font-bold py-2.5 rounded-lg transition-colors"
                      >
                        ✗ Reject
                      </button>
                    </div>
                  )}
                  {status !== 'pending' && (
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
  )
}

import type { PolicyData } from '../../types'

interface Props {
  policy: PolicyData
  zoneName: string
  onRenew?: () => void
  onCancel?: () => void
}

export default function PolicyCard({ policy, zoneName, onRenew, onCancel }: Props) {
  const start = new Date(policy.coverage_start).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })
  const end = new Date(policy.coverage_end).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })
  const isActive = policy.status === 'active'

  return (
    <div className="bg-gradient-to-br from-amber-500 to-orange-500 rounded-2xl p-6 text-white shadow-lg shadow-amber-200">
      <div className="flex items-start justify-between mb-5">
        <div>
          <p className="text-amber-100 text-xs font-medium uppercase tracking-wide mb-1">Weekly Coverage</p>
          <h2 className="text-2xl font-bold">{zoneName}</h2>
          <p className="text-amber-200 text-sm">Policy {policy.id}</p>
        </div>
        <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold ${
          isActive ? 'bg-white/20' : 'bg-white/10 text-amber-200'
        }`}>
          {isActive && <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />}
          {policy.status.toUpperCase()}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-5">
        <div className="bg-white/15 rounded-xl p-3">
          <p className="text-amber-100 text-xs mb-1">Premium</p>
          <p className="text-white font-bold text-xl">₹{policy.weekly_premium}</p>
          <p className="text-amber-200 text-xs">per week</p>
        </div>
        <div className="bg-white/15 rounded-xl p-3">
          <p className="text-amber-100 text-xs mb-1">Max Payout</p>
          <p className="text-white font-bold text-xl">₹{policy.max_payout.toLocaleString()}</p>
          <p className="text-amber-200 text-xs">if all 4 signals fire</p>
        </div>
      </div>

      <div className="bg-white/10 rounded-xl px-4 py-2.5 flex items-center justify-between mb-4">
        <span className="text-amber-100 text-xs">Coverage: {start} – {end}</span>
        {policy.is_forward_locked && (
          <span className="bg-white/20 text-xs font-bold px-2 py-0.5 rounded-full">
            🔒 Forward Locked · 8% off
          </span>
        )}
      </div>

      {isActive && (
        <div className="flex gap-2">
          {onRenew && (
            <button
              onClick={onRenew}
              className="flex-1 bg-white/20 hover:bg-white/30 text-white font-bold text-sm py-2 rounded-xl transition-colors"
            >
              Renew Policy
            </button>
          )}
          {onCancel && (
            <button
              onClick={onCancel}
              className="bg-white/10 hover:bg-white/20 text-amber-200 text-sm py-2 px-4 rounded-xl transition-colors"
            >
              Cancel
            </button>
          )}
        </div>
      )}
    </div>
  )
}

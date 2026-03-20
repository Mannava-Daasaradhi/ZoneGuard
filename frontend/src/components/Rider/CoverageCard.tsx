import type { Zone } from '../../types'

interface Props {
  zone: Zone
  premiumPaid: number
  maxPayout: number
  isActive: boolean
}

export default function CoverageCard({ zone, premiumPaid, maxPayout, isActive }: Props) {
  return (
    <div className="bg-gradient-to-br from-amber-500 to-orange-500 rounded-2xl p-6 text-white shadow-lg shadow-amber-200">
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <p className="text-amber-100 text-xs font-medium uppercase tracking-wide mb-1">Weekly Coverage</p>
          <h2 className="text-2xl font-bold">{zone.name}</h2>
          <p className="text-amber-200 text-sm">{zone.pinCode} · {zone.riskTier} risk zone</p>
        </div>
        <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold ${
          isActive ? 'bg-white/20' : 'bg-white/10 text-amber-200'
        }`}>
          {isActive && <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />}
          {isActive ? 'ACTIVE' : 'INACTIVE'}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 mb-5">
        <div className="bg-white/15 rounded-xl p-3">
          <p className="text-amber-100 text-xs mb-1">Premium Paid</p>
          <p className="text-white font-bold text-xl">₹{premiumPaid}</p>
          <p className="text-amber-200 text-xs">this week</p>
        </div>
        <div className="bg-white/15 rounded-xl p-3">
          <p className="text-amber-100 text-xs mb-1">Max Payout</p>
          <p className="text-white font-bold text-xl">₹{maxPayout.toLocaleString()}</p>
          <p className="text-amber-200 text-xs">if all 4 signals fire</p>
        </div>
      </div>

      {/* Zone signal live indicator */}
      <div className="bg-white/10 rounded-xl px-4 py-2.5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-300 animate-pulse" />
          <span className="text-amber-100 text-xs">4 signals monitored · Live</span>
        </div>
        <span className="text-white text-xs font-medium">
          Risk score: {zone.riskScore}/100
        </span>
      </div>
    </div>
  )
}

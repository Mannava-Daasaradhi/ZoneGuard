import { useNavigate } from 'react-router-dom'
import { RIDER, RAVI_WEEK, PAYOUTS } from '../data/mock'
import WeekTimeline from '../components/Rider/WeekTimeline'
import CoverageCard from '../components/Rider/CoverageCard'

export default function RiderDashboard() {
  const navigate = useNavigate()
  const totalEarned = RAVI_WEEK.reduce((s, d) => s + d.earnings, 0)
  const totalPayout = RAVI_WEEK.reduce((s, d) => s + (d.payoutAmount ?? 0), 0)

  return (
    <div className="min-h-screen bg-[#FFFBF3]">
      {/* Top bar */}
      <header className="bg-white border-b border-amber-100 px-4 py-3 flex items-center justify-between sticky top-0 z-10 shadow-sm">
        <div className="flex items-center gap-3">
          <button
            aria-label="Go back"
            onClick={() => navigate('/')}
            className="w-8 h-8 rounded-lg flex items-center justify-center hover:bg-amber-50 text-amber-600 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div>
            <h1 className="text-stone-800 font-bold text-base leading-tight">{RIDER.name}</h1>
            <p className="text-stone-500 text-xs">{RIDER.riderId}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 rounded-full px-3 py-1">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-emerald-700 text-xs font-semibold">Covered</span>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-6 space-y-4">
        {/* Coverage card */}
        <CoverageCard
          zone={RIDER.zone}
          premiumPaid={RIDER.zone.weeklyPremium}
          maxPayout={RIDER.zone.maxWeeklyPayout}
          isActive={RIDER.coverageActive}
        />

        {/* Summary strip */}
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'Earned this week', value: `₹${totalEarned.toLocaleString()}`, highlight: false },
            { label: 'ZG paid out', value: `₹${totalPayout.toLocaleString()}`, highlight: true },
            { label: 'Total income', value: `₹${(totalEarned + totalPayout).toLocaleString()}`, highlight: false },
          ].map(({ label, value, highlight }) => (
            <div
              key={label}
              className={`rounded-xl p-3 text-center border ${
                highlight
                  ? 'bg-emerald-50 border-emerald-200'
                  : 'bg-white border-amber-100'
              }`}
            >
              <p className={`font-bold text-sm ${highlight ? 'text-emerald-700' : 'text-stone-800'}`}>
                {value}
              </p>
              <p className="text-stone-500 text-xs mt-0.5 leading-tight">{label}</p>
            </div>
          ))}
        </div>

        {/* Week timeline */}
        <WeekTimeline week={RAVI_WEEK} />

        {/* Payout history */}
        <div className="bg-white rounded-2xl border border-amber-100 shadow-sm p-6">
          <h2 className="text-stone-800 font-bold text-lg mb-4">Payout History</h2>
          <div className="space-y-2.5">
            {PAYOUTS.map((p, i) => (
              <div
                key={p.id}
                className={`flex items-center justify-between p-3.5 rounded-xl border ${
                  i === 0
                    ? 'bg-emerald-50 border-emerald-200'
                    : 'bg-stone-50 border-stone-100'
                }`}
              >
                <div>
                  <p className="text-stone-800 font-semibold text-sm">{p.trigger}</p>
                  <p className="text-stone-500 text-xs mt-0.5">
                    {p.date} · {p.zone} · Ref: {p.upiRef}
                  </p>
                </div>
                <div className="text-right">
                  <p className={`font-bold text-sm ${i === 0 ? 'text-emerald-600' : 'text-stone-700'}`}>
                    +₹{p.amount.toLocaleString()}
                  </p>
                  <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                    p.confidence === 'HIGH'
                      ? 'bg-emerald-100 text-emerald-700'
                      : 'bg-amber-100 text-amber-700'
                  }`}>
                    {p.confidence}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Zone signal status */}
        <div className="bg-white rounded-2xl border border-amber-100 shadow-sm p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-50 rounded-xl flex items-center justify-center text-xl">
              📡
            </div>
            <div>
              <p className="text-stone-800 font-semibold text-sm">Zone Signals: Normal</p>
              <p className="text-stone-500 text-xs">All 4 signals monitored · Last checked 3 min ago</p>
            </div>
          </div>
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
        </div>

        {/* Tenure info */}
        <div className="text-center pb-4">
          <p className="text-stone-400 text-xs">
            Member for {RIDER.tenureWeeks} weeks · {RIDER.zone.name} zone ·
            ZoneGuard v1.0 · Guidewire DEVTrails 2026
          </p>
        </div>
      </main>
    </div>
  )
}

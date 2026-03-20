import type { WeekDay } from '../../types'

interface Props { week: WeekDay[] }

export default function WeekTimeline({ week }: Props) {
  const maxEarnings = 3000

  return (
    <div className="bg-white rounded-2xl border border-amber-100 shadow-sm p-6">
      <h2 className="text-stone-800 font-bold text-lg mb-1">This Week's Protection</h2>
      <p className="text-stone-500 text-sm mb-6">HSR Layout · Week of Mar 16–22, 2026</p>

      <div className="flex gap-2 items-end justify-between">
        {week.map((day) => {
          const barHeight = day.status === 'payout'
            ? 72
            : day.earnings > 0
              ? Math.max(20, Math.round((day.earnings / maxEarnings) * 72))
              : 12

          return (
            <div key={day.day} className="flex-1 flex flex-col items-center gap-2">
              {/* Top label */}
              <div className="text-center min-h-[44px] flex flex-col justify-end">
                {day.status === 'payout' && (
                  <>
                    <span className="text-emerald-600 font-bold text-sm leading-tight">
                      +₹{day.payoutAmount?.toLocaleString()}
                    </span>
                    <span className="text-emerald-500 text-xs">ZG payout</span>
                  </>
                )}
                {day.status === 'normal' && day.earnings > 0 && (
                  <>
                    <span className="text-stone-700 font-semibold text-sm leading-tight">
                      ₹{day.earnings.toLocaleString()}
                    </span>
                    <span className="text-stone-400 text-xs">earned</span>
                  </>
                )}
                {day.status === 'normal' && day.earnings === 0 && (
                  <span className="text-stone-300 text-xs">Rest</span>
                )}
              </div>

              {/* Bar */}
              <div className="w-full flex flex-col justify-end" style={{ height: '80px' }}>
                {day.status === 'payout' ? (
                  <div
                    className="w-full bg-emerald-500 rounded-xl flex items-center justify-center"
                    style={{ height: `${barHeight}px` }}
                  >
                    <span className="text-white text-lg">⚡</span>
                  </div>
                ) : day.earnings > 0 ? (
                  <div
                    className="w-full bg-amber-400 rounded-xl"
                    style={{ height: `${barHeight}px` }}
                  />
                ) : (
                  <div className="w-full bg-stone-100 rounded-lg" style={{ height: '12px' }} />
                )}
              </div>

              {/* Day label */}
              <span className={`text-xs font-semibold ${
                day.status === 'payout' ? 'text-emerald-600' : 'text-stone-500'
              }`}>
                {day.day}
              </span>
            </div>
          )
        })}
      </div>

      {/* Disruption callout */}
      {week.filter(d => d.status === 'payout').length > 0 && (
        <div className="mt-5 bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-3 flex items-start gap-3">
          <span className="text-emerald-500 mt-0.5">⚡</span>
          <div>
            <p className="text-emerald-800 font-semibold text-sm">ZoneGuard paid out on 2 days this week</p>
            <p className="text-emerald-600 text-xs mt-0.5">
              {week.find(d => d.status === 'payout')?.disruptionType} · Auto-payout within 2 hours
            </p>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="flex gap-4 mt-4 pt-4 border-t border-stone-100">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded bg-amber-400" />
          <span className="text-stone-400 text-xs">Normal earnings</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded bg-emerald-500" />
          <span className="text-stone-400 text-xs">ZoneGuard payout</span>
        </div>
      </div>
    </div>
  )
}

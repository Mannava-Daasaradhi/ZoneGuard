import type { PremiumBreakdown as PremiumBreakdownType } from '../../types'

const FACTOR_LABELS: Record<string, string> = {
  disruption_freq: 'Disruption Frequency',
  imd_forecast: 'IMD Forecast',
  rider_tenure: 'Rider Tenure',
  zone_class: 'Zone Classification',
  claim_history: 'Claim History',
}

const FACTOR_COLORS: Record<string, string> = {
  disruption_freq: 'bg-red-400',
  imd_forecast: 'bg-amber-400',
  rider_tenure: 'bg-blue-400',
  zone_class: 'bg-purple-400',
  claim_history: 'bg-emerald-400',
}

interface Props {
  data: PremiumBreakdownType
  darkMode?: boolean
}

export default function PremiumBreakdown({ data, darkMode }: Props) {
  const { factor_breakdown, risk_score, premium, tier } = data

  return (
    <div className={`rounded-xl border p-5 ${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-amber-100'}`}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className={`font-bold text-lg ${darkMode ? 'text-white' : 'text-stone-800'}`}>
            Premium Breakdown
          </h3>
          <p className={`text-xs ${darkMode ? 'text-slate-400' : 'text-stone-500'}`}>
            Transparent factor-weighted calculation
          </p>
        </div>
        <div className="text-right">
          <p className={`font-bold text-2xl ${darkMode ? 'text-white' : 'text-stone-800'}`}>₹{premium}</p>
          <p className={`text-xs ${darkMode ? 'text-slate-400' : 'text-stone-500'}`}>per week · {tier} tier</p>
        </div>
      </div>

      {/* Risk score bar */}
      <div className="mb-4">
        <div className="flex justify-between text-xs mb-1">
          <span className={darkMode ? 'text-slate-400' : 'text-stone-500'}>Risk Score</span>
          <span className={`font-bold ${darkMode ? 'text-white' : 'text-stone-800'}`}>{risk_score}/100</span>
        </div>
        <div className={`h-2 rounded-full ${darkMode ? 'bg-slate-700' : 'bg-stone-100'}`}>
          <div
            className="h-2 rounded-full bg-gradient-to-r from-emerald-400 via-amber-400 to-red-400 transition-all"
            style={{ width: `${risk_score}%` }}
          />
        </div>
      </div>

      {/* Factor breakdown */}
      <div className="space-y-3">
        {Object.entries(factor_breakdown).map(([key, factor]) => (
          <div key={key}>
            <div className="flex items-center justify-between text-xs mb-1">
              <div className="flex items-center gap-2">
                <div className={`w-2.5 h-2.5 rounded-full ${FACTOR_COLORS[key]}`} />
                <span className={darkMode ? 'text-slate-300' : 'text-stone-700'}>
                  {FACTOR_LABELS[key]} ({(factor.weight * 100).toFixed(0)}%)
                </span>
              </div>
              <span className={`font-medium ${darkMode ? 'text-white' : 'text-stone-800'}`}>
                {factor.raw_score.toFixed(0)}/100 → ₹{factor.contribution_inr.toFixed(1)}
              </span>
            </div>
            <div className={`h-1.5 rounded-full ${darkMode ? 'bg-slate-700' : 'bg-stone-100'}`}>
              <div
                className={`h-1.5 rounded-full ${FACTOR_COLORS[key]} transition-all`}
                style={{ width: `${factor.raw_score}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

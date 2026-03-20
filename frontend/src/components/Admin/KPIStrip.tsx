import { LineChart, Line, ResponsiveContainer } from 'recharts'
import type { KPI } from '../../types'

interface Props { kpis: KPI[] }

export default function KPIStrip({ kpis }: Props) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {kpis.map((kpi) => {
        const isPositiveTrend = kpi.label === 'Loss Ratio' ? kpi.trend === 'down' : kpi.trend === 'up'
        return (
          <div key={kpi.label} className="bg-slate-800 border border-slate-700 rounded-xl p-4">
            <p className="text-slate-400 text-xs font-medium mb-1">{kpi.label}</p>
            <p className="text-white font-bold text-2xl mb-1">{kpi.value}</p>
            <p className={`text-xs font-medium mb-2 ${isPositiveTrend ? 'text-emerald-400' : 'text-red-400'}`}>
              {kpi.delta} vs last week
            </p>
            <div className="h-8">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={kpi.sparkline.map((v, i) => ({ v, i }))}>
                  <Line
                    type="monotone"
                    dataKey="v"
                    stroke={isPositiveTrend ? '#10b981' : '#f59e0b'}
                    strokeWidth={1.5}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )
      })}
    </div>
  )
}

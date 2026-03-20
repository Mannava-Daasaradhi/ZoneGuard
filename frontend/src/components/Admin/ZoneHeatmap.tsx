import { useState } from 'react'
import type { Zone } from '../../types'

interface Props { zones: Zone[] }

const riskColor = (score: number) => {
  if (score < 30) return '#10B981'
  if (score < 55) return '#F59E0B'
  if (score < 75) return '#F97316'
  return '#EF4444'
}

const ZONE_POSITIONS: Record<string, { x: number; y: number }> = {
  'hsr':             { x: 50, y: 62 },
  'koramangala':     { x: 44, y: 56 },
  'whitefield':      { x: 76, y: 50 },
  'indiranagar':     { x: 53, y: 50 },
  'electronic-city': { x: 54, y: 78 },
  'bellandur':       { x: 64, y: 66 },
  'btm-layout':      { x: 46, y: 70 },
  'jp-nagar':        { x: 40, y: 72 },
  'yelahanka':       { x: 46, y: 22 },
  'hebbal':          { x: 50, y: 34 },
}

export default function ZoneHeatmap({ zones }: Props) {
  const [selected, setSelected] = useState<Zone | null>(null)

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-white font-bold text-lg">Bengaluru Zone Risk Map</h2>
          <p className="text-slate-400 text-xs">Click a zone for details</p>
        </div>
        <div className="flex items-center gap-3 text-xs">
          {[['#10B981', 'Low'], ['#F59E0B', 'Med'], ['#F97316', 'High'], ['#EF4444', 'Flood']] .map(([color, label]) => (
            <div key={label} className="flex items-center gap-1">
              <div className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
              <span className="text-slate-400">{label}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* SVG Map */}
        <div className="md:col-span-2">
          <svg
            viewBox="0 0 100 100"
            className="w-full h-64 bg-slate-900 rounded-xl border border-slate-700"
          >
            {/* City silhouette */}
            <ellipse cx="50" cy="52" rx="36" ry="42" fill="#1e293b" stroke="#334155" strokeWidth="0.5" />

            {zones.map((zone) => {
              const pos = ZONE_POSITIONS[zone.id]
              if (!pos) return null
              const color = riskColor(zone.riskScore)
              const isSelected = selected?.id === zone.id

              return (
                <g
                  key={zone.id}
                  onClick={() => setSelected(zone === selected ? null : zone)}
                  className="cursor-pointer"
                >
                  {/* Pulse ring for high-risk zones */}
                  {zone.riskScore >= 70 && (
                    <circle cx={pos.x} cy={pos.y} r="4" fill={color} fillOpacity="0.0" stroke={color} strokeOpacity="0.4" strokeWidth="1">
                      <animate attributeName="r" values="4;9;4" dur="2.5s" repeatCount="indefinite" />
                      <animate attributeName="stroke-opacity" values="0.4;0;0.4" dur="2.5s" repeatCount="indefinite" />
                    </circle>
                  )}
                  {/* Zone dot */}
                  <circle
                    cx={pos.x}
                    cy={pos.y}
                    r={isSelected ? 5.5 : 4}
                    fill={color}
                    fillOpacity={isSelected ? 1 : 0.85}
                    stroke={isSelected ? 'white' : 'transparent'}
                    strokeWidth={isSelected ? 1.5 : 0}
                  />
                  {/* Zone label */}
                  <text
                    x={pos.x}
                    y={pos.y + 9}
                    textAnchor="middle"
                    fontSize="3"
                    fill="#94a3b8"
                    className="pointer-events-none"
                  >
                    {zone.name.split(' ')[0]}
                  </text>
                </g>
              )
            })}
          </svg>
        </div>

        {/* Detail panel */}
        <div className="bg-slate-900 rounded-xl border border-slate-700 p-4">
          {selected ? (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <div
                  className="w-3 h-3 rounded-full flex-shrink-0"
                  style={{ background: riskColor(selected.riskScore) }}
                />
                <h3 className="text-white font-bold text-base">{selected.name}</h3>
              </div>
              <p className="text-slate-500 text-xs mb-4">{selected.pinCode}</p>
              {([
                ['Risk Score', `${selected.riskScore}/100`],
                ['Risk Tier', selected.riskTier],
                ['Weekly Premium', `₹${selected.weeklyPremium}`],
                ['Max Payout', `₹${selected.maxWeeklyPayout.toLocaleString()}`],
                ['Active Riders', `${selected.activeRiders}`],
                ['Disruptions/yr', `~${selected.disruptions} days`],
              ] as [string, string][]).map(([k, v]) => (
                <div key={k} className="flex justify-between py-1.5 border-b border-slate-800 last:border-0">
                  <span className="text-slate-400 text-xs">{k}</span>
                  <span className="text-white text-xs font-medium capitalize">{v}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-center py-8">
              <p className="text-slate-500 text-sm">Select a zone on the map to view risk details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

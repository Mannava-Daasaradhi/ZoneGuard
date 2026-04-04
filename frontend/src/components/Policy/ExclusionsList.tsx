import type { Exclusion } from '../../types'

const CATEGORY_STYLE: Record<string, string> = {
  standard: 'bg-slate-100 text-slate-600',
  operational: 'bg-amber-100 text-amber-700',
  behavioral: 'bg-red-100 text-red-700',
}

interface Props {
  exclusions: Exclusion[]
  compact?: boolean
  darkMode?: boolean
}

export default function ExclusionsList({ exclusions, compact, darkMode }: Props) {
  if (compact) {
    return (
      <div className={`rounded-xl border p-4 ${darkMode ? 'bg-slate-900 border-slate-700' : 'bg-red-50/50 border-red-200'}`}>
        <p className={`text-xs font-semibold mb-2 ${darkMode ? 'text-red-400' : 'text-red-600'}`}>
          What's NOT covered (10 standard exclusions)
        </p>
        <div className="space-y-1.5">
          {exclusions.map(e => (
            <div key={e.id} className="flex items-start gap-2">
              <span className={`text-xs mt-0.5 ${darkMode ? 'text-red-400' : 'text-red-500'}`}>✗</span>
              <span className={`text-xs ${darkMode ? 'text-slate-300' : 'text-stone-600'}`}>{e.name}</span>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {exclusions.map(e => (
        <div
          key={e.id}
          className={`rounded-xl border p-3 ${darkMode ? 'bg-slate-900 border-slate-700' : 'bg-white border-stone-100'}`}
        >
          <div className="flex items-center justify-between mb-1">
            <span className={`font-semibold text-sm ${darkMode ? 'text-white' : 'text-stone-800'}`}>{e.name}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full ${CATEGORY_STYLE[e.category]}`}>
              {e.category}
            </span>
          </div>
          <p className={`text-xs leading-relaxed ${darkMode ? 'text-slate-400' : 'text-stone-500'}`}>
            {e.description}
          </p>
        </div>
      ))}
    </div>
  )
}

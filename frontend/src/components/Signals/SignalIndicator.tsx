import { useMemo } from 'react'

export type SignalType = 'S1' | 'S2' | 'S3' | 'S4'

export interface SignalData {
  status: string
  value: string
  threshold: string
  raw?: Record<string, unknown>
}

interface Props {
  type: SignalType
  signal: SignalData
}

const SIGNAL_CONFIG: Record<SignalType, {
  label: string
  description: string
  icon: string
  metrics: string[]
}> = {
  S1: {
    label: 'Environmental',
    description: 'Rainfall, AQI, Temperature',
    icon: '🌧️',
    metrics: ['rainfall', 'AQI', 'temperature'],
  },
  S2: {
    label: 'Mobility',
    description: 'Zone mobility index',
    icon: '🚗',
    metrics: ['mobility_index'],
  },
  S3: {
    label: 'Economic',
    description: 'Order volume',
    icon: '📦',
    metrics: ['order_volume'],
  },
  S4: {
    label: 'Crowd',
    description: 'Rider inactivity %',
    icon: '👥',
    metrics: ['inactivity_pct'],
  },
}

function parseNumericValue(value: string): number {
  // Handle formats like "85mm/hr", "150 AQI", "45%", "0.3", etc.
  const match = value.match(/[\d.]+/)
  return match ? parseFloat(match[0]) : 0
}

function calculateProgress(value: string, threshold: string): number {
  const currentVal = parseNumericValue(value)
  const thresholdVal = parseNumericValue(threshold)
  
  if (thresholdVal === 0) return 0
  
  // For most signals, higher value means closer to threshold breach
  const progress = (currentVal / thresholdVal) * 100
  return Math.min(100, Math.max(0, progress))
}

export default function SignalIndicator({ type, signal }: Props) {
  const config = SIGNAL_CONFIG[type]
  const isFiring = signal.status === 'firing' || signal.status === 'breached'
  
  const progress = useMemo(
    () => calculateProgress(signal.value, signal.threshold),
    [signal.value, signal.threshold]
  )
  
  // Determine color based on progress
  const getProgressColor = () => {
    if (isFiring) return 'bg-red-500'
    if (progress >= 80) return 'bg-amber-500'
    if (progress >= 50) return 'bg-yellow-400'
    return 'bg-emerald-500'
  }

  return (
    <div
      className={`
        relative bg-white rounded-xl border p-4 transition-all duration-300
        ${isFiring 
          ? 'border-red-300 bg-red-50 shadow-sm shadow-red-100' 
          : 'border-stone-100 hover:border-amber-200'
        }
      `}
    >
      {/* Firing pulse effect */}
      {isFiring && (
        <div className="absolute inset-0 rounded-xl border-2 border-red-400 animate-pulse opacity-50" />
      )}
      
      {/* Header: Icon + Label + Status dot */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <div 
            className={`
              w-10 h-10 rounded-lg flex items-center justify-center text-xl
              ${isFiring ? 'bg-red-100' : 'bg-amber-50'}
            `}
          >
            {config.icon}
          </div>
          <div>
            <h4 className="text-stone-800 font-semibold text-sm leading-tight">
              {type}: {config.label}
            </h4>
            <p className="text-stone-400 text-xs mt-0.5">{config.description}</p>
          </div>
        </div>
        
        {/* Status indicator */}
        <div
          className={`
            w-3 h-3 rounded-full flex-shrink-0 mt-1
            ${isFiring 
              ? 'bg-red-500 animate-pulse shadow-lg shadow-red-300' 
              : 'bg-emerald-500'
            }
          `}
          aria-label={isFiring ? 'Signal firing' : 'Signal inactive'}
        />
      </div>

      {/* Values */}
      <div className="flex items-baseline justify-between mb-2.5">
        <div className="flex items-baseline gap-1.5">
          <span className={`text-lg font-bold ${isFiring ? 'text-red-600' : 'text-stone-800'}`}>
            {signal.value || '—'}
          </span>
          <span className="text-stone-400 text-xs">current</span>
        </div>
        <div className="flex items-baseline gap-1">
          <span className="text-stone-500 text-sm font-medium">
            {signal.threshold || '—'}
          </span>
          <span className="text-stone-400 text-xs">threshold</span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="relative h-2 bg-stone-100 rounded-full overflow-hidden">
        <div
          className={`absolute left-0 top-0 h-full rounded-full transition-all duration-500 ${getProgressColor()}`}
          style={{ width: `${progress}%` }}
        />
        {/* Threshold marker */}
        <div 
          className="absolute top-0 h-full w-0.5 bg-stone-400"
          style={{ left: '100%', transform: 'translateX(-2px)' }}
        />
      </div>
      
      {/* Status label */}
      <div className="mt-2.5 flex items-center justify-between">
        <span
          className={`
            inline-flex items-center gap-1.5 text-xs font-semibold px-2 py-0.5 rounded-full
            ${isFiring 
              ? 'bg-red-100 text-red-700' 
              : 'bg-emerald-50 text-emerald-700'
            }
          `}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${isFiring ? 'bg-red-500' : 'bg-emerald-500'}`} />
          {isFiring ? 'FIRING' : 'Normal'}
        </span>
        <span className="text-stone-400 text-xs">
          {Math.round(progress)}% of threshold
        </span>
      </div>
    </div>
  )
}

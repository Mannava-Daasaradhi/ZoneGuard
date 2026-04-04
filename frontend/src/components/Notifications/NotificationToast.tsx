import { useEffect } from 'react'

export type NotificationType = 'POLICY_ACTIVATED' | 'SIGNAL_ALERT' | 'CLAIM_CREATED' | 'PAYOUT_SENT'

interface NotificationToastProps {
  id: string
  type: NotificationType
  title: string
  message: string
  onDismiss: (id: string) => void
}

const ICONS: Record<NotificationType, string> = {
  POLICY_ACTIVATED: '🛡️',
  SIGNAL_ALERT: '📡',
  CLAIM_CREATED: '📋',
  PAYOUT_SENT: '💰',
}

const TYPE_COLORS: Record<NotificationType, string> = {
  POLICY_ACTIVATED: 'border-emerald-200 bg-emerald-50',
  SIGNAL_ALERT: 'border-amber-200 bg-amber-50',
  CLAIM_CREATED: 'border-blue-200 bg-blue-50',
  PAYOUT_SENT: 'border-green-200 bg-green-50',
}

export default function NotificationToast({ id, type, title, message, onDismiss }: NotificationToastProps) {
  useEffect(() => {
    const timer = setTimeout(() => onDismiss(id), 5000)
    return () => clearTimeout(timer)
  }, [id, onDismiss])

  return (
    <div
      role="alert"
      aria-live="polite"
      className={`animate-slide-in bg-white border ${TYPE_COLORS[type]} rounded-xl shadow-lg p-4 max-w-sm flex gap-3`}
    >
      <span className="text-2xl flex-shrink-0" aria-hidden="true">{ICONS[type]}</span>
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-stone-800 text-sm">{title}</p>
        <p className="text-stone-500 text-xs mt-0.5 truncate">{message}</p>
      </div>
      <button
        onClick={() => onDismiss(id)}
        className="text-stone-400 hover:text-stone-600 text-xl leading-none flex-shrink-0 h-fit"
        aria-label="Dismiss notification"
      >
        ×
      </button>
    </div>
  )
}

import { useState, useRef, useEffect } from 'react'
import { useNotifications } from '../../hooks/useNotifications'
import type { Notification } from './NotificationProvider'
import type { NotificationType } from './NotificationToast'

const ICONS: Record<NotificationType, string> = {
  POLICY_ACTIVATED: '🛡️',
  SIGNAL_ALERT: '📡',
  CLAIM_CREATED: '📋',
  PAYOUT_SENT: '💰',
}

function formatTimeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  
  if (seconds < 60) return 'Just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}

function NotificationItem({ 
  notification, 
  onMarkRead 
}: { 
  notification: Notification
  onMarkRead: (id: string) => void
}) {
  return (
    <button
      onClick={() => !notification.isRead && onMarkRead(notification.id)}
      className={`w-full text-left px-4 py-3 hover:bg-stone-50 transition-colors flex gap-3 ${
        !notification.isRead ? 'bg-amber-50/50' : ''
      }`}
    >
      <span className="text-lg flex-shrink-0" aria-hidden="true">
        {ICONS[notification.type]}
      </span>
      <div className="flex-1 min-w-0">
        <p className={`text-sm ${notification.isRead ? 'text-stone-600' : 'text-stone-800 font-medium'}`}>
          {notification.title}
        </p>
        <p className="text-xs text-stone-500 truncate mt-0.5">{notification.message}</p>
        <p className="text-xs text-stone-400 mt-1">{formatTimeAgo(notification.createdAt)}</p>
      </div>
      {!notification.isRead && (
        <span className="w-2 h-2 rounded-full bg-amber-500 flex-shrink-0 mt-1.5" aria-label="Unread" />
      )}
    </button>
  )
}

export default function NotificationBell() {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)
  
  const { notifications, unreadCount, markAsRead, markAllAsRead } = useNotifications()

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Close on escape
  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') setIsOpen(false)
    }
    
    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      return () => document.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen])

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg hover:bg-stone-100 transition-colors"
        aria-label={`Notifications${unreadCount > 0 ? `, ${unreadCount} unread` : ''}`}
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
          className="w-6 h-6 text-stone-600"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0"
          />
        </svg>
        
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] flex items-center justify-center bg-amber-500 text-white text-xs font-medium rounded-full px-1">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div
          ref={dropdownRef}
          role="menu"
          className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-lg border border-stone-200 overflow-hidden z-50"
        >
          {/* Header */}
          <div className="px-4 py-3 border-b border-stone-100 flex items-center justify-between">
            <h3 className="font-semibold text-stone-800">Notifications</h3>
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="text-xs text-amber-600 hover:text-amber-700 font-medium"
              >
                Mark all read
              </button>
            )}
          </div>

          {/* Notification list */}
          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="py-8 text-center">
                <p className="text-stone-400 text-sm">No notifications yet</p>
              </div>
            ) : (
              <div className="divide-y divide-stone-100">
                {notifications.slice(0, 10).map(notification => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    onMarkRead={markAsRead}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          {notifications.length > 10 && (
            <div className="px-4 py-2 border-t border-stone-100 text-center">
              <button className="text-xs text-amber-600 hover:text-amber-700 font-medium">
                View all notifications
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

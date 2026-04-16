import { createContext, useCallback, useState, useEffect, type ReactNode } from 'react'
import NotificationToast, { type NotificationType } from './NotificationToast'

export interface Notification {
  id: string
  type: NotificationType
  title: string
  message: string
  data?: Record<string, unknown>
  isRead: boolean
  createdAt: Date
}

interface NotificationContextValue {
  notifications: Notification[]
  unreadCount: number
  toasts: Notification[]
  addNotification: (notification: Omit<Notification, 'id' | 'isRead' | 'createdAt'>) => void
  markAsRead: (id: string) => void
  markAllAsRead: () => void
  dismissToast: (id: string) => void
  clearAll: () => void
  fetchNotifications: (riderId: string) => Promise<void>
}

// eslint-disable-next-line react-refresh/only-export-components
export const NotificationContext = createContext<NotificationContextValue | null>(null)

import { API_URL } from '../../services/api'

interface Props {
  children: ReactNode
}

export default function NotificationProvider({ children }: Props) {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [toasts, setToasts] = useState<Notification[]>([])

  const unreadCount = notifications.filter(n => !n.isRead).length

  const fetchNotifications = useCallback(async (riderId: string) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/notifications?rider_id=${riderId}`)
      if (!res.ok) return
      
      const data = await res.json()
      const mapped: Notification[] = data.map((n: {
        id: string
        type: NotificationType
        title: string
        message: string
        data?: Record<string, unknown>
        is_read: boolean
        created_at: string
      }) => ({
        id: n.id,
        type: n.type,
        title: n.title,
        message: n.message,
        data: n.data,
        isRead: n.is_read,
        createdAt: new Date(n.created_at),
      }))
      setNotifications(mapped)
    } catch (err) {
      console.error('Failed to fetch notifications:', err)
    }
  }, [])

  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'isRead' | 'createdAt'>) => {
    const newNotification: Notification = {
      ...notification,
      id: crypto.randomUUID(),
      isRead: false,
      createdAt: new Date(),
    }
    
    setNotifications(prev => [newNotification, ...prev])
    setToasts(prev => [...prev, newNotification])
  }, [])

  const markAsRead = useCallback(async (id: string) => {
    setNotifications(prev =>
      prev.map(n => (n.id === id ? { ...n, isRead: true } : n))
    )
    
    // Optimistically mark as read, fire API call in background
    try {
      await fetch(`${API_URL}/api/v1/notifications/${id}/read`, { method: 'PATCH' })
    } catch (err) {
      console.error('Failed to mark notification as read:', err)
    }
  }, [])

  const markAllAsRead = useCallback(() => {
    setNotifications(prev => prev.map(n => ({ ...n, isRead: true })))
    // Note: Backend would need a bulk endpoint for this to persist
  }, [])

  const dismissToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const clearAll = useCallback(() => {
    setNotifications([])
    setToasts([])
  }, [])

  // Auto-dismiss toasts after they've been shown
  useEffect(() => {
    if (toasts.length === 0) return
    
    const timer = setTimeout(() => {
      setToasts(prev => prev.slice(1))
    }, 5500) // Slightly longer than toast auto-dismiss to ensure smooth transition
    
    return () => clearTimeout(timer)
  }, [toasts])

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        unreadCount,
        toasts,
        addNotification,
        markAsRead,
        markAllAsRead,
        dismissToast,
        clearAll,
        fetchNotifications,
      }}
    >
      {children}
      
      {/* Toast container - fixed position at top right */}
      <div
        aria-live="polite"
        aria-label="Notifications"
        className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none"
      >
        {toasts.slice(0, 3).map(toast => (
          <div key={toast.id} className="pointer-events-auto">
            <NotificationToast
              id={toast.id}
              type={toast.type}
              title={toast.title}
              message={toast.message}
              onDismiss={dismissToast}
            />
          </div>
        ))}
      </div>
    </NotificationContext.Provider>
  )
}

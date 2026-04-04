const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `API error: ${res.status}`)
  }
  return res.json()
}

// Zones
export const getZones = () => fetchAPI<any[]>('/api/v1/zones')
export const getZone = (id: string) => fetchAPI<any>(`/api/v1/zones/${id}`)
export const getZoneSignals = (id: string) => fetchAPI<any>(`/api/v1/zones/${id}/signals/current`)
export const getZoneRiskScore = (id: string) => fetchAPI<any>(`/api/v1/zones/${id}/risk-score`)

// Riders
export const registerRider = (data: any) =>
  fetchAPI<any>('/api/v1/riders/register', { method: 'POST', body: JSON.stringify(data) })
export const getRider = (id: string) => fetchAPI<any>(`/api/v1/riders/${id}`)

// Policies
export const createPolicy = (data: any) =>
  fetchAPI<any>('/api/v1/policies', { method: 'POST', body: JSON.stringify(data) })
export const getPolicies = (riderId?: string) =>
  fetchAPI<any[]>(`/api/v1/policies${riderId ? `?rider_id=${riderId}` : ''}`)
export const getPolicy = (id: string) => fetchAPI<any>(`/api/v1/policies/${id}`)
export const getPolicyExclusions = (id: string) => fetchAPI<any[]>(`/api/v1/policies/${id}/exclusions`)
export const renewPolicy = (id: string) =>
  fetchAPI<any>(`/api/v1/policies/${id}/renew`, { method: 'POST' })
export const cancelPolicy = (id: string) =>
  fetchAPI<any>(`/api/v1/policies/${id}/cancel`, { method: 'POST' })

// Premium
export const calculatePremium = (zoneId: string, riderId?: string) =>
  fetchAPI<any>(`/api/v1/premium/calculate?zone_id=${zoneId}${riderId ? `&rider_id=${riderId}` : ''}`)

// Claims
export const getClaims = (params?: { status?: string; zone_id?: string; rider_id?: string }) => {
  const qs = new URLSearchParams(params as any).toString()
  return fetchAPI<any[]>(`/api/v1/claims${qs ? `?${qs}` : ''}`)
}
export const getClaim = (id: string) => fetchAPI<any>(`/api/v1/claims/${id}`)
export const reviewClaim = (id: string, action: 'approve' | 'reject') =>
  fetchAPI<any>(`/api/v1/claims/${id}/review`, {
    method: 'POST',
    body: JSON.stringify({ action, reviewed_by: 'admin' }),
  })

// Signals
export const pollSignals = (zoneId: string) =>
  fetchAPI<any>(`/api/v1/signals/poll/${zoneId}`, { method: 'POST' })
export const getActiveEvents = () => fetchAPI<any[]>('/api/v1/signals/active-events')

// Payouts
export const getPayouts = (riderId?: string) =>
  fetchAPI<any[]>(`/api/v1/payouts${riderId ? `?rider_id=${riderId}` : ''}`)

// Admin
export const getKPIs = () => fetchAPI<any>('/api/v1/admin/kpis')

// Simulator
export const triggerSimulation = (zoneId: string, scenario: string) =>
  fetchAPI<any>('/api/v1/simulator/trigger', {
    method: 'POST',
    body: JSON.stringify({ zone_id: zoneId, scenario }),
  })
export const getActiveSimulations = () => fetchAPI<any[]>('/api/v1/simulator/active')
export const stopSimulation = (simId: string) =>
  fetchAPI<any>(`/api/v1/simulator/stop/${simId}`, { method: 'DELETE' })
export const getScenarios = () => fetchAPI<any>('/api/v1/simulator/scenarios')

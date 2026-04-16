import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock fetch globally before importing api module
const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

// Mock localStorage
const mockStorage: Record<string, string> = {}
vi.stubGlobal('localStorage', {
  getItem: (key: string) => mockStorage[key] ?? null,
  setItem: (key: string, val: string) => { mockStorage[key] = val },
  removeItem: (key: string) => { delete mockStorage[key] },
})

// Dynamic import so mocks are in place
const api = await import('../services/api')

describe('API service', () => {
  beforeEach(() => {
    mockFetch.mockReset()
    Object.keys(mockStorage).forEach((k) => delete mockStorage[k])
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  function mockOk(data: unknown) {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => data,
    })
  }

  function mockError(status: number, detail: string) {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status,
      statusText: 'Error',
      json: async () => ({ detail }),
    })
  }

  it('getZones calls /api/v1/zones', async () => {
    const zones = [{ id: 'hsr', name: 'HSR Layout' }]
    mockOk(zones)
    const result = await api.getZones()
    expect(result).toEqual(zones)
    expect(mockFetch).toHaveBeenCalledOnce()
    const url = mockFetch.mock.calls[0][0] as string
    expect(url).toContain('/api/v1/zones')
  })

  it('getClaims builds correct query string', async () => {
    mockOk([])
    await api.getClaims({ status: 'pending_review', zone_id: 'hsr' })
    const url = mockFetch.mock.calls[0][0] as string
    expect(url).toContain('status=pending_review')
    expect(url).toContain('zone_id=hsr')
  })

  it('getClaims works without params', async () => {
    mockOk([])
    await api.getClaims()
    const url = mockFetch.mock.calls[0][0] as string
    expect(url).toContain('/api/v1/claims')
    expect(url).not.toContain('?')
  })

  it('sendChatMessage sends POST with body', async () => {
    mockOk({ response: 'Hello!', source: 'gemini' })
    const result = await api.sendChatMessage('hi', 'rider-1')
    expect(result.response).toBe('Hello!')
    const [, opts] = mockFetch.mock.calls[0]
    expect(opts.method).toBe('POST')
    const body = JSON.parse(opts.body as string)
    expect(body.message).toBe('hi')
    expect(body.rider_id).toBe('rider-1')
  })

  it('throws on API error with detail message', async () => {
    mockError(404, 'Claim not found')
    await expect(api.getClaim('bad-id')).rejects.toThrow('Claim not found')
  })

  it('includes Authorization header when token present', async () => {
    mockStorage['zoneguard_token'] = 'test-jwt-token'
    mockOk([])
    await api.getZones()
    const [, opts] = mockFetch.mock.calls[0]
    expect(opts.headers.Authorization).toBe('Bearer test-jwt-token')
  })

  it('omits Authorization header when no token', async () => {
    mockOk([])
    await api.getZones()
    const [, opts] = mockFetch.mock.calls[0]
    expect(opts.headers.Authorization).toBeUndefined()
  })

  it('triggerSimulation sends correct payload', async () => {
    mockOk({ zone_id: 'hsr', scenario: 'flash_flood' })
    await api.triggerSimulation('hsr', 'flash_flood')
    const [, opts] = mockFetch.mock.calls[0]
    expect(opts.method).toBe('POST')
    const body = JSON.parse(opts.body as string)
    expect(body.zone_id).toBe('hsr')
    expect(body.scenario).toBe('flash_flood')
  })

  it('getAdminClaims builds paginated query', async () => {
    mockOk({ items: [], total: 0, page: 1, per_page: 20, pages: 0 })
    await api.getAdminClaims({ status: 'approved', page: 2, per_page: 20 })
    const url = mockFetch.mock.calls[0][0] as string
    expect(url).toContain('status=approved')
    expect(url).toContain('page=2')
    expect(url).toContain('per_page=20')
  })

  it('reviewClaim sends approve action', async () => {
    mockOk({ status: 'approved' })
    await api.reviewClaim('claim-1', 'approve')
    const [, opts] = mockFetch.mock.calls[0]
    const body = JSON.parse(opts.body as string)
    expect(body.action).toBe('approve')
    expect(body.reviewed_by).toBe('admin')
  })
})

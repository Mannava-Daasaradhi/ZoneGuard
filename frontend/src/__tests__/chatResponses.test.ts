import { describe, it, expect } from 'vitest'
import { findResponse, CHAT_RESPONSES, DEFAULT_RESPONSE, WELCOME_MESSAGE } from '../data/chatResponses'

describe('chatResponses', () => {
  it('WELCOME_MESSAGE is defined and non-empty', () => {
    expect(WELCOME_MESSAGE).toBeTruthy()
    expect(WELCOME_MESSAGE.length).toBeGreaterThan(10)
  })

  it('DEFAULT_RESPONSE is defined and non-empty', () => {
    expect(DEFAULT_RESPONSE).toBeTruthy()
    expect(DEFAULT_RESPONSE.length).toBeGreaterThan(10)
  })

  it('CHAT_RESPONSES has at least 5 entries', () => {
    expect(CHAT_RESPONSES.length).toBeGreaterThanOrEqual(5)
  })

  it('every response entry has keywords and response', () => {
    for (const entry of CHAT_RESPONSES) {
      expect(entry.keywords.length).toBeGreaterThan(0)
      expect(entry.response.length).toBeGreaterThan(0)
    }
  })

  it('findResponse matches claim status keyword', () => {
    const result = findResponse('What is my claim status?')
    expect(result).not.toBe(DEFAULT_RESPONSE)
    expect(result.toLowerCase()).toContain('claim')
  })

  it('findResponse matches payout keyword', () => {
    const result = findResponse('How is payout calculated?')
    expect(result).not.toBe(DEFAULT_RESPONSE)
    expect(result).toContain('55%')
  })

  it('findResponse matches coverage keyword', () => {
    const result = findResponse('Tell me about coverage')
    expect(result).not.toBe(DEFAULT_RESPONSE)
    expect(result.toLowerCase()).toContain('cover')
  })

  it('findResponse matches exclusion keyword', () => {
    const result = findResponse('What is not covered?')
    expect(result).not.toBe(DEFAULT_RESPONSE)
    expect(result.toLowerCase()).toContain('exclusion')
  })

  it('findResponse matches premium keyword', () => {
    const result = findResponse('How much does it cost?')
    expect(result).not.toBe(DEFAULT_RESPONSE)
    expect(result).toContain('₹')
  })

  it('findResponse matches signal keyword', () => {
    const result = findResponse('How do the 4 signals work?')
    expect(result).not.toBe(DEFAULT_RESPONSE)
    expect(result).toContain('S1')
  })

  it('findResponse is case-insensitive', () => {
    const lower = findResponse('claim status')
    const upper = findResponse('CLAIM STATUS')
    expect(lower).toBe(upper)
  })

  it('findResponse returns DEFAULT_RESPONSE for unknown input', () => {
    const result = findResponse('xyzzy foobar baz')
    expect(result).toBe(DEFAULT_RESPONSE)
  })

  it('findResponse handles greeting', () => {
    const result = findResponse('hello')
    expect(result).not.toBe(DEFAULT_RESPONSE)
    expect(result.toLowerCase()).toContain('hello')
  })

  it('findResponse handles empty string', () => {
    const result = findResponse('')
    expect(result).toBe(DEFAULT_RESPONSE)
  })
})

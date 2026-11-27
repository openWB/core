import { afterEach, describe, expect, it, vi } from 'vitest'
import { readStorage, writeStorage } from './storage'

afterEach(() => vi.unstubAllGlobals())

describe('storage helpers', () => {
  it('read and write through localStorage', () => {
    const data: Record<string, string> = {}
    vi.stubGlobal('localStorage', { getItem: (k: string) => data[k] ?? null, setItem: (k: string, v: string) => (data[k] = v) })
    writeStorage('a', '1')
    expect(readStorage('a')).toBe('1')
    expect(readStorage('missing')).toBeNull()
  })

  // blocked site data / private mode: even touching localStorage throws, the page must still start
  it('do not throw when the browser refuses access to localStorage', () => {
    vi.stubGlobal('localStorage', {
      getItem: () => {
        throw new DOMException('denied', 'SecurityError')
      },
      setItem: () => {
        throw new DOMException('denied', 'SecurityError')
      },
    })
    expect(readStorage('a')).toBeNull()
    expect(() => writeStorage('a', '1')).not.toThrow()
  })
})

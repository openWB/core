import { describe, expect, it } from 'vitest'
import { parseNumberInput } from './numberInput'

describe('parseNumberInput', () => {
  it('keeps the previous value for empty or unusable input', () => {
    expect(parseNumberInput('', 12, 0)).toBe(12)
    expect(parseNumberInput('  ', 12)).toBe(12)
    expect(parseNumberInput('abc', 12)).toBe(12)
  })

  it('reads numbers, also with a decimal comma', () => {
    expect(parseNumberInput('7.5', 0)).toBe(7.5)
    expect(parseNumberInput('7,5', 0)).toBe(7.5)
    expect(parseNumberInput('0', 5)).toBe(0)
  })

  it('clamps to min and max', () => {
    expect(parseNumberInput('-3', 1, 0)).toBe(0)
    expect(parseNumberInput('500', 1, 0, 100)).toBe(100)
  })
})

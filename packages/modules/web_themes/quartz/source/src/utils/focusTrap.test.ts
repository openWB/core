import { describe, expect, it } from 'vitest'
import { trapTarget } from './focusTrap'

const [a, b, c] = ['a', 'b', 'c']
const dialog = 'dialog'

describe('trapTarget', () => {
  it('wraps from the last element to the first when tabbing forward', () => {
    expect(trapTarget([a, b, c], c, false, dialog)).toBe(a)
  })

  it('wraps from the first element (or the dialog) to the last when tabbing back', () => {
    expect(trapTarget([a, b, c], a, true, dialog)).toBe(c)
    expect(trapTarget([a, b, c], dialog, true, dialog)).toBe(c)
  })

  it('leaves the browser alone in the middle of the dialog', () => {
    expect(trapTarget([a, b, c], b, false, dialog)).toBeNull()
    expect(trapTarget([a, b, c], b, true, dialog)).toBeNull()
  })

  it('brings focus back in when it is outside the dialog', () => {
    expect(trapTarget([a, b, c], 'outside', false, dialog)).toBe(a)
    expect(trapTarget([a, b, c], 'outside', true, dialog)).toBe(c)
  })

  it('does nothing for a dialog without focusable elements', () => {
    expect(trapTarget([], dialog, false, dialog)).toBeNull()
  })
})

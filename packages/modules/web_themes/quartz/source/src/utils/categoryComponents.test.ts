import { describe, expect, it } from 'vitest'
import { categoryHasComponent } from './categoryComponents'
import type { useMqttStore } from '@/stores/mqtt-store'

function store(overrides: Record<string, unknown>): ReturnType<typeof useMqttStore> {
  return {
    pvConfigured: false,
    batteryConfigured: false,
    inverterIds: [],
    batteryIds: [],
    chargePointIds: [],
    consumerIds: [],
    consumerInstanceIsHomeConsumption: () => false,
    ...overrides,
  } as unknown as ReturnType<typeof useMqttStore>
}

describe('categoryHasComponent', () => {
  it('grid and house always exist', () => {
    expect(categoryHasComponent('grid', store({}), 0)).toBe(true)
    expect(categoryHasComponent('house', store({}), 0)).toBe(true)
  })

  it('the others need a configured component', () => {
    expect(categoryHasComponent('pv', store({}), 0)).toBe(false)
    expect(categoryHasComponent('pv', store({ inverterIds: [1] }), 0)).toBe(true)
    expect(categoryHasComponent('battery', store({ batteryIds: [2] }), 0)).toBe(true)
    // the live feed carries the lines although the user may not see the components
    expect(categoryHasComponent('pv', store({ pvConfigured: true }), 0)).toBe(true)
    expect(categoryHasComponent('battery', store({ batteryConfigured: true }), 0)).toBe(true)
    expect(categoryHasComponent('chargepoint', store({ chargePointIds: [3] }), 0)).toBe(true)
  })

  it('consumers inside the house consumption do not make a consumer category', () => {
    const inHouse = store({ consumerIds: [5], consumerInstanceIsHomeConsumption: () => true })
    expect(categoryHasComponent('consumer', inHouse, 0)).toBe(false)
    expect(categoryHasComponent('consumer', store({ consumerIds: [5] }), 0)).toBe(true)
  })

  it('counter follows the lines of the loaded data', () => {
    expect(categoryHasComponent('counter', store({}), 0)).toBe(false)
    expect(categoryHasComponent('counter', store({}), 2)).toBe(true)
  })
})

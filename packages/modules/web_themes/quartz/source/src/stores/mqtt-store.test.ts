import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'

const publishAsync = vi.fn()
const connectOptions: Record<string, unknown>[] = []

vi.mock('mqtt', () => {
  class ErrorWithReasonCode extends Error {
    code: number
    constructor(message: string, code: number) {
      super(message)
      this.code = code
    }
  }
  return {
    default: {
      ErrorWithReasonCode,
      connect: (_url: string, options: Record<string, unknown>) => {
        connectOptions.push(options)
        return { on: vi.fn(), subscribe: vi.fn(), unsubscribe: vi.fn(), end: vi.fn(), publishAsync }
      },
    },
  }
})

import { useMqttStore } from './mqtt-store'
import { useToasts } from '@/composables/useToasts'

function newStore() {
  const store = useMqttStore()
  store.initialize()
  return store
}

beforeEach(() => {
  vi.stubGlobal('location', { protocol: 'http:', hostname: 'openwb', port: '', reload: vi.fn() })
  vi.stubGlobal('document', { cookie: '' })
  setActivePinia(createPinia())
  publishAsync.mockReset()
  publishAsync.mockResolvedValue(undefined)
  connectOptions.length = 0
  useToasts().toasts.value = []
})

describe('connection', () => {
  it('uses MQTT 5 with a clean session and a client id the backend accepts in topics', () => {
    newStore()
    const options = connectOptions[0]
    expect(options.protocolVersion).toBe(5)
    expect(options.clean).not.toBe(false)
    expect(options.clientId).toMatch(/^[A-Za-z0-9_]+$/)
  })
})

describe('commands', () => {
  // setdata.py drops a command whose topic does not end in the command name once user management is on,
  // and the broker roles only allow openWB/set/command/+/todo/<command>
  it('publishes to the topic that ends in the command name, not retained, exactly once', async () => {
    const store = newStore()
    store.fetchDailyLog(new Date(2026, 10, 27))
    await nextTick()
    const [topic, payload, options] = publishAsync.mock.calls[0]
    expect(topic).toMatch(/^openWB\/set\/command\/[A-Za-z0-9_]+\/todo\/getDailyLog$/)
    expect(JSON.parse(payload)).toEqual({ command: 'getDailyLog', data: { date: '20261127' } })
    expect(options).toEqual({ qos: 2, retain: false })
  })

  it('password reset commands carry their name in the topic as well', async () => {
    const store = newStore()
    store.requestPasswordResetToken('anna')
    store.resetUserPassword('anna', 'tok', 'pw')
    await nextTick()
    expect(publishAsync.mock.calls.map((c) => c[0].split('/').pop())).toEqual([
      'createPasswordResetToken',
      'resetUserPassword',
    ])
  })
})

describe('writes', () => {
  it('puts the old value back and tells the user when the broker refuses the write', async () => {
    const store = newStore()
    store.topics['openWB/chargepoint/3/set/manual_lock'] = false
    publishAsync.mockRejectedValueOnce(new Error('Not authorized'))
    store.setChargePointManualLock(3, true)
    expect(store.topics['openWB/chargepoint/3/set/manual_lock']).toBe(true)
    await vi.waitFor(() => expect(store.topics['openWB/chargepoint/3/set/manual_lock']).toBe(false))
    expect(useToasts().toasts.value).toHaveLength(1)
  })

  it('keeps the new value when the broker accepts it', async () => {
    const store = newStore()
    store.topics['openWB/chargepoint/3/set/manual_lock'] = false
    store.setChargePointManualLock(3, true)
    await nextTick()
    expect(publishAsync.mock.calls[0][0]).toBe('openWB/set/chargepoint/3/set/manual_lock')
    expect(store.topics['openWB/chargepoint/3/set/manual_lock']).toBe(true)
    expect(useToasts().toasts.value).toHaveLength(0)
  })

  it('restores a nested field of a template on refusal', async () => {
    const store = newStore()
    store.topics['openWB/chargepoint/3/set/charge_template'] = { id: 7, chargemode: { selected: 'stop' } }
    publishAsync.mockRejectedValueOnce(new Error('Not authorized'))
    store.setChargePointChargeMode(3, 'instant_charging')
    await vi.waitFor(() =>
      expect(store.topics['openWB/chargepoint/3/set/charge_template']).toEqual({
        id: 7,
        chargemode: { selected: 'stop' },
      }),
    )
  })
})

describe('charge plans', () => {
  // plan ids are numbered by the backend across all templates - the client must not invent them
  it('adds plans through the backend commands', async () => {
    const store = newStore()
    store.topics['openWB/chargepoint/3/set/charge_template'] = { id: 7, chargemode: { selected: 'stop' } }
    store.addChargePlan(3, 'time')
    store.addChargePlan(3, 'scheduled')
    await nextTick()
    const sent = publishAsync.mock.calls.map((c) => ({ command: c[0].split('/').pop(), ...JSON.parse(c[1]).data }))
    expect(sent).toEqual([
      { command: 'addChargeTemplateTimeChargingPlan', template: 7, chargepoint: 3, changed_in_theme: true },
      { command: 'addChargeTemplateSchedulePlan', template: 7, chargepoint: 3, changed_in_theme: true },
    ])
  })
})

describe('missing data', () => {
  // a role without graph access never receives the live feed - its zeros must not pass for real values
  it('knows whether the live feed has arrived', () => {
    const store = newStore()
    expect(store.liveValuesReceived).toBe(false)
    store.topics['openWB/graph/lastlivevaluesJson'] = { grid: 0 }
    expect(store.liveValuesReceived).toBe(true)
  })

  it('knows whether a battery is configured', () => {
    const store = newStore()
    expect(store.batteryConfigured).toBe(false)
    store.topics['openWB/bat/config/configured'] = true
    expect(store.batteryConfigured).toBe(true)
  })

  it('knows whether an inverter is configured', () => {
    const store = newStore()
    expect(store.pvConfigured).toBe(false)
    store.topics['openWB/pv/config/configured'] = true
    expect(store.pvConfigured).toBe(true)
  })

  it('only knows what a user may do once the user-management flag has arrived', () => {
    const store = newStore()
    expect(store.userManagementKnown()).toBe(false)
    store.topics['openWB/system/security/user_management_active'] = false
    expect(store.userManagementKnown()).toBe(true)
  })

  it('knows whether the user may change the battery settings', () => {
    const store = newStore()
    expect(store.accessBatteryControlAllowed()).toBe(false)
    store.topics['openWB/system/security/access/ActiveBatControlConfiguration'] = true
    expect(store.accessBatteryControlAllowed()).toBe(true)
  })

  describe('controls with user management', () => {
    const UM = 'openWB/system/security/user_management_active'
    const cpConfig = 'openWB/chargepoint/3/config'

    it('offers nothing until it is known whether user management is on', () => {
      const store = newStore()
      store.topics[cpConfig] = { name: 'CP', template: 0 }
      expect(store.accessChargePointAllowed(3)).toBe(false)
    })

    it('without user management a chargepoint with a configuration is offered', () => {
      const store = newStore()
      store.topics[UM] = false
      store.topics[cpConfig] = { name: 'CP', template: 0 }
      expect(store.accessChargePointAllowed(3)).toBe(true)
    })

    // an installer role reads the configuration but not the control topics, and may not write them
    it('with user management a chargepoint needs its control topic as well', () => {
      const store = newStore()
      store.topics[UM] = true
      store.topics[cpConfig] = { name: 'CP', template: 0 }
      expect(store.accessChargePointAllowed(3)).toBe(false)
      store.topics['openWB/chargepoint/3/set/manual_lock'] = false
      expect(store.accessChargePointAllowed(3)).toBe(true)
    })

    it('consumers and manual SoC follow the same rule', () => {
      const store = newStore()
      store.topics[UM] = true
      store.topics['openWB/consumer/5/module'] = { name: 'WP' }
      expect(store.accessConsumerAllowed(5)).toBe(false)
      store.topics['openWB/consumer/5/usage'] = {}
      expect(store.accessConsumerAllowed(5)).toBe(true)
      expect(store.vehicleSocEditable(2)).toBe(false)
      store.topics['openWB/vehicle/2/soc_module/calculated_soc_state'] = {}
      expect(store.vehicleSocEditable(2)).toBe(true)
    })
  })
})

describe('current price and forecast', () => {
  const at = (h: number, m: number) => String(Math.floor(new Date(2026, 10, 27, h, m).getTime() / 1000))

  // the backend prunes old prices only every few minutes - the slot that just ended must not count as current
  it('uses the price of the slot that is running, not simply the first entry', () => {
    vi.useFakeTimers()
    try {
      vi.setSystemTime(new Date(2026, 10, 27, 12, 20))
      const store = newStore()
      store.topics['openWB/optional/ep/get/prices'] = { [at(12, 0)]: 0.0003, [at(12, 15)]: 0.0002, [at(12, 30)]: 0.0004 }
      expect(store.currentElectricityPrice).toBe(20)
      store.topics['openWB/optional/ep/get/prices'] = { [at(13, 0)]: 0.0005 }
      expect(store.currentElectricityPrice).toBe(50) // nothing started yet: the first entry
    } finally {
      vi.useRealTimers()
    }
  })

  it('uses the forecast of the slot that is running', () => {
    vi.useFakeTimers()
    try {
      vi.setSystemTime(new Date(2026, 10, 27, 12, 20))
      const store = newStore()
      store.topics['openWB/optional/forecast/get/values'] = { [at(12, 0)]: 1000, [at(13, 0)]: 3000 }
      expect(store.currentForecastPower).toBe(1)
    } finally {
      vi.useRealTimers()
    }
  })
})

describe('consumer temperatures and range unit', () => {
  it('skips a sensor without a reading but keeps the numbering', () => {
    const store = newStore()
    store.topics['openWB/consumer/5/get/temperatures'] = [null, 41.5, 38]
    expect(store.consumerTemperatures(5)).toEqual([
      { index: 1, value: 41.5 },
      { index: 2, value: 38 },
    ])
  })

  it('takes the range unit from the general setting, then from a connected chargepoint, else km', () => {
    const store = newStore()
    expect(store.rangeUnit(2)).toBe('km')
    store.topics['openWB/chargepoint/3/get/connected_vehicle/info'] = { id: 2, name: 'Auto' }
    store.topics['openWB/chargepoint/3/get/connected_vehicle/soc'] = { range_unit: 'mi' }
    expect(store.rangeUnit(2)).toBe('mi')
    store.topics['openWB/general/range_unit'] = 'km'
    expect(store.rangeUnit(2)).toBe('km')
  })
})

describe('what the live feed tells about the installation', () => {
  // a role that gets the graph feed but not the configured flags still has to see inverter and battery
  it('knows about an inverter and a battery from the live feed fields', () => {
    const store = newStore()
    expect(store.pvConfigured).toBe(false)
    expect(store.batteryConfigured).toBe(false)
    store.topics['openWB/graph/lastlivevaluesJson'] = { grid: 1, 'pv-all': 4.9, 'bat-all-soc': 60 }
    expect(store.pvConfigured).toBe(true)
    expect(store.batteryConfigured).toBe(true)
  })

  it('only lists components whose configuration the user receives', () => {
    const store = newStore()
    store.topics['openWB/counter/get/hierarchy'] = [
      { id: 0, type: 'counter', children: [{ id: 1, type: 'inverter', children: [] }, { id: 15, type: 'counter', children: [] }] },
    ]
    expect(store.inverterIds).toEqual([])
    expect(store.gridCounterAccessible()).toBe(false)
    store.topics['openWB/system/device/1/component/1/config'] = { name: 'WR' }
    store.topics['openWB/system/device/1/component/0/config'] = { name: 'EVU' }
    expect(store.inverterIds).toEqual([1])
    expect(store.gridCounterAccessible()).toBe(true)
  })
})

describe('SoC capability of the connected vehicle', () => {
  it('uses the vehicle SoC module when it can be read, else the SoC the chargepoint reports', () => {
    const store = newStore()
    store.topics['openWB/chargepoint/4/get/connected_vehicle/info'] = { id: 1, name: 'Auto' }
    expect(store.chargePointConnectedVehicleSocType(4)).toBeUndefined()
    store.topics['openWB/chargepoint/4/get/connected_vehicle/soc'] = { soc: 64, range_charged: 0, range_unit: 'km' }
    expect(store.chargePointConnectedVehicleSocType(4)).toBe('reported')
    store.topics['openWB/vehicle/1/soc_module/config'] = { type: 'mqtt' }
    expect(store.chargePointConnectedVehicleSocType(4)).toBe('mqtt')
  })
})

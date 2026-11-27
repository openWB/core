// @vitest-environment happy-dom
import { describe, expect, it, vi } from 'vitest'
import { createApp, nextTick } from 'vue'
import { createPinia } from 'pinia'

vi.mock('mqtt', () => ({
  default: {
    ErrorWithReasonCode: class extends Error {},
    connect: () => ({ on: vi.fn(), subscribe: vi.fn(), unsubscribe: vi.fn(), end: vi.fn(), publishAsync: vi.fn() }),
  },
}))
// the charts need a canvas, which the test DOM does not have - they are not what this test is about
const chartData: { datasets: { label?: string; data: { x: number; y: number }[] }[] }[] = []
vi.mock('vue-chartjs', () => ({
  Line: {
    props: ['data', 'options'],
    setup(props: { data: (typeof chartData)[number] }) {
      return () => {
        chartData.push(props.data)
        return null
      }
    },
  },
}))

import App from './App.vue'
import { useMqttStore } from './stores/mqtt-store'

// Type-checking cannot see an error that only happens while the app starts (e.g. a value used before it is
// defined) and the result is a blank page. Mounting the whole component tree runs every setup() and watcher.
async function mountApp(topics: Record<string, unknown>): Promise<string> {
  const app = createApp(App)
  // Vue reports errors in setup and watchers to this handler instead of throwing them
  app.config.errorHandler = (error) => {
    throw error
  }
  const pinia = createPinia()
  app.use(pinia)
  const store = useMqttStore(pinia)
  store.initialize()
  Object.assign(store.topics, topics)
  const root = document.createElement('div')
  document.body.appendChild(root)
  app.mount(root)
  await nextTick()
  await nextTick()
  const html = root.innerHTML
  app.unmount()
  root.remove()
  return html
}

describe('App start-up', () => {
  it('renders with no data at all', async () => {
    expect(await mountApp({})).toContain('openWB')
  })

  it('renders a chargepoint for a user who may control it', async () => {
    const html = await mountApp({
      'openWB/system/security/user_management_active': true,
      'openWB/counter/get/hierarchy': [{ id: 0, type: 'counter', children: [{ id: 4, type: 'cp', children: [] }] }],
      'openWB/chargepoint/4/config': { name: 'MQTT-Ladepunkt 4', template: 0 },
      'openWB/chargepoint/4/set/manual_lock': false,
    })
    expect(html).toContain('MQTT-Ladepunkt 4')
  })

  it('renders for a user who receives only the basic topics', async () => {
    const html = await mountApp({
      'openWB/system/security/user_management_active': true,
      'openWB/counter/get/hierarchy': [{ id: 0, type: 'counter', children: [{ id: 4, type: 'cp', children: [] }] }],
    })
    expect(html).toContain('openWB')
    expect(html).not.toContain('MQTT-Ladepunkt 4')
  })

  // Chart.js' 'index' tooltip pairs the datasets by array position, so every dataset must be on the same timestamps
  it('puts the forecast and the log lines of a mid-day start on the same timestamps', async () => {
    const day = new Date()
    day.setHours(0, 0, 0, 0)
    const at = (hour: number, minute = 0) => Math.floor(new Date(day).setHours(hour, minute, 0, 0) / 1000)
    const dateString = `${day.getFullYear()}${String(day.getMonth() + 1).padStart(2, '0')}${String(day.getDate()).padStart(2, '0')}`
    const entry = (hour: number, minute: number, pv: number) => ({
      timestamp: at(hour, minute),
      counter: { counter0: { grid: true, power_imported: 0, power_exported: pv } },
      pv: { all: { power_exported: pv }, pv1: { power_exported: pv } },
    })
    chartData.length = 0
    await mountApp({
      'openWB/system/security/user_management_active': false,
      'openWB/counter/get/hierarchy': [{ id: 0, type: 'counter', children: [{ id: 1, type: 'inverter', children: [] }] }],
      'openWB/system/device/1/component/1/config': { name: 'WR' },
      'openWB/pv/config/configured': true,
      'openWB/optional/forecast/configured': true,
      // forecast every hour of the day, the log only starts at 13:00 and ends at 13:10
      'openWB/optional/forecast/get/values': Object.fromEntries(Array.from({ length: 24 }, (_, h) => [at(h), h * 100])),
      [`openWB/log/daily/${dateString}`]: { entries: [entry(13, 0, 2), entry(13, 5, 3), entry(13, 10, 4)], names: {} },
    })
    const datasets = chartData.at(-1)?.datasets ?? []
    expect(datasets.map((d) => d.label)).toContain('Prognose')
    const xs = datasets.map((d) => d.data.map((p) => p.x))
    xs.forEach((x) => expect(x).toEqual(xs[0]))
    const forecast = datasets.find((d) => d.label === 'Prognose')!
    const grid = datasets.find((d) => d.label === 'Netz')!
    const first = grid.data.findIndex((p) => Number.isFinite(p.y))
    // the first log entry (13:00) is compared with the forecast of 13:00
    expect(forecast.data[first].x).toBe(at(13) * 1000)
    expect(forecast.data[first].y).toBe(1.3)
  })

  // every stop of the tooltip inside the logged range must have the log values, not only the forecast
  it('has no tooltip stop with only the forecast while the log has data', async () => {
    const day = new Date()
    day.setHours(0, 0, 0, 0)
    const at = (hour: number, minute = 0, second = 0) => Math.floor(new Date(day).setHours(hour, minute, second, 0) / 1000)
    const dateString = `${day.getFullYear()}${String(day.getMonth() + 1).padStart(2, '0')}${String(day.getDate()).padStart(2, '0')}`
    // log every 5 minutes at 27 s past, forecast every 15 minutes on the full minute
    const entries = Array.from({ length: 7 }, (_, i) => ({
      timestamp: at(12, i * 5, 27),
      counter: { counter0: { grid: true, power_imported: 1, power_exported: 0 } },
    }))
    chartData.length = 0
    await mountApp({
      'openWB/system/security/user_management_active': false,
      'openWB/counter/get/hierarchy': [{ id: 0, type: 'counter', children: [] }],
      'openWB/optional/forecast/configured': true,
      'openWB/optional/forecast/get/values': Object.fromEntries([0, 15, 30, 45].map((m) => [at(12, m), m * 10]).concat([[at(13), 600]])),
      [`openWB/log/daily/${dateString}`]: { entries, names: {} },
    })
    const datasets = chartData.at(-1)?.datasets ?? []
    const grid = datasets.find((d) => d.label === 'Netz')!
    const firstLogged = at(12, 0, 27) * 1000
    const lastLogged = at(12, 30, 27) * 1000
    const inside = grid.data.filter((p) => p.x >= firstLogged && p.x <= lastLogged)
    expect(inside.length).toBe(7)
    inside.forEach((p) => expect(Number.isFinite(p.y)).toBe(true))
  })
})

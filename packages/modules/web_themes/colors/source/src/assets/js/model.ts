/*
 * model.ts
 * colors theme for openwb 2.0
 * Copyright (c) 2022 Claus Hagen
 */

// this is the model for global data. It contains all values required by the different parts of the front end
// Components have their local model

import { reactive, ref } from 'vue'
import { ShDevice, GlobalData } from './types'
import type { PowerItem, ItemProps } from './types'

export const masterData: { [key: string] : ItemProps } = reactive({
  evuIn: {name: 'Netz', color: 'var(--color-evu)', icon: "\uf275"},
  pv: { name: 'PV', color: 'var(--color-pv', icon: "\uf5ba" },
  batOut: { name: 'Bat >', color: 'var(--color-battery)', icon: "\uf5df\uf061" },
  evuOut: { name: 'Export', color: 'var(--color-export)', icon: "\uf061\uf57d" },
  charging: { name: 'Laden', color: 'var(--color-charging)', icon: "\uf5e7" },
  devices: { name: 'Geräte', color: 'var(--color-devices)', icon: "\uf1e6" },
  batIn: { name: '> Bat', color: 'var(--color-battery)', icon: "\uf061\uf5df" },
  house: { name: 'Haus', color: 'var(--color-house)', icon: "\uf015" },
})
export const historicSummary: { [key: string]: PowerItem } = reactive({
  //evuIn: { name: 'Netz', power: 0, energy: 0, energyPv: 0, energyBat: 0, pvPercentage: 0, color: 'var(--color-evu)', icon: masterData.evuIn.icon },
  evuIn: createPowerItem ('evuIn'),
  pv: createPowerItem ('pv'),
  batOut: createPowerItem ('batOut'),
  evuOut: createPowerItem ('evuOut'),
  charging: createPowerItem ('charging'),
  devices: createPowerItem ('devices'),
  batIn: createPowerItem ('batIn'),
  house: createPowerItem ('house'),
})
export const sourceSummary: { [key: string]: PowerItem } = reactive({
  // evuIn: { name: 'Netz', power: 0, energy: 0, energyPv: 0, energyBat: 0, pvPercentage: 0, color: 'var(--color-evu)', icon: masterData.evuIn.icon },
  evuIn: createPowerItem ('evuIn'),
  pv: createPowerItem ('pv'),
  batOut: createPowerItem ('batOut'),
})
export const usageSummary: { [key: string]: PowerItem } = reactive({
  evuOut: createPowerItem ('evuOut'),
  charging: createPowerItem ('charging'),
  devices: createPowerItem ('devices'),
  batIn: createPowerItem ('batIn'),
  house: createPowerItem ('house'),
})
export const shDevices: { [key: number]: ShDevice }= reactive([])
export const globalData = reactive(new GlobalData())
export const etPriceList = ref('')
// Initiate the model
Array.from({ length: 9 }, (v, i) => shDevices[i]= new ShDevice(i))
// init colors

Object.values(shDevices).forEach (device => {
  device.color = 'var(--color-sh' + (device.id + 1) + ')'
})

function createPowerItem (key: string) : PowerItem {
  let p: PowerItem = {
    name: masterData[key].name, power: 0, energy: 0, energyPv: 0, energyBat: 0, pvPercentage: 0, color: masterData[key].color, icon: masterData[key].icon
  }
  return (p)
}

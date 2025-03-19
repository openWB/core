/*
 * model.ts
 * colors theme for openwb 2.0
 * Copyright (c) 2022 Claus Hagen
 */

// this is the model for global data. It contains all values required by the different parts of the front end
// Components have their local model

import { reactive, ref } from 'vue'
import { GlobalData } from './themeConfig'
import type { PowerItem, ItemProps } from './types'
import { PvSystem } from './types'

export const masterData: { [key: string]: ItemProps } = reactive({
	evuIn: { name: 'Netz', color: 'var(--color-evu)', icon: '\uf275' },
	pv: { name: 'PV', color: 'var(--color-pv', icon: '\uf5ba' },
	batOut: {
		name: 'Bat >',
		color: 'var(--color-battery)',
		icon: '\uf5df\uf061',
	},
	evuOut: {
		name: 'Export',
		color: 'var(--color-export)',
		icon: '\uf061\uf57d',
	},
	charging: { name: 'Laden', color: 'var(--color-charging)', icon: '\uf5e7' },
	devices: { name: 'Geräte', color: 'var(--color-devices)', icon: '\uf1e6' },
	batIn: { name: '> Bat', color: 'var(--color-battery)', icon: '\uf061\uf5df' },
	house: { name: 'Haus', color: 'var(--color-house)', icon: '\uf015' },
	cp1: { name: 'Ladepunkt', color: 'var(--color-cp1)', icon: 'Ladepunkt' },
	cp2: { name: 'Ladepunkt', color: 'var(--color-cp2)', icon: 'Ladepunkt' },
	cp3: { name: 'Ladepunkt', color: 'var(--color-cp3)', icon: 'Ladepunkt' },
	cp4: { name: 'Ladepunkt', color: 'var(--color-cp4)', icon: 'Ladepunkt' },
	cp5: { name: 'Ladepunkt', color: 'var(--color-cp5)', icon: 'Ladepunkt' },
	cp6: { name: 'Ladepunkt', color: 'var(--color-cp6)', icon: 'Ladepunkt' },
	cp7: { name: 'Ladepunkt', color: 'var(--color-cp7)', icon: 'Ladepunkt' },
	cp8: { name: 'Ladepunkt', color: 'var(--color-cp8)', icon: 'Ladepunkt' },
	sh1: { name: 'Gerät', color: 'var(--color-sh1)', icon: 'Gerät' },
	sh2: { name: 'Gerät', color: 'var(--color-sh2)', icon: 'Gerät' },
	sh3: { name: 'Gerät', color: 'var(--color-sh3)', icon: 'Gerät' },
	sh4: { name: 'Gerät', color: 'var(--color-sh4)', icon: 'Gerät' },
	sh5: { name: 'Gerät', color: 'var(--color-sh5)', icon: 'Gerät' },
	sh6: { name: 'Gerät', color: 'var(--color-sh6)', icon: 'Gerät' },
	sh7: { name: 'Gerät', color: 'var(--color-sh7)', icon: 'Gerät' },
	sh8: { name: 'Gerät', color: 'var(--color-sh8)', icon: 'Gerät' },
	sh9: { name: 'Gerät', color: 'var(--color-sh9)', icon: 'Gerät' },
	pv1: { name: 'PV', color: 'var(--color-pv1)', icon: 'Wechselrichter' },
	pv2: { name: 'PV', color: 'var(--color-pv2)', icon: 'Wechselrichter' },
	pv3: { name: 'PV', color: 'var(--color-pv3)', icon: 'Wechselrichter' },
	pv4: { name: 'PV', color: 'var(--color-pv4)', icon: 'Wechselrichter' },
	pv5: { name: 'PV', color: 'var(--color-pv5)', icon: 'Wechselrichter' },
	pv6: { name: 'PV', color: 'var(--color-pv6)', icon: 'Wechselrichter' },
	pv7: { name: 'PV', color: 'var(--color-pv7)', icon: 'Wechselrichter' },
	pv8: { name: 'PV', color: 'var(--color-pv8)', icon: 'Wechselrichter' },
	pv9: { name: 'PV', color: 'var(--color-pv9)', icon: 'Wechselrichter' },
	bat1: { name: 'Speicher', color: 'var(--color-battery)', icon: 'Speicher' },
	bat2: { name: 'Speicher', color: 'var(--color-battery)', icon: 'Speicher' },
	bat3: { name: 'Speicher', color: 'var(--color-battery)', icon: 'Speicher' },
	bat4: { name: 'Speicher', color: 'var(--color-battery)', icon: 'Speicher' },
	bat5: { name: 'Speicher', color: 'var(--color-battery)', icon: 'Speicher' },
	bat6: { name: 'Speicher', color: 'var(--color-battery)', icon: 'Speicher' },
	bat7: { name: 'Speicher', color: 'var(--color-battery)', icon: 'Speicher' },
	bat8: { name: 'Speicher', color: 'var(--color-battery)', icon: 'Speicher' },
	bat9: { name: 'Speicher', color: 'var(--color-battery)', icon: 'Speicher' },
})
class HistoricSummary {
	private _items: { [key: string]: PowerItem } = {}
	constructor() {
		this.addItem('evuIn')
		this.addItem('pv')
		this.addItem('batOut')
		this.addItem('evuOut')
		this.addItem('charging')
		this.addItem('devices')
		this.addItem('batIn')
		this.addItem('house')
	}
	get items() {
		return this._items
	}
	keys() {
		return Object.keys(this._items)
	}
	values() {
		return Object.values(this._items)
	}
	addItem(key: string, useColor?: string) {
		this._items[key] = useColor
			? createPowerItem(key, useColor)
			: createPowerItem(key)
	}
	setEnergy(cat: string, val: number) {
		if (!this.keys().includes(cat)) {
			this.addItem(cat)
		}
		this._items[cat].energy = val
	}
	setEnergyPv(cat: string, val: number) {
		if (!this.keys().includes(cat)) {
			this.addItem(cat)
		}
		this._items[cat].energyPv = val
	}
	setEnergyBat(cat: string, val: number) {
		if (!this.keys().includes(cat)) {
			this.addItem(cat)
		}
		this._items[cat].energyBat = val
	}
	setPvPercentage(cat: string, val: number) {
		if (!this.keys().includes(cat)) {
			this.addItem(cat)
		}
		this._items[cat].pvPercentage = val <= 100 ? val : 100
	}
	calculateHouseEnergy() {
		this._items.house.energy =
			this._items.evuIn.energy +
			this._items.pv.energy +
			this._items.batOut.energy -
			this._items.evuOut.energy -
			this._items.batIn.energy -
			this._items.charging.energy -
			this._items.devices.energy
	}
}
export let historicSummary = reactive(new HistoricSummary())
export function resetHistoricSummary() {
	historicSummary = new HistoricSummary()
}
export const sourceSummary: { [key: string]: PowerItem } = reactive({
	evuIn: createPowerItem('evuIn'),
	pv: createPowerItem('pv'),
	batOut: createPowerItem('batOut'),
})
export const usageSummary: { [key: string]: PowerItem } = reactive({
	evuOut: createPowerItem('evuOut'),
	charging: createPowerItem('charging'),
	devices: createPowerItem('devices'),
	batIn: createPowerItem('batIn'),
	house: createPowerItem('house'),
})
export const globalData = reactive(new GlobalData())
export const etPriceList = ref('')
export const energyMeterNeedsRedraw = ref(false)
function createPowerItem(key: string, useColor?: string): PowerItem {
	const p: PowerItem = {
		name: masterData[key] ? masterData[key].name : 'item',
		power: 0,
		energy: 0,
		energyPv: 0,
		energyBat: 0,
		pvPercentage: 0,
		color: useColor
			? useColor
			: masterData[key]
				? masterData[key].color
				: 'var(--color-charging)',
		icon: masterData[key] ? masterData[key].icon : '',
		showInGraph: true,
	}
	return p
}
export function correctHouseConsumption() {
	usageSummary.house.power =
		usageSummary.house.power - usageSummary.devices.power
}

export const currentTime = ref(new Date())
export const pvSystems = ref(new Map<number, PvSystem>())
export const addPvSystem = (index: number) => {
	pvSystems.value.set(index, new PvSystem(index))
	pvSystems.value.get(index)!.color =
		masterData['pv' + pvSystems.value.size].color
}

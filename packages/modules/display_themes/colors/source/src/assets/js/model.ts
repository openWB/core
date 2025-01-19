/*
 * model.ts
 * colors theme for openwb 2.0
 * Copyright (c) 2022 Claus Hagen
 */

// this is the model for global data. It contains all values required by the different parts of the front end
// Components have their local model

import { reactive, ref } from 'vue'
import { Modal } from 'bootstrap'
import { GlobalData } from './types'
import type { PowerItem, ItemProps } from './types'

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
	addItem(key: string) {
		this._items[key] = createPowerItem(key)
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
		this._items[cat].pvPercentage = val
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
export let historicSummary = new HistoricSummary()
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
function createPowerItem(key: string): PowerItem {
	const p: PowerItem = {
		name: masterData[key] ? masterData[key].name : 'item',
		power: 0,
		energy: 0,
		energyPv: 0,
		energyBat: 0,
		pvPercentage: 0,
		color: masterData[key] ? masterData[key].color : 'var(--color-charging)',
		icon: masterData[key] ? masterData[key].icon : '',
	}
	return p
}
export const displayConfig = reactive({
	active: false,
	locked: true,
	usePin: false,
	code: '',
	timeout: 60,
	localCpOnly: false,
})
export function unlockDisplay() {
	if (displayConfig.usePin && displayConfig.locked) {
		const numberpad = new Modal('#numberpad')
		numberpad.toggle()
	} else {
		displayConfig.locked = false
		setTimeout(() => {
			displayConfig.locked = true
		}, displayConfig.timeout * 1000)
	}
}

export function checkCode(code: string) {
	return code == displayConfig.code
}

export const currentTime = ref(new Date())

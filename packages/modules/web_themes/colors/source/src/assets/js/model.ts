/*
 * model.ts
 * colors theme for openwb 2.0
 * Copyright (c) 2022 Claus Hagen
 */

// this is the model for global data. It contains all values required by the different parts of the front end
// Components have their local model

import { reactive, ref } from 'vue'
import { GlobalData } from './themeConfig'
import { type PowerItem, type ItemProps, PowerItemType } from './types'
import { PvSystem } from './types'
import { graphData } from '@/components/powerGraph/model'
//import { Counter } from '@/components/counterList/model'

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
	counters: { name: 'Zähler', color: 'var(--color-counters)', icon: '\uf0eb' },
	batIn: { name: '> Bat', color: 'var(--color-battery)', icon: '\uf061\uf5df' },
	house: { name: 'Haus', color: 'var(--color-house)', icon: '\uf015' },
})
export const colormap: Map<string, string[]> = new Map([
	[
		'pv',
		[
			'var(--color-pv1)',
			'var(--color-pv2)',
			'var(--color-pv3)',
			'var(--color-pv4)',
			'var(--color-pv5)',
			'var(--color-pv6)',
			'var(--color-pv7)',
			'var(--color-pv8)',
			'var(--color-pv9)	',
		],
	],
	[
		'bat',
		[
			'var(--color-bat1)',
			'var(--color-bat2)',
			'var(--color-bat3)',
			'var(--color-bat4)',
			'var(--color-bat5)',
			'var(--color-bat6)',
			'var(--color-bat7)',
			'var(--color-bat8)',
			'var(--color-bat9)	',
		],
	],
	[
		'cp',
		[
			'var(--color-cp1)',
			'var(--color-cp2)',
			'var(--color-cp3)',
			'var(--color-cp4)',
			'var(--color-cp5)',
			'var(--color-cp6)',
			'var(--color-cp7)',
			'var(--color-cp8)	',
		],
	],
	[
		'counter',
		[
			'var(--color-ctr1)',
			'var(--color-ctr2)',
			'var(--color-ctr3)',
			'var(--color-ctr4)',
			'var(--color-ctr5)',
			'var(--color-ctr6)',
			'var(--color-ctr7)',
			'var(--color-ctr8)',
			'var(--color-ctr9)',
			'var(--color-ctr10)	',
		],
	],
	[
		'sh',
		[
			'var(--color-sh1)',
			'var(--color-sh2)',
			'var(--color-sh3)',
			'var(--color-sh4)',
			'var(--color-sh5)',
			'var(--color-sh6)',
			'var(--color-sh7)',
			'var(--color-sh8)',
			'var(--color-sh9)	',
		],
	],
])

export function getColor(category: string, index: number): string {
	if (colormap.has(category)) {
		const colors = colormap.get(category)!
		return colors[index % colors.length]
	}
	return 'var(--color-charging)'
}
class ItemList {
	private _items: Map<string, PowerItem> = new Map()
	constructor() {
		this.addItem('evuIn')
		this.addItem('pv')
		this.addItem('batOut')
		this.addItem('evuOut')
		this.addItem('charging')
		this.addItem('devices')
		this.addItem('counters')
		this.addItem('batIn')
		this.addItem('house')
	}
	get items() {
		return this._items
	}
	get usageSummary(): PowerItem[] {
		return [
			this._items.get('evuOut')!,
			this._items.get('charging')!,
			this._items.get('devices')!,
			this._items.get('counters')!,
			this._items.get('batIn')!,
			this._items.get('house')!,
		]
	}
	get sourceSummary() {
		return [
			this._items.get('evuIn')!,
			this._items.get('pv')!,
			this._items.get('batOut')!,
		]
	}
	keys() {
		return Array.from(this._items.keys())
	}
	values() {
		return Array.from(this._items.values())
	}
	getItem(key: string): PowerItem {
		return this._items.get(key)!
	}
	addItem(
		key: string,
		type?: PowerItemType,
		template?: PowerItem,
		useColor?: string,
	) {
		let itemType: PowerItemType
		if (type) {
			itemType = type
		} else {
			switch (key) {
				case 'evuIn':
					itemType = PowerItemType.counter
					break
				case 'pv':
					itemType = PowerItemType.inverter
					break
				case 'batOut':
					itemType = PowerItemType.battery
					break
				case 'evuOut':
					itemType = PowerItemType.counter
					break
				case 'charging':
					itemType = PowerItemType.chargepoint
					break
				case 'devices':
					itemType = PowerItemType.device
					break
				case 'counters':
					itemType = PowerItemType.counter
					break
				case 'batIn':
					itemType = PowerItemType.battery
					break
				case 'house':
					itemType = PowerItemType.house
					break
				default:
					itemType = PowerItemType.counter
			}
		}
		this._items.set(
			key,
			useColor
				? createPowerItem(key, itemType, useColor)
				: createPowerItem(key, itemType),
		)
		if (template) {
			this._items.get(key)!.name = template.name
			this._items.get(key)!.icon = template.icon
			this._items.get(key)!.color = template.color
		}
	}
	duplicateItem(key: string, source: PowerItem) {
		let p: PowerItem = createPowerItem(key, source.type)
		p = { ...source }
		this._items.set(key, p)
	}
	getPower(cat: string) {
		return this._items.get(cat)!.power
	}
	setPower(cat: string, val: number) {
		if (!this.items.has(cat)) {
			console.error(`item ${cat} not found in item list`)
		}
		this._items.get(cat)!.power = val
	}
	getEnergy(cat: string) {
		if (!this.items.has(cat)) {
			this.addItem(cat)
		}
		if (graphData.usePastData) {
			return this._items.get(cat)!.past.energy
		} else {
			return this._items.get(cat)!.now.energy
		}
	}
	setEnergy(cat: string, val: number) {
		if (!this.items.has(cat)) {
			console.error(`item ${cat} not found in item list`)
		}
		if (graphData.usePastData) {
			this._items.get(cat)!.past.energy = val
		} else {
			this._items.get(cat)!.now.energy = val
		}
	}
	setEnergyPv(cat: string, val: number) {
		if (!this.items.has(cat)) {
			this.addItem(cat)
		}
		if (graphData.usePastData) {
			this._items.get(cat)!.past.energyPv = val
		} else {
			this._items.get(cat)!.now.energyPv = val
		}
	}
	setEnergyBat(cat: string, val: number) {
		if (!this.items.has(cat)) {
			this.addItem(cat)
		}
		if (graphData.usePastData) {
			this._items.get(cat)!.past.energyBat = val
		} else {
			this._items.get(cat)!.now.energyBat = val
		}
	}
	setPvPercentage(cat: string, val: number) {
		if (!this.items.has(cat)) {
			console.error(`item ${cat} not found in item list`)
		}
		if (graphData.usePastData) {
			this._items.get(cat)!.past.pvPercentage = val <= 100 ? val : 100
		} else {
			this._items.get(cat)!.now.pvPercentage = val <= 100 ? val : 100
		}
	}
	calculatePvPercentage(cat: string) {
		if (!this.items.has(cat)) {
			console.error(`item ${cat} not found in item list`)
		}
		this._items.get(cat)![graphData.graphScope].pvPercentage = Math.round(
			((this.items.get(cat)![graphData.graphScope].energyPv +
				this.items.get(cat)![graphData.graphScope].energyBat) /
				this.items.get(cat)![graphData.graphScope].energy) *
				100,
		)
	}

	calculateHouseEnergy(past = false) {
		if (past) {
			this._items.get('house')!.past.energy =
				this._items.get('evuIn')!.past.energy +
				this._items.get('pv')!.past.energy +
				this._items.get('batOut')!.past.energy -
				this._items.get('evuOut')!.past.energy -
				this._items.get('batIn')!.past.energy -
				this._items.get('charging')!.past.energy -
				this._items.get('devices')!.past.energy -
				this._items.get('counters')!.past.energy
		} else {
			this._items.get('house')!.now.energy =
				this._items.get('evuIn')!.now.energy +
				this._items.get('pv')!.now.energy +
				this._items.get('batOut')!.now.energy -
				this._items.get('evuOut')!.now.energy -
				this._items.get('batIn')!.now.energy -
				this._items.get('charging')!.now.energy -
				this._items.get('devices')!.now.energy -
				this._items.get('counters')!.now.energy
		}
	}
}
export const registry = reactive(new ItemList())
export function resetHistoricData() {
	registry.values().forEach((item) => {
		item.past.energy = 0
		item.past.energyPv = 0
		item.past.energyBat = 0
		item.past.pvPercentage = 0
	})
}
export const sourceSummary: { [key: string]: PowerItem } = reactive({
	evuIn: createPowerItem('evuIn', PowerItemType.counter),
	pv: createPowerItem('pv', PowerItemType.pvSummary),
	batOut: createPowerItem('batOut', PowerItemType.batterySummary),
})
/* export const usageSummary: { [key: string]: PowerItem } = reactive({
	evuOut: createPowerItem('evuOut', PowerItemType.counter),
	charging: createPowerItem('charging', PowerItemType.chargeSummary),
	devices: createPowerItem('devices', PowerItemType.deviceSummary),
	counters: createPowerItem('counters', PowerItemType.counterSummary),
	batIn: createPowerItem('batIn', PowerItemType.batterySummary),
	house: createPowerItem('house', PowerItemType.house),
}) */
export const globalData = reactive(new GlobalData())
export const etPriceList = ref('')
export const energyMeterNeedsRedraw = ref(false)

export function createPowerItem(
	key: string,
	type: PowerItemType,
	useColor?: string,
): PowerItem {
	const p: PowerItem = {
		name: masterData[key] ? masterData[key].name : 'item',
		type: type,
		power: 0,
		now: {
			energy: 0,
			energyPv: 0,
			energyBat: 0,
			pvPercentage: 0,
		},
		past: {
			energy: 0,
			energyPv: 0,
			energyBat: 0,
			pvPercentage: 0,
		},
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
	registry.setPower(
		'house',
		registry.getItem('house')!.power - registry.getItem('devices')!.power,
	)
}

export const currentTime = ref(new Date())
export const pvSystems = ref(new Map<number, PvSystem>())
export const addPvSystem = (index: number) => {
	pvSystems.value.set(index, new PvSystem(index))
	assignPvSystemColors()
	//pvSystems.value.get(index)!.color =
	//masterData['pv' + pvSystems.value.size].color
}

function assignPvSystemColors() {
	const pvSystemsSorted = [...pvSystems.value.values()].sort(
		(a, b) => a.id - b.id,
	)
	pvSystemsSorted.forEach((system, index) => {
		//system.color = masterData['pv' + (index + 1)].color
		system.color = getColor('pv', index)
	})
}

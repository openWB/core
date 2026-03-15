import { registry } from '@/assets/js/model'
import { savePrefs } from '@/assets/js/themeConfig'
import {
	PowerItemType,
	type EnergyData,
	type PowerItem,
} from '@/assets/js/types'
import { reactive } from 'vue'
export class Counter implements PowerItem {
	id: number
	name = 'Zähler'
	power = 0
	now: EnergyData = {
		energy: 0,
		energyPv: 0,
		energyBat: 0,
		pvPercentage: 0,
	}
	past: EnergyData = {
		energy: 0,
		energyPv: 0,
		energyBat: 0,
		pvPercentage: 0,
	}
	energy_imported = 0
	energy_exported = 0
	grid = false
	counterType = 'counter'
	type = PowerItemType.counter
	color = 'var(--color-ctr7)'
	icon = 'Zähler'
	_showInGraph = false
	constructor(index: number) {
		this.id = index
	}
	get showInGraph() {
		return this._showInGraph
	}
	set showInGraph(value: boolean) {
		this._showInGraph = value
		savePrefs()
	}
}

//export const counters: { [key: number]: Counter } = reactive({})
export const counters = reactive(new Map<number, Counter>())
export function addCounter(index: number, counterType: string, grid = false) {
	if (!counters.has(index)) {
		counters.set(index, new Counter(index))
		counters.get(index)!.counterType = counterType
		counters.get(index)!.grid = grid
		switch (counterType) {
			case 'counter':
				counters.get(index)!.color = grid
					? 'var(--color-evu)'
					: 'var(--color-ctr' + (counters.size - 1) + ')'
				break
			case 'inverter':
				counters.get(index)!.color = 'var(--color-pv)'
				break
			case 'cp':
				counters.get(index)!.color = 'var(--color-charging)'
				break
			case 'bat':
				counters.get(index)!.color = 'var(--color-bat)'
				break
		}
		//console.info('Added counter ' + index)
	} else {
		console.info('Duplicate counter message: ' + index)
	}
}

export function updateCounterSummary(cat: string) {
	switch (cat) {
		case 'power':
			registry.setPower(
				'counters',
				[...counters.values()]
					.filter((ctr) => ctr.showInGraph)
					.reduce((sum, consumer) => sum + consumer.power, 0),
			)
			break
		case 'energy':
			registry.setEnergy(
				'counters',
				[...counters.values()]
					.filter((ctr) => !ctr.showInGraph)
					.reduce((sum, consumer) => sum + consumer.now.energy, 0),
			)
			break
		default:
			console.error('Unknown category')
	}
}

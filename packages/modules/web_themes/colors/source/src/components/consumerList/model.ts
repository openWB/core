import { reactive } from 'vue'
import { savePrefs } from '@/assets/js/themeConfig'
import { registry } from '@/assets/js/model'
import {
	PowerItemType,
	type EnergyData,
	type PowerItem,
} from '@/assets/js/types'
import { shDevices } from '../smartHome/model'

export class Consumer implements PowerItem {
	id: number
	name = 'Verbraucher'
	icon = 'Verbraucher'
	type = PowerItemType.consumer
	power = 0
	runningTime = 0
	private _showInGraph = true
	color = 'white'
	showInList = true
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

	constructor(index: number, showInList = true) {
		this.id = index
		this.showInList = showInList
	}
	get showInGraph() {
		return this._showInGraph
	}
	set showInGraph(val: boolean) {
		this._showInGraph = val
		registry.items.get('consumer' + this.id)!.showInGraph = val
		savePrefs()
	}
	setShowInGraph(val: boolean) {
		this._showInGraph = val
	}
}

export const consumers = reactive(new Map<number, Consumer>())

export function addConsumer(index: number, showInList = true) {
	const consumerColorCount = 5
	if (!consumers.has(index)) {
		consumers.set(index, new Consumer(index, showInList))
		const dev = consumers.get(index)!
		dev.color =
			'var(--color-consumer' +
			(((consumers.size - 1) % consumerColorCount) + 1) +
			')'
		// console.log('Added consumer with index ' + index + ' and color ' + dev.color)
	} else {
		console.warn('Consumer with index ' + index + ' already exists.')
	}
}

export function resetConsumers() {
	consumers.clear()
}

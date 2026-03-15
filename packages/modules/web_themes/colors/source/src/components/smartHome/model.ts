import { reactive } from 'vue'
import { savePrefs } from '@/assets/js/themeConfig'
import { registry } from '@/assets/js/model'
import {
	PowerItemType,
	type EnergyData,
	type PowerItem,
} from '@/assets/js/types'
export class ShDevice implements PowerItem {
	id: string
	name = 'Gerät'
	type = PowerItemType.device
	power = 0
	status = 'off'
	runningTime = 0
	configured = false
	private _showInGraph = true
	color = 'white'
	canSwitch = false
	countAsHouse = false
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
	pvPercentage = 0
	tempConfigured = 0
	temp = [300.0, 300.0, 300.0]
	on = false
	isAutomatic = true
	icon = ''
	constructor(index: string) {
		this.id = index
	}
	get showInGraph() {
		return this._showInGraph
	}
	set showInGraph(val: boolean) {
		this._showInGraph = val
		registry.items.get('sh' + this.id)!.showInGraph = val
		savePrefs()
	}
	setShowInGraph(val: boolean) {
		this._showInGraph = val
	}
}

export const shDevices = reactive(new Map<string, ShDevice>())
export function addShDevice(shIndex: string) {
	if (!shDevices.has(shIndex)) {
		shDevices.set(shIndex, new ShDevice(shIndex))
		shDevices.get(shIndex)!.color = 'var(--color-sh' + shDevices.size + ')'
		// console.info('Added sh device ' + shIndex)
	} else {
		console.info('Duplicate sh device message: ' + shIndex)
	}
}

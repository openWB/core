import { reactive } from 'vue'
import { savePrefs } from '@/assets/js/themeConfig'
import { historicSummary } from '@/assets/js/model'
import { PowerItemType } from '@/assets/js/types'
export class ShDevice {
	id: number
	name = 'Gerät'
	type = PowerItemType.device
	power = 0
	status = 'off'
	energy = 0
	runningTime = 0
	configured = false
	private _showInGraph = true
	color = 'white'
	canSwitch = false
	countAsHouse = false
	energyPv = 0
	energyBat = 0
	pvPercentage = 0
	tempConfigured = 0
	temp = [300.0, 300.0, 300.0]
	on = false
	isAutomatic = true
	icon = ''
	constructor(index: number) {
		this.id = index
	}
	get showInGraph() {
		return this._showInGraph
	}
	set showInGraph(val: boolean) {
		this._showInGraph = val
		historicSummary.items['sh' + this.id].showInGraph = val
		savePrefs()
	}
	setShowInGraph(val: boolean) {
		this._showInGraph = val
	}
}

// export const shDevices: { [key: number]: ShDevice } = reactive({})
export const shDevices = reactive(new Map<number, ShDevice>())
export function addShDevice(shIndex: number) {
	if (!shDevices.has(shIndex)) {
		// shDevices[shIndex] = new ShDevice(shIndex)
		shDevices.set(shIndex, new ShDevice(shIndex))
		//shDevices[shIndex].color =
		//	'var(--color-sh' + Object.values(shDevices).length + ')'
		shDevices.get(shIndex)!.color = 'var(--color-sh' + shDevices.size + ')'
		// console.info('Added sh device ' + shIndex)
	} else {
		console.info('Duplicate sh device message: ' + shIndex)
	}
}

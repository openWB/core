import { reactive } from 'vue'
import { savePrefs } from '@/assets/js/themeConfig'
import { registry } from '@/assets/js/model'
import {
	PowerItemType,
	type EnergyData,
	type PowerItem,
	ChargeMode,
} from '@/assets/js/types'
import { updateConsumerUsage } from '@/assets/js/sendMessages'

type ConsumerUsage = {
	chargemode: string
	eco_charging: {
		price_limit: number
	}
	scheduled_charging: {
		plans: any[]
	}
	time_charging: {
		active: boolean
		plans: any[]
	}
	type: 'continuous' | 'discrete'
	reset_chargemode: {
		active: boolean
		time: string
		frequency: {
			selected: 'daily' | 'once' | 'weekly'
			once: string
			weekly: boolean[]
		}
		chargemode: string
	}
	wait_for_start_active: boolean
}
const usageSample: ConsumerUsage = {
	chargemode: ChargeMode.pv_charging,
	eco_charging: { price_limit: 0.0002 },
	scheduled_charging: { plans: [] },
	time_charging: { active: false, plans: [] },
	type: 'continuous',
	reset_chargemode: {
		active: false,
		time: '07:00',
		frequency: {
			selected: 'daily',
			once: '2026-10-09',
			weekly: [false, false, false, false, false, false, false],
		},
		chargemode: ChargeMode.instant_charging,
	},
	wait_for_start_active: true,
}

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
	priority = 0
	usage: ConsumerUsage | null = null
	statusText = ''
	faultState = 0
	faultText = ''
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
	get chargeMode() {
		const u = this.usage
		if (u) {
			return u.chargemode as ChargeMode
		}
		return ChargeMode['pv_charging']
	}
	set chargeMode(cm: ChargeMode) {
		if (this.usage) {
			this.usage.chargemode = cm
			updateConsumerUsage(this.id, this.usage)
		}
	}
}

export const consumers = reactive(new Map<number, Consumer>())

export function addConsumer(index: number, showInList = true) {
	const consumerColorCount = 9
	if (!consumers.has(index)) {
		consumers.set(index, new Consumer(index, showInList))
		const dev = consumers.get(index)!
		dev.color =
			'var(--color-sh' + (((consumers.size - 1) % consumerColorCount) + 1) + ')'
		// console.log('Added consumer with index ' + index + ' and color ' + dev.color)
	} else {
		console.warn('Consumer with index ' + index + ' already exists.')
	}
}

export function resetConsumers() {
	consumers.clear()
}

import { computed, reactive, ref } from 'vue'
import { extent, scaleBand } from 'd3'
import { mqttSubscribe, mqttUnsubscribe } from '../../assets/js/mqttClient'
import { sendCommand } from '@/assets/js/sendMessages'
import { globalConfig } from '@/assets/js/themeConfig'
import {
	energyMeterNeedsRedraw,
	historicSummary,
	usageSummary,
} from '@/assets/js/model'
import { shDevices } from '../smartHome/model'
import { chargePoints } from '../chargePointList/model'

export const width = 500
export const height = 500
export const margin = { top: 10, right: 20, bottom: 10, left: 25 }

export const consumerCategories = ['charging', 'house', 'batIn', 'devices']

export interface GraphDataItem {
	[key: string]: number
}
export interface RawGraphDataItem {
	[key: string]: string
}
export interface RawDayGraphDataItem {
	timestamp: number
	date: string
	counter: object
	pv: {
		all: { power_exported: number; energy_exported: number; exported: number }
	}
	hc: {
		all: {
			power_imported: number
			energy_imported: number
			energy_exported: number
			imported: number
		}
	}
	bat: {
		all: {
			power_imported: number
			power_exported: number
			energy_imported: number
			energy_exported: number
			imported: number
			exported: number
			soc: number
		}
	}
	cp: object
	ev: object
	sh: object
}

export class GraphData {
	data: GraphDataItem[] = []
	private _graphMode = ''

	get graphMode() {
		return this._graphMode
	}
	set graphMode(mode: string) {
		this._graphMode = mode
	}
}

export const graphData = reactive(new GraphData())
export let animateSourceGraph = true
export let animateUsageGraph = true
export function sourceGraphIsInitialized() {
	animateSourceGraph = false
}
export function sourceGraphIsNotInitialized() {
	animateSourceGraph = true
}

export function usageGraphIsInitialized() {
	animateUsageGraph = false
}
export function usageGraphIsNotInitialized() {
	animateUsageGraph = true
}
export function setInitializeUsageGraph(val: boolean) {
	animateUsageGraph = val
}
export function setGraphData(d: GraphDataItem[]) {
	graphData.data = d
	// graphData.graphMode = graphData.graphMode
}
export const liveGraph = reactive({
	refreshTopicPrefix: 'openWB/graph/' + 'alllivevaluesJson',
	updateTopic: 'openWB/graph/lastlivevaluesJson',
	configTopic: 'openWB/graph/config/#',
	initialized: false,
	initCounter: 0,
	graphRefreshCounter: 0,
	rawDataPacks: [] as RawGraphDataItem[][],
	duration: 0,

	activate() {
		graphData.data = []
		this.unsubscribeUpdates()
		this.subscribeRefresh()
		mqttSubscribe(this.configTopic)
		this.initialized = false
		this.initCounter = 0
		this.graphRefreshCounter = 0
		this.rawDataPacks = []
		resetPvValues()
		energyMeterNeedsRedraw.value = true
	},
	deactivate() {
		this.unsubscribeRefresh()
		this.unsubscribeUpdates()
		mqttUnsubscribe(this.configTopic)
	},
	subscribeRefresh() {
		for (let segment = 1; segment < 17; segment++) {
			mqttSubscribe(this.refreshTopicPrefix + segment)
		}
	},
	unsubscribeRefresh() {
		for (let segment = 1; segment < 17; segment++) {
			mqttUnsubscribe(this.refreshTopicPrefix + segment)
		}
	},
	subscribeUpdates() {
		mqttSubscribe(this.updateTopic)
	},
	unsubscribeUpdates() {
		mqttUnsubscribe(this.updateTopic)
	},
})
export const dayGraph = reactive({
	topic: 'openWB/log/daily/#',
	date: new Date(),
	activate() {
		if (graphData.graphMode == 'day' || graphData.graphMode == 'today') {
			if (graphData.graphMode == 'today') {
				this.date = new Date()
			}
			const dateString =
				this.date.getFullYear().toString() +
				(this.date.getMonth() + 1).toString().padStart(2, '0') +
				this.date.getDate().toString().padStart(2, '0')
			mqttSubscribe(this.topic)
			sendCommand('getDailyLog',{ day: dateString })
			
			// graphData.data = []
		}
	},
	deactivate() {
		mqttUnsubscribe(this.topic)
	},
	back() {
		this.date = new Date(this.date.setTime(this.date.getTime() - 86400000))
	},
	forward() {
		this.date = new Date(this.date.setTime(this.date.getTime() + 86400000))
	},
	setDate(newDate: Date) {
		this.date = newDate
	},
	getDate() {
		return this.date
	},
})
export const monthGraph = reactive({
	topic: 'openWB/log/monthly/#',
	month: new Date().getMonth() + 1,
	year: new Date().getFullYear(),
	activate() {
		const dateString =
			this.year.toString() + this.month.toString().padStart(2, '0')
		graphData.data = []
		mqttSubscribe(this.topic)
		sendCommand('getMonthlyLog',{ month: dateString })
	},
	deactivate() {
		mqttUnsubscribe(this.topic)
	},
	back() {
		this.month -= 1
		if (this.month < 1) {
			this.month = 12
			this.year -= 1
		}
		this.activate()
	},
	forward() {
		const now = new Date()
		if (now.getFullYear() == this.year) {
			if (this.month - 1 < now.getMonth()) {
				this.month = this.month + 1
			}
		} else {
			this.month = this.month + 1
			if (this.month > 12) {
				this.month = 1
				this.year += 1
			}
		}
		this.activate()
	},
	getDate() {
		return new Date(this.year, this.month)
	},
})
export const yearGraph = reactive({
	topic: 'openWB/log/yearly/#',
	month: new Date().getMonth() + 1,
	year: new Date().getFullYear(),
	activate() {
		const dateString = this.year.toString()
		graphData.data = []
		mqttSubscribe(this.topic)
		sendCommand('getYearlyLog', { year: dateString })
	},
	deactivate() {
		mqttUnsubscribe(this.topic)
	},
	back() {
		this.year -= 1
		this.activate()
	},
	forward() {
		if (this.year < new Date().getFullYear()) {
			this.year = this.year + 1
			this.activate()
		}
	},
	getDate() {
		return new Date(this.year, this.month)
	},
})
export function initGraph(reloadOnly = false) {
	if (graphData.graphMode == '') {
		setGraphMode(globalConfig.graphPreference)
	} else if (graphData.graphMode == 'live') {
		globalConfig.graphPreference = 'live'
	} else {
		globalConfig.graphPreference = 'today'
	}
	if (!reloadOnly) {
		animateSourceGraph = true
		animateUsageGraph = true
	}
	switch (graphData.graphMode) {
		case 'live':
			dayGraph.deactivate()
			monthGraph.deactivate()
			yearGraph.deactivate()
			liveGraph.activate()
			break
		case 'today':
			liveGraph.deactivate()
			monthGraph.deactivate()
			yearGraph.deactivate()
			dayGraph.activate()
			break
		case 'day':
			liveGraph.deactivate()
			monthGraph.deactivate()
			yearGraph.deactivate()
			dayGraph.activate()
			break
		case 'month':
			liveGraph.deactivate()
			dayGraph.deactivate()
			yearGraph.deactivate()
			monthGraph.activate()
			break
		case 'year':
			liveGraph.deactivate()
			dayGraph.deactivate()
			monthGraph.deactivate()
			yearGraph.activate()
			break
	}
}
export function setGraphMode(mode: string) {
	graphData.graphMode = mode
}
export function calculateAutarchy(cat: string, values: GraphDataItem) {
	if (values[cat] > 0) {
		historicSummary.items[cat].energyPv +=
			((1000 / 12) * (values[cat] * (values.pv - values.evuOut))) /
			(values.pv - values.evuOut + values.evuIn + values.batOut)
		historicSummary.items[cat].energyBat +=
			((1000 / 12) * (values[cat] * values.batOut)) /
			(values.pv - values.evuOut + values.evuIn + values.batOut)
	}
}
export function calculateMonthlyAutarchy(cat: string, values: GraphDataItem) {
	if (values[cat] > 0) {
		historicSummary.items[cat].energyPv +=
			(1000 * (values[cat] * (values.pv - values.evuOut))) /
			(values.pv - values.evuOut + values.evuIn + values.batOut)
		historicSummary.items[cat].energyBat +=
			(1000 * (values[cat] * values.batOut)) /
			(values.pv - values.evuOut + values.evuIn + values.batOut)
	}
}
const nonPvCategories = ['evuIn', 'pv', 'batIn', 'evuOut']
export const noData = ref(false)

export function updateEnergyValues(
	totals: RawDayGraphDataItem,
	gridCounters: string[],
) {
	if (Object.entries(totals).length > 0) {
		noData.value = false
		Object.entries(totals.counter).forEach(([id, values]) => {
			if (gridCounters.length == 0 || gridCounters.includes(id)) {
				historicSummary.items.evuIn.energy += values.energy_imported
				historicSummary.items.evuOut.energy += values.energy_exported
			}
		})
		historicSummary.items.pv.energy = totals.pv.all.energy_exported
		if (totals.bat.all) {
			historicSummary.items.batIn.energy = totals.bat.all.energy_imported
			historicSummary.items.batOut.energy = totals.bat.all.energy_exported
		}
		Object.entries(totals.cp).forEach(([id, values]) => {
			if (id == 'all') {
				historicSummary.setEnergy('charging', values.energy_imported)
			} else {
				historicSummary.setEnergy(id, values.energy_imported)
			}
		})
		historicSummary.setEnergy('devices', 0)
		Object.entries(totals.sh).forEach(([id, values]) => {
			historicSummary.setEnergy(id, values.energy_imported)
			const idNumber = id.substring(2)
			if (!shDevices.get(+idNumber)!.countAsHouse) {
				historicSummary.items.devices.energy += values.energy_imported
			}
		})
		if (totals.hc && totals.hc.all) {
			historicSummary.setEnergy('house', totals.hc.all.energy_imported)
		} else {
			historicSummary.calculateHouseEnergy()
		}
		historicSummary.keys().map((cat) => {
			if (!nonPvCategories.includes(cat)) {
				historicSummary.setPvPercentage(
					cat,
					Math.round(
						((historicSummary.items[cat].energyPv +
							historicSummary.items[cat].energyBat) /
							historicSummary.items[cat].energy) *
							100,
					),
				)
				if (consumerCategories.includes(cat)) {
					usageSummary[cat].energy = historicSummary.items[cat].energy
					usageSummary[cat].energyPv = historicSummary.items[cat].energyPv
					usageSummary[cat].energyBat = historicSummary.items[cat].energyBat
					usageSummary[cat].pvPercentage =
						historicSummary.items[cat].pvPercentage
				}
			}
		})
		if (graphData.graphMode == 'today') {
			Object.values(chargePoints).map((cp) => {
				const hcp = historicSummary.items['cp' + cp.id]
				if (hcp) {
					cp.energyPv = hcp.energyPv
					cp.energyBat = hcp.energyBat
					cp.pvPercentage = hcp.pvPercentage
				}
			})
			shDevices.forEach((device) => {
				const hDevice = historicSummary.items['sh' + device.id]
				if (hDevice) {
					device.energy = hDevice.energy
					device.energyPv = hDevice.energyPv
					device.energyBat = hDevice.energyBat
					device.pvPercentage = hDevice.pvPercentage
				}
			})
		}
	} else {
		noData.value = true
	}
	energyMeterNeedsRedraw.value = true
}
function resetPvValues() {
	historicSummary.keys().map((cat) => {
		if (consumerCategories.includes(cat)) {
			usageSummary[cat].energy = historicSummary.items[cat].energy
			usageSummary[cat].energyPv = 0
			usageSummary[cat].energyBat = 0
			usageSummary[cat].pvPercentage = 0
		}
	})
	Object.values(chargePoints).map((cp) => {
		cp.energyPv = 0
		cp.energyBat = 0
		cp.pvPercentage = 0
	})
	shDevices.forEach((device) => {
		device.energyPv = 0
		device.energyBat = 0
		device.pvPercentage = 0
	})
}

export const xScaleMonth = computed(() => {
	const e = extent(graphData.data, (d) => d.date)
	if (e[1]) {
		return scaleBand<number>()
			.domain(Array.from({ length: e[1] }, (v, k) => k + 1))
			.paddingInner(0.4)
			.range([0, width - margin.left - 2])
	} else {
		return scaleBand<number>().range([0, 0])
	}
})
export function shiftLeft() {
	switch (graphData.graphMode) {
		case 'live':
			graphData.graphMode = 'today'
			globalConfig.showRightButton = true
			initGraph()
			break
		case 'today':
			graphData.graphMode = 'day'
			dayGraph.date = new Date()
			dayGraph.back()
			initGraph()
			break
		case 'day':
			dayGraph.back()
			initGraph()
			break
		case 'month':
			monthGraph.back()
			break
		case 'year':
			yearGraph.back()
			break
		default:
			break
	}
}
export function shiftRight() {
	const now = new Date()
	switch (graphData.graphMode) {
		case 'live':
			break
		case 'today':
			graphData.graphMode = 'live'
			globalConfig.showRightButton = false
			initGraph()
			break
		case 'day':
			dayGraph.forward()
			if (
				dayGraph.date.getDate() == now.getDate() &&
				dayGraph.date.getMonth() == now.getMonth() &&
				dayGraph.date.getFullYear() == now.getFullYear()
			) {
				graphData.graphMode = 'today'
			}
			initGraph()
			break
		case 'month':
			monthGraph.forward()
			break
		case 'year':
			yearGraph.forward()
			break
		default:
			break
	}
}
export function shiftUp() {
	switch (graphData.graphMode) {
		case 'live':
			shiftLeft()
			break
		case 'day':
		case 'today':
			graphData.graphMode = 'month'
			initGraph()
			break
		case 'month':
			graphData.graphMode = 'year'
			initGraph()
			break
		default:
			break
	}
}
export function shiftDown() {
	switch (graphData.graphMode) {
		case 'year':
			graphData.graphMode = 'month'
			initGraph()
			break
		case 'month':
			graphData.graphMode = 'today'
			initGraph()
			break
		case 'today':
		case 'day':
			graphData.graphMode = 'live'
			initGraph()
			break
		default:
			break
	}
}
export function setGraphDate(newDate: Date) {
	if (graphData.graphMode == 'day' || graphData.graphMode == 'today') {
		dayGraph.setDate(newDate)
		const now = new Date()
		if (
			dayGraph.date.getDate() == now.getDate() &&
			dayGraph.date.getMonth() == now.getMonth() &&
			dayGraph.date.getFullYear() == now.getFullYear()
		) {
			graphData.graphMode = 'today'
		} else {
			graphData.graphMode = 'day'
		}
		initGraph()
	}
}

export function toggleMonthlyView() {
	switch (graphData.graphMode) {
		case 'month':
			graphData.graphMode = 'today'
			initGraph()
			break
		default:
			graphData.graphMode = 'month'
			initGraph()
			break
	}
}

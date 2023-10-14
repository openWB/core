import { reactive } from 'vue'
import { mqttSubscribe, mqttUnsubscribe } from '../../assets/js/mqttClient'
import { sendCommand } from '@/assets/js/sendMessages'
import { globalConfig, setInitializeEnergyGraph } from '@/assets/js/themeConfig'
import { historicSummary } from '@/assets/js/model'

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
	pv: object
	bat: object
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
			graphData.data = []
			mqttSubscribe(this.topic)
			sendCommand({
				command: 'getDailyLog',
				data: { day: dateString },
			})
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
		sendCommand({
			command: 'getMonthlyLog',
			data: { month: dateString },
		})
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
		if (this.month - 1 < new Date().getMonth()) {
			this.month = this.month + 1
			if (this.month > 12) {
				this.month = 1
				this.year += 1
			}
			this.activate()
		}
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
		sendCommand({
			command: 'getYearlyLog',
			data: { year: dateString },
		})
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
		if (this.month - 1 < new Date().getMonth()) {
			this.month = this.month + 1
			if (this.month > 12) {
				this.month = 1
				this.year += 1
			}
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
	setInitializeEnergyGraph(true)
}
export function setGraphMode(mode: string) {
	graphData.graphMode = mode
}
export function calculateAutarchy(cat: string, values: GraphDataItem) {
	values[cat + 'Pv'] =
		1000 * (values[cat] * (values.solarPower - values.gridPush)) /
		(values.solarPower - values.gridPush + values.gridPull + values.batOut)
	values[cat + 'Bat'] =
		1000 * (values[cat] * values.batOut) /
		(values.solarPower - values.gridPush + values.gridPull + values.batOut)
}
export function updateEnergyValues(powerValues: { [key: string]: number }) {
	historicSummary.pv.energy = powerValues.solarPower * 1000
	historicSummary.evuIn.energy = powerValues.gridPull * 1000
	historicSummary.batOut.energy = powerValues.batOut * 1000
	historicSummary.evuOut.energy = powerValues.gridPush * 1000
	historicSummary.batIn.energy = powerValues.batIn * 1000
	historicSummary.charging.energy = powerValues.charging * 1000
	historicSummary.devices.energy = powerValues.devices * 1000

	historicSummary.house.energy =
		historicSummary.evuIn.energy +
		historicSummary.pv.energy +
		historicSummary.batOut.energy -
		historicSummary.evuOut.energy -
		historicSummary.batIn.energy -
		historicSummary.charging.energy -
		historicSummary.devices.energy

	consumerCategories.map((cat) => {
		historicSummary[cat].pvPercentage = Math.round(
			((historicSummary[cat].energyPv + historicSummary[cat].energyBat) /
				historicSummary[cat].energy) *
			100,
		)
	})
}
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
			graphData.graphMode = 'day'
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

import { computed, reactive, ref } from 'vue'
import { extent, scaleBand, scaleTime, scaleUtc, zoomIdentity } from 'd3'
import { mqttSubscribe, mqttUnsubscribe } from '../../assets/js/mqttClient'
import { sendCommand } from '@/assets/js/sendMessages'
import { globalConfig } from '@/assets/js/themeConfig'
import { energyMeterNeedsRedraw, registry } from '@/assets/js/model'
import { shDevices } from '../smartHome/model'
import { counters } from '../counterList/model'

export const width = 500
export const height = 500
export const margin = { top: 15, right: 20, bottom: 10, left: 25 }

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
			energy_imported_pv: number
			energy_imported_bat: number
			imported: number
		}
	}
	bat: {
		all: {
			power_imported: number
			power_exported: number
			energy_imported: number
			energy_imported_pv: number
			energy_imported_bat: number
			energy_exported: number
			imported: number
			exported: number
			soc: number
		}
	}
	cp: object
	ev: object
	sh: object
	prices: {
		grid: number
		pv: number
		bat: number
		cp: number
	}
}

export class GraphData {
	data: GraphDataItem[] = []
	private _graphMode = ''
	waitForData = true

	get graphMode() {
		return this._graphMode
	}
	set graphMode(mode: string) {
		this._graphMode = mode
	}
	get usePastData() {
		return this.graphMode != 'live' && this.graphMode != 'today'
	}
	get graphScope() {
		return this.usePastData ? 'past' : 'now'
	}
}

export const graphData = reactive(new GraphData())
export const mytransform = ref(zoomIdentity)
export const zoomedRange = computed(() =>
	[0, width - margin.left - 2 * margin.right].map((d) =>
		mytransform.value.applyX(d),
	),
)
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
	if (graphData.graphMode == 'live' && d.length > 0) {
		const windowStart =
			new Date().getTime() - globalConfig.liveGraphDuration * 1000
		graphData.data = d.filter((e) => e.date > windowStart)
		graphData.waitForData = false
	} else {
		graphData.data = d
		graphData.waitForData = false
	}
}
// LIVE GRAPH
export const liveGraph = reactive({
	refreshTopicPrefix: 'openWB/graph/' + 'alllivevaluesJson',
	updateTopic: 'openWB/graph/lastlivevaluesJson',
	configTopic: 'openWB/graph/config/#',
	initialized: false,
	initCounter: 0,
	graphRefreshCounter: 0,
	rawDataPacks: [] as RawGraphDataItem[][],
	duration: 0,

	activate(erase?: boolean) {
		// graphData.data = []
		this.unsubscribeUpdates()
		this.subscribeRefresh()
		if (erase) {
			graphData.data = []
		}
		graphData.waitForData = true
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
// DAY GRAPH
export const dayGraph = reactive({
	topic: 'openWB/log/daily/#',
	date: new Date(),
	activate(erase?: boolean) {
		if (graphData.graphMode == 'day' || graphData.graphMode == 'today') {
			if (graphData.graphMode == 'today') {
				this.date = new Date()
			}
			const dateString =
				this.date.getFullYear().toString() +
				(this.date.getMonth() + 1).toString().padStart(2, '0') +
				this.date.getDate().toString().padStart(2, '0')

			this.topic = 'openWB/log/daily/' + dateString
			mqttSubscribe(this.topic)
			if (erase) {
				graphData.data = []
			}
			graphData.waitForData = true
			sendCommand({
				command: 'getDailyLog',
				data: { date: dateString },
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
// MONTH GRAPH
export const monthGraph = reactive({
	topic: 'openWB/log/monthly/#',
	month: new Date().getMonth() + 1,
	year: new Date().getFullYear(),
	activate(erase?: boolean) {
		const dateString =
			this.year.toString() + this.month.toString().padStart(2, '0')
		graphData.data = []
		mqttSubscribe(this.topic)
		if (erase) {
			graphData.data = []
		}
		graphData.waitForData = true
		sendCommand({
			command: 'getMonthlyLog',
			data: { date: dateString },
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
// YEAR GRAPH
export const yearGraph = reactive({
	topic: 'openWB/log/yearly/#',
	month: new Date().getMonth() + 1,
	year: new Date().getFullYear(),
	activate(erase?: boolean) {
		const dateString = this.year.toString()
		// graphData.data = []
		mqttSubscribe(this.topic)
		if (erase) {
			graphData.data = []
		}
		graphData.waitForData = true
		sendCommand({
			command: 'getYearlyLog',
			data: { date: dateString },
		})
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
// ----- initGraph -----
export function initGraph(reloadOnly: boolean = false) {
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
			liveGraph.activate(!reloadOnly)
			break
		case 'today':
			liveGraph.deactivate()
			monthGraph.deactivate()
			yearGraph.deactivate()
			dayGraph.activate(!reloadOnly)
			break
		case 'day':
			liveGraph.deactivate()
			monthGraph.deactivate()
			yearGraph.deactivate()
			dayGraph.activate(!reloadOnly)
			break
		case 'month':
			liveGraph.deactivate()
			dayGraph.deactivate()
			yearGraph.deactivate()
			monthGraph.activate(!reloadOnly)
			break
		case 'year':
			liveGraph.deactivate()
			dayGraph.deactivate()
			monthGraph.deactivate()
			yearGraph.activate(!reloadOnly)
			break
	}
}
export function setGraphMode(mode: string) {
	graphData.graphMode = mode
}
export const noData = ref(false)

export function updateEnergyValues(
	totals: RawDayGraphDataItem,
	gridCounters: string[],
) {
	if (Object.entries(totals).length == 0) {
		noData.value = true
	} else {
		noData.value = false
		Object.entries(totals.counter).forEach(([id, values]) => {
			if (gridCounters.length == 0 || gridCounters.includes(id)) {
				registry.setEnergy('evuIn', values.energy_imported)
				registry.setEnergy('evuOut', values.energy_exported)
			}
		})
		registry.setEnergy('pv', totals.pv.all.energy_exported)
		if (totals.bat.all) {
			registry.setEnergy('batIn', totals.bat.all.energy_imported)
			registry.setEnergy('batOut', totals.bat.all.energy_exported)
		}
		// Chargepoints
		Object.entries(totals.cp).forEach(([id, values]) => {
			if (id == 'all') {
				updatePvValues(values, 'charging')
			} else {
				updatePvValues(values, id)
			}
		})
		// Devices
		registry.setEnergy('devices', 0)
		let devicesPvEnergy = 0
		let devicesBatEnergy = 0

		Object.entries(totals.sh).forEach(([id, values]) => {
			registry.setEnergy(id, values.energy_imported)
			registry.calculatePvPercentage(id)
			if (!shDevices.get(id)!.countAsHouse) {
				registry.setEnergy(
					'devices',
					registry.getEnergy('devices') + values.energy_imported,
				)
				devicesPvEnergy += registry.getItem(id)![graphData.graphScope].energyPv
				devicesBatEnergy +=
					registry.getItem(id)![graphData.graphScope].energyBat
			}
		})
		registry.setEnergyPv('devices', devicesPvEnergy)
		registry.setEnergyBat('devices', devicesBatEnergy)
		registry.calculatePvPercentage('devices')

		// Counters
		registry.setEnergy('counters', 0)
		let counterEnergy = 0
		let counterPvEnergy = 0
		let counterBatEnergy = 0
		Object.entries(totals.counter).forEach(([id, values]) => {
			if (
				!values.grid &&
				counters.get(+id.slice(7)) &&
				counters.get(+id.slice(7))!.showInGraph
			) {
				updatePvValues(values, id)
				counterEnergy += values.energy_imported
				counterPvEnergy += values.energy_imported_pv
				counterBatEnergy += values.energy_imported_bat
			}
		})
		registry.setEnergy('counters', counterEnergy)
		registry.setEnergyPv('counters', counterPvEnergy)
		registry.setEnergyBat('counters', counterBatEnergy)
		registry.calculatePvPercentage('counters')

		// house
		registry.setEnergy('house', 0)
		if (totals.hc && totals.hc.all) {
			registry.setEnergy('house', totals.hc.all.energy_imported)
			if (totals.hc.all.energy_imported_pv != undefined) {
				registry.setEnergyPv('house', totals.hc.all.energy_imported_pv)
				registry.setEnergyBat('house', totals.hc.all.energy_imported_bat)
			}
		} else {
			registry.calculateHouseEnergy()
		}
	}
	energyMeterNeedsRedraw.value = true
}

export const xScale = computed(() => {
	const e = extent(graphData.data, (d) => new Date(d.date))
	if (e[0] && e[1]) {
		return scaleUtc<number>()
			.domain(e)
			.range([0, width - margin.left - 2 * margin.right])
	} else {
		return scaleTime().range([0, 0])
	}
})
function updatePvValues(values: GraphDataItem, id: string) {
	registry.setEnergy(id, values.energy_imported)
	registry.setEnergyPv(id, values.energy_imported_pv)
	registry.setEnergyBat(id, values.energy_imported_bat)
	registry.calculatePvPercentage(id)
}
function resetPvValues() {
	registry.items.forEach((item) => {
		//item.now.energy = item.past.energy
		item.now.energyPv = 0
		item.now.energyBat = 0
		item.now.pvPercentage = 0
	})
}

export const xScaleMonth = computed(() => {
	const e = extent(graphData.data, (d) => d.date)
	if (e[1]) {
		return scaleBand<number>()
			.domain(Array.from({ length: e[1] }, (v, k) => k + 1))
			.paddingInner(0.4)
			.range([0, width - margin.left - 20])
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
			dayGraph.deactivate()
			//dayGraph.date = new Date()
			dayGraph.back()
			dayGraph.activate()
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
export const itemNames = ref(new Map<string, string>())

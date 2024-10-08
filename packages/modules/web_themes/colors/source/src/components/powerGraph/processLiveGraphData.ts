import { globalData } from '../../assets/js/model'
import { chargePoints } from '../chargePointList/model'
import {
	type GraphDataItem,
	type RawGraphDataItem,
	graphData,
	setGraphData,
	liveGraph,
} from './model'

// methods:
export function processLiveGraphMessages(topic: string, message: string) {
	if (topic == 'openWB/graph/boolDisplayLiveGraph') {
		globalData.displayLiveGraph = +message == 1
	} else if (topic.match(/^openwb\/graph\/alllivevaluesJson[1-9][0-9]*$/i)) {
		reloadLiveGraph(topic, message)
	} else if (topic == 'openWB/graph/lastlivevaluesJson') {
		updateLiveGraph(topic, message)
	} else if (topic == 'openWB/graph/config/duration') {
		liveGraph.duration = JSON.parse(message)
	} else {
		//console.warn('Ignored GRAPH message: [' + topic + '](' + message + ')')
	}
}
// initial/refresh delivery of all graph data
export function reloadLiveGraph(topic: string, rawMessage: string) {
	if (!liveGraph.initialized) {
		let graphRecords: RawGraphDataItem[] = []
		const stringTable = rawMessage.toString().split('\n')
		if (stringTable.length > 1) {
			graphRecords = stringTable.map(
				(recordString) => JSON.parse(recordString) as RawGraphDataItem,
			)
		} else {
			graphRecords = []
		}
		const numbersFound = topic.match(/(\d+)$/g)
		const serialNo = numbersFound ? numbersFound[0] : ''
		if (serialNo != '') {
			if (typeof liveGraph.rawDataPacks[+serialNo - 1] === 'undefined') {
				liveGraph.rawDataPacks[+serialNo - 1] = graphRecords
				liveGraph.initCounter++
			}
		}
	}
	if (liveGraph.initCounter == 16) {
		// Initialization complete
		const newGraphData: GraphDataItem[] = []
		liveGraph.unsubscribeRefresh()
		liveGraph.initialized = true
		liveGraph.rawDataPacks.forEach((dataPack) => {
			dataPack.forEach((rawItem) => {
				const values = extractValues(rawItem)
				newGraphData.push(values)
			})
		})
		setGraphData(newGraphData)
		liveGraph.subscribeUpdates()
	}
}
// incremental update message for the live graph
export function updateLiveGraph(topic: string, rawString: string) {
	const rawItem = JSON.parse(rawString) as RawGraphDataItem
	const values = extractValues(rawItem)
	liveGraph.graphRefreshCounter++
	setGraphData(graphData.data.concat(values))
	if (liveGraph.graphRefreshCounter > 60) {
		liveGraph.activate()
	}
}
function extractValues(data: RawGraphDataItem): GraphDataItem {
	const car1 =
		Object.values(chargePoints).length > 0
			? Object.values(chargePoints)[0].connectedVehicle
			: 0
	const car2 =
		Object.values(chargePoints).length > 1
			? Object.values(chargePoints)[1].connectedVehicle
			: 1
	const car1id = 'ev' + car1 + '-soc'
	const car2id = 'ev' + car2 + '-soc'
	const values: GraphDataItem = {}
	values.date = +data.timestamp * 1000
	if (+data.grid > 0) {
		values.evuIn = +data.grid
		values.evuOut = 0
	} else if (+data.grid <= 0) {
		values.evuIn = 0
		values.evuOut = -data.grid
	} else {
		values.evuIn = 0
		values.evuOut = 0
	}
	if (+data['pv-all'] >= 0) {
		values.pv = +data['pv-all']
		values.inverter = 0
	} else {
		values.pv = 0
		values.inverter = -data['pv-all']
	}
	values.house = +data['house-power']
	//battery
	if (+data['bat-all-power'] > 0) {
		values.batOut = 0
		values.batIn = +data['bat-all-power']
	} else if (+data['bat-all-power'] < 0) {
		values.batOut = -data['bat-all-power']
		values.batIn = 0
	} else {
		values.batOut = 0
		values.batIn = 0
	}
	if (data['bat-all-soc']) {
		values.batSoc = +data['bat-all-soc']
	} else {
		values.batSoc = 0
	}
	if (data[car1id]) {
		values['soc' + car1] = +data[car1id]
	}
	if (data[car2id]) {
		values['soc' + car2] = +data[car2id]
	}

	values.charging = +data['charging-all']
	// charge points - we only show a maximum of 10 chargepoints in the graph
	for (let i = 0; i < 10; i++) {
		const idx = 'cp' + i
		values[idx] = +(data[idx + '-power'] ?? 0)
	}
	values.selfUsage = values.pv - values.evuOut
	if (values.selfUsage < 0) {
		values.selfUsage = 0
	}
	values.devices = 0
	return values
}

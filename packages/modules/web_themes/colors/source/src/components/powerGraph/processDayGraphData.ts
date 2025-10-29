import {
	graphData,
	type GraphDataItem,
	type RawDayGraphDataItem,
	setGraphData,
	dayGraph,
	updateEnergyValues,
} from './model'

import { registry, resetHistoricData } from '@/assets/js/model'
import { globalConfig } from '@/assets/js/themeConfig'
import { shDevices } from '../smartHome/model'
import { itemNames } from './model'
import { counters } from '../counterList/model'
import { chargePoints } from '../chargePointList/model'
// methods:
/* const noAutarchyCalculation = [
	'evuIn',
	'pv',
	'batOut',
	'evuOut',
	'charging',
	'house',
] */
let gridCounters: string[] = []
// Process incoming day graph data
export function processDayGraphMessages(topic: string, message: string) {
	const {
		entries: inputTable,
		names: itemNames2,
		totals: energyValues,
	} = JSON.parse(message)
	itemNames.value = new Map(Object.entries(itemNames2))
	resetHistoricData()
	gridCounters = []
	registry.keys().forEach((cat) => {
		//consumerCategories.forEach((cat) => {
		registry.setEnergyPv(cat, 0)
		registry.setEnergyBat(cat, 0)
	})
	const transformedTable = transformDatatable(inputTable)
	setGraphData(transformedTable)
	updateEnergyValues(energyValues, gridCounters)
	if (globalConfig.debug) {
		printDebugOutput(inputTable, energyValues, transformedTable)
	}
	if (graphData.graphMode == 'today') {
		setTimeout(() => dayGraph.activate(), 300000)
	}
}
// Transform the incoming data to the format used in the graph
function transformDatatable(
	inputTable: RawDayGraphDataItem[],
): GraphDataItem[] {
	const outputTable: GraphDataItem[] = []
	let transformedRow: GraphDataItem = {}

	inputTable.forEach((inputRow) => {
		transformedRow = transformRow(inputRow)
		const values = transformedRow
		outputTable.push(values)
	})
	return outputTable
}
// Transform a single row of the incoming data to the format used in the graph
function transformRow(currentRow: RawDayGraphDataItem): GraphDataItem {
	const currentItem: GraphDataItem = {}
	currentItem.date = currentRow.timestamp * 1000
	currentItem.evuOut = 0
	currentItem.evuIn = 0
	Object.entries(currentRow.counter).forEach(([id, values]) => {
		if (values.grid) {
			currentItem.evuOut += values.power_exported
			currentItem.evuIn += values.power_imported
			if (!gridCounters.includes(id)) {
				gridCounters.push(id)
			}
		}
	})
	if (currentItem.evuOut == 0 && currentItem.evuIn == 0) {
		// legacy mode
		Object.entries(currentRow.counter).forEach((item) => {
			currentItem.evuOut += item[1].power_exported
			currentItem.evuIn += item[1].power_imported
		})
	}
	Object.entries(currentRow.pv).forEach(([id, values]) => {
		if (id != 'all') {
			currentItem[id] = values.power_exported
		} else currentItem.pv = values.power_exported
	})

	if (Object.entries(currentRow.bat).length > 0) {
		currentItem.batIn = currentRow.bat.all.power_imported
		currentItem.batOut = currentRow.bat.all.power_exported
		currentItem.batSoc = currentRow.bat.all.soc ?? 0
	} else {
		currentItem.batIn = 0
		currentItem.batOut = 0
		currentItem.batSoc = 0
	}

	Object.entries(currentRow.cp).forEach(([id, values]) => {
		if (id != 'all') {
			currentItem[id] = values.power_imported
			if (!registry.keys().includes(id)) {
				registry.duplicateItem(id, chargePoints[+id.slice(2)])
			}
		} else {
			currentItem['charging'] = values.power_imported
		}
	})
	Object.entries(currentRow.ev).forEach(([id, values]) => {
		if (id != 'all') {
			currentItem['soc' + id.substring(2)] = values.soc
		}
	})

	// Smart Home Devices
	currentItem.devices = 0
	let shEnergyToBeExtractedFromHouse = 0
	const pvFactor =
		((1000 / 12) * (currentItem.pv - currentItem.evuOut)) /
		(currentItem.pv -
			currentItem.evuOut +
			currentItem.evuIn +
			currentItem.batOut)
	Object.entries(currentRow.sh).forEach(([id, values]) => {
		if (id != 'all') {
			currentItem[id] = values.power_imported ?? 0
			if (!registry.keys().includes(id)) {
				registry.duplicateItem(id, shDevices.get(id)!)
			}
			if (shDevices.get(id)?.countAsHouse) {
				shEnergyToBeExtractedFromHouse += values.power_imported
			} else {
				currentItem.devices += values.power_imported ?? 0
			}
		}
		// Autarchy PV / Battery calculation
		if (values.power_imported > 0) {
			registry.items.get(id)![graphData.graphScope].energyPv +=
				values.power_imported * pvFactor
			registry.items.get(id)![graphData.graphScope].energyBat +=
				((1000 / 12) * (values.power_imported * currentItem.batOut)) /
				(currentItem.pv -
					currentItem.evuOut +
					currentItem.evuIn +
					currentItem.batOut)
		}
	})

	// Counters
	currentItem.counters = 0
	Object.entries(currentRow.counter).forEach(([id, values]) => {
		if (!values.grid) {
		currentItem[id] = values.power_imported ?? 0
			if (!registry.keys().includes(id)) {
				registry.duplicateItem(id, counters.get(+id.slice(7))!)
				//registry.items.get(id)!.showInGraph = true
			}
			if (registry.items.get(id)!.showInGraph) {
				currentItem.counters += values.power_imported ?? 0
			}
		}
	})
	// Self Usage
	currentItem.selfUsage = Math.max(0, currentItem.pv - currentItem.evuOut)
	// House
	if (currentRow.hc && currentRow.hc.all) {
		currentItem.house =
			currentRow.hc.all.power_imported - shEnergyToBeExtractedFromHouse
	} else {
		currentItem.house =
			currentItem.evuIn +
			currentItem.batOut +
			currentItem.pv -
			currentItem.evuOut -
			currentItem.charging -
			currentItem.devices -
			currentItem.counters -
			currentItem.batOut
	}
	return currentItem
}

function printDebugOutput(
	inputTable: RawDayGraphDataItem[],
	energyValues: RawDayGraphDataItem,
	transformedTable: GraphDataItem[],
) {
	console.debug('---------------------------------------- Graph Data -')
	console.debug(['--- Incoming graph data:', inputTable])
	console.debug(['--- Incoming energy data:', energyValues])
	console.debug(['--- Data to be displayed:', transformedTable])
	console.debug('-----------------------------------------------------')
}

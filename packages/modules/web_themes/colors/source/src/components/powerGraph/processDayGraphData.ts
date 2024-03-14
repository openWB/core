import { timeParse } from 'd3'
import {
	graphData,
	type GraphDataItem,
	type RawDayGraphDataItem,
	setGraphData,
	dayGraph,
	calculateAutarchy,
	consumerCategories,
	updateEnergyValues,
} from './model'
import { historicSummary, resetHistoricSummary } from '@/assets/js/model'
import { globalConfig } from '@/assets/js/themeConfig'
// methods:

const nonPvCategories = ['evuIn', 'pv', 'batIn', 'evuOut']
let gridCounters: string[] = []

export function processDayGraphMessages(_: string, message: string) {
	const inputTable: RawDayGraphDataItem[] = JSON.parse(message).entries
	const energyValues: RawDayGraphDataItem = JSON.parse(message).totals
	resetHistoricSummary()
	gridCounters = []
	consumerCategories.map((cat) => {
		historicSummary.setEnergyPv(cat, 0)
		historicSummary.setEnergyBat(cat, 0)
	})
	const transformedTable = transformDatatable(inputTable)
	setGraphData(transformedTable)
	updateEnergyValues(energyValues, gridCounters)
	if (globalConfig.debug) {
		console.debug(
			'---------------------------------------- Graph Data ---------------------------',
		)
		console.debug('--- Incoming graph data:')
		console.debug(inputTable)
		console.debug('data to be displayed:')
		console.debug(transformedTable)
		console.debug(
			'-------------------------------------------------------------------------------',
		)
	}

	if (graphData.graphMode == 'today') {
		setTimeout(() => dayGraph.activate(), 300000)
	}
}

function transformDatatable(
	inputTable: RawDayGraphDataItem[],
): GraphDataItem[] {
	const outputTable: GraphDataItem[] = []
	let transformedRow: GraphDataItem = {}

	inputTable.map((inputRow) => {
		transformedRow = transformRow(inputRow)
		const values = transformedRow
		outputTable.push(values)
	})
	return outputTable
}

function transformRow(currentRow: RawDayGraphDataItem): GraphDataItem {
	const currentItem: GraphDataItem = {}
	if (graphData.graphMode == 'day' || graphData.graphMode == 'today') {
		if (typeof currentRow.date == 'number') {
			currentItem.date = new Date(+currentRow.date * 1000).getTime()
		} else {
			const d = timeParse('%H:%M')(currentRow.date)
			if (d) {
				d.setMonth(dayGraph.date.getMonth())
				d.setDate(dayGraph.date.getDate())
				d.setFullYear(dayGraph.date.getFullYear())
				currentItem.date = d.getTime()
			}
		}
	} else {
		if (typeof currentRow.date == 'string') {
			const d = timeParse('%Y%m%d')(currentRow.date)
			if (d) {
				currentItem.date = d.getDate()
			}
		}
	}
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
	currentItem.pv = currentRow.pv.all.power_exported
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
			if (!historicSummary.keys().includes(id)) {
				historicSummary.addItem(id)
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
	// Devices
	currentItem.devices = 0
	Object.entries(currentRow.sh).forEach(([id, values]) => {
		if (id != 'all') {
			currentItem[id] = values.power_imported ?? 0
			currentItem.devices += values.power_imported ?? 0
			if (!historicSummary.keys().includes(id)) {
				historicSummary.addItem(id)
			}
		}
	})
	// Self Usage
	currentItem.selfUsage = currentItem.pv - currentItem.evuOut
	// House
	if (currentRow.hc && currentRow.hc.all) {
		currentItem.house = currentRow.hc.all.power_imported
	} else {
		currentItem.house =
			currentItem.evuIn +
			currentItem.batOut +
			currentItem.pv -
			currentItem.evuOut -
			currentItem.charging -
			currentItem.devices -
			currentItem.batOut
	}
	// Autarchy
	const usedEnergy = currentItem.evuIn + currentItem.batOut + currentItem.pv
	if (usedEnergy > 0) {
		historicSummary
			.keys()
			.filter((key) => !nonPvCategories.includes(key))
			.map((cat) => {
				calculateAutarchy(cat, currentItem)
			})
	} else {
		Object.keys(currentItem).map((cat) => {
			currentItem[cat + 'Pv'] = 0
			currentItem[cat + 'Bat'] = 0
		})
	}
	return currentItem
}

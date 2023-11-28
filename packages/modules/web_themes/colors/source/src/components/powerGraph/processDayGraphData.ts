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
		const d = timeParse('%H:%M')(currentRow.date)
		if (d) {
			d.setMonth(dayGraph.date.getMonth())
			d.setDate(dayGraph.date.getDate())
			d.setFullYear(dayGraph.date.getFullYear())
			currentItem.date = d.getTime()
		}
	} else {
		const d = timeParse('%Y%m%d')(currentRow.date)
		if (d) {
			currentItem.date = d.getDate()
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
			currentItem[id] = values.power_imported
			currentItem.devices += values.power_imported
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
/* function updateEnergyValues(totals: RawDayGraphDataItem) {
	console.log(totals)
	if (Object.entries(totals).length > 0) {
	Object.entries(totals.counter).forEach(([id, values]) => {
		if (gridCounters.length == 0 || gridCounters.includes(id)) {
			historicSummary.items.evuIn.energy += values.imported
			historicSummary.items.evuOut.energy += values.exported
		}
	})
	historicSummary.items.pv.energy = totals.pv.all.exported
	if (totals.bat.all) {
		historicSummary.items.batIn.energy = totals.bat.all.imported
		historicSummary.items.batOut.energy = totals.bat.all.exported
	}
	Object.entries(totals.cp).forEach(([id, values]) => {
		if (id == 'all') {
			historicSummary.setEnergy('charging', values.imported)
		} else {
			historicSummary.setEnergy(id, values.imported)
		}
	})
	historicSummary.setEnergy('devices', 0)
	Object.entries(totals.sh).forEach(([id, values]) => {
		historicSummary.setEnergy(id, values.imported)
		const idNumber = id.substring(2)
		if (!shDevices[+idNumber].countAsHouse) {
			historicSummary.items.devices.energy += values.imported
		}
	})
	if (totals.hc && totals.hc.all) {
		historicSummary.setEnergy('house', totals.hc.all.imported)
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
				if (graphData.graphMode != 'today') {
				usageSummary[cat].energy = historicSummary.items[cat].energy
				}
				usageSummary[cat].energyPv = historicSummary.items[cat].energyPv
				usageSummary[cat].energyBat = historicSummary.items[cat].energyBat
				usageSummary[cat].pvPercentage = historicSummary.items[cat].pvPercentage
			}
		}
	})
}
console.log(sourceSummary)
	energyMeterNeedsRedraw.value = true
} */

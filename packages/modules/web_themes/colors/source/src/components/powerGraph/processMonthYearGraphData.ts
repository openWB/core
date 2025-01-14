import { timeParse } from 'd3'
import {
	type GraphDataItem,
	type RawDayGraphDataItem,
	setGraphData,
	updateEnergyValues,
	graphData,
	calculateMonthlyAutarchy,
} from './model'
import { historicSummary, resetHistoricSummary } from '@/assets/js/model'
import { itemNames } from './model'

let columnValues: { [key: string]: number } = {}
const consumerCategories = ['charging', 'house', 'batIn', 'devices']
const nonPvCategories = [
	'evuIn',
	'pv',
	'batOut',
	'batIn',
	'evuOut',
	'devices',
	'sh1',
	'sh2',
	'sh3',
	'sh4',
	'sh5',
	'sh6',
	'sh7',
	'sh8',
	'sh9',
]
let gridCounters: string[] = []

// methods:
// Process a new message with monthly graph data. A single message contains all data
export function processMonthGraphMessages(topic: string, message: string) {
	//const inputTable: RawDayGraphDataItem[] = JSON.parse(message).entries
	//const energyValues: RawDayGraphDataItem = JSON.parse(message).totals
	const {
		entries: inputTable,
		names: itemNames2,
		totals: energyValues,
	} = JSON.parse(message)
	itemNames.value = new Map(Object.entries(itemNames2))
	resetHistoricSummary()
	gridCounters = []
	consumerCategories.forEach((cat) => {
		historicSummary.items[cat].energyPv = 0
		historicSummary.items[cat].energyBat = 0
	})
	if (inputTable.length > 0) {
		setGraphData(transformDatatable(inputTable))
	}
	updateEnergyValues(energyValues, gridCounters)

	// reloadMonthGraph(topic, message)
}
export function processYearGraphMessages(topic: string, message: string) {
	//const inputTable: RawDayGraphDataItem[] = JSON.parse(message).entries
	//const energyValues: RawDayGraphDataItem = JSON.parse(message).totals
	const {
		entries: inputTable,
		names: itemNames2,
		totals: energyValues,
	} = JSON.parse(message)
	itemNames.value = new Map(Object.entries(itemNames2))
	resetHistoricSummary()
	gridCounters = []
	consumerCategories.forEach((cat) => {
		historicSummary.items[cat].energyPv = 0
		historicSummary.items[cat].energyBat = 0
	})
	if (inputTable.length > 0) {
		setGraphData(transformDatatable(inputTable))
	}
	updateEnergyValues(energyValues, gridCounters)
}
// transform the incoming format into the format used by the graph
function transformDatatable(
	inputTable: RawDayGraphDataItem[],
): GraphDataItem[] {
	const outputTable: GraphDataItem[] = []
	let currentItem: GraphDataItem = {}
	columnValues = {}
	inputTable.forEach((inputRow) => {
		currentItem = transformRow(inputRow)
		outputTable.push(currentItem)
		Object.keys(currentItem).forEach((field) => {
			if (field != 'date') {
				if (currentItem[field] < 0) {
					console.warn(
						`Negative energy value for ${field} in row ${currentItem['date']}. Ignoring the value.`,
					)
					currentItem[field] = 0
				}
				if (columnValues[field]) {
					columnValues[field] += currentItem[field]
				} else {
					columnValues[field] = currentItem[field]
				}
			}
		})
	})
	return outputTable
}
function transformRow(inputRow: RawDayGraphDataItem): GraphDataItem {
	const outputRow: GraphDataItem = {}
	// date
	const d = timeParse('%Y%m%d')(inputRow.date as string)
	if (d) {
		outputRow.date =
			graphData.graphMode == 'month' ? d.getDate() : d.getMonth() + 1
	}
	// counters
	outputRow.evuOut = 0
	outputRow.evuIn = 0
	let evuOutTotal = 0
	let evuInTotal = 0
	Object.entries(inputRow.counter).forEach(([id, values]) => {
		evuOutTotal += values.energy_exported
		evuInTotal += values.energy_imported
		if (values.grid) {
			outputRow.evuOut += values.energy_exported
			outputRow.evuIn += values.energy_imported
			if (!gridCounters.includes(id)) {
				gridCounters.push(id)
			}
		}
	})
	if (gridCounters.length == 0) {
		outputRow.evuOut = evuOutTotal
		outputRow.evuIn = evuInTotal
	}
	// PV
	outputRow.pv = inputRow.pv.all.energy_exported

	// Battery
	if (Object.entries(inputRow.bat).length > 0) {
		if (inputRow.bat.all.energy_imported >= 0) {
			outputRow.batIn = inputRow.bat.all.energy_imported
		} else {
			console.warn('ignoring negative value for batIn on day ' + outputRow.date)
			outputRow.batIn = 0
		}
		if (inputRow.bat.all.energy_exported >= 0) {
			outputRow.batOut = inputRow.bat.all.energy_exported
		} else {
			console.warn(
				'ignoring negative value for batOut on day ' + outputRow.date,
			)
			outputRow.batOut = 0
		}
	} else {
		outputRow.batIn = 0
		outputRow.batOut = 0
	}
	// Charge points
	Object.entries(inputRow.cp).forEach(([id, values]) => {
		if (id != 'all') {
			if (!historicSummary.keys().includes(id)) {
				historicSummary.addItem(id)
			}
			outputRow[id] = values.energy_imported
		} else {
			outputRow['charging'] = values.energy_imported
		}
	})
	// Vehicles
	Object.entries(inputRow.ev).forEach(([id, values]) => {
		if (id != 'all') {
			outputRow['soc-' + id] = values.soc
		}
	})
	// Devices
	outputRow.devices = Object.entries(inputRow.sh).reduce<number>(
		(sum: number, item) => {
			if (!historicSummary.keys().includes(item[0])) {
				historicSummary.addItem(item[0])
			}
			if (item[1].energy_imported >= 0) {
				sum += item[1].energy_imported
			} else {
				console.warn(
					`Negative energy value for device ${item[0]} in row ${outputRow.date}. Ignoring this value`,
				)
			}
			return sum
		},
		0,
	)
	// House
	if (inputRow.hc && inputRow.hc.all) {
		outputRow.house = inputRow.hc.all.energy_imported // (seems this is now centrally computed) - currentItem.devices
	} else {
		outputRow.house =
			outputRow.pv +
			outputRow.evuIn +
			outputRow.batOut -
			outputRow.evuOut -
			outputRow.batIn -
			outputRow.charging
	}
	// Self usage
	outputRow.selfUsage = outputRow.pv - outputRow.evuOut
	// Autarchy
	const usedEnergy = outputRow.evuIn + outputRow.batOut + outputRow.pv
	if (usedEnergy > 0) {
		historicSummary
			.keys()
			.filter((key) => !nonPvCategories.includes(key))
			.forEach((cat) => {
				calculateMonthlyAutarchy(cat, outputRow)
			})
	} else {
		consumerCategories.map((cat) => {
			outputRow[cat + 'Pv'] = 0
			outputRow[cat + 'Bat'] = 0
		})
	}
	return outputRow
}

import { timeParse } from 'd3'
import {
	type GraphDataItem,
	type RawDayGraphDataItem,
	setGraphData,
	calculateAutarchy,
	updateEnergyValues,
} from './model'
import { historicSummary, resetHistoricSummary } from '@/assets/js/model'
let columnValues: { [key: string]: number } = {}
const consumerCategories = ['charging', 'house', 'batIn', 'devices']

// methods:
// Process a new message with monthly graph data. A single message contains all data
export function processMonthGraphMessages(topic: string, message: string) {
	const inputTable: RawDayGraphDataItem[] = JSON.parse(message).entries
	resetHistoricSummary()
	consumerCategories.map((cat) => {
		historicSummary.items[cat].energyPv = 0
		historicSummary.items[cat].energyBat = 0
	})
	setGraphData(transformDatatable(inputTable))
	updateEnergyValues(columnValues)
	// reloadMonthGraph(topic, message)
}
export function processYearGraphMessages(topic: string, message: string) {
	const inputTable: RawDayGraphDataItem[] = JSON.parse(message).entries
	resetHistoricSummary()
	consumerCategories.map((cat) => {
		historicSummary.items[cat].energyPv = 0
		historicSummary.items[cat].energyBat = 0
	})
	setGraphData(transformDatatable(inputTable))
	updateEnergyValues(columnValues)
	// reloadMonthGraph(topic, message)
}
// transform the incoming format into the format used by the graph
function transformDatatable(
	inputTable: RawDayGraphDataItem[],
): GraphDataItem[] {
	const outputTable: GraphDataItem[] = []
	let currentItem: GraphDataItem = {}
	columnValues = {}
	inputTable.map((inputRow) => {
		currentItem = transformRow(inputRow)
		outputTable.push(currentItem)
		consumerCategories.map((cat) => {
			historicSummary.items[cat].energyPv += currentItem[cat + 'Pv']
			historicSummary.items[cat].energyBat += currentItem[cat + 'Bat']
		})
		Object.keys(currentItem).map((field) => {
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
// initial/refresh delivery of all graph data
/* export function reloadMonthGraph(topic: string, rawMessage: string) {
	const graphRecords: RawDayGraphDataItem[] = JSON.parse(rawMessage).entries

	const newGraphData: GraphDataItem[] = []
	graphRecords.map((dayData) => {
		const values = transformRow(dayData)
		newGraphData.push(values)
	})
} */

function transformRow(inputRow: RawDayGraphDataItem): GraphDataItem {
	const outputRow: GraphDataItem = {}
	// date
	const d = timeParse('%Y%m%d')(inputRow.date)
	if (d) {
		outputRow.date = d.getDate()
	}
	// counters
	outputRow.evuOut = 0
	outputRow.evuIn = 0
	Object.entries(inputRow.counter).forEach((item) => {
		outputRow.evuOut += item[1].energy_exported
		outputRow.evuIn += item[1].energy_imported
	})
	// PV
	outputRow.pv = inputRow.pv.all.energy_exported

	// Battery
	if (Object.entries(inputRow.bat).length > 0) {
		if (inputRow.bat.all.energy_imported > 0) {
			outputRow.batIn = inputRow.bat.all.energy_imported
		} else {
			console.warn('ignoring negative value for batIn on day ' + outputRow.date)
			outputRow.batIn = 0
		}
		if (inputRow.bat.all.energy_exported > 0) {
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
	outputRow.house =
		outputRow.pv +
		outputRow.evuIn +
		outputRow.batOut -
		outputRow.evuOut -
		outputRow.batIn -
		outputRow.charging
	outputRow.selfUsage = outputRow.pv - outputRow.evuOut
	// outputRow.inverter = 0
	const usedEnergy = outputRow.evuIn + outputRow.batOut + outputRow.pv
	if (usedEnergy > 0) {
		consumerCategories.map((cat) => calculateAutarchy(cat, outputRow))
		// pvChargeCounter += (result.charging * result.pv / usedEnergy / 12 * 1000)
		// batChargeCounter += (result.charging * result.batOut / usedEnergy / 12 * 1000)
	} else {
		consumerCategories.map((cat) => {
			outputRow[cat + 'Pv'] = 0
			outputRow[cat + 'Bat'] = 0
		})
	}
	return outputRow
}

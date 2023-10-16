import { timeParse } from 'd3'
import {
	type GraphDataItem,
	type RawDayGraphDataItem,
	setGraphData,
	calculateAutarchy,
	updateEnergyValues,
} from './model'
import { historicSummary } from '@/assets/js/model'
let yearlyValues: { [key: string]: number } = {}
const consumerCategories = ['charging', 'house', 'batIn', 'devices']

// methods:
// Process a new message with yearly graph data. A single message contains all data
export function processYearGraphMessages(topic: string, message: string) {
	const inputTable: RawDayGraphDataItem[] = JSON.parse(message).entries
	consumerCategories.map((cat) => {
		historicSummary[cat].energyPv = 0
		historicSummary[cat].energyBat = 0
	})
	setGraphData(transformDatatable(inputTable))
	updateEnergyValues(yearlyValues)
	reloadMonthGraph(topic, message)
}
// transform the incoming format into the format used by the graph
function transformDatatable(
	inputTable: RawDayGraphDataItem[],
): GraphDataItem[] {
	const outputTable: GraphDataItem[] = []
	let currentItem: GraphDataItem = {}
	yearlyValues = {}
	inputTable.map((inputRow) => {
		currentItem = transformRow(inputRow)
		outputTable.push(currentItem)
		consumerCategories.map((cat) => {
			historicSummary[cat].energyPv += currentItem[cat + 'Pv']
			historicSummary[cat].energyBat += currentItem[cat + 'Bat']
		})
		Object.keys(currentItem).map((field) => {
			if (field != 'date') {
				if (currentItem[field] < 0) {
					console.warn(
						`Negative energy value for ${field} in row ${currentItem['date']}. Ignoring the value.`,
					)
					currentItem[field] = 0
				}
				if (yearlyValues[field]) {
					yearlyValues[field] += currentItem[field]
				} else {
					yearlyValues[field] = currentItem[field]
				}
			}
		})
	})
	return outputTable
}
// initial/refresh delivery of all graph data
export function reloadMonthGraph(topic: string, rawMessage: string) {
	const graphRecords: RawDayGraphDataItem[] = JSON.parse(rawMessage).entries

	const newGraphData: GraphDataItem[] = []
	graphRecords.map((dayData) => {
		const values = transformRow(dayData)
		newGraphData.push(values)
	})
}

function transformRow(inputRow: RawDayGraphDataItem): GraphDataItem {
	const outputRow: GraphDataItem = {}
	// date
	const d = timeParse('%Y%m%d')(inputRow.date)
	if (d) {
		outputRow.date = d.getMonth() + 1
	}
	// counters
	outputRow.gridPush = 0
	outputRow.grdPull = 0
	outputRow.gridPush = 0
	outputRow.gridPull = 0
	Object.entries(inputRow.counter).forEach((item) => {
		outputRow.gridPush += item[1].energy_exported / 1000
		outputRow.gridPull += item[1].energy_imported / 1000
	})
	// PV
	outputRow.solarPower = inputRow.pv.all.energy_exported / 1000
	// Battery
	if (Object.entries(inputRow.bat).length > 0) {
		outputRow.batIn = inputRow.bat.all.energy_imported / 1000
		outputRow.batOut = inputRow.bat.all.energy_exported / 1000
	} else {
		outputRow.batIn = 0
		outputRow.batOut = 0
	}
	// Charge points
	Object.entries(inputRow.cp).forEach(([id, values]) => {
		if (id != 'all') {
			outputRow[id] = values.energy_imported / 1000
			// outputRow['soc' + id] = values.soc
		} else {
			outputRow['charging'] = values.energy_imported / 1000
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
				sum += item[1].energy_imported / 1000
			} else {
				console.warn(
					`Negative energy value for device ${item[0]} in row ${outputRow.date}. Ignoring this value`,
				)
			}
			return sum
		},
		0,
	)
	outputRow.selfUsage = outputRow.solarPower - outputRow.gridPush
	// House

	outputRow.house =
		outputRow.solarPower +
		outputRow.gridPull +
		outputRow.batOut -
		outputRow.gridPush -
		outputRow.batIn -
		outputRow.charging

	outputRow.inverter = 0
	const usedEnergy =
		outputRow.gridPull + outputRow.batOut + outputRow.solarPower
	if (usedEnergy > 0) {
		consumerCategories.map((cat) => calculateAutarchy(cat, outputRow))
	} else {
		consumerCategories.map((cat) => {
			outputRow[cat + 'Pv'] = 0
			outputRow[cat + 'Bat'] = 0
		})
	}
	return outputRow
}

import { timeParse } from 'd3'
import {
	type GraphDataItem,
	type RawDayGraphDataItem,
	setGraphData,
	calculateAutarchy,
	updateEnergyValues,
} from './model'
import { historicSummary } from '@/assets/js/model'
let monthlyValues: { [key: string]: number } = {}
const consumerCategories = ['charging', 'house', 'batIn', 'devices']

// methods:
// Process a new message with monthly graph data. A single message contains all data
export function processMonthGraphMessages(topic: string, message: string) {
	const inputTable: RawDayGraphDataItem[] = JSON.parse(message).entries
	consumerCategories.map((cat) => {
		historicSummary[cat].energyPv = 0
		historicSummary[cat].energyBat = 0
	})
	setGraphData(transformDatatable(inputTable))
	updateEnergyValues(monthlyValues)
	reloadMonthGraph(topic, message)
}
// transform the incoming format into the format used by the graph
function transformDatatable(
	inputTable: RawDayGraphDataItem[],
): GraphDataItem[] {
	const outputTable: GraphDataItem[] = []
	let currentItem: GraphDataItem = {}
	monthlyValues = {}
	inputTable.map((inputRow) => {
		currentItem = transformRow(inputRow)
		outputTable.push(currentItem)
		consumerCategories.map((cat) => {
			historicSummary[cat].energyPv += currentItem[cat + 'Pv']
			historicSummary[cat].energyBat += currentItem[cat + 'Bat']
		})
		Object.keys(currentItem).map((field) => {
			if (field != 'date') {
				if (monthlyValues[field]) {
					monthlyValues[field] += currentItem[field]
				} else {
					monthlyValues[field] = currentItem[field]
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
		outputRow.date = d.getDate()
	}
	// counters
	outputRow.gridPush = 0
	outputRow.gridPull = 0
	Object.entries(inputRow.counter).forEach((item) => {
		outputRow.gridPush += item[1].energy_exported
		outputRow.gridPull += item[1].energy_imported
	})
	// PV
	outputRow.solarPower = inputRow.pv.all.energy_exported

	// Battery
	if (Object.entries(inputRow.bat).length > 0) {
		outputRow.batIn = inputRow.bat.all.energy_imported
		outputRow.batOut = inputRow.bat.all.energy_exported
	} else {
		outputRow.batIn = 0
		outputRow.batOut = 0
	}
	// Charge points
	Object.entries(inputRow.cp).forEach(([id, values]) => {
		if (id != 'all') {
			outputRow[id] = values.energy_imported
			// outputRow['soc' + id] = values.soc
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
			sum += item[1].energy_imported
			return sum
		},
		0,
	)
	outputRow.house =
		outputRow.solarPower +
		outputRow.gridPull +
		outputRow.batOut -
		outputRow.gridPush -
		outputRow.batIn -
		outputRow.charging
	outputRow.selfUsage = outputRow.solarPower - outputRow.gridPush
	outputRow.inverter = 0
	const usedEnergy =
		outputRow.gridPull + outputRow.batOut + outputRow.solarPower
	if (usedEnergy > 0) {
		consumerCategories.map((cat) => calculateAutarchy(cat, outputRow))
		// pvChargeCounter += (result.charging * result.solarPower / usedEnergy / 12 * 1000)
		// batChargeCounter += (result.charging * result.batOut / usedEnergy / 12 * 1000)
	} else {
		consumerCategories.map((cat) => {
			outputRow[cat + 'Pv'] = 0
			outputRow[cat + 'Bat'] = 0
		})
	}

	return outputRow
}

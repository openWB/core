import { timeParse } from 'd3'
import {
	graphData,
	type GraphDataItem,
	type RawDayGraphDataItem,
	setGraphData,
	dayGraph,
	calculateAutarchy,
	consumerCategories,
} from './model'
import { historicSummary, usageSummary } from '@/assets/js/model'
import { vehicles } from '../chargePointList/model'

let startValues: GraphDataItem = {}
let endValues: GraphDataItem = {}
let evSocs: string[] = []
let shs: string[] = []
let cps: string[] = []
// methods:

export function processDayGraphMessages(_: string, message: string) {
	const inputTable: RawDayGraphDataItem[] = JSON.parse(message).entries
	evSocs = Object.values(vehicles).map((v) => 'soc-ev' + v.id.toString())
	consumerCategories.map((cat) => {
		historicSummary[cat].energyPv = 0
		historicSummary[cat].energyBat = 0
	})
	shs = []
	cps = []
	const transformedTable = transformDatatable(inputTable)
	setGraphData(transformedTable)
	consumerCategories.map((cat) => {
		historicSummary[cat].energyPv =
			Math.round(historicSummary[cat].energyPv * 100) / 100
		historicSummary[cat].energyBat =
			Math.round(historicSummary[cat].energyBat * 100) / 100
	})
	updateEnergyValues(startValues, endValues)
	if (graphData.graphMode == 'today') {
		setTimeout(() => dayGraph.activate(), 300000)
	}
}

// analyse the incoming data table and create a data table ready for display
function transformDatatable(
	inputTable: RawDayGraphDataItem[],
): GraphDataItem[] {
	const outputTable: GraphDataItem[] = []
	let previousRow: GraphDataItem = {}
	let transformedRow: GraphDataItem = {}

	inputTable.map((inputRow, index) => {
		transformedRow = transformRow(inputRow)
		if (index == 0) {
			startValues = transformedRow
			startValues.chargingPv = 0
			startValues.chargingBat = 0
		} else {
			const values = calculatePowerValues(transformedRow, previousRow)
			outputTable.push(values)
			consumerCategories.map((cat) => {
				historicSummary[cat].energyPv += values[cat + 'Pv'] / 12
				historicSummary[cat].energyBat += values[cat + 'Bat'] / 12
			})
		}
		previousRow = transformedRow
	})
	endValues = transformedRow

	return outputTable
}

// transform one row of the incoming graph data table
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
	currentItem.gridPush = 0
	currentItem.gridPull = 0
	Object.entries(currentRow.counter).forEach((item) => {
		currentItem.gridPush += item[1].exported
		currentItem.gridPull += item[1].imported
	})
	currentItem.solarPower = currentRow.pv.all.exported

	if (Object.entries(currentRow.bat).length > 0) {
		currentItem.batIn = currentRow.bat.all.imported
		currentItem.batOut = currentRow.bat.all.exported
	} else {
		currentItem.batIn = 0
		currentItem.batOut = 0
	}
	Object.entries(currentRow.cp).forEach(([id, values]) => {
		if (id != 'all') {
			currentItem[id] = values.imported
			currentItem['soc' + id] = values.soc
			if (!(id in cps)) {
				cps.push(id)
			}
		} else {
			currentItem['charging'] = values.imported
		}
	})
	Object.entries(currentRow.ev).forEach(([id, values]) => {
		if (id != 'all') {
			currentItem['soc-' + id] = values.soc
		}
	})
	currentItem.devices = 0
	Object.entries(currentRow.sh).forEach(([id, values]) => {
		if (id != 'all') {
			currentItem[id] = values.imported
			currentItem.devices += values.imported
			if (!(id in shs)) {
				shs.push(id)
			}
		} /* else {
			currentItem['devices'] += values.imported
		} */
	})
	//currentItem['devices']=0
	return currentItem
}
// calculate the graph values for one row based on the delta between two input rows
function calculatePowerValues(
	currentRow: GraphDataItem,
	previousRow: GraphDataItem,
): GraphDataItem {
	const result: GraphDataItem = {}
	result.date = currentRow.date
	const cats = [
		'gridPull',
		'gridPush',
		'solarPower',
		'batIn',
		'batOut',
		'charging',
		'devices',
	]

	cats
		.concat(cps)
		.concat(shs)
		.forEach((category) => {
			result[category] = calculatePower(currentRow, previousRow, category)
		})
	result.soc0 = evSocs[0] ? currentRow[evSocs[0]] : 0
	result.soc1 = evSocs[1] ? currentRow[evSocs[1]] : 0
	result.selfUsage = result.solarPower - result.gridPush
	result.house =
		result.solarPower +
		result.gridPull +
		result.batOut -
		result.gridPush -
		result.batIn -
		result.charging -
		result.devices

	result.inverter = 0

	const usedEnergy = result.gridPull + result.batOut + result.solarPower
	if (usedEnergy > 0) {
		consumerCategories.map((cat) => calculateAutarchy(cat, result))
	} else {
		consumerCategories.map((cat) => {
			result[cat + 'Pv'] = 0
			result[cat + 'Bat'] = 0
		})
	}
	return result
}

function calculatePower(
	currentRow: { [key: string]: number },
	previousRow: { [key: string]: number },
	category: string,
) {
	if (
		currentRow[category] !== undefined &&
		previousRow[category] !== undefined &&
		currentRow[category] > previousRow[category]
	) {
		return (12 * (currentRow[category] - previousRow[category])) / 1000
	} else {
		currentRow[category] = previousRow[category]
		return 0
	}
}

function updateEnergyValues(
	startValues: GraphDataItem,
	endValues: GraphDataItem,
) {
	historicSummary.pv.energy = endValues.solarPower - startValues.solarPower
	historicSummary.evuIn.energy = endValues.gridPull - startValues.gridPull
	historicSummary.batOut.energy = endValues.batOut - startValues.batOut
	historicSummary.evuOut.energy = endValues.gridPush - startValues.gridPush
	historicSummary.batIn.energy = endValues.batIn - startValues.batIn
	historicSummary.charging.energy = endValues.charging - startValues.charging
	historicSummary.devices.energy = endValues.devices - startValues.devices
	// historicSummary.charging.energyPv = (endValues.chargingPv - startValues.chargingPv)
	// historicSummary.charging.energyBat = (endValues.chargingBat - startValues.chargingBat)
	historicSummary.charging.pvPercentage = Math.round(
		((historicSummary.charging.energyPv + historicSummary.charging.energyBat) /
			historicSummary.charging.energy) *
			100,
	)

	historicSummary.house.energy =
		historicSummary.evuIn.energy +
		historicSummary.pv.energy +
		historicSummary.batOut.energy -
		historicSummary.evuOut.energy -
		historicSummary.batIn.energy -
		historicSummary.charging.energy -
		historicSummary.devices.energy
	usageSummary.devices.energy = historicSummary.devices.energy
	consumerCategories.map((cat) => {
		usageSummary[cat].energyPv = historicSummary[cat].energyPv
		usageSummary[cat].energyBat = historicSummary[cat].energyBat
		historicSummary[cat].pvPercentage = Math.round(
			((historicSummary[cat].energyPv + historicSummary[cat].energyBat) /
				historicSummary[cat].energy) *
				100,
		)
		usageSummary[cat].pvPercentage = historicSummary[cat].pvPercentage
	})
}

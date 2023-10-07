import * as d3 from 'd3'
import {
  type GraphDataItem,
  type RawDayGraphDataItem,
  setGraphData,
  calculateAutarchy,
  graphData,
} from './model'
import { historicSummary, usageSummary } from '@/assets/js/model'
let monthlyValues: {[key:string]:number} = {}
let pvChargeCounter = 0
let batChargeCounter = 0
const consumerCategories = ['charging', 'house', 'batIn','devices']

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
  let outputTable: GraphDataItem[] = []
  let currentItem: GraphDataItem = {}
  monthlyValues = {}
  inputTable.map((inputRow, index) => {
    currentItem = transformRow(inputRow)
    outputTable.push(currentItem)
    consumerCategories.map((cat) => {
      historicSummary[cat].energyPv += currentItem[cat + 'Pv'] 
      historicSummary[cat].energyBat += currentItem[cat + 'Bat'] 
    })
    if (index == 0) {
      pvChargeCounter = 0
      batChargeCounter = 0
    }
    Object.keys(currentItem).map (field => {
      if (field != 'date') {
        if (monthlyValues[field]) {
          monthlyValues[field]+= currentItem[field]
        } else {
          monthlyValues[field]= currentItem[field]
        }
      }
    })
  })
  return outputTable
}
// initial/refresh delivery of all graph data
export function reloadMonthGraph(topic: string, rawMessage: string) {
  let graphRecords: RawDayGraphDataItem[] = JSON.parse(rawMessage).entries

  let newGraphData: GraphDataItem[] = []
  graphRecords.map((dayData) => {
    const values = transformRow(dayData)
    newGraphData.push(values)
  })
}


function transformRow(inputRow: RawDayGraphDataItem): GraphDataItem {
  let outputRow: GraphDataItem = {}
  const categories = ['']
  // date
  let d = d3.timeParse('%Y%m%d')(inputRow.date)
  if (d) {
    outputRow.date = d.getDate()
  }
  // counters
  Object.entries(inputRow.counter).forEach(([id, values]) => {
    outputRow.gridPush = values.energy_exported
    outputRow.gridPull = values.energy_imported
  })
  // PV
  Object.entries(inputRow.pv).forEach(([id, values]) => {
    if (id == 'all') {
      outputRow.solarPower = values.energy_exported
    }
  })
  // Battery
  if (Object.entries(inputRow.bat).length > 0) {
    Object.entries(inputRow.bat).forEach(([id, values]) => {
      if (id == 'all') {
        outputRow.batIn = values.energy_imported
        outputRow.batOut = values.energy_exported
      }
    })
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
  outputRow.devices = Object.entries(inputRow.sh).reduce<number>((sum: number, item) => {
    sum += item[1].energy_imported
    return sum
  }, 0 )

  
  outputRow.selfUsage = outputRow.solarPower - outputRow.gridPush
  outputRow.house = outputRow.solarPower + outputRow.gridPull + outputRow.batOut
  - outputRow.gridPush - outputRow.batIn - outputRow.charging 
  outputRow.inverter = 0
  let usedEnergy = outputRow.gridPull + outputRow.batOut + outputRow.solarPower
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

function updateEnergyValues(
  monthlyValues: {[key:string]:number}
) {
  historicSummary.pv.energy = monthlyValues.solarPower
  historicSummary.evuIn.energy = monthlyValues.gridPull
  historicSummary.batOut.energy = monthlyValues.batOut
  historicSummary.evuOut.energy = monthlyValues.gridPush
  historicSummary.batIn.energy = monthlyValues.batIn
  historicSummary.charging.energy = monthlyValues.charging
  historicSummary.devices.energy = monthlyValues.devices

  historicSummary.house.energy =
    historicSummary.evuIn.energy +
    historicSummary.pv.energy +
    historicSummary.batOut.energy -
    historicSummary.evuOut.energy -
    historicSummary.batIn.energy -
    historicSummary.charging.energy -
    historicSummary.devices.energy

    consumerCategories.map((cat) => {
      historicSummary[cat].pvPercentage = Math.round(
        ((historicSummary[cat].energyPv + historicSummary[cat].energyBat) /
          historicSummary[cat].energy) *
          100,
      )
      })
  }

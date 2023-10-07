import { timeParse } from 'd3'
import {
  graphData,
  type GraphDataItem,
  type RawDayGraphDataItem,
  setGraphData,
  initGraph,
  dayGraph,
} from './model'
import { historicSummary, usageSummary } from '@/assets/js/model'
import { vehicles } from '../chargePointList/model'
let startValues: GraphDataItem = {}
let endValues: GraphDataItem = {}
let consumerCategories = ['charging', 'house', 'batIn', 'devices']
let evSocs: string[] = []
// methods:

export function processDayGraphMessages(topic: string, message: string) {
  const inputTable: RawDayGraphDataItem[] = JSON.parse(message).entries
  evSocs = Object.values(vehicles).map(v => 'soc-ev' + v.id.toString())

  consumerCategories.map((cat) => {
    historicSummary[cat].energyPv = 0
    historicSummary[cat].energyBat = 0
  })

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
    setTimeout(() => initGraph(), 300000)
  }
}

// analyse the incoming data table and create a data table ready for display
function transformDatatable(
  inputTable: RawDayGraphDataItem[],
): GraphDataItem[] {
  let outputTable: GraphDataItem[] = []
  let previousRow: GraphDataItem = {}
  let transformedRow: GraphDataItem = {}

  inputTable.map((inputRow, index) => {
    //for (let index = 0; index < inputTable.length; index++) {
    transformedRow = transformRow(inputRow)
    if (index == 0) {
      startValues = transformedRow
      startValues.chargingPv = 0
      startValues.chargingBat = 0
      // pvChargeCounter = 0
      // batChargeCounter = 0
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
  let currentItem: GraphDataItem = {}
  currentItem.devices = 0
  if (graphData.graphMode == 'day' || graphData.graphMode == 'today') {
    let d = timeParse('%H:%M')(currentRow.date)
    if (d) {
      d.setMonth(dayGraph.date.getMonth())
      d.setDate(dayGraph.date.getDate())
      d.setFullYear(dayGraph.date.getFullYear())
      currentItem.date = d.getTime()
    }
  } else {
    let d = timeParse('%Y%m%d')(currentRow.date)

    if (d) {
      currentItem.date = d.getDate()
    }
  }
  Object.entries(currentRow.counter).forEach(([id, values]) => {
    currentItem.gridPush = values.exported
    currentItem.gridPull = values.imported
  })
  Object.entries(currentRow.pv).forEach(([id, values]) => {
    if (id == 'pv1') {
      currentItem.solarPower = values.exported
    }
  })
  if (Object.entries(currentRow.bat).length > 0) {
    Object.entries(currentRow.bat).forEach(([id, values]) => {
      if (id == 'all') {
        currentItem.batIn = values.imported
        currentItem.batOut = values.exported
      }
    })
  } else {
    currentItem.batIn = 0
    currentItem.batOut = 0
  }
  Object.entries(currentRow.cp).forEach(([id, values]) => {
    if (id != 'all') {
      currentItem[id] = values.imported
      currentItem['soc' + id] = values.soc
    } else {
      currentItem['charging'] = values.imported
    }
  })
  Object.entries(currentRow.ev).forEach(([id, values]) => {
    if (id != 'all') {
      currentItem['soc-' + id] = values.soc
    }
  })
  Object.entries(currentRow.sh).forEach(([id, values]) => {
    if (id != 'all') {
      currentItem[id] = values.imported
      currentItem['devices'] += values.imported
    } else {
      currentItem['devices'] += values.imported
    }
  })
  //currentItem['devices']=0
  return currentItem
}

// list of chargepoints we have
const cps = [
  'cp0',
  'cp1',
  'cp2',
  'cp3',
  'cp4',
  'cp5',
  'cp6',
  'cp7',
  'cp8',
  'cp9',
]

const shs = ['sh0', 'sh1', 'sh2', 'sh3', 'sh4']
// calculate the graph values for one row based on the delta between two input rows
function calculatePowerValues(
  currentRow: GraphDataItem,
  previousRow: GraphDataItem,
): GraphDataItem {
  let result: GraphDataItem = {}
  result.date = currentRow.date
  const cats = [
    'gridPull',
    'gridPush',
    'solarPower',
    'batIn',
    'batOut',
    'charging',
    'devices'
  ]

  cats.concat(cps).forEach((category) => {
    result[category] = calculatePower(currentRow, previousRow, category)
    if (category == 'cp6') {
    }
  })
  cats.concat(shs).forEach((category) => {
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

  let usedEnergy = result.gridPull + result.batOut + result.solarPower
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
    previousRow[category] !== undefined
  ) {
    return (12 * (currentRow[category] - previousRow[category])) / 1000
  } else {
    return 0
  }
}
function calculateAutarchy(cat: string, values: GraphDataItem) {
  values[cat + 'Pv'] =
    (values[cat] * (values.solarPower - values.gridPush)) /
    (values.solarPower - values.gridPush + values.gridPull + values.batOut)
  values[cat + 'Bat'] =
    (values[cat] * values.batOut) /
    (values.solarPower - values.gridPush + values.gridPull + values.batOut)
}
function updateEnergyValues(
  startValues: GraphDataItem,
  endValues: GraphDataItem,
) {
  //const startValues = extractCounters (rawData[0]);
  //const endValues = extractCounters(rawData[rawData.length - 1]);
  historicSummary.pv.energy =
    (endValues.solarPower - startValues.solarPower) / 1000
  historicSummary.evuIn.energy =
    (endValues.gridPull - startValues.gridPull) / 1000
  historicSummary.batOut.energy = (endValues.batOut - startValues.batOut) / 1000
  historicSummary.evuOut.energy =
    (endValues.gridPush - startValues.gridPush) / 1000
  historicSummary.batIn.energy = (endValues.batIn - startValues.batIn) / 1000
  historicSummary.charging.energy =
    (endValues.charging - startValues.charging) / 1000
  historicSummary.devices.energy =
    (endValues.devices - startValues.devices) / 1000
  // historicSummary.charging.energyPv = (endValues.chargingPv - startValues.chargingPv) / 1000
  // historicSummary.charging.energyBat = (endValues.chargingBat - startValues.chargingBat) / 1000
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

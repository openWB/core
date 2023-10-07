import * as d3 from 'd3'
import { mqttSubscribe, mqttUnsubscribe } from '../../assets/js/mqttClient'
import { globalData } from '../../assets/js/model'
import {
  type GraphDataItem,
  type RawGraphDataItem,
  graphData,
  setGraphData,
  liveGraph,
} from './model'

// methods:
export function processLiveGraphMessages(topic: string, message: string) {
  if (topic == 'openWB/graph/boolDisplayLiveGraph') {
    globalData.displayLiveGraph = +message == 1
  } else if (topic.match(/^openwb\/graph\/alllivevaluesJson[1-9][0-9]*$/i)) {
    reloadLiveGraph(topic, message)
  } else if (topic == 'openWB/graph/lastlivevaluesJson') {
    updateLiveGraph(topic, message)
  } else if (topic == 'openWB/graph/config/duration') {
    //  updateGlobal("liveGraphDuration", JSON.parse(message));
  } else {
    console.warn('Ignored GRAPH message: [' + topic + '](' + message + ')')
  }
}
// initial/refresh delivery of all graph data
export function reloadLiveGraph(topic: string, rawMessage: string) {
  if (!liveGraph.initialized) {
    let graphRecords: RawGraphDataItem[] = []
    let stringTable = rawMessage.toString().split('\n')
    if (stringTable.length > 1) {
      graphRecords = stringTable.map(
        (recordString) => JSON.parse(recordString) as RawGraphDataItem,
      )
    } else {
      graphRecords = []
    }
    let numbersFound = topic.match(/(\d+)$/g)
    const serialNo = numbersFound ? numbersFound[0] : ''
    if (serialNo != '') {
      if (typeof liveGraph.rawDataPacks[+serialNo - 1] === 'undefined') {
        liveGraph.rawDataPacks[+serialNo - 1] = graphRecords
        liveGraph.initCounter++
      }
    }
  }
  if (liveGraph.initCounter == 16) {
    // Initialization complete
    let newGraphData: GraphDataItem[] = []
    liveGraph.unsubscribeRefresh()
    liveGraph.initialized = true
    liveGraph.rawDataPacks.map((dataPack) => {
      dataPack.map((rawItem) => {
        const values = extractValues(rawItem)
        newGraphData.push(values)
      })
    })
    setGraphData(newGraphData)
    liveGraph.subscribeUpdates()
  }
}
// incremental update message for the live graph
export function updateLiveGraph(topic: string, rawString: string) {
  let rawItem = JSON.parse(rawString) as RawGraphDataItem
  const values = extractValues(rawItem)
  liveGraph.graphRefreshCounter++
  setGraphData(graphData.data.concat(values))
  if (liveGraph.graphRefreshCounter > 60) {
    liveGraph.activate()
  }
}
function extractValues(data: RawGraphDataItem): GraphDataItem {
  let values: GraphDataItem = {}
  values.date = fullDate(data.time).valueOf()
  if (+data.grid > 0) {
    values.gridPull = +data.grid
    values.gridPush = 0
  } else if (+data.grid <= 0) {
    values.gridPull = 0
    values.gridPush = -data.grid
  } else {
    values.gridPull = 0
    values.gridPush = 0
  }
  if (+data['pv-all'] >= 0) {
    values.solarPower = +data['pv-all']
    values.inverter = 0
  } else {
    values.solarPower = 0
    values.inverter = -data['pv-all']
  }
  values.house = +data['house-power']
  //battery
  if (+data['bat-all-power'] > 0) {
    values.batOut = 0
    values.batIn = +data['bat-all-power']
  } else if (+data['bat-all-power'] < 0) {
    values.batOut = -data['bat-all-power']
    values.batIn = 0
  } else {
    values.batOut = 0
    values.batIn = 0
  }
  if (data['bat-all-soc']) {
    values.batterySoc = +data['bat-all-soc']
  } else {
    values.batterySoc = 0
  }
  values.charging = +data['charging-all']
  // charge points - we only show a maximum of 10 chargepoints in the graph
  for (let i = 0; i < 10; i++) {
    if (data['cp' + i + '-power']) {
      values['cp' + i] = +data['cp' + i + '-power']
    } else {
      values['cp' + i] = 0
    }
  }
  values.selfUsage = values.solarPower - values.gridPush
  if (values.selfUsage < 0) {
    values.selfUsage = 0
  }
  values.devices = 0
  return values
}
function fullDate(timeString: string) {
  const now = new Date(Date.now())
  const mSecondsPerDay = 86400000 // milliseconds in a day
  let date = new Date()
  let parsedDate = d3.timeParse('%H:%M:%S')(timeString)
  if (parsedDate) {
    date = parsedDate
    date.setDate(now.getDate())
    date.setMonth(now.getMonth())
    date.setFullYear(now.getFullYear())
    if (date.getHours() > now.getHours()) {
      // this is an entry from yesterday
      date = new Date(date.getTime() - mSecondsPerDay) // change date to yesterday
    }
  }
  return date
}

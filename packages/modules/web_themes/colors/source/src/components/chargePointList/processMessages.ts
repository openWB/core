import { usageSummary, globalData } from '@/assets/js/model'
import {
  chargePoints,
  vehicles,
  chargeTemplates,
  evTemplates,
  Vehicle,
  ChargeMode,
  type ChargeTimePlan,
} from './model'
import type {
  ConnectedVehicleConfig,
  ChargeTemplate,
  EvTemplate,
} from './model'

export function processChargepointMessages(topic: string, message: string) {
  let index = getIndex(topic)
  if (index && !(index in chargePoints)) {
    console.warn('Invalid chargepoint id received: ' + index)
    return
  }
  // General Chargepoint messages
  if (topic == 'openWB/chargepoint/get/power') {
    usageSummary.charging.power = +message
  } else if (topic == 'openWB/chargepoint/get/daily_imported') {
    usageSummary.charging.energy = +message / 1000
  }
  if (topic == 'openWB/chargepoint/get/daily_exported') {
    globalData.cpDailyExported = +message
  } else if (index) {
    if (topic.match(/^openwb\/chargepoint\/[0-9]+\/config$/i)) {
      if (chargePoints[index]) {
        var configMessage = JSON.parse(message)
        chargePoints[index].name = configMessage.name
        chargePoints[index].icon = configMessage.name

      } else {
        console.warn('invalid chargepoint index: ' + index)
      }
    } else if (topic.match(/^openwb\/chargepoint\/[0-9]+\/get\/state_str$/i)) {
      chargePoints[index].stateStr = JSON.parse(message)
    } else if (topic.match(/^openwb\/chargepoint\/[0-9]+\/get\/fault_str$/i)) {
      chargePoints[index].faultStr = JSON.parse(message)
    } else if (
      topic.match(/^openwb\/chargepoint\/[0-9]+\/get\/fault_state$/i)
    ) {
      chargePoints[index].faultState = +message
    } else if (topic.match(/^openWB\/chargepoint\/[0-9]+\/get\/power$/i)) {
      chargePoints[index].power = +message
    } else if (
      topic.match(/^openWB\/chargepoint\/[0-9]+\/get\/daily_imported$/i)
    ) {
      chargePoints[index].dailyYield = +message / 1000
    } else if (topic.match(/^openwb\/chargepoint\/[0-9]+\/get\/plug_state$/i)) {
      chargePoints[index].isPluggedIn = message == 'true'
    } else if (
      topic.match(/^openwb\/chargepoint\/[0-9]+\/get\/charge_state$/i)
    ) {
      chargePoints[index].isCharging = message == 'true'
    } else if (
      topic.match(/^openwb\/chargepoint\/[0-9]+\/set\/manual_lock$/i)
    ) {
      chargePoints[index].updateIsLocked(message == 'true')
    } else if (topic.match(/^openwb\/chargepoint\/[0-9]+\/get\/enabled$/i)) {
      chargePoints[index].isEnabled = message == '1'
    } else if (
      topic.match(/^openwb\/chargepoint\/[0-9]+\/get\/phases_in_use/i)
    ) {
      chargePoints[index].phasesInUse = +message
    } else if (topic.match(/^openwb\/chargepoint\/[0-9]+\/set\/current/i)) {
      chargePoints[index].current = +message
    } else if (topic.match(/^openwb\/chargepoint\/[0-9]+\/set\/log/i)) {
      const obj = JSON.parse(message)
      chargePoints[index].chargedSincePlugged = obj.imported_since_plugged
    }
    else if (
      topic.match(/^openwb\/chargepoint\/[0-9]+\/get\/connected_vehicle\/soc$/i)
    ) {
      // console.warn('Ignored Connected Vehicle SOC ' + topic + ' : ' + message)
      const obj = JSON.parse(message)
      chargePoints[index].rangeCharged = obj.range_charged
      chargePoints[index].rangeUnit = obj.range_unit
    } else if (
      topic.match(
        /^openwb\/chargepoint\/[0-9]+\/get\/connected_vehicle\/soc_config$/i,
      )
    ) {
      chargePoints[index].isSocManual = message == 'manual'
    } else if (
      topic.match(
        /^openwb\/chargepoint\/[0-9]+\/get\/connected_vehicle\/info$/i,
      )
    ) {
      let info = JSON.parse(message)
      chargePoints[index].vehicleName = String(info.name)
      chargePoints[index].updateConnectedVehicle(+info.id)
    } else if (
      topic.match(
        /^openwb\/chargepoint\/[0-9]+\/get\/connected_vehicle\/config$/i,
      )
    ) {
      let config: ConnectedVehicleConfig = JSON.parse(message)
      switch (config.chargemode) {
        case 'instant_charging':
          chargePoints[index].updateChargeMode(ChargeMode.instant_charging)
          break
        case 'pv_charging':
          chargePoints[index].updateChargeMode(ChargeMode.pv_charging)
          break
        case 'scheduled_charging':
          chargePoints[index].updateChargeMode(ChargeMode.scheduled_charging)
          break
        case 'standby':
          chargePoints[index].updateChargeMode(ChargeMode.standby)
          break
        case 'stop':
          chargePoints[index].updateChargeMode(ChargeMode.stop)
          break
      }
      chargePoints[index].chargeTemplate = config.charge_template
      chargePoints[index].averageConsumption = config.average_consumption
    } else {
      // console.warn('Ignored chargepoint message: ' + topic)
    }
  } else {
    // console.warn('Ignored chargepoint message: ' + topic)
  }
}
export function processVehicleMessages(topic: string, message: string) {
  let index = getIndex(topic)
  if (index != undefined) {
    if (!(index in vehicles)) {
      let v = new Vehicle(index)
      vehicles[index] = v
      console.info('New vehicle created: ' + index)
    }
    if (topic.match(/^openwb\/vehicle\/[0-9]+\/name$/i)) {
      // set car Name for charge point
      Object.values(chargePoints).forEach((cp) => {
        if (cp.connectedVehicle == index) {
          cp.vehicleName = JSON.parse(message)
        }
      })
      vehicles[index].name = JSON.parse(message)
    } else if (topic.match(/^openwb\/vehicle\/[0-9]+\/get\/soc$/i)) {
      // set soc for cp
      Object.values(chargePoints).forEach((cp) => {
        if (cp.connectedVehicle == index) {
          cp.soc = JSON.parse(message)
        }
      })
    } else if (topic.match(/^openwb\/vehicle\/[0-9]+\/get\/range$/i)) {
      vehicles[index].range = +message
    }
    else if (topic.match(/^openwb\/vehicle\/[0-9]+\/charge_template$/i)) {
      vehicles[index].updateChargeTemplateId(+message)
    } else if (topic.match(/^openwb\/vehicle\/[0-9]+\/ev_template$/i)) {
      vehicles[index].updateEvTemplateId(+message)
    } else {
      // console.warn('Ignored vehicle message [' + topic + ']=' + message)
    }
  }
}
export function processVehicleTemplateMessages(topic: string, message: string) {
  if (topic.match(/^openwb\/vehicle\/template\/charge_template\/[0-9]+$/i)) {
    let match = topic.match(/[0-9]+$/i)
    if (match) {
      let index = +match[0]
      let template: ChargeTemplate = JSON.parse(message) as ChargeTemplate
      if (!template.chargemode.scheduled_charging.plans) {
        template.chargemode.scheduled_charging.plans = {}
      }
      if (!template.time_charging.plans) {
        template.time_charging.plans = {}
      }
      chargeTemplates[index] = template
      updateCpFromChargeTemplate(index, template)
    }
  } else if (
    topic.match(
      /^openwb\/vehicle\/template\/charge_template\/[0-9]+\/time_charging\/plans\/[0-9]+$/i,
    )
  ) {
    let tidMatch = topic.match(/(?:\/)([0-9]+)(?:\/)/g)
    let pidMatch = topic.match(/[0-9]+$/i)
    if (tidMatch && pidMatch) {
      let tId = +tidMatch[0].replace(/[^0-9]+/g, '')
      let pId = +pidMatch[0]
      let plan: ChargeTimePlan = JSON.parse(message)
      chargeTemplates[tId].time_charging.plans[pId] = plan
    }
  } else if (topic.match(/^openwb\/vehicle\/template\/ev_template\/[0-9]+$/i)) {
    let match = topic.match(/[0-9]+$/i)
    if (match) {
      let index = +match[0]
      let template: EvTemplate = JSON.parse(message) as EvTemplate
      evTemplates[index] = template
      // updateCpFromChargeTemplate(index, template)
    }
  } else {
    // console.warn('Ignored VEHICLE TEMPLATE message [' + topic + ']=' + message)
  }
}
function updateCpFromChargeTemplate(index: number, template: ChargeTemplate) {
  Object.values(chargePoints).forEach((cp) => {
    if (cp.chargeTemplate == index) {
      cp.updateCpPriority(template.prio)
      // cp.updateChargeMode(template.chargemode.selected)
      cp.updateInstantChargeLimitMode(
        template.chargemode.instant_charging.limit.selected,
      )
      cp.updateInstantTargetCurrent(
        template.chargemode.instant_charging.current,
      )
      cp.updateInstantTargetSoc(template.chargemode.instant_charging.limit.soc)
      cp.updateInstantMaxEnergy(
        template.chargemode.instant_charging.limit.amount,
      )
      cp.updateScheduledCharging(template.time_charging.active)
      cp.updatePvFeedInLimit(template.chargemode.pv_charging.feed_in_limit)
      cp.updatePvMinCurrent(template.chargemode.pv_charging.min_current)
      cp.updatePvMaxSoc(template.chargemode.pv_charging.max_soc)
      cp.updatePvMinSoc(template.chargemode.pv_charging.min_soc)
      cp.updatePvMinSocCurrent(template.chargemode.pv_charging.min_soc_current)
    }
  })
}

function getIndex(topic: string): number | undefined {
  let index = 0
  try {
    var matches = topic.match(/(?:\/)([0-9]+)(?=\/)/g)
    if (matches) {
      index = +matches[0].replace(/[^0-9]+/g, '')
      return index
    } else {
      return undefined
    }
  } catch (e) {
    console.warn('Parser error in getIndex for topic ' + topic)
  }
}

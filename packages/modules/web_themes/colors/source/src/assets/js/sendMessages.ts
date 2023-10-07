/*
 * sendMessages.ts
 * colors theme for openwb 2.0
 * Copyright (c) 2022 Claus Hagen
 */

import { mqttPublish, mqttClientId } from './mqttClient'
import { chargePoints, chargeTemplates } from '@/components/chargePointList/model'

const topics: { [topic: string]: string } = {
  cpLock: 'openWB/set/chargepoint/%/set/manual_lock',
  chargeMode:
    'openWB/set/vehicle/template/charge_template/%/chargemode/selected',
  cpPriority: 'openWB/set/vehicle/template/charge_template/%/prio',
  cpScheduledCharging:
    'openWB/set/vehicle/template/charge_template/%/time_charging/active',
  pvBatteryPriority:
    'openWB/set/general/chargemode_config/pv_charging/bat_prio',
  chargeTemplate: 'openWB/set/vehicle/template/charge_template/%',
  cpVehicle: 'openWB/set/chargepoint/%/config/ev',
  cpInstantChargeLimitMode:
    'openWB/set/vehicle/template/charge_template/%/chargemode/instant_charging/limit/selected',
  cpInstantTargetCurrent:
    'openWB/set/vehicle/template/charge_template/%/chargemode/instant_charging/current',
  cpInstantTargetSoc:
    'openWB/set/vehicle/template/charge_template/%/chargemode/instant_charging/limit/soc',
  cpInstantMaxEnergy:
    'openWB/set/vehicle/template/charge_template/%/chargemode/instant_charging/limit/amount',
  cpPvFeedInLimit:
    'openWB/set/vehicle/template/charge_template/%/chargemode/pv_charging/feed_in_limit',
  cpPvMinCurrent:
    'openWB/set/vehicle/template/charge_template/%/chargemode/pv_charging/min_current',
  cpPvMaxSoc:
    'openWB/set/vehicle/template/charge_template/%/chargemode/pv_charging/max_soc',
  cpPvMinSoc:
    'openWB/set/vehicle/template/charge_template/%/chargemode/pv_charging/min_soc',
  cpPvMinSocCurrent:
    'openWB/set/vehicle/template/charge_template/%/chargemode/pv_charging/min_soc_current',
  etMaxPrice: 'openWB/set/optional/et/max_price',
  vhChargeTemplateId: 'openWB/set/vehicle/%/charge_template',
  vhEvTemplateId: 'openWB/set/vehicle/%/ev_template',
  // SmartHome
  // shSetManual: 'openWB/config/set/SmartHome/Devices/%/mode',
  shSetManual: 'openWB/set/LegacySmartHome/config/set/Devices/%/mode',
  shSwitchOn: 'openWB/set/LegacySmartHome/config/set/Devices/%/device_manual_control',
}
export function updateServer(
  item: string,
  value: string | number | boolean,
  index: number = 0,
) {
  if (isNaN(index)) {
    console.warn('Invalid index')
    return
  }
  let topic = topics[item]
  if (!topic) {
    console.warn('No topic for update type ' + item)
    return
  }
  switch (item) {
    case 'chargeMode':
    case 'cpPriority':
    case 'cpScheduledCharging':
    case 'cpInstantTargetCurrent':
    case 'cpInstantChargeLimitMode':
    case 'cpInstantTargetSoc':
    case 'cpInstantMaxEnergy':
    case 'cpPvFeedInLimit':
    case 'cpPvMinCurrent':
    case 'cpPvMaxSoc':
    case 'cpPvMinSoc':
    case 'cpPvMinSocCurrent': // these values are set in the charge template
      let templateId = chargePoints[index].chargeTemplate
      topic = topic.replace('%', String(templateId))
      break
    default:
      topic = topic.replace('%', String(index))
  }
  switch (typeof value) {
    case 'number':
      mqttPublish(topic, JSON.stringify(+value))
      break
    default:
      mqttPublish(topic, JSON.stringify(value))
  }
}

export function updateChargeTemplate (templateId: number) {
  let template = chargeTemplates[templateId]
  if (template) {
    let topic = 'openWB/set/vehicle/template/charge_template/' + templateId
  mqttPublish(topic, JSON.stringify(template))
  }
}
export function sendCommand (event: Object) {
 // console.log ("SENDCOMMAND " + JSON.stringify(event))
    mqttPublish ('openWB/set/command/' + mqttClientId() + '/todo', JSON.stringify(event))
}

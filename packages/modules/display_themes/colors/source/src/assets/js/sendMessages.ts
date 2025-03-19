/*
 * sendMessages.ts
 * colors theme for openwb 2.0
 * Copyright (c) 2022 Claus Hagen
 */

import { mqttPublish, mqttClientId } from './mqttClient'
import { chargePoints } from '@/components/chargePointList/model'

const topics: { [topic: string]: string } = {
	cpLock: 'openWB/set/chargepoint/%/set/manual_lock',
	chargeMode:
		'openWB/set/vehicle/template/charge_template/%/chargemode/selected',
	cpPriority: 'openWB/set/vehicle/template/charge_template/%/prio',
	cpTimedCharging:
		'openWB/set/vehicle/template/charge_template/%/time_charging/active',
	cpTimedPlanActive:
		'openWB/set/vehicle/template/charge_template/%/time_charging/plans/@/active',
	cpScheduledPlanActive:
		'openWB/set/vehicle/template/charge_template/%/chargemode/scheduled_charging/plans/@/active',
	pvBatteryPriority:
		'openWB/set/general/chargemode_config/pv_charging/bat_mode',
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
	cpEtMaxPrice: 'openWB/set/vehicle/template/charge_template/%/et/max_price',
	//etMaxPrice: 'openWB/set/optional/et/max_price',
	vhChargeTemplateId: 'openWB/set/vehicle/%/charge_template',
	vhEvTemplateId: 'openWB/set/vehicle/%/ev_template',
	shSetManual: 'openWB/set/LegacySmartHome/config/set/Devices/%/mode',
	shSwitchOn:
		'openWB/set/LegacySmartHome/config/set/Devices/%/device_manual_control',
	socUpdate: 'openWB/set/vehicle/%/get/force_soc_update',
	setSoc: 'openWB/set/vehicle/%/soc_module/calculated_soc_state/manual_soc',
	priceCharging: 'openWB/set/vehicle/template/charge_template/%/et/active',
}
export function updateServer(
	item: string,
	value: string | number | boolean,
	index: number = 0,
	index2: number | undefined = undefined,
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
		case 'cpEtMaxPrice':
		case 'cpPvMinSocCurrent':
			// these values are set in the charge template
			topic = topic.replace('%', chargePoints[index].chargeTemplate.toString())
			break
		default:
			topic = topic.replace('%', String(index))
			if (index2 != undefined) {
				topic = topic.replace('@', String(index2))
			}
	}
	switch (typeof value) {
		case 'number':
			mqttPublish(topic, JSON.stringify(+value))
			break
		default:
			mqttPublish(topic, JSON.stringify(value))
	}
}

export function sendCommand(command: string, data: object = {}) {
	console.log('send command ' + command + ' ' + JSON.stringify(data))

	mqttPublish(
		`openWB/set/command/${mqttClientId()}/todo`,
		JSON.stringify({ command: command, data: data }),
	)
}

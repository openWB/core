import { usageSummary, globalData, masterData } from '@/assets/js/model'
import {
	chargePoints,
	vehicles,
	evTemplates,
	Vehicle,
	chargeTemplates,
} from './model'
import type {
	ConnectedVehicleConfig,
	EvTemplate,
	ChargeTemplate,
} from './model'

export function processChargepointMessages(topic: string, message: string) {
	const index = getIndex(topic)
	if (index && !(index in chargePoints)) {
		console.warn('Invalid chargepoint id received: ' + index)
		return
	}
	// General Chargepoint messages
	if (topic == 'openWB/chargepoint/get/power') {
		usageSummary.charging.power = +message
	} else if (topic == 'openWB/chargepoint/get/daily_imported') {
		usageSummary.charging.energy = +message
	}
	if (topic == 'openWB/chargepoint/get/daily_exported') {
		globalData.cpDailyExported = +message
	} else if (index) {
		if (topic.match(/^openwb\/chargepoint\/[0-9]+\/config$/i)) {
			if (chargePoints[index]) {
				const configMessage = JSON.parse(message)
				chargePoints[index].name = configMessage.name
				chargePoints[index].icon = configMessage.name
				if (masterData['cp' + index]) {
					masterData['cp' + index].name = configMessage.name
					masterData['cp' + index].icon = configMessage.name
				} else {
					masterData['cp' + index] = {
						name: configMessage.name,
						icon: configMessage.name,
						color: 'var(--color-charging)',
					}
				}
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
			chargePoints[index].dailyYield = +message
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
		} else if (topic.match(/^openwb\/chargepoint\/[0-9]+\/get\/currents/i)) {
			chargePoints[index].currents = JSON.parse(message)
		} else if (topic.match(/^openwb\/chargepoint\/[0-9]+\/set\/log/i)) {
			const obj = JSON.parse(message)
			chargePoints[index].chargedSincePlugged = obj.imported_since_plugged
		} else if (
			topic.match(/^openwb\/chargepoint\/[0-9]+\/get\/connected_vehicle\/soc$/i)
		) {
			// console.warn('Ignored Connected Vehicle SOC ' + topic + ' : ' + message)
			const obj = JSON.parse(message)
			chargePoints[index].soc = obj.soc
			chargePoints[index].waitingForSoc = false
			chargePoints[index].rangeCharged = obj.range_charged
			chargePoints[index].rangeUnit = obj.range_unit
		} else if (
			topic.match(
				/^openwb\/chargepoint\/[0-9]+\/get\/connected_vehicle\/info$/i,
			)
		) {
			const info = JSON.parse(message)
			chargePoints[index].vehicleName = String(info.name)
			chargePoints[index].updateConnectedVehicle(+info.id)
		} else if (
			topic.match(
				/^openwb\/chargepoint\/[0-9]+\/get\/connected_vehicle\/config$/i,
			)
		) {
			const config: ConnectedVehicleConfig = JSON.parse(message)
			chargePoints[index].averageConsumption = config.average_consumption
		} else if (
			topic.match(/^openwb\/chargepoint\/[0-9]+\/set\/charge_template$/i)
		) {
			chargePoints[index].chargeTemplate = JSON.parse(message)
		} else {
			// console.warn('Ignored chargepoint message: ' + topic)
		}
	} else {
		// console.warn('Ignored chargepoint message: ' + topic)
	}
}
export function processVehicleMessages(topic: string, message: string) {
	const index = getIndex(topic)
	if (index != undefined) {
		if (!(index in vehicles)) {
			const v = new Vehicle(index)
			vehicles[index] = v
			// console.info('New vehicle created: ' + index)
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
			vehicles[index].soc = JSON.parse(message)
		} else if (topic.match(/^openwb\/vehicle\/[0-9]+\/get\/range$/i)) {
			if (isNaN(+message)) {
				vehicles[index].range = 0
			} else {
				vehicles[index].range = +message
			}
		} else if (topic.match(/^openwb\/vehicle\/[0-9]+\/charge_template$/i)) {
			vehicles[index].updateChargeTemplateId(+message)
		} else if (topic.match(/^openwb\/vehicle\/[0-9]+\/ev_template$/i)) {
			vehicles[index].updateEvTemplateId(+message)
		} else if (topic.match(/^openwb\/vehicle\/[0-9]+\/soc_module\/config$/i)) {
			const config = JSON.parse(message)
			Object.values(chargePoints).forEach((cp) => {
				if (cp.connectedVehicle == index) {
					cp.isSocConfigured = config.type !== null
					cp.isSocManual = config.type == 'manual'
				}
			})
			vehicles[index].isSocConfigured = config.type !== null
			vehicles[index].isSocManual = config.type == 'manual'
		} else {
			// console.warn('Ignored vehicle message [' + topic + ']=' + message)
		}
	}
}
export function processVehicleTemplateMessages(topic: string, message: string) {
	if (topic.match(/^openwb\/vehicle\/template\/charge_template\/[0-9]+$/i)) {
		const match = topic.match(/[0-9]+$/i)
		if (match) {
			const index = +match[0]
			chargeTemplates[index] = JSON.parse(message) as ChargeTemplate
		}
	} else if (topic.match(/^openwb\/vehicle\/template\/ev_template\/[0-9]+$/i)) {
		const match = topic.match(/[0-9]+$/i)
		if (match) {
			const index = +match[0]
			const template: EvTemplate = JSON.parse(message) as EvTemplate
			evTemplates[index] = template
		}
	} else {
		// console.warn('Ignored VEHICLE TEMPLATE message [' + topic + ']=' + message)
	}
}

function getIndex(topic: string): number | undefined {
	let index = 0
	try {
		const matches = topic.match(/(?:\/)([0-9]+)(?=\/)/g)
		if (matches) {
			index = +matches[0].replace(/[^0-9]+/g, '')
			return index
		} else {
			return undefined
		}
	} catch (e) {
		console.warn('Parser error in getIndex for topic ' + topic + ': ' + e)
	}
}

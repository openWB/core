import { mqttRegister, mqttSubscribe, mqttUnsubscribe } from './mqttClient'
import type { Hierarchy } from './types'
import { globalData, sourceSummary, usageSummary } from './model'
import { processLiveGraphMessages } from '../../components/powerGraph/processLiveGraphData'
import { processDayGraphMessages } from '../../components/powerGraph/processDayGraphData'
import { processMonthGraphMessages } from '../../components/powerGraph/processMonthYearGraphData'
import { processYearGraphMessages } from '../../components/powerGraph/processMonthYearGraphData'
import { initGraph } from '@/components/powerGraph/model'
import { processBatteryMessages } from '@/components/batteryList/processMessages'
import { processEtProviderMessages } from '@/components/priceChart/processMessages'
import {
	addChargePoint,
	resetChargePoints,
} from '@/components/chargePointList/model'
import { addBattery, resetBatteries } from '@/components/batteryList/model'
import {
	processChargepointMessages,
	processVehicleMessages,
	processVehicleTemplateMessages,
} from '@/components/chargePointList/processMessages'
import { processSmarthomeMessages } from '@/components/smartHome/processMessages'
import { addCounter, counters } from '@/components/counterList/model'
import { mqttClientId } from './mqttClient'
import { displayConfig } from './model'

const topicsToSubscribe = [
	'openWB/counter/#',
	'openWB/bat/#',
	'openWB/pv/get/#',
	'openWB/chargepoint/#',
	'openWB/vehicle/#',
	'openWB/general/chargemode_config/pv_charging/#',
	'openWB/optional/et/#',
	'openWB/system/#',
	'openWB/LegacySmartHome/#',
	'openWB/command/' + mqttClientId() + '/#',
	'openWB/optional/int_display/#',
]
export function msgInit() {
	mqttRegister(processMqttMessage)
	topicsToSubscribe.forEach((topic) => {
		mqttSubscribe(topic)
	})
	initGraph()
}
export function msgStop() {
	topicsToSubscribe.forEach((topic) => {
		mqttUnsubscribe(topic)
	})
}
function processMqttMessage(topic: string, payload: Buffer) {
	const message = payload.toString()
	if (topic.match(/^openwb\/counter\/[0-9]+\//i)) {
		processCounterMessages(topic, message)
	} else if (topic.match(/^openwb\/counter\//i)) {
		processGlobalCounterMessages(topic, message)
	} else if (topic.match(/^openwb\/bat\//i)) {
		processBatteryMessages(topic, message)
	} else if (topic.match(/^openwb\/pv\//i)) {
		processPvMessages(topic, message)
	} else if (topic.match(/^openwb\/chargepoint\//i)) {
		processChargepointMessages(topic, message)
	} else if (topic.match(/^openwb\/vehicle\/template\//i)) {
		processVehicleTemplateMessages(topic, message)
	} else if (topic.match(/^openwb\/vehicle\//i)) {
		processVehicleMessages(topic, message)
	} else if (
		topic.match(/^openwb\/general\/chargemode_config\/pv_charging\//i)
	) {
		processPvConfigMessages(topic, message)
	} else if (topic.match(/^openwb\/graph\//i)) {
		processLiveGraphMessages(topic, message)
	} else if (topic.match(/^openwb\/log\/daily\//i)) {
		processDayGraphMessages(topic, message)
	} else if (topic.match(/^openwb\/log\/monthly\//i)) {
		processMonthGraphMessages(topic, message)
	} else if (topic.match(/^openwb\/log\/yearly\//i)) {
		processYearGraphMessages(topic, message)
	} else if (topic.match(/^openwb\/optional\/et\//i)) {
		processEtProviderMessages(topic, message)
	} // else if ( mqttTopic.match( /^openwb\/global\//i) ) { processGlobalMessages(mqttTopic, message); }
	else if (topic.match(/^openwb\/system\//i)) {
		processSystemMessages(topic, message)
	} // else if ( mqttTopic.match( /^openwb\/verbraucher\//i) ) { processVerbraucherMessages(mqttTopic, message); }
	// else if ( mqttTopic.match( /^openwb\/hook\//i) ) { processHookMessages(mqttTopic, message); }
	// else if ( mqttTopic.match( /^openwb\/SmartHome\/Devices\//i) ) { processSmartHomeDevicesMessages(mqttTopic, message); }
	else if (topic.match(/^openwb\/LegacySmartHome\//i)) {
		processSmarthomeMessages(topic, message)
	} else if (topic.match(/^openwb\/command\//i)) {
		processCommandMessages(topic, message)
	} else if (topic.match(/^openwb\/optional\//i)) {
		processDisplayMessages(topic, message)
	}
	// else if ( mqttTopic.match( /^openwb\/config\/get\/sofort\/lp\//i) ) { processSofortConfigMessages(mqttTopic, message); }
}
function processCounterMessages(topic: string, message: string) {
	const elements = topic.split('/')
	const id = +elements[2]
	if (id == globalData.evuId) {
		processEvuMessages(topic, message)
	} else if (elements[3] == 'config') {
		// console.warn('Ignored counter config message')
	}
	if (elements[3] == 'get' && id in counters) {
		switch (elements[4]) {
			case 'power':
				counters[id].power = +message
				break
			case 'config':
				break
			case 'fault_str':
				break
			case 'fault_state':
				break
			case 'power_factors':
				break
			case 'imported':
				break
			case 'exported':
				break
			case 'frequency':
				break
			case 'daily_imported':
				counters[id].energy_imported = +message
				break
			case 'daily_exported':
				counters[id].energy_exported = +message
				break
			default:
			// console.warn('Ignored COUNTER message: ' + topic)
		}
	}
}
function processGlobalCounterMessages(topic: string, message: string) {
	if (topic.match(/^openwb\/counter\/get\/hierarchy$/i)) {
		const hierarchy = JSON.parse(message)
		if (hierarchy.length) {
			resetChargePoints()
			resetBatteries()

			for (const element of hierarchy) {
				if (element.type == 'counter') {
					globalData.evuId = element.id
				}
			}
			processHierarchy(hierarchy[0])
		}
	} else if (topic.match(/^openwb\/counter\/set\/home_consumption$/i)) {
		usageSummary.house.power = +message
	} else if (
		topic.match(/^openwb\/counter\/set\/daily_yield_home_consumption$/i)
	) {
		usageSummary.house.energy = +message
	} else {
		// console.warn('Ignored GLOBAL COUNTER message: ' + topic)
	}
}
function processHierarchy(hierarchy: Hierarchy) {
	switch (hierarchy.type) {
		case 'counter':
			// console.info('counter in hierachy: ' + hierarchy.id)
			addCounter(hierarchy.id, hierarchy.type)
			break
		case 'cp':
			addChargePoint(hierarchy.id)
			break
		case 'bat':
			addBattery(hierarchy.id)
			break
		case 'inverter':
			// addInverter (todo)
			// console.info('inverter id ' + hierarchy.id)
			break
		default:
		// console.warn('Ignored Hierarchy type: ' + hierarchy.type)
	}

	// recursively process the hierarchy
	hierarchy.children.forEach((element) => processHierarchy(element))
}

function processPvMessages(topic: string, message: string) {
	switch (topic) {
		case 'openWB/pv/get/power':
			sourceSummary.pv.power = -message
			break
		case 'openWB/pv/get/daily_exported':
			sourceSummary.pv.energy = +message
			break
		default:
		// console.warn('Ignored PV msg: [' + topic + '] ' + message)
	}
}

function processPvConfigMessages(topic: string, message: string) {
	const elements = topic.split('/')
	if (elements.length > 0) {
		switch (elements[4]) {
			case 'bat_mode':
				globalData.updatePvBatteryPriority(JSON.parse(message))
				break
			default:
			// console.warn('Ignored PV CONFIG msg: [' + topic + '] ' + message)
		}
	}
}

function processEvuMessages(topic: string, message: string) {
	const elements = topic.split('/')
	switch (elements[4]) {
		case 'power':
			if (+message > 0) {
				sourceSummary.evuIn.power = +message
				usageSummary.evuOut.power = 0
			} else {
				sourceSummary.evuIn.power = 0
				usageSummary.evuOut.power = -message
			}
			break
		case 'daily_imported':
			sourceSummary.evuIn.energy = +message
			break
		case 'daily_exported':
			usageSummary.evuOut.energy = +message
			break
		default:
	}
}
function processSystemMessages(topic: string, message: string) {
	if (
		topic.match(/^openWB\/system\/device\/[0-9]+\/component\/[0-9]+\/config$/i)
	) {
		const config = JSON.parse(message)
		if (config.type == 'counter') {
			counters[config.id].name = config.name
		}
	} else if (topic.match(/^openWB\/system\/ip_address$/i)) {
		globalData.ipAddress = JSON.parse(message)
	} else if (topic.match(/^openWB\/system\/time$/i)) {
		globalData.systemTime = JSON.parse(message)
	} else if (topic.match(/^openWB\/system\/version$/i)) {
		globalData.version = JSON.parse(message)
	} else if (topic.match(/^openWB\/system\/current_commit$/i)) {
		globalData.versionDetails = JSON.parse(message)
	} else if (topic.match(/^openWB\/system\/current_branch$/i)) {
		globalData.devBranch = JSON.parse(message)
	}
}
function processCommandMessages(topic: string, message: string) {
	const tokens = topic.split('/')
	if (topic.match(/^openWB\/command\/[a-z]+\/error$/i)) {
		if (tokens[2] == mqttClientId()) {
			const err = JSON.parse(message)
			console.error(
				`Error message from openWB: \nCommand: ${err.command}\nData: JSON.stringify(err.data)\nError:\n ${err.error}`,
			)
		}
	}
}
function processDisplayMessages(topic: string, message: string) {
	if (topic.match(/^openwb\/optional\/int_display\/active$/i)) {
		displayConfig.active = JSON.parse(message)
	} else if (
		topic.match(/^openwb\/optional\/int_display\/only_local_charge_points$/i)
	) {
		displayConfig.localCpOnly = JSON.parse(message)
	} else if (topic.match(/^openwb\/optional\/int_display\/theme$/i)) {
		const config = JSON.parse(message)
		displayConfig.usePin = config.configuration.lock_changes
		displayConfig.code = config.configuration.lock_changes_code
	}
}

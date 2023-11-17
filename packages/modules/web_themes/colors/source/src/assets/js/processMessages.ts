import { mqttRegister, mqttSubscribe } from './mqttClient'
import type { Hierarchy } from './types'
import {
	correctHouseConsumption,
	globalData,
	sourceSummary,
	usageSummary,
} from './model'
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
]
export function msgInit() {
	mqttRegister(processMqttMessage)
	topicsToSubscribe.forEach((topic) => {
		mqttSubscribe(topic)
	})
	initGraph()
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
	//else if (topic.match(/^openwb\/system\//i)) {
	//	processSystemMessages(topic, message)
	//}  else if ( mqttTopic.match( /^openwb\/verbraucher\//i) ) { processVerbraucherMessages(mqttTopic, message); }
	// else if ( mqttTopic.match( /^openwb\/hook\//i) ) { processHookMessages(mqttTopic, message); }
	// else if ( mqttTopic.match( /^openwb\/SmartHome\/Devices\//i) ) { processSmartHomeDevicesMessages(mqttTopic, message); }
	else if (topic.match(/^openwb\/LegacySmartHome\//i)) {
		processSmarthomeMessages(topic, message)
	}
	// else if ( mqttTopic.match( /^openwb\/config\/get\/sofort\/lp\//i) ) { processSofortConfigMessages(mqttTopic, message); }
}
function processCounterMessages(topic: string, message: string) {
	const elements = topic.split('/')
	if (+elements[2] == globalData.evuId) {
		processEvuMessages(topic, message)
	} else if (elements[3] == 'config') {
		// console.warn('Ignored counter config message')
	} else {
		switch (elements[4]) {
			case 'power':
			case 'config':
			case 'fault_str':
			case 'fault_state':
			case 'power_factors':
			case 'imported':
			case 'exported':
			case 'frequency':
			case 'daily_yield_import':
			case 'daily_yield_export':
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
					// console.info('EVU counter is ' + globalData.evuId)
				}
			}
			processHierarchy(hierarchy[0])
		}
	} else if (topic.match(/^openwb\/counter\/set\/home_consumption$/i)) {
		usageSummary.house.power = +message
		correctHouseConsumption()
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
			case 'bat_prio':
				globalData.updatePvBatteryPriority(message == 'true')
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

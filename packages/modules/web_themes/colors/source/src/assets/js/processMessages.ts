import { mqttRegister, mqttSubscribe, mqttUnsubscribe } from './mqttClient'
import { PvSystem, type Hierarchy } from './types'
import { addPvSystem, registry, globalData, pvSystems } from './model'
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
import {
	addBattery,
	batteries,
	resetBatteries,
} from '@/components/batteryList/model'
import {
	processChargepointMessages,
	processVehicleMessages,
	processVehicleTemplateMessages,
} from '@/components/chargePointList/processMessages'
import { processSmarthomeMessages } from '@/components/smartHome/processMessages'
import {
	addCounter,
	counters,
	updateCounterSummary,
} from '@/components/counterList/model'
import { mqttClientId } from './mqttClient'
import { add } from '@/components/mqttViewer/model'
import { globalConfig } from './themeConfig'

const topicsToSubscribe = [
	'openWB/counter/#',
	'openWB/bat/#',
	'openWB/pv/#',
	'openWB/chargepoint/#',
	'openWB/vehicle/#',
	'openWB/general/chargemode_config/pv_charging/#',
	'openWB/optional/et/#',
	'openWB/system/#',
	'openWB/LegacySmartHome/#',
	'openWB/command/' + mqttClientId() + '/#',
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
	add(topic, payload.toString())
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
	} else if (topic.match(/^openwb\/system\//i)) {
		processSystemMessages(topic, message)
	} else if (topic.match(/^openwb\/LegacySmartHome\//i)) {
		processSmarthomeMessages(topic, message)
	} else if (topic.match(/^openwb\/command\//i)) {
		processCommandMessages(topic, message)
	}
}
function processCounterMessages(topic: string, message: string) {
	const id = getIndex(topic)
	if (id != undefined) {
		if (id == globalData.evuId) {
			processEvuMessages(topic, message)
		} else if (!counters.has(id)) {
			console.warn('Invalid counter index: ' + id)
		} else if (topic.match(/^openWB\/counter\/[0-9]+\/get\/power$/i)) {
			counters.get(id)!.power = +message
			updateCounterSummary('power')
		} else if (topic.match(/^openWB\/counter\/[0-9]+\/get\/daily_imported$/i)) {
			counters.get(id)!.energy_imported = +message
			counters.get(id)!.now.energy = +message
		} else if (topic.match(/^openWB\/counter\/[0-9]+\/get\/daily_exported$/i)) {
			counters.get(id)!.energy_exported = +message
		} else {
			//console.info('Ignored COUNTER msg: [' + topic + '] ' + message)
		}
	}
}
function processGlobalCounterMessages(topic: string, message: string) {
	if (topic.match(/^openwb\/counter\/get\/hierarchy$/i)) {
		const hierarchy = JSON.parse(message)
		if (hierarchy.length) {
			resetChargePoints()
			resetBatteries()
			globalData.evuId = hierarchy[0].id
			processHierarchy(hierarchy[0])
		}
	} else if (topic.match(/^openwb\/counter\/set\/home_consumption$/i)) {
		registry.setPower('house', +message)
		// correctHouseConsumption()
	} else if (
		topic.match(/^openwb\/counter\/set\/daily_yield_home_consumption$/i)
	) {
		registry.setEnergy('house', +message)
	} else {
		// console.warn('Ignored GLOBAL COUNTER message: ' + topic)
	}
}
function processHierarchy(hierarchy: Hierarchy) {
	switch (hierarchy.type) {
		case 'counter':
			// console.info('counter in hierachy: ' + hierarchy.id)
			addCounter(hierarchy.id, hierarchy.type, hierarchy.id == globalData.evuId)
			if (globalConfig.countersToShow.includes(hierarchy.id)) {
				counters.get(hierarchy.id)!.showInGraph = true
			}
			break
		case 'cp':
			addChargePoint(hierarchy.id)
			break
		case 'bat':
			addBattery(hierarchy.id)
			break
		case 'inverter':
			addPvSystem(hierarchy.id)
			break
		default:
		// console.warn('Ignored Hierarchy type: ' + hierarchy.type)
	}

	// recursively process the hierarchy
	hierarchy.children.forEach((element) => processHierarchy(element))
}

function processPvMessages(topic: string, message: string) {
	const index = getIndex(topic)
	if (index && !pvSystems.value.has(index)) {
		console.warn('Invalid PV system index: ' + index)
		// addPvSystem(index)
	} else {
		if (topic == 'openWB/pv/get/power') {
			registry.setPower('pv', -message)
		} else if (topic == 'openWB/pv/get/daily_exported') {
			registry.setEnergy('pv', +message)
		} else if (topic.match(/^openWB\/pv\/[0-9]+\/get\/power$/i)) {
			pvSystems.value.get(index!)!.power = +message
		} else if (topic.match(/^openWB\/pv\/[0-9]+\/get\/daily_exported$/i)) {
			pvSystems.value.get(index!)!.now.energy = +message
		} else if (topic.match(/^openWB\/pv\/[0-9]+\/get\/monthly_exported$/i)) {
			pvSystems.value.get(index!)!.energy_month = +message
		} else if (topic.match(/^openWB\/pv\/[0-9]+\/get\/yearly_exported$/i)) {
			pvSystems.value.get(index!)!.energy_year = +message
		} else if (topic.match(/^openWB\/pv\/[0-9]+\/get\/exported$/i)) {
			pvSystems.value.get(index!)!.energy_total = +message
		} else {
			// console.warn('Ignored PV msg: [' + topic + '] ' + message)
		}
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
				registry.setPower('evuIn', +message)
				registry.setPower('evuOut', 0)
			} else {
				registry.setPower('evuIn', 0)
				registry.setPower('evuOut', -message)
			}
			break
		case 'daily_imported':
			registry.setEnergy('evuIn', +message)
			break
		case 'daily_exported':
			registry.setEnergy('evuOut', +message)
			break
		default:
	}
}

function processSystemMessages(topic: string, message: string) {
	if (
		topic.match(/^openWB\/system\/device\/[0-9]+\/component\/[0-9]+\/config$/i)
	) {
		const config = JSON.parse(message)
		switch (config.type) {
			case 'counter':
			case 'consumption_counter':
				if (counters.get(config.id)!) {
					counters.get(config.id)!.name = config.name
					counters.get(config.id)!.icon = config.name
				}
				break
			case 'inverter':
			case 'inverter_secondary':
				if (!pvSystems.value.has(config.id)) {
					pvSystems.value.set(config.id, new PvSystem(config.id))
				}
				pvSystems.value.get(config.id)!.name = config.name
				break
			case 'bat':
				if (!batteries.value.has(config.id)) {
					addBattery(config.id)
				}
				batteries.value.get(config.id)!.name = config.name
		}

		/* 	if (
			(config.type == 'counter' || config.type == 'consumption_counter') &&
			counters[config.id]
		) {
			counters[config.id].name = config.name
		} else if (config.type == 'inverter' ) {
			if (!pvSystems.value.has(config.id)) {
				pvSystems.value.set(config.id, new PvSystem(config.id))
			}
			pvSystems.value.get(config.id)!.name = config.name
		} else if (config.type == 'bat') {
			if (!batteries.value.has(config.id)) {
				addBattery(config.id)
			}
			batteries.value.get(config.id)!.name = config.name
		} */
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

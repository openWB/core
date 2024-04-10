import { masterData, usageSummary } from '@/assets/js/model'
import { shDevices, addShDevice } from './model'

export function processSmarthomeMessages(topic: string, message: string) {
	if (topic.match(/^openWB\/LegacySmarthome\/config\//i)) {
		processSmarthomeConfigMessages(topic, message)
	} else if (topic.match(/^openWB\/LegacySmarthome\/Devices\//i)) {
		processSmarthomeDeviceMessages(topic, message)
	} else {
		// console.warn('Ignored Smarthome status message: ' + topic)
	}
}

function processSmarthomeConfigMessages(topic: string, message: string) {
	const index = getIndex(topic)
	if (index == undefined) {
		// console.warn('Smarthome: Missing index in ' + topic)
		return
	}
	if (!(index in shDevices)) {
		// console.warn('Invalid sh device id received: ' + index)
		addShDevice(index)
	}
	if (
		topic.match(
			/^openWB\/LegacySmarthome\/config\/get\/Devices\/[0-9]+\/device_configured$/i,
		)
	) {
		shDevices[index].configured = message != '0'
	} else if (
		topic.match(
			/^openWB\/LegacySmarthome\/config\/get\/Devices\/[0-9]+\/device_name$/i,
		)
	) {
		shDevices[index].name = message.toString()
		shDevices[index].icon = message.toString()

		masterData['sh' + index].name = message.toString()
		masterData['sh' + index].icon = message.toString()
	} else if (
		topic.match(
			/^openWB\/LegacySmarthome\/config\/set\/Devices\/[0-9]+\/mode$/i,
		)
	) {
		shDevices[index].isAutomatic = message == '0'
	} else if (
		topic.match(
			/^openWB\/LegacySmarthome\/config\/get\/Devices\/[0-9]+\/device_canSwitch$/i,
		)
	) {
		shDevices[index].canSwitch = message == '1'
	} else if (
		topic.match(
			/^openWB\/LegacySmarthome\/config\/get\/Devices\/[0-9]+\/device_homeConsumtion$/i,
		)
	) {
		shDevices[index].countAsHouse = message == '1'
	} else if (
		topic.match(
			/^openWB\/LegacySmarthome\/config\/get\/Devices\/[0-9]+\/device_temperatur_configured$/i,
		)
	) {
		shDevices[index].tempConfigured = +message
	} else {
		// console.warn('Ignored Smarthome config message: ' + topic)
	}
}

function processSmarthomeDeviceMessages(topic: string, message: string) {
	const index = getIndex(topic)
	if (index == undefined) {
		console.warn('Smarthome: Missing index in ' + topic)
		return
	}
	if (!(index in shDevices)) {
		// console.warn('Invalid sh device id received: ' + index)
		addShDevice(index)
	}
	if (topic.match(/^openWB\/LegacySmarthome\/Devices\/[0-9]+\/Watt$/i)) {
		shDevices[index].power = +message
		updateShSummary('power')
	} else if (topic.match(/^openWB\/LegacySmarthome\/Devices\/[0-9]+\/Wh$/i)) {
		//shDevices[index].energy = +message
		//updateShSummary('energy')
	} else if (
		topic.match(/^openWB\/LegacySmarthome\/Devices\/[0-9]+\/RunningTimeToday$/i)
	) {
		shDevices[index].runningTime = +message
	} else if (
		topic.match(
			/^openWB\/LegacySmarthome\/Devices\/[0-9]+\/TemperatureSensor0$/i,
		)
	) {
		shDevices[index].temp[0] = +message
	} else if (
		topic.match(
			/^openWB\/LegacySmarthome\/Devices\/[0-9]+\/TemperatureSensor1$/i,
		)
	) {
		shDevices[index].temp[1] = +message
	} else if (
		topic.match(
			/^openWB\/LegacySmarthome\/Devices\/[0-9]+\/TemperatureSensor2$/i,
		)
	) {
		shDevices[index].temp[2] = +message
	} else if (
		topic.match(/^openWB\/LegacySmartHome\/Devices\/[0-9]+\/Status$/i)
	) {
		switch (+message) {
			case 10:
				shDevices[index].status = 'off'
				break
			case 11:
				shDevices[index].status = 'on'
				break
			case 20:
				shDevices[index].status = 'detection'
				break
			case 30:
				shDevices[index].status = 'timeout'
				break
			default:
				shDevices[index].status = 'off'
		}
	} else {
		// console.warn('Ignored Smarthome device message: ' + topic)
	}
}

function updateShSummary(cat: string) {
	switch (cat) {
		case 'power':
			usageSummary['devices'].power = Object.values(shDevices)
				.filter((dev) => dev.configured && !dev.countAsHouse)
				.reduce((sum, consumer) => sum + consumer.power, 0)
			break
		case 'energy':
			usageSummary['devices'].energy = Object.values(shDevices)
				.filter((dev) => dev.configured && !dev.countAsHouse)
				.reduce((sum, consumer) => sum + consumer.energy, 0)
			break
		default:
			console.error('Unknown category')
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
		console.warn('Parser error in getIndex for topic ' + topic)
	}
}

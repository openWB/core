import { registry } from '@/assets/js/model'
import { consumers, addConsumer } from './model'
import { updateShSummary } from '../smartHome/processMessages'

// Process incoming messages for consumers based on the topic
export function processConsumerMessages(topic: string, message: string) {
	if (topic.match(/^openWB\/consumer\/[0-9]+\//i)) {
		processConsumerDeviceMessages(topic, message)
	} else {
		processConsumerGlobalMessages(topic, message)
	}
}

// Consumers device messages
function processConsumerDeviceMessages(topic: string, message: string) {
	const index = getIndex(topic)
	if (index == undefined) {
		console.warn('Consumer: Missing index in ' + topic)
		return
	}
	if (!consumers.has(index)) {
		console.warn('Invalid consumer id received: ' + index)
	}
	const dev = consumers.get(index)!
	if (topic.match(/^openWB\/consumer\/[0-9]+\/get\/power$/i)) {
		dev.power = +message
	} else if (topic.match(/^openWB\/consumer\/[0-9]+\/get\/daily_imported$/i)) {
		dev.now.energy = +message
	} else if (topic.match(/^openWB\/consumer\/[0-9]+\/module$/i)) {
		// the message is a string in JSON. Create an object from it and update the device properties accordingly
		try {
			const moduleData = JSON.parse(message)
			if (moduleData) {
				console.log(
					'Consumer module data for consumer ' +
						index +
						' received: ' +
						JSON.stringify(moduleData),
				)
				dev.name = moduleData.name
				dev.icon = moduleData.name
			}
		} catch (e) {
			console.warn('Error parsing consumer module data: ' + e)
		}
	} else if (topic.match(/^openWB\/consumer\/[0-9]+\/set\/on_time$/i)) {
		dev.runningTime = +message
	} else if (topic.match(/^openWB\/consumer\/[0-9]+\/usage$/i)) {
		try {
			const usage = JSON.parse(message)
			if (usage) {
				console.log(
					'Consumer usage data for consumer ' +
						index +
						' received: ' +
						JSON.stringify(usage),
				)
				dev.usage = usage
			}
		} catch (e) {
			console.warn('Error parsing consumer usage data: ' + e)
		}
	} else if (topic.match(/^openWB\/consumer\/[0-9]+\/get\/state_str$/i)) {
		dev.statusText = JSON.parse(message)
	} else if (topic.match(/^openWB\/consumer\/[0-9]+\/get\/fault_state$/i)) {
		dev.faultState = JSON.parse(message)
	} else if (topic.match(/^openWB\/consumer\/[0-9]+\/get\/fault_str$/i)) {
		dev.faultText = JSON.parse(message)
	}
}

// Consumers global messages
function processConsumerGlobalMessages(topic: string, message: string) {
	if (topic.match(/^openWB\/consumer\/get\/daily_imported$/i)) {
		registry.setEnergy('consumers', +message)
	} else if (topic.match(/^openWB\/consumer\/get\/power$/i)) {
		registry.setPower('consumers', +message)
		updateShSummary('power')
	}
}

// Helper function to extract the index from the topic string
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

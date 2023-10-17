import { mqttRegister, mqttSubscribe } from './mqttClient'
import { add } from './model'

const topicsToSubscribe = ['openWB/#']

export function msgInit() {
	mqttRegister(processMqttMessage)
	topicsToSubscribe.forEach((topic) => {
		mqttSubscribe(topic)
	})
}
function processMqttMessage(topic: string, message: Buffer) {
	add(topic, message.toString())
}

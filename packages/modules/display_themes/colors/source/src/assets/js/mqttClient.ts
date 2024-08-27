/*
 * mqttClient.ts
 * colors theme for openwb 2.0
 * Copyright (c) 2022 Claus Hagen
 */

// functions to interact with MQTT

import mqtt from 'mqtt'
import { type QoS } from 'mqtt-packet'

const defaultQoS: QoS = 0
const mqttConnection = {
	host: location.hostname,
	port: location.protocol == 'https:' ? 443 : 80,
	endpoint: '/ws',
	protocol: (location.protocol == 'https:' ? 'wss' : 'ws') as mqtt.MqttProtocol,
	connectTimeout: 4000,
	reconnectPeriod: 4000,
	clean: false,
	clientId: Math.random()
		.toString(36)
		.replace(/[^a-z]+/g, '')
		.substring(0, 6),
}
const subscription = {
	topic: '',
	qos: defaultQoS,
}
let client: mqtt.MqttClient
const { host, port, endpoint, ...options } = mqttConnection
const connectUrl = `${options.protocol}://${host}:${port}${endpoint}`
try {
	client = mqtt.connect(connectUrl, options)
	client.on('connect', () => {
		console.info('MQTT connection successful.')
	})
	client.on('disconnect', () => {
		console.info('MQTT disconnected')
	})
	client.on('error', (error) => {
		console.error('MQTT connection failed: ', error)
	})
} catch (error) {
	console.error('MQTT connect error: ', error)
}

//}
// register a callback
export async function mqttRegister(callback: mqtt.OnMessageCallback) {
	await checkConnection()
	if (client) {
		client.on('message', callback)
	} else {
		console.error('MqttRegister: MQTT client not available')
	}
}
export async function mqttSubscribe(toTopic: string) {
	subscription.topic = toTopic
	const { topic, qos } = subscription

	await checkConnection()
	client.subscribe(topic, { qos }, (error) => {
		if (error) {
			console.error('MQTT Subscription error: ' + error)
			return
		}
	})
}
export function mqttUnsubscribe(fromTopic: string) {
	subscription.topic = fromTopic
	const { topic } = subscription
	client.unsubscribe(topic, (error: Error | undefined) => {
		if (error) {
			console.error('MQTT Unsubscribe from ' + fromTopic + ' failed: ' + error)
			return
		}
	})
}
export async function mqttPublish(topic: string, message: string) {
	const qos: QoS = 0
	let connected = client.connected
	let retries = 0
	while (!connected && retries < 10) {
		console.warn('MQTT not connected. Waiting 0.1 seconds')
		await delay(100)
		connected = client.connected
		retries += 1
	}
	// console.warn ('MQTT publish: Now connected')
	if (retries < 10) {
		try {
			client.publish(topic, message, { qos }, (error) => {
				if (error) {
					console.warn('MQTT publish error: ', error)
				}
				console.info(
					'MQTT publish: Message sent: [' + topic + '](' + message + ')',
				)
			})
		} catch (error) {
			console.warn('MQTT publish: caught error: ' + error)
		}
	} else {
		console.error(
			'MQTT publish: Lost connection to MQTT server. Please reload the page',
		)
	}
}
export function mqttClientId() {
	return mqttConnection.clientId
}

const MAX_RETRIES = 20
async function checkConnection(): Promise<boolean> {
	let connected = client.connected
	let retries = 0
	while (!connected && retries < MAX_RETRIES) {
		console.warn('MQTT not connected. Waiting 0.1 seconds')
		await delay(100)
		connected = client.connected
		retries += 1
	}
	return new Promise<boolean>((resolve, reject) => {
		if (retries < MAX_RETRIES) {
			resolve(true)
		} else {
			reject(false)
		}
	})
}
function delay(ms: number) {
	return new Promise((resolve) => setTimeout(resolve, ms))
}

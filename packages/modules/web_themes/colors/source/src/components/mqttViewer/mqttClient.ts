// functions to interact with MQTT
import {
	MqttClient,
	connect,
	type OnMessageCallback,
	type MqttProtocol,
} from 'mqtt'
import { type QoS } from 'mqtt-packet'

const defaultQoS: QoS = 0
const mqttConnection = {
	host: location.hostname,
	port: location.protocol == 'https:' ? 443 : 80,
	endpoint: '/ws',
	protocol: (location.protocol == 'https:' ? 'wss' : 'ws') as MqttProtocol,
	clean: true,
	connectTimeout: 4000,
	reconnectPeriod: 4000,
	clientId: Math.random()
		.toString(36)
		.replace(/[^a-z]+/g, '')
		.substring(0, 6),
	username: 'openWB',
	password: 'openWB',
}
const subscription = {
	topic: '',
	qos: defaultQoS,
}
let client: MqttClient

//export function MqttConnect(callback: (t: string, m: string) => void, topiclist: string[]) {
const { host, port, endpoint, ...options } = mqttConnection
const connectUrl = `${options.protocol}://${host}:${port}${endpoint}`
try {
	client = connect(connectUrl, options)
	client.on('connect', () => {
		console.info('MQTT connection successful')
		// topiclist.forEach((topic) => {
		//  subscribe(topic);
		// });
	})
	client.on('error', (error) => {
		console.error('MQTT connection failed: ', error)
	})
} catch (error) {
	console.error('MQTT connect error: ', error)
}

//}
export function mqttRegister(callback: OnMessageCallback) {
	if (client) {
		client.on('message', callback)
	} else {
		console.error('MqttRegister: MQTT client not available')
	}
}
export function mqttSubscribe(toTopic: string) {
	subscription.topic = toTopic
	const { topic, qos } = subscription
	client.subscribe(topic, { qos }, (error) => {
		if (error) {
			console.error('MQTT Subscription error: ' + error)
			return
		}
		console.info('MQTT Subscription successful: ' + toTopic)
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
		console.info('MQTT unsubscribe successful: ' + topic)
	})
}
export function mqttPublish(topic: string, message: string) {
	const qos: QoS = 0
	client.publish(topic, message, { qos }, (error) => {
		if (error) {
			console.warn('MQTT publish error: ', error)
		}
		console.info('Message sent: [' + topic + '](' + message + ')')
	})
}

/**
 * Functions to provide services for MQTT
 *
 * @author Kevin Wieland
 * @author Michael Ortenstein
 * @author Lutz Bender
 */

// these topics will be subscribed
// index 1 represents flag if value was received, needed for preloader progress bar
// if flags are preset with 1 they are not counted on reload and page will show even if topic was not received

// add topics here which should be subscribed before any other topics
var topicsToSubscribeFirst = [
	// check which devices are configured
	["openWB/LegacySmartHome/config/get/Devices/1/device_configured", 1],
	["openWB/LegacySmartHome/config/get/Devices/2/device_configured", 1],
	["openWB/LegacySmartHome/config/get/Devices/3/device_configured", 1],
	["openWB/LegacySmartHome/config/get/Devices/4/device_configured", 1],
	["openWB/LegacySmartHome/config/get/Devices/5/device_configured", 1],
	["openWB/LegacySmartHome/config/get/Devices/6/device_configured", 1],
	["openWB/LegacySmartHome/config/get/Devices/7/device_configured", 1],
	["openWB/LegacySmartHome/config/get/Devices/8/device_configured", 1],
	["openWB/LegacySmartHome/config/get/Devices/9/device_configured", 1]
];

// add any other topics here
var topicsToSubscribe = [
	// data for all devices
	["openWB/LegacySmartHome/config/get/Devices/+/device_name", 1],
	["openWB/LegacySmartHome/config/set/Devices/+/mode", 1],
	["openWB/LegacySmartHome/Devices/+/Watt", 1],
	["openWB/LegacySmartHome/Devices/+/RunningTimeToday", 1],
	["openWB/LegacySmartHome/Devices/+/Status", 1],
	["openWB/LegacySmartHome/Devices/+/DailyYieldKwh", 1],
	["openWB/LegacySmartHome/Devices/+/TemperatureSensor0", 1],
	["openWB/LegacySmartHome/Devices/+/TemperatureSensor1", 1],
	["openWB/LegacySmartHome/Devices/+/TemperatureSensor2", 1],
];

// holds number of topics flagged 1 initially
var countTopicsNotForPreloader = topicsToSubscribeFirst.filter(row => row[1] === 1).length + topicsToSubscribe.filter(row => row[1] === 1).length;

var retries = 0;

//Connect Options
var isSSL = location.protocol == 'https:'
var port = parseInt(location.port) || (location.protocol == "https:" ? 443 : 80);

var options = {
	timeout: 5,
	useSSL: isSSL,
	//Gets Called if the connection has been established
	onSuccess: function () {
		retries = 0;
		topicsToSubscribeFirst.forEach((topic) => {
			client.subscribe(topic[0], { qos: 0 });
		});
		setTimeout(function () {
			topicsToSubscribe.forEach((topic) => {
				client.subscribe(topic[0], { qos: 0 });
			});
		}, 200);
	},
	//Gets Called if the connection could not be established
	onFailure: function (message) {
		setTimeout(function () { client.connect(options); }, 5000);
	}
};

var clientUid = Math.random().toString(36).replace(/[^a-z]+/g, "").substr(0, 5);
console.debug(`connecting to broker on ${location.hostname}:${port} as client "${clientUid}"`);
var client = new Messaging.Client(location.hostname, port, clientUid);

$(document).ready(function () {
	client.connect(options);
	timeOfLastMqttMessage = Date.now();
});

//Gets  called if the websocket/mqtt connection gets disconnected for any reason
client.onConnectionLost = function (responseObject) {
	client.connect(options);
};

//Gets called whenever you receive a message
client.onMessageArrived = function (message) {
	handleMessage(message.destinationName, message.payloadString);
};

//Creates a new Messaging.Message Object and sends it
function publish(payload, topic) {
	console.debug(`publishing message: ${topic} -> ${payload}`);
	if (topic != undefined) {
		var message = new Messaging.Message(JSON.stringify(payload));
		message.destinationName = topic;
		message.qos = 2;
		message.retained = true;
		client.send(message);
		var message = new Messaging.Message("local client uid: " + clientUid + " sent: " + topic);
		message.destinationName = "openWB/set/system/topicSender";
		message.qos = 2;
		message.retained = true;
		client.send(message);
	} else {
		console.error("not publishing message without topic!");
	}
}

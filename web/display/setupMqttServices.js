/**
 * Functions to provide services for MQTT
 *
 * @author Kevin Wieland
 * @author Michael Ortenstein
 */

// these topics will be subscribed
var topicsToSubscribe = {
	// system topics
	"openWB/system/version": false,
	"openWB/system/boot_done": false,
	"openWB/system/update_in_progress": false,
	"openWB/general/extern": false,
	"openWB/optional/int_display/theme": false,
	// "openWB/isss/parentWB": false,
	// "openWB/isss/parentCPlp1": false,
	// "openWB/isss/parentCPlp2": false,
};

var data = {};
var retries = 0;

//Connect Options
var isSSL = location.protocol == 'https:';
var port = parseInt(location.port) || (location.protocol == "https:" ? 443 : 80);

var options = {
	timeout: 5,
	useSSL: isSSL,
	//Gets Called if the connection has been established
	onSuccess: function () {
		console.debug("connected!");
		retries = 0;
		Object.keys(topicsToSubscribe).forEach((topic) => {
			client.subscribe(topic, { qos: 0 });
		});
	},
	//Gets Called if the connection could not be established
	onFailure: function (message) {
		console.error("error connecting to broker!");
		setTimeout(() => {
			client.connect(options);
		}, 5000);
	}
};

var client_uid = Math.random().toString(36).replace(/[^a-z]+/g, "").substring(0, 5);
console.debug(`connecting to broker on ${location.hostname}:${port} as client "${client_uid}"`);
var client = new Messaging.Client(location.hostname, port, client_uid);

console.debug("connecting...");
client.connect(options);
timeOfLastMqttMessage = Date.now();

//Gets  called if the websocket/mqtt connection gets disconnected for any reason
client.onConnectionLost = function (responseObject) {
	console.debug("reconnecting...");
	setTimeout(() => {
		client.connect(options);
	}, 2000);
};
//Gets called whenever you receive a message
client.onMessageArrived = function (message) {
	topicsToSubscribe[message.destinationName] = true;
	data[message.destinationName] = JSON.parse(message.payloadString);
	handleMessage(message.destinationName, message.payloadString);
};

//Creates a new Messaging.Message Object and sends it
function publish(payload, topic) {
	var message = new Messaging.Message(payload);
	message.destinationName = topic;
	message.qos = 2;
	message.retained = true;
	client.send(message);
	var message = new Messaging.Message("local client uid: " + client_uid + " sent: " + topic);
	message.destinationName = "openWB/set/system/topicSender";
	message.qos = 2;
	message.retained = true;
	client.send(message);
}

function allTopicsReceived() {
	var ready = true;
	Object.keys(topicsToSubscribe).forEach((topic) => {
		ready &= topicsToSubscribe[topic];
	});
	return ready;
}

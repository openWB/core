/**
 * Functions to provide services for MQTT
 */

// these topics will be subscribed
var topicsToSubscribe = {
	// system topics
	"openWB/system/version": false,
	"openWB/system/boot_done": false,
	"openWB/system/update_in_progress": false,
	"openWB/system/usage_terms_acknowledged": false,
	"openWB/general/extern": false,
	"openWB/general/web_theme": false,
}
var secondaryTopicsToSubscribe = {
	"openWB/internal_chargepoint/global_data": false,
	"openWB/internal_chargepoint/0/data/parent_cp": false,
	"openWB/internal_chargepoint/1/data/parent_cp": false,
};

var data = {};
var retries = 0;

// Connect Options
var isSSL = location.protocol == 'https:';
var port = parseInt(location.port) || (location.protocol == "https:" ? 443 : 80);

var options = {
	timeout: 5,
	useSSL: isSSL,
	// Gets Called if the connection has been established
	onSuccess: function () {
		console.debug("connected!");
		retries = 0;
		updateProgress();
		Object.keys(topicsToSubscribe).forEach((topic) => {
			client.subscribe(topic, { qos: 0 });
		});
		Object.keys(secondaryTopicsToSubscribe).forEach((topic) => {
			client.subscribe(topic, { qos: 0 });
		});
	},
	// Gets Called if the connection could not be established
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

// Gets called if the websocket/mqtt connection gets disconnected for any reason
client.onConnectionLost = function (responseObject) {
	console.debug("reconnecting...");
	setTimeout(() => {
		client.connect(options);
	}, 2000);
};

// Gets called whenever you receive a message
client.onMessageArrived = function (message) {
	if (message.destinationName.includes("/internal_chargepoint/")) {
		secondaryTopicsToSubscribe[message.destinationName] = true;
	} else {
		topicsToSubscribe[message.destinationName] = true;
	}
	data[message.destinationName] = JSON.parse(message.payloadString);
	updateProgress();
	handleMessage(message.destinationName, message.payloadString);
};

console.debug("connecting...");
client.connect(options);
timeOfLastMqttMessage = Date.now();

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

function totalTopicCount() {
	var counter = Object.keys(topicsToSubscribe).length;
	if (data["openWB/general/extern"] === true) {
		counter += Object.keys(secondaryTopicsToSubscribe).length;
	}
	return counter;
}

function missingTopics() {
	var counter = 0;
	Object.keys(topicsToSubscribe).forEach((topic) => {
		if (!topicsToSubscribe[topic]) {
			counter++;
		};
	});
	if (data["openWB/general/extern"] === true) {
		Object.keys(secondaryTopicsToSubscribe).forEach((topic) => {
			if (!secondaryTopicsToSubscribe[topic]) {
				counter++;
			};
		});
	}
	return counter;
}

function allTopicsReceived() {
	return (missingTopics() == 0);
}

function updateProgress() {
	document.getElementById("progress-value").style.width = `${(totalTopicCount() - missingTopics()) / totalTopicCount() * 100}%`;
}

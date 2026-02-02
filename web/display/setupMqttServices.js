/**
 * Functions to provide services for MQTT
 */

// these topics will be subscribed
var topicsToSubscribe = {
	// system topics
	"openWB/system/version": false,
	"openWB/system/boot_done": false,
	"openWB/system/update_in_progress": false,
	"openWB/general/extern": false,
}
var primaryTopicsToSubscribe = {
	"openWB/optional/int_display/theme": false,
	"openWB/optional/int_display/only_local_charge_points": false,
}
var secondaryTopicsToSubscribe = {
	"openWB/system/ip_address": false,
	"openWB/system/current_branch": false,
	"openWB/system/current_commit": false,
	"openWB/general/extern_display_mode": false,
	"openWB/internal_chargepoint/global_data": false,
	"openWB/internal_chargepoint/0/data/parent_cp": false,
	"openWB/internal_chargepoint/1/data/parent_cp": false,
};

var data = {};
var retries = 0;
var credentialsFetched = false;

// Connect Options
var connection = {
	protocol: location.protocol == "https:" ? "wss" : "ws",
	protocolVersion: 5,
	host: location.hostname,
	port: parseInt(location.port) || (location.protocol == "https:" ? 443 : 80),
	path: "/ws",
	connectTimeout: 4000,
	reconnectPeriod: 4000,
	resubscribe: true,
	properties: {
		requestResponseInformation: true,
		requestProblemInformation: true,
	},
};

function setCookie(cookieName, cookieValue, expireDays = 30, path = "/") {
	let currentDate = new Date();
	currentDate.setTime(currentDate.getTime() + (expireDays * 24 * 60 * 60 * 1000));
	const expires = "expires=" + currentDate.toUTCString();
	document.cookie = `${cookieName}=${encodeURIComponent(cookieValue)};${expires};path=${path}; SameSite=Lax; Secure`;
};

function deleteCookie(cookieName, path = "/") {
	setCookie(cookieName, "", -1, path);
}

// Connect string, and specify the connection method used through protocol
// ws not encrypted WebSocket connection
// wss encrypted WebSocket connection
const { protocol, host, port, path, ...options } = connection;
const connectUrl = `${protocol}://${host}:${port}${path}`;
addLog(`hostname: ${location.hostname}, port: ${port}`);
addLog("try to read stored credentials");
fetch("/openWB/runs/dynsec_helper/display.php")
	.then(response => {
		console.debug("ok?", response.ok, "status:", response.status);
		if (response.ok) {
			response.json()
				.then((credentials) => {
					setCookie("mqtt", `${credentials.username}:${credentials.password}`);
					credentialsFetched = true;
					addLog(`Using mqtt credentials from dynsec-storage: ${credentials.username} / ${credentials.password.charAt(0)}...`);
					if (credentials.username === "admin" && credentials.password === "openwb") {
						console.warn("Using default mqtt credentials!");
						addLog("Warnung: Es werden die Standard MQTT Anmeldedaten verwendet!", true);
					}
				});
		} else {
			console.debug("no credentials for client found, using anonymous mqtt connection");
			deleteCookie("mqtt");
			addLog(`Keine Anmeldedaten gefunden. ${location.hostname}`, true);
		}
	});
console.debug("connecting to broker:", connectUrl);
timeOfLastMqttMessage = Date.now();
client = mqtt.connect(connectUrl, options);

client.on("connect", (ack) => {
	console.debug("connected!", ack);
	retries = 0;
	updateProgress();
	Object.keys(topicsToSubscribe).forEach((topic) => {
		client.subscribe(topic, { qos: 0 });
	});
	Object.keys(primaryTopicsToSubscribe).forEach((topic) => {
		client.subscribe(topic, { qos: 0 });
	});
	Object.keys(secondaryTopicsToSubscribe).forEach((topic) => {
		client.subscribe(topic, { qos: 0 });
	});
});

client.on("error", (error) => {
	console.error("Connection failed", error);
	addLog("MQTT Verbindung fehlgeschlagen.");
	addLog("Lösche evtl. vorhandene Anmeldedaten und lade die Seite neu...");
	deleteCookie("mqtt");
	window.location.reload();
});

// Gets called whenever you receive a message
client.on("message", (topic, message) => {
	if (Object.keys(topicsToSubscribe).includes(topic)) {
		topicsToSubscribe[topic] = true;
	} else if (Object.keys(primaryTopicsToSubscribe).includes(topic)) {
		primaryTopicsToSubscribe[topic] = true;
	} else if (Object.keys(secondaryTopicsToSubscribe).includes(topic)) {
		secondaryTopicsToSubscribe[topic] = true;
	}
	data[topic] = JSON.parse(message);
	updateProgress();
	handleMessage(topic, message);
});

// Publishes a message to the broker
function publish(payload, topic) {
	client.publish(topic, payload, { qos: 2, retain: true });
	client.publish("openWB/set/system/topicSender", "local client uid: " + client_uid + " sent: " + topic, { qos: 2, retain: true });
}

function totalTopicCount() {
	var counter = Object.keys(topicsToSubscribe).length;
	if (data["openWB/general/extern"] === true) {
		counter += Object.keys(secondaryTopicsToSubscribe).length;
	} else {
		Object.keys(primaryTopicsToSubscribe).forEach((topic) => {
			counter += primaryTopicsToSubscribe[topic];
		});
	}
	return counter;
}

function missingTopics() {
	var counter = 0;
	Object.keys(topicsToSubscribe).forEach((topic) => {
		if (topicsToSubscribe[topic] === false) {
			counter++;
		};
	});
	if (data["openWB/general/extern"] === true) {
		Object.keys(secondaryTopicsToSubscribe).forEach((topic) => {
			if (secondaryTopicsToSubscribe[topic] === false) {
				counter++;
			};
		});
	} else {
		Object.keys(primaryTopicsToSubscribe).forEach((topic) => {
			if (primaryTopicsToSubscribe[topic] === false) {
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

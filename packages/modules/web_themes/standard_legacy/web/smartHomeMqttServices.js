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
var connection = {
	protocol: location.protocol == "https:" ? "wss" : "ws",
	protocolVersion: 5,
	host: location.hostname,
	port: parseInt(location.port) || (location.protocol == "https:" ? 443 : 80),
	path: "/ws",
	connectTimeout: 4000,
	reconnectPeriod: 4000,
	properties: {
		requestResponseInformation: true,
		requestProblemInformation: true,
	},
};

function getCookie(cookieName) {
	const name = cookieName + "=";
	const decodedCookies = decodeURIComponent(document.cookie);
	const cookieArray = decodedCookies.split(';');
	for (let cookie of cookieArray) {
		cookie = cookie.trim();
		if (cookie.indexOf(name) === 0) {
			return decodeURIComponent(cookie.substring(name.length, cookie.length));
		}
	}
	return null;
};

function setCookie(cookieName, cookieValue, expireDays = 30, path = "/") {
	let currentDate = new Date();
	currentDate.setTime(currentDate.getTime() + (expireDays * 24 * 60 * 60 * 1000));
	const expires = "expires=" + currentDate.toUTCString();
	document.cookie = `${cookieName}=${encodeURIComponent(cookieValue)};${expires};path=${path}; SameSite=Lax; Secure`;
}

function deleteCookie(cookieName, path = "/") {
	setCookie(cookieName, "", -1, path);
}

// For testing purposes only, set a test cookie
// setCookie("mqtt", "unknown:user");
// setCookie("mqtt", "koala:openwb");
// setCookie("mqtt", "admin:openwb");

// Connect string, and specify the connection method used through protocol
// ws not encrypted WebSocket connection
// wss encrypted WebSocket connection
const { protocol, host, port, path, ...options } = connection;
const connectUrl = `${protocol}://${host}:${port}${path}`;
// Check for default credentials
const [user, pass] = getCookie("mqtt")?.split(":") || [null, null];
if (!(user && pass)) {
	console.debug("Anonymous mqtt connection (no cookie set)");
}
if (protocol == "wss" && user && pass) {
	console.debug("Using mqtt credentials from cookie:", user, "/", pass);
	options.username = user;
	options.password = pass;
	if (user === "admin" && pass === "openwb") {
		console.warn("Using default mqtt credentials!");
	}
}
console.debug("connecting to broker:", connectUrl);
timeOfLastMqttMessage = Date.now();
client = mqtt.connect(connectUrl, options);

// Gets Called if the connection has been established
client.on("connect", (ack) => {
	console.debug("connected!", ack);
	retries = 0;
	topicsToSubscribeFirst.forEach((topic) => {
		client.subscribe(topic[0], { qos: 0 });
	});
	setTimeout(function () {
		topicsToSubscribe.forEach((topic) => {
			client.subscribe(topic[0], { qos: 0 }, (err) => {
				if (!err) {
					console.debug("subscribed to topic:", topic[0]);
				} else {
					console.error("could not subscribe to topic:", topic[0], err);
				}
			});
		});
	}, 200);
});

// Gets Called if the connection could not be established
client.on("error", (error) => {
	console.error("Connection failed", error);
	addLog("MQTT Verbindung fehlgeschlagen.");
});

//Gets called whenever you receive a message
client.on("message", (topic, message) => {
	handleMessage(topic, message.toString());
});

// Publishes a message to the broker
function publish(payload, topic) {
	console.debug(`publishing message: ${topic} -> ${payload}`);
	if (topic != undefined) {
		client.publish(topic, JSON.stringify(payload), { qos: 2, retain: true }, (err) => {
			if (err) {
				console.error("error publishing message:", err);
			}
		});
		client.publish("openWB/set/system/topicSender", "local client uid: " + clientUid + " sent: " + topic, { qos: 2, retain: true }, (err) => {
			if (err) {
				console.error("error publishing message:", err);
			}
		});
	} else {
		console.error("not publishing message without topic!");
	}
}

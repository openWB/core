/**
 * Functions to provide services for MQTT
 * topic set with array var topicsToSubscribe has to be loaded before
 *
 * @author Kevin Wieland
 * @author Michael Ortenstein
 */

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

// function setCookie(cookieName, cookieValue, expireDays = 30, path = "/") {
// 	let currentDate = new Date();
// 	currentDate.setTime(currentDate.getTime() + (expireDays * 24 * 60 * 60 * 1000));
// 	const expires = "expires=" + currentDate.toUTCString();
// 	document.cookie = `${cookieName}=${encodeURIComponent(cookieValue)};${expires};path=${path}; SameSite=Lax; Secure`;
// }

// function deleteCookie(cookieName, path = "/") {
// 	setCookie(cookieName, "", -1, path);
// }

// For testing purposes only, set a test cookie
// setCookie("mqtt", "unknown:user");
// setCookie("mqtt", "admin:openwb");

// Connect string, and specify the connection method used through protocol
// ws not encrypted WebSocket connection
// wss encrypted WebSocket connection
const { protocol, host, port, path, ...options } = connection;
const connectUrl = `${protocol}://${host}:${port}${path}`;
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
	topicsToSubscribe.forEach((topic) => {
		client.subscribe(topic[0], { qos: 0 });
	});
});

// Gets Called if the connection could not be established
client.on("error", (error) => {
	console.error("Connection failed", error);
});

// Gets called whenever you receive a message
client.on("message", (topic, message) => {
	// func processMessages defined in respective processAllMqttMsg_
	processMessages(topic, message);
});

// Publishes a message to the broker
function publish(payload, topic) {
	console.debug(`publishing message: ${topic} -> ${payload}`);
	if (topic != undefined) {
		client.publish(topic, payload, { qos: 2, retain: true }, (err) => {
			if (err) {
				console.error("error publishing message:", err);
			}
		});
	} else {
		console.error("not publishing message without topic!");
	}
}

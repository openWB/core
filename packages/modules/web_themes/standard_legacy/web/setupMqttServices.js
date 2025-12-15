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
	["openWB/general/web_theme", 0], // theme configuration
	["openWB/counter/get/hierarchy", 0] // hierarchy of all counters and charge points
];

// add any other topics here
var topicsToSubscribe = [
	// data for all charge points
	["openWB/chargepoint/get/power", 1], // total actual charging power; int, unit: Wh
	["openWB/chargepoint/get/daily_imported", 1], // total counted energy for charging; float, unit: kWh
	["openWB/chargepoint/get/daily_exported", 1], // total counted energy for discharging (V2G/V2H); float, unit: kWh

	// // pv topics
	["openWB/pv/config/configured", 1], // is a pv module configured? bool
	["openWB/pv/get/power", 1], // total actual power; negative int, unit: W
	["openWB/pv/get/daily_exported", 1], // total daily yield; float, unit: kWh

	// // house battery
	["openWB/bat/config/configured", 1], // is a battery module configured? bool
	["openWB/bat/get/power", 1], // total actual power; int, unit: W
	["openWB/bat/get/soc", 1], // total actual soc; int, unit: %, 0-100
	["openWB/bat/get/daily_exported", 1], // total daily imported energy; float, unit: kWh
	["openWB/bat/get/daily_imported", 1], // total daily imported energy; float, unit: kWh

	// counter topics
	["openWB/counter/set/home_consumption", 1], // actual home power
	["openWB/counter/set/daily_yield_home_consumption", 1], // daily home energy
	["openWB/counter/+/get/power", 1], // actual power; int, unit: W
	["openWB/counter/+/get/daily_imported", 1], // daily imported energy; float, unit: kWh
	["openWB/counter/+/get/daily_exported", 1], // daily exported energy; float, unit: kWh

	// charge point topics
	["openWB/chargepoint/+/config", 1], // chargepoint configuration; JSON { name: str, template: int, connected_phases: int, phase_1: int, auto_phase_switch_hardware: bool, control_pilot_interruption_hw: bool, connection_module: JSON { selected: str, config: JSON } }
	["openWB/chargepoint/+/get/state_str", 1], // information about actual state; str
	["openWB/chargepoint/+/get/fault_str", 1], // any error messages; str
	["openWB/chargepoint/+/get/fault_state", 1], // error state; int, 0 = ok, 1 = warning, 2 = error
	["openWB/chargepoint/+/set/log", 1], // log data: energy charged since the vehicle was plugged in; float, unit: kWh
	["openWB/chargepoint/+/get/power", 1], // actual charging power
	["openWB/chargepoint/+/get/phases_in_use", 1], // actual number of phases used while charging; int, 0-3
	["openWB/chargepoint/+/get/plug_state", 1], // state of plug; int, 0 = disconnected, 1 = connected
	["openWB/chargepoint/+/get/charge_state", 1], // state of charge; int, 0 = not charging, 1 = charging
	["openWB/chargepoint/+/set/manual_lock", 1], // is manual lock active? int, 0 = off, 1 = on
	["openWB/chargepoint/+/get/enabled", 1], // is the chargepoint enabled? int, 0 = disabled, 1 = enabled
	["openWB/chargepoint/+/set/current", 1], // actual set current; float, unit: A

	// devices and components
	["openWB/system/device/+/component/+/config", 1], // configuration of components

	// information for connected vehicle
	["openWB/chargepoint/+/get/connected_vehicle/info", 1], // general info of the vehicle; JSON { "id": int, "name": str }
	["openWB/chargepoint/+/get/connected_vehicle/config", 1], // general configuration of the vehicle; JSON { "charge_template": int, "ev_template": int, "chargemode": str, "priority": bool, "average_consumption": int (Wh/100km) }
	["openWB/chargepoint/+/get/connected_vehicle/soc", 1], // soc info of the vehicle; JSON {"soc": float (%), "range_charged": int, "range": float, "range_unit": str, "timestamp": int, "fault_stat": int, "fault_str": str }
	["openWB/chargepoint/+/set/charge_template", 1], // populate a list of charge templates
	["openWB/chargepoint/+/set/charge_template/chargemode/scheduled_charging/plans/+", 1], // populate a list of schedule plans
	["openWB/chargepoint/+/set/charge_template/time_charging/plans/+", 1], // populate a list of time charge plans

	// vehicle topics
	["openWB/vehicle/+/name", 1], // populate a list of vehicle id/name info
	["openWB/vehicle/+/soc_module/config", 1], // soc configuration of the vehicle; JSON { "type": text, "configuration": object }


	// charge mode config
	["openWB/general/chargemode_config/pv_charging/bat_mode", 0],

	// electricity tariff
	["openWB/optional/ep/configured", 1], // ep provider information
	["openWB/optional/ep/get/prices", 1], // current price list
	["openWB/optional/dc_charging", 1], // dc charging is configured

	// graph topics
	["openWB/graph/alllivevaluesJson1", 1],
	["openWB/graph/alllivevaluesJson2", 1],
	["openWB/graph/alllivevaluesJson3", 1],
	["openWB/graph/alllivevaluesJson4", 1],
	["openWB/graph/alllivevaluesJson5", 1],
	["openWB/graph/alllivevaluesJson6", 1],
	["openWB/graph/alllivevaluesJson7", 1],
	["openWB/graph/alllivevaluesJson8", 1],
	["openWB/graph/alllivevaluesJson9", 1],
	["openWB/graph/alllivevaluesJson10", 1],
	["openWB/graph/alllivevaluesJson11", 1],
	["openWB/graph/alllivevaluesJson12", 1],
	["openWB/graph/alllivevaluesJson13", 1],
	["openWB/graph/alllivevaluesJson14", 1],
	["openWB/graph/alllivevaluesJson15", 1],
	["openWB/graph/alllivevaluesJson16", 1],
	["openWB/graph/lastlivevaluesJson", 1],
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
	if (options.username) {
		addLog("Lösche evtl. vorhandene Anmeldedaten und lade die Seite neu...");
		deleteCookie("mqtt");
		location.reload();
	}
});

//Gets called whenever you receive a message
client.on("message", (topic, message) => {
	handleMessage(topic, message.toString());
});

//Creates a new Messaging.Message Object and sends it
function publish(payload, topic) {
	console.debug(`publishing message: ${topic} -> ${payload}`);
	if (topic != undefined) {
		client.send(message);
		client.publish(topic, JSON.stringify(payload), { qos: 2, retain: true }, (err) => {
			if (err) {
				console.error("error publishing message:", err);
			}
		});
	} else {
		console.error("not publishing message without topic!");
	}
}

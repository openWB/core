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

	// vehicle topics
	["openWB/vehicle/+/name", 1], // populate a list of vehicle id/name info
	["openWB/vehicle/+/soc_module/config", 1], // soc configuration of the vehicle; JSON { "type": text, "configuration": object }
	["openWB/vehicle/template/charge_template/+", 1], // populate a list of charge templates
	["openWB/vehicle/template/charge_template/+/chargemode/scheduled_charging/plans/+", 1], // populate a list of schedule plans
	["openWB/vehicle/template/charge_template/+/time_charging/plans/+", 1], // populate a list of time charge plans

	// charge mode config
	["openWB/general/chargemode_config/pv_charging/bat_mode", 0],

	// electricity tariff
	["openWB/optional/et/active", 1], // et provider is configured
	["openWB/optional/et/provider", 1], // et provider information
	["openWB/optional/et/get/prices", 1], // current price list
	["openWB/optional/dc_charging", 1], // dc charging is configured

	// graph topics
	["openWB/graph/config/duration", 1], // maximum duration to display in landing page
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

/**
 * Functions to provide services for MQTT
 *
 * @author Kevin Wieland
 * @author Michael Ortenstein
 */

// these topics will be subscribed
// index 1 represents flag if value was received, needed for preloaderbar progress
// if flags are preset with 1 they are not counted on reload and page will show even if topic was not received

// add topics here which should be subscribed bevore any other topics
var topicsToSubscribeFirst = [
	["openWB/counter/get/hierarchy", 0] // hierarchy of all counters and chargepoints
];

// add any other topics here
var topicsToSubscribe = [
	// data for all chargepoints
	["openWB/chargepoint/get/power_all", 1], // total actual charging power; int, unit: Wh
	["openWB/chargepoint/get/daily_imported_all", 1], // total counted energy for charging; float, unit: kWh
	["openWB/chargepoint/get/daily_exported_all", 1], // total counted energy for discharging (V2G/V2H); float, unit: kWh

	// // pv topics
	["openWB/pv/config/configured", 1], // is a pv module configured? bool
	["openWB/pv/get/power", 1], // total actual power; negative int, unit: W
	["openWB/pv/get/daily_yield", 1], // total daily yield; float, unit: kWh

	// // housebattery
	["openWB/bat/config/configured", 1], // is a battery module configured? bool
	["openWB/bat/get/power", 1], // total actual power; int, unit: W
	["openWB/bat/get/soc", 1], // total actual soc; int, unit: %, 0-100
	["openWB/bat/get/daily_yield_export", 1], // total daily imported energy; float, unit: kWh
	["openWB/bat/get/daily_yield_import", 1], // total daily imported energy; float, unit: kWh

	// counter topics, counter with index 0 is always main grid counter
	["openWB/counter/set/home_consumption", 1], // actual home power
	["openWB/counter/set/daily_energy_home_consumption", 1], // daily home energy
	["openWB/counter/0/get/power_all", 1], // actual power; int, unit: W
	["openWB/counter/0/get/daily_yield_import", 1], // daily imported energy; float, unit: kWh
	["openWB/counter/0/get/daily_yield_export", 1], // daily exported energy; float, unit: kWh

	// chargepoint topics
	["openWB/chargepoint/+/config", 1], // chargepoint configuration; JSON { name: str, template: int, connected_phases: int, phase_1: int, auto_phase_switch_hardware: bool, control_pilot_interruption_hw: bool, connection_module: JSON { selected: str, config: JSON } }
	["openWB/chargepoint/+/get/state_str", 1], // information about actual state; str
	["openWB/chargepoint/+/get/fault_str", 1], // any error messages; str
	["openWB/chargepoint/+/get/fault_state", 1], // error state; int, 0 = ok, 1 = warning, 2 = error
	["openWB/chargepoint/+/get/charged_since_plugged_counter", 1], // energy charged since the vehicle was plugged in; float, unit: kWh
	["openWB/chargepoint/+/get/power_all", 1], // actuel charging power
	["openWB/chargepoint/+/get/phases_in_use", 1], // actual number of phases used while charging; int, 0-3
	["openWB/chargepoint/+/get/plug_state", 1], // state of plug; int, 0 = disconnected, 1 = connected
	["openWB/chargepoint/+/get/charge_state", 1], // state of charge; int, 0 = not charging, 1 = charging
	["openWB/chargepoint/+/get/manual_lock", 1], // is manual lock active? int, 0 = off, 1 = on
	["openWB/chargepoint/+/get/enabled", 1], // is the chargepoint enabled? int, 0 = disabled, 1 = enabled
	["openWB/chargepoint/+/set/current", 1], // actual set current; float, unit: A

	// information for connected vehicle
	["openWB/chargepoint/+/get/connected_vehicle/info", 1], // general info of the vehicle; JSON { "id": int, "name": str }
	["openWB/chargepoint/+/get/connected_vehicle/config", 1], // general configuration of the vehicle; JSON { "charge_template": int, "ev_template": int, "chargemode": str, "priority": bool, "average_consumption": int (Wh/100km) }
	["openWB/chargepoint/+/get/connected_vehicle/soc", 1], // soc info of the vehicle; JSON {"soc": float (%), "range": int, "range_unit": str, "timestamp": int, "fault_stat": int, "fault_str": str }
	["openWB/chargepoint/+/get/connected_vehicle/soc_config", 1], // soc configuration of the vehicle; JSON { "configured": bool, "manual": bool }

	// vehicle topics
	["openWB/vehicle/+/name", 1], // populate a list of vehicle id/name info
	["openWB/vehicle/template/charge_template/+", 1], // populate a list of charge templates

	// chargemode config
	["openWB/general/chargemode_config/pv_charging/bat_prio", 0],

	// electricity tariff
	["openWB/optional/et/active", 1], // et provider is configured
	["openWB/optional/et/provider", 1], // et privider name
	["openWB/optional/et/get/price", 1], // current price
	["openWB/optional/et/config/max_price", 1], // configured max price

	// graph topcis
	["openWB/graph/config/duration", 1], // maximum duration to display in landing page
	["openWB/graph/boolDisplayLp1", 1],
	["openWB/graph/boolDisplayLp2", 1],
	["openWB/graph/boolDisplayLp3", 1],
	["openWB/graph/boolDisplayLp4", 1],
	["openWB/graph/boolDisplayLp5", 1],
	["openWB/graph/boolDisplayLp6", 1],
	["openWB/graph/boolDisplayLp7", 1],
	["openWB/graph/boolDisplayLp8", 1],
	["openWB/graph/boolDisplayHouseConsumption", 1],
	["openWB/graph/boolDisplayLoad1", 1],
	["openWB/graph/boolDisplayLoad2", 1],
	["openWB/graph/boolDisplayLp1Soc", 1],
	["openWB/graph/boolDisplayLp2Soc", 1],
	["openWB/graph/boolDisplayLpAll", 1],
	["openWB/graph/boolDisplaySpeicherSoc", 1],
	["openWB/graph/boolDisplaySpeicher", 1],
	["openWB/graph/boolDisplayEvu", 1],
	["openWB/graph/boolDisplayLegend", 1],
	["openWB/graph/boolDisplayLiveGraph", 1],
	["openWB/graph/boolDisplayPv", 1],
	// ["openWB/graph/1alllivevalues", 1],
	// ["openWB/graph/2alllivevalues", 1],
	// ["openWB/graph/3alllivevalues", 1],
	// ["openWB/graph/4alllivevalues", 1],
	// ["openWB/graph/5alllivevalues", 1],
	// ["openWB/graph/6alllivevalues", 1],
	// ["openWB/graph/7alllivevalues", 1],
	// ["openWB/graph/8alllivevalues", 1],
	// ["openWB/graph/9alllivevalues", 1],
	// ["openWB/graph/10alllivevalues", 1],
	// ["openWB/graph/11alllivevalues", 1],
	// ["openWB/graph/12alllivevalues", 1],
	// ["openWB/graph/13alllivevalues", 1],
	// ["openWB/graph/14alllivevalues", 1],
	// ["openWB/graph/15alllivevalues", 1],
	// ["openWB/graph/16alllivevalues", 1],
	// ["openWB/graph/lastlivevalues", 1],
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

	// // hook Konfiguration
	// ["openWB/hook/1/boolHookConfigured", 0],
	// ["openWB/hook/2/boolHookConfigured", 0],
	// ["openWB/hook/3/boolHookConfigured", 0],
	// // verbraucher Konfiguration
	// ["openWB/Verbraucher/1/Configured", 0],
	// ["openWB/Verbraucher/1/Name", 1],
	// ["openWB/Verbraucher/1/Watt", 1],
	// ["openWB/Verbraucher/1/DailyYieldImportkWh", 1],
	// ["openWB/Verbraucher/2/Configured", 0],
	// ["openWB/Verbraucher/2/Name", 1],
	// ["openWB/Verbraucher/2/Watt", 1],
	// ["openWB/Verbraucher/2/DailyYieldImportkWh", 1],

	// // global topics
	// ["openWB/global/strLastmanagementActive", 1],

	// ["openWB/config/get/pv/minCurrentMinPv", 1],
	// // system topics
	// ["openWB/system/Timestamp", 1],

	// // geladene kWh seit anstecken des EV
	// // geladene kWh seit Reset Lademengenbegrenzung
	// ["openWB/lp/1/kWhActualCharged", 1],
	// ["openWB/lp/2/kWhActualCharged", 1],
	// ["openWB/lp/3/kWhActualCharged", 1],
	// ["openWB/lp/4/kWhActualCharged", 1],
	// ["openWB/lp/5/kWhActualCharged", 1],
	// ["openWB/lp/6/kWhActualCharged", 1],
	// ["openWB/lp/7/kWhActualCharged", 1],
	// ["openWB/lp/8/kWhActualCharged", 1],
	// // Status Nachtladen
	// ["openWB/lp/1/boolChargeAtNight", 1],
	// ["openWB/lp/2/boolChargeAtNight", 1],
	// // Restzeit
	// ["openWB/lp/1/TimeRemaining", 1],
	// ["openWB/lp/2/TimeRemaining", 1],
	// ["openWB/lp/3/TimeRemaining", 1],
	// ["openWB/lp/4/TimeRemaining", 1],
	// ["openWB/lp/5/TimeRemaining", 1],
	// ["openWB/lp/6/TimeRemaining", 1],
	// ["openWB/lp/7/TimeRemaining", 1],
	// ["openWB/lp/8/TimeRemaining", 1],

	// ["openWB/lp/1/boolDirectChargeMode_none_kwh_soc", 1],
	// ["openWB/lp/2/boolDirectChargeMode_none_kwh_soc", 1],
	// ["openWB/lp/3/boolDirectChargeMode_none_kwh_soc", 1],
	// ["openWB/lp/4/boolDirectChargeMode_none_kwh_soc", 1],
	// ["openWB/lp/5/boolDirectChargeMode_none_kwh_soc", 1],
	// ["openWB/lp/6/boolDirectChargeMode_none_kwh_soc", 1],
	// ["openWB/lp/7/boolDirectChargeMode_none_kwh_soc", 1],
	// ["openWB/lp/8/boolDirectChargeMode_none_kwh_soc", 1],
	//
	// // Status Autolock konfiguriert
	// ["openWB/lp/1/AutolockConfigured", 1],
	// ["openWB/lp/2/AutolockConfigured", 1],
	// ["openWB/lp/3/AutolockConfigured", 1],
	// ["openWB/lp/4/AutolockConfigured", 1],
	// ["openWB/lp/5/AutolockConfigured", 1],
	// ["openWB/lp/6/AutolockConfigured", 1],
	// ["openWB/lp/7/AutolockConfigured", 1],
	// ["openWB/lp/8/AutolockConfigured", 1],
	// // Status Autolock
	// ["openWB/lp/1/AutolockStatus", 1],
	// ["openWB/lp/2/AutolockStatus", 1],
	// ["openWB/lp/3/AutolockStatus", 1],
	// ["openWB/lp/4/AutolockStatus", 1],
	// ["openWB/lp/5/AutolockStatus", 1],
	// ["openWB/lp/6/AutolockStatus", 1],
	// ["openWB/lp/7/AutolockStatus", 1],
	// ["openWB/lp/8/AutolockStatus", 1],
	// ["openWB/lp/1/ADirectModeAmps", 1],
	// ["openWB/lp/2/ADirectModeAmps", 1],
	// ["openWB/lp/3/ADirectModeAmps", 1],
	// ["openWB/lp/4/ADirectModeAmps", 1],
	// ["openWB/lp/5/ADirectModeAmps", 1],
	// ["openWB/lp/6/ADirectModeAmps", 1],
	// ["openWB/lp/7/ADirectModeAmps", 1],
	// ["openWB/lp/8/ADirectModeAmps", 1],
	// // Zielladen
	// ["openWB/lp/1/boolFinishAtTimeChargeActive", 1],

	// // hook status
	// ["openWB/hook/1/boolHookStatus", 1],
	// ["openWB/hook/2/boolHookStatus", 1],
	// ["openWB/hook/3/boolHookStatus", 1],

	// // Config Vars Sofort current
	// ["openWB/config/get/sofort/lp/1/current", 1],
	// ["openWB/config/get/sofort/lp/2/current", 1],
	// ["openWB/config/get/sofort/lp/3/current", 1],
	// ["openWB/config/get/sofort/lp/4/current", 1],
	// ["openWB/config/get/sofort/lp/5/current", 1],
	// ["openWB/config/get/sofort/lp/6/current", 1],
	// ["openWB/config/get/sofort/lp/7/current", 1],
	// ["openWB/config/get/sofort/lp/8/current", 1],
	// ["openWB/config/get/sofort/lp/1/chargeLimitation", 1],
	// ["openWB/config/get/sofort/lp/2/chargeLimitation", 1],
	// ["openWB/config/get/sofort/lp/3/chargeLimitation", 1],
	// ["openWB/config/get/sofort/lp/4/chargeLimitation", 1],
	// ["openWB/config/get/sofort/lp/5/chargeLimitation", 1],
	// ["openWB/config/get/sofort/lp/6/chargeLimitation", 1],
	// ["openWB/config/get/sofort/lp/7/chargeLimitation", 1],
	// ["openWB/config/get/sofort/lp/8/chargeLimitation", 1],
	// ["openWB/config/get/sofort/lp/1/energyToCharge", 1],
	// ["openWB/config/get/sofort/lp/2/energyToCharge", 1],
	// ["openWB/config/get/sofort/lp/3/energyToCharge", 1],
	// ["openWB/config/get/sofort/lp/4/energyToCharge", 1],
	// ["openWB/config/get/sofort/lp/5/energyToCharge", 1],
	// ["openWB/config/get/sofort/lp/6/energyToCharge", 1],
	// ["openWB/config/get/sofort/lp/7/energyToCharge", 1],
	// ["openWB/config/get/sofort/lp/8/energyToCharge", 1],
	// ["openWB/config/get/sofort/lp/1/socToChargeTo", 1],
	// ["openWB/config/get/sofort/lp/2/socToChargeTo", 1],

	// ["openWB/pv/bool70PVDynStatus", 1],
	// ["openWB/config/get/pv/nurpv70dynact", 1]
];

// holds number of topics flagged 1 initially
var countTopicsNotForPreloader = topicsToSubscribeFirst.filter(row => row[1] === 1).length + topicsToSubscribe.filter(row => row[1] === 1).length;

var retries = 0;

//Connect Options
var isSSL = location.protocol == 'https:'
var options = {
	timeout: 5,
	useSSL: isSSL,
	//Gets Called if the connection has sucessfully been established
	onSuccess: function() {
		retries = 0;
		topicsToSubscribeFirst.forEach((topic) => {
			client.subscribe(topic[0], { qos: 0 });
		});
		setTimeout(function() {
			topicsToSubscribe.forEach((topic) => {
				client.subscribe(topic[0], { qos: 0 });
			});
		}, 200);
	},
	//Gets Called if the connection could not be established
	onFailure: function(message) {
		setTimeout(function() { client.connect(options); }, 5000);
	}
};

var clientuid = Math.random().toString(36).replace(/[^a-z]+/g, "").substr(0, 5);
var client = new Messaging.Client(location.hostname, 9001, clientuid);

$(document).ready(function() {
	client.connect(options);
	timeOfLastMqttMessage = Date.now();
});

//Gets  called if the websocket/mqtt connection gets disconnected for any reason
client.onConnectionLost = function(responseObject) {
	client.connect(options);
};

//Gets called whenever you receive a message
client.onMessageArrived = function(message) {
	handlevar(message.destinationName, message.payloadString);
};

//Creates a new Messaging.Message Object and sends it
function publish(payload, topic) {
	console.log("publish: " + topic + ": " + payload);
	if (topic != undefined) {
		var message = new Messaging.Message(JSON.stringify(payload));
		message.destinationName = topic;
		message.qos = 2;
		message.retained = true;
		client.send(message);
		var message = new Messaging.Message("local client uid: " + clientuid + " sent: " + topic);
		message.destinationName = "openWB/set/system/topicSender";
		message.qos = 2;
		message.retained = true;
		client.send(message);
	} else {
		console.log("not publishing message without topic!");
	}
}

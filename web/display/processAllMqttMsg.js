/**
 * Functions to update graph and gui values via MQTT-messages
 *
 * @author Kevin Wieland
 * @author Michael Ortenstein
 * @author Lutz Bender
 */

function reloadDisplay() {
	/** @function reloadDisplay
	 * triggers a reload of the current page
	 */
	// wait some seconds to allow other instances receive this message
	setTimeout(() => {
		publish("0", "openWB/set/system/reloadDisplay");
		// wait again to give the broker some time and avoid a reload loop
		setTimeout(() => {
			location.reload();
		}, 2000);
	}, 2000);
}

function setIframeSource(host) {
	if (allTopicsReceived()) {
		if (!data["openWB/system/boot_done"]) {
			addLog("backend still booting");
			return;
		}
		if (data["openWB/system/update_in_progress"]) {
			addLog("update in progress");
			return;
		}
		const host = location.host;
		var query = "";
		if (data["openWB/general/extern"]) {
			host = data["openWB/isss/parentWB"];
			query += `?parentCPlp1=${data["openWB/isss/parentCPlp1"]}`;
			query += `&parentCPlp2=${data["openWB/isss/parentCPlp2"]}`;
		}
		const theme = data["openWB/optional/int_display/theme"];
		const destination = `http://${host}/openWB/web/display/themes/${theme}/${query}`;
		const iframe = document.getElementById("displayTarget");
		if (destination != iframe.src) {
			addLog(`all done, starting theme '${theme}'`);
			setTimeout(() => {
				document.getElementById("notReady").classList.add("hide");
				iframe.src = destination;
				iframe.classList.remove("hide");
			}, 2000);
		}
	} else {
		console.debug("some topics still missing");
	}
}

function addLog(message) {
	document.getElementById("log").innerText += message + "\n";
}

function handleMessage(topic, payload) {
	addLog(`Topic: ${topic} Payload: ${payload}`);
	// receives all topics and calls respective function to process them
	if (topic.match(/^openwb\/system\//i)) { processSystemTopics(topic, payload); }
	setIframeSource(location.host);
}  // end handleMessage

function processSystemTopics(topic, payload) {
	// processes topic for topic openWB/system
	// called by handleMessage
	if (topic == 'openWB/system/reloadDisplay') {
		if (payload == '1') {
			reloadDisplay();
		}
	}
}

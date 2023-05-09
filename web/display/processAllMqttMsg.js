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

function setIframeSource() {
	if (allTopicsReceived()) {
		const startup = document.querySelector("#notReady");
		const iframe = document.querySelector("#displayTarget");
		if (!data["openWB/system/boot_done"]) {
			addLog("backend still booting");
			startup.classList.remove("hide");
			iframe.classList.add("hide");
			return;
		}
		if (data["openWB/system/update_in_progress"]) {
			addLog("update in progress");
			startup.classList.remove("hide");
			iframe.classList.add("hide");
			return;
		}
		let host = location.host;
		var query = "";
		if (data["openWB/general/extern"]) {
			host = data["openWB/isss/parentWB"];
			query += `?parentChargePoint1=${data["openWB/isss/parentCPlp1"]}`;
			query += `&parentChargePoint2=${data["openWB/isss/parentCPlp2"]}`;
		}
		const theme = data["openWB/optional/int_display/theme"].type;
		const destination = `${location.protocol}//${host}/openWB/web/display/themes/${theme}/${query}`;

		var request = new XMLHttpRequest();
		request.onload = function () {
			if (this.readyState == 4) {
				if (this.status == 200) {
					addLog(`theme '${theme}' is valid`)
					if (destination != iframe.src) {
						addLog(`all done, starting theme '${theme}' with url '${destination}'`);
						iframe.src = destination;
					}
					setTimeout(() => {
						startup.classList.add("hide");
						iframe.classList.remove("hide");
					}, 2000);
				} else {
					addLog(`theme '${theme}' not found on server!`);
				}
			}
		};
		request.ontimeout = function () {
			console.warn("onTimeout", this.readyState, this.status);
			addLog(`check for theme '${theme}' timed out!`);
		};
		request.timeout = 2000;
		console.debug("checking url:", destination);
		request.open("GET", destination, true);
		request.send();
	} else {
		console.debug("some topics still missing");
	}
}

function addLog(message) {
	const logElement = document.querySelector('#log');
	logElement.insertAdjacentHTML("beforeend", "<br />");
	logElement.insertAdjacentText("beforeend", message);
}

function handleMessage(topic, payload) {
	addLog(`Topic: ${topic} Payload: ${payload}`);
	// receives all topics and calls respective function to process them
	if (topic.match(/^openwb\/system\//i)) { processSystemTopics(topic, payload); }
	setIframeSource();
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

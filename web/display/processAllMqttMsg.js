/**
 * Functions to update graph and gui values via MQTT-messages
 */

/** @function reloadDisplay
 * triggers a reload of the current page
 */
function reloadDisplay() {
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
		var host = "";
		var query = new URLSearchParams();
		var destination = "";
		if (data["openWB/general/extern"]) {
			switch (data["openWB/general/extern_display_mode"]) {
				case "local":
					// host = location.host;
					// ...
					// break;
					// ToDo, fallback to primary
					addLog("Local display in secondary mode not yet supported! fallback to primary display");
				case "primary":
				default:
					// retrieve display theme from primary
					host = data["openWB/internal_chargepoint/global_data"]["parent_ip"];
					// we need to know how to map local charge points to primary
					query.append("parentChargePoint1", data["openWB/internal_chargepoint/0/data/parent_cp"]);
					query.append("parentChargePoint2", data["openWB/internal_chargepoint/1/data/parent_cp"]);
					break;
			}
			// load display from primary or local
			destination = `${location.protocol}//${host}/openWB/web/display/?${query.toString()}`;
			if (destination != iframe.src) {
				addLog(`all done, loading theme from primary`);
				// iframe.src = destination;
			}
			setTimeout(() => {
				// startup.classList.add("hide");
				// iframe.classList.remove("hide");
				location.href = destination;
			}, 2000);
		} else {
			host = location.host;
			const theme = data["openWB/optional/int_display/theme"].type;

			if (data["openWB/optional/int_display/only_local_charge_points"]) {
				const searchParams = new URLSearchParams(location.search);

				if (searchParams.has("parentChargePoint1")) {
					query.append("parentChargePoint1", searchParams.get("parentChargePoint1"));
				}
				if (searchParams.has("parentChargePoint2")) {
					query.append("parentChargePoint2", searchParams.get("parentChargePoint2"));
				}
			}
			destination = `${location.protocol}//${host}/openWB/web/display/themes/${theme}/?${query.toString()}`;

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
		}
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

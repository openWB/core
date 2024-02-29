/**
 * Functions to update gui values via MQTT-messages
 */

function loadTarget() {
	if (allTopicsReceived()) {
		var destination = "";
		const logMessages = document.getElementById("log");
		if (!data["openWB/system/boot_done"]) {
			addLog("backend still booting");
			return;
		}
		if (data["openWB/system/update_in_progress"]) {
			addLog("update in progress");
			return;
		}
		if (data["openWB/system/usage_terms_acknowledged"] === false) {
			addLog("usage terms not accepted, redirecting...");
			destination = "settings/";
			setTimeout(() => {
				location.href = destination
			}, 2500);
			return;
		}
		const theme = data["openWB/general/web_theme"].type;
		destination = `themes/${theme}/`;
		if (data["openWB/general/extern"]) {
			console.log("openWB is configured as external charge point");
			logMessages.classList.add("hide");
			return;
		} else {
			logMessages.classList.remove("hide");
		}

		var request = new XMLHttpRequest();
		request.onload = function () {
			if (this.readyState == 4) {
				if (this.status == 200) {
					addLog(`theme '${theme}' is valid`)
					addLog(`all done, starting theme '${theme}' with url '${destination}'`);
					setTimeout(() => {
						location.href = destination
					}, 250);
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
	const logElement = document.getElementById('log');
	logElement.insertAdjacentHTML("beforeend", "<br />");
	logElement.insertAdjacentText("beforeend", message);
}

function handleMessage(topic, payload) {
	addLog(`Topic: ${topic} Payload: ${payload}`);
	if (data["openWB/general/extern"]) {
		document.getElementById("secondary-mode").classList.remove("hide");
	} else {
		document.getElementById("secondary-mode").classList.add("hide");
	}
	if (!data["openWB/system/boot_done"]) {
		document.getElementById("boot").classList.remove("hide");
	} else {
		document.getElementById("boot").classList.add("hide");
	}
	if (data["openWB/system/update_in_progress"]) {
		document.getElementById("update").classList.remove("hide");
	} else {
		document.getElementById("update").classList.add("hide");
	}
	if (data["openWB/internal_chargepoint/global_data"]) {
		document.getElementById("primary-link").setAttribute("href", `https://${data["openWB/internal_chargepoint/global_data"].parent_ip}/`);
	}
	loadTarget();
}

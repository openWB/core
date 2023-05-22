/**
 * Functions to update graph and gui values via MQTT-messages
 */

function setIframeSource() {
	if (allTopicsReceived()) {
		const startup = document.querySelector("#notReady");
		const iframe = document.querySelector("#themeTarget");
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
		const theme = data["openWB/general/web_theme"].type;
		let destination = `${location.protocol}//${host}/openWB/web/themes/${theme}/${query}`;
		if (data["openWB/general/extern"]) {
			console.log("openWB is configured as external charge point");
			startup.classList.remove("hide");
			iframe.classList.add("hide");
			return;
		}

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
	if (data["openWB/general/extern"]) {
		document.querySelector("#isss").classList.remove("hide");
	} else {
		document.querySelector("#isss").classList.add("hide");
	}
	setIframeSource();
}  // end handleMessage

/**
 * Functions to update graph and gui values via MQTT-messages
 */

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
		if (data["openWB/general/extern"] === true) {
			// load secondary display (from secondary openWB)
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
					const queryObject = {
						// we need our own ip address for status information
						localIp: data["openWB/system/ip_address"],
						// we need to know the current branch, commit and version
						localBranch: data["openWB/system/current_branch"],
						localCommit: data["openWB/system/current_commit"],
						localVersion: data["openWB/system/version"],
						// we need to know how to map local charge points to primary
						parentChargePoint1: data["openWB/internal_chargepoint/0/data/parent_cp"],
						parentChargePoint2: data["openWB/internal_chargepoint/1/data/parent_cp"]
					}
					query.append("data", JSON.stringify(queryObject));
					break;
			}
			// load display from primary or local
			destination = `${location.protocol}//${host}/openWB/web/display/?${query.toString()}`;
			addLog(`all done, loading theme from primary`);
			// no iframe here as this would result in another nesting with the wrapper on primary
			setTimeout(() => {
				location.href = destination;
			}, 2000);
		} else {
			// load primary display (from primary or secondary openWB)
			host = location.host;
			const theme = data["openWB/optional/int_display/theme"].type;
			const searchParams = new URLSearchParams(location.search);

			if (data["openWB/optional/int_display/only_local_charge_points"]) {
				if (searchParams.has("data")) {
					query.append("data", searchParams.get("data"));
				}
			}
			if (credentialsFetched) {
				addLog("hiding login/-out in query string");
				query.append("hide_login", "1");
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

function addLog(message, forceDisplay = false) {
	const logElement = document.getElementById('log');
	let displayedMessages = logElement.innerHTML.split("\n");
	if (displayedMessages.length > 25) {
		displayedMessages.shift();
	}
	displayedMessages.push(message);
	logElement.innerHTML = displayedMessages.join("\n");
	if (forceDisplay) {
		logElement.classList.remove("hide");
	}
	logElement.scrollTo(0, logElement.scrollHeight); // Scroll to the last element
}

function handleMessage(topic, payload) {
	addLog(`Topic: ${topic} Payload: ${payload}`);
	// receives all topics and calls respective function to process them
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
	setIframeSource();
}  // end handleMessage

/**
 * helper functions for setup-pages
 *
 * @author Michael Ortenstein
 * @author Lutz Bender
 */

/**
 * setCookie
 * stores a cookie in the current browser
 * @param {string} cname cookie name
 * @param {string} cvalue cookie value
 * @param {int} exdays expires in days
 */
function setCookie(cname, cvalue, exdays) {
	var d = new Date();
	d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
	var expires = "expires=" + d.toGMTString();
	document.cookie = cname + "=" + cvalue + ";" + expires + "; path=/openWB/";
}

/**
 * getCookie
 * returns a cookie value
 * @param {string} cname cookie name
 * @returns {string}
 */
function getCookie(cname) {
	var name = cname + '=';
	var decodedCookie = decodeURIComponent(document.cookie);
	var ca = decodedCookie.split(';');
	for (var i = 0; i < ca.length; i++) {
		var c = ca[i];
		while (c.charAt(0) == ' ') {
			c = c.substring(1);
		}
		if (c.indexOf(name) == 0) {
			return c.substring(name.length, c.length);
		}
	}
	return '';
}

var originalValues = {}; // holds all topics and its values received by mqtt as objects before possible changes made by user

var changedValuesHandler = {
	deleteProperty: function(obj, key, value) {
		delete obj[key];
		// if array is empty after delete, all send topics have been received with correct value
		// so redirect to main page
		// array is only filled by function getChangedValues!
		// console.log("num changed values left: "+Object.keys(changedValues).length);
		if (Object.keys(changedValues).length === 0) {
			console.log("done");
			setTimeout(function() {
				$('#saveprogress').addClass('hide');
				// window.location.href = './index.php';
			}, 200);
		} else {
			return true;
		}
	}
}

var changedValues = new Proxy({}, changedValuesHandler);

function sendValues() {
	/** @function sendValues
	 * send all topic-value-pairs from valueList
	 * @typedef {Object} topic-value-pair
	 * @property {string} topic - the topic
	 * @property {string} value - the value
	 * @param {topic-value-pair} - the changed values and their topics
	 * @requires global variable 'toBeSendValues'
	 * @requires modal with id 'noValuesChangedInfoModal'
	 */
	if (!(Object.keys(changedValues).length === 0)) {
		// there are changed values
		// so first show saveprogress on page
		$('#saveprogress').removeClass('hide');
		// delay in ms between publishes
		var intervall = 200;
		// then send changed values

		Object.keys(changedValues).forEach(function(topic, index) {
			var value = this[topic];
			setTimeout(function() {
				console.log("publishing changed value: " + topic + ": " + value);
				// as all empty messages are not processed by mqttsub.py, we have to send something usefull
				if (value.length == 0) {
					publish("none", topic);
					// delete empty values as we will never get an answer
					console.log("deleting empty changedValue: " + topic)
					delete changedValues[topic];
				} else {
					publish(value, topic);
				}
			}, index * intervall);
		}, changedValues);

	} else {
		$('#noValuesChangedInfoModal').modal();
	}
}

function getChangedValues() {
	/** @function getChangedValues
	 * gets all topic-value-pairs changed by the user and sets topic from /get/ to /set/
	 * @typedef {Object} topic-value-pair
	 * @property {string} topic - the topic
	 * @property {string} value - the value
	 * @return {topic-value-pair} - the changed values and their topics
	 */
	for (element in vApp.$refs) {
		console.log("checking: " + element);
		if (vApp.$refs[element].changed && !vApp.$refs[element].disabled) {
			console.log("value ist changed and not disabled");
			var message = JSON.stringify(vApp.$refs[element].value);
			var topic = element.replace(/^openWB\//, 'openWB/set/');
			changedValues[topic] = message;
		}
	}
}

/**
 * processes mqtt messages
 *
 * @author Michael Ortenstein
 */

function checkAllSaved(topic, value) {
	/** @function checkAllSaved
	 * checks if received value equals the last saved and removes key from array
	 * @param {string} topic - the complete mqtt topic
	 * @param {string} value - the value for the topic
	 * @requires global var:changedValues - is declared with proxy in helperFunctions.js
	 */
	topic = topic.replace('openWB/', 'openWB/set/');
	if (changedValues.hasOwnProperty(topic) && changedValues[topic] == value) {
		// received topic-value-pair equals one that was send before
		delete changedValues[topic]; // delete it
		// proxy will initiate redirect to main page if array is now empty
	}
};

function processMessages(topic, payload) {
	checkAllSaved(topic, payload);
	if (topic in vApp.$refs) {
		jsonPayload = JSON.parse(payload);
		vApp.$refs[topic].initialValue = jsonPayload;
		vApp.$refs[topic].value = jsonPayload;
	} else {
		console.log("no ref found: " + topic);
	}
}

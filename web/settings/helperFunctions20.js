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

// var originalValues = {}; // holds all topics and its values received by mqtt as objects before possible changes made by user

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
				$('#saveprogressModal').modal('hide');
				// window.location.href = './index.php';
			}, 200);
		} else {
			return true;
		}
	}
}

var changedValues = new Proxy({}, changedValuesHandler);

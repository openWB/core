<?php
$updateInProgress = false;
$bootInProgress = false;
$isExtern = false;
$dataProtectionAcknowledged = false;

// check if update.sh is still running
$output = null;
$resultCode = null;
exec("mosquitto_sub -t 'openWB/system/update_in_progress' -C 1 -W 1", $output, $resultCode);
if ($resultCode == 0 && $output[0] == "true") {
	$updateInProgress = true;
}
// check if atreboot.sh is still running
$output = null;
$resultCode = null;
exec("mosquitto_sub -t 'openWB/system/boot_done' -C 1 -W 1", $output, $resultCode);
if ($resultCode == 0 && $output[0] !== "true") {
	$bootInProgress = true;
}
// if yes, show placeholder. If not, show theme
if ($bootInProgress or $updateInProgress) {
	//atreboot.sh or update.sh still in progress, wait 5 seconds and retry
	include 'notReady.html';
} else {
	// check for acknowledgement of data protection
	// $output = null;
	// $resultCode = null;
	// exec("mosquitto_sub -t 'openWB/system/dataprotection_acknowledged' -C 1 -W 1", $output, $resultCode);
	// if($resultCode == 0 && $output[0] == "true"){
	// 	$dataProtectionAcknowledged = true;
	// }
	// if ( ! $dataProtectionAcknowledged ) {
	//	// load dataprotection page
	// 	include 'settings/#/System/DataProtection';
	// } else {

	// check for external mode
	$output = null;
	$resultCode = null;
	exec("mosquitto_sub -t 'openWB/general/extern' -C 1 -W 1", $output, $resultCode);
	if ($resultCode == 0 && $output[0] == "true") {
		$isExtern = true;
	}
	if ($isExtern) {
		// load chargepoint only page
		include 'isExtern.html';
	} else {
		// load normal UI
		// check if theme cookie exists and theme is installed
		// else set standard theme
		if (!(isset($_COOKIE['openWBTheme']) === true) || !(is_dir('themes/' . $_COOKIE['openWBTheme']) === true)) {
			$_COOKIE['openWBTheme'] = 'standard';
		}
		// expand expiring-date to now + 2 years
		$expire = time() + (60 * 60 * 24 * 365 * 2);
		setcookie('openWBTheme', $_COOKIE['openWBTheme'], $expire, '/openWB/');
		if (file_exists($_SERVER['DOCUMENT_ROOT'] . '/openWB/web/themes/' . $_COOKIE['openWBTheme'] . '/theme.php')) {
			include 'themes/' . $_COOKIE['openWBTheme'] . '/theme.php';
		} else {
			include 'themes/' . $_COOKIE['openWBTheme'] . '/theme.html';
		}
	}
	// }
}

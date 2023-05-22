<?php
define("BASE_WEB_PATH", "/openWB/web/");

function redirect($target)
{
	header("Location: " . BASE_WEB_PATH . $target);
	exit;
}

$updateInProgress = false;
$bootInProgress = false;
$isExtern = false;
$dataProtectionAcknowledged = false;
$usageTermsAcknowledged = false;

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
// if updating or booting, show placeholder. If not, show theme
if ($bootInProgress or $updateInProgress) {
	//atreboot.sh or update.sh still in progress, wait 5 seconds and retry
	include $_SERVER["DOCUMENT_ROOT"] . BASE_WEB_PATH . "notReady.html";
	exit;
}

// check for acknowledgement of usage terms
$output = null;
$resultCode = null;
exec("mosquitto_sub -t 'openWB/system/usage_terms_acknowledged' -C 1 -W 1", $output, $resultCode);
if ($resultCode == 0 && $output[0] == "true") {
	$usageTermsAcknowledged = true;
}
if (!$usageTermsAcknowledged) {
	// load usage terms page
	redirect("settings/#/System/LegalSettings");
	exit;
}

// check for external mode
$output = null;
$resultCode = null;
exec("mosquitto_sub -t 'openWB/general/extern' -C 1 -W 1", $output, $resultCode);
if ($resultCode == 0 && $output[0] == "true") {
	$isExtern = true;
}
if ($isExtern) {
	// load chargepoint only page
	include $_SERVER["DOCUMENT_ROOT"] . BASE_WEB_PATH . "isExtern.html";
	exit;
}

// load normal UI
// check if theme cookie exists and theme is installed
// else set standard theme
if (!(isset($_COOKIE["openWBTheme"]) === true) || !(is_dir("themes/" . $_COOKIE["openWBTheme"]) === true)) {
	$_COOKIE["openWBTheme"] = "standard_legacy";
}
// expand expiring-date to now + 2 years
$expire = time() + (60 * 60 * 24 * 365 * 2);
setcookie("openWBTheme", $_COOKIE["openWBTheme"], $expire, "/openWB/");
if (file_exists($_SERVER["DOCUMENT_ROOT"] . BASE_WEB_PATH . "themes/" . $_COOKIE["openWBTheme"] . "/theme.php")) {
	$target = "themes/" . $_COOKIE["openWBTheme"] . "/theme.php";
} elseif( file_exists($_SERVER['DOCUMENT_ROOT'] . '/openWB/web/themes/' . $_COOKIE['openWBTheme'] . '/theme.html') ) {
	 $target = "themes/" . $_COOKIE["openWBTheme"] . "/theme.html";
} else {
	$target = "themes/".$_COOKIE["openWBTheme"]."/index.html";
}
redirect($target);


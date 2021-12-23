<?php
	// check if update.sh is still running
	// $updateinprogress = file_get_contents($_SERVER['DOCUMENT_ROOT'] . '/openWB/ramdisk/updateinprogress');
	$updateinprogress = false;
	// --> openWB/system/update_in_progress
	// check if atreboot.sh is still running
	$bootinprogress = ! file_exists($_SERVER['DOCUMENT_ROOT'] . '/openWB/ramdisk/bootdone');
	// --> openWB/system/boot_done
	// if yes, show placeholder. If not, show theme
	if ( $bootinprogress or $updateinprogress) {
		//atreboot.sh or update.sh still in progress, wait 5 seconds and retry
		include 'notready.html';
	} else {
		// load openwb.conf
		// $lines = file($_SERVER['DOCUMENT_ROOT'] . '/openWB/openwb.conf');
		// foreach($lines as $line) {
		// 	list($key, $value) = explode("=", $line, 2);
		// 	${$key."old"} = trim( $value, " '\t\n\r\0\x0B" ); // remove all garbage and single quotes
		// }

		// check for acknoledgement of dataprotection
		// if ( $datenschutzackold == 0 && $clouduserold !== "leer") {
		// 	// --> openWB/system/dataprotection_acknowledged
		// 	// load dataprotection page
		// 	include 'settings/datenschutz.html';
		// } elseif ( !isset($wizzarddoneold) || ($wizzarddoneold < 100) ) {
		// 	// --> openWB/system/wizzard_done
		// 	// load wizzard page
		// 	include 'settings/wizzard.php';
		// } elseif ( $isssold == 1 ) {
		// 	// --> openWB/general/extern
		// 	// load chargepoint only page
		// 	include 'isss.html';
		// } else {
			// load normal UI
			// check if theme cookie exists and theme is installed
			// else set standard theme
			if ( !(isset($_COOKIE['openWBTheme'] ) === true) || !(is_dir('themes/'.$_COOKIE['openWBTheme']) === true) ) {
				$_COOKIE['openWBTheme'] = 'standard';
			}
			// expand expiring-date to now + 2 years
			$expire = time()+(60*60*24*365*2);
			setcookie('openWBTheme', $_COOKIE['openWBTheme'], $expire, '/openWB/');
			if( file_exists($_SERVER['DOCUMENT_ROOT'] . '/openWB/web/themes/' . $_COOKIE['openWBTheme'] . '/theme.php') ){
				include 'themes/'.$_COOKIE['openWBTheme'].'/theme.php';
			} else {
				include 'themes/'.$_COOKIE['openWBTheme'].'/theme.html';
			}
		// }
	}
?>

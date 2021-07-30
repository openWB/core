<?php
session_start();

$themeCookie = "standard";
if( isset($_COOKIE['openWBTheme'] )){
	$themeCookie = $_COOKIE['openWBTheme'];
} else {
	setCookie("openWBTheme", $themeCookie, mktime().time()+60*60*24*365);
}
?>
<!DOCTYPE html>
<html lang="de">
	<head>
		<base href="/openWB/web/">
		<meta charset="UTF-8">
		<meta http-equiv="X-UA-Compatible" content="IE=edge">
		<meta name="viewport" content="width=device-width, initial-scale=1">
		<title>openWB Einstellungen</title>
		<meta name="description" content="Control your charge" />
		<meta name="author" content="Lutz Bender" />
		<!-- Favicons (created with http://realfavicongenerator.net/)-->
		<link rel="apple-touch-icon" sizes="57x57" href="img/favicons/apple-touch-icon-57x57.png">
		<link rel="apple-touch-icon" sizes="60x60" href="img/favicons/apple-touch-icon-60x60.png">
		<link rel="icon" type="image/png" href="img/favicons/favicon-32x32.png" sizes="32x32">
		<link rel="icon" type="image/png" href="img/favicons/favicon-16x16.png" sizes="16x16">
		<link rel="manifest" href="manifest.json">
		<link rel="shortcut icon" href="img/favicons/favicon.ico">
		<meta name="msapplication-TileColor" content="#00a8ff">
		<meta name="msapplication-config" content="img/favicons/browserconfig.xml">
		<meta name="theme-color" content="#ffffff">

		<!-- Bootstrap -->
		<link rel="stylesheet" type="text/css" href="css/bootstrap-4.4.1/bootstrap.min.css">
		<!-- Bootstrap-Toggle -->
		<link rel="stylesheet" type="text/css" href="css/bootstrap4-toggle/bootstrap4-toggle.min.css">
		<!-- Normalize -->
		<link rel="stylesheet" type="text/css" href="css/normalize-8.0.1.css">
		<!-- Font Awesome -->
		<link rel="stylesheet" type="text/css" href="fonts/font-awesome-5.8.2/css/all.css">
		<!-- include settings-style -->
		<link rel="stylesheet" type="text/css" href="css/settings_style20.css">
		<link rel="stylesheet" href="themes/<?php echo $themeCookie; ?>/settings.css?v=20210330">

		<!-- important scripts to be loaded -->
		<script src="js/jquery-3.6.0.min.js"></script>
		<script src="js/bootstrap-4.4.1/bootstrap.bundle.min.js"></script>
		<script src="js/bootstrap4-toggle/bootstrap4-toggle.min.js"></script>
		<script src="js/bootstrap-selectpicker/bootstrap-select.min.js"></script>
		<!-- load helper functions -->
		<script src = "settings/helperFunctions20.js?ver=20210329" ></script>
		<!-- load mqtt library -->
		<script src = "js/mqttws31.js" ></script>
		<!-- vue.js -->
		<script src="js/vue.js-3.1.5/vue.global.js"></script>
	</head>
	<body>
		<div id="app">

			<!-- Saveprogress -->
			<div id="saveprogress" class="hide">
				<div id="saveprogress-inner">
					<div class="row">
						<div class="mx-auto d-block justify-content-center">
							<img id="saveprogress-image" src="img/favicons/preloader-image.png" alt="openWB">
						</div>
					</div>
					<div id="saveprogress-info" class="row justify-content-center mt-2">
						<div class="col-10 col-sm-6">
							Bitte warten, geänderte Einstellungen werden gespeichert.
						</div>
					</div>
				</div>
			</div>

			<div id="nav"></div> <!-- placeholder for navbar -->

			<div role="main" class="container">

				<div id="content">
					<h1>Optionale Komponenten</h1>

					<form id="myForm">

						<div class="card border-secondary">
							<div class="card-header bg-secondary">
								<div class="form-group mb-0">
									<div class="form-row vaRow mb-1">
										<div class="col">
											RFID
										</div>
									</div>
								</div>
							</div>
							<div class="card-body">
								<buttongroup-input
									title="Modus"
									ref="openWB/optional/rfid/mode"
									toggle-selector='rfidMode'
									:buttons="[
										{buttonValue: 0, text: 'Aus', class: 'btn-outline-danger', icon: 'fas fa-times'},
										{buttonValue: 1, text: 'Modus 1', class: 'btn-outline-success'},
										{buttonValue: 2, text: 'Modus 2', class: 'btn-outline-success'}
									]"
									:default-value=0>
								</buttongroup-input>
								<div v-show="visibility.rfidMode != 0">
									<hr>
									<alert
										subtype="info">
										<template #message>
											ToDo: Anzeige Mode 1 oder 2
										</template>
									</alert>
									<hr>
								</div>
								<div v-show="visibility.rfidMode == 1">
									<alert
										subtype="info">
										<template #message>
											ToDo: Anzeige Mode 1
										</template>
									</alert>
								</div>
								<div v-show="visibility.rfidMode == 2">
									<alert
										subtype="info">
										<template #message>
											Im Modus 2 wird eine Kommaseparierte Liste mit gültigen RFID Tags hinterlegt. Gescannt werden kann an jedem möglichen RFID Leser.<br>
											Der gescannte Tag wird dem zuletzt angeschlossenenen Auto zugewiesen, schaltet den Ladepunkt frei und vermerkt dies für das Ladelog.<br>
											Wird erst gescannt und dann ein Auto angeschlossen, so wird der Tag dem Auto zugewiesen, das als nächstes angesteckt wird. Wird 5 Minuten nach Scannen kein Auto angeschlossen wird der Tag verworfen.<br>
											Jeder Ladepunkt wird nach abstecken automatisch wieder gesperrt.
										</template>
									</alert>
								</div>
							</div>
						</div>

						<div class="card border-secondary">
							<div class="card-header bg-secondary">
								<div class="form-group mb-0">
									<div class="form-row vaRow mb-1">
										<div class="col">
											LED-Ausgänge
										</div>
									</div>
								</div>
							</div>
							<div class="card-body">
								<buttongroup-input
									title="LED-Ausgänge aktivieren"
									ref="openWB/optional/led/active"
									toggle-selector='ledOn'
									:buttons="[
										{buttonValue: false, text: 'Aus', class: 'btn-outline-danger', icon: 'fas fa-times'},
										{buttonValue: true, text: 'An', class: 'btn-outline-success'}
									]"
									:default-value=false>
								</buttongroup-input>
								<div v-show="visibility.ledOn">
									<alert
										subtype="info">
										<template #message>
											ToDo: Informationen zu den verwendeten GPOIs ergänzen!
										</template>
									</alert>
									<hr>
									<heading>
										Ladung nicht freigegeben
									</heading>
									<select-input
										title="Sofortladen"
										ref="ToDo/optional/led/instant_blocked"
										:options="[
											{value: ['off','off','off'], text: 'Alle aus'}
										]"
										:groups="[
											{label: 'Dauernd an', options: [
												{value: ['on', 'off','off'], text: 'LED 1'},
												{value: ['off','on', 'off'], text: 'LED 2'},
												{value: ['off','off','on' ], text: 'LED 3'},
												{value: ['on', 'on', 'off'], text: 'LEDs 1+2'},
												{value: ['on', 'off','on' ], text: 'LEDs 1+3'},
												{value: ['off','on', 'on' ], text: 'LEDs 2+3'},
												{value: ['on', 'on', 'on' ], text: 'alle'}
											] },
											{label: 'Blinkend', options: [
												{value: ['blink', 'off',   'off'   ], text: 'LED 1'},
												{value: ['off',   'blink', 'off'   ], text: 'LED 2'},
												{value: ['off',   'off',   'blink' ], text: 'LED 3'},
												{value: ['blink', 'blink', 'off'   ], text: 'LEDs 1+2'},
												{value: ['blink', 'off',   'blink' ], text: 'LEDs 1+3'},
												{value: ['off',   'blink', 'blink' ], text: 'LEDs 2+3'},
												{value: ['blink', 'blink', 'blink' ], text: 'alle'}
											] }
										]"
										:default-value="['off','off','off']"
										:is-disabled='!visibility.ledOn'>
									</select-input>
									<select-input
										title="PV"
										ref="ToDo/optional/led/pv_blocked"
										:options="[
											{value: ['off','off','off'], text: 'Alle aus'}
										]"
										:groups="[
											{label: 'Dauernd an', options: [
												{value: ['on', 'off','off'], text: 'LED 1'},
												{value: ['off','on', 'off'], text: 'LED 2'},
												{value: ['off','off','on' ], text: 'LED 3'},
												{value: ['on', 'on', 'off'], text: 'LEDs 1+2'},
												{value: ['on', 'off','on' ], text: 'LEDs 1+3'},
												{value: ['off','on', 'on' ], text: 'LEDs 2+3'},
												{value: ['on', 'on', 'on' ], text: 'alle'}
											] },
											{label: 'Blinkend', options: [
												{value: ['blink', 'off',   'off'   ], text: 'LED 1'},
												{value: ['off',   'blink', 'off'   ], text: 'LED 2'},
												{value: ['off',   'off',   'blink' ], text: 'LED 3'},
												{value: ['blink', 'blink', 'off'   ], text: 'LEDs 1+2'},
												{value: ['blink', 'off',   'blink' ], text: 'LEDs 1+3'},
												{value: ['off',   'blink', 'blink' ], text: 'LEDs 2+3'},
												{value: ['blink', 'blink', 'blink' ], text: 'alle'}
											] }
										]"
										:default-value="['off','off','off']"
										:is-disabled='!visibility.ledOn'>
									</select-input>
									<select-input
										title="Zielladen"
										ref="ToDo/optional/led/scheduled_blocked"
										:options="[
											{value: ['off','off','off'], text: 'Alle aus'}
										]"
										:groups="[
											{label: 'Dauernd an', options: [
												{value: ['on', 'off','off'], text: 'LED 1'},
												{value: ['off','on', 'off'], text: 'LED 2'},
												{value: ['off','off','on' ], text: 'LED 3'},
												{value: ['on', 'on', 'off'], text: 'LEDs 1+2'},
												{value: ['on', 'off','on' ], text: 'LEDs 1+3'},
												{value: ['off','on', 'on' ], text: 'LEDs 2+3'},
												{value: ['on', 'on', 'on' ], text: 'alle'}
											] },
											{label: 'Blinkend', options: [
												{value: ['blink', 'off',   'off'   ], text: 'LED 1'},
												{value: ['off',   'blink', 'off'   ], text: 'LED 2'},
												{value: ['off',   'off',   'blink' ], text: 'LED 3'},
												{value: ['blink', 'blink', 'off'   ], text: 'LEDs 1+2'},
												{value: ['blink', 'off',   'blink' ], text: 'LEDs 1+3'},
												{value: ['off',   'blink', 'blink' ], text: 'LEDs 2+3'},
												{value: ['blink', 'blink', 'blink' ], text: 'alle'}
											] }
										]"
										:default-value="['off','off','off']"
										:is-disabled='!visibility.ledOn'>
									</select-input>
									<select-input
										title="Standby"
										ref="ToDo/optional/led/standby_blocked"
										:options="[
											{value: ['off','off','off'], text: 'Alle aus'}
										]"
										:groups="[
											{label: 'Dauernd an', options: [
												{value: ['on', 'off','off'], text: 'LED 1'},
												{value: ['off','on', 'off'], text: 'LED 2'},
												{value: ['off','off','on' ], text: 'LED 3'},
												{value: ['on', 'on', 'off'], text: 'LEDs 1+2'},
												{value: ['on', 'off','on' ], text: 'LEDs 1+3'},
												{value: ['off','on', 'on' ], text: 'LEDs 2+3'},
												{value: ['on', 'on', 'on' ], text: 'alle'}
											] },
											{label: 'Blinkend', options: [
												{value: ['blink', 'off',   'off'   ], text: 'LED 1'},
												{value: ['off',   'blink', 'off'   ], text: 'LED 2'},
												{value: ['off',   'off',   'blink' ], text: 'LED 3'},
												{value: ['blink', 'blink', 'off'   ], text: 'LEDs 1+2'},
												{value: ['blink', 'off',   'blink' ], text: 'LEDs 1+3'},
												{value: ['off',   'blink', 'blink' ], text: 'LEDs 2+3'},
												{value: ['blink', 'blink', 'blink' ], text: 'alle'}
											] }
										]"
										:default-value="['off','off','off']"
										:is-disabled='!visibility.ledOn'>
									</select-input>
									<select-input
										title="Stop"
										ref="ToDo/optional/led/stop_blocked"
										:options="[
											{value: ['off','off','off'], text: 'Alle aus'}
										]"
										:groups="[
											{label: 'Dauernd an', options: [
												{value: ['on', 'off','off'], text: 'LED 1'},
												{value: ['off','on', 'off'], text: 'LED 2'},
												{value: ['off','off','on' ], text: 'LED 3'},
												{value: ['on', 'on', 'off'], text: 'LEDs 1+2'},
												{value: ['on', 'off','on' ], text: 'LEDs 1+3'},
												{value: ['off','on', 'on' ], text: 'LEDs 2+3'},
												{value: ['on', 'on', 'on' ], text: 'alle'}
											] },
											{label: 'Blinkend', options: [
												{value: ['blink', 'off',   'off'   ], text: 'LED 1'},
												{value: ['off',   'blink', 'off'   ], text: 'LED 2'},
												{value: ['off',   'off',   'blink' ], text: 'LED 3'},
												{value: ['blink', 'blink', 'off'   ], text: 'LEDs 1+2'},
												{value: ['blink', 'off',   'blink' ], text: 'LEDs 1+3'},
												{value: ['off',   'blink', 'blink' ], text: 'LEDs 2+3'},
												{value: ['blink', 'blink', 'blink' ], text: 'alle'}
											] }
										]"
										:default-value="['off','off','off']"
										:is-disabled='!visibility.ledOn'>
									</select-input>
									<hr>
									<heading>
										Ladung freigegeben
									</heading>
									<select-input
										title="Sofortladen"
										ref="ToDo/optional/led/instant"
										:options="[
											{value: ['off','off','off'], text: 'Alle aus'}
										]"
										:groups="[
											{label: 'Dauernd an', options: [
												{value: ['on', 'off','off'], text: 'LED 1'},
												{value: ['off','on', 'off'], text: 'LED 2'},
												{value: ['off','off','on' ], text: 'LED 3'},
												{value: ['on', 'on', 'off'], text: 'LEDs 1+2'},
												{value: ['on', 'off','on' ], text: 'LEDs 1+3'},
												{value: ['off','on', 'on' ], text: 'LEDs 2+3'},
												{value: ['on', 'on', 'on' ], text: 'alle'}
											] },
											{label: 'Blinkend', options: [
												{value: ['blink', 'off',   'off'   ], text: 'LED 1'},
												{value: ['off',   'blink', 'off'   ], text: 'LED 2'},
												{value: ['off',   'off',   'blink' ], text: 'LED 3'},
												{value: ['blink', 'blink', 'off'   ], text: 'LEDs 1+2'},
												{value: ['blink', 'off',   'blink' ], text: 'LEDs 1+3'},
												{value: ['off',   'blink', 'blink' ], text: 'LEDs 2+3'},
												{value: ['blink', 'blink', 'blink' ], text: 'alle'}
											] }
										]"
										:default-value="['off','off','off']"
										:is-disabled='!visibility.ledOn'>
									</select-input>
									<select-input
										title="PV"
										ref="ToDo/optional/led/pv"
										:options="[
											{value: ['off','off','off'], text: 'Alle aus'}
										]"
										:groups="[
											{label: 'Dauernd an', options: [
												{value: ['on', 'off','off'], text: 'LED 1'},
												{value: ['off','on', 'off'], text: 'LED 2'},
												{value: ['off','off','on' ], text: 'LED 3'},
												{value: ['on', 'on', 'off'], text: 'LEDs 1+2'},
												{value: ['on', 'off','on' ], text: 'LEDs 1+3'},
												{value: ['off','on', 'on' ], text: 'LEDs 2+3'},
												{value: ['on', 'on', 'on' ], text: 'alle'}
											] },
											{label: 'Blinkend', options: [
												{value: ['blink', 'off',   'off'   ], text: 'LED 1'},
												{value: ['off',   'blink', 'off'   ], text: 'LED 2'},
												{value: ['off',   'off',   'blink' ], text: 'LED 3'},
												{value: ['blink', 'blink', 'off'   ], text: 'LEDs 1+2'},
												{value: ['blink', 'off',   'blink' ], text: 'LEDs 1+3'},
												{value: ['off',   'blink', 'blink' ], text: 'LEDs 2+3'},
												{value: ['blink', 'blink', 'blink' ], text: 'alle'}
											] }
										]"
										:default-value="['off','off','off']"
										:is-disabled='!visibility.ledOn'>
									</select-input>
									<select-input
										title="Zielladen"
										ref="ToDo/optional/led/scheduled"
										:options="[
											{value: ['off','off','off'], text: 'Alle aus'}
										]"
										:groups="[
											{label: 'Dauernd an', options: [
												{value: ['on', 'off','off'], text: 'LED 1'},
												{value: ['off','on', 'off'], text: 'LED 2'},
												{value: ['off','off','on' ], text: 'LED 3'},
												{value: ['on', 'on', 'off'], text: 'LEDs 1+2'},
												{value: ['on', 'off','on' ], text: 'LEDs 1+3'},
												{value: ['off','on', 'on' ], text: 'LEDs 2+3'},
												{value: ['on', 'on', 'on' ], text: 'alle'}
											] },
											{label: 'Blinkend', options: [
												{value: ['blink', 'off',   'off'   ], text: 'LED 1'},
												{value: ['off',   'blink', 'off'   ], text: 'LED 2'},
												{value: ['off',   'off',   'blink' ], text: 'LED 3'},
												{value: ['blink', 'blink', 'off'   ], text: 'LEDs 1+2'},
												{value: ['blink', 'off',   'blink' ], text: 'LEDs 1+3'},
												{value: ['off',   'blink', 'blink' ], text: 'LEDs 2+3'},
												{value: ['blink', 'blink', 'blink' ], text: 'alle'}
											] }
										]"
										:default-value="['off','off','off']"
										:is-disabled='!visibility.ledOn'>
									</select-input>
									<select-input
										title="Standby"
										ref="ToDo/optional/led/standby"
										:options="[
											{value: ['off','off','off'], text: 'Alle aus'}
										]"
										:groups="[
											{label: 'Dauernd an', options: [
												{value: ['on', 'off','off'], text: 'LED 1'},
												{value: ['off','on', 'off'], text: 'LED 2'},
												{value: ['off','off','on' ], text: 'LED 3'},
												{value: ['on', 'on', 'off'], text: 'LEDs 1+2'},
												{value: ['on', 'off','on' ], text: 'LEDs 1+3'},
												{value: ['off','on', 'on' ], text: 'LEDs 2+3'},
												{value: ['on', 'on', 'on' ], text: 'alle'}
											] },
											{label: 'Blinkend', options: [
												{value: ['blink', 'off',   'off'   ], text: 'LED 1'},
												{value: ['off',   'blink', 'off'   ], text: 'LED 2'},
												{value: ['off',   'off',   'blink' ], text: 'LED 3'},
												{value: ['blink', 'blink', 'off'   ], text: 'LEDs 1+2'},
												{value: ['blink', 'off',   'blink' ], text: 'LEDs 1+3'},
												{value: ['off',   'blink', 'blink' ], text: 'LEDs 2+3'},
												{value: ['blink', 'blink', 'blink' ], text: 'alle'}
											] }
										]"
										:default-value="['off','off','off']"
										:is-disabled='!visibility.ledOn'>
									</select-input>
									<select-input
										title="Stop"
										ref="ToDo/optional/led/stop"
										:options="[
											{value: ['off','off','off'], text: 'Alle aus'}
										]"
										:groups="[
											{label: 'Dauernd an', options: [
												{value: ['on', 'off','off'], text: 'LED 1'},
												{value: ['off','on', 'off'], text: 'LED 2'},
												{value: ['off','off','on' ], text: 'LED 3'},
												{value: ['on', 'on', 'off'], text: 'LEDs 1+2'},
												{value: ['on', 'off','on' ], text: 'LEDs 1+3'},
												{value: ['off','on', 'on' ], text: 'LEDs 2+3'},
												{value: ['on', 'on', 'on' ], text: 'alle'}
											] },
											{label: 'Blinkend', options: [
												{value: ['blink', 'off',   'off'   ], text: 'LED 1'},
												{value: ['off',   'blink', 'off'   ], text: 'LED 2'},
												{value: ['off',   'off',   'blink' ], text: 'LED 3'},
												{value: ['blink', 'blink', 'off'   ], text: 'LEDs 1+2'},
												{value: ['blink', 'off',   'blink' ], text: 'LEDs 1+3'},
												{value: ['off',   'blink', 'blink' ], text: 'LEDs 2+3'},
												{value: ['blink', 'blink', 'blink' ], text: 'alle'}
											] }
										]"
										:default-value="['off','off','off']"
										:is-disabled='!visibility.ledOn'>
									</select-input>
								</div>
							</div>
						</div>

						<div class="card border-secondary">
							<div class="card-header bg-secondary">
								<div class="form-group mb-0">
									<div class="form-row vaRow mb-1">
										<div class="col">
											Display (intern oder extern)
										</div>
									</div>
								</div>
							</div>
							<div class="card-body">
								<buttongroup-input
									title="Integriertes Display"
									ref="openWB/optional/int_display/active"
									toggle-selector='intDisplayOn'
									:buttons="[
										{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
										{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
									]"
									:default-value=false>
								</buttongroup-input>
								<div v-show="visibility.intDisplayOn">
									<hr>
									<heading>
										Display Standby
									</heading>
									<range-input
										title="Ausschaltzeit"
										:min=0 :max=12 :step=1
										ref="openWB/optional/int_display/standby"
										:default-value=0
										unit="Sek"
										:labels='[{"label":"Immer an","value":0},{"label":5,"value":5},{"label":10,"value":10},{"label":15,"value":15},{"label":30,"value":30},{"label":45,"value":45},{"label":"1 Min","value":60},{"label":"1,5 Min","value":90},{"label":"2 Min","value":120},{"label":"3 Min","value":180},{"label":"4 Min","value":240},{"label":"5 Min","value":300},{"label":"10 Min","value":600}]'
										:is-disabled='!visibility.intDisplayOn'>
									</range-input>
									<buttongroup-input
										title="Automatisch einschalten"
										ref="openWB/optional/int_display/on_if_plugged_in"
										:buttons="[
											{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
											{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
										]"
										:default-value='false'
										:is-disabled='!visibility.intDisplayOn'>
										<template #help>
											Wird diese Funktion aktiviert, dann schaltet sich das Display automatisch ein, wenn ein Fahrzeug angesteckt wird.
										</template>
									</buttongroup-input>
								</div>
								<hr>
								<heading>
									PIN-Sperre
								</heading>
								<buttongroup-input
									title="Display mit PIN schützen"
									ref="openWB/optional/int_display/pin_active"
									toggle-selector='intDisplayPinOn'
									:buttons="[
										{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
										{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
									]"
									:default-value='false'>
								</buttongroup-input>
								<div v-show="visibility.intDisplayPinOn">
									<password-input
										title="PIN-Code"
										ref="openWB/optional/int_display/pin_code"
										pattern="[0-9]{4}"
										:is-disabled='!visibility.intDisplayPinOn'>
										<template #help>
											Der PIN-Code muss vierstellig sein und darf nur Zahlen enthalten.
										</template>
									</password-input>
								</div>
								<hr>
								<select-input
									title="Theme des Displays"
									ref="openWB/optional/int_display/theme"
									toggle-selector="displayTheme"
									:options="[
										{value: 'cards', text: 'Cards'},
										{value: 'gauges', text: 'Gauges'},
										{value: 'slave', text: 'Nur Ladeleistung (keine Bedienung möglich)'},
									]"
									default-value='cards'>
								</select-input>
								<div v-show="visibility.displayTheme == 'cards'">
									<alert
										subtype="info">
										<template #message>
											ToDo: Optionen für das Cards-Theme...
										</template>
									</alert>
								</div>
								<div v-show="visibility.displayTheme == 'gauges'">
									<alert
										subtype="info">
										<template #message>
											ToDo: Optionen für das Gauges-Theme...
										</template>
									</alert>
								</div>
								<div v-show="visibility.displayTheme == 'slave'">
									<alert
										subtype="info">
										<template #message>
											Das Theme "Nur Ladeleistung" bietet keine Optionen.
										</template>
									</alert>
								</div>
							</div>
						</div>

						<div class="card border-secondary">
							<div class="card-header bg-secondary">
								<div class="form-group mb-0">
									<div class="form-row vaRow mb-1">
										<div class="col">
											Loadsharing
										</div>
									</div>
								</div>
							</div>
							<div class="card-body">
								<buttongroup-input
									title="Loadsharing aktivieren"
									ref="openWB/optional/load_sharing/active"
									toggle-selector='loadsharingOn'
									:buttons="[
										{buttonValue: false, text: 'Aus', class: 'btn-outline-danger', icon: 'fas fa-times'},
										{buttonValue: true, text: 'An', class: 'btn-outline-success'}
									]"
									:default-value=false>
									<template #help>
										Wenn Ladepunkt 1 und 2 sich eine Zuleitung teilen, diese Option aktivieren. Sie stellt in jedem Lademodus sicher, dass nicht mehr als die eingestellte Stromstärke je Phase in der Summe von Ladepunkt 1 und 2 genutzt werden.<br>
										<span class="text-danger">Bei der OpenWB Duo muss diese Option aktiviert werden!</span>
									</template>
								</buttongroup-input>
								<div v-show="visibility.loadsharingOn">
									<range-input
										title="Maximaler Strom"
										:min=16 :max=32 :step=1
										ref="openWB/optional/load_sharing/max_current"
										:default-value=16
										unit="A"
										:is-disabled='!visibility.loadsharingOn'>
										<template #help>
											<p class="text-danger">Der richtige Anschluss ist zu gewährleisten.</p>
											<div class="row">
												<div class="col-md-4">Ladepunkt 1:</div>
												<div class="col">
													<ul>
														<li>Zuleitung Phase 1 = Phase 1</li>
														<li>Zuleitung Phase 2 = Phase 2</li>
														<li>Zuleitung Phase 3 = Phase 3</li>
													</ul>
												</div>
											</div>
											<div class="row">
												<div class="col-md-4">Ladepunkt 2:</div>
												<div class="col">
													<ul>
														<li>Zuleitung Phase 1 = <span class="text-danger">Phase 2</span></li>
														<li>Zuleitung Phase 2 = <span class="text-danger">Phase 3</span></li>
														<li>Zuleitung Phase 3 = <span class="text-danger">Phase 1</span></li>
													</ul>
												</div>
											</div>
											<p>Durch das Drehen der Phasen ist sichergestellt, dass 2 einphasige Autos mit voller Geschwindigkeit laden können.</p>
										</template>
									</range-input>
								</div>
							</div>
						</div>

						<div class="card border-secondary">
							<div class="card-header bg-secondary">
								<div class="form-group mb-0">
									<div class="form-row vaRow mb-1">
										<div class="col">
											Variable Stromtarife
										</div>
									</div>
								</div>
							</div>
							<div class="card-body">
								<buttongroup-input
									title="Stromtarife aktivieren"
									ref="openWB/optional/et/active"
									toggle-selector='etProviderOn'
									:buttons="[
										{buttonValue: false, text: 'Aus', class: 'btn-outline-danger', icon: 'fas fa-times'},
										{buttonValue: true, text: 'An', class: 'btn-outline-success'}
									]"
									:default-value=false>
								</buttongroup-input>
								<div v-show="visibility.etProviderOn">
									<text-input
										title="Anbieter"
										ref="openWB/optional/et/config/provider"
										:is-disabled='!visibility.etProviderOn'>
										<template #help>
											ToDo: JSON aufteilen
										</template>
									</text-input>
									<range-input
										title="Maximaler Strompreis"
										:min=-30 :max=30 :step=0.1
										ref="openWB/optional/et/config/max_price"
										:default-value=0
										unit="ct"
										:is-disabled='!visibility.etProviderOn'>
										<template #help>
											ToDo: Rundungsfehler???
										</template>
									</range-input>
								</div>
							</div>
						</div>

						<div class="row justify-content-center">
							<div class="col-md-4 d-flex py-1 justify-content-center">
								<button id="saveSettingsBtn" type="button" class="btn btn-block btn-success" @click="saveSettings()">Speichern</button>
							</div>
							<div class="col-md-4 d-flex py-1 justify-content-center">
								<button id="modalResetBtn" type="button" class="btn btn-block btn-warning" @click="showResetModal()">Änderungen verwerfen</button>
							</div>
							<div class="col-md-4 d-flex py-1 justify-content-center">
								<button id="modalDefaultsBtn" type="button" class="btn btn-block btn-danger" @click="showDefaultsModal()">Werkseinstellungen</button>
							</div>
						</div>

					</form>
				</div>

				<div class="mt-3 alert alert-dark text-center">
					Open Source made with love!<br>
					Jede Spende hilft die Weiterentwicklung von openWB voranzutreiben<br>
					<form action="https://www.paypal.com/cgi-bin/webscr" method="post" target="_top">
						<input type="hidden" name="cmd" value="_s-xclick">
						<input type="hidden" name="hosted_button_id" value="2K8C4Y2JTGH7U">
						<button type="submit" class="btn btn-warning">Spenden <i class="fab fa-paypal"></i></button>
					</form>
				</div>

			</div>  <!-- main container -->

			<footer id="footer" class="footer bg-dark text-light font-small">
				<div class="container text-center">
					<small>Sie befinden sich hier: Einstellungen / Optionale Komponenten</small>
				</div>
			</footer>

		</div><!-- app -->

		<script>
			$.get(
				{ url: "settings/navbar20.html", cache: false },
				function(data){
					$("#nav").replaceWith(data);
					// disable navbar entry for current page
					$('#navAllgemein').addClass('disabled');
				}
			);
		</script>

		<?php include_once './settings.vapp.php'; ?>

	</body>
</html>

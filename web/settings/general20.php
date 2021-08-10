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
			<content title="Allgemeine Einstellungen" footer="Allgemein" nav="#navGeneral">

				<card title="openWB">
					<buttongroup-input
						title="Nur Ladepunkt"
						v-model="componentData['openWB/general/extern']"
						:buttons="[
							{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
							{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
						]">
						<template #help>
							Wird hier "Ja" gewählt ist diese openWB nur ein Ladepunkt und übernimmt keine eigene Regelung.
							Hier ist "Ja" zu wählen wenn, bereits eine openWB vorhanden ist und diese nur ein weiterer Ladepunkt der vorhandenen openWB sein soll.
							<span class="text-danger">Alle in dieser openWB getätigten Einstellungen werden NICHT beachtet.</span>
							An der Haupt openWB wird als Ladepunkt "externe openWB" gewählt und die IP Adresse eingetragen.
						</template>
					</buttongroup-input>
					<select-input
						id="select1"
						title="Display-Theme"
						v-model="componentData['openWB/general/extOpenWBDisplay']"
						:options="[
							{value: 'normal', text: 'Normal'},
							{value: 'parent', text: 'Display der übergeordneten openWB'}
						]"
						v-if="componentData['openWB/general/extern'] === true">
						<template #help>
							Das Theme "Normal" zeigt lediglich die Ladeleistung des Ladepunktes an. Änderungen sind nicht möglich.<br>
							Wird hier "Display der übergeordneten openWB" ausgewählt, dann ist die Anzeige identisch zum Display der regelnden openWB. Alle Anzeigen und Änderungen sind möglich.
						</template>
					</select-input>
				</card>

				<card title="Hardware" v-if="componentData['openWB/general/extern'] === false">
					<buttongroup-input
						title="Geschwindigkeit Regelintervall"
						v-model="componentData['openWB/general/control_interval']"
						:buttons="[
							{buttonValue: 10, text: 'Normal'},
							{buttonValue: 20, text: 'Langsam'},
							{buttonValue: 60, text: 'Sehr Langsam'}
						]">
						<template #help>
							Sollten Probleme oder fehler auftreten, zunächst das Regelintervall auf "Normal" (10s) stellen.<br>
							Werden Module genutzt, welche z.B. eine Online-API nutzen oder soll langsamer geregelt werden, kann hier "Langsam" (20s) oder "Sehr Langsam" (60s) gewählt werden.<br>
							<span class="text-danger">Nicht nur die Regelung der PV-geführten Ladung, sondern auch Lademoduswechsel werden dann nur noch in diesem Intervall ausgeführt!</span>
						</template>
					</buttongroup-input>
					<buttongroup-input
						title="Netzschutz"
						v-model="componentData['openWB/general/grid_protection_configured']"
						:buttons="[
							{buttonValue: false, text: 'Aus'},
							{buttonValue: true, text: 'An'}
						]">
						<template #help>
							Diese Option ist standardmäßig aktiviert und sollte so belassen werden.
							Bei Unterschreitung einer kritischen Frequenz des Stromnetzes wird die Ladung nach einer zufälligen Zeit zwischen 1 und 90 Sekunden pausiert.
							Der Lademodus wechselt auf "Stop". Sobald die Frequenz wieder in einem normalen Bereich ist wird automatisch der zuletzt gewählte Lademodus wieder aktiviert.
							Ebenso wird die Ladung bei Überschreiten von 51,8 Hz unterbrochen. Dies ist dann der Fall, wenn der Energieversorger Wartungsarbeiten am (Teil-)Netz durchführt und auf einen vorübergehenden Generatorbetrieb umschaltet.
							Die Erhöhung der Frequenz wird durchgeführt, um die PV Anlagen abzuschalten.<br>
							<span class="text-danger">Die Option ist nur aktiv, wenn der Ladepunkt die Frequenz übermittelt. Jede openWB Series1/2 unterstützt dies.</span>
						</template>
					</buttongroup-input>
					<buttongroup-input
						title="Taster-Eingänge"
						v-model="componentData['openWB/general/external_buttons_hw']"
						:buttons="[
							{buttonValue: false, text: 'Aus'},
							{buttonValue: true, text: 'An'}
						]">
						<template #help>
							Wenn diese Option aktiviert ist, können bis zu fünf Taster an die openWB angeschlossen werden. Die entsprechenden Kontakte sind auf der Add-On-Platine beschriftet.<br>
							Bei Installationen ohne die Zusatzplatine können folgende GPIOs benutzt werden, die durch die Taster auf Masse zu schalten sind:
							<ul>
								<li>Taster 1: Pin 32 / GPIO 12</li>
								<li>Taster 2: Pin 36 / GPIO 16</li>
								<li>Taster 3: Pin 31 / GPIO 6</li>
								<li>Taster 4: Pin 33 / GPIO 13</li>
								<li>Taster 5: Pin 40 / GPIO 21</li>
							</ul>
						</template>
					</buttongroup-input>
				</card>

				<card title="Benachrichtigungen" v-if="componentData['openWB/general/extern'] === false">
					<select-input
						title="Anbieter"
						v-model="componentData['openWB/general/notifications/selected']"
						:options="[
							{value: 'none', text: 'Kein Anbieter'},
							{value: 'pushover', text: 'Pushover'}
						]">
					</select-input>
					<div v-if="componentData['openWB/general/notifications/selected'] == 'pushover'">
						<alert
							subtype="info">
							Zur Nutzung von Pushover muss ein Konto auf Pushover.net bestehen. Zudem muss im Pushover-Nutzerkonto eine Applikation openWB eingerichtet werden, um den benötigten API-Token/Key zu erhalten.<br>
							Wenn Pushover eingeschaltet ist, werden die Zählerstände aller konfigurierten Ladepunkte immer zum 1. des Monats gepusht.
						</alert>
						<text-input
							title="Einstellungen"
							subtype="json"
							disabled="disabled"
							v-model="componentData['openWB/general/notifications/configuration']">
							<template #help>
								Nur zur Info!
							</template>
						</text-input>
						<text-input
							title="Pushover User Key"
							v-model="componentData['openWB/general/notifications/configuration'].user"
							subtype="user">
						</text-input>
						<text-input
							title="Pushover API-Token/Key"
							subtype="password"
							v-model="componentData['openWB/general/notifications/configuration'].key">
						</text-input>
						<hr>
						<heading>
							Benachrichtigungen
						</heading>
						<buttongroup-input
							title="Beim Starten der Ladung"
							v-model="componentData['openWB/general/notifications/start_charging']"
							:buttons="[
								{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
								{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
							]">
						</buttongroup-input>
						<buttongroup-input
							title="Beim Stoppen der Ladung"
							v-model="componentData['openWB/general/notifications/stop_charging']"
							:buttons="[
								{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
								{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
							]">
						</buttongroup-input>
						<buttongroup-input
							title="Beim Einstecken eines Fahrzeugs"
							v-model="componentData['openWB/general/notifications/plug']"
							:buttons="[
								{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
								{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
							]">
						</buttongroup-input>
						<buttongroup-input
							title="Bei Triggern von Smart Home Aktionen"
							v-model="componentData['openWB/general/notifications/smart_home']"
							:buttons="[
								{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
								{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
							]">
						</buttongroup-input>
					</div>
				</card>

				<card title="Ladelog" v-if="componentData['openWB/general/extern'] === false">
					<number-input
						title="Preis je kWh"
						:min=0 :step=0.0001
						v-model="componentData['openWB/general/price_kwh']">
						<template #help>
							Dient zur Berechnung der Ladekosten im Ladelog.<br>
							Es können bis zu 4 Nachkommastellen genutzt werden.
						</template>
					</number-input>
					<buttongroup-input
						title="Einheit für Entfernungen"
						v-model="componentData['openWB/general/range_unit']"
						:buttons="[
							{buttonValue: 'km', text: 'Kilometer'},
							{buttonValue: 'mi', text: 'Meilen'}
						]">
						<template #help>
							ToDo: Hilfetext ergänzen!
						</template>
					</buttongroup-input>
				</card>

			</content>
		</div><!-- app -->

		<script>
			// define topics and default values here
			const componentDefaultData = {
				'openWB/general/extern': false,
				'openWB/general/extOpenWBDisplay': "normal",
				'openWB/general/control_interval': 10,
				'openWB/general/grid_protection_configured': false,
				'openWB/general/external_buttons_hw': false,
				'openWB/general/notifications/selected': "none",
				'openWB/general/notifications/configuration': {},
				'openWB/general/notifications/start_charging': false,
				'openWB/general/notifications/stop_charging': false,
				'openWB/general/notifications/plug': false,
				'openWB/general/notifications/smart_home': false,
				'openWB/general/price_kwh': 0.30,
				'openWB/general/range_unit': "km"
			}
		</script>
		<?php include_once './settings-2.vapp.php'; ?>

	</body>
</html>

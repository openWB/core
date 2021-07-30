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
		<div id="app" data-title="Allgemeine Einstellungen" data-footer="Allgemein">

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
					<h1>{{ title }}</h1>

					<form id="myForm">

						<card title="openWB">
							<buttongroup-input
								title="Nur Ladepunkt"
								ref="openWB/general/extern"
								toggle-selector='extOpenWBOn'
								:buttons="[
									{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
									{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
								]"
								:default-value=false>
								<template #help>
									Wird hier "Ja" gewählt ist diese openWB nur ein Ladepunkt und übernimmt keine eigene Regelung.
									Hier ist "Ja" zu wählen wenn, bereits eine openWB vorhanden ist und diese nur ein weiterer Ladepunkt der vorhandenen openWB sein soll.
									<span class="text-danger">Alle in dieser openWB getätigten Einstellungen werden NICHT beachtet.</span>
									An der Haupt openWB wird als Ladepunkt "externe openWB" gewählt und die IP Adresse eingetragen.
								</template>
							</buttongroup-input>
							<div v-show="visibility.extOpenWBOn">
								<select-input
									id="select1"
									title="Display-Theme"
									ref="openWB/general/extOpenWBDisplay"
									toggle-selector='displayTheme'
									:options="[
										{value: 'normal', text: 'Normal'},
										{value: 'parent', text: 'Display der übergeordneten openWB'}
									]"
									default-value="normal"
									:is-disabled='!visibility.extOpenWBOn'>
									<template #help>
										Das Theme "Normal" zeigt lediglich die Ladeleistung des Ladepunktes an. Änderungen sind nicht möglich.<br>
										Wird hier "Display der übergeordneten openWB" ausgewählt, dann ist die Anzeige identisch zum Display der regelnden openWB. Alle Anzeigen und Änderungen sind möglich.
									</template>
								</select-input>
							</div>
						</card>

						<card title="Hardware">
							<buttongroup-input
								title="Geschwindigkeit Regelintervall"
								ref="openWB/general/control_interval"
								:buttons="[
									{buttonValue: 10, text: 'Normal'},
									{buttonValue: 20, text: 'Langsam'},
									{buttonValue: 60, text: 'Sehr Langsam'}
								]"
								:default-value=10
								:is-disabled='visibility.extOpenWBOn'>
								<template #help>
									Sollten Probleme oder fehler auftreten, zunächst das Regelintervall auf "Normal" (10s) stellen.<br>
									Werden Module genutzt, welche z.B. eine Online-API nutzen oder soll langsamer geregelt werden, kann hier "Langsam" (20s) oder "Sehr Langsam" (60s) gewählt werden.<br>
									<span class="text-danger">Nicht nur die Regelung der PV-geführten Ladung, sondern auch Lademoduswechsel werden dann nur noch in diesem Intervall ausgeführt!</span>
								</template>
							</buttongroup-input>
							<buttongroup-input
								title="Netzschutz"
								ref="openWB/general/grid_protection_configured"
								:buttons="[
									{buttonValue: false, text: 'Aus'},
									{buttonValue: true, text: 'An'}
								]"
								:default-value=false
								:is-disabled='visibility.extOpenWBOn'>
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
								ref="openWB/general/external_buttons_hw"
								:buttons="[
									{buttonValue: false, text: 'Aus'},
									{buttonValue: true, text: 'An'}
								]"
								:default-value=false
								:is-disabled='visibility.extOpenWBOn'>
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

						<card title="Benachrichtigungen">
							<select-input
								title="Anbieter"
								ref="openWB/general/notifications/selected"
								toggle-selector="notificationProvider"
								:options="[
									{value: 'none', text: 'Kein Anbieter'},
									{value: 'pushover', text: 'Pushover'}
								]"
								default-value="none"
								:is-disabled='visibility.extOpenWBOn'>
							</select-input>
							<div v-show="visibility.notificationProvider=='pushover'">
								<alert
									subtype="info">
									<template #message>
										Zur Nutzung von Pushover muss ein Konto auf Pushover.net bestehen. Zudem muss im Pushover-Nutzerkonto eine Applikation openWB eingerichtet werden, um den benötigten API-Token/Key zu erhalten.<br>
										Wenn Pushover eingeschaltet ist, werden die Zählerstände aller konfigurierten Ladepunkte immer zum 1. des Monats gepusht.
									</template>
								</alert>
								<text-input
									title="Einstellungen"
									ref="ToDo/notifications/config"
									:is-disabled='visibility.extOpenWBOn || visibility.notificationProvider!="pushover"'>
									<template #help>
										ToDo: JSON aufteilen
									</template>
								</text-input>
								<!-- <text-input
									title="Pushover User Key"
									ref="ToDo/notifications/PushoverUser"
									subtype="user"
									:is-disabled='visibility.extOpenWBOn || visibility.notificationProvider!="pushover"'>
								</text-input>
								<password-input
									title="Pushover API-Token/Key"
									ref="ToDo/notifications/PushoverKey"
									:is-disabled='visibility.extOpenWBOn || visibility.notificationProvider!="pushover"'>
								</password-input> -->
								<hr>
								<heading>
									Benachrichtigungen
								</heading>
								<buttongroup-input
									title="Beim Starten der Ladung"
									ref="openWB/general/notifications/start_charging"
									:buttons="[
										{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
										{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
									]"
									:default-value=false
									:is-disabled='visibility.extOpenWBOn || visibility.notificationProvider!="pushover"'>
								</buttongroup-input>
								<buttongroup-input
									title="Beim Stoppen der Ladung"
									ref="openWB/general/notifications/stop_charging"
									:buttons="[
										{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
										{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
									]"
									:default-value=false
									:is-disabled='visibility.extOpenWBOn || visibility.notificationProvider!="pushover"'>
								</buttongroup-input>
								<buttongroup-input
									title="Beim Einstecken eines Fahrzeugs"
									ref="openWB/general/notifications/plug"
									:buttons="[
										{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
										{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
									]"
									:default-value=false
									:is-disabled='visibility.extOpenWBOn || visibility.notificationProvider!="pushover"'>
								</buttongroup-input>
								<buttongroup-input
									title="Bei Triggern von Smart Home Aktionen"
									ref="openWB/general/notifications/smart_home"
									:buttons="[
										{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
										{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
									]"
									:default-value=false
									:is-disabled='visibility.extOpenWBOn || visibility.notificationProvider!="pushover"'>
								</buttongroup-input>
							</div>
						</card>

						<card title="Ladelog">
							<number-input
								title="Preis je kWh"
								:min=0 :step=0.0001
								ref="openWB/general/price_kwh"
								:default-value=0.30
								:is-disabled='visibility.extOpenWBOn'>
								<template #help>
									Dient zur Berechnung der Ladekosten im Ladelog.<br>
									Es können bis zu 4 Nachkommastellen genutzt werden.
								</template>
							</number-input>
							<buttongroup-input
							title="Einheit für Entfernungen"
								ref="openWB/general/range_unit"
								:buttons="[
									{buttonValue: 'km', text: 'Kilometer'},
									{buttonValue: 'mi', text: 'Meilen'}
								]"
								default-value='km'
								:is-disabled='visibility.extOpenWBOn'>
								<template #help>
									ToDo: Hilfetext ergänzen!
								</template>
							</buttongroup-input>
						</card>

						<submit-buttons></submit-butons>

					</form>
				</div>

				<donation-banner></donation-banner>

			</div>  <!-- main container -->

			<page-footer :location='footer'></page-footer>

		</div><!-- app -->

		<script>
			$.get(
				{ url: "settings/navbar20.html", cache: false },
				function(data){
					$("#nav").replaceWith(data);
					// disable navbar entry for current page
					$('#navGeneral').addClass('disabled');
				}
			);
		</script>

		<?php include_once './settings.vapp.php'; ?>

	</body>
</html>

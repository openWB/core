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
					<h1>Allgemeine Einstellungen</h1>

					<form id="myForm">
						<div class="card border-secondary">
							<div class="card-header bg-secondary">
								<div class="form-group mb-0">
									<div class="form-row vaRow mb-1">
										<div class="col">
											openWB
										</div>
									</div>
								</div>
							</div>
							<div class="card-body">
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
							</div>
						</div>

						<div class="card border-secondary" v-show="!visibility.extOpenWBOn">
							<div class="card-header bg-secondary">
								<div class="form-group mb-0">
									<div class="form-row vaRow mb-1">
										<div class="col">
											Hardware-Einstellungen
										</div>
									</div>
								</div>
							</div>
							<div class="card-body">
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
							</div>
						</div>

						<div class="card border-secondary" v-show="!visibility.extOpenWBOn">
							<div class="card-header bg-secondary">
								<div class="form-group mb-0">
									<div class="form-row vaRow mb-1">
										<div class="col">
											Benachrichtigungen
										</div>
									</div>
								</div>
							</div>
							<div class="card-body">
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
										title="Pushover User Key"
										ref="ToDo/notifications/PushoverUser"
										subtype="user"
										:is-disabled='visibility.extOpenWBOn && visibility.notificationProvider!="pushover"'>
									</text-input>
									<password-input
										title="Pushover API-Token/Key"
										ref="ToDo/notifications/PushoverKey"
										:is-disabled='visibility.extOpenWBOn && visibility.notificationProvider!="pushover"'>
									</password-input>
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
										:is-disabled='visibility.extOpenWBOn && visibility.notificationProvider!="pushover"'>
									</buttongroup-input>
									<buttongroup-input
										title="Beim Stoppen der Ladung"
										ref="openWB/general/notifications/stop_charging"
										:buttons="[
											{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
											{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
										]"
										:default-value=false
										:is-disabled='visibility.extOpenWBOn && visibility.notificationProvider!="pushover"'>
									</buttongroup-input>
									<buttongroup-input
										title="Beim Einstecken eines Fahrzeugs"
										ref="openWB/general/notifications/plug"
										:buttons="[
											{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
											{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
										]"
										:default-value=false
										:is-disabled='visibility.extOpenWBOn && visibility.notificationProvider!="pushover"'>
									</buttongroup-input>
									<buttongroup-input
										title="Bei Triggern von Smart Home Aktionen"
										ref="openWB/general/notifications/smart_home"
										:buttons="[
											{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
											{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
										]"
										:default-value=false
										:is-disabled='visibility.extOpenWBOn && visibility.notificationProvider!="pushover"'>
									</buttongroup-input>
								</div>
							</div>
						</div>

						<div class="card border-secondary" v-show="!visibility.extOpenWBOn">
							<div class="card-header bg-secondary">
								<div class="form-group mb-0">
									<div class="form-row vaRow mb-1">
										<div class="col">
											Ladelog
										</div>
									</div>
								</div>
							</div>
							<div class="card-body">
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
					<small>Sie befinden sich hier: Einstellungen / Allgemein</small>
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

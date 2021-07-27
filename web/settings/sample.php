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
		<style>
			#saveprogress {
				background-color:white;
				position:fixed;
				top:0px;
				left:0px;
				width:100%;
				height:100%;
				z-index:999999;
				opacity: 90%;
			}
			#saveprogress-inner {
				margin-top: 150px;
				text-align: center;
			}
			#saveprogress-image {
				max-width: 300px;
			}
			#saveprogress-info {
				color:grey;
			}
		</style>
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
					<h1>Beispiel 1</h1>

					<form id="myForm">
						<div class="card border-secondary">
							<div class="card-header bg-secondary">
								<div class="form-group mb-0">
									<div class="form-row vaRow mb-1">
										<div class="col">
											Beispielelemente
										</div>
									</div>
								</div>
							</div>
							<div class="card-body">
								<text-input
									title="1. Text"
									ref="openWB/general/testText1"
									default-value="abc"
									:is-disabled='visibility.extOpenWBOn'>
									<template #help>
										Einfacher Text
									</template>
								</text-input>
								<text-input
									title="2. Text (E-Mail)"
									ref="openWB/general/testText2"
									subtype="email"
									:is-disabled='visibility.extOpenWBOn'>
									<template #help>
										Eingabefeld für E-Mailadressen
									</template>
								</text-input>
								<text-input
									title="3. Text (Host)"
									ref="openWB/general/testText3"
									subtype="host"
									:is-disabled='visibility.extOpenWBOn'>
									<template #help>
										Eingabefeld für Hosts (IP oder Namen)
									</template>
								</text-input>
								<text-input
									title="4. Text (URL)"
									ref="openWB/general/testText4"
									subtype="url"
									:is-disabled='visibility.extOpenWBOn'>
									<template #help>
										Eingabefeld für URLs
									</template>
								</text-input>
								<text-input
									title="5. Text (User)"
									ref="openWB/general/testText5"
									subtype="user"
									:is-disabled='visibility.extOpenWBOn'>
									<template #help>
										Eingabefeld für Benutzernamen
									</template>
								</text-input>
								<number-input
									title="1. Zahl"
									:min=5 :max=9 :step=2
									ref="openWB/general/testNumber1"
									:default-value=7
									unit="kW"
									:is-disabled='visibility.extOpenWBOn'>
									<template #help>
										Zahl mit Einheit
									</template>
								</number-input>
								<hr>
								<number-input
									title="2. Zahl"
									:min=10 :max=32 :step=2
									ref="openWB/general/testNumber2"
									:default-value=12
									:is-disabled='visibility.extOpenWBOn'>
									<template #help>
										Eingabefeld für Zahlen ohne Einheit
									</template>
								</number-input>
								<password-input
									title="1. Passwort"
									ref="openWB/general/testPassword"
									:is-disabled='visibility.extOpenWBOn'>
									<template #help>
										Das Passwort kann per Klick auf das Schloss oder Auge angezeigt werden.
									</template>
								</password-input>
								<range-input
									title="1. Range"
									:min=6 :max=32 :step=1
									ref="openWB/general/testRange1"
									:default-value=6
									unit="A"
									:is-disabled='visibility.extOpenWBOn'>
									<template #help>
										Range ohne spezielle Labels
									</template>
								</range-input>
								<range-input
									title="2. Range"
									:min=0 :max=11 :step=1
									ref="openWB/general/testRange2"
									:default-value=0
									unit="A"
									:labels='[{"label":"Aus","value":0},{"label":6,"value":6},{"label":7,"value":7},{"label":8,"value":8},{"label":9,"value":9},{"label":10,"value":10},{"label":11,"value":11},{"label":12,"value":12},{"label":13,"value":13},{"label":14,"value":14},{"label":15,"value":15},{"label":16,"value":16}]'
									:is-disabled='visibility.extOpenWBOn'>
									<template #help>
										Range mit speziellen Labels
									</template>
								</range-input>
								<textarea-input
									title="1. Textarea"
									ref="openWB/general/testTextarea1"
									default-value="abc"
									:is-disabled='visibility.extOpenWBOn'>
									<template #help>
										Textarea
									</template>
								</textarea-input>
								<select-input
									title="1. Select"
									ref="openWB/general/testSelect1"
									toggle-selector="select1"
									:options="[
										{value: 1, text: 'Eins'},
										{value: 2, text: 'Zwei'}
									]"
									:default-value=2
									:is-disabled='visibility.extOpenWBOn'>
									<template #help>
										Select mit einfachen Optionen
									</template>
								</select-input>
								<select-input
									title="2. Select"
									ref="openWB/general/testSelect2"
									toggle-selector="select2"
									:groups="[
										{label: 'Gruppe 1', options: [
											{value: 1, text: 'Eins'},
											{value: 2, text: 'Zwei'}
										] },
										{label: 'Gruppe 2', options: [
											{value: 3, text: 'Drei'},
											{value: 4, text: 'Vier'}
										] }
									]"
									:default-value=3
									:is-disabled='visibility.extOpenWBOn'>
									<template #help>
										Select mit Gruppen
									</template>
								</select-input>
								<buttongroup-input
									title="1. Button-Group"
									ref="openWB/general/testButtonGroup1"
									:buttons="[
										{buttonValue: 1, text: 'Eins'},
										{buttonValue: 2, text: 'Zwei'}
									]"
									:default-value=2
									:is-disabled='visibility.extOpenWBOn'>
									<template #help>
										Hilfetext
									</template>
								</buttongroup-input>
								<checkbox-input
									title="1. Checkbox"
									ref="openWB/general/testCheckbox1"
									:default-value=false
									:is-disabled='visibility.extOpenWBOn'>
									<template #help>
										Hilfetext
									</template>
								</checkbox-input>
								<hr>
								<alert>
									<template #message>
										Meldung ohne speziellen Subtype.
									</template>
								</alert>
								<alert
									subtype="info">
									<template #message>
										Infomeldung
									</template>
								</alert>
								<alert
									subtype="warning">
									<template #message>
										Warnmeldung
									</template>
								</alert>
								<alert
									subtype="danger">
									<template #message>
										Fehlermeldung
									</template>
								</alert>
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
					<small>Sie befinden sich hier: Einstellungen / Beispiel 1</small>
				</div>
			</footer>

		</div><!-- app -->

		<script>
			$.get(
				{ url: "settings/navbar20.html", cache: false },
				function(data){
					$("#nav").replaceWith(data);
					// disable navbar entry for current page
					$('#navbarSample1').addClass('disabled');
				}
			);
		</script>

		<?php include_once './settings.vapp.php'; ?>

	</body>
</html>

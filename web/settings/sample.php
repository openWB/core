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
		<!-- load topics -->
		<script src = "settings/topicsToSubscribe_sample.js?ver=20210712" ></script>
		<!-- load service -->
		<script src = "settings/setupMqttServices.js?ver=20201207" ></script>
		<!-- load mqtt handler-->
		<script src = "settings/processAllMqttMsg20.js?ver=20210712" ></script>
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
		<!-- Saveprogress with Progress Bar -->
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

		<div id="app">

			<div role="main" class="container pt-4 mt-3">
				<div id="content">
					<h1>{{ title }}</h1>

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
								<!-- <div v-show="visibility.extOpenWBOn"> ToDo: toggle visibility -->
								<div>
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
										:is-disabled='! visibility.extOpenWBOn'>
										<template #help>
											Hilfetext
										</template>
									</select-input>
								</div>
							</div>
						</div>

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
										Hilfetext
									</template>
								</text-input>
								<text-input
									title="2. Text (E-Mail)"
									ref="openWB/general/testText2"
									subtype="email"
									:is-disabled='visibility.extOpenWBOn'>
									<template #help>
										Hilfetext
									</template>
								</text-input>
								<text-input
									title="3. Text (Host)"
									ref="openWB/general/testText3"
									subtype="host"
									:is-disabled='visibility.extOpenWBOn'>
									<template #help>
										Hilfetext
									</template>
								</text-input>
								<text-input
									title="4. Text (URL)"
									ref="openWB/general/testText4"
									subtype="url"
									:is-disabled='visibility.extOpenWBOn'>
									<template #help>
										Hilfetext
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
										Hilfetext
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
										Hilfetext
									</template>
								</number-input>
								<password-input
									title="1. Passwort"
									ref="openWB/general/testPassword"
									:is-disabled='visibility.extOpenWBOn'>
									<template #help>
										Hilfetext
									</template>
								</password-input>
								<range-input
									title="1. Range"
									:min=6 :max=32 :step=2
									ref="openWB/general/testRange"
									:default-value=6
									unit="A"
									:is-disabled='visibility.extOpenWBOn'>
									<template #help>
										Hilfetext
									</template>
								</range-input>
								<textarea-input
									title="1. Textarea"
									ref="openWB/general/testTextarea1"
									default-value="abc"
									:is-disabled='visibility.extOpenWBOn'>
									<template #help>
										Hilfetext
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
									:default-value=2
									:is-disabled='visibility.extOpenWBOn'>
									<template #help>
										Hilfetext
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
										Info-Meldung
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
								<button id="saveSettingsBtn" type="button" class="btn btn-block btn-success">Speichern</button>
							</div>
							<div class="col-md-4 d-flex py-1 justify-content-center">
								<button id="modalResetBtn" type="button" class="btn btn-block btn-warning">Änderungen verwerfen</button>
							</div>
							<div class="col-md-4 d-flex py-1 justify-content-center">
								<button id="modalDefaultsBtn" type="button" class="btn btn-block btn-danger">Werkseinstellungen</button>
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

				<!-- modal set-defaults-confirmation window -->
				<div class="modal fade" id="setDefaultsConfirmationModal" role="dialog">
					<div class="modal-dialog" role="document">
						<div class="modal-content">
							<!-- modal header -->
							<div class="modal-header bg-danger">
								<h4 class="modal-title text-light">Achtung</h4>
							</div>
							<!-- modal body -->
							<div class="modal-body text-center">
								<p>
									Alle Einstellungen auf dieser Seite werden auf die Werkseinstellungen zurückgesetzt.<br>
									Sie müssen anschließend auf "Speichern" clicken, um die Werte zu übernehmen.
								</p>
								<p>
									Sollen die übergreifenden Ladeeinstellungen wirklich auf Werkseinstellungen zurückgesetzt werden?
								</p>
							</div>
							<!-- modal footer -->
							<div class="modal-footer d-flex justify-content-center">
								<button type="button" class="btn btn-success" data-dismiss="modal" id="saveDefaultsBtn">Fortfahren</button>
								<button type="button" class="btn btn-danger" data-dismiss="modal">Abbruch</button>
							</div>
						</div>
					</div>
				</div>

				<!-- modal reset-confirmation window -->
				<div class="modal fade" id="resetConfirmationModal" role="dialog">
					<div class="modal-dialog" role="document">
						<div class="modal-content">
							<!-- modal header -->
							<div class="modal-header bg-warning">
								<h4 class="modal-title">Achtung</h4>
							</div>
							<!-- modal body -->
							<div class="modal-body text-center">
								<p>
									Sollen die Änderungen wirklich zurückgesetzt werden?
								</p>
							</div>
							<!-- modal footer -->
							<div class="modal-footer d-flex justify-content-center">
								<button type="button" class="btn btn-success" data-dismiss="modal" id="resetBtn">Fortfahren</button>
								<button type="button" class="btn btn-danger" data-dismiss="modal">Abbruch</button>
							</div>
						</div>
					</div>
				</div>

				<!-- modal not-valid-confirmation window -->
				<div class="modal fade" id="formNotValidModal" role="dialog">
					<div class="modal-dialog" role="document">
						<div class="modal-content">
							<!-- modal header -->
							<div class="modal-header bg-danger">
								<h4 class="modal-title text-light">Fehler</h4>
							</div>
							<!-- modal body -->
							<div class="modal-body text-center">
								<p>
									Es wurden fehlerhafte Eingaben gefunden, speichern ist nicht möglich! Bitte überprüfen Sie alle Eingaben.
								</p>
							</div>
							<!-- modal footer -->
							<div class="modal-footer d-flex justify-content-center">
								<button type="button" class="btn btn-primary" data-dismiss="modal">Schließen</button>
							</div>
						</div>
					</div>
				</div>

				<!-- modal no-values-changed window -->
				<div class="modal fade" id="noValuesChangedInfoModal" role="dialog">
					<div class="modal-dialog" role="document">
						<div class="modal-content">
							<!-- modal header -->
							<div class="modal-header bg-info">
								<h4 class="modal-title text-light">Info</h4>
							</div>
							<!-- modal body -->
							<div class="modal-body text-center">
								<p>
									Es wurden keine geänderten Einstellungen gefunden.
								</p>
							</div>
							<!-- modal footer -->
							<div class="modal-footer d-flex justify-content-center">
								<button type="button" class="btn btn-success" data-dismiss="modal">Ok</button>
							</div>
						</div>
					</div>
				</div>

			</div>  <!-- container -->

			<footer id="footer" class="footer bg-dark text-light font-small">
				<div class="container text-center">
					<small>Sie befinden sich hier: {{ footer }}</small>
				</div>
			</footer>

		</div><!-- app -->

		<script>
			function saveSettings() {
				// sends all changed values by mqtt if valid
				var formValid = $("#myForm")[0].checkValidity();
				console.log("validity: "+formValid);
				if ( !formValid ) {
					$('#formNotValidModal').modal();
					return;
				};
				getChangedValues();
				sendValues();
			}

			function visibility(element) {
				// nothing here
			}

			$(function() {
				$('#saveSettingsBtn').on("click",function() {
					console.log("saving settings...");
					saveSettings();
				});

				$('#modalResetBtn').on("click",function() {
					$('#resetConfirmationModal').modal();
				});

				$('#resetBtn').on('click',function() {
					console.log("resetting input elements...");
					for (element in vApp.$refs) {
						console.log(element);
						vApp.$refs[element].resetValue();
					};
				})

				$('#modalDefaultsBtn').on("click",function() {
					$('#setDefaultsConfirmationModal').modal();
				});

				$('#saveDefaultsBtn').on("click",function() {
					console.log("setting defaults...");
					for (element in vApp.$refs) {
						console.log(element);
						vApp.$refs[element].setDefaultValue();
					};
				});
			});
		</script>

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

		<!-- vue templates start here -->

		<script type="text/x-template" id="text-input-template">
			<div class="form-row mb-1">
				<label v-on:click="toggleHelp" class="col-md-4 col-form-label">
					{{ title }}
					<i v-if="this.$slots.help" class="fa-question-circle" :class="showHelp ? 'fas text-info' : 'far'"></i>
				</label>
				<div class="col-md-8">
					<div class="form-row">
						<div class="input-group">
							<div v-if="subtype != 'text'" class="input-group-prepend">
								<div class="input-group-text">
									<i v-if="subtype == 'email'" class="fa fa-fw fa-envelope"></i>
									<i v-if="subtype == 'host'" class="fas fa-fw fa-network-wired"></i>
									<i v-if="subtype == 'url'" class="fas fa-fw fa-globe"></i>
								</div>
							</div>
							<input v-if="subtype === 'text'" type="text" class="form-control" v-model="value" :disabled="disabled" :pattern="pattern">
							<input v-if="subtype === 'host'" type="text" class="form-control" v-model="value" :disabled="disabled" pattern="^(((\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.){3}(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])|[A-Za-z0-9\._\-]*)$">
							<input v-if="['email', 'url'].includes(subtype)" :type="subtype" class="form-control" v-model="value" :disabled="disabled">
						</div>
					</div>
					<span v-if="showHelp" class="form-row alert alert-info my-1 small">
						<slot name="help"></slot>
					</span>
				</div>
			</div>
		</script>

		<script type="text/x-template" id="password-input-template">
			<div class="form-row mb-1">
				<label v-on:click="toggleHelp" class="col-md-4 col-form-label">
					{{ title }}
					<i v-if="this.$slots.help" class="fa-question-circle" :class="showHelp ? 'fas text-info' : 'far'"></i>
				</label>
				<div class="col-md-8">
					<div class="form-row">
						<div class="input-group">
							<div class="input-group-prepend" v-on:click="togglePassword">
								<div class="input-group-text">
									<i class="fa fa-fw" :class="showPassword ? 'fa-unlock' : 'fa-lock'"></i>
								</div>
							</div>
							<input :type="showPassword ? 'text' : 'password'" class="form-control" v-model="value" :disabled="disabled">
						</div>
					</div>
					<span v-if="showHelp" class="form-row alert alert-info my-1 small">
						<slot name="help"></slot>
					</span>
				</div>
			</div>
		</script>

		<script type="text/x-template" id="number-input-template">
			<div class="form-row mb-1">
				<label v-on:click="toggleHelp" class="col-md-4 col-form-label">
					{{ title }}
					<i v-if="this.$slots.help" class="fa-question-circle" :class="showHelp ? 'fas text-info' : 'far'"></i>
				</label>
				<div class="col-md-8">
					<div class="form-row">
						<div class="input-group">
							<input type="number" class="form-control" :min="min" :max="max" :step="step" v-model.number="value" :disabled="disabled">
							<div v-if="unit" class="input-group-append">
								<div class="input-group-text">
									{{ unit }}
								</div>
							</div>
						</div>
					</div>
					<span v-if="showHelp" class="form-row alert alert-info my-1 small">
						<slot name="help"></slot>
					</span>
				</div>
			</div>
		</script>

		<script type="text/x-template" id="range-input-template">
			<div class="form-row mb-1">
				<label v-on:click="toggleHelp" class="col-md-4 col-form-label">
					{{ title }}
					<i v-if="this.$slots.help" class="fa-question-circle" :class="showHelp ? 'fas text-info' : 'far'"></i>
				</label>
				<div class="col-md-8">
					<div class="form-row vaRow mb-1">
						<label for="XXX" class="col-2 col-form-label valueLabel">{{ value }} {{ unit }}</label>
						<div class="col-10">
							<!-- <input type="range" class="form-control-range rangeInput" :min="min" :max="max" :step="step" v-model="value" :disabled="disabled"> -->
							<input type="range" class="form-control-range rangeInput" :min="min" :max="max" :step="step" v-model.number="value" :disabled="disabled">
						</div>
					</div>
					<span v-if="showHelp" class="form-row alert alert-info my-1 small">
						<slot name="help"></slot>
					</span>
				</div>
			</div>
		</script>

		<script type="text/x-template" id="textarea-input-template">
			<div class="form-row mb-1">
				<label v-on:click="toggleHelp" class="col-md-4 col-form-label">
					{{ title }}
					<i v-if="this.$slots.help" class="fa-question-circle" :class="showHelp ? 'fas text-info' : 'far'"></i>
				</label>
				<div class="col-md-8">
					<div class="form-row">
						<textarea class="form-control" :disabled="disabled">{{ value }}</textarea>
					</div>
					<span v-if="showHelp" class="form-row alert alert-info my-1 small">
						<slot name="help"></slot>
					</span>
				</div>
			</div>
		</script>

		<script type="text/x-template" id="select-input-template">
			<div class="form-row mb-1">
				<label v-on:click="toggleHelp" class="col-md-4 col-form-label">
					{{ title }}
					<i v-if="this.$slots.help" class="fa-question-circle" :class="showHelp ? 'fas text-info' : 'far'"></i>
				</label>
				<div class="col-md-8">
					<div class="form-row">
						<select class="form-control" v-model="value" :disabled="disabled">
							<!-- select elements without option groups -->
							<option v-for="(option) in options" :value="option.value">{{ option.text }}</option>
							<!-- option groups with options -->
							<optgroup v-for="(group) in groups" :label="group.label">
								<option v-for="(option) in group.options" :value="option.value">{{ option.text }}</option>
							</optgroup>
						</select>
					</div>
					<span v-if="showHelp" class="form-row alert alert-info my-1 small">
						<slot name="help"></slot>
					</span>
				</div>
			</div>
		</script>

		<script type="text/x-template" id="buttongroup-input-template">
			<div class="form-row mb-1">
				<label v-on:click="toggleHelp" class="col-md-4 col-form-label">
					{{ title }}
					<i v-if="this.$slots.help" class="fa-question-circle" :class="showHelp ? 'fas text-info' : 'far'"></i>
				</label>
				<div class="col-md-8">
					<div class="form-row">
						<div class="btn-group btn-block btn-group-toggle">
							<label v-for="button in buttons" class="btn" :class="[ value == button.buttonValue ? 'active' : '', button.class ? button.class : 'btn-outline-info', disabled ? 'disabled' : '' ]">
								<input type="radio" v-model="value" :value="button.buttonValue" :disabled="disabled">{{ button.text }}
								<i v-if="value == button.buttonValue" class="" :class="[ button.icon ? button.icon : 'fas fa-check']"></i>
							</label>
						</div>
					</div>
					<span v-if="showHelp" class="form-row alert alert-info my-1 small">
						<slot name="help"></slot>
					</span>
				</div>
			</div>
		</script>

		<script type="text/x-template" id="checkbox-input-template">
			<div class="form-row mb-1">
				<label v-on:click="toggleHelp" class="col-md-4 col-form-label">
					{{ title }}
					<i v-if="this.$slots.help" class="fa-question-circle" :class="showHelp ? 'fas text-info' : 'far'"></i>
				</label>
				<div class="col-md-8">
					<div class="form-row">
						<!-- <input type="checkbox" v-model="value" :disabled="disabled" data-toggle="toggle" :data-on="labelOn" :data-off="labelOff" :data-onstyle="styleOn" :data-offstyle="styleOff" :data-style="style"> -->
						<input class="form-control" type="checkbox" v-model="value" :disabled="disabled">
					</div>
					<span v-if="showHelp" class="form-row alert alert-info my-1 small">
						<slot name="help"></slot>
					</span>
				</div>
			</div>
		</script>

		<script type="text/x-template" id="alert-template">
			<div class="card-text alert" :class="'alert-'+subtype">
				<slot name="message"></slot>
			</div>
		</script>

		<!-- vue apps start here -->
		<script>
			const textInputComponent = {
				template: '#text-input-template',
				props: {
					title: String,
					defaultValue: { type: String, default: "" },
					isDisabled: { type: Boolean, default: false },
					toggleSelector: String,
					subtype: { validator: function(value){
						return ['text', 'email', 'host', 'url'].indexOf(value) !== -1;
						}, default: 'text'
					},
					pattern: String
				},
				data() {
					return {
						value: this.defaultValue,
						initialValue: this.defaultValue,
						showHelp: false
					}
				},
				computed: {
					disabled() {
						return this.isDisabled;
					},
					changed() {
						return this.value != this.initialValue;
					}
				},
				watch: {
					value(newValue) {
						var toggleSelector = this.toggleSelector;
						if(toggleSelector) {
							var appData = this.$root.$data['visibility'];
							appData[toggleSelector] = newValue;
						}
					}
				},
				methods: {
					setInitialValue(newDefault) {
						this.initialValue = newDefault;
					},
					resetValue() {
						this.value = this.initialValue;
					},
					setDefaultValue() {
						this.value = this.defaultValue;
					},
					toggleHelp() {
						this.showHelp = !this.showHelp && this.$slots.help;
					}
				}
			};

			const passwordInputComponent = {
				template: '#password-input-template',
				props: {
					title: String,
					defaultValue: { type: String, default: "" },
					isDisabled: { type: Boolean, default: false },
					toggleSelector: String
				},
				data() {
					return {
						value: this.defaultValue,
						initialValue: this.defaultValue,
						showHelp: false,
						showPassword: false
					}
				},
				computed: {
					disabled() {
						return this.isDisabled;
					},
					changed() {
						return this.value != this.initialValue;
					}
				},
				watch: {
					value(newValue) {
						var toggleSelector = this.toggleSelector;
						if(toggleSelector) {
							var appData = this.$root.$data['visibility'];
							appData[toggleSelector] = newValue;
						}
					}
				},
				methods: {
					setInitialValue(newDefault) {
						this.initialValue = newDefault;
					},
					resetValue() {
						this.value = this.initialValue;
					},
					setDefaultValue() {
						this.value = this.defaultValue;
					},
					toggleHelp() {
						this.showHelp = !this.showHelp && this.$slots.help;
					},
					togglePassword() {
						this.showPassword = !this.showPassword;
					}
				}
			};

			const numberInputComponent = {
				template: '#number-input-template',
				props: {
					title: String,
					defaultValue: { type: Number, default: 0 },
					isDisabled: { type: Boolean, default: false },
					toggleSelector: String,
					unit: String,
					min: Number,
					max: Number,
					step: Number
				},
				data() {
					return {
						value: this.defaultValue,
						initialValue: this.defaultValue,
						showHelp: false
					}
				},
				computed: {
					disabled() {
						return this.isDisabled;
					},
					changed() {
						return this.value != this.initialValue;
					}
				},
				watch: {
					value(newValue) {
						var toggleSelector = this.toggleSelector;
						if(toggleSelector) {
							var appData = this.$root.$data['visibility'];
							appData[toggleSelector] = newValue;
						}
					}
				},
				methods: {
					setInitialValue(newDefault) {
						this.initialValue = newDefault;
					},
					resetValue() {
						this.value = this.initialValue;
					},
					setDefaultValue() {
						this.value = this.defaultValue;
					},
					toggleHelp() {
						this.showHelp = !this.showHelp && this.$slots.help;
					}
				}
			};

			const rangeInputComponent = {
				template: '#range-input-template',
				props: {
					title: String,
					defaultValue: { type: Number, default: 0 },
					isDisabled: { type: Boolean, default: false },
					toggleSelector: String,
					unit: String,
					min: { type: Number, default: 0 },
					max: { type: Number, default: 100 },
					step: { type: Number, default: 1 }
				},
				data() {
					return {
						value: this.defaultValue,
						initialValue: this.defaultValue,
						showHelp: false
					}
				},
				computed: {
					disabled() {
						return this.isDisabled;
					},
					changed() {
						return this.value != this.initialValue;
					}
				},
				watch: {
					value(newValue) {
						var toggleSelector = this.toggleSelector;
						if(toggleSelector) {
							var appData = this.$root.$data['visibility'];
							appData[toggleSelector] = newValue;
						}
					}
				},
				methods: {
					setInitialValue(newDefault) {
						this.initialValue = newDefault;
					},
					resetValue() {
						this.value = this.initialValue;
					},
					setDefaultValue() {
						this.value = this.defaultValue;
					},
					toggleHelp() {
						this.showHelp = !this.showHelp && this.$slots.help;
					}
				}
			};

			const textareaInputComponent = {
				template: '#textarea-input-template',
				props: {
					title: String,
					defaultValue: { type: String, default: "" },
					isDisabled: { type: Boolean, default: false },
					toggleSelector: String
				},
				data() {
					return {
						value: this.defaultValue,
						initialValue: this.defaultValue,
						showHelp: false
					}
				},
				computed: {
					disabled() {
						return this.isDisabled;
					},
					changed() {
						return this.value != this.initialValue;
					}
				},
				watch: {
					value(newValue) {
						var toggleSelector = this.toggleSelector;
						if(toggleSelector) {
							var appData = this.$root.$data['visibility'];
							appData[toggleSelector] = newValue;
						}
					}
				},
				methods: {
					setInitialValue(newDefault) {
						this.initialValue = newDefault;
					},
					resetValue() {
						this.value = this.initialValue;
					},
					setDefaultValue() {
						this.value = this.defaultValue;
					},
					toggleHelp() {
						this.showHelp = !this.showHelp && this.$slots.help;
					}
				}
			};

			const selectInputComponent = {
				template: '#select-input-template',
				props: {
					title: String,
					defaultValue: { type: [String, Number], default: "" },
					isDisabled: { type: Boolean, default: false },
					toggleSelector: String,
					groups: Object,
					options: Object
				},
				data() {
					return {
						value: this.defaultValue,
						initialValue: this.defaultValue,
						showHelp: false
					}
				},
				computed: {
					disabled() {
						return this.isDisabled;
					},
					changed() {
						return this.value != this.initialValue;
					}
				},
				watch: {
					value(newValue) {
						var toggleSelector = this.toggleSelector;
						console.log("toggleSelector: "+toggleSelector);
						if(toggleSelector) {
							var done = false;
							var appData = this.$root.$data['visibility'];
							this.options.some(function(option){
								console.log("option check: "+newValue);
								if(option.value === newValue) {
									appData[toggleSelector] = newValue;
									done = true;
									return true;
								}
							});
							if(!done){
								this.groups.some(function(group){
									console.log("group check: "+newValue);
									return group.options.some(function(option){
										console.log("option check: "+newValue);
										if(option.value === newValue) {
											appData[toggleSelector] = newValue;
											done = true;
											return true;
										}
									});
								});
							}
						}
					}
				},
				methods: {
					setInitialValue(newDefault) {
						this.initialValue = newDefault;
					},
					resetValue() {
						this.value = this.initialValue;
					},
					setDefaultValue() {
						this.value = this.defaultValue;
					},
					toggleHelp() {
						this.showHelp = !this.showHelp && this.$slots.help;
					}
				}
			};

			const buttongroupInputComponent = {
				template: '#buttongroup-input-template',
				props: {
					title: String,
					defaultValue: [String, Number, Boolean],
					isDisabled: { type: Boolean, default: false },
					toggleSelector: String,
					buttons: Object
				},
				data() {
					return {
						value: this.defaultValue,
						initialValue: this.defaultValue,
						showHelp: false
					}
				},
				computed: {
					disabled() {
						return this.isDisabled;
					},
					changed() {
						return this.value != this.initialValue;
					}
				},
				watch: {
					value(newValue) {
						var toggleSelector = this.toggleSelector;
						if(toggleSelector) {
							var appData = this.$root.$data['visibility'];
							this.buttons.forEach(function(button){
								if(button.buttonValue === newValue) {
									appData[toggleSelector] = newValue;
								}
							});
						}
					}
				},
				methods: {
					setInitialValue(newDefault) {
						this.initialValue = newDefault;
					},
					resetValue() {
						this.value = this.initialValue;
					},
					setDefaultValue() {
						this.value = this.defaultValue;
					},
					toggleHelp() {
						this.showHelp = !this.showHelp && this.$slots.help;
					}
				}
			};

			const checkboxInputComponent = {
				template: '#checkbox-input-template',
				props: {
					title: String,
					defaultValue: { type: Boolean, default: false },
					isDisabled: { type: Boolean, default: false },
					toggleSelector: String
				},
				data() {
					return {
						value: this.defaultValue,
						initialValue: this.defaultValue,
						showHelp: false,
					}
				},
				computed: {
					disabled() {
						return this.isDisabled;
					},
					changed() {
						return this.value != this.initialValue;
					}
				},
				watch: {
					value(newValue) {
						var toggleSelector = this.toggleSelector;
						if(toggleSelector) {
							var appData = this.$root.$data['visibility'];
							appData[toggleSelector] = newValue;
						}
					}
				},
				methods: {
					setInitialValue(newDefault) {
						this.initialValue = newDefault;
					},
					resetValue() {
						this.value = this.initialValue;
					},
					setDefaultValue() {
						this.value = this.defaultValue;
					},
					toggleHelp() {
						this.showHelp = !this.showHelp && this.$slots.help;
					}
				}
			};

			const alertComponent = {
				template: '#alert-template',
				props: {
					subtype: { validator: function(value){
						return ['info', 'success', 'warning', 'danger', 'primary', 'secondary', 'light', 'dark'].indexOf(value) !== -1;
						}, default: 'secondary'
					}
				}
			};

			const ContentApp = {
				data() {
					return {
						title: "Allgemeine Einstellungen",
						footer: "Einstellungen / Allgemein",
						visibility: {
							extOpenWBOn: false
						}
					}
				},
				components: {
					'text-input': textInputComponent,
					'password-input': passwordInputComponent,
					'number-input': numberInputComponent,
					'range-input': rangeInputComponent,
					'textarea-input': textareaInputComponent,
					'select-input': selectInputComponent,
					'buttongroup-input': buttongroupInputComponent,
					'checkbox-input': checkboxInputComponent,
					'alert': alertComponent
				}
			}

			const vApp = Vue.createApp(ContentApp).mount('#app');
		</script>

	</body>
</html>

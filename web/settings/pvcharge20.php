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
			<content title="Einstellungen PV-Laden" footer="PV-Laden">

				<card title="PV-Laden">
					<buttongroup-input
						title="Regelmodus"
						ref="ToDo/pv_charge/control_mode"
						toggle-selector='controlmode'
						:buttons="[
							{buttonValue: 'export', text: 'Einspeisung'},
							{buttonValue: 'import', text: 'Bezug'},
							{buttonValue: 'individual', text: 'Individuell'}
						]"
						default-value='export'>
						<template #help>
							ToDo
						</template>
					</buttongroup-input>
					<text-input
						title="Regelbereich"
						ref="openWB/general/chargemode_config/pv_charging/control_range"
						default-value="abc"
						:is-disabled='visibility.extOpenWBOn'>
						<template #help>
							ToDo
						</template>
					</text-input>
					<div v-show='visibility.controlmode=="individual"'>
						<number-input
							title="Minimum"
							:min=-10000 :max=10000
							ref="ToDo/pv_charge/control_min"
							:default-value=-230
							unit="W"
							:is-disabled='visibility.controlmode!="individual"'>
							<template #help>
								ToDo
							</template>
						</number-input>
						<number-input
							title="Maximum"
							:min=-10000 :max=10000
							ref="ToDo/pv_charge/control_max"
							:default-value=0
							unit="W"
							:is-disabled='visibility.controlmode!="individual"'>
							<template #help>
								ToDo
							</template>
						</number-input>
					</div>
					<number-input
						title="Regelpunkt Einspeisegrenze"
						:min=0 :step=100
						ref="openWB/general/chargemode_config/pv_charging/feed_in_yield"
						:default-value=0
						unit="W">
						<template #help>
							Parameter für den 70%-Regelpunkt im Modus PV-Laden. Dieser Parameter ist nur wirksam bei der Einstellung "70%-Regelung eingeschaltet". Der hier eingetragene Wert sollte zur optimalen Eigenverbrauchssteuerung 70% der installierten Generatorleistung betragen.<br>
							Die Nutzung dieser Option ergibt nur Sinn wenn ein Wechselrichter und Smartmeter verbaut ist welches eine dynamische Begrenzung der Einspeiseleistung bietet.
						</template>
					</number-input>
					<hr>
					<number-input
						title="Einschaltschwelle"
						:min=0 :step=1
						ref="openWB/general/chargemode_config/pv_charging/switch_on_threshold"
						:default-value=1320
						unit="W">
					</number-input>
					<number-input
						title="Einschaltverzögerung"
						:min=0 :step=1
						ref="openWB/general/chargemode_config/pv_charging/switch_on_delay"
						:default-value=20
						unit="W">
					</number-input>
					<hr>
					<number-input
						title="Abschaltschwelle"
						:min=0 :step=1
						ref="openWB/general/chargemode_config/pv_charging/switch_off_threshold"
						:default-value=0
						unit="W">
					</number-input>
					<number-input
						title="Abschaltverzögerung"
						:min=0 :step=1
						ref="openWB/general/chargemode_config/pv_charging/switch_off_delay"
						:default-value=60
						unit="W">
					</number-input>
				</card>
				<card title="Phasenumschaltung">
					<buttongroup-input
						title="Anzahl Phasen"
						ref="openWB/general/chargemode_config/pv_charging/phases_to_use"
						toggle-selector="pvPhases"
						:buttons="[
							{buttonValue: 1, text: '1'},
							{buttonValue: 3, text: 'Maximum'},
							{buttonValue: 0, text: 'Automatisch'}
						]"
						:default-value=0>
						<template #help>
							ToDo
						</template>
					</buttongroup-input>
					<div v-show='visibility.pvPhases=="auto"'>
						<range-input
							title="Schaltzeiten Automatikmodus"
							:min=1 :max=15 :step=1
							ref="openWB/general/chargemode_config/pv_charging/phase_switch_delay"
							:default-value=8
							unit="Minuten"
							:is-disabled='visibility.pvPhases!="auto"'>
							<template #help>
								Um zu viele Schaltungen im Automatikmodus zu vermeiden, wird hier definiert, wann die Umschaltung erfolgen soll. Ist bei einphasigen Laden für durchgehend x Minuten die Maximalstromstärke erreicht, wird auf dreiphasige Ladung umgestellt. Ist die Ladung nur für ein Intervall unterhalb der Maximalstromstärke, beginnt der Counter für die Umschaltung erneut. Ist die Ladung im dreiphasigen Modus für 16 - x Minuten bei der Minimalstromstärke, wird wieder auf einphasige Ladung gewechselt.<br>
								Standardmäßig ist dieser Wert bei 8 Minuten, sprich nach 8 Minuten Maximalstromstärke wird auf 3 Phasige Ladung umgestellt und nach 16 - 8 = 8 Minuten bei Minimalstromstärke wird wieder auf einphasige Ladung gewechselt.
							</template>
						</range-input>
					</div>
				</card>
				<card title="Speicher-Beachtung">
					<buttongroup-input
						title="Priorisierung"
						ref="openWB/general/chargemode_config/pv_charging/bat_prio"
						:buttons="[
							{buttonValue: false, text: 'Fahrzeuge'},
							{buttonValue: true, text: 'Speicher'}
						]"
						:default-value='true'>
						<template #help>
							ToDo
						</template>
					</buttongroup-input>
					<range-input
						title="Einschalt-SoC"
						:min=0 :max=19 :step=1
						ref="openWB/general/chargemode_config/pv_charging/switch_on_soc"
						:default-value=0
						unit="%"
						:labels='[{"label":"Aus","value":0},{"label":5,"value":5},{"label":10,"value":10},{"label":15,"value":15},{"label":20,"value":20},{"label":25,"value":25},{"label":30,"value":30},{"label":35,"value":35},{"label":40,"value":40},{"label":45,"value":45},{"label":50,"value":50},{"label":55,"value":55},{"label":60,"value":60},{"label":65,"value":65},{"label":70,"value":70},{"label":75,"value":75},{"label":80,"value":80},{"label":85,"value":85},{"label":90,"value":90},{"label":95,"value":95}]'>
						<template #help>
							ToDo
						</template>
					</range-input>
					<range-input
						title="Ausschalt-SoC"
						:min=0 :max=19 :step=1
						ref="openWB/general/chargemode_config/pv_charging/switch_off_soc"
						:default-value=0
						unit="%"
						:labels='[{"label":"Aus","value":0},{"label":5,"value":5},{"label":10,"value":10},{"label":15,"value":15},{"label":20,"value":20},{"label":25,"value":25},{"label":30,"value":30},{"label":35,"value":35},{"label":40,"value":40},{"label":45,"value":45},{"label":50,"value":50},{"label":55,"value":55},{"label":60,"value":60},{"label":65,"value":65},{"label":70,"value":70},{"label":75,"value":75},{"label":80,"value":80},{"label":85,"value":85},{"label":90,"value":90},{"label":95,"value":95}]'>
						<template #help>
							ToDo
						</template>
					</range-input>
					<number-input
						title="Reservierte Ladeleistung"
						:min=0 :step=100
						ref="openWB/general/chargemode_config/pv_charging/charging_power_reserve"
						:default-value=0
						unit="W">
						<template #help>
							ToDo
						</template>
					</number-input>
					<number-input
						title="Erlaubte Entladeleistung"
						:min=0 :step=100
						ref="openWB/general/chargemode_config/pv_charging/rundown_power"
						:default-value=0
						unit="W">
						<template #help>
							ToDo
						</template>
					</number-input>
					<range-input
						title="Minimaler Entlade-SoC"
						:min=0 :max=20 :step=1
						ref="openWB/general/chargemode_config/pv_charging/rundown_soc"
						:default-value=0
						unit="%"
						:labels='[{"label":0,"value":0},{"label":5,"value":5},{"label":10,"value":10},{"label":15,"value":15},{"label":20,"value":20},{"label":25,"value":25},{"label":30,"value":30},{"label":35,"value":35},{"label":40,"value":40},{"label":45,"value":45},{"label":50,"value":50},{"label":55,"value":55},{"label":60,"value":60},{"label":65,"value":65},{"label":70,"value":70},{"label":75,"value":75},{"label":80,"value":80},{"label":85,"value":85},{"label":90,"value":90},{"label":95,"value":95},{"label":"Aus","value":100}]'>
						<template #help>
							ToDo
						</template>
					</range-input>
				</card>

			</content>
		</div><!-- app -->

		<script>
			$.get(
				{ url: "settings/navbar20.html", cache: false },
				function(data){
					$("#nav").replaceWith(data);
					// disable navbar entry for current page
					$('#navPVCharge').addClass('disabled');
				}
			);
		</script>

		<?php include_once './settings.vapp.php'; ?>

	</body>
</html>

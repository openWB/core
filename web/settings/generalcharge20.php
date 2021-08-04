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
			<content title="Allgemeine Einstellungen der Lademodi" footer="Lademodi">

				<!-- hidden toggle-only components: BEGIN -->
				<buttongroup-input
					title="Nur Ladepunkt"
					ref="openWB/general/extern"
					:is-hidden="true"
					toggle-selector='extOpenWBOn'
					:buttons="[
						{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
						{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
					]"
					:default-value=false>
				</buttongroup-input>
				<!-- hidden toggle-only components: END -->

				<card title="Allgemein">
					<div v-show="visibility.extOpenWBOn">
						<alert
							subtype="info">
							Diese Einstellungen sind nicht verfügbar, solange sich diese openWB im Modus "Nur Ladepunkt" befindet.
						</alert>
					</div>
					<div v-show="!visibility.extOpenWBOn">
						<buttongroup-input
							title="Lademodus"
							ref="openWB/general/chargemode_config/individual_mode"
							:buttons="[
								{buttonValue: false, text: 'Einheitlich'},
								{buttonValue: true, text: 'Individuell'}
							]"
							:default-value=false
							:is-disabled='visibility.extOpenWBOn'>
							<template #help>
								ToDo
							</template>
						</buttongroup-input>
						<hr>
						<buttongroup-input
							title="Begrenzung der Schieflast"
							ref="openWB/general/chargemode_config/unbalanced_load"
							toggle-selector='unbalancedOn'
							:buttons="[
								{buttonValue: false, text: 'Nein', class: 'btn-outline-danger', icon: 'fas fa-times'},
								{buttonValue: true, text: 'Ja', class: 'btn-outline-success'}
							]"
							:default-value=false
							:is-disabled='visibility.extOpenWBOn'>
							<template #help>
								ToDo
							</template>
						</buttongroup-input>
						<div v-show="visibility.unbalancedOn">
							<range-input
								title="Erlaubte Schieflast"
								:min=10 :max=32 :step=1
								ref="openWB/general/chargemode_config/unbalanced_load_limit"
								:default-value=20
								unit="A"
								:is-disabled='!visibility.unbalancedOn || visibility.extOpenWBOn'>
								<template #help>
									ToDo
								</template>
							</range-input>
						</div>
					</div>
				</card>

			</content>
		</div><!-- app -->

		<script>
			$.get(
				{ url: "settings/navbar20.html", cache: false },
				function(data){
					$("#nav").replaceWith(data);
					// disable navbar entry for current page
					$('#navGeneralCharge').addClass('disabled');
				}
			);
		</script>

		<?php include_once './settings.vapp.php'; ?>

	</body>
</html>

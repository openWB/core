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
			<content title="Beispiele" footer="Beispiele" nav="navbarSample2">

				<card title="Einfache Eingabefelder">
					<text-input
						title="1. Text"
						v-model="componentData['openWB/general/testText1']">
						<template #help>
							Einfacher Text
						</template>
					</text-input>
					<text-input
						title="2. Text (E-Mail)"
						subtype="email"
						v-model="componentData['openWB/general/testText2']">
						<template #help>
							Eingabefeld für E-Mailadressen
						</template>
					</text-input>
					<text-input
						title="3. Text (Host)"
						subtype="host"
						v-model="componentData['openWB/general/testText3']">
						<template #help>
							Eingabefeld für Hosts (IP oder Namen)
						</template>
					</text-input>
					<text-input
						title="4. Text (URL)"
						subtype="url"
						v-model="componentData['openWB/general/testText4']">
						<template #help>
							Eingabefeld für URLs
						</template>
					</text-input>
					<text-input
						title="5. Text (User)"
						subtype="user"
						v-model="componentData['openWB/general/testText5']">
						<template #help>
							Eingabefeld für Benutzernamen
						</template>
					</text-input>
					<hr>
					<number-input
						title="1. Zahl"
						:min=5 :max=9 :step=2
						unit="kW"
						v-model="componentData['openWB/general/testNumber1']">
						<template #help>
							Zahl mit Einheit
						</template>
					</number-input>
					<number-input
						title="2. Zahl"
						:min=10 :max=32 :step=2
						v-model="componentData['openWB/general/testNumber2']">
						<template #help>
							Eingabefeld für Zahlen ohne Einheit
						</template>
					</number-input>
					<text-input
						title="1. Passwort"
						subtype="password"
						v-model="componentData['openWB/general/testPassword1']">
						<template #help>
							Das Passwort kann per Klick auf das Schloss oder Auge angezeigt werden.
						</template>
					</text-input>
					<hr>
					<textarea-input
						title="1. Textarea"
						v-model="componentData['openWB/general/testTextarea1']">
						<template #help>
							Textarea
						</template>
					</textarea-input>
				</card>

				<card title="Spezielle Elemente">
					<range-input
						title="1. Range"
						:min=6 :max=32 :step=1
						v-model="componentData['openWB/general/testRange1']"
						unit="A">
						<template #help>
							Range ohne spezielle Labels
						</template>
					</range-input>
					<range-input
						title="2. Range"
						:min=0 :max=11 :step=1
						v-model="componentData['openWB/general/testRange2']"
						unit="A"
						:labels='[{"label":"Aus","value":0},{"label":6,"value":6},{"label":7,"value":7},{"label":8,"value":8},{"label":9,"value":9},{"label":10,"value":10},{"label":11,"value":11},{"label":12,"value":12},{"label":13,"value":13},{"label":14,"value":14},{"label":15,"value":15},{"label":16,"value":16}]'>
						<template #help>
							Range mit speziellen Labels
						</template>
					</range-input>
					<hr>
					<select-input
						title="1. Select"
						v-model="componentData['openWB/general/testSelect1']"
						:options="[
							{value: 1, text: 'Eins'},
							{value: 2, text: 'Zwei'}
						]">
						<template #help>
							Select mit einfachen Optionen
						</template>
					</select-input>
					<select-input
						title="2. Select"
						v-model="componentData['openWB/general/testSelect2']"
						:groups="[
							{label: 'Gruppe 1', options: [
								{value: 1, text: 'Eins'},
								{value: 2, text: 'Zwei'}
							] },
							{label: 'Gruppe 2', options: [
								{value: 3, text: 'Drei'},
								{value: 4, text: 'Vier'}
							] }
						]">
						<template #help>
							Select mit Gruppen
						</template>
					</select-input>
					<hr>
					<buttongroup-input
						title="1. Button-Group"
						v-model="componentData['openWB/general/testButtonGroup1']"
						:buttons="[
							{buttonValue: 1, text: 'Eins'},
							{buttonValue: 2, text: 'Zwei'}
						]">
						<template #help>
							Hilfetext
						</template>
					</buttongroup-input>
					<hr>
					<checkbox-input
						title="1. Checkbox"
						v-model="componentData['openWB/general/testCheckbox1']">
						<template #help>
							Hilfetext
						</template>
					</checkbox-input>
				</card>

				<card title="JSON Gruppe">
					<text-input
						title="JSON 1"
						subtype="json"
						v-model="componentData['openWB/general/testJson1']">
						<template #help>
							JSON Objekt
						</template>
					</text-input>
					<text-input
						title="JSON 1 Text"
						v-model="componentData['openWB/general/testJson1'].text">
						<template #help>
							Text im JSON Objekt
						</template>
					</text-input>
					<number-input
						title="JSON 1 Zahl"
						v-model="componentData['openWB/general/testJson1'].value">
						<template #help>
							Zahl im JSON Objekt
						</template>
					</number-input>
				</card>

				<card title="Meldungen">
					<alert>
						Meldung ohne speziellen Subtype.
					</alert>
					<alert
						subtype="info">
						Infomeldung
					</alert>
					<alert
						subtype="warning">
						Warnmeldung
					</alert>
					<alert
						subtype="danger">
						Fehlermeldung
					</alert>
				</card>

			</content>
		</div><!-- app -->

		<script>
			// define topics and default values here
			const componentDefaultData = {
				'openWB/general/testJson1': {'text':'TEXT','value':999},
				'openWB/general/testText1': "Text 1",
				'openWB/general/testText2': "user@mail.com",
				'openWB/general/testText3': "host.domain",
				'openWB/general/testText4': "http://url.domain:8080/get/value",
				'openWB/general/testText5': "Username",
				'openWB/general/testNumber1': 5,
				'openWB/general/testNumber2': 10,
				'openWB/general/testPassword1': "GeHeIm123",
				'openWB/general/testTextarea1': "Das ist ein langer Text...",
				'openWB/general/testRange1': 10,
				'openWB/general/testRange2': 6,
				'openWB/general/testSelect1': 1,
				'openWB/general/testSelect2': 3,
				'openWB/general/testButtonGroup1': 2,
				'openWB/general/testCheckbox1': true
			}
		</script>
		<?php include_once './settings-2.vapp.php'; ?>

	</body>
</html>

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
		<!-- Normalize -->
		<link rel="stylesheet" type="text/css" href="css/normalize-8.0.1.css">
		<!-- Font Awesome -->
		<link rel="stylesheet" type="text/css" href="fonts/font-awesome-5.8.2/css/all.css">
		<!-- include settings-style -->
		<link rel="stylesheet" type="text/css" href="css/settings_style.css">
		<link rel="stylesheet" href="themes/<?php echo $themeCookie; ?>/settings.css?v=20200801">

		<!-- important scripts to be loaded -->
		<script src="js/jquery-3.6.0.min.js"></script>
		<script src="js/bootstrap-4.4.1/bootstrap.bundle.min.js"></script>
		<script src="js/bootstrap-selectpicker/bootstrap-select.min.js"></script>
		<!-- load helper functions -->
		<!-- <script src = "settings/helperFunctions.js?ver=20210329" ></script> -->
		<!-- load mqtt library -->
		<!-- <script src = "js/mqttws31.js" ></script> -->
		<!-- load topics -->
		<!-- <script src = "settings/<?php echo $currentPage['id']; ?>/topicsToSubscribe.js?ver=20210215" ></script> -->
		<!-- load service -->
		<!-- <script src = "settings/setupMqttServices.js?ver=20201207" ></script> -->
		<!-- load mqtt handler-->
		<!-- <script src = "settings/processAllMqttMsg.js?ver=20210104" ></script> -->
		<!-- vue.js -->
		<script src="js/vue.js-3.1.5/vue.global.js"></script>
	</head>
	<body>
		<div id="nav"></div> <!-- placeholder for navbar -->

		<div role="main" class="container pt-4" style="margin-top:20px">
			<div id="content">
				<h1>{{ title }}</h1>

				<openwb-card v-for="card in cards" :key="card.id" :title="card.title" v-model="card"></openwb-card>
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
		</div>  <!-- container -->

		<footer id="footer" class="footer bg-dark text-light font-small">
			<div class="container text-center">
				<small>Sie befinden sich hier: Einstellungen / {{ pageName }}</small>
			</div>
		</footer>

		<!-- vue apps start here -->
		<script type="text/x-template" id="openwb-card-section-template">
			Section...
		</script>

		<script type="text/x-template" id="openwb-card-template">
			<div class="card border-secondary">
				<div class="card-header bg-secondary">
					<div class="form-group mb-0">
						<div class="form-row vaRow mb-0">
							<div class="col">{{ title }}</div>
							<div v-if="buttons" class="col-8">
								<div class="btn-group btn-block btn-group-toggle">
									<label v-for="button in buttons" class="btn btn-sm btn-outline-info" :class="{ active: value === button.buttonValue }">
										<input type="radio" :name="name" v-model.number="value" :value="button.buttonValue">{{ button.text }}
									</label>
								</div>
							</div>
						</div>
					</div>
				</div>
				<div class="card-body">
					<card-section v-for="(section, index) in sections" v-bind="section" :index="index"></card-section>
				</div>
			</div>
		</script>

		<script>
			const cardSectionComponent = {
				props: [
					
				],
				template: '#openwb-card-section-template',
				components: {
				}
			}

			const cardComponent = {
				props: [
					'title',
					'buttons',
					'sections'
				],
				template: '#openwb-card-template',
				components: {
					'card-section': cardSectionComponent
				}
			}

			const ContentApp = {
				data() {
					return {
						title: "Übergreifende Ladeeinstellungen",
						cards: [
							{ id: 1, title: "Titel 1", name: "c1", value: 1, buttons: [ { text: "Aus", buttonValue: 0 }, { text: "An", buttonValue: 1 } ],
								sections: [
									{ heading: "Überschrift Bereich 1", elements: [
										{ id: 1, title: "Element 1.1", description: "Beschreibung 1.1", name: "s1e1", value: "dummy", type: "text" },
										{ id: 7, title: "Element 1.7", description: "Beschreibung 1.7", name: "s1e7", value: "", type: "email" },
										{ id: 8, title: "Element 1.8", description: "Beschreibung 1.8", name: "s1e8", value: "", type: "host" },
										{ id: 9, title: "Element 1.9", description: "Beschreibung 1.9", name: "s1e9", value: "", type: "url" },
										{ id: 3, title: "Element 1.3", description: "Beschreibung 1.3", name: "s1e3", value: 42, type: "number", min: 0, max: 100, step: 5 },
										{ id: 4, title: "Element 1.4", description: "Beschreibung 1.4", name: "s1e4", value: "", type: "password" },
									]},
									{ heading: "Überschrift Bereich 2", elements: [
										{ id: 6, title: "Element 1.6", description: "Beschreibung 1.6", name: "s1e6", value: "Langer Text", type: "textarea" },
										{ id: 2, title: "Element 1.2", description: "Beschreibung 1.2", name: "s1e2", value: 10, type: "range", unit: "A", min: 6, max: 32, step: 1 },
										{ id: 5, title: "Element 1.5", description: "Beschreibung 1.5", name: "s1e5", value: 1, type: "buttongroup", buttons: [ { text: "Aus", buttonValue: 0 }, { text: "An", buttonValue: 1 } ] },
										{ id: 10, title: "Element 1.10", description: "Beschreibung 1.10", name: "s1e10", value: "", type: "select", groups: [ { label: "Group 1", options: [ { text: "Option 1.1", value: "1" }, { text: "Option 1.2", value: 2 } ] } ], options: [ { text: "Option 1", value: "1" }, { text: "Option 2", value: 2 } ] },
									]}
								]
							},
							{ id: 2, title: "Titel 2",
								sections: [
									{ elements: [
										{ id: 1, description: "Beschreibung 2.1", name: "s2e1", type: "alert-info" },
										{ id: 2, description: "Beschreibung 2.2", name: "s2e2", type: "alert-warning" },
										{ id: 3, description: "Beschreibung 2.3", name: "s2e3", type: "alert-danger" },
									]},
								]
							},
						]
					}
				},
				components: {
					'openwb-card': cardComponent
				}
			}

			vContentApp = Vue.createApp(ContentApp).mount('#content');
		</script>

		<script>
			const FooterApp = {
				data() {
					return {
						pageName: "Allgemein"
					}
				},

			};

			vFooter = Vue.createApp(FooterApp).mount('#footer');

			$.get(
				{ url: "settings/navbar20.html", cache: false },
				function(data){
					$("#nav").replaceWith(data);
					// disable navbar entry for current page
					$('#navbarSample3').addClass('disabled');
				}
			);
		</script>
	</body>
</html>

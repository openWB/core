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
		<div id="nav"></div> <!-- placeholder for navbar -->

		<div role="main" class="container">

			<div id="content">
				<h1>{{ title }}</h1>

				<div v-for="card in cards" :key="card.id" class="card border-secondary">
					<div class="card-header bg-secondary">
						<div class="form-group mb-0">
							<div class="form-row vaRow mb-0">
								<div class="col">{{ card.title }}</div>
								<div v-if="card.buttons" class="col-8">
									<div class="btn-group btn-block btn-group-toggle">
										<label v-for="button in card.buttons" class="btn btn-sm btn-outline-info" :class="{ active: card.value === button.buttonValue }">
											<input type="radio" :name="card.name" v-model.number="card.value" :value="button.buttonValue">{{ button.text }}
										</label>
									</div>
								</div>
							</div>
						</div>
					</div>
					<div class="card-body">
						<div v-if="card.value !== 0">
							<div v-for="(section, index) in card.sections" :index="index">
								<hr v-if="index > 0">
								<div class="form-group mb-0">
									<div v-if="section.heading" class="form-row">
										<div class="col">
											{{ section.heading }}
										</div>
									</div>
									<div v-for="element in section.elements">
										<div v-if='element.type.search("alert-") === 0' class="card-text alert" :class="element.type">
											{{ element.description }}
										</div>
										<div v-else class="form-row mb-1">
											<label for="XXX" class="col-md-4 col-form-label">
												{{ element.title }}
											</label>
											<div class="col-md-8">
												<!-- text input -->
												<div v-if='element.type === "text"' class="form-row">
													<input type="text" :name="element.name" class="form-control" v-model="element.value">
												</div>
												<!-- email input -->
												<div v-if='element.type === "email"' class="form-row">
													<div class="input-group">
														<div class="input-group-prepend">
															<div class="input-group-text">
																<i class="fa fa-envelope"></i>
															</div>
														</div>
														<input type="email" :name="element.name" v-model="element.value" class="form-control">
													</div>
												</div>
												<!-- email input -->
												<div v-if='element.type === "host"' class="form-row">
													<div class="input-group">
														<div class="input-group-prepend">
															<div class="input-group-text">
																<i class="fas fa-network-wired"></i>
															</div>
														</div>
														<input type="text" :name="element.name" v-model="element.value" class="form-control" pattern="^(((\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.){3}(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])|[A-Za-z0-9\._\-]*)$">
														<!-- ip: "^((\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.){3}(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$" -->
														<!-- hostname: "[A-Za-z0-9\._\-]*" -->
													</div>
												</div>
												<!-- url input -->
												<div v-if='element.type === "url"' class="form-row">
													<div class="input-group">
														<div class="input-group-prepend">
															<div class="input-group-text">
																<i class="fas fa-globe"></i>
															</div>
														</div>
														<input type="url" :name="element.name" v-model="element.value" class="form-control">
													</div>
												</div>
												<!-- password input -->
												<div v-if='element.type === "password"' class="form-row">
													<div class="input-group">
														<div class="input-group-prepend">
															<div class="input-group-text">
																<i class="fa fa-lock"></i>
															</div>
														</div>
														<input type="password" :name="element.name" v-model="element.value" class="form-control">
													</div>
												</div>
												<!-- number input -->
												<div v-if='element.type === "number"' class="form-row">
													<input type="number" :name="element.name" class="form-control" :min="element.min" :max="element.max" :step="element.step" v-model.number="element.value">
												</div>
												<!-- text area input -->
												<div v-if='element.type === "textarea"' class="form-row">
													<textarea class="form-control" :name="element.name">{{ element.value }}</textarea>
													<!-- <textarea class="form-control" id="debugMessage" name="debugMessage" rows="3" placeholder="Fehlerbeschreibung" minlength="20" maxlength="500" required="required"></textarea> -->
												</div>
												<!-- range input -->
												<div v-if='element.type === "range"' class="form-row vaRow mb-1">
													<label for="XXX" class="col-2 col-form-label valueLabel">{{ element.value }} {{ element.unit }}</label>
													<div class="col-10">
														<input type="range" class="form-control-range rangeInput" :name="element.name" :min="element.min" :max="element.max" :step="element.step" v-model.number="element.value" data-default="0" data-topicprefix="XXX">
													</div>
												</div>
												<!-- buttongroup input -->
												<div v-if='element.type === "buttongroup"' class="form-row">
													<div class="btn-group btn-block btn-group-toggle">
														<label v-for="button in element.buttons" class="btn btn-outline-info" :class="{ active: element.value === button.buttonValue }">
															<input type="radio" :name="element.name" v-model="element.value" :value="button.buttonValue">{{ button.text }}
														</label>
													</div>
												</div>
												<!-- select input -->
												<div v-if='element.type === "select"' class="form-row">
													<select :name="element.name" class="form-control">
														<optgroup v-for="(group) in element.groups" :label="group.label">
															<option v-for="(option) in group.options" :value="option.value">{{ option.text}}</option>
														</optgroup>
														<!-- select elements without option groups -->
														<option v-for="(option) in element.options" :value="option.value">{{ option.text}}</option>
													</select>
												</div>
												<!-- <span v-if="showHelp" class="form-text small">{{ description }}</span> -->
												<span class="form-text small">{{ element.description }} [Wert: {{ element.value }}]</span>
											</div>
										</div>
									</div>
								</div>
							</div>
						</div>
						<div v-else>
						</div>
					</div>
				</div>

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
		<script type="text/x-template" id="card-template">
			<div class="card border-secondary">
				<div class="card-header bg-secondary">
					<div class="form-group mb-0">
						<div class="form-row vaRow mb-0">
							<div class="col">{{ title }}</div>
							<div v-if="buttons" class="col-8">
								<div class="btn-group btn-block btn-group-toggle" data-toggle="buttons">
									<element-button v-for="button in buttons" v-bind="button" :value="value" :name="name"></element-button>
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

		<script type="text/x-template" id="card-section-template">
			<hr v-if="index > 0">
			<div class="form-group mb-0">
				<setting-element v-for="element in elements" v-bind="element"></setting-element>
			</div>
		</script>

		<script type="text/x-template" id="setting-element-template">
			<div v-if='type.search("alert-") === 0' class="card-text alert" :class="type">
				{{ description }}
			</div>
			<div v-else class="form-row mb-1">
				<label for="XXX" class="col-md-4 col-form-label">
					{{ title }}
					<i v-on:click="toggleHelp" class="fa-question-circle" :class="showHelp ? 'fas' : 'far'"></i>
				</label>
				<div class="col-md-8">
					<!-- text input -->
					<!-- <div v-if='type === "text"' class="form-row">
						<input type="text" :name="name" class="form-control" v-model="value">
					</div> -->
					<!-- password input -->
					<!-- <div v-if='type === "password"' class="form-row">
						<div class="input-group">
							<div class="input-group-prepend">
								<div class="input-group-text">
									<i class="fa fa-lock"></i>
								</div>
							</div>
							<input type="password" :name="name" v-model="value" class="form-control">
						</div>
					</div> -->
					<!-- number input -->
					<!-- <div v-if='type === "number"' class="form-row">
						<input type="number" :name="name" class="form-control" :min="min" :max="max" :step="step" v-model="value">
					</div> -->
					<!-- range input -->
					<!-- <div v-if='type === "range"' class="form-row vaRow mb-1">
						<label for="XXX" class="col-2 col-form-label valueLabel">{{ value }} {{ unit }}</label>
						<div class="col-10">
							<input type="range" class="form-control-range rangeInput" :name="name" :min="min" :max="max" :step="step" v-model="value" data-default="0" data-topicprefix="XXX">
						</div>
					</div> -->
					<!-- buttongroup input -->
					<!-- <div v-if='type === "buttongroup"' class="form-row">
						<div class="btn-group btn-block btn-group-toggle" data-toggle="buttons">
							<element-button v-for="button in buttons" v-bind="button" :initialValue="value" :name="name"></element-button>
						</div>
					</div> -->
					<span v-if="showHelp" class="form-text small">{{ description }}</span>
				</div>
			</div>
		</script>

		<script type="text/x-template" id="element-button-template">
			<label class="btn btn-outline-info">
				<input type="radio" :name="name" v-model="value" :value="buttonValue">{{ text }}
			</label>
		</script>

		<script>
			// const elementButtonComponent = {
			// 	props: [
			// 		'text',
			// 		'name',
			// 		'value',
			// 		'buttonValue'
			// 	],
			// 	template: '#element-button-template',
			// }

			// const settingElementComponent = {
			// 	props: [
			// 		'title',
			// 		'id',
			// 		'name',
			// 		'description',
			// 		'type',
			// 		'value',
			// 		'unit',
			// 		'min', 'max', 'step',
			// 		'buttons'
			// 	],
			// 	data() {
			// 		return {
			// 			showHelp: false
			// 		}
			// 	},
			// 	components: {
			// 		'element-button': elementButtonComponent
			// 	},
			// 	template: '#setting-element-template',
			// 	methods: {
			// 		toggleHelp() {
			// 			this.showHelp = !this.showHelp;
			// 		}
			// 	}
			// }

			// const sectionComponent = {
			// 	props: [
			// 		'index',
			// 		'elements'
			// 	],
			// 	components: {
			// 		'setting-element': settingElementComponent
			// 	},
			// 	template: '#card-section-template'
			// }

			const cardComponent = {
				props: [
					'title',
					'buttons',
					'sections'
				],
				// components: {
				// 	'card-section': sectionComponent,
				// 	'element-button': elementButtonComponent
				// },
				template: '#card-template'
			}

			const ContentApp = {
				data() {
					return {
						title: "Übergreifende Ladeeinstellungen",
						cards: [
							{ id: 1, title: "Titel 1", name: "c1", value: 1, buttons: [ { text: "Aus", buttonValue: 0 }, { text: "An", buttonValue: 1 } ],
							// { id: 1, title: "Titel 1",
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
				// components: {
				// 	'element-button': elementButtonComponent,
					'card': cardComponent
				// }
			}

			vContentApp = Vue.createApp(ContentApp).mount('#content');

		</script>

		<script>
			const FooterApp = {
				data() {
					return {
						pageName: "Allgemein"
					}
				}
			};

			vFooter = Vue.createApp(FooterApp).mount('#footer');

			$.get(
				{ url: "settings/navbar20.html", cache: false },
				function(data){
					$("#nav").replaceWith(data);
					// disable navbar entry for current page
					$('#navbarSample2').addClass('disabled');
				}
			);
		</script>
	</body>
</html>

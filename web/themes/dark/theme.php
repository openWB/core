<!DOCTYPE html>
<html lang="de">

	<head>
		<!-- theme for openWB layout for standard and dark, only css is different-->
		<!-- 2020 Michael Ortenstein -->

		<title>openWB</title>
		<meta charset="UTF-8">
		<meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, user-scalable=0">
		<meta name="apple-mobile-web-app-capable" content="yes">
		<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
		<meta name="apple-mobile-web-app-title" content="openWB">
		<meta name="apple-mobile-web-app-status-bar-style" content="default">
		<link rel="apple-touch-startup-image" href="/openWB/web/img/favicons/splash1125x2436w.png"  />
		<link rel="apple-touch-startup-image" media="(width: 375px) and (height: 812px) and (-webkit-device-pixel-ratio: 3)" href="img/favicons/splash1125x2436w.png">
		<meta name="apple-mobile-web-app-title" content="openWB">
		<meta name="description" content="openWB">
		<meta name="keywords" content="openWB">
		<meta name="author" content="Michael Ortenstein">
		<link rel="apple-touch-icon" sizes="72x72" href="img/favicons/apple-icon-72x72.png">
		<link rel="apple-touch-icon" sizes="76x76" href="img/favicons/apple-icon-76x76.png">
		<link rel="apple-touch-icon" sizes="114x114" href="img/favicons/apple-icon-114x114.png">
		<link rel="apple-touch-icon" sizes="120x120" href="img/favicons/apple-icon-120x120.png">
		<link rel="apple-touch-icon" sizes="144x144" href="img/favicons/apple-icon-144x144.png">
		<link rel="apple-touch-icon" sizes="152x152" href="img/favicons/apple-icon-152x152.png">
		<link rel="apple-touch-icon" sizes="180x180" href="img/favicons/apple-icon-180x180.png">
		<link rel="icon" type="image/png" sizes="192x192"  href="img/favicons/android-icon-192x192.png">
		<link rel="icon" type="image/png" sizes="32x32" href="img/favicons/favicon-32x32.png">
		<link rel="icon" type="image/png" sizes="96x96" href="img/favicons/favicon-96x96.png">
		<link rel="icon" type="image/png" sizes="16x16" href="img/favicons/favicon-16x16.png">
		<meta name="msapplication-TileColor" content="#ffffff">
		<meta name="msapplication-TileImage" content="/ms-icon-144x144.png">
		<link rel="apple-touch-icon" sizes="57x57" href="img/favicons/apple-touch-icon-57x57.png">
		<link rel="apple-touch-icon" sizes="60x60" href="img/favicons/apple-touch-icon-60x60.png">
		<link rel="manifest" href="manifest.json">
		<link rel="shortcut icon" href="img/favicons/favicon.ico">
		<!-- <link rel="apple-touch-startup-image" href="img/loader.gif"> -->
		<meta name="msapplication-config" content="img/favicons/browserconfig.xml">
		<meta name="theme-color" content="#ffffff">

		<!-- Bootstrap -->
		<link rel="stylesheet" type="text/css" href="css/bootstrap-4.4.1/bootstrap.min.css">
		<!-- Bootstrap-Toggle -->
		<link rel="stylesheet" type="text/css" href="css/bootstrap4-toggle/bootstrap4-toggle.min.css">
		<!-- Normalize -->
		<link rel="stylesheet" type="text/css" href="css/normalize-8.0.1.css">
		<!-- Font Awesome, all styles -->
		<link rel="stylesheet" type="text/css" href="fonts/font-awesome-5.8.2/css/all.css">
		<!-- local css due to async loading of theme css -->
		<style>
			#preloader {
				background-color:white;
				position:fixed;
				top:0px;
				left:0px;
				width:100%;
				height:100%;
				z-index:999999;
			}
			#preloader-inner {
				margin-top: 150px;
				text-align: center;
			}
			#preloader-image {
				max-width: 300px;
			}
			#preloader-info {
				color:grey;
			}
		</style>
		<!-- important scripts to be loaded -->
		<script src="js/jquery-3.6.0.min.js"></script>
		<script src="js/bootstrap-4.4.1/bootstrap.bundle.min.js"></script>
		<script src="js/bootstrap4-toggle/bootstrap4-toggle.min.js"></script>
		<script>
			function getCookie(cname) {
				var name = cname + '=';
				var decodedCookie = decodeURIComponent(document.cookie);
				var ca = decodedCookie.split(';');
				for(var i = 0; i <ca.length; i++) {
					var c = ca[i];
					while (c.charAt(0) == ' ') {
						c = c.substring(1);
					}
					if (c.indexOf(name) == 0) {
						return c.substring(name.length, c.length);
					}
				}
				return '';
			}
			var themeCookie = getCookie('openWBTheme');
			// include special Theme style
			$('head').append('<link rel="stylesheet" href="themes/' + themeCookie + '/style.css?v=23122021">');
		</script>
	</head>

	<body>
		<!-- Preloader with Progress Bar -->
		<div id="preloader">
			<div id="preloader-inner">
				<div class="row">
					<div class="mx-auto d-block justify-content-center">
						<img id="preloader-image" src="img/favicons/preloader-image.png" alt="openWB">
					</div>
				</div>
				<div id="preloader-info" class="row justify-content-center mt-2">
					<div class="col-10 col-sm-6">
						Bitte warten, während die Seite aufgebaut wird.
					</div>
				</div>
				<div class="row justify-content-center mt-2">
					<div class="col-10 col-sm-6">
						<div class="progress active">
							<div class="progress-bar progress-bar-success progress-bar-striped progress-bar-animated" id="preloaderbar" role="progressbar">
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Landing Page -->
		<div id="nav-placeholder"></div>

		<div class="container regularTextSize">

			<!-- Header Section -->
			<div id="infoheader" class="row no-gutters">

				<!-- Battery Card -->
				<div class="housebattery-configured col-sm hide">
					<div class="card border-warning">
						<div class="card-header bg-warning collapsed" data-toggle="collapse" data-target="#cardBat">
							<i class="fas fa-car-battery"></i>
							<span class="housebattery-sum-soc">XX %</span>
							<i class="housebattery-sum-charging fas fa-angle-double-left hide"></i>
							<i class="housebattery-sum-discharging fas fa-angle-double-right hide"></i>
							<span class="housebattery-sum-power">XX W</span>
							<span class="collPlus"></span>
						</div>
						<div id="cardBat" class="card-body collapse">
							<div class="row">
								<div class="col pr-0">
									SoC
								</div>
								<div class="housebattery-sum-soc col pl-0 text-right">
									XX %
								</div>
							</div>
							<div class="row">
								<div class="col font-italic font-weight-bold">
									Heute:
								</div>
							</div>
							<div class="row">
								<div class="col pr-0">
									Geladen
								</div>
								<div class="housebattery-sum-import col pl-0 text-right">
									XX kWh
								</div>
							</div>
							<div class="row">
								<div class="col pr-0">
									Entladen
								</div>
								<div class="housebattery-sum-export col pl-0 text-right">
									XX kWh
								</div>
							</div>
							<div class="pv-configured">
								<hr class="border-warning">
								<div class="row">
									<div class="col font-italic font-weight-bold">
										Einstellungen:
									</div>
								</div>
								<div class="row vaRow">
									<div class="col pr-0">
										Vorrang PV
									</div>
									<div class="col text-right">
										<input class="housebattery-priority" type="checkbox" data-toggle="toggle" data-topic="openWB/set/general/chargemode_config/pv_charging/bat_prio" data-on='<i class="fas fa-car-battery"></i>' data-off='<i class="fas fa-car-side"></i>' data-onstyle="warning" data-offstyle="primary" data-size="sm" data-style="w-100">
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- PV Card -->
				<div class="pv-configured col-sm">
					<div class="card border-success">
						<div class="card-header bg-success collapsed" data-toggle="collapse" data-target="#cardPV">
							<i class="fas fa-solar-panel"></i>
							<span class="pv-sum-power">-- W</span>
							<span class="collPlus"></span>
						</div>
						<div id="cardPV" class="card-body collapse">
							<div class="row">
								<div class="col font-italic font-weight-bold">
									Heute:
								</div>
							</div>
							<div class="row">
								<div class="col pr-0">
									Ertrag 
								</div>
								<div class="pv-sum-production col pl-0 text-right">
									-- kWh
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- Grid Card -->
				<div class="grid-configured col-sm">
					<div class="card border-danger">
						<div class="card-header bg-danger collapsed" data-toggle="collapse" data-target="#cardGrid">
							<i class="fas fa-home"></i>
							<i class="grid-exporting fas fa-angle-double-right hide"></i>
							<i class="grid-importing fas fa-angle-double-left hide"></i>
							<img src="img/icons/electric-tower.svg" alt="electric tower" style="width: 1.1em;" >
							<span class="et-configured hide">
								<i class="et-blocked fas fa-coins hide"></i>
								<i class="et-not-blocked fas fa-coins text-success hide"></i>
							</span>
							<span class="grid-power">600 W</span>
							<span class="collPlus"></span>
						</div>
						<div id="cardGrid" class="card-body collapse">
							<div class="row">
								<div class="col font-italic font-weight-bold">
									Heute:
								</div>
							</div>
							<div class="row">
								<div class="col pr-0">
									Bezug
								</div>
								<div class="grid-import col pl-0 text-right">
									XX kWh
								</div>
							</div>
							<div class="row">
								<div class="col pr-0">
									Einspeisung
								</div>
								<div class="grid-export col pl-0 text-right">
									XX kWh
								</div>
							</div>
							<div class="et-configured hide">
								<hr class="border-danger">
								<div class="row">
									<div class="col font-italic font-weight-bold">
										Strompreis:
									</div>
								</div>
								<div class="row">
									<div class="col pr-0">
										Anbieter
									</div>
									<div class="et-name col pl-0 text-right">
										?
									</div>
								</div>
								<div class="row">
									<div class="col pr-0">
										aktuell
									</div>
									<div class="et-current-price col pl-0 text-right">
										XX ct/kWh
									</div>
								</div>
								<div class="row">
									<div class="col pr-0">
										Preisgrenze
									</div>
									<div class="et-price-limit col pl-0 text-right">
										XX ct/kWh
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- House Card -->
				<div class="houseconsumption-configured col-sm">
					<div class="card border-secondary">
						<div class="card-header bg-secondary collapsed" data-toggle="collapse" data-target="#cardHouseconsumption">
							<i class="fas fa-home"></i>
							<span class="houseconsumption-power">? W</span>
							<span class="collPlus"></span>
						</div>
						<div id="cardHouseconsumption" class="card-body collapse">
							<div class="row">
								<div class="col font-italic font-weight-bold">
									Heute:
								</div>
							</div>
							<div class="row">
								<div class="col pr-0">
									Energie 
								</div>
								<div class="houseconsumption-daily col pl-0 text-right">
									XX kWh
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- Chargepoint Sum Card -->
				<div class="chargepoint-sum-configured col-sm">
					<div class="card border-primary">
						<div class="card-header bg-primary collapsed" data-toggle="collapse" data-target="#cardChargepointSum">
							<i class="fas fa-charging-station"></i>
							<span class="chargepoint-sum-power">XX W</span>
							<span class="collPlus"></span>
						</div>
						<div id="cardChargepointSum" class="card-body collapse">
							<div class="row">
								<div class="col font-italic font-weight-bold">
									Heute:
								</div>
							</div>
							<div class="row">
								<div class="col pr-0">
									Geladen
								</div>
								<div class="chargepoint-sum-importdaily col pl-0 text-right">
									XX kWh
								</div>
							</div>
							<!-- Preparation for bidirectional charging V2H/V2G
							<div class="row">
								<div class="col pr-0">
									Entladen
								</div>
								<div class="chargepoint-sum-exportdaily col pl-0 text-right">
									XX kWh
								</div>
							</div>
							-->
						</div>
					</div>
				</div>

			</div>

			<!-- Chart Section -->
			<div class="row">
				<div class="col">
					<div class="card border-light">
						<div class="card-header bg-light" data-toggle="collapse" data-target="#cardGraph">
							<i class="fas fa-chart-area"></i>
							Diagramm
							<span class="collPlus"></span>
						</div>
						<div id="cardGraph" class="card-body collapse show">
							<div class="row justify-content-center my-2" id="thegraph">
								<!-- will be refreshed using MQTT (in livechart.js)-->
								<div class="col-sm-12 text-center smallTextSize">
									<div id="waitforgraphloadingdiv">
										Graph lädt, bitte warten...
									</div>
									<canvas id="canvas"></canvas>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Warning Section -->
			<div class="row text-center bg-darkgrey">
				<div class="col">
					<span id="lastregelungaktiv" class="regularTextSize text-red animate-alertPulsation"></span>
				</div>
			</div>

			<!-- chargepoint info header -->
			<div class="card text-grey">
				<div class="card-header bg-darkgrey font-weight-bold">
					<div class="form-row">
						<div class="col-3">
							Ladepunkt <span id="etproviderEnabledIcon" class="fa fa-chart-line hide"></span>
						</div>
						<div class="col-3">
							Lademodus
						</div>
						<div class="col-3">
							Parameter
						</div>
						<div class="col-3">
							geladen
						</div>
					</div>
					<div class="form-row">
						<div class="col-3">
						</div>
						<div class="col-3">
							Fahrzeug
						</div>
						<div class="col-3">
							SoC
						</div>
						<div class="col-3">
						</div>
					</div>
				</div>
			</div>

			<div class="accordion" id="chargepointaccordion">
				<div class="chargepoint-card card border-dark text-grey chargepoint-template hide" data-cp="0" data-chargetemplate="0" data-evtemplate="0">
					<div class="card-header bg-lightgrey collapsed" data-toggle="collapse" data-target="#collapseChargepoint0">
						<div class="form-row">
							<div class="col-3">
								<span class="fas fa-xs hide autolockConfiguredCp"></span>
								<span class="font-weight-bold chargepoint-name chargepoint-stateenabled">?</span>
								<span class="fa fa-xs fa-plug text-orange hide chargepoint-plugstate chargepoint-chargestate"></span>
								<span class="fa fa-xs fa-flag-checkered hide targetChargingCp"></span>
								<span class="fa fa-xs fa-moon hide nightChargingCp"></span>
							</div>
							<div class="col-3">
								<span class="chargepoint-vehiclechargemode">?</span>
							</div>
							<div class="col-3">
								<span class="chargepoint-power">?</span> <span class="chargepoint-phasesinuse">?</span> <span class="chargepoint-setcurrent">?</span>
							</div>
							<div class="col-3 collPlus">
								<span class="chargepoint-energysinceplugged">?</span><span class="chargepoint-rangesinceplugged" data-consumption="0">?</span> 
							</div>
						</div>
						<div class="form-row">
							<div class="col-3">
								<div class="chargepoint-alert alert m-0 px-1 py-0">
									<!-- <i class="chargepoint-faultstate fas fa-check-circle text-success hide" data-option="0"></i> -->
									<i class="chargepoint-faultstate fas fa-exclamation-triangle text-warning hide" data-option="1"></i>
									<i class="chargepoint-faultstate fas fa-times-circle text-danger hide" data-option="2"></i>
									<span class="chargepoint-faultstr"></span>
								</div>
							</div>
							<div class="col-3 chargepoint-vehiclename">?</div>
							<div class="col-3">
								<div class="chargepoint-socconfigured hide">
									<span class="chargepoint-soc">?</span> %
									<i class="small chargepoint-reloadsocsymbol fas fa-redo-alt"></i>
									<i class="chargepoint-manualsocsymbol fas fa-edit hide"></i>
								</div>
							</div>
						</div>
					</div>
					<div id="collapseChargepoint0" data-parent="#chargepointaccordion" class="card-body collapse">
						<div class="form-group">
							<div class="form-row my-1 alert alert-info">
								<div class="col">
									<i class="fas fa-info-circle"></i>
									<span class="chargepoint-statestr">--</span>
								</div>
							</div>
							<div class="form-row mb-1">
								<div class="col">
									<i class="fas fa-lock"></i>
									Ladepunkt sperren
								</div>
								<div class="col-md-8 text-right">
									<input class="chargepoint-manuallock" type="checkbox" data-toggle="toggle" data-topic="openWB/set/chargepoint/<cp>/set/manual_lock" data-on="Ja" data-off="Nein" data-onstyle="danger" data-offstyle="success" data-size="sm" data-style="w-100">
								</div>
							</div>
							<hr>
							<div class="chargepoint-vehicledata" data-ev="">
								<div class="form-row mb-1">
									<label class="col col-form-label">
										<i class="fas fa-car-side"></i>
										Fahrzeug
									</label>
									<div class="col-md-8">
										<select name="chargepoint-vehicleselect" class="form-control chargepoint-vehicleselect" data-topic="openWB/set/chargepoint/template/<et>/ev">
											<option value="0">-- Nicht ausgewählt --</option>
										</select>
									</div>
								</div>
								<div class="form-row mb-1">
									<div class="col">
										<label class="col-form-label">Lademodus</label>
									</div>
									<div class="col-md-8 btn-group btn-group-toggle chargepoint-chargemode" data-toggle="buttons" data-name="chargemode" data-topic="openWB/set/vehicle/template/charge_template/<ct>/chargemode/selected">
										<label class="btn btn-outline-danger btn-toggle">
											<input type="radio" name="chargemode" data-option="instant_charging">Sofortladen
										</label>
										<label class="btn btn-outline-success btn-toggle">
											<input type="radio" name="chargemode" data-option="pv_charging">PV
										</label>
										<label class="btn btn-outline-primary btn-toggle">
											<input type="radio" name="chargemode" data-option="scheduled_charging">Zielladen
										</label>
										<label class="btn btn-outline-secondary btn-toggle">
											<input type="radio" name="chargemode" data-option="standby">Standby
										</label>
										<label class="btn btn-outline-dark btn-toggle">
											<input type="radio" name="chargemode" data-option="stop">Stop
										</label>
									</div>
								</div>
								<div class="form-row mb-1">
									<div class="col">
										<i class="fas fa-star"></i>
										Priorität
									</div>
									<div class="col-md-8 text-right">
										<input class="chargepoint-vehiclepriority" type="checkbox" data-toggle="toggle" data-topic="openWB/set/vehicle/template/charge_template/<ct>/prio" data-on="Ja" data-off="Nein" data-onstyle="success" data-offstyle="danger" data-size="sm" data-style="w-100">
									</div>
								</div>
								<div class="form-row mb-1">
									<div class="col">
										<i class="far fa-clock"></i>
										Zeitladen
									</div>
									<div class="col-md-8 text-right">
										<input class="chargepoint-timechargingactive" type="checkbox" data-toggle="toggle" data-topic="openWB/set/vehicle/template/charge_template/<ct>/time_charging/active" data-on="Ja" data-off="Nein" data-onstyle="success" data-offstyle="danger" data-size="sm" data-style="w-100">
									</div>
								</div>
								<div class="chargepoint-chargemodeoptions mb-0 hide">
									<hr>
									<div class="chargemode-options chargemode-option-instant_charging">
										<h3>Einstellungen für "Sofortladen"</h3>
										<div class="form-row vaRow mb-0">
											<div class="col">
												Stromstärke
											</div>
											<div class="col-md-8">
												<div class="form-row form-group mb-1 vaRow">
													<div class="col">
														<input type="range" class="chargepoint-instantchargecurrent form-control-range rangeInput" id="currentInstantChargeCp0" data-topic="openWB/set/vehicle/template/charge_template/<ct>/chargemode/instant_charging/current" min="6" max="32" step="1">
													</div>
													<label for="currentInstantChargeCp0" class="col-form-label valueLabel" data-suffix="A">? A</label>
												</div>
											</div>
										</div>
										<div class="form-row vaRow">
											<div class="col">
												<label class="col-form-label">Begrenzung</label>
											</div>
											<div class="col-md-8 btn-group btn-group-toggle chargepoint-instantchargelimitselected" id="limitInstantChargeCp0" data-name="limitCp" data-toggle="buttons" data-topic="openWB/set/vehicle/template/charge_template/<ct>/chargemode/instant_charging/limit/selected">
												<label class="btn btn-outline-info btn-toggle">
													<input type="radio" name="limitCp" data-option="none"> keine
												</label>
												<label class="btn btn-outline-info btn-toggle">
													<input type="radio" name="limitCp" data-option="soc"> EV-SoC
												</label>
												<label class="btn btn-outline-info btn-toggle">
													<input type="radio" name="limitCp" data-option="amount"> Energiemenge
												</label>
											</div>
										</div>
										<div class="chargemode-limit-options">
											<div class="form-row form-group mb-1 vaRow regularTextSize chargemode-limit-option chargemode-limit-option-soc">
												<div class="col">
													Maximaler SoC
												</div>
												<div class="col-md-8">
													<div class="form-row form-group mb-1 vaRow">
														<div class="col">
															<input type="range" class="chargepoint-instantchargelimitsoc form-control-range rangeInput" id="soclimitCp0" min="5" max="100" step="5" data-topic="openWB/set/vehicle/template/charge_template/<ct>/chargemode/instant_charging/limit/soc">
														</div>
														<label for="soclimitCp0" class="col-form-label valueLabel" data-suffix="%">? %</label>
													</div>
												</div>
											</div>
											<div class="form-row form-group mb-1 vaRow regularTextSize chargemode-limit-option chargemode-limit-option-amount">
												<div class="col">
													Zu ladende Energie
												</div>
												<div class="col-md-8">
													<div class="form-row form-group mb-1 vaRow">
														<div class="col">
															<input type="range" class="chargepoint-instantchargelimitamount form-control-range rangeInput" id="amountlimitCp0" min="1" max="50" step="1" data-transformation='{"out":"<v>*1000","in":"<v>/1000"}' data-topic="openWB/set/vehicle/template/charge_template/<ct>/chargemode/instant_charging/limit/amount">
														</div>
														<label for="amountlimitCp0" class="col-form-label valueLabel" data-suffix="kWh">? kWh</label>
													</div>
												</div>
											</div>
										</div>
									</div>
									<div class="chargemode-options chargemode-option-pv_charging">
										<h3>Einstellungen für "PV"</h3>
										<div class="form-row mb-1">
											<div class="col">
												Einspeisegrenze beachten
											</div>
											<div class="col-md-8 text-right">
												<input class="chargepoint-pvchargefeedinlimit" type="checkbox" data-toggle="toggle" data-topic="openWB/set/vehicle/template/charge_template/<ct>/chargemode/pv_charging/feed_in_limit" data-on="Ja" data-off="Nein" data-onstyle="success" data-offstyle="danger" data-size="sm" data-style="w-100">
											</div>
										</div>
										<div class="form-row vaRow mb-0">
											<div class="col">
												Minimal Stromstärke
											</div>
											<div class="col-md-8">
												<div class="form-row form-group mb-1 vaRow">
													<div class="col">
														<input type="range" class="chargepoint-pvchargemincurrent form-control-range rangeInput" id="minCurrentPvCp0" data-topic="openWB/set/vehicle/template/charge_template/<ct>/chargemode/pv_charging/min_current" min="0" max="11" step="1" data-list="0,6,7,8,9,10,11,12,13,14,15,16">
													</div>
													<label for="minCurrentPvCp0" class="col-form-label valueLabel" data-suffix="A">? A</label>
												</div>
											</div>
										</div>
										<div class="form-row vaRow mb-0">
											<div class="col">
												Minimal SoC
											</div>
											<div class="col-md-8">
												<div class="form-row form-group mb-1 vaRow">
													<div class="col">
														<input type="range" class="chargepoint-pvchargeminsoc form-control-range rangeInput" id="minSocPvCp0" data-topic="openWB/set/vehicle/template/charge_template/<ct>/chargemode/pv_charging/min_soc" min="0" max="99" step="1">
													</div>
													<label for="minSocPvCp0" class="col-form-label valueLabel" data-suffix="%">? %</label>
												</div>
											</div>
										</div>
										<div class="form-row vaRow mb-0">
											<div class="col">
												Minimal SoC Stromstärke
											</div>
											<div class="col-md-8">
												<div class="form-row form-group mb-1 vaRow">
													<div class="col">
														<input type="range" class="chargepoint-pvchargeminsoccurrent form-control-range rangeInput" id="minSocCurrentPvCp0" data-topic="openWB/set/vehicle/template/charge_template/<ct>/chargemode/pv_charging/min_soc_current" min="6" max="16" step="1">
													</div>
													<label for="minSocCurrentPvCp0" class="col-form-label valueLabel" data-suffix="A">? A</label>
												</div>
											</div>
										</div>
										<div class="form-row vaRow mb-0">
											<div class="col">
												Maximal SoC
											</div>
											<div class="col-md-8">
												<div class="form-row form-group mb-1 vaRow">
													<div class="col">
														<input type="range" class="chargepoint-pvchargemaxsoc form-control-range rangeInput" id="maxSocPvCp0" data-topic="openWB/set/vehicle/template/charge_template/<ct>/chargemode/pv_charging/max_soc" min="1" max="100" step="1">
													</div>
													<label for="maxSocPvCp0" class="col-form-label valueLabel" data-suffix="%">? %</label>
												</div>
											</div>
										</div>
									</div>
									<div class="chargemode-options chargemode-option-scheduled_charging">
										<div class="form-row vaRow mb-1">
											<div class="col">
												<h3 class="mb-0">Einstellungen für "Zielladen"</h3>
											</div>
											<div class="col-2 text-right">
												<button type="button" class="btn btn-sm btn-secondary">
													<i class="fas fa-cogs"></i>
												</button>
											</div>
										</div>
										<div class="form-row mb-1 chargepoint-scheduleplan chargepoint-scheduleplan-template hide" data-plan="0">
											<div class="col">
												<div class="form-row">
													<div class="col">
														<span class="chargepoint-schedulename">?</span>
														<span class="chargepoint-scheduleedit"><i class="fas fa-edit"></i></span>
													</div>
													<div class="col-lg-6">
														<span class="chargepoint-schedulefrequency">
															<i class="fas fa-calendar-alt"></i>
															<span class="chargepoint-schedulefrequencyvalue">?</span>
														</span>
														<span class="chargepoint-scheduledate">
															<i class="fas fa-calendar-day"></i>
															<span class="chargepoint-scheduledatevalue">?</span>
														</span>
														<i class="fas fa-clock"></i> <span class="chargepoint-scheduletime">?</span>
														<i class="fas fa-car-battery"></i> <span class="chargepoint-schedulesoc">?</span>%
													</div>
												</div>
											</div>
											<div class="col-4 text-right">
												<input class="chargepoint-scheduleactive" type="checkbox" data-toggle="toggle" data-topic="openWB/set/vehicle/template/charge_template/<ct>/chargemode/scheduled_charging/<sched>/active" data-on="An" data-off="Aus" data-onstyle="success" data-offstyle="danger" data-size="sm" data-style="w-100">
											</div>
										</div>
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- modal SoC-window -->
			<div class="modal fade" id="socModal">
				<div class="modal-dialog">
					<div class="modal-content">
						<!-- modal header -->
						<div class="modal-header bg-warning">
							<h4 class="modal-title text-dark">Manuelle SoC-Eingabe - Ladepunkt <span class="chargepoint-soc"></span></h4>
						</div>
						<!-- modal body -->
						<div class="modal-body">
							<div class="row justify-content-center">
								<div class="col-2 px-1 py-1">
									<button type="button" id="manualSocDecrement" class="btn btn-block btn-secondary">-</button>
								</div>
								<div class="col-5 py-1">
									<div class="input-group">
										<input id="manualSocBox" type="number" min="0" max="100" step="1" value="0" name="socBox" class="form-control text-right">
										<div class="input-group-append">
											<div class="input-group-text">
												%
											</div>
										</div>
									</div>
								</div>
								<div class="col-2 px-1 py-1">
									<button type="button" id="manualSocIncrement" class="btn btn-block btn-secondary">+</button>
								</div>
							</div>
							<div class="row justify-content-center">
								<div class="col-sm-5 py-1">
									<button type="button" id="manualSocOk" class="btn btn-lg btn-block btn-success" data-dismiss="modal">Übernehmen</button>
								</div>
							</div>
							<div class="row justify-content-center">
								<div class="col-sm-5 py-1">
									<button type="button" id="manualSocCancel" class="btn btn-lg btn-block btn-secondary" data-dismiss="modal">Abbrechen</button>
								</div>
							</div>
						</div>
					</div>
				</div>
				<script>
					function clearSocForm(){
						$("#manualSocBox").val("0");
					}

					function submitSocForm() {
						var currentCp = $('#socModal').find('.chargepoint-soc').text();
						var manualSoc = $("#manualSocBox").val();
						// console.log("SoC for CP"+currentCp+": "+manualSoc);
						publish(manualSoc, "openWB/set/lp/"+currentCp+"/manualSoc");
						// reset input after publishing
						clearSocForm();
					};

					$(document).ready(function(){

						$('#manualSocDecrement').click(function() {
							var currentValue = parseInt($('#manualSocBox').val());
							var newValue = 0;
							if( !isNaN(currentValue) ){
								newValue = Math.max( currentValue - 1, 0 );
							}
							$('#manualSocBox').val(newValue);
						});

						$('#manualSocIncrement').click(function() {
							var currentValue = parseInt($('#manualSocBox').val());
							var newValue = 0;
							if( !isNaN(currentValue) ){
								newValue = Math.min( currentValue + 1, 100 );
							}
							$('#manualSocBox').val(newValue);
						});

						$('#manualSocCancel').click(function() {
							clearSocForm();
						});

						$('#manualSocOk').click(function() {
							submitSocForm();
						});

					});
				</script>
			</div>

		</div>  <!-- container -->

		<script>

			// load navbar, be carefull: it loads asynchonously
			$.get(
				{ url: "themes/navbar.html", cache: false },
				function(data){
					$("#nav-placeholder").replaceWith(data);
				}
			);

			var timeOfLastMqttMessage = 0;  // holds timestamp of last received message
			var landingpageShown = false;  // holds flag for landing page being shown

			function chargemodeOptionsShowHide(btnGrp, option) {
				// show/hide all option-parameters in form-rows for selected option
				var parent = btnGrp.closest('.chargepoint-card[data-cp]');  // get parent div element for charge limitation options
				var chargemodeOptionsElement = $(parent).find('.chargepoint-chargemodeoptions');
				if( option == "stop" || option == "standby" ) {
					chargemodeOptionsElement.addClass('hide');
				} else {
					chargemodeOptionsElement.removeClass('hide');
					$(chargemodeOptionsElement).find('.chargemode-options.chargemode-option-'+option).removeClass('hide');  // now show option elements for selected option
					$(chargemodeOptionsElement).find('.chargemode-options').not('.chargemode-option-'+option).addClass('hide');  // hide all other option elements
				}
			}

			function chargemodeLimitOptionsShowHide(btnGrp, option) {
				// show/hide all option-parameters in form-rows for selected option
				var parent = btnGrp.closest('.chargepoint-card[data-cp]');  // get parent div element for charge limitation options
				var chargemodeLimitOptionsElement = $(parent).find('.chargemode-limit-options');
				// console.log('option: '+option);
				// console.log(chargemodeLimitOptionsElement);
				if( option == "none" ) {
					chargemodeLimitOptionsElement.addClass('hide');
				} else {
					chargemodeLimitOptionsElement.removeClass('hide');
					$(chargemodeLimitOptionsElement).find('.chargemode-limit-option.chargemode-limit-option-'+option).removeClass('hide');  // now show option elements for selected option
					$(chargemodeLimitOptionsElement).find('.chargemode-limit-option').not('.chargemode-limit-option-'+option).addClass('hide');  // hide all other option elements
				}
			}

			function processPreloader(mqttTopic) {
				// sets flag for topic received in topic-array
				// and updates the preloader progress bar
				// console.log("preloader handling message: "+mqttTopic);
				if ( !landingpageShown ) {
					var countTopicsReceived = 0;
					for ( var index = 0; index < topicsToSubscribeFirst.length; index ++) {
						if ( topicsToSubscribeFirst[index][0] == mqttTopic && topicsToSubscribeFirst[index][1] == 0 ) {
							// topic found in array
							topicsToSubscribeFirst[index][1] = 1;  // mark topic as received
						};
						if ( topicsToSubscribeFirst[index][1] > 0 ) {
							countTopicsReceived++;
						}
					};
					for ( var index = 0; index < topicsToSubscribe.length; index ++) {
						if ( topicsToSubscribe[index][0] == mqttTopic && topicsToSubscribe[index][1] == 0 ) {
							// topic found in array
							topicsToSubscribe[index][1] = 1;  // mark topic as received
						};
						if ( topicsToSubscribe[index][1] > 0 ) {
							countTopicsReceived++;
						}
					};
					// countTopicsToBeReceived holds all topics flagged 1 and not only those for preloader
					countTopicsReceived = countTopicsReceived - countTopicsNotForPreloader;
					var countTopicsToBeReceived = topicsToSubscribeFirst.length + topicsToSubscribe.length - countTopicsNotForPreloader;
					var percentageReceived = (countTopicsReceived / countTopicsToBeReceived * 100).toFixed(0);
					var timeBetweenTwoMesagges = Date.now() - timeOfLastMqttMessage;
					if ( timeBetweenTwoMesagges > 3000 ) {
						// latest after 3 sec without new messages
						percentageReceived = 100;
						// debug output
						topicsToSubscribeFirst.forEach((item, i) => {
							if ( item[1] == 0 ) {
								console.log('not received: ' + item[0]);
							}
						});
						topicsToSubscribe.forEach((item, i) => {
							if ( item[1] == 0 ) {
								console.log('not received: ' + item[0]);
							}
						});

					}
					timeOfLastMqttMessage = Date.now();
					$("#preloaderbar").width(percentageReceived+"%");
					$("#preloaderbar").text(percentageReceived+" %");
					if ( percentageReceived == 100 ) {
						landingpageShown = true;
						setTimeout(function (){
							// delay a little bit
							$("#preloader").fadeOut(1000);
						}, 500);
					}
				}
			}

			var delayUserInput = (function () {
				// sets a timeout on call and resets timout if called again for same id before timeout fires
				var timeoutHandles = {};
				return function (id, callback, ms) {
					if ( timeoutHandles[id] ) {
						clearTimeout(timeoutHandles[id]);
					};
					timeoutHandles[id] = setTimeout(function(){
						delete timeoutHandles[id];
						callback(id);
					}, ms);
				};
			})();

			$(document).ready(function(){

				// load scripts synchronously in order specified
				var scriptsToLoad = [
					// time/date library for chart.js
					'js/luxon/luxon.min.js',
					// load Chart.js library
					'js/chart.js-3.2.1/chart.min.js',
					// load Chart.js annotation plugin
					// 'js/chartjs-plugin-annotation.min.js',
					'js/chartjs-adapter-luxon/chartjs-adapter-luxon.min.js',
					// load mqtt library
					'js/mqttws31.js',
					// some helper functions
					'themes/dark/helperFunctions.js?ver=20210504',
					// functions for processing messages
					'themes/dark/processAllMqttMsg.js?ver=20210504',
					// respective Chart.js definition live
					'themes/dark/livechart.js?ver=20201218',
					// respective Chart.js definition
					// 'themes/dark/electricityPriceChart.js?ver=20210120',
					// functions performing mqtt and start mqtt-service
					'themes/dark/setupMqttServices.js?ver=20210504',
				];
				scriptsToLoad.forEach(function(src) {
					var script = document.createElement('script');
					script.src = src;
					script.async = false;
					document.body.appendChild(script);
				});

				$('.container').on('change', 'input[type=checkbox]', function(event){
					// console.log("checkbox changed");
					// send mqtt set to enable/disable charge point after click
					var topic = $(this).data('topic');
					if( topic != undefined ) {
						var cp = parseInt($(this).closest('[data-cp]').data('cp'));  // get attribute cp-# of parent element
						var ev = parseInt($(this).closest('[data-ev]').data('ev'));  // get attribute ev-# of parent element
						var ct = parseInt($(this).closest('[data-chargetemplate]').data('chargetemplate'));  // get attribute chargetemplate-# of parent element
						var et = parseInt($(this).closest('[data-evtemplate]').data('evtemplate'));  // get attribute evtemplate-# of parent element
						var schedule = parseInt($(this).closest('[data-plan]').data('plan'));  // get attribute plan-# of parent element
						topic = topic.replace( '<cp>', cp );
						topic = topic.replace( '<ev>', ev );
						topic = topic.replace( '<ct>', ct );
						topic = topic.replace( '<et>', et );
						topic = topic.replace( '<sched>', schedule );
						if( topic.includes('/NaN/') ) {
							console.log( 'missing cp, ev, ct, et or sched data' );
						} else {
							if ( $(this).prop('checked') ) {
								publish(true, topic);
							} else {
								publish(false, topic);
							}
						}
					} else {
						console.log("checkbox without topic changed");
					}
				});

				$('.container').on('change', '.chargepoint-vehicleselect', function(event){
					// update data in parent element
					$(this).closest('[data-ev]').attr('data-ev', $(this).val()).data('ev', $(this).val());
					// send update to broker
					var topic = $(this).data('topic');
					if( topic != undefined ) {
						var cp = parseInt($(this).closest('[data-cp]').data('cp'));  // get attribute cp-# of parent element
						var ev = parseInt($(this).closest('[data-ev]').data('ev'));  // get attribute ev-# of parent element
						var ct = parseInt($(this).closest('[data-chargetemplate]').data('chargetemplate'));  // get attribute chargetemplate-# of parent element
						var et = parseInt($(this).closest('[data-evtemplate]').data('evtemplate'));  // get attribute evtemplate-# of parent element
						topic = topic.replace( '<cp>', cp );
						topic = topic.replace( '<ev>', ev );
						topic = topic.replace( '<ct>', ct );
						topic = topic.replace( '<et>', ct );
						if( topic.includes('/NaN/') ) {
							console.log( 'missing cp, ev, ct, or et data' );
						} else {
							publish(parseInt($(this).val()), topic);
						}
					}
				});

				$('.container').on('click', '.chargepoint-socconfigured', function(event){
					event.stopPropagation();
					// send mqtt set to force reload of charge point SoC after click
					var cp = parseInt($(this).closest('[data-cp]').data('cp'));  // get attribute cp-# of parent element
					if ( !isNaN(cp) && cp > 0 ) {
						if ( $(this).hasClass('manualSoC') ) {
							var currentSoc = parseInt($(this).find('.chargepoint-soc').text());
							if( isNaN(currentSoc) ){
								currentSoc = 0;
							}
							$('#socModal').find('.chargepoint-soc').text(cp);
							$("#manualSocBox").val(currentSoc);
							$('#socModal').modal("show");
						} else {
							var spinner = $(this).find('.chargepoint-reloadsocsymbol');
							var isRunning = spinner.hasClass("fa-spin");
							if ( !isRunning ) {
								spinner.addClass("fa-spin");
								publish(1, "openWB/set/lp/" + cp + "/ForceSoCUpdate");
							}
						}
					}
				});

				// $('.btn[value="Reset"]').click(function(event){
				// 	var topic = getTopicToSendTo($(this).attr('id'));
				// 	publish(1, topic);
				// });

				$('.container').on('change', '.btn-group-toggle', function(event){
					var ct = parseInt($(this).closest('[data-chargetemplate]').data('chargetemplate'));  // get attribute chargetemplate-# of parent element
					var option = $(this).find('input[type="radio"]:checked').data('option').toString();
					var topic = $(this).data('topic').replace('/<ct>/', '/'+ct+'/');
					if( topic.includes('/NaN/') ) {
							console.log( 'missing ct data' );
					} else {
						publish(option, topic);
						// show/hide respective option-values and progress
						if ($(this).hasClass('chargepoint-chargemode')){
							chargemodeOptionsShowHide(this, option);
						}
						if ($(this).hasClass('chargepoint-instantchargelimitselected')){
							// console.log('btnGroup chargepoint-instantchargelimitselected');
							chargemodeLimitOptionsShowHide(this, option);
						}
					}
				});

				// $('.priceMore, .priceLess').click(function(event){
				// 	// change Slider upon click on buttons
				// 	event.preventDefault();
				// 	var currentMaxPrice = parseFloat($('#MaxPriceForCharging').val());
				// 	var rangeMin = parseFloat($('#MaxPriceForCharging').attr('min'));
				// 	var rangeMax = parseFloat($('#MaxPriceForCharging').attr('max'));
				// 	var step = parseFloat($('#MaxPriceForCharging').attr('step'));
				// 	if ( $(this).hasClass ('priceLess') ) {
				// 		currentMaxPrice -= step;
				// 	} else {
				// 		currentMaxPrice += step;
				// 	}
				// 	// prevent timeout of delayUserInput when clicking "beyond" range
				// 	if ( currentMaxPrice < rangeMin ) {
				// 		currentMaxPrice = rangeMin;
				// 	} else if ( currentMaxPrice > rangeMax ) {
				// 		currentMaxPrice = rangeMax;
				// 	}
				// 	$('#MaxPriceForCharging').val(currentMaxPrice);
				// 	$('#MaxPriceForCharging').trigger('input');
				// });

				$('.container').on('input', '.rangeInput', function() {
					// show slider value in label of class valueLabel
					var elementId = $(this).attr('id');
					updateLabel(elementId);
					var element = $('#' + $.escapeSelector(elementId));
					var label = $('label[for="' + elementId + '"].valueLabel');
					label.addClass('text-danger');
					// if ( $.escapeSelector(elementId) == 'MaxPriceForCharging') {
					// 	// marks times in the pricechart where the price is low enough so charging would be allowed
					// 	var priceAnnotations = createPriceAnnotations();
					// 	electricityPricechart.options.annotation.annotations = priceAnnotations;
					// 	electricityPricechart.update();
					// }

					delayUserInput(elementId, function (id) {
						// gets executed on callback, 2000ms after last input-change
						// changes label color back to normal and sends input-value by mqtt
						var elem = $('#' + $.escapeSelector(id));
						var value = parseFloat(elem.val());
						var label = $('label[for="' + id + '"].valueLabel');
						if(list = $(elem).attr('data-list')){
							value = parseFloat(list.split(',')[parseInt(value)]);
						} else if(formula = $(elem).attr('data-transformation')){
							formula = JSON.parse(formula);
							formula = formula.out.replace('<v>', value);
							value = transformRangeValue(formula);
						}
						var topic = getTopicToSendTo(id);
						publish(value, topic);
						label.removeClass('text-danger');
						// if rangeInput is for chargeLimitation, recalc progress
						// if ( id.includes('/energyToCharge') ) {
						// 	var parent = elem.closest('.chargeLimitation')  // get parent div element for charge limitation
						// 	var element = parent.find('.progress-bar');  // now get parents progressbar
						// 	var actualCharged = element.data('actualCharged');  // get stored value
						// 	if ( isNaN(parseFloat(actualCharged)) ) {
						// 		actualCharged = 0;  // minimum value
						// 	}
						// 	var progress = (actualCharged / value * 100).toFixed(0);
						// 	element.width(progress+"%");
						// }
					}, 2000);
				});

				// register an event listener for changes in visibility
				let hidden;
				let visibilityChange;
				if (typeof document.hidden !== 'undefined') { // Opera 12.10 and Firefox 18 and later support
					hidden = 'hidden';
					visibilityChange = 'visibilitychange';
				} else if (typeof document.msHidden !== 'undefined') {
					hidden = 'msHidden';
					visibilityChange = 'msvisibilitychange';
				} else if (typeof document.webkitHidden !== 'undefined') {
					hidden = 'webkitHidden';
					visibilityChange = 'webkitvisibilitychange';
				}
				window.document.addEventListener(visibilityChange, () => {
					if (!document[hidden]) {
						// once page is unhidden... reload graph completety
						initialread = 0;
						all1 = 0;
						all2 = 0;
						all3 = 0;
						all4 = 0;
						all5 = 0;
						all6 = 0;
						all7 = 0;
						all8 = 0;
						all9 = 0;
						all10 = 0;
						all11 = 0;
						all12 = 0;
						all13 = 0;
						all14 = 0;
						all15 = 0;
						all16 = 0;
						// console.log("subscribing graph topics");
						subscribeMqttGraphSegments();
					}
				});

			});  // end document ready
		</script>

	</body>

</html>

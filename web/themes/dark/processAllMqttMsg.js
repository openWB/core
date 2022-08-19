/**
 * Functions to update graph and gui values via MQTT-messages
 *
 * @author Kevin Wieland
 * @author Michael Ortenstein
 * @author Lutz Bender
 */

var graphRefreshCounter = 0;
var chargeModeTemplate = {};
var schedulePlan = {};
var vehicleSoc = {};
var evuCounterIndex = undefined;

// function getCol(matrix, col){
// 	var column = [];
// 	for(var i=0; i<matrix.length; i++){
// 		column.push(matrix[i][col]);
// 	}
// 	return column;
// }

// function convertToKw(dataColum) {
// 	var convertedDataColumn = [];
// 	dataColum.forEach((value) => {
// 		convertedDataColumn.push(value / 1000);
// 	});
// 	return convertedDataColumn;
// }

function getIndex(topic) {
	// get occurrence of numbers between / / in topic
	// since this is supposed to be the index like in openwb/lp/4/w
	// no lookbehind supported by safari, so workaround with replace needed
	var index = topic.match(/(?:\/)([0-9]+)(?=\/)/g)[0].replace(/[^0-9]+/g, '');
	if (typeof index === 'undefined') {
		index = '';
	}
	return index;
}

function createChargePoint(hierarchy) {
	if (hierarchy.type == "cp") {
		var chargePointIndex = hierarchy.id;
		if ($('.charge-point-card[data-cp=' + chargePointIndex + ']').length == 0) {
			if (typeof chargePointIndex !== 'undefined') {
				console.debug("creating charge-point " + chargePointIndex);
				var sourceElement = $('.charge-point-card.charge-point-template');
				// remove checkbox toggle button style as they will not function after cloning
				sourceElement.find('input[type=checkbox][data-toggle^=toggle]').bootstrapToggle('destroy');
				var clonedElement = sourceElement.clone();
				// recreate checkbox toggle button styles in source element
				// sourceElement.find('input[type=checkbox][data-toggle^=toggle]').bootstrapToggle();
				// update all data referencing the old index in our clone
				clonedElement.attr('data-cp', chargePointIndex).data('cp', chargePointIndex);
				clonedElement.attr('data-charge-point-template', 0).data('charge-point-template', 0);
				clonedElement.attr('data-charge-template', 0).data('charge-template', 0);
				clonedElement.attr('data-ev-template', 0).data('ev-template', 0);
				clonedElement.find('.card-header').attr('data-target', '#collapseChargepoint' + chargePointIndex).data('target', '#collapseChargepoint' + chargePointIndex).addClass('collapsed');
				clonedElement.find('.card-body').attr('id', 'collapseChargepoint' + chargePointIndex).removeClass('show');
				clonedElement.find('label[for=minCurrentPvCpT]').attr('for', 'minCurrentPvCp' + chargePointIndex);
				clonedElement.find('#minCurrentPvCpT').attr('id', 'minCurrentPvCp' + chargePointIndex);
				clonedElement.find('label[for=minSocPvCpT]').attr('for', 'minSocPvCp' + chargePointIndex);
				clonedElement.find('#minSocPvCpT').attr('id', 'minSocPvCp' + chargePointIndex);
				clonedElement.find('label[for=maxSocPvCpT]').attr('for', 'maxSocPvCp' + chargePointIndex);
				clonedElement.find('#maxSocPvCpT').attr('id', 'maxSocPvCp' + chargePointIndex);
				clonedElement.find('label[for=minSocCurrentPvCpT]').attr('for', 'minSocCurrentPvCp' + chargePointIndex);
				clonedElement.find('#minSocCurrentPvCpT').attr('id', 'minSocCurrentPvCp' + chargePointIndex);
				clonedElement.find('label[for=currentInstantChargeCpT]').attr('for', 'currentInstantChargeCp' + chargePointIndex);
				clonedElement.find('#currentInstantChargeCpT').attr('id', 'currentInstantChargeCp' + chargePointIndex);
				clonedElement.find('label[for=limitInstantChargeCpT]').attr('for', 'limitInstantChargeCp' + chargePointIndex);
				clonedElement.find('#limitInstantChargeCpT').attr('id', 'limitInstantChargeCp' + chargePointIndex);
				clonedElement.find('label[for=soclimitCpT]').attr('for', 'soclimitCp' + chargePointIndex);
				clonedElement.find('#soclimitCpT').attr('id', 'soclimitCp' + chargePointIndex);
				clonedElement.find('label[for=amountlimitCpT]').attr('for', 'amountlimitCp' + chargePointIndex);
				clonedElement.find('#amountlimitCpT').attr('id', 'amountlimitCp' + chargePointIndex);
				// insert after last existing charge point to honor sorting from the array
				target = $('.charge-point-card[data-cp]').last();
				// console.log("target: "+target.data('cp')+" index: "+chargePointIndex);
				// insert clone into DOM
				clonedElement.insertAfter($(target));
				// now get our created element and add checkbox toggle buttons
				chargePointElement = $('.charge-point-card[data-cp="' + chargePointIndex + '"]');
				chargePointElement.find('input[type=checkbox][data-toggle^=toggle]').bootstrapToggle();
				// finally show our new charge point
				chargePointElement.removeClass('charge-point-template').removeClass('hide');
			}
		} else {
			console.error("charge point '" + chargePointIndex + "' already exists");
		}
	}
	hierarchy.children.forEach(element => {
		createChargePoint(element);
	});
}

function refreshChargeTemplate(templateIndex) {
	if (chargeModeTemplate.hasOwnProperty(templateIndex)) {
		parents = $('.charge-point-card[data-charge-template=' + templateIndex + ']');
		if (parents.length > 0) {
			// console.debug("selected elements", parents);
			for (currentParent of parents) {
				// console.debug("currentParent", currentParent);
				parent = $(currentParent);
				// console.debug("parent", parent);

				// ***** time_charging *****
				// time_charging.active
				element = parent.find('.charge-point-time-charging-active');
				if (chargeModeTemplate[templateIndex].time_charging.active) {
					element.bootstrapToggle('on', true);
				} else {
					element.bootstrapToggle('off', true);
				}

				// ***** instant_charging *****
				// chargemode.instant_charging.current
				element = parent.find('.charge-point-instant-charge-current');
				setInputValue(element.attr('id'), chargeModeTemplate[templateIndex].chargemode.instant_charging.current);
				// chargemode.instant_charging.limit.selected
				element = parent.find('.charge-point-instant-charge-limit-selected');
				setToggleBtnGroup(element.attr('id'), chargeModeTemplate[templateIndex].chargemode.instant_charging.limit.selected);
				// chargemode.instant_charging.limit.soc
				element = parent.find('.charge-point-instant-charge-limit-soc');
				setInputValue(element.attr('id'), chargeModeTemplate[templateIndex].chargemode.instant_charging.limit.soc);
				// chargemode.instant_charging.limit.soc
				element = parent.find('.charge-point-instant-charge-limit-amount');
				setInputValue(element.attr('id'), chargeModeTemplate[templateIndex].chargemode.instant_charging.limit.amount);

				// ***** pv_charging *****
				// chargemode.pv_charging.min_current
				element = parent.find('.charge-point-pv-charge-min-current');
				setInputValue(element.attr('id'), chargeModeTemplate[templateIndex].chargemode.pv_charging.min_current);
				// chargemode.pv_charging.min_soc
				element = parent.find('.charge-point-pv-charge-min-soc');
				setInputValue(element.attr('id'), chargeModeTemplate[templateIndex].chargemode.pv_charging.min_soc);
				// chargemode.pv_charging.max_soc
				element = parent.find('.charge-point-pv-charge-max-soc');
				setInputValue(element.attr('id'), chargeModeTemplate[templateIndex].chargemode.pv_charging.max_soc);
				// chargemode.pv_charging.min_soc_current
				element = parent.find('.charge-point-pv-charge-min-soc-current');
				setInputValue(element.attr('id'), chargeModeTemplate[templateIndex].chargemode.pv_charging.min_soc_current);
				// chargemode.pv_charging.feed_in_limit
				var element = parent.find('.charge-point-pv-charge-feed-in-limit'); // now get parents respective child element
				if (chargeModeTemplate[templateIndex].chargemode.pv_charging.feed_in_limit == true) {
					// element.prop('checked', true);
					element.bootstrapToggle('on', true); // do not fire a changed-event to prevent a loop!
				} else {
					// element.prop('checked', false);
					element.bootstrapToggle('off', true); // do not fire a changed-event to prevent a loop!
				}

				// ***** scheduled_charging *****
				// chargemode.scheduled_charging.X
				// first remove all schedule plans except the template
				parent.find('.charge-point-schedule-plan[data-plan]').not('.charge-point-schedule-plan-template').remove();
				var sourceElement = parent.find('.charge-point-schedule-plan-template');
				// remove checkbox toggle button style as they will not function after cloning
				sourceElement.find('input[type=checkbox][data-toggle^=toggle]').bootstrapToggle('destroy');
				// now create any other schedule plan
				if (templateIndex in schedulePlan) {
					parent.find(".charge-point-schedule-plan-missing").addClass("hide");
					for (const [key, value] of Object.entries(schedulePlan[templateIndex])) {
						console.debug("schedule", key, value);
						if (parent.find('.charge-point-schedule-plan[data-plan=' + key + ']').length == 0) {
							// console.log('creating schedule plan with id "'+key+'"');
							var clonedElement = sourceElement.clone();
							// update all data referencing the old index in our clone
							clonedElement.attr('data-plan', key).data('plan', key);
							// insert after last existing plan to honor sorting from the array
							target = parent.find('.charge-point-schedule-plan').last();
							// console.log("target: "+target.data('plan')+" index: "+key);
							// console.log(target);
							// insert clone into DOM
							clonedElement.insertAfter($(target));
							// now get our created element and add checkbox toggle buttons
							schedulePlanElement = parent.find('.charge-point-schedule-plan[data-plan=' + key + ']');
							schedulePlanElement.find('input[type=checkbox][data-toggle^=toggle]').bootstrapToggle();
							// set values from payload
							schedulePlanElement.find('.charge-point-schedule-name').text(value.name);
							if (value.limit.selected == "soc") {
								schedulePlanElement.find('.charge-point-schedule-limit').text(value.limit.soc + "%");
								schedulePlanElement.find('.charge-point-schedule-limit-icon').removeClass('fa-bolt');
								schedulePlanElement.find('.charge-point-schedule-limit-icon').addClass('fa-car-battery');
							} else {
								schedulePlanElement.find('.charge-point-schedule-limit').text((value.limit.amount/1000) + "kWh");
								schedulePlanElement.find('.charge-point-schedule-limit-icon').removeClass('fa-car-battery');
								schedulePlanElement.find('.charge-point-schedule-limit-icon').addClass('fa-bolt');
							}
							schedulePlanElement.find('.charge-point-schedule-time').text(value.time);
							if (value.active == true) {
								schedulePlanElement.find('.charge-point-schedule-active').removeClass('alert-danger border-danger');
								schedulePlanElement.find('.charge-point-schedule-active').addClass('alert-success border-success');
							} else {
								schedulePlanElement.find('.charge-point-schedule-active').removeClass('alert-success border-success');
								schedulePlanElement.find('.charge-point-schedule-active').addClass('alert-danger border-danger');
							}
							switch (value.frequency.selected) {
								case "once":
									schedulePlanElement.find('.charge-point-schedule-frequency').addClass('hide');
									schedulePlanElement.find('.charge-point-schedule-date').removeClass('hide');
									const d = new Date(value.frequency.once);
									schedulePlanElement.find('.charge-point-schedule-date-value').text(d.toLocaleDateString(undefined, { year: "numeric", month: "2-digit", day: "2-digit", weekday: "short" }));
									break;
								case "daily":
									schedulePlanElement.find('.charge-point-schedule-frequency').removeClass('hide');
									schedulePlanElement.find('.charge-point-schedule-date').addClass('hide');
									schedulePlanElement.find('.charge-point-schedule-frequency-value').text('täglich');
									break;
								case "weekly":
									const days = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"];
									var daysText = '';
									value.frequency.weekly.forEach(function (dayValue, index) {
										if (dayValue == true) {
											if (daysText.length > 0) {
												daysText += ',';
											}
											daysText += days[index];
										}
									});
									schedulePlanElement.find('.charge-point-schedule-frequency').removeClass('hide');
									schedulePlanElement.find('.charge-point-schedule-date').addClass('hide');
									schedulePlanElement.find('.charge-point-schedule-frequency-value').text(daysText);
									break;
								default:
									console.error("unknown schedule frequency: " + value.frequency.selected);
							}
							// finally show our new charge point
							clonedElement.removeClass('charge-point-schedule-plan-template').removeClass('hide');
						} else {
							console.error('schedule plan ' + key + ' already exists');
						}
					}
				} else {
					parent.find(".charge-point-schedule-plan-missing").removeClass("hide");
				}
			}
		} else {
			console.debug('no charge points with charge template "' + templateIndex + '" found');
		}
	}
}

function refreshVehicleSoc(vehicleIndex) {
	if (vehicleSoc.hasOwnProperty(vehicleIndex)) {
		$('.charge-point-vehicle-data[data-ev="'+vehicleIndex+'"]').each(function () {
			var parent = $(this).closest('.charge-point-card');
			var elementIsConfigured = $(parent).find('.charge-point-soc-configured'); // now get parents respective child element
			var elementIsNotConfigured = $(parent).find('.charge-point-soc-not-configured'); // now get parents respective child element
			if (vehicleSoc[vehicleIndex].type === null) {
				// not configured
				$(elementIsNotConfigured).removeClass('hide');
				$(elementIsConfigured).addClass('hide');
			} else {
				// configured
				$(elementIsNotConfigured).addClass('hide');
				$(elementIsConfigured).removeClass('hide');
			}
			if (vehicleSoc[vehicleIndex].type == "manual") {
				// "manual"
				$(elementIsConfigured).addClass('manualSoC');
				$(elementIsConfigured).find('.charge-point-manual-soc-symbol').removeClass('hide');
				$(elementIsConfigured).find('.charge-point-reload-soc-symbol').addClass('hide');
			} else {
				$(elementIsConfigured).removeClass('manualSoC');
				$(elementIsConfigured).find('.charge-point-manual-soc-symbol').addClass('hide');
				$(elementIsConfigured).find('.charge-point-reload-soc-symbol').removeClass('hide');
			}
		});
	} else {
		console.warn("no vehicle soc data found for index", vehicleIndex);
	}
}

function handleMessage(mqttTopic, mqttPayload) {
	// receives all messages and calls respective function to process them
	// console.info("new message: "+mqttTopic+": "+mqttPayload);
	processPreloader(mqttTopic);
	if (mqttTopic.match(/^openwb\/counter\/[0-9]+\//i)) { processCounterMessages(mqttTopic, mqttPayload) }
	else if (mqttTopic.match(/^openwb\/counter\//i)) { processGlobalCounterMessages(mqttTopic, mqttPayload); }
	else if (mqttTopic.match(/^openwb\/bat\//i)) { processBatteryMessages(mqttTopic, mqttPayload); }
	else if (mqttTopic.match(/^openwb\/pv\//i)) { processPvMessages(mqttTopic, mqttPayload); }
	else if (mqttTopic.match(/^openwb\/chargepoint\//i)) { processChargePointMessages(mqttTopic, mqttPayload); }
	else if (mqttTopic.match(/^openwb\/vehicle\//i)) { processVehicleMessages(mqttTopic, mqttPayload); }
	else if (mqttTopic.match(/^openwb\/general\/chargemode_config\/pv_charging\//i)) { processPvConfigMessages(mqttTopic, mqttPayload); }
	else if (mqttTopic.match(/^openwb\/graph\//i)) { processGraphMessages(mqttTopic, mqttPayload); }
	else if (mqttTopic.match(/^openwb\/optional\/et\//i)) { processETProviderMessages(mqttTopic, mqttPayload); }
	// else if ( mqttTopic.match( /^openwb\/global\//i) ) { processGlobalMessages(mqttTopic, mqttPayload); }
	// else if ( mqttTopic.match( /^openwb\/system\//i) ) { processSystemMessages(mqttTopic, mqttPayload); }
	// else if ( mqttTopic.match( /^openwb\/verbraucher\//i) ) { processVerbraucherMessages(mqttTopic, mqttPayload); }
	// else if ( mqttTopic.match( /^openwb\/hook\//i) ) { processHookMessages(mqttTopic, mqttPayload); }
	// else if ( mqttTopic.match( /^openwb\/SmartHome\/Devices\//i) ) { processSmartHomeDevicesMessages(mqttTopic, mqttPayload); }
	// else if ( mqttTopic.match( /^openwb\/config\/get\/SmartHome\/Devices\//i) ) { processSmartHomeDevicesConfigMessages(mqttTopic, mqttPayload); }
	// else if ( mqttTopic.match( /^openwb\/config\/get\/sofort\/lp\//i) ) { processSofortConfigMessages(mqttTopic, mqttPayload); }
} // end handleMessage

function processGlobalCounterMessages(mqttTopic, mqttPayload) {
	if (mqttTopic.match(/^openwb\/counter\/get\/hierarchy$/i)) {
		// this topic is used to populate the charge point list
		// unsubscribe from other topics relevant for charge points
		topicsToSubscribe.forEach((topic) => {
			if (topic[0].match(/^openwb\/(chargepoint|vehicle)\//i)) {
				client.unsubscribe(topic[0]);
			}
		});
		// first remove all charge points except the template
		$('.charge-point-card[data-cp]').not('.charge-point-template').remove();
		// now create any other charge point
		var hierarchy = JSON.parse(mqttPayload);
		if (hierarchy.length) {
			for (const element of hierarchy) {
				if (element.type == "counter") {
					evuCounterIndex = element.id
					break
				}
			}
			console.debug("EVU counter index: " + evuCounterIndex);
			createChargePoint(hierarchy[0]);
			// subscribe to other topics relevant for charge points
			topicsToSubscribe.forEach((topic) => {
				if (topic[0].match(/^openwb\/(chargepoint|vehicle)\//i)) {
					client.subscribe(topic[0], { qos: 0 });
				}
			});
		}
	} else if (mqttTopic.match(/^openwb\/counter\/set\/home_consumption$/i)) {
		var unit = 'W';
		var powerHome = parseInt(mqttPayload, 10);
		if (isNaN(powerHome)) {
			powerHome = 0;
		}
		if (powerHome > 999) {
			powerHome = (powerHome / 1000).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
			unit = 'k' + unit;
		} else {
			powerHome = powerHome.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
		}
		$('.house-consumption-power').text(powerHome + ' ' + unit);
	} else if (mqttTopic.match(/^openwb\/counter\/set\/daily_yield_home_consumption$/i)) {
		var unit = "Wh";
		var unitPrefix = "";
		var houseDailyYield = parseFloat(mqttPayload);
		if (isNaN(houseDailyYield)) {
			houseDailyYield = 0;
		}
		if (houseDailyYield > 999) {
			houseDailyYield = (houseDailyYield / 1000).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
			unitPrefix = "k";
		} else {
			houseDailyYield = houseDailyYield.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
		}
		$('.house-consumption-daily').text(houseDailyYield + ' ' + unitPrefix + unit);
	}
}

function processEvuMessages(mqttTopic, mqttPayload) {
	// processes mqttTopic for topic openWB/counter/0
	// called by handleMessage
	if (mqttTopic == 'openWB/counter/' + evuCounterIndex + '/get/power') {
		var unit = 'W';
		var powerEvu = parseInt(mqttPayload, 10);
		if (isNaN(powerEvu)) {
			powerEvu = 0;
		}
		var importing = (powerEvu >= 0);
		if (powerEvu < 0) {
			powerEvu *= -1;
		}
		if (powerEvu > 999) {
			powerEvu = (powerEvu / 1000).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
			unit = 'k' + unit;
		} else {
			powerEvu = powerEvu.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
		}
		if (importing) {
			$('.grid-importing').removeClass('hide');
			$('.grid-exporting').addClass('hide');
		} else {
			$('.grid-exporting').removeClass('hide');
			$('.grid-importing').addClass('hide');
		}
		$('.grid-power').text(powerEvu + ' ' + unit);
	} else if (mqttTopic == 'openWB/counter/' + evuCounterIndex + '/get/daily_imported') {
		var unit = "Wh";
		var unitPrefix = "";
		var gridDailyYield = parseFloat(mqttPayload);
		if (isNaN(gridDailyYield)) {
			gridDailyYield = 0;
		}
		if (gridDailyYield > 999) {
			gridDailyYield = (gridDailyYield / 1000).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
			unitPrefix = "k";
		} else {
			gridDailyYield = gridDailyYield.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
		}
		$('.grid-import').text(gridDailyYield + ' ' + unitPrefix + unit);
	} else if (mqttTopic == 'openWB/counter/' + evuCounterIndex + '/get/daily_exported') {
		var unit = "Wh";
		var unitPrefix = "";
		var gridDailyYield = parseFloat(mqttPayload);
		if (isNaN(gridDailyYield)) {
			gridDailyYield = 0;
		}
		if (gridDailyYield > 999) {
			gridDailyYield = (gridDailyYield / 1000).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
			unitPrefix = "k";
		} else {
			gridDailyYield = gridDailyYield.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
		}
		$('.grid-export').text(gridDailyYield + ' ' + unitPrefix + unit);
	}
}

function processCounterMessages(mqttTopic, mqttPayload) {
	let counterIndex = getIndex(mqttTopic);
	if (counterIndex == evuCounterIndex) {
		console.debug("evu counter message received");
		processEvuMessages(mqttTopic, mqttPayload);
	} else {
		/* nothing here yet */
	}
}

function processBatteryMessages(mqttTopic, mqttPayload) {
	// processes mqttTopic for topic openWB/housebattery
	// called by handleMessage
	if (mqttTopic == 'openWB/bat/config/configured') {
		if (mqttPayload == "true") {
			$('.house-battery-configured').removeClass('hide');
		} else {
			$('.house-battery-configured').addClass('hide');
		}
	} else if (mqttTopic == 'openWB/bat/get/power') {
		var unit = 'W';
		var speicherWatt = parseInt(mqttPayload, 10);
		var charging = (speicherWatt >= 0);
		if (isNaN(speicherWatt)) {
			speicherWatt = 0;
		}
		if (speicherWatt < 0) {
			speicherWatt *= -1;
		}
		if (speicherWatt > 999) {
			speicherWatt = (speicherWatt / 1000).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
			unit = 'k' + unit;
		} else {
			speicherWatt = speicherWatt.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
		}
		$('.house-battery-sum-power').text(speicherWatt + ' ' + unit);
		if (charging == true) {
			$('.house-battery-sum-charging').removeClass('hide');
			$('.house-battery-sum-discharging').addClass('hide');
		} else {
			$('.house-battery-sum-discharging').removeClass('hide');
			$('.house-battery-sum-charging').addClass('hide');
		}
	} else if (mqttTopic == 'openWB/bat/get/soc') {
		var unit = "%";
		var speicherSoc = parseInt(mqttPayload, 10);
		if (isNaN(speicherSoc) || speicherSoc < 0 || speicherSoc > 100) {
			speicherSoc = '--';
		}
		$('.house-battery-sum-soc').text(speicherSoc + ' ' + unit);
	} else if (mqttTopic == 'openWB/bat/get/daily_exported') {
		var unit = "Wh";
		var unitPrefix = "";
		var batDailyYield = parseFloat(mqttPayload);
		if (isNaN(batDailyYield)) {
			batDailyYield = 0;
		}
		if (batDailyYield > 999) {
			batDailyYield = (batDailyYield / 1000).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
			unitPrefix = "k";
		} else {
			batDailyYield = batDailyYield.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
		}
		$('.house-battery-sum-export').text(batDailyYield + ' ' + unitPrefix + unit);
	} else if (mqttTopic == 'openWB/bat/get/daily_imported') {
		var unit = "Wh";
		var unitPrefix = "";
		var batDailyYield = parseFloat(mqttPayload);
		if (isNaN(batDailyYield)) {
			batDailyYield = 0;
		}
		if (batDailyYield > 999) {
			batDailyYield = (batDailyYield / 1000).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
			unitPrefix = "k";
		} else {
			batDailyYield = batDailyYield.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
		}
		$('.house-battery-sum-import').text(batDailyYield + ' ' + unitPrefix + unit);
	}
}

function processPvMessages(mqttTopic, mqttPayload) {
	// processes mqttTopic for topic openWB/pv
	// called by handleMessage
	if (mqttTopic == 'openWB/pv/config/configured') {
		if (mqttPayload == "true") {
			$('.pv-configured').removeClass('hide');
		} else {
			$('.pv-configured').addClass('hide');
		}
	} else if (mqttTopic == 'openWB/pv/get/power') {
		var unit = 'W';
		var unitPrefix = '';
		var pvWatt = parseInt(mqttPayload, 10);
		if (isNaN(pvWatt)) {
			pvWatt = 0;
		}
		if (pvWatt <= 0) {
			// production is negative for calculations so adjust for display
			pvWatt *= -1;
		}
		// adjust and add unit
		if (pvWatt > 999) {
			pvWatt = (pvWatt / 1000).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
			unitPrefix = 'k'
		} else {
			pvWatt = pvWatt.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
		}
		$('.pv-sum-power').text(pvWatt + ' ' + unitPrefix + unit);
	} else if (mqttTopic == 'openWB/pv/get/daily_exported') {
		var unit = "Wh";
		var unitPrefix = "";
		var pvDailyYield = parseFloat(mqttPayload);
		if (isNaN(pvDailyYield)) {
			pvDailyYield = 0;
		}
		if (pvDailyYield > 999) {
			pvDailyYield = (pvDailyYield / 1000).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
			unitPrefix = "k";
		} else {
			pvDailyYield = pvDailyYield.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
		}
		$('.pv-sum-production').text(pvDailyYield + ' ' + unitPrefix + unit);
	}
	// else if ( mqttTopic == 'openWB/pv/bool70PVDynStatus') {
	// 	switch (mqttPayload) {
	// 		case '0':
	// 			// deaktiviert
	// 			$('#70PvBtn').removeClass('btn-success');
	// 			break;
	// 		case '1':
	// 			// ev priority
	// 			$('#70PvBtn').addClass('btn-success');
	// 		break;
	// 	}
	// }
}

function processPvConfigMessages(mqttTopic, mqttPayload) {
	if (mqttTopic == 'openWB/general/chargemode_config/pv_charging/bat_prio') {
		var element = $('.house-battery-priority');
		data = JSON.parse(mqttPayload);
		if (data == true) {
			element.bootstrapToggle('on', true); // do not fire a changed-event to prevent a loop!
		} else {
			element.bootstrapToggle('off', true); // do not fire a changed-event to prevent a loop!
		}
	}
	// else if ( mqttTopic == 'openWB/config/get/pv/nurpv70dynact' ) {
	// 	//  and sets icon in mode select button
	// 	switch (mqttPayload) {
	// 		case '0':
	// 			// deaktiviert
	// 			$('#70ModeBtn').addClass('hide');
	// 			break;
	// 		case '1':
	// 			// aktiviert
	// 			$('#70ModeBtn').removeClass('hide');
	// 		break;
	// 	}
	// }
	// else if ( mqttTopic == 'openWB/config/get/pv/minCurrentMinPv' ) {
	// 	setInputValue('minCurrentMinPv', mqttPayload);
	// }
}

function processChargePointMessages(mqttTopic, mqttPayload) {
	// processes mqttTopic for topic openWB/chargepoint
	// called by handleMessage
	if (mqttTopic == 'openWB/chargepoint/get/power') {
		var unit = "W";
		var unitPrefix = "";
		var powerAllLp = parseInt(mqttPayload, 10);
		if (isNaN(powerAllLp)) {
			powerAllLp = 0;
		}
		if (powerAllLp > 999) {
			powerAllLp = (powerAllLp / 1000).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
			unitPrefix = 'k';
		} else {
			powerAllLp = powerAllLp.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
		}
		$('.charge-point-sum-power').text(powerAllLp + ' ' + unitPrefix + unit);
	} else if (mqttTopic == 'openWB/chargepoint/get/daily_imported') {
		var unit = "Wh";
		var unitPrefix = "";
		var dailyYield = parseFloat(mqttPayload);
		if (isNaN(dailyYield)) {
			dailyYield = 0;
		}
		if (dailyYield > 999) {
			dailyYield = (dailyYield / 1000).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
			unitPrefix = "k";
		} else {
			dailyYield = dailyYield.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
		}
		$('.charge-point-sum-import-daily').text(dailyYield + ' ' + unitPrefix + unit);
	} else if (mqttTopic == 'openWB/chargepoint/get/daily_exported') {
		var unit = "Wh";
		var unitPrefix = "";
		var dailyYield = parseFloat(mqttPayload);
		if (isNaN(dailyYield)) {
			dailyYield = 0;
		}
		if (dailyYield > 999) {
			dailyYield = (dailyYield / 1000).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
			unitPrefix = "k";
		} else {
			dailyYield = dailyYield.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
		}
		$('.charge-point-sum-export-daily').text(dailyYield + ' ' + unitPrefix + unit);
	} else if (mqttTopic.match(/^openwb\/chargepoint\/[0-9]+\/config$/i)) {
		// JSON data
		// name: str
		// template: int
		// connected_phases: int
		// phase_1: int
		// auto_phase_switch_hw: bool
		// control_pilot_interruption_hw: bool
		// connection_module: JSON: { selected: str, config: JSON: individual configuration parameters for module }
		var index = getIndex(mqttTopic); // extract number between two / /
		var configMessage = JSON.parse(mqttPayload);
		var parent = $('.charge-point-card[data-cp="' + index + '"]'); // get parent row element for charge point
		// name
		var element = parent.find('.charge-point-name'); // now get parents respective child element
		$(element).text(configMessage.name);
		// template
		parent.attr('data-charge-point-template', configMessage.template).data('charge-point-template', configMessage.template);
	} else if (mqttTopic.match(/^openwb\/chargepoint\/[0-9]+\/get\/state_str$/i)) {
		var index = getIndex(mqttTopic); // extract number between two / /
		var parent = $('.charge-point-card[data-cp="' + index + '"]'); // get parent row element for charge point
		var element = parent.find('.charge-point-state-str'); // now get parents respective child element
		element.text(JSON.parse(mqttPayload));
	} else if (mqttTopic.match(/^openwb\/chargepoint\/[0-9]+\/get\/fault_str$/i)) {
		// console.log("fault str");
		var index = getIndex(mqttTopic); // extract number between two / /
		var parent = $('.charge-point-card[data-cp="' + index + '"]'); // get parent row element for charge point
		var element = parent.find('.charge-point-fault-str'); // now get parents respective child element
		element.text(JSON.parse(mqttPayload));
	} else if (mqttTopic.match(/^openwb\/chargepoint\/[0-9]+\/get\/fault_state$/i)) {
		// console.log("fault state");
		var index = getIndex(mqttTopic); // extract number between two / /
		var parent = $('.charge-point-card[data-cp="' + index + '"]'); // get parent row element for charge point
		parent.find('.charge-point-fault-state[data-option="' + mqttPayload + '"').removeClass('hide');
		parent.find('.charge-point-fault-state').not('[data-option="' + mqttPayload + '"]').addClass('hide');
		// textElement = parent.find('.charge-point-fault-str');
		alertElement = parent.find('.charge-point-alert');
		switch (parseInt(mqttPayload, 10)) {
			case 1: // warning
				$(alertElement).addClass('alert-warning');
				$(alertElement).removeClass('alert-danger');
				$(alertElement).removeClass('hide');
				break;
			case 2: // error
				$(alertElement).removeClass('alert-warning');
				$(alertElement).addClass('alert-danger');
				$(alertElement).removeClass('hide');
				break;
			default:
				$(alertElement).addClass('hide');
				$(alertElement).removeClass('alert-warning');
				$(alertElement).removeClass('alert-danger');
		}
	} else if (mqttTopic.match(/^openWB\/chargepoint\/[0-9]+\/get\/power$/i)) {
		var unit = "W";
		var index = getIndex(mqttTopic); // extract number between two / /
		var parent = $('.charge-point-card[data-cp="' + index + '"]'); // get parent row element for charge point
		var element = parent.find('.charge-point-power'); // now get parents respective child element
		var actualPower = parseInt(mqttPayload, 10);
		if (isNaN(actualPower)) {
			actualPower = 0;
		}
		if (actualPower > 999) {
			actualPower = (actualPower / 1000).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
			unit = 'k' + unit;
		} else {
			actualPower = actualPower.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
		}
		element.text(actualPower + ' ' + unit);
	} else if (mqttTopic.match(/^openWB\/chargepoint\/[0-9]+\/set\/log\/imported_since_plugged$/i)) {
		// energy charged since ev was plugged in
		// also calculates and displays km charged
		// console.log("charged since plugged counter");
		var index = getIndex(mqttTopic); // extract number between two / /
		var parent = $('.charge-point-card[data-cp="' + index + '"]'); // get parent row element for charge point
		var element = parent.find('.charge-point-energy-since-plugged'); // now get parents respective child element
		var energyCharged = parseFloat(mqttPayload) / 1000;
		if (isNaN(energyCharged)) {
			energyCharged = 0;
		}
		element.text(energyCharged.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + ' kWh');
		var rangeChargedElement = parent.find('.charge-point-range-since-plugged'); // now get parents child element
		var consumption = parseFloat($(rangeChargedElement).data('consumption'));
		var rangeCharged = '';
		if (!isNaN(consumption) && consumption > 0) {
			rangeCharged = (energyCharged / consumption) * 100;
			rangeCharged = ' / ' + rangeCharged.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + ' km';
		}
		$(rangeChargedElement).text(rangeCharged);
	} else if (mqttTopic.match(/^openwb\/chargepoint\/[0-9]+\/get\/plug_state$/i)) {
		// status ev plugged in or not
		var index = getIndex(mqttTopic); // extract number between two / /
		var parent = $('.charge-point-card[data-cp="' + index + '"]'); // get parent row element for charge point
		var element = parent.find('.charge-point-plug-state'); // now get parents respective child element
		if (JSON.parse(mqttPayload) == true) {
			element.removeClass('hide');
		} else {
			element.addClass('hide');
		}
	} else if (mqttTopic.match(/^openwb\/chargepoint\/[0-9]+\/get\/charge_state$/i)) {
		var index = getIndex(mqttTopic); // extract number between two / /
		var parent = $('.charge-point-card[data-cp="' + index + '"]'); // get parent row element for charge point
		var element = parent.find('.charge-point-charge-state'); // now get parents respective child element
		if (JSON.parse(mqttPayload) == true) {
			element.removeClass('text-orange').addClass('text-green');
		} else {
			element.removeClass('text-green').addClass('text-orange');
		}
	} else if (mqttTopic.match(/^openwb\/chargepoint\/[0-9]+\/set\/manual_lock$/i)) {
		// console.log("charge point manual_lock");
		var index = getIndex(mqttTopic); // extract number between two / /
		var parent = $('.charge-point-card[data-cp="' + index + '"]'); // get parent row element for charge point
		var element = parent.find('.charge-point-manual-lock'); // now get parents respective child element
		if (JSON.parse(mqttPayload) == true) {
			// element.prop('checked', true);
			element.bootstrapToggle('on', true); // do not fire a changed-event to prevent a loop!
		} else {
			// element.prop('checked', false);
			element.bootstrapToggle('off', true); // do not fire a changed-event to prevent a loop!
		}
	} else if (mqttTopic.match(/^openwb\/chargepoint\/[0-9]+\/get\/enabled$/i)) {
		// console.log("charge point enabled");
		var index = getIndex(mqttTopic); // extract number between two / /
		var parent = $('.charge-point-card[data-cp="' + index + '"]'); // get parent row element for charge point
		element = parent.find('.charge-point-state-enabled');
		if (JSON.parse(mqttPayload) == true) {
			$(element).addClass('charge-point-enabled');
			$(element).removeClass('charge-point-disabled');
		} else {
			$(element).removeClass('charge-point-enabled');
			$(element).addClass('charge-point-disabled');
		}
	} else if (mqttTopic.match(/^openwb\/chargepoint\/[0-9]+\/get\/phases_in_use/i)) {
		// console.log("charge point phases_in_use");
		var index = getIndex(mqttTopic); // extract number between two / /
		var parent = $('.charge-point-card[data-cp="' + index + '"]'); // get parent row element for charge point
		var element = parent.find('.charge-point-phases-in-use'); // now get parents respective child element
		var phasesInUse = parseInt(mqttPayload, 10);
		if (isNaN(phasesInUse) || phasesInUse < 1 || phasesInUse > 3) {
			element.text('/');
		} else {
			var phaseSymbols = ['', '\u2460', '\u2461', '\u2462'];
			element.text(phaseSymbols[phasesInUse]);
		}
	} else if (mqttTopic.match(/^openwb\/chargepoint\/[0-9]+\/set\/current/i)) {
		// target current value at charge point
		// console.log("charge point set current");
		var unit = "A";
		var index = getIndex(mqttTopic); // extract number between two / /
		var parent = $('.charge-point-card[data-cp="' + index + '"]'); // get parent row element for charge point
		var element = parent.find('.charge-point-set-current'); // now get parents respective child element
		var targetCurrent = parseInt(mqttPayload, 10);
		if (isNaN(targetCurrent)) {
			targetCurrent = 0;
		}
		element.text(targetCurrent + ' ' + unit);
	} else if (mqttTopic.match(/^openwb\/chargepoint\/[0-9]+\/get\/connected_vehicle\/soc$/i)) {
		// { "soc", "range", "range_unit", "timestamp", "fault_stat", "fault_str" }
		var index = getIndex(mqttTopic); // extract number between two / /
		var socData = JSON.parse(mqttPayload);
		var parent = $('.charge-point-card[data-cp="' + index + '"]'); // get parent row element for charge point
		// "soc" float unit: %
		var element = parent.find('.charge-point-soc'); // now get parents respective child element
		var soc = socData.soc;
		if (isNaN(soc) || soc < 0 || soc > 100) {
			soc = '--';
		}
		element.text(soc);
		var spinner = parent.find('.charge-point-reload-soc-symbol');
		spinner.removeClass('fa-spin');
		// "range" + "range_unit" + "timestamp"
		element.attr('title', Math.round(socData.range) + socData.range_unit + " (" + socData.timestamp + ")");
		// "fault_stat" ToDo
		// "fault_str" ToDo
	} else if (mqttTopic.match(/^openwb\/chargepoint\/[0-9]+\/get\/connected_vehicle\/info$/i)) {
		// info of the vehicle if connected
		// { "id", "name" }
		var index = getIndex(mqttTopic); // extract number between two / /
		var infoData = JSON.parse(mqttPayload);
		var parent = $('.charge-point-card[data-cp="' + index + '"]'); // get parent row element for charge point
		// "id" int
		parent.find('.charge-point-vehicle-select').val(infoData.id); // set selectBox to received id
		parent.find('.charge-point-vehicle-data[data-ev]').attr('data-ev', infoData.id).data('ev', infoData.id); // set data-ev setting for this charge point
		// "name" str
		parent.find('.charge-point-vehicle-name').text(infoData.name);
		refreshVehicleSoc(infoData.id);
	} else if (mqttTopic.match(/^openwb\/chargepoint\/[0-9]+\/get\/connected_vehicle\/config$/i)) {
		// settings of the vehicle if connected
		// { "charge_template", "ev_template", "chargemode", "priority", "average_consumption" }
		var index = getIndex(mqttTopic); // extract number between two / /
		var configData = JSON.parse(mqttPayload);
		var parent = $('.charge-point-card[data-cp="' + index + '"]'); // get parent row element for charge point
		// "charge_template" int
		parent.attr('data-charge-template', configData.charge_template).data('charge-template', configData.charge_template);
		refreshChargeTemplate(configData.charge_template);
		// "ev_template" int
		parent.attr('data-ev-template', configData.ev_template).data('ev-template', configData.ev_template);
		// "chargemode" str
		chargemodeRadio = parent.find('.charge-point-charge-mode input[type=radio][data-option="' + configData.chargemode + '"]');
		chargemodeRadio.prop('checked', true); // check selected chargemode radio button
		friendlyChargemode = chargemodeRadio.parent().text();
		parent.find('.charge-point-vehicle-charge-mode').text(friendlyChargemode); // set chargemode in card header
		chargemodeRadio.parent().addClass('active'); // activate selected chargemode button
		parent.find('.charge-point-charge-mode input[type=radio]').not('[data-option="' + configData.chargemode + '"]').each(function () {
			$(this).prop('checked', false); // uncheck all other radio buttons
			$(this).parent().removeClass('active'); // deselect all other chargemode buttons
		});
		chargemodeOptionsShowHide(chargemodeRadio, configData.chargemode);
		// "priority" bool
		var priorityElement = parent.find('.charge-point-vehicle-priority'); // now get parents respective child element
		if (configData.priority == true) {
			// element.prop('checked', true);
			priorityElement.bootstrapToggle('on', true); // do not fire a changed-event to prevent a loop!
		} else {
			// element.prop('checked', false);
			priorityElement.bootstrapToggle('off', true); // do not fire a changed-event to prevent a loop!
		}
		// "average_consumption" int unit: Wh/100km
		var rangeChargedElement = parent.find('.charge-point-range-since-plugged');
		rangeChargedElement.data('consumption', configData.average_consumption).attr('data-consumption', configData.average_consumption);
		// if already energyCharged-displayed, update rangeCharged
		var energyCharged = parseFloat(parent.find('.charge-point-energy-since-plugged').text().replace(',', '.')); // now get parents respective energyCharged child element
		var rangeCharged = '';
		if (!isNaN(energyCharged) && configData.average_consumption > 0) {
			rangeCharged = (energyCharged / configData.average_consumption) * 100;
			rangeCharged = ' / ' + rangeCharged.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + ' km';
		}
		$(rangeChargedElement).text(rangeCharged);
	}
	// else if ( mqttTopic.match( /^openwb\/lp\/[0-9]+\/kWhactualcharged$/i ) ) {
	// 	// energy charged since reset of limitation
	// 	var index = getIndex(mqttTopic);  // extract number between two / /
	// 	if ( isNaN(mqttPayload) ) {
	// 		mqttPayload = 0;
	// 	}
	// 	var parent = $('.charge-point-card[data-cp="' + index + '"]');  // get parent div element for charge limitation
	// 	var element = parent.find('.progress-bar');  // now get parents progressbar
	// 	element.data('actualCharged', mqttPayload);  // store value received
	// 	var limitElementId = 'lp/' + index + '/energyToCharge';
	// 	var limit = $('#' + $.escapeSelector(limitElementId)).val();  // slider value
	// 	if ( isNaN(limit) || limit < 2 ) {
	// 		limit = 2;  // minimum value
	// 	}
	// 	var progress = (mqttPayload / limit * 100).toFixed(0);
	// 	element.width(progress+"%");
	// }
	// else if ( mqttTopic.match( /^openwb\/lp\/[0-9]+\/timeremaining$/i ) ) {
	// 	// time remaining for charging to target value
	// 	var index = getIndex(mqttTopic);  // extract number between two / /
	// 	var parent = $('.charge-point-card[data-cp="' + index + '"]');  // get parent div element for charge limitation
	// 	var element = parent.find('.restzeitLp');  // get element
	// 	element.text('Restzeit ' + mqttPayload);
	// }
	// else if ( mqttTopic.match( /^openwb\/lp\/[0-9]+\/boolchargeatnight$/i ) ) {
	// 	var index = getIndex(mqttTopic);  // extract number between two / /
	// 	var parent = $('.charge-point-card[data-cp="' + index + '"]');  // get parent row element for charge point
	// 	var element = parent.find('.nightChargingLp');  // now get parents respective child element
	// 	if ( mqttPayload == 1 ) {
	// 		element.removeClass('hide');
	// 	} else {
	// 		element.addClass('hide');
	// 	}
	// }
	// else if ( mqttTopic.match( /^openwb\/lp\/[0-9]+\/autolockconfigured$/i ) ) {
	// 	var index = getIndex(mqttTopic);  // extract first match = number from
	// 	var parent = $('.charge-point-card[data-cp="' + index + '"]');  // get parent row element for charge point
	// 	var element = parent.find('.autolockConfiguredLp');  // now get parents respective child element
	// 	if ( mqttPayload == 0 ) {
	// 		element.addClass('hide');
	// 	} else {
	// 		element.removeClass('hide');
	// 	}
	// }
	// else if ( mqttTopic.match( /^openwb\/lp\/[0-9]+\/autolockstatus$/i ) ) {
	// 	// values used for AutolockStatus flag:
	// 	// 0 = standby
	// 	// 1 = waiting for autolock
	// 	// 2 = autolock performed
	// 	// 3 = auto-unlock performed
	// 	var index = getIndex(mqttTopic);  // extract number between two / /
	// 	var parent = $('.charge-point-card[data-cp="' + index + '"]');  // get parent row element for charge point
	// 	var element = parent.find('.autolockConfiguredLp');  // now get parents respective child element
	// 	switch ( mqttPayload ) {
	// 		case '0':
	// 			// remove animation from span and set standard colored key icon
	// 			element.removeClass('fa-lock fa-lock-open animate-alertPulsation text-red text-green');
	// 			element.addClass('fa-key');
	// 			break;
	// 		case '1':
	// 			// add animation to standard icon
	// 			element.removeClass('fa-lock fa-lock-open text-red text-green');
	// 			element.addClass('fa-key animate-alertPulsation');
	// 			break;
	// 		case '2':
	// 			// add red locked icon
	// 			element.removeClass('fa-lock-open fa-key animate-alertPulsation text-green');
	// 			element.addClass('fa-lock text-red');
	// 			break;
	// 		case '3':
	// 			// add green unlock icon
	// 			element.removeClass('fa-lock fa-key animate-alertPulsation text-red');
	// 			element.addClass('fa-lock-open text-green');
	// 			break;
	// 	}
	// }
	// else if ( mqttTopic.match( /^openwb\/lp\/[0-9]+\/boolfinishattimechargeactive$/i ) ) {
	// 	// respective charge point configured
	// 	var index = getIndex(mqttTopic);  // extract number between two / /
	// 	var parent = $('.charge-point-card[data-cp="' + index + '"]');  // get parent row element for charge point
	// 	var element = parent.find('.targetChargingLp');  // now get parents respective child element
	// 	if (mqttPayload == 1) {
	// 		element.removeClass('hide');
	// 	} else {
	// 		element.addClass('hide');
	// 	}
	// }
}

function processVehicleMessages(mqttTopic, mqttPayload) {
	if (mqttTopic.match(/^openwb\/vehicle\/[0-9]+\/name$/i)) {
		// this topic is used to populate the charge point list
		var index = getIndex(mqttTopic); // extract number between two / /
		$('.charge-point-vehicle-select').each(function () {
			myOption = $(this).find('option[value=' + index + ']');
			if (myOption.length > 0) {
				myOption.text(JSON.parse(mqttPayload)); // update vehicle name if option with index is present
			} else {
				$(this).append('<option value="' + index + '">' + JSON.parse(mqttPayload) + '</option>'); // add option with index
				if (parseInt($(this).closest('.charge-point-vehicle-data[data-ev]').data('ev')) == index) { // update selected element if match with our index
					$(this).val(index);
				}
			}
		});
	} else if (mqttTopic.match(/^openwb\/vehicle\/[0-9]+\/soc_module\/config$/i)) {
		// { "type": "<selected module>", "configuration": { <module specific data> } }
		// we use the data "type" to detect, if a soc module is configure (type != None) or manual soc is selected (type == manual)
		var vehicleIndex = getIndex(mqttTopic); // extract number between two / /
		var configData = JSON.parse(mqttPayload);
		vehicleSoc[vehicleIndex] = configData;
		console.debug("update vehicle soc config", vehicleIndex, configData);
		refreshVehicleSoc(vehicleIndex);
	} else if (mqttTopic.match(/^openwb\/vehicle\/template\/charge_template\/[0-9]+$/i)) {
		templateIndex = mqttTopic.match(/[0-9]+$/i);
		chargeModeTemplate[templateIndex] = JSON.parse(mqttPayload);
		refreshChargeTemplate(templateIndex);
	} else if (mqttTopic.match(/^openwb\/vehicle\/template\/charge_template\/[0-9]+\/chargemode\/scheduled_charging\/plans\/[0-9]+$/i)) {
		templateIndex = mqttTopic.match(/[0-9]+/i)[0];
		planIndex = mqttTopic.match(/[0-9]+$/i)[0];
		try {
			const newPlan = JSON.parse(mqttPayload);
			if (! (templateIndex in schedulePlan)) {
				schedulePlan[templateIndex] = {};
			}
			schedulePlan[templateIndex][planIndex] = newPlan;
		} catch (error) {
			console.error("error parsing schedule plan!");
			delete schedulePlan[templateIndex][planIndex];
			if (Object.keys(schedulePlan[templateIndex]).length == 0) {
				delete schedulePlan[templateIndex];
			}
		}
		refreshChargeTemplate(templateIndex);
	}
}

function processGraphMessages(mqttTopic, mqttPayload) {
	// processes mqttTopic for topic openWB/graph
	// called by handleMessage
	if (mqttTopic == 'openWB/graph/boolDisplayHouseConsumption') {
		if (mqttPayload == 1) {
			boolDisplayHouseConsumption = false;
			hidehaus = 'foo';
		} else {
			boolDisplayHouseConsumption = true;
			hidehaus = 'Hausverbrauch';
		}
		checkgraphload();
	} else if (mqttTopic == 'openWB/graph/boolDisplayLegend') {
		if (mqttPayload == 0) {
			boolDisplayLegend = false;
		} else {
			boolDisplayLegend = true;
		}
		checkgraphload();
	} else if (mqttTopic == 'openWB/graph/boolDisplayLiveGraph') {
		if (mqttPayload == 0) {
			$('#theGraph').addClass('hide');
			boolDisplayLiveGraph = false;
		} else {
			$('#theGraph').removeClass('hide');
			boolDisplayLiveGraph = true;
		}
	} else if (mqttTopic == 'openWB/graph/boolDisplayEvu') {
		if (mqttPayload == 1) {
			boolDisplayEvu = false;
			hideevu = 'foo';
		} else {
			boolDisplayEvu = true;
			hideevu = 'Bezug';
		}
		checkgraphload();
	} else if (mqttTopic == 'openWB/graph/boolDisplayPv') {
		if (mqttPayload == 1) {
			boolDisplayPv = false;
			hidepv = 'foo';
		} else {
			boolDisplayPv = true;
			hidepv = 'PV';
		}
		checkgraphload();
	} else if (mqttTopic.match(/^openwb\/graph\/booldisplaylp[0-9]+$/i)) {
		var index = mqttTopic.match(/(\d+)(?!.*\d)/g)[0]; // extract last match = number from mqttTopic
		// now call functions or set variables corresponding to the index
		if (mqttPayload == 1) {
			window['boolDisplayLp' + index] = false;
			window['hidelp' + index] = 'foo';
		} else {
			window['boolDisplayLp' + index] = true;
			window['hidelp' + index] = 'Lp' + index;
		}
		checkgraphload();
	} else if (mqttTopic == 'openWB/graph/boolDisplayLpAll') {
		if (mqttPayload == 1) {
			boolDisplayLpAll = false;
			hidelpa = 'foo';
		} else {
			boolDisplayLpAll = true;
			hidelpa = 'LP Gesamt';
		}
		checkgraphload();
	} else if (mqttTopic == 'openWB/graph/boolDisplaySpeicher') {
		if (mqttPayload == 1) {
			boolDisplaySpeicher = false;
			hidespeicher = 'foo';
		} else {
			hidespeicher = 'Speicher';
			boolDisplaySpeicher = true;
		}
		checkgraphload();
	} else if (mqttTopic == 'openWB/graph/boolDisplaySpeicherSoc') {
		if (mqttPayload == 1) {
			hidespeichersoc = 'foo';
			boolDisplaySpeicherSoc = false;
		} else {
			hidespeichersoc = 'Speicher SoC';
			boolDisplaySpeicherSoc = true;
		}
		checkgraphload();
	} else if (mqttTopic.match(/^openwb\/graph\/booldisplaylp[0-9]+soc$/i)) {
		var index = mqttTopic.match(/(\d+)(?!.*\d)/g)[0]; // extract last match = number from mqttTopic
		if (mqttPayload == 1) {
			$('#socenabledlp' + index).removeClass('hide');
			window['boolDisplayLp' + index + 'Soc'] = false;
			window['hidelp' + index + 'soc'] = 'foo';
		} else {
			$('#socenabledlp' + index).addClass('hide');
			window['boolDisplayLp' + index + 'Soc'] = true;
			window['hidelp' + index + 'soc'] = 'LP' + index + ' SoC';
		}
		checkgraphload();
	} else if (mqttTopic.match(/^openwb\/graph\/booldisplayload[1-9][0-9]*$/i)) {
		var index = mqttTopic.match(/(\d+)(?!.*\d)/g)[0]; // extract last match = number from mqttTopic
		// now call functions or set variables corresponding to the index
		if (mqttPayload == 1) {
			window['hideload' + index] = 'foo';
			window['boolDisplayLoad' + index] = false;
		} else {
			window['hideload' + index] = 'Verbraucher ' + index;
			window['boolDisplayLoad' + index] = true;
		}
		checkgraphload();
	} else if (mqttTopic.match(/^openwb\/graph\/alllivevaluesJson[1-9][0-9]*$/i)) {
		// graph messages if local connection
		var index = mqttTopic.match(/(\d+)$/g)[0]; // extract last match = number from mqttTopic
		// now call functions or set variables corresponding to the index
		if (initialRead == 0 && window['all' + index] == 0) {
			window['all' + index + 'p'] = mqttPayload;
			window['all' + index] = 1;
			mergeGraphData();
		}
	} else if (mqttTopic == 'openWB/graph/lastlivevaluesJson') {
		// graph messages if local connection
		if (initialRead > 0) {
			updateGraph(mqttPayload);
		}
		if (graphRefreshCounter > 60) {
			// reload graph completely
			initialRead = 0;
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
			graphCefreshCounter = 0;
			subscribeMqttGraphSegments();
		}
		graphRefreshCounter += 1;
	} else if (mqttTopic == 'openWB/graph/config/duration') {
		console.debug("graph duration: " + mqttPayload + " minutes");
		var duration = JSON.parse(mqttPayload);
		if (isNaN(duration) || duration < 10 || duration > 120) {
			console.error("bad graph duration received: " + mqttPayload + " setting to default of 30");
			duration = 30;
		}
		maxDisplayLength = duration * 6; // we get 6 measurements in every minute
	}
} // end processGraphMessages

function processETProviderMessages(mqttTopic, mqttPayload) {
	// processes mqttTopic for topic openWB/global
	// called by handleMessage
	if (mqttTopic == 'openWB/optional/et/active') {
		// console.log("et configured: "+mqttPayload);
		data = JSON.parse(mqttPayload);
		if (data == true) {
			$('.et-configured').removeClass('hide');
		} else {
			$('.et-configured').addClass('hide');
		}
	} else if (mqttTopic == 'openWB/optional/et/get/price') {
		var currentPrice = parseFloat(mqttPayload);
		$('.et-current-price').text(currentPrice.toLocaleString(undefined, { maximumFractionDigits: 2, minimumFractionDigits: 2 }) + ' ct/kWh');
		var maxPrice = parseFloat($('.et-price-limit').first().text().split(" ")[0].replace(/,/, '.'));
		// console.log("max: "+maxPrice+" current: "+currentPrice);
		if (!isNaN(currentPrice) && !isNaN(maxPrice)) {
			if (currentPrice <= maxPrice) {
				$('.et-blocked').addClass('hide');
				$('.et-not-blocked').removeClass('hide');
			} else {
				$('.et-not-blocked').addClass('hide');
				$('.et-blocked').removeClass('hide');
			}
		}
	} else if (mqttTopic == 'openWB/optional/et/config/max_price') {
		var maxPrice = parseFloat(mqttPayload);
		$('.et-price-limit').text(maxPrice.toLocaleString(undefined, { maximumFractionDigits: 2, minimumFractionDigits: 2 }) + ' ct/kWh');
		var currentPrice = parseFloat($('.et-current-price').first().text().split(" ")[0].replace(/,/, '.'));
		// console.log("max: "+maxPrice+" current: "+currentPrice);
		if (!isNaN(currentPrice) && !isNaN(maxPrice)) {
			if (currentPrice <= maxPrice) {
				$('.et-blocked').addClass('hide');
				$('.et-not-blocked').removeClass('hide');
			} else {
				$('.et-not-blocked').addClass('hide');
				$('.et-blocked').removeClass('hide');
			}
		}
	} else if (mqttTopic == 'openWB/optional/et/provider') {
		$('.et-name').text(JSON.parse(mqttPayload));
	}
	// else if ( mqttTopic == 'openWB/global/ETProvider/modulePath' ) {
	// 	$('.etproviderLink').attr("href", "/openWB/modules/"+mqttPayload+"/stromtarifinfo/infopage.php");
	// }
	// else if ( mqttTopic == 'openWB/global/awattar/pricelist' ) {
	// 	// read etprovider values and trigger graph creation
	// 	// loadElectricityPriceChart will show electricityPriceChartCanvas if etprovideraktiv=1 in openwb.conf
	// 	// graph will be redrawn after 5 minutes (new data pushed from cron5min.sh)
	// 	var csvData = [];
	// 	var rawcsv = mqttPayload.split(/\r?\n|\r/);
	// 	// skip first entry: it is module-name responsible for list
	// 	for (var i = 1; i < rawcsv.length; i++) {
	// 		csvData.push(rawcsv[i].split(','));
	// 	}
	// 	// Timeline (x-Achse) ist UNIX Timestamp in UTC, deshalb Umrechnung (*1000) in Javascript-Timestamp (mit Millisekunden)
	// 	electricityPriceTimeline = getCol(csvData, 0).map(function(x) { return x * 1000; });
	// 	// Chartline (y-Achse) ist Preis in ct/kWh
	// 	electricityPriceChartline = getCol(csvData, 1);

	// 	loadElectricityPriceChart();
	// }
}

// function processSofortConfigMessages(mqttTopic, mqttPayload) {
// 	// processes mqttTopic for topic openWB/config/get/sofort/
// 	// called by handleMessage
// 	var elementId = mqttTopic.replace('openWB/config/get/sofort/', '');
// 	var element = $('#' + $.escapeSelector(elementId));
// 	if ( element.attr('type') == 'range' ) {
// 		setInputValue(elementId, mqttPayload);
// 	} else if ( element.hasClass('btn-group-toggle') ) {
// 		setToggleBtnGroup(elementId, mqttPayload);
// 	}
// }

// function processGlobalMessages(mqttTopic, mqttPayload) {
// 	// processes mqttTopic for topic openWB/global
// 	// called by handleMessage
// 	if ( mqttTopic == 'openWB/global/WHouseConsumption' ) {
// 		var powerHouse = parseInt(mqttPayload, 10);
// 		if ( isNaN(powerHouse) ) {
// 			powerHouse = 0;
// 		}
// 		if ( powerHouse > 999 ) {
// 			powerHouse = (powerHouse / 1000).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' kW';
// 		} else {
// 			powerHouse += ' W';
// 		}
// 		$('#hausverbrauch').text(powerHouse);
// 	}
// 	else if ( mqttTopic == 'openWB/global/strLastmanagementActive' ) {
// 		if ( mqttPayload.length >= 5 ) {
// 			// if there is info-text in payload for topic, show the text
// 			$('#lastregelungaktiv').text(mqttPayload);
// 		} else {
// 			// if there is no text, show nothing (hides row)
// 			$('#lastregelungaktiv').text('');
// 		}
// 	}
// 	else if ( mqttTopic == 'openWB/global/ChargeMode' ) {
// 		// set modal button colors depending on charge mode
// 		// set visibility of divs
// 		// set visibility of priority icon depending on charge mode
// 		// (priority icon is encapsulated in another element hidden/shown by house battery configured or not)
// 		switch (mqttPayload) {
// 			case '0':
// 				// mode sofort
// 				$('#chargeModeSelectBtnText').text('Sofortladen');  // text btn mainpage
// 				$('.chargeModeBtn').removeClass('btn-success');  // changes to select btns in modal
// 				$('#chargeModeSofortBtn').addClass('btn-success');
// 				$('#targetChargingProgress').removeClass('hide');  // visibility of divs for special settings
// 				$('#sofortladenEinstellungen').removeClass('hide');
// 				$('#priorityEvBatteryIcon').addClass('hide');  // visibility of priority icon
// 				$('#minundpvladenEinstellungen').addClass('hide');

// 				break;
// 			case '1':
// 				// mode min+pv
// 				$('#chargeModeSelectBtnText').text('Min+PV-Laden');
// 				$('.chargeModeBtn').removeClass('btn-success');
// 				$('#chargeModeMinPVBtn').addClass('btn-success');
// 				$('#targetChargingProgress').addClass('hide');
// 				$('#sofortladenEinstellungen').addClass('hide');
// 				$('#priorityEvBatteryIcon').addClass('hide');
// 				$('#minundpvladenEinstellungen').removeClass('hide');

// 				break;
// 			case '2':
// 				// mode pv
// 				$('#chargeModeSelectBtnText').text('PV-Laden');
// 				$('.chargeModeBtn').removeClass('btn-success');
// 				$('#chargeModePVBtn').addClass('btn-success');
// 				$('#targetChargingProgress').addClass('hide');
// 				$('#sofortladenEinstellungen').addClass('hide');
// 				$('#priorityEvBatteryIcon').removeClass('hide');
// 				$('#minundpvladenEinstellungen').addClass('hide');

// 				break;
// 			case '3':
// 				// mode stop
// 				$('#chargeModeSelectBtnText').text('Stop');
// 				$('.chargeModeBtn').removeClass('btn-success');
// 				$('#chargeModeStopBtn').addClass('btn-success');
// 				$('#targetChargingProgress').addClass('hide');
// 				$('#sofortladenEinstellungen').addClass('hide');
// 				$('#priorityEvBatteryIcon').addClass('hide');
// 				$('#minundpvladenEinstellungen').addClass('hide');

// 				break;
// 			case '4':
// 				// mode standby
// 				$('#chargeModeSelectBtnText').text('Standby');
// 				$('.chargeModeBtn').removeClass('btn-success');
// 				$('#chargeModeStdbyBtn').addClass('btn-success');
// 				$('#targetChargingProgress').addClass('hide');
// 				$('#sofortladenEinstellungen').addClass('hide');
// 				$('#priorityEvBatteryIcon').addClass('hide');
// 				$('#minundpvladenEinstellungen').addClass('hide');
// 		}
// 	}
// 	else if ( mqttTopic == 'openWB/global/DailyYieldAllChargePointsKwh') {
// 		var llaDailyYield = parseFloat(mqttPayload);
// 		if ( isNaN(llaDailyYield) ) {
// 			llaDailyYield = 0;
// 		}
// 		if ( llaDailyYield >= 0 ) {
// 			var llaDailyYieldStr = ' (' + llaDailyYield.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' kWh)';
// 			$('#lladailyyield').text(llaDailyYieldStr);
// 		} else {
// 			$('#lladailyyield').text("");
// 		}

// 	}
// 	else if ( mqttTopic == 'openWB/global/DailyYieldHausverbrauchKwh') {
// 		var hausverbrauchDailyYield = parseFloat(mqttPayload);
// 		if ( isNaN(hausverbrauchDailyYield) ) {
// 			hausverbrauchDailyYield = 0;
// 		}
// 		if ( hausverbrauchDailyYield >= 0 ) {
// 			var hausverbrauchDailyYieldStr = ' (' + hausverbrauchDailyYield.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' kWh)';
// 			$('#hausverbrauchdailyyield').text(hausverbrauchDailyYieldStr);
// 		} else {
// 			$('#hausverbrauchdailyyield').text("");
// 		}

// 	}
// }

// function processSystemMessages(mqttTopic, mqttPayload) {
// 	// processes mqttTopic for topic openWB/system
// 	// called by handleMessage
// 	// console.log("received system msg: " + mqttTopic + ": " + mqttPayload);
// 	if ( mqttTopic == 'openWB/system/Timestamp') {
// 		var dateObject = new Date(mqttPayload * 1000);  // Unix timestamp to date-object
// 		var time = '&nbsp;';
// 		var date = '&nbsp;';
// 		if ( dateObject instanceof Date && !isNaN(dateObject.valueOf()) ) {
// 			// timestamp is valid date so process
// 			var HH = String(dateObject.getHours()).padStart(2, '0');
// 			var MM = String(dateObject.getMinutes()).padStart(2, '0');
// 			time = HH + ':'  + MM;
// 			var dd = String(dateObject.getDate()).padStart(2, '0');  // format with leading zeros
// 			var mm = String(dateObject.getMonth() + 1).padStart(2, '0'); //January is 0 so add +1!
// 			var dayOfWeek = dateObject.toLocaleDateString('de-DE', { weekday: 'short'});
// 			date = dayOfWeek + ', ' + dd + '.' + mm + '.' + dateObject.getFullYear();
// 		}
// 		$('#time').text(time);
// 		$('#date').text(date);
// 	}
// }

// function processVerbraucherMessages(mqttTopic, mqttPayload) {
// 	// processes mqttTopic for topic openWB/Verbraucher
// 	// called by handleMessage
// 	var index = getIndex(mqttTopic);  // extract number between two / /
// 	if ( mqttTopic.match( /^openwb\/Verbraucher\/[1-2]\/Configured$/i ) ) {
// 		if ( mqttPayload == 1 ) {
// 			// if at least one device is configured, show info-div
// 			$('#verbraucher').removeClass("hide");
// 			// now show info-div for this device
// 			$('#verbraucher'+index).removeClass("hide");
// 		} else {
// 			$('#verbraucher'+index).addClass("hide");
// 		}
// 	} else if ( mqttTopic.match( /^openwb\/Verbraucher\/[1-2]\/Name$/i ) ) {
// 		if ( mqttPayload != "Name" ){
// 			$('#verbraucher'+index+'name').text(mqttPayload);
// 		}
// 	} else if ( mqttTopic.match( /^openwb\/Verbraucher\/[1-2]\/Watt$/i ) ) {
// 		var unit = ' W';
// 		var verbraucherwatt = parseInt(mqttPayload, 10);
// 		if ( isNaN(verbraucherwatt) ) {
// 			verbraucherwatt = 0;
// 		}
// 		if ( verbraucherwatt > 999 ) {
// 			verbraucherwatt = (verbraucherwatt / 1000).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
// 			unit = ' kW';
// 		}
// 		$('#verbraucher'+index+'leistung').text(verbraucherwatt + unit);
// 	} else if ( mqttTopic.match( /^openwb\/Verbraucher\/[1-2]\/DailyYieldImportkWh$/i ) ) {
// 		var verbraucherDailyYield = parseFloat(mqttPayload);
// 		if ( isNaN(verbraucherDailyYield) ) {
// 			verbraucherDailyYield = 0;
// 		}
// 		if ( verbraucherDailyYield >= 0 ) {
// 			var verbraucherDailyYieldStr = ' (' + verbraucherDailyYield.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' kWh)';
// 			$('#verbraucher'+index+'dailyyield').text(verbraucherDailyYieldStr);
// 		} else {
// 			$('#verbraucher'+index+'dailyyield').text("");
// 		}

// 	}
// }

// function processHookMessages(mqttTopic, mqttPayload) {
// 	// processes mqttTopic for topic openWB/hook
// 	// called by handleMessage
// 	if ( mqttTopic.match( /^openwb\/hook\/[1-9][0-9]*\/boolhookstatus$/i ) ) {
// 		var index = getIndex(mqttTopic);  // extract number between two / /
// 		if ( mqttPayload == 1 ) {
// 			$('#hook' + index).removeClass("bg-danger").addClass("bg-success");
// 		} else {
// 			$('#hook' + index).removeClass("bg-success").addClass("bg-danger");
// 		}
// 	}
// 	else if ( mqttTopic.match( /^openwb\/hook\/[1-9][0-9]*\/boolhookconfigured$/i ) ) {
// 		var index = getIndex(mqttTopic);  // extract number between two / /
// 		if ( mqttPayload == 1 ) {
// 			$('#hook' + index).removeClass('hide');
// 		} else {
// 			$('#hook' + index).addClass('hide');
// 		}
// 	}
// }
// function processSmartHomeDevicesMessages(mqttTopic, mqttPayload) {
// 	// processes mqttTopic for topic openWB/SmartHomeDevices - actual values only!
// 	// called by handleMessage
// 	processPreloader(mqttTopic);
// 	if ( mqttTopic.match( /^openwb\/SmartHome\/Devices\/[1-9][0-9]*\/Watt$/i ) ) {
// 		var index = getIndex(mqttTopic);  // extract number between two / /
// 		var parent = $('[data-dev="' + index + '"]');  // get parent row element for SH Device
// 		var element = parent.find('.actualPowerDevice');  // now get parents respective child element
// 		var actualPower = parseInt(mqttPayload, 10);
// 		if ( isNaN(actualPower) ) {
// 			actualPower = 0;
// 		}
// 		if (actualPower > 999) {
// 			actualPower = (actualPower / 1000).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
// 			actualPower += ' kW';
// 		} else {
// 			actualPower += ' W';
// 		}
// 		element.text(actualPower);
// 	}
// 	else if ( mqttTopic.match( /^openwb\/SmartHome\/Devices\/[1-9][0-9]*\/DailyYieldKwh$/i ) ) {
// 		var index = getIndex(mqttTopic);  // extract number between two / /
// 		var parent = $('[data-dev="' + index + '"]');  // get parent row element for SH Device
// 		var element = parent.find('.actualDailyYieldDevice');  // now get parents respective child element
// 		var actualDailyYield = parseFloat(mqttPayload);
// 		if ( isNaN(actualDailyYield) ) {
// 			siiDailyYield = 0;
// 		}
// 		if ( actualDailyYield >= 0 ) {
// 			var actualDailyYieldStr = ' (' + actualDailyYield.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' kWh)';
// 			element.text(actualDailyYieldStr);
// 		} else {
// 			element.text("");
// 		}
// 	}
// 	else if ( mqttTopic.match( /^openwb\/SmartHome\/Devices\/[1-9][0-9]*\/RunningTimeToday$/i ) ) {
// 		var index = getIndex(mqttTopic);  // extract number between two / /
// 		var parent = $('[data-dev="' + index + '"]');  // get parent row element for SH Device
// 		var element = parent.find('.actualRunningTimeDevice');  // now get parents respective child element
// 		var actualPower = parseInt(mqttPayload, 10);
// 		if ( isNaN(actualPower) ) {
// 			actualPower = 0;
// 		}
// 		if (actualPower < 3600) {
// 			actualPower = (actualPower / 60).toFixed(0);
// 			actualPower += ' Min';
// 		} else {
// 			rest = (actualPower % 3600 / 60).toFixed(0);
// 			ganz = Math.floor(actualPower / 3600);
// 			actualPower = ganz + ' H ' + rest +' Min';
// 		}
// 		element.text(actualPower);
// 	}
// 	else if ( mqttTopic.match( /^openwb\/SmartHome\/Devices\/[1-9][0-9]*\/RelayStatus$/i ) ) {
// 		var index = getIndex(mqttTopic);  // extract number between two / /
// 		$('.nameDevice').each(function() {  // check all elements of class '.nameLp'
// 			var dev = $(this).closest('[data-dev]').data('dev');  // get attribute lp from parent
// 			if ( dev == index ) {
// 				if ( $(this).hasClass('enableDevice') ) {
// 					// but only apply styles to element in charge point info data block
// 					if ( mqttPayload == 0 ) {
// 						$(this).removeClass('lpEnabledStyle').removeClass('lpWaitingStyle').addClass('lpDisabledStyle');
// 					} else {
// 						$(this).removeClass('lpDisabledStyle').removeClass('lpWaitingStyle').addClass('lpEnabledStyle');
// 					}
// 				}
// 			}
// 		});
// 	}
// 	else if ( mqttTopic.match( /^openwb\/SmartHome\/Devices\/[1-9][0-9]*\/TemperatureSensor0$/i ) ) {
// 		var index = getIndex(mqttTopic);  // extract number between two / /
// 		var parent = $('.SmartHomeTemp[data-dev="' + index + '"]');  // get parent row element for SH Device
// 		var element = parent.find('.actualTemp0Device');  // now get parents respective child element
// 		var actualTemp = parseFloat(mqttPayload);
// 		if ( isNaN(actualTemp) ) {
// 			StringTemp = '';
// 			parent.addClass('hide');
// 		} else {
// 			if (actualTemp > 200) {
// 				StringTemp = ''; // display only something if we got a value
// 				parent.addClass('hide');
// 			} else {
// 				StringTemp = 'Temp1 ' + actualTemp.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}); // make complete string to display
// 				parent.removeClass('hide');
// 			}
// 		}
// 		element.text(StringTemp);
// 	}
// 	else if ( mqttTopic.match( /^openwb\/SmartHome\/Devices\/[1-9][0-9]*\/TemperatureSensor1$/i ) ) {
// 		var index = getIndex(mqttTopic);  // extract number between two / /
// 		var parent = $('.SmartHomeTemp[data-dev="' + index + '"]');  // get parent row element for charge point
// 		var element = parent.find('.actualTemp1Device');  // now get parents respective child element
// 		var actualTemp = parseFloat(mqttPayload);
// 		if ( isNaN(actualTemp) ) {
// 			StringTemp = '';
// 		} else {
// 			if (actualTemp > 200) {
// 				StringTemp = ''; // display only something if we got a value
// 			} else {
// 				StringTemp = 'Temp2 ' + actualTemp.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}); // make complete string to display
// 			}
// 		}
// 		element.text(StringTemp);
// 	}
// 	else if ( mqttTopic.match( /^openwb\/SmartHome\/Devices\/[1-9][0-9]*\/TemperatureSensor2$/i ) ) {
// 		var index = getIndex(mqttTopic);  // extract number between two / /
// 		var parent = $('.SmartHomeTemp[data-dev="' + index + '"]');  // get parent row element for charge point
// 		var element = parent.find('.actualTemp2Device');  // now get parents respective child element
// 		var actualTemp = parseFloat(mqttPayload);
// 		if ( isNaN(actualTemp) ) {
// 			StringTemp = '';
// 		} else {
// 			if (actualTemp > 200) {
// 				StringTemp = ''; // display only something if we got a value
// 			} else {
// 				StringTemp = 'Temp3 ' + actualTemp.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}); // make complete string to display
// 			}
// 		}
// 		element.text(StringTemp);
// 	}
// }

function processSmartHomeDevicesConfigMessages(mqttTopic, mqttPayload) {
	// processes mqttTopic for topic openWB/config/get/SmartHome/Devices - config variables (Name / configured only!), actual Variables in proccessSMartHomeDevices
	// called by handleMessage
	processPreloader(mqttTopic);
	if (mqttTopic.match(/^openwb\/config\/get\/SmartHome\/Devices\/[1-9][0-9]*\/device_configured$/i)) {
		// respective SH Device configured
		var index = getIndex(mqttTopic);  // extract number between two / /
		var infoElement = $('[data-dev="' + index + '"]');  // get row of SH Device
		if (mqttPayload == 1) {
			infoElement.removeClass('hide');
		} else {
			infoElement.addClass('hide');
		}
		var visibleRows = $('.smartHome [data-dev]').not('.hide');  // show/hide complete block depending on visible rows within
		if (visibleRows.length > 0) {
			$('.smartHome').removeClass('hide');
		} else {
			$('.smartHome').addClass('hide');
		}
	}
	else if (mqttTopic.match(/^openwb\/config\/get\/SmartHome\/Devices\/[1-9][0-9]*\/mode$/i)) {
		var index = getIndex(mqttTopic);  // extract number between two / /
		var parent = $('[data-dev="' + index + '"]');  // get parent row element for SH Device
		var element = parent.find('.actualModeDevice');  // now get parents respective child element
		if (mqttPayload == 0) {
			actualMode = "Automatik"
		} else {
			actualMode = "Manuell"
		}
		element.text(actualMode);
		$('.nameDevice').each(function () {  // check all elements of class '.nameDevice'
			var dev = $(this).closest('[data-dev]').data('dev');  // get attribute Device from parent
			if (dev == index) {
				if ($(this).hasClass('enableDevice')) {
					// but only apply styles to element in charge point info data block
					if (mqttPayload == 1) {
						$(this).addClass('cursor-pointer').addClass('locked');
					} else {
						$(this).removeClass('cursor-pointer').removeClass('locked');
					}
				}
			}
		});
	}
	else if (mqttTopic.match(/^openWB\/config\/get\/SmartHome\/Devices\/[1-9][0-9]*\/device_name$/i)) {
		var index = getIndex(mqttTopic);  // extract number between two / /
		var parent = $('[data-dev="' + index + '"]');  // get parent row element for SH Device
		var element = parent.find('.nameDevice');  // now get parents respective child element
		element.text(mqttPayload);
		window['d' + index + 'name'] = mqttPayload;
	}
}

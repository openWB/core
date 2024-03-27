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
var timeChargePlan = {};
var vehicleSoc = {};
var evuCounterIndex = undefined;
var chartLabels = {
	// define some default labels, they will be extended for components and vehicles
	"grid": "EVU",
	"house-power": "Hausverbr.",
	"charging-all": "LP ges.",
	"pv-all": "PV ges.",
	"bat-all-power": "Speicher ges.",
	"bat-all-soc": "Speicher ges. SoC",
};

function getIndex(topic, position = 0) {
	// get occurrence of numbers between / / in topic
	// since this is supposed to be the index like in openwb/lp/4/w
	// no lookbehind supported by safari, so workaround with replace needed
	// there may be multiple occurrences of numbers in the topic, so we need to specify the position
	var index = topic.match(/(?:\/)([0-9]+)(?=\/)/g)[position].replace(/[^0-9]+/g, '');
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
				// console.debug("creating charge-point " + chargePointIndex);
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
				clonedElement.find('#timeChargeCpT').attr('id', 'timeChargeCp' + chargePointIndex);
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
		console.debug("refreshing charge template", templateIndex);
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
				setInputValue(element.attr('id'), chargeModeTemplate[templateIndex].time_charging.active ? 1 : 0);
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
				// et.active
				headerElement = parent.find('.charge-point-vehicle-et-active')
				toggleElement = parent.find('.charge-point-price-charging-active')
				if (chargeModeTemplate[templateIndex].et.active) {
					headerElement.removeClass("hide");
					toggleElement.bootstrapToggle('on', true);
				} else {
					headerElement.addClass("hide");
					toggleElement.bootstrapToggle('off', true);
				}
				// et.max_price
				element = parent.find('.charge-point-max-price-button');
				var max_price = parseFloat((chargeModeTemplate[templateIndex].et.max_price * 100000).toFixed(2));
				element.data('max-price', max_price);
				element.attr('data-max-price', max_price).data('max-price', max_price);
				element.find('.charge-point-price-charging-max_price').text(max_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }));

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
						// console.debug("schedule", key, value);
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
								schedulePlanElement.find('.charge-point-schedule-limit').text(value.limit.soc_scheduled + "%");
								schedulePlanElement.find('.charge-point-schedule-limit-icon').removeClass('fa-bolt');
								schedulePlanElement.find('.charge-point-schedule-limit-icon').addClass('fa-car-battery');
							} else {
								schedulePlanElement.find('.charge-point-schedule-limit').text((value.limit.amount / 1000) + "kWh");
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

				// time charging schedules
				// time_charging.X
				// first remove all schedule plans except the template
				parent.find('.charge-point-time-charge-plan[data-plan]').not('.charge-point-time-charge-plan-template').remove();
				var sourceElement = parent.find('.charge-point-time-charge-plan-template');
				// remove checkbox toggle button style as they will not function after cloning
				sourceElement.find('input[type=checkbox][data-toggle^=toggle]').bootstrapToggle('destroy');
				// now create any other schedule plan
				if (templateIndex in timeChargePlan) {
					// console.log("time charge plan found", templateIndex, timeChargePlan[templateIndex]);
					parent.find(".charge-point-time-charge-plan-missing").addClass("hide");
					for (const [key, value] of Object.entries(timeChargePlan[templateIndex])) {
						// console.debug("schedule", key, value);
						if (parent.find('.charge-point-time-charge-plan[data-plan=' + key + ']').length == 0) {
							// console.log('creating time charge plan with id "'+key+'"');
							var clonedElement = sourceElement.clone();
							// update all data referencing the old index in our clone
							clonedElement.attr('data-plan', key).data('plan', key);
							// insert after last existing plan to honor sorting from the array
							target = parent.find('.charge-point-time-charge-plan').last();
							// console.log("target: "+target.data('plan')+" index: "+key);
							// console.log(target);
							// insert clone into DOM
							clonedElement.insertAfter($(target));
							// now get our created element and add checkbox toggle buttons
							timeChargePlanElement = parent.find('.charge-point-time-charge-plan[data-plan=' + key + ']');
							timeChargePlanElement.find('input[type=checkbox][data-toggle^=toggle]').bootstrapToggle();
							// set values from payload
							timeChargePlanElement.find('.charge-point-time-charge-name').text(value.name);
							timeChargePlanElement.find('.charge-point-time-charge-time').text(value.time[0] + " - " + value.time[1]);
							if (value.active == true) {
								timeChargePlanElement.find('.charge-point-time-charge-active').removeClass('alert-danger border-danger');
								timeChargePlanElement.find('.charge-point-time-charge-active').addClass('alert-success border-success');
							} else {
								timeChargePlanElement.find('.charge-point-time-charge-active').removeClass('alert-success border-success');
								timeChargePlanElement.find('.charge-point-time-charge-active').addClass('alert-danger border-danger');
							}
							switch (value.frequency.selected) {
								case "once":
									timeChargePlanElement.find('.charge-point-time-charge-frequency').addClass('hide');
									timeChargePlanElement.find('.charge-point-time-charge-date').removeClass('hide');
									const begin = new Date(value.frequency.once[0]);
									const begin_text = begin.toLocaleDateString(undefined, { year: "numeric", month: "2-digit", day: "2-digit", weekday: "short" });
									const end = new Date(value.frequency.once[1]);
									const end_text = end.toLocaleDateString(undefined, { year: "numeric", month: "2-digit", day: "2-digit", weekday: "short" });
									timeChargePlanElement.find('.charge-point-time-charge-date-value').text(begin_text + " - " + end_text);
									break;
								case "daily":
									timeChargePlanElement.find('.charge-point-time-charge-frequency').removeClass('hide');
									timeChargePlanElement.find('.charge-point-time-charge-date').addClass('hide');
									timeChargePlanElement.find('.charge-point-time-charge-frequency-value').text('täglich');
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
									timeChargePlanElement.find('.charge-point-time-charge-frequency').removeClass('hide');
									timeChargePlanElement.find('.charge-point-time-charge-date').addClass('hide');
									timeChargePlanElement.find('.charge-point-time-charge-frequency-value').text(daysText);
									break;
								default:
									console.error("unknown schedule frequency: " + value.frequency.selected);
							}
							// finally show our new charge point
							clonedElement.removeClass('charge-point-time-charge-plan-template').removeClass('hide');
						} else {
							console.error('time charge plan ' + key + ' already exists');
						}
					}
				} else {
					// console.log("no time charge plan defined", templateIndex);
					parent.find(".charge-point-time-charge-plan-missing").removeClass("hide");
				}
			}
		} else {
			console.debug('no charge points with charge template "' + templateIndex + '" found');
		}
	}
}

function refreshVehicleSoc(vehicleIndex) {
	if (vehicleSoc.hasOwnProperty(vehicleIndex)) {
		$('.charge-point-vehicle-data[data-ev="' + vehicleIndex + '"]').each(function () {
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
	processPreloader(mqttTopic);
	if (mqttTopic.match(/^openwb\/counter\/[0-9]+\//i)) { processCounterMessages(mqttTopic, mqttPayload) }
	else if (mqttTopic.match(/^openwb\/counter\//i)) { processGlobalCounterMessages(mqttTopic, mqttPayload); }
	else if (mqttTopic.match(/^openwb\/system\/device\/[0-9]+\/component\/[0-9]+\//i)) { processComponentMessages(mqttTopic, mqttPayload); }
	else if (mqttTopic.match(/^openwb\/bat\//i)) { processBatteryMessages(mqttTopic, mqttPayload); }
	else if (mqttTopic.match(/^openwb\/pv\//i)) { processPvMessages(mqttTopic, mqttPayload); }
	else if (mqttTopic.match(/^openwb\/chargepoint\//i)) { processChargePointMessages(mqttTopic, mqttPayload); }
	else if (mqttTopic.match(/^openwb\/vehicle\//i)) { processVehicleMessages(mqttTopic, mqttPayload); }
	else if (mqttTopic.match(/^openwb\/general\/chargemode_config\/pv_charging\//i)) { processPvConfigMessages(mqttTopic, mqttPayload); }
	else if (mqttTopic.match(/^openwb\/graph\//i)) { processGraphMessages(mqttTopic, mqttPayload); }
	else if (mqttTopic.match(/^openwb\/optional\/et\//i)) { processETProviderMessages(mqttTopic, mqttPayload); }
	else if (mqttTopic.match(/^openwb\/LegacySmartHome\//i)) { processSmartHomeDeviceMessages(mqttTopic, mqttPayload); }
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
			// console.debug("EVU counter index: " + evuCounterIndex);
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
		processEvuMessages(mqttTopic, mqttPayload);
	} else {
		/* nothing here yet */
	}
}

function processComponentMessages(mqttTopic, mqttPayload) {
	// let deviceIndex = getIndex(mqttTopic, 0);  // first number in topic
	// let componentIndex = getIndex(mqttTopic, 1);  // second number in topic
	if (mqttTopic.match(/^openWB\/system\/device\/[0-9]+\/component\/[0-9]+\/config$/i)) {
		// JSON data
		// name: str
		// type: str
		// id: int
		// configuration: JSON
		var configMessage = JSON.parse(mqttPayload);
		// chart label
		if (configMessage.type.includes("counter")) {
			let key = `counter${configMessage.id}-power`;
			if (configMessage.id == evuCounterIndex) {
				key = "grid";
			}
			chartLabels[key] = configMessage.name;
		}
	}
}

function processBatteryMessages(mqttTopic, mqttPayload) {
	// processes mqttTopic for topic openWB/bat
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
		if (pvWatt > 0) {
			$('.pv-sum-power-production').addClass('hide');
			$('.pv-sum-power-consumption').removeClass('hide');
		} else {
			$('.pv-sum-power-consumption').addClass('hide');
			$('.pv-sum-power-production').removeClass('hide');
		}
		if (isNaN(pvWatt)) {
			pvWatt = 0;
		}
		// production should be displayed positive, consumption negative
		pvWatt *= -1;
		// adjust and add unit
		if (Math.abs(pvWatt) > 999) {
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
		if (Math.abs(powerAllLp) > 999) {
			powerAllLp = (powerAllLp / 1000).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
			unitPrefix = 'k';
		} else {
			powerAllLp = powerAllLp.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
		}
		$('.charge-point-sum-power').text(powerAllLp + ' ' + unitPrefix + unit);
		if (powerAllLp < 0) {
			$('.charge-point-sum-power-charging').addClass('hide');
			$('.charge-point-sum-power-discharging').removeClass('hide');
		} else {
			$('.charge-point-sum-power-discharging').addClass('hide');
			$('.charge-point-sum-power-charging').removeClass('hide');
		}
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
		// chart label
		chartLabels[`cp${index}-power`] = configMessage.name;
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
	} else if (mqttTopic.match(/^openWB\/chargepoint\/[0-9]+\/set\/log$/i)) {
		// energy charged since ev was plugged in
		// also calculates and displays km charged
		// console.log("charged since plugged counter");
		var index = getIndex(mqttTopic); // extract number between two / /
		var parent = $('.charge-point-card[data-cp="' + index + '"]'); // get parent row element for charge point
		var element = parent.find('.charge-point-energy-since-mode-switch'); // now get parents respective child element
		var logData = JSON.parse(mqttPayload);
		var energyCharged = parseFloat(logData.imported_since_mode_switch) / 1000;
		if (isNaN(energyCharged)) {
			energyCharged = 0;
		}
		element.text(energyCharged.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + ' kWh');
		var rangeChargedElement = parent.find('.charge-point-range-since-mode-switch'); // now get parents child element
		var rangeCharged = parseFloat(logData.range_charged);
		rangeCharged = ' / ' + rangeCharged.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + ' km';
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
		let timeString = new Date(socData.timestamp * 1000).toLocaleString();
		element.attr('title', Math.round(socData.range) + socData.range_unit + " (" + timeString + ")");
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
		if (parent.attr('data-charge-template') != configData.charge_template) {
			parent.attr('data-charge-template', configData.charge_template).data('charge-template', configData.charge_template);
			refreshChargeTemplate(configData.charge_template);
		}
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
	}
}

function processVehicleMessages(mqttTopic, mqttPayload) {
	if (mqttTopic.match(/^openwb\/vehicle\/[0-9]+\/name$/i)) {
		// this topic is used to populate the charge point list
		var index = getIndex(mqttTopic); // extract number between two / /
		var vehicleName = JSON.parse(mqttPayload)
		$('.charge-point-vehicle-select').each(function () {
			myOption = $(this).find('option[value=' + index + ']');
			if (myOption.length > 0) {
				myOption.text(vehicleName); // update vehicle name if option with index is present
			} else {
				$(this).append(`<option value="${index}">${vehicleName}</option>`); // add option with index
				if (parseInt($(this).closest('.charge-point-vehicle-data[data-ev]').data('ev')) == index) { // update selected element if match with our index
					$(this).val(index);
				}
			}
		});
		// chart label
		chartLabels[`ev${index}-soc`] = vehicleName;
	} else if (mqttTopic.match(/^openwb\/vehicle\/[0-9]+\/soc_module\/config$/i)) {
		// { "type": "<selected module>", "configuration": { <module specific data> } }
		// we use the data "type" to detect, if a soc module is configure (type != None) or manual soc is selected (type == manual)
		var vehicleIndex = getIndex(mqttTopic); // extract number between two / /
		var configData = JSON.parse(mqttPayload);
		vehicleSoc[vehicleIndex] = configData;
		// console.debug("update vehicle soc config", vehicleIndex, configData);
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
			if (!(templateIndex in schedulePlan)) {
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
	} else if (mqttTopic.match(/^openwb\/vehicle\/template\/charge_template\/[0-9]+\/time_charging\/plans\/[0-9]+$/i)) {
		templateIndex = mqttTopic.match(/[0-9]+/i)[0];
		planIndex = mqttTopic.match(/[0-9]+$/i)[0];
		try {
			// console.log("received time charge plan", templateIndex, planIndex, mqttPayload);
			const newPlan = JSON.parse(mqttPayload);
			if (!(templateIndex in timeChargePlan)) {
				timeChargePlan[templateIndex] = {};
			}
			timeChargePlan[templateIndex][planIndex] = newPlan;
		} catch (error) {
			console.error("error parsing time charge plan!");
			delete timeChargePlan[templateIndex][planIndex];
			if (Object.keys(timeChargePlan[templateIndex]).length == 0) {
				delete timeChargePlan[templateIndex];
			}
		}
		refreshChargeTemplate(templateIndex);
	}
}

function processGraphMessages(mqttTopic, mqttPayload) {
	// processes mqttTopic for topic openWB/graph
	// called by handleMessage
	if (mqttTopic.match(/^openwb\/graph\/alllivevaluesJson[1-9][0-9]*$/i)) {
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
			graphRefreshCounter = 0;
			subscribeMqttGraphSegments();
		}
		graphRefreshCounter += 1;
	} else if (mqttTopic == 'openWB/graph/config/duration') {
		// console.debug("graph duration: " + mqttPayload + " minutes");
		var duration = JSON.parse(mqttPayload);
		if (isNaN(duration) || duration < 10 || duration > 120) {
			console.error("bad graph duration received: " + mqttPayload + " setting to default of 30 minutes");
			duration = 30;
		}
		maxDisplayLength = duration * 60 * 1000;  // convert minutes to milliseconds
	}
} // end processGraphMessages

function processETProviderMessages(mqttTopic, mqttPayload) {
	// processes mqttTopic for topic openWB/optional/et
	if (mqttTopic == 'openWB/optional/et/provider') {
		data = JSON.parse(mqttPayload);
		if (data.type) {
			$('.et-name').text(data.name);
			$('.et-configured').removeClass('hide');
		} else {
			$('.et-configured').addClass('hide');
		}
	} else if (mqttTopic == 'openWB/optional/et/get/prices') {
		electricityPriceList = JSON.parse(mqttPayload);
		var currentPrice = electricityPriceList[Object.keys(electricityPriceList)[0]] * 100000;
		$('.et-current-price').text(currentPrice.toLocaleString(undefined, { maximumFractionDigits: 2, minimumFractionDigits: 2 }) + ' ct/kWh');
	}
}

function processSmartHomeDeviceMessages(mqttTopic, mqttPayload) {
	processPreloader(mqttTopic);
	var deviceIndex = getIndex(mqttTopic);  // extract number between two / /
	var deviceElement = $('.smarthome-device-card[data-smart-home-device="' + deviceIndex + '"]');  // get device card
	if (mqttTopic.match(/^openWB\/LegacySmartHome\/config\/get\/Devices\/[1-9][0-9]*\/device_configured$/i)) {
		if (mqttPayload == 1) {
			deviceElement.removeClass('hide');
		} else {
			deviceElement.addClass('hide');
		}
	}
	else if (mqttTopic.match(/^openWB\/LegacySmartHome\/config\/get\/Devices\/[1-9][0-9]*\/device_name$/i)) {
		// device name
		var element = deviceElement.find('.nameDevice');  // now get parents child element
		element.text(mqttPayload);
		// window['d'+index+'name']=mqttPayload; // store name for chart
	}
	else if (mqttTopic.match(/^openWB\/LegacySmartHome\/config\/set\/Devices\/[1-9][0-9]*\/mode$/i)) {
		// device mode
		var modeElement = deviceElement.find('.actualModeDevice');  // now get parents respective child element
		var actualMode = "";
		if (mqttPayload == 0) {
			actualMode = "Automatik"
		} else if (mqttPayload == 1) {
			actualMode = "Manuell"
		} else {
			console.warn("unknown mode", mqttPayload);
		}
		modeElement.text(actualMode);
		var nameElement = deviceElement.find('.nameDevice');
		if (mqttPayload == 1) {
			nameElement.addClass('cursor-pointer').addClass('locked');
		} else {
			nameElement.removeClass('cursor-pointer').removeClass('locked');
		}
	}
	else if (mqttTopic.match(/^openWB\/LegacySmartHome\/Devices\/[1-9][0-9]*\/Watt$/i)) {
		// device power
		var element = deviceElement.find('.actualPowerDevice');  // now get parents child element
		var actualPower = parseInt(mqttPayload, 10);
		if (isNaN(actualPower)) {
			actualPower = 0;
		}
		if (actualPower > 999) {
			actualPower = (actualPower / 1000).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
			actualPower += '&nbsp;kW';
		} else {
			actualPower += '&nbsp;W';
		}
		element.html(actualPower);
	}
	else if (mqttTopic.match(/^openWB\/LegacySmartHome\/Devices\/[1-9][0-9]*\/RunningTimeToday$/i)) {
		// device running time
		var element = deviceElement.find('.actualRunningTimeDevice');  // now get parents child element
		var runningTime = parseInt(mqttPayload, 10);
		if (isNaN(runningTime)) {
			runningTime = 0;
		}
		var seconds = runningTime % 60;
		var minutes = ((runningTime - seconds) % 3600) / 60;
		var hours = (runningTime - seconds - minutes * 60) / 3600;
		var runningTimeText = seconds + "s";
		if (runningTime >= 60) {
			runningTimeText = minutes + "m&nbsp;" + runningTimeText;
		}
		if (runningTime >= 3600) {
			runningTimeText = hours + "h&nbsp;" + runningTimeText;
		}
		element.html(runningTimeText);
	}
	else if (mqttTopic.match(/^openWB\/LegacySmartHome\/Devices\/[1-9][0-9]*\/Status$/i)) {
		// device state
		var element = deviceElement.find('.nameDevice');  // now get parents child element
		if (mqttPayload == 10) {
			// 10 device on (manual or automatic)
			element.removeClass('charge-point-enabled').removeClass('text-blue').removeClass('text-white').removeClass('charge-point-waiting').addClass('charge-point-disabled');
		} else if (mqttPayload == 11) {
			// 11 device off (manual or automatic)
			element.removeClass('charge-point-disabled').removeClass('text-blue').removeClass('text-white').removeClass('charge-point-waiting').addClass('charge-point-enabled');
		} else if (mqttPayload == 20) {
			// 20 startup detection active
			element.removeClass('charge-point-disabled').removeClass('charge-point-enabled').removeClass('text-white').removeClass('charge-point-waiting').addClass('text-blue');
		} else if (mqttPayload == 30) {
			// 30 finish time running
			element.removeClass('charge-point-disabled').removeClass('charge-point-enabled').removeClass('text-blue').removeClass('charge-point-waiting').addClass('text-white');
		} else {
			console.warn("unknown state message", mqttTopic, mqttPayload);
		}
	}
	else if (mqttTopic.match(/^openWB\/LegacySmartHome\/Devices\/[1-9][0-9]*\/DailyYieldKwh$/i)) {
		// device daily yield
		var element = deviceElement.find('.actualDailyYieldDevice');  // now get parents respective child element
		var actualDailyYield = parseFloat(mqttPayload);
		if (isNaN(actualDailyYield)) {
			actualDailyYield = 0;
		}
		if (actualDailyYield >= 0) {
			var actualDailyYieldStr = '&nbsp;(' + actualDailyYield.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + '&nbsp;kWh)';
			element.html(actualDailyYieldStr);
		} else {
			element.text("");
		}
	}
	else if (mqttTopic.match(/^openWB\/LegacySmartHome\/Devices\/[1-9][0-9]*\/TemperatureSensor[0-2]$/i)) {
		// device temperature sensor
		var sensorIndex = mqttTopic.match(/(?:\/TemperatureSensor)([0-2]+)$/g)[0].replace(/[^0-9]+/g, '');
		var deviceTemperatureElement = deviceElement.find('.SmartHomeTemp');
		var sensorElement = deviceTemperatureElement.find('[data-smart-home-temperature="' + sensorIndex + '"]');
		var sensorValueElement = sensorElement.find('.temperature');
		var actualTemp = parseFloat(mqttPayload);
		if (isNaN(actualTemp)) {
			actualTemp = 999;
		}
		if (actualTemp > 200) {
			sensorValueElement.text(''); // display only something if we got a value
			sensorElement.addClass('hide');
		} else {
			sensorValueElement.text('Temp' + sensorIndex + ' ' + actualTemp.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
			sensorElement.removeClass('hide');
		}
		var visibleRows = deviceTemperatureElement.find('[data-smart-home-temperature]').not('.hide');  // show/hide complete block depending on visible rows within
		if (visibleRows.length > 0) {
			deviceTemperatureElement.removeClass('hide');
		} else {
			deviceTemperatureElement.addClass('hide');
		}
	}
}

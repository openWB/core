/**
 * helper functions
 *
 * @author Michael Ortenstein
 * @author Lutz Bender
 */

function updateLabel(elementId) {
	/** @function updateLabel
	 * sets the value-label (if exists) attached to the element to the element value
	 * @param {string} elementId - the id of the element
	 * @requires class:valueLabel assigned to the attached label
	 */
	var element = $('#' + $.escapeSelector(elementId));
	var label = $('label[for="' + elementId + '"].valueLabel');
	if (label.length == 1) {
		var suffix = label.attr('data-suffix');
		var value = parseFloat(element.val());
		var text;
		if (list = $(element).attr('data-list')) {
			jsonList = JSON.parse(list);
			if (Array.isArray(jsonList[value])) {
				text = jsonList[value][1];
			} else {
				text = jsonList[value].toLocaleString(undefined, { maximumFractionDigits: 2 });
				if (suffix != '') {
					text += ' ' + suffix;
				}
			}
		} else {
			text = value.toLocaleString(undefined, { maximumFractionDigits: 2 });
			if (suffix != '') {
				text += ' ' + suffix;
			}
		}
		label.text(text);
	}
}

function transformRangeValue(formula) {
	return new Function('return ' + formula)();
}

function setInputValue(elementId, value) {
	/** @function setInputValue
	 * sets the value-label (if exists) attached to the element to the element value
	 * @param {string} elementId - the id of the element
	 * @param {string} value - the value the element has to be set to
	 * if the element has data-attribute 'signCheckbox' the checkbox with the id of the attribute
	 * will represent negative numbers by being checked
	 * if the element has data-attribute 'list' the value will be selected from the list
	 * if the element hat data-attribute 'transformation' the value will be calculated by the given formula
	 */
	// console.debug("input elementID", elementId);
	if (!isNaN(value)) {
		var element = $('#' + $.escapeSelector(elementId));
		if (list = $(element).attr('data-list')) {
			jsonList = JSON.parse(list);
			value = jsonList.findIndex(item => {
				if (Array.isArray(item)) {
					return item[0] == value;
				} else {
					return item == value;
				}
			});
		} else if (formula = $(element).attr('data-transformation')) {
			// console.log(formula);
			formula = JSON.parse(formula);
			// console.log(formula);
			formula = formula.in.replace('<v>', value);
			// console.log(formula);
			value = transformRangeValue(formula);
		}
		var signCheckboxName = element.data('signCheckbox');
		var signCheckbox = $('#' + signCheckboxName);
		if (signCheckbox.length == 1) {
			// checkbox exists
			if (value < 0) {
				signCheckbox.prop('checked', true);
				value *= -1;
			} else {
				signCheckbox.prop('checked', false);
			}
		}
		element.val(value);
		if (element.attr('type') == 'range') {
			updateLabel(elementId);
		}
		if (element.hasClass('charge-point-time-charging-active')) {
			timeChargeOptionsShowHide(element, value == 1);
		}
	} else {
		console.error("invalid value for input element", elementId, value);
	}
}

function getTopic(element) {
	var topic = element.data('topic');
	if (topic === undefined) {
		return undefined;
	}
	var cp = parseInt(element.closest('[data-cp]').data('cp'));  // get attribute cp-# of parent element
	var ev = parseInt(element.closest('[data-ev]').data('ev'));  // get attribute ev-# of parent element
	var ct = parseInt(element.closest('[data-charge-template]').data('charge-template'));  // get attribute charge-template-# of parent element
	var cpt = parseInt(element.closest('[data-charge-point-template]').data('charge-point-template'));  // get attribute charge-point-template-# of parent element
	var et = parseInt(element.closest('[data-ev-template]').data('ev-template'));  // get attribute ev-template-# of parent element
	var schedule = parseInt(element.closest('[data-plan]').data('plan'));  // get attribute plan-# of parent element
	topic = topic.replace('<cp>', cp);
	topic = topic.replace('<ev>', ev);
	topic = topic.replace('<ct>', ct);
	topic = topic.replace('<cpt>', cpt);
	topic = topic.replace('<et>', et);
	topic = topic.replace('<sched>', schedule);
	if (topic.includes('/NaN/')) {
		console.error('missing cp, ev, ct, cpt, et or sched data');
		return undefined;
	}
	return topic;
}

function setToggleBtnGroup(groupId, option) {
	/** @function setInputValue
	 * sets the value-label (if exists) attached to the element to the element value
	 * @param {string} groupId - the id of the button group
	 * @param {string} option - the option the group buttons will be set to
	 * @requires data-attribute 'option' (unique for group) assigned to every radio-btn
	 */
	var btnGroup = $('#' + $.escapeSelector(groupId));
	// console.log(btnGroup);
	btnGroup.find('input[data-option=' + option + ']').prop('checked', true);
	btnGroup.find('input[data-option=' + option + ']').closest('label').addClass('active');
	// and uncheck all others
	btnGroup.find('input').not('[data-option=' + option + ']').each(function () {
		$(this).prop('checked', false);
		$(this).closest('label').removeClass('active');
	});
	// show/hide respective option-values and progress
	if (btnGroup.hasClass('charge-point-charge-mode')) {
		chargemodeOptionsShowHide(btnGroup, option);
	}
	if (btnGroup.hasClass('charge-point-instant-charge-limit-selected')) {
		chargemodeLimitOptionsShowHide(btnGroup, 'instant', option);
	}
	if (btnGroup.hasClass('charge-point-pv-charge-limit-selected')) {
		chargemodeLimitOptionsShowHide(btnGroup, 'pv', option);
	}
	if (btnGroup.hasClass('charge-point-eco-charge-limit-selected')) {
		chargemodeLimitOptionsShowHide(btnGroup, 'eco', option);
	}
}

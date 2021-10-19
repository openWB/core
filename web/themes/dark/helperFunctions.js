/**
 * helper functions for setup-pages
 *
 * @author Michael Ortenstein
 */

function updateLabel(elementId) {
    /** @function updateLabel
     * sets the value-label (if exists) attached to the element to the element value
     * @param {string} elementId - the id of the element
     * @requires class:valueLabel assigned to the attached label
     */
    var element = $('#' + $.escapeSelector(elementId));
    var label = $('label[for="' + elementId + '"].valueLabel');
    if ( label.length == 1 ) {
        var suffix = label.attr('data-suffix');
        var value = parseFloat(element.val());
        if(list = $(element).attr('data-list')){
            value = list.split(',')[parseInt(value)];
        }
        var text = value.toLocaleString(undefined, {maximumFractionDigits: 2});
        if ( suffix != '' ) {
            text += ' ' + suffix;
        }
        label.text(text);
    }
}

function transformRangeValue(formula){
    return new Function('return ' + formula)();
}

function setInputValue(elementId, value) {
    /** @function setInputValue
     * sets the value-label (if exists) attached to the element to the element value
     * @param {string} elementId - the id of the element
     * @param {string} value - the value the element has to be set to
     * if the element has data-attribute 'signcheckbox' the checkbox with the id of the attribute
     * will represent negative numbers by being checked
     * if the element has data-attribute 'list' the value will be selected from the list
     * if the element hat data-attribute 'transformation' the value will be calculated by the given formula
     */
    if ( !isNaN(value) ) {
        var element = $('#' + $.escapeSelector(elementId));
        if(list = $(element).attr('data-list')){
            value = parseInt(list.split(',').findIndex(item => item == value));
        } else if(formula = $(element).attr('data-transformation')){
            // console.log(formula);
            formula = JSON.parse(formula);
            // console.log(formula);
            formula = formula.in.replace('<v>', value);
            // console.log(formula);
            value = transformRangeValue(formula);
        }
        var signCheckboxName = element.data('signcheckbox');
        var signCheckbox = $('#' + signCheckboxName);
        if ( signCheckbox.length == 1 ) {
            // checkbox exists
            if ( value < 0 ) {
                signCheckbox.prop('checked', true);
                value *= -1;
            } else {
                signCheckbox.prop('checked', false);
            }
        }
        element.val(value);
        if ( element.attr('type') == 'range' ) {
            updateLabel(elementId);
        }
    }
}

function getTopicToSendTo (elementId) {
    var element = $('#' + $.escapeSelector(elementId));
    // var topic = element.data('topicprefix') + elementId;
    // topic = topic.replace('/get/', '/set/');
    // if (topic.includes('MaxPriceForCharging')) {
    //     topic = 'openWB/set/awattar/MaxPriceForCharging'
    // }
    var topic = $(element).data('topic');
    if( topic != undefined ) {
        var cp = parseInt($(element).closest('[data-cp]').data('cp'));  // get attribute cp-# of parent element
        var ev = parseInt($(element).closest('[data-ev]').data('ev'));  // get attribute ev-# of parent element
        var ct = parseInt($(element).closest('[data-chargetemplate]').data('chargetemplate'));  // get attribute chargetemplate-# of parent element
        topic = topic.replace( '<cp>', cp );
        topic = topic.replace( '<ev>', ev );
        topic = topic.replace( '<ct>', ct );
        if( topic.includes('/NaN/') ) {
            console.error( 'missing cp, ev or ct data' );
            topic = undefined;
        }
    } else {
        console.warn("element without topic changed!");
    }
    return topic;
}

function setToggleBtnGroup(groupId, option) {
    /** @function setInputValue
     * sets the value-label (if exists) attached to the element to the element value
     * @param {string} groupId - the id of the button group
     * @param {string} option - the option the group btns will be set to
     * @requires data-attribute 'option' (unique for group) assigned to every radio-btn
     */
    var btnGroup = $('#' + $.escapeSelector(groupId));
    // console.log(btnGroup);
    btnGroup.find('input[data-option=' + option + ']').prop('checked', true);
    btnGroup.find('input[data-option=' + option + ']').closest('label').addClass('active');
    // and uncheck all others
    btnGroup.find('input').not('[data-option=' + option + ']').each(function() {
        $(this).prop('checked', false);
        $(this).closest('label').removeClass('active');
    });
    // show/hide respective option-values and progress
    if (btnGroup.hasClass('chargepoint-chargemode')){
        chargemodeOptionsShowHide(btnGroup, option);
    }
    if (btnGroup.hasClass('chargepoint-instantchargelimitselected')){
        // console.log('btnGroup chargepoint-instantchargelimitselected');
        chargemodeLimitOptionsShowHide(btnGroup, option);
    }

}

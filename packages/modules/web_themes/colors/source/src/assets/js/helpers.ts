/*
 * helpers.ts
 * colors theme for openwb 2.0
 * Copyright (c) 2022 Claus Hagen
 */

export function formatWatt(watt: number, decimalPlaces = 1) {
	let wattResult;
	if (watt >= 1000 && decimalPlaces < 4) {
		switch (decimalPlaces) {
			case 0:
				wattResult = Math.round(watt / 1000);
				break;
			case 1:
				wattResult = (Math.round(watt / 100) / 10)
				break;
			case 2:
				wattResult = (Math.round(watt / 10) / 100)
				break;
			case 3:
				wattResult = (Math.round(watt) / 1000)
				break
			default:
				wattResult = Math.round(watt / 100) / 10;
				break;
		}
		return (wattResult?.toLocaleString(undefined, { minimumFractionDigits: decimalPlaces }) + " kW");
	} else {
		return (Math.round(watt).toLocaleString(undefined) + " W");
	}
}

export function formatWattH(wattH: number, decimalPlaces = 1, useMWh = false) {
	let wattResult
	if (wattH >= 1000 && decimalPlaces < 4) {
		switch (decimalPlaces) {
			case 0:
				wattResult = Math.round(wattH / 1000);
				break;
			case 1:
				wattResult = (Math.round(wattH / 100) / 10).toFixed(1);
				break;
			case 2:
				wattResult = (Math.round(wattH / 10) / 100).toFixed(2);
				break;
			case 3:
				wattResult = (Math.round(wattH) / 1000).toFixed(3);
				break;
			default:
				wattResult = Math.round(wattH / 100) / 10;
				break;
		}
		return (wattResult.toLocaleString(undefined, { minimumFractionDigits: decimalPlaces }) + (useMWh ? " MWh":" kWh"))
	} else {
		return (Math.round(wattH).toLocaleString(undefined) + (useMWh ? " kWh" :  " Wh"))
	}
}
export function formatTime(seconds: number) {
	const hours = Math.floor(seconds / 3600);
	const minutes = ((seconds % 3600) / 60).toFixed(0);
	if (hours > 0) {
		return (hours + "h " + minutes + " min");
	} else {
		return (minutes + " min");
	}
}
export function formatDate(d: Date, mode: string = 'day') {
	switch (mode) {
		case 'day':
		case 'today':
			return `${d.getDate()}.${d.getMonth() + 1}.${d.getFullYear()}`
		case 'month':
			return `${d.getMonth()}-${d.getFullYear()}`
		case 'year':
			return `${d.getFullYear()}`
	}
}

export function formatMonth(month: number, year: number) {
	const months = ['Jan', 'Feb', 'März', 'April', 'Mai', 'Juni', 'Juli', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'];
	return (months[month] + " " + year);
}

export function formatTemp(t: number) {
	return ((Math.round(t * 10) / 10).toLocaleString(undefined, { minimumFractionDigits: 1 }) + "°")
}

/* function shiftLeft() {
	switch (wbdata.graphMode) {
		case 'live':
			wbdata.graphMode = 'day';
			wbdata.graphPreference = 'day';
			wbdata.showTodayGraph = true;
			powerGraph.deactivateLive();
			powerGraph.activateDay();
			wbdata.prefs.showLG = false;
			wbdata.persistGraphPreferences();
			d3.select("button#graphRightButton").classed("disabled", false)
			break;
		case 'day':
			wbdata.showTodayGraph = false;
			wbdata.graphDate.setTime(wbdata.graphDate.getTime() - 86400000);
			powerGraph.activateDay();
			break;
		case 'month':
			wbdata.graphMonth.month = wbdata.graphMonth.month - 1;
			if (wbdata.graphMonth.month < 0) {
				wbdata.graphMonth.month = 11;
				wbdata.graphMonth.year = wbdata.graphMonth.year - 1;
			}
			powerGraph.activateMonth();
			break;
		default: break;		
	}
}
 */
/* function shiftRight() {
	today = new Date();
	const d = wbdata.graphDate;
	switch (wbdata.graphMode) {
		case 'live':
			break;
		case 'day':
			if (d.getDate() == today.getDate() && d.getMonth() == today.getMonth() && d.getFullYear() == today.getFullYear()) { // date is today, switch to live graph
				wbdata.graphMode = 'live';
				powerGraph.deactivateDay();
				powerGraph.activateLive();
				wbdata.graphPreference = 'live';
				wbdata.prefs.showLG = true;
				wbdata.persistGraphPreferences();
				d3.select("button#graphLeftButton").classed("disabled", false)
				d3.select("button#graphRightButton").classed("disabled", true)
			} else { // currently looking at a previous day
				wbdata.graphDate.setTime(wbdata.graphDate.getTime() + 86400000);
				const nd = wbdata.graphDate;
				if (nd.getDate() == today.getDate() && nd.getMonth() == today.getMonth() && nd.getFullYear() == today.getFullYear()) {
					wbdata.showTodayGraph = true;
				}
				powerGraph.activateDay();
			}
			break;
		case 'month':
			if ((today.getMonth() != wbdata.graphMonth.month) || (today.getFullYear() != wbdata.graphMonth.year)) { // we are looking at a previous month
				wbdata.graphMonth.month = wbdata.graphMonth.month + 1;
				if (wbdata.graphMonth.month == 12) {
					wbdata.graphMonth.month = 0;
					wbdata.graphMonth.year = wbdata.graphMonth.year + 1;
				}
				powerGraph.activateMonth();
			} 
		}
	
} */

/* function toggleGrid() {
	wbdata.showGrid = !wbdata.showGrid;
	powerGraph.updateGraph();
	yieldMeter.update();
	wbdata.persistGraphPreferences();
} */

/* function switchDecimalPlaces() {
	if (wbdata.decimalPlaces  < 3) {
		wbdata.decimalPlaces = wbdata.decimalPlaces+1;
	} else {
		wbdata.decimalPlaces = 0;
	}
	wbdata.persistGraphPreferences();
	powerMeter.update();
	yieldMeter.update();
	smartHomeList.update();
} */

/* function switchSmartHomeColors() {
	const doc = d3.select("html");
	switch (wbdata.smartHomeColors) {
		case 'normal':
			wbdata.smartHomeColors = 'standard';
			doc.classed("shcolors-normal", false);
			doc.classed("shcolors-standard", true);
			doc.classed("shcolors-advanced", false);
			break;
		case 'standard':
			wbdata.smartHomeColors = 'advanced';
			doc.classed("shcolors-normal", false);
			doc.classed("shcolors-standard", false);
			doc.classed("shcolors-advanced", true);
			break;
		case 'advanced':
			wbdata.smartHomeColors = 'normal';
			doc.classed("shcolors-normal", true);
			doc.classed("shcolors-standard", false);
			doc.classed("shcolors-advanced", false);
			break;
		default:
			wbdata.smartHomeColors = 'normal';
			doc.classed("shcolors-normal", true);
			doc.classed("shcolors-standard", false);
			doc.classed("shcolors-advanced", false);
			break;
	}
	wbdata.persistGraphPreferences();
} */

/* function toggleMonthView() {
	if (wbdata.graphMode == 'month') {
		wbdata.graphMode = wbdata.graphPreference;
		if (wbdata.graphPreference == 'live') {
			powerGraph.activateLive();
			powerGraph.deactivateMonth();
		} else {
			powerGraph.activateDay();
			powerGraph.deactivateMonth();
		}
	} else {
		wbdata.graphMode = 'month';
		powerGraph.activateMonth();
		powerGraph.deactivateDay();
		powerGraph.deactivateLive();	
	}
	yieldMeter.update();
}
 */
/*export default {
	formatWatt,
	formatWattH,
	formatTime,
	formatMonth,
	 shiftLeft,
	shiftRight,
	toggleGrid,
	switcDecimalPlaces,
	switchSmartHomeColors,
	toggleMonthView 
}*/
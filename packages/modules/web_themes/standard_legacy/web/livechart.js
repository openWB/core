var style = getComputedStyle(document.body);
var fontColor = style.getPropertyValue('--fontCol');
var gridColor = style.getPropertyValue('--gridCol');
var xGridColor = style.getPropertyValue('--xGridCol');
var gridSocColor = style.getPropertyValue('--gridSocCol');
var tickColor = style.getPropertyValue('--tickCol');
var cpColor = style.getPropertyValue('--cpCol');
var cpBgColor = style.getPropertyValue('--cpBgCol');
var evSocColor = style.getPropertyValue('--evSocCol');
var evuColor = style.getPropertyValue('--evuCol');
var evuBgColor = style.getPropertyValue('--evuBgCol');
var counterColor = style.getPropertyValue('--counterCol');
var counterBgColor = style.getPropertyValue('--counterBgCol');
var pvAllColor = style.getPropertyValue('--pvCol');
var pvAllBgColor = style.getPropertyValue('--pvBgCol');
var batAllColor = style.getPropertyValue('--batteryCol');
var batAllBgColor = style.getPropertyValue('--batteryBgCol');
var batAllSocColor = style.getPropertyValue('--batterySocCol');
var batAllSocBgColor = style.getPropertyValue('--batterySocBgCol');
var homeColor = style.getPropertyValue('--homeConsumptionCol');
var homeBgColor = style.getPropertyValue('--homeConsumptionBgCol');
var cpAllColor = style.getPropertyValue('--cpSumCol');
var cpAllBgColor = style.getPropertyValue('--cpSumBgCol');
var loadColor = style.getPropertyValue('--loadCol');
var loadBgColor = style.getPropertyValue('--loadBgCol');
var smartHomeColor = style.getPropertyValue('--smartHomeDeviceCol');
var smartHomeBgColor = style.getPropertyValue('--smartHomeDeviceBgCol');

var initialRead = 0;
var graphLoaded = 0;
var maxDisplayLength;
var boolDisplayHouseConsumption;
var boolDisplayLoad1;
var boolDisplayLoad2;
var boolDisplayCp1Soc;
var boolDisplayCp2Soc;
var boolDisplayCp1;
var boolDisplayCp2;
var boolDisplayCp3;
var boolDisplayCpAll;
var boolDisplayBatterySoc;
var boolDisplayBattery;
var boolDisplayEvu;
var boolDisplayPv;
var boolDisplayLegend;
var boolDisplayLiveGraph;
var boolDisplaySHD1;
var boolDisplaySHD2;
var boolDisplaySHD3;
var boolDisplaySHD4;
var boolDisplaySHD5;
var boolDisplaySHD6;
var boolDisplaySHD7;
var boolDisplaySHD8;
var boolDisplaySHD9;
var all1 = 0;
var all2 = 0;
var all3 = 0;
var all4 = 0;
var all5 = 0;
var all6 = 0;
var all7 = 0;
var all8 = 0;
var all9 = 0;
var all10 = 0;
var all11 = 0;
var all12 = 0;
var all13 = 0;
var all14 = 0;
var all15 = 0;
var all16 = 0;
var all1p = "";
var all2p = "";
var all3p = "";
var all4p = "";
var all5p = "";
var all6p = "";
var all7p = "";
var all8p = "";
var all9p = "";
var all10p = "";
var all11p = "";
var all12p = "";
var all13p = "";
var all14p = "";
var all15p = "";
var all16p = "";

var hideHaus;
var myLine;
var allChartData = [];
var chartUpdateBuffer = [];

function parseData(allData) {
	var result = [];
	allData.split("\n").forEach(function(line) {
		if (line.length > 5) {
			try {
				lineJson = JSON.parse(line);
				lineJson.timestamp = lineJson.timestamp * 1000;
				result.push(lineJson);
			} catch (e) {
				if (e instanceof SyntaxError) {
					console.warn("bad json syntax: " + line);
				} else {
					console.error(e.name + ': ' + e.message);
				}
			}
		} else {
			console.debug('line too short:', line);
		}
	});
	return result;
}

// not used for time scale chart
// function getXScaleData(matrix){
// 	return matrix.map(function(row){
// 		// return row.time;
// 		return row.timestamp*1000;
// 	});
// }

// not used, parsing is done in chart object
// function getColData(matrix, colLabel){
// 	console.log('getColData: '+colLabel);
// 	return matrix.map(function(row){
// 		data = {x:row.timestamp};
// 		if(row[colLabel]){
// 			data['y'] = row[colLabel];
// 		} else {
// 			data['y'] = 0;
// 		}
// 		return data;
// 	});
// }

let datasetTemplates = {
	// optional components
	"pv-all": {
		label: 'PV ges.',
		jsonKey: null,
		borderColor: pvAllColor,
		backgroundColor: pvAllBgColor,
		fill: true,
		lineTension: 0.2,
		hidden: boolDisplayPv,
		borderWidth: 1,
		data: null,
		yAxisID: 'y1',
		parsing: {
			xAxisKey: 'timestamp',
			yAxisKey: null
		}
	},
	"bat-all-power": {
		label: 'Speicher ges.',
		jsonKey: null,
		borderColor: batAllColor,
		backgroundColor: batAllBgColor,
		fill: true,
		lineTension: 0.2,
		borderWidth: 1,
		data: null,
		hidden: boolDisplayBattery,
		yAxisID: 'y1',
		parsing: {
			xAxisKey: 'timestamp',
			yAxisKey: null
		}
	},
	"bat-all-soc": {
		label: 'Speicher ges. SoC',
		jsonKey: null,
		borderColor: batAllSocColor,
		backgroundColor: batAllSocBgColor,
		borderDash: [10, 5],
		hidden: boolDisplayBatterySoc,
		fill: false,
		lineTension: 0.2,
		borderWidth: 2,
		data: null,
		yAxisID: 'y2',
		parsing: {
			xAxisKey: 'timestamp',
			yAxisKey: null
		}
	},
	// additional counter
	"counter-power": {
		label: 'Zähler',
		jsonKey: null,
		borderColor: counterColor,
		backgroundColor: counterBgColor,
		borderWidth: 2,
		hidden: false,
		fill: false,
		lineTension: 0.2,
		data: null,
		yAxisID: 'y1',
		parsing: {
			xAxisKey: 'timestamp',
			yAxisKey: null
		}
	},
	// charge points
	"cp-power": {
		label: 'LP',
		jsonKey: null,
		borderColor: cpColor,
		backgroundColor: cpBgColor,
		borderWidth: 2,
		hidden: false,
		fill: false,
		lineTension: 0.2,
		data: null,
		yAxisID: 'y1',
		parsing: {
			xAxisKey: 'timestamp',
			yAxisKey: null
		}
	},
	// vehicles
	"ev-soc": {
		label: 'EV SoC',
		jsonKey: null,
		borderColor: evSocColor,
		borderDash: [10, 5],
		borderWidth: 2,
		hidden: false,
		fill: false,
		lineTension: 0.2,
		data: null,
		yAxisID: 'y2',
		parsing: {
			xAxisKey: 'timestamp',
			yAxisKey: null
		}
	},
	// SmartHome
	"load-power": {
		label: 'Verbraucher',
		jsonKey: null,
		borderColor: loadColor,
		backgroundColor: loadBgColor,
		fill: false,
		lineTension: 0.2,
		borderWidth: 2,
		hidden: boolDisplayLoad1,
		data: null,
		yAxisID: 'y1',
		parsing: {
			xAxisKey: 'timestamp',
			yAxisKey: null
		}
	},
	// SmartHome 2.0 devices
	"sh-power": {
		label: "Gerät",
		jsonKey: null,
		borderColor: smartHomeColor,
		backgroundColor: smartHomeBgColor,
		fill: false,
		lineTension: 0.2,
		borderWidth: 2,
		data: null,
		yAxisID: 'y1',
		hidden: boolDisplaySHD1,
		parsing: {
			xAxisKey: 'timestamp',
			yAxisKey: null
		}
	},
	// SmartHome 2.0 device temperatures
	// "sh-temp": {
	// 	label: 'Temperatur',
	// 	borderColor: "rgba(250, 250, 155, 0.7)",
	// 	backgroundColor: 'blue',
	// 	fill: false,
	// 	lineTension: 0.2,
	// 	borderWidth: 2,
	// 	data: null,
	// 	yAxisID: 'y2',
	// 	hidden: boolDisplaySHD1T1,
	// 	parsing: {
	// 	xAxisKey: 'timestamp',
	// 		yAxisKey: null
	// 	}
	// }
};

var chartDatasets = [
	// always available elements
	{
		label: 'EVU',
		jsonKey: 'grid',
		borderColor: evuColor,
		backgroundColor: evuBgColor,
		borderWidth: 1,
		fill: true,
		lineTension: 0.2,
		data: allChartData,
		hidden: boolDisplayEvu,
		yAxisID: 'y1',
		parsing: {
			xAxisKey: 'timestamp',
			yAxisKey: 'grid'
		}
	},
	{
		label: 'Hausverbrauch',
		jsonKey: 'house-power',
		borderColor: homeColor,
		backgroundColor: homeBgColor,
		fill: false,
		lineTension: 0.2,
		borderWidth: 2,
		hidden: boolDisplayHouseConsumption,
		data: allChartData,
		yAxisID: 'y1',
		parsing: {
			xAxisKey: 'timestamp',
			yAxisKey: 'house-power'
		}
	},
	{
		label: 'LP ges.',
		jsonKey: 'charging-all',
		borderColor: cpAllColor,
		backgroundColor: cpAllBgColor,
		fill: true,
		lineTension: 0.2,
		borderWidth: 2,
		data: allChartData,
		hidden: boolDisplayCpAll,
		yAxisID: 'y1',
		parsing: {
			xAxisKey: 'timestamp',
			yAxisKey: 'charging-all'
		}
	}
];

function loadGraph(animationDuration = 1000) {

	var chartData = {
		// labels not used with time scale
		// labels: atime,
		datasets: chartDatasets
	}

	function getMaxTicksLimit(width) {
		if (width < 350) {
			return 6;
		} else if (width < 470) {
			return 9;
		} else if (width < 768) {
			return 12;
		} else {
			return 18;
		}
	}

	function setGraphLineBorderWidth(theGraph, newWidth) {
		// sets borderWidth attribute for all single lines without fill
		for (var index = 0; index < theGraph.config.data.datasets.length; index++) {
			if (!theGraph.config.data.datasets[index].fill) {
				theGraph.config.data.datasets[index].borderWidth = newWidth;
			}
		}
	}

	function doGraphResponsive(chartInstance) {
		// changes graph responding to screen size
		// quantity of x-axis labels
		chartInstance.config.options.scales.x.ticks.maxTicksLimit = getMaxTicksLimit(chartInstance.width);
		// other settings
		if (chartInstance.width > 390) {
			setGraphLineBorderWidth(chartInstance, 2);
			chartInstance.config.options.scales.x.ticks.font.size = 12;
			chartInstance.config.options.scales.y1.ticks.font.size = 12;
			chartInstance.config.options.scales.y1.title.font.size = 12;
			chartInstance.config.options.scales.y2.ticks.font.size = 12;
			chartInstance.config.options.scales.y2.title.font.size = 12;
		} else {
			setGraphLineBorderWidth(chartInstance, 1);
			chartInstance.config.options.scales.x.ticks.font.size = 10;
			chartInstance.config.options.scales.y1.ticks.font.size = 9;
			chartInstance.config.options.scales.y1.title.font.size = 10;
			chartInstance.config.options.scales.y2.ticks.font.size = 9;
			chartInstance.config.options.scales.y2.title.font.size = 10;
		}
		chartInstance.update();
	}

	var ctx = document.getElementById('canvas').getContext('2d');

	window.myLine = new Chart(ctx, {
		type: 'line',
		plugins: [{
			afterInit: doGraphResponsive,
			resize: doGraphResponsive
		}],
		data: chartData,
		options: {
			plugins: {
				title: {
					display: false
				},
				tooltip: {
					enabled: true
				},
				legend: {
					display: boolDisplayLegend,
					labels: {
						color: fontColor,
						// filter: function(item,chart) {
						// 	if (
						// 		item.text.includes(hideHaus) ||
						// 		...
						// 	) {
						// 		return false;
						// 	} else {
						// 		return true;
						// 	}
						// }
					}
				}
			},
			elements: {
				point: {
					radius: 0
				}
			},
			animation: {
				duration: animationDuration,
				onComplete: function(animation) {
					// if duration was set to 0 to avoid pumping after reload, set back to default
					this.options.animation.duration = 1000
				}
			},
			responsive: true,
			maintainAspectRatio: false,
			scales: {
				x: {
					type: 'time',
					time: {
						unit: 'minute'
					},
					display: true,
					title: {
						display: false
					},
					ticks: {
						source: 'data',
						font: {
							size: 12
						},
						color: tickColor,
						maxTicksLimit: 15
					},
					grid: {
						color: xGridColor
					}
				},
				y1: {
					// horizontal line for values displayed on the left side (power, kW)
					position: 'left',
					type: 'linear',
					display: 'auto',
					suggestedMin: 0,
					suggestedMax: 0,
					title: {
						font: {
							size: 12
						},
						display: true,
						text: 'Leistung [kW]',
						color: fontColor
					},
					grid: {
						color: gridColor
					},
					ticks: {
						font: {
							size: 12
						},
						stepSize: 0.2,
						maxTicksLimit: 10,
						color: tickColor
					}
				},
				y2: {
					// horizontal line for values displayed on the right side (SoC, %)
					position: 'right',
					type: 'linear',
					display: 'auto',
					suggestedMin: 0,
					suggestedMax: 100,
					title: {
						font: {
							size: 12
						},
						display: true,
						text: 'SoC [%]',
						color: fontColor
					},
					grid: {
						color: gridSocColor,
					},
					ticks: {
						font: {
							size: 12
						},
						color: tickColor
					}
				}
			}
		}
	});

	initialRead = 1;
	$('#waitForGraphLoadingDiv').hide();
}  // end loadGraph

// Sichtbarkeit für SmartHome Devices im Graph
function setVisibility(dataArray, hideVar, hideValue, boolDisplay) {
	var arrayLength = dataArray.length;
	var vis = 0
	for (var i = 0; i < arrayLength; i++) {
		if ((dataArray[i] >= 0.010) || (dataArray[i] <= -0.010)) {
			vis = 1
		}
	}
	if (vis == 0) {
		window[hideVar] = hideValue;
		window[boolDisplay] = true;
	} else {
		window[hideVar] = 'foo';
		window[boolDisplay] = false;
	}
}

function getDatasetIndex(datasetId) {
	index = chartDatasets.findIndex(function(dataset) {
		return dataset.jsonKey == datasetId;
	});
	if (index != -1) {
		console.debug('index for dataset "' + datasetId + '": ' + index);
		return index;
	}
	console.debug('no index found for "' + datasetId + '"');
	return
}

function addDataset(datasetId) {
	var datasetTemplate = datasetId.replace(/\d/g, '');
	var datasetIndex = undefined;
	if (number = datasetId.match(/([\d]+)/g)) {
		datasetIndex = number[0];
	}
	console.debug('template name: ' + datasetTemplate + ' index: ' + datasetIndex);
	if (datasetTemplates[datasetTemplate]) {
		newDataset = JSON.parse(JSON.stringify(datasetTemplates[datasetTemplate]));
		newDataset.parsing.yAxisKey = datasetId;
		newDataset.jsonKey = datasetId;
		if (datasetIndex) {
			newDataset.label = newDataset.label + ' ' + datasetIndex;
		}
		return chartDatasets.push(newDataset) - 1;
	} else {
		console.warn('no matching template found: ' + datasetId);
	}
	return
}

function initDataset(datasetId) {
	var index = getDatasetIndex(datasetId);
	if (index == undefined) {
		index = addDataset(datasetId);
	}
	if (index != undefined) {
		chartDatasets[index].data = allChartData;
	}
}

function truncateData(data) {
	if (typeof maxDisplayLength !== "undefined" && data.length > maxDisplayLength) {
		console.debug("datasets: " + data.length + " removing: " + (data.length - maxDisplayLength));
		data.splice(0, data.length - maxDisplayLength);
	}
}

function mergeGraphData() {
	if ((all1 == 1) && (all2 == 1) && (all3 == 1) && (all4 == 1) && (all5 == 1) && (all6 == 1) && (all7 == 1) && (all8 == 1) && (all9 == 1) && (all10 == 1) && (all11 == 1) && (all12 == 1) && (all13 == 1) && (all14 == 1) && (all15 == 1) && (all16 == 1)) {
		var allData = all1p + "\n" + all2p + "\n" + all3p + "\n" + all4p + "\n" + all5p + "\n" + all6p + "\n" + all7p + "\n" + all8p + "\n" + all9p + "\n" + all10p + "\n" + all11p + "\n" + all12p + "\n" + all13p + "\n" + all14p + "\n" + all15p + "\n" + all16p;
		allChartData = parseData(allData);
		truncateData(allChartData);
		if (allChartData.length >= 30) { // 5 minutes * 6 measurements/min
			Object.keys(allChartData[allChartData.length - 1]).forEach(function(key) {
				if (key != 'time' && key != 'timestamp') {
					initDataset(key);
				}
			});
			// after receipt of all data segments, unsubscribe from these topics to save bandwidth
			unsubscribeMqttGraphSegments();

			initialRead = 1;
			$('#waitForGraphLoadingDiv').text('Graph lädt...');
			checkGraphLoad();
			// now we are ready to receive small updates for graph data
		} else {
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

			var percent = (allChartData.length / 30 * 100).toFixed();
			$('#waitForGraphLoadingDiv').text('Erst ca. ' + percent + '% der mindestens benötigten Datenpunkte für das Diagramm vorhanden.');
		}
	}
} // end mergeGraphData

function updateGraph(dataset) {
	chartUpdateBuffer = chartUpdateBuffer.concat(parseData(dataset));
	if (initialRead == 1 && myLine != undefined) {
		chartUpdateBuffer.forEach(function(row, index) {
			if (row.timestamp > allChartData[allChartData.length-1].timestamp) {
				allChartData.push(row);
			} else {
				console.warn("old data detected:", row.timestamp, row.time);
				console.warn("last timestamp:", allChartData[allChartData.length-1].timestamp, allChartData[allChartData.length-1].time);
			}
		});
		truncateData(allChartData);
		chartUpdateBuffer = [];
		myLine.update();
		console.debug('graph updated, last dataset:', allChartData[allChartData.length-1].timestamp, allChartData[allChartData.length-1].time);
	} else {
		console.debug('graph not yet initialized, data stored in buffer');
	}
}

function checkGraphLoad() {
	if (graphLoaded == 1) {
		myLine.destroy();
		loadGraph(0); // when reloading graph, no more "pumping" animations
		return;
	}
	if (typeof boolDisplayHouseConsumption === "boolean" &&
		typeof boolDisplayCpAll === "boolean" &&
		typeof boolDisplayEvu === "boolean"
	) {
		if (initialRead != 0) {
			if (graphLoaded == 0) {
				graphLoaded = 1;
			} else {
				myLine.destroy();
			}
			loadGraph();
		}
	}
}

function forceGraphLoad() {
	if (graphLoaded == 0) {
		if (!(typeof boolDisplayHouseConsumption === "boolean")) {
			showHideDataset('boolDisplayHouseConsumption');
		}
		if (!(typeof boolDisplayCpAll === "boolean")) {
			showHideDataset('boolDisplayCpAll');
		}
		if (!(typeof boolDisplayEvu === "boolean")) {
			showHideDataset('boolDisplayEvu');
		}
		if (!(typeof boolDisplayLegend === "boolean")) {
			showHideDataset('boolDisplayLegend');
		}
		if (typeof maxDisplayLength === "undefined") {
			console.info("setting graph duration to default of 30 minutes");
			maxDisplayLength = 30 * 6;
		}
		checkGraphLoad();
	}
} // end forceGraphLoad

function showHideDataset(theDataset) {
	if (window[theDataset] == true) {
		publish("1", "openWB/graph/" + theDataset);
	} else if (window[theDataset] == false) {
		publish("0", "openWB/graph/" + theDataset);
	} else {
		publish("1", "openWB/graph/" + theDataset);
	}
}

function showHideLegend(theDataset) {
	if (window[theDataset] == true) {
		publish("0", "openWB/graph/" + theDataset);
	} else if (window[theDataset] == false) {
		publish("1", "openWB/graph/" + theDataset);
	} else {
		publish("0", "openWB/graph/" + theDataset);
	}
}

function showHide(theDataset) {
	if (window[theDataset] == 0) {
		publish("1", "openWB/graph/" + theDataset);
	} else if (window[theDataset] == 1) {
		publish("0", "openWB/graph/" + theDataset);
	} else {
		publish("1", "openWB/graph/" + theDataset);
	}
}

function subscribeMqttGraphSegments() {
	console.debug('subscribing to graph topics');
	for (var segments = 1; segments < 17; segments++) {
		topic = "openWB/graph/alllivevaluesJson" + segments;
		client.subscribe(topic, { qos: 0 });
	}
}

function unsubscribeMqttGraphSegments() {
	console.debug('unsubscribing from graph topics');
	for (var segments = 1; segments < 17; segments++) {
		topic = "openWB/graph/alllivevaluesJson" + segments;
		client.unsubscribe(topic);
	}
}

$(document).ready(function() {
	setTimeout(forceGraphLoad, 15000);
});

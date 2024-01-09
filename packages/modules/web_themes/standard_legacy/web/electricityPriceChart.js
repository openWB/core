function createPriceAnnotations(){
	let colorUnblocked = 'rgba(73, 238, 73, 0.3)';
	let colorBlocked = 'rgba(255, 10, 13, 0.3)';
	// creates green annotation boxes for all times where price is <= maxPrice
	class Annotation {
		type = 'box';
		drawTime = "beforeDatasetsDraw"; // (default)
		xMin = myData[0].timestamp;
		xMax = myData[0].timestamp;
		borderWidth = 2;
		cornerRadius = 0;
	}
	var annotations = [];
	var maxPrice = $('#maxPriceBox')[0].value;
	if ( !isNaN(maxPrice) ) {
		for ( var i = 0; i < myData.length; i++ ) {
			if ( myData[i].price <= maxPrice ) {
				var newAnnotation = new Annotation();
				newAnnotation.borderColor = colorUnblocked;
				newAnnotation.backgroundColor = colorUnblocked;
				newAnnotation.xMin = myData[i].timestamp;  // set left edge of box
				while ( i < myData.length && myData[i].price <= maxPrice ) {
					i++;
				}
				if ( i == myData.length ) {
					// correct index if out of bounds
					i--;
				}
				newAnnotation.xMax = myData[i].timestamp;  // first index myData[i] > maxPrice is right edge of box
				annotations.push(newAnnotation);  // add box to annotations
			}
		}
		for ( var i = 0; i < myData.length; i++ ) {
			if ( myData[i].price > maxPrice ) {
				var newAnnotation = new Annotation();
				newAnnotation.borderColor = colorBlocked;
				newAnnotation.backgroundColor = colorBlocked;
				newAnnotation.xMin = myData[i].timestamp;  // set left edge of box
				while ( i < myData.length && myData[i].price > maxPrice ) {
					i++;
				}
				if ( i == myData.length ) {
					// correct index if out of bounds
					i--;
				}
				newAnnotation.xMax = myData[i].timestamp;  // first index myData[i] > maxPrice is right edge of box
				annotations.push(newAnnotation);  // add box to annotations
			}
		}
	}
	return annotations;
}

function loadElectricityPriceChart() {
	if (typeof electricityPriceList === 'undefined') {
		console.error("'electricityPriceTimeline' not defined. Skipping chart update.");
		return
	}

	myData = [];
	// proper scaling:
	// timestamp: seconds -> milliseconds
	// price: €/Wh -> €/kWh
	for (const [key, value] of Object.entries(electricityPriceList)) {
		myData.push({
			timestamp: key * 1000,
			price: value * 100000,
		});
	}
	// repeat last dataset with 59min 95sec offset
	const lastData = myData.slice(-1)[0];
	myData.push({
		timestamp: lastData.timestamp + (60 * 60 - 1) * 1000,
		price: lastData.price,
	});

	var electricityPriceChartData = {
		datasets: [
			{
				label: "Stromtarif",
				unit: "ct/kWh",
				type: "line",
				stepped: true,
				borderColor: "rgba(255, 0, 0, 0.7)",
				backgroundColor: "rgba(255, 10, 13, 0.3)",
				fill: false,
				pointStyle: "circle",
				pointRadius: 0,
				pointHoverRadius: 4,
				cubicInterpolationMode: "monotone",
				hidden: false,
				borderWidth: 1,
				data: myData,
				yAxisID: "y",
				parsing: {
					xAxisKey: "timestamp",
					yAxisKey: "price",
				},
			},
		],
	}

	var ctxElectricityPricechart = $('#electricityPriceChartCanvas')[0].getContext('2d');

	window.electricityPricechart = new Chart(ctxElectricityPricechart, {
		type: 'line',
		data: electricityPriceChartData,
		options: {
			plugins: {
				title: {
					display: false
				},
				tooltips: {
					enabled: true,
				},
				legend: {
					display: false
				},
				annotation: {
					annotations: createPriceAnnotations()
				},
			},
			elements: {
				point: {
					radius: 2,
				},
			},
			responsive: true,
			maintainAspectRatio: false,
			interaction: {
				mode: "index",
				intersect: false,
			},
			animation: false,
			scales: {
				x: {
					type: "time",
					time: {
						unit: "hour",
						// tooltipFormat: "DD T",
						text: "Zeit",
						maxTicksLimit: 24,
					},
					display: true,
					title: {
						display: false,
						text: "Uhrzeit",
					},
					ticks: {
						font: {
							size: 12,
						},
						// color: tickColor,
						maxTicksLimit: 0,
					},
					grid: {
						// color: xGridColor,
					},
				},
				y: {
					position: "left",
					type: "linear",
					display: "auto",
					// suggestedMin: 0,
					// suggestedMax: 0,
					title: {
						font: {
							size: 12,
						},
						display: true,
						text: "Preis [ct/kWh]",
						// color: fontColor
					},
					grid: {
						// color: gridColor
					},
					ticks: {
						font: {
							size: 12,
						},
						stepSize: 0.5,
						maxTicksLimit: 6,
						// color: tickColor
					},
				},
			}
		}
	});
}

// global var containing current et provider data
var electricityPriceList = undefined;
var myData = [];

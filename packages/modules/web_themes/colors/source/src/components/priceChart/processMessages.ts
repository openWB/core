import { etData } from './model'

export function processEtProviderMessages(topic: string, message: string) {
    if (topic == 'openWB/optional/et/active') {
      etData.isEtEnabled = JSON.parse(message)
    } else if (topic == 'openWB/optional/et/get/price') {
      etData.etCurrentPrice = parseFloat(message)
    } else if (topic == 'openWB/optional/et/config/max_price') {
     etData.updateEtMaxPrice( parseFloat(message))
    } else if (topic == 'openWB/optional/et/provider') {
      etData.etProvider = JSON.parse(message)
    } else {
      console.warn('Ignored ET Provider message: ' + topic)
    }
    // else if ( mqttTopic == 'openWB/global/ETProvider/modulePath' ) {
    // 	$('.etproviderLink').attr("href", "/openWB/modules/"+mqttPayload+"/stromtarifinfo/infopagephp");
    // }
    // else if ( mqttTopic == 'openWB/global/awattar/pricelist' ) {
    // 	// read etprovider values and trigger graph creation
    // 	// loadElectricityPriceChart will show electricityPriceChartCanvas if etprovideraktiv=1 in openwb.conf
    // 	// graph will be redrawn after 5 minutes (new data pushed from cron5min.sh)
    // 	var csvData = [];
    // 	var rawcsv = mqttPayload.split(/\r?\n|\r/);
    // 	// skip first entry: it is module-name responsible for list
    // 	for (var i = 1; i < rawcsv.length; i++) {
    // 		csvDatapush(rawcsv[i].split(','));
    // 	}
    // 	// Timeline (x-Achse) ist UNIX Timestamp in UTC, deshalb Umrechnung (*1000) in Javascript-Timestamp (mit Millisekunden)
    // 	electricityPriceTimeline = getCol(csvData, 0).map(function(x) { return x * 1000; });
    // 	// Chartline (y-Achse) ist Preis in ct/kWh
    // 	electricityPriceChartline = getCol(csvData, 1);
  
    // 	loadElectricityPriceChart();
    // }
  }
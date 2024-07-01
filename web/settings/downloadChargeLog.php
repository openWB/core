<?php
$charge_log_path = $_SERVER["DOCUMENT_ROOT"] . "/openWB/data/charge_log/";

if (!preg_match("/[0-9]{4}/", $_GET["year"]) || !preg_match("/^((0?[1-9])|(1[0-2]))$/", $_GET["month"])) {
	http_response_code(400);
	die("invalid data");
}

$file_name = sprintf('%04d%02d', $_GET["year"], $_GET["month"]);
$charge_log_file = $charge_log_path . $file_name . ".json";
$charge_log_data = json_decode(file_get_contents($charge_log_file), true);

function translateHeading($value) {
	$translationList = [
		"chargepoint id" => "Ladepunkt-ID",
		"chargepoint name" => "Ladepunkt",
		"chargepoint serial_number" => "Ladepunkt Seriennummer",
		"chargepoint imported_at_start" => "Zählerstand Ladestart",
		"chargepoint imported_at_end" => "Zählerstand Ladeende",
		"vehicle id" => "Fahrzeug-ID",
		"vehicle name" => "Fahrzeug",
		"vehicle chargemode" => "Lademodus",
		"vehicle prio" => "Priorität",
		"vehicle rfid" => "ID-Tag",
		"vehicle soc_at_start" => "SoC bei Start",
		"vehicle soc_at_end" => "SoC bei Ende",
		"vehicle range_at_start" => "Reichweite bei Start",
		"vehicle range_at_end" => "Reichweite bei Ende",
		"time begin" => "Beginn",
		"time end" => "Ende",
		"time time_charged" => "Dauer",
		"data range_charged" => "Reichweite",
		"data imported_since_mode_switch" => "Energie",
		"data imported_since_plugged" => "Energie seit Anstecken",
		"data power" => "Leistung",
		"data costs" => "Kosten",
		"data power_source"	=> "Energie-Anteile",
	];

	return $translationList[$value] ?? $value;
}

function translateChargeMode($value) {
	$chargeModeTranslations = [
		"instant_charging" => "Sofortladen",
		"pv_charging" => "PV",
		"scheduled_charging" => "Zielladen",
		"time_charging" => "Zeitladen",
		"standby" => "Standby",
		"stop" => "Stop",
		"false" => "Nein",
		"true" => "Ja",
	];

	return $chargeModeTranslations[$value] ?? $value;
}

if (is_array($charge_log_data)) {
	header("Content-Type: text/csv");
	header("Content-Disposition: attachment; filename=ChargeLog-" . $file_name . ".csv");
	$header_done = false;
	foreach ($charge_log_data as $log_entry) {
		// prepare data
		$csv_row = [];
		foreach ($log_entry as $section_key => &$section_value) {
			foreach ($section_value as $key => &$value) {
				if (is_bool($value)) {
					$value = $value ? "true" : "false";
				}
				$translated_key = translateHeading($section_key . " " . $key);
				$csv_row[$translated_key] = translateChargeMode($value);
			}
		}
		if (!$header_done) {
			print(implode(";", array_keys($csv_row)) . "\n");
			$header_done = true;
		}
		print(implode(";", $csv_row) . "\n");
	}
}
?>

<?php
$charge_log_path = $_SERVER["DOCUMENT_ROOT"] . "/openWB/data/charge_log/";

$csv_format = [
	"time begin" => ["header" => "Beginn", "type" => "datetime"],
	"time end" => ["header" => "Ende", "type" => "datetime"],
	"time begin_timestamp" => ["header" => "Zeitstempel Beginn", "type" => "timestamp"],
	"time end_timestamp" => ["header" => "Zeitstempel Ende", "type" => "timestamp"],
	"time time_charged" => ["header" => "Dauer", "type" => "string"],
	"data costs" => ["header" => "Kosten", "type" => "money"],
	"data power_source grid" => ["header" => "Energieanteil Netz", "type" => "percent"],
	"data power_source cp"	=> ["header" => "Energieanteil Ladepunkte", "type" => "percent"],
	"data power_source bat" => ["header" => "Energieanteil Speicher", "type" => "percent"],
	"data power_source pv"	=> ["header" => "Energieanteil PV", "type" => "percent"],
	"vehicle name" => ["header" => "Fahrzeug", "type" => "string"],
	"vehicle id" => ["header" => "Fahrzeug-ID", "type" => "int"],
	"vehicle chargemode" => ["header" => "Lademodus", "type" => "chargemode"],
	"vehicle prio" => ["header" => "Priorität", "type" => "bool"],
	"vehicle rfid" => ["header" => "ID-Tag", "type" => "string"],
	"vehicle soc_at_start" => ["header" => "SoC Beginn", "type" => "int"],
	"vehicle soc_at_end" => ["header" => "SoC Ende", "type" => "int"],
	"vehicle range_at_start" => ["header" => "Reichweite Beginn", "type" => "range"],
	"vehicle range_at_end" => ["header" => "Reichweite Ende", "type" => "range"],
	"chargepoint name" => ["header" => "Ladepunkt", "type" => "string"],
	"chargepoint id" => ["header" => "Ladepunkt-ID", "type" => "int"],
	"chargepoint serial_number" => ["header" => "Zähler Seriennummer", "type" => "string"],
	"data imported_since_mode_switch" => ["header" => "Energie", "type" => "energy"],
	"data range_charged" => ["header" => "Reichweite", "type" => "range"],
	// "data power" => ["header"=>"Leistung", "type"=>"power"],
	"chargepoint imported_at_start" => ["header" => "Zählerstand Beginn", "type" => "energy"],
	"chargepoint imported_at_end" => ["header" => "Zählerstand Ende", "type" => "energy"],
	"data imported_since_plugged" => ["header" => "Energie seit Anstecken", "type" => "energy"],
];

// If the "year" parameter is missing or invalid, respond with HTTP 400 and return an error message.
if (!isset($_GET["year"]) || !preg_match("/^[0-9]{4}$/", $_GET["year"])) {
    http_response_code(400);
    echo json_encode(["error" => "Invalid 'year' parameter. A four-digit year, e.g., 2023, is expected."]);
    exit;
}
$year = intval($_GET["year"]);

// If the "month" parameter is provided and matches the regex for valid months (1-12), use it
if (isset($_GET["month"])) {
    if (preg_match("/^((0?[1-9])|(1[0-2]))$/", $_GET["month"])) {
        $month = $_GET["month"];
        // Format the file name based on the year and month
        $file_name = sprintf('%04d%02d', $year, $month);
        $output_file_name = $file_name;
        $charge_log_file = $charge_log_path . $file_name . ".json";

        // Attempt to load the charge log file for the specific month
        if (file_exists($charge_log_file)) {
            $charge_log_data = json_decode(file_get_contents($charge_log_file), true);
        } else {
            $charge_log_data = []; // Default to an empty array if the file does not exist
        }
    } else {
        // If the "month" parameter is invalid, return HTTP 400 Bad Request
        http_response_code(400);
        echo json_encode(["error" => "Invalid 'month' parameter. Expected a value between 1 and 12."]);
        exit;
    }
} else {
    // If no "month" is provided, process all months for the given year
    $charge_log_data = [];
    for ($month = 1; $month <= 12; $month++) {
        // Format the file name based on the year and month
        $file_name = sprintf('%04d%02d', $year, $month);
        $output_file_name = sprintf('%04d', $year);
        $charge_log_file = $charge_log_path . $file_name . ".json";

        // Append data from each month's charge log file if it exists
        if (file_exists($charge_log_file)) {
            $monthly_data = json_decode(file_get_contents($charge_log_file), true);
            if (is_array($monthly_data)) {
                $charge_log_data = array_merge($charge_log_data, $monthly_data);
            }
        }
    }
}

function newRow()
{
	global $csv_format;
	$row = $csv_format;
	foreach ($row as $key => $value) {
		$row[$key] = null;
	}
	return $row;
}

function translateHeading($value)
{
	global $csv_format;
	return $csv_format[$value] ? $csv_format[$value]["header"] : $value;
}

function formatTimestamp($value)
{
	$timestamp = strtotime($value);
	if ($timestamp === false) {
		return null;
	}
	return $timestamp;
}

function formatDateTime($timestamp)
{
	if ($timestamp === null) {
		return null;
	}
	return date("d.m.Y, H:i:s", $timestamp);
}

function formatInt($value)
{
	return round($value);
}

function formatString($value)
{
	return '"' . $value . '"';
}

function formatMoney($value)
{
	return number_format($value, 2, ",", "");
}

function formatPercent($value)
{
	return number_format($value * 100, 2, ",", "");
}

function formatChargeMode($value)
{
	$chargeModeTranslations = [
		"instant_charging" => "Sofort",
		"pv_charging" => "PV",
		"scheduled_charging" => "Zielladen",
		"time_charging" => "Zeitladen",
		"standby" => "Standby",
		"stop" => "Stop",
	];
	return $chargeModeTranslations[$value] ?? $value;
}

function formatBool($value)
{
	return $value ? "Ja" : "Nein";
}

function formatRange($value)
{
	return round($value);
}

function formatEnergy($value)
{
	return number_format($value / 1000, 2, ",", "");
}

if (is_array($charge_log_data)) {
	header("Content-Type: text/csv");
	header("Content-Disposition: attachment; filename=ChargeLog-" . $output_file_name . ".csv");

	# Output CSV header
	$csv_header = newRow();
	$translated_header = array_map("translateHeading", array_keys($csv_header));
	print('"' . implode('";"', $translated_header) . "\"\n");

	# Output CSV data
	foreach ($charge_log_data as $log_entry) {
		$csv_row = newRow();
		foreach ($csv_row as $column_key => $_) {
			$parts = explode(" ", $column_key);
			$section_key = $parts[0];
			$sub_key = $parts[1];
			$sub_sub_key = isset($parts[2]) ? $parts[2] : null;
			if ($sub_sub_key !== null && isset($log_entry[$section_key][$sub_key][$sub_sub_key])) {
				$csv_row[$column_key] = $log_entry[$section_key][$sub_key][$sub_sub_key];
			} elseif ($sub_sub_key === null && isset($log_entry[$section_key][$sub_key])) {
				$csv_row[$column_key] = $log_entry[$section_key][$sub_key];
			}
			if ($csv_row[$column_key] === null) {
				continue;
			}
			switch ($csv_format[$column_key]["type"]) {
				case "timestamp":
					# value is calculated from datetime
					break;
				case "datetime":
					$timestamp = formatTimestamp($csv_row[$column_key]);
					$csv_row[$column_key . "_timestamp"] = $timestamp;
					$csv_row[$column_key] = formatString(formatDateTime($timestamp));
					break;
				case "int":
					$csv_row[$column_key] = formatInt($csv_row[$column_key]);
					break;
				case "string":
					$csv_row[$column_key] = formatString($csv_row[$column_key]);
					break;
				case "money":
					$csv_row[$column_key] = formatMoney($csv_row[$column_key]);
					break;
				case "percent":
					$csv_row[$column_key] = formatPercent($csv_row[$column_key]);
					break;
				case "chargemode":
					$csv_row[$column_key] = formatString(formatChargeMode($csv_row[$column_key]));
					break;
				case "bool":
					$csv_row[$column_key] = formatString(formatBool($csv_row[$column_key]));
					break;
				case "range":
					$csv_row[$column_key] = formatRange($csv_row[$column_key]);
					break;
				case "energy":
					$csv_row[$column_key] = formatEnergy($csv_row[$column_key]);
					break;
			}
		}
		print(implode(";", $csv_row) . "\n");
	}
}

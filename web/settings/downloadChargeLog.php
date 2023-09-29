<?php
$charge_log_path = $_SERVER["DOCUMENT_ROOT"] . "/openWB/data/charge_log/";

if (!preg_match("/[0-9]{4}/", $_GET["year"]) || !preg_match("/^((0?[1-9])|(1[0-2]))$/", $_GET["month"])) {
	http_response_code(400);
	die("invalid data");
}

$file_name = sprintf('%04d%02d', $_GET["year"], $_GET["month"]);
$charge_log_file = $charge_log_path . $file_name . ".json";
$charge_log_data = json_decode(file_get_contents($charge_log_file), true);

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
				$csv_row[$section_key . " " . $key] = $value;
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

<?php
header('Content-Type: application/json');
$ip = $_SERVER['REMOTE_ADDR'];
$filename = __DIR__ . "/../../data/clients/display-" . str_replace('.', '_', $ip) . ".json";
if (file_exists($filename)) {
	$json = file_get_contents($filename);
	$data = json_decode($json, true);
	if (is_array($data)) {
		$data['ip'] = $ip;
		echo json_encode($data);
	} else {
		http_response_code(500);
		echo json_encode(["error" => "Ungültige JSON-Struktur in $filename"]);
	}
} else {
	http_response_code(404);
	echo json_encode(["error" => "Datei nicht gefunden", "ip" => $ip]);
}

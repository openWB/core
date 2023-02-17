<?php
$valid_commands = array(
	"update"
);
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
	print("invalid request");
	http_response_code(400);
	exit(1);
}
if (!isset($_REQUEST["command"])) {
	print("missing command");
	http_response_code(400);
	exit(1);
}
if (!in_array($_REQUEST["command"], $valid_commands)) {
	print("unsupported command: " . $_REQUEST["command"]);
	http_response_code(400);
	exit(1);
}
if (!isset($_REQUEST["data"])) {
	print("missing data");
	http_response_code(400);
	exit(1);
}
$data = json_decode($_REQUEST["data"], true);
if (is_null($data)) {
	print("invalid data");
	http_response_code(400);
	exit(1);
}
if (!array_key_exists("ip_address", $data)) {
	print("incomplete data");
	http_response_code(400);
	exit(1);
}
if (!filter_var($data["ip_address"], FILTER_VALIDATE_IP)) {
	print("invalid ip");
	http_response_code(400);
	exit(1);
}

print("executing command '" . $_REQUEST["command"] . "' with ip '" . $data["ip_address"] . "'\n");
switch ($_REQUEST["command"]) {
	case 'update':
		$data = array("update" => 1);
		$url = "http://" . $data["ip_address"] . "/connect.php";
		$options = array(
			"http" => array(
				"header" =>  "Content-type: application/x-www-form-urlencoded",
				'method'  => 'POST',
				'content' => http_build_query($data)
			)
		);
		$context  = stream_context_create($options);
		$result = file_get_contents($url, false, $context);
		break;
}

if ($result === false) {
	print("command failed");
	http_response_code(500);
	exit(1);
}

print("command done");

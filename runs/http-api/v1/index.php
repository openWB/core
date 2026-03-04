<?php

header("Content-Type: application/json; charset=UTF-8");

// HTTP Basic Auth prüfen bei Apache2
$auth_user = isset($_SERVER['PHP_AUTH_USER']) ? $_SERVER['PHP_AUTH_USER'] : null;
$auth_pass = isset($_SERVER['PHP_AUTH_PW']) ? $_SERVER['PHP_AUTH_PW'] : null;

function exit_with_error(array $response, int $code = 400)
{
	http_response_code($code);
	echo json_encode($response);
	exit;
}

function return_result(array $response, int $code = 200)
{
	http_response_code($code);
	echo json_encode($response);
	exit;
}

// read input stream and parse contents as json
// this allows us to send json data in the request body
// instead of query parameters
// "topic" and "message" in the request body will override query parameters
$input = file_get_contents("php://input", false, null, 0, 1024);
if ($input !== false) {
	$post_data = json_decode($input, true);
	if ($post_data !== null) {
		if (array_key_exists("topic", $post_data)) {
			$_REQUEST["topic"] = $post_data["topic"];
		}
		if (array_key_exists("message", $post_data)) {
			$_REQUEST["message"] = $post_data["message"];
		}
	}
}

// validate topic string
if (!isset($_REQUEST["topic"]) || strlen($_REQUEST["topic"]) < 3) {
	exit_with_error(array(
		"status" => "failed",
		"error" => "Missing or invalid topic."
	));
}

if (!isset($_REQUEST["message"])) {
	// block reading set topics
	if (strpos($_REQUEST["topic"], "openWB/set/") === 0) {
		exit_with_error(array(
			"status" => "failed",
			"error" => "Reading set topics is not allowed."
		));
	}
	// read topic request
	$cmd = "mosquitto_sub -h 127.0.0.1 -p 8883 -V mqttv5 --insecure -C 1 -W 1 --quiet -t " . escapeshellarg($_REQUEST["topic"]);
	if ($auth_user !== null && $auth_pass !== null) {
		$cmd .= " -u " . escapeshellarg($auth_user) . " -P " . escapeshellarg($auth_pass);
	}
	$response = exec($cmd, $output, $result_code);
	if ($result_code > 0) {
		// an error occurred
		exit_with_error(array(
			"status" => "failed",
			"topic" => $_REQUEST["topic"],
			"error" => "Topic not found!",
			"user" => $auth_user
		));
	} else {
		// decode message
		$payload = json_decode($response, true);
		if (json_last_error() !== JSON_ERROR_NONE) {
			// failed to decode message
			exit_with_error(array(
				"status" => "failed",
				"topic" => $_REQUEST["topic"],
				"error" => "Failed to decode message: " . json_last_error_msg(),
				"user" => $auth_user
			));
		}
		// return the message
		return_result(array(
			"status" => "success",
			"topic" => $_REQUEST["topic"],
			"message" => $payload
		));
	}
} else {
	// set topic request
	// validate topic string
	if (strpos($_REQUEST["topic"], "openWB/set/") !== 0) {
		// topic is invalid
		exit_with_error(array(
			"status" => "failed",
			"error" => "Invalid topic. Only openWB/set/ topics are writable."
		));
	} else {
		// topic is valid
		$cmd = "mosquitto_pub -h 127.0.0.1 -p 8883 -V mqttv5 --insecure -t " . escapeshellarg($_REQUEST["topic"]) . " -m " . escapeshellarg($_REQUEST["message"]);
		if ($auth_user !== null && $auth_pass !== null) {
			$cmd .= " -u " . escapeshellarg($auth_user) . " -P " . escapeshellarg($auth_pass);
		}
		$response = exec($cmd, $output, $result_code);
		if ($result_code > 0) {
			exit_with_error(array(
				"status" => "failed",
				"topic" => $_REQUEST["topic"],
				"error" => "Failed to publish message.",
				"user" => $auth_user
			));
		} else {
			return_result(array(
				"status" => "success",
				"topic" => $_REQUEST["topic"],
				"message" => $_REQUEST["message"]
			));
		}
	}
}

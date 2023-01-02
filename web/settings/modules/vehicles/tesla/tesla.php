<?php
	header("Content-type: application/json");

	// https://raw.githubusercontent.com/teslascope/tokens/master/auth.tokens.py
	// https://github.com/timdorr/tesla-api/discussions/288
	// https://github.com/timdorr/tesla-api/discussions/296
	// https://github.com/timdorr/tesla-api/discussions/362

	function tesla_connect($url, $returntransfer=1, $referer="", $http_header="", $post="", $need_header=0, $cookies="", $timeout = 10)
	{
		if(!empty($post)) { $cpost = 1; } else { $cpost = 0; }
		if(is_array($http_header)) { $chheader = 1; } else { $chheader = 0; }

		$ch = curl_init();
		curl_setopt($ch, CURLOPT_URL, $url);
		curl_setopt($ch, CURLOPT_RETURNTRANSFER, $returntransfer);
		curl_setopt($ch, CURLOPT_TIMEOUT, $timeout);
		curl_setopt($ch, CURLOPT_HEADER, $need_header);
		curl_setopt($ch, CURLOPT_POST, $cpost);
		curl_setopt($ch, CURLOPT_FRESH_CONNECT, 0);
		curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, 1);
		curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 2);
		if (defined('CURL_SSLVERSION_MAX_TLSv1_2')) curl_setopt ($ch, CURLOPT_SSLVERSION,CURL_SSLVERSION_MAX_TLSv1_2); // FM - force tls1.2
		curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);

		if(!empty($referer)) { curl_setopt($ch, CURLOPT_REFERER, $referer); }

		if($chheader == 1) { curl_setopt($ch, CURLOPT_HTTPHEADER, $http_header); }

		if($cpost == 1) { curl_setopt($ch, CURLOPT_POSTFIELDS, $post); }

		if(!empty($cookies)) { curl_setopt($ch, CURLOPT_COOKIE, $cookies); }

		$response = curl_exec($ch);
		$header = curl_getinfo($ch);
		curl_close($ch);

		return array("response" => $response, "header" => $header);
	}


	function return_msg($code, $msg, $exit = false)
	{
		http_response_code($code);
		echo $msg;
		if ($exit) {
			exit;
		}
	}


	function login($url, $data, $user_agent)
	{
		$tesla_api_oauth2 = 'https://auth.tesla.com/oauth2/v3';
		// Get the Bearer token
		$http_header = array('Content-Type: application/json', 'Accept: application/json', 'User-Agent: '.$user_agent);
		$post = json_encode(array("grant_type" => "authorization_code", "client_id" => "ownerapi", "code" => $data["code"], "code_verifier" => $data["code_verifier"], "redirect_uri" => $data["redirect_uri"]));
		$response = tesla_connect($tesla_api_oauth2."/token", 1, "", $http_header, $post, 0);
		if ($response["header"]["http_code"] >= 400) {
			return_msg($response["header"]["http_code"], $response["response"], true);
			// return_msg($response["header"]["http_code"], $response["response"]["error"] . ": " . $response["response"]["error_description"], true);
		}
		$tokens = json_decode($response["response"], true);
		if(empty($tokens['access_token'])) {
			return_msg(500, "Token issue!", true);
		}
		$now = new DateTime();
		$tokens["created_at"] = $now->getTimestamp();
		$return_message = json_encode($tokens);

		// Output
		return_msg(200, $return_message);
	}

	// Get the JSON contents
	$post_data = json_decode(file_get_contents('php://input'), true);
	login($post_data["url"], $post_data["data"], $post_data["user_agent"]);
?>

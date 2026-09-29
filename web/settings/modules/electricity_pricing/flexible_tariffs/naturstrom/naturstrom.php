<?php
header("Content-type: application/json");

function naturstrom_connect($url, $returntransfer = 1, $referer = "", $http_header = "", $post = "", $need_header = 0, $cookies = "", $timeout = 10)
{
  if (!empty($post)) {
    $cpost = 1;
  } else {
    $cpost = 0;
  }
  if (is_array($http_header)) {
    $chheader = 1;
  } else {
    $chheader = 0;
  }

  $ch = curl_init();
  curl_setopt($ch, CURLOPT_URL, $url);
  curl_setopt($ch, CURLOPT_RETURNTRANSFER, $returntransfer);
  curl_setopt($ch, CURLOPT_TIMEOUT, $timeout);
  curl_setopt($ch, CURLOPT_HEADER, $need_header);
  curl_setopt($ch, CURLOPT_POST, $cpost);
  curl_setopt($ch, CURLOPT_FRESH_CONNECT, 0);
  curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, 1);
  curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 2);
  if (defined('CURL_SSLVERSION_MAX_TLSv1_2')) curl_setopt($ch, CURLOPT_SSLVERSION, CURL_SSLVERSION_MAX_TLSv1_2); // FM - force tls1.2
  curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);

  if (!empty($referer)) {
    curl_setopt($ch, CURLOPT_REFERER, $referer);
  }

  if ($chheader == 1) {
    curl_setopt($ch, CURLOPT_HTTPHEADER, $http_header);
  }

  if ($cpost == 1) {
    curl_setopt($ch, CURLOPT_POSTFIELDS, $post);
  }

  if (!empty($cookies)) {
    curl_setopt($ch, CURLOPT_COOKIE, $cookies);
  }

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


function exchange_token($oauth_base_url, $data, $user_agent)
{
  $token_url = rtrim($oauth_base_url, "/") . "/api/public-auth/oauth2/token";

  $grant_type = isset($data["grant_type"]) ? $data["grant_type"] : "authorization_code";
  $client_id = isset($data["client_id"]) ? $data["client_id"] : "";
  $code = isset($data["code"]) ? $data["code"] : "";
  $code_verifier = isset($data["code_verifier"]) ? $data["code_verifier"] : "";
  $redirect_uri = isset($data["redirect_uri"]) ? $data["redirect_uri"] : "";

  if (empty($client_id) || empty($code) || empty($code_verifier) || empty($redirect_uri)) {
    return_msg(400, json_encode(array("error" => "missing_fields", "message" => "client_id, code, code_verifier und redirect_uri sind erforderlich.")), true);
  }

  $http_header = array(
    'Content-Type: application/x-www-form-urlencoded',
    'Accept: application/json',
    'User-Agent: ' . $user_agent,
  );
  $post = http_build_query(array(
    "grant_type" => $grant_type,
    "client_id" => $client_id,
    "code" => $code,
    "code_verifier" => $code_verifier,
    "redirect_uri" => $redirect_uri,
  ));

  $response = naturstrom_connect($token_url, 1, "", $http_header, $post, 0);
  if ($response["header"]["http_code"] >= 400) {
    return_msg($response["header"]["http_code"], $response["response"], true);
  }

  $raw_response = $response["response"];
  $tokens = json_decode($raw_response, true);

  if (!is_array($tokens)) {
    return_msg(502, json_encode(array(
      "error" => "invalid_token_response",
      "message" => "Token-Antwort ist kein gültiges JSON.",
      "raw_response" => $raw_response,
    )), true);
  }

  if (empty($tokens['access_token'])) {
    return_msg(500, json_encode(array(
      "error" => "token_issue",
      "message" => "Token-Antwort enthält kein access_token.",
      "provider_response" => $tokens,
      "raw_response" => $raw_response,
    )), true);
  }

  $now = new DateTime();
  $tokens["created_at"] = $now->getTimestamp();

  return_msg(200, json_encode($tokens));
}

function fetch_accounts($oauth_base_url, $data, $user_agent)
{
  $access_token = isset($data["access_token"]) ? $data["access_token"] : "";
  if (empty($access_token)) {
    return_msg(400, json_encode(array("error" => "missing_fields", "message" => "access_token ist erforderlich.")), true);
  }

  $accounts_url = rtrim($oauth_base_url, "/") . "/api/public/accounts";
  
  $http_header = array(
    'Accept: application/json',
    'Authorization: Bearer ' . $access_token,
    'User-Agent: ' . $user_agent,
  );

  $response = naturstrom_connect($accounts_url, 1, "", $http_header, "", 0);

  if ($response["header"]["http_code"] >= 400) {
    return_msg($response["header"]["http_code"], $response["response"], true);
  }

  $raw_response = $response["response"];
  $decoded = json_decode($raw_response, true);
  if (!is_array($decoded)) {
    return_msg(502, json_encode(array(
      "error" => "invalid_accounts_response",
      "message" => "Accounts-Antwort ist kein gültiges JSON.",
      "raw_response" => $raw_response,
    )), true);
  }

  return_msg(200, json_encode($decoded), true);
}

$post_data = json_decode(file_get_contents('php://input'), true);
$oauth_base_url = isset($post_data["url"]) ? $post_data["url"] : "";
$data = isset($post_data["data"]) ? $post_data["data"] : array();
$user_agent = isset($post_data["user_agent"]) ? $post_data["user_agent"] : "openwb-ui-settings";
$action = isset($post_data["action"]) ? $post_data["action"] : "token";

if (empty($oauth_base_url) || !is_array($data)) {
  return_msg(400, json_encode(array("error" => "invalid_request", "message" => "Ungültiger Request-Body.")), true);
}

if ($action === "token") {
  exchange_token($oauth_base_url, $data, $user_agent);
} elseif ($action === "accounts") {
  fetch_accounts($oauth_base_url, $data, $user_agent);
} else {
  return_msg(400, json_encode(array("error" => "unsupported_action", "message" => "Unbekannte action.")), true);
}

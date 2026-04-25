<?php
header('Content-Type: application/json');

$input = json_decode(file_get_contents('php://input'), true);
if (!is_array($input)) {
    http_response_code(400);
    echo json_encode(['error' => 'Ungültige Anfrage.']);
    exit;
}
$client_id = $input['client_id'] ?? '';

if (!$client_id) {
    http_response_code(400);
    echo json_encode(['error' => 'Client ID fehlt.']);
    exit;
}

// PKCE generieren
$code_verifier = rtrim(strtr(base64_encode(random_bytes(64)), '+/', '-_'), '=');
$code_challenge = rtrim(strtr(base64_encode(hash('sha256', $code_verifier, true)), '+/', '-_'), '=');

// BMW Device Code anfordern
$post_data = http_build_query([
    'client_id'             => $client_id,
    'response_type'         => 'device_code',
    'scope'                 => 'authenticate_user openid cardata:api:read cardata:streaming:read',
    'code_challenge'        => $code_challenge,
    'code_challenge_method' => 'S256',
]);

$ch = curl_init('https://customer.bmwgroup.com/gcdm/oauth/device/code');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, $post_data);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Content-Type: application/x-www-form-urlencoded',
    'Accept: application/json',
]);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, true);
curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 2);

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curl_error = curl_error($ch);
curl_close($ch);

if ($curl_error) {
    error_log('BMW auth_start cURL error: ' . $curl_error);
    http_response_code(502);
    echo json_encode(['error' => 'Verbindungsfehler zur BMW API.']);
    exit;
}

if ($http_code >= 400) {
    error_log('BMW auth_start HTTP error ' . $http_code . ': ' . $response);
    http_response_code(502);
    echo json_encode(['error' => 'BMW API Fehler: HTTP ' . $http_code . '.']);
    exit;
}

$data = json_decode($response, true);
if (!$data || empty($data['device_code'])) {
    error_log('BMW auth_start invalid response: ' . $response);
    http_response_code(502);
    echo json_encode(['error' => 'Ungültige Antwort von BMW.']);
    exit;
}

// Alle Auth-Daten an die UI zurückgeben – UI speichert sie im Broker
echo json_encode([
    'user_code'        => $data['user_code'],
    'verification_uri' => $data['verification_uri_complete'] ?? $data['verification_uri'] ?? '',
    'device_code'      => $data['device_code'],
    'code_verifier'    => $code_verifier,
    'expires_at'       => time() + ($data['expires_in'] ?? 300),
    'interval'         => $data['interval'] ?? 5,
    'message'          => 'BMW Anmeldung gestartet. Bitte BMW-Seite öffnen und Code eingeben.',
    'error'            => '',
]);

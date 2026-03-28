<?php
header('Content-Type: application/json');

$input = json_decode(file_get_contents('php://input'), true);
$client_id = $input['client_id'] ?? '';

if (!$client_id) {
    echo json_encode(['connected' => false, 'error' => 'Client ID fehlt.']);
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

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curl_error = curl_error($ch);
curl_close($ch);

if ($curl_error) {
    echo json_encode(['connected' => false, 'error' => 'Verbindungsfehler: ' . $curl_error]);
    exit;
}

if ($http_code >= 400) {
    echo json_encode(['connected' => false, 'error' => 'BMW API Fehler: HTTP ' . $http_code . ' – ' . $response]);
    exit;
}

$data = json_decode($response, true);
if (!$data || empty($data['device_code'])) {
    echo json_encode(['connected' => false, 'error' => 'Ungültige Antwort von BMW: ' . $response]);
    exit;
}

// Status-Datei speichern (für Poll)
$status = [
    'connected'        => false,
    'client_id'        => $client_id,
    'device_code'      => $data['device_code'],
    'user_code'        => $data['user_code'],
    'verification_uri' => $data['verification_uri_complete'] ?? $data['verification_uri'] ?? '',
    'interval'         => $data['interval'] ?? 5,
    'expires_at'       => time() + ($data['expires_in'] ?? 300),
    'code_verifier'    => $code_verifier,
    'message'          => 'BMW Auth gestartet. Bitte BMW-Seite öffnen und Code eingeben.',
    'error'            => '',
];

$status_file = '/var/www/html/openWB/data/bmw_cardata_auth_status.json';
file_put_contents($status_file, json_encode($status, JSON_PRETTY_PRINT));
chmod($status_file, 0600);

echo json_encode([
    'connected'        => false,
    'user_code'        => $status['user_code'],
    'verification_uri' => $status['verification_uri'],
    'message'          => $status['message'],
    'error'            => '',
]);

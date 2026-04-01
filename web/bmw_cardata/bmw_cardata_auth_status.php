<?php
header('Content-Type: application/json');

// Auth-Daten kommen von der UI (aus dem Broker)
$input = json_decode(file_get_contents('php://input'), true);
$client_id    = $input['client_id'] ?? '';
$device_code  = $input['device_code'] ?? '';
$code_verifier = $input['code_verifier'] ?? '';
$expires_at   = $input['expires_at'] ?? 0;

if (!$client_id || !$device_code || !$code_verifier) {
    echo json_encode([
        'connected' => false,
        'message'   => 'Noch keine BMW Auth gestartet.',
        'error'     => '',
    ]);
    exit;
}

// Abgelaufen?
if (time() > $expires_at) {
    echo json_encode([
        'connected' => false,
        'message'   => '',
        'error'     => 'BMW Auth ist abgelaufen. Bitte erneut starten.',
    ]);
    exit;
}

// Token pollen
$post_data = http_build_query([
    'client_id'     => $client_id,
    'device_code'   => $device_code,
    'grant_type'    => 'urn:ietf:params:oauth:grant-type:device_code',
    'code_verifier' => $code_verifier,
]);

$ch = curl_init('https://customer.bmwgroup.com/gcdm/oauth/token');
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
    echo json_encode([
        'connected' => false,
        'message'   => 'Warte auf BMW-Bestätigung...',
        'error'     => '',
    ]);
    exit;
}

$data = json_decode($response, true);
$error = $data['error'] ?? '';

// Noch nicht bestätigt
if (in_array($error, ['authorization_pending', 'slow_down']) || $http_code === 400) {
    echo json_encode([
        'connected' => false,
        'message'   => 'Warte auf BMW-Bestätigung...',
        'error'     => '',
    ]);
    exit;
}

// Erfolgreich
if ($http_code === 200 && !empty($data['access_token'])) {
    echo json_encode([
        'connected'     => true,
        'access_token'  => $data['access_token'],
        'refresh_token' => $data['refresh_token'] ?? '',
        'expires_at'    => time() + ($data['expires_in'] ?? 3600) - 60,
        'message'       => 'BMW verbunden.',
        'error'         => '',
    ]);
    exit;
}

// Sonstiger Fehler
echo json_encode([
    'connected' => false,
    'message'   => '',
    'error'     => 'Fehler: ' . ($response ?: 'HTTP ' . $http_code),
]);
